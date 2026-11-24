#!/usr/bin/env python3
"""Builds docs/perfboard.html: moving the clock from the breadboard to its 70 x 40 mm perfboard.

The board is 27 x 15 holes on a 2.54 mm grid: columns 1-27 left to right, rows A-O front to back (row A is the
edge nearest the clock's front). The ESP32 plugs into two 22-way female headers in rows C and M, columns 4-25.
The same layout is in hardware/components.scad (ref_perfboard), so the 3D model matches these pictures.
"""
import html, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'docs', 'perfboard.html')
PINS = open(os.path.join(HERE, '..', 'firmware', 'src', 'pins.h')).read()
G = lambda n: int(re.search(r'#define\s+%s\s+(\d+)' % n, PINS).group(1))

IMGV = '20261123a'           # cache-buster for the rendered pictures and model
COLS, ROWS = 27, 15
RL = 'ABCDEFGHIJKLMNO'
BW, BH = 70.0, 40.0
X0, Y0 = 1.98, 2.22           # first hole from the left and front edges, mm
P = 2.54
J1 = ['3V3', '3V3', 'RST', '4', '5', '6', '7', '15', '16', '17', '18', '8', '3', '46', '9', '10', '11', '12', '13', '14', '5V', 'G']
J3 = ['G', 'TX', 'RX', '1', '2', '42', '41', '40', '39', '38', '37', '36', '35', '0', '45', '48', '47', '21', '20', '19', 'G', 'G']
HC0 = 4                       # header column of the first pin
ROW_J1, ROW_J3 = 2, 12        # rows C and M


def col_of(gpio):
    s = str(gpio)
    if s in J1: return HC0 + J1.index(s), ROW_J1
    return HC0 + J3.index(s), ROW_J3


def pad(name):                # '7A' -> (7, 0)
    m = re.match(r'(\d+)([A-O])$', name)
    return int(m.group(1)), RL.index(m.group(2))


GND, V33, V5 = 1, 2, 3        # bus columns

# ---------------------------------------------------------------- what goes where
def sig(gpio, front=True, row=None):
    c, r = col_of(gpio)
    if row is None: row = 0 if r == ROW_J1 else 14
    return f'{c}{RL[row]}'

GROUPS = [
    dict(id='front', name='Front display', to='the TM1637 behind the front window', color='#c0392b', wires=[
        ('CLK', sig(G('PIN_TM_CLK')), f'GPIO {G("PIN_TM_CLK")}', '#7d3c98'), ('DIO', sig(G('PIN_TM_DIO')), f'GPIO {G("PIN_TM_DIO")}', '#2e86c1'),
        ('VCC', '2E', '3.3 V', '#e67e22'), ('GND', '1C', 'ground', '#222')]),   # 1B/2B sit under the capacitor
    dict(id='proj', name='Projector display', to='the TM1637 in the barrel (out past the display holder)', color='#c0392b', wires=[
        ('CLK', sig(G('PIN_PROJ_CLK')), f'GPIO {G("PIN_PROJ_CLK")}', '#7d3c98'), ('DIO', sig(G('PIN_PROJ_DIO')), f'GPIO {G("PIN_PROJ_DIO")}', '#2e86c1'),
        ('VCC', '2D', '3.3 V', '#e67e22'), ('GND', '1D', 'ground', '#222')]),
    dict(id='amp', name='Amplifier', to='the MAX98357A on the floor', color='#1f618d', wires=[
        ('BCLK', sig(G('PIN_I2S_BCLK')), f'GPIO {G("PIN_I2S_BCLK")}', '#17a589'), ('LRC', sig(G('PIN_I2S_LRC')), f'GPIO {G("PIN_I2S_LRC")}', '#d4ac0d'),
        ('DIN', sig(G('PIN_I2S_DOUT')), f'GPIO {G("PIN_I2S_DOUT")}', '#ca6f1e'), ('VIN', '3E', '5 V', '#e74c3c'), ('GND', '1E', 'ground', '#222')]),
    dict(id='rtc', name='Clock module (DS3231)', to='the DS3231 on the floor', color='#1f4e8c', wires=[
        ('SDA', sig(G('PIN_SDA')), f'GPIO {G("PIN_SDA")}', '#2e86c1'), ('SCL', sig(G('PIN_SCL')), f'GPIO {G("PIN_SCL")}', '#d4ac0d'),
        ('VCC', '2F', '3.3 V', '#e67e22'), ('GND', '1F', 'ground', '#222')]),
    dict(id='lid', name='Lid: buttons, lights and light sensor', to='the lid (see the lid harness below)', color='#5b2c6f', wires=[
        ('Snooze', sig(G('PIN_BTN_A')), f'GPIO {G("PIN_BTN_A")}', '#16a085'), ('Alarm 1 button', sig(G('PIN_BTN_AL1')), f'GPIO {G("PIN_BTN_AL1")}', '#8e44ad'),
        ('Alarm 2 button', sig(G('PIN_BTN_AL2')), f'GPIO {G("PIN_BTN_AL2")}', '#00acc1'), ('Light sensor', sig(G('PIN_LDR')), f'GPIO {G("PIN_LDR")}', '#7f8c8d'),
        ('Alarm 1 light', sig(G('PIN_LED_AL1')), f'GPIO {G("PIN_LED_AL1")}', '#a04000'), ('Alarm 2 light', sig(G('PIN_LED_AL2')), f'GPIO {G("PIN_LED_AL2")}', '#95a5a6'),
        ('3.3 V', '2G', '3.3 V', '#e67e22'), ('GND', '1G', 'ground', '#222')]),
    dict(id='btnb', name='Button B', to='the button on the left wall', color='#5b2c6f', wires=[
        ('Button B', sig(G('PIN_BTN_B')), f'GPIO {G("PIN_BTN_B")}', '#27ae60'), ('GND', '1H', 'ground', '#222')]),
    dict(id='bat', name='Battery boards (optional)', to='the charger and fuel gauge beside the battery', color='#1d1d1d', wires=[
        ('Charger CE', sig(G('PIN_CHG_CE')), f'GPIO {G("PIN_CHG_CE")}', '#e91e63'), ('Charger PGOOD', sig(G('PIN_PGOOD')), f'GPIO {G("PIN_PGOOD")}', '#43a047'),
        ('Charger GND', '1I', 'ground', '#222'), ('Gauge SDA', sig(G('PIN_SDA'), row=13), f'GPIO {G("PIN_SDA")}', '#2e86c1'),
        ('Gauge SCL', sig(G('PIN_SCL'), row=13), f'GPIO {G("PIN_SCL")}', '#d4ac0d'), ('Gauge VIN', '2J', '3.3 V', '#e67e22'), ('Gauge GND', '1J', 'ground', '#222')]),
    dict(id='power', name='Power in', to='the 5 V boost (or straight to the USB-C breakout without the battery)', color='#c0392b', wires=[
        ('5 V in', '3O', '5 V', '#e74c3c'), ('GND in', '1O', 'ground', '#222')]),
]
SHORT = dict(front='front display', proj='projector display', amp='amplifier', rtc='clock module', lid='lid', btnb='button B',
             bat='battery boards', power='power-in')
