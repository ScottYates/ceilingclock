// Ceiling projection alarm clock
// ESP32-S3 + two TM1637 4-digit displays (one on the front, one imaged onto the ceiling through a
// lens and mirror) + MAX98357A audio + DS3231 RTC. Time from NTP, kept by the RTC when offline.
#include <Arduino.h>
#include <WiFi.h>
#include <WiFiManager.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <LittleFS.h>
#include <Update.h>
#include <Wire.h>
#include "battery_logic.h"
#include <RTClib.h>
#include <TM1637Display.h>
#include <ArduinoJson.h>
#include <esp_sntp.h>
#include <sys/time.h>
#include "Audio.h"

#include "pins.h"
#include "segments.h"
#include "settings.h"
#include "alarm_logic.h"
#include "web_ui.h"
#include "feed_scan.h"
#include "net_fetch.h"
#include "persist.h"
#include "sys_info.h"
#include <esp_task_wdt.h>
#include <atomic>

#define FW_VERSION "2.8.0"   // bump on every release
#ifndef FW_BUILD
#define FW_BUILD __DATE__ " " __TIME__   // set by build_stamp.py in PlatformIO builds
#endif
#define HOSTNAME "ceilingclock"

// What every output is doing right now, reported to the web page's live view.
struct LiveState {
  bool projOn = false;  uint8_t projBright = 0;
  uint8_t timeSegs[4] = {0, 0, 0, 0};   // the time as it should read on the ceiling
  uint8_t projSegs[4] = {0, 0, 0, 0};   // what the projector's own display shows (mirrored)
  bool frontOn = false; uint8_t frontBright = 0;
  uint8_t vol = 0;
  bool alarmLed[2] = {false, false};
} live;

// ---------------------------------------------------------------- hardware
TM1637Display front(PIN_TM_CLK, PIN_TM_DIO);
TM1637Display proj(PIN_PROJ_CLK, PIN_PROJ_DIO);   // imaged onto the ceiling
RTC_DS3231 rtc;
bool rtcPresent = false;

WebServer server(80);
WiFiManager wm;
bool serverStarted = false;

// The loop watchdog (set up at the end of setup()). Long uploads are handled inside one web server call,
// so they feed it as each chunk arrives.
inline void feedWatchdog() { esp_task_wdt_reset(); }

// ---------------------------------------------------------------- state kept across resets
bool startedWarm = false;   // this start was a reset (kept state was intact), not a power-on
RTC_NOINIT_ATTR Persist persist;
bool persistLoad() {
  esp_reset_reason_t why = esp_reset_reason();
  bool ok = why != ESP_RST_POWERON && why != ESP_RST_UNKNOWN && persist.magic == PERSIST_MAGIC && persist.crc == persistCrc(persist);
  if (!ok) { memset(&persist, 0, sizeof persist); persist.magic = PERSIST_MAGIC; persist.ringAlarm = -1; persistSave(); }
  return ok;
}
void persistSave() { persist.crc = persistCrc(persist); }

// ---------------------------------------------------------------- time state
volatile time_t lastNtpSync = 0;
volatile bool ntpJustSynced = false;
static bool timeValid() { return time(nullptr) > 1700000000; }

void onNtpSync(struct timeval* tv) {
  lastNtpSync = tv->tv_sec;
  ntpJustSynced = true;
}

void applyTimeConfig() {
  sntp_set_sync_interval(60 * 60 * 1000);  // resync every hour
  sntp_set_time_sync_notification_cb(onNtpSync);
  configTzTime(cfg.tz.c_str(), cfg.ntp.c_str(), "time.nist.gov", "time.google.com");
}

// ---------------------------------------------------------------- audio task
// The Audio object lives on its own task so playback stays smooth while the
// web server and displays are busy. Looking up a podcast feed also happens there.
enum AudioCmdType : uint8_t { AC_PLAY, AC_STREAM, AC_STOP, AC_VOL };
struct AudioCmd { AudioCmdType type; uint8_t vol; char path[300]; };
QueueHandle_t audioQ;
volatile bool audioRunning = false;

// Stream status, written by the audio task.
enum StreamState : uint8_t { SS_IDLE, SS_CONNECTING, SS_PLAYING, SS_FAILED, SS_ENDED };
volatile uint8_t streamState = SS_IDLE;
char streamTitle[100] = "";   // podcast episode, or the station's "now playing"
char streamNote[64] = "";     // why a stream failed
uint32_t streamStartMs = 0;

Audio* audioPlayer = nullptr;

// ---- podcast feeds
// A feed URL becomes its newest episode's audio URL (and title). Radio streams and links to audio files come
// back unchanged. Feeds used by alarms are looked up ahead of time by a background task (feedTask, every hour
// and whenever an alarm's feed changes), so an alarm normally starts its episode at once instead of first
// downloading the feed. A lookup older than FEED_FRESH_MS is done again at ring time.
const uint32_t FEED_REFRESH_MS = 60UL * 60 * 1000, FEED_FRESH_MS = 12UL * 60 * 60 * 1000;
struct FeedEntry { std::string feed, url, title, err; uint32_t atMs = 0; bool ok = false; int64_t date = 0; };
static FeedEntry feedCache[4];
// a tiny lock shared by the feed task, the audio task and the web server (held only to copy a few strings)
struct FeedLock {
  std::atomic_flag f = ATOMIC_FLAG_INIT;
  void lock() { while (f.test_and_set(std::memory_order_acquire)) vTaskDelay(1); }
  void unlock() { f.clear(std::memory_order_release); }
};
struct FeedGuard { FeedLock& l; explicit FeedGuard(FeedLock& x) : l(x) { l.lock(); } ~FeedGuard() { l.unlock(); } };
static FeedLock feedMx;

static bool feedCached(const char* feed, std::string& url, std::string& title) {
  FeedGuard g(feedMx);
  for (auto& e : feedCache)
    if (e.ok && e.feed == feed && millis() - e.atMs < FEED_FRESH_MS) { url = e.url; title = e.title; return true; }
  return false;
}
static void feedStore(const char* feed, bool ok, const std::string& url, const std::string& title, const std::string& err, int64_t date) {
  FeedGuard g(feedMx);
  FeedEntry* slot = nullptr;
  for (auto& e : feedCache) if (e.feed == feed) slot = &e;
  if (!slot) {                                       // oldest slot
    slot = &feedCache[0];
    for (auto& e : feedCache) if (e.feed.empty() || e.atMs < slot->atMs) { slot = &e; if (e.feed.empty()) break; }
  }
  if (!ok && slot->ok && slot->feed == feed && millis() - slot->atMs < FEED_FRESH_MS) { slot->err = err; return; }   // keep the last good answer
  slot->feed = feed; slot->ok = ok; slot->url = url; slot->title = title; slot->err = err; slot->date = date; slot->atMs = millis();
}

// Downloads the feed and picks its newest episode. True with the episode's URL in out (or the URL unchanged
// if it turned out to be audio).
// While sound is playing the background lookups wait: a feed download competing with the episode or radio
// stream for the Wi-Fi made the start of playback choppy. audioBusy is set by loop().
std::atomic<bool> audioBusy{false};
static bool lookupFeed(const char* url, std::string& out, std::string& title, std::string& err, int64_t& date, bool yieldToAudio = false) {
  out = url; date = 0;
  FeedScan scan;
  bool sniffed = false, isAudio = false, interrupted = false;
  size_t total = 0;
  std::string ctype;
  bool ok = netFetch(url, ctype, [&](const char* p, size_t n) {
    if (!sniffed) {
      sniffed = true;
      std::string ct = ctype;
      for (auto& ch : ct) ch = (char)tolower((unsigned char)ch);
      if (ct.rfind("audio/", 0) == 0 || ct.find("mpegurl") != std::string::npos || ct.find("scpls") != std::string::npos ||
          !FeedScan::looksLikeXml(p, n)) { isAudio = true; return false; }
    }
    if (yieldToAudio && audioBusy) { interrupted = true; return false; }
    scan.feed(p, n);
    total += n;
    return !scan.done() && total < 4u * 1024 * 1024;   // a newest-first feed stops after a few episodes
  });
  if (interrupted) { err = "interrupted"; return false; }
  if (!ok) { err = "could not reach the URL"; return false; }
  if (isAudio || !sniffed) return true;
  scan.finish();
  if (!scan.found()) { err = "no episodes found in the feed"; return false; }
  out = scan.url();
  title = scan.title();
  date = scan.date();
  return true;
}

bool resolveStream(const char* url, std::string& out, std::string& title, std::string& err) {
  out = url;
  if (urlLooksLikeAudio(url)) return true;
  if (feedCached(url, out, title)) return true;
  int64_t date;
  bool ok = lookupFeed(url, out, title, err, date);
  if (ok && out != url) feedStore(url, true, out, title, "", date);
  return ok;
}

