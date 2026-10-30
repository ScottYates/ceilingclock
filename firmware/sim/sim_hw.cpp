// PC simulator: implementations of the Arduino / ESP32 stand-ins in shim/.
#include "Arduino.h"
#include "sim_libs.h"
#include "LittleFS.h"
#include "WebServer.h"
#include "Audio.h"
#include "pins.h"

#include <chrono>
#include <deque>
#include <mutex>
#include <thread>
#include <cstdarg>
#include <sys/stat.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <poll.h>
#ifndef MSG_NOSIGNAL
#define MSG_NOSIGNAL 0   // macOS: SIGPIPE is ignored in main() instead
#endif

#include "shim/glcdfont.c"   // Adafruit GFX "classic" 5x7 font (BSD licence)

SerialClass Serial;
EspClass ESP;
WiFiClass WiFi;
MDNSClass MDNS;
UpdateClass Update;
TwoWire Wire;
fs::FS LittleFS;

namespace sim {
Hw hw;
long timeOffset = 0;
static unsigned long btnUntil[2] = {0, 0};
}

int Print::printf(const char* f, ...) {
  char buf[512];
  va_list ap; va_start(ap, f);
  int n = vsnprintf(buf, sizeof buf, f, ap);
  va_end(ap);
  write((const uint8_t*)buf, strlen(buf));
  return n;
}

// ---------------------------------------------------------------- time
static const auto t0 = std::chrono::steady_clock::now();
unsigned long millis() {
  return (unsigned long)std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - t0).count();
}
void delay(unsigned long ms) { usleep(ms * 1000); }
extern "C" time_t sim_time(time_t* t) noexcept {
  time_t v = ::time(nullptr) + sim::timeOffset;
  if (t) *t = v;
  return v;
}
static sntp_sync_cb g_sntpCb = nullptr;
void sntp_set_sync_interval(uint32_t) {}
void sntp_set_time_sync_notification_cb(sntp_sync_cb cb) { g_sntpCb = cb; }
static void fakeSync() {
  if (!g_sntpCb) return;
  struct timeval tv = {sim_time(nullptr), 0};
  g_sntpCb(&tv);
}
bool sntp_restart() { fakeSync(); return true; }
void configTzTime(const char* tz, const char*, const char*, const char*) {
  setenv("TZ", tz, 1);
  tzset();
  fakeSync();   // the simulator's "NTP server" answers immediately with the host clock
}
void EspClass::restart() { printf("ESP.restart()\n"); exit(0); }

// ---------------------------------------------------------------- GPIO
void pinMode(int, int) {}
int digitalRead(int pin) {
  int i = pin == PIN_BTN_A ? 0 : pin == PIN_BTN_B ? 1 : -1;
  if (i < 0) return HIGH;
  bool down = millis() < sim::btnUntil[i];
  sim::hw.btnDown[i] = down;
  return down ? LOW : HIGH;
}
int analogRead(int) { return sim::hw.ldr; }
void analogReadResolution(int) {}
bool ledcAttach(int, int, int) { return true; }
void ledcWrite(int, uint32_t duty) { sim::hw.projDuty = duty; }

// ---------------------------------------------------------------- FreeRTOS
struct SimQueue { std::mutex m; std::deque<std::vector<uint8_t>> q; size_t item; int cap; };
QueueHandle_t xQueueCreate(int len, size_t itemSize) { auto* q = new SimQueue; q->item = itemSize; q->cap = len; return q; }
BaseType_t xQueueSend(QueueHandle_t h, const void* item, int) {
  auto* q = (SimQueue*)h; std::lock_guard<std::mutex> l(q->m);
  if ((int)q->q.size() >= q->cap) return pdFALSE;
  q->q.emplace_back((const uint8_t*)item, (const uint8_t*)item + q->item);
  return pdTRUE;
}
BaseType_t xQueueReceive(QueueHandle_t h, void* item, int) {
  auto* q = (SimQueue*)h; std::lock_guard<std::mutex> l(q->m);
  if (q->q.empty()) return pdFALSE;
  memcpy(item, q->q.front().data(), q->item);
  q->q.pop_front();
  return pdTRUE;
}
void vTaskDelay(int ticks) { usleep(ticks * 1000); }
BaseType_t xTaskCreatePinnedToCore(void (*fn)(void*), const char*, int, void* arg, int, TaskHandle_t*, int) {
  std::thread(fn, arg).detach();
  return pdTRUE;
}

