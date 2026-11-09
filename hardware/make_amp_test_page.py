# Usage: python3 hardware/make_amp_test_page.py
# Writes docs/amp-test.html: an illustrated page for checking the MAX98357A amplifier with a multimeter and an
# oscilloscope (written around the FNIRSI 2C53T scope-multimeter, but any meter and scope work the same way).
import os, html, math, random

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'docs', 'amp-test.html')

def esc(s): return html.escape(str(s), quote=True)
class Svg:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" class="fig" font-family="system-ui,-apple-system,Segoe UI,sans-serif">',
                  f'<rect width="{w}" height="{h}" fill="#fbfaf6"/>']
    def add(self, s): self.o.append(s)
    def text(self, x, y, s, size=12, fill='#222', anchor='start', weight=400, extra=''):
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" {extra}>{esc(s)}</text>')
    def rect(self, x, y, w, h, fill, stroke='none', rx=4, sw=1, extra=''):
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')
    def circle(self, x, y, r, fill, stroke='none', sw=1):
        self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    def line(self, x1, y1, x2, y2, col, w=1.5, extra=''):
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{col}" stroke-width="{w}" stroke-linecap="round" {extra}/>')
    def path(self, d, col, w=2, fill='none', extra=''):
        self.add(f'<path d="{d}" fill="{fill}" stroke="{col}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round" {extra}/>')
    def done(self):
        return '\n'.join(self.o + ['</svg>'])

PCB, PCBE, PAD, JOINT = '#2f5fae', '#1f437d', '#e3c26a', '#c3c8cf'
PINS = ['LRC', 'BCLK', 'DIN', 'GAIN', 'SD', 'GND', 'VIN']
ORANGE, RED, GREEN, BLUE = '#e8743b', '#d32f2f', '#2e9e44', '#2b5fd9'

def amp_board(s, x0, y0, scale=1.0, hilite=()):
    """Top view of the MAX98357A breakout: header joints along the bottom, screw terminal at the top.
    Returns {label: (x, y)} of each header joint and the two terminal screws."""
    W, H = 250 * scale, 180 * scale
    s.rect(x0, y0, W, H, PCB, PCBE, 10 * scale, 1.5)
    s.rect(x0 + W / 2 - 22 * scale, y0 + H / 2 - 18 * scale, 44 * scale, 36 * scale, '#1d1d1d', rx=3)
    s.text(x0 + W / 2, y0 + H / 2 + 34 * scale, 'MAX98357A', 10 * scale, '#dce6f7', 'middle', 700)
    pts = {}
    for i, nm in enumerate(PINS):
        x = x0 + 28 * scale + i * 32.5 * scale
        y = y0 + H - 22 * scale
        on = nm in hilite
        s.circle(x, y, 9 * scale, PAD, ORANGE if on else '#a8862e', 3 if on else 1)
        s.circle(x, y, 5 * scale, JOINT, '#8e949c', 0.8)
        s.text(x, y - 16 * scale, nm, 10 * scale, '#ffd27a' if on else '#ffffff', 'middle', 800)
        pts[nm] = (x, y)
    # screw terminal
    tx0, ty0 = x0 + W / 2 - 50 * scale, y0 - 10 * scale
    s.rect(tx0, ty0, 100 * scale, 46 * scale, '#2f9ad1', '#1d6f99', 5, 1.5)
    for k, (lab, dx) in enumerate((('+', 25), ('−', 75))):
        cx, cy = tx0 + dx * scale, ty0 + 22 * scale
        on = lab in hilite
        s.circle(cx, cy, 13 * scale, '#d7dbe0', ORANGE if on else '#8a9099', 3 if on else 1.2)
        s.line(cx - 8 * scale, cy, cx + 8 * scale, cy, '#555', 2.5)
        s.text(cx, ty0 + 66 * scale, lab, 16 * scale, '#ffffff', 'middle', 800)
        pts[lab] = (cx, cy)
    return pts

