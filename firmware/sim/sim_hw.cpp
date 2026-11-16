// PC simulator: implementations of the Arduino / ESP32 stand-ins in shim/.
#include "Arduino.h"
#include "sim_libs.h"
#include "LittleFS.h"
#include "WebServer.h"
#include "Audio.h"
#include "pins.h"

#include <chrono>
#include <deque>
#include <map>
#include <cstdarg>
#include <sys/stat.h>
#ifndef SIM_WASM
#include <mutex>
#include <thread>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <poll.h>
#endif
#if !defined(MSG_NOSIGNAL) && !defined(SIM_WASM)
#define MSG_NOSIGNAL 0   // macOS: SIGPIPE is ignored in main() instead
#endif


SerialClass Serial;
EspClass ESP;
WiFiClass WiFi;
MDNSClass MDNS;
UpdateClass Update;
TwoWire Wire;
fs::FS LittleFS;

namespace sim {
Hw hw;
long timeOffset = 0;
static unsigned long btnUntil[4] = {0, 0, 0, 0};
}

int Print::printf(const char* f, ...) {
  char buf[512];
  va_list ap; va_start(ap, f);
  int n = vsnprintf(buf, sizeof buf, f, ap);
  va_end(ap);
  write((const uint8_t*)buf, strlen(buf));
  return n;
}

// ---------------------------------------------------------------- time
static const auto t0 = std::chrono::steady_clock::now();
unsigned long millis() {
  return (unsigned long)std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - t0).count();
}
#ifdef SIM_WASM
void delay(unsigned long) {}          // the browser calls loop() on a timer instead
#else
void delay(unsigned long ms) { usleep(ms * 1000); }
#endif
// Two clocks: the real time in the simulated world (host clock + /sim/time offset), and the clock's own
// system time, which (in the PC build) starts unknown at power-on like the ESP32's: it reads "uptime since
// 1970" until NTP, the backup clock or the firmware sets it. /sim/clockerror makes it run wrong by N seconds.
static time_t hostTime() { return (time_t)std::chrono::duration_cast<std::chrono::seconds>(std::chrono::system_clock::now().time_since_epoch()).count(); }
uint32_t simRealTime() { return (uint32_t)(hostTime() + sim::timeOffset); }
namespace sim { bool sysValid = false; long sysDelta = 0; }
// The firmware's time() and settimeofday(): these replace the C library's for the whole program.
static time_t sim_time(time_t* t) {
#ifdef SIM_WASM
  time_t v = hostTime() + sim::timeOffset;   // the browser demo always knows the time
#else
  time_t v = sim::sysValid ? (time_t)simRealTime() + sim::sysDelta : (time_t)(millis() / 1000);
#endif
  if (t) *t = v;
  return v;
}
extern "C" time_t time(time_t* t) SIM_NOEXCEPT { return sim_time(t); }
extern "C" int settimeofday(const struct timeval* tv, const struct timezone*) SIM_NOEXCEPT {
#ifndef SIM_WASM
  sim::sysValid = true;
  sim::sysDelta = (long)(tv->tv_sec - (time_t)simRealTime());
#endif
  return 0;
}
static sntp_sync_cb g_sntpCb = nullptr;
static bool g_ntpConfigured = false;
void sntp_set_sync_interval(uint32_t) {}
void sntp_set_time_sync_notification_cb(sntp_sync_cb cb) { g_sntpCb = cb; }
bool sim::wifiLinked() { return hw.wifiConnected && hw.wifiUp; }

// Simulator settings from the environment (PC build): SIM_RTC=1 fits a DS3231; SIM_WIFI=0 starts with the
// router down; SIM_NET=0 with the internet down; SIM_RESET=warm starts as after a crash or restart (the state
// kept in RTC memory survives: see persist.h), anything else as after power-on.
static struct SimEnv {
  SimEnv() {
    auto on = [](const char* k, bool def) { const char* v = getenv(k); return v ? strcmp(v, "0") != 0 : def; };
    sim::hw.rtcPresent = on("SIM_RTC", false);
    sim::hw.wifiUp = on("SIM_WIFI", true);
    sim::hw.netOk = on("SIM_NET", true);
#ifndef SIM_WASM
    // The simulated world's time keeps going across restarts and power cuts (a test can add time spent off).
    FILE* f = fopen(worldPath().c_str(), "r");
    if (f) { long o = 0; if (fscanf(f, "%ld", &o) == 1) sim::timeOffset = o; fclose(f); }
#endif
  }
#ifndef SIM_WASM
  static std::string worldPath() { const char* e = getenv("SIM_FS_DIR"); return std::string(e ? e : "sim_fs") + "/.worldtime"; }
#endif
} g_simEnv;
#ifndef SIM_WASM
static void saveWorldTime() {
  const char* e = getenv("SIM_FS_DIR");
  FILE* f = fopen((std::string(e ? e : "sim_fs") + "/.worldtime").c_str(), "w");
  if (f) { fprintf(f, "%ld\n", sim::timeOffset); fclose(f); }
}
#endif

