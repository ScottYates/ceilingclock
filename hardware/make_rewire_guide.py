# Usage: python3 hardware/make_rewire_guide.py
# Writes docs/rewire.html: how to change a breadboard built from the old guide (firmware 1.x: Nokia 5110 LCD,
# sunrise ring, projector LED and MOSFET) into the current one (second TM1637 as the projector, two alarm
# buttons with lights), for the one-breadboard layout. The pictures use make_breadboard_guide.py's layout and
# drawing code; the old parts sit where the old guide (commit 5269020) put them.
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_breadboard_guide as g
from make_breadboard_guide import W_, esp, hl, rl, md, esc, COL, COLNAME, MIRROR

g.LAY = 'one'
# the old modules, where the old guide drew them
g.MODS.update({
    'lcd':    (800, 30, 980, 175, 'left', ['RST', 'CE', 'DC', 'DIN', 'CLK', 'VCC', 'BL', 'GND'], '#b03030', 'Nokia 5110 LCD', ''),
    'ring':   (800, 200, 980, 320, 'left', ['DI', '5V', 'GND'], '#1d1d1d', 'WS2812B ring', ''),
    'mosfet': (800, 345, 980, 455, 'left', ['TRIG', 'GND', 'VIN+', 'VIN−', 'OUT+', 'OUT−'], '#2a6f9e', 'MOSFET module', ''),
    'led':    (840, 490, 980, 570, 'left', ['LED +', 'LED −'], '#d39a00', '3 W LED star', 'on metal'),
})
G = g.G
NEW = {s['id']: s for s in g.build_steps()}
g.check_holes(list(NEW.values()))

def part(**k):
    k.setdefault('wires', []); k.setdefault('parts', []); k.setdefault('mods', [])
    return k

# ---------------------------------------------------------------- the board as built from the old guide
# (old pins: LCD RST 8, DC 9, CE 10, DIN 11, CLK 12; projector LED 13; ring 18)
KEEP = [NEW[i] for i in ('power', 'buttons', 'tm1637', 'ldr', 'supply', 'amp')]   # unchanged since then
LCD_GONE = part(wires=[W_('brown', esp('8'), md('lcd', 'RST', 'LCD RST')),
                       W_('purple', esp('10'), md('lcd', 'CE', 'LCD CE')),
                       W_('cyan', esp('9'), md('lcd', 'DC', 'LCD DC')),
                       W_('gnd', md('lcd', 'BL', 'LCD BL'), rl('t-', 27))], mods=['lcd'])
LCD_STAYS = part(wires=[W_('green', esp('11'), md('lcd', 'DIN', 'LCD DIN')),
                        W_('yellow', esp('12'), md('lcd', 'CLK', 'LCD CLK')),
                        W_('3v3', md('lcd', 'VCC', 'LCD VCC'), rl('t+', 28)),
                        W_('gnd', md('lcd', 'GND', 'LCD GND'), rl('t-', 29))])
RING = part(wires=[W_('green', esp('18'), hl(50, 'j', note='one end of the 330 Ω')),
                   W_('green', hl(54, 'j', note='other end of the 330 Ω'), md('ring', 'DI', 'ring DI')),
                   W_('5v', md('ring', '5V', 'ring 5V'), rl('b+', 27)),
                   W_('gnd', md('ring', 'GND', 'ring GND'), rl('b-', 28))],
            parts=[('res', 50, 54, 'h', '330 Ω', None), ('cap', 23, '1000 µF')], mods=['ring'])
LED = part(wires=[W_('grey', esp('13'), md('mosfet', 'TRIG', 'module TRIG')),
                  W_('gnd', md('mosfet', 'GND', 'module trigger GND'), rl('b-', 26)),
                  W_('5v', md('mosfet', 'VIN+', 'module VIN+', None), rl('b+', 29), 'screw terminal–male'),
                  W_('gnd', md('mosfet', 'VIN−', 'module VIN−', None), rl('b-', 25), 'screw terminal–male'),
                  W_('5v', md('mosfet', 'OUT+', 'module OUT+', None), hl(56, 'a', note='one end of the 4.7 Ω'), 'screw terminal–male'),
                  W_('5v', hl(60, 'a', note='other end of the 4.7 Ω'), md('led', 'LED +', 'LED +', None), 'male–soldered lead'),
                  W_('gnd', md('led', 'LED −', 'LED −', None), md('mosfet', 'OUT−', 'module OUT−', None), 'soldered lead–screw terminal')],
           parts=[('res', 56, 60, 'c', '4.7 Ω 2 W', None)], mods=['mosfet', 'led'])