def meter_probe(s, tip, colour, label, ang=-60, length=150):
    """A multimeter test lead: pointed metal tip at `tip`, handle running off at angle `ang`."""
    a = math.radians(ang)
    dx, dy = math.cos(a), math.sin(a)
    x1, y1 = tip[0] + 18 * dx, tip[1] + 18 * dy
    x2, y2 = tip[0] + 90 * dx, tip[1] + 90 * dy
    x3, y3 = tip[0] + length * dx, tip[1] + length * dy
    s.line(tip[0], tip[1], x1, y1, '#9aa0a6', 3)
    s.line(x1, y1, x2, y2, colour, 11)
    s.line(x2, y2, x3, y3, colour, 4)
    s.text(x3 + 6 * (1 if dx >= 0 else -1), y3 + 4, label, 12, colour, 'start' if dx >= 0 else 'end', 800)

def scope_probe(s, tip, ang=-55, length=170, label='scope probe (CH1)'):
    a = math.radians(ang)
    dx, dy = math.cos(a), math.sin(a)
    p = lambda d: (tip[0] + d * dx, tip[1] + d * dy)
    s.line(*tip, *p(14), '#9aa0a6', 2.5)                 # sharp tip
    s.line(*p(14), *p(30), '#cfd3d8', 9)                  # hook sleeve
    s.line(*p(30), *p(105), '#2d2f33', 13)                # body
    s.line(*p(105), *p(length), '#444', 4)                # cable
    x, y = p(length)
    s.text(x + 6, y + 4, label, 12, '#2d2f33', 'start', 800)
    return p(70)                                          # where the ground lead leaves the body

def ground_clip(s, frm, to, label='ground clip'):
    mx, my = (frm[0] + to[0]) / 2, max(frm[1], to[1]) + 50
    s.path(f'M{frm[0]:.1f},{frm[1]:.1f} Q{mx:.1f},{my:.1f} {to[0]:.1f},{to[1] - 14:.1f}', '#111', 2.5)
    s.rect(to[0] - 6, to[1] - 22, 12, 18, '#111', rx=3)                       # crocodile clip
    s.path(f'M{to[0] - 6},{to[1] - 4} l3,6 l3,-6 l3,6 l3,-6', '#9aa0a6', 1.5)
    s.text(to[0] + 12, to[1] - 10, label, 11.5, '#111', 'start', 800)

def callout(s, x, y, tx, ty, lines, anchor='start', colour='#333'):
    s.line(x, y, tx, ty, ORANGE, 1.4)
    s.circle(x, y, 3, ORANGE)
    for i, ln in enumerate(lines):
        s.text(tx + (5 if anchor == 'start' else -5), ty + 4 + i * 15, ln, 11.5, colour, anchor, 800 if i == 0 else 400)

def screen(s, x, y, w, h, title, wave, colour=GREEN, note=''):
    """A small scope screen with a sketched trace."""
    s.rect(x, y, w, h, '#101418', '#2a2f36', 6, 1.5)
    for i in range(1, 4): s.line(x + i * w / 4, y + 4, x + i * w / 4, y + h - 4, '#25303a', 1)
    for i in range(1, 3): s.line(x + 4, y + i * h / 3, x + w - 4, y + i * h / 3, '#25303a', 1)
    lo, hi = y + h * 0.78, y + h * 0.22
    pts = []
    random.seed(7)
    if wave == 'square':
        n = 6
        for k in range(n):
            xa, xb = x + 8 + k * (w - 16) / n, x + 8 + (k + 0.5) * (w - 16) / n
            pts += [(xa, lo), (xa, hi), (xb, hi), (xb, lo)]
        pts.append((x + w - 8, lo))
    elif wave == 'fast':
        n = 22
        for k in range(n):
            xa, xb = x + 8 + k * (w - 16) / n, x + 8 + (k + 0.5) * (w - 16) / n
            pts += [(xa, lo), (xa, hi), (xb, hi), (xb, lo)]
        pts.append((x + w - 8, lo))
    elif wave == 'data':
        n, lvl = 26, lo
        for k in range(n + 1):
            xa = x + 8 + k * (w - 16) / n
            pts.append((xa, lvl))
            lvl = hi if random.random() < 0.5 else lo
            pts.append((xa, lvl))
    elif wave == 'pwm':
        n = 18
        for k in range(n):
            duty = 0.5 + 0.4 * math.sin(k / n * 2 * math.pi)
            xa = x + 8 + k * (w - 16) / n
            xb = xa + duty * (w - 16) / n
            pts += [(xa, lo), (xa, hi), (xb, hi), (xb, lo)]
        pts.append((x + w - 8, lo))
    else:  # flat
        pts = [(x + 8, lo), (x + w - 8, lo)]
    s.path('M' + ' L'.join(f'{a:.1f},{b:.1f}' for a, b in pts), colour, 2)
    s.text(x + w / 2, y + h + 17, title, 12, '#222', 'middle', 800)
    if note: s.text(x + w / 2, y + h + 32, note, 11, '#6b7280', 'middle')