// ---------------------------------------------------------------- reset reason and RTC memory
// The firmware's RTC_NOINIT_ATTR variable (persist, in main.cpp) is written to sim_fs/.rtcmem when the
// simulated clock resets, with why it reset. A "warm" start (SIM_RESET=warm) reads both back before setup();
// any other start is a power-on, where RTC memory holds whatever the chip powered up with (random bytes).
#include "persist.h"
extern Persist persist;
static esp_reset_reason_t g_resetReason = ESP_RST_POWERON;
esp_reset_reason_t esp_reset_reason() { return g_resetReason; }
#ifndef SIM_WASM
static std::string fsPath(const char* name) { const char* e = getenv("SIM_FS_DIR"); return std::string(e ? e : "sim_fs") + "/" + name; }
#endif
void sim::powerOn() {
  uint8_t* p = (uint8_t*)&persist;
  for (size_t i = 0; i < sizeof persist; i++) p[i] = (uint8_t)rand();
  g_resetReason = ESP_RST_POWERON;
#ifndef SIM_WASM
  const char* r = getenv("SIM_RESET");
  if (!r || strcmp(r, "warm")) return;
  FILE* f = fopen(fsPath(".rtcmem").c_str(), "rb");
  if (!f) return;
  int why = ESP_RST_SW;
  if (fread(&persist, sizeof persist, 1, f) != 1 || fread(&why, sizeof why, 1, f) != 1) why = ESP_RST_SW;
  fclose(f);
  g_resetReason = (esp_reset_reason_t)why;
#endif
}
[[noreturn]] void sim::reset(esp_reset_reason_t why) {
#ifndef SIM_WASM
  FILE* f = fopen(fsPath(".rtcmem").c_str(), "wb");
  if (f) { int w = why; fwrite(&persist, sizeof persist, 1, f); fwrite(&w, sizeof w, 1, f); fclose(f); }
#endif
  fflush(stdout);
  exit(0);
}

// ---------------------------------------------------------------- task watchdog (esp_task_wdt.h)
#include "esp_task_wdt.h"
#ifndef SIM_WASM
#include <atomic>
static std::atomic<unsigned long> g_wdtFed{0};
static std::atomic<uint32_t> g_wdtTimeout{5000};
static std::atomic<bool> g_wdtWatching{false};
#endif
esp_err_t esp_task_wdt_init(const esp_task_wdt_config_t* c) { return esp_task_wdt_reconfigure(c); }
esp_err_t esp_task_wdt_reconfigure(const esp_task_wdt_config_t* c) {
#ifndef SIM_WASM
  g_wdtTimeout = c->timeout_ms;
#endif
  return ESP_OK;
}
esp_err_t esp_task_wdt_reset() {
#ifndef SIM_WASM
  g_wdtFed = millis();
#endif
  return ESP_OK;
}
esp_err_t esp_task_wdt_add(TaskHandle_t) {
#ifndef SIM_WASM
  g_wdtFed = millis();
  if (!g_wdtWatching.exchange(true))
    std::thread([] {
      for (;;) {
        usleep(200000);
        if (millis() - g_wdtFed > g_wdtTimeout) {
          printf("[sim] task watchdog: loop() stuck for %u ms, resetting\n", (unsigned)g_wdtTimeout);
          sim::reset(ESP_RST_TASK_WDT);
        }
      }
    }).detach();
#endif
  return ESP_OK;
}

// NTP: answers with the real time, but only when the clock is on Wi-Fi and the internet is up
static void fakeSync() {
  if (!g_ntpConfigured || !sim::wifiLinked() || !sim::hw.netOk) return;
#ifndef SIM_WASM
  sim::sysValid = true; sim::sysDelta = 0;
#endif
  if (!g_sntpCb) return;
  struct timeval tv = {sim_time(nullptr), 0};
  g_sntpCb(&tv);
}
// SNTP keeps trying in the background until it gets an answer (and the real one resyncs hourly)
void sim::tick() {
  static unsigned long last = 0;
  if (millis() - last < 2000) return;
  last = millis();
  // SIM_WIFI_UP_AFTER=N: the router comes up N seconds after the clock starts (a slow router after a power cut)
  static const char* upAfter = getenv("SIM_WIFI_UP_AFTER");
  if (upAfter && !hw.wifiUp && millis() >= (unsigned long)atol(upAfter) * 1000) hw.wifiUp = true;
  if (!sysValid) fakeSync();
}
bool sntp_restart() { fakeSync(); return true; }
void configTzTime(const char* tz, const char*, const char*, const char*) {
  g_ntpConfigured = true;
  setenv("TZ", tz, 1);
  tzset();
  fakeSync();   // the simulator's "NTP server" answers immediately with the host clock
}
void EspClass::restart() { printf("ESP.restart()\n"); sim::reset(ESP_RST_SW); }

// ---------------------------------------------------------------- GPIO
void pinMode(int, int) {}
int digitalRead(int pin) {
  int i = pin == PIN_BTN_A ? 0 : pin == PIN_BTN_B ? 1 : pin == PIN_BTN_AL1 ? 2 : pin == PIN_BTN_AL2 ? 3 : -1;
  if (i < 0) return HIGH;
  bool down = millis() < sim::btnUntil[i];
  sim::hw.btnDown[i] = down;
  return down ? LOW : HIGH;
}
int analogRead(int) { return sim::hw.ldr; }
void analogReadResolution(int) {}
bool ledcAttach(int, int, int) { return true; }
void ledcWrite(int pin, uint32_t duty) {
  if (pin == PIN_LED_AL1) sim::hw.alarmLed[0] = duty;
  if (pin == PIN_LED_AL2) sim::hw.alarmLed[1] = duty;
}

