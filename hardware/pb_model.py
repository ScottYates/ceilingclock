"""3D model of the clock's perfboard at every build stage, for the pictures in docs/perfboard.html.

Uses the layout in make_perfboard_guide.py (pads, bridges, links, wires), so the pictures and the hole maps
always agree. Coordinates in mm: x along the columns (column 1 at the left), y along the rows (row A at the
front), z up; the board's underside is z = 0 and its top z = 1.6. stage(name) returns a trimesh.Scene with one
mesh per material, with PBR materials, ready to export as GLB.
"""
import math
import numpy as np
import trimesh
from trimesh.visual.material import PBRMaterial
from trimesh.visual import TextureVisuals

import make_perfboard_guide as G

T = 1.6                                  # board thickness
LITE = False                             # fewer facets, for the page's interactive model
P = G.P


def hole(c, r):
    return np.array([G.X0 + (c - 1) * P, G.Y0 + r * P])


def padxy(name):
    c, r = G.pad(name)
    return hole(c, r)


# ---------------------------------------------------------------- materials
def hexrgb(h, a=1.0):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(ch * 2 for ch in h)
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)] + [a]


def mat(color, metal=0.0, rough=0.6):
    return dict(color=color, metal=metal, rough=rough)


MATS = {
    'board': mat('#c69a5c', 0, 0.75),
    'copper': mat('#d48a4f', 1, 0.32),
    'solder': mat('#d7dbe0', 1, 0.22),
    'header': mat('#161616', 0, 0.45),
    'gold': mat('#d4a64a', 1, 0.3),
    'cap': mat('#24508f', 0, 0.32),
    'cap_stripe': mat('#cfd6df', 0, 0.35),
    'alu': mat('#c3c7cc', 1, 0.3),
    'pcb_black': mat('#141414', 0, 0.5),
    'pcb_blue': mat('#2a4d7a', 0, 0.45),
    'shield': mat('#b9bec4', 1, 0.28),
    'usb': mat('#c9ccd0', 1, 0.25),
    'white': mat('#eeeeee', 0, 0.4),
    'res_body': mat('#d9c18f', 0, 0.55),
    'res_body_blue': mat('#6e9bc9', 0, 0.45),
}


def wire_mat(color, old=False):
    key = ('wire_old_' if old else 'wire_') + color.lstrip('#')
    if key not in MATS:
        c = color
        if old:                                   # earlier wires: desaturated and lighter so the new ones stand out
            rgb = np.array(hexrgb(color)[:3]) * 0.3 + np.array([0.66, 0.66, 0.64]) * 0.7
            c = '#%02x%02x%02x' % tuple(int(v * 255) for v in rgb)
        MATS[key] = mat(c, 0, 0.42)
    return key


class Build:
    def __init__(self):
        self.parts = {}

    def add(self, m, mesh):
        self.parts.setdefault(m, []).append(mesh)

    def scene(self, flip=False):
        sc = trimesh.Scene()
        for m, meshes in sorted(self.parts.items()):
            mesh = trimesh.util.concatenate(meshes)
            if flip:                                 # turned over left to right: x -> width - x, z -> 1.6 - z
                M = np.eye(4); M[0, 0] = -1; M[2, 2] = -1; M[0, 3] = G.BW; M[2, 3] = T
                mesh.apply_transform(M)
            d = MATS[m]
            lin = [((ch + 0.055) / 1.055) ** 2.4 if ch > 0.04045 else ch / 12.92 for ch in hexrgb(d['color'])[:3]] + [1.0]
            mesh.visual = TextureVisuals(material=PBRMaterial(name=m, baseColorFactor=lin,
                                                              metallicFactor=d['metal'], roughnessFactor=d['rough'], doubleSided=False))
            sc.add_geometry(mesh, node_name=m, geom_name=m)
        return sc


# ---------------------------------------------------------------- primitives
def box(x0, y0, z0, x1, y1, z1):
    b = trimesh.creation.box(extents=[x1 - x0, y1 - y0, z1 - z0])
    b.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return b


def cyl(r, p0, p1, sections=14):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    if np.linalg.norm(p1 - p0) < 1e-6:
        return None
    return trimesh.creation.cylinder(radius=r, segment=[p0, p1], sections=sections)


def ball(r, p, sub=1):
    s = trimesh.creation.icosphere(subdivisions=sub, radius=r)
    s.apply_translation(p)
    return s


