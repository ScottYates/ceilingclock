// Ceiling projection alarm clock
// ESP32-S3 + Nokia 5110 LCD projector + TM1637 front display + MAX98357A audio
// + WS2812B sunrise ring + DS3231 RTC. Time from NTP, kept by the RTC when offline.
#include <Arduino.h>
#include <WiFi.h>
#include <WiFiManager.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <LittleFS.h>
#include <Update.h>
#include <Wire.h>
#include <RTClib.h>
#include <TM1637Display.h>
#include <Adafruit_GFX.h>
#include <Adafruit_PCD8544.h>
#include <Adafruit_NeoPixel.h>
#include <ArduinoJson.h>
#include <esp_sntp.h>
#include <sys/time.h>
#include "Audio.h"

#include "pins.h"
#include "settings.h"
#include "alarm_logic.h"
#include "web_ui.h"
#include "feed_scan.h"
#include "net_fetch.h"

#define FW_VERSION "1.0.0"
#define HOSTNAME "ceilingclock"

// What every output is doing right now, reported to the web page's live view.
struct LiveState {
  bool projOn = false;  uint8_t projPct = 0;
  bool frontOn = false; uint8_t frontBright = 0;
  uint8_t ring[3] = {0, 0, 0}; float sunrise = 0;
  uint8_t vol = 0;
} live;

// ---------------------------------------------------------------- hardware
Adafruit_PCD8544 lcd(PIN_LCD_CLK, PIN_LCD_DIN, PIN_LCD_DC, PIN_LCD_CE, PIN_LCD_RST);
GFXcanvas1 canvas(84, 48);
TM1637Display front(PIN_TM_CLK, PIN_TM_DIO);
Adafruit_NeoPixel ring(RING_COUNT, PIN_RING, NEO_GRB + NEO_KHZ800);
RTC_DS3231 rtc;
bool rtcPresent = false;

WebServer server(80);
WiFiManager wm;
bool serverStarted = false;

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

// Podcast feed URL -> the newest episode's audio URL (and its title). Radio streams and
// links to audio files come back unchanged. False if it can't be reached or has no episodes.
bool resolveStream(const char* url, std::string& out, std::string& title, std::string& err) {
  out = url;
  if (urlLooksLikeAudio(url)) return true;
  FeedScan scan;
  bool sniffed = false, isAudio = false;
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
    scan.feed(p, n);
    total += n;
    return !scan.done() && total < 512 * 1024;
  });
  if (!ok) { err = "could not reach the URL"; return false; }
  if (isAudio || !sniffed) return true;
  if (!scan.found()) { err = "no episodes found in the feed"; return false; }
  out = scan.url();
  title = scan.title();
  return true;
}

void audioInit() {
  audioPlayer = new Audio();
  audioPlayer->setPinout(PIN_I2S_BCLK, PIN_I2S_LRC, PIN_I2S_DOUT);
  audioPlayer->setVolume(0);
  Audio::audio_info_callback = [](Audio::msg_t m) {
    if (!m.msg || !*m.msg) return;
    if (m.e == Audio::evt_streamtitle || (m.e == Audio::evt_name && !streamTitle[0])) strlcpy(streamTitle, m.msg, sizeof streamTitle);
  };
}

