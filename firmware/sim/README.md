# Ceiling Clock PC simulator

Runs the real firmware (`../src/main.cpp`, `settings.cpp`, the alarm logic and the web page) on a Linux or macOS PC, so you can use the clock's web interface without the hardware. The ESP32 parts are replaced by stand-ins in `shim/`:

| On the clock | In the simulator |
| --- | --- |
| Wi-Fi + web server on port 80 | Web server on http://localhost:8080 (`SIM_PORT` to change) |
| LittleFS flash | The folder `sim_fs/` (`SIM_FS_DIR` to change) |
| NTP time | Your computer's clock (you can fast-forward it, see below) |
| LCD, LED, TM1637, LED ring, buttons, light sensor | Simulated; their state is at `/sim/hw` |
| Speaker | Simulated: a sound "plays" for its length, silently |

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

Differences in the browser: files are kept in memory (lost on reload), local time comes from the browser's time zone, and the audio work runs from `loop()` because there are no threads (`SIM_NO_THREADS`).

## Simulator-only controls

| Request | Effect |
| --- | --- |
| `GET /sim/hw` | What the firmware is sending to each piece of hardware (LCD pixels, LED PWM, display segments, ring colours, audio) |
| `POST /sim/time?add=600` | Fast-forward the clock by 600 seconds. Keep steps under 300 s when you want alarms to fire: the firmware treats bigger jumps as a clock correction |
| `POST /sim/button?b=A&ms=150` | Press button A (top) or B (side) for that many milliseconds; `ms=2500` is a long press |
| `POST /sim/ldr?v=300` | Set the light-sensor reading (0–4095) |
| `POST /sim/net?ok=0` | Turn the simulated internet off (`ok=1` on): streams stop and feeds can't be read, so the backup sound rings |
| `POST /sim/streamfail` | Report that the stream couldn't be played (the browser demo sends this when its player fails) |
| `GET /sim/file?path=/sounds/beep.wav` | A sound file's bytes, so the browser demo can play it |

Streams are simulated: the firmware's stream "plays" until it's stopped or the internet goes off. Podcast feeds are really fetched: with `curl` in the PC build, and by the page in the browser build (where the browser only allows feeds from sites that permit it; `docs/demo/sample-feed.xml` always works).

Example: `curl -X POST "localhost:8080/sim/time?add=240"`
