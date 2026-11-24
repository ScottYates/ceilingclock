#!/usr/bin/env python3
"""Builds docs/printing.html and docs/img/print-*.png: every printed part, how it sits on the bed, and its settings.
Pictures are rendered from the STL files themselves, so they always show the orientation the files are saved in.
Needs openscad and xvfb-run."""
import os, subprocess, html, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, '..', 'docs')
STL = os.path.join(HERE, 'stl')

# file, name, colour, layer, supports, notes, camera distance
PARTS = [
    ('base', 'Base', 'Dark', '0.2 mm', 'None',
     'The biggest print (170 × 135 × 72 mm), floor flat on the bed. The front display window, the USB-C slot and the side button hole are small bridges your slicer handles without help. '
     'Stick four 6 mm rubber feet under the corners afterwards: they lift the floor so the speaker can breathe. Use <code>base_056.stl</code> instead if your front display is a 0.56" module.', 560),
    ('lid', 'Lid', 'Dark', '0.2 mm', 'None',
     'Prints upside down, top face on the bed, so the top comes out smooth. The pin ramps underneath face up.', 380),
    ('barrel', 'Barrel', 'Matte black', '0.2 mm', 'None',
     'Stands on its open end. Tall and narrow: add a 5 mm brim so it can\'t be knocked over. The mirror ramp inside is a 45° slope and prints as it is.', 300),
    ('disp_holder', 'Display holder', 'Matte black', '0.2 mm', 'None',
     'Lies on the face that points at the mirror. The slot for the display opens out of its edge.', 200),
    ('end_cap', 'End cap', 'Dark', '0.2 mm', 'Inside only',
     'Stands on its open collar, pin tabs up. The flat ceiling inside is a 46 mm bridge: turn on supports set to <b>touching the build plate only</b>; they stand inside the cap and pull out through the collar. Nothing touches the outside.', 230),
    ('lens_mount', 'Lens mount', 'Matte black', '0.12–0.16 mm', 'Under the two tabs only',
     'Upside down, round top on the bed. Paint supports (or use support enforcers) under the two pin tabs that stick out of the sides, and leave automatic supports off: they would fill the thread inside.', 300),
    ('sleeve_61in', 'Focus ring, 61in', 'Matte black', '0.12–0.16 mm', 'None',
     'Grip down. Pick this one (or <code>sleeve_44in.stl</code>) by the distance from the lens to your ceiling: 61in for about 50–75 in, 44in for about 36–55 in. The number is engraved on its top face. '
     'Turn on elephant\'s-foot compensation (about 0.2 mm): the lens pocket is on the bed side.', 220),
    ('lens_cap_61in', 'Lens cap, 61in', 'Any', '0.2 mm', 'None',
     'Ring on the bed, tube up. Use the cap with the same number as the focus ring: its tube is cut to the depth of that ring\'s lens pocket.', 200),
    ('batt_tray', 'Battery tray', 'Any', '0.2 mm', 'None',
     'Only if you fit the battery, and only for the 5000 mAh pouch cell: a bigger pack goes in the bay without it. Prints flat as it is, 74 × 66 × 10 mm. '
     'The pocket is 67.5 × 56.6 mm, 1 mm larger than a 65.5 × 54.6 mm cell all round so it isn\'t squeezed: for a cell of another size, change <code>pouch</code> in enclosure.scad and export again.', 200),
    ('pins', 'Twist-lock pins', 'Any (PETG is a little tougher)', '0.16 mm', 'None',
     'Wing heads flat on the bed. One file prints the whole set: short pins for the lid corners, long ones for the end cap and the lens mount. Print a spare set; they are small.', 160),
]


def render(name, dist):
    out = os.path.join(DOCS, 'img', f'print-{name}.png')
    with tempfile.NamedTemporaryFile('w', suffix='.scad', delete=False) as f:
        f.write(f'color("#d8d4c8") translate([-110, -110, -1.25]) cube([220, 220, 1.2]);\n'
                f'color("#3d5a80") import("{os.path.join(STL, name + ".stl")}");\n')
        scad = f.name
    import trimesh
    m = trimesh.load(os.path.join(STL, name + '.stl'))
    c = m.bounds.mean(0)
    subprocess.run(['xvfb-run', '-a', 'openscad', '-q', '-o', out, '--imgsize=900,640', f'--camera={c[0]:.1f},{c[1]:.1f},{c[2]:.1f},58,0,-30,{dist}',
                    '--colorscheme=Tomorrow', scad], check=True)
    os.unlink(scad)
    return (m.bounds[1] - m.bounds[0])


