# Usage: python3 hardware/make_breadboard_guide.py
# Writes docs/breadboard.html: an illustrated, step-by-step breadboard test for beginners.
# Every picture is drawn here from firmware/src/pins.h and the ESP32-S3-DevKitC-1 header order,
# so the wires in the pictures go to the right physical pins.
#
# Two bench layouts, switched by a button on the page:
#   plug   - the ESP32 plugged in across two full-size breadboards side by side, straddling the two rail
#            strips at the join (about 1", the DevKitC-1's pin spacing). Top edge pins (J3) in column a of
#            the upper board, bottom edge pins (J1) in column j of the lower board, from row 5. Each pin
#            has four free holes beside it.
# Letters: the code places parts by 'design' letters with a at the top of each board; the pictures and the
# text print the real letter (MIRROR), because a real breadboard with row 1 on the left has j at the top.
#   beside - the ESP32 next to a single breadboard, connected with female jumper leads.
# In both, the top rails are 3V3 + GND and the bottom rails are the external 5 V + GND, with the grounds joined.
import os, re, html, math

HERE = os.path.dirname(os.path.abspath(__file__))
PINS = dict(re.findall(r'#define (PIN_\w+)\s+(\d+)', open(os.path.join(HERE, '..', 'firmware', 'src', 'pins.h')).read()))
G = lambda k: int(PINS[k])

# ESP32-S3-DevKitC-1 headers (Espressif user guide). Pin 1 is at the antenna end.
J1 = ['3V3', '3V3', 'RST', '4', '5', '6', '7', '15', '16', '17', '18', '8', '3', '46', '9', '10', '11', '12', '13', '14', '5V', 'G']
J3 = ['G', 'TX', 'RX', '1', '2', '42', '41', '40', '39', '38', '37', '36', '35', '0', '45', '48', '47', '21', '20', '19', 'G', 'G']

def esp_pin(name, which=None):
    """(header, index) of a pin name like '15' or '3V3'."""
    for hdr, lst in (('J1', J1), ('J3', J3)):
        if which and hdr != which: continue
        if name in lst: return hdr, lst.index(name)
    raise KeyError(name)

# ---------------------------------------------------------------- geometry
W, H = 1000, 690
P = 15                                   # breadboard pitch in the drawing
BX0 = 300                                # x of row 1
ROWS = 30
PLUG_ROW0 = 5                            # breadboard row of the ESP32's first pin (plug layout)
ONE_ROW0 = 1                             # one board: the ESP32 starts at row 1, its antenna past the end of the board

def cols(y_a, y_f, p=P):
    d = {c: y_a + i * p for i, c in enumerate('abcde')}
    d.update({c: y_f + i * p for i, c in enumerate('fghij')})
    return d
ONE_P, ONE_X0 = 10, 255                  # one full-size board: 60 rows at a smaller pitch

LAYOUTS = {
  'beside': dict(
      boards={'': dict(label='', y0=380, y1=638, cols=cols(436, 526), rails={'t+': 398, 't-': 412, 'b+': 610, 'b-': 624},
                       gap=503, rowy=425, dead=None)},
      esp=(330, 70, 690, 180), epitch=15.5),
  'plug': dict(
      boards={'U': dict(label='upper board', y0=36, y1=282, cols=cols(88, 178), rails={'t+': 52, 't-': 66},
                        gap=155, rowy=80, dead=(256, 270)),
              'L': dict(label='lower board', y0=285, y1=530, cols=cols(334, 424), rails={'b+': 502, 'b-': 516},
                        gap=401, rowy=495, dead=(298, 312))},
      esp=(BX0 + (PLUG_ROW0 - 1) * P - 16, 226, BX0 + (PLUG_ROW0 + 20) * P + 16, 346), epitch=P),
  'one': dict(
      boards={'': dict(label='', y0=236, y1=436, cols=cols(280, 350, ONE_P), rails={'t+': 250, 't-': 262, 'b+': 408, 'b-': 420},
                       gap=327, rowy=272.5, dead=None)},
      esp=(ONE_X0 + (ONE_ROW0 - 1) * ONE_P - 24, 268, ONE_X0 + (ONE_ROW0 + 20) * ONE_P + 14, 392), epitch=ONE_P,
      P=ONE_P, X0=ONE_X0, ROWS=60, W=1100, rdx=100),
}
LAY = 'beside'                           # the layout being built or drawn
MIRROR = dict(zip('abcdefghij', 'jihgfedcba'))   # design letter -> letter printed on a real breadboard
def LY(): return LAYOUTS[LAY]
def X(beside, plug, one=None):
    if LAY == 'one': return plug if one is None else one
    return plug if LAY == 'plug' else beside
def pp(): return LY().get('P', P)
def bx(): return LY().get('X0', BX0)
def nr(): return LY().get('ROWS', ROWS)
def ww(): return LY().get('W', W)
ONBOARD = ('plug', 'one')                # layouts where the ESP32 is plugged into the breadboard
def RAILY(k):
    for b in LY()['boards'].values():
        if k in b['rails']: return b['rails'][k]
def rx(r): return bx() + (r - 1) * pp()
def board(b=None): return LY()['boards'][b or ('L' if LAY == 'plug' else '')]
def hole(r, c, b=None): return (rx(r), board(b)['cols'][c])
def rail(k, r): return (rx(r), RAILY(k))
def epin(name, which=None):
    """Where the pin itself is drawn."""
    hdr, i = esp_pin(name, which)
    if LAY == 'one':
        return hole(ONE_ROW0 + i, 'i') if hdr == 'J1' else hole(ONE_ROW0 + i, 'a')
    if LAY == 'plug':
        return hole(PLUG_ROW0 + i, 'a', 'L') if hdr == 'J1' else hole(PLUG_ROW0 + i, 'j', 'U')
    EX0, EY0, EX1, EY1 = LY()['esp']
    x = EX0 + 15 + i * LY()['epitch']
    return (x, EY1 + 8) if hdr == 'J1' else (x, EY0 - 8)

# ---------------------------------------------------------------- wire ends
# An end is dict(pt, dir, txt, end): 'end' is what the jumper needs there ('male' for a breadboard hole,
# 'female' for a header pin), or None for soldered leads and screw terminals.
RAILNAME = {'t+': 'top + rail', 't-': 'top − rail', 'b+': 'bottom + rail', 'b-': 'bottom − rail'}
def E(pt, d, txt, end): return dict(pt=pt, dir=d, txt=txt, end=end)
def pn(name): return f'pin {name}'
def esp(name, which=None, note=''):
    hdr, i = esp_pin(name, which)
    if LAY == 'one':
        assert hdr == 'J1', f'{name}: no free hole beside the {hdr} pins on one breadboard'
        r = ONE_ROW0 + i
        return E(hole(r, 'j'), 'auto', f'hole {MIRROR["j"]}{r} (beside ESP32 {pn(name)}{note})', 'male')
    if LAY == 'plug':
        r = PLUG_ROW0 + i
        b, c = ('L', 'b') if hdr == 'J1' else ('U', 'i')
        return E(hole(r, c, b), 'auto', f'hole {MIRROR[c]}{r}, {board(b)["label"]} (the row of ESP32 {pn(name)}{note})', 'male')
    return E(epin(name, which), (0, 1) if hdr == 'J1' else (0, -1), f'ESP32 {pn(name)}{note}', 'female')
def hl(r, c, b=None, note=''):
    where = f', {board(b)["label"]}' if LAY == 'plug' else ''
    return E(hole(r, c, b), 'auto', f'hole {MIRROR[c]}{r}{where}' + (f' ({note})' if note else ''), 'male')
def rl(k, r, note=''): return E(rail(k, r), 'auto', RAILNAME[k] + (f' {note}' if note else ''), 'male')

# modules (off the breadboard): name -> (x0, y0, x1, y1, pin side, [pins], colour, title, subtitle)
MODS = {
  'ds3231': (30, 30, 200, 125, 'right', ['VCC (+)', 'SDA (D)', 'SCL (C)', 'NC', 'GND (−)'], '#1f4e8c', 'DS3231 clock', 'pins: check your board'),
  'tm1637': (30, 150, 200, 225, 'right', ['CLK', 'DIO', 'VCC', 'GND'], '#c0392b', 'TM1637 display', ''),
  'amp':    (30, 250, 200, 370, 'right', ['LRC', 'BCLK', 'DIN', 'GAIN', 'SD', 'GND', 'VIN'], '#7b3fa0', 'MAX98357A amp', ''),
  'usbc':   (30, 560, 170, 625, 'right', ['VBUS', 'GND'], '#2a6f9e', 'USB-C breakout', '5 V 3 A supply'),
  'lcd':    (800, 30, 980, 175, 'left', ['RST', 'CE', 'DC', 'DIN', 'CLK', 'VCC', 'BL', 'GND'], '#b03030', 'Nokia 5110 LCD', ''),
  'ring':   (800, 200, 980, 320, 'left', ['DI', '5V', 'GND'], '#1d1d1d', 'WS2812B ring', ''),
  'mosfet': (800, 345, 980, 455, 'left', ['TRIG', 'GND', 'VIN+', 'VIN−', 'OUT+', 'OUT−'], '#2a6f9e', 'MOSFET module', ''),
  'led':    (840, 490, 980, 570, 'left', ['LED +', 'LED −'], '#d39a00', '3 W LED star', 'on metal'),
}
def mod_box(mod):
    x0, y0, x1, y1, side, *rest = MODS[mod]
    dx = LY().get('rdx', 0) if side == 'left' else 0      # modules on the right move with a wider picture
    return (x0 + dx, y0, x1 + dx, y1, side, *rest)