# ------------------------------------------------------------------ figures
def fig_pieces():
    s = Svg(960, 420)
    s.text(20, 30, 'The pieces', 16, '#222', 'start', 800)
    # scope probe, laid out horizontally with its parts named
    y = 110
    s.rect(30, y - 16, 34, 32, '#c9ccd1', '#8a9099', 5, 1.2)     # BNC plug
    s.rect(64, y - 9, 18, 18, '#9aa0a6', rx=3)
    s.path(f'M82,{y} C150,{y - 40} 190,{y + 40} 250,{y}', '#444', 4)
    s.rect(250, y - 11, 160, 22, '#2d2f33', rx=10)               # probe body
    s.rect(300, y - 15, 26, 8, '#e8e1cf', rx=2)                  # x1/x10 switch
    s.rect(410, y - 6, 34, 12, '#cfd3d8', rx=4)                  # hook sleeve
    s.line(444, y, 470, y, '#9aa0a6', 2.5)                       # tip
    s.path(f'M330,{y + 11} C330,{y + 60} 400,{y + 70} 430,{y + 70}', '#111', 2.5)   # ground lead
    s.rect(430, y + 61, 26, 18, '#111', rx=3)
    callout(s, 47, y - 16, 40, 56, ['BNC plug', 'push on, twist to lock,', 'into the socket marked CH1'])
    callout(s, 313, y - 15, 280, 56, ['×1 / ×10 switch', 'set ×10, and set the', "channel's probe to ×10"])
    callout(s, 427, y - 6, 470, 56, ['hook tip', 'pull the sleeve back for', 'the sharp point underneath'])
    callout(s, 456, y + 70, 490, y + 66, ['ground clip', 'always on GND'])
    # meter leads
    y2 = 300
    for i, (col, plug, lab) in enumerate(((RED, 'VΩ', 'red lead'), ('#222', 'COM', 'black lead'))):
        yy = y2 + i * 46
        s.rect(30, yy - 7, 30, 14, col, rx=3); s.line(60, yy, 230, yy, col, 4)
        s.rect(230, yy - 7, 80, 14, col, rx=6); s.line(310, yy, 336, yy, '#9aa0a6', 3)
        s.text(30, yy - 13, f'{lab}: banana plug into the multimeter socket {plug}', 11.5, col, 'start', 800)
    s.text(30, y2 + 82, 'Never the 10A or mA socket for any of these checks.', 11.5, RED, 'start', 800)
    # amp board
    pts = amp_board(s, 640, 150, 1.0)
    s.text(765, 120, 'speaker terminal', 11.5, '#333', 'middle', 700)
    s.text(765, 362, 'header joints: probe these silver bumps on top', 11.5, '#333', 'middle', 700)
    s.text(765, 378, '(the jumpers stay plugged in underneath)', 11, '#6b7280', 'middle')
    return s.done()

def fig_meter():
    s = Svg(960, 470)
    s.text(20, 30, 'Check 1: power, with the multimeter', 16, '#222', 'start', 800)
    s.text(20, 52, 'Multimeter mode, DC volts. Black on GND for every reading; move only the red one.', 12, '#555')
    for k, (pin, read, ok) in enumerate((('VIN', '5.2 V', 'about 5 V: powered'), ('SD', '0.6 V', 'about 0.5–0.8 V: switched on'))):
        x0 = 40 + k * 470
        pts = amp_board(s, x0 + 60, 150, 1.0, hilite=('GND', pin))
        meter_probe(s, pts['GND'], '#222', 'black: GND', ang=115, length=105)
        meter_probe(s, pts[pin], RED, f'red: {pin}', ang=65, length=105)
        s.rect(x0 + 250, 76, 120, 52, '#d8e3c8', '#7a8a62', 8, 1.5)
        s.text(x0 + 310, 112, read, 24, '#1f2a14', 'middle', 800, extra='font-family="ui-monospace,monospace"')
        s.text(x0 + 310, 146, ok, 11.5, GREEN, 'middle', 800)
    s.text(40, 458, 'VIN reads 0: the amp has no power. SD reads 0: the amp is switched off (look for solder joining SD to GND, they sit side by side).', 11.5, RED, 'start', 700)
    return s.done()

