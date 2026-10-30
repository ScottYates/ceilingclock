// PC simulator: a small single-threaded HTTP/1.0 server with the ESP32 WebServer API.
// Paths under /sim/ are handled by the simulator itself (hardware state, time travel, buttons).
#pragma once
#include "Arduino.h"
#include <map>

enum HTTPMethod { HTTP_ANY = 0, HTTP_GET = 1, HTTP_POST = 2 };
enum { UPLOAD_FILE_START, UPLOAD_FILE_WRITE, UPLOAD_FILE_END, UPLOAD_FILE_ABORTED };
struct HTTPUpload {
  int status = 0;
  String filename;
  uint8_t buf[2048];
  size_t currentSize = 0;
};

class WebServer {
 public:
  typedef std::function<void()> Handler;
  explicit WebServer(int port) : port_(port) {}
  void on(const char* uri, HTTPMethod m, Handler h) { routes_.push_back({uri, m, h, nullptr}); }
  void on(const char* uri, HTTPMethod m, Handler h, Handler up) { routes_.push_back({uri, m, h, up}); }
  void onNotFound(Handler h) { notFound_ = h; }
  void begin();
  void handleClient();
  void send(int code, const char* type, const String& body);
  void send(int code, const char* type, const char* body) { send(code, type, String(body)); }
  void send_P(int code, const char* type, const char* body) { send(code, type, String(body)); }
  String arg(const char* name);
  bool hasArg(const char* name) { return args_.count(name) > 0; }
  bool authenticate(const char* user, const char* pass);
  void requestAuthentication();
  HTTPUpload& upload() { return upload_; }

  // Runs one request through the firmware's handlers. The response is captured in resp*
  // (used by the browser build, where there are no sockets).
  void handleRequest(const std::string& method, const std::string& target, const std::string& ctype,
                     const std::string& body, const std::string& auth = "");
  int respCode = 0;
  std::string respType, respBody;

 private:
  struct Route { std::string uri; HTTPMethod m; Handler h, up; };
  void dispatch(int fd, const std::string& method, const std::string& path, const std::string& body,
                const std::map<std::string, std::string>& headers);
  bool simRoute(const std::string& path);
  int port_, listen_ = -1, client_ = -1;
  bool sent_ = false;
  std::vector<Route> routes_;
  Handler notFound_;
  std::map<std::string, std::string> args_, headers_;
  std::string extraHeaders_;
  HTTPUpload upload_;
};
