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
// Where the firmware looks for the DS3231 if it isn't on pins 1 and 2: the only two free pins on the ESP32's
// front edge, the side that keeps free holes when the ESP32 is on one breadboard. GPIO 3 is a strapping pin,
// but only with an eFuse that is off from the factory, and the module's pull-ups would hold it at the
// default level anyway.
#define PIN_SDA_ALT   18
#define PIN_SCL_ALT    3

// Buttons (to GND, internal pull-ups)
#define PIN_BTN_A      6   // top: snooze / hold = stop; when quiet: show the time and which alarms are on
#define PIN_BTN_B     14   // back: front display on/off, hold 3 s = projector on/off, hold 10 s = Wi-Fi reset

// Alarm buttons: 16 mm momentary buttons with an LED inside (red or green), for example Adafruit 1440.
// Button to GND (internal pull-up); LED pin -> 220 ohm -> LED +, LED - to GND (about 5 mA). Buttons sold with
// a built-in resistor for 3-6 V go straight to the pin. The lights only come on
// briefly: after a press, when you press snooze to check, and while that alarm rings.
#define PIN_BTN_AL1    8   // alarm 1 on/off
#define PIN_BTN_AL2    9   // alarm 2 on/off
#define PIN_LED_AL1   10
#define PIN_LED_AL2   13

// Light sensor: LDR from 3.3V to this pin, 10k from this pin to GND
#define PIN_LDR        7
