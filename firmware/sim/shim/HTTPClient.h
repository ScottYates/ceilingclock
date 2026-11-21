// PC simulator: the ESP32 HTTPClient, enough of it for the firmware's net_fetch_esp.cpp. GET() fetches the
// whole response (curl on the PC, the page's own request in the browser build; at most 512 KB, so a radio
// stream isn't downloaded forever) and only while the simulated Wi-Fi and internet are up.
#pragma once
#include "Arduino.h"
#include "WiFiClientSecure.h"
#include <map>
#define HTTP_CODE_OK 200
typedef enum { HTTPC_DISABLE_FOLLOW_REDIRECTS, HTTPC_STRICT_FOLLOW_REDIRECTS, HTTPC_FORCE_FOLLOW_REDIRECTS } followRedirects_t;
class HTTPClient {
 public:
  void setFollowRedirects(followRedirects_t f) { follow_ = f != HTTPC_DISABLE_FOLLOW_REDIRECTS; }
  void setRedirectLimit(uint16_t n) { redirects_ = n; }
  void setConnectTimeout(int32_t ms) { connectMs_ = ms; }
  void setTimeout(uint16_t ms) { timeoutMs_ = ms; }
  void setUserAgent(const String& ua) { ua_ = ua.c_str(); }
  void collectHeaders(const char* keys[], size_t n) { for (size_t i = 0; i < n; i++) want_.push_back(keys[i]); }
  bool begin(WiFiClient& client, const String& url) { client_ = &client; url_ = url.c_str(); return url_.rfind("http", 0) == 0; }
  int GET();
  String header(const char* name);
  WiFiClient* getStreamPtr() { return client_; }
  // Hands the body to a Stream in pieces, as the ESP32 one does (it also undoes chunked encoding, which the
  // simulator's fetch has already done). A short write ends it with HTTPC_ERROR_STREAM_WRITE (-10).
  int writeToStream(Stream* s) {
    if (!client_) return -1;
    char b[1024]; int total = 0;
    while (client_->available() > 0) {
      size_t n = client_->readBytes(b, sizeof b);
      if (!n) break;
      if (s->write((const uint8_t*)b, n) != n) return -10;
      total += (int)n;
    }
    return total;
  }
  int getSize() { return size_; }
  bool connected() { return client_ && client_->connected(); }
  void end() {}
 private:
  WiFiClient* client_ = nullptr;
  std::string url_, ua_ = "ESP32HTTPClient";
  bool follow_ = false;
  int redirects_ = 10, connectMs_ = 5000, timeoutMs_ = 5000, size_ = -1;
  std::vector<std::string> want_;
  std::map<std::string, std::string> headers_;   // lower-case names
};
