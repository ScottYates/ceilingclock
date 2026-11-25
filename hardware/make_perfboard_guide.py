#!/usr/bin/env python3
"""Builds docs/perfboard.html: moving the clock from the breadboard to its perfboard.

Scott's board (2026-11-25): a 70 x 50 mm double-sided prototype board, 24 x 18 plated holes on a 2.54 mm grid,
used whole. Columns A-X left to right, rows 1-18 front to back (row 1 is the edge nearest the clock's front), as
printed on the board. The ESP32 plugs into two 22-way female headers in rows 3 and 13, columns B-W. The three
power rails run left to right along the back: row 16 is 5 V, row 17 is 3.3 V, row 18 is ground.
The same layout is in hardware/components.scad (ref_perfboard) and hardware/pb_model.py (the pictures).
"""
import html, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'docs', 'perfboard.html')
PINS = open(os.path.join(HERE, '..', 'firmware', 'src', 'pins.h')).read()
G = lambda n: int(re.search(r'#define\s+%s\s+(\d+)' % n, PINS).group(1))

IMGV = '20261125a'           # cache-buster for the rendered pictures and model
COLS, ROWS = 24, 18
CL = 'ABCDEFGHIJKLMNOPQRSTUVWX'
BW, BH = 70.0, 50.0
P = 2.54
X0 = (BW - (COLS - 1) * P) / 2   # column A from the left edge, mm
Y0 = (BH - (ROWS - 1) * P) / 2   # row 1 from the front edge
J1 = ['3V3', '3V3', 'RST', '4', '5', '6', '7', '15', '16', '17', '18', '8', '3', '46', '9', '10', '11', '12', '13', '14', '5V', 'G']
J3 = ['G', 'TX', 'RX', '1', '2', '42', '41', '40', '39', '38', '37', '36', '35', '0', '45', '48', '47', '21', '20', '19', 'G', 'G']
HC0 = 2                       # header column of the first pin (B)
ROW_J1, ROW_J3 = 3, 13
V5, V33, GND = 16, 17, 18     # rail rows
RAIL = {V5: '5 V', V33: '3.3 V', GND: 'ground'}


def pname(c, r):
    return f'{CL[c - 1]}{r}'


def pad(name):                # 'G1' -> (7, 1)
    m = re.match(r'([A-X])(\d+)$', name)
    return CL.index(m.group(1)) + 1, int(m.group(2))


def col_of(gpio):
    s = str(gpio)
    if s in J1: return HC0 + J1.index(s), ROW_J1
    return HC0 + J3.index(s), ROW_J3


# ---------------------------------------------------------------- what goes where
def sig(gpio, row=None):
    c, r = col_of(gpio)
    if row is None: row = 1 if r == ROW_J1 else 15
    return pname(c, row)

# Power and ground wires go into the rails, one wire per column, in columns that nothing else on the back rows
# uses (so no wire leaving over the back edge passes over another wire's hole).
RAIL_COLS = iter([4] + list(range(9, 22)) + [23, 24])   # D, I-U, W, X  (A-C: capacitor and links; E-H: back pins; V: 5 V link)
def rail(row):
    return pname(next(RAIL_COLS), row)