def fig_scope():
    s = Svg(960, 520)
    s.text(20, 30, 'Check 2: the signals, with the oscilloscope (sound playing)', 16, '#222', 'start', 800)
    s.text(20, 52, 'Ground clip on a GND point and left there. Touch the sharp probe tip to one joint at a time, then press Auto.', 12, '#555')
    pts = amp_board(s, 110, 120, 1.0, hilite=('LRC', 'BCLK', 'DIN'))
    # ground point: a spare jumper pushed into the bottom − rail
    s.rect(40, 360, 330, 40, '#f3f1ea', '#cfcabc', 4, 1)
    s.line(48, 380, 362, 380, BLUE, 1)
    for i in range(18): s.rect(52 + i * 17, 376, 5, 5, '#8a8577', rx=1)
    s.text(48, 414, 'bottom − rail (GND)', 11, BLUE, 'start', 700)
    s.rect(78, 344, 7, 30, '#222', rx=1.5); s.line(81, 344, 81, 334, '#9aa0a6', 2)   # spare jumper standing up
    s.text(48, 432, 'the clip grips a spare jumper pushed into the − rail', 11, '#333')
    body = scope_probe(s, pts['DIN'], ang=-58, length=165)
    ground_clip(s, body, (81, 334))
    # what to expect
    sx = 430
    screen(s, sx, 90, 150, 90, 'LRC', 'square', note='0–3.3 V square, ≈44 kHz')
    screen(s, sx + 180, 90, 150, 90, 'BCLK', 'fast', note='0–3.3 V square, ≈1.4–2.8 MHz')
    screen(s, sx + 360, 90, 150, 90, 'DIN, sound playing', 'data', note='busy 0–3.3 V pulses')
    screen(s, sx + 90, 270, 150, 90, 'DIN, nothing playing', 'flat', colour='#8aa0b4', note='flat at 0 V is normal')
    screen(s, sx + 270, 270, 150, 90, 'Any pin flat while playing', 'flat', colour=RED, note='that signal is not arriving')
    s.text(sx, 420, 'Tip: probe LRC on CH1 and DIN on CH2 to see both at once.', 11.5, '#333', 'start', 700)
    s.text(sx, 438, 'DIN should change in step with LRC.', 11.5, '#6b7280')
    return s.done()

def fig_output():
    s = Svg(960, 400)
    s.text(20, 30, "Check 3: the amp's output (sound playing)", 16, '#222', 'start', 800)
    s.text(20, 52, 'Ground clip stays on GND. Touch only the probe tip to the + speaker screw.', 12, '#555')
    pts = amp_board(s, 190, 150, 1.0, hilite=('+',))
    body = scope_probe(s, pts['+'], ang=-40, length=160)
    s.rect(40, 330, 330, 40, '#f3f1ea', '#cfcabc', 4, 1)
    s.line(48, 350, 362, 350, BLUE, 1)
    for i in range(18): s.rect(52 + i * 17, 346, 5, 5, '#8a8577', rx=1)
    s.rect(60, 314, 7, 30, '#222', rx=1.5); s.line(63, 314, 63, 304, '#9aa0a6', 2)
    ground_clip(s, body, (63, 304))
    screen(s, 490, 100, 180, 100, 'Working: fast 5 V pulses', 'pwm', note='their width follows the sound')
    screen(s, 720, 100, 180, 100, 'Flat line', 'flat', colour=RED, note='the amp is not running')
    # do-not panel
    s.rect(490, 260, 420, 110, '#fff3e0', '#ffd59a', 10, 1.2)
    s.text(510, 288, '✗ Never put the ground clip on a speaker screw', 13, RED, 'start', 800)
    s.text(510, 310, 'The amp drives both speaker wires. The scope ground is the', 11.5, '#333')
    s.text(510, 326, 'same as the circuit ground (through USB), so clipping it to', 11.5, '#333')
    s.text(510, 342, 'either screw shorts that output and can damage the amp.', 11.5, '#333')
    return s.done()