def revolve(profile, at, sections=20):
    """profile: [(r, z), ...] from the axis out and back; revolved about z, placed at `at` (x, y, z)."""
    m = trimesh.creation.revolve(np.array(profile, float), sections=sections)
    m.apply_translation(at)
    return m


def tube(points, r, sections=12):
    if LITE: sections = min(sections, 8)
    """A round wire along a polyline: cylinders with balls at the bends."""
    out = []
    pts = [np.asarray(p, float) for p in points]
    for a, b in zip(pts, pts[1:]):
        c = cyl(r, a, b, sections)
        if c is not None:
            out.append(c)
    for p in pts[1:-1]:
        out.append(ball(r, p, 1))
    return trimesh.util.concatenate(out)


def bezier(p0, p1, p2, p3, n=12):
    p0, p1, p2, p3 = (np.asarray(p, float) for p in (p0, p1, p2, p3))
    t = np.linspace(0, 1, n)[:, None]
    return list((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3)


# ---------------------------------------------------------------- the board
_board_cache = {}


def board(b):
    if LITE not in _board_cache:
        slab = box(0, 0, 0, G.BW, G.BH, T)
        holes = [cyl(0.5, (*hole(c, r), -1), (*hole(c, r), T + 1), 8) for c in range(1, G.COLS + 1) for r in range(G.ROWS)]
        slab = slab.difference(trimesh.util.concatenate(holes), engine='manifold')
        ring = trimesh.creation.annulus(r_min=0.5, r_max=0.95, height=0.05, sections=7 if LITE else 12)
        pads = []
        for c in range(1, G.COLS + 1):
            for r in range(G.ROWS):
                x, y = hole(c, r)
                for z in (-0.025, T + 0.025):
                    m = ring.copy(); m.apply_translation([x, y, z]); pads.append(m)
        _board_cache[LITE] = (slab, trimesh.util.concatenate(pads))
    slab, pads = _board_cache[LITE]
    b.add('board', slab.copy())
    b.add('copper', pads.copy())


def joint(b, xy, stub=0.9, r=0.95):
    """Solder joint on the underside: a fillet cone round a lead stub."""
    b.add('solder', revolve([(0, 0.02), (r, 0.02), (r * 0.97, -0.18), (r * 0.82, -0.42), (r * 0.58, -0.68), (0.34, -0.95), (0.3, -stub - 0.15),
                             (0.2, -stub - 0.3), (0, -stub - 0.33)], (xy[0], xy[1], 0), 9 if LITE else 18))


def top_joint(b, xy, r=0.85):
    b.add('solder', revolve([(0, T - 0.02), (r, T - 0.02), (r * 0.7, T + 0.3), (0.3, T + 0.55), (0, T + 0.6)], (xy[0], xy[1], 0)))


def bridge(b, a, z, solder_every=True):
    """Bare tinned wire along a column on the underside, soldered at every pad it crosses."""
    (c1, r1), (c2, r2) = G.pad(a), G.pad(z)
    p0, p1 = hole(c1, r1), hole(c2, r2)
    b.add('solder', cyl(0.3, (*p0, -0.3), (*p1, -0.3), 10))
    for r in range(min(r1, r2), max(r1, r2) + 1):
        x, y = hole(c1, r)
        b.add('solder', revolve([(0, 0.02), (1.0, 0.02), (0.85, -0.3), (0.5, -0.62), (0, -0.7)], (x, y, 0), 8 if LITE else 16))


def link(b, a, z, color):
    """Insulated link on the underside, ends through the holes and soldered."""
    pa, pz = padxy(a), padxy(z)
    lo = -1.6
    if a == '24C':                                   # the long 5 V link: back toward the middle, across, then down to 3K
        mid1 = hole(23, 7); mid2 = hole(5, 9)
        path = [(*pa, -0.4), (*pa, lo)] + bezier((*pa, lo), (pa[0], pa[1] + 10, lo), (mid1[0] + 4, mid1[1], lo), (*mid1, lo), 8)[1:] \
            + bezier((*mid1, lo), (mid1[0] - 10, mid1[1], lo), (mid2[0] + 10, mid2[1], lo), (*mid2, lo), 10)[1:] \
            + bezier((*mid2, lo), (mid2[0] - 2, mid2[1] + 1, lo), (pz[0] + 1, pz[1] - 2, lo), (*pz, lo), 8)[1:] + [(*pz, -0.4)]
    else:
        m = (pa + pz) / 2
        path = [(*pa, -0.4), (*pa, lo)] + bezier((*pa, lo), (pa[0], pa[1] - 2.5, lo - 0.6), (pz[0], pz[1] - 2.5, lo - 0.6), (*pz, lo), 10)[1:] + [(*pz, -0.4)]
    b.add(wire_mat(color), tube(path[1:-1], 0.55, 10))
    for p in (pa, pz):
        joint(b, p, 0.6)


def header(b, row, socket=True, pins_soldered=True, lift=0.0):
    x0 = hole(G.HC0, row)[0] - P / 2; x1 = hole(G.HC0 + 21, row)[0] + P / 2
    y = hole(1, row)[1]
    body = box(x0, y - P / 2, T + lift, x1, y + P / 2, T + 8.5 + lift)
    cut = [box(hole(G.HC0 + i, row)[0] - 0.5, y - 0.5, T + 3 + lift, hole(G.HC0 + i, row)[0] + 0.5, y + 0.5, T + 9 + lift) for i in range(22)]
    body = body.difference(trimesh.util.concatenate(cut), engine='manifold')
    b.add('header', body)
    for i in range(22):
        x = hole(G.HC0 + i, row)[0]
        b.add('gold', box(x - 0.32, y - 0.12, (-1.8 if pins_soldered else -2.8) + lift, x + 0.32, y + 0.12, T + 1 + lift))
        if pins_soldered:
            joint(b, (x, y), 1.0)


def capacitor(b, lying=False, at=None):
    if lying:                                         # loose, for the parts picture
        x, y = at
        b.add('cap', cyl(3.15, (x, y, 3.15), (x + 11, y, 3.15), 28))
        s = cyl(3.18, (x + 0.6, y, 3.15), (x + 10.4, y, 3.15), 28).intersection(box(x, y - 4, 4.2, x + 11, y + 4, 7), engine='manifold')
        b.add('cap_stripe', s)
        b.add('alu', cyl(2.9, (x + 11, y, 3.15), (x + 11.05, y, 3.15), 24))
        for dy, L in ((-1.25, 16), (1.25, 13.5)):
            b.add('solder', cyl(0.3, (x, y + dy, 3.15), (x - L, y + dy, 0.3), 8))
        return
    plus, minus = padxy(G.CAP[0]), padxy(G.CAP[1])
    c = (plus + minus) / 2
    z0 = T + 0.6
    b.add('cap', cyl(3.15, (*c, z0), (*c, z0 + 11), 32))
    # the minus stripe faces the minus pad (toward column 1)
    d = (minus - plus) / np.linalg.norm(minus - plus)
    ang = math.degrees(math.atan2(d[1], d[0]))
    s = cyl(3.18, (*c, z0 + 0.4), (*c, z0 + 10.6), 32)
    wedge = box(0, -4, z0, 5, 4, z0 + 11)
    wedge.apply_transform(trimesh.transformations.rotation_matrix(math.radians(ang), [0, 0, 1]))
    wedge.apply_translation([*c, 0])
    b.add('cap_stripe', s.intersection(wedge, engine='manifold'))
    b.add('alu', cyl(2.95, (*c, z0 + 11), (*c, z0 + 11.05), 28))
    b.add('header', cyl(3.0, (*c, z0 - 0.4), (*c, z0), 28))           # rubber bung
    for p, off in ((plus, -1.25), (minus, 1.25)):
        leg_top = c + d * off
        b.add('solder', tube([(*leg_top, z0 - 0.2), (*leg_top, T + 0.35), (*p, T + 0.1), (*p, -1.0)], 0.28, 8))
        joint(b, p, 0.8)


def esp32(b):
    L, W = 62.7, 28.0
    cx = hole(14.5, 7)[0]; cy = hole(4, 7)[1]
    x0, y0 = cx - L / 2, cy - W / 2
    z0 = T + 8.5 + 2.5
    b.add('pcb_black', box(x0, y0, z0, x0 + L, y0 + W, z0 + 1.6))
    b.add('pcb_blue', box(x0 - 0.5, y0 + (W - 18) / 2, z0 + 1.6, x0 + 25, y0 + (W + 18) / 2, z0 + 2.4))
    b.add('shield', box(x0 + 6.5, y0 + (W - 15.8) / 2, z0 + 2.4, x0 + 24.1, y0 + (W + 15.8) / 2, z0 + 4.8))
    for k in range(4):                                # antenna trace
        b.add('gold', box(x0 + 0.6 + k * 1.3, y0 + (W - 14) / 2, z0 + 2.4, x0 + 1.1 + k * 1.3, y0 + (W + 14) / 2, z0 + 2.45))
    for s in (-1, 1):
        b.add('usb', box(x0 + L - 7.3, y0 + W / 2 + s * 6.3 - 4.5, z0 + 1.6, x0 + L + 0.2, y0 + W / 2 + s * 6.3 + 4.5, z0 + 4.8))
        b.add('header', box(x0 + L - 14, y0 + W / 2 + s * 9 - 2, z0 + 1.6, x0 + L - 10.5, y0 + W / 2 + s * 9 + 2, z0 + 3.0))
    b.add('white', box(x0 + L - 18, y0 + W / 2 - 1, z0 + 1.6, x0 + L - 16, y0 + W / 2 + 1, z0 + 2.4))
    b.add('header', box(x0 + L - 30, y0 + W / 2 - 4, z0 + 1.6, x0 + L - 24, y0 + W / 2, z0 + 2.8))
    for row in (G.ROW_J1, G.ROW_J3):                  # male pin strips going down into the sockets
        y = hole(1, row)[1]
        xa, xb = hole(G.HC0, row)[0] - P / 2, hole(G.HC0 + 21, row)[0] + P / 2
        b.add('header', box(xa, y - P / 2, z0 - 2.5, xb, y + P / 2, z0))
        for i in range(22):
            x = hole(G.HC0 + i, row)[0]
            b.add('gold', box(x - 0.32, y - 0.32, z0 - 8.5, x + 0.32, y + 0.32, z0 + 2.2))


def resistor(b, at, bands, body='res_body', length=6.3):
    x, y, z = at
    b.add(body, cyl(1.15, (x, y, z), (x + length, y, z), 18))
    for k, colr in enumerate(bands):
        key = wire_mat(colr)
        b.add(key, cyl(1.19, (x + 1.0 + k * 1.05, y, z), (x + 1.55 + k * 1.05, y, z), 18))
    b.add('solder', cyl(0.25, (x - 12, y, z), (x, y, z), 8))
    b.add('solder', cyl(0.25, (x + length, y, z), (x + length + 12, y, z), 8))


# ---------------------------------------------------------------- module wires
def wire(b, pad_name, color, old=False, floor=-1.4, rise=None, ends=True):
    """A module wire: in from the top, soldered underneath, out over the nearest edge and down onto the mat."""
    c, r = G.pad(pad_name)
    x, y = hole(c, r)
    R = 0.62                                           # 26 AWG with insulation
    key = wire_mat(color, old)
    if c <= 3:                                         # rail pads: out to the left; column 3 rides highest
        h = T + 1.3 + (c - 1) * 1.75
        out = np.array([-1, 0]); edge = x + 3
    elif r == 0:
        h = T + 1.3; out = np.array([0, -1]); edge = y + 3
    else:
        h = T + 1.3 + (14 - r) * 1.75; out = np.array([0, 1]); edge = G.BH - y + 3
    if rise is not None:
        h = rise
    p_in = np.array([x, y, T + 0.9])
    bend = np.array([x, y, h - 0.9])
    run0 = np.array([x + out[0] * 1.6, y + out[1] * 1.6, h])
    run1 = np.array([x + out[0] * edge, y + out[1] * edge, h])
    drop = floor + R + 0.05
    curve = bezier(run1, run1 + np.r_[out * 6, 0], np.r_[run1[:2] + out * 10, drop], np.r_[run1[:2] + out * 18, drop], 10)
    tail = np.r_[run1[:2] + out * 40, drop]
    pts = [p_in, bend] + bezier(bend, bend + [0, 0, 0.7], run0 - np.r_[out * 0.7, 0], run0, 5)[1:] + [run1] + curve[1:] + [tail]
    b.add(key, tube(pts, R, 12))
    # stripped, tinned end
    if ends:
        b.add('solder', cyl(0.3, tail, np.r_[run1[:2] + out * 43.5, drop], 8))
    # the lead through the board and its joint underneath
    b.add('solder', cyl(0.3, (x, y, T + 1.0), (x, y, -0.6), 8))
    joint(b, (x, y), 0.9)


# ---------------------------------------------------------------- stages
GROUP_IDS = [g['id'] for g in G.GROUPS]


def underside_basics(b, rails=True, signals=True, links=True):
    if rails:
        for c in (G.GND, G.V33, G.V5):
            bridge(b, f'{c}A', f'{c}O')
    if signals:
        for c in G.SIG_COLS_FRONT:
            bridge(b, f'{c}A', f'{c}C')
        for c in G.SIG_COLS_BACK:
            bridge(b, f'{c}M', f'{c}O')
    if links:
        for a, z, _, colr in G.LINKS:
            link(b, a, z, colr)


def stage(name):
    """Returns (scene, flip, floor_z): floor_z is where the mat goes in the picture."""
    b = Build()
    if name == 'kit':
        board(b)
        hb = Build()
        header(hb, G.ROW_J1, pins_soldered=False)
        sc = Build()
        for m, meshes in hb.parts.items():               # two loose header strips, lying in front of the board
            for k, dy in enumerate((-14, -22)):
                for mesh in meshes:
                    mm = mesh.copy(); mm.apply_translation([0, dy - hole(1, G.ROW_J1)[1], -T + 2.8])
                    b.add(m, mm)
        capacitor(b, lying=True, at=(94, 31))
        resistor(b, (90, 16, 1.15), ['#c0392b', '#c0392b', '#6b3a1f', '#d4a64a'])      # 220 R: red red brown gold
        resistor(b, (90, 9, 1.15), ['#c0392b', '#c0392b', '#6b3a1f', '#d4a64a'])
        resistor(b, (90, 2, 1.15), ['#6b3a1f', '#111111', '#e67e22', '#d4a64a'])      # 10 k: brown black orange gold
        for k, colr in enumerate(['#c0392b', '#222222', '#e67e22', '#7d3c98', '#2e86c1', '#17a589']):   # hookup wire offcuts
            b.add(wire_mat(colr), tube([(78 + k * 3.2, -4, 0.62), (80 + k * 3.2, -16, 0.62), (79 + k * 3.2, -30, 0.62)], 0.62))
        coil = [(18 + 8 * math.cos(t), -38 + 5 * math.sin(t), 0.3 + 0.12 * t) for t in np.linspace(0, 6 * math.pi, 120)]
        b.add('solder', tube(coil, 0.3, 8))
        return b.scene(), False, 0.0
    if name in ('rails', 'bridges', 'links'):
        board(b)
        underside_basics(b, True, name != 'rails', name == 'links')
        return b.scene(flip=True), True, 0.0
    if name == 'jig':
        board(b)
        underside_basics(b)
        for row in (G.ROW_J1, G.ROW_J3):
            header(b, row, pins_soldered=False)
        esp32(b)
        return b.scene(), False, -1.4
    board(b); underside_basics(b)
    for row in (G.ROW_J1, G.ROW_J3):
        header(b, row)
    capacitor(b)
    if name == 'headers':
        return b.scene(), False, -1.4
    if name.startswith('g:'):
        gid = name[2:]
        upto = GROUP_IDS.index(gid)
        for i, g in enumerate(G.GROUPS[:upto + 1]):
            for label, p_, what, colr in g['wires']:
                wire(b, p_, colr, old=i < upto)
        return b.scene(), False, -1.4
    if name in ('all', 'esp32', 'final'):
        for g in G.GROUPS:
            for label, p_, what, colr in g['wires']:
                wire(b, p_, colr)
        if name == 'esp32':
            esp32(b)
        sc = b.scene()
        if name == 'final':                               # the ESP32 as its own nodes, so the page can take it out
            e = Build(); esp32(e)
            for nm, geom in e.scene().geometry.items():
                sc.add_geometry(geom, node_name='esp32_' + nm, geom_name='esp32_' + nm)
        return sc, False, -1.4
    if name == 'all_under':                              # turned over, propped on the capacitor and headers
        floor = T + 0.6 + 11.05
        for g in G.GROUPS:
            for label, p_, what, colr in g['wires']:
                wire(b, p_, colr, floor=floor)
        return b.scene(flip=True), True, T - floor
    raise ValueError(name)


STAGES = ['kit', 'rails', 'bridges', 'links', 'jig', 'headers'] + ['g:' + g for g in GROUP_IDS] + ['all', 'all_under', 'esp32']

if __name__ == '__main__':
    import sys, os
    out = sys.argv[1] if len(sys.argv) > 1 else '/tmp/pb_glb'
    os.makedirs(out, exist_ok=True)
    for s in (sys.argv[2:] or STAGES):
        sc, flip, floor = stage(s)
        fn = os.path.join(out, s.replace(':', '_') + '.glb')
        sc.export(fn)
        print(s, 'floor', round(floor, 2), 'faces', sum(len(g.faces) for g in sc.geometry.values()), os.path.getsize(fn) // 1024, 'KB')