GROUPS = [
    dict(id='front', name='Front display', to='the TM1637 behind the front window', color='#c0392b', wires=[
        ('CLK', sig(G('PIN_TM_CLK')), f'GPIO {G("PIN_TM_CLK")}', '#7d3c98'), ('DIO', sig(G('PIN_TM_DIO')), f'GPIO {G("PIN_TM_DIO")}', '#2e86c1'),
        ('VCC', rail(V33), '3.3 V', '#e67e22'), ('GND', rail(GND), 'ground', '#222')]),
    dict(id='proj', name='Projector display', to='the TM1637 in the barrel (out past the display holder)', color='#c0392b', wires=[
        ('CLK', sig(G('PIN_PROJ_CLK')), f'GPIO {G("PIN_PROJ_CLK")}', '#7d3c98'), ('DIO', sig(G('PIN_PROJ_DIO')), f'GPIO {G("PIN_PROJ_DIO")}', '#2e86c1'),
        ('VCC', rail(V33), '3.3 V', '#e67e22'), ('GND', rail(GND), 'ground', '#222')]),
    dict(id='amp', name='Amplifier', to='the MAX98357A on the floor', color='#1f618d', wires=[
        ('BCLK', sig(G('PIN_I2S_BCLK')), f'GPIO {G("PIN_I2S_BCLK")}', '#17a589'), ('LRC', sig(G('PIN_I2S_LRC')), f'GPIO {G("PIN_I2S_LRC")}', '#d4ac0d'),
        ('DIN', sig(G('PIN_I2S_DOUT')), f'GPIO {G("PIN_I2S_DOUT")}', '#ca6f1e'), ('VIN', rail(V5), '5 V', '#e74c3c'), ('GND', rail(GND), 'ground', '#222')]),
    dict(id='rtc', name='Clock module (DS3231)', to='the DS3231 on the floor', color='#1f4e8c', wires=[
        ('SDA', sig(G('PIN_SDA')), f'GPIO {G("PIN_SDA")}', '#2e86c1'), ('SCL', sig(G('PIN_SCL')), f'GPIO {G("PIN_SCL")}', '#d4ac0d'),
        ('VCC', rail(V33), '3.3 V', '#e67e22'), ('GND', rail(GND), 'ground', '#222')]),
    dict(id='lid', name='Lid: buttons, lights and light sensor', to='the lid (see the lid harness below)', color='#5b2c6f', wires=[
        ('Snooze', sig(G('PIN_BTN_A')), f'GPIO {G("PIN_BTN_A")}', '#16a085'), ('Alarm 1 button', sig(G('PIN_BTN_AL1')), f'GPIO {G("PIN_BTN_AL1")}', '#8e44ad'),
        ('Alarm 2 button', sig(G('PIN_BTN_AL2')), f'GPIO {G("PIN_BTN_AL2")}', '#00acc1'), ('Light sensor', sig(G('PIN_LDR')), f'GPIO {G("PIN_LDR")}', '#7f8c8d'),
        ('Alarm 1 light', sig(G('PIN_LED_AL1')), f'GPIO {G("PIN_LED_AL1")}', '#a04000'), ('Alarm 2 light', sig(G('PIN_LED_AL2')), f'GPIO {G("PIN_LED_AL2")}', '#95a5a6'),
        ('3.3 V', rail(V33), '3.3 V', '#e67e22'), ('GND', rail(GND), 'ground', '#222')]),
    dict(id='btnb', name='Button B', to='the button on the left wall', color='#5b2c6f', wires=[
        ('Button B', sig(G('PIN_BTN_B')), f'GPIO {G("PIN_BTN_B")}', '#27ae60'), ('GND', rail(GND), 'ground', '#222')]),
    dict(id='bat', name='Battery boards (optional)', to='the charger and fuel gauge beside the battery', color='#1d1d1d', wires=[
        ('Charger CE', sig(G('PIN_CHG_CE')), f'GPIO {G("PIN_CHG_CE")}', '#e91e63'), ('Charger PGOOD', sig(G('PIN_PGOOD')), f'GPIO {G("PIN_PGOOD")}', '#43a047'),
        ('Charger GND', rail(GND), 'ground', '#222'), ('Gauge SDA', sig(G('PIN_SDA'), row=14), f'GPIO {G("PIN_SDA")}', '#2e86c1'),
        ('Gauge SCL', sig(G('PIN_SCL'), row=14), f'GPIO {G("PIN_SCL")}', '#d4ac0d'), ('Gauge VIN', rail(V33), '3.3 V', '#e67e22'), ('Gauge GND', rail(GND), 'ground', '#222')]),
    dict(id='power', name='Power in', to='the 5 V boost (or straight to the USB-C breakout without the battery)', color='#c0392b', wires=[
        ('5 V in', rail(V5), '5 V', '#e74c3c'), ('GND in', rail(GND), 'ground', '#222')]),
]
SHORT = dict(front='front display', proj='projector display', amp='amplifier', rtc='clock module', lid='lid', btnb='button B',
             bat='battery boards', power='power-in')
SIG_COLS_FRONT = sorted({pad(w[1])[0] for g in GROUPS for w in g['wires'] if pad(w[1])[1] == 1})
SIG_COLS_BACK = sorted({pad(w[1])[0] for g in GROUPS for w in g['wires'] if pad(w[1])[1] in (14, 15)})
CAP = ('A16', 'A18')          # 100 uF: + in A16 (5 V), - in A18 (ground); its body sits over A17 and B17
LINKS = [('C3', 'C17', '3.3 V: the ESP32\'s 3V3 pin to the 3.3 V rail', '#e67e22'),
         ('B13', 'B18', 'ground: the ESP32\'s G pin to the ground rail', '#222'),
         ('V3', 'V16', '5 V: the ESP32\'s 5V pin to the 5 V rail', '#e74c3c')]
KEEP_CLEAR = {'A17', 'B17'}   # under the capacitor

