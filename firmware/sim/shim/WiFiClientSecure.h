// PC simulator: network clients for HTTPClient (see HTTPClient.h). The simulator fetches a whole response
// up front; a client then hands its body out like a socket would.
#pragma once
#include "Arduino.h"
#include <string>
class WiFiClient {
 public:
  virtual ~WiFiClient() = default;
  int available() { return (int)(body_.size() - pos_); }
  size_t readBytes(char* buf, size_t n) {
    n = std::min(n, body_.size() - pos_);
    memcpy(buf, body_.data() + pos_, n); pos_ += n;
    return n;
  }
  bool connected() { return pos_ < body_.size(); }
  void simSetBody(std::string b) { body_ = std::move(b); pos_ = 0; }
 private:
  std::string body_;
  size_t pos_ = 0;
};
class WiFiClientSecure : public WiFiClient {
 public:
  void setInsecure() {}
};