// Background lookups: the main loop queues the feeds that alarms use; this task fetches them one at a time.
struct FeedReq { char url[300]; };
QueueHandle_t feedQ;
void feedTask(void*) {
  FeedReq r;
  for (;;) {
    if (xQueueReceive(feedQ, &r, pdMS_TO_TICKS(1000)) != pdTRUE) { vTaskDelay(pdMS_TO_TICKS(250)); continue; }
    std::string out, title, err;
    int64_t date;
    bool ok;
    for (;;) {                                       // wait for quiet, and start again if sound starts meanwhile
      while (audioBusy) vTaskDelay(pdMS_TO_TICKS(1000));
      if (WiFi.status() != WL_CONNECTED) { ok = false; break; }
      ok = lookupFeed(r.url, out, title, err, date, true);
      if (ok || err != "interrupted") break;
    }
    if (WiFi.status() != WL_CONNECTED) continue;
    if (ok && out == r.url) continue;               // plain audio or a radio stream: nothing to remember
    feedStore(r.url, ok, out, title, err, date);
  }
}
// Called from loop(): queue the alarms' feeds when they change and every hour (not while an alarm rings).
void scheduleFeedLookups(bool busy) {
  static uint32_t lastCheck = 0, lastAll = 0;
  static std::string lastSet;
  if (millis() - lastCheck < 5000 || busy || WiFi.status() != WL_CONNECTED) return;
  lastCheck = millis();
  std::string set;
  for (int i = 0; i < cfg.alarmCount; i++) {
    const AlarmCfg& a = cfg.alarms[i];
    if (!a.t.enabled || !a.stream.length() || urlLooksLikeAudio(a.stream.c_str())) continue;
    if (set.find(std::string(a.stream.c_str()) + "\n") == std::string::npos) set += std::string(a.stream.c_str()) + "\n";
  }
  bool due = set != lastSet || (lastAll && millis() - lastAll > FEED_REFRESH_MS) || (!lastAll && millis() > 30000);
  if (!due || set.empty()) { if (set != lastSet) lastSet = set; return; }
  lastSet = set; lastAll = millis();
  for (size_t a = 0, b; (b = set.find('\n', a)) != std::string::npos; a = b + 1) {
    FeedReq r;
    strlcpy(r.url, set.substr(a, b - a).c_str(), sizeof r.url);
    xQueueSend(feedQ, &r, 0);
  }
}

// ---- audio diagnostics (/api/audiodiag): the library's last messages and the loudest sample seen,
// before and after volume, since the last play started. Helps tell "no data" from "silent data".
static char audioLog[8][96];
static uint8_t audioLogN = 0;
static char startNote[64];   // the library's "start buffer ... bytes after ... ms" for the last stream start
static volatile int32_t peakRaw = 0, peakOut = 0;
static volatile uint32_t samplesOut = 0;
static volatile uint32_t audioFrames = 0;   // grows while sound reaches the amplifier; never reset (sound watchdog)
static void audioLogAdd(const char* m) {
  strlcpy(audioLog[audioLogN % 8], m, sizeof audioLog[0]);
  audioLogN++;
}
static int32_t absPeak(const int32_t* b, int n) {
  int32_t p = 0;
  for (int i = 0; i < n; i++) { int32_t v = b[i] < 0 ? -(b[i] + 1) : b[i]; if (v > p) p = v; }
  return p;
}
void audio_process_raw_samples(int32_t* outBuff, int16_t validSamples) {
  int32_t p = absPeak(outBuff, validSamples); if (p > peakRaw) peakRaw = p;
}
void audio_process_i2s(int32_t* outBuff, int16_t validSamples, bool* continueI2S) {
  int32_t p = absPeak(outBuff, validSamples); if (p > peakOut) peakOut = p;
  samplesOut += validSamples;
  audioFrames += validSamples;
}

void audioInit() {
  audioPlayer = new Audio();
  audioPlayer->setPinout(PIN_I2S_BCLK, PIN_I2S_LRC, PIN_I2S_DOUT);
  audioPlayer->setVolume(0);
  // A gentle curve: every step is audible (step 1 is -34 dB, 21 is 0 dB). The library's default made
  // anything under about a third of the slider practically silent.
  audioPlayer->setVolumeCurve([](float t) { return -36.0f * (1.0f - t); });
  // Streams and podcast episodes start once about 8 s of audio has arrived (10 s at most), so a weak
  // Wi-Fi link doesn't run the buffer dry in the first few seconds. Added to the library by patch_audio.py.
  audioPlayer->setStartBuffer(8000, 10000);
  Audio::audio_info_callback = [](Audio::msg_t m) {
    if (!m.msg || !*m.msg) return;
    audioLogAdd(m.msg);
    if (!strncmp(m.msg, "start buffer", 12)) strlcpy(startNote, m.msg, sizeof startNote);
    if (m.e == Audio::evt_streamtitle || (m.e == Audio::evt_name && !streamTitle[0])) strlcpy(streamTitle, m.msg, sizeof streamTitle);
  };
}

// Handles queued commands and feeds the decoder; called continuously by the audio task.
void audioStep() {
  AudioCmd c;
  while (xQueueReceive(audioQ, &c, 0) == pdTRUE) {
    if (c.type == AC_PLAY) {
      audioPlayer->stopSong();
      peakRaw = peakOut = 0; samplesOut = 0;
      audioPlayer->setVolume(c.vol);
      bool ok = audioPlayer->connecttoFS(LittleFS, c.path);
      char m[96]; snprintf(m, sizeof m, "play %s vol %u: %s", c.path, c.vol, ok ? "started" : "FAILED");
      audioLogAdd(m);
    } else if (c.type == AC_STREAM) {
      audioPlayer->stopSong();
      audioPlayer->setVolume(c.vol);
      startNote[0] = 0;
      std::string url, title, err;
      streamTitle[0] = streamNote[0] = 0;
      if (resolveStream(c.path, url, title, err) && audioPlayer->connecttohost(url.c_str())) {
        strlcpy(streamTitle, title.c_str(), sizeof streamTitle);
        streamStartMs = millis();
        streamState = SS_PLAYING;
      } else {
        strlcpy(streamNote, err.empty() ? "the stream did not start" : err.c_str(), sizeof streamNote);
        streamState = SS_FAILED;
      }
    } else if (c.type == AC_STOP) {
      audioPlayer->stopSong();
    } else {
      audioPlayer->setVolume(c.vol);
    }
  }
  audioPlayer->loop();
  audioRunning = audioPlayer->isRunning();
  static bool streamRan = false;
  if (streamState != SS_PLAYING) streamRan = false;
  else if (audioRunning) streamRan = true;
  if (streamState == SS_PLAYING && !audioRunning && (streamRan || millis() - streamStartMs > 3000)) {
    strlcpy(streamNote, "the stream stopped", sizeof streamNote);
    streamState = SS_ENDED;
  }
}

void audioTask(void*) {
  audioInit();
  for (;;) {
    audioStep();
    vTaskDelay(1);
  }
}

void audioPlay(const String& path, uint8_t vol) {
  AudioCmd c{AC_PLAY, vol, {0}};
  String p = path;
  if (!LittleFS.exists(p)) p = "/sounds/beep.wav";
  strlcpy(c.path, p.c_str(), sizeof(c.path));
  streamState = SS_IDLE;
  xQueueSend(audioQ, &c, pdMS_TO_TICKS(100));
  audioRunning = true;  // assume started until the task reports otherwise
  live.vol = vol;
}
void audioStream(const String& url, uint8_t vol) {
  AudioCmd c{AC_STREAM, vol, {0}};
  strlcpy(c.path, url.c_str(), sizeof(c.path));
  streamState = SS_CONNECTING;
  streamTitle[0] = streamNote[0] = 0;
  xQueueSend(audioQ, &c, pdMS_TO_TICKS(100));
  live.vol = vol;
}
void audioStop() { AudioCmd c{AC_STOP, 0, {0}}; streamState = SS_IDLE; xQueueSend(audioQ, &c, pdMS_TO_TICKS(100)); }
// Volume steps are only sent while the queue is nearly empty, so they can never crowd out a play command
// (a stream that is still connecting holds the audio task for a while). The ramp sends the next step later.
bool audioVolume(uint8_t v) {
  if (uxQueueMessagesWaiting(audioQ) > 2) return false;
  AudioCmd c{AC_VOL, v, {0}};
  if (xQueueSend(audioQ, &c, 0) != pdTRUE) return false;
  live.vol = v;
  return true;
}
bool soundPlaying() { return audioRunning || streamState == SS_PLAYING; }

// Writes a short beep-beep WAV so there is always a sound, even before you upload any.
void ensureDefaultSound() {
  LittleFS.mkdir("/sounds");
  const uint32_t rate = 16000, samples = rate * 14 / 10;  // 1.4 s
  if (LittleFS.exists("/sounds/beep.wav")) {   // keep it unless it got damaged
    File old = LittleFS.open("/sounds/beep.wav", "r");
    bool good = old && old.size() == 44 + samples * 2;
    if (old) old.close();
    if (good) return;
    LittleFS.remove("/sounds/beep.wav");
  }
  File f = LittleFS.open("/sounds/beep.wav", "w");
  if (!f) return;
  auto w32 = [&](uint32_t v) { f.write((uint8_t*)&v, 4); };
  auto w16 = [&](uint16_t v) { f.write((uint8_t*)&v, 2); };
  f.write((const uint8_t*)"RIFF", 4); w32(36 + samples * 2);
  f.write((const uint8_t*)"WAVEfmt ", 8); w32(16); w16(1); w16(1); w32(rate); w32(rate * 2); w16(2); w16(16);
  f.write((const uint8_t*)"data", 4); w32(samples * 2);
  int16_t buf[256];
  for (uint32_t i = 0; i < samples;) {
    int n = 0;
    for (; n < 256 && i < samples; n++, i++) {
      uint32_t ms = i * 1000 / rate;
      bool on = ms < 800 && (ms % 200) < 100;  // 4 beeps, then silence
      buf[n] = on ? (int16_t)(12000 * sinf(2 * PI * 1000.0f * i / rate)) : 0;
    }
    f.write((uint8_t*)buf, n * 2);
  }
  f.close();
}

