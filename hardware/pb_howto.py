"""How-to drawings for docs/perfboard.html, for someone soldering for the first time: making a joint, good and
bad joints, preparing a wire, the capacitor's legs, the beep test, and why the bars lie beside the holes.

Side views are cross-sections: the board is the green band, each plated hole a gap lined with metal, pads on both
faces. Every label sits below or beside its drawing, never across a line (Scott's rule for all drawings).
"""
import html

GREEN, GREEN_D, PAD, SOLDER, LEAD = '#1f6b45', '#174f33', '#b9c0c6', '#d4d9de', '#9aa3ab'
INK, MUT, ACC = '#222', '#555', '#e8743b'


def esc(s):
    return html.escape(str(s), quote=True)


def svg(w, h, label, body):
    return (f'<svg viewBox="0 0 {w} {h}" class="pbsvg howto" role="img" aria-label="{esc(label)}" xmlns="http://www.w3.org/2000/svg" '
            f'font-family="system-ui,sans-serif"><rect width="{w}" height="{h}" fill="#fbfaf6"/>{body}</svg>')


def caption(x, y, title, lines, w=180):
    out = f'<text x="{x}" y="{y}" text-anchor="middle" font-size="15" font-weight="800" fill="{INK}">{esc(title)}</text>'
    for i, ln in enumerate(lines):
        out += f'<text x="{x}" y="{y + 20 + i * 17}" text-anchor="middle" font-size="12.5" fill="{MUT}">{esc(ln)}</text>'
    return out


def board_section(cx, y, w=150, hole=True, pads=True):
    """Board cross-section centred on a hole at cx; top face at y. Returns svg."""
    t = 16
    s = f'<rect x="{cx - w/2}" y="{y}" width="{w}" height="{t}" fill="{GREEN}"/>'
    if hole:
        s += f'<rect x="{cx - 6}" y="{y}" width="12" height="{t}" fill="#fbfaf6"/>'
        s += f'<rect x="{cx - 7}" y="{y}" width="2" height="{t}" fill="{PAD}"/><rect x="{cx + 5}" y="{y}" width="2" height="{t}" fill="{PAD}"/>'
    if pads:
        for yy in (y - 3, y + t):
            s += f'<rect x="{cx - 17}" y="{yy}" width="10" height="3" fill="{PAD}"/><rect x="{cx + 7}" y="{yy}" width="10" height="3" fill="{PAD}"/>'
    return s


def iron(x, y, angle=-35):
    """Soldering iron tip touching (x, y), handle up and to the right."""
    return (f'<g transform="translate({x},{y}) rotate({angle})">'
            f'<path d="M0,0 L10,-5 L70,-7 L70,7 L10,5 Z" fill="#8a8f95" stroke="#555"/>'
            f'<rect x="70" y="-10" width="60" height="20" rx="3" fill="#b8bcc0" stroke="#666"/>'
            f'<rect x="130" y="-14" width="90" height="28" rx="10" fill="#2b5f8a"/></g>')


def solder_wire(x, y, angle=-145, length=120):
    return (f'<g transform="translate({x},{y}) rotate({angle})">'
            f'<line x1="0" y1="0" x2="{length}" y2="0" stroke="{SOLDER}" stroke-width="5" stroke-linecap="round"/>'
            f'<line x1="0" y1="0" x2="{length}" y2="0" stroke="#8a9096" stroke-width="1" opacity=".6"/></g>')