# sanity: every pad used once, signal pads in a bridged column, header pins are what the wires say, and at most one
# wire per column on the power rows (two back-pin wires may share a column: rows 14 and 15)
used = {}
for g in GROUPS:
    for w in g['wires']:
        assert w[1] not in used, (w, used.get(w[1])); used[w[1]] = w
for p_ in CAP + tuple(l[0] for l in LINKS) + tuple(l[1] for l in LINKS) + tuple(KEEP_CLEAR):
    assert p_ not in used, p_; used[p_] = p_
back_cols = {}
SIG_COLS_BACK = sorted({pad(w[1])[0] for g in GROUPS for w in g['wires'] if pad(w[1])[1] in (14, 15)})
for g in GROUPS:
    for label, p_, what, _ in g['wires']:
        c, r = pad(p_)
        if r in RAIL:
            assert RAIL[r] == what, (label, p_, what)
        else:
            hdr = J1 if r <= ROW_J1 else J3
            assert hdr[c - HC0] == what.split()[-1], (label, p_, hdr[c - HC0], what)
        if r in RAIL:                                 # a rail wire's column has nothing else on the back rows
            assert c not in back_cols, (p_, back_cols.get(c)); back_cols[c] = p_
for c in SIG_COLS_BACK:
    assert c not in back_cols, (pname(c, 15), back_cols[c])
for a, b, lab, _ in LINKS:
    assert pad(a)[0] == pad(b)[0]                     # links run straight along a column
    assert (J1 if pad(a)[1] == ROW_J1 else J3)[pad(a)[0] - HC0] in ('3V3', 'G', '5V')


# ---------------------------------------------------------------- drawing
S = 11.0                       # px per mm
MX, MY = 190, 150              # margins around the board in the picture (MY = top)
MB = 175                       # bottom margin
W_ = int(BW * S + 2 * MX); H_ = int(BH * S + MY + MB)
GREEN, GREEN_D = '#1f6b45', '#174f33'

def hx(c, bottom=False):
    x = X0 + (c - 1) * P
    if bottom: x = BW - x
    return MX + x * S

def hy(r):
    return MY + (BH - (Y0 + (r - 1) * P)) * S

def esc(s): return html.escape(str(s), quote=True)

def svg_open(title):
    return [f'<svg viewBox="0 0 {W_} {H_}" class="pbsvg" role="img" aria-label="{esc(title)}" xmlns="http://www.w3.org/2000/svg" font-family="system-ui,sans-serif">',
            '<defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M1 1L9 5L1 9z" fill="#e8743b"/></marker></defs>']

def board(o, bottom=False, label=True, dim=False):
    o.append(f'<rect x="{MX}" y="{MY}" width="{BW*S}" height="{BH*S}" rx="6" fill="{GREEN if not bottom else GREEN_D}" stroke="#0e3a24" stroke-width="2"/>')
    for x in (2.0, BW - 2.0):                         # corner mounting holes
        for y in (2.0, BH - 2.0):
            o.append(f'<circle cx="{MX + x*S:.1f}" cy="{MY + y*S:.1f}" r="{1.1*S:.1f}" fill="#fbfaf6" stroke="#0e3a24"/>')
    for c in range(1, COLS + 1):
        for r in range(1, ROWS + 1):
            o.append(f'<circle cx="{hx(c, bottom):.1f}" cy="{hy(r):.1f}" r="5.6" fill="#cfd4d8" stroke="#8b939a" stroke-width="1"/>'
                     f'<circle cx="{hx(c, bottom):.1f}" cy="{hy(r):.1f}" r="2.2" fill="#26302b"/>')
    if label:
        for c in range(1, COLS + 1):
            for y in (MY - 10, MY + BH*S + 22):
                o.append(f'<text x="{hx(c, bottom):.1f}" y="{y}" text-anchor="middle" font-size="13" font-weight="700" fill="#555">{CL[c - 1]}</text>')
        for r in range(1, ROWS + 1):
            for xl in (MX - 16, MX + BW * S + 16):
                o.append(f'<text x="{xl}" y="{hy(r) + 5:.1f}" text-anchor="middle" font-size="13" fill="#555">{r}</text>')
        o.append(f'<text x="{MX + BW*S/2}" y="{H_ - 14}" text-anchor="middle" font-size="15" font-weight="700" fill="#b9471c">▼ FRONT edge, row 1 (toward the clock\'s front)</text>')
        o.append(f'<text x="16" y="24" font-size="15" font-weight="700" fill="#444">{"UNDERSIDE (solder side): the board turned over left to right" if bottom else "TOP (parts side)"}</text>')
    if dim:
        o.append(f'<rect x="{MX}" y="{MY}" width="{BW*S}" height="{BH*S}" rx="6" fill="#fff" opacity=".45"/>')