def mpin_xy(mod, label):
    x0, y0, x1, y1, side, pins, *_ = mod_box(mod)
    y = y0 + 34 + pins.index(label) * 13
    return ((x1 + 2, y), (1, 0)) if side == 'right' else ((x0 - 2, y), (-1, 0))
def md(mod, label, txt, end='female'):
    p, d = mpin_xy(mod, label)
    return E(p, d, txt, end)

# ---------------------------------------------------------------- drawing helpers
def esc(s): return html.escape(str(s), quote=True)
class Svg:
    def __init__(self): self.o = []
    def add(self, s): self.o.append(s)
    def text(self, x, y, s, size=11, fill='#222', anchor='start', weight=400, extra=''):
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" {extra}>{esc(s)}</text>')
    def rect(self, x, y, w, h, fill, stroke='none', rx=4, sw=1, extra=''):
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')
    def circle(self, x, y, r, fill, stroke='none', sw=1, extra=''):
        self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')
    def line(self, x1, y1, x2, y2, col, w=1.5, extra=''):
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{col}" stroke-width="{w}" stroke-linecap="round" {extra}/>')

def autodir(a, b):
    # breadboard ends: leave toward the other end, mostly upward (wires lie on top of the board)
    dx, dy = b[0] - a[0], b[1] - a[1]
    if abs(dx) > 1.6 * abs(dy) and abs(dx) > 40: return (1 if dx > 0 else -1, -0.35)
    return (0, -1) if dy < 0 or abs(dy) < 30 else (0, 1)

def bez(p, q):
    a, da, b, db = p['pt'], p['dir'], q['pt'], q['dir']
    if da == 'auto': da = autodir(a, b)
    if db == 'auto': db = autodir(b, a)
    d = max(35, min(170, 0.42 * ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5))
    c1 = (a[0] + da[0] * d, a[1] + da[1] * d)
    c2 = (b[0] + db[0] * d, b[1] + db[1] * d)
    path = f'M{a[0]:.1f},{a[1]:.1f} C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {b[0]:.1f},{b[1]:.1f}'
    m = [(a[i] + 3 * c1[i] + 3 * c2[i] + b[i]) / 8 for i in (0, 1)]   # midpoint, for the number badge
    return path, m

PRE = {'plug': 'p:', 'one': 'o:', 'beside': ''}     # checkbox / highlight id prefix per layout
SID = {'plug': 'p-', 'one': 'o-', 'beside': 's-'}   # section id prefix
COL = {'3v3': '#f39c12', 'gnd': '#222222', '5v': '#d32f2f', 'yellow': '#e6b800', 'green': '#2e9e44', 'blue': '#2c6fd6',
       'purple': '#8e44ad', 'white': '#9aa0a6', 'brown': '#8d5a2b', 'cyan': '#14a3b8', 'pink': '#e05297', 'grey': '#6b7280'}
COLNAME = {'3v3': 'orange', 'gnd': 'black', '5v': 'red', 'yellow': 'yellow', 'green': 'green', 'blue': 'blue', 'purple': 'purple',
           'white': 'white', 'brown': 'brown', 'cyan': 'cyan', 'pink': 'pink', 'grey': 'grey'}
JUMPERS = ('female–female', 'female–male', 'male–male')

# ---------------------------------------------------------------- the steps
def W_(col, a, b, kind=None, ta=None, tb=None):
    if kind is None:
        ends = sorted([a['end'], b['end']])            # 'female' sorts before 'male'
        kind = f'{ends[0]}–{ends[1]}'
    return dict(col=col, a=a, b=b, ta=ta or a['txt'], tb=tb or b['txt'], kind=kind)

def jumper_need(wires):
    n = {k: sum(1 for w in wires if w['kind'] == k) for k in JUMPERS}
    tot = sum(n.values())
    if not tot: return []
    return [f'{tot} jumper wire{"s" if tot > 1 else ""}: ' + ', '.join(f'{v} {k}' for k, v in n.items() if v)]

def power_debug():
    """Step-by-step check for 'no 3.3 V on the rails', with this layout's hole names."""
    one, plug = LAY == 'one', LAY == 'plug'
    j = MIRROR['j']
    pin3 = X('the female end on the ESP32\'s 3V3 pin', f'hole {MIRROR["b"]}{PLUG_ROW0}, lower board', f'hole {j}{ONE_ROW0}')
    gnd = X('the black wire from the ESP32\'s G pin (by the USB ports) to the top − rail, and the black wire joining the two − rails at the right-hand end',
            f'the black wire from hole {MIRROR["i"]}{PLUG_ROW0}, upper board (the ESP32\'s first GND pin) to the top − rail',
            f'the black wire from hole {j}{ONE_ROW0 + 21} to the bottom − rail, and the black wire joining the top and bottom − rails at row 60')
    return [
      ('Set the meter up', '<b>Red lead in the V socket, not A or mA</b>: this is the most common mistake, and on amps the meter shorts the supply (the ESP32\'s light flashes as it restarts). Turn the dial to <b>DC volts</b> (V with a straight line; the 20 V range if it isn\'t auto-ranging). Black lead in <b>COM</b>. Meter probes are often too thick to reach the metal inside a breadboard hole: push the male end of a spare jumper into the hole and touch the probe to that instead.'),
      ('Is the ESP32 on?', 'With the USB cable in the port marked <b>USB</b>, the board\'s small power LED should be lit and the clock\'s page should open. If not, try another cable and USB port before anything else.'),
      ('Measure on the ESP32 itself', 'Red probe on the solder joint of the <b>3V3</b> pin, black on the joint of a <b>G</b> pin. It should read about 3.3 V. If it reads 0 V, the board isn\'t getting power (cable or port). If it reads well under 3 V, or the board gets warm, unplug at once and look for solder bridging two header pins.'),
      ('Measure the 3V3 pin\'s row', f'Keep black on the G joint and put red in {pin3}. 3.3 V here means the pin is making contact. 0 V means it isn\'t: press the ESP32 down firmly (the pins should disappear into the holes), and count the rows to check the 3V3 pin is really in the row you think.' if LAY != 'beside' else f'Keep black on the G joint and touch red to the male end of the orange wire. 0 V means the female end isn\'t gripping the pin: push it fully on, or try another jumper.'),
      ('Measure the + rail', 'Keep black on the G joint and put red in the top + rail, near where the orange wire goes in. 0 V here: the orange wire isn\'t in the rail (check it is in the rail row by the red line, marked +, not the blue − row), or the jumper is broken: swap it for another.'),
      ('Check the rail runs the whole length', 'Many full-size breadboards split each rail in the middle; look for a break in the red and blue lines halfway along. Put red in the + rail at the far end. If it reads 0 V there but 3.3 V near the wire, the rail is split: bridge the two halves with a short jumper, on the − rails too.'),
      ('Measure + rail to − rail', f'Now red in the top + rail, black in the top − rail. If the earlier checks passed but this reads 0 V, the − rail isn\'t connected to ground: check {gnd}.'),
      ('Reads −3.3 V', 'The probes are swapped. Nothing is wrong.'),
      ('The ESP32\'s light flashes when you touch the probes on', 'Stop: the meter is shorting the supply and the board restarts each time. Usually the dial is on current (A or mA) or the red lead is in the <b>A</b> or <b>mA</b> socket: move it to <b>V</b> and the dial to DC volts. On amps the meter can blow its internal fuse, so check it on a battery afterwards. Otherwise a probe tip is touching two pins at once, or the black probe is touching the RST pin (it sits next to the 3V3 pins): probe the breadboard holes rather than the pins.'),
      ('No meter?', 'Skip ahead to the buttons and the front display: if they work, the rails are fine.'),
    ]

