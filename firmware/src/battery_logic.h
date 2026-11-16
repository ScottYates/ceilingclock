#pragma once
// Charge limit for the battery base. Charging stops at the limit and starts again 3 points below it, so the
// charger isn't switched on and off all the time. Without a working fuel gauge, or with the limit at 100 %,
// charging is left on: the charger then stops by itself at 4.2 V (full), which is always safe.
inline bool chargeWanted(float soc, int limit, bool chargingNow, bool gaugeOk) {
  if (!gaugeOk || limit >= 100) return true;
  if (chargingNow) return soc < limit;
  return soc <= limit - 3;
}