def bridge(o, a, b, bottom=True, color='#e9edf0', w=9, new=True):
    (c1, r1), (c2, r2) = pad(a), pad(b)
    o.append(f'<line x1="{hx(c1, bottom):.1f}" y1="{hy(r1):.1f}" x2="{hx(c2, bottom):.1f}" y2="{hy(r2):.1f}" stroke="{color}" stroke-width="{w}" stroke-linecap="round" opacity="{1 if new else .45}"/>')
    if new:
        o.append(f'<line x1="{hx(c1, bottom):.1f}" y1="{hy(r1):.1f}" x2="{hx(c2, bottom):.1f}" y2="{hy(r2):.1f}" stroke="#7d868d" stroke-width="2" stroke-linecap="round" opacity=".7"/>')

def ring(o, p_, bottom=False, color='#e8743b'):
    c, r = pad(p_)
    o.append(f'<circle cx="{hx(c, bottom):.1f}" cy="{hy(r):.1f}" r="9" fill="none" stroke="{color}" stroke-width="3"/>')

def link(o, a, b, color, label=None, k=0):
    (c1, r1), (c2, r2) = pad(a), pad(b)
    x1, y1, x2, y2 = hx(c1, True), hy(r1), hx(c2, True), hy(r2)
    bow = -12 if c1 < 12 else 12                             # bowed a little to one side, off the pads it crosses
    d = f'M{x1:.1f},{y1:.1f} C{x1 + bow:.1f},{y1 - 20:.1f} {x2 + bow:.1f},{y2 + 20:.1f} {x2:.1f},{y2:.1f}'
    o.append(f'<path d="{d}" fill="none" stroke="#111" stroke-width="7" stroke-linecap="round"/>')
    o.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="5" stroke-linecap="round"/>')
    for x, y in ((x1, y1), (x2, y2)): o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="#e9edf0" stroke="#666"/>')

def rails(o, bottom=True, new=True, names=True):
    for r, nm, col in ((V5, 'row 16 = 5 V', '#c0392b'), (V33, 'row 17 = 3.3 V', '#b9600c'), (GND, 'row 18 = ground', '#333')):
        bridge(o, pname(1, r), pname(COLS, r), bottom, new=new)
        if names and new:
            o.append(f'<text x="{MX + BW*S + 34}" y="{hy(r) + 5:.1f}" font-size="12.5" font-weight="800" fill="{col}">{nm}</text>')

def headers(o, new=True):
    for r in (ROW_J1, ROW_J3):
        x = hx(HC0) - 1.27 * S; y = hy(r) - 1.27 * S
        o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{22*P*S:.1f}" height="{P*S:.1f}" rx="3" fill="#1b1b1b" opacity="{1 if new else .5}"/>')
        for i in range(22):
            o.append(f'<rect x="{hx(HC0 + i) - 3:.1f}" y="{hy(r) - 3:.1f}" width="6" height="6" fill="#555"/>')
        names = J1 if r == ROW_J1 else J3
        for i, nme in enumerate(names):
            o.append(f'<text x="{hx(HC0 + i):.1f}" y="{hy(r) + (24 if r == ROW_J1 else -16):.1f}" text-anchor="middle" font-size="10.5" font-weight="700" fill="{"#fff" if not new else "#f4f1e6"}" opacity="{.95 if new else .6}">{esc(nme)}</text>')
    cx = (hx(HC0) + hx(HC0 + 21))/2; cy = (hy(ROW_J1) + hy(ROW_J3))/2
    o.append(f'<rect x="{cx - 230:.1f}" y="{cy - 16:.1f}" width="460" height="30" rx="8" fill="#fbfaf6" opacity=".88"/>'
             f'<text x="{cx:.1f}" y="{cy + 5:.1f}" text-anchor="middle" font-size="15" font-weight="600" fill="#1d4d34">ESP32 plugs in here: antenna end left, USB end right</text>')