def fillet(cx, y, kind='good'):
    """Solder on the pad you're working on: the board's top face at y (y grows downward, the joint grows up)."""
    if kind == 'good':
        return f'<path d="M{cx - 17},{y} L{cx - 2},{y - 17} L{cx + 2},{y - 17} L{cx + 17},{y} Q{cx},{y - 3} {cx - 17},{y}z" fill="{SOLDER}" stroke="#8a9096"/>' \
               f'<path d="M{cx - 15},{y - 1} Q{cx - 4},{y - 5} {cx - 2},{y - 16} L{cx - 9},{y - 6}z" fill="#fff" opacity=".55"/>'
    if kind == 'little':
        return f'<path d="M{cx - 6},{y} L{cx - 2},{y - 8} L{cx + 2},{y - 8} L{cx + 6},{y}z" fill="{SOLDER}" stroke="#8a9096"/>'
    if kind == 'much':
        return f'<circle cx="{cx}" cy="{y - 12}" r="16" fill="{SOLDER}" stroke="#8a9096"/><circle cx="{cx - 6}" cy="{y - 18}" r="4" fill="#fff" opacity=".6"/>'
    if kind == 'cold':
        return f'<path d="M{cx - 15},{y} C{cx - 18},{y - 8} {cx - 6},{y - 6} {cx - 8},{y - 14} C{cx - 2},{y - 20} {cx + 6},{y - 10} {cx + 9},{y - 16} C{cx + 16},{y - 9} {cx + 14},{y - 4} {cx + 15},{y}z" fill="#a5a9ab" stroke="#777"/>'
    return ''


def lead(cx, top, bottom, w=4):
    return f'<rect x="{cx - w/2}" y="{top}" width="{w}" height="{bottom - top}" fill="{LEAD}" stroke="#6c737a" stroke-width=".8"/>'


def part_below(cx, y):
    """The part the lead belongs to, under the board (a resistor body), so it's clear which side is which."""
    return f'<rect x="{cx - 22}" y="{y + 44}" width="44" height="16" rx="7" fill="#d8c08c" stroke="#8a6a3b"/>'


NOTE = 'Side view, cut through one hole. The board is turned over as you solder it: the part is underneath, you work on top.'


# ---------------------------------------------------------------- 1. making a joint
def how_to_solder():
    W, H, y = 1000, 340, 140
    body = f'<text x="500" y="325" text-anchor="middle" font-size="14" font-weight="700" fill="{MUT}">{NOTE}</text>'
    xs = [125, 375, 625, 875]
    for i, x in enumerate(xs):
        body += board_section(x, y) + part_below(x, y) + lead(x, y - 14, y + 44)
    x = xs[0]; body += iron(x + 6, y - 5, -40)
    body += caption(x, 225, '1  Heat both', ['Touch the iron\'s tip to the', 'pad and the lead together.', 'Count to two.'])
    x = xs[1]; body += iron(x + 6, y - 5, -40) + solder_wire(x - 6, y - 5, -140, 110)
    body += f'<path d="M{x - 12},{y} L{x - 2},{y - 8} L{x + 2},{y - 8} L{x + 8},{y}z" fill="{SOLDER}"/>'
    body += caption(x, 225, '2  Feed the solder', ['Touch the solder to the joint', 'on the side away from the iron,', 'not to the tip. It melts and flows.'])
    x = xs[2]; body += fillet(x, y) + iron(x + 30, y - 40, -40) + solder_wire(x - 30, y - 40, -140, 100)
    body += caption(x, 225, '3  Solder away, then iron', ['About 3 mm of solder is enough.', 'Take the solder away first,', 'then the iron. Don\'t move it.'])
    x = xs[3]; body += fillet(x, y)
    body += caption(x, 225, '4  Done', ['A shiny little cone round the', 'lead. Let it set for 3 seconds,', 'then trim the lead to 1 mm.'])
    return svg(W, H, 'How to make a solder joint, in four steps', body)


