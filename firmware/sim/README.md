# Ceiling Clock PC simulator

Runs the real firmware on a Linux or macOS PC, so you can use the clock's web interface and test it without the hardware. Every file in `../src` is compiled exactly as it is for the clock: the firmware has no simulator-only code, and `make` refuses to build if any creeps in (`make check-src`). What differs is underneath it: the ESP32 hardware and libraries are replaced by stand-ins in `shim/`, implemented in `sim_hw.cpp`:

| On the clock | In the simulator |
| --- | --- |
| Wi-Fi + web server on port 80 | Web server on http://localhost:8080 (`SIM_PORT` to change) |
| LittleFS flash | The folder `sim_fs/` (`SIM_FS_DIR` to change) |
| NTP time | Your computer's clock (you can fast-forward it, see below) |
| Both TM1637 displays, buttons, light sensor | Simulated; their state is at `/sim/hw` |
| Speaker | Simulated: a sound "plays" for its length, silently, and passes stand-in samples to the firmware's sample hooks (`audio_process_i2s`), which its sound watchdog counts |
| Date and time functions (newlib) | The same newlib code, see below |
| RTC memory (`RTC_NOINIT_ATTR`) and the reset reason | Written to `sim_fs/.rtcmem` when the clock resets; read back when it starts with `SIM_RESET=warm`. A power-on fills it with random bytes, as on the chip |
| Task watchdog (30 s) | A thread that resets the simulated clock if `loop()` stops feeding it |
| HTTPClient (podcast feeds) | `curl` |

## Same date code as the clock

Local time, daylight saving included, is worked out by the C library's `mktime`, `localtime_r` and `tzset`. The PC's own (glibc) doesn't always agree with the ESP32's (newlib): in the hour that happens twice when daylight saving ends, newlib always takes the second, while glibc's answer depends on earlier calls. So the simulator uses the ESP32's. `newlib/` holds the unchanged time sources from Espressif's newlib (branch `esp-4.3.0`, newlib 4.3.0, the C library in the esp-14.2.0 toolchain that builds the firmware), plus a few lines of glue for the PC. `newlib/Makefile` builds them into `libnltime.a`; linked into a program, its functions replace the PC's for every call. The browser build compiles the same files. `../test/test_alarm_schedule.cpp` links them too, and checks newlib against the PC's library on 737,856 local times.

## Build and run

```
cd firmware
pio pkg install        # once, downloads ArduinoJson used by the simulator too
cd sim
make run
```

Then open http://localhost:8080/. On Windows, use WSL.

## Browser build (live demo)

`make wasm` compiles the same firmware to WebAssembly with the system clang, using Ubuntu's wasm32 libraries (`apt install wasi-libc libc++-18-dev-wasm32 libc++abi-18-dev-wasm32 libclang-rt-18-dev-wasm32`). It writes `docs/demo/ceilingclock.wasm` and regenerates `docs/demo/index.html` from `src/web_ui.h`. `docs/demo/sim.js` runs the firmware in the page and answers the page's `/api/...` requests from it.

Differences in the browser: files are kept in memory (lost on reload), and there are no threads, so `sim_wasm.cpp` runs the audio task's work (`audioInit()`, then `audioStep()` after every `loop()`) instead of a separate task, and there is no task watchdog. The demo sets the clock's time zone to the visitor's at start; from then on the firmware works out local time itself, as on the clock.

## Simulator-only controls

| Request | Effect |
| --- | --- |
| `GET /sim/hw` | What the firmware is sending to each piece of hardware (each display's on/off, brightness and segments, audio) |
| `POST /sim/time?add=600` | Fast-forward the clock by 600 seconds (`set=<epoch>` jumps to a time). An alarm in a step of up to 30 minutes still rings |
| `POST /sim/button?b=A&ms=150` | Press button A (snooze), B (side), 1 or 2 (alarm buttons) for that many milliseconds; `ms=2500` is a long press. `/sim/hw` shows the alarm buttons' lights in `alarmLeds` |
| `POST /sim/ldr?v=300` | Set the light-sensor reading (0–4095) |
| `POST /sim/net?ok=0` | Turn the simulated internet off (`ok=1` on): streams stop and feeds can't be read, so the backup sound rings |
| `POST /sim/wifi?up=0` | Take the router down (`up=1` back up). The clock rejoins by itself |
| `POST /sim/ntp` | Answer a time sync now (if on Wi-Fi with internet) |
| `POST /sim/clockerror?sec=-1200` | Make the clock's own time wrong by that many seconds; the next sync corrects it |
| `POST /sim/audiofail?path=/sounds/x.mp3&mode=fail` | Make a sound go wrong: `fail` (won't open), `stall` (no sound comes out), `hang` (the audio task freezes), `ok`. `path=*` for all files, `path=stream` for streams |
| `POST /sim/crash` | Simulate a crash: the process exits; start it again with `SIM_RESET=warm` |
| `POST /sim/hang` | `loop()` stops coming back: the task watchdog resets the clock after 30 s |
| `GET /sim/clock` | The clock's own time, the real time, Wi-Fi and setup-portal state |
| `POST /sim/streamfail` | Report that the stream couldn't be played (the browser demo sends this when its player fails) |
| `GET /sim/file?path=/sounds/beep.wav` | A sound file's bytes, so the browser demo can play it |

Environment: `SIM_RTC=1` fits a DS3231; `SIM_WIFI=0` starts with the router down (`SIM_WIFI_UP_AFTER=N` brings it up after N s); `SIM_NET=0` without internet; `SIM_RESET=warm` starts as after a reset (the state kept in RTC memory survives), otherwise as after power-on, when the clock's time is unknown until a sync or the DS3231; `SIM_FAST_PORTAL=1` closes the setup portal after 3 s. The simulated world's time is kept in `.worldtime` in the storage folder, so it carries on across restarts.

Streams are simulated: the firmware's stream "plays" until it's stopped or the internet goes off. Podcast feeds are really fetched, through the firmware's own `net_fetch_esp.cpp`: by the `HTTPClient` stand-in with `curl` in the PC build, and by the page in the browser build (where the browser only allows feeds from sites that permit it; `docs/demo/sample-feed.xml` always works).

Example: `curl -X POST "localhost:8080/sim/time?add=240"`