def capacitor(o, new=True):
    (c1, r1), (c2, r2) = pad(CAP[0]), pad(CAP[1])
    cx = (hx(c1) + hx(c2)) / 2; cy = (hy(r1) + hy(r2)) / 2
    R = 3.15 * S
    o.append(f'<g opacity="{1 if new else .55}"><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{R:.1f}" fill="#1f4e8c" stroke="#0c2a4f" stroke-width="2"/>'
             f'<path d="M{cx - R:.1f},{cy:.1f} A{R:.1f},{R:.1f} 0 0 1 {cx + R:.1f},{cy:.1f} L{cx + 2.4*S:.1f},{cy - 1.0*S:.1f} L{cx - 2.4*S:.1f},{cy - 1.0*S:.1f}z" fill="#d6dbe2"/>'
             f'<text x="{cx:.1f}" y="{cy - 1.6*S:.1f}" text-anchor="middle" font-size="16" font-weight="800" fill="#1f4e8c">−</text>'
             f'<text x="{cx:.1f}" y="{cy + 1.4*S:.1f}" text-anchor="middle" font-size="12" font-weight="800" fill="#fff">100µF</text></g>')

def wire_out(o, p_, color, label, k=0, n=1, bold=True):
    c, r = pad(p_)
    x, y = hx(c), hy(r)
    if r == 1:                                     # front edge
        ex, ey = x, MY + BH * S + 30
    else:                                          # back edge
        ex, ey = x, MY - 28
    pts = f'{x:.1f},{y:.1f} {ex:.1f},{ey:.1f}'
    o.append(f'<polyline points="{pts}" fill="none" stroke="#111" stroke-width="6.5" stroke-linecap="round" stroke-linejoin="round"/>')
    o.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>')
    o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#e9edf0" stroke="#555"/>')
    if label:
        if r == 1:
            o.append(f'<line x1="{ex:.1f}" y1="{ey:.1f}" x2="{ex:.1f}" y2="{ey + 8 + (k % 4) * 17:.1f}" stroke="#999" stroke-width="1"/>'
                     f'<text x="{ex:.1f}" y="{ey + 22 + (k % 4) * 17:.1f}" text-anchor="middle" font-size="12.5" font-weight="700" fill="#222">{esc(label)} · {p_}</text>')
        else:
            o.append(f'<line x1="{ex:.1f}" y1="{ey:.1f}" x2="{ex:.1f}" y2="{ey - 6 - (k % 4) * 17:.1f}" stroke="#999" stroke-width="1"/>'
                     f'<text x="{ex:.1f}" y="{ey - 10 - (k % 4) * 17:.1f}" text-anchor="middle" font-size="12.5" font-weight="700" fill="#222">{esc(label)} · {p_}</text>')


def pic_board():
    o = svg_open('The board: 24 by 18 holes')
    board(o)
    o.append(f'<rect x="{MX + BW*S/2 - 260}" y="{MY + BH*S/2 - 40}" width="520" height="74" rx="10" fill="#fbfaf6" opacity=".93"/>')
    o.append(f'<text x="{MX + BW*S/2}" y="{MY + BH*S/2 - 10}" text-anchor="middle" font-size="22" font-weight="800" fill="#1d4d34">70 × 50 mm · 24 × 18 holes, used whole</text>')
    o.append(f'<text x="{MX + BW*S/2}" y="{MY + BH*S/2 + 20}" text-anchor="middle" font-size="15" fill="#1d4d34">a hole is its column letter, then its row number: the ringed one is E1</text>')
    ring(o, 'E1')
    return '\n'.join(o) + '</svg>'

def pic_bridges():
    o = svg_open('Underside: solder bridges')
    board(o, bottom=True)
    rails(o)
    for c in SIG_COLS_FRONT: bridge(o, pname(c, 1), pname(c, ROW_J1))
    for c in SIG_COLS_BACK: bridge(o, pname(c, ROW_J3), pname(c, 15))
    return '\n'.join(o) + '</svg>'

def pic_links():
    o = svg_open('Underside: three insulated links')
    board(o, bottom=True)
    rails(o, new=False)
    for c in SIG_COLS_FRONT: bridge(o, pname(c, 1), pname(c, ROW_J1), new=False)
    for c in SIG_COLS_BACK: bridge(o, pname(c, ROW_J3), pname(c, 15), new=False)
    for k, (a, b, lab, colr) in enumerate(LINKS):
        link(o, a, b, colr, lab, k)
    return '\n'.join(o) + '</svg>'

def pic_top():
    o = svg_open('Top: headers and capacitor')
    board(o)
    headers(o)
    capacitor(o)
    return '\n'.join(o) + '</svg>'