# the projector display, wired with the LCD's old jumpers: the green one stays on DIO
PROJ = part(wires=[W_('yellow', esp(str(G('PIN_PROJ_CLK'))), md('proj', 'CLK', 'projector CLK')),
                   W_('green', esp(str(G('PIN_PROJ_DIO'))), md('proj', 'DIO', 'projector DIO')),
                   W_('3v3', md('proj', 'VCC', 'projector VCC'), rl('t+', 28)),
                   W_('gnd', md('proj', 'GND', 'projector GND'), rl('t-', 29))], mods=['proj'])
ALARM = NEW['alarmbtn']

def merge(*xs): return part(wires=[w for x in xs for w in x['wires']], parts=[p for x in xs for p in x['parts']],
                            mods=[m for x in xs for m in x['mods']])

# ---------------------------------------------------------------- pictures
def picture(sid, before, now, remove=False, badges=True):
    """The board with `before` faded and `now` bright and numbered; with remove, `now` is crossed out."""
    S = [dict(before, id='rw-ctx'), dict(now, id=sid)]
    svg = g.draw_step(S, 1)
    if not badges:   # drop the number badges (drawn last, each in its own group)
        import re
        svg = re.sub(r'<g class="wire" data-w="[^"]*">\n<circle [^>]*/>\n<text [^>]*>\d+</text>\n</g>\n?', '', svg)
    if not remove: return svg
    s = g.Svg()
    def cross(x, y, r=6):
        for col, w in (('#fff', 6), ('#d0021b', 3)):
            s.line(x - r, y - r, x + r, y + r, col, w); s.line(x - r, y + r, x + r, y - r, col, w)
    for w in now['wires']:
        for e in (w['a'], w['b']): cross(*e['pt'])
    for p in now['parts']:
        if p[0] == 'res':
            a, b = g.hole(p[1], p[3], p[5]), g.hole(p[2], p[3], p[5])
            cross((a[0] + b[0]) / 2, a[1] - 1, 9)
        elif p[0] == 'cap':
            a, b = g.rail('b+', p[1]), g.rail('b-', p[1] + 1)
            cross((a[0] + b[0]) / 2, g.RAILY('b-') + 30, 10)
    for m in now['mods']:
        x0, y0, x1, y1, *_ = g.mod_box(m)
        s.add(f'<g opacity="0.85"><line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y1}" stroke="#d0021b" stroke-width="4"/>'
              f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y0}" stroke="#d0021b" stroke-width="4"/></g>')
        s.text((x0 + x1) / 2, y1 + 15, 'comes out', 11, '#d0021b', 'middle', 800, extra='stroke="#fbfaf6" stroke-width="3" paint-order="stroke"')
    return svg.replace('</svg>', '\n'.join(s.o) + '</svg>')

def wire_list(sid, wires, verb, texts=None):
    out = []
    for j, w in enumerate(wires):
        wid = f'{g.PRE["one"]}{sid}-{j + 1}'
        body = texts[j] if texts else f'{w["ta"]} <span class="arr">→</span> {w["tb"]}'
        out.append(f'<li data-w="{wid}"><label><input type="checkbox" data-k="{wid}"><span class="badge" style="border-color:{COL[w["col"]]}">{j + 1}</span>'
                   f'<span class="sw" style="background:{COL[w["col"]]}"></span><span class="wt"><b>{verb} the {esc(COLNAME[w["col"]])} wire</b> ({esc(w["kind"])}):<br>{body}</span></label></li>')
    return f'<ul class="wires">{"".join(out)}</ul>'

STEPS = []
def step(sid, title, time, intro, pic, lists='', after='', test='', fix=(), warn=''):
    STEPS.append(dict(sid=sid, title=title, time=time, intro=intro, pic=pic, lists=lists, after=after, test=test, fix=fix, warn=warn))

step('unplug', 'Unplug everything', '1 min',
     'Unplug the USB cable from the computer and the 5 V adapter. Every change below is made with the power off.',
     picture('rw-unplug', part(), merge(*KEEP, LCD_GONE, LCD_STAYS, RING, LED), badges=False),
     after='<p class="mut">This is your board now, built from the old guide: the Nokia LCD, the sunrise ring and the projector LED on the right. Your ESP32 already runs the new firmware (2.3.0), which no longer uses the LCD, the ring or the LED.</p>')

