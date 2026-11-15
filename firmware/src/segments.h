#pragma once
// Segment patterns for 4-digit TM1637 displays, and the mirroring the ceiling projector needs.
// Bit order is the TM1637Display library's: a=0x01 b=0x02 c=0x04 d=0x08 e=0x10 f=0x20 g=0x40,
// and on the usual "clock" modules bit 0x80 of the second digit lights the colon.
//
//    aaa
//   f   b
//    ggg
//   e   c
//    ddd
#include <stdint.h>

namespace seg {

constexpr uint8_t DIGIT[10] = {0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07, 0x7F, 0x6F};
constexpr uint8_t DASH = 0x40, COLON = 0x80;

// One digit flipped left-to-right: b<->f, c<->e.
inline uint8_t mirrorDigitX(uint8_t s) {
  uint8_t o = s & (0x01 | 0x08 | 0x40);
  if (s & 0x02) o |= 0x20;
  if (s & 0x20) o |= 0x02;
  if (s & 0x04) o |= 0x10;
  if (s & 0x10) o |= 0x04;
  return o;
}
// One digit flipped top-to-bottom: a<->d, b<->c, f<->e.
inline uint8_t mirrorDigitY(uint8_t s) {
  uint8_t o = s & 0x40;
  if (s & 0x01) o |= 0x08;
  if (s & 0x08) o |= 0x01;
  if (s & 0x02) o |= 0x04;
  if (s & 0x04) o |= 0x02;
  if (s & 0x20) o |= 0x10;
  if (s & 0x10) o |= 0x20;
  return o;
}

// The time as four digits (colon not included). Blank first digit for 1-9 o'clock on a 12-hour clock.
inline void timeDigits(int hour, int minute, bool h24, bool valid, uint8_t out[4]) {
  if (!valid) { for (int i = 0; i < 4; i++) out[i] = DASH; return; }
  int h = hour;
  if (!h24) { h %= 12; if (h == 0) h = 12; }
  out[0] = (h24 || h >= 10) ? DIGIT[h / 10] : 0;
  out[1] = DIGIT[h % 10];
  out[2] = DIGIT[minute / 10];
  out[3] = DIGIT[minute % 10];
}

// What to send to the projector's display so the picture reads correctly on the ceiling.
// mirrorX: the optics flip left/right; mirrorY: they flip top/bottom; upsideDown turns it 180 degrees
// (both flips at once, so it cancels a flip that is already set). The colon sits in the middle of
// the module, so it stays put; it is added after the digits are rearranged.
inline void forProjector(const uint8_t in[4], bool colon, bool mirrorX, bool mirrorY, bool upsideDown, uint8_t out[4]) {
  bool mx = mirrorX != upsideDown, my = mirrorY != upsideDown;
  for (int i = 0; i < 4; i++) {
    uint8_t s = in[mx ? 3 - i : i] & 0x7F;
    if (mx) s = mirrorDigitX(s);
    if (my) s = mirrorDigitY(s);
    out[i] = s;
  }
  if (colon) out[1] |= COLON;
}

}  // namespace seg