// Handles queued commands and feeds the decoder; called continuously by the audio task.
void audioStep() {
  AudioCmd c;
  while (xQueueReceive(audioQ, &c, 0) == pdTRUE) {
    if (c.type == AC_PLAY) {
      audioPlayer->stopSong();
      audioPlayer->setVolume(c.vol);
      audioPlayer->connecttoFS(LittleFS, c.path);
    } else if (c.type == AC_STREAM) {
      audioPlayer->stopSong();
      audioPlayer->setVolume(c.vol);
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
  xQueueSend(audioQ, &c, 0);
  audioRunning = true;  // assume started until the task reports otherwise
  live.vol = vol;
}
void audioStream(const String& url, uint8_t vol) {
  AudioCmd c{AC_STREAM, vol, {0}};
  strlcpy(c.path, url.c_str(), sizeof(c.path));
  streamState = SS_CONNECTING;
  streamTitle[0] = streamNote[0] = 0;
  xQueueSend(audioQ, &c, 0);
  live.vol = vol;
}
void audioStop() { AudioCmd c{AC_STOP, 0, {0}}; streamState = SS_IDLE; xQueueSend(audioQ, &c, 0); }
void audioVolume(uint8_t v) { AudioCmd c{AC_VOL, v, {0}}; xQueueSend(audioQ, &c, 0); live.vol = v; }
bool soundPlaying() { return audioRunning || streamState == SS_PLAYING; }

// Writes a short beep-beep WAV so there is always a sound, even before you upload any.
void ensureDefaultSound() {
  LittleFS.mkdir("/sounds");
  if (LittleFS.exists("/sounds/beep.wav")) return;
  const uint32_t rate = 16000, samples = rate * 14 / 10;  // 1.4 s
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
time_t lastFired[MAX_ALARMS] = {0};
time_t lastCheck = 0;
bool testPlaying = false;
// what the ringing alarm is playing: its sound file, its stream, or the sound file as a backup for a failed stream
enum RingSrc : uint8_t { SRC_FILE, SRC_STREAM, SRC_BACKUP };
RingSrc ringSrc = SRC_FILE;
uint8_t streamTries = 0;
const uint32_t STREAM_CONNECT_MS = 25000;  // give up on a stream that hasn't started by then

void ringSound(const AlarmCfg& a, uint8_t vol) {
  if (a.stream.length() && ringSrc != SRC_BACKUP) { ringSrc = SRC_STREAM; audioStream(a.stream, vol); }
  else { if (!a.stream.length()) ringSrc = SRC_FILE; audioPlay(a.sound, vol); }
  lastPlayMs = millis();
}

uint32_t peekUntilMs = 0;  // button A "show me the time" while displays are off

uint8_t prevFrontMode = DM_ON, prevProjMode = DM_ON;

void startRing(int i, uint32_t rampSec) {
  if (i < 0 || i >= cfg.alarmCount) return;
  ringAlarm = i;
  ringState = RS_RINGING;
  ringStart = time(nullptr);
  ringRampSec = rampSec;
  lastSentVol = rampVolume(cfg.alarms[i].volume, 0, rampSec);
  ringSrc = SRC_FILE;
  streamTries = 1;
  ringSound(cfg.alarms[i], lastSentVol);
  testPlaying = false;
  Serial.printf("Alarm %d (%s) ringing\n", i, cfg.alarms[i].label.c_str());
}

void snooze() {
  if (ringState != RS_RINGING) return;
  audioStop();
  ringState = RS_SNOOZED;
  snoozeUntil = time(nullptr) + cfg.alarms[ringAlarm].snoozeMin * 60;
}

void dismiss() {
  if (ringState == RS_IDLE) return;
  audioStop();
  ringState = RS_IDLE;
  ringAlarm = -1;
}

void checkAlarms(time_t now) {
  if (!timeValid()) { lastCheck = 0; return; }
  if (lastCheck == 0 || now < lastCheck || now - lastCheck > 300) { lastCheck = now; return; }  // clock jumped
  if (now == lastCheck) return;
  bool changed = false;
  for (int i = 0; i < cfg.alarmCount; i++) {
    AlarmCfg& a = cfg.alarms[i];
    if (!alarmDueBetween(a.t, lastCheck, now)) continue;
    if (lastFired[i] && now - lastFired[i] < 23 * 3600) continue;  // DST fall-back repeat
    lastFired[i] = now;
    bool skip = a.t.skipNext;
    if (a.t.skipNext) { a.t.skipNext = false; changed = true; }
    if (a.t.days == 0) { a.t.enabled = false; changed = true; }  // one-time alarm
    if (!skip) startRing(i, a.rampSec);
  }
  lastCheck = now;
  if (changed) saveConfig();
}

void serviceRing(time_t now) {
  if (ringState == RS_RINGING) {
    const AlarmCfg& a = cfg.alarms[ringAlarm];
    uint32_t el = now - ringStart;
    uint8_t v = rampVolume(a.volume, el, ringRampSec);
    if (v != lastSentVol) { audioVolume(v); lastSentVol = v; }
    if (ringSrc == SRC_STREAM) {
      bool slow = streamState == SS_CONNECTING && millis() - lastPlayMs > STREAM_CONNECT_MS;
      if (streamState == SS_ENDED && streamTries < 3 && millis() - lastPlayMs > 60000) {
        streamTries++;  // it played for a while and dropped: reconnect
        ringSound(a, v);
      } else if (slow || streamState == SS_FAILED || streamState == SS_ENDED) {
        Serial.printf("Stream didn't play (%s); ringing with the backup sound\n", slow ? "too slow to start" : streamNote);
        ringSrc = SRC_BACKUP;  // so the alarm still wakes you
        ringSound(a, v);
      }
    } else if (!audioRunning && millis() - lastPlayMs > 1500) {  // loop the sound file
      ringSound(a, v);
    }
    if (el > (uint32_t)a.maxRingMin * 60) dismiss();
  } else if (ringState == RS_SNOOZED && now >= snoozeUntil) {
    startRing(ringAlarm, 10);
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

// ---------------------------------------------------------------- projector rendering
static const uint8_t SEG[10] = {0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07, 0x7F, 0x6F};

void drawDigit(int x, int y, int d, int w = 16, int h = 32, int t = 4) {
  if (d < 0) return;
  uint8_t s = (d == 10) ? 0x40 : SEG[d];  // 10 = dash
  int hh = h / 2;
  if (s & 0x01) canvas.fillRect(x + 1, y, w - 2, t, 1);                 // a
  if (s & 0x02) canvas.fillRect(x + w - t, y + 1, t, hh - 1, 1);        // b
  if (s & 0x04) canvas.fillRect(x + w - t, y + hh, t, hh - 1, 1);       // c
  if (s & 0x08) canvas.fillRect(x + 1, y + h - t, w - 2, t, 1);         // d
  if (s & 0x10) canvas.fillRect(x, y + hh, t, hh - 1, 1);               // e
  if (s & 0x20) canvas.fillRect(x, y + 1, t, hh - 1, 1);                // f
  if (s & 0x40) canvas.fillRect(x + 1, y + hh - t / 2, w - 2, t, 1);    // g
}

String fmtTime(int h, int m) {
  char b[12];
  if (cfg.hour24) snprintf(b, sizeof b, "%02d:%02d", h, m);
  else snprintf(b, sizeof b, "%d:%02d%s", (h % 12) ? h % 12 : 12, m, h < 12 ? "a" : "p");
  return b;
}

String statusLine(const struct tm& lt, time_t now) {
  if (WiFi.getMode() & WIFI_AP) return "WIFI SETUP";
  if (!timeValid()) return "NO TIME YET";
  if (ringState == RS_RINGING) return "GOOD MORNING";
  if (ringState == RS_SNOOZED) {
    struct tm s; localtime_r(&snoozeUntil, &s);
    return "SNOOZE " + fmtTime(s.tm_hour, s.tm_min);
  }
  String out;
  time_t when; int i = nextAlarm(now, when);
  if (i >= 0 && when - now < 24 * 3600) {
    struct tm a; localtime_r(&when, &a);
    out = "AL " + fmtTime(a.tm_hour, a.tm_min);
  }
  if (!cfg.hour24) {
    while (out.length() < 12) out += ' ';
    out += lt.tm_hour < 12 ? "AM" : "PM";
  }
  return out;
}

// Draws the clock face into the 84 x 48 canvas (also used by the web page's live view).
void composeCanvas(const struct tm& lt, time_t now) {
  canvas.fillScreen(0);
  if (timeValid()) {
    int h = lt.tm_hour;
    if (!cfg.hour24) { h %= 12; if (h == 0) h = 12; }
    drawDigit(0, 2, (cfg.hour24 || h >= 10) ? h / 10 : -1);
    drawDigit(19, 2, h % 10);
    canvas.fillRect(39, 10, 4, 4, 1);
    canvas.fillRect(39, 22, 4, 4, 1);
    drawDigit(46, 2, lt.tm_min / 10);
    drawDigit(65, 2, lt.tm_min % 10);
  } else {
    for (int i = 0; i < 4; i++) drawDigit(i < 2 ? i * 19 : 46 + (i - 2) * 19, 2, 10);
  }
  canvas.setTextSize(1);
  canvas.setTextColor(1);
  canvas.setCursor(0, 40);
  canvas.print(statusLine(lt, now));
}

// Copies the canvas to the LCD with mirroring.
void pushLcd() {
  // Copy to the LCD with mirroring. On the LCD a "set" pixel is dark and blocks light.
  lcd.clearDisplay();
  for (int y = 0; y < 48; y++)
    for (int x = 0; x < 84; x++) {
      bool lit = canvas.getPixel(x, y);
      bool dark = cfg.projInvert ? !lit : lit;
      if (dark) lcd.drawPixel(cfg.projMirrorX ? 83 - x : x, cfg.projMirrorY ? 47 - y : y, BLACK);
    }
  lcd.display();
}

void setProjectorLed(uint8_t pct) {
  live.projPct = pct;
  uint32_t duty = (uint32_t)pct * pct * 1023 / 10000;  // rough perceptual curve
  ledcWrite(PIN_PROJ_LED, duty);
}

// ---------------------------------------------------------------- front display
void renderFront(const struct tm& lt, bool visible, uint8_t bright) {
  live.frontOn = visible;
  live.frontBright = bright;
  static int lastKey = -2;
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

// ---------------------------------------------------------------- sunrise ring
void renderRing(time_t now) {
  float p = 0;
  if (ringState != RS_IDLE && ringAlarm >= 0 && cfg.alarms[ringAlarm].sunriseMin > 0) {
    p = 1;
  } else if (ringState == RS_IDLE && timeValid()) {
    for (int i = 0; i < cfg.alarmCount; i++) {
      const AlarmCfg& a = cfg.alarms[i];
      if (!a.sunriseMin) continue;
      time_t t = alarmNext(a.t, now, true);
      if (!t) continue;
      long lead = (long)a.sunriseMin * 60;
      long left = (long)(t - now);
      if (left <= lead) p = max(p, 1.0f - (float)left / lead);
    }
  }
  static int lastLevel = -1;
  int level = (int)(p * 255);
  live.sunrise = p;
  if (level == lastLevel) return;
  lastLevel = level;
  // deep red -> orange -> warm white, with a squared curve so it starts very dim
  float b = p * p * cfg.sunriseMaxBright / 255.0f;
  uint8_t r = 255 * b;
  uint8_t g = (p < 0.3f ? p / 0.3f * 40 : 40 + (p - 0.3f) / 0.7f * 140) * b;
  uint8_t bl = (p < 0.6f ? 0 : (p - 0.6f) / 0.4f * 70) * b;
  live.ring[0] = r; live.ring[1] = g; live.ring[2] = bl;
  for (int i = 0; i < RING_COUNT; i++) ring.setPixelColor(i, r, g, bl);
  ring.show();
}

// ---------------------------------------------------------------- buttons
struct Button {
  uint8_t pin; bool down = false; uint32_t t0 = 0, lastChange = 0; uint8_t longLevel = 0;
  explicit Button(uint8_t p) : pin(p) {}
};
Button btnA(PIN_BTN_A), btnB(PIN_BTN_B);

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

void handleButtons() {
  static const uint32_t aLevels[] = {2000};
  static const uint32_t bLevels[] = {3000, 10000};
  int a = pollButton(btnA, aLevels, 1);
  if (a == 1) {
    if (ringState == RS_RINGING) snooze();
    else peekUntilMs = millis() + 15000;
  } else if (a == 2) {
    dismiss();
  }
  int b = pollButton(btnB, bLevels, 2);
  if (b == 1) toggleFront();
  else if (b == 2) toggleProjector();
  else if (b == 3) {
    Serial.println("Wi-Fi reset");
    wm.resetSettings();
    delay(200);
    ESP.restart();
  }
}

// ---------------------------------------------------------------- web server
bool authed() {
  if (cfg.webPassword.isEmpty()) return true;
  if (server.authenticate("admin", cfg.webPassword.c_str())) return true;
  server.requestAuthentication();
  return false;
}

void sendJson(JsonDocument& doc, int code = 200) {
  String s;
  serializeJson(doc, s);
  server.send(code, "application/json", s);
}

void apiState() {
  if (!authed()) return;
  JsonDocument d;
  time_t now = time(nullptr);
  d["now"] = (long long)now;
  d["timeValid"] = timeValid();
  d["lastSync"] = (long long)lastNtpSync;
  d["rtc"] = rtcPresent;
  d["ip"] = WiFi.localIP().toString();
  d["rssi"] = WiFi.RSSI();
  d["ring"] = ringState == RS_RINGING ? "ringing" : ringState == RS_SNOOZED ? "snoozed" : "idle";
  if (ringAlarm >= 0) d["ringLabel"] = cfg.alarms[ringAlarm].label;
  d["snoozeUntil"] = (long long)snoozeUntil;
  time_t when; int i = nextAlarm(now, when);
  if (i >= 0) { d["nextId"] = i; d["nextAt"] = (long long)when; d["nextLabel"] = cfg.alarms[i].label; }
  d["ldr"] = ldrRaw;
  d["night"] = nightNow;
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
  d["fw"] = FW_VERSION;
  d["fsUsed"] = LittleFS.usedBytes();
  d["fsTotal"] = LittleFS.totalBytes();
  JsonObject lv = d["live"].to<JsonObject>();
  lv["projOn"] = live.projOn;
  lv["projPct"] = live.projPct;
  lv["frontOn"] = live.frontOn;
  lv["frontBright"] = live.frontBright;
  JsonArray rgb = lv["ring"].to<JsonArray>();
  for (int i = 0; i < 3; i++) rgb.add(live.ring[i]);
  lv["sunrise"] = live.sunrise;
  lv["vol"] = soundPlaying() ? live.vol : 0;
  lv["invert"] = cfg.projInvert;
  // the 84 x 48 projector image, 1 bit per pixel, 11 bytes per row, as hex
  static const char* hx = "0123456789abcdef";
  const uint8_t* buf = canvas.getBuffer();
  String lcd;
  lcd.reserve(84 / 8 * 48 * 2 + 100);
  for (int i = 0; i < 11 * 48; i++) { lcd += hx[buf[i] >> 4]; lcd += hx[buf[i] & 15]; }
  lv["lcd"] = lcd;
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
  if (ringState != RS_IDLE) dismiss();  // alarm indices may change
  configFromJson(cfg, d.as<JsonVariantConst>());
  for (auto& t : lastFired) t = 0;
  saveConfig();
  if (cfg.tz != oldTz || cfg.ntp != oldNtp) applyTimeConfig();
  lcd.setContrast(cfg.lcdContrast);
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
    if (uploadOk && LittleFS.totalBytes() - LittleFS.usedBytes() < up.currentSize + 16384) uploadOk = false;
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
                if (!cfg.webPassword.isEmpty() && !server.authenticate("admin", cfg.webPassword.c_str())) return;
                Update.begin(UPDATE_SIZE_UNKNOWN);
              } else if (up.status == UPLOAD_FILE_WRITE) {
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
  analogReadResolution(12);

  ledcAttach(PIN_PROJ_LED, 10000, 10);  // 10 kHz: no visible flicker, well inside the MOSFET module's 0-20 kHz rating
  ledcWrite(PIN_PROJ_LED, 0);

  ring.begin();
  ring.clear();
  ring.show();

  front.setBrightness(2, true);
  front.clear();

  if (!LittleFS.begin(true)) Serial.println("LittleFS mount failed");
  loadConfig();
  ensureDefaultSound();

  lcd.begin(cfg.lcdContrast);
  lcd.clearDisplay();
  lcd.display();

  // Seed the clock from the DS3231 so alarms work even without Wi-Fi.
  Wire.begin(PIN_SDA, PIN_SCL);
  rtcPresent = rtc.begin(&Wire);
  setenv("TZ", cfg.tz.c_str(), 1);
  tzset();
  if (rtcPresent && !rtc.lostPower()) {
    struct timeval tv = {(time_t)rtc.now().unixtime(), 0};  // RTC holds UTC
    settimeofday(&tv, nullptr);
    Serial.println("Time loaded from RTC");
  }

  audioQ = xQueueCreate(8, sizeof(AudioCmd));
#ifdef SIM_NO_THREADS   // browser simulator has no threads: audio work runs from loop() instead
  audioInit();
#else
  xTaskCreatePinnedToCore(audioTask, "audio", 8192, nullptr, 3, nullptr, 0);
#endif

  WiFi.setHostname(HOSTNAME);
  wm.setConfigPortalBlocking(false);
  wm.setHostname(HOSTNAME);
  if (wm.autoConnect("CeilingClock-Setup")) Serial.println("Wi-Fi connected");
  else Serial.println("Wi-Fi setup portal: join 'CeilingClock-Setup'");
  applyTimeConfig();
}

void loop() {
#ifdef SIM_NO_THREADS
  audioStep();
#endif
  wm.process();
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
  if (testPlaying && !soundPlaying() && streamState != SS_CONNECTING) testPlaying = false;

  static uint32_t lastFrame = 0;
  if (millis() - lastFrame >= 250) {
    lastFrame = millis();
    ldrRaw = (ldrRaw * 3 + analogRead(PIN_LDR)) / 4;
    struct tm lt;
    localtime_r(&now, &lt);
    nightNow = computeNight(lt);

    bool projOn = displayVisible(cfg.proj);
    uint8_t projB = nightNow ? cfg.proj.nightBright : cfg.proj.dayBright;
    if (projOn && projB < 15 && (millis() < peekUntilMs || ringState != RS_IDLE)) projB = 15;
    setProjectorLed(projOn ? projB : 0);
    live.projOn = projOn;
    static time_t lastRender = 0;
    if (now != lastRender) {
      composeCanvas(lt, now);
      if (projOn) pushLcd();
      lastRender = now;
    }

    renderFront(lt, displayVisible(cfg.front), nightNow ? cfg.front.nightBright : cfg.front.dayBright);
    renderRing(now);
  }
  delay(2);
}