def build_steps():
    S = []
    def step(**k):
        k['need'] = k['need'] + jumper_need(k['wires'])
        if k['id'] == 'power': k['debug'] = power_debug()
        S.append(k)
    plug, one = LAY == 'plug', LAY == 'one'
    A, B_ = str(G('PIN_BTN_A')), str(G('PIN_BTN_B'))
    sb = 'U' if plug else None                     # board for the light sensor

    step(id='flash', title='Flash the firmware', time='10 min', mods=[], parts=[], wires=[],
         need=['ESP32-S3 board', 'USB-C data cable', 'Computer'],
         intro='No wiring yet. Get the ESP32 running first, on its own, so you know the board and the firmware are good before anything else is connected.',
         todo=['Plug the USB-C cable into the port marked <b>USB</b> on the ESP32 (the board has two; this one carries the log).',
               'Flash the firmware from the <a href="firmware.html">Firmware</a> page: the web flasher needs nothing installed.',
               'Open a serial monitor at <b>115200</b> baud (the web flasher has one, or PlatformIO\'s monitor).',
               'On your phone, join the Wi-Fi network <b>CeilingClock-Setup</b> and pick your home network.'],
         test='Open <b>http://ceilingclock.local/</b> on your phone or computer. You should see the clock\'s page with the time and a green <b>synced just now</b>.',
         fix=[('ceilingclock.local doesn\'t open', 'Some Android phones don\'t support .local names. Use the IP address printed in the serial monitor instead.'),
              ('Nothing in the serial monitor', 'Use the port marked USB, not UART, at 115200 baud. Some USB-C cables only carry power: try another.'),
              ('No CeilingClock-Setup network', 'Press the RST button on the ESP32 and wait 20 seconds.')])

    if one:
        step(id='power', title='ESP32 onto the breadboard, and power rails', time='10 min', mods=[], parts=[],
             need=['1 full-size breadboard (830 holes, 60+ rows)'],
             intro='The ESP32 plugs into the left end of the breadboard, with its antenna sticking out past row 1. It covers most of the holes beside its pins, so each pin on one side keeps a single free hole in column a, and the pins on the other side get none. Every part after this goes in the free rows to the right of it.',
             todo=['Unplug the USB cable.',
                   'The pictures show the board turned so row 1 is on the left, with column j at the top. If yours stands upright with row 1 at the top, column a is on the left.',
                   f'Turn the ESP32 so its antenna points toward row 1 and hangs over the end of the board. Its row of pins starting with <b>3V3</b> goes into column <b>b</b>; the row starting with <b>GND, TX, RX</b> goes into column <b>j</b>. The first pins go in row <b>{ONE_ROW0}</b>, so the last ones are in row {ONE_ROW0 + 21}. Press down evenly on both rows of pins, not on the metal can.',
                   f'Each wire to an ESP32 pin goes into <b>column a</b> in the same row as that pin: the only hole beside it that the ESP32 doesn\'t cover.'],
             wires=[W_('3v3', esp('3V3'), rl('t+', 2)),
                    W_('gnd', esp('G', 'J1'), rl('b-', 22)),
                    W_('gnd', E((rx(60), RAILY('t-')), (1, -0.3), 'top − rail, right end', 'male'),
                              E((rx(60), RAILY('b-')), (1, 0.3), 'bottom − rail, right end', 'male'))],
             test='Plug the USB cable back in: the clock starts as before. With a multimeter, the top + and − rails read about 3.3 V. Before you measure, check the meter\'s red lead is in the socket marked <b>V</b>, not <b>A</b> or <b>mA</b>, and the dial is on DC volts: on amps the meter shorts the supply and the ESP32 restarts.',
             fix=[('The ESP32 doesn\'t start on the breadboard', 'A pin may be folded under the board. Lift it out gently, straighten the pin and press it in again.'),
                  ('The ESP32 goes dark when you add the wires', f'The orange wire is in a ground row or rail. It must start in a{ONE_ROW0} (the row of the first pin, 3V3) and end in the top + rail.')],
             warn=f'Leave hole a{ONE_ROW0 + J1.index("5V")} (the row of the ESP32\'s <b>5V</b> pin) empty.')
    elif plug:
        step(id='power', title='ESP32 onto the breadboards, and power rails', time='10 min', mods=[], parts=[],
             need=['2 full-size breadboards (830 holes)'],
             intro='The ESP32 is too wide for one breadboard: on one board its pins would cover every free hole. Two boards side by side give each row of pins its own board, with free holes beside every pin. Then three short wires set up the rails: the top rails become 3.3 V and ground, the bottom rails ground for the 5 V supply.',
             todo=['Unplug the USB cable.',
                   'Put the two breadboards side by side, both the same way round, so column <b>j</b> of one board sits next to column <b>a</b> of the other, with two rail strips between them. Leave all the rail strips on.',
                   'The pictures show the boards turned a quarter turn so row 1 is on the left. If yours stand upright with row 1 at the top, the left board is the <b>lower board</b> and the right board is the <b>upper board</b>.',
                   f'Turn the ESP32 so its antenna points toward row 1. Its row of pins starting with <b>3V3</b> goes into column <b>j</b> of the lower board; the row starting with <b>GND, TX, RX</b> goes into column <b>a</b> of the upper board. The first pins go in row <b>{PLUG_ROW0}</b>. It sits over the two middle rail strips, which stay unused. Press down evenly on both rows of pins, not on the metal can.',
                   'If the pins don\'t quite reach columns j and a on your boards, use i and b instead, or pull one middle rail strip off and push the boards together. What matters is that each pin has free holes beside it on the outside: the free holes in the same row of five as a pin are connected to that pin.'],
             wires=[W_('3v3', esp('3V3'), rl('t+', 1)),
                    W_('gnd', esp('G', 'J3'), rl('t-', 7)),
                    W_('gnd', esp('G', 'J1'), rl('b-', 22))],
             test='Plug the USB cable back in: the clock starts as before. With a multimeter, the top + and − rails read about 3.3 V. Before you measure, check the meter\'s red lead is in the socket marked <b>V</b>, not <b>A</b> or <b>mA</b>, and the dial is on DC volts: on amps the meter shorts the supply and the ESP32 restarts.',
             fix=[('The ESP32 doesn\'t start on the breadboard', 'A pin may be folded under the board. Lift it out gently, straighten the pin and press it in again.'),
                  ('The ESP32 goes dark when you add the wires', 'The orange wire is in a ground row or rail. It must start in the row of the first pin (3V3) and end in the top + rail.')],
             warn=f'Leave the row of the ESP32\'s <b>5V</b> pin (row {PLUG_ROW0 + J1.index("5V")}, lower board) empty.')
    else:
        step(id='power', title='Power rails', time='5 min', mods=[], parts=[],
             need=['Breadboard'],
             intro='The two rails along the top of the breadboard become 3.3 V (from the ESP32) and ground. Every small module will plug into them. A wire over the right-hand end joins the top ground rail to the bottom one.',
             wires=[W_('3v3', esp('3V3', note=' (the first pin, by the antenna)'), rl('t+', 1)),
                    W_('gnd', esp('G', 'J1', ' (last pin on the same side, by the USB ports)'), rl('t-', 26)),
                    W_('gnd', E((rx(30), RAILY('t-')), (1, -0.3), 'top − rail, right end', 'male'),
                              E((rx(30), RAILY('b-')), (1, 0.3), 'bottom − rail, right end', 'male'))],
             test='Nothing to see yet. If you have a multimeter, the top + and − rails should read about 3.3 V with the USB cable plugged in. Before you measure, check the meter\'s red lead is in the socket marked <b>V</b>, not <b>A</b> or <b>mA</b>, and the dial is on DC volts: on amps the meter shorts the supply and the ESP32 restarts.',
             fix=[('The ESP32 goes dark or resets when you plug in the wire', 'The 3V3 wire is in the − rail or touching G. Unplug USB and check: orange to +, black to −.')])

    if one:
        bA, bB = (33, None), (39, None)
        bw = [W_('green', esp(A), hl(33, 'a', note='button A, top-left leg')),
              W_('gnd', hl(35, 'j', note='button A, bottom-right leg'), rl('b-', 35)),
              W_('blue', esp(B_), hl(39, 'a', note='button B, top-left leg')),
              W_('gnd', hl(41, 'j', note='button B, bottom-right leg'), rl('b-', 41))]
        legs = f'{MIRROR["a"]}33 and {MIRROR["j"]}35, {MIRROR["a"]}39 and {MIRROR["j"]}41'
    elif plug:
        bA, bB = (1, 'L'), (28, 'L')
        bw = [W_('green', esp(A), hl(1, 'a', 'L', 'button A, top-left leg')),
              W_('gnd', hl(3, 'j', 'L', 'button A, bottom-right leg'), rl('b-', 3)),
              W_('blue', esp(B_), hl(28, 'a', 'L', 'button B, top-left leg')),
              W_('gnd', hl(30, 'j', 'L', 'button B, bottom-right leg'), rl('b-', 30))]
        legs = f'{MIRROR["a"]}1 and {MIRROR["j"]}3, {MIRROR["a"]}28 and {MIRROR["j"]}30'
    else:
        bA, bB = (3, None), (8, None)
        bw = [W_('green', esp(A), hl(3, 'a', note='button A, top-left leg')),
              W_('gnd', hl(5, 'j', note='button A, bottom-right leg'), rl('b-', 5)),
              W_('blue', esp(B_), hl(8, 'a', note='button B, top-left leg')),
              W_('gnd', hl(10, 'j', note='button B, bottom-right leg'), rl('b-', 10))]
        legs = f'{MIRROR["a"]}3 and {MIRROR["j"]}5, {MIRROR["a"]}8 and {MIRROR["j"]}10'
    step(id='buttons', title='Buttons', time='10 min', mods=[],
         need=['2 small 6 × 6 mm push buttons (from your tactile switch kit)'],
         intro='For testing, use two small 4-legged push buttons; the 16 mm panel buttons go in later. Each one sits <b>across the gap</b> in the middle of the breadboard. Wire to <b>diagonally opposite legs</b>: that way it works whichever way round the button sits.'
               + X('', ' On the lower board the rows beside the ESP32 are taken, so the buttons go at the two ends.', ' They go in the free rows to the right of the ESP32.'),
         parts=[('button', bA[0], 'A', bA[1]), ('button', bB[0], 'B', bB[1])], wires=bw,
         test='On the clock\'s page, press button <b>B</b>: the <b>Front display</b> button on the page flips between on and off. Now press B and keep holding it: 3 seconds after you pressed, <b>Projector</b> flips on the page (the page can take another second to show it). Let go after it flips; letting go sooner counts as a short press. (Button A snoozes an alarm; you\'ll try it later.)',
         fix=[('Nothing happens', f'Check the wires go to diagonally opposite legs ({legs}) and that the button straddles the gap.'),
              ('It acts as if always pressed', 'The button is turned so both wires land on legs that are always connected. Turn it 90°.')])

    step(id='tm1637', title='Front display (TM1637)', time='5 min', mods=['tm1637'], parts=[],
         need=['TM1637 display'],
         intro='The four-digit display that shows the time on the front of the clock. Its two data pins go straight to the ESP32; power comes from the top rails.',
         wires=[W_('yellow', esp(str(G('PIN_TM_CLK'))), md('tm1637', 'CLK', 'display CLK')),
                W_('white', esp(str(G('PIN_TM_DIO'))), md('tm1637', 'DIO', 'display DIO')),
                W_('3v3', md('tm1637', 'VCC', 'display VCC'), rl('t+', 4)),
                W_('gnd', md('tm1637', 'GND', 'display GND'), rl('t-', 5))],
         test='The display shows the time within a second. On the settings page, change the front display\'s brightness: it follows.',
         fix=[('Display stays blank', 'CLK and DIO swapped? VCC must go to the + rail (3.3 V).'),
              ('Shows 88:88 or garbage', 'A loose jumper: push each one firmly onto its pin.')])

    step(id='lcd', title='Projector LCD (Nokia 5110)', time='10 min', mods=['lcd'], parts=[],
         need=['Nokia 5110 LCD (no need to cut it yet)'],
         intro='The LCD makes the image on the ceiling. Test it as it comes, before cutting its window: lighting its own backlight lets you read it on the bench.',
         wires=[W_('brown', esp(str(G('PIN_LCD_RST'))), md('lcd', 'RST', 'LCD RST')),
                W_('purple', esp(str(G('PIN_LCD_CE'))), md('lcd', 'CE', 'LCD CE')),
                W_('cyan', esp(str(G('PIN_LCD_DC'))), md('lcd', 'DC', 'LCD DC')),
                W_('green', esp(str(G('PIN_LCD_DIN'))), md('lcd', 'DIN', 'LCD DIN')),
                W_('yellow', esp(str(G('PIN_LCD_CLK'))), md('lcd', 'CLK', 'LCD CLK')),
                W_('3v3', md('lcd', 'VCC', 'LCD VCC'), rl('t+', 28)),
                W_('gnd', md('lcd', 'BL', 'LCD BL (bench only: lights it)'), rl('t-', 27)),
                W_('gnd', md('lcd', 'GND', 'LCD GND'), rl('t-', 29))],
         test='The LCD shows the time, <b>back to front</b>: the clock mirrors it for the projector. Untick <b>Mirror left/right</b> in the projector settings to read it, and tick it again before testing the optics.',
         fix=[('Blank or solid black', 'Adjust <b>LCD contrast</b> on the settings page. Check RST and CE.'),
              ('No backlight', 'On some boards BL lights when connected to + instead of −. Move that one wire to the top + rail.')])

    L1, L2 = (45, 48) if one else (13, 16)
    step(id='ldr', title='Light sensor', time='5 min', mods=[],
         need=['GL5528 light sensor', '10 kΩ resistor (brown-black-orange)'],
         intro='A light-dependent resistor and a fixed 10 kΩ resistor make a divider: the voltage between them rises as the room gets brighter. Neither part has a polarity.'
               + X('', ' They go on the upper board, next to the 3.3 V rail.', ''),
         parts=[('ldr', L1, L2, sb), ('res_rail', L2, 't-', '10 kΩ', sb)],
         wires=[W_('3v3', rl('t+', L1), hl(L1, 'a', sb, 'one leg of the sensor')),
                W_('pink', esp(str(G('PIN_LDR'))), hl(L2, 'd', sb, 'where sensor and resistor meet'))],
         test='In the night settings, watch <b>sensor now</b> next to "Dark below". It goes up with a torch on the sensor and down when you cover it with a finger.',
         fix=[('Always about 0', f'The sensor leg isn\'t in row {L1} or the orange wire isn\'t on the + rail.'),
              ('Always about 4095', 'The 10 kΩ resistor isn\'t reaching the − rail.')])

    if one:
        step(id='ds3231', title='Clock module (DS3231): test it later', time='0 min', mods=[], parts=[], wires=[],
             need=['Nothing for now'],
             intro='The clock module connects to ESP32 pins 1 and 2. On one breadboard those pins are in column j, and the ESP32 covers every hole beside them, so there is nowhere to plug its wires. Skip this step: the clock runs fine without the module, setting its time from the internet, and the page shows <b>no RTC</b>.',
             todo=['Test the module when the electronics move to the perfboard (<a href="assembly.html#step-4">assembly step 4</a>), or switch to the two-breadboard layout at the top of this page.'],
             test='Nothing to test yet. The clock\'s page says <b>no RTC</b>, which is expected.',
             fix=[('I want to test it now', 'Use the <b>Plugged in across two breadboards</b> layout at the top of the page: there, pins 1 and 2 have free holes.')])
    else:
      step(id='ds3231', title='Clock module (DS3231)', time='5 min', mods=['ds3231'], parts=[],
         need=['DS3231 module (with its coin cell)'],
         intro='The battery-backed clock that keeps time when Wi-Fi or power drops. '
               + X('Its two data pins are on the <b>other</b> side of the ESP32 (pins 1 and 2), so route those wires round the end of the board.',
                   'Its two data pins are on the ESP32\'s top edge (pins 1 and 2), so these two wires start on the upper board.'),
         wires=[W_('blue', esp(str(G('PIN_SDA')), 'J3', X(' (far side)', '')), md('ds3231', 'SDA (D)', 'module SDA (marked D on mini boards)')),
                W_('yellow', esp(str(G('PIN_SCL')), 'J3', X(' (far side)', '')), md('ds3231', 'SCL (C)', 'module SCL (marked C)')),
                W_('3v3', md('ds3231', 'VCC (+)', 'module VCC (+)'), rl('t+', 2)),
                W_('gnd', md('ds3231', 'GND (−)', 'module GND (−)'), rl('t-', 3))],
         test='The page shows <b>RTC backup ok</b>. Turn your router\'s Wi-Fi off and press RST on the ESP32: the time is still right.',
         fix=[('Still says "no RTC"', 'SDA and SCL swapped, or VCC on 5 V instead of 3.3 V.'),
              ('ZS-042 (larger) board', 'It charges its battery. With a non-rechargeable CR2032, remove the 200 Ω resistor or diode beside the holder first.')])

    step(id='supply', title='5 V supply', time='10 min', mods=['usbc'], parts=[],
         need=['USB-C breakout + 5 V 3 A adapter', '2 wires soldered to VBUS and GND (or header pins)'],
         intro='From here on, parts need more current than the ESP32 can give. The 5 V supply feeds the <b>bottom</b> rails only. The ESP32 stays on your computer\'s USB, and the grounds are already joined.',
         wires=[W_('5v', md('usbc', 'VBUS', 'breakout VBUS', None), rl('b+', 1), 'soldered lead'),
                W_('gnd', md('usbc', 'GND', 'breakout GND', None), rl('b-', 2), 'soldered lead')],
         test='Plug the adapter in. Everything carries on as before. With a multimeter, the bottom rails read about 5 V.',
         fix=[('Reads 0 V', 'Some breakouts only switch on with a USB-C to USB-C charger and 5.1 kΩ CC resistors (yours has them). Try another cable.')],
         warn='Never connect this 5 V to the ESP32\'s <b>5V</b> pin while the computer is plugged in: two supplies would fight through the board. In the finished clock the computer stays unplugged.')

    step(id='amp', title='Amplifier and speaker', time='10 min', mods=['amp'],
         need=['MAX98357A amplifier', '40 mm speaker', '100 µF capacitor'],
         intro='Plays the alarm sounds. The capacitor steadies its supply; the long leg is +, and the stripe marks −.',
         parts=[('cap', 19, '100 µF')],
         wires=[W_('purple', esp(str(G('PIN_I2S_BCLK'))), md('amp', 'BCLK', 'amp BCLK')),
                W_('cyan', esp(str(G('PIN_I2S_LRC'))), md('amp', 'LRC', 'amp LRC')),
                W_('white', esp(str(G('PIN_I2S_DOUT'))), md('amp', 'DIN', 'amp DIN')),
                W_('5v', md('amp', 'VIN', 'amp VIN'), rl('b+', 6, '(5 V)')),
                W_('gnd', md('amp', 'GND', 'amp GND'), rl('b-', 7))],
         test='Screw the speaker leads into the amp\'s + and − terminals. Under <b>Sounds</b>, press <b>Play</b> on beep.wav: four beeps. Then give an alarm a radio or podcast URL and press <b>Preview stream</b>.',
         fix=[('Silent', 'Is the 5 V adapter plugged in? Check BCLK, LRC and DIN aren\'t swapped. Leave GAIN and SD unconnected.'),
              ('Crackles', 'Push the capacitor\'s legs fully into the rails (long leg to +).')])

    if one:
        rr, rw = ('res', 50, 54, 'h', '330 Ω', None), [W_('green', esp(str(G('PIN_RING'))), hl(50, 'j', note='one end of the 330 Ω')),
                                                   W_('green', hl(54, 'j', note='other end of the 330 Ω'), md('ring', 'DI', 'ring DI (data in)'))]
    elif plug:
        rr, rw = ('res', 15, 19, 'h', '330 Ω', 'L'), [W_('green', esp(str(G('PIN_RING'))), hl(15, 'f', 'L', 'one end of the 330 Ω')),
                                                  W_('green', hl(19, 'f', 'L', 'other end of the 330 Ω'), md('ring', 'DI', 'ring DI (data in)'))]
    else:
        rr, rw = ('res', 21, 25, 'c', '330 Ω', None), [W_('green', esp(str(G('PIN_RING'))), hl(21, 'a', note='one end of the 330 Ω')),
                                                   W_('green', hl(25, 'a', note='other end of the 330 Ω'), md('ring', 'DI', 'ring DI (data in)'))]
    step(id='ring', title='Sunrise ring', time='10 min', mods=['ring'],
         need=['WS2812B 16-LED ring (with leads soldered on)', '330 Ω resistor (orange-orange-brown)', '1000 µF capacitor'],
         intro='The sunrise light. The 330 Ω resistor protects the ring\'s data input; the big capacitor smooths the current the LEDs draw. Mind the capacitor\'s stripe: it goes to −.',
         parts=[rr, ('cap', 23, '1000 µF')],
         wires=rw + [W_('5v', md('ring', '5V', 'ring 5V'), rl('b+', 27)),
                     W_('gnd', md('ring', 'GND', 'ring GND'), rl('b-', 28))],
         test='Give an alarm a sunrise time (for example 15 minutes) and press <b>Ring now</b>: the ring glows warm white until you press <b>Dismiss</b> (or hold button A for 2 seconds).',
         fix=[('Nothing lights', 'Make sure the wire goes to DI (in), not DO (out). Check the 5 V adapter is on.'),
              ('Flickers or wrong colours', 'Keep the data wire short. If it persists, a 74AHCT125 level shifter on the data line fixes it.')])

    lr = ('res', 22, 26, 'h', '4.7 Ω 2 W', 'L') if plug else ('res', 56, 60, 'c', '4.7 Ω 2 W', None) if one else ('res', 26, 30, 'g', '4.7 Ω 2 W', None)
    lb = 'L' if plug else None
    lc = 'a' if one else 'j'               # design letter of the free hole in the resistor's rows
    step(id='led', title='Projector LED', time='15 min', mods=['mosfet', 'led'],
         need=['MOSFET module', '3 W LED on its star (leads soldered on)', '4.7 Ω 2 W resistor', 'Something metal to sit the LED on'],
         intro='The bright LED that lights the LCD. The MOSFET module switches and dims it for the ESP32. The 4.7 Ω resistor limits the current to about 400 mA, and it gets warm, so keep it off the plastic.',
         parts=[lr],
         wires=[W_('grey', esp(str(G('PIN_PROJ_LED'))), md('mosfet', 'TRIG', 'module TRIG / PWM')),
                W_('gnd', md('mosfet', 'GND', 'module trigger GND'), rl('b-', 26)),
                W_('5v', md('mosfet', 'VIN+', 'module VIN+', None), rl('b+', 29, '(5 V)'), 'screw terminal–male'),
                W_('gnd', md('mosfet', 'VIN−', 'module VIN−', None), rl('b-', 25), 'screw terminal–male'),
                W_('5v', md('mosfet', 'OUT+', 'module OUT+', None), hl(lr[1], lc, lb, 'one end of the 4.7 Ω'), 'screw terminal–male'),
                W_('5v', hl(lr[2], lc, lb, 'other end of the 4.7 Ω'), md('led', 'LED +', 'LED +', None), 'male–soldered lead'),
                W_('gnd', md('led', 'LED −', 'LED −', None), md('mosfet', 'OUT−', 'module OUT−', None), 'soldered lead–screw terminal')],
         test='On the clock\'s page, switch the <b>Projector</b> off and on: the LED goes off and on. Change the projector\'s day brightness: it dims.',
         fix=[('LED never lights', 'LED + and − swapped? Check OUT+ goes through the resistor to LED +.'),
              ('Always on full', 'TRIG is on the wrong pin, or the module\'s trigger GND isn\'t connected.')],
         warn='Don\'t look straight into the lit LED. Without its heatsink it heats up in seconds: sit the star on metal and don\'t leave it at full brightness for more than a few seconds.')
    return S

