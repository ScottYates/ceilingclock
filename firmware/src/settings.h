#pragma once
#include <Arduino.h>
#include <ArduinoJson.h>
#include "alarm_logic.h"

constexpr int MAX_ALARMS = 8;

// Display visibility modes
enum DispMode : uint8_t { DM_ON = 0, DM_OFF = 1, DM_NIGHT_ONLY = 2, DM_DAY_ONLY = 3 };

struct AlarmCfg {
  AlarmTime t;
  String label = "Alarm";
  String sound = "/sounds/beep.wav";  // file to play; also the backup when a stream can't play
  String stream = "";       // optional http(s) URL: internet radio, an audio file, or a podcast feed (newest episode)
  uint8_t volume = 12;      // 0-21
  uint16_t rampSec = 60;    // fade-in time for the sound
  uint8_t sunriseMin = 15;  // light ramps up this many minutes before; 0 = off
  uint8_t snoozeMin = 9;
  uint8_t maxRingMin = 30;  // stops by itself after this long
};

struct DisplayCfg {
  uint8_t mode = DM_ON;
  uint8_t dayBright = 50;   // front: 0-7, projector: 0-100 %
  uint8_t nightBright = 20;
};

struct Config {
  String tz = "CST6CDT,M3.2.0,M11.1.0";  // America/Chicago
  String ntp = "pool.ntp.org";
  bool hour24 = false;
  uint16_t nightStart = 22 * 60;  // minutes after midnight
  uint16_t nightEnd = 7 * 60;
  bool useLdr = false;            // also treat "dark room" as night
  uint16_t ldrThreshold = 400;    // raw ADC (0-4095) below this = dark
  DisplayCfg front;               // TM1637, brightness 0-7
  DisplayCfg proj;                // ceiling projector, brightness %
  bool projMirrorX = true;
  bool projMirrorY = false;
  bool projInvert = true;         // true = bright digits on dark ceiling
  uint8_t lcdContrast = 60;
  uint8_t sunriseMaxBright = 160; // 0-255; caps ring current
  bool showOnAlarm = true;        // displays turn on while ringing even if set to off
  String webPassword = "";        // empty = no login (user name is "admin")
  uint8_t alarmCount = 0;
  AlarmCfg alarms[MAX_ALARMS];
};

extern Config cfg;

void configDefaults(Config& c);
void configToJson(const Config& c, JsonDocument& doc);
bool configFromJson(Config& c, JsonVariantConst v);
bool loadConfig();
bool saveConfig();
