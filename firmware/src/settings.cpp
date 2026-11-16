#include "settings.h"
#include <LittleFS.h>

Config cfg;
static const char* CFG_PATH = "/config.json";

void configDefaults(Config& c) {
  c = Config();
  c.front.dayBright = 4; c.front.nightBright = 1;
  c.proj.dayBright = 7; c.proj.nightBright = 5;  // projected LED digits are dim: run them bright
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
  doc["projMirrorX"] = c.projMirrorX; doc["projMirrorY"] = c.projMirrorY;
  doc["projUpsideDown"] = c.projUpsideDown;
  doc["showOnAlarm"] = c.showOnAlarm;
  doc["webPassword"] = c.webPassword;
  JsonArray tr = doc["trusted"].to<JsonArray>();
  for (int i = 0; i < c.trustedCount; i++) tr.add(c.trusted[i]);
  JsonArray arr = doc["alarms"].to<JsonArray>();
  for (int i = 0; i < c.alarmCount; i++) {
    const AlarmCfg& a = c.alarms[i];
    JsonObject o = arr.add<JsonObject>();
    o["enabled"] = a.t.enabled; o["hour"] = a.t.hour; o["minute"] = a.t.minute;
    o["days"] = a.t.days; o["skipNext"] = a.t.skipNext; o["label"] = a.label; o["sound"] = a.sound;
    o["stream"] = a.stream;
    o["volume"] = a.volume; o["rampSec"] = a.rampSec;
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
  // Settings saved by firmware 1.x had projector brightness in % (for the LCD's LED); now it is 0-7.
  if (!v["lcdContrast"].isNull()) {
    JsonVariantConst p = v["proj"];
    if (!p.isNull()) {
      c.proj.mode = constrain((int)(p["mode"] | c.proj.mode), 0, 3);
      c.proj.dayBright = constrain(((int)(p["dayBright"] | 100) * 7 + 50) / 100, 0, 7);
      c.proj.nightBright = constrain(((int)(p["nightBright"] | 70) * 7 + 50) / 100, 0, 7);
    }
  } else {
    dispFromJson(c.proj, v["proj"], 7);
  }
  c.projMirrorX = v["projMirrorX"] | c.projMirrorX; c.projMirrorY = v["projMirrorY"] | c.projMirrorY;
  c.projUpsideDown = v["projUpsideDown"] | c.projUpsideDown;
  c.showOnAlarm = v["showOnAlarm"] | c.showOnAlarm;
  c.webPassword = v["webPassword"] | c.webPassword;
  JsonArrayConst tr = v["trusted"];
  if (!tr.isNull()) {
    c.trustedCount = 0;
    for (JsonVariantConst t : tr) {
      String ip = t | "";
      ip.trim();
      if (ip.length() >= 7 && ip.length() <= 15 && c.trustedCount < Config::MAX_TRUSTED) c.trusted[c.trustedCount++] = ip;
    }
  }
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
      a.stream = o["stream"] | "";
      a.stream.trim();
      if (a.stream.length() > 280 || !(a.stream.startsWith("http://") || a.stream.startsWith("https://"))) a.stream = "";
      a.volume = constrain((int)(o["volume"] | 12), 0, 21);
      a.rampSec = constrain((int)(o["rampSec"] | 60), 0, 1800);
      a.snoozeMin = constrain((int)(o["snoozeMin"] | 9), 1, 60);
      a.maxRingMin = constrain((int)(o["maxRingMin"] | 30), 1, 120);
      c.alarms[c.alarmCount++] = a;
    }
  }
  return true;
}

// Settings survive a power cut at any moment: a save writes /config.tmp, reads it back to check it,
// keeps the previous good file as /config.bak, then renames the new one into place (LittleFS renames are
// atomic). Loading tries /config.json, then /config.tmp, then /config.bak, so the alarms are never lost.
static bool loadFrom(const char* path) {
  File f = LittleFS.open(path, "r");
  if (!f) return false;
  JsonDocument doc;
  DeserializationError err = deserializeJson(doc, f);
  f.close();
  if (err || !doc["alarms"].is<JsonArrayConst>()) return false;
  Config c;
  configDefaults(c);
  if (!configFromJson(c, doc.as<JsonVariantConst>())) return false;
  cfg = c;
  return true;
}

bool loadConfig() {
  configDefaults(cfg);
  for (const char* p : {CFG_PATH, "/config.tmp", "/config.bak"}) {
    if (loadFrom(p)) {
      if (strcmp(p, CFG_PATH) != 0) { Serial.printf("Settings recovered from %s\n", p); saveConfig(); }
      return true;
    }
  }
  return false;
}

bool saveConfig() {
  JsonDocument doc;
  configToJson(cfg, doc);
  size_t want = measureJson(doc);
  File f = LittleFS.open("/config.tmp", "w");
  if (!f) return false;
  size_t wrote = serializeJson(doc, f);
  f.close();
  // check it reads back whole (a full file system writes short files)
  File chk = LittleFS.open("/config.tmp", "r");
  bool ok = chk && wrote == want && chk.size() == want;
  if (ok) { JsonDocument back; ok = !deserializeJson(back, chk); }
  if (chk) chk.close();
  if (!ok) { LittleFS.remove("/config.tmp"); Serial.println("Settings NOT saved: storage full or failing"); return false; }
  if (LittleFS.exists(CFG_PATH)) LittleFS.rename(CFG_PATH, "/config.bak");
  return LittleFS.rename("/config.tmp", CFG_PATH);
}