def fig_scope_panel():
    """The FNIRSI 2C53T's front, drawn from a photo: buttons, the four banana sockets, and the three BNCs on top."""
    s = Svg(960, 660)
    s.text(20, 30, 'Your 2C53T: where each lead goes and which buttons you use', 16, '#222', 'start', 800)
    X0, Y0, BW, BH = 330, 150, 300, 480
    # three BNC sockets on the top edge
    for i, x in enumerate((X0 + 70, X0 + 150, X0 + 230)):
        s.rect(x - 16, Y0 - 34, 32, 36, '#b9bec6', '#7d838c', 4, 1.2)
        s.rect(x - 10, Y0 - 46, 20, 14, '#d9dde2', '#7d838c', 3, 1)
        s.circle(x, Y0 - 39, 3, '#555')
    s.rect(X0, Y0, BW, BH, '#1c1f24', '#3a9ad9', 28, 4)
    s.rect(X0 + 22, Y0 + 20, BW - 44, 170, '#2a2e33', '#111', 6, 1.5)
    s.text(X0 + BW - 30, Y0 + 40, '2C53T', 12, '#e6e6e6', 'end', 800)
    def btn(x, y, w, label, hi=None, col='#2b2f35', tc='#f2f2f2', fs=10.5):
        s.rect(x, y, w, 26, col, ORANGE if hi else '#444', 7, 3 if hi else 1)
        s.text(x + w / 2, y + 17, label, fs, tc, 'middle', 800)
    row = Y0 + 206
    for i, lab in enumerate(('MOVE', 'SELECT', 'TRIGGER', 'PRM')):
        btn(X0 + 18 + i * 68, row, 58, lab, fs=9.5)
    btn(X0 + 18, row + 40, 54, 'CH1')
    btn(X0 + BW - 72, row + 40, 54, 'CH2')
    btn(X0 + 18, row + 80, 54, 'AUTO', hi=True)
    btn(X0 + BW - 72, row + 80, 54, 'SAVE')
    s.circle(X0 + 45, row + 133, 14, '#2b2f35', '#e0573a', 2); s.text(X0 + 45, row + 138, '⏻', 13, '#e0573a', 'middle')
    s.rect(X0 + BW - 74, row + 120, 58, 26, '#2b2f35', ORANGE, 13, 3); s.text(X0 + BW - 45, row + 137, 'MENU', 10.5, '#f0a35a', 'middle', 800)
    # navigation pad
    cx, cy = X0 + BW / 2, row + 93
    s.rect(cx - 52, cy - 52, 104, 104, '#22262b', '#3a9ad9', 18, 3)
    s.rect(cx - 16, cy - 13, 32, 26, '#3a9ad9', rx=6); s.text(cx, cy + 5, '▶', 12, '#fff', 'middle')
    for dx, dy, ch in ((0, -36, '▲'), (0, 40, '▼'), (-36, 4, '◀'), (36, 4, '▶')):
        s.text(cx + dx, cy + dy, ch, 13, '#eee', 'middle')
    # banana sockets along the bottom
    jy = Y0 + BH - 52
    jacks = [('10A', X0 + 48), ('mA', X0 + 116), ('COM', X0 + 184), ('VΩ', X0 + 252)]
    pos = {}
    for lab, x in jacks:
        ring = '#3a9ad9' if lab != 'COM' else '#555'
        s.circle(x, jy, 20, '#111', '#333', 2); s.circle(x, jy, 11, ring); s.circle(x, jy, 5, '#000')
        s.text(x, jy + 38, lab, 13, '#eee', 'middle', 800)
        pos[lab] = (x, jy)
    s.add(f'<line x1="{X0 + 30}" y1="{jy + 46}" x2="{X0 + 140}" y2="{jy + 46}" stroke="{RED}" stroke-width="3"/>')
    # leads
    for lab, col, txt, ex in (('VΩ', RED, 'red lead → VΩ', 790), ('COM', '#111', 'black lead → COM', 760)):
        x, y = pos[lab]
        s.circle(x, y, 7, col)
        s.path(f'M{x},{y} C{x + 40},{y + 70} {ex - 80},{y + 60} {ex},{y - 10}', col, 5)
        s.text(ex + 8, y - 6 if lab == 'VΩ' else y + 14, txt, 13, col, 'start', 800)
    s.text(X0 + 84, jy + 64, 'never 10A or mA here', 11.5, RED, 'middle', 800)
    # probe into a top BNC
    bx = X0 + 70
    s.path(f'M{bx},{Y0 - 46} C{bx - 20},{Y0 - 80} {bx - 120},{Y0 - 60} {bx - 190},{Y0 - 40}', '#444', 4)
    s.rect(bx - 8, Y0 - 60, 16, 16, '#c9ccd1', '#8a9099', 3, 1)
    s.text(bx - 196, Y0 - 50, 'scope probe → the top socket', 13, '#222', 'end', 800)
    s.text(bx - 196, Y0 - 34, 'labelled CH1 (push, twist to lock)', 12, '#555', 'end')
    s.text(X0 + 260, Y0 - 100, 'three BNC sockets on top: CH1, CH2 and the generator output', 11.5, '#555', 'middle')
    # callouts for the buttons
    callout(s, X0 + 18, row + 93, 40, 400, ['AUTO', 'press once to find', 'and show the signal'], 'start')
    callout(s, X0 + BW - 16, row + 133, 700, 380, ['MENU', 'switch between oscilloscope', 'and multimeter'], 'start')
    callout(s, X0 + 45, row + 40 + 13, 40, 300, ['CH1', 'channel 1 settings, including', 'the probe ×1/×10 setting'], 'start')
    return s.done()

