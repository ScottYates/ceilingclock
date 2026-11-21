// Finds the most recent episode in a podcast feed (RSS or Atom) while it downloads, without keeping the feed
// in memory. Feed it the bytes in chunks of any size, then call finish() when the download ends (or stop early
// once done() is true). found(), url() and title() then describe the newest episode that has audio.
//
// "Newest" goes by each item's date (RSS <pubDate>, Atom <published>/<updated>, <dc:date>), so feeds listed
// oldest-first and feeds with an older trailer pinned at the top still give the latest episode. A feed whose
// items carry no dates gives its first item. Most feeds list newest-first: once three dated episodes in a row
// get older, the rest of the feed is skipped (done() turns true).
// Plain C++ (no Arduino types) so it is unit tested on a PC: test/test_feed_scan.cpp.
#pragma once
#include <string>
#include <cstring>
#include <cstddef>
#include <cstdint>
#include <cctype>
#include <cstdlib>
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

  // Seconds since 1970 (UTC) from an RFC 822 date ("Fri, 20 Nov 2026 06:00:00 -0600") or an ISO 8601 one
  // ("2026-11-20T06:00:00Z"); 0 if it can't be read.
  static int64_t parseDate(const std::string& s) {
    int64_t t = parseIso(s);
    return t ? t : parseRfc822(s);
  }

  void feed(const char* p, size_t n) {
    for (size_t i = 0; i < n && !done_; i++) put(p[i]);
  }
  void finish() { done_ = true; }   // the download ended: the best episode so far is the answer
  bool done() const { return done_; }
  bool found() const { return !bestUrl_.empty(); }
  const std::string& url() const { return bestUrl_; }
  const std::string& title() const { return bestTitle_; }
  int64_t date() const { return bestDate_; }
  int episodes() const { return withAudio_; }

 private:
  enum Mode : uint8_t { TEXT, TAG, COMMENT, CDATA };
  enum Cap : uint8_t { NONE, C_TITLE, C_ITITLE, C_DATE, C_UPDATED };
  Mode mode_ = TEXT;
  Cap cap_ = NONE;
  std::string tag_, text_;
  char quote_ = 0;
  bool tagOverflow_ = false, done_ = false, inItem_ = false;
  // the item being read
  std::string url_, mediaUrl_, title_, ititle_, date_, updated_;
  bool urlIsAudio_ = false;
  // the best so far
  std::string bestUrl_, bestTitle_;
  int64_t bestDate_ = 0;
  int withAudio_ = 0, undatedRun_ = 0;
  int64_t recent_[3] = {0, 0, 0};   // dates of the last three episodes, newest entry last

  static constexpr size_t TAG_MAX = 4096, TEXT_MAX = 600;

  void put(char c) {
    switch (mode_) {
      case TEXT:
        if (c == '<') { mode_ = TAG; tag_.clear(); quote_ = 0; tagOverflow_ = false; }
        else if (cap_ != NONE && text_.size() < TEXT_MAX) text_ += c;
        break;
      case TAG:
        if (quote_) { if (c == quote_) quote_ = 0; }
        else if ((c == '"' || c == '\'') && tag_.find('=') != std::string::npos) quote_ = c;
        else if (c == '>') { mode_ = TEXT; if (!tagOverflow_) onTag(); return; }
        if (tag_.size() < TAG_MAX) tag_ += c; else tagOverflow_ = true;
        if (tag_.size() == 3 && tag_ == "!--") { mode_ = COMMENT; tag_.clear(); }
        else if (tag_.size() == 8 && tag_ == "![CDATA[") { mode_ = CDATA; tag_.clear(); }
        break;
      case COMMENT:   // until -->
        tag_ += c; if (tag_.size() > 3) tag_.erase(0, tag_.size() - 3);
        if (tag_ == "-->") { mode_ = TEXT; tag_.clear(); }
        break;
      case CDATA:     // until ]]>, kept as text when it is a field we want
        if (cap_ != NONE && text_.size() < TEXT_MAX) text_ += c;
        tag_ += c; if (tag_.size() > 3) tag_.erase(0, tag_.size() - 3);
        if (tag_ == "]]>") {
          mode_ = TEXT; tag_.clear();
          if (text_.size() >= 3 && text_.compare(text_.size() - 3, 3, "]]>") == 0) text_.resize(text_.size() - 3);
        }
        break;
    }
  }

  static std::string lower(std::string s) { for (auto& ch : s) ch = (char)tolower((unsigned char)ch); return s; }
  static std::string trim(const std::string& s) {
    size_t a = s.find_first_not_of(" \t\r\n"), b = s.find_last_not_of(" \t\r\n");
    return a == std::string::npos ? "" : s.substr(a, b - a + 1);
  }
  static std::string decode(std::string s) {
    const char* ents[][2] = {{"&lt;", "<"}, {"&gt;", ">"}, {"&quot;", "\""}, {"&apos;", "'"}, {"&#39;", "'"}, {"&#039;", "'"}, {"&amp;", "&"}};
    for (auto& e : ents)
      for (size_t k = 0; (k = s.find(e[0], k)) != std::string::npos; k++) s.replace(k, strlen(e[0]), e[1]);
    return trim(s);
  }
  // attribute value from a tag's text (everything between < and >), or ""
  static std::string attr(const std::string& tag, const char* name) {
    size_t n = strlen(name);
    for (size_t k = 0; (k = tag.find(name, k)) != std::string::npos; k += n) {
      if (k == 0 || !isspace((unsigned char)tag[k - 1])) continue;
      size_t e = k + n;
      while (e < tag.size() && isspace((unsigned char)tag[e])) e++;
      if (e >= tag.size() || tag[e] != '=') continue;
      e++;
      while (e < tag.size() && isspace((unsigned char)tag[e])) e++;
      if (e >= tag.size()) return "";
      char q = tag[e];
      if (q != '"' && q != '\'') return "";
      size_t end = tag.find(q, e + 1);
      return end == std::string::npos ? "" : decode(tag.substr(e + 1, end - e - 1));
    }
    return "";
  }

  void onTag() {
    if (tag_.empty() || tag_[0] == '?' || tag_[0] == '!') return;
    bool closing = tag_[0] == '/';
    bool selfClosing = !closing && tag_.back() == '/';
    size_t a = closing ? 1 : 0, b = a;
    while (b < tag_.size() && !isspace((unsigned char)tag_[b]) && tag_[b] != '/') b++;
    std::string name = lower(tag_.substr(a, b - a));
    size_t colon = name.find(':');
    std::string local = colon == std::string::npos ? name : name.substr(colon + 1);

    if (closing) {
      if (cap_ != NONE && (name == capName_ || local == capName_)) endCapture();
      if (local == "item" || local == "entry") endItem();
      return;
    }
    if (local == "item" || local == "entry") { startItem(); if (selfClosing) endItem(); return; }
    if (!inItem_) return;
    if (name == "title" || (local == "title" && colon != std::string::npos && name != "itunes:title" && name != "media:title")) startCapture(C_TITLE, name, selfClosing);
    else if (name == "itunes:title") startCapture(C_ITITLE, name, selfClosing);
    else if (name == "pubdate" || name == "published" || name == "dc:date" || local == "published") startCapture(C_DATE, name, selfClosing);
    else if (local == "updated") startCapture(C_UPDATED, name, selfClosing);
    else if (name == "enclosure") {
      std::string u = attr(tag_, "url"), type = lower(attr(tag_, "type"));
      considerUrl(u, type);
    } else if (local == "link" && lower(attr(tag_, "rel")) == "enclosure") {
      considerUrl(attr(tag_, "href"), lower(attr(tag_, "type")));
    } else if (name == "media:content" && mediaUrl_.empty()) {
      std::string type = lower(attr(tag_, "type")), medium = lower(attr(tag_, "medium"));
      if (type.rfind("audio/", 0) == 0 || medium == "audio") mediaUrl_ = attr(tag_, "url");
    }
  }
  std::string capName_;
  void startCapture(Cap c, const std::string& name, bool selfClosing) {
    if (selfClosing) return;
    cap_ = c; capName_ = name; text_.clear();
  }
  void endCapture() {
    std::string v = decode(text_);
    if (cap_ == C_TITLE && title_.empty()) title_ = v;
    else if (cap_ == C_ITITLE && ititle_.empty()) ititle_ = v;
    else if (cap_ == C_DATE && date_.empty()) date_ = v;
    else if (cap_ == C_UPDATED && updated_.empty()) updated_ = v;
    cap_ = NONE; text_.clear();
  }
  void considerUrl(const std::string& u, const std::string& type) {
    if (u.empty() || type.rfind("video/", 0) == 0 || type.rfind("image/", 0) == 0) return;
    bool audio = type.rfind("audio/", 0) == 0;
    if (url_.empty() || (audio && !urlIsAudio_)) { url_ = u; urlIsAudio_ = audio; }
  }
  void startItem() {
    inItem_ = true; cap_ = NONE;
    url_.clear(); mediaUrl_.clear(); title_.clear(); ititle_.clear(); date_.clear(); updated_.clear(); urlIsAudio_ = false;
  }
  void endItem() {
    if (!inItem_) return;
    inItem_ = false; cap_ = NONE;
    std::string u = url_.empty() ? mediaUrl_ : url_;
    if (u.empty()) return;                       // no audio in this one (a text post, a video)
    int64_t d = parseDate(date_);
    if (!d) d = parseDate(updated_);
    withAudio_++;
    if (bestUrl_.empty() || d > bestDate_) { bestUrl_ = u; bestTitle_ = title_.empty() ? ititle_ : title_; bestDate_ = d; }
    // stop early: newest-first feeds (three dated episodes in a row getting older), or feeds without dates
    recent_[0] = recent_[1]; recent_[1] = recent_[2]; recent_[2] = d;
    undatedRun_ = d ? 0 : undatedRun_ + 1;
    if (withAudio_ >= 3 && recent_[0] && recent_[0] > recent_[1] && recent_[1] > recent_[2] && bestDate_ >= recent_[0]) done_ = true;
    if (withAudio_ >= 3 && undatedRun_ >= 3 && bestDate_ == 0) done_ = true;
  }

  // ---- dates
  static int64_t daysFromCivil(int64_t y, unsigned m, unsigned d) {   // Howard Hinnant's algorithm
    y -= m <= 2;
    const int64_t era = (y >= 0 ? y : y - 399) / 400;
    const unsigned yoe = (unsigned)(y - era * 400);
    const unsigned doy = (153 * (m + (m > 2 ? -3 : 9)) + 2) / 5 + d - 1;
    const unsigned doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    return era * 146097 + (int64_t)doe - 719468;
  }
  static int64_t make(int y, int mo, int d, int h, int mi, int s, int offMin) {
    if (y < 1970 || y > 2200 || mo < 1 || mo > 12 || d < 1 || d > 31 || h > 24 || mi > 59 || s > 60) return 0;
    return daysFromCivil(y, mo, d) * 86400 + h * 3600 + mi * 60 + s - offMin * 60;
  }
  static int num(const std::string& s, size_t& i, int maxDigits) {
    int v = 0, n = 0;
    while (i < s.size() && n < maxDigits && isdigit((unsigned char)s[i])) { v = v * 10 + (s[i] - '0'); i++; n++; }
    return n ? v : -1;
  }
  static int zone(const std::string& z) {   // minutes east of UTC, or -9999 if unknown
    if (z.empty()) return 0;
    if (z[0] == '+' || z[0] == '-') {
      std::string d; for (char c : z) if (isdigit((unsigned char)c)) d += c;
      if (d.size() != 4 && d.size() != 2) return -9999;
      int hh = atoi(d.substr(0, 2).c_str()), mm = d.size() == 4 ? atoi(d.substr(2, 2).c_str()) : 0;
      return (z[0] == '-' ? -1 : 1) * (hh * 60 + mm);
    }
    static const struct { const char* n; int m; } Z[] = {{"gmt", 0}, {"ut", 0}, {"utc", 0}, {"z", 0}, {"est", -300}, {"edt", -240},
      {"cst", -360}, {"cdt", -300}, {"mst", -420}, {"mdt", -360}, {"pst", -480}, {"pdt", -420}, {"bst", 60}, {"cet", 60}, {"cest", 120}};
    std::string l = lower(z);
    for (auto& e : Z) if (l == e.n) return e.m;
    return 0;   // an unknown name: treat as UTC (a few hours either way still orders episodes days apart)
  }
  static int64_t parseIso(const std::string& in) {
    std::string s = trim(in);
    size_t i = 0;
    int y = num(s, i, 4); if (y < 0 || i != 4 || i >= s.size() || s[i] != '-') return 0; i++;
    int mo = num(s, i, 2); if (mo < 0 || i >= s.size() || s[i] != '-') return 0; i++;
    int d = num(s, i, 2); if (d < 0) return 0;
    int h = 0, mi = 0, se = 0;
    if (i < s.size() && (s[i] == 'T' || s[i] == 't' || s[i] == ' ')) {
      i++; h = num(s, i, 2); if (h < 0 || i >= s.size() || s[i] != ':') return 0; i++;
      mi = num(s, i, 2); if (mi < 0) return 0;
      if (i < s.size() && s[i] == ':') { i++; se = num(s, i, 2); if (se < 0) se = 0; }
      if (i < s.size() && s[i] == '.') { i++; while (i < s.size() && isdigit((unsigned char)s[i])) i++; }
    }
    int off = zone(s.substr(i));
    if (off == -9999) off = 0;
    return make(y, mo, d, h, mi, se, off);
  }
  static int64_t parseRfc822(const std::string& in) {
    std::string s = trim(in);
    size_t comma = s.find(',');
    if (comma != std::string::npos && comma < 12) s = trim(s.substr(comma + 1));
    // day month year [hh:mm[:ss]] [zone]
    size_t i = 0;
    int d = num(s, i, 2); if (d < 0) return 0;
    while (i < s.size() && (s[i] == ' ' || s[i] == '-')) i++;
    std::string mon = lower(s.substr(i, 3)); i += 3;
    while (i < s.size() && isalpha((unsigned char)s[i])) i++;   // "November"
    static const char* M[] = {"jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"};
    int mo = 0; for (int k = 0; k < 12; k++) if (mon == M[k]) mo = k + 1;
    if (!mo) return 0;
    while (i < s.size() && (s[i] == ' ' || s[i] == '-')) i++;
    size_t y0 = i;
    int y = num(s, i, 4); if (y < 0) return 0;
    if (i - y0 == 2) y += y < 70 ? 2000 : 1900;
    int h = 0, mi = 0, se = 0;
    while (i < s.size() && s[i] == ' ') i++;
    if (i < s.size() && isdigit((unsigned char)s[i])) {
      h = num(s, i, 2); if (i >= s.size() || s[i] != ':') return 0; i++;
      mi = num(s, i, 2); if (mi < 0) return 0;
      if (i < s.size() && s[i] == ':') { i++; se = num(s, i, 2); if (se < 0) se = 0; }
    }
    int off = zone(trim(s.substr(i)));
    if (off == -9999) off = 0;
    return make(y, mo, d, h, mi, se, off);
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