def check_holes(S):
    """No breadboard hole or rail hole gets two things."""
    used = {}
    for st in S:
        for w in st['wires']:
            for e in (w['a'], w['b']):
                if e['end'] == 'male' or (e['dir'] == 'auto'):
                    key = tuple(round(v) for v in e['pt'])
                    assert key not in used, f'{LAY}: {st["id"]} {e["txt"]} clashes with {used[key]}'
                    used[key] = f'{st["id"]} {e["txt"]}'

# ---------------------------------------------------------------- drawing one step
def draw_board(s):
    P, BX0, ROWS = pp(), bx(), nr()
    hs = min(4.4, 0.36 * P)
    for bid, B in LY()['boards'].items():
        s.rect(BX0 - 22, B['y0'], (ROWS - 1) * P + 44, B['y1'] - B['y0'], '#f3f1ea', '#cfcabc', 10, 1.2)
        if B['dead']:
            for y in B['dead']:
                for r in range(1, ROWS + 1): s.rect(rx(r) - hs / 2, y - hs / 2, hs, hs, '#cfcabc', rx=0.8)
        for key, y in B['rails'].items():
            col = '#d33a2c' if key.endswith('+') else '#2b5fd9'
            ly = y - 7 if key.endswith('+') else y + 7
            if key == 't+': ly = y - 7
            s.line(BX0 - 10, ly, rx(ROWS) + 10, ly, col, 1)
            s.text(BX0 - 18, y + 3.5, '+' if key.endswith('+') else '−', 11, col, 'end', 700)
            for r in range(1, ROWS + 1): s.rect(rx(r) - hs / 2, y - hs / 2, hs, hs, '#8a8577', rx=0.8)
        if 't+' in B['rails']: s.text(rx(ROWS) + 14, B['rails']['t+'] + 4, '3.3 V', 10, '#d33a2c', 'start', 700)
        if 'b+' in B['rails']: s.text(rx(ROWS) + 14, B['rails']['b+'] + 4, '5 V', 10, '#d33a2c', 'start', 700)
        for c, y in B['cols'].items():
            s.text(BX0 - 14, y + 3.5, MIRROR[c], 9.5, '#8a8577', 'middle')
            for r in range(1, ROWS + 1): s.rect(rx(r) - hs / 2, y - hs / 2, hs, hs, '#8a8577', rx=0.8)
        s.rect(BX0 - 6, B['gap'], (ROWS - 1) * P + 12, 16, '#e6e2d6', rx=2)
        if B['label']: s.text(rx(15.5), B['gap'] + 11.5, B['label'].upper(), 9.5, '#a29c8b', 'middle', 700, extra='letter-spacing="2"')
        for r in [1] + list(range(5, ROWS + 1, 5)): s.text(rx(r), B['rowy'], r, 8.5 if P > 12 else 7.5, '#8a8577', 'middle')