# ---------------------------------------------------------------- 2. good and bad joints
def joints():
    W, H, y = 1000, 330, 110
    body = ''
    items = [('good', 'Good', ['Shiny, smooth, a cone that', 'hugs the lead and covers', 'the pad. Like a little volcano.']),
             ('little', 'Too little', ['Pad still shows round it.', 'Heat it again and add', 'a touch more solder.']),
             ('much', 'Too much', ['A ball sitting on top: the', 'pad wasn\'t hot. Reheat; soak', 'the extra up with braid.']),
             ('cold', 'Dull and lumpy', ['It moved while it set, or', 'wasn\'t hot enough. Reheat', 'until it flows shiny.']),
             ('bridge', 'Bridge', ['Solder joins two pads that', 'should be separate. Soak', 'it up with braid.'])]
    for i, (kind, title, lines) in enumerate(items):
        x = 100 + i * 200
        body += f'<rect x="{x - 90}" y="30" width="180" height="160" rx="10" fill="{"#e8f5ec" if kind == "good" else "#fbeee8"}"/>'
        body += f'<text x="{x}" y="60" text-anchor="middle" font-size="22" font-weight="800" fill="{"#1e7a43" if kind == "good" else "#b9471c"}">{"✓" if kind == "good" else "✗"}</text>'
        if kind == 'bridge':
            body += f'<rect x="{x - 70}" y="{y}" width="140" height="16" fill="{GREEN}"/>'
            for cx in (x - 22, x + 22):
                body += f'<rect x="{cx - 6}" y="{y}" width="12" height="16" fill="#fbfaf6"/>' + lead(cx, y - 12, y + 40)
            body += f'<path d="M{x - 40},{y} Q{x - 30},{y - 20} {x},{y - 14} Q{x + 30},{y - 20} {x + 40},{y}z" fill="{SOLDER}" stroke="#8a9096"/>'
        else:
            body += board_section(x, y, 120) + lead(x, y - 14, y + 40) + fillet(x, y, kind)
        body += caption(x, 220, title, lines)
    return svg(W, H, 'A good solder joint and four common problems', body)


# ---------------------------------------------------------------- 3. preparing a wire
def wire_prep():
    W, H = 1000, 330
    body = ''
    def ins(x0, x1, y, col='#2e86c1'):
        return f'<rect x="{x0}" y="{y - 7}" width="{x1 - x0}" height="14" rx="6" fill="{col}"/>'
    # 1 strip
    x = 100
    body += ins(20, 140, 100) + ''.join(f'<line x1="140" y1="{100 + d}" x2="178" y2="{100 + d * 1.6}" stroke="#c98b55" stroke-width="1.6"/>' for d in (-3, -1.5, 0, 1.5, 3))
    body += f'<line x1="140" y1="122" x2="178" y2="122" stroke="{ACC}" stroke-width="2"/><text x="159" y="140" text-anchor="middle" font-size="12" font-weight="700" fill="{ACC}">3 mm</text>'
    body += caption(x, 210, '1  Strip 3 mm', ['Wire strippers in the 26 AWG', 'notch. Don\'t cut the thin', 'copper strands inside.'])
    # 2 twist
    x = 300
    body += ins(220, 340, 100) + f'<path d="M340,100 C348,94 356,106 364,100 C370,95 374,104 378,100" stroke="#c98b55" stroke-width="5" fill="none" stroke-linecap="round"/>'
    body += caption(x, 210, '2  Twist', ['Twist the strands tight', 'between finger and thumb,', 'so none stick out.'])
    # 3 tin
    x = 500
    body += ins(420, 540, 100) + f'<rect x="540" y="96" width="38" height="8" rx="3" fill="{SOLDER}" stroke="#8a9096"/>' + iron(560, 92, -60)
    body += caption(x, 210, '3  Tin the end', ['Heat the strands with the iron', 'and touch solder to them: it', 'soaks in and makes them one.'])
    # 4 through the hole
    x = 700
    body += board_section(x, 120, 130) + f'<rect x="{x - 7}" y="40" width="14" height="78" rx="6" fill="#2e86c1"/><rect x="{x - 3}" y="116" width="6" height="34" fill="{SOLDER}" stroke="#8a9096" stroke-width=".8"/>'
    body += caption(x, 210, '4  In from the top', ['Push it into its hole from the', 'top until the insulation', 'touches the board.'])
    # 5 turned over: wire below, joint on top, trim
    x = 900
    body += board_section(x, 120, 130) + f'<rect x="{x - 7}" y="138" width="14" height="60" rx="6" fill="#2e86c1"/>' + lead(x, 100, 138, 6) + fillet(x, 120)
    body += f'<path d="M{x + 14},98 l26,6 l0,-14 z" fill="#c0392b"/><line x1="{x - 20}" y1="102" x2="{x + 20}" y2="102" stroke="{ACC}" stroke-dasharray="4 3"/>'
    body += caption(x, 210, '5  Turn over, solder, trim', ['Solder it on the underside,', 'then snip the end to about', '1 mm. Hold the bit: it flies.'])
    return svg(W, H, 'Preparing a wire and soldering it in, in five steps', body)