// ---------------------------------------------------------------- FreeRTOS
#ifdef SIM_WASM
struct NoLock { void lock() {} void unlock() {} };   // single-threaded in the browser
#define SIM_LOCK(q)
struct SimQueue { std::deque<std::vector<uint8_t>> q; size_t item; int cap; };
#else
#define SIM_LOCK(q) std::lock_guard<std::mutex> l((q)->m)
struct SimQueue { std::mutex m; std::deque<std::vector<uint8_t>> q; size_t item; int cap; };
#endif
QueueHandle_t xQueueCreate(int len, size_t itemSize) { auto* q = new SimQueue; q->item = itemSize; q->cap = len; return q; }
BaseType_t xQueueSend(QueueHandle_t h, const void* item, int) {
  auto* q = (SimQueue*)h; SIM_LOCK(q);
  if ((int)q->q.size() >= q->cap) return pdFALSE;
  q->q.emplace_back((const uint8_t*)item, (const uint8_t*)item + q->item);
  return pdTRUE;
}
int uxQueueMessagesWaiting(QueueHandle_t h) { auto* q = (SimQueue*)h; SIM_LOCK(q); return (int)q->q.size(); }
BaseType_t xQueueReceive(QueueHandle_t h, void* item, int) {
  auto* q = (SimQueue*)h; SIM_LOCK(q);
  if (q->q.empty()) return pdFALSE;
  memcpy(item, q->q.front().data(), q->item);
  q->q.pop_front();
  return pdTRUE;
}
#ifdef SIM_WASM
void vTaskDelay(int) {}
BaseType_t xTaskCreatePinnedToCore(void (*)(void*), const char*, int, void*, int, TaskHandle_t*, int) { return pdFALSE; }
#else
void vTaskDelay(int ticks) { usleep(ticks * 1000); }
BaseType_t xTaskCreatePinnedToCore(void (*fn)(void*), const char*, int, void* arg, int, TaskHandle_t*, int) {
  std::thread(fn, arg).detach();
  return pdTRUE;
}
#endif

// ---------------------------------------------------------------- TM1637
static const uint8_t DIGIT_SEG[10] = {0x3f, 0x06, 0x5b, 0x4f, 0x66, 0x6d, 0x7d, 0x07, 0x7f, 0x6f};
void TM1637Display::setSegments(const uint8_t* segs, uint8_t len, uint8_t pos) {
  sim::Hw::Tm& t = sim::hw.tm[idx_];
  for (int i = 0; i < len && pos + i < 4; i++) t.segs[pos + i] = segs[i];
  t.on = on_;
  t.bright = bright_;
}
void TM1637Display::showNumberDecEx(int num, uint8_t dots, bool leading_zero, uint8_t length, uint8_t pos) {
  uint8_t d[4] = {0, 0, 0, 0};
  if (num == 0 && !leading_zero) {
    d[length - 1] = DIGIT_SEG[0];
  } else {
    for (int i = length - 1; i >= 0; i--) {
      int digit = num % 10;
      d[i] = (digit == 0 && num == 0 && !leading_zero) ? 0 : DIGIT_SEG[digit];
      num /= 10;
    }
  }
  for (int i = 0; i < 4; i++) { d[i] |= (dots & 0x80); dots <<= 1; }
  setSegments(d, length, pos);
}

#ifndef SIM_WASM
// ---------------------------------------------------------------- LittleFS on a folder
static std::string fsRoot() { const char* e = getenv("SIM_FS_DIR"); return e ? e : "sim_fs"; }
std::string fs::FS::real(const char* path) { return fsRoot() + (path[0] == '/' ? "" : "/") + path; }
// Like the real one, mounting fails unless the label matches the partition in partitions.csv.
bool fs::FS::begin(bool, const char*, uint8_t, const char* label) { if (std::string(label) != "littlefs") return false; ::mkdir(fsRoot().c_str(), 0755); return true; }
File fs::FS::open(const char* path, const char* mode) { return File(real(path), mode); }
bool fs::FS::exists(const char* path) { struct stat st; return ::stat(real(path).c_str(), &st) == 0; }
bool fs::FS::remove(const char* path) { return ::remove(real(path).c_str()) == 0; }
bool fs::FS::rename(const char* a, const char* b) { return ::rename(real(a).c_str(), real(b).c_str()) == 0; }
bool fs::FS::mkdir(const char* path) { return ::mkdir(real(path).c_str(), 0755) == 0; }
static size_t dirSize(const std::string& p) {
  size_t total = 0; DIR* d = opendir(p.c_str()); if (!d) return 0;
  while (dirent* e = readdir(d)) {
    if (e->d_name[0] == '.') continue;
    std::string q = p + "/" + e->d_name; struct stat st;
    if (stat(q.c_str(), &st) == 0) total += S_ISDIR(st.st_mode) ? dirSize(q) : st.st_size;
  }
  closedir(d); return total;
}
size_t fs::FS::usedBytes() { return dirSize(fsRoot()); }

