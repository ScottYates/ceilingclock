// PC simulator: stand-ins for the ESP32 libraries the firmware uses.
#pragma once
#include "Arduino.h"
#include <map>

// ---------------------------------------------------------------- Wi-Fi, mDNS, OTA, I2C
#define WL_CONNECTED 3
#define WIFI_STA 1
#define WIFI_AP 2
struct IPAddressSim { String toString() const { return "127.0.0.1"; } };
struct WiFiClass {
  int status() { return WL_CONNECTED; }
  int getMode() { return WIFI_STA; }
  IPAddressSim localIP() { return {}; }
  int RSSI() { return -52; }
  void setHostname(const char*) {}
};
extern WiFiClass WiFi;
struct WiFiManager {
  void setConfigPortalBlocking(bool) {}
  void setHostname(const char*) {}
  bool autoConnect(const char*) { return true; }
  void process() {}
  void resetSettings() {}
};
struct MDNSClass { bool begin(const char*) { return true; } void addService(const char*, const char*, int) {} };
extern MDNSClass MDNS;
#define UPDATE_SIZE_UNKNOWN 0xFFFFFFFF
struct UpdateClass {
  bool running = false; size_t total = 0;
  bool begin(size_t) { running = true; total = 0; return true; }
  size_t write(const uint8_t*, size_t n) { total += n; return n; }
  bool end(bool) { running = false; return true; }
  bool isRunning() { return running; }
  bool hasError() { return false; }
};
extern UpdateClass Update;
struct TwoWire { void begin(int, int) {} };
extern TwoWire Wire;

// ---------------------------------------------------------------- RTC (absent in the simulator; time comes from "NTP")
struct DateTime {
  uint32_t t;
  DateTime(uint32_t x = 0) : t(x) {}
  uint32_t unixtime() const { return t; }
};
struct RTC_DS3231 {
  bool begin(TwoWire*) { return false; }
  bool lostPower() { return true; }
  DateTime now() { return DateTime((uint32_t)sim_time(nullptr)); }
  void adjust(const DateTime&) {}
};

// ---------------------------------------------------------------- SNTP
typedef void (*sntp_sync_cb)(struct timeval*);
void sntp_set_sync_interval(uint32_t ms);
void sntp_set_time_sync_notification_cb(sntp_sync_cb cb);
bool sntp_restart();

// ---------------------------------------------------------------- TM1637
#define SEG_A 0b00000001
#define SEG_B 0b00000010
#define SEG_C 0b00000100
#define SEG_D 0b00001000
#define SEG_E 0b00010000
#define SEG_F 0b00100000
#define SEG_G 0b01000000
class TM1637Display {
 public:
  TM1637Display(int, int) {}
  void setBrightness(uint8_t b, bool on = true) { bright_ = b; on_ = on; }
  void setSegments(const uint8_t* segs, uint8_t len = 4, uint8_t pos = 0);
  void clear() { uint8_t z[4] = {0, 0, 0, 0}; setSegments(z); }
  void showNumberDecEx(int num, uint8_t dots = 0, bool leading_zero = false, uint8_t length = 4, uint8_t pos = 0);
 private:
  uint8_t bright_ = 7; bool on_ = true;
};

// ---------------------------------------------------------------- Adafruit GFX canvas + PCD8544
#define BLACK 1
#define WHITE 0
class GFXcanvas1 {
 public:
  GFXcanvas1(int w, int h) : w_(w), h_(h), buf_(((w + 7) / 8) * h, 0) {}
  void drawPixel(int x, int y, int c);
  bool getPixel(int x, int y) const;
  void fillScreen(int c) { std::fill(buf_.begin(), buf_.end(), c ? 0xFF : 0); }
  void fillRect(int x, int y, int w, int h, int c) { for (int j = y; j < y + h; j++) for (int i = x; i < x + w; i++) drawPixel(i, j, c); }
  void setTextSize(int s) { size_ = s; }
  void setTextColor(int c) { color_ = c; }
  void setCursor(int x, int y) { cx_ = x; cy_ = y; }
  void print(const String& s) { for (unsigned i = 0; i < s.length(); i++) drawChar(s[i]); }
  void print(const char* s) { print(String(s)); }
  uint8_t* getBuffer() { return buf_.data(); }
 private:
  void drawChar(char c);
  int w_, h_, size_ = 1, color_ = 1, cx_ = 0, cy_ = 0;
  std::vector<uint8_t> buf_;
};
class Adafruit_PCD8544 {
 public:
  Adafruit_PCD8544(int, int, int, int, int) {}
  bool begin(uint8_t contrast = 40, uint8_t bias = 4) { sim::hw.lcdContrast = contrast; return true; }
  void setContrast(uint8_t c) { sim::hw.lcdContrast = c; }
  void clearDisplay() { memset(buf_, 0, sizeof buf_); }
  void drawPixel(int x, int y, int c) {
    if (x < 0 || y < 0 || x >= 84 || y >= 48) return;
    if (c) buf_[x + (y / 8) * 84] |= 1 << (y % 8); else buf_[x + (y / 8) * 84] &= ~(1 << (y % 8));
  }
  void display() { memcpy(sim::hw.lcdShown, buf_, sizeof buf_); }
 private:
  uint8_t buf_[6 * 84] = {0};
};

// ---------------------------------------------------------------- NeoPixel
#define NEO_GRB 0
#define NEO_KHZ800 0
class Adafruit_NeoPixel {
 public:
  Adafruit_NeoPixel(int n, int, int) : n_(n) {}
  void begin() {}
  void clear() { for (int i = 0; i < 16; i++) px_[i][0] = px_[i][1] = px_[i][2] = 0; }
  void setPixelColor(int i, uint8_t r, uint8_t g, uint8_t b) { if (i >= 0 && i < 16) { px_[i][0] = r; px_[i][1] = g; px_[i][2] = b; } }
  void show() { memcpy(sim::hw.ring, px_, sizeof px_); }
 private:
  int n_; uint8_t px_[16][3] = {{0}};
};
