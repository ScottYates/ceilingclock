// PC unit test for the projector's segment mirroring: g++ -std=c++17 -Isrc test/test_segments.cpp && ./a.out
#include "segments.h"
#include <cstdio>
static int fails = 0;
#define CHECK(c) do { if (!(c)) { printf("FAIL line %d: %s\n", __LINE__, #c); fails++; } } while (0)
using namespace seg;

// Renders 4 digits as a 5-row ASCII picture, 22 columns wide (4-wide digits, 2-column gaps), so a mirrored display can be compared with a flipped picture.
static void draw(const uint8_t d[4], char out[5][25]) {
  for (int r = 0; r < 5; r++) { for (int c = 0; c < 24; c++) out[r][c] = ' '; out[r][24] = 0; }
  for (int i = 0; i < 4; i++) {
    int x = i * 6; uint8_t s = d[i];
    if (s & 0x01) out[0][x + 1] = out[0][x + 2] = '-';
    if (s & 0x20) out[1][x] = '|';
    if (s & 0x02) out[1][x + 3] = '|';
    if (s & 0x40) out[2][x + 1] = out[2][x + 2] = '-';
    if (s & 0x10) out[3][x] = '|';
    if (s & 0x04) out[3][x + 3] = '|';
    if (s & 0x08) out[4][x + 1] = out[4][x + 2] = '-';
  }
}

int main() {
  // every digit flipped twice comes back
  for (int s = 0; s < 128; s++) { CHECK(mirrorDigitX(mirrorDigitX(s)) == s); CHECK(mirrorDigitY(mirrorDigitY(s)) == s); }
  // known shapes: 2 and 5 are mirror images left/right; 6 upside down is 9; 7 left/right has a on top and f
  CHECK(mirrorDigitX(DIGIT[2]) == DIGIT[5]);
  CHECK(mirrorDigitY(mirrorDigitX(DIGIT[6])) == DIGIT[9]);
  CHECK(mirrorDigitX(DIGIT[7]) == (0x01 | 0x20 | 0x10));
  CHECK(mirrorDigitY(DIGIT[0]) == DIGIT[0] && mirrorDigitX(DIGIT[8]) == DIGIT[8]);

  // timeDigits
  uint8_t t[4];
  timeDigits(7, 5, false, true, t);  CHECK(t[0] == 0 && t[1] == DIGIT[7] && t[2] == DIGIT[0] && t[3] == DIGIT[5]);
  timeDigits(19, 42, false, true, t); CHECK(t[0] == 0 && t[1] == DIGIT[7] && t[2] == DIGIT[4] && t[3] == DIGIT[2]);
  timeDigits(19, 42, true, true, t);  CHECK(t[0] == DIGIT[1] && t[1] == DIGIT[9]);
  timeDigits(0, 0, false, true, t);   CHECK(t[0] == DIGIT[1] && t[1] == DIGIT[2]);
  timeDigits(0, 0, true, false, t);   CHECK(t[0] == DASH && t[3] == DASH);

  // forProjector: the mirrored module, seen in a mirror, matches the plain time picture
  timeDigits(12, 34, true, true, t);
  uint8_t p[4]; char a[5][25], b[5][25];
  forProjector(t, true, true, false, false, p);
  CHECK(p[1] & COLON);
  draw(t, a); draw(p, b);
  for (int r = 0; r < 5; r++) for (int c = 0; c < 22; c++) {
    char m = b[r][21 - c];  // read the module's picture right to left
    CHECK(a[r][c] == m);
  }
  // top/bottom
  forProjector(t, false, false, true, false, p);
  draw(p, b);
  for (int r = 0; r < 5; r++) for (int c = 0; c < 22; c++) CHECK(a[r][c] == b[4 - r][c]);
  // upside down cancels both: mirrorX + upsideDown = top/bottom only
  uint8_t q[4];
  forProjector(t, true, true, false, true, p); forProjector(t, true, false, true, false, q);
  for (int i = 0; i < 4; i++) CHECK(p[i] == q[i]);
  // no flips: digits unchanged, colon added
  forProjector(t, true, false, false, false, p);
  CHECK(p[0] == t[0] && p[1] == (t[1] | COLON) && p[2] == t[2] && p[3] == t[3]);

  printf(fails ? "%d FAILED\n" : "all segment tests passed\n", fails);
  return fails != 0;
}
