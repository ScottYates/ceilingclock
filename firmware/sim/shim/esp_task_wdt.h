// PC simulator: the ESP32 task watchdog. If the subscribed task (the firmware's loop) stops calling
// esp_task_wdt_reset() for the configured time, the simulated clock resets, as the real one does
// (with trigger_panic). Not modelled in the browser build, which has no threads to watch with.
#pragma once
#include "Arduino.h"
typedef struct {
  uint32_t timeout_ms;
  uint32_t idle_core_mask;
  bool trigger_panic;
} esp_task_wdt_config_t;
esp_err_t esp_task_wdt_init(const esp_task_wdt_config_t* config);
esp_err_t esp_task_wdt_reconfigure(const esp_task_wdt_config_t* config);
esp_err_t esp_task_wdt_add(TaskHandle_t task);
esp_err_t esp_task_wdt_reset(void);