// ---------------------------------------------------------------- TM1637
static const uint8_t DIGIT_SEG[10] = {0x3f, 0x06, 0x5b, 0x4f, 0x66, 0x6d, 0x7d, 0x07, 0x7f, 0x6f};
void TM1637Display::setSegments(const uint8_t* segs, uint8_t len, uint8_t pos) {
  for (int i = 0; i < len && pos + i < 4; i++) sim::hw.tmSegs[pos + i] = segs[i];
  sim::hw.tmOn = on_;
  sim::hw.tmBright = bright_;
}
void TM1637Display::showNumberDecEx(int num, uint8_t dots, bool leading_zero, uint8_t length, uint8_t pos) {
  uint8_t d[4] = {0, 0, 0, 0};
  if (num == 0 && !leading_zero) {
    d[length - 1] = DIGIT_SEG[0];
  } else {
    for (int i = length - 1; i >= 0; i--) {
      int digit = num % 10;
      d[i] = (digit == 0 && num == 0 && !leading_zero) ? 0 : DIGIT_SEG[digit];
      num /= 10;
    }
  }
  for (int i = 0; i < 4; i++) { d[i] |= (dots & 0x80); dots <<= 1; }
  setSegments(d, length, pos);
}

// ---------------------------------------------------------------- GFX canvas
void GFXcanvas1::drawPixel(int x, int y, int c) {
  if (x < 0 || y < 0 || x >= w_ || y >= h_) return;
  uint8_t& b = buf_[(x / 8) + y * ((w_ + 7) / 8)];
  if (c) b |= 0x80 >> (x & 7); else b &= ~(0x80 >> (x & 7));
}
bool GFXcanvas1::getPixel(int x, int y) const {
  if (x < 0 || y < 0 || x >= w_ || y >= h_) return false;
  return buf_[(x / 8) + y * ((w_ + 7) / 8)] & (0x80 >> (x & 7));
}
void GFXcanvas1::drawChar(char c) {
  if (c == '\n') { cx_ = 0; cy_ += 8 * size_; return; }
  for (int i = 0; i < 5; i++) {
    uint8_t line = font[(uint8_t)c * 5 + i];
    for (int j = 0; j < 8; j++, line >>= 1)
      if (line & 1) fillRect(cx_ + i * size_, cy_ + j * size_, size_, size_, color_);
  }
  cx_ += 6 * size_;
}

// ---------------------------------------------------------------- LittleFS on a folder
static std::string fsRoot() { const char* e = getenv("SIM_FS_DIR"); return e ? e : "sim_fs"; }
std::string fs::FS::real(const char* path) { return fsRoot() + (path[0] == '/' ? "" : "/") + path; }
bool fs::FS::begin(bool) { ::mkdir(fsRoot().c_str(), 0755); return true; }
File fs::FS::open(const char* path, const char* mode) { return File(real(path), mode); }
bool fs::FS::exists(const char* path) { struct stat st; return ::stat(real(path).c_str(), &st) == 0; }
bool fs::FS::remove(const char* path) { return ::remove(real(path).c_str()) == 0; }
bool fs::FS::rename(const char* a, const char* b) { return ::rename(real(a).c_str(), real(b).c_str()) == 0; }
bool fs::FS::mkdir(const char* path) { return ::mkdir(real(path).c_str(), 0755) == 0; }
static size_t dirSize(const std::string& p) {
  size_t total = 0; DIR* d = opendir(p.c_str()); if (!d) return 0;
  while (dirent* e = readdir(d)) {
    if (e->d_name[0] == '.') continue;
    std::string q = p + "/" + e->d_name; struct stat st;
    if (stat(q.c_str(), &st) == 0) total += S_ISDIR(st.st_mode) ? dirSize(q) : st.st_size;
  }
  closedir(d); return total;
}
size_t fs::FS::usedBytes() { return dirSize(fsRoot()); }