def page(sizes):
    rows = ''
    for (f, name, colour, layer, sup, notes, _), sz in zip(PARTS, sizes):
        rows += f'''
<section class="pp">
  <img src="img/print-{f}.png?v=20261120c" alt="{html.escape(name)} on the print bed" loading="lazy">
  <div><h2>{html.escape(name)} <small><code>{f}.stl</code></small></h2>
  <table class="pins"><tr><th>Size</th><td>{sz[0]:.0f} × {sz[1]:.0f} × {sz[2]:.0f} mm</td></tr><tr><th>Colour</th><td>{colour}</td></tr>
  <tr><th>Layer height</th><td>{layer}</td></tr><tr><th>Supports</th><td>{sup}</td></tr></table>
  <p>{notes}</p></div>
</section>'''
    return f'''<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Printing · Ceiling Clock</title>
<link rel="stylesheet" href="style.css?v=20261030w">
<style>
.pp{{display:grid;grid-template-columns:minmax(260px,420px) 1fr;gap:18px;border:1px solid var(--line);border-radius:16px;padding:14px;margin:18px 0;background:var(--paper)}}
.pp img{{width:100%;border-radius:10px;border:1px solid var(--line);background:#fff}}
.pp h2{{margin:2px 0 8px}}.pp h2 small{{font-weight:400;color:var(--mut);font-size:.8rem}}
.pins{{border-collapse:collapse;margin:6px 0 10px}}.pins td,.pins th{{border:1px solid var(--line);padding:4px 10px;text-align:left}}.pins th{{background:#f3f1ea;font-weight:600}}
@media (max-width:720px){{.pp{{grid-template-columns:1fr}}}}
</style>
</head><body>
<header class="site"><div class="in">
<a class="brand" href="index.html"><span class="dot"></span>Ceiling Clock</a>
<nav><a href="index.html">3D model</a><a href="printing.html" class="on">Printing</a><a href="assembly.html">Assembly</a><a href="wiring.html">Wiring</a><a href="breadboard.html">Breadboard test</a><a href="perfboard.html">Perfboard</a><a href="parts.html">Parts</a><a href="demo/">Live demo</a><a href="firmware.html">Firmware &amp; use</a><a href="https://github.com/ScottYates/ceilingclock">GitHub</a></nav>
</div></header>
<main class="in">
<h1>Printing the parts</h1>
<p class="lead">Nine files in <a href="https://github.com/ScottYates/ceilingclock/tree/main/hardware/stl"><code>hardware/stl/</code></a>, each saved the way it should sit on the bed: load it and don't rotate it. The pictures below are rendered from those files.</p>
<h2>Settings for every part</h2>
<ul>
<li><b>Material:</b> PLA or PETG, 0.4 mm nozzle.</li>
<li><b>Walls</b> 3, <b>top and bottom</b> 4 layers, <b>infill</b> 15–20 %.</li>
<li><b>Colour:</b> matte black for the barrel, display holder, lens mount and focus ring. Light bouncing around inside lighter plastic washes out the time on the ceiling. The rest can be any colour you like.</li>
<li><b>Layer height:</b> 0.2 mm, except the two threaded parts (lens mount, focus ring) at 0.12–0.16 mm so the thread turns smoothly.</li>
<li><b>Supports:</b> only where a part below says so.</li>
</ul>
<p>After printing, screw the focus ring into the lens mount before fitting the lens: it should turn by hand with a slight drag. If it's stiff, run it in and out a few times.</p>
{rows}
</main></body></html>'''


if __name__ == '__main__':
    sizes = [render(p[0], p[6]) for p in PARTS]
    open(os.path.join(DOCS, 'printing.html'), 'w').write(page(sizes))
    print('wrote docs/printing.html')
