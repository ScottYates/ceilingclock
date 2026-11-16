# Usage: python3 hardware/make_rewire_guide.py
# Writes docs/rewire.html: bringing a one-breadboard build made before firmware 2.0 up to date. Such a board
# has the build guide's steps up to the amplifier; the old projector parts (Nokia LCD, sunrise ring, projector
# LED) weren't wired. Added: the second TM1637 as the projector, and the two alarm buttons with lights. The
# pictures use make_breadboard_guide.py's layout and drawing code.
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_breadboard_guide as g
from make_breadboard_guide import W_, esp, hl, rl, md, esc, COL, COLNAME, MIRROR

g.LAY = 'one'
G = g.G
NEW = {s['id']: s for s in g.build_steps()}
g.check_holes(list(NEW.values()))

def part(**k):
    k.setdefault('wires', []); k.setdefault('parts', []); k.setdefault('mods', [])
    return k

# ---------------------------------------------------------------- the board as it is (build guide up to the amplifier)
KEEP = [NEW[i] for i in ('power', 'buttons', 'tm1637', 'ldr', 'supply', 'amp')]
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

PROJ_NEW = part(wires=NEW['proj']['wires'], mods=['proj'])
step('start', 'Your board now, and clearing space', '5 min',
     'Your board has everything up to the amplifier from the <a href="breadboard.html">build guide</a>, on one breadboard: the front display, buttons A and B, the light sensor, the 5 V supply and the amplifier. The old projector parts (Nokia LCD, sunrise ring, projector LED) were never wired, so nothing has to come out. ESP32 pins 8 to 13 are free, and the right-hand end of the board (rows 49 to 60) is empty: that\'s where the new parts go.',
     picture('rw-start', part(), merge(*KEEP), badges=False),
     after='<ol class="todo"><li>Unplug the USB cable from the computer and the 5 V adapter.</li>'
           '<li>Lift the computer\'s USB cable off the breadboard and lay it to the right of the ESP32\'s USB port, away from rows 25 to 60. It lies across the holes the alarm buttons and lights use.</li>'
           '<li>If a loose wire runs from beside the ESP32 to a foil tab (a probe point from <a href="amp-test.html">testing the amplifier</a>), take it out. It isn\'t part of the clock.</li></ol>')

step('proj', 'Projector display (second TM1637)', '5 min',
     NEW['proj']['intro'] + ' It needs four new female–male jumper wires.',
     picture('rw-proj', merge(*KEEP), PROJ_NEW),
     lists='<h3>Connect</h3>' + wire_list('rw-proj', PROJ_NEW['wires'], 'Add') +
           '<p class="mut">The two data wires go in the holes in front of the yellow strip, beside pins 11 and 12. That\'s rows 17 (pin 11) and 18 (pin 12); counting back from the <b>5V</b> pin\'s hole, they\'re the 4th and 3rd. Wire colours don\'t matter; the pictures use the guide\'s.</p>',
     after='<p>Plug the USB cable back into the computer.</p>',
     test=NEW['proj']['test'], fix=NEW['proj']['fix'],
     warn='Don\'t mix up the two displays: the front one stays on pins 4 and 5.')

step('alarm', 'Alarm buttons and their lights', '15 min',
     ALARM['intro'] + ' Unplug the USB cable while you add them.',
     picture('rw-alarm', merge(*KEEP, PROJ_NEW), ALARM),
     lists='<h3>Place the parts</h3><ol class="place">' + ''.join(f'<li>{t}</li>' for t in ALARM['place']) + '</ol>'
           '<h3>Connect</h3>' + wire_list('rw-alarm', ALARM['wires'], 'Add'),
     test='Plug the USB cable back in. ' + ALARM['test'], fix=ALARM['fix'],
     warn='Rows 49 and 55 are next to the light sensor\'s resistor (row 48). Count carefully: the purple wire goes in row 49, not 48.')

FINAL = [s for s in g.build_steps() if s['id'] in ('power', 'buttons', 'alarmbtn', 'tm1637', 'proj', 'ldr', 'supply', 'amp')]
final_lines = [(st['title'], w) for st in FINAL for w in st['wires']]
final_wires = [w for _, w in final_lines]
step('check', 'Check the whole board', '10 min',
     'Everything on the board, as the build guide has it. Go through the list once with the power off and tick each wire as you find it. Your colours may differ (your amplifier wires are purple, blue and white, and the light sensor\'s wire is red); what matters is where each end goes.',
     picture('rw-check', part(), merge(*KEEP, PROJ_NEW, ALARM) | dict(wires=final_wires)),
     lists=wire_list('rw-check', final_wires, 'Check', [f'<span class="mut">{esc(t)}</span><br>{w["ta"]} <span class="arr">→</span> {w["tb"]}' for t, w in final_lines]),
     test='Plug in the USB cable and the 5 V adapter. The front display shows the time; the projector display shows it flipped; '
          'alarm buttons 1 and 2 switch their alarms and their lights blink; button B switches the front display (hold 3 s for the projector); '
          'button A lights the LEDs of the alarms that are on; under <b>Sounds</b>, <b>Play</b> on beep.wav beeps four times.')

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
<title>Update an older breadboard · Ceiling Clock</title>
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
<h1>Update an older breadboard</h1>
<p class="lead">For a breadboard built before firmware 2.0 on <b>one breadboard</b>: everything up to the amplifier from the <a href="breadboard.html">build guide</a>. Since 2.0 the ceiling projector is a second TM1637 display (the Nokia LCD, sunrise ring and projector LED are gone from the design), and two alarm buttons with lights switch the alarms on and off. Nothing on your board changes; you add those two things. Allow 30 minutes. The pictures show your board turned with row 1 on the left.</p>

<h2>What's new</h2>
<table class="pins"><tr><th>ESP32 pin</th><th>Goes to</th></tr>
<tr><td>12</td><td>Projector display CLK</td></tr>
<tr><td>11</td><td>Projector display DIO</td></tr>
<tr><td>8</td><td>Alarm button 1</td></tr>
<tr><td>9</td><td>Alarm button 2</td></tr>
<tr><td>10</td><td>Alarm 1 light</td></tr>
<tr><td>13</td><td>Alarm 2 light</td></tr></table>
<div class="need"><b>You need:</b> <span class="chip">A second TM1637 display, the same kind as the front one</span><span class="chip">2 small push buttons</span><span class="chip">2 LEDs, any colour</span><span class="chip">2 × 220 Ω resistors (red-red-brown)</span><span class="chip">4 female–male jumper wires</span><span class="chip">6 male–male jumper wires</span></div>
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
