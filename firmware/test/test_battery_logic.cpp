// Native test: g++ -std=c++17 -Isrc test/test_battery_logic.cpp && ./a.out
#include <cstdio>
#include "battery_logic.h"
static int fails = 0;
#define CHECK(c, ...) do { if (!(c)) { printf("FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); fails++; } } while (0)
int main() {
  // a charge from 50 % with the default 80 % limit: on until 80, off, back on at 77
  bool on = true;
  for (float p = 50; p < 79.9f; p += 0.5f) { on = chargeWanted(p, 80, on, true); CHECK(on, "on at %.1f", p); }
  on = chargeWanted(80, 80, on, true); CHECK(!on, "off at 80");
  for (float p = 80; p > 77.1f; p -= 0.5f) { on = chargeWanted(p, 80, on, true); CHECK(!on, "still off at %.1f", p); }
  on = chargeWanted(77, 80, on, true); CHECK(on, "on again at 77");
  // without a gauge, or at 100 %, charging is always left on
  CHECK(chargeWanted(95, 80, false, false), "no gauge: on");
  CHECK(chargeWanted(100, 100, true, true), "limit 100: on");
  CHECK(!chargeWanted(60, 50, true, true), "limit 50 at 60: off");
  printf(fails ? "%d failed\n" : "all battery tests passed\n", fails);
  return fails != 0;
}
