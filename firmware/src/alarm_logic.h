#pragma once
// Pure scheduling logic (no Arduino dependencies) so it can be unit-tested on a PC.
// All times are in the local time zone set by TZ / configTzTime().
#include <time.h>
#include <stdint.h>

struct AlarmTime {
  bool enabled = false;
  uint8_t hour = 7;      // 0-23 local
  uint8_t minute = 0;    // 0-59
  uint8_t days = 0;      // bit0 = Sunday ... bit6 = Saturday; 0 = one-time alarm
  bool skipNext = false; // skip only the next occurrence
};

// Next time (strictly after `after`) this alarm is scheduled to go off.
// honorSkip: when true, the occurrence covered by skipNext is passed over.
// Returns 0 if the alarm will not go off.
inline time_t alarmNext(const AlarmTime& a, time_t after, bool honorSkip = true) {
  if (!a.enabled) return 0;
  if (honorSkip && a.skipNext && a.days == 0) return 0;  // skipped one-time alarm never fires
  struct tm base;
  localtime_r(&after, &base);
  bool skipped = false;
  for (int d = 0; d < 16; d++) {
    struct tm c = base;
    c.tm_mday = base.tm_mday + d;
    c.tm_hour = a.hour;
    c.tm_min = a.minute;
    c.tm_sec = 0;
    c.tm_isdst = -1;
    time_t t = mktime(&c);  // normalizes c, fills tm_wday
    if (t <= after) continue;
    if (a.days && !(a.days & (1 << c.tm_wday))) continue;
    if (honorSkip && a.skipNext && !skipped) { skipped = true; continue; }
    return t;
  }
  return 0;
}

// True if an occurrence of the alarm falls in (from, to]. Skip flag is ignored here;
// the caller decides what to do with a skipped occurrence.
inline bool alarmDueBetween(const AlarmTime& a, time_t from, time_t to) {
  time_t t = alarmNext(a, from, false);
  return t != 0 && t <= to;
}

// Minutes-of-day window that may wrap past midnight (e.g. 22:00-07:00).
inline bool inWindow(uint16_t nowMin, uint16_t startMin, uint16_t endMin) {
  if (startMin == endMin) return false;
  if (startMin < endMin) return nowMin >= startMin && nowMin < endMin;
  return nowMin >= startMin || nowMin < endMin;
}

// Volume during a ramp: from 1 up to target over rampSec seconds.
inline uint8_t rampVolume(uint8_t target, uint32_t elapsedSec, uint32_t rampSec) {
  if (target == 0) return 0;
  if (rampSec == 0 || elapsedSec >= rampSec) return target;
  return (uint8_t)(1 + (uint32_t)(target - 1) * elapsedSec / rampSec);
}