SIG_COLS_FRONT = sorted({pad(w[1])[0] for g in GROUPS for w in g['wires'] if pad(w[1])[1] == 0 and pad(w[1])[0] > 3})
SIG_COLS_BACK = sorted({pad(w[1])[0] for g in GROUPS for w in g['wires'] if pad(w[1])[1] >= 13 and pad(w[1])[0] > 3})
CAP = ('3A', '1A')            # 100 uF: + in 3A (5 V), - in 1A (ground)
LINKS = [('4C', '2C', '3.3 V: ESP32 3V3 pin to the 3.3 V column', '#e67e22'),
         ('4M', '1M', 'ground: ESP32 G pin to the ground column', '#222'),
         ('24C', '3K', '5 V: ESP32 5V pin to the 5 V column', '#e74c3c')]

# sanity: every pad used once, signal pads in a bridged column, header pins are what the wires say
used = {}
for g in GROUPS:
    for w in g['wires']:
        assert w[1] not in used, (w, used.get(w[1])); used[w[1]] = w
for p_ in CAP + tuple(l[1] for l in LINKS):
    assert p_ not in used, p_; used[p_] = p_
for g in GROUPS:
    for label, p_, what, _ in g['wires']:
        c, r = pad(p_)
        if c > 3:
            hdr = J1 if r <= 2 else J3
            assert hdr[c - HC0] == what.split()[-1], (label, p_, hdr[c - HC0], what)
        else:
            assert {1: 'ground', 2: '3.3 V', 3: '5 V'}[c] == what, (label, p_, what)


# ---------------------------------------------------------------- drawing
S = 11.0                       # px per mm
MX, MY = 190, 105              # margins around the board in the picture (MY = top)
MB = 135                       # bottom margin
W_ = int(BW * S + 2 * MX); H_ = int(BH * S + MY + MB)

def hx(c, bottom=False):
    x = X0 + (c - 1) * P
    if bottom: x = BW - x
    return MX + x * S

def hy(r):
    return MY + (BH - (Y0 + r * P)) * S

def esc(s): return html.escape(str(s), quote=True)

def svg_open(title):
    return [f'<svg viewBox="0 0 {W_} {H_}" class="pbsvg" role="img" aria-label="{esc(title)}" xmlns="http://www.w3.org/2000/svg" font-family="system-ui,sans-serif">',
            '<defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M1 1L9 5L1 9z" fill="#e8743b"/></marker></defs>']

def board(o, bottom=False, label=True, dim=False):
    fill = '#c9a26a' if not bottom else '#b8925b'
    o.append(f'<rect x="{MX}" y="{MY}" width="{BW*S}" height="{BH*S}" rx="6" fill="{fill}" stroke="#8a6a3b" stroke-width="2"/>')
    for c in range(1, COLS + 1):
        for r in range(ROWS):
            o.append(f'<circle cx="{hx(c, bottom):.1f}" cy="{hy(r):.1f}" r="5.2" fill="{"#d7a04a" if bottom else "#e2b866"}" stroke="#9c7434" stroke-width="1"/>'
                     f'<circle cx="{hx(c, bottom):.1f}" cy="{hy(r):.1f}" r="1.9" fill="#3b2a12"/>')
    if label:
        for c in range(1, COLS + 1):
            if c in (1, 2, 3, 4, 7, 10, 13, 15, 18, 20, 22, 25, 27) or c % 5 == 0:
                o.append(f'<text x="{hx(c, bottom):.1f}" y="{MY - 10}" text-anchor="middle" font-size="13" fill="#555">{c}</text>')
                o.append(f'<text x="{hx(c, bottom):.1f}" y="{MY + BH*S + 22}" text-anchor="middle" font-size="13" fill="#555">{c}</text>')
        for r in range(ROWS):
            xl = MX - 14 if not bottom else MX + BW * S + 14
            o.append(f'<text x="{xl}" y="{hy(r) + 5:.1f}" text-anchor="middle" font-size="13" font-weight="700" fill="#555">{RL[r]}</text>')
            xr = MX + BW * S + 14 if not bottom else MX - 14
            o.append(f'<text x="{xr}" y="{hy(r) + 5:.1f}" text-anchor="middle" font-size="13" font-weight="700" fill="#555">{RL[r]}</text>')
        o.append(f'<text x="{MX + BW*S/2}" y="{H_ - 14}" text-anchor="middle" font-size="15" font-weight="700" fill="#b9471c">▼ FRONT edge (toward the clock\'s front)</text>')
        o.append(f'<text x="16" y="24" font-size="15" font-weight="700" fill="#444">{"UNDERSIDE (solder side): the board turned over left to right" if bottom else "TOP (parts side)"}</text>')
    if dim:
        o.append(f'<rect x="{MX}" y="{MY}" width="{BW*S}" height="{BH*S}" rx="6" fill="#fff" opacity=".45"/>')