File::File(const std::string& path, const char* mode) : path_(path) {
  auto slash = path.rfind('/');
  name_ = slash == std::string::npos ? path : path.substr(slash + 1);
  struct stat st;
  if (mode[0] == 'r' && stat(path.c_str(), &st) == 0 && S_ISDIR(st.st_mode)) { dir_ = opendir(path.c_str()); return; }
  fp_ = fopen(path.c_str(), mode[0] == 'w' ? "wb" : mode[0] == 'a' ? "ab" : "rb");
}
File& File::operator=(File&& o) noexcept {
  if (this != &o) { close(); fp_ = o.fp_; dir_ = o.dir_; path_ = o.path_; name_ = o.name_; o.fp_ = nullptr; o.dir_ = nullptr; }
  return *this;
}
const char* File::name() const { return name_.c_str(); }
size_t File::size() const { struct stat st; return stat(path_.c_str(), &st) == 0 ? st.st_size : 0; }
void File::close() { if (fp_) fclose(fp_); if (dir_) closedir(dir_); fp_ = nullptr; dir_ = nullptr; }
int File::available() { if (!fp_) return 0; long p = ftell(fp_); fseek(fp_, 0, SEEK_END); long e = ftell(fp_); fseek(fp_, p, SEEK_SET); return (int)(e - p); }
int File::read() { return fp_ ? fgetc(fp_) : -1; }
size_t File::readBytes(char* b, size_t n) { return fp_ ? fread(b, 1, n, fp_) : 0; }
size_t File::write(uint8_t c) { return fp_ ? fwrite(&c, 1, 1, fp_) : 0; }
size_t File::write(const uint8_t* b, size_t n) { return fp_ ? fwrite(b, 1, n, fp_) : 0; }
File File::openNextFile() {
  if (!dir_) return File();
  while (dirent* e = readdir(dir_)) {
    if (e->d_name[0] == '.') continue;
    return File(path_ + "/" + e->d_name, "r");
  }
  return File();
}

#else
// ---------------------------------------------------------------- LittleFS in memory (browser build)
namespace memfs {
std::map<std::string, std::vector<uint8_t>> files;
bool isDir(const std::string& p) {
  std::string pre = p + (p.size() && p.back() == '/' ? "" : "/");
  for (auto& kv : files) if (kv.first.rfind(pre, 0) == 0) return true;
  return p == "/" || p == "/sounds";
}
}
std::string fs::FS::real(const char* path) { return path; }
bool fs::FS::begin(bool, const char*, uint8_t, const char* label) { return std::string(label) == "littlefs"; }
File fs::FS::open(const char* path, const char* mode) { return File(path, mode); }
bool fs::FS::exists(const char* path) { return memfs::files.count(path) || memfs::isDir(path); }
bool fs::FS::remove(const char* path) { return memfs::files.erase(path) > 0; }
bool fs::FS::rename(const char* a, const char* b) {
  auto it = memfs::files.find(a); if (it == memfs::files.end()) return false;
  memfs::files[b] = std::move(it->second); memfs::files.erase(a); return true;
}
bool fs::FS::mkdir(const char*) { return true; }
size_t fs::FS::usedBytes() { size_t t = 0; for (auto& kv : memfs::files) t += kv.second.size(); return t; }

File::File(const std::string& path, const char* mode) : path_(path) {
  auto slash = path.rfind('/');
  name_ = slash == std::string::npos ? path : path.substr(slash + 1);
  if (mode[0] == 'r' && !memfs::files.count(path) && memfs::isDir(path)) {
    mdir_ = true; mopen_ = true;
    std::string pre = path + (path.back() == '/' ? "" : "/");
    for (auto& kv : memfs::files)
      if (kv.first.rfind(pre, 0) == 0 && kv.first.find('/', pre.size()) == std::string::npos) mlist_.push_back(kv.first);
    return;
  }
  if (mode[0] == 'w') { memfs::files[path].clear(); mopen_ = true; }
  else if (mode[0] == 'a') { mopen_ = true; mpos_ = memfs::files[path].size(); }
  else mopen_ = memfs::files.count(path) > 0;
}
File& File::operator=(File&& o) noexcept {
  if (this != &o) {
    path_ = o.path_; name_ = o.name_; mopen_ = o.mopen_; mdir_ = o.mdir_; mpos_ = o.mpos_; midx_ = o.midx_; mlist_ = std::move(o.mlist_);
    o.mopen_ = false;
  }
  return *this;
}
const char* File::name() const { return name_.c_str(); }
size_t File::size() const { auto it = memfs::files.find(path_); return it == memfs::files.end() ? 0 : it->second.size(); }
void File::close() { mopen_ = false; }
int File::available() { return mopen_ && !mdir_ ? (int)(size() - mpos_) : 0; }
int File::read() { if (!available()) return -1; return memfs::files[path_][mpos_++]; }
size_t File::readBytes(char* b, size_t n) {
  size_t k = std::min(n, (size_t)available());
  if (k) memcpy(b, memfs::files[path_].data() + mpos_, k);
  mpos_ += k; return k;
}
size_t File::write(uint8_t c) { return write(&c, 1); }
size_t File::write(const uint8_t* b, size_t n) {
  if (!mopen_ || mdir_) return 0;
  auto& v = memfs::files[path_]; v.insert(v.end(), b, b + n); mpos_ = v.size(); return n;
}
File File::openNextFile() {
  if (!mdir_ || midx_ >= mlist_.size()) return File();
  return File(mlist_[midx_++], "r");
}