def draw_esp(s):
    EX0, EY0, EX1, EY1 = LY()['esp']
    plug = LAY in ONBOARD
    s.rect(EX0, EY0, EX1 - EX0, EY1 - EY0, '#1e2126', '#000', 6, extra='opacity="0.94"' if plug else '')
    L, h = EX1 - EX0, EY1 - EY0
    sw = 0.3 * L                                           # the metal can over the ESP32-S3 module
    s.rect(EX0 + 6, EY0 + 24, sw, h - 48, '#c8ccd2', rx=3)
    for i in range(5): s.line(EX0 + 12, EY0 + 32 + i * 12, EX0 + 30, EY0 + 32 + i * 12, '#9aa0a8', 2)
    s.text(EX0 + 6 + sw / 2, EY0 + h / 2 + 4, 'ESP32-S3', 10 if L > 300 else 8.5, '#5b6068', 'middle', 700)
    # RST and BOOT push buttons, just past the can on the GND/TX/RX side (as on the board)
    by = EY0 + 0.36 * h
    for fx, lab in ((0.42, 'RST'), (0.51, 'BOOT')):
        bxc = EX0 + fx * L
        s.rect(bxc - 7, by - 6, 14, 12, '#d9dde2', '#8a9099', 1.5, 1)
        s.circle(bxc, by, 3.6, '#2b2f36')
        s.text(bxc, by + 17, lab, 7.5 if L > 300 else 6.5, '#ffffff', 'middle', 700)
    s.rect(EX1 - 2, EY0 + 28, 16, 20, '#9aa0a8', rx=2); s.rect(EX1 - 2, EY0 + 68, 16, 20, '#9aa0a8', rx=2)
    halo = 'stroke="#fbfaf6" stroke-width="3" paint-order="stroke"' if plug else ''
    s.text(EX1 + 18, EY0 + 42, 'UART', 8.5, '#6b7280', extra=halo)
    s.text(EX1 + 18, EY0 + 82, 'USB → computer', 8.5, '#2b5fd9', 'start', 700, extra=halo)
    s.text(EX0 + 0.76 * L, EY0 + h / 2 + 4, 'DevKitC-1', 11 if L > 300 else 9, '#cfd3da', 'middle', 700)
    for hdr, lst in (('J1', J1), ('J3', J3)):
        for i, nm in enumerate(lst):
            x, y = epin(nm, hdr)
            if not plug: y = y - 14 if hdr == 'J1' else y + 14
            s.circle(x, y, 2.6, '#d8ad45')
            ty = (y - 9) if hdr == 'J1' else (y + 13)
            s.text(x, ty, nm, 7.5 if pp() > 12 else 6, '#ffd27a' if nm == '5V' else '#e7e9ec', 'middle')