// ---------------------------------------------------------------- alarm state
enum RingState : uint8_t { RS_IDLE, RS_RINGING, RS_SNOOZED };
RingState ringState = RS_IDLE;
int ringAlarm = -1;
time_t ringStart = 0, snoozeUntil = 0;
uint32_t ringRampSec = 0, lastPlayMs = 0;
uint8_t lastSentVol = 255;
time_t lastCheck = 0;
bool testPlaying = false;
AlarmCfg ringCfg;   // a copy of the ringing alarm, so editing or deleting alarms meanwhile can't change or stop it
// what the ringing alarm is playing: its sound file, its stream, the sound file as a backup for a failed
// stream, or the built-in beep when its own sound didn't play
enum RingSrc : uint8_t { SRC_FILE, SRC_STREAM, SRC_BACKUP, SRC_BEEP };
RingSrc ringSrc = SRC_FILE;
uint8_t streamTries = 0;
uint32_t srcStartMs = 0;      // when the current sound source started (not each loop of a file)
uint32_t lastFrameMs = 0;     // when sound last reached the amplifier
const uint32_t STREAM_CONNECT_MS = 25000;  // give up on a stream that hasn't started by then
const uint32_t SOUND_SILENT_MS = 10000;    // a sound that has produced nothing for this long has failed
const char* BEEP = "/sounds/beep.wav";
const uint8_t ALARM_MIN_VOLUME = 6;        // an alarm never ends up quieter than this (of 21)
const time_t CATCH_UP_SEC = 30 * 60;       // alarms still ring if the clock jumped or the loop was held up this long
const time_t BOOT_CATCH_UP_SEC = 15 * 60;  // after power-on, alarms due in the last 15 minutes still ring

void ringSound(uint8_t vol) {
  if (ringSrc == SRC_BEEP) audioPlay(BEEP, vol);
  else if (ringCfg.stream.length() && ringSrc != SRC_BACKUP) { ringSrc = SRC_STREAM; audioStream(ringCfg.stream, vol); }
  else { if (!ringCfg.stream.length()) ringSrc = SRC_FILE; audioPlay(ringCfg.sound, vol); }
  lastPlayMs = millis();
}

// The target volume and fade-in for the ringing alarm: never too quiet to hear, and the fade-in always
// finishes well inside the time the alarm is allowed to ring.
uint8_t ringTargetVolume() { return max(ringCfg.volume, ALARM_MIN_VOLUME); }
uint32_t ringRampLimit(uint32_t rampSec) { return min(rampSec, (uint32_t)ringCfg.maxRingMin * 60 / 3); }

uint32_t peekUntilMs = 0;  // button A "show me the time" while displays are off

uint8_t prevFrontMode = DM_ON, prevProjMode = DM_ON;

// Starts ringing alarm i. useBeep: its own sound already failed (after a restart), so go straight to the beep.
// keepCfg: ring the copy taken when it first rang (after a snooze), even if the alarms were edited since.
void startRing(int i, uint32_t rampSec, bool useBeep = false, bool keepCfg = false) {
  if (!keepCfg) {
    if (i >= 0 && i < cfg.alarmCount) ringCfg = cfg.alarms[i];
    else { ringCfg = AlarmCfg(); ringCfg.label = "Alarm"; }   // gone: ring with the defaults
  }
  if (!keepCfg && !useBeep) persist.restarts = 0;   // a new ring, not a resumed one
  ringAlarm = i;
  ringState = RS_RINGING;
  ringStart = time(nullptr);
  ringRampSec = ringRampLimit(rampSec);
  lastSentVol = rampVolume(ringTargetVolume(), 0, ringRampSec);
  ringSrc = useBeep ? SRC_BEEP : SRC_FILE;
  streamTries = 1;
  ringSound(lastSentVol);
  srcStartMs = millis();
  testPlaying = false;
  Serial.printf("Alarm %d (%s) ringing\n", i, ringCfg.label.c_str());
}

// The current sound isn't playing: step down to something that will. Stream -> its backup sound ->
// the built-in beep -> restart the clock (it carries on ringing, with the beep, after the restart).
void soundFailed(const char* why) {
  Serial.printf("Alarm sound failed (%s)\n", why);
  if (ringSrc == SRC_STREAM) ringSrc = SRC_BACKUP;
  else if (ringSrc != SRC_BEEP) ringSrc = SRC_BEEP;
  else if (persist.restarts < 3) {   // even the beep is silent: the audio task is stuck
    persist.restarts++;
    persist.useBeep = 1;
    persist.ringState = RS_RINGING;
    persist.ringAlarm = ringAlarm;
    persist.ringStart = ringStart;
    persistSave();
    Serial.println("Restarting to get the alarm sound going again");
    delay(100);
    ESP.restart();
  }
  ringSound(lastSentVol);
  srcStartMs = millis();
}

void showFront(const uint8_t m[4], uint32_t ms);
void thenFront(const uint8_t m[4], uint32_t ms);
void showClockTime(time_t t, uint32_t ms);
void snooze() {
  if (ringState != RS_RINGING) return;
  audioStop();
  ringState = RS_SNOOZED;
  snoozeUntil = time(nullptr) + ringCfg.snoozeMin * 60;
  const uint8_t m[4] = {0x6D, 0x54, 0x5C, 0x5B};  // SnoZ
  showFront(m, 1200);
  showClockTime(snoozeUntil, 2000);
}

void dismiss() {
  if (ringState == RS_IDLE) return;
  audioStop();
  ringState = RS_IDLE;
  ringAlarm = -1;
  persist.restarts = 0;
  persist.useBeep = 0;
  const uint8_t m[4] = {0x6D, 0x78, 0x5C, 0x73};  // StoP
  showFront(m, 1500);
}

// Rings every alarm with an occurrence since the last check. The window reaches back up to 30 minutes, so
// an alarm still rings if the clock jumps forward over it (the first time sync after starting from the
// backup clock) or something held the loop up. After power-on it reaches back 15 minutes. Each occurrence
// rings once (lastFiredAt, kept across resets), and an alarm moved to a later time the same day still rings.
void checkAlarms(time_t now) {
  if (!timeValid()) return;
  if (lastCheck == 0) lastCheck = now - BOOT_CATCH_UP_SEC;
  if (now < lastCheck) { lastCheck = now; return; }   // the clock went back: nothing new is due
  if (now == lastCheck) return;
  bool changed = false;
  for (int i = 0; i < cfg.alarmCount; i++) {
    AlarmCfg& a = cfg.alarms[i];
    time_t t = alarmToRing(a.t, lastCheck, now, persist.lastFiredAt[i], CATCH_UP_SEC);
    if (!t) continue;
    persist.lastFiredAt[i] = t;
    bool skip = a.t.skipNext;
    if (a.t.skipNext) { a.t.skipNext = false; changed = true; }
    if (a.t.days == 0) { a.t.enabled = false; changed = true; }  // one-time alarm
    if (!skip) startRing(i, a.rampSec);
  }
  lastCheck = now;
  if (changed) saveConfig();
}

void serviceRing(time_t now) {
  static uint32_t lastFrames = 0;
  if (audioFrames != lastFrames) { lastFrames = audioFrames; lastFrameMs = millis(); }
  if (ringState == RS_RINGING) {
    uint32_t el = now > ringStart ? now - ringStart : 0;
    uint8_t v = rampVolume(ringTargetVolume(), el, ringRampSec);
    if (v != lastSentVol && audioVolume(v)) lastSentVol = v;
    uint32_t quietMs = millis() - max(lastFrameMs, srcStartMs);   // no sound since the source started
    if (ringSrc == SRC_STREAM) {
      bool slow = streamState == SS_CONNECTING && millis() - lastPlayMs > STREAM_CONNECT_MS;
      if (streamState == SS_ENDED && streamTries < 3 && millis() - lastPlayMs > 60000) {
        streamTries++;  // it played for a while and dropped: reconnect
        ringSound(v);
      } else if (slow || streamState == SS_FAILED || streamState == SS_ENDED) {
        soundFailed(slow ? "stream too slow to start" : streamNote);
      } else if (streamState == SS_PLAYING && quietMs > SOUND_SILENT_MS + 10000) {   // allows for the start buffer
        soundFailed("stream connected but no sound");
      }
    } else {
      if (!audioRunning && millis() - lastPlayMs > 1500) ringSound(v);   // loop the sound file
      if (quietMs > SOUND_SILENT_MS) soundFailed("no sound from the file");
    }
    if (el > (uint32_t)ringCfg.maxRingMin * 60) dismiss();
  } else if (ringState == RS_SNOOZED && now >= snoozeUntil) {
    startRing(ringAlarm, 10, persist.useBeep, true);
  }
}