def bridge(o, a, b, bottom=True, color='#c8ccd2', w=9, new=True):
    (c1, r1), (c2, r2) = pad(a), pad(b)
    o.append(f'<line x1="{hx(c1, bottom):.1f}" y1="{hy(r1):.1f}" x2="{hx(c2, bottom):.1f}" y2="{hy(r2):.1f}" stroke="{color}" stroke-width="{w}" stroke-linecap="round" opacity="{1 if new else .55}"/>')
    if new:
        o.append(f'<line x1="{hx(c1, bottom):.1f}" y1="{hy(r1):.1f}" x2="{hx(c2, bottom):.1f}" y2="{hy(r2):.1f}" stroke="#fff" stroke-width="2" stroke-linecap="round" opacity=".7"/>')

def ring(o, p_, bottom=False, color='#e8743b'):
    c, r = pad(p_)
    o.append(f'<circle cx="{hx(c, bottom):.1f}" cy="{hy(r):.1f}" r="9" fill="none" stroke="{color}" stroke-width="3"/>')

def link(o, a, b, color, label=None, k=0):
    (c1, r1), (c2, r2) = pad(a), pad(b)
    x1, y1, x2, y2 = hx(c1, True), hy(r1), hx(c2, True), hy(r2)
    if a == '24C':                                            # long one: under the ESP32 area
        d = f'M{x1:.1f},{y1:.1f} C{x1:.1f},{y1 - 70:.1f} {x2 + 60:.1f},{y2 + 20:.1f} {x2:.1f},{y2:.1f}'
    else:
        d = f'M{x1:.1f},{y1:.1f} C{(x1 + x2)/2:.1f},{y1 - 34 - 10*k:.1f} {(x1 + x2)/2:.1f},{y2 - 34 - 10*k:.1f} {x2:.1f},{y2:.1f}'
    o.append(f'<path d="{d}" fill="none" stroke="#111" stroke-width="7" stroke-linecap="round"/>')
    o.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="5" stroke-linecap="round"/>')
    for x, y in ((x1, y1), (x2, y2)): o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="#c8ccd2" stroke="#666"/>')

def headers(o, new=True):
    for r in (ROW_J1, ROW_J3):
        x = hx(HC0) - 1.27 * S; y = hy(r) - 1.27 * S
        o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{22*P*S:.1f}" height="{P*S:.1f}" rx="3" fill="#1b1b1b" opacity="{1 if new else .5}"/>')
        for i in range(22):
            o.append(f'<rect x="{hx(HC0 + i) - 3:.1f}" y="{hy(r) - 3:.1f}" width="6" height="6" fill="#555"/>')
        names = J1 if r == ROW_J1 else J3
        for i, nme in enumerate(names):
            o.append(f'<text x="{hx(HC0 + i):.1f}" y="{hy(r) + (24 if r == ROW_J1 else -16):.1f}" text-anchor="middle" font-size="10.5" font-weight="700" fill="{"#fff" if not new else "#1b1b1b"}" opacity="{.95 if new else .6}">{esc(nme)}</text>')
    cx = (hx(HC0) + hx(HC0 + 21))/2; cy = (hy(ROW_J1) + hy(ROW_J3))/2
    o.append(f'<rect x="{cx - 230:.1f}" y="{cy - 16:.1f}" width="460" height="30" rx="8" fill="#fbfaf6" opacity=".85"/>'
             f'<text x="{cx:.1f}" y="{cy + 5:.1f}" text-anchor="middle" font-size="15" font-weight="600" fill="#6b5330">ESP32 plugs in here: antenna end left, USB end right</text>')

def capacitor(o, new=True):
    (c1, r1), (c2, r2) = pad(CAP[0]), pad(CAP[1])
    cx = (hx(c1) + hx(c2)) / 2; cy = hy(r1) - 2
    o.append(f'<g opacity="{1 if new else .55}"><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{3.15*S:.1f}" fill="#1f4e8c" stroke="#0c2a4f" stroke-width="2"/>'
             f'<path d="M{cx - 3.15*S:.1f},{cy:.1f} A{3.15*S:.1f},{3.15*S:.1f} 0 0 1 {cx - 1.4*S:.1f},{cy - 2.8*S:.1f} L{cx - 1.4*S:.1f},{cy + 2.8*S:.1f} A{3.15*S:.1f},{3.15*S:.1f} 0 0 1 {cx - 3.15*S:.1f},{cy:.1f}z" fill="#d6dbe2"/>'
             f'<text x="{cx - 2.3*S:.1f}" y="{cy + 5:.1f}" text-anchor="middle" font-size="16" font-weight="800" fill="#1f4e8c">−</text>'
             f'<text x="{cx + 1.2*S:.1f}" y="{cy + 5:.1f}" text-anchor="middle" font-size="14" font-weight="800" fill="#fff">100µF</text></g>')

def wire_out(o, p_, color, label, k=0, n=1, bold=True):
    c, r = pad(p_)
    x, y = hx(c), hy(r)
    if c <= 3:                                     # rail pads: out to the left, fanned so they don't overlap
        ex, ey = MX - 50, y - (c - 1) * 17
        pts = f'{x:.1f},{y:.1f} {MX - 6:.1f},{ey:.1f} {ex:.1f},{ey:.1f}'
    elif r == 0:                                   # front edge
        ex, ey = x, MY + BH * S + 28
        pts = f'{x:.1f},{y:.1f} {ex:.1f},{ey:.1f}'
    else:                                          # back edge
        ex, ey = x, MY - 26
        pts = f'{x:.1f},{y:.1f} {ex:.1f},{ey:.1f}'
    o.append(f'<polyline points="{pts}" fill="none" stroke="#111" stroke-width="6.5" stroke-linecap="round" stroke-linejoin="round"/>')
    o.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>')
    o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#c8ccd2" stroke="#555"/>')
    if label:
        if c <= 3:
            o.append(f'<text x="{ex - 6:.1f}" y="{ey + 4:.1f}" text-anchor="end" font-size="12.5" font-weight="700" fill="#222">{esc(label)} · {p_}</text>')
        elif r == 0:
            o.append(f'<line x1="{ex:.1f}" y1="{ey:.1f}" x2="{ex:.1f}" y2="{ey + 8 + (k % 3) * 17:.1f}" stroke="#999" stroke-width="1"/>'
                     f'<text x="{ex:.1f}" y="{ey + 22 + (k % 3) * 17:.1f}" text-anchor="middle" font-size="12.5" font-weight="700" fill="#222">{esc(label)} · {p_}</text>')
        else:
            o.append(f'<line x1="{ex:.1f}" y1="{ey:.1f}" x2="{ex:.1f}" y2="{ey - 6 - (k % 3) * 17:.1f}" stroke="#999" stroke-width="1"/>'
                     f'<text x="{ex:.1f}" y="{ey - 10 - (k % 3) * 17:.1f}" text-anchor="middle" font-size="12.5" font-weight="700" fill="#222">{esc(label)} · {p_}</text>')


