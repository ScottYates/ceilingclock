#pragma once
// Pin map for ESP32-S3-DevKitC-1. Change here if you wire differently.
// Avoided: 0/3/45/46 (strapping), 19/20 (USB), 26-37 (flash/PSRAM), 38/48 (onboard RGB LED).

// Projector: a second TM1637 4-digit 7-segment module, imaged onto the ceiling
#define PIN_PROJ_CLK  12
#define PIN_PROJ_DIO  11

// Front display: TM1637 4-digit 7-segment
#define PIN_TM_CLK     4
#define PIN_TM_DIO     5

// Audio: MAX98357A I2S amplifier
#define PIN_I2S_BCLK  15
#define PIN_I2S_LRC   16
#define PIN_I2S_DOUT  17

// DS3231 real-time clock (I2C)
#define PIN_SDA        1
#define PIN_SCL        2

// Buttons (to GND, internal pull-ups)
#define PIN_BTN_A      6   // top: snooze / hold = dismiss / peek
#define PIN_BTN_B     14   // back: front display on/off, hold 3 s = projector on/off, hold 10 s = Wi-Fi reset

// Light sensor: LDR from 3.3V to this pin, 10k from this pin to GND
#define PIN_LDR        7