def draw_step(S, k):
    s = Svg()
    s.add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ww()} {H}" class="bbsvg" font-family="system-ui,-apple-system,Segoe UI,sans-serif">')
    s.rect(0, 0, ww(), H, '#fbfaf6', rx=0)
    mods_now = [m for st in S[:k + 1] for m in st['mods']]
    new_mods = S[k]['mods']
    draw_board(s)
    if LAY == 'beside': draw_esp(s)
    # parts on the breadboard
    parts_svg = Svg()
    for idx, st in enumerate(S[:k + 1]):
        p_ = parts_svg
        p_.add(f'<g opacity="{"1" if idx == k else "0.45"}">')
        for p in st['parts']:
            if p[0] == 'button':
                r, B = p[1], board(p[3])
                ye, yf = B['cols']['e'], B['cols']['f']
                x0, x1 = rx(r) - 4, rx(r + 2) + 4
                if pp() < 12: x0, x1 = rx(r) - 5, rx(r + 2) + 5
                p_.rect(x0, ye - 6, x1 - x0, yf - ye + 12, '#30343b', rx=3)
                p_.circle((x0 + x1) / 2, (ye + yf) / 2, 8, '#111', '#5b6068')
                for y in (ye, yf):
                    for rr in (r, r + 2): p_.circle(rx(rr), y, 2.6, '#c8ccd2')
                p_.text(x1 + 9, (ye + yf) / 2 + 4, p[2], 11, '#30343b', 'middle', 700)
            elif p[0] == 'ldr':
                a, b = hole(p[1], 'c', p[3]), hole(p[2], 'c', p[3])
                p_.line(*a, (a[0] + b[0]) / 2 - 8, a[1] - 14, '#888', 1.6); p_.line(*b, (a[0] + b[0]) / 2 + 8, a[1] - 14, '#888', 1.6)
                p_.circle((a[0] + b[0]) / 2, a[1] - 18, 9, '#f4e2c0', '#b98a3a', 1.5)
                p_.add(f'<path d="M{(a[0]+b[0])/2-6},{a[1]-18} q3,-5 6,0 q3,5 6,0" fill="none" stroke="#b03030" stroke-width="1.6"/>')
                p_.text((a[0] + b[0]) / 2, a[1] - 31, 'light sensor', 9, '#6b5a2b', 'middle', 700)
            elif p[0] == 'res_rail':
                a, b = hole(p[1], 'a', p[4]), rail(p[2], p[1] + 1)
                p_.line(*a, *b, '#888', 1.6)
                mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
                p_.rect(mx - 4, my - 9, 8, 18, '#d9c49a', '#9a8455', 2)
                p_.text(mx + 10, my + 3, p[3], 9, '#6b5a2b', 'start', 700)
            elif p[0] == 'res':
                a, b = hole(p[1], p[3], p[5]), hole(p[2], p[3], p[5])
                p_.line(*a, *b, '#888', 1.6)
                mx = (a[0] + b[0]) / 2
                big = '2 W' in p[4]
                p_.rect(mx - (16 if big else 11), a[1] - (5 if big else 4), 32 if big else 22, 10 if big else 8, '#7ab3d6' if big else '#d9c49a', '#55606e' if big else '#9a8455', 3)
                p_.text(mx, a[1] - 9, p[4], 9, '#55606e', 'middle', 700, extra='stroke="#f3f1ea" stroke-width="3" paint-order="stroke"')
            elif p[0] == 'cap':
                r = p[1]
                a, b = rail('b+', r), rail('b-', r + 1)
                cx, cy = (a[0] + b[0]) / 2, RAILY('b-') + 26
                p_.line(*a, cx - 3, cy - 8, '#888', 1.4); p_.line(*b, cx + 3, cy - 8, '#888', 1.4)
                big = '1000' in p[2]
                rw = 9 if big else 6
                p_.rect(cx - rw, cy - 8, 2 * rw, 20 if big else 14, '#2140a0', rx=3)
                p_.rect(cx + rw - 4, cy - 8, 3, 20 if big else 14, '#c8ccd2', rx=1)
                p_.text(cx, cy + (25 if big else 19), p[2], 8.5, '#2140a0', 'middle', 700)
        p_.add('</g>')
    s.o += parts_svg.o
    if LAY in ONBOARD: draw_esp(s)         # plugged in: the board sits on top of the breadboards
    # modules present
    for m in mods_now:
        x0, y0, x1, y1, side, pins, col, title, sub = mod_box(m)
        s.add(f'<g opacity="{"1" if m in new_mods else "0.45"}">')
        s.rect(x0, y0, x1 - x0, y1 - y0, '#fffdf8', col, 8, 2)
        s.rect(x0, y0, x1 - x0, 20, col, rx=8); s.rect(x0, y0 + 12, x1 - x0, 8, col, rx=0)
        s.text(x0 + 8, y0 + 14.5, title, 11, '#fff', 'start', 700)
        if sub: s.text(x0 + (x1 - x0) / 2, y1 - 6, sub, 8.5, '#8a8577', 'middle')
        for pnm in pins:
            (px, py), _ = mpin_xy(m, pnm)
            s.circle(px, py, 3, '#d8ad45', '#6b5a2b', 0.8)
            s.text(px - 7 if side == 'right' else px + 7, py + 3.5, pnm, 9, '#333', 'end' if side == 'right' else 'start')
        if m == 'amp':   # speaker on its terminal
            s.circle(x0 + 55, y1 + 32, 22, '#3b3b3b'); s.circle(x0 + 55, y1 + 32, 9, '#777')
            s.line(x0 + 50, y1, x0 + 48, y1 + 12, '#d32f2f', 2); s.line(x0 + 62, y1, x0 + 64, y1 + 12, '#222', 2)
            s.text(x0 + 85, y1 + 36, 'speaker', 9, '#6b7280')
        if m == 'ring':
            s.add(f'<circle cx="{x0 + 120}" cy="{y0 + 66}" r="30" fill="none" stroke="#1d1d1d" stroke-width="9"/>')
            for a in range(16):
                s.circle(x0 + 120 + 30 * math.cos(a * math.pi / 8), y0 + 66 + 30 * math.sin(a * math.pi / 8), 3, '#ffe9a8')
        if m == 'led':
            s.rect(x0 + 50, y0 + 26, 80, 40, '#9aa0a8', rx=3)
            for i in range(6): s.line(x0 + 56 + i * 13, y0 + 66, x0 + 56 + i * 13, y0 + 74, '#7b8088', 3)
            s.circle(x0 + 90, y0 + 36, 13, '#e9edf2', '#b8bec6'); s.circle(x0 + 90, y0 + 36, 4, '#ffe07a')
        if m == 'usbc':
            s.rect(x0 - 26, y0 + 22, 22, 26, '#e8eaed', '#9aa0a8', 3); s.text(x0 - 15, y0 + 60, '5 V', 8.5, '#6b7280', 'middle')
            s.line(x0 - 4, y0 + 35, x0 + 6, y0 + 35, '#555', 4)
        s.add('</g>')
    # wires: earlier steps faded, this step bright with number badges
    n = 0
    pre = PRE[LAY]
    for idx, st in enumerate(S[:k + 1]):
        cur = idx == k
        for w in st['wires']:
            path, m = bez(w['a'], w['b'])
            col = COL[w['col']]
            if cur:
                n += 1
                s.add(f'<g class="wire" data-w="{pre}{S[k]["id"]}-{n}"><path d="{path}" fill="none" stroke="#fff" stroke-width="6.5" stroke-linecap="round"/>'
                      f'<path d="{path}" fill="none" stroke="{col}" stroke-width="3.6" stroke-linecap="round"/>')
                for e in (w['a'], w['b']): s.circle(*e['pt'], 3.6, col, '#fff', 1.2)
                s.circle(m[0], m[1], 9, '#fff', col, 2); s.text(m[0], m[1] + 3.8, n, 10.5, '#111', 'middle', 700)
                s.add('</g>')
            else:
                s.add(f'<path d="{path}" fill="none" stroke="{col}" stroke-width="2.4" stroke-linecap="round" opacity="0.28"/>')
    s.add('</svg>')
    return '\n'.join(s.o)

# ---------------------------------------------------------------- small explainer pictures
def svg_basics():
    s = Svg()
    s.add('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 560 330" class="bbsvg" font-family="system-ui,-apple-system,Segoe UI,sans-serif">')
    s.rect(0, 0, 560, 330, '#fbfaf6', rx=0)
    x0, p, n = 46, 13, 12
    cols = {'a': 98, 'b': 110, 'c': 122, 'd': 134, 'e': 146, 'f': 170, 'g': 182, 'h': 194, 'i': 206, 'j': 218}
    ys = {'t+': 58, 't-': 72, 'b+': 244, 'b-': 258}
    s.rect(x0 - 18, 42, n * p + 26, 232, '#f3f1ea', '#cfcabc', 10)
    s.rect(x0 - 6, 152, n * p - 2, 12, '#e6e2d6', rx=2)
    s.rect(x0 - 8, ys['t+'] - 6, n * p - 2, 12, '#ffd6d1', rx=6)
    s.rect(x0 + 5 * p - 6, cols['a'] - 6, 12, cols['e'] - cols['a'] + 12, '#c9f0cf', rx=6)
    s.rect(x0 + 5 * p - 6, cols['f'] - 6, 12, cols['j'] - cols['f'] + 12, '#cfe0ff', rx=6)
    for y in list(ys.values()) + list(cols.values()):
        for r in range(n): s.rect(x0 + r * p - 2.3, y - 2.3, 4.6, 4.6, '#8a8577', rx=1)
    for c, y in cols.items(): s.text(x0 - 10, y + 3.5, MIRROR[c], 9.5, '#8a8577', 'end')
    s.text(x0 - 10, ys['t+'] + 4, '+', 11, '#d33a2c', 'end', 700); s.text(x0 - 10, ys['t-'] + 4, '−', 11, '#2b5fd9', 'end', 700)
    tx = x0 + n * p + 22
    def note(y, head, body, col):
        s.text(tx, y, head, 12.5, col, 'start', 700)
        for i, ln in enumerate(body): s.text(tx, y + 17 + i * 15, ln, 11.5, '#333')
    note(52, 'Rails (red and blue lines)', ['Each line of holes along the edge is one long', 'connection. Use them for + power and − ground.'], '#c0392b')
    note(112, 'Columns of five', ['Holes f–j in one column are joined, so', 'anything in the same five is connected.'], '#2e8b3d')
    note(172, 'The gap in the middle', ['Splits each column: f–j and a–e are separate.', 'Push buttons sit across it.'], '#555')
    note(232, 'a–e: another group of five', ['Joined to each other, not to f–j.'], '#2b5fd9')
    s.add('</svg>')
    return '\n'.join(s.o)

