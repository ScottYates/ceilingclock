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

// ---- local time from the browser (wasi-libc has no time zones)
extern "C" WASM_IMPORT(js_local_offset) double js_local_offset(double epochSeconds);   // minutes east of UTC
extern "C" WASM_IMPORT(js_mktime) double js_mktime(int y, int mon, int d, int h, int mi, int s);
extern "C" WASM_IMPORT(js_std_offset) double js_std_offset(double epochSeconds);       // standard-time offset that year

extern "C" struct tm* sim_localtime_r(const time_t* t, struct tm* out) {
  double off = js_local_offset((double)*t);
  time_t shifted = *t + (time_t)(off * 60);
  gmtime_r(&shifted, out);
  out->tm_isdst = off > js_std_offset((double)*t) ? 1 : 0;
  return out;
}
extern "C" time_t sim_mktime(struct tm* tm) {
  time_t r = (time_t)js_mktime(tm->tm_year + 1900, tm->tm_mon, tm->tm_mday, tm->tm_hour, tm->tm_min, tm->tm_sec);
  sim_localtime_r(&r, tm);   // normalise fields and fill in tm_wday / tm_yday like mktime does
  return r;
}

// ---- C++ runtime pieces libc++abi expects (the firmware never throws)
extern "C" void* __cxa_allocate_exception(unsigned long) { abort(); }
extern "C" void __cxa_throw(void*, void*, void (*)(void*)) { abort(); }

// ---- exports
WASM_EXPORT(sim_alloc) void* sim_alloc(int n) { return malloc(n); }
WASM_EXPORT(sim_free) void sim_free(void* p) { free(p); }
WASM_EXPORT(sim_setup) void sim_setup() { setup(); }
WASM_EXPORT(sim_loop) void sim_loop(int n) { while (n-- > 0) loop(); }

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