#endif

// ---------------------------------------------------------------- Audio (simulated playback)
// /sim/audiofail?path=X&mode=fail|stall|hang|ok makes a file (or "*" = every file, "stream" = streams) go wrong:
// fail = won't open (like a damaged file), stall = opens but no sound comes out, hang = the audio task freezes.
static std::map<std::string, std::string> g_audioFail;
#ifdef SIM_WASM
#define FAIL_LOCK
#else
static std::mutex g_audioFailM;
#define FAIL_LOCK std::lock_guard<std::mutex> l(g_audioFailM)
#endif
static std::string audioFailMode(const std::string& path) {
  FAIL_LOCK;
  auto it = g_audioFail.find(path); if (it != g_audioFail.end()) return it->second;
  it = g_audioFail.find("*"); return it != g_audioFail.end() ? it->second : "";
}
static void audioMaybeHang(const std::string& mode) {
#ifndef SIM_NO_THREADS
  while (mode == "hang") usleep(1000000);   // the audio task never comes back
#endif
}
void Audio::setVolume(uint8_t v) { sim::hw.audioVol = v; }
void Audio::loop() {
  if (!isRunning() || stalled_) return;   // a stalled sound sends nothing on to the amplifier
  static int32_t buf[64];
  int32_t a = 1000 + (int32_t)sim::hw.audioVol * 50000;
  for (int i = 0; i < 64; i++) buf[i] = (i & 8) ? a : -a;   // a stand-in square wave at the set volume
  bool more = true;
  if (audio_process_raw_samples) audio_process_raw_samples(buf, 64);
  if (audio_process_i2s) audio_process_i2s(buf, 64, &more);
}
bool Audio::connecttoFS(fs::FS& f, const char* path) {
  std::string fm = audioFailMode(path);
  audioMaybeHang(fm);
  File fp = f.open(path, "r");
  if (!fp || fm == "fail") { if (fp) fp.close(); playing_ = false; sim::hw.audioPlaying = false; return false; }
  stalled_ = fm == "stall";
  long size = (long)fp.size();
  durMs_ = 3000;
  if (strstr(path, ".wav") && size > 44) {
    char hdr[32]; uint32_t byteRate = 0;
    if (fp.readBytes(hdr, 32) == 32) memcpy(&byteRate, hdr + 28, 4);
    if (byteRate) durMs_ = (unsigned long)((size - 44) * 1000ULL / byteRate);
  }
  fp.close();
  playing_ = true; streaming_ = false; start_ = millis();
  sim::hw.audioPlaying = true; sim::hw.audioFile = path; sim::hw.audioUrl.clear(); sim::hw.audioSeq++;
  return true;
}
bool Audio::connecttohost(const char* url, const char*, const char*) {
  stopSong();
  if (!sim::hw.netOk || !sim::wifiLinked() || !url || strncmp(url, "http", 4) != 0) return false;
  std::string fm = audioFailMode("stream");
  audioMaybeHang(fm);
  if (fm == "fail") return false;
  stalled_ = fm == "stall";
  playing_ = streaming_ = true; start_ = millis();
  sim::hw.streamDrop = false;
  sim::hw.audioPlaying = true; sim::hw.audioFile.clear(); sim::hw.audioUrl = url; sim::hw.audioSeq++;
  return true;
}
void Audio::stopSong() { playing_ = streaming_ = false; sim::hw.audioPlaying = false; }
bool Audio::isRunning() {
  if (playing_ && streaming_ && (!sim::hw.netOk || sim::hw.streamDrop)) stopSong();
  if (playing_ && !streaming_ && millis() - start_ >= durMs_) stopSong();
  return playing_;
}

