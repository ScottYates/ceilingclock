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
  TM1637Display(int, int) { static int made = 0; idx_ = made < 2 ? made++ : 1; }  // 0 front, 1 projector
  void setBrightness(uint8_t b, bool on = true) { bright_ = b; on_ = on; }
  void setSegments(const uint8_t* segs, uint8_t len = 4, uint8_t pos = 0);
  void clear() { uint8_t z[4] = {0, 0, 0, 0}; setSegments(z); }
  void showNumberDecEx(int num, uint8_t dots = 0, bool leading_zero = false, uint8_t length = 4, uint8_t pos = 0);
 private:
  uint8_t bright_ = 7; bool on_ = true; int idx_ = 0;
};

