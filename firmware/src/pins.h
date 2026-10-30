#pragma once
// Pin map for ESP32-S3-DevKitC-1. Change here if you wire differently.
// Avoided: 0/3/45/46 (strapping), 19/20 (USB), 26-37 (flash/PSRAM), 38/48 (onboard RGB LED).

// Projector LCD: Nokia 5110 (PCD8544), software SPI
#define PIN_LCD_CLK   12
#define PIN_LCD_DIN   11
#define PIN_LCD_DC     9
#define PIN_LCD_CE    10
#define PIN_LCD_RST    8

// Projector LED: PWM into the gate of a logic-level MOSFET module
#define PIN_PROJ_LED  13

// Front display: TM1637 4-digit 7-segment
#define PIN_TM_CLK     4
#define PIN_TM_DIO     5

// Audio: MAX98357A I2S amplifier
#define PIN_I2S_BCLK  15
#define PIN_I2S_LRC   16
#define PIN_I2S_DOUT  17

// Sunrise light: WS2812B ring
#define PIN_RING      18
#define RING_COUNT    16

// DS3231 real-time clock (I2C)
#define PIN_SDA        1
#define PIN_SCL        2

// Buttons (to GND, internal pull-ups)
#define PIN_BTN_A      6   // top: snooze / hold = dismiss / peek
#define PIN_BTN_B     14   // back: front display on/off, hold 3 s = projector on/off, hold 10 s = Wi-Fi reset

// Light sensor: LDR from 3.3V to this pin, 10k from this pin to GND
#define PIN_LDR        7
