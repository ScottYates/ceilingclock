// PC simulator: the ESP32-audioI2S API. Playback is simulated: a file "plays" for its real
// duration if it is a WAV, otherwise for 3 seconds; a stream plays until stopped, the
// simulated internet goes off (/sim/net?ok=0) or the demo page reports it can't play it.
#pragma once
#include "Arduino.h"
#include "LittleFS.h"
#include <functional>
class Audio {
 public:
  typedef enum { evt_info = 0, evt_id3data, evt_eof, evt_name, evt_icydescription, evt_streamtitle } event_t;
  typedef struct _msg { const char* msg = nullptr; const char* s = nullptr; event_t e = evt_info; } msg_t;
  inline static std::function<void(msg_t i)> audio_info_callback;
  bool setPinout(int, int, int) { return true; }
  void setVolume(uint8_t v);
  bool connecttoFS(fs::FS& fs, const char* path);
  bool connecttohost(const char* url, const char* user = nullptr, const char* pwd = nullptr);
  void stopSong();
  void loop() {}
  bool isRunning();
 private:
  unsigned long start_ = 0, durMs_ = 0;
  bool playing_ = false, streaming_ = false;
};
