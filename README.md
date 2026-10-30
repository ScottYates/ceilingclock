# Ceiling Clock

A Wi-Fi ceiling projection alarm clock built on an ESP32-S3.

**Project site (3D model, assembly, wiring, parts list with Amazon links):** https://scottyates.github.io/ceilingclock/

- Keeps time from internet time servers (NTP), with a DS3231 battery-backed clock for outages.
- Projects the time onto the ceiling through a Nokia 5110 LCD lit by a 1 W LED and a 50 mm lens.
- Front 4-digit display that can be switched completely off.
- Up to 8 alarms with per-alarm days, sound, volume fade-in, snooze, and sunrise light.
- Upload your own MP3/WAV alarm sounds and change every setting from a phone at `http://ceilingclock.local/`.

## Repository layout

| Folder | Contents |
| --- | --- |
| `firmware/` | PlatformIO project for the ESP32-S3 |
| `hardware/` | OpenSCAD enclosure source (`enclosure.scad`), printable STLs (`stl/`), wiring diagram generator |
| `docs/` | Project website: 3D assembly viewer, build steps, wiring, parts list |

## Build the firmware

1. Install VS Code and the PlatformIO IDE extension.
2. Open the `firmware/` folder and click Upload with the board connected over USB.
3. On first boot, join the `CeilingClock-Setup` Wi-Fi network from your phone and choose your home network.
4. Open `http://ceilingclock.local/` to set alarms.

The alarm scheduling logic has unit tests that run on a PC:

```
g++ -std=c++17 -Ifirmware/src firmware/test/test_alarm_logic.cpp && ./a.out
```

## Rebuild the 3D files

```
cd hardware
for p in base lid tower carrier sleeve lens_cap ring_holder dome; do
  openscad -D "part=\"$p\"" -D print=true -o stl/$p.stl enclosure.scad
done
```

For a 0.56" front display, add `-D 'tm_size="0.56"'` when exporting the base (the repo includes `stl/base_056.stl`).

The web viewer loads `docs/models/clock.glb`, which holds every part in its assembled position.
