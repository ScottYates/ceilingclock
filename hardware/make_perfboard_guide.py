#!/usr/bin/env python3
"""Builds docs/perfboard.html: moving the clock from the breadboard to its perfboard.

Scott's board (2026-11-25): a 70 x 50 mm double-sided prototype board, 24 x 18 plated holes on a 2.54 mm grid,
used whole. Columns A-X left to right, rows 1-18 front to back (row 1 is the edge nearest the clock's front), as
printed on the board. The ESP32 plugs into two 22-way female headers in rows 3 and 13, columns B-W. The three
power rails run left to right along the back: row 16 is 5 V, row 17 is 3.3 V, row 18 is ground.
The same layout is in hardware/components.scad (ref_perfboard) and hardware/pb_model.py (the pictures).
"""
import html, os, re

import pb_howto as HT

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'docs', 'perfboard.html')
PINS = open(os.path.join(HERE, '..', 'firmware', 'src', 'pins.h')).read()
G = lambda n: int(re.search(r'#define\s+%s\s+(\d+)' % n, PINS).group(1))

IMGV = '20261126a'           # cache-buster for the rendered pictures and model
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


# ---------------------------------------------------------------- how the bars are soldered
# The bars (rails and short bridges) lie along one side of their holes, not across them, so the holes stay open.
# They are soldered only where nothing else goes into the hole later; every wire, link end or capacitor leg that
# lands on a bar is soldered to it in the same joint when it goes in.
LATER = {w[1] for g in GROUPS for w in g['wires']} | {l[0] for l in LINKS} | {l[1] for l in LINKS} | set(CAP)

def _anchors(r):
    out = []
    for want in (1, 6, 11, 16, 21, 24):                  # both ends and about every fifth hole
        for d in (0, 1, -1, 2, -2, 3, -3):
            c = want + d
            if 1 <= c <= COLS and pname(c, r) not in LATER and c not in out:
                out.append(c); break
    return sorted(out)

RAIL_ANCHORS = {r: _anchors(r) for r in RAIL}           # columns to solder each rail at
def bridge_solder_rows(c, front):
    """Rows where a short bridge is soldered when it goes on: the socket pin's row, plus any unused middle hole."""
    rows = [2, ROW_J1] if front else [ROW_J3] + ([14] if pname(c, 14) not in LATER else [])
    return rows
ON_BAR = {pname(c, r) for r in RAIL for c in range(1, COLS + 1)} | \
         {pname(c, r) for c in SIG_COLS_FRONT for r in (1, 2, 3)} | {pname(c, r) for c in SIG_COLS_BACK for r in (13, 14, 15)}


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

def bridge(o, a, b, bottom=True, color='#e9edf0', w=5, new=True, solder=()):
    """A bare-wire bar, drawn beside its holes as it lies on the board, with a solder blob at each hole in `solder`."""
    (c1, r1), (c2, r2) = pad(a), pad(b)
    side = 0.8 * S
    dx, dy = (0, -side) if r1 == r2 else ((-side if bottom else side), 0)
    x1, y1, x2, y2 = hx(c1, bottom) + dx, hy(r1) + dy, hx(c2, bottom) + dx, hy(r2) + dy
    o.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#5c656c" stroke-width="{w + 2}" stroke-linecap="round" opacity="{1 if new else .4}"/>'
             f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{w}" stroke-linecap="round" opacity="{1 if new else .4}"/>')
    if new:
        for nm in solder:
            c, r = pad(nm)
            o.append(f'<ellipse cx="{hx(c, bottom) + dx * .45:.1f}" cy="{hy(r) + dy * .45:.1f}" rx="8.5" ry="8.5" fill="#e8743b" stroke="#9c3d12" stroke-width="1.5"/>')

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
        bridge(o, pname(1, r), pname(COLS, r), bottom, new=new, solder=[pname(c, r) for c in RAIL_ANCHORS[r]])
        if names and new:
            o.append(f'<text x="{MX + BW*S + 34}" y="{hy(r) + 5:.1f}" font-size="12.5" font-weight="800" fill="{col}">{nm}</text>')

def solder_key(o, text='solder here now'):
    o.append(f'<ellipse cx="{MX + 8}" cy="{H_ - 48}" rx="8.5" ry="8.5" fill="#e8743b" stroke="#9c3d12" stroke-width="1.5"/>'
             f'<text x="{MX + 24}" y="{H_ - 43}" font-size="14" font-weight="700" fill="#333">= {text}</text>')

def header_joints(o):
    """The socket pins' joints, seen from underneath."""
    for r in (ROW_J1, ROW_J3):
        for i in range(22):
            o.append(f'<circle cx="{hx(HC0 + i, True):.1f}" cy="{hy(r):.1f}" r="5.5" fill="#d4d9de" stroke="#8a9096"/>')

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

def pic_headers():
    o = svg_open('Top: the two sockets')
    board(o)
    headers(o)
    return '\n'.join(o) + '</svg>'

def pic_rails():
    o = svg_open('Underside: the three power rails')
    board(o, bottom=True)
    header_joints(o)
    rails(o)
    solder_key(o, 'solder the bar to its pad here; leave every other hole open')
    return '\n'.join(o) + '</svg>'

