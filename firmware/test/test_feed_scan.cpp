// PC unit test for the podcast feed scanner: g++ -std=c++17 -Isrc test/test_feed_scan.cpp && ./a.out
#include "feed_scan.h"
#include <cstdio>
#include <string>
static int fails = 0;
#define CHECK(c) do { if (!(c)) { printf("FAIL line %d: %s\n", __LINE__, #c); fails++; } } while (0)

static FeedScan scanAll(const std::string& xml, size_t chunk) {
  FeedScan f;
  for (size_t i = 0; i < xml.size() && !f.done(); i += chunk) f.feed(xml.data() + i, std::min(chunk, xml.size() - i));
  return f;
}

int main() {
  std::string rss =
      "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<rss version=\"2.0\"><channel><title>Show</title>"
      "<image><title>Logo</title></image><description>A <b>show</b></description>\n"
      "<item>\n<title><![CDATA[Episode 42: Mornings & Coffee]]></title>\n<pubDate>Fri, 30 Oct 2026</pubDate>"
      "<enclosure length=\"123\" type=\"audio/mpeg\" url=\"https://cdn.example.com/ep42.mp3?a=1&amp;b=2\"/>\n</item>"
      "<item><title>Episode 41</title><enclosure url=\"https://cdn.example.com/ep41.mp3\"/></item></channel></rss>";
  for (size_t chunk : {1u, 3u, 7u, 64u, 5000u}) {
    FeedScan f = scanAll(rss, chunk);
    CHECK(f.done() && f.found());
    CHECK(f.url() == "https://cdn.example.com/ep42.mp3?a=1&b=2");
    CHECK(f.title() == "Episode 42: Mornings & Coffee");
  }
  // first item without audio -> next one
  std::string skip = "<rss><channel><item><title>Trailer text</title></item><item><title>Real</title>"
                     "<enclosure url='http://x.org/real.m4a' type='audio/x-m4a'></enclosure></item></channel></rss>";
  FeedScan s = scanAll(skip, 5);
  CHECK(s.found() && s.url() == "http://x.org/real.m4a" && s.title() == "Real");
  // Atom
  std::string atom = "<?xml version='1.0'?><feed xmlns='http://www.w3.org/2005/Atom'><title>F</title>"
                     "<entry><title>Atom ep</title><link rel=\"alternate\" href=\"https://x/page\"/>"
                     "<link rel=\"enclosure\" type=\"audio/mpeg\" href=\"https://x/a.mp3\"/></entry></feed>";
  FeedScan a = scanAll(atom, 4);
  CHECK(a.found() && a.url() == "https://x/a.mp3" && a.title() == "Atom ep");
  // <itemize> is not an item; no enclosure anywhere -> not found
  FeedScan n = scanAll("<rss><itemize/><channel><title>x</title></channel></rss>", 3);
  CHECK(!n.found());
  // sniffing
  CHECK(FeedScan::looksLikeXml("\xEF\xBB\xBF  <?xml version", 18));
  CHECK(FeedScan::looksLikeXml("\n<rss version", 13));
  CHECK(!FeedScan::looksLikeXml("ID3\x04\x00", 5));
  CHECK(!FeedScan::looksLikeXml("\xFF\xFB\x90\x00", 4));
  CHECK(urlLooksLikeAudio("https://a.b/c/stream.MP3?x=1"));
  CHECK(urlLooksLikeAudio("http://radio/list.pls"));
  CHECK(!urlLooksLikeAudio("https://feeds.npr.org/500005/podcast.xml"));
  CHECK(!urlLooksLikeAudio("http://icecast.example/stream"));
  printf(fails ? "%d FAILED\n" : "feed scan tests passed\n", fails);
  return fails != 0;
}