# ---------------------------------------------------------------- 4. the capacitor
def capacitor():
    W, H = 1000, 300
    cx = 230
    body = (f'<rect x="{cx - 40}" y="30" width="80" height="140" rx="12" fill="#1f4e8c"/>'
            f'<rect x="{cx - 40}" y="30" width="26" height="140" fill="#d6dbe2"/>'
            f'<rect x="{cx - 40}" y="30" width="80" height="140" rx="12" fill="none" stroke="#0c2a4f" stroke-width="2"/>'
            + ''.join(f'<text x="{cx - 27}" y="{60 + i * 30}" text-anchor="middle" font-size="20" font-weight="900" fill="#1f4e8c">−</text>' for i in range(4))
            + f'<line x1="{cx - 15}" y1="170" x2="{cx - 15}" y2="225" stroke="{LEAD}" stroke-width="4"/>'
            f'<line x1="{cx + 15}" y1="170" x2="{cx + 15}" y2="265" stroke="{LEAD}" stroke-width="4"/>')
    body += f'<text x="{cx - 70}" y="232" text-anchor="end" font-size="15" font-weight="800" fill="{INK}">short leg: −</text>'
    body += f'<text x="{cx + 40}" y="270" font-size="15" font-weight="800" fill="#c0392b">long leg: +</text>'
    body += f'<text x="{cx + 60}" y="100" font-size="14" fill="{MUT}">the pale stripe with − marks</text><text x="{cx + 60}" y="118" font-size="14" fill="{MUT}">is on the − side</text>'
    tx = 560
    for i, ln in enumerate(['This kind of capacitor has a + and a − leg,', 'and it must go in the right way round.',
                            '', 'Long leg (+) into A16, the 5 V rail.', 'Short leg and the stripe (−) into A18,', 'the ground rail, toward the back edge.',
                            '', 'Backwards, it can get hot and burst.', 'Check twice before you solder.']):
        body += f'<text x="{tx}" y="{60 + i * 24}" font-size="16" font-weight="{800 if i in (3, 4, 7) else 400}" fill="{INK if i != 7 else "#b9471c"}">{esc(ln)}</text>'
    return svg(W, H, 'Which way round the capacitor goes', body)