def _lev(wires):
    lev = {}
    for edge in ('front', 'back'):
        ws = sorted((w for w in wires if (pad(w[1])[1] == 1) == (edge == 'front')), key=lambda w: pad(w[1])[0])
        for i, w in enumerate(ws): lev[w[1]] = i % 4
    return lev

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
    lev = _lev(g['wires'])
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
    L = {w[0]: w[1] for w in next(g for g in GROUPS if g['id'] == 'lid')['wires']}
    o.append(f'<path d="M60,440 L940,440" stroke="#222" stroke-width="6"/><text x="60" y="470" font-size="14" font-weight="700">GND from pad {L["GND"]} — one wire, then loop it from part to part</text>')
    o.append(f'<path d="M60,90 L940,90" stroke="#e67e22" stroke-width="5"/><text x="60" y="80" font-size="14" font-weight="700" fill="#b9600c">3.3 V from pad {L["3.3 V"]} (only the light sensor needs it)</text>')
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
    btn(170, 250, 'Snooze', f'to {L["Snooze"]}', '#16a085')
    btn(450, 250, 'Alarm 1', f'to {L["Alarm 1 button"]}', '#8e44ad', f'to {L["Alarm 1 light"]}', '#a04000')
    btn(730, 250, 'Alarm 2', f'to {L["Alarm 2 button"]}', '#00acc1', f'to {L["Alarm 2 light"]}', '#95a5a6')
    # LDR
    x, y = 905, 250
    o.append(f'<text x="{x}" y="{y - 85}" text-anchor="middle" font-size="15" font-weight="800">Light sensor</text>')
    o.append(f'<ellipse cx="{x}" cy="{y - 40}" rx="16" ry="12" fill="#e8d9a8" stroke="#8a6a3b"/><path d="M{x - 6},{y - 40} L{x - 6},90 M{x + 6},{y - 40} L{x + 6},{y + 20}" stroke="#777" stroke-width="3"/>')
    o.append(f'<rect x="{x - 2}" y="{y + 30}" width="16" height="40" rx="5" fill="#d8c08c" stroke="#8a6a3b"/><text x="{x - 6}" y="{y + 55}" text-anchor="end" font-size="12" font-weight="700">10 kΩ</text>')
    o.append(f'<path d="M{x + 6},{y + 20} L{x + 6},{y + 30} M{x + 6},{y + 70} L{x + 6},440" stroke="#777" stroke-width="3"/>')
    o.append(f'<path d="M{x + 6},{y + 22} C{x - 40},{y + 40} {x - 50},{y + 120} {x - 50},{y + 170}" stroke="#7f8c8d" stroke-width="5" fill="none"/><text x="{x - 50}" y="{y + 190}" text-anchor="middle" font-size="12" font-weight="700">to {L["Light sensor"]}</text>')
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
<li>Double-sided prototype board, <b>70 × 50 mm</b>, 24 × 18 plated holes on a 2.54 mm grid, used whole: no cutting. It sits on the four posts in the base with its front and back edges overhanging them.</li>
<li>Two 22-way 2.54 mm <b>female</b> header strips (cut longer strips with a knife, sacrificing one socket)</li>
<li>One 100 µF electrolytic capacitor, 10 V or more</li>
<li>Bare tinned wire (or resistor leg offcuts) for the bridges; thin insulated solid-core wire (wire-wrap or 26 AWG) for three links</li>
<li>Stranded 26 AWG hookup wire in several colours for the module wires, 22 AWG for the two power wires; female Dupont ends or crimp housings if your modules have pins</li>
<li>Two 220 Ω resistors and one 10 kΩ resistor (the same ones from the breadboard), heat-shrink</li>
<li>Soldering iron, solder, side cutters, multimeter</li></ul>
<p>Every hole has a name, printed on the board: its <b>column</b> letter A–X counted from the left, then its <b>row</b> number 1–18 counted from the front. Hold the board with row 1 toward you, so the numbers count up away from you and the letters read left to right, whenever you read the pictures.</p>''',
         pic=pic_board(), shots=[('kit', 'The parts for the board: the 70 × 50 mm board, two 22-way female headers, the 100 µF capacitor, the resistors for the lid, bare wire for the bridges and hookup wire in several colours.')])
    step('bridges', 'Solder bridges on the underside', '25 min',
         'Turn the board over <b>left to right</b>, so row 1 is still toward you; column A is now on your right. That is how the underside pictures are drawn. '
         'Make each grey line by laying bare wire across the pads and soldering it to every pad it crosses (or by flooding solder from pad to pad on short ones).',
         pic=pic_bridges(),
         shots=[('rails', 'Start with the three power rails along the back: one straight piece of bare wire across each of rows 16, 17 and 18, soldered at all 24 pads. Seen from underneath, so column A is on the right.'),
                ('bridges', 'Then the short bridges: rows 1 to 3 at the front and 13 to 15 at the back, one for each ESP32 pin that has a wire.'),
                ('bridges-close', 'Close up: the bare wire lies flat on the pads, with a small shiny fillet of solder at every pad it crosses. No solder may join one column to the next, or row 15 to the 5 V rail behind it.')],
         after=f'''<ul>
