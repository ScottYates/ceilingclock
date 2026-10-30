# Usage: python3 hardware/make_wiring_svg.py
# Generates docs/img/wiring.svg from the pin map in firmware/src/pins.h
import re
pins = dict(re.findall(r'#define (PIN_\w+)\s+(\d+)', open(__import__('os').path.join(__import__('os').path.dirname(__file__), '..', 'firmware', 'src', 'pins.h')).read()))
g = lambda k: int(pins[k])
left = [
  ("Nokia 5110 LCD (projector)", "#b03030", [("RST", g("PIN_LCD_RST")), ("CE", g("PIN_LCD_CE")), ("DC", g("PIN_LCD_DC")), ("DIN", g("PIN_LCD_DIN")), ("CLK", g("PIN_LCD_CLK"))], "VCC → 3V3 · GND · BL not connected"),
  ("MOSFET module (projector LED)", "#2a6f9e", [("SIG / PWM", g("PIN_PROJ_LED"))], "5V → VIN+ · OUT+ → 4.7 Ω 2 W → LED+ · LED− → OUT−"),
  ("TM1637 front display", "#c0392b", [("CLK", g("PIN_TM_CLK")), ("DIO", g("PIN_TM_DIO"))], "VCC → 3V3 · GND"),
  ("Buttons (other leg to GND)", "#555", [("A · top snooze", g("PIN_BTN_A")), ("B · left side", g("PIN_BTN_B"))], "internal pull-ups, no resistors"),
  ("Light sensor", "#8a6d00", [("LDR / 10k junction", g("PIN_LDR"))], "LDR to 3V3 · 10 kΩ to GND"),
]
right = [
  ("MAX98357A amplifier", "#7b3fa0", [("BCLK", g("PIN_I2S_BCLK")), ("LRC", g("PIN_I2S_LRC")), ("DIN", g("PIN_I2S_DOUT"))], "VIN → 5V · GND · speaker on + / −"),
  ("WS2812B 16-LED ring", "#1d1d1d", [("DIN (via 330 Ω)", g("PIN_RING"))], "5V · GND · 1000 µF across 5V/GND"),
  ("DS3231 clock module", "#1f4e8c", [("SDA", g("PIN_SDA")), ("SCL", g("PIN_SCL"))], "VCC → 3V3 · GND"),
]
W = 1100; ROW = 30; MODW = 300; ESPX = 470; ESPW = 160
out = []
def esc(s): return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
def side(mods, x0, is_left):
    y = 70; wires = []
    for name, col, sig, pw in mods:
        h = 40 + ROW * len(sig) + 22
        out.append(f'<rect x="{x0}" y="{y}" width="{MODW}" height="{h}" rx="10" fill="#fffdf8" stroke="{col}" stroke-width="2"/>')
        out.append(f'<rect x="{x0}" y="{y}" width="{MODW}" height="30" rx="10" fill="{col}"/><rect x="{x0}" y="{y+20}" width="{MODW}" height="10" fill="{col}"/>')
        out.append(f'<text x="{x0+14}" y="{y+20}" fill="#fff" font-weight="700" font-size="14">{esc(name)}</text>')
        for i, (lab, gp) in enumerate(sig):
            py = y + 50 + i * ROW
            px = x0 + MODW if is_left else x0
            out.append(f'<text x="{(x0+MODW-14) if is_left else x0+14}" y="{py+5}" text-anchor="{"end" if is_left else "start"}" font-size="13">{esc(lab)}</text>')
            out.append(f'<circle cx="{px}" cy="{py}" r="4" fill="{col}"/>')
            wires.append((px, py, gp, col))
        out.append(f'<text x="{x0+14}" y="{y+h-10}" font-size="11.5" fill="#626a73">{esc(pw)}</text>')
        y += h + 18
    return wires, y
lw, ly = side(left, 30, True)
rw, ry = side(right, W - 30 - MODW, False)
allw = lw + rw
H = max(ly, ry) + 20
# ESP32 pin column ordered by the wire y positions to avoid crossings
lw_sorted = sorted(lw, key=lambda w: w[1]); rw_sorted = sorted(rw, key=lambda w: w[1])
top = 90; pitch = (H - top - 70) / max(len(lw_sorted), len(rw_sorted))
out.insert(0, f'<rect x="{ESPX}" y="40" width="{ESPW}" height="{H-60}" rx="12" fill="#1f4e8c"/>')
out.insert(1, f'<text x="{ESPX+ESPW/2}" y="66" fill="#fff" text-anchor="middle" font-weight="700" font-size="15">ESP32-S3</text>')
out.insert(2, f'<text x="{ESPX+ESPW/2}" y="{H-32}" fill="#c9d6ea" text-anchor="middle" font-size="11.5">DevKitC-1 N16R8</text>')
for lst, is_left in ((lw_sorted, True), (rw_sorted, False)):
    for i, (px, py, gp, col) in enumerate(lst):
        ey = top + i * pitch + pitch / 2
        ex = ESPX if is_left else ESPX + ESPW
        mx = (px + ex) / 2
        out.append(f'<path d="M{px},{py} C{mx},{py} {mx},{ey} {ex},{ey}" fill="none" stroke="{col}" stroke-width="2.4"/>')
        out.append(f'<text x="{ex + (10 if is_left else -10)}" y="{ey+4.5}" fill="#fff" font-size="12.5" text-anchor="{"start" if is_left else "end"}">GPIO {gp}</text>')
svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="ui-sans-serif,system-ui,sans-serif" fill="#1d2126">' + ''.join(out) + '</svg>'
open(__import__('os').path.join(__import__('os').path.dirname(__file__), '..', 'docs', 'img', 'wiring.svg'), 'w').write(svg)
print('ok', W, H, len(allw), 'signal wires')