// Soonest upcoming alarm (honouring skip). Returns index or -1.
int nextAlarm(time_t now, time_t& when) {
  int best = -1; when = 0;
  for (int i = 0; i < cfg.alarmCount; i++) {
    time_t t = alarmNext(cfg.alarms[i].t, now, true);
    if (t && (!when || t < when)) { when = t; best = i; }
  }
  return best;
}

// ---------------------------------------------------------------- light / visibility
int ldrRaw = 0;
bool nightNow = false;

bool computeNight(const struct tm& lt) {
  bool n = inWindow(lt.tm_hour * 60 + lt.tm_min, cfg.nightStart, cfg.nightEnd);
  if (cfg.useLdr && ldrRaw < cfg.ldrThreshold) n = true;
  return n;
}

bool displayVisible(const DisplayCfg& d) {
  if (millis() < peekUntilMs) return true;
  if (ringState != RS_IDLE && cfg.showOnAlarm) return true;
  switch (d.mode) {
    case DM_OFF: return false;
    case DM_NIGHT_ONLY: return nightNow;
    case DM_DAY_ONLY: return !nightNow;
    default: return true;
  }
}

// ---------------------------------------------------------------- projector
// The projector is a second TM1637 module. The lens and mirror flip its picture, so the digits are
// sent pre-flipped (segments.h): left/right, top/bottom, or turned 180 degrees, as set on the web page.
bool projRedraw = true;  // set when the flip settings change

void renderProj(const struct tm& lt, bool visible, uint8_t bright) {
  seg::timeDigits(lt.tm_hour, lt.tm_min, cfg.hour24, timeValid(), live.timeSegs);
  seg::forProjector(live.timeSegs, timeValid(), cfg.projMirrorX, cfg.projMirrorY, cfg.projUpsideDown, live.projSegs);
  live.projOn = visible;
  live.projBright = visible ? bright : 0;
  static int lastKey = -2;
  int key = visible ? ((lt.tm_hour * 60 + lt.tm_min) * 8 + bright) * 2 + timeValid() : -1;
  if (key == lastKey && !projRedraw) return;
  lastKey = key;
  projRedraw = false;
  if (!visible) { proj.setBrightness(0, false); proj.clear(); return; }
  proj.setBrightness(bright, true);
  proj.setSegments(live.projSegs);
}

// ---------------------------------------------------------------- front display
// Short messages on the front display whenever something changes, from a button or from the web page,
// so you can tell what happened (shown even when the display is switched off):
//   1 on / 1 oF   alarm 1 switched on (then its time, and A or P in 12-hour mode) or off; 2..8 likewise
//   d on / d oF   front display on or off        P on / P oF   ceiling projection on or off
//   SnoZ          snoozed (then the time it rings again, and A or P)        StoP   alarm stopped
//   AL12 / AL1- / AL-2 / AL--   which of alarms 1 and 2 are on (snooze button when nothing rings)
//   FLIP          projection turned upside down    rSEt   Wi-Fi forgotten, restarting
//   SEt1          setting alarm 1's time (hold its button); CAnC: left without saving
//   bAtt / PLug   USB power lost (running on the battery base) / back; bA 9: battery below 10 %
const uint8_t LET_P = SEG_A | SEG_B | SEG_E | SEG_F | SEG_G, LET_d = SEG_B | SEG_C | SEG_D | SEG_E | SEG_G;
const uint8_t LET_o = SEG_C | SEG_D | SEG_E | SEG_G, LET_n = SEG_C | SEG_E | SEG_G, LET_F = SEG_A | SEG_E | SEG_F | SEG_G;
const uint8_t LET_O = SEG_A | SEG_B | SEG_C | SEG_D | SEG_E | SEG_F, LET_E = SEG_A | SEG_D | SEG_E | SEG_F | SEG_G;
const uint8_t LET_S = 0x6D, LET_Z = 0x5B, LET_t = 0x78, LET_A = 0x77, LET_L = 0x38, LET_I = 0x06, LET_r = 0x50, LET_DASH = 0x40;
uint8_t frontMsg[4];
uint32_t frontMsgUntil = 0, frontMsgSeq = 0;
struct QueuedMsg { uint8_t s[4]; uint16_t ms; };
QueuedMsg frontNext[3];
uint8_t frontNextN = 0;
// Show a message now, replacing whatever message is up (and anything queued after it)
void showFront(const uint8_t m[4], uint32_t ms) {
  memcpy(frontMsg, m, 4);
  frontMsgUntil = millis() + ms;
  frontMsgSeq++;
  frontNextN = 0;
}
// Show a message after the current one (or now, if none is up)
void thenFront(const uint8_t m[4], uint32_t ms) {
  if (!frontMsgUntil || (int32_t)(millis() - frontMsgUntil) >= 0) { showFront(m, ms); return; }
  if (frontNextN == 3) return;
  memcpy(frontNext[frontNextN].s, m, 4);
  frontNext[frontNextN++].ms = ms;
}
// The current message has run out: move to the next queued one. Returns false when there is none.
bool nextFront() {
  if (!frontNextN) return false;
  memcpy(frontMsg, frontNext[0].s, 4);
  frontMsgUntil = millis() + frontNext[0].ms;
  frontMsgSeq++;
  for (int i = 1; i < frontNextN; i++) frontNext[i - 1] = frontNext[i];
  frontNextN--;
  return true;
}
void flashFront(uint8_t who, bool on) {
  const uint8_t m[4] = {who, 0, LET_o, on ? LET_n : LET_F};
  showFront(m, 1500);
}

// Setting an alarm's time from the clock (hold its button): which alarm (-1 = not setting), which part
// (0 = hours, 1 = minutes), the time being set, and when a button was last pressed.
int setAlarm = -1;
uint8_t setField = 0;
int setH = 0, setM = 0;
uint32_t setLastMs = 0, setStepMs = 0;
const uint32_t SET_TIMEOUT_MS = 30000;

void renderFront(const struct tm& lt, bool visible, uint8_t bright) {
  live.frontOn = visible;
  live.frontBright = bright;
  static int lastKey = -2;
  static uint32_t shownSeq = 0;
  if (frontMsgUntil && (int32_t)(millis() - frontMsgUntil) >= 0) nextFront();
  if (frontMsgUntil && (int32_t)(millis() - frontMsgUntil) < 0) {
    if (shownSeq != frontMsgSeq) {
      shownSeq = frontMsgSeq;
      front.setBrightness(max(bright, (uint8_t)3), true);
      front.setSegments(frontMsg);
      lastKey = -2;  // redraw the time when the message ends
    }
    return;
  }
  frontMsgUntil = 0;
  if (setAlarm >= 0) {   // setting an alarm: its time in 24-hour form, the part being set blinking
    uint32_t ms = millis();
    bool show = (ms / 400) % 2 == 0 || ms - setStepMs < 600;   // steady while it is being changed
    uint8_t d[4];
    seg::timeDigits(setH, setM, true, true, d);
    d[1] |= seg::COLON;
    if (!show) { d[setField * 2] = 0; d[setField * 2 + 1] &= seg::COLON; }
    static uint8_t lastD[4] = {1, 1, 1, 1};
    if (memcmp(d, lastD, 4) || lastKey != -3) {
      front.setBrightness(max(bright, (uint8_t)3), true);
      front.setSegments(d);
      memcpy(lastD, d, 4);
      lastKey = -3;
    }
    return;
  }
  int key = visible ? (lt.tm_hour * 60 + lt.tm_min) * 8 + bright + (timeValid() ? 0 : 100000) : -1;
  if (key == lastKey) return;
  lastKey = key;
  if (!visible) {  // fully dark: blank segments and switch the driver off
    front.setBrightness(0, false);
    front.clear();
    return;
  }
  front.setBrightness(bright, true);
  if (!timeValid()) {
    const uint8_t dashes[4] = {SEG_G, SEG_G, SEG_G, SEG_G};
    front.setSegments(dashes);
    return;
  }
  int h = lt.tm_hour;
  if (!cfg.hour24) { h %= 12; if (h == 0) h = 12; }
  front.showNumberDecEx(h * 100 + lt.tm_min, 0b01000000, cfg.hour24, 4, 0);
}

// ---------------------------------------------------------------- buttons
struct Button {
  uint8_t pin; bool down = false; uint32_t t0 = 0, lastChange = 0, nextRepeat = 0; uint8_t longLevel = 0;
  explicit Button(uint8_t p) : pin(p) {}
};
Button btnA(PIN_BTN_A), btnB(PIN_BTN_B), btnAl[2] = {Button(PIN_BTN_AL1), Button(PIN_BTN_AL2)};

// The alarm buttons' lights are dark except for short feedback:
//   LS_SHOW   steady for a few seconds (the alarm is on)
//   LS_OFF    two quick blinks, then dark (the alarm is now off)
//   while that alarm rings: slow blink, so you can see which button stops it
const uint8_t LED_PIN[2] = {PIN_LED_AL1, PIN_LED_AL2};
enum LedShow : uint8_t { LS_DARK, LS_SHOW, LS_OFF };
LedShow ledShow[2] = {LS_DARK, LS_DARK};
uint32_t ledFrom[2] = {0, 0};
void ledFeedback(int i, LedShow s) { ledShow[i] = s; ledFrom[i] = millis(); }