# ---------------------------------------------------------------- 5. the beep test
def beep():
    W, H = 1000, 300
    mx, my = 150, 60
    body = (f'<rect x="{mx - 70}" y="{my}" width="140" height="200" rx="16" fill="#f1c232" stroke="#8a6d0b" stroke-width="2"/>'
            f'<rect x="{mx - 52}" y="{my + 18}" width="104" height="44" rx="4" fill="#cfd8c9" stroke="#555"/>'
            f'<text x="{mx}" y="{my + 48}" text-anchor="middle" font-size="22" font-family="monospace" fill="{INK}">0.2 Ω</text>'
            f'<circle cx="{mx}" cy="{my + 115}" r="34" fill="#333"/><line x1="{mx}" y1="{my + 115}" x2="{mx + 22}" y2="{my + 92}" stroke="#fff" stroke-width="4"/>'
            f'<text x="{mx + 30}" y="{my + 86}" font-size="16">🔊</text>'
            f'<circle cx="{mx - 30}" cy="{my + 178}" r="8" fill="#111"/><circle cx="{mx + 30}" cy="{my + 178}" r="8" fill="#c0392b"/>')
    # probes on two pads of a rail
    px = [420, 560]
    body += f'<rect x="360" y="140" width="260" height="26" fill="{GREEN_D}"/>'
    for x in range(375, 620, 30):
        body += f'<circle cx="{x}" cy="153" r="9" fill="{PAD}"/><circle cx="{x}" cy="153" r="3.5" fill="#26302b"/>'
    body += f'<line x1="365" y1="160" x2="615" y2="160" stroke="#e9edf0" stroke-width="4"/>'
    body += f'<path d="M{mx - 30},{my + 178} C260,300 380,230 {px[0] - 5},158" stroke="#111" stroke-width="3" fill="none"/>'
    body += f'<path d="M{mx + 30},{my + 178} C300,280 520,240 {px[1] + 5},158" stroke="#c0392b" stroke-width="3" fill="none"/>'
    body += f'<text x="490" y="120" text-anchor="middle" font-size="13.5" fill="{MUT}">probe tips on two pads of a rail</text>'
    tx = 660
    for i, ln in enumerate(['Turn the dial to the symbol that looks', 'like a speaker or sound waves: the', '"continuity" or beep setting.', '',
                            'Touch the two probe tips together:', 'it beeps. That means "connected".', '',
                            'Beep between two pads: they\'re joined.', 'Silence: they\'re not.']):
        body += f'<text x="{tx}" y="{48 + i * 24}" font-size="15.5" font-weight="{800 if i in (7, 8) else 400}" fill="{INK}">{esc(ln)}</text>'
    return svg(W, H, 'Using the multimeter\'s beep test', body)


# ---------------------------------------------------------------- 6. bars beside the holes
def bar_beside():
    W, H = 1000, 270
    body = ''
    def row(x0, y, across):
        s = f'<rect x="{x0 - 20}" y="{y - 26}" width="330" height="52" rx="6" fill="{GREEN_D}"/>'
        for i in range(10):
            cx = x0 + i * 30
            s += f'<circle cx="{cx}" cy="{y}" r="11" fill="{PAD}"/><circle cx="{cx}" cy="{y}" r="4.5" fill="#1b1d1c"/>'
        yy = y if across else y + 8
        s += f'<line x1="{x0 - 6}" y1="{yy}" x2="{x0 + 276}" y2="{yy}" stroke="#eef1f3" stroke-width="5"/><line x1="{x0 - 6}" y1="{yy}" x2="{x0 + 276}" y2="{yy}" stroke="#7d868d" stroke-width="1"/>'
        return s
    body += row(60, 90, True)
    body += caption(195, 150, '✗  Across the holes', ['The bar covers every hole:', 'a wire can\'t go in later.'])
    body += row(560, 90, False)
    for i in (0, 5, 9):
        body += f'<ellipse cx="{560 + i * 30}" cy="94" rx="12" ry="10" fill="{SOLDER}" stroke="#8a9096"/>'
    body += f'<circle cx="{560 + 3 * 30}" cy="90" r="15" fill="none" stroke="{ACC}" stroke-width="3"/>'
    body += caption(695, 150, '✓  Beside the holes', ['Lay it along the edge of the pads, so', 'the holes stay open. Solder it only at a', 'few holes nothing else uses. A wire goes', 'into a hole like the ringed one later.'], 300)
    return svg(W, H, 'Lay the bare wire beside the holes, not across them', body)


ALL = dict(how_to_solder=how_to_solder, joints=joints, wire_prep=wire_prep, capacitor=capacitor, beep=beep, bar_beside=bar_beside)
