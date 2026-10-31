# Ceiling Clock

A Wi-Fi ceiling projection alarm clock built on an ESP32-S3.

**Project site (3D model, assembly, wiring, parts list with Amazon links):** https://scottyates.github.io/ceilingclock/

- Keeps time from internet time servers (NTP), with a DS3231 battery-backed clock for outages.
- Projects the time onto the ceiling through a Nokia 5110 LCD lit by a 3 W LED. The LCD, a 45° mirror and the lens ride in a barrel along the back of the clock, so the clock is only about 10 cm tall, and rolling the barrel aims the time up to about 1 m forward on the ceiling.
- Front 4-digit display that can be switched completely off.
- Up to 8 alarms with per-alarm days, sound, volume fade-in, snooze, and sunrise light.
- Upload your own MP3/WAV alarm sounds, or wake to an internet radio stream or the newest episode of a podcast (with a sound file as backup if the stream won't play), and change every setting from a phone at `http://ceilingclock.local/`.

## Repository layout

| Folder | Contents |
| --- | --- |
| `firmware/` | PlatformIO project for the ESP32-S3 |
| `hardware/` | OpenSCAD enclosure source (`enclosure.scad`), printable STLs (`stl/`), wiring diagram generator. The case needs no screws: printed quarter-turn lock pins (the same as the VoiceLabels case) and clips hold it together. |
| `docs/` | Project website: 3D assembly viewer, build steps, wiring, breadboard test guide, parts list |

## Prebuilt firmware

`docs/downloads/ceilingclock-esp32s3-factory.bin` is a complete image for a first flash at address 0x0 (for example with https://espressif.github.io/esptool-js/). `ceilingclock-esp32s3-update.bin` is for the web page's firmware update.

## Try it without hardware

Live demo in the browser: https://scottyates.github.io/ceilingclock/demo/ (the real firmware compiled to WebAssembly). `firmware/sim/` also builds it as a Linux or Mac program. See its README.

## Build the firmware

1. Install VS Code and the PlatformIO IDE extension.
2. Open the `firmware/` folder and click Upload with the board connected over USB.
3. On first boot, join the `CeilingClock-Setup` Wi-Fi network from your phone and choose your home network.
4. Open `http://ceilingclock.local/` to set alarms.

The alarm scheduling logic has unit tests that run on a PC:

```
g++ -std=c++17 -Ifirmware/src firmware/test/test_alarm_logic.cpp && ./a.out
g++ -std=c++17 -Ifirmware/src firmware/test/test_feed_scan.cpp && ./a.out
```

## Rebuild the 3D files

```
cd hardware
for p in base lid barrel lcd_holder led_cap lens_mount sleeve lens_cap ring_holder dome pins; do
  openscad -D "part=\"$p\"" -D print=true -o stl/$p.stl enclosure.scad
done
```

For a 0.56" front display, add `-D 'tm_size="0.56"'` when exporting the base (the repo includes `stl/base_056.stl`).

The web viewer loads `docs/models/clock.glb`, which holds every part in its assembled position. Rebuild it with `python3 hardware/export_viewer_model.py` (needs openscad and trimesh); bought components are modelled in `hardware/components.scad`, one mesh per material.