<li><b>Rows 16, 17 and 18, all 24 holes A–X:</b> the power rails, along the back. Row 16 is 5 V, row 17 is 3.3 V, row 18 (the back edge) is ground. Use one straight piece of bare wire for each.</li>
<li><b>Rows 1–2–3 in columns {", ".join(CL[c - 1] for c in SIG_COLS_FRONT)}:</b> each joins an ESP32 pin (row 3, under its socket) to the hole two rows in front of it, where that pin's wire will go.</li>
<li><b>Rows 13–14–15 in columns {", ".join(CL[c - 1] for c in SIG_COLS_BACK)}:</b> the same for the back row of pins.</li>
<li>Columns not listed get no bridge: those ESP32 pins aren't used.</li></ul>''',
         test='With the meter on continuity (beep): A18 to X18 beeps, and the same along rows 17 and 16. A16 to A17 and A17 to A18 must <b>not</b> beep, and nor may row 15 to row 16 in columns E–H. Then E1 to F1 (no beep), and so on for each pair of neighbouring signal columns. A beep between neighbours means a solder bridge where it shouldn\'t be: clean it with desoldering braid.')
    step('links', 'Three insulated links on the underside', '10 min',
         'These connect the ESP32\'s power pins to the rails. Use insulated wire: each one crosses other bridges. Strip only the ends.',
         pic=pic_links(),
         shots=[('links', 'The three links, still from underneath, each straight along one column: orange 3.3 V from C3 to C17, black ground from B13 to B18, and red 5 V from V3 to V16. They cross the rails they don\'t join, so they must be insulated.')],
         after='<ul>' + ''.join(f'<li><b>{a} → {b}</b>: {esc(lab)}.</li>' for a, b, lab, _ in LINKS) + '</ul>'
               '<p>Each runs straight along its column, mostly under where the ESP32 will sit. Lay it flat and keep it clear of the pads it crosses.</p>',
         test='Beep test: C3 to X17 (3.3 V), B13 to X18 (ground), V3 to A16 (5 V). Then rows 16, 17 and 18 must still be silent to each other.')
    step('headers', 'Sockets for the ESP32, and the capacitor', '15 min',
         'Back to the top side. Push the two 22-way female headers into rows <b>3</b> and <b>13</b>, columns <b>B to W</b>. '
         'Tip: plug them onto the ESP32 first and use the ESP32 as a jig, so they are exactly the right distance apart; solder one pin at each end, take the ESP32 out, then solder the rest.',
         pic=pic_top(),
         shots=[('jig', 'The jig trick: plug both headers onto the ESP32, then drop the whole thing into rows 3 and 13, columns B to W. Solder one pin at each end of each header from underneath, then lift the ESP32 off.'),
                ('headers', 'Headers soldered, and the 100 µF capacitor standing at the back left in A16 (+) and A18 (−, the striped side, toward the back edge). Its body covers A17 and B17: nothing else goes there.')],
         after='<p><b>100 µF capacitor:</b> long leg (+) in <b>A16</b> (5 V rail), short leg and the stripe (−) in <b>A18</b> (ground rail). It steadies the 5 V for the amplifier. Stand it up, under 11 mm tall.</p>',
         test='Beep test, top side: each socket pin you bridged beeps to its pad two rows out (for example the socket in E3 to pad E1). The socket in C3 beeps to row 17, B13 to row 18, V3 to row 16.',
         warn='Don\'t plug the ESP32 in yet.')
    for g in GROUPS:
        extra = ''
        if g['id'] == 'lid':
            extra = ('<p>The three lid buttons, both alarm lights and the light sensor share one ground wire and the light sensor takes the only 3.3 V. '
                     'Solder the <b>220 Ω</b> resistors in the light wires right at each button\'s LED + tab and the <b>10 kΩ</b> from the light sensor\'s signal leg to ground at the sensor, '
                     'each covered with heat-shrink. That keeps the board simple.</p><div class="pic">' + pic_lid() + '</div>')
        if g['id'] == 'bat':
            extra = '<p>Skip this group if you are not fitting the battery. The gauge\'s SDA and SCL go into <b>E14</b> and <b>F14</b>, right in front of the clock module\'s E15 and F15: same pins, two wires. The gauge\'s wires ride over the clock module\'s holes as they leave.</p>'
        if g['id'] == 'power':
            extra = ('<p>Use 22 AWG for these two. With the battery: from the boost\'s <b>VOUT</b> and <b>GND</b>. Without it: straight from the USB-C breakout\'s <b>VBUS</b> and <b>GND</b>.</p>')
        step(g['id'], f'Wires: {g["name"]}', '10 min',
             f'Wires for {esc(g["to"])}. Cut each long enough to reach with the board in place in the case and the lid lifted off (about 15 cm for most; 25 cm for the lid and the projector, which has to reach the barrel\'s end). '
             'Strip 3 mm, push it into the pad from the top and solder it underneath. Label the far ends with tape as you go.',
             pic=pic_group(g['id']), after=wire_table(g) + extra,
             shots=[(f'g-{g["id"]}', f'The {SHORT[g["id"]]} wires in colour; earlier wires are shown pale. '
                     'Wires in row 1 leave over the front edge. Power and ground wires go into the rails in rows 16–18 and leave over the back edge, like the back pins\' wires in rows 14 and 15.')])
    step('all', 'All the wires at once', '–', 'For checking: every wire and its pad. Wires leaving the front edge (row 1) go to the displays, the amplifier, the lid, button B and the charger; wires leaving the back edge carry power and ground (rows 16–18) and go to the clock module, the alarm lights and the battery gauge (rows 14 and 15).',
         pic=pic_all(),
         shots=[('all', 'Every wire in place, before the ESP32 goes in.'),
                ('all-under', 'The underside when it\'s finished: the three rails, the short bridges, the three links, and a joint at every header pin and wire.')],
         mid='''<h3>Turn it round</h3><p>Drag to turn the finished board, scroll or pinch to zoom.</p>
<div class="pb3d"><canvas id="pb3d"></canvas><div class="pb3dbar">
<button type="button" data-v="top">Top</button><button type="button" data-v="under">Underside</button><button type="button" data-v="esp">Take the ESP32 out</button></div></div>''')
    step('move', 'Move the ESP32 over and test, one module at a time', '30 min',
         'With nothing plugged into the sockets, check once more that rows 16, 17 and 18 don\'t beep to each other. Then:',
         after='''<ol>
<li>Unplug the USB cable and lift the ESP32 off the breadboard. Plug it into the perfboard's sockets with its antenna end over column B and its USB ports at column W. Every pin must be in a socket: count that 22 pins sit in each row.</li>
<li>Connect only the power wires and the <b>front display</b>. Power it from the USB-C supply. The front display shows the time within 30 seconds.</li>
<li>Add the modules one at a time, powering off between each: projector display, amplifier, clock module, lid, button B, battery boards. After each, run that module's test from the <a href="breadboard.html">breadboard guide</a>.</li>
<li>Open the clock's web page: status should show the clock module found, and with the battery boards a Battery line.</li></ol>''',
         shots=[('esp32', 'The ESP32 in its sockets: antenna end over column B, USB ports at the right. 22 pins in each row.'),
                ('esp32-back', 'From the back right: the USB ports, the power and ground wires leaving the rails over the back edge, and the 100 µF capacitor at the far end.')],
         test='Everything that worked on the breadboard works here. If one module doesn\'t, its wires are the only new thing: beep each one from the module\'s pin to its pad.',
         warn='Never plug the USB-C supply and the ESP32\'s own USB port into power at the same time.')
    step('fit', 'Into the case', '10 min',
         'The board sits on the four posts at the front right of the base, ESP32 USB end toward the right wall, row 1 toward the front. '
         'Slide it forward until its back edge clears the barrel\'s bearing block in the back-right corner: about 10 mm of the board then hangs past the front posts. '
         'Press it down until the two hooks on each short side click over its ends. '
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
<p class="lead">From the breadboard to the board that goes in the case: about two and a half hours of soldering. Each step has a picture of the board as it should look when the step is done, and a hole map underneath that names every hole used, by its column (A–X) and row (1–18), as printed on the board. Both are drawn from the same layout, to scale. At the end you can turn the finished board round in 3D.</p>
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
  // Underside turns the board over left to right, as you would in your hands: row 1 stays toward you, column A goes right
  const pivot = new THREE.Group(); pivot.position.copy(v(35, 25, 0.8)); st.scene.add(pivot);
  let flipTo = 0, anim = null;
  function go(k) {{
    if (k === 'top' || k === 'under') {{ flipTo = k === 'under' ? Math.PI : 0; anim = performance.now(); }}
    st.look([35, -72, 105], [35, 25, 4], 32); ctl.target.copy(v(35, 25, 4)); ctl.update(); need = true;
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
