// PC simulator: minimal Arduino / ESP32 API so the real firmware sources compile on Linux.
// Hardware is simulated; its state is exposed at /sim/hw by the simulated web server.
#pragma once
#include <cstdint>
#include <cstring>
#include <cstdio>
#include <cstdlib>
#include <cctype>
#include <cmath>
#include <string>
#include <vector>
#include <algorithm>
#include <functional>
#include <time.h>
#include <sys/time.h>
#include <unistd.h>

// glibc declares time() noexcept; wasi-libc (browser build) does not. The simulator's time() must match.
#ifdef __wasi__
#define SIM_NOEXCEPT
#else
#define SIM_NOEXCEPT noexcept
#endif
#ifndef PI
#define PI 3.14159265358979f
#endif
#define LOW 0
#define HIGH 1
#define INPUT 0
#define OUTPUT 1
#define INPUT_PULLUP 2
#define PROGMEM
#define constrain(amt, low, high) ((amt) < (low) ? (low) : ((amt) > (high) ? (high) : (amt)))
using std::min;
using std::max;

#if defined(__GLIBC__) && (__GLIBC__ == 2 && __GLIBC_MINOR__ < 38)   // macOS and newer glibc have strlcpy
inline size_t strlcpy(char* d, const char* s, size_t n) {
  size_t l = strlen(s);
  if (n) { size_t c = l >= n ? n - 1 : l; memcpy(d, s, c); d[c] = 0; }
  return l;
}
#endif

// ---------------------------------------------------------------- String
class String {
 public:
  std::string s;
  String() {}
  String(const char* c) : s(c ? c : "") {}
  String(const std::string& x) : s(x) {}
  String(char c) : s(1, c) {}
  explicit String(int v) : s(std::to_string(v)) {}
  explicit String(unsigned v) : s(std::to_string(v)) {}
  explicit String(long v) : s(std::to_string(v)) {}
  const char* c_str() const { return s.c_str(); }
  unsigned length() const { return s.size(); }
  bool isEmpty() const { return s.empty(); }
  void reserve(size_t n) { s.reserve(n); }
  bool concat(const char* c) { s += c; return true; }
  bool concat(const char* c, size_t n) { s.append(c, n); return true; }
  bool concat(char c) { s += c; return true; }
  String substring(int a) const { return a >= (int)s.size() ? String() : String(s.substr(a)); }
  String substring(int a, int b) const { return String(s.substr(a, b - a)); }
  int lastIndexOf(char c) const { auto p = s.rfind(c); return p == std::string::npos ? -1 : (int)p; }
  int indexOf(char c) const { auto p = s.find(c); return p == std::string::npos ? -1 : (int)p; }
  bool endsWith(const char* e) const { size_t n = strlen(e); return s.size() >= n && s.compare(s.size() - n, n, e) == 0; }
  bool startsWith(const char* e) const { return s.rfind(e, 0) == 0; }
  void toLowerCase() { for (auto& c : s) c = tolower((unsigned char)c); }
  void trim() { size_t a = s.find_first_not_of(" \t\r\n"), b = s.find_last_not_of(" \t\r\n"); s = a == std::string::npos ? "" : s.substr(a, b - a + 1); }
  long toInt() const { return atol(s.c_str()); }
  char operator[](unsigned i) const { return i < s.size() ? s[i] : 0; }
  String& operator+=(const String& o) { s += o.s; return *this; }
  String& operator+=(const char* o) { s += o; return *this; }
  String& operator+=(char c) { s += c; return *this; }
  bool operator==(const String& o) const { return s == o.s; }
  bool operator==(const char* o) const { return s == o; }
  bool operator!=(const String& o) const { return s != o.s; }
  bool operator!=(const char* o) const { return s != o; }
  bool operator<(const String& o) const { return s < o.s; }
};
inline String operator+(const String& a, const String& b) { return String(a.s + b.s); }
inline String operator+(const String& a, const char* b) { return String(a.s + b); }
inline String operator+(const char* a, const String& b) { return String(std::string(a) + b.s); }
inline String operator+(const String& a, char b) { return String(a.s + b); }

// ---------------------------------------------------------------- Print / Stream
class Print {
 public:
  virtual ~Print() {}
  virtual size_t write(uint8_t c) = 0;
  virtual size_t write(const uint8_t* b, size_t n) { size_t k = 0; while (n--) k += write(*b++); return k; }
  size_t write(const char* s) { return write((const uint8_t*)s, strlen(s)); }
  size_t print(const char* s) { return write(s); }
  size_t print(const String& s) { return write(s.c_str()); }
  size_t println(const char* s = "") { size_t n = print(s); return n + write((uint8_t)'\n'); }
  size_t println(const String& s) { return println(s.c_str()); }
  int printf(const char* f, ...) __attribute__((format(printf, 2, 3)));
};
class Printable {
 public:
  virtual ~Printable() {}
  virtual size_t printTo(Print& p) const = 0;
};
class Stream : public Print {
 public:
  virtual int available() = 0;
  virtual int read() = 0;
  virtual size_t readBytes(char* b, size_t n) { size_t k = 0; while (k < n) { int c = read(); if (c < 0) break; b[k++] = (char)c; } return k; }
};
class SerialClass : public Print {
 public:
  void begin(unsigned long) {}
  size_t write(uint8_t c) override { fputc(c, stdout); fflush(stdout); return 1; }
};
extern SerialClass Serial;

