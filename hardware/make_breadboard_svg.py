# Usage: python3 hardware/make_breadboard_svg.py
# Draws docs/img/breadboard.svg: how to power the parts for bench testing, with each module's
# GPIO connections from firmware/src/pins.h. The ESP32 runs from the computer's USB (so you can
# watch its log); the 5 V supply feeds only the LED, ring and amplifier; the grounds are joined.
import os, re
here = os.path.dirname(os.path.abspath(__file__))
pins = dict(re.findall(r'#define (PIN_\w+)\s+(\d+)', open(os.path.join(here, '..', 'firmware', 'src', 'pins.h')).read()))
g = lambda k: pins[k]
W, H = 1120, 720
o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="system-ui,-apple-system,Segoe UI,sans-serif">',
     '<rect width="100%" height="100%" fill="#fbfaf6"/>']
def esc(s): return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
def rect(x, y, w, h, fill, stroke='none', rx=8, sw=1.5): o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
def text(x, y, s, size=13, fill='#222', anchor='start', weight=400): o.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{esc(s)}</text>')
def line(pts, col, w=3, dash=''): o.append('<polyline fill="none" stroke="%s" stroke-width="%s" %s stroke-linejoin="round" stroke-linecap="round" points="%s"/>' % (col, w, f'stroke-dasharray="{dash}"' if dash else '', ' '.join(f'{x},{y}' for x, y in pts)))
def dot(x, y, col): o.append(f'<circle cx="{x}" cy="{y}" r="5" fill="{col}"/>')
RED, BLUE, ORANGE = '#d33a2c', '#2b5fd9', '#e08a00'
L, R = 60, 1060
# rails
T5, TG, B3, BG = 150, 175, 545, 570
for y, col, lab in ((T5, RED, '+5 V rail: external supply only'), (TG, BLUE, 'GND rail'), (B3, ORANGE, '+3V3 rail: from the ESP32\'s 3V3 pin'), (BG, BLUE, 'GND rail')):
    line([(L, y), (R, y)], col, 5)
    text(L + 4, y - 7, lab, 12, col, 'start', 700)
line([(R, TG), (R, BG)], BLUE, 5)
text(R - 8, (TG + BG) / 2, 'join the GND rails', 12, BLUE, 'end', 700)
# 5 V supply
rect(L, 30, 250, 78, '#fffdf8', '#2a6f9e', 10, 2)
text(L + 12, 54, '5 V 3 A USB-C supply', 13.5, '#2a6f9e', 'start', 700)
text(L + 12, 74, '→ USB-C breakout (5.1 kΩ CC)', 12, '#333')
text(L + 12, 94, 'VBUS → +5 V rail · GND → GND rail', 12, '#333')
line([(L + 40, 108), (L + 40, T5)], RED, 3); dot(L + 40, T5, RED)
line([(L + 70, 108), (L + 70, TG)], BLUE, 3); dot(L + 70, TG, BLUE)
# 5 V modules (top), hanging below the top rails
top = [('MAX98357A amplifier', '#7b3fa0', [f'BCLK → GPIO {g("PIN_I2S_BCLK")}', f'LRC → GPIO {g("PIN_I2S_LRC")}', f'DIN → GPIO {g("PIN_I2S_DOUT")}', 'VIN → +5 V, GND → GND', '40 mm speaker on + / −', '100 µF across VIN/GND']),
       ('WS2812B ring', '#1d1d1d', [f'DIN → 330 Ω → GPIO {g("PIN_RING")}', '5V → +5 V, GND → GND', '1000 µF across 5V/GND,', 'right at the ring (− to GND)']),
       ('MOSFET module + LED', '#2a6f9e', [f'SIG/PWM → GPIO {g("PIN_PROJ_LED")}', 'VIN+ → +5 V, VIN− → GND', 'OUT+ → 4.7 Ω 2 W → LED+', 'LED− → OUT−', 'LED star on a heatsink', '(or metal) while testing'])]
x = 330
for name, col, lines_ in top:
    w, h = 220, 40 + 17 * len(lines_)
    y0 = 200
    rect(x, y0, w, h, '#fffdf8', col, 10, 2)
    rect(x, y0, w, 26, col, 'none', 10); rect(x, y0 + 16, w, 10, col, 'none', 0)
    text(x + 10, y0 + 18, name, 12.5, '#fff', 'start', 700)
    for k, s in enumerate(lines_): text(x + 10, y0 + 44 + k * 17, s, 11.5, '#222')
    line([(x + 30, y0), (x + 30, T5)], RED, 3); dot(x + 30, T5, RED)
    line([(x + 55, y0), (x + 55, TG)], BLUE, 3); dot(x + 55, TG, BLUE)
    x += 240
