// PC simulator: the ESP32-audioI2S API. Playback is simulated (no sound): a file "plays" for
// its real duration if it is a WAV, otherwise for 3 seconds.
#pragma once
#include "Arduino.h"
#include "LittleFS.h"
class Audio {
 public:
  bool setPinout(int, int, int) { return true; }
  void setVolume(uint8_t v);
  bool connecttoFS(fs::FS& fs, const char* path);
  void stopSong();
  void loop() {}
  bool isRunning();
 private:
  unsigned long start_ = 0, durMs_ = 0;
  bool playing_ = false;
};