def pic_cut():
    o = svg_open('The board: 27 by 15 holes')
    board(o)
    o.append(f'<rect x="{MX + BW*S/2 - 250}" y="{MY + BH*S/2 - 40}" width="500" height="74" rx="10" fill="#fbfaf6" opacity=".92"/>')
    o.append(f'<text x="{MX + BW*S/2}" y="{MY + BH*S/2 - 10}" text-anchor="middle" font-size="22" font-weight="800" fill="#5a3d12">70 × 40 mm · 27 × 15 holes</text>')
    o.append(f'<text x="{MX + BW*S/2}" y="{MY + BH*S/2 + 20}" text-anchor="middle" font-size="15" fill="#5a3d12">holes are named by column and row; the ringed one is 7A</text>')
    ring(o, '7A')
    return '\n'.join(o) + '</svg>'

def pic_bridges():
    o = svg_open('Underside: solder bridges')
    board(o, bottom=True)
    for k, (c, nm, col) in enumerate(((GND, 'column 1 = ground', '#333'), (V33, 'column 2 = 3.3 V', '#b9600c'), (V5, 'column 3 = 5 V', '#c0392b'))):
        bridge(o, f'{c}A', f'{c}O')
        o.append(f'<text x="{MX + BW*S + 30}" y="{hy(13 - k) + 5:.1f}" font-size="12.5" font-weight="800" fill="{col}">{nm}</text>')
    for c in SIG_COLS_FRONT: bridge(o, f'{c}A', f'{c}C')
    for c in SIG_COLS_BACK: bridge(o, f'{c}M', f'{c}O')
    return '\n'.join(o) + '</svg>'

def pic_links():
    o = svg_open('Underside: three insulated links')
    board(o, bottom=True)
    for c in (GND, V33, V5): bridge(o, f'{c}A', f'{c}O', new=False)
    for c in SIG_COLS_FRONT: bridge(o, f'{c}A', f'{c}C', new=False)
    for c in SIG_COLS_BACK: bridge(o, f'{c}M', f'{c}O', new=False)
    for k, (a, b, lab, colr) in enumerate(LINKS):
        link(o, a, b, colr, lab, k)
    o.append(f'<rect x="{hx(19, True) - 150:.1f}" y="{hy(10.4) - 18:.1f}" width="300" height="46" rx="8" fill="#fbfaf6" opacity=".92"/>')
    o.append(f'<text x="{hx(19, True):.1f}" y="{hy(10.4):.1f}" text-anchor="middle" font-size="15" font-weight="700" fill="#5a3d12">the long 5 V link crosses the middle,</text>'
             f'<text x="{hx(19, True):.1f}" y="{hy(10.4) + 20:.1f}" text-anchor="middle" font-size="15" font-weight="700" fill="#5a3d12">where the ESP32 will sit</text>')
    return '\n'.join(o) + '</svg>'

def pic_top():
    o = svg_open('Top: headers and capacitor')
    board(o)
    headers(o)
    capacitor(o)
    return '\n'.join(o) + '</svg>'

def pic_group(gid):
    g = next(x for x in GROUPS if x['id'] == gid)
    o = svg_open(g['name'])
    board(o, label=True)
    headers(o, new=False)
    capacitor(o, new=False)
    for other in GROUPS:                         # earlier groups faint
        if other is g: break
        for label, p_, what, colr in other['wires']:
            c, r = pad(p_)
            o.append(f'<circle cx="{hx(c):.1f}" cy="{hy(r):.1f}" r="6" fill="{colr}" opacity=".45"/>')
    lev = {}
    for edge in ('front', 'back'):
        ws = sorted((w for w in g['wires'] if pad(w[1])[0] > 3 and (pad(w[1])[1] == 0) == (edge == 'front')), key=lambda w: pad(w[1])[0])
        for i, w in enumerate(ws): lev[w[1]] = i % 3
    for label, p_, what, colr in g['wires']:
        wire_out(o, p_, colr, label, lev.get(p_, 0))
    return '\n'.join(o) + '</svg>'

def pic_all():
    o = svg_open('All wires')
    board(o)
    headers(o, new=False)
    capacitor(o, new=False)
    for g in GROUPS:
        for k, (label, p_, what, colr) in enumerate(g['wires']):
            wire_out(o, p_, colr, None)
    return '\n'.join(o) + '</svg>'