File::File(const std::string& path, const char* mode) : path_(path) {
  auto slash = path.rfind('/');
  name_ = slash == std::string::npos ? path : path.substr(slash + 1);
  struct stat st;
  if (mode[0] == 'r' && stat(path.c_str(), &st) == 0 && S_ISDIR(st.st_mode)) { dir_ = opendir(path.c_str()); return; }
  fp_ = fopen(path.c_str(), mode[0] == 'w' ? "wb" : mode[0] == 'a' ? "ab" : "rb");
}
File& File::operator=(File&& o) noexcept {
  if (this != &o) { close(); fp_ = o.fp_; dir_ = o.dir_; path_ = o.path_; name_ = o.name_; o.fp_ = nullptr; o.dir_ = nullptr; }
  return *this;
}
const char* File::name() const { return name_.c_str(); }
size_t File::size() const { struct stat st; return stat(path_.c_str(), &st) == 0 ? st.st_size : 0; }
void File::close() { if (fp_) fclose(fp_); if (dir_) closedir(dir_); fp_ = nullptr; dir_ = nullptr; }
int File::available() { if (!fp_) return 0; long p = ftell(fp_); fseek(fp_, 0, SEEK_END); long e = ftell(fp_); fseek(fp_, p, SEEK_SET); return (int)(e - p); }
int File::read() { return fp_ ? fgetc(fp_) : -1; }
size_t File::readBytes(char* b, size_t n) { return fp_ ? fread(b, 1, n, fp_) : 0; }
size_t File::write(uint8_t c) { return fp_ ? fwrite(&c, 1, 1, fp_) : 0; }
size_t File::write(const uint8_t* b, size_t n) { return fp_ ? fwrite(b, 1, n, fp_) : 0; }
File File::openNextFile() {
  if (!dir_) return File();
  while (dirent* e = readdir(dir_)) {
    if (e->d_name[0] == '.') continue;
    return File(path_ + "/" + e->d_name, "r");
  }
  return File();
}

// ---------------------------------------------------------------- Audio (simulated playback)
void Audio::setVolume(uint8_t v) { sim::hw.audioVol = v; }
bool Audio::connecttoFS(fs::FS& f, const char* path) {
  std::string real = f.real(path);
  FILE* fp = fopen(real.c_str(), "rb");
  if (!fp) { playing_ = false; sim::hw.audioPlaying = false; return false; }
  fseek(fp, 0, SEEK_END); long size = ftell(fp);
  durMs_ = 3000;
  if (strstr(path, ".wav") && size > 44) {
    uint32_t byteRate = 0; fseek(fp, 28, SEEK_SET);
    if (fread(&byteRate, 4, 1, fp) == 1 && byteRate) durMs_ = (unsigned long)((size - 44) * 1000ULL / byteRate);
  }
  fclose(fp);
  playing_ = true; start_ = millis();
  sim::hw.audioPlaying = true; sim::hw.audioFile = path;
  return true;
}
void Audio::stopSong() { playing_ = false; sim::hw.audioPlaying = false; }
bool Audio::isRunning() {
  if (playing_ && millis() - start_ >= durMs_) { playing_ = false; sim::hw.audioPlaying = false; }
  return playing_;
}

// ---------------------------------------------------------------- HTTP server
static std::string urlDecode(const std::string& s) {
  std::string o;
  for (size_t i = 0; i < s.size(); i++) {
    if (s[i] == '+') o += ' ';
    else if (s[i] == '%' && i + 2 < s.size()) { o += (char)strtol(s.substr(i + 1, 2).c_str(), nullptr, 16); i += 2; }
    else o += s[i];
  }
  return o;
}
static void parseArgs(const std::string& q, std::map<std::string, std::string>& out) {
  size_t i = 0;
  while (i < q.size()) {
    size_t amp = q.find('&', i); if (amp == std::string::npos) amp = q.size();
    std::string kv = q.substr(i, amp - i); size_t eq = kv.find('=');
    if (!kv.empty()) out[urlDecode(kv.substr(0, eq))] = eq == std::string::npos ? "" : urlDecode(kv.substr(eq + 1));
    i = amp + 1;
  }
}
static std::string b64decode(const std::string& in) {
  static const std::string tbl = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
  std::string out; int val = 0, bits = -8;
  for (char c : in) { auto p = tbl.find(c); if (p == std::string::npos) break; val = (val << 6) + (int)p; bits += 6; if (bits >= 0) { out += char((val >> bits) & 0xFF); bits -= 8; } }
  return out;
}

