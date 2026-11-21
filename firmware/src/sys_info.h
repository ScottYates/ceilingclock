// Readings for the System section of the settings page (/api/sys): processor load, memory and
// firmware space. In sys_info_esp.cpp on the clock; the simulator supplies its own.
#pragma once
#include <cstdint>

struct SysInfo {
  uint32_t upSec = 0;          // since the last restart
  const char* reset = "";      // why it last restarted, in words
  int8_t cpu[2] = {-1, -1};    // percent busy per core since the last reading, -1 until there are two readings
  uint16_t mhz = 0;
  float tempC = 0;             // the chip's own sensor (runs warmer than the room)
  uint16_t tasks = 0;
  uint32_t heapFree = 0, heapTotal = 0, heapMin = 0, heapBig = 0;   // internal RAM; min = lowest since restart
  uint32_t psFree = 0, psTotal = 0, psMin = 0;                      // PSRAM
  uint32_t appUsed = 0, appSlot = 0;                                // this firmware, and the space an update can use
};

void sysInfoRead(SysInfo& s);