void renderAlarmLeds(bool night) {
  uint32_t ms = millis();
  uint16_t full = night ? 120 : 1023;  // 10-bit PWM; dim at night
  for (int i = 0; i < 2; i++) {
    bool on = false;
    uint32_t t = ms - ledFrom[i];
    if (ringState == RS_RINGING && ringAlarm == i) on = (ms / 500) % 2 == 0;
    else if (setAlarm == i) on = true;   // being set: steady, so you can see which alarm
    else if (ledShow[i] == LS_SHOW) { on = t < 3000; if (!on) ledShow[i] = LS_DARK; }
    else if (ledShow[i] == LS_OFF) { on = t < 800 && (t / 200) % 2 == 0; if (t >= 800) ledShow[i] = LS_DARK; }
    uint16_t duty = on ? full : 0;
    live.alarmLed[i] = on;
    static uint16_t last[2] = {9999, 9999};
    if (duty != last[i]) { ledcWrite(LED_PIN[i], duty); last[i] = duty; }
  }
}

// A clock time on the front display after the current message, e.g. " 6:30". In 12-hour mode a short "A" or "P"
// follows in the last digit: the display can't show AM/PM any other way (no "M", and the colon's two dots are one LED).
void showClockTime(int hour, int minute, uint32_t ms) {
  uint8_t d[4];
  seg::timeDigits(hour, minute, cfg.hour24, true, d);
  d[1] |= seg::COLON;
  thenFront(d, ms);
  if (!cfg.hour24) {
    const uint8_t ap[4] = {0, 0, 0, hour < 12 ? LET_A : LET_P};
    thenFront(ap, 900);
  }
}
void showClockTime(time_t t, uint32_t ms) {
  struct tm lt;
  localtime_r(&t, &lt);
  showClockTime(lt.tm_hour, lt.tm_min, ms);
}

// Watches the settings for changes, whatever made them (a button, the web page), and says on the front
// display what happened; the alarm buttons' lights give the same feedback. Changes an alarm makes to
// itself when it fires (a one-time alarm switching off) are not announced.
void announceChanges() {
  static bool first = true;
  static uint8_t count = 0;
  static uint16_t bits = 0;
  static bool frontOn = false, projOn = false, upside = false;
  uint16_t nb = 0;
  for (int i = 0; i < cfg.alarmCount; i++) if (cfg.alarms[i].t.enabled) nb |= 1 << i;
  bool fOn = cfg.front.mode != DM_OFF, pOn = cfg.proj.mode != DM_OFF;
  if (!first && ringState == RS_IDLE) {
    if (cfg.alarmCount == count && nb != bits) {
      for (int i = 0; i < count; i++) {
        bool on = nb >> i & 1;
        if (on == (bool)(bits >> i & 1)) continue;
        const uint8_t m[4] = {seg::DIGIT[(i + 1) % 10], 0, LET_o, on ? LET_n : LET_F};
        showFront(m, 1200);
        if (on) showClockTime(cfg.alarms[i].t.hour, cfg.alarms[i].t.minute, 2000);
        if (i < 2) ledFeedback(i, on ? LS_SHOW : LS_OFF);
      }
    }
    if (fOn != frontOn) flashFront(LET_d, fOn);
    if (pOn != projOn) flashFront(LET_P, pOn);
    if (cfg.projUpsideDown != upside) { const uint8_t m[4] = {LET_F, LET_L, LET_I, LET_P}; showFront(m, 1500); }
  }
  first = false;
  count = cfg.alarmCount; bits = nb; frontOn = fOn; projOn = pOn; upside = cfg.projUpsideDown;
}

// Alarm button i: switch alarm i on or off. While an alarm rings, either button stops it (it stays on
// for next time). Feedback: on = the alarm's time on the front display and the light on for 3 s;
// off = "OFF" and two quick blinks.
void alarmButton(int i) {
  if (ringState != RS_IDLE) { dismiss(); ledFeedback(i, LS_DARK); return; }
  if (i >= cfg.alarmCount) {           // no alarm set up for this button yet
    const uint8_t m[4] = {LET_n, LET_o, LET_n, LET_E};
    showFront(m, 2000);
    ledFeedback(i, LS_OFF);
    return;
  }
  AlarmTime& t = cfg.alarms[i].t;
  t.enabled = !t.enabled;
  t.skipNext = false;
  saveConfig();   // announceChanges() shows "1 on" and the time, or "1 oF", and drives the light
}

// Snooze button while nothing rings: light the buttons of the alarms that are on, for a quick check
void showAlarmStatus() {
  uint8_t m[4] = {LET_A, LET_L, LET_DASH, LET_DASH};
  for (int i = 0; i < 2; i++) if (i < cfg.alarmCount && cfg.alarms[i].t.enabled) { ledFeedback(i, LS_SHOW); m[2 + i] = seg::DIGIT[i + 1]; }
  showFront(m, 2500);
}

void toggleFront() {
  if (cfg.front.mode != DM_OFF) { prevFrontMode = cfg.front.mode; cfg.front.mode = DM_OFF; }
  else cfg.front.mode = prevFrontMode;
  saveConfig();
}
void toggleProjector() {
  if (cfg.proj.mode != DM_OFF) { prevProjMode = cfg.proj.mode; cfg.proj.mode = DM_OFF; }
  else cfg.proj.mode = prevProjMode;
  saveConfig();
}

// returns 0 = nothing, 1 = short press (on release), 2.. = long levels (fired while held)
int pollButton(Button& b, const uint32_t* levels, int nLevels) {
  bool pressed = digitalRead(b.pin) == LOW;
  uint32_t ms = millis();
  if (pressed != b.down && ms - b.lastChange > 30) {
    b.lastChange = ms;
    b.down = pressed;
    if (pressed) { b.t0 = ms; b.longLevel = 0; return 0; }
    return b.longLevel == 0 ? 1 : 0;
  }
  if (b.down && b.longLevel < nLevels && ms - b.t0 >= levels[b.longLevel]) {
    b.longLevel++;
    return 1 + b.longLevel;
  }
  return 0;
}

// ---------------------------------------------------------------- setting an alarm's time from the clock
// Hold an alarm button 2 s: "SEt1", then the alarm's time (24-hour form) with the hours blinking. Snooze (top)
// adds one, the side button takes one away; holding either repeats. A tap on the alarm button moves to the
// minutes; the next tap saves, switches the alarm on, and shows "1 on" and the time. 30 s without a press
// leaves it unchanged ("CAnC"). An alarm that starts ringing ends setting without saving.
const uint8_t LET_C = SEG_A | SEG_D | SEG_E | SEG_F;
void startSetting(int i) {
  if (i >= cfg.alarmCount) { const uint8_t m[4] = {LET_n, LET_o, LET_n, LET_E}; showFront(m, 2000); ledFeedback(i, LS_OFF); return; }
  setAlarm = i; setField = 0;
  setH = cfg.alarms[i].t.hour; setM = cfg.alarms[i].t.minute;
  setLastMs = millis(); setStepMs = 0;
  btnA.longLevel = btnB.longLevel = 1;   // a press already under way doesn't count
  const uint8_t m[4] = {LET_S, LET_E, LET_t, seg::DIGIT[(i + 1) % 10]};
  showFront(m, 900);
}
void endSetting(bool save) {
  int i = setAlarm;
  setAlarm = -1;
  if (i < 0) return;
  if (!save) {
    if (ringState == RS_IDLE) { const uint8_t m[4] = {LET_C, LET_A, LET_n, LET_C}; showFront(m, 1500); }
    return;
  }
  AlarmTime& t = cfg.alarms[i].t;
  bool wasOn = t.enabled;
  t.hour = setH; t.minute = setM; t.enabled = true; t.skipNext = false;
  saveConfig();
  if (wasOn) {   // announceChanges() only speaks up when on/off changes: say it here
    const uint8_t m[4] = {seg::DIGIT[(i + 1) % 10], 0, LET_o, LET_n};
    showFront(m, 1200);
    showClockTime(setH, setM, 2000);
    ledFeedback(i, LS_SHOW);
  }
}
void stepSetting(int dir) {
  if (setField == 0) setH = (setH + dir + 24) % 24;
  else setM = (setM + dir + 60) % 60;
  setLastMs = setStepMs = millis();
}
// Snooze and the side button while setting: a step on each press, then repeats while held
void setKey(Button& b, int dir) {
  bool pressed = digitalRead(b.pin) == LOW;
  uint32_t ms = millis();
  if (pressed != b.down && ms - b.lastChange > 30) {
    b.lastChange = ms;
    b.down = pressed;
    b.longLevel = 1;   // so letting go after setting ends isn't taken as a press
    if (pressed) { stepSetting(dir); b.nextRepeat = ms + 600; }
    return;
  }
  if (b.down && (int32_t)(ms - b.nextRepeat) >= 0) { stepSetting(dir); b.nextRepeat = ms + (setField ? 80 : 200); }
}

