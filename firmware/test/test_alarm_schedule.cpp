// Exhaustive PC test of the alarm schedule: an alarm must ring exactly once for every day it is set for.
//   g++ -std=c++17 -O2 -Isrc test/test_alarm_schedule.cpp -o /tmp/tsched && /tmp/tsched
// Drives alarmToRing() the way checkAlarms() does, with checks at irregular intervals (1 s to 10 min, plus
// forward clock jumps of up to 29 min) through three years, for many alarm times (including the hour that
// daylight saving skips or repeats), every weekday pattern, and several time zones.
#include "alarm_logic.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#include <vector>
#include <random>

static int fails = 0;
#define CHECK(c, ...) do { if (!(c)) { if (fails++ < 40) { printf("FAIL: "); printf(__VA_ARGS__); printf("\n"); } } } while (0)

static long dayKey(time_t t) { struct tm l; localtime_r(&t, &l); return (l.tm_year + 1900) * 1000L + l.tm_yday; }
static time_t mkLocal(int y, int mo, int d, int h, int mi) {
  struct tm t = {}; t.tm_year = y - 1900; t.tm_mon = mo - 1; t.tm_mday = d; t.tm_hour = h; t.tm_min = mi; t.tm_isdst = -1;
  return mktime(&t);
}

// Runs one alarm through [start, end) with irregular checks; returns ring times keyed by local day.
static std::map<long, std::vector<time_t>> run(const AlarmTime& a, time_t start, time_t end, unsigned seed, bool jumps) {
  std::mt19937 rng(seed);
  std::map<long, std::vector<time_t>> rings;
  time_t lastCheck = start, lastFired = 0;
  for (time_t now = start + 1; now < end;) {
    time_t t = alarmToRing(a, lastCheck, now, lastFired, 30 * 60);
    if (t) {
      CHECK(now >= t, "rang before its time");
      CHECK(now - t <= 30 * 60, "rang %ld s late", (long)(now - t));
      lastFired = t;
      rings[dayKey(t)].push_back(now);
    }
    lastCheck = now;
    int r = rng() % 1000;
    if (jumps && r == 0) now += 60 + rng() % (29 * 60);   // the clock jumps forward (a time sync) or the loop stalls
    else if (r < 700) now += 1 + rng() % 5;              // usual: checked every loop
    else now += 1 + rng() % 600;                           // busy for a while
  }
  return rings;
}

static void scheduleTest(const char* tz, int hour, int minute, uint8_t days, unsigned seed) {
  setenv("TZ", tz, 1); tzset();
  AlarmTime a; a.enabled = true; a.hour = hour; a.minute = minute; a.days = days;
  time_t start = mkLocal(2026, 1, 1, 0, 0), end = mkLocal(2029, 1, 1, 0, 0);
  auto rings = run(a, start - 3600, end, seed, true);   // start checking an hour before the first day
  // every day in range: exactly one ring on the days it is set for, none on the others
  int expected = 0, got = 0;
  for (time_t d = start + 12 * 3600; d < end - 12 * 3600; d += 86400) {
    struct tm l; localtime_r(&d, &l);
    bool set = days == 0x7F || (days & (1 << l.tm_wday));
    long k = dayKey(d);
    size_t n = rings.count(k) ? rings[k].size() : 0;
    if (set) { expected++; got += n; }
    CHECK(n == (set ? 1u : 0u), "%s %02d:%02d days=%02x: %zu rings on %04d-%02d-%02d (want %d)", tz, hour, minute, days, n,
          l.tm_year + 1900, l.tm_mon + 1, l.tm_mday, set ? 1 : 0);
  }
  printf("%-34s %02d:%02d days=%02x  %d of %d days rang\n", tz, hour, minute, days, got, expected);
}

int main() {
  const char* zones[] = {"CST6CDT,M3.2.0,M11.1.0", "EST5EDT,M3.2.0,M11.1.0", "GMT0BST,M3.5.0/1,M10.5.0",
                         "AEST-10AEDT,M10.1.0,M4.1.0/3", "IST-5:30", "NST3:30NDT,M3.2.0,M11.1.0", "UTC0"};
  int times[][2] = {{0, 0}, {1, 30}, {2, 0}, {2, 30}, {3, 0}, {6, 30}, {12, 0}, {23, 59}};
  uint8_t masks[] = {0x7F, 0x3E, 0x41, 0x01, 0x40, 0x15};
  unsigned seed = 1;
  for (const char* z : zones)
    for (auto& t : times)
      for (uint8_t m : masks) scheduleTest(z, t[0], t[1], m, seed++);

  // ---- specific situations
  setenv("TZ", "CST6CDT,M3.2.0,M11.1.0", 1); tzset();
  AlarmTime a; a.enabled = true; a.hour = 7; a.minute = 0; a.days = 0x7F;
  time_t seven = mkLocal(2026, 11, 16, 7, 0);
  // rang at 7:00, then moved to 7:30 the same morning: rings again at 7:30
  time_t fired = alarmToRing(a, seven - 1, seven, 0, 1800);
  CHECK(fired == seven, "7:00 rings");
  a.minute = 30;
  CHECK(alarmToRing(a, seven + 1799, seven + 1800, fired, 1800) == seven + 1800, "moved to 7:30 the same day rings again");
  a.minute = 0;
  // clock jumps forward 20 minutes over 7:00 (first time sync after starting from a slow backup clock)
  CHECK(alarmToRing(a, seven - 600, seven + 600, 0, 1800) == seven, "a 20-minute jump over the alarm still rings");
  // clock jumps back after ringing: no second ring
  CHECK(alarmToRing(a, seven - 300, seven + 5, seven, 1800) == 0, "no second ring after the clock goes back");
  // power-on 10 minutes after the alarm: the 15-minute catch-up rings it
  CHECK(alarmToRing(a, seven + 600 - 900, seven + 600, 0, 1800) == seven, "power back on 10 min late still rings");
  // an alarm set a few seconds into its own minute, after that minute: not until tomorrow
  CHECK(alarmToRing(a, seven + 10, seven + 11, 0, 1800) == 0, "set after its time: waits for tomorrow");
  // one-time alarm with skip: due (the caller consumes the skip instead of ringing)
  AlarmTime once = a; once.days = 0; once.skipNext = true;
  CHECK(alarmToRing(once, seven - 1, seven, 0, 1800) == seven, "skipped one-time alarm is reported so the skip is used up");
  // disabled alarm never rings
  AlarmTime off = a; off.enabled = false;
  CHECK(alarmToRing(off, seven - 1, seven, 0, 1800) == 0, "disabled alarm doesn't ring");

  printf(fails ? "\n%d FAILED\n" : "\nall schedule tests passed\n", fails);
  return fails != 0;
}