step('ring', 'Take out the sunrise ring', '5 min',
     'The sunrise light is gone from the design. Take out its four wires, the 330 Ω resistor and the big 1000 µF capacitor in the bottom rails. '
     f'The resistor in row 50–54 sits exactly where the first alarm light goes in step 6.',
     picture('rw-ring', merge(*KEEP, LCD_GONE, LCD_STAYS, LED), RING, remove=True),
     lists=wire_list('rw-ring', RING['wires'], 'Pull out') +
           f'<ol class="place"><li>Pull out the <b>330 Ω resistor</b> (orange-orange-brown) from <b>{MIRROR["h"]}50</b> and <b>{MIRROR["h"]}54</b>.</li>'
           '<li>Pull out the <b>1000 µF capacitor</b> (the big blue one) from the bottom rails. The small <b>100 µF</b> one by the amplifier stays.</li>'
           '<li>Put the ring away; it isn\'t used any more.</li></ol>',
     fix=[('Two capacitors in the bottom rails: which is which?', 'The 1000 µF is the bigger one, at about row 23. The 100 µF that stays is at about row 19, next to the amplifier\'s wires.')])

step('led', 'Take out the projector LED and its switch', '5 min',
     'The projector no longer needs a lamp: the new projector display lights its own digits. Take out the MOSFET module, the 3 W LED and the 4.7 Ω resistor with their seven wires.',
     picture('rw-led', merge(*KEEP, LCD_GONE, LCD_STAYS), LED, remove=True),
     lists=wire_list('rw-led', LED['wires'], 'Take out') +
           f'<ol class="place"><li>Pull out the <b>4.7 Ω 2 W resistor</b> (the big blue one) from <b>{MIRROR["c"]}56</b> and <b>{MIRROR["c"]}60</b>. It\'s next to where the second alarm button goes.</li>'
           '<li>Unscrew the wires from the MOSFET module\'s terminals. Keep the module and LED for something else; the clock doesn\'t use them.</li></ol>',
     fix=[('A wire is soldered to the LED star', 'Leave it on the star; just pull its other end out of the breadboard or terminal.')])

step('lcd', 'Unplug the LCD', '5 min',
     'The new projector display needs only two data wires: GPIO 12 and 11, the LCD\'s old CLK and DIN wires. They stay, along with its + and − wires. The other four come out: RST, CE and DC (GPIO 8, 10 and 9; the alarm buttons use those pins now) and the backlight wire.',
     picture('rw-lcd', merge(*KEEP, LCD_STAYS), LCD_GONE, remove=True),
     lists=wire_list('rw-lcd', LCD_GONE['wires'], 'Take out') +
           '<p>Then pull the female ends of the other four wires (yellow CLK, green DIN, orange VCC, black GND) off the LCD\'s pins, and leave their other ends in the breadboard. Put the LCD away.</p>',
     warn='Leave the yellow wire in the row of <b>pin 12</b> and the green one in the row of <b>pin 11</b>. Those two go to the new display in the next step.')

step('proj', 'Fit the second TM1637 as the projector', '5 min',
     'The projector is now a second four-digit display, the same kind as the front one. A lens in the clock images its digits onto the ceiling. It plugs onto the four wires the LCD had, with the breadboard ends where they already are.',
     picture('rw-proj', merge(*KEEP), PROJ),
     lists=wire_list('rw-proj', PROJ['wires'], 'Move', [
         'from the LCD\'s <b>CLK</b> to the projector display\'s <b>CLK</b>. Its other end stays beside ESP32 pin 12.',
         'from the LCD\'s <b>DIN</b> to the projector display\'s <b>DIO</b>. Its other end stays beside ESP32 pin 11. (The build guide draws this wire white; colour doesn\'t matter.)',
         'from the LCD\'s <b>VCC</b> to the projector display\'s <b>VCC</b>. Its other end stays in the top + rail.',
         'from the LCD\'s <b>GND</b> to the projector display\'s <b>GND</b>. Its other end stays in the top − rail.']),
     after='<p>Plug the USB cable back into the computer (the 5 V adapter can wait).</p>',
     test=NEW['proj']['test'], fix=NEW['proj']['fix'],
     warn='Don\'t swap the two displays\' wires: the front display stays on pins 4 and 5.')

step('alarm', 'Add the two alarm buttons and their lights', '15 min',
     ALARM['intro'] + ' They go in the rows the ring\'s and LED\'s resistors used. Unplug the USB cable while you add them.',
     picture('rw-alarm', merge(*KEEP, PROJ), ALARM),
     lists='<h3>Place the parts</h3><ol class="place">' + ''.join(f'<li>{t}</li>' for t in ALARM['place']) + '</ol>'
           '<h3>Connect</h3>' + wire_list('rw-alarm', ALARM['wires'], 'Add'),
     test='Plug the USB cable back in. ' + ALARM['test'], fix=ALARM['fix'],
     warn='Each wire to the ESP32 goes into the free hole beside the pin, in the column nearest you (the same column as every other ESP32 wire).')