// ---------------------------------------------------------------- HTTPClient (podcast feed lookup)
#include "HTTPClient.h"
static const size_t HTTP_MAX = 512 * 1024;
#ifdef SIM_WASM
// The page fetches it (synchronous request; the browser's cross-origin rules apply).
extern "C" __attribute__((import_module("env"), import_name("js_http_get"))) int js_http_get(const char* url, char* buf, int max);
int HTTPClient::GET() {
  if (!client_ || !sim::wifiLinked() || !sim::hw.netOk) return -1;
  static std::vector<char> buf(HTTP_MAX);
  int n = js_http_get(url_.c_str(), buf.data(), (int)buf.size());
  if (n < 0) return -1;
  headers_.clear();
  client_->simSetBody(std::string(buf.data(), n));
  size_ = n;
  return HTTP_CODE_OK;
}
#else
// Uses curl, with the response headers first (one block per redirect) and then the body.
int HTTPClient::GET() {
  if (!client_ || !sim::wifiLinked() || !sim::hw.netOk) return -1;
  for (char c : url_)
    if (c <= ' ' || c == '\'' || c == '"' || c == '\\' || c == '`') return -1;
  char opts[160];
  snprintf(opts, sizeof opts, "curl -s -D - %s--max-redirs %d --connect-timeout %d --max-time %d -A '%s' '",
           follow_ ? "-L " : "", redirects_, (connectMs_ + 999) / 1000, 12, ua_.c_str());
  FILE* p = popen((opts + url_ + "' 2>/dev/null").c_str(), "r");
  if (!p) return -1;
  int code = -1;
  char line[1024];
  headers_.clear();
  while (fgets(line, sizeof line, p)) {   // header blocks: keep the last one (after any redirects)
    if (!strncmp(line, "HTTP/", 5)) { headers_.clear(); const char* sp = strchr(line, ' '); code = sp ? atoi(sp + 1) : -1; continue; }
    if (line[0] == '\r' || line[0] == '\n') { if (code < 300 || code >= 400 || !follow_) break; continue; }
    const char* colon = strchr(line, ':');
    if (!colon) continue;
    std::string k(line, colon - line), v(colon + 1);
    for (auto& ch : k) ch = (char)tolower((unsigned char)ch);
    while (!v.empty() && (v[0] == ' ')) v.erase(0, 1);
    while (!v.empty() && (v.back() == '\r' || v.back() == '\n')) v.pop_back();
    headers_[k] = v;
  }
  std::string body;
  char buf[4096];
  size_t n;
  while (body.size() < HTTP_MAX && (n = fread(buf, 1, std::min(sizeof buf, HTTP_MAX - body.size()), p)) > 0) body.append(buf, n);
  pclose(p);
  client_->simSetBody(body);
  size_ = (int)body.size();
  return code;
}
#endif
String HTTPClient::header(const char* name) {
  std::string k(name);
  for (auto& ch : k) ch = (char)tolower((unsigned char)ch);
  auto it = headers_.find(k);
  return String(it == headers_.end() ? "" : it->second.c_str());
}

// ---------------------------------------------------------------- HTTP server
static std::string urlDecode(const std::string& s) {
  std::string o;
  for (size_t i = 0; i < s.size(); i++) {
    if (s[i] == '+') o += ' ';
    else if (s[i] == '%' && i + 2 < s.size()) { o += (char)strtol(s.substr(i + 1, 2).c_str(), nullptr, 16); i += 2; }
    else o += s[i];
  }
  return o;
}
static void parseArgs(const std::string& q, std::map<std::string, std::string>& out) {
  size_t i = 0;
  while (i < q.size()) {
    size_t amp = q.find('&', i); if (amp == std::string::npos) amp = q.size();
    std::string kv = q.substr(i, amp - i); size_t eq = kv.find('=');
    if (!kv.empty()) out[urlDecode(kv.substr(0, eq))] = eq == std::string::npos ? "" : urlDecode(kv.substr(eq + 1));
    i = amp + 1;
  }
}
static std::string b64decode(const std::string& in) {
  static const std::string tbl = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
  std::string out; int val = 0, bits = -8;
  for (char c : in) { auto p = tbl.find(c); if (p == std::string::npos) break; val = (val << 6) + (int)p; bits += 6; if (bits >= 0) { out += char((val >> bits) & 0xFF); bits -= 8; } }
  return out;
}

void WebServer::handleRequest(const std::string& method, const std::string& target, const std::string& ctype,
                              const std::string& body, const std::string& auth) {
  std::map<std::string, std::string> h;
  if (!ctype.empty()) h["content-type"] = ctype;
  if (!auth.empty()) h["authorization"] = auth;
  h["content-length"] = std::to_string(body.size());
  respCode = 0; respType.clear(); respBody.clear();
  dispatch(-1, method, target, body, h);
}

#ifdef SIM_WASM
void WebServer::begin() { printf("[sim] web server running inside the browser page\n"); }
void WebServer::handleClient() {}
#else
void WebServer::begin() {
  const char* e = getenv("SIM_PORT");
  int port = e ? atoi(e) : 8080;
  listen_ = socket(AF_INET, SOCK_STREAM, 0);
  int one = 1; setsockopt(listen_, SOL_SOCKET, SO_REUSEADDR, &one, sizeof one);
  sockaddr_in a{}; a.sin_family = AF_INET; a.sin_port = htons(port); a.sin_addr.s_addr = htonl(INADDR_ANY);
  if (bind(listen_, (sockaddr*)&a, sizeof a) < 0) { perror("bind"); exit(1); }
  listen(listen_, 16);
  fcntl(listen_, F_SETFL, O_NONBLOCK);
  printf("[sim] web server on http://localhost:%d/  (firmware asked for port %d)\n", port, port_);
}

