// Every mesh in models/clock.glb, with display info.
// explode: [x, y, z] offset in mm (model coordinates, z up) at full explode.
export const PARTS = {
  base:          { label: 'Base',                   kind: 'print', color: 0x39404a, explode: [0, 0, 0] },
  lid:           { label: 'Lid',                    kind: 'print', color: 0x55606e, explode: [0, 0, 70] },
  tower:         { label: 'Projector tower',        kind: 'print', color: 0x2d323a, explode: [0, 0, 150] },
  carrier:       { label: 'Optics carrier',         kind: 'print', color: 0xe8743b, explode: [0, 0, 105] },
  sleeve:        { label: 'Lens sleeve',            kind: 'print', color: 0x8f99a6, explode: [0, 0, 235] },
  lens_cap:      { label: 'Lens cap',               kind: 'print', color: 0xe8743b, explode: [0, 0, 270] },
  ring_holder:   { label: 'Sunrise ring holder',    kind: 'print', color: 0x8f99a6, explode: [0, 0, 85] },
  dome:          { label: 'Diffuser dome',          kind: 'print', color: 0xf4f1ea, explode: [0, 0, 125], opacity: 0.7 },
  ref_perfboard: { label: 'Perfboard',              kind: 'part',  color: 0x2f8f5b, explode: [0, 0, 18] },
  ref_esp32:     { label: 'ESP32-S3 board',         kind: 'part',  color: 0x1f4e8c, explode: [0, 0, 32] },
  ref_amp:       { label: 'MAX98357A amplifier',    kind: 'part',  color: 0x7b3fa0, explode: [0, 0, 14] },
  ref_rtc:       { label: 'DS3231 clock module',    kind: 'part',  color: 0x1f4e8c, explode: [0, 0, 14] },
  ref_mosfet:    { label: 'MOSFET module',          kind: 'part',  color: 0x2a6f9e, explode: [0, 0, 14] },
  ref_speaker:   { label: 'Speaker',                kind: 'part',  color: 0x3b3b3b, explode: [0, 0, 30] },
  ref_tm1637:    { label: 'TM1637 front display',   kind: 'part',  color: 0xc0392b, explode: [0, -30, 0] },
  ref_usbc:      { label: 'USB-C power breakout',   kind: 'part',  color: 0x2a6f9e, explode: [0, 30, 0] },
  ref_button:    { label: 'Snooze button',          kind: 'part',  color: 0xb8bec6, explode: [0, 0, 95] },
  ref_led:       { label: '3 W LED on star',        kind: 'part',  color: 0xf2c94c, explode: [0, 0, 70] },
  ref_lcd:       { label: 'Nokia 5110 LCD',         kind: 'part',  color: 0xb03030, explode: [0, 0, 150] },
  ref_lens:      { label: '50 mm lens (f = 100)',   kind: 'part',  color: 0x9fd3ff, explode: [0, 0, 255], opacity: 0.55 },
  ref_ring:      { label: 'WS2812B 16-LED ring',    kind: 'part',  color: 0x111111, explode: [0, 0, 100] },
};

export const ALL = Object.keys(PARTS);
