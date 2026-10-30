"""Exports the 3D viewer model (docs/models/clock.glb) from enclosure.scad.

Printed parts become one mesh each. Bought components (components.scad) become one mesh per
material, named "<part>__<material>", so the viewer can colour circuit boards, metal, pins,
lit segments and so on. Needs: openscad, python3 with trimesh.

Usage: python3 hardware/export_viewer_model.py
"""
import os, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
SCAD = os.path.join(HERE, 'enclosure.scad')
OUT = os.path.join(HERE, '..', 'docs', 'models', 'clock.glb')

PRINTED = ['base', 'lid', 'barrel', 'lcd_holder', 'led_cap', 'lens_mount', 'sleeve', 'lens_cap', 'ring_holder', 'dome', 'pins_asm',
           'pins_barrel']
COMPONENTS = ['ref_tm1637', 'ref_window', 'ref_button', 'ref_buttonB', 'ref_ldr', 'ref_perfboard', 'ref_esp32',
              'ref_amp', 'ref_rtc', 'ref_mosfet', 'ref_speaker', 'ref_usbc', 'ref_led', 'ref_diffuser', 'ref_lcd',
              'ref_mirror', 'ref_lens', 'ref_ring', 'ref_wires']
MATERIALS = ['pcb_blue', 'pcb_green', 'pcb_red', 'pcb_purple', 'pcb_black', 'black', 'metal', 'metal_dark', 'alu',
             'gold', 'copper', 'white', 'mirror', 'led_red', 'seg_off', 'led_yellow', 'glass', 'lcd_glass', 'acrylic_red',
             'diffuser', 'screw_green', 'resistor', 'cap_blue', 'cone', 'wire_red', 'wire_black', 'wire_yellow',
             'wire_white', 'wire_blue', 'wire_green']


def render(job):
    name, part, mat, tmp = job
    out = os.path.join(tmp, name + '.stl')
    args = ['openscad', '-q', '-D', f'part="{part}"', '-o', out, SCAD]
    if mat:
        args[2:2] = ['-D', f'mat="{mat}"']
    subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not os.path.exists(out) or os.path.getsize(out) < 200:
        return None
    m = trimesh.load(out, force='mesh')
    if m.is_empty:
        return None
    m.merge_vertices()
    return name, m


def main():
    with tempfile.TemporaryDirectory() as tmp:
        jobs = [(p, p, None, tmp) for p in PRINTED]
        jobs += [(f'{c}__{m}', c, m, tmp) for c in COMPONENTS for m in MATERIALS]
        with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as ex:
            results = [r for r in ex.map(render, jobs) if r]
    scene = trimesh.Scene()
    for name, mesh in sorted(results):
        scene.add_geometry(mesh, node_name=name, geom_name=name)
    scene.export(OUT)
    faces = sum(len(m.faces) for _, m in results)
    print(f'{len(results)} meshes, {faces} triangles -> {os.path.relpath(OUT)} ({os.path.getsize(OUT) / 1e6:.2f} MB)')
    for name, _ in sorted(results):
        print(' ', name)


if __name__ == '__main__':
    sys.exit(main())
