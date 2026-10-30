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
  http.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);
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
  WiFiClient* s = http.getStreamPtr();
  int left = http.getSize();  // -1 = unknown length
  char buf[1024];
  uint32_t last = millis();
  while (http.connected() && left != 0 && millis() - last < 8000) {
    int n = s->available();
    if (n <= 0) { delay(5); continue; }
    n = s->readBytes(buf, n < (int)sizeof buf ? n : (int)sizeof buf);
    if (n <= 0) continue;
    last = millis();
    if (left > 0) left -= n;
    if (!sink(buf, n)) break;
  }
  http.end();
  return true;
}