void WebServer::handleClient() {
  if (listen_ < 0) return;
  int fd = accept(listen_, nullptr, nullptr);
  if (fd < 0) return;
  timeval tv{3, 0}; setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof tv);
  std::string req; char buf[8192]; size_t hdrEnd = std::string::npos;
  while (hdrEnd == std::string::npos) {
    ssize_t n = recv(fd, buf, sizeof buf, 0); if (n <= 0) { close(fd); return; }
    req.append(buf, n); hdrEnd = req.find("\r\n\r\n");
  }
  std::string head = req.substr(0, hdrEnd), body = req.substr(hdrEnd + 4);
  std::map<std::string, std::string> headers;
  size_t le = head.find("\r\n");
  std::string line = head.substr(0, le);
  for (size_t p = le + 2; p < head.size();) {
    size_t q = head.find("\r\n", p); if (q == std::string::npos) q = head.size();
    std::string h = head.substr(p, q - p); size_t c = h.find(':');
    if (c != std::string::npos) { std::string k = h.substr(0, c); for (auto& ch : k) ch = tolower(ch); headers[k] = h.substr(c + 1 + (h[c + 1] == ' ')); }
    p = q + 2;
  }
  size_t clen = headers.count("content-length") ? atol(headers["content-length"].c_str()) : 0;
  while (body.size() < clen) { ssize_t n = recv(fd, buf, sizeof buf, 0); if (n <= 0) break; body.append(buf, n); }
  std::string method = line.substr(0, line.find(' '));
  std::string target = line.substr(method.size() + 1, line.rfind(' ') - method.size() - 1);
  dispatch(fd, method, target, body, headers);
  close(fd);
}

#endif

void WebServer::dispatch(int fd, const std::string& method, const std::string& target, const std::string& body,
                         const std::map<std::string, std::string>& headers) {
  args_.clear(); headers_ = headers; extraHeaders_.clear(); sent_ = false; client_ = fd;
  std::string path = target, query;
  size_t qm = target.find('?'); if (qm != std::string::npos) { path = target.substr(0, qm); query = target.substr(qm + 1); }
  parseArgs(query, args_);
  std::string ctype = headers.count("content-type") ? headers.at("content-type") : "";
  bool multipart = ctype.find("multipart/form-data") != std::string::npos;
  if (ctype.find("application/x-www-form-urlencoded") != std::string::npos) parseArgs(body, args_);
  if (!multipart) args_["plain"] = body;
  HTTPMethod m = method == "POST" ? HTTP_POST : HTTP_GET;

  if (path.rfind("/sim/", 0) == 0 && simRoute(path)) return;

  for (auto& r : routes_) {
    if (r.uri != path || (r.m != HTTP_ANY && r.m != m)) continue;
    if (multipart && r.up) {
      std::string boundary = "--" + ctype.substr(ctype.find("boundary=") + 9);
      size_t ps = body.find(boundary), he = body.find("\r\n\r\n", ps);
      std::string ph = body.substr(ps, he - ps);
      size_t fnp = ph.find("filename=\"");
      upload_.filename = fnp == std::string::npos ? "" : ph.substr(fnp + 10, ph.find('"', fnp + 10) - fnp - 10).c_str();
      size_t ds = he + 4, de = body.find("\r\n" + boundary, ds);
      upload_.status = UPLOAD_FILE_START; upload_.currentSize = 0; r.up();
      for (size_t p = ds; p < de; p += sizeof upload_.buf) {
        upload_.currentSize = std::min(sizeof upload_.buf, de - p);
        memcpy(upload_.buf, body.data() + p, upload_.currentSize);
        upload_.status = UPLOAD_FILE_WRITE; r.up();
      }
      upload_.status = UPLOAD_FILE_END; upload_.currentSize = 0; r.up();
    }
    r.h();
    if (!sent_) send(500, "text/plain", "handler sent nothing");
    return;
  }
  if (notFound_) notFound_(); else send(404, "text/plain", "not found");
}

void WebServer::send(int code, const char* type, const String& b) {
  if (sent_) return;
  sent_ = true;
  const char* reason = code == 200 ? "OK" : code == 401 ? "Unauthorized" : code == 404 ? "Not Found" : code == 400 ? "Bad Request" : "Error";
  if (client_ < 0) {   // in-page request (browser build)
    respCode = code; respType = type; respBody = b.s;
    return;
  }
#ifndef SIM_WASM
  std::string out = "HTTP/1.1 " + std::to_string(code) + " " + reason + "\r\nContent-Type: " + type +
                    "\r\nContent-Length: " + std::to_string(b.length()) + "\r\nCache-Control: no-store\r\nConnection: close\r\n" + extraHeaders_ + "\r\n" + b.s;
  size_t off = 0;
  while (off < out.size()) { ssize_t n = ::send(client_, out.data() + off, out.size() - off, MSG_NOSIGNAL); if (n <= 0) break; off += n; }
#endif
}
String WebServer::arg(const char* name) { auto it = args_.find(name); return it == args_.end() ? String() : String(it->second); }
bool WebServer::authenticate(const char* user, const char* pass) {
  auto it = headers_.find("authorization");
  if (it == headers_.end() || it->second.rfind("Basic ", 0) != 0) return false;
  return b64decode(it->second.substr(6)) == std::string(user) + ":" + pass;
}
void WebServer::requestAuthentication() {
  extraHeaders_ = "WWW-Authenticate: Basic realm=\"Login Required\"\r\n";
  send(401, "text/plain", "login required");
}

static std::string jesc(const std::string& s) {
  std::string o;
  for (char c : s) { if (c == '"' || c == '\\') o += '\\'; if ((unsigned char)c >= 32) o += c; }
  return o;
}