def page():
    style = open(os.path.join(HERE, '..', 'docs', 'breadboard.html')).read()
    ver = style[style.index('style.css?v='):].split('"')[0]
    return f'''<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Testing the amplifier · Ceiling Clock</title>
<link rel="stylesheet" href="{ver}">
<style>
.fig{{width:100%;height:auto;display:block;border:1px solid var(--line);border-radius:12px;margin:10px 0 6px}}
.card{{border:1px solid var(--line);border-radius:16px;padding:16px 18px;margin:20px 0;background:var(--paper)}}
.warn{{background:#fff3e0;border:1px solid #ffd59a;border-radius:10px;padding:10px 12px;margin:10px 0}}
.test{{background:#eaf7ec;border:1px solid #bfe5c6;border-radius:10px;padding:10px 12px;margin:10px 0}}
table{{border-collapse:collapse;width:100%;margin:8px 0}}td,th{{border:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}}th{{background:#f3f1ea}}
ol li{{margin:5px 0}}
</style>
</head><body>
<header class="site"><div class="in">
<a class="brand" href="index.html"><span class="dot"></span>Ceiling Clock</a>
<nav><a href="index.html">3D model</a><a href="assembly.html">Assembly</a><a href="wiring.html">Wiring</a><a href="breadboard.html" class="on">Breadboard test</a><a href="parts.html">Parts</a><a href="demo/">Live demo</a><a href="firmware.html">Firmware &amp; use</a><a href="https://github.com/ScottYates/ceilingclock">GitHub</a></nav>
</div></header>
<main>
<p><a href="breadboard.html#o-amp">← back to the breadboard test</a></p>
<h1>Testing the amplifier</h1>
<p class="lead">No sound from the speaker? Three checks, in order, find where it stops: power to the amp, the three signals from the ESP32, and the amp's output. Written for the FNIRSI 2C53T, which is a multimeter and an oscilloscope in one, but any meter and scope work the same way.</p>

<div class="card">
<h2>What's in the 2C53T box, and what you need here</h2>
<ul>
<li><b>Oscilloscope probes</b> (P6100, ×1/×10): one or two, depending on the bundle. Each has a BNC plug, a ×1/×10 switch on the handle, a hook tip and a ground clip. You need one.</li>
<li><b>Multimeter test leads</b>, red and black. You need both.</li>
<li><b>BNC-to-crocodile-clip cable</b>: that one is for the signal generator output. Leave it in the case.</li>
</ul>
<p>The three BNC sockets on top are the scope's <b>CH1</b> and <b>CH2</b> and the signal generator output; the probe goes in the one labelled <b>CH1</b>. The four banana sockets along the bottom are for the multimeter: <b>10A</b>, <b>mA</b>, <b>COM</b> and <b>VΩ</b>. Use <b>MENU</b> to switch between the oscilloscope and the multimeter.</p>
{fig_scope_panel()}
</div>

<div class="card">
<h2>Before you start</h2>
<ol>
<li>Wire the amp as in the <a href="breadboard.html#o-amp">amplifier step</a>, speaker connected, 5 V adapter and USB plugged in.</li>
<li>On the clock's page, under <b>Sounds</b>, play a sound to have something to measure. A long, steady sound is easiest to read (the built-in beep is mostly silence).</li>
<li>Every check measures from the amp's <b>GND</b>. The amp's pins are covered by the jumpers underneath, so probe the <b>silver solder joints on top</b> of the board.</li>
</ol>
{fig_pieces()}
</div>

<div class="card">
<h2>Check 1: power</h2>
<ol>
<li>Plug the <b>black</b> lead into <b>COM</b> and the <b>red</b> lead into <b>VΩ</b>, the right-hand socket (not 10A or mA). Switch the 2C53T to its multimeter.</li>
<li>The meter picks AC or DC volts by itself, but its automatic mode doesn't work below about 0.7 V, and SD sits right around there. If SD reads blank or 0, step the meter to <b>DC volts</b> by hand: short presses of the function key cycle through AC/DC, diode/continuity and so on.</li>
<li>Black tip on the <b>GND</b> joint. Red tip on <b>VIN</b>, then on <b>SD</b>.</li>
</ol>
{fig_meter()}
<table><tr><th>Red on</th><th>Expect</th><th>If not</th></tr>
<tr><td>VIN</td><td>about 5 V</td><td>0 V: check the 5 V adapter, the bottom rails and the amp's VIN and GND jumpers.</td></tr>
<tr><td>SD</td><td>about 0.5–0.8 V</td><td>0 V: the amp is held off. Look for solder joining SD to its neighbour GND.</td></tr></table>
</div>

<div class="card">
<h2>Check 2: the signals from the ESP32</h2>
<ol>
<li>Push the probe's BNC plug into <b>CH1</b> and twist it to lock. Set the switch on the probe's handle to <b>×10</b>, and set CH1's probe setting on the scope to <b>×10</b> too: the manual says both must be on the same setting, or the voltages read 10 times wrong.</li>
<li>Push a spare jumper into the <b>bottom − rail</b> and fix the <b>ground clip</b> on its metal end. Leave it there.</li>
<li>Switch the 2C53T to the oscilloscope. Pull the hook sleeve back and touch the <b>sharp tip</b> to the <b>LRC</b> joint, then press <b>AUTO</b> once. Repeat for <b>BCLK</b> and <b>DIN</b>.</li>
<li>Using both channels? Put both probes' ground clips on the same GND point. The manual forbids connecting the two ground clips to different points.</li>
</ol>
{fig_scope()}
<table><tr><th>Pin</th><th>Healthy, with sound playing</th><th>If it's flat</th></tr>
<tr><td>LRC</td><td>Square wave 0–3.3 V, about 44 kHz (16 kHz for the built-in beep)</td><td>The LRC jumper or hole a9 is not connected to ESP32 pin 16.</td></tr>
<tr><td>BCLK</td><td>Square wave 0–3.3 V, about 1.4–2.8 MHz</td><td>The BCLK jumper or hole a8 is not connected to pin 15.</td></tr>
<tr><td>DIN</td><td>Busy, ever-changing pulses 0–3.3 V</td><td>The DIN jumper or hole a10 is not connected to pin 17, or nothing is playing.</td></tr></table>
<div class="test">All three look right but there's still no sound? Go to check 3.</div>
</div>

<div class="card">
<h2>Check 3: the amp's output</h2>
<ol>
<li>Keep the ground clip on the − rail.</li>
<li>Touch only the probe tip to the <b>+</b> speaker screw.</li>
</ol>
{fig_output()}
<div class="warn">⚠️ <b>Never clip the ground lead to either speaker screw.</b> The amp drives both speaker wires, and the scope's ground is joined to the circuit's ground through USB, so the clip would short an output.</div>
<table><tr><th>You see</th><th>Means</th></tr>
<tr><td>Fast 5 V pulses that change with the sound</td><td>The amp works. Check the speaker wires are clamped tight and the speaker clicks on an AA battery.</td></tr>
<tr><td>A flat line, with power and all three signals good</td><td>The amp board itself is faulty, or a header joint is cracked. Reflow its 7 joints; if that doesn't help, try a spare amp.</td></tr></table>
</div>
</main>
<footer>Ceiling Clock · drawn by <code>hardware/make_amp_test_page.py</code></footer>
</body></html>
'''

if __name__ == '__main__':
    open(OUT, 'w').write(page())
    print('wrote', os.path.relpath(OUT))
