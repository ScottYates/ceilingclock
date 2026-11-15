#pragma once
// State that must survive a crash, a watchdog reset or a restart (not a power cut): the last known time,
// the last alarm check, which occurrence of each alarm has rung, and an alarm that is ringing or snoozed.
// On the ESP32 it lives in RTC memory that a reset leaves alone; the simulator keeps it in a file.
// A checksum tells intact contents from leftovers after power-on.
#include <stdint.h>
#include <stddef.h>
#include <time.h>
#include "settings.h"

struct Persist {
  uint32_t magic;
  time_t clock;                     // last known valid time (0 = none)
  time_t lastCheck;                 // alarms were checked up to here
  time_t lastFiredAt[MAX_ALARMS];   // the occurrence each alarm last rang for
  uint8_t ringState;                // RingState of the ringing/snoozed alarm
  int8_t ringAlarm;
  time_t ringStart, snoozeUntil;
  uint8_t useBeep;                  // the alarm's own sound failed: ring with the built-in beep
  uint8_t restarts;                 // restarts made to unstick the sound during this ring
  uint32_t crc;
};

constexpr uint32_t PERSIST_MAGIC = 0xC10CA1A5;

inline uint32_t persistCrc(const Persist& p) {
  const uint8_t* b = (const uint8_t*)&p;
  uint32_t h = 2166136261u;
  for (size_t i = 0; i < offsetof(Persist, crc); i++) h = (h ^ b[i]) * 16777619u;
  return h;
}

extern Persist persist;
bool persistLoad();   // true if the contents survived a reset intact (false after power-on: then cleared)
void persistSave();   // updates the checksum and keeps it (cheap on the ESP32; the simulator writes a file on change)