// Simulator-only endpoints: real hardware state, time travel, buttons, light level, internet, sound files.
bool WebServer::simRoute(const std::string& path) {
  using sim::hw;
  if (path == "/sim/hw") {
    std::string j = "{\"time\":" + std::to_string(sim_time(nullptr)) + ",\"timeOffset\":" + std::to_string(sim::timeOffset);
    for (int k = 0; k < 2; k++) {
      const sim::Hw::Tm& t = hw.tm[k];
      j += std::string(k ? ",\"proj\"" : ",\"front\"") + ":{\"on\":" + (t.on ? "true" : "false") + ",\"bright\":" + std::to_string(t.bright) + ",\"segs\":[";
      for (int i = 0; i < 4; i++) j += std::to_string(t.segs[i]) + (i < 3 ? "," : "");
      j += "]}";
    }
    j += ",\"audio\":{\"playing\":" + std::string(hw.audioPlaying ? "true" : "false") + ",\"vol\":" + std::to_string(hw.audioVol) +
         ",\"file\":\"" + jesc(hw.audioFile) + "\",\"url\":\"" + jesc(hw.audioUrl) + "\",\"seq\":" + std::to_string(hw.audioSeq) +
         "},\"alarmLeds\":[" + std::to_string(hw.alarmLed[0]) + "," + std::to_string(hw.alarmLed[1]) + "]" +
         ",\"net\":" + (hw.netOk ? "true" : "false") + ",\"ldr\":" + std::to_string(hw.ldr) + "}";
    send(200, "application/json", String(j));
    return true;
  }
  if (path == "/sim/time") {
    sim::timeOffset += atol(arg("add").c_str()); if (hasArg("set")) sim::timeOffset = atol(arg("set").c_str()) - hostTime();
#ifndef SIM_WASM
    saveWorldTime();
#endif
    send(200, "text/plain", "ok"); return true;
  }
  if (path == "/sim/button") {
    String b = arg("b");
    int i = b == "B" ? 1 : b == "1" ? 2 : b == "2" ? 3 : 0;
    long ms = hasArg("ms") ? atol(arg("ms").c_str()) : 150;
    sim::btnUntil[i] = millis() + ms;
    send(200, "text/plain", "ok"); return true;
  }
  if (path == "/sim/ldr") { hw.ldr = atoi(arg("v").c_str()); send(200, "text/plain", "ok"); return true; }
  if (path == "/sim/net") { hw.netOk = arg("ok") != "0"; if (hw.netOk) fakeSync(); send(200, "text/plain", "ok"); return true; }
  if (path == "/sim/wifi") { hw.wifiUp = arg("up") != "0"; send(200, "text/plain", "ok"); return true; }
  if (path == "/sim/ntp") { fakeSync(); send(200, "text/plain", "ok"); return true; }
#ifndef SIM_WASM
  if (path == "/sim/clockerror") { sim::sysDelta = atol(arg("sec").c_str()); send(200, "text/plain", "ok"); return true; }
#endif
  if (path == "/sim/audiofail") {
    { FAIL_LOCK; if (arg("mode") == "ok") g_audioFail.erase(arg("path").c_str()); else g_audioFail[arg("path").c_str()] = arg("mode").c_str(); }
    send(200, "text/plain", "ok"); return true;
  }
#ifndef SIM_WASM   // not in the browser: a frozen page has no watchdog to reset it
  if (path == "/sim/hang") {   // loop() stops coming back (runs inside it): the task watchdog must reset the clock
    send(200, "text/plain", "hanging"); printf("[sim] loop() hangs\n"); fflush(stdout);
    for (;;) usleep(1000000);
  }
#endif
  if (path == "/sim/crash") { send(200, "text/plain", "restarting"); printf("[sim] crash\n"); sim::reset(ESP_RST_PANIC); }
  if (path == "/sim/clock") {   // the clock's own idea of the time, and what it is really
    send(200, "application/json", "{\"system\":" + std::to_string(sim_time(nullptr)) + ",\"real\":" + std::to_string(simRealTime()) +
         ",\"wifi\":" + (sim::wifiLinked() ? "true" : "false") + ",\"portal\":" + (hw.portalActive ? "true" : "false") + "}");
    return true;
  }
  if (path == "/sim/streamfail") { hw.streamDrop = true; send(200, "text/plain", "ok"); return true; }
  if (path == "/sim/file") {   // a sound file's bytes, so the demo page can play it
    std::string p = arg("path").c_str();
    if (p.rfind("/sounds/", 0) != 0 || p.find("..") != std::string::npos) { send(400, "text/plain", "bad path"); return true; }
    File f = LittleFS.open(p.c_str(), "r");
    if (!f) { send(404, "text/plain", "not found"); return true; }
    std::string data((size_t)f.size(), '\0');
    f.readBytes(&data[0], data.size());
    f.close();
    const char* type = p.find(".wav") != std::string::npos ? "audio/wav" : p.find(".mp3") != std::string::npos ? "audio/mpeg" : "application/octet-stream";
    send(200, type, String(data));
    return true;
  }
  return false;
}