void handleButtons() {
  static const uint32_t aLevels[] = {2000};
  static const uint32_t bLevels[] = {3000, 10000};
  static const uint32_t alLevels[] = {2000};
  if (setAlarm >= 0) {
    if (ringState != RS_IDLE) { endSetting(false); return; }
    setKey(btnA, +1);
    setKey(btnB, -1);
    for (int i = 0; i < 2; i++) {
      int r = pollButton(btnAl[i], alLevels, 1);
      if (r == 1 && i == setAlarm) {
        setLastMs = millis();
        if (setField == 0) { setField = 1; setStepMs = 0; }
        else endSetting(true);
      }
    }
    if (setAlarm >= 0 && millis() - setLastMs > SET_TIMEOUT_MS) endSetting(false);
    return;
  }
  int a = pollButton(btnA, aLevels, 1);
  if (a == 1) {
    if (ringState == RS_RINGING) snooze();
    else { peekUntilMs = millis() + 15000; showAlarmStatus(); }
  } else if (a == 2) {
    dismiss();
  }
  for (int i = 0; i < 2; i++) {
    int r = pollButton(btnAl[i], alLevels, 1);
    if (r == 1) alarmButton(i);
    else if (r == 2) {   // held 2 s: set its time (or, while an alarm rings, stop it like a tap)
      if (ringState != RS_IDLE) { dismiss(); ledFeedback(i, LS_DARK); }
      else startSetting(i);
      if (setAlarm >= 0) return;
    }
  }
  int b = pollButton(btnB, bLevels, 2);
  if (b == 1) toggleFront();            // announceChanges() shows "d on" / "d oF"
  else if (b == 2) toggleProjector();   // "P on" / "P oF"
  else if (b == 3) {
    Serial.println("Wi-Fi reset");
    const uint8_t m[4] = {LET_r, LET_S, LET_E, LET_t};
    front.setBrightness(4, true);
    front.setSegments(m);
    wm.resetSettings();
    delay(1500);
    ESP.restart();
  }
}

// ---------------------------------------------------------------- web server
// ---------------------------------------------------------------- battery base (optional)
// A MAX17048 fuel gauge (I2C 0x36) reports the charge; the BQ24074 charger runs the clock from USB when it's
// there (load sharing) and from the battery when it isn't. Charging stops at cfg.chargeLimit (battery_logic.h).
// No gauge found: nothing changes (charging left on; the charger stops at full by itself).
const uint8_t GAUGE_ADDR = 0x36;
const uint32_t GAUGE_LOST_MS = 30000;    // gauge silent this long: give up on it and leave charging on
struct Battery {
  bool gauge = false;      // fuel gauge answering
  float pct = 0, volts = 0, rate = 0;   // charge %, cell volts, %/hour (+ charging, - discharging)
  bool external = true;    // USB power present (PGOOD low)
  bool chargeOn = true;    // charging allowed (CE low)
  uint32_t lastOk = 0;
} bat;
bool onBattery() { return bat.gauge && !bat.external; }
bool i2cPresent(uint8_t addr) { Wire.beginTransmission(addr); return Wire.endTransmission() == 0; }
bool gaugeRead(uint8_t reg, uint16_t& v) {
  Wire.beginTransmission(GAUGE_ADDR);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(GAUGE_ADDR, (uint8_t)2) != 2) return false;
  v = (uint16_t)Wire.read() << 8;
  v |= Wire.read();
  return true;
}
const uint8_t LET_b = SEG_C | SEG_D | SEG_E | SEG_F | SEG_G, LET_u = SEG_C | SEG_D | SEG_E, LET_g = 0x6F;
void serviceBattery() {
  static uint32_t last = 0, lastLowMsg = 0;
  uint32_t ms = millis();
  if (ms - last < 2000 && last) return;
  last = ms;
  uint16_t vc, sc, cr;
  if (gaugeRead(0x02, vc) && gaugeRead(0x04, sc) && gaugeRead(0x16, cr)) {
    bat.volts = vc * 78.125e-6f;
    bat.pct = min(100.0f, sc / 256.0f);
    bat.rate = (int16_t)cr * 0.208f;
    bat.gauge = true;
    bat.lastOk = ms;
  } else if (bat.gauge && ms - bat.lastOk > GAUGE_LOST_MS) {
    bat.gauge = false;
    Serial.println("battery gauge lost: charging left on");
  }
  bool ext = !bat.gauge || digitalRead(PIN_PGOOD) == LOW;
  if (bat.gauge && ext != bat.external) {   // say what happened on the front display
    const uint8_t plug[4] = {LET_P, LET_L, LET_u, LET_g}, batt[4] = {LET_b, LET_A, LET_t, LET_t};
    showFront(ext ? plug : batt, 2000);
    Serial.println(ext ? "USB power back" : "running on battery");
  }
  bat.external = ext;
  bat.chargeOn = chargeWanted(bat.pct, cfg.chargeLimit, bat.chargeOn, bat.gauge);
  digitalWrite(PIN_CHG_CE, bat.chargeOn ? LOW : HIGH);
  // Low battery: "bA 9" every 10 minutes below 10 %
  if (onBattery() && bat.pct < 10 && (lastLowMsg == 0 || ms - lastLowMsg > 600000) && ringState == RS_IDLE) {
    lastLowMsg = ms;
    int p = (int)bat.pct;
    const uint8_t m[4] = {LET_b, LET_A, (uint8_t)(p >= 10 ? seg::DIGIT[p / 10] : 0), seg::DIGIT[p % 10]};
    showFront(m, 3000);
  }
}

// The address of the computer making this request, as the clock sees it on the home network
String clientIp() { return server.client().remoteIP().toString(); }
// A computer on the trusted list (Settings > Security) doesn't need the password; everyone else does
bool trustedClient() {
  String ip = clientIp();
  for (int i = 0; i < cfg.trustedCount; i++) if (cfg.trusted[i] == ip) return true;
  return false;
}
bool authed() {
  if (cfg.webPassword.isEmpty() || trustedClient()) return true;
  if (server.authenticate("admin", cfg.webPassword.c_str())) return true;
  server.requestAuthentication();
  return false;
}

void sendJson(JsonDocument& doc, int code = 200) {
  String s;
  serializeJson(doc, s);
  server.send(code, "application/json", s);
}

// The System section of the settings page, asked for every 2 s while it's showing.
void apiSys() {
  if (!authed()) return;
  SysInfo y;
  sysInfoRead(y);
  JsonDocument d;
  d["up"] = y.upSec; d["reset"] = y.reset;
  JsonArray cpu = d["cpu"].to<JsonArray>();
  for (int c = 0; c < 2; c++) { if (y.cpu[c] < 0) cpu.add(nullptr); else cpu.add(y.cpu[c]); }
  d["mhz"] = y.mhz; d["temp"] = round(y.tempC * 10) / 10; d["tasks"] = y.tasks;
  d["heapFree"] = y.heapFree; d["heapTotal"] = y.heapTotal; d["heapMin"] = y.heapMin; d["heapBig"] = y.heapBig;
  d["psFree"] = y.psFree; d["psTotal"] = y.psTotal; d["psMin"] = y.psMin;
  d["fsUsed"] = LittleFS.usedBytes(); d["fsTotal"] = LittleFS.totalBytes();
  d["appUsed"] = y.appUsed; d["appSlot"] = y.appSlot;
  d["rssi"] = WiFi.RSSI();
  String out; serializeJson(d, out);
  server.send(200, "application/json", out);
}

