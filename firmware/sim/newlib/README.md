# newlib date code (from the ESP32's C library)

Unchanged copies of newlib's time sources, so the simulator and the PC tests work out local time exactly as
the clock does (see `../README.md`). They come from Espressif's newlib, https://github.com/espressif/newlib-esp32,
branch `esp-4.3.0` (commit d16a927c7334602a563893fa53b3746afdd31c0d), `newlib/libc/time/` and
`newlib/libc/include/sys/_tz_structs.h`. That is newlib 4.3.0, the version in the esp-14.2.0 toolchain that
PlatformIO uses to build the firmware (`_NEWLIB_VERSION` in its headers). Licences: `COPYING.NEWLIB`.

Glue for the PC, not from newlib: `compat/` (stand-ins for `<_ansi.h>` and `<reent.h>`), `nl_rename.h` (gives
newlib's internal names an `nl_` prefix), `nl_lock.c` (the time-zone lock) and `Makefile`.
