// Browser build of the simulator: the firmware compiled to WebAssembly.
// The page (docs/demo/sim.js) calls these exports: sim_setup() once, sim_loop() on a timer,
// and sim_request() for every fetch() the firmware's web page makes.
#ifdef SIM_WASM
#include "Arduino.h"
#include "WebServer.h"

#define WASM_EXPORT(name) extern "C" __attribute__((export_name(#name)))
#define WASM_IMPORT(name) __attribute__((import_module("env"), import_name(#name)))

extern WebServer server;   // the firmware's server object (main.cpp)
void setup();
void loop();
void audioInit();   // main.cpp: what its audio task runs. The browser has no threads, so the task isn't
void audioStep();   // started (the shim's xTaskCreatePinnedToCore does nothing) and its work runs from here.

// ---- C++ runtime pieces libc++abi expects (the firmware never throws)
extern "C" void* __cxa_allocate_exception(unsigned long) { abort(); }
extern "C" void __cxa_throw(void*, void*, void (*)(void*)) { abort(); }

// ---- exports
WASM_EXPORT(sim_alloc) void* sim_alloc(int n) { return malloc(n); }
WASM_EXPORT(sim_free) void sim_free(void* p) { free(p); }
WASM_EXPORT(sim_setup) void sim_setup() { sim::powerOn(); setup(); audioInit(); }
WASM_EXPORT(sim_loop) void sim_loop(int n) { while (n-- > 0) { loop(); audioStep(); } }

// Runs one HTTP request. Strings are NUL-terminated; body is binary (len bytes).
WASM_EXPORT(sim_request) int sim_request(const char* method, const char* target, const char* ctype,
                                         const char* body, int len, const char* auth) {
  server.handleRequest(method, target, ctype ? ctype : "", std::string(body ? body : "", len), auth ? auth : "");
  return server.respCode;
}
WASM_EXPORT(sim_resp_type) const char* sim_resp_type() { return server.respType.c_str(); }
WASM_EXPORT(sim_resp_body) const char* sim_resp_body() { return server.respBody.data(); }
WASM_EXPORT(sim_resp_len) int sim_resp_len() { return (int)server.respBody.size(); }
#endif