void apiState() {
  if (!authed()) return;
  JsonDocument d;
  time_t now = time(nullptr);
  d["now"] = (long long)now;
  d["timeValid"] = timeValid();
  d["lastSync"] = (long long)lastNtpSync;
  {
    JsonObject b = d["battery"].to<JsonObject>();
    b["present"] = bat.gauge;
    if (bat.gauge) {
      b["pct"] = roundf(bat.pct * 10) / 10; b["volts"] = roundf(bat.volts * 100) / 100; b["rate"] = roundf(bat.rate * 10) / 10;
      b["external"] = bat.external; b["limit"] = cfg.chargeLimit;
      b["state"] = !bat.external ? "battery" : !bat.chargeOn ? "held" : bat.pct >= 99.5f ? "full" : "charging";
      if (!bat.external && bat.rate < -0.05f) b["hoursLeft"] = (int)(bat.pct / -bat.rate);
    }
  }
  d["you"] = clientIp();  d["youTrusted"] = trustedClient();
  d["rtc"] = rtcPresent;
  d["ip"] = WiFi.localIP().toString();
  d["rssi"] = WiFi.RSSI();
  d["ring"] = ringState == RS_RINGING ? "ringing" : ringState == RS_SNOOZED ? "snoozed" : "idle";
  if (ringState != RS_IDLE) d["ringLabel"] = ringCfg.label;
  d["snoozeUntil"] = (long long)snoozeUntil;
  time_t when; int i = nextAlarm(now, when);
  if (i >= 0) { d["nextId"] = i; d["nextAt"] = (long long)when; d["nextLabel"] = cfg.alarms[i].label; }
  d["ldr"] = ldrRaw;
  d["night"] = nightNow;
  int on = 0;
  for (int k = 0; k < cfg.alarmCount; k++) if (cfg.alarms[k].t.enabled) on |= 1 << k;
  d["alarmsOn"] = on;   // so the page notices the alarm buttons
  d["lastStart"] = startedWarm ? "reset" : "power-on";
  d["frontMode"] = cfg.front.mode;  // and the side button
  d["projMode"] = cfg.proj.mode;
  d["frontOn"] = displayVisible(cfg.front);
  d["projOn"] = displayVisible(cfg.proj);
  d["playing"] = soundPlaying();
  d["source"] = ringState == RS_RINGING ? (ringSrc == SRC_STREAM ? "stream" : ringSrc == SRC_BACKUP ? "backup" : "file")
                                        : (streamState != SS_IDLE ? "stream" : "file");
  static const char* ssName[] = {"idle", "connecting", "playing", "failed", "ended"};
  JsonObject st = d["stream"].to<JsonObject>();
  st["state"] = ssName[streamState];
  st["title"] = streamTitle;
  st["note"] = streamNote;
  {   // the newest episode of each alarm's podcast feed, as last looked up
    FeedGuard g(feedMx);
    JsonArray fa = d["feeds"].to<JsonArray>();
    for (auto& e : feedCache) {
      if (e.feed.empty()) continue;
      JsonObject f = fa.add<JsonObject>();
      f["feed"] = e.feed.c_str(); f["ok"] = e.ok; f["title"] = e.title.c_str(); f["url"] = e.url.c_str();
      f["err"] = e.err.c_str(); f["age"] = (millis() - e.atMs) / 1000; f["date"] = (long long)e.date;
    }
  }
  d["fw"] = FW_VERSION;
  d["fwBuild"] = FW_BUILD;
  d["fsUsed"] = LittleFS.usedBytes();
  d["fsTotal"] = LittleFS.totalBytes();
  JsonObject lv = d["live"].to<JsonObject>();
  lv["projOn"] = live.projOn;
  lv["projBright"] = live.projBright;
  JsonArray ts = lv["timeSegs"].to<JsonArray>();
  JsonArray ps = lv["projSegs"].to<JsonArray>();
  for (int i = 0; i < 4; i++) { ts.add(live.timeSegs[i]); ps.add(live.projSegs[i]); }
  lv["frontOn"] = live.frontOn;
  lv["frontBright"] = live.frontBright;
  lv["vol"] = soundPlaying() ? live.vol : 0;
  lv["mirrorX"] = cfg.projMirrorX;
  lv["mirrorY"] = cfg.projMirrorY;
  lv["upsideDown"] = cfg.projUpsideDown;
  JsonArray al = lv["alarmLeds"].to<JsonArray>();
  for (int i = 0; i < 2; i++) al.add(live.alarmLed[i]);
  sendJson(d);
}

void apiGetConfig() {
  if (!authed()) return;
  JsonDocument d;
  configToJson(cfg, d);
  sendJson(d);
}

void apiPostConfig() {
  if (!authed()) return;
  JsonDocument d;
  if (deserializeJson(d, server.arg("plain"))) { server.send(400, "text/plain", "bad JSON"); return; }
  String oldTz = cfg.tz, oldNtp = cfg.ntp;
  // A ringing or snoozed alarm carries on: it rings from its own copy (ringCfg), so saving settings,
  // even editing or deleting that alarm, never silences it. Use Stop for that.
  configFromJson(cfg, d.as<JsonVariantConst>());
  saveConfig();
  if (cfg.tz != oldTz || cfg.ntp != oldNtp) applyTimeConfig();
  projRedraw = true;
  apiGetConfig();
}

void apiSounds() {
  if (!authed()) return;
  JsonDocument d;
  JsonArray arr = d.to<JsonArray>();
  File dir = LittleFS.open("/sounds");
  for (File f = dir.openNextFile(); f; f = dir.openNextFile()) {
    JsonObject o = arr.add<JsonObject>();
    o["path"] = String("/sounds/") + f.name();
    o["size"] = f.size();
  }
  sendJson(d);
}

String safeName(String n) {
  int slash = n.lastIndexOf('/');
  if (slash >= 0) n = n.substring(slash + 1);
  String out;
  for (unsigned i = 0; i < n.length(); i++) {
    char c = n[i];
    if (isalnum((unsigned char)c) || c == '.' || c == '-' || c == '_') out += c;
  }
  if (out.length() > 40) out = out.substring(out.length() - 40);
  String lower = out; lower.toLowerCase();
  const char* ok[] = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus"};
  for (auto e : ok) if (lower.endsWith(e)) return out;
  return "";
}

File uploadFile;
bool uploadOk = false;
void handleSoundUpload() {
  HTTPUpload& up = server.upload();
  if (up.status == UPLOAD_FILE_START) {
    uploadOk = false;
    if (!authed()) return;
    String n = safeName(up.filename);
    if (n.isEmpty()) return;
    uploadFile = LittleFS.open("/sounds/" + n, "w");
    uploadOk = (bool)uploadFile;
  } else if (up.status == UPLOAD_FILE_WRITE) {
    feedWatchdog();
    if (uploadOk && LittleFS.totalBytes() - LittleFS.usedBytes() < up.currentSize + 65536) uploadOk = false;  // keep room for the settings
    if (uploadOk && uploadFile.write(up.buf, up.currentSize) != up.currentSize) uploadOk = false;
  } else if (up.status == UPLOAD_FILE_END || up.status == UPLOAD_FILE_ABORTED) {
    if (uploadFile) {
      String p = String("/sounds/") + uploadFile.name();
      uploadFile.close();
      if (!uploadOk) LittleFS.remove(p);
    }
  }
}

void apiDeleteSound() {
  if (!authed()) return;
  String n = safeName(server.arg("name"));
  if (n.isEmpty() || n == "beep.wav") { server.send(400, "text/plain", "cannot delete"); return; }
  LittleFS.remove("/sounds/" + n);
  server.send(200, "text/plain", "ok");
}

void apiAction() {
  if (!authed()) return;
  String what = server.arg("do");
  int id = server.hasArg("id") ? server.arg("id").toInt() : -1;
  if (what == "snooze") snooze();
  else if (what == "dismiss") dismiss();
  else if (what == "peek") peekUntilMs = millis() + 15000;
  else if (what == "front") toggleFront();
  else if (what == "proj") toggleProjector();
  else if (what == "flip") { cfg.projUpsideDown = !cfg.projUpsideDown; saveConfig(); projRedraw = true; }
  else if (what == "ring" && id >= 0 && id < cfg.alarmCount) startRing(id, cfg.alarms[id].rampSec);
  else if (what == "skip" && id >= 0 && id < cfg.alarmCount) { cfg.alarms[id].t.skipNext = !cfg.alarms[id].t.skipNext; saveConfig(); }
  else if (what == "test") {
    if (ringState == RS_IDLE) {
      uint8_t v = constrain(server.arg("vol").toInt(), 0, 21);
      String st = server.arg("stream");
      if (st.startsWith("http://") || st.startsWith("https://")) audioStream(st, v);
      else audioPlay(server.arg("sound"), v);
      testPlaying = true;
    }
  } else if (what == "stop") { if (ringState == RS_IDLE) audioStop(); testPlaying = false; }
  else if (what == "resync") sntp_restart();
  else { server.send(400, "text/plain", "unknown action"); return; }
  server.send(200, "text/plain", "ok");
}

void setupServer() {
  server.on("/", HTTP_GET, [] { if (authed()) server.send_P(200, "text/html", INDEX_HTML); });
  server.on("/api/state", HTTP_GET, apiState);
  server.on("/api/sys", HTTP_GET, apiSys);
  server.on("/api/audiodiag", HTTP_GET, [] {
    JsonDocument d;
    d["peakRaw"] = peakRaw; d["peakOut"] = peakOut; d["samplesOut"] = samplesOut;
    d["volume"] = audioPlayer ? audioPlayer->getVolume() : -1;
    d["buffered"] = audioPlayer ? audioPlayer->inBufferFilled() : 0;   // bytes waiting to be played
    d["start"] = startNote;
    JsonArray a = d["log"].to<JsonArray>();
    uint8_t n = audioLogN < 8 ? audioLogN : 8;
    for (uint8_t i = 0; i < n; i++) a.add(audioLog[(audioLogN - n + i) % 8]);
    String out; serializeJson(d, out);
    server.send(200, "application/json", out);
  });
  server.on("/api/config", HTTP_GET, apiGetConfig);
  server.on("/api/config", HTTP_POST, apiPostConfig);
  server.on("/api/sounds", HTTP_GET, apiSounds);
  server.on("/api/sounds", HTTP_POST,
            [] { if (authed()) server.send(uploadOk ? 200 : 400, "text/plain", uploadOk ? "ok" : "upload failed (name, type or space)"); },
            handleSoundUpload);
  server.on("/api/sounds/delete", HTTP_POST, apiDeleteSound);
  server.on("/api/action", HTTP_POST, apiAction);
  server.on("/update", HTTP_POST,
            [] {
              if (!authed()) return;
              bool ok = !Update.hasError();
              server.send(ok ? 200 : 500, "text/plain", ok ? "Updated, rebooting" : "Update failed");
              if (ok) { delay(500); ESP.restart(); }
            },
            [] {
              HTTPUpload& up = server.upload();
              if (up.status == UPLOAD_FILE_START) {
                if (!cfg.webPassword.isEmpty() && !trustedClient() && !server.authenticate("admin", cfg.webPassword.c_str())) return;
                Update.begin(UPDATE_SIZE_UNKNOWN);
              } else if (up.status == UPLOAD_FILE_WRITE) {
    feedWatchdog();
                if (Update.isRunning()) Update.write(up.buf, up.currentSize);
              } else if (up.status == UPLOAD_FILE_END) {
                if (Update.isRunning()) Update.end(true);
              }
            });
  server.onNotFound([] { server.send(404, "text/plain", "not found"); });
  server.begin();
  MDNS.begin(HOSTNAME);
  MDNS.addService("http", "tcp", 80);
  serverStarted = true;
  Serial.printf("Web UI: http://%s.local/  (%s)\n", HOSTNAME, WiFi.localIP().toString().c_str());
}

