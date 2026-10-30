// PC simulator entry point: runs the firmware's setup() once and loop() forever, like the ESP32 core.
#include "Arduino.h"
#include <csignal>
void setup();
void loop();
int main() {
  setvbuf(stdout, nullptr, _IOLBF, 0);
  signal(SIGPIPE, SIG_IGN);   // a browser closing a connection must not kill the simulator
  printf("[sim] Ceiling Clock firmware simulator (hardware is simulated; see /sim/hw)\n");
  setup();
  for (;;) loop();
}