def svg_jumpers():
    s = Svg()
    s.add('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 130" class="bbsvg" font-family="system-ui,-apple-system,Segoe UI,sans-serif">')
    s.rect(0, 0, 640, 130, '#fbfaf6', rx=0)
    def end(x, y, male, flip):
        d = -1 if flip else 1
        if male:
            s.rect(x - 7 if d > 0 else x - 1, y - 5, 8, 10, '#222', rx=1)
            s.line(x + d * 1, y, x + d * 12, y, '#c9a227', 2.4)
        else:
            s.rect(x - 9 if d > 0 else x - 3, y - 6, 12, 12, '#222', rx=1.5)
            s.circle(x + d * 2, y, 2, '#555')
    for i, (a, b, lab, use) in enumerate([(True, True, 'male–male', 'breadboard hole to breadboard hole'),
                                          (False, True, 'female–male', 'ESP32 or module pin to a breadboard hole'),
                                          (False, False, 'female–female', 'ESP32 pin straight to a module pin')]):
        x = 30 + i * 205
        s.add(f'<path d="M{x+14},64 C{x+60},30 {x+110},98 {x+150},64" fill="none" stroke="{["#2e9e44","#e6b800","#2c6fd6"][i]}" stroke-width="4" stroke-linecap="round"/>')
        end(x + 8, 64, a, True); end(x + 156, 64, b, False)
        s.text(x + 82, 22, lab, 13, '#222', 'middle', 700)
        s.text(x + 82, 112, use, 10.5, '#555', 'middle')
    s.add('</svg>')
    return '\n'.join(s.o)

def svg_optics():
    s = Svg()
    s.add('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 330" class="bbsvg" font-family="system-ui,-apple-system,Segoe UI,sans-serif">')
    s.rect(0, 0, 640, 330, '#1d2026', rx=0)
    s.add('<polygon points="250,300 330,300 470,16 110,16" fill="#ffe6b0" opacity="0.10"/>')
    s.rect(60, 8, 520, 10, '#3a3f47', rx=2); s.text(320, 34, 'ceiling: the time, sharp when the lens is right', 11.5, '#ffd696', 'middle', 700)
    def part(y, w, h, col, lab, sub):
        s.rect(290 - w / 2, y, w, h, col, rx=2)
        s.line(290 + w / 2 + 6, y + h / 2, 362, y + h / 2, '#5b6068', 1)
        s.text(370, y + h / 2 + 4, lab, 12, '#e8e8e8', 'start', 700)
        s.text(370 + 7.2 * len(lab) + 8, y + h / 2 + 4, sub, 10.5, '#aab0b8')
    s.add('<ellipse cx="290" cy="110" rx="34" ry="5" fill="#9fd3ff" opacity="0.8"/>')
    s.text(370, 106, 'lens (50 mm, f = 100)', 12, '#e8e8e8', 'start', 700); s.text(370, 122, 'move it up and down to focus', 10.5, '#aab0b8')
    part(232, 46, 4, '#c8ccd2', 'LCD, glass up', '30 mm above the LED')
    part(266, 50, 2, '#ffffff', 'baking paper', '10 mm above the LED')
    s.rect(272, 296, 36, 8, '#9aa0a8', rx=2); s.circle(290, 294, 5, '#ffe07a')
    s.line(314, 298, 362, 298, '#5b6068', 1); s.text(370, 302, 'LED, pointing up', 12, '#e8e8e8', 'start', 700)
    s.line(230, 112, 230, 232, '#ffd696', 1.2); s.line(224, 112, 236, 112, '#ffd696', 1.2); s.line(224, 232, 236, 232, '#ffd696', 1.2)
    s.text(222, 176, 'about 106 mm', 11, '#ffd696', 'end', 700)
    s.add('</svg>')
    return '\n'.join(s.o)

# ---------------------------------------------------------------- the page
def sections():
    """Both layouts' steps; the page shows one set at a time."""
    global LAY
    out, navs, totals = [], [], {}
    for lay in ('plug', 'one', 'beside'):
        LAY = lay
        S = build_steps()
        check_holes(S)
        pre, sid = PRE[lay], SID[lay]
        totals[lay] = sum(len(st['wires']) for st in S)
        navs.append(f'<div class="toc only-{lay}">' + ''.join(f'<a href="#{sid}{st["id"]}"><span>{i + 1}</span>{esc(st["title"])}</a>' for i, st in enumerate(S)) + '</div>')
        for i, st in enumerate(S):
            wl = []
            for j, w in enumerate(st['wires']):
                wid = f'{pre}{st["id"]}-{j + 1}'
                wl.append(f'<li data-w="{wid}"><label><input type="checkbox" data-k="{wid}"><span class="badge" style="border-color:{COL[w["col"]]}">{j + 1}</span>'
                          f'<span class="sw" style="background:{COL[w["col"]]}"></span><span class="wt"><b>{esc(COLNAME[w["col"]].capitalize())} wire</b> ({esc(w["kind"])}):<br>'
                          f'{w["ta"]} <span class="arr">→</span> {w["tb"]}</span></label></li>')
            todo = ''.join(f'<li>{t}</li>' for t in st.get('todo', []))
            fixes = ''.join(f'<dt>{esc(a)}</dt><dd>{b}</dd>' for a, b in st['fix'])
            need = ''.join(f'<span class="chip">{esc(n)}</span>' for n in st['need'])
            warn = f'<div class="warn">⚠️ {st["warn"]}</div>' if st.get('warn') else ''
            out.append(f'''
<section class="bbstep only-{lay}" id="{sid}{st['id']}">
  <div class="bbhead"><span class="num">{i + 1}</span><h2>{esc(st['title'])}</h2><span class="time">⏱ {st['time']}</span></div>
  <p>{st['intro']}</p>
  <div class="need"><b>You need:</b> {need}</div>
  {warn}
  <div class="pic">{draw_step(S, i)}</div>
  {'<p class="mut" style="margin:4px 0 10px">New wires are bright and numbered; earlier ones are faded. Hover a wire in the list to find it in the picture.</p>' if st['wires'] else ''}
  {f'<ol class="todo">{todo}</ol>' if todo else ''}
  {f'<h3>Connect</h3><ul class="wires">{"".join(wl)}</ul>' if wl else ''}
  <div class="test"><b>✅ Test it:</b> {st['test']}</div>
  {f'<details class="dbg"><summary>Not reading 3.3 V on the rails? Check in this order</summary><ol>' + ''.join(f'<li><b>{a}{"" if a.endswith("?") else "."}</b> {b}</li>' for a, b in st['debug']) + '</ol></details>' if st.get('debug') else ''}
  <details><summary>Not working?</summary><dl>{fixes}</dl></details>
</section>''')
    LAY = 'beside'
    return ''.join(out), ''.join(navs), totals

