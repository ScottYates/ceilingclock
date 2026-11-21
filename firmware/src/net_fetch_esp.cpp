// netFetch() on the ESP32 (see net_fetch.h).
#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include "net_fetch.h"

bool netFetch(const char* url, std::string& contentType, const std::function<bool(const char*, size_t)>& sink) {
  if (WiFi.status() != WL_CONNECTED) return false;
  bool https = strncmp(url, "https://", 8) == 0;
  WiFiClientSecure secure;
  WiFiClient plain;
  if (https) secure.setInsecure();  // no certificate store on the clock; podcast feeds are public
  HTTPClient http;
  http.setFollowRedirects(HTTPC_FORCE_FOLLOW_REDIRECTS);   // podcast hosts redirect through trackers
  http.setRedirectLimit(6);
  http.setConnectTimeout(8000);
  http.setTimeout(8000);
  http.setUserAgent("CeilingClock/1.0");
  const char* keys[] = {"Content-Type"};
  http.collectHeaders(keys, 1);
  if (!(https ? http.begin(secure, url) : http.begin(plain, url))) return false;
  int code = http.GET();
  if (code != HTTP_CODE_OK) { http.end(); return false; }
  contentType = http.header("Content-Type").c_str();
  // writeToStream() undoes chunked transfer encoding (most podcast hosts send feeds chunked); reading the
  // raw socket would mix the chunk-size lines into the XML.
  struct Sink : public Stream {
    const std::function<bool(const char*, size_t)>& fn;
    bool stopped = false;
    explicit Sink(const std::function<bool(const char*, size_t)>& f) : fn(f) {}
    size_t write(const uint8_t* b, size_t n) override {
      if (stopped) return 0;
      if (!fn((const char*)b, n)) { stopped = true; return 0; }   // enough read: a short write ends the transfer
      return n;
    }
    size_t write(uint8_t c) override { return write(&c, 1); }
    int available() override { return 0; }
    int read() override { return -1; }
    int peek() override { return -1; }
    void flush() override {}
  } sink_(sink);
  int r = http.writeToStream(&sink_);
  http.end();
  return r >= 0 || sink_.stopped;
}
