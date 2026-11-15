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

// The occurrence of the alarm that falls in (from, to], or 0 if none does. Skip is ignored here (the caller
// consumes a skip instead of ringing). Used with a window that covers everything since the last check, so
// an alarm still rings after the clock jumps forward over it or the loop was busy for a while.
inline time_t alarmDueIn(const AlarmTime& a, time_t from, time_t to) {
  if (to <= from) return 0;
  time_t t = alarmNext(a, from, false);
  return (t != 0 && t <= to) ? t : 0;
}

// True if two occurrence times are the same alarm occurrence: equal, or the same local date and time of day
// within two hours (the repeated hour when daylight saving ends). Used so an occurrence rings only once,
// while an alarm moved to a later time the same day still rings.
inline bool sameOccurrence(time_t x, time_t y) {
  if (x == y) return true;
  if (!x || !y || (x > y ? x - y : y - x) > 2 * 3600) return false;
  struct tm a, b;
  localtime_r(&x, &a);
  localtime_r(&y, &b);
  return a.tm_year == b.tm_year && a.tm_yday == b.tm_yday && a.tm_hour == b.tm_hour && a.tm_min == b.tm_min;
}

// The occurrence of alarm a that should ring now, or 0. Looks at everything since the last check, but no
// further back than catchUp seconds, and leaves out the occurrence it last rang for.
inline time_t alarmToRing(const AlarmTime& a, time_t lastCheck, time_t now, time_t lastFiredAt, time_t catchUp) {
  if (now <= lastCheck) return 0;
  time_t from = lastCheck > now - catchUp ? lastCheck : now - catchUp;
  time_t t = alarmDueIn(a, from, now);
  if (!t || sameOccurrence(t, lastFiredAt)) return 0;
  return t;
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