ALL = merge(*KEEP, PROJ, ALARM)
FINAL = [s for s in g.build_steps() if s['id'] in ('power', 'buttons', 'alarmbtn', 'tm1637', 'proj', 'ldr', 'supply', 'amp')]
final_lines = []
for st in FINAL:
    for w in (PROJ['wires'] if st['id'] == 'proj' else st['wires']): final_lines.append((st['title'], w))   # your green DIO wire
final_wires = [w for _, w in final_lines]
step('check', 'Check the whole board', '10 min',
     'Everything on the board, as the current build guide has it. Go through the list once with the power off; tick each wire as you find it. Anything left over that isn\'t on the list (a stray wire in rows 23–29 of the rails, or in rows 49–60) should come out.',
     picture('rw-check', part(), merge(*KEEP, PROJ, ALARM) | dict(wires=final_wires)),
     lists=wire_list('rw-check', final_wires, 'Check', [f'<span class="mut">{esc(t)}</span><br>{w["ta"]} <span class="arr">→</span> {w["tb"]}' for t, w in final_lines]),
     test='Plug in the USB cable and the 5 V adapter. The front display shows the time; the projector display shows it flipped; '
          'alarm buttons 1 and 2 switch their alarms and their lights blink; button B switches the front display (hold 3 s for the projector); '
          'button A shows which alarms are on; under <b>Sounds</b>, <b>Play</b> on beep.wav beeps four times.')

