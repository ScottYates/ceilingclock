// Finds the newest episode in a podcast feed (RSS or Atom) while it downloads, without
// keeping the whole feed in memory. Feed it the bytes in any size chunks; once done() is
// true, url() is the audio file of the first <item>/<entry> and title() its title.
// Plain C++ (no Arduino types) so it is unit tested on a PC: test/test_feed_scan.cpp.
#pragma once
#include <string>
#include <cstring>
#include <cstddef>
#include <cctype>
#include <algorithm>

class FeedScan {
 public:
  // True if the first bytes look like XML (a feed) rather than audio.
  static bool looksLikeXml(const char* p, size_t n) {
    size_t i = 0;
    if (n >= 3 && (unsigned char)p[0] == 0xEF && (unsigned char)p[1] == 0xBB && (unsigned char)p[2] == 0xBF) i = 3;  // BOM
    while (i < n && (p[i] == ' ' || p[i] == '\t' || p[i] == '\r' || p[i] == '\n')) i++;
    if (i >= n || p[i] != '<') return false;
    std::string head(p + i, std::min(n - i, (size_t)200));
    return head.compare(0, 5, "<?xml") == 0 || head.compare(0, 4, "<rss") == 0 || head.compare(0, 5, "<feed") == 0 ||
           head.compare(0, 4, "<!--") == 0;
  }

  void feed(const char* p, size_t n) {
    if (done_ || n == 0) return;
    buf_.append(p, n);
    scan();
    // keep memory bounded: before the first item only a short tail is needed; inside it, 16 KB
    if (itemAt_ == std::string::npos) {
      if (buf_.size() > 64) buf_.erase(0, buf_.size() - 64);
    } else if (buf_.size() > 16384) {
      giveUp_ = true; done_ = true;
    }
  }
  bool done() const { return done_; }
  bool found() const { return !url_.empty(); }
  const std::string& url() const { return url_; }
  const std::string& title() const { return title_; }

 private:
  std::string buf_, url_, title_;
  size_t itemAt_ = std::string::npos;
  bool done_ = false, giveUp_ = false;

  static std::string decode(std::string s) {
    // CDATA, entities and surrounding whitespace
    size_t c = s.find("<![CDATA[");
    if (c != std::string::npos) {
      size_t e = s.find("]]>", c);
      s = s.substr(c + 9, e == std::string::npos ? std::string::npos : e - c - 9);
    }
    const char* ents[][2] = {{"&amp;", "&"}, {"&lt;", "<"}, {"&gt;", ">"}, {"&quot;", "\""}, {"&apos;", "'"}, {"&#39;", "'"}};
    for (auto& e : ents)
      for (size_t k; (k = s.find(e[0])) != std::string::npos;) s.replace(k, strlen(e[0]), e[1]);
    size_t a = s.find_first_not_of(" \t\r\n"), b = s.find_last_not_of(" \t\r\n");
    return a == std::string::npos ? "" : s.substr(a, b - a + 1);
  }
  static std::string attr(const std::string& tag, const char* name) {
    std::string key = std::string(" ") + name + "=";
    size_t k = tag.find(key);
    if (k == std::string::npos) { key[0] = '\n'; k = tag.find(key); }
    if (k == std::string::npos) { key[0] = '\t'; k = tag.find(key); }
    if (k == std::string::npos) return "";
    k += key.size();
    if (k >= tag.size()) return "";
    char q = tag[k];
    if (q != '"' && q != '\'') return "";
    size_t e = tag.find(q, k + 1);
    return e == std::string::npos ? "" : decode(tag.substr(k + 1, e - k - 1));
  }
  static size_t findTag(const std::string& s, const char* name, size_t from) {
    // "<name" followed by space, '>' or '/', so <item> doesn't match <itemize>
    std::string t = std::string("<") + name;
    for (size_t k = s.find(t, from); k != std::string::npos; k = s.find(t, k + 1)) {
      size_t e = k + t.size();
      if (e < s.size() && (s[e] == ' ' || s[e] == '>' || s[e] == '/' || s[e] == '\n' || s[e] == '\r' || s[e] == '\t')) return k;
      if (e >= s.size()) return std::string::npos;   // need more bytes
    }
    return std::string::npos;
  }

  void scan() {
    if (itemAt_ == std::string::npos) {
      size_t a = findTag(buf_, "item", 0), b = findTag(buf_, "entry", 0);
      size_t k = a < b ? a : b;
      if (k == std::string::npos) return;
      buf_.erase(0, k);
      itemAt_ = 0;
    }
    // title of this item
    if (title_.empty()) {
      size_t t = findTag(buf_, "title", 1);
      if (t != std::string::npos) {
        size_t gt = buf_.find('>', t), end = buf_.find("</title>", t);
        if (gt != std::string::npos && end != std::string::npos && gt < end) title_ = decode(buf_.substr(gt + 1, end - gt - 1));
      }
    }
    // RSS: <enclosure url="..." type="audio/mpeg"/>; Atom: <link rel="enclosure" href="..."/>
    for (size_t e = findTag(buf_, "enclosure", 1); e != std::string::npos; e = findTag(buf_, "enclosure", e + 1)) {
      size_t gt = buf_.find('>', e);
      if (gt == std::string::npos) return;  // tag not complete yet
      std::string u = attr(buf_.substr(e, gt - e), "url");
      if (!u.empty()) { url_ = u; done_ = true; return; }
    }
    for (size_t l = findTag(buf_, "link", 1); l != std::string::npos; l = findTag(buf_, "link", l + 1)) {
      size_t gt = buf_.find('>', l);
      if (gt == std::string::npos) return;
      std::string tag = buf_.substr(l, gt - l);
      if (attr(tag, "rel") == "enclosure") {
        std::string u = attr(tag, "href");
        if (!u.empty()) { url_ = u; done_ = true; return; }
      }
    }
    // the first item had no audio: try the next one
    size_t next = std::string::npos;
    size_t a = findTag(buf_, "item", 1), b = findTag(buf_, "entry", 1);
    next = a < b ? a : b;
    if (next != std::string::npos) { buf_.erase(0, next); title_.clear(); scan(); }
  }
};

// True if a URL obviously points at audio (no need to look inside it).
inline bool urlLooksLikeAudio(const char* url) {
  std::string u(url);
  size_t q = u.find_first_of("?#");
  if (q != std::string::npos) u.resize(q);
  for (auto& c : u) c = (char)tolower((unsigned char)c);
  const char* ext[] = {".mp3", ".aac", ".m4a", ".ogg", ".opus", ".flac", ".wav", ".m3u", ".m3u8", ".pls"};
  for (auto e : ext) {
    size_t n = strlen(e);
    if (u.size() >= n && u.compare(u.size() - n, n, e) == 0) return true;
  }
  return false;
}
