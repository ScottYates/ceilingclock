// Native test: g++ -std=c++17 -I../src test_alarm_logic.cpp && ./a.out
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include "alarm_logic.h"

static int fails = 0;
static time_t mk(int y, int mo, int d, int h, int mi, int s = 0) {
  struct tm t = {}; t.tm_year = y - 1900; t.tm_mon = mo - 1; t.tm_mday = d;
  t.tm_hour = h; t.tm_min = mi; t.tm_sec = s; t.tm_isdst = -1; return mktime(&t);
}
static void fmt(time_t t, char* b) { struct tm l; localtime_r(&t, &l); strftime(b, 40, "%a %Y-%m-%d %H:%M %Z", &l); }
static void expect(const char* name, time_t got, time_t want) {
  char g[40] = "0", w[40] = "0"; if (got) fmt(got, g); if (want) fmt(want, w);
  bool ok = got == want; if (!ok) fails++;
  printf("%s %-40s got %-28s want %s\n", ok ? "PASS" : "FAIL", name, g, w);
}
static void expectB(const char* name, bool got, bool want) {
  bool ok = got == want; if (!ok) fails++; printf("%s %-40s got %d want %d\n", ok ? "PASS" : "FAIL", name, got, want);
}

int main() {
  setenv("TZ", "CST6CDT,M3.2.0,M11.1.0", 1); tzset();
  const uint8_t WEEKDAYS = 0b0111110, WEEKEND = 0b1000001;
  AlarmTime a; a.enabled = true; a.hour = 7; a.minute = 0; a.days = WEEKDAYS;

  // Friday 2026-10-30 08:00 CDT. DST ends Sunday Nov 1.
  time_t fri = mk(2026, 10, 30, 8, 0);
  expect("weekday alarm over weekend + DST end", alarmNext(a, fri), mk(2026, 11, 2, 7, 0));
  expectB("Monday 07:00 is CST (UTC-6)", mk(2026, 11, 2, 7, 0) - mk(2026, 10, 30, 7, 0) == 3 * 86400 + 3600, true);
  a.skipNext = true;
  expect("skipNext jumps to Tuesday", alarmNext(a, fri), mk(2026, 11, 3, 7, 0));
  expect("skip ignored when asked", alarmNext(a, fri, false), mk(2026, 11, 2, 7, 0));
  a.skipNext = false;
  expect("before alarm same day", alarmNext(a, mk(2026, 10, 30, 6, 59, 59)), mk(2026, 10, 30, 7, 0));
  expect("exactly at alarm -> next day", alarmNext(a, mk(2026, 10, 30, 7, 0)), mk(2026, 11, 2, 7, 0));

  AlarmTime w; w.enabled = true; w.hour = 9; w.minute = 30; w.days = WEEKEND;
  expect("weekend alarm", alarmNext(w, fri), mk(2026, 10, 31, 9, 30));

  AlarmTime o; o.enabled = true; o.hour = 5; o.minute = 15; o.days = 0;
  expect("one-time tomorrow", alarmNext(o, fri), mk(2026, 10, 31, 5, 15));
  o.skipNext = true;
  expect("one-time skipped -> never", alarmNext(o, fri), 0);

  AlarmTime off = a; off.enabled = false;
  expect("disabled -> never", alarmNext(off, fri), 0);

  AlarmTime sp; sp.enabled = true; sp.hour = 2; sp.minute = 30; sp.days = 0b1111111;
  { // DST starts Sun 2027-03-14; 02:30 doesn't exist that day. Must still ring once that morning, then 02:30 Monday.
    time_t t1 = alarmNext(sp, mk(2027, 3, 13, 12, 0)); struct tm l; localtime_r(&t1, &l);
    expectB("spring-forward day still rings on Mar 14", l.tm_mday == 14 && (l.tm_hour == 1 || l.tm_hour == 3), true);
    expect("then normal on Mar 15", alarmNext(sp, t1), mk(2027, 3, 15, 2, 30));
  }
  { // DST ends Sun 2026-11-01; 01:30 happens twice. Guard in firmware (23 h) prevents double ring.
    AlarmTime fb; fb.enabled = true; fb.hour = 1; fb.minute = 30; fb.days = 0b1111111;
    time_t t1 = alarmNext(fb, mk(2026, 10, 31, 12, 0)); time_t t2 = alarmNext(fb, t1);
    expectB("fall-back: second hit is <23h or next day", (t2 - t1) < 23 * 3600 || (t2 - t1) >= 24 * 3600, true);
  }

  expectB("due in (06:59:58, 07:00:00]", alarmDueBetween(a, mk(2026, 10, 30, 6, 59, 58), mk(2026, 10, 30, 7, 0, 0)), true);
  expectB("not due after it passed", alarmDueBetween(a, mk(2026, 10, 30, 7, 0, 0), mk(2026, 10, 30, 7, 0, 1)), false);
  expectB("not due on Saturday", alarmDueBetween(a, mk(2026, 10, 31, 6, 59), mk(2026, 10, 31, 7, 1)), false);

  expectB("window 22-07 at 23:00", inWindow(23 * 60, 22 * 60, 7 * 60), true);
  expectB("window 22-07 at 03:00", inWindow(3 * 60, 22 * 60, 7 * 60), true);
  expectB("window 22-07 at 12:00", inWindow(12 * 60, 22 * 60, 7 * 60), false);
  expectB("window 01-05 at 03:00", inWindow(3 * 60, 60, 300), true);
  expectB("ramp start=1", rampVolume(15, 0, 60) == 1, true);
  expectB("ramp half", rampVolume(15, 30, 60) == 8, true);
  expectB("ramp done", rampVolume(15, 90, 60) == 15, true);
  printf(fails ? "\n%d FAILED\n" : "\nall passed\n", fails);
  return fails != 0;
}