def pic_lid():
    """Lid harness: what is soldered where on the lid parts."""
    W, H = 1000, 520
    o = [f'<svg viewBox="0 0 {W} {H}" class="pbsvg" role="img" aria-label="Lid harness" xmlns="http://www.w3.org/2000/svg" font-family="system-ui,sans-serif">']
    o.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#fbfaf6"/>')
    o.append('<text x="500" y="30" text-anchor="middle" font-size="17" font-weight="800" fill="#333">Under the lid (seen from below, front edge at the bottom)</text>')
    # ground bus wire
    o.append('<path d="M60,440 L940,440" stroke="#222" stroke-width="6"/><text x="60" y="470" font-size="14" font-weight="700">GND from pad 1G — one wire, then loop it from part to part</text>')
    o.append('<path d="M60,90 L940,90" stroke="#e67e22" stroke-width="5"/><text x="60" y="80" font-size="14" font-weight="700" fill="#b9600c">3.3 V from pad 2G (only the light sensor needs it)</text>')
    def btn(x, y, name, sigpad, colr, led=None, ledcol=None):
        o.append(f'<circle cx="{x}" cy="{y}" r="58" fill="#e9e6dd" stroke="#888" stroke-width="2"/><text x="{x}" y="{y - 70}" text-anchor="middle" font-size="15" font-weight="800">{name}</text>')
        # switch terminals left/right, led terminals top/bottom
        o.append(f'<rect x="{x - 40}" y="{y - 8}" width="14" height="16" fill="#b0b0b0"/><rect x="{x + 26}" y="{y - 8}" width="14" height="16" fill="#b0b0b0"/>')
        o.append(f'<text x="{x}" y="{y + 5}" text-anchor="middle" font-size="11" fill="#555">switch</text>')
        o.append(f'<path d="M{x - 33},{y} C{x - 70},{y + 60} {x - 70},{y + 120} {x - 70},{y + 170}" stroke="{colr}" stroke-width="5" fill="none"/><text x="{x - 76}" y="{y + 190}" text-anchor="middle" font-size="12" font-weight="700">{sigpad}</text>')
        o.append(f'<path d="M{x + 33},{y} L{x + 33},{440}" stroke="#222" stroke-width="4" fill="none"/>')
        if led:
            o.append(f'<rect x="{x - 7}" y="{y - 44}" width="14" height="14" fill="#d9534f"/><text x="{x + 12}" y="{y - 32}" font-size="11" fill="#a33">LED +</text>')
            o.append(f'<rect x="{x - 7}" y="{y + 30}" width="14" height="14" fill="#555"/><text x="{x + 12}" y="{y + 42}" font-size="11" fill="#333">LED −</text>')
            o.append(f'<path d="M{x},{y - 44} L{x},{y - 70} L{x + 70},{y - 70} L{x + 70},{y + 150}" stroke="{ledcol}" stroke-width="4" fill="none"/>')
            o.append(f'<rect x="{x + 62}" y="{y + 70}" width="16" height="40" rx="5" fill="#d8c08c" stroke="#8a6a3b"/><text x="{x + 84}" y="{y + 95}" font-size="12" font-weight="700">220 Ω</text>')
            o.append(f'<text x="{x + 70}" y="{y + 170}" text-anchor="middle" font-size="12" font-weight="700">{led}</text>')
            o.append(f'<path d="M{x},{y + 44} L{x + 18},{y + 60} L{x + 18},{440}" stroke="#222" stroke-width="3" fill="none"/>')
    btn(170, 250, 'Snooze', 'to 9A', '#16a085')
    btn(450, 250, 'Alarm 1', 'to 15A', '#8e44ad', 'to 10O', '#a04000')
    btn(730, 250, 'Alarm 2', 'to 18A', '#00acc1', 'to 9O', '#95a5a6')
    # LDR
    x, y = 905, 250
    o.append(f'<text x="{x}" y="{y - 85}" text-anchor="middle" font-size="15" font-weight="800">Light sensor</text>')
    o.append(f'<ellipse cx="{x}" cy="{y - 40}" rx="16" ry="12" fill="#e8d9a8" stroke="#8a6a3b"/><path d="M{x - 6},{y - 40} L{x - 6},90 M{x + 6},{y - 40} L{x + 6},{y + 20}" stroke="#777" stroke-width="3"/>')
    o.append(f'<rect x="{x - 2}" y="{y + 30}" width="16" height="40" rx="5" fill="#d8c08c" stroke="#8a6a3b"/><text x="{x - 6}" y="{y + 55}" text-anchor="end" font-size="12" font-weight="700">10 kΩ</text>')
    o.append(f'<path d="M{x + 6},{y + 20} L{x + 6},{y + 30} M{x + 6},{y + 70} L{x + 6},440" stroke="#777" stroke-width="3"/>')
    o.append(f'<path d="M{x + 6},{y + 22} C{x - 40},{y + 40} {x - 50},{y + 120} {x - 50},{y + 170}" stroke="#7f8c8d" stroke-width="5" fill="none"/><text x="{x - 50}" y="{y + 190}" text-anchor="middle" font-size="12" font-weight="700">to 10A</text>')
    o.append('<text x="500" y="505" text-anchor="middle" font-size="13" fill="#555">Each alarm button has four tabs: two for the switch, two for its light (+ is usually marked or the longer tab).</text>')
    return '\n'.join(o) + '</svg>'


# ---------------------------------------------------------------- page
def wire_table(g):
    rows = ''.join(f'<tr><td><span class="sw" style="background:{c}"></span>{esc(lab)}</td><td><b>{p_}</b></td><td>{esc(w)}</td></tr>' for lab, p_, w, c in g['wires'])
    return f'<table class="pins"><tr><th>Wire</th><th>Pad</th><th>ESP32 / supply</th></tr>{rows}</table>'