def pic_bridges():
    o = svg_open('Underside: the short bridges')
    board(o, bottom=True)
    header_joints(o)
    rails(o, new=False)
    for c in SIG_COLS_FRONT: bridge(o, pname(c, 1), pname(c, ROW_J1), solder=[pname(c, r) for r in bridge_solder_rows(c, True)])
    for c in SIG_COLS_BACK: bridge(o, pname(c, ROW_J3), pname(c, 15), solder=[pname(c, r) for r in bridge_solder_rows(c, False)])
    solder_key(o, 'solder the bridge here (the socket pin\'s joint, and the middle hole); leave its end open')
    return '\n'.join(o) + '</svg>'

def pic_links():
    o = svg_open('Underside: three insulated links')
    board(o, bottom=True)
    header_joints(o)
    rails(o, new=False)
    for c in SIG_COLS_FRONT: bridge(o, pname(c, 1), pname(c, ROW_J1), new=False)
    for c in SIG_COLS_BACK: bridge(o, pname(c, ROW_J3), pname(c, 15), new=False)
    for k, (a, b, lab, colr) in enumerate(LINKS):
        link(o, a, b, colr, lab, k)
    return '\n'.join(o) + '</svg>'

def pic_cap():
    o = svg_open('Top: the capacitor')
    board(o)
    headers(o, new=False)
    capacitor(o)
    for nm in CAP: ring(o, nm)
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
    def step(sid, title, time, intro, pic='', after='', test='', warn='', shots=(), mid='', pre=''):
        steps.append(dict(sid=sid, title=title, time=time, intro=intro, pic=pic, after=after, test=test, warn=warn, shots=shots, mid=mid, pre=pre))
    def ol(*items): return '<ol class="do">' + ''.join(f'<li>{i}</li>' for i in items) + '</ol>'
    def ul(*items): return '<ul>' + ''.join(f'<li>{i}</li>' for i in items) + '</ul>'
    def why(t): return f'<div class="why"><b>Why?</b> {t}</div>'
    def tip(t): return f'<div class="tip"><b>Tip:</b> {t}</div>'
    def cols(cs): return ', '.join(CL[c - 1] for c in cs)
    howto = lambda name: f'<figure class="pic">{HT.ALL[name]()}</figure>'

    # ------------------------------------------------------------ 1
    step('what', 'What you are building', '5 min read',
         'On the breadboard, everything was pushed in with jumper wires. That is perfect for testing, but the wires can wiggle loose, and it doesn\'t fit in the case. '
         'This guide moves exactly the same connections onto a small board where they are <b>soldered</b>: joined with melted metal, so they stay put for years.',
         after='''<h3>The board</h3>
<p>The board is a <b>perfboard</b> (also called a prototype board): a sheet of fibreglass with a grid of small holes, 2.54 mm apart. That is a tenth of an inch, the same spacing as the pins on the ESP32, so its pins line up with the holes.</p>
<p>Each hole has a shiny metal ring around it on both faces of the board, called a <b>pad</b>. On your board the holes are also <b>plated</b>: metal lines the inside of each hole, joining its top and bottom pads.</p>
<p><b>The most important thing to know: the holes are not connected to each other.</b> A blank perfboard does nothing. Every connection is one you make, with solder and bits of wire. That is what this guide walks you through.</p>
<h3>What goes on it</h3>'''
         + ul('<b>Two sockets</b> the ESP32 plugs into, so you can take it out again later.',
              '<b>Three power rails</b>: long bare wires along the back of the board that carry 5 V, 3.3 V and ground to everything.',
              '<b>Short bridges</b>: little bare wires that connect each ESP32 pin to a free hole beside it, where that pin\'s wire goes.',
              '<b>Three links</b>: covered wires that connect the ESP32\'s own power pins to the rails.',
              '<b>One capacitor</b>, which steadies the power for the loudspeaker\'s amplifier.',
              '<b>Wires</b> out to every part of the clock: the displays, the amplifier, the clock module, the buttons and lights, and the battery boards.')
         + '<p>Each step below has a picture of what the board should look like when the step is done, and a <b>hole map</b> showing exactly which holes to use. Don\'t rush: if you are new to soldering, the whole board takes about four hours, and it is fine to spread it over a few evenings.</p>',
         pic=pic_board(), shots=[('kit', 'Everything that goes on the board: the 70 × 50 mm board, two 22-way sockets (called female headers), the 100 µF capacitor, the resistors for the lid, bare wire for the rails and bridges, and coloured wire for the modules.')])

    # ------------------------------------------------------------ 2
    gl = [('Solder', 'A soft metal wire that melts at about 190–220 °C. When it cools it holds parts together and carries electricity. Use thin (0.6–0.8 mm) solder with "rosin core" or "flux core" in its name.'),
          ('Soldering iron', 'A pen-shaped heater. Its metal <b>tip</b> gets hot enough to melt solder; the rest of the metal near the tip is hot too.'),
          ('Joint', 'One spot where solder joins two things, for example a wire and a pad.'),
          ('Pad', 'The metal ring round a hole. Solder sticks to pads; it doesn\'t stick to the green board.'),
          ('Lead', 'Said "leed": a metal leg on a part, like the two legs on the capacitor.'),
          ('Flux', 'A cleaning paste or liquid that helps solder flow and stick. There is already some inside your solder; a flux pen adds more when a joint won\'t flow.'),
          ('Tinning', 'Coating something with a thin layer of solder before you join it: the iron\'s tip, or the end of a wire.'),
          ('Bare wire', 'Wire with no plastic covering, usually silver-coloured ("tinned copper"). Used for the rails and bridges. Resistor legs you have cut off work too.'),
          ('Hookup wire', 'Wire with a plastic covering (the <b>insulation</b>). <b>Stranded</b> wire has many thin strands inside and bends easily; <b>solid</b> wire has one thick strand and stays where you bend it.'),
          ('AWG', 'The wire\'s thickness. A bigger number is a thinner wire: 26 AWG is thin, 22 AWG thicker.'),
          ('Strip', 'Remove the plastic covering from the end of a wire, with wire strippers.'),
          ('Rail', 'Also called a <b>bus bar</b> or power bus: one long strip of metal that many wires connect to, so they all get the same power. Like a power strip, or the red and blue lines along the edges of the breadboard.'),
          ('Ground (GND)', 'The "0 volts" that every part\'s power comes back to. Every module needs a ground wire as well as its power wire, or it won\'t work.'),
          ('3.3 V and 5 V', 'The two power supplies. The ESP32, displays and sensors use 3.3 V; the amplifier and the ESP32\'s input use 5 V. Mixing them up can damage parts, so the guide always says which.'),
          ('Bridge', 'In this guide: a short piece of bare wire you solder on to connect neighbouring holes on purpose. (A <b>solder bridge</b> is the mistake: a blob of solder joining holes that should be separate.)'),
          ('Link', 'A piece of covered wire joining two holes that are far apart, on the underside.'),
          ('Socket / female header', 'A plastic strip of little metal sockets. The ESP32\'s pins push into them.'),
          ('Capacitor', 'A part that stores a little electricity and lets it out quickly, smoothing the power. The one used here has a + and a − leg and must go in the right way round (its <b>polarity</b>).'),
          ('Continuity test', 'The multimeter\'s beep setting. It beeps when its two probe tips touch things that are connected.'),
          ('Desoldering braid', 'Also called solder wick: a flat copper braid. Pressed onto a joint with the iron, it soaks up solder, to fix mistakes.'),
          ('Flush cutters', 'Small sharp cutters that snip wire and leads flat against the board.'),
          ('Top and underside', 'The <b>top</b> (parts side) is where the sockets, capacitor and wires go in. The <b>underside</b> (solder side) is where you solder them and where the rails and bridges lie.'),
          ('Anchor', 'In this guide: one of the few holes where a rail or bridge is soldered when it goes on. The rest of its holes are left open for later.')]
    step('words', 'Words you will see', '5 min read',
         'Soldering has its own words. Here is every one this guide uses, in plain terms. Come back to this list whenever a word is unfamiliar.',
         after='<dl class="gloss">' + ''.join(f'<dt>{t}</dt><dd>{d}</dd>' for t, d in gl) + '</dl>')

    # ------------------------------------------------------------ 3
    step('tools', 'Tools, materials and safety', '10 min',
         'Get everything together before you start, so you never have to put a hot iron down to go looking for something.',
         after='<h3>Tools</h3>' + ul(
             '<b>Soldering iron</b> with a temperature control, a stand to rest it in, and a damp sponge or a ball of brass wool to clean the tip. A fine conical or small chisel tip.',
             'Set it to about <b>330–350 °C</b> (625–660 °F) for ordinary tin-lead solder, or <b>350–380 °C</b> (660–715 °F) for lead-free solder.',
             '<b>Solder</b>: 0.6–0.8 mm, rosin core. Tin-lead (often labelled 63/37 or 60/40) is the easiest to learn with.',
             '<b>Flush cutters</b> and <b>wire strippers</b> (with a 26 AWG notch, or an adjustable one).',
             '<b>Multimeter</b> with a continuity (beep) setting.',
             '<b>Desoldering braid</b> (solder wick), 2–2.5 mm wide, for fixing mistakes. A <b>flux pen</b> helps too.',
             'Something to hold the board: a "helping hands" clamp, a small vice, or a lump of putty. Masking tape or Kapton tape for holding wires in place.',
             'A bright lamp and a magnifying glass, or your phone\'s camera zoomed in, for checking joints.',
             'Isopropyl alcohol (rubbing alcohol, 90% or more) and an old toothbrush, for cleaning the board at the end.')
         + '<h3>Materials</h3>' + ul(
             'The <b>70 × 50 mm perfboard</b>, 24 × 18 holes. It goes in whole: no cutting. A spare one from the kit for practice.',
             'Two 22-way 2.54 mm <b>female headers</b> (sockets). If yours are longer, cut them to 22 with a sharp knife, cutting through the 23rd socket.',
             'One <b>100 µF electrolytic capacitor</b>, 10 V or more.',
             '<b>Bare tinned wire</b>, about 0.5–0.6 mm (22–24 AWG), about 30 cm in all.',
             '<b>Solid insulated wire</b>, thin (26–30 AWG), about 30 cm, for the three links.',
             '<b>Stranded hookup wire</b>, 26 AWG, in several colours (red, orange, black and others), and a little 22 AWG red and black for the power input.',
             'The two <b>220 Ω</b> resistors and one <b>10 kΩ</b> resistor from the breadboard, and some heat-shrink tubing.')
         + '<h3>Staying safe</h3>' + ul(
             '<b>The iron\'s tip is hotter than an oven.</b> Always put it back in its stand, never on the bench. Never touch the metal part, even after it\'s off: it stays hot for several minutes.',
             '<b>Fumes:</b> the smoke is from the flux. Work with a window open or a small fan blowing it away from your face, and don\'t breathe it in.',
             '<b>Wear glasses</b> when you snip leads: the cut-off bits fly.',
             'If your solder contains lead, <b>wash your hands</b> after soldering, and don\'t eat or drink at the bench.',
             'Work on something that won\'t burn: a silicone mat, a tile or a piece of wood.',
             'Keep the clock\'s battery <b>unplugged</b> while you work on the board.',
             '<b>Turn the iron off</b> when you take a break and when you finish.'),
         warn='Never touch the iron\'s metal, and always return it to its stand.')

    # ------------------------------------------------------------ 4
    step('learn', 'Learn to make a good joint (practise first)', '30 min',
         'Every joint on this board is made the same way. Spend half an hour practising on a <b>spare board</b> from the kit, using cut-off resistor legs or bits of bare wire, before you touch the real one. '
         'Twenty practice joints make a huge difference.',
         after=howto('how_to_solder') + ol(
             '<b>Clean and tin the tip.</b> Wipe the hot tip on the damp sponge or brass wool, then touch a little solder to it so it looks shiny all over. A shiny tip passes heat well; a dull grey one doesn\'t. Do this every few joints.',
             '<b>Push a lead through a hole</b> from the top. Turn the board over so you are looking at the underside, and bend the lead out a little so it can\'t fall out.',
             '<b>Heat both:</b> touch the tip so it touches the pad <i>and</i> the lead at the same time. Count "one, two".',
             '<b>Feed the solder</b> into the joint from the other side: touch the solder to where the lead meets the pad, not to the iron. It melts and flows around the lead and over the pad. About 3 mm of solder is enough for one joint.',
             '<b>Take the solder away first, then the iron.</b> Keep the board still for 3 seconds while the joint sets.',
             '<b>Look at it.</b> Compare it with the pictures below. Then snip the lead about 1 mm above the joint with the flush cutters.')
         + howto('joints')
         + '<h3>Fixing a joint</h3>' + ul(
             '<b>Too little, dull or lumpy:</b> touch the iron to it again (add a dab of flux if you have it) until it melts and flows shiny, then take the iron away.',
             '<b>Too much, or a bridge:</b> lay the end of the desoldering braid on the solder, press the iron on top of the braid, and wait two seconds: the braid soaks up the solder. Lift both off together, then snip off the used, silvery end of the braid.',
             'Most mistakes come from not heating long enough, or from melting the solder on the iron and dabbing it on. Heat the joint, and let the joint melt the solder.')
         + tip('Practise taking a joint apart with the braid too. Then a mistake on the real board is nothing to worry about.'))

    # ------------------------------------------------------------ 5
    step('know', 'Get to know your board', '5 min',
         'Every hole has a name, printed on the board: its <b>column</b> letter, A to X, counting from the left, and its <b>row</b> number, 1 to 18, counting from the front. So <b>E1</b> means column E, row 1.',
         after=ol('Hold the board so the numbers count up away from you, with <b>row 1 nearest you</b> and the letters reading A to X from left to right.',
                  'Put a small piece of masking tape on the edge nearest you and write <b>FRONT</b> on it. Put another on the top face, in a corner, and write <b>TOP</b>. These two labels save a lot of confusion.',
                  'To find a hole, put a finger on its letter and slide it toward you to its row number.')
         + '<p><b>Turning the board over:</b> some steps are done on the underside. Always turn it over <b>left to right</b>, like turning a page, so the FRONT edge stays nearest you. Seen from underneath, column A is then on your <b>right</b>, and the letters read X to A. The underside pictures are drawn that way.</p>',
         pic=pic_board())

    # ------------------------------------------------------------ 6
    step('headers', 'Fit the ESP32\'s sockets', '20 min',
         'The ESP32 doesn\'t get soldered to the board: it plugs into two strips of sockets, so you can take it out again. These go on first. '
         'The trick is to plug the sockets onto the ESP32 before you solder them, so it holds them exactly the right distance apart.',
         after=ol('Push the two 22-way socket strips onto the ESP32\'s two rows of pins, all the way down.',
                  'Lower the ESP32, with its sockets, onto the top of the board so the sockets\' legs go into <b>rows 3 and 13, columns B to W</b>. The ESP32\'s metal-covered end (the antenna end) goes over column B; its USB sockets end over column W. Check: the first leg is in B3 and the last in W3.',
                  'Hold the ESP32 down and turn the whole thing over left to right, so it rests on the mat on the ESP32 and you see the underside. (Use putty or a folded cloth to keep it level.)',
                  'Solder <b>one leg at each end of each strip</b>: four joints. Heat each for no more than about 3 seconds: the plastic can melt.',
                  'Turn it back over and check both strips sit flat on the board. If one doesn\'t, reheat one of its joints while pressing the strip down gently, then let go of the iron first.',
                  'Lift the ESP32 straight up and out of the sockets. Put it somewhere safe.',
                  'Turn the board over again and solder the remaining 40 legs. They are short: there\'s no need to trim them.')
         + why('You can\'t put a wire into the same hole as a socket\'s leg, so each socket leg gets its own joint here, and the module wires join the pins through the bridges and links in the next steps.'),
         pic=pic_headers(),
         shots=[('jig', 'The sockets plugged onto the ESP32 and dropped into rows 3 and 13: the ESP32 holds them straight and the right distance apart while you solder the end legs.'),
                ('headers', 'Both sockets soldered and the ESP32 taken out.')],
         test='Look at all 44 joints in a bright light: each a small shiny cone, none touching its neighbour. Then, with the meter on beep, touch neighbouring legs in each row (B3 and C3, C3 and D3, and so on): none may beep.')

    # ------------------------------------------------------------ 7
    anch = {r: cols(RAIL_ANCHORS[r]) for r in RAIL}
    step('rails', 'The three power rails', '30 min',
         'A <b>rail</b> (or bus bar) is one long bare wire that many wires connect to, so they all share the same power, like a power strip. '
         'The breadboard had them too: the long lines along its edges. This board has three, side by side along the back, on the underside: <b>row 16 is 5 V, row 17 is 3.3 V, row 18 is ground.</b> Later, every module\'s power and ground wire goes into one of these rows.',
         pre=howto('bar_beside'),
         after='<p><b>Lay each bar beside its holes, not across them</b>, as in the drawing above, and solder it only at the six orange holes on the hole map. '
               'The other holes stay open: a wire, a link or the capacitor goes into some of them later, and its joint then takes in the bar too.</p>'
         + ol('Turn the board over left to right, so you see the underside with the FRONT edge nearest you. It rests on the sockets.',
              'Cut a piece of bare wire about 65 mm long. <b>Straighten it:</b> hold one end in pliers and pull the other end firmly with another pair (or wrap it round a pencil and pull). A straight bar lies flat and is much easier to solder.',
              'Lay it along <b>row 18</b>, the row nearest the far edge, running along the far side of the pads from column A to column X. Hold it down with a strip of tape across the middle.',
              f'Solder it at the six orange holes for row 18: columns <b>{anch[GND]}</b>. For each: touch the iron to the pad and the bar together, feed a little solder, and let it flow round the bar onto the pad. Use only a little: it mustn\'t fill the hole.',
              'Take the tape off. Snip the ends about 1 mm past the last pads.',
              f'Do the same for <b>row 17</b> (solder at columns <b>{anch[V33]}</b>), then <b>row 16</b> (columns <b>{anch[V5]}</b>).')
         + why('If you soldered every hole, the solder would fill them, and you would have to clear them again for the wires that go in later.'),
         pic=pic_rails(),
         shots=[('rails', 'The three rails from underneath, so column A is on the right. Row 18 is at the far edge.'),
                ('rails-close', 'Close up: each bar lies along the edge of its pads and is soldered at a few holes. The holes in between stay open.')],
         test='Meter on beep: each rail beeps from end to end (for example A18 to X18; touch the bar itself). Rows 16, 17 and 18 must <b>not</b> beep to each other, and row 16 must not beep to row 15. A beep between two rails means solder is joining them: find it with the light and clear it with braid.')

    # ------------------------------------------------------------ 8
    step('bridges', 'The short bridges', '25 min',
         'Each ESP32 pin sits in a socket leg in row 3 or row 13. A module\'s wire can\'t share that hole, so it goes into a free hole two rows away, and a short bare wire on the underside joins the two. That is a <b>bridge</b>. '
         'There is one for every ESP32 pin that has a wire; the other pins aren\'t used.',
         after=ol('Board still upside down, FRONT edge nearest you.',
                  'Cut a piece of bare wire about 9 mm long and straighten it.',
                  f'<b>Front bridges</b>, columns <b>{cols(SIG_COLS_FRONT)}</b>: lay the wire beside the holes of rows 1, 2 and 3 in that column, touching the socket leg\'s joint in row 3.',
                  'Solder it at the two orange holes: in <b>row 3</b>, reheat the socket leg\'s joint so the bar sinks into it, adding a touch of solder; in <b>row 2</b>, solder the bar to its pad. <b>Leave row 1 open</b>: that hole gets the module\'s wire later.',
                  'Snip the ends. Do the next column. Check each one sits in its own column: it must not touch the bridges either side.',
                  f'<b>Back bridges</b>, columns <b>{cols(SIG_COLS_BACK)}</b>: the same along rows 13, 14 and 15, soldered at the row 13 socket leg (and at row 14 where the hole map shows an orange dot). Leave the other holes open.')
         + why('Holes in row 1, 14 and 15 are where the module wires go in. Leaving them open now makes the wires easy to fit.'),
         pic=pic_bridges(),
         shots=[('bridges', 'All the short bridges: rows 1 to 3 at the front, rows 13 to 15 at the back.'),
                ('bridges-close', 'Close up: each bridge lies beside its column of holes, soldered to the socket leg and the middle pad, with the end hole left open for a wire.')],
         test='Meter on beep: from each bridge\'s row 1 pad to its socket leg in row 3, it beeps. Between neighbouring columns (E1 and F1, F1 and G1, and so on), it must not.')

    # ------------------------------------------------------------ 9
    step('links', 'Three insulated links', '15 min',
         'The ESP32 has its own power pins, and they need joining to the rails: its 3.3 V pin to the 3.3 V rail, a ground pin to the ground rail, and its 5 V pin to the 5 V rail. '
         'These wires cross other bare wires on the way, so they must have a plastic covering: that is what makes them <b>links</b> rather than bridges.',
         after=ol('Board still upside down. Use the thin solid insulated wire.',
                  'For each link: cut a piece a little longer than the distance on the hole map, and strip about 3 mm from each end.',
                  '<b>3.3 V (orange): C3 to C17.</b> At C3, lay the bare end against the socket leg\'s joint and reheat the joint so it takes the wire in. At C17, lay the other end on the pad and the row 17 bar and solder them together.',
                  '<b>Ground (black): B13 to B18</b>, the same way: onto the socket leg at B13, onto the pad and bar at B18.',
                  '<b>5 V (red): V3 to V16</b>, the same way.',
                  'Lay each link flat along its column, away from the pads it passes. A dab of tape or glue keeps it down.')
         + why('Without these, the ESP32 would get no power from the rails, and its 3.3 V wouldn\'t reach the modules.'),
         pic=pic_links(),
         shots=[('links', 'The three links from underneath: each runs straight along one column, from a socket leg to a rail.')],
         test='Meter on beep: C3 to any pad on row 17, B13 to row 18, V3 to row 16. Then check again that rows 16, 17 and 18 don\'t beep to each other.')

    # ------------------------------------------------------------ 10
    step('cap', 'The capacitor', '10 min',
         'The capacitor is a little store of electricity that smooths the 5 V power when the amplifier suddenly needs more for a loud sound. It has a + leg and a − leg, and they must go in the right way round.',
         pre=howto('capacitor'),
         after=ol('Turn the board top side up, FRONT edge nearest you.',
                  'Push the <b>long leg (+)</b> into <b>A16</b> and the <b>short leg (−)</b>, the one on the striped side, into <b>A18</b>, from the top. The stripe faces the back edge.',
                  'Push it down until it stands about 1 mm above the board. It has to stay under 11 mm tall.',
                  'Turn the board over. Bend each leg out a little so it stays put.',
                  'Solder each leg: touch the iron to the pad, the leg and the rail\'s bar together, so one joint holds all three. Snip the legs to 1 mm.')
         + tip('Nothing else goes in A17 or B17: the capacitor\'s body sits over them.'),
         pic=pic_cap(),
         shots=[('cap', 'The capacitor standing at the back left, + in A16 and − in A18, beside the sockets.')],
         test='Meter on beep: A16 beeps to row 16, A18 to row 18. Between A16 and A18 you may hear a short chirp that stops: that\'s the capacitor charging from the meter, and it\'s fine. A steady beep is not: it means solder is joining the rails.')

    # ------------------------------------------------------------ 11
    step('wireprep', 'How to fit a module wire', '5 min read',
         'All the remaining steps fit wires that run out to the clock\'s parts. Every wire goes in the same way.',
         pre=howto('wire_prep'),
         after=ol('<b>Cut it to length.</b> Long enough to reach its part with the board in place in the case and the lid lifted off: about 15 cm for most, 25 cm for the lid and the projector display. Too long is easy to tuck away; too short means starting again.',
                  '<b>Strip 3 mm</b> of the covering from the board end, <b>twist</b> the strands, and <b>tin</b> them.',
                  '<b>Push it into its hole from the top</b> (the hole maps and tables say which), until the covering touches the board.',
                  'Turn the board over. Bend the end over a little toward the bar if the hole is on a rail or bridge.',
                  '<b>Solder it.</b> If the hole is on a rail or a bridge, touch the iron to the pad, the wire and the bar together, so one joint holds all three.',
                  'Snip the end to about 1 mm.',
                  '<b>Label the far end</b> with a flag of masking tape: what it is ("front CLK", "amp GND"…). You will thank yourself later.',
                  'Give the wire a gentle tug. It mustn\'t move.')
         + '<p><b>Colours:</b> use the colours in the tables if you have them. Whatever you have, keep to <b>red for 5 V, orange for 3.3 V and black for ground</b>. Then you can always tell the power wires apart.</p>'
         + tip('Wires in row 1 leave over the front edge. Wires in rows 14 to 18 leave over the back edge. Keep them flat against the board as they go.'))

    for g in GROUPS:
        extra = ''
        if g['id'] == 'lid':
            extra = ('<p>The three lid buttons, both alarm lights and the light sensor share <b>one ground wire</b>: run it to the nearest part, then on from part to part (a short wire from one tab to the next). Only the light sensor needs the 3.3 V wire.</p>'
                     + ol('Solder a <b>220 Ω</b> resistor onto each alarm button\'s LED + tab, then the light wire onto the resistor\'s other leg. Slide heat-shrink over the resistor and shrink it with the side of the iron or a lighter held well away.',
                          'Solder the <b>10 kΩ</b> resistor from the light sensor\'s signal leg (the one with its wire) to its ground leg, and cover it with heat-shrink too.',
                          'Each alarm button has four tabs: two for the switch, two for its light. The light\'s + tab is usually marked; if not, find it with the meter\'s diode setting (the light glows faintly with the red probe on +).')
                     + '<div class="pic">' + pic_lid() + '</div>')
        if g['id'] == 'bat':
            extra = ('<p>Skip this step if you are not fitting the battery.</p><p>The battery gauge shares two ESP32 pins with the clock module, so its two wires go into <b>E14</b> and <b>F14</b>, just in front of the clock module\'s E15 and F15. '
                     'They are the same pins, so it doesn\'t matter that they are side by side. The gauge\'s wires pass over the clock module\'s holes as they leave: lay them flat.</p>')
        if g['id'] == 'power':
            extra = ('<p>These two bring power to the board. Use the thicker <b>22 AWG</b> wire. With the battery, they come from the 5 V booster board\'s <b>VOUT</b> (red) and <b>GND</b> (black). Without it, they come straight from the USB-C socket board\'s <b>VBUS</b> (red) and <b>GND</b> (black).</p>'
                     '<div class="warn">⚠️ Double-check these two before you power anything: red into the 5 V rail (row 16), black into ground (row 18). Swapped, they can damage the ESP32.</div>')
        step(g['id'], f'Wires: {g["name"]}', '10–15 min',
             f'These go to {esc(g["to"])}. Fit each wire as in the step above, into the hole in the table.',
             pic=pic_group(g['id']), after=wire_table(g) + extra,
             shots=[(f'g-{g["id"]}', f'The {SHORT[g["id"]]} wires in colour; wires from earlier steps are shown pale. '
                     'Wires in row 1 leave over the front edge; power and ground wires (rows 16–18) and the back pins\' wires (rows 14 and 15) leave over the back edge.')])

    step('all', 'Check every wire', '15 min',
         'Before anything goes near power, check the whole board against this map and the pictures. Go wire by wire with a finger on the map.',
         after=ol('Every wire is in the hole the tables say, and its far end is labelled.',
                  'The power wires: red into row 16 (5 V), orange into row 17 (3.3 V), black into row 18 (ground).',
                  'Nothing is in A17 or B17, under the capacitor.'),
         pic=pic_all(),
         shots=[('all', 'Every wire in place, before the ESP32 goes back in.'),
                ('all-under', 'The finished underside: the three rails, the short bridges, the three links, and a joint at every socket leg and wire.')],
         mid='''<h3>Turn it round</h3><p>Drag to turn the finished board; scroll or pinch to zoom. "Underside" turns it over left to right, the same way as in your hands.</p>
<div class="pb3d"><canvas id="pb3d"></canvas><div class="pb3dbar">
<button type="button" data-v="top">Top</button><button type="button" data-v="under">Underside</button><button type="button" data-v="esp">Take the ESP32 out</button></div></div>''')

    step('clean', 'Clean the underside, and protect it', '20 min',
         'Leftover flux is sticky and can hide tiny solder bridges. Cleaning it off lets you see every joint clearly.',
         pre=howto('beep'),
         after=ol('Dip an old toothbrush in isopropyl alcohol and scrub the underside gently, a small area at a time. Wipe with a paper towel. Let it dry for a few minutes.',
                  'Look over every joint in a bright light, with a magnifier or your phone\'s camera zoomed in. Look especially <b>between</b> neighbouring pads: any silver thread of solder joining them must go.',
                  'Look for stray wire strands poking out of a joint, and snip them.',
                  'Do the beep tests once more: rows 16, 17 and 18 must not beep to each other, and no two neighbouring columns in rows 1 to 3 may beep.',
                  'When everything has passed (after the test in the next step is best), cover the underside with <b>Kapton tape</b>, which is heat-proof and thin. Lay strips side by side over the rails and bridges. It stops anything in the case touching the bare wires.'),
         test='Every beep test passes, and you can\'t see any solder joining two pads that the hole maps don\'t join.')

    step('move', 'Plug in the ESP32 and test, one part at a time', '30–45 min',
         'Now move the ESP32 over from the breadboard and bring the clock back to life, one part at a time, so that if something is wrong you know exactly which wires to look at.',
         after=ol('Unplug all power. Lift the ESP32 off the breadboard, rocking it gently from end to end.',
                  'Plug it into the board\'s sockets: antenna end over column B, USB sockets at column W. Every pin must go into a socket: count 22 in each row.',
                  'Connect only the two <b>power-in</b> wires and the <b>front display</b>\'s four wires. Plug in the USB-C power. Within 30 seconds the front display shows the time.',
                  'If anything gets hot or smells hot, unplug at once and see "If something doesn\'t work" below.',
                  'Unplug the power. Connect the next part: projector display, then the amplifier, the clock module, the lid, button B and the battery boards. Power up after each one and run that part\'s test from the <a href="breadboard.html">breadboard guide</a>.',
                  'Open the clock\'s web page: its status shows the clock module found, and with the battery boards, a Battery line.'),
         shots=[('esp32', 'The ESP32 in its sockets: antenna end over column B, USB sockets at the right.'),
                ('esp32-back', 'From the back right: the USB sockets, the power and ground wires leaving over the back edge, and the capacitor at the far end.')],
         test='Everything that worked on the breadboard works here.',
         warn='Never plug the USB-C power and the ESP32\'s own USB socket in at the same time.')

    step('fit', 'Into the case', '10 min',
         'The board sits on the four posts at the front right of the base, with the ESP32\'s USB end toward the right wall and the FRONT edge toward the front.',
         after=ol('Lower it onto the posts, then slide it forward until its back edge clears the barrel\'s bearing block in the back-right corner. About 10 mm of the board then hangs past the front posts.',
                  'Press it down until the two hooks on each short side click over its ends.',
                  'Route the lid and projector wires up the right side. Leave the battery and clock-module wires along the floor. Keep everything clear of the barrel: it turns.',
                  'See the <a href="assembly.html">assembly steps</a> for the rest.'),
         shots=[('incase', 'Where it ends up: at the front right of the base, ESP32 on top, with the battery, the floor modules and the wiring around it.')])

    step('trouble', 'If something doesn\'t work', '–',
         'Almost every problem is one joint or one wire. Unplug the power before you touch anything, then:',
         after=ul('<b>Nothing lights up:</b> check the power-in wires: red in row 16, black in row 18. Beep from the power board\'s VOUT to any pad on row 16, and from its GND to row 18. Check the 5 V link (V3 to row 16).',
                  '<b>Something gets hot, or the power supply cuts out:</b> two rails are joined. Beep rows 16, 17 and 18 against each other with the ESP32 out, and look for a solder bridge between them.',
                  '<b>One part doesn\'t work:</b> its wires are the only new thing. Beep each one from the part\'s own pin to its pad on the board, and from that pad to the ESP32 socket leg (through its bridge). One that doesn\'t beep is a bad joint or a broken wire.',
                  '<b>A part works sometimes, or the clock restarts at random:</b> usually a dull, lumpy joint on a power or ground wire. Reheat the joints in rows 16 to 18 until they are shiny.',
                  '<b>A display shows garbage:</b> its CLK and DIO wires are swapped. Swap them at the part\'s end.',
                  '<b>Two neighbouring columns beep together:</b> a solder bridge. Clear it with braid.')
         + '<p>If you are stuck, the <a href="wiring.html">wiring page</a> lists every connection by the module\'s pin names.</p>')
    toc = ''.join(f'<a href="#{s["sid"]}"><span>{i + 1}</span>{esc(re.sub("<[^>]+>", "", s["title"]))}</a>' for i, s in enumerate(steps))
    secs = ''.join(f'''
<section class="bbstep" id="{s['sid']}">
  <div class="bbhead"><span class="num">{i + 1}</span><h2>{s['title']}</h2><span class="time">⏱ {s['time']}</span></div>
  <p>{s['intro']}</p>
  {f'<div class="warn">⚠️ {s["warn"]}</div>' if s['warn'] else ''}
  {s['pre']}
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
ol.do{{padding-left:1.4em}}ol.do li{{margin:.45em 0;line-height:1.5}}
.why{{border-left:4px solid #2e86c1;background:#eef5fb;padding:8px 12px;border-radius:0 8px 8px 0;margin:12px 0}}
.tip{{border-left:4px solid #27ae60;background:#eef8f1;padding:8px 12px;border-radius:0 8px 8px 0;margin:12px 0}}
dl.gloss{{display:grid;grid-template-columns:minmax(120px,190px) 1fr;gap:8px 16px;margin:12px 0}}
dl.gloss dt{{font-weight:800}}dl.gloss dd{{margin:0;line-height:1.45}}
@media (max-width:640px){{dl.gloss{{grid-template-columns:1fr}}dl.gloss dd{{margin-bottom:8px}}}}
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
<p class="lead">From the breadboard to the board that goes in the case, written for someone who has never soldered before. It starts with what everything is and how to make a good joint, then goes one small step at a time. Each step has a picture of the board as it should look when the step is done, and a hole map that names every hole used, by its column (A–X) and row (1–18), as printed on the board. Allow about four hours, over a few sittings if you like.</p>
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
