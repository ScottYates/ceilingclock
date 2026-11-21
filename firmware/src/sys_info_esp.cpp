// sysInfoRead() on the ESP32 (see sys_info.h).
#include <Arduino.h>
#include <esp_heap_caps.h>
#include <esp_system.h>
#include <esp_timer.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include "sys_info.h"

static const char* resetText(esp_reset_reason_t r) {
  switch (r) {
    case ESP_RST_POWERON: return "power on";
    case ESP_RST_EXT: return "reset button";
    case ESP_RST_SW: return "restarted by the clock (update, settings or recovery)";
    case ESP_RST_PANIC: return "crash";
    case ESP_RST_INT_WDT: case ESP_RST_TASK_WDT: case ESP_RST_WDT: return "watchdog (something hung)";
    case ESP_RST_BROWNOUT: return "power dipped too low";
    case ESP_RST_DEEPSLEEP: return "woke from sleep";
    case ESP_RST_USB: return "USB reset";
    default: return "unknown";
  }
}

// Processor load comes from how long each core's idle task ran since the previous reading (FreeRTOS
// run-time stats, counted in microseconds, 32-bit: readings more than an hour apart start over).
void sysInfoRead(SysInfo& s) {
  static uint32_t prevIdle[2] = {0, 0}, prevUs = 0;
  static bool havePrev = false;

  s.upSec = (uint32_t)(esp_timer_get_time() / 1000000);
  s.reset = resetText(esp_reset_reason());
  s.mhz = getCpuFrequencyMhz();
  s.tempC = temperatureRead();

  UBaseType_t room = uxTaskGetNumberOfTasks() + 4;
  TaskStatus_t* ts = (TaskStatus_t*)malloc(sizeof(TaskStatus_t) * room);
  if (ts) {
    uint32_t us = (uint32_t)esp_timer_get_time();
    UBaseType_t n = uxTaskGetSystemState(ts, room, nullptr);
    s.tasks = n;
    uint32_t idle[2] = {0, 0};
    for (UBaseType_t i = 0; i < n; i++)
      for (int c = 0; c < 2; c++)
        if (ts[i].xHandle == xTaskGetIdleTaskHandleForCore(c)) idle[c] = ts[i].ulRunTimeCounter;
    free(ts);
    uint32_t dt = us - prevUs;
    if (havePrev && dt > 200000 && dt < 3600000000UL) {
      for (int c = 0; c < 2; c++) {
        float busy = 100.0f - (float)(idle[c] - prevIdle[c]) * 100.0f / dt;
        s.cpu[c] = (int8_t)constrain((int)(busy + 0.5f), 0, 100);
      }
    }
    prevIdle[0] = idle[0]; prevIdle[1] = idle[1]; prevUs = us; havePrev = true;
  }

  s.heapFree = heap_caps_get_free_size(MALLOC_CAP_INTERNAL);
  s.heapTotal = heap_caps_get_total_size(MALLOC_CAP_INTERNAL);
  s.heapMin = heap_caps_get_minimum_free_size(MALLOC_CAP_INTERNAL);
  s.heapBig = heap_caps_get_largest_free_block(MALLOC_CAP_INTERNAL);
  s.psFree = heap_caps_get_free_size(MALLOC_CAP_SPIRAM);
  s.psTotal = heap_caps_get_total_size(MALLOC_CAP_SPIRAM);
  s.psMin = heap_caps_get_minimum_free_size(MALLOC_CAP_SPIRAM);
  s.appUsed = ESP.getSketchSize();
  s.appSlot = ESP.getFreeSketchSpace();
}
