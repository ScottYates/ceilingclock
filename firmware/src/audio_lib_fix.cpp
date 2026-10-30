// ESP32-audioI2S 4.0.x declares these two Decoder virtuals but never defines them, which leaves
// the Decoder vtable undefined at link time. Every real decoder overrides both, so these
// defaults are never called; they only exist so the linker can emit the vtable.
#ifndef NATIVE_SIM
#include "Audio.h"
const char* Decoder::getStreamTitle() { return nullptr; }
const char* Decoder::whoIsIt() { return ""; }
#endif
