#include "settings.h"
#include <LittleFS.h>

Config cfg;
static const char* CFG_PATH = "/config.json";

void configDefaults(Config& c) {
  c = Config();
  c.front.dayBright = 4; c.front.nightBright = 1;
  c.proj.dayBright = 60; c.proj.nightBright = 30;
  c.alarmCount = 2;
  c.alarms[0].label = "Weekdays"; c.alarms[0].t.hour = 6; c.alarms[0].t.minute = 30; c.alarms[0].t.days = 0b0111110;
  c.alarms[1].label = "Weekend";  c.alarms[1].t.hour = 8; c.alarms[1].t.minute = 30; c.alarms[1].t.days = 0b1000001;
}

static void dispToJson(const DisplayCfg& d, JsonObject o) {
  o["mode"] = d.mode; o["dayBright"] = d.dayBright; o["nightBright"] = d.nightBright;
}
static void dispFromJson(DisplayCfg& d, JsonVariantConst o, uint8_t maxB) {
  if (o.isNull()) return;
  d.mode = constrain((int)(o["mode"] | d.mode), 0, 3);
  d.dayBright = constrain((int)(o["dayBright"] | d.dayBright), 0, maxB);
  d.nightBright = constrain((int)(o["nightBright"] | d.nightBright), 0, maxB);
}

void configToJson(const Config& c, JsonDocument& doc) {
  doc["tz"] = c.tz; doc["ntp"] = c.ntp; doc["hour24"] = c.hour24;
  doc["nightStart"] = c.nightStart; doc["nightEnd"] = c.nightEnd;
  doc["useLdr"] = c.useLdr; doc["ldrThreshold"] = c.ldrThreshold;
  dispToJson(c.front, doc["front"].to<JsonObject>());
  dispToJson(c.proj, doc["proj"].to<JsonObject>());
  doc["projMirrorX"] = c.projMirrorX; doc["projMirrorY"] = c.projMirrorY; doc["projInvert"] = c.projInvert;
  doc["lcdContrast"] = c.lcdContrast; doc["sunriseMaxBright"] = c.sunriseMaxBright;
  doc["showOnAlarm"] = c.showOnAlarm;
  doc["webPassword"] = c.webPassword;
  JsonArray arr = doc["alarms"].to<JsonArray>();
  for (int i = 0; i < c.alarmCount; i++) {
    const AlarmCfg& a = c.alarms[i];
    JsonObject o = arr.add<JsonObject>();
    o["enabled"] = a.t.enabled; o["hour"] = a.t.hour; o["minute"] = a.t.minute;
    o["days"] = a.t.days; o["skipNext"] = a.t.skipNext; o["label"] = a.label; o["sound"] = a.sound;
    o["volume"] = a.volume; o["rampSec"] = a.rampSec; o["sunriseMin"] = a.sunriseMin;
    o["snoozeMin"] = a.snoozeMin; o["maxRingMin"] = a.maxRingMin;
  }
}

bool configFromJson(Config& c, JsonVariantConst v) {
  if (!v.is<JsonObjectConst>()) return false;
  c.tz = v["tz"] | c.tz; c.ntp = v["ntp"] | c.ntp; c.hour24 = v["hour24"] | c.hour24;
  c.nightStart = constrain((int)(v["nightStart"] | c.nightStart), 0, 1439);
  c.nightEnd = constrain((int)(v["nightEnd"] | c.nightEnd), 0, 1439);
  c.useLdr = v["useLdr"] | c.useLdr;
  c.ldrThreshold = constrain((int)(v["ldrThreshold"] | c.ldrThreshold), 0, 4095);
  dispFromJson(c.front, v["front"], 7);
  dispFromJson(c.proj, v["proj"], 100);
  c.projMirrorX = v["projMirrorX"] | c.projMirrorX; c.projMirrorY = v["projMirrorY"] | c.projMirrorY;
  c.projInvert = v["projInvert"] | c.projInvert;
  c.lcdContrast = constrain((int)(v["lcdContrast"] | c.lcdContrast), 0, 127);
  c.sunriseMaxBright = constrain((int)(v["sunriseMaxBright"] | c.sunriseMaxBright), 0, 255);
  c.showOnAlarm = v["showOnAlarm"] | c.showOnAlarm;
  c.webPassword = v["webPassword"] | c.webPassword;
  JsonArrayConst arr = v["alarms"];
  if (!arr.isNull()) {
    c.alarmCount = 0;
    for (JsonVariantConst o : arr) {
      if (c.alarmCount >= MAX_ALARMS) break;
      AlarmCfg a;
      a.t.enabled = o["enabled"] | false;
      a.t.hour = constrain((int)(o["hour"] | 7), 0, 23);
      a.t.minute = constrain((int)(o["minute"] | 0), 0, 59);
      a.t.days = (int)(o["days"] | 0) & 0x7F;
      a.t.skipNext = o["skipNext"] | false;
      a.label = o["label"] | "Alarm";
      a.sound = o["sound"] | "/sounds/beep.wav";
      a.volume = constrain((int)(o["volume"] | 12), 0, 21);
      a.rampSec = constrain((int)(o["rampSec"] | 60), 0, 1800);
      a.sunriseMin = constrain((int)(o["sunriseMin"] | 15), 0, 60);
      a.snoozeMin = constrain((int)(o["snoozeMin"] | 9), 1, 60);
      a.maxRingMin = constrain((int)(o["maxRingMin"] | 30), 1, 120);
      c.alarms[c.alarmCount++] = a;
    }
  }
  return true;
}

bool loadConfig() {
  configDefaults(cfg);
  File f = LittleFS.open(CFG_PATH, "r");
  if (!f) return false;
  JsonDocument doc;
  DeserializationError err = deserializeJson(doc, f);
  f.close();
  if (err) return false;
  return configFromJson(cfg, doc.as<JsonVariantConst>());
}

bool saveConfig() {
  JsonDocument doc;
  configToJson(cfg, doc);
  File f = LittleFS.open("/config.tmp", "w");
  if (!f) return false;
  serializeJson(doc, f);
  f.close();
  LittleFS.remove(CFG_PATH);
  return LittleFS.rename("/config.tmp", CFG_PATH);
}