# ESP32
EX, EY = 60, 250
rect(EX, EY, 240, 150, '#1e2126', '#000', 10)
rect(EX + 10, EY + 40, 60, 70, '#c8ccd2', 'none', 4)
text(EX + 155, EY + 34, 'ESP32-S3-DevKitC-1', 13.5, '#fff', 'middle', 700)
text(EX + 155, EY + 60, 'USB → your computer:', 11.5, '#cfd3da', 'middle')
text(EX + 155, EY + 76, 'power, flashing and', 11.5, '#cfd3da', 'middle')
text(EX + 155, EY + 92, 'the serial log (115200)', 11.5, '#cfd3da', 'middle')
text(EX + 155, EY + 120, '5V pin: leave unconnected', 11.5, '#ff8a80', 'middle', 700)
text(EX + 155, EY + 136, 'while on the computer\'s USB', 11.5, '#ff8a80', 'middle')
line([(EX + 60, EY + 150), (EX + 60, B3)], ORANGE, 3); dot(EX + 60, B3, ORANGE); text(EX + 66, EY + 172, '3V3', 11.5, ORANGE, 'start', 700)
line([(EX + 110, EY + 150), (EX + 110, BG)], BLUE, 3); dot(EX + 110, BG, BLUE); text(EX + 116, EY + 172, 'GND', 11.5, BLUE, 'start', 700)
# 3.3 V modules (bottom)
bot = [('Nokia 5110 LCD', '#b03030', [f'RST {g("PIN_LCD_RST")} · CE {g("PIN_LCD_CE")} · DC {g("PIN_LCD_DC")}', f'DIN {g("PIN_LCD_DIN")} · CLK {g("PIN_LCD_CLK")}', 'VCC → 3V3, GND → GND']),
       ('TM1637 display', '#c0392b', [f'CLK → GPIO {g("PIN_TM_CLK")}', f'DIO → GPIO {g("PIN_TM_DIO")}', 'VCC → 3V3, GND → GND']),
       ('DS3231 clock', '#1f4e8c', [f'SDA → GPIO {g("PIN_SDA")}', f'SCL → GPIO {g("PIN_SCL")}', 'VCC → 3V3, GND → GND']),
       ('Light sensor', '#8a6d00', ['GL5528: 3V3 → junction', '10 kΩ: junction → GND', f'junction → GPIO {g("PIN_LDR")}']),
       ('Buttons', '#555', [f'A: GPIO {g("PIN_BTN_A")} → button → GND', f'B: GPIO {g("PIN_BTN_B")} → button → GND', 'no resistors needed'])]
x = 60
for name, col, lines_ in bot:
    w, h = 190, 40 + 17 * len(lines_)
    y0 = 600
    rect(x, y0, w, h, '#fffdf8', col, 10, 2)
    rect(x, y0, w, 26, col, 'none', 10); rect(x, y0 + 16, w, 10, col, 'none', 0)
    text(x + 10, y0 + 18, name, 12.5, '#fff', 'start', 700)
    for k, s in enumerate(lines_): text(x + 10, y0 + 44 + k * 17, s, 11.5, '#222')
    if name != 'Buttons': line([(x + 30, y0), (x + 30, B3)], ORANGE, 3); dot(x + 30, B3, ORANGE)
    line([(x + 55, y0), (x + 55, BG)], BLUE, 3); dot(x + 55, BG, BLUE)
    x += 202
text(330, 470, 'Signal wires go straight from each module to the GPIO shown (numbers as printed on the board).', 12.5, '#333')
text(330, 490, 'Logic modules run on 3.3 V. Only the amplifier, ring and LED use the external 5 V.', 12.5, '#333')
text(330, 510, 'Use short, thick leads for the LED and ring: breadboard contacts are fine for testing, not for keeps.', 12.5, '#626a73')
o.append('</svg>')
open(os.path.join(here, '..', 'docs', 'img', 'breadboard.svg'), 'w').write('\n'.join(o))
print('wrote docs/img/breadboard.svg')
