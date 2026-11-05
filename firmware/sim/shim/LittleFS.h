// PC simulator: LittleFS backed by a folder on disk (SIM_FS_DIR, default ./sim_fs).
#pragma once
#include "Arduino.h"
#include <dirent.h>

class File : public Stream {
 public:
  File() {}
  File(const std::string& path, const char* mode);
  File(const File&) = delete;
  File& operator=(const File&) = delete;
  File(File&& o) noexcept { *this = std::move(o); }
  File& operator=(File&& o) noexcept;
  ~File() { close(); }
#ifdef SIM_WASM
  explicit operator bool() const { return mopen_; }
#else
  explicit operator bool() const { return fp_ || dir_; }
#endif
  const char* name() const;
  size_t size() const;
  void close();
  int available() override;
  int read() override;
  size_t readBytes(char* b, size_t n) override;
  size_t write(uint8_t c) override;
  size_t write(const uint8_t* b, size_t n) override;
  File openNextFile();
 private:
  FILE* fp_ = nullptr;
  DIR* dir_ = nullptr;
  std::string path_, name_;
#ifdef SIM_WASM
  // browser build: files live in memory (see sim_hw.cpp)
  bool mopen_ = false, mdir_ = false;
  size_t mpos_ = 0, midx_ = 0;
  std::vector<std::string> mlist_;
#endif
};

namespace fs {
class FS {
 public:
  bool begin(bool formatOnFail = false, const char* basePath = "/littlefs", uint8_t maxOpenFiles = 10, const char* partitionLabel = "spiffs");
  File open(const char* path, const char* mode = "r");
  File open(const String& path, const char* mode = "r") { return open(path.c_str(), mode); }
  bool exists(const char* path);
  bool exists(const String& p) { return exists(p.c_str()); }
  bool remove(const char* path);
  bool remove(const String& p) { return remove(p.c_str()); }
  bool rename(const char* a, const char* b);
  bool mkdir(const char* path);
  size_t usedBytes();
  size_t totalBytes() { return 10354688; }   // same as the 0x9E0000 partition
  std::string real(const char* path);
};
}
extern fs::FS LittleFS;