// ---------------------------------------------------------------- setup / loop
void setup() {
  Serial.begin(115200);
  pinMode(PIN_BTN_A, INPUT_PULLUP);
  pinMode(PIN_BTN_B, INPUT_PULLUP);
  pinMode(PIN_BTN_AL1, INPUT_PULLUP);
  pinMode(PIN_BTN_AL2, INPUT_PULLUP);
  for (int i = 0; i < 2; i++) { ledcAttach(LED_PIN[i], 5000, 10); ledcWrite(LED_PIN[i], 0); }
  analogReadResolution(12);

  front.setBrightness(2, true);
  front.clear();
  proj.setBrightness(2, true);
  proj.clear();

  // The partition is labelled "littlefs" in partitions.csv; LittleFS.begin() looks for "spiffs" unless told.
  if (!LittleFS.begin(true, "/littlefs", 10, "littlefs")) Serial.println("LittleFS mount failed");
  loadConfig();
  ensureDefaultSound();
  bool warm = persistLoad();   // survived a crash or restart: the time, alarm checks and a ringing alarm
  startedWarm = warm;
  Serial.printf("Start (%s)\n", warm ? "after a reset: resuming" : "power-on");

  // Seed the clock from the DS3231 so alarms work even without Wi-Fi.
  // The DS3231 and the battery gauge share one I2C bus: pins 1 and 2, or on one breadboard the front-edge
  // pins (pins.h). Use whichever pair something answers on.
  Wire.begin(PIN_SDA, PIN_SCL);
  if (!i2cPresent(0x68) && !i2cPresent(GAUGE_ADDR)) {
    Wire.end();
    Wire.begin(PIN_SDA_ALT, PIN_SCL_ALT);
    if (i2cPresent(0x68) || i2cPresent(GAUGE_ADDR)) Serial.printf("I2C on pins %d and %d\n", PIN_SDA_ALT, PIN_SCL_ALT);
  }
  rtcPresent = rtc.begin(&Wire);
  pinMode(PIN_CHG_CE, OUTPUT);
  digitalWrite(PIN_CHG_CE, LOW);   // charging on until the gauge says otherwise
  pinMode(PIN_PGOOD, INPUT_PULLUP);
  serviceBattery();
  if (bat.gauge) Serial.printf("battery %.0f%% %.2f V\n", bat.pct, bat.volts);
  setenv("TZ", cfg.tz.c_str(), 1);
  tzset();
  if (rtcPresent && !rtc.lostPower()) {
    struct timeval tv = {(time_t)rtc.now().unixtime(), 0};  // RTC holds UTC
    settimeofday(&tv, nullptr);
    Serial.println("Time loaded from RTC");
  }
  // No backup clock (or it lost power) and this is a reset, not a power cut: carry on from the time kept in
  // RTC memory, so an alarm isn't lost just because the clock restarted while the internet was down.
  if (!timeValid() && warm && persist.clock > 1700000000) {
    struct timeval tv = {persist.clock + 2, 0};
    settimeofday(&tv, nullptr);
    Serial.println("Time carried over from before the reset");
  }
  if (warm) lastCheck = persist.lastCheck;

  audioQ = xQueueCreate(8, sizeof(AudioCmd));
  xTaskCreatePinnedToCore(audioTask, "audio", 8192, nullptr, 3, nullptr, 0);
  feedQ = xQueueCreate(6, sizeof(FeedReq));
  xTaskCreatePinnedToCore(feedTask, "feeds", 12288, nullptr, 1, nullptr, 1);

  WiFi.setHostname(HOSTNAME);
  wm.setConfigPortalBlocking(false);
  wm.setHostname(HOSTNAME);
  // With Wi-Fi already set up, a failed connection (the router is still starting after a power cut) only
  // opens the setup portal for 3 minutes; then the clock keeps retrying the saved network (see loop()).
  if (wm.getWiFiIsSaved()) wm.setConfigPortalTimeout(180);
  if (wm.autoConnect("CeilingClock-Setup")) Serial.println("Wi-Fi connected");
  else Serial.println("Wi-Fi setup portal: join 'CeilingClock-Setup'");
  applyTimeConfig();

  // An alarm was ringing or snoozed when the clock reset: carry on with it.
  if (warm && persist.ringState == RS_RINGING) {
    ringAlarm = persist.ringAlarm;
    startRing(ringAlarm, 0, persist.useBeep);
    if (persist.ringStart > 1700000000) ringStart = persist.ringStart;   // keep its stop-after time
    Serial.println("Alarm resumed after the reset");
  } else if (warm && persist.ringState == RS_SNOOZED) {
    ringAlarm = persist.ringAlarm;
    if (ringAlarm >= 0 && ringAlarm < cfg.alarmCount) ringCfg = cfg.alarms[ringAlarm];
    ringState = RS_SNOOZED;
    snoozeUntil = persist.snoozeUntil;
  } else {
    persist.restarts = 0;
    persist.useBeep = 0;
  }

  // If the loop ever hangs, the watchdog resets the clock; an alarm then carries on (above).
  esp_task_wdt_config_t wdt = {.timeout_ms = 30000, .idle_core_mask = 0, .trigger_panic = true};
  if (esp_task_wdt_reconfigure(&wdt) != ESP_OK) esp_task_wdt_init(&wdt);
  esp_task_wdt_add(NULL);
}

// Keeps the state that must survive a reset up to date (see persist.h).
void keepPersist(time_t now) {
  if (timeValid()) persist.clock = now;
  persist.lastCheck = lastCheck;
  persist.ringState = ringState;
  persist.ringAlarm = ringAlarm;
  persist.ringStart = ringStart;
  persist.snoozeUntil = snoozeUntil;
  if (ringState != RS_IDLE) persist.useBeep = ringSrc == SRC_BEEP;
  persistSave();
}

void loop() {
  esp_task_wdt_reset();
  wm.process();
  // Not connected and the setup portal has closed: retry the saved network every 30 s.
  static uint32_t lastWifiTry = 0;
  if (WiFi.status() != WL_CONNECTED && !wm.getConfigPortalActive() && wm.getWiFiIsSaved() && millis() - lastWifiTry > 30000) {
    lastWifiTry = millis();
    WiFi.mode(WIFI_STA);
    WiFi.begin();
  }
  // Wait for the setup portal (also on port 80) to close before starting our server.
  if (!serverStarted && WiFi.status() == WL_CONNECTED && !(WiFi.getMode() & WIFI_AP)) setupServer();
  if (serverStarted) server.handleClient();

  if (ntpJustSynced) {
    ntpJustSynced = false;
    if (rtcPresent) rtc.adjust(DateTime((uint32_t)time(nullptr)));
    Serial.println("NTP synced");
  }

  handleButtons();

  time_t now = time(nullptr);
  checkAlarms(now);
  serviceRing(now);
  keepPersist(now);
  if (testPlaying && !soundPlaying() && streamState != SS_CONNECTING) testPlaying = false;

  serviceBattery();
  {
    bool busy = ringState == RS_RINGING || soundPlaying() || streamState == SS_CONNECTING;
    audioBusy = busy;
    scheduleFeedLookups(busy);
    // Wi-Fi power saving delays packets; with a weak signal that starves a stream. Keep the radio fully awake
    // while sound plays, and let it save power (the battery) the rest of the time.
    static int8_t sleepOn = -1;
    if (WiFi.status() == WL_CONNECTED && sleepOn != (busy ? 0 : 1)) { sleepOn = busy ? 0 : 1; WiFi.setSleep(!busy); }
  }
  announceChanges();
  renderAlarmLeds(nightNow);  // every pass: the blinks are faster than a frame
  static uint32_t lastFrame = 0;
  if (millis() - lastFrame >= 250) {
    lastFrame = millis();
    ldrRaw = (ldrRaw * 3 + analogRead(PIN_LDR)) / 4;
    struct tm lt;
    localtime_r(&now, &lt);
    nightNow = computeNight(lt);

    bool dim = nightNow || onBattery();   // on battery both displays use their night brightness, to save power
    uint8_t projB = dim ? cfg.proj.nightBright : cfg.proj.dayBright;
    if (projB < 4 && (millis() < peekUntilMs || ringState != RS_IDLE)) projB = 4;  // easy to see while peeking or ringing
    renderProj(lt, displayVisible(cfg.proj), projB);
    renderFront(lt, displayVisible(cfg.front), dim ? cfg.front.nightBright : cfg.front.dayBright);
  }
  delay(2);
}