// ---------------------------------------------------------------- timing, GPIO, PWM, ADC
unsigned long millis();
void delay(unsigned long ms);
void pinMode(int pin, int mode);
int digitalRead(int pin);
int analogRead(int pin);
void analogReadResolution(int bits);
bool ledcAttach(int pin, int freq, int res);
void ledcWrite(int pin, uint32_t duty);
// time(), settimeofday() and the date functions are the real names: the simulator supplies time() and
// settimeofday() itself (sim_hw.cpp) and links in the ESP32's own mktime/localtime_r/tzset (newlib/), which
// replace the PC C library's for the whole program.
#ifdef __wasi__
struct timezone;
extern "C" int settimeofday(const struct timeval* tv, const struct timezone* tz);   // wasi-libc leaves these out
extern "C" void tzset(void);
#endif
void configTzTime(const char* tz, const char* s1, const char* s2 = nullptr, const char* s3 = nullptr);

struct EspClass { [[noreturn]] void restart(); };
extern EspClass ESP;

// ---------------------------------------------------------------- reset reason and RTC memory (esp_system.h)
typedef enum {
  ESP_RST_UNKNOWN, ESP_RST_POWERON, ESP_RST_EXT, ESP_RST_SW, ESP_RST_PANIC, ESP_RST_INT_WDT, ESP_RST_TASK_WDT,
  ESP_RST_WDT, ESP_RST_DEEPSLEEP, ESP_RST_BROWNOUT, ESP_RST_SDIO
} esp_reset_reason_t;
esp_reset_reason_t esp_reset_reason();
// Variables marked RTC_NOINIT_ATTR keep their contents across a reset but not a power cut. The simulator
// writes them out when the clock resets and reads them back when it starts "warm" (see sim_hw.cpp).
#define RTC_NOINIT_ATTR
typedef int esp_err_t;
#define ESP_OK 0

// ---------------------------------------------------------------- FreeRTOS (threads + a queue)
typedef void* QueueHandle_t;
typedef void* TaskHandle_t;
typedef int BaseType_t;
#define pdTRUE 1
#define pdFALSE 0
#define pdMS_TO_TICKS(ms) ((int)(ms))
int uxQueueMessagesWaiting(QueueHandle_t q);
QueueHandle_t xQueueCreate(int len, size_t itemSize);
BaseType_t xQueueSend(QueueHandle_t q, const void* item, int ticks);
BaseType_t xQueueReceive(QueueHandle_t q, void* item, int ticks);
void vTaskDelay(int ticks);
BaseType_t xTaskCreatePinnedToCore(void (*fn)(void*), const char*, int, void*, int, TaskHandle_t*, int);

// ---------------------------------------------------------------- simulated hardware state
namespace sim {
struct Hw {
  struct Tm { bool on = false; int bright = 0; uint8_t segs[4] = {0}; };
  Tm tm[2];                           // [0] front display, [1] ceiling projector (in the order main.cpp makes them)
  bool audioPlaying = false; int audioVol = 0; std::string audioFile;
  std::string audioUrl;               // stream being played (empty = a file)
  int audioSeq = 0;                   // counts every start, so the demo page can restart its player
  bool netOk = true;                  // simulated internet connection
  bool streamDrop = false;            // the demo page couldn't play the stream
  int ldr = 2000;
  bool btnDown[4] = {false, false, false, false};   // A, B, alarm 1, alarm 2
  uint32_t alarmLed[2] = {0, 0};      // the alarm buttons' lights (10-bit PWM)
  bool wifiUp = true;                 // the router is reachable
  bool wifiConnected = false;         // the clock has joined it (needs autoConnect() or WiFi.begin())
  bool portalActive = false; unsigned long portalStart = 0, portalTimeoutMs = 0;
  bool rtcPresent = false;            // a DS3231 is fitted (SIM_RTC=1)
};
extern Hw hw;
bool wifiLinked();
void powerOn();                                  // before setup(): RTC memory as after power-on or a reset
[[noreturn]] void reset(esp_reset_reason_t why);  // the clock resets (keeps RTC memory)                    // joined and the router is up
void tick();                          // called by the simulator's main loop: background NTP sync
extern long timeOffset;
}