void WebServer::begin() {
  const char* e = getenv("SIM_PORT");
  int port = e ? atoi(e) : 8080;
  listen_ = socket(AF_INET, SOCK_STREAM, 0);
  int one = 1; setsockopt(listen_, SOL_SOCKET, SO_REUSEADDR, &one, sizeof one);
  sockaddr_in a{}; a.sin_family = AF_INET; a.sin_port = htons(port); a.sin_addr.s_addr = htonl(INADDR_ANY);
  if (bind(listen_, (sockaddr*)&a, sizeof a) < 0) { perror("bind"); exit(1); }
  listen(listen_, 16);
  fcntl(listen_, F_SETFL, O_NONBLOCK);
  printf("[sim] web server on http://localhost:%d/  (firmware asked for port %d)\n", port, port_);
}

void WebServer::handleClient() {
  if (listen_ < 0) return;
  int fd = accept(listen_, nullptr, nullptr);
  if (fd < 0) return;
  timeval tv{3, 0}; setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof tv);
  std::string req; char buf[8192]; size_t hdrEnd = std::string::npos;
  while (hdrEnd == std::string::npos) {
    ssize_t n = recv(fd, buf, sizeof buf, 0); if (n <= 0) { close(fd); return; }
    req.append(buf, n); hdrEnd = req.find("\r\n\r\n");
  }
  std::string head = req.substr(0, hdrEnd), body = req.substr(hdrEnd + 4);
  std::map<std::string, std::string> headers;
  size_t le = head.find("\r\n");
  std::string line = head.substr(0, le);
  for (size_t p = le + 2; p < head.size();) {
    size_t q = head.find("\r\n", p); if (q == std::string::npos) q = head.size();
    std::string h = head.substr(p, q - p); size_t c = h.find(':');
    if (c != std::string::npos) { std::string k = h.substr(0, c); for (auto& ch : k) ch = tolower(ch); headers[k] = h.substr(c + 1 + (h[c + 1] == ' ')); }
    p = q + 2;
  }
  size_t clen = headers.count("content-length") ? atol(headers["content-length"].c_str()) : 0;
  while (body.size() < clen) { ssize_t n = recv(fd, buf, sizeof buf, 0); if (n <= 0) break; body.append(buf, n); }
  std::string method = line.substr(0, line.find(' '));
  std::string target = line.substr(method.size() + 1, line.rfind(' ') - method.size() - 1);
  dispatch(fd, method, target, body, headers);
  close(fd);
}

void WebServer::dispatch(int fd, const std::string& method, const std::string& target, const std::string& body,
                         const std::map<std::string, std::string>& headers) {
  args_.clear(); headers_ = headers; extraHeaders_.clear(); sent_ = false; client_ = fd;
  std::string path = target, query;
  size_t qm = target.find('?'); if (qm != std::string::npos) { path = target.substr(0, qm); query = target.substr(qm + 1); }
  parseArgs(query, args_);
  std::string ctype = headers.count("content-type") ? headers.at("content-type") : "";
  bool multipart = ctype.find("multipart/form-data") != std::string::npos;
  if (ctype.find("application/x-www-form-urlencoded") != std::string::npos) parseArgs(body, args_);
  if (!multipart) args_["plain"] = body;
  HTTPMethod m = method == "POST" ? HTTP_POST : HTTP_GET;

  if (path.rfind("/sim/", 0) == 0 && simRoute(path)) return;

  for (auto& r : routes_) {
    if (r.uri != path || (r.m != HTTP_ANY && r.m != m)) continue;
    if (multipart && r.up) {
      std::string boundary = "--" + ctype.substr(ctype.find("boundary=") + 9);
      size_t ps = body.find(boundary), he = body.find("\r\n\r\n", ps);
      std::string ph = body.substr(ps, he - ps);
      size_t fnp = ph.find("filename=\"");
      upload_.filename = fnp == std::string::npos ? "" : ph.substr(fnp + 10, ph.find('"', fnp + 10) - fnp - 10).c_str();
      size_t ds = he + 4, de = body.find("\r\n" + boundary, ds);
      upload_.status = UPLOAD_FILE_START; upload_.currentSize = 0; r.up();
      for (size_t p = ds; p < de; p += sizeof upload_.buf) {
        upload_.currentSize = std::min(sizeof upload_.buf, de - p);
        memcpy(upload_.buf, body.data() + p, upload_.currentSize);
        upload_.status = UPLOAD_FILE_WRITE; r.up();
      }
      upload_.status = UPLOAD_FILE_END; upload_.currentSize = 0; r.up();
    }
    r.h();
    if (!sent_) send(500, "text/plain", "handler sent nothing");
    return;
  }
  if (notFound_) notFound_(); else send(404, "text/plain", "not found");
}

