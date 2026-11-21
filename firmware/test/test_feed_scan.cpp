// PC unit test for the podcast feed scanner: g++ -std=c++17 -Isrc test/test_feed_scan.cpp && ./a.out
#include "feed_scan.h"
#include <cstdio>
#include <string>
static int fails = 0;
#define CHECK(c) do { if (!(c)) { printf("FAIL line %d: %s\n", __LINE__, #c); fails++; } } while (0)

static FeedScan scanAll(const std::string& xml, size_t chunk) {
  FeedScan f;
  for (size_t i = 0; i < xml.size() && !f.done(); i += chunk) f.feed(xml.data() + i, std::min(chunk, xml.size() - i));
  f.finish();
  return f;
}
static std::string item(const std::string& title, const std::string& date, const std::string& url, const std::string& extra = "") {
  return "<item><title>" + title + "</title>" + (date.empty() ? "" : "<pubDate>" + date + "</pubDate>") + extra +
         (url.empty() ? "" : "<enclosure url=\"" + url + "\" type=\"audio/mpeg\" length=\"1\"/>") + "</item>\n";
}
static std::string rss(const std::string& items) {
  return "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<rss version=\"2.0\" xmlns:itunes=\"http://www.itunes.com/dtds/podcast-1.0.dtd\"><channel>"
         "<title>Show</title><image><title>Logo</title></image><description>A <b>show</b></description>\n" + items + "</channel></rss>";
}