def page():
    steps = []
    def step(sid, title, time, intro, pic='', after='', test='', warn='', shots=(), mid=''):
        steps.append(dict(sid=sid, title=title, time=time, intro=intro, pic=pic, after=after, test=test, warn=warn, shots=shots, mid=mid))

    step('first', 'Before you start', '5 min',
         'Do this once the <a href="breadboard.html">breadboard test</a> works end to end: every module has done what its test step said. '
         'The perfboard does the breadboard\'s job in a form that fits in the case: the ESP32 plugs into two sockets, and every module gets its own wires, soldered to the board.',
         after='''<h3>You need</h3><ul>
<li>Perfboard with a copper pad round every hole (single-sided is fine), 2.54 mm pitch, cut to <b>70 × 40 mm</b> (27 × 15 holes)</li>
<li>Two 22-way 2.54 mm <b>female</b> header strips (cut longer strips with a knife, sacrificing one socket)</li>
<li>One 100 µF electrolytic capacitor, 10 V or more</li>
<li>Bare tinned wire (or resistor leg offcuts) for the bridges; thin insulated solid-core wire (wire-wrap or 26 AWG) for three links</li>
<li>Stranded 26 AWG hookup wire in several colours for the module wires, 22 AWG for the two power wires; female Dupont ends or crimp housings if your modules have pins</li>
<li>Two 220 Ω resistors and one 10 kΩ resistor (the same ones from the breadboard), heat-shrink</li>
<li>Soldering iron, solder, side cutters, multimeter</li></ul>
<p>Every hole has a name: its <b>column</b> number 1–27 counted from the left, then its <b>row</b> letter A–O counted from the front. Hold the board with row A toward you whenever you read the pictures.</p>''',
         pic=pic_cut(), shots=[('kit', 'The parts for the board: the perfboard, two 22-way female headers, the 100 µF capacitor, the resistors for the lid, bare wire for the bridges and hookup wire in several colours.')])
    step('bridges', 'Solder bridges on the underside', '25 min',
         'Turn the board over <b>left to right</b>, so row A is still toward you; column 1 is now on your right. That is how the underside pictures are drawn. '
         'Make each grey line by laying bare wire across the pads and soldering it to every pad it crosses (or by flooding solder from pad to pad on short ones).',
         pic=pic_bridges(),
         shots=[('rails', 'Start with the three power rails: one straight piece of bare wire down each of columns 1, 2 and 3, soldered at all 15 pads. Seen from underneath, so column 1 is on the right.'),
                ('bridges', 'Then the short bridges: rows A to C at the front and M to O at the back, one for each ESP32 pin that has a wire.'),
                ('bridges-close', 'Close up: the bare wire lies flat on the pads, with a small shiny fillet of solder at every pad it crosses. No solder may join one column to the next.')],
         after=f'''<ul>
<li><b>Columns 1, 2 and 3, all 15 holes A–O:</b> the power rails. Column 1 is ground, column 2 is 3.3 V, column 3 is 5 V. Long runs are easiest with one piece of bare wire.</li>
<li><b>Rows A–B–C in columns {", ".join(map(str, SIG_COLS_FRONT))}:</b> each joins an ESP32 pin (row C, under its socket) to the hole two rows in front of it, where that pin's wire will go.</li>
<li><b>Rows M–N–O in columns {", ".join(map(str, SIG_COLS_BACK))}:</b> the same for the back row of pins.</li>
<li>Columns not listed get no bridge: those ESP32 pins aren't used.</li></ul>''',
         test='With the meter on continuity (beep): touch the probes to 1A and 1O (beeps), 1A and 2A (<b>no beep</b>), 2A and 3A (no beep), then 7A to 8A (no beep) for each pair of neighbouring signal columns. A beep between neighbours means a solder bridge where it shouldn\'t be: clean it with desoldering braid.')
    step('links', 'Three insulated links on the underside', '10 min',
         'These connect the ESP32\'s power pins to the rails. Use insulated wire: each one crosses other bridges. Strip only the ends.',
         pic=pic_links(),
         shots=[('links', 'The three links, still from underneath: the short black one is ground (4M to 1M), the short orange one is 3.3 V (4C to 2C), and the long red one is 5 V (24C to 3K), across the middle.')],
         after='<ul>' + ''.join(f'<li><b>{a} → {b}</b>: {esc(lab)}.</li>' for a, b, lab, _ in LINKS) + '</ul>'
               '<p>The 5 V link is the long one: run it across the middle of the board, where nothing else is soldered.</p>',
         test='Beep test: 4C to 2O (3.3 V), 4M to 1A (ground), 24C to 3A (5 V). Then 1A to 2A and 1A to 3A must still be silent.')
    step('headers', 'Sockets for the ESP32, and the capacitor', '15 min',
         'Back to the top side. Push the two 22-way female headers into rows <b>C</b> and <b>M</b>, columns <b>4 to 25</b>. '
         'Tip: plug them onto the ESP32 first and use the ESP32 as a jig, so they are exactly the right distance apart; solder one pin at each end, take the ESP32 out, then solder the rest.',
         pic=pic_top(),
         shots=[('jig', 'The jig trick: plug both headers onto the ESP32, then drop the whole thing into rows C and M, columns 4 to 25. Solder one pin at each end of each header from underneath, then lift the ESP32 off.'),
                ('headers', 'Headers soldered, and the 100 µF capacitor standing in 3A (+) and 1A (−, the striped side). Its body covers pads 2A and 2B: nothing else goes there.')],
         after='<p><b>100 µF capacitor:</b> long leg (+) in <b>3A</b> (5 V), short leg and the stripe (−) in <b>1A</b> (ground). It steadies the 5 V for the amplifier. Solder it flat to the board or standing: keep it under 11 mm tall.</p>',
         test='Beep test, top side: each socket pin you bridged beeps to its pad two rows out (for example the socket in 7C to pad 7A). The socket in 4C beeps to column 2, 4M to column 1, 24C to column 3.',
         warn='Don\'t plug the ESP32 in yet.')
    for g in GROUPS:
        extra = ''
        if g['id'] == 'lid':
            extra = ('<p>The three lid buttons, both alarm lights and the light sensor share one ground wire and the light sensor takes the only 3.3 V. '
                     'Solder the <b>220 Ω</b> resistors in the light wires right at each button\'s LED + tab and the <b>10 kΩ</b> from the light sensor\'s signal leg to ground at the sensor, '
                     'each covered with heat-shrink. That keeps the board simple.</p><div class="pic">' + pic_lid() + '</div>')
        if g['id'] == 'bat':
            extra = '<p>Skip this group if you are not fitting the battery. The gauge\'s SDA and SCL go into <b>7N</b> and <b>8N</b>, right next to the clock module\'s 7O and 8O: same pins, two wires.</p>'
        if g['id'] == 'power':
            extra = ('<p>Use 22 AWG for these two. With the battery: from the boost\'s <b>VOUT</b> and <b>GND</b>. Without it: straight from the USB-C breakout\'s <b>VBUS</b> and <b>GND</b>.</p>')
        step(g['id'], f'Wires: {g["name"]}', '10 min',
             f'Wires for {esc(g["to"])}. Cut each long enough to reach with the board in place in the case and the lid lifted off (about 15 cm for most; 25 cm for the lid and the projector, which has to reach the barrel\'s end). '
             'Strip 3 mm, push it into the pad from the top and solder it underneath. Label the far ends with tape as you go.',
             pic=pic_group(g['id']), after=wire_table(g) + extra,
             shots=[(f'g-{g["id"]}', f'The {SHORT[g["id"]]} wires in colour; earlier wires are shown pale. '
                     'Wires on the power columns leave to the left, wires in row A leave over the front edge, and wires in rows N and O leave over the back edge.')])
    step('all', 'All the wires at once', '–', 'For checking: every wire and its pad. Wires leaving the front edge (row A) go to the modules at the front and the lid; the left column (rails) carries power and ground; the back edge (rows N and O) goes to the clock module, the alarm lights and the battery boards.',
         pic=pic_all(),
         shots=[('all', 'Every wire in place, before the ESP32 goes in.'),
                ('all-under', 'The underside when it\'s finished: the three rails, the short bridges, the three links, and a joint at every header pin and wire.')],
         mid='''<h3>Turn it round</h3><p>Drag to turn the finished board, scroll or pinch to zoom.</p>
<div class="pb3d"><canvas id="pb3d"></canvas><div class="pb3dbar">
<button type="button" data-v="top">Top</button><button type="button" data-v="under">Underside</button><button type="button" data-v="esp">Take the ESP32 out</button></div></div>''')
    step('move', 'Move the ESP32 over and test, one module at a time', '30 min',
         'With nothing plugged into the sockets, check once more that 1, 2 and 3 don\'t beep to each other. Then:',
         after='''<ol>
<li>Unplug the USB cable and lift the ESP32 off the breadboard. Plug it into the perfboard's sockets with its antenna end over column 4 and its USB ports at column 25. Every pin must be in a socket: count that 22 pins sit in each row.</li>
<li>Connect only the power wires and the <b>front display</b>. Power it from the USB-C supply. The front display shows the time within 30 seconds.</li>
<li>Add the modules one at a time, powering off between each: projector display, amplifier, clock module, lid, button B, battery boards. After each, run that module's test from the <a href="breadboard.html">breadboard guide</a>.</li>
<li>Open the clock's web page: status should show the clock module found, and with the battery boards a Battery line.</li></ol>''',
         shots=[('esp32', 'The ESP32 in its sockets: antenna end over column 4, USB ports at the right. 22 pins in each row.'),
                ('esp32-back', 'From the back right: the USB ports, the back edge\'s wires to the clock module, alarm lights and battery boards, and the power-in pair on the left.')],
         test='Everything that worked on the breadboard works here. If one module doesn\'t, its wires are the only new thing: beep each one from the module\'s pin to its pad.',
         warn='Never plug the USB-C supply and the ESP32\'s own USB port into power at the same time.')
    step('fit', 'Into the case', '10 min',
         'The board sits on the four pads at the front right of the base, ESP32 USB end toward the right wall, row A toward the front. Press it down until the two hooks on each short side click over its edges. '
         'Route the lid and projector wires up the right side, leave the battery and clock-module wires along the floor, and keep everything clear of the barrel, which turns. '
         'See the <a href="assembly.html">assembly steps</a> for the rest.',
         shots=[('incase', 'Where it ends up: the board at the front right of the base, ESP32 on top, with the battery, the floor modules and the wiring around it.')])
    toc = ''.join(f'<a href="#{s["sid"]}"><span>{i + 1}</span>{esc(re.sub("<[^>]+>", "", s["title"]))}</a>' for i, s in enumerate(steps))
    secs = ''.join(f'''
<section class="bbstep" id="{s['sid']}">
  <div class="bbhead"><span class="num">{i + 1}</span><h2>{s['title']}</h2><span class="time">⏱ {s['time']}</span></div>
  <p>{s['intro']}</p>
  {f'<div class="warn">⚠️ {s["warn"]}</div>' if s['warn'] else ''}
  {''.join(f'<figure class="shot"><img src="img/pb-{n}.jpg?v={IMGV}" alt="{esc(re.sub("<[^>]+>", "", c))}" width="1400" height="875" loading="lazy"><figcaption>{c}</figcaption></figure>' for n, c in s['shots'])}
  {f'<figure class="pic"><figcaption class="maptitle">Hole map</figcaption>{s["pic"]}</figure>' if s['pic'] else ''}
  {s['after']}
  {s['mid']}
  {f'<div class="test"><b>✅ Check:</b> {s["test"]}</div>' if s['test'] else ''}
</section>''' for i, s in enumerate(steps))
    return f'''<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Perfboard · Ceiling Clock</title>
<link rel="stylesheet" href="style.css?v=20261030w">
<script type="importmap">{{"imports":{{"three":"./vendor/three.module.min.js","three/addons/":"./vendor/addons/"}}}}</script>
<style>
.pbsvg{{width:100%;height:auto;display:block;border:1px solid var(--line);border-radius:12px;background:#fbfaf6}}
.toc{{display:flex;flex-wrap:wrap;gap:6px;margin:14px 0 6px}}
.toc a{{display:flex;align-items:center;gap:6px;border:1px solid var(--line);border-radius:999px;padding:4px 10px 4px 4px;text-decoration:none;color:inherit;font-size:.88rem;background:var(--paper)}}
.toc a span{{display:inline-grid;place-items:center;width:22px;height:22px;border-radius:50%;background:#e8743b;color:#fff;font-weight:700;font-size:.8rem}}
.bbstep{{border:1px solid var(--line);border-radius:16px;padding:18px 18px 10px;margin:22px 0;background:var(--paper)}}
.bbhead{{display:flex;align-items:center;gap:12px}}.bbhead h2{{margin:0;flex:1}}
.bbhead .num{{display:grid;place-items:center;width:38px;height:38px;border-radius:50%;background:#e8743b;color:#fff;font-weight:800;font-size:1.1rem}}
.time{{color:var(--mut);font-size:.9rem}}
.pic{{margin:10px 0}}
.shot{{margin:12px 0 16px}}.shot img{{width:100%;height:auto;display:block;border-radius:12px;border:1px solid var(--line);background:#2a5444}}
.shot figcaption{{color:var(--mut);font-size:.93rem;margin-top:6px;line-height:1.45}}
.maptitle{{font-weight:700;font-size:.9rem;color:var(--mut);margin:4px 0 6px}}
.pb3d{{position:relative;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:#e9e6df;margin:8px 0 16px}}
.pb3d canvas{{display:block;width:100%;aspect-ratio:16/10;touch-action:none;cursor:grab}}
.pb3dbar{{position:absolute;left:10px;bottom:10px;display:flex;gap:6px;flex-wrap:wrap}}
.pb3dbar button{{border:1px solid var(--line);background:#fbfaf6;border-radius:999px;padding:6px 12px;font:inherit;font-size:.88rem;cursor:pointer}}
.pb3dbar button[aria-pressed=true]{{background:#e8743b;color:#fff;border-color:#e8743b}}
.pins{{border-collapse:collapse;margin:8px 0 14px}}.pins td,.pins th{{border:1px solid var(--line);padding:5px 10px;text-align:left}}.pins th{{background:#f3f1ea}}
.sw{{display:inline-block;width:10px;height:16px;border-radius:3px;margin-right:8px;vertical-align:-3px}}
.test{{background:#eef7ee;border:1px solid #cfe6cf;border-radius:10px;padding:10px 12px;margin:10px 0}}
.warn{{background:#fff4e5;border:1px solid #f2d3a6;border-radius:10px;padding:10px 12px;margin:10px 0}}
</style>
</head><body>
<header class="site"><div class="in">
<a class="brand" href="index.html"><span class="dot"></span>Ceiling Clock</a>
<nav><a href="index.html">3D model</a><a href="printing.html">Printing</a><a href="assembly.html">Assembly</a><a href="wiring.html">Wiring</a><a href="breadboard.html">Breadboard test</a><a href="perfboard.html" class="on">Perfboard</a><a href="parts.html">Parts</a><a href="demo/">Live demo</a><a href="firmware.html">Firmware &amp; use</a><a href="https://github.com/ScottYates/ceilingclock">GitHub</a></nav>
</div></header>
<main class="in">
<h1>Wiring the perfboard</h1>
<p class="lead">From the breadboard to the board that goes in the case: about two and a half hours of soldering. Each step has a picture of the board as it should look when the step is done, and a hole map underneath that names every hole used, by its column (1–27) and row (A–O). Both are drawn from the same layout, to scale. At the end you can turn the finished board round in 3D.</p>
<nav class="toc">{toc}</nav>
{secs}
</main>
<script src="js/declutter.js?v=4"></script>
<script type="module">
import * as THREE from 'three';
import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
import {{ makeStudio, v }} from './js/pbscene.js?v={IMGV}';
const cv = document.getElementById('pb3d');
if (cv) {{
  const st = makeStudio(cv, {{ width: cv.clientWidth, height: cv.clientWidth * 10 / 16, shadows: false }});
  st.mat.visible = false;
  st.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  const ctl = new OrbitControls(st.camera, cv);
  ctl.enableDamping = true; ctl.minDistance = 40; ctl.maxDistance = 400;
  let need = true; ctl.addEventListener('change', () => need = true);
  // Underside turns the board over left to right, as you would in your hands: row A stays toward you, column 1 goes right
  const pivot = new THREE.Group(); pivot.position.copy(v(35, 20, 0.8)); st.scene.add(pivot);
  let flipTo = 0, anim = null;
  function go(k) {{
    if (k === 'top' || k === 'under') {{ flipTo = k === 'under' ? Math.PI : 0; anim = performance.now(); }}
    st.look([35, -70, 95], [35, 20, 4], 32); ctl.target.copy(v(35, 20, 4)); ctl.update(); need = true;
  }}
  let started = false;
  const start = async () => {{
    if (started) return; started = true;
    await st.load('models/perfboard.glb?v={IMGV}', 0);
    pivot.add(st.model); st.model.position.copy(pivot.position).negate(); go('top');
    const esp = []; st.model.traverse(o => {{ if (o.isMesh && /^esp32_/.test(o.name)) esp.push(o); }});
    document.querySelectorAll('.pb3dbar button').forEach(b => b.addEventListener('click', () => {{
      if (b.dataset.v === 'esp') {{ const out = b.getAttribute('aria-pressed') !== 'true'; b.setAttribute('aria-pressed', out); esp.forEach(o => o.visible = !out); b.textContent = out ? 'Put the ESP32 in' : 'Take the ESP32 out'; need = true; }}
      else go(b.dataset.v);
    }}));
    (function loop(t) {{
      requestAnimationFrame(loop); ctl.update();
      if (anim !== null) {{
        const d = flipTo - pivot.rotation.z;
        if (Math.abs(d) < 0.01) {{ pivot.rotation.z = flipTo; anim = null; }} else pivot.rotation.z += d * 0.16;
        need = true;
      }}
      if (need) {{ st.render(); need = false; }}
    }})();
  }};
  new IntersectionObserver((es, o) => {{ if (es.some(e => e.isIntersecting)) {{ o.disconnect(); start(); }} }}, {{ rootMargin: '300px' }}).observe(cv);
  addEventListener('resize', () => {{ st.renderer.setSize(cv.clientWidth, cv.clientWidth * 10 / 16, false); st.camera.aspect = 1.6; st.camera.updateProjectionMatrix(); need = true; }});
}}
</script>
</body></html>'''


if __name__ == '__main__':
    open(OUT, 'w').write(page())
    print('wrote', os.path.relpath(OUT))