void WebServer::send(int code, const char* type, const String& b) {
  if (sent_) return;
  sent_ = true;
  const char* reason = code == 200 ? "OK" : code == 401 ? "Unauthorized" : code == 404 ? "Not Found" : code == 400 ? "Bad Request" : "Error";
  std::string out = "HTTP/1.1 " + std::to_string(code) + " " + reason + "\r\nContent-Type: " + type +
                    "\r\nContent-Length: " + std::to_string(b.length()) + "\r\nCache-Control: no-store\r\nConnection: close\r\n" + extraHeaders_ + "\r\n" + b.s;
  size_t off = 0;
  while (off < out.size()) { ssize_t n = ::send(client_, out.data() + off, out.size() - off, MSG_NOSIGNAL); if (n <= 0) break; off += n; }
}
String WebServer::arg(const char* name) { auto it = args_.find(name); return it == args_.end() ? String() : String(it->second); }
bool WebServer::authenticate(const char* user, const char* pass) {
  auto it = headers_.find("authorization");
  if (it == headers_.end() || it->second.rfind("Basic ", 0) != 0) return false;
  return b64decode(it->second.substr(6)) == std::string(user) + ":" + pass;
}
void WebServer::requestAuthentication() {
  extraHeaders_ = "WWW-Authenticate: Basic realm=\"Login Required\"\r\n";
  send(401, "text/plain", "login required");
}

// Simulator-only endpoints: real hardware state, time travel, buttons, light level.
bool WebServer::simRoute(const std::string& path) {
  using sim::hw;
  if (path == "/sim/hw") {
    static const char* hx = "0123456789abcdef";
    std::string lcd, j;
    for (uint8_t b : hw.lcdShown) { lcd += hx[b >> 4]; lcd += hx[b & 15]; }
    j = "{\"time\":" + std::to_string(sim_time(nullptr)) + ",\"timeOffset\":" + std::to_string(sim::timeOffset) +
        ",\"projDuty\":" + std::to_string(hw.projDuty) + ",\"lcdContrast\":" + std::to_string(hw.lcdContrast) +
        ",\"lcd\":\"" + lcd + "\",\"tm\":{\"on\":" + (hw.tmOn ? "true" : "false") + ",\"bright\":" + std::to_string(hw.tmBright) + ",\"segs\":[";
    for (int i = 0; i < 4; i++) j += std::to_string(hw.tmSegs[i]) + (i < 3 ? "," : "");
    j += "]},\"ring\":[";
    for (int i = 0; i < 16; i++) j += "[" + std::to_string(hw.ring[i][0]) + "," + std::to_string(hw.ring[i][1]) + "," + std::to_string(hw.ring[i][2]) + "]" + (i < 15 ? "," : "");
    j += "],\"audio\":{\"playing\":" + std::string(hw.audioPlaying ? "true" : "false") + ",\"vol\":" + std::to_string(hw.audioVol) +
         ",\"file\":\"" + hw.audioFile + "\"},\"ldr\":" + std::to_string(hw.ldr) + "}";
    send(200, "application/json", String(j));
    return true;
  }
  if (path == "/sim/time") { sim::timeOffset += atol(arg("add").c_str()); if (hasArg("set")) sim::timeOffset = atol(arg("set").c_str()) - ::time(nullptr); send(200, "text/plain", "ok"); return true; }
  if (path == "/sim/button") {
    int i = arg("b") == "B" ? 1 : 0;
    long ms = hasArg("ms") ? atol(arg("ms").c_str()) : 150;
    sim::btnUntil[i] = millis() + ms;
    send(200, "text/plain", "ok"); return true;
  }
  if (path == "/sim/ldr") { hw.ldr = atoi(arg("v").c_str()); send(200, "text/plain", "ok"); return true; }
  return false;
}