# ---------------------------------------------------------------- page
def page():
    secs, toc = [], []
    for i, st in enumerate(STEPS):
        toc.append(f'<a href="#{st["sid"]}"><span>{i + 1}</span>{esc(st["title"])}</a>')
        fixes = ''.join(f'<dt>{esc(a)}</dt><dd>{b}</dd>' for a, b in st['fix'])
        secs.append(f'''
<section class="bbstep" id="{st['sid']}">
  <div class="bbhead"><span class="num">{i + 1}</span><h2>{esc(st['title'])}</h2><span class="time">⏱ {st['time']}</span></div>
  <p>{st['intro']}</p>
  {f'<div class="warn">⚠️ {st["warn"]}</div>' if st['warn'] else ''}
  <div class="pic">{st['pic']}</div>
  {st['after']}
  {st['lists']}
  {f'<div class="test"><b>✅ Test it:</b> {st["test"]}</div>' if st['test'] else ''}
  {f'<details><summary>Not working?</summary><dl>{fixes}</dl></details>' if fixes else ''}
</section>''')
    gp = g.page()
    css = gp[gp.index('<style>'):gp.index('</style>') + 8]
    return f'''<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rewire an older breadboard · Ceiling Clock</title>
<link rel="stylesheet" href="style.css?v=20261030w">
{css}
<style>.pins{{border-collapse:collapse;margin:8px 0 14px}}.pins td,.pins th{{border:1px solid var(--line);padding:5px 10px;text-align:left}}.pins th{{background:#f3f1ea}}
.next li{{margin:8px 0}}</style>
</head><body>
<header class="site"><div class="in">
<a class="brand" href="index.html"><span class="dot"></span>Ceiling Clock</a>
<nav><a href="index.html">3D model</a><a href="assembly.html">Assembly</a><a href="wiring.html">Wiring</a><a href="breadboard.html" class="on">Breadboard test</a><a href="parts.html">Parts</a><a href="demo/">Live demo</a><a href="firmware.html">Firmware &amp; use</a><a href="https://github.com/ScottYates/ceilingclock">GitHub</a></nav>
</div></header>
<main>
<h1>Rewire an older breadboard</h1>
<p class="lead">For a breadboard built from the first version of the guide, on <b>one breadboard</b>: with the Nokia LCD, the sunrise ring and the projector LED. Since firmware 2.0 the projector is a second TM1637 display, the ring and LED are gone, and two alarm buttons with lights switch the alarms on and off. Allow 45 minutes. The pictures show your board turned with row 1 on the left, as in the <a href="breadboard.html">build guide</a>.</p>

<h2>What changes</h2>
<table class="pins"><tr><th>ESP32 pin</th><th>Old board</th><th>Now</th></tr>
<tr><td>8</td><td>LCD RST</td><td>Alarm button 1</td></tr>
<tr><td>9</td><td>LCD DC</td><td>Alarm button 2</td></tr>
<tr><td>10</td><td>LCD CE</td><td>Alarm 1 light</td></tr>
<tr><td>11</td><td>LCD DIN</td><td>Projector display DIO (same wire)</td></tr>
<tr><td>12</td><td>LCD CLK</td><td>Projector display CLK (same wire)</td></tr>
<tr><td>13</td><td>Projector LED (MOSFET TRIG)</td><td>Alarm 2 light</td></tr>
<tr><td>18</td><td>Sunrise ring</td><td>Not used</td></tr>
<tr><td>4, 5, 6, 7, 14, 15, 16, 17</td><td colspan="2">Unchanged: front display, buttons A and B, light sensor, amplifier</td></tr></table>
<div class="need"><b>You need:</b> <span class="chip">A second TM1637 display, the same kind as the front one</span><span class="chip">2 small push buttons</span><span class="chip">2 LEDs, any colour</span><span class="chip">2 × 220 Ω resistors (red-red-brown)</span><span class="chip">6 male–male jumper wires</span></div>
<p class="mut">Firmware: your clock already runs 2.3.0, which expects this wiring. Nothing to flash.</p>
<div class="toc" style="display:flex">{''.join(toc)}</div>
{''.join(secs)}

<h2>Where to go from here</h2>
<ol class="next">
<li><b>See it on the ceiling.</b> In a dark room, hold the lens about 106 mm above the projector display and focus it on the ceiling (<a href="breadboard.html#s-optics">bonus step in the build guide</a>). Set the flips under <b>Settings › Ceiling picture</b>.</li>
<li><b>Get the parts the breadboard doesn't use</b> (<a href="parts.html">parts list</a>): the two <b>16 mm lit buttons</b> for the alarms, the 16 mm buttons for A and B, the <b>DS3231</b> clock module, the perfboard, the lens and the mirror.</li>
<li><b>Print the case</b> while you wait (<a href="assembly.html#step-1">assembly step 1</a>). It already has the two alarm-button holes in the lid and the projector display's holder in the barrel.</li>
<li><b>Build the electronics board</b> (<a href="assembly.html#step-4">assembly step 4</a>): the same connections, soldered on perfboard, <b>with the DS3231</b>. On one breadboard there's no room for it, and it closes the one gap left in the alarms: after a power cut while the internet is also down, the clock only knows the time if the DS3231 is fitted. From then on the 5 V supply powers the ESP32 too, and firmware updates go over Wi-Fi.</li>
<li><b>Assemble the case</b>: <a href="assembly.html#step-2">speaker</a>, front display, the projector display and lens in the barrel, the lid buttons, then focus and aim (assembly steps 2–9). The <a href="wiring.html">wiring page</a> has the full pin list.</li>
</ol>
</main>
<footer>Ceiling Clock · pictures drawn by <code>hardware/make_rewire_guide.py</code> with the build guide's layout</footer>
<script>
(() => {{
  const KEY = 'ceilingclock-rewire';
  let saved = {{}};
  try {{ saved = JSON.parse(localStorage.getItem(KEY) || '{{}}'); }} catch (e) {{}}
  const boxes = [...document.querySelectorAll('.wires input')];
  function update() {{
    const toc = [...document.querySelectorAll('.toc a')];
    document.querySelectorAll('.bbstep').forEach((s, i) => {{
      const bs = [...s.querySelectorAll('.wires input')];
      const ok = bs.length > 0 && bs.every(b => b.checked);
      s.classList.toggle('done', ok);
      if (toc[i]) toc[i].classList.toggle('done', ok);
    }});
  }}
  boxes.forEach(b => {{
    b.checked = !!saved[b.dataset.k];
    b.onchange = () => {{ saved[b.dataset.k] = b.checked; try {{ localStorage.setItem(KEY, JSON.stringify(saved)); }} catch (e) {{}} update(); }};
  }});
  const hl = (id, on) => document.querySelectorAll('[data-w="' + id + '"]').forEach(e => e.classList.toggle('hl', on));
  document.querySelectorAll('[data-w]').forEach(e => {{
    e.addEventListener('mouseenter', () => hl(e.dataset.w, true));
    e.addEventListener('mouseleave', () => hl(e.dataset.w, false));
  }});
  update();
}})();
</script>
</body></html>'''

if __name__ == '__main__':
    out = os.path.join(HERE, '..', 'docs', 'rewire.html')
    open(out, 'w').write(page())
    print('wrote', os.path.relpath(out))
