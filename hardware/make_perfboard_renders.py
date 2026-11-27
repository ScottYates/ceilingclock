#!/usr/bin/env python3
"""Renders the perfboard pictures for docs/perfboard.html: docs/img/pb-*.jpg, and docs/models/perfboard.glb for
the page's 3D view.

Builds each stage of the board with pb_model.py, then renders it with three.js in headless Chromium
(pb_render/render.html via pb_render/shoot.js). Needs node with playwright, and Pillow.
"""
import json, os, shutil, subprocess, sys, time, socket
from PIL import Image

import pb_model

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
OUT = os.path.join(HERE, 'pb_render', '.out')           # stage models and raw PNGs (not committed)
IMG = os.path.join(ROOT, 'docs', 'img')

FRONT = dict(cam=[30, -95, 95], target=[35, 12, 2], fov=32)
BACK = dict(cam=[-20, 115, 100], target=[36, 24, 2], fov=32)
ABOVE = dict(cam=[33, -60, 135], target=[35, 15, 2], fov=34)
UNDER = dict(cam=[35, -52, 86], target=[35, 27, 0], fov=31)
WIRES = dict(cam=[35, -42, 118], target=[35, 25, 2], fov=37)                 # every wire step: row A toward you, both edges in view
GROUP_VIEW = {g: WIRES for g in pb_model.GROUP_IDS}

SHOTS = [
    ('kit', 'kit', dict(cam=[50, -110, 120], target=[50, 0, 0], fov=32)),
    ('jig', 'jig', dict(cam=[18, -82, 95], target=[35, 24, 8], fov=31)),
    ('headers', 'headers', dict(cam=[30, -72, 95], target=[35, 25, 3], fov=31)),
    ('rails', 'rails', UNDER),
    ('rails-close', 'rails', dict(cam=[38, 18, 34], target=[37, 44, 0], fov=30)),
    ('bridges', 'bridges', UNDER),
    ('bridges-close', 'bridges', dict(cam=[48, -24, 34], target=[46, 6, 0], fov=30)),
    ('links', 'links', UNDER),
    ('cap', 'cap', dict(cam=[-22, -10, 62], target=[12, 40, 4], fov=32)),
] + [(f'g-{g}', f'g:{g}', GROUP_VIEW[g]) for g in pb_model.GROUP_IDS] + [
    ('all', 'all', WIRES),
    ('all-under', 'all_under', dict(cam=[30, -70, 100], target=[35, 22, -3], fov=34)),
    ('esp32', 'esp32', dict(cam=[-10, -90, 100], target=[35, 20, 5], fov=33)),
    ('esp32-back', 'esp32', dict(cam=[110, 118, 100], target=[35, 27, 5], fov=33)),
]
CASE_SHOT = ('incase', dict(cam=[40, -125, 330], target=[18, -8, 20], fov=34,
                            show=['base', 'ref_feet', 'ref_perfboard', 'ref_esp32', 'ref_amp', 'ref_rtc', 'ref_speaker', 'ref_tm1637',
                                  'ref_usbc', 'ref_buttonB', 'ref_window', 'ref_bb_boards', 'ref_packs', 'batt_tray', 'ref_wires']))


def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p


def main(only=None):
    os.makedirs(OUT, exist_ok=True)
    stages = sorted({st for _, st, _ in SHOTS})
    floors = {}
    for st in stages:
        sc, flip, floor = pb_model.stage(st)
        sc.export(os.path.join(OUT, st.replace(':', '_') + '.glb'))
        floors[st] = floor
    pb_model.LITE = True
    sc, _, _ = pb_model.stage('final')
    pb_model.LITE = False
    sc.export(os.path.join(ROOT, 'docs', 'models', 'perfboard.glb'))
    print('stages built:', len(stages), ' perfboard.glb', os.path.getsize(os.path.join(ROOT, 'docs', 'models', 'perfboard.glb')) // 1024, 'KB')

    rel = os.path.relpath(OUT, ROOT).replace(os.sep, '/')
    jobs = []
    for name, st, view in SHOTS:
        if only and name not in only: continue
        jobs.append(dict(out=os.path.join(OUT, name + '.png'), model=f'/{rel}/{st.replace(":", "_")}.glb', floor=floors[st], **view))
    if not only or CASE_SHOT[0] in only:
        jobs.append(dict(out=os.path.join(OUT, CASE_SHOT[0] + '.png'), model='/docs/models/clock.glb', floor=0, **CASE_SHOT[1]))
    jf = os.path.join(OUT, 'jobs.json')
    json.dump(jobs, open(jf, 'w'))

    port = free_port()
    srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=ROOT,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1)
        env = dict(os.environ)
        env.setdefault('NODE_PATH', subprocess.run(['npm', 'root', '-g'], capture_output=True, text=True).stdout.strip())
        subprocess.run(['node', os.path.join(HERE, 'pb_render', 'shoot.js'), f'http://127.0.0.1:{port}', jf], check=True, env=env)
    finally:
        srv.terminate()

    for j in jobs:
        im = Image.open(j['out']).convert('RGB').resize((1400, 875), Image.LANCZOS)
        name = os.path.splitext(os.path.basename(j['out']))[0]
        im.save(os.path.join(IMG, f'pb-{name}.jpg'), quality=84, optimize=True, progressive=True)
    print('wrote', len(jobs), 'pictures to docs/img/pb-*.jpg')


if __name__ == '__main__':
    main(set(sys.argv[1:]) or None)