int main() {
  // dates
  CHECK(FeedScan::parseDate("Fri, 20 Nov 2026 06:00:00 GMT") == 1795154400);
  CHECK(FeedScan::parseDate("Fri, 20 Nov 2026 00:00:00 -0600") == 1795154400);
  CHECK(FeedScan::parseDate("20 Nov 2026 00:00:00 CST") == 1795154400);
  CHECK(FeedScan::parseDate("2026-11-20T06:00:00Z") == 1795154400);
  CHECK(FeedScan::parseDate("2026-11-20T01:00:00.123-05:00") == 1795154400);
  CHECK(FeedScan::parseDate("Fri, 30 Oct 2026") > 0);
  CHECK(FeedScan::parseDate("Friday, 20 November 2026 06:00 GMT") == 1795154400);
  CHECK(FeedScan::parseDate("not a date") == 0);

  // newest-first feed (the usual case), any chunk size, entities and CDATA in the title
  std::string normal = rss(
      "<item>\n<title><![CDATA[Episode 42: Mornings & Coffee]]></title>\n<pubDate>Fri, 30 Oct 2026 05:00:00 GMT</pubDate>"
      "<enclosure length=\"123\" type=\"audio/mpeg\" url=\"https://cdn.example.com/ep42.mp3?a=1&amp;b=2\"/>\n</item>" +
      item("Episode 41", "Fri, 23 Oct 2026 05:00:00 GMT", "https://cdn.example.com/ep41.mp3"));
  for (size_t chunk : {1u, 3u, 7u, 64u, 5000u}) {
    FeedScan f = scanAll(normal, chunk);
    CHECK(f.found());
    CHECK(f.url() == "https://cdn.example.com/ep42.mp3?a=1&b=2");
    CHECK(f.title() == "Episode 42: Mornings & Coffee");
  }
  // oldest-first feed: the newest is the last one
  std::string oldestFirst = rss(item("One", "Mon, 05 Jan 2026 10:00:00 GMT", "https://x/1.mp3") + item("Two", "Mon, 12 Jan 2026 10:00:00 GMT", "https://x/2.mp3") +
                                item("Three", "Mon, 19 Jan 2026 10:00:00 GMT", "https://x/3.mp3") + item("Four", "Mon, 26 Jan 2026 10:00:00 GMT", "https://x/4.mp3"));
  FeedScan o = scanAll(oldestFirst, 11);
  CHECK(o.found() && o.url() == "https://x/4.mp3" && o.title() == "Four");
  // an old trailer pinned at the top
  std::string pinned = rss(item("Trailer", "Thu, 01 Jan 2026 00:00:00 GMT", "https://x/trailer.mp3") + item("Ep 9", "Fri, 20 Nov 2026 06:00:00 GMT", "https://x/9.mp3") +
                           item("Ep 8", "Fri, 13 Nov 2026 06:00:00 GMT", "https://x/8.mp3") + item("Ep 7", "Fri, 06 Nov 2026 06:00:00 GMT", "https://x/7.mp3") +
                           item("Ep 6", "Fri, 30 Oct 2026 06:00:00 GMT", "https://x/6.mp3"));
  FeedScan pn = scanAll(pinned, 13);
  CHECK(pn.url() == "https://x/9.mp3" && pn.title() == "Ep 9");
  // newest-first: stops reading once three episodes in a row get older
  std::string many;
  for (int k = 0; k < 200; k++) {
    char d[64]; snprintf(d, sizeof d, "Fri, %02d Oct 2026 06:00:00 GMT", 28 - (k % 28));
    many += item("Ep " + std::to_string(200 - k), k < 28 ? d : "Thu, 01 Jan 2026 00:00:00 GMT", "https://x/" + std::to_string(200 - k) + ".mp3");
  }
  FeedScan m; std::string mx = rss(many); size_t used = 0;
  for (size_t i = 0; i < mx.size() && !m.done(); i += 100) { m.feed(mx.data() + i, std::min<size_t>(100, mx.size() - i)); used = i + 100; }
  CHECK(m.done() && m.url() == "https://x/200.mp3" && used < mx.size() / 10);
  // first item without audio -> next one; a video enclosure doesn't count
  std::string skip = rss("<item><title>Trailer text</title><pubDate>Fri, 20 Nov 2026 07:00:00 GMT</pubDate></item>" +
                         item("Video", "Fri, 20 Nov 2026 06:30:00 GMT", "", "<enclosure url='https://x/v.mp4' type='video/mp4'/>") +
                         "<item><title>Real</title><pubDate>Fri, 20 Nov 2026 06:00:00 GMT</pubDate><enclosure url='http://x.org/real.m4a' type='audio/x-m4a'></enclosure></item>");
  FeedScan s = scanAll(skip, 5);
  CHECK(s.found() && s.url() == "http://x.org/real.m4a" && s.title() == "Real");
  // a long show-notes block (with markup, CDATA and a comment) before the enclosure
  std::string notes(200000, 'x');
  std::string big = rss("<item><title>Long</title><pubDate>Fri, 20 Nov 2026 06:00:00 GMT</pubDate><description><![CDATA[<p>" + notes +
                        " </item> <enclosure url=\"bad\"/>]]></description><!-- <enclosure url=\"https://x/comment.mp3\"/> -->"
                        "<content:encoded>&lt;p&gt;" + notes + "</content:encoded><enclosure url=\"https://x/long.mp3\" type=\"audio/mpeg\"/></item>" +
                        item("Older", "Fri, 13 Nov 2026 06:00:00 GMT", "https://x/older.mp3"));
  FeedScan b = scanAll(big, 1000);
  CHECK(b.url() == "https://x/long.mp3" && b.title() == "Long");
  // itunes:title when there's no plain title; media:content as the audio
  FeedScan it = scanAll(rss("<item><itunes:title>Only iTunes</itunes:title><pubDate>Fri, 20 Nov 2026 06:00:00 GMT</pubDate>"
                            "<media:content url=\"https://x/m.mp3\" type=\"audio/mpeg\"/></item>"), 9);
  CHECK(it.url() == "https://x/m.mp3" && it.title() == "Only iTunes");
  // no dates at all: the first episode
  FeedScan nd = scanAll(rss(item("First", "", "https://x/a.mp3") + item("Second", "", "https://x/b.mp3")), 7);
  CHECK(nd.url() == "https://x/a.mp3");
  // Atom, newest by <published>
  std::string atom = "<?xml version='1.0'?><feed xmlns='http://www.w3.org/2005/Atom'><title>F</title>"
                     "<entry><title>Older ep</title><published>2026-11-01T06:00:00Z</published><link rel=\"enclosure\" type=\"audio/mpeg\" href=\"https://x/o.mp3\"/></entry>"
                     "<entry><title type=\"text\">Atom ep</title><updated>2026-11-19T06:00:00-06:00</updated><link rel=\"alternate\" href=\"https://x/page\"/>"
                     "<link href=\"https://x/a.mp3\" rel=\"enclosure\" type=\"audio/mpeg\"/></entry></feed>";
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