def page():
    steps_html, navs, totals = sections()
    return f'''<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Breadboard test · Ceiling Clock</title>
<link rel="stylesheet" href="style.css?v=20261030w">
<style>
.bbsvg{{width:100%;height:auto;display:block;border:1px solid var(--line);border-radius:12px;background:#fbfaf6}}
.toc{{display:flex;flex-wrap:wrap;gap:6px;margin:14px 0 6px}}
.toc a{{display:flex;align-items:center;gap:6px;border:1px solid var(--line);border-radius:999px;padding:4px 10px 4px 4px;text-decoration:none;color:inherit;font-size:.88rem;background:var(--paper)}}
.toc a span{{display:inline-grid;place-items:center;width:22px;height:22px;border-radius:50%;background:#e8743b;color:#fff;font-weight:700;font-size:.8rem}}
.toc a.done span{{background:#2e9e44}}
.progress{{position:sticky;top:0;z-index:5;background:var(--bg,#fff);padding:8px 0;border-bottom:1px solid var(--line)}}
.progress .bar{{height:8px;border-radius:99px;background:#e9e6dd;overflow:hidden}}.progress .bar i{{display:block;height:100%;width:0;background:#2e9e44;transition:width .3s}}
.progress small{{color:var(--mut)}}
.bbstep{{border:1px solid var(--line);border-radius:16px;padding:18px 18px 10px;margin:22px 0;background:var(--paper)}}
.bbhead{{display:flex;align-items:center;gap:12px}}.bbhead h2{{margin:0;flex:1}}
.bbhead .num{{display:grid;place-items:center;width:38px;height:38px;border-radius:50%;background:#e8743b;color:#fff;font-weight:800;font-size:1.1rem}}
.bbstep.done .bbhead .num{{background:#2e9e44}}
.time{{color:var(--mut);font-size:.9rem}}
.chip{{display:inline-block;background:#eef2f7;border:1px solid #d8e0ea;border-radius:999px;padding:2px 9px;margin:2px 3px;font-size:.85rem}}
.need{{margin:8px 0 10px}}
.pic{{margin:8px 0}}
.wires{{list-style:none;padding:0;margin:6px 0 10px;display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:6px}}
.wires li label{{display:flex;align-items:flex-start;gap:8px;border:1px solid var(--line);border-radius:10px;padding:8px;cursor:pointer;background:#fff}}
.wires li.hl label{{border-color:#e8743b;box-shadow:0 0 0 2px #f6c3a9}}
.wires input{{margin-top:3px;width:18px;height:18px;accent-color:#2e9e44}}
.wires li input:checked ~ .wt{{color:#6b7280;text-decoration:line-through}}
.badge{{display:inline-grid;place-items:center;min-width:22px;height:22px;border-radius:50%;border:2.5px solid;font-weight:800;font-size:.8rem}}
.sw{{width:10px;height:22px;border-radius:3px;flex:none}}
.arr{{color:#e8743b;font-weight:800}}
.todo li{{margin:4px 0}}
.test{{background:#eaf7ec;border:1px solid #bfe5c6;border-radius:10px;padding:10px 12px;margin:10px 0}}
.warn{{background:#fff3e0;border:1px solid #ffd59a;border-radius:10px;padding:10px 12px;margin:10px 0}}
.dbg ol{{margin:8px 0;padding-left:22px}}.dbg li{{margin:6px 0}}
details{{margin:6px 0 8px}}summary{{cursor:pointer;font-weight:700;color:#b5541f}}dl{{margin:8px 0}}dt{{font-weight:700;margin-top:6px}}dd{{margin:2px 0 0 0;color:#444}}
.wire{{cursor:pointer}}.bbsvg .wire.hl path:last-of-type{{stroke-width:6}}
.legend{{display:flex;flex-wrap:wrap;gap:14px;margin:8px 0}}.legend span{{display:flex;align-items:center;gap:6px}}.legend i{{width:22px;height:6px;border-radius:3px;display:inline-block}}
.only-beside,.only-plug,.only-one{{display:none}}
body.lay-beside .only-beside,body.lay-plug .only-plug,body.lay-one .only-one{{display:block}}
body.lay-beside .toc.only-beside,body.lay-plug .toc.only-plug,body.lay-one .toc.only-one{{display:flex}}
.layout{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin:16px 0 8px}}@media(max-width:700px){{.layout{{grid-template-columns:1fr}}}}
.layout button{{text-align:left;border:2px solid var(--line);border-radius:14px;padding:10px 12px;background:var(--paper);cursor:pointer;font:inherit;color:inherit}}
.layout button b{{display:block;font-size:1.02rem;margin-bottom:2px}}.layout button small{{color:var(--mut)}}
.layout button[aria-pressed=true]{{border-color:#e8743b;box-shadow:0 0 0 3px #f6c3a9;background:#fff8f3}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}@media(max-width:800px){{.two{{grid-template-columns:1fr}}}}
</style>
</head><body class="lay-plug">
<header class="site"><div class="in">
<a class="brand" href="index.html"><span class="dot"></span>Ceiling Clock</a>
<nav><a href="index.html">3D model</a><a href="assembly.html">Assembly</a><a href="wiring.html">Wiring</a><a href="breadboard.html" class="on">Breadboard test</a><a href="parts.html">Parts</a><a href="demo/">Live demo</a><a href="firmware.html">Firmware &amp; use</a><a href="https://github.com/ScottYates/ceilingclock">GitHub</a></nav>
</div></header>
<main>
<h1>Breadboard test</h1>
<p class="lead">Wire the clock's electronics up on a breadboard and check every part works, before you solder anything or print the case. You add one part at a time and test it, so if something doesn't work you know exactly where to look. No soldering is needed except for the parts that only come with solder pads (the USB-C breakout, the LED and the ring). Allow an evening.</p>

<h2>Where does the ESP32 go?</h2>
<p>Pick one; the pictures and wire lists below change to match. Your ticks are kept separately for each.</p>
<div class="layout" role="group" aria-label="Breadboard layout">
<button type="button" data-lay="plug" aria-pressed="false"><b>Plugged in across two breadboards</b><small>The ESP32 sits on the boards. Most wires are short hops from the hole beside a pin, and nothing dangles. Needs two full-size breadboards.</small></button>
<button type="button" data-lay="one" aria-pressed="false"><b>Plugged into one breadboard</b><small>The ESP32 plugs into the left end of one full-size board and everything else goes to its right. Each pin on one side has just one free hole, and the clock module (DS3231) can't connect, so you test it later.</small></button>
<button type="button" data-lay="beside" aria-pressed="false"><b>Beside one breadboard</b><small>The ESP32 stays loose next to the board and every pin is reached with a female jumper. Needs only one breadboard, but more wires and they can pull off.</small></button>
</div>
<div class="progress"><div class="bar"><i id="pbar"></i></div><small id="ptext">0 wires connected</small></div>
{navs}

<h2>Before you start</h2>
<div class="two">
<div><h3>How a breadboard works</h3>{svg_basics()}</div>
<div><h3>Three kinds of jumper wire</h3>{svg_jumpers()}
<p class="only-plug only-one">With the ESP32 plugged in, a wire to one of its pins goes into a free hole <b>in the same row of five</b> as that pin, so those ends are male. Modules have pins, so their end of a wire is female.</p>
<p class="only-beside">The ESP32 sits <b>next to</b> the breadboard and you connect to its pins with the <b>female</b> end of a jumper. Most modules have pins too, so a female–female jumper goes straight from the ESP32 to the module.</p></div>
</div>
<h3>Wire colours used here</h3>
<div class="legend"><span><i style="background:{COL['3v3']}"></i>3.3 V</span><span><i style="background:{COL['5v']}"></i>5 V</span><span><i style="background:{COL['gnd']}"></i>ground (GND)</span><span><i style="background:linear-gradient(90deg,{COL['yellow']},{COL['green']},{COL['blue']},{COL['purple']})"></i>signals</span></div>
<p>Your jumpers can be any colour, but sticking to red for 5 V, orange (or another one colour) for 3.3 V and black for ground makes mistakes easy to spot.</p>
<div class="warn">⚠️ <b>Golden rules.</b> Unplug the USB cable (and later the 5 V adapter) every time you change wires. Keep the ESP32 on your computer's USB the whole time and <b>never</b> connect the 5 V adapter to its <b>5V</b> pin. Make sure the two ground rails stay joined.</div>
<p>You'll also want the two small 6 × 6 mm push buttons from your tactile switch kit; the 16 mm panel buttons need soldering, so they go in during final assembly.</p>
{steps_html}

<section class="bbstep" id="s-optics">
  <div class="bbhead"><span class="num">★</span><h2>Bonus: see it on the ceiling</h2><span class="time">⏱ 15 min</span></div>
  <p>Once the LCD has its window cut (<a href="assembly.html#step-5">assembly step 5</a>), you can try the projector by hand in a dark room before printing anything.</p>
  <div class="two"><div>{svg_optics()}</div><div><ol class="todo">
  <li>Point the LED up, sitting on its metal.</li>
  <li>Hold a piece of baking paper about 10 mm above it, and the LCD, glass up, about 30 mm above it.</li>
  <li>Hold the lens about 106 mm above the LCD, look at the ceiling, and move the lens up and down until the digits are sharp. That's what the focus ring does in the finished clock.</li>
  <li>Use <b>Mirror left/right</b> and <b>Flip projection</b> on the clock's page until it reads right from where you lie. In the clock the mirror adds one more flip, so expect to change Mirror left/right once it's built.</li></ol></div></div>
</section>

<h2>Done?</h2>
<p>When every step passes, move the same connections onto the perfboard (<a href="assembly.html#step-4">assembly step 4</a>). Two things change in the finished clock: the 16 mm buttons replace the small ones, and the 5 V supply also feeds the ESP32's 5V pin, so from then on leave the computer unplugged and update the firmware over Wi-Fi. The full pin list is on the <a href="wiring.html">wiring page</a>.</p>
</main>
<footer>Ceiling Clock · pictures drawn from <a href="https://github.com/ScottYates/ceilingclock/blob/main/firmware/src/pins.h">pins.h</a> by <code>hardware/make_breadboard_guide.py</code></footer>
<script>
(() => {{
  const KEY = 'ceilingclock-breadboard';
  let saved = {{}};
  try {{ saved = JSON.parse(localStorage.getItem(KEY) || '{{}}'); }} catch (e) {{}}
  const LKEY = 'ceilingclock-breadboard-layout';
  let lay = 'plug';
  try {{ const v = localStorage.getItem(LKEY); if (v === 'plug' || v === 'one' || v === 'beside') lay = v; }} catch (e) {{}}
  const allBoxes = [...document.querySelectorAll('.wires input')];
  function update() {{
    const boxes = allBoxes.filter(b => b.closest('.only-' + lay));
    const done = boxes.filter(b => b.checked).length;
    document.getElementById('pbar').style.width = (100 * done / boxes.length) + '%';
    document.getElementById('ptext').textContent = done + ' of ' + boxes.length + ' wires connected';
    const toc = [...document.querySelectorAll('.toc.only-' + lay + ' a')];
    document.querySelectorAll('.bbstep.only-' + lay).forEach((s, i) => {{
      const bs = [...s.querySelectorAll('.wires input')];
      const ok = bs.length > 0 && bs.every(b => b.checked);
      s.classList.toggle('done', ok);
      if (toc[i]) toc[i].classList.toggle('done', ok);
    }});
  }}
  function setLay(v) {{
    lay = v;
    ['plug', 'one', 'beside'].forEach(k => document.body.classList.toggle('lay-' + k, v === k));
    document.querySelectorAll('.layout button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.lay === v)));
    try {{ localStorage.setItem(LKEY, v); }} catch (e) {{}}
    update();
  }}
  document.querySelectorAll('.layout button').forEach(b => b.onclick = () => setLay(b.dataset.lay));
  allBoxes.forEach(b => {{
    b.checked = !!saved[b.dataset.k];
    b.onchange = () => {{ saved[b.dataset.k] = b.checked; try {{ localStorage.setItem(KEY, JSON.stringify(saved)); }} catch (e) {{}} update(); }};
  }});
  // hover a wire in the list or the picture to highlight both
  const hl = (id, on) => document.querySelectorAll('[data-w="' + id + '"]').forEach(e => e.classList.toggle('hl', on));
  document.querySelectorAll('[data-w]').forEach(e => {{
    e.addEventListener('mouseenter', () => hl(e.dataset.w, true));
    e.addEventListener('mouseleave', () => hl(e.dataset.w, false));
  }});
  setLay(lay);
}})();
</script>
</body></html>'''

if __name__ == '__main__':
    out = os.path.join(HERE, '..', 'docs', 'breadboard.html')
    open(out, 'w').write(page())
    print('wrote', os.path.relpath(out))
