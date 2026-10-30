import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { PARTS, ALL, MATERIALS, AXIS } from './parts.js?v=20261030t';
import { optics, LENS, CEILING } from './optics.js?v=20261030t';

// createViewer(container) -> { ready: Promise, setState({visible, highlight, explode, tilt, focus, beam, camera, target}), onPick }
export function createViewer(container, { background = 0xf6f4ef, modelUrl = 'models/clock.glb' } = {}) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  container.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(background);
  const camera = new THREE.PerspectiveCamera(35, 1, 1, 5000);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;

  scene.add(new THREE.HemisphereLight(0xffffff, 0x8a8f99, 1.6));
  const key = new THREE.DirectionalLight(0xffffff, 1.6);
  key.position.set(300, 500, 400);
  scene.add(key);
  const fill = new THREE.DirectionalLight(0xffffff, 0.5);
  fill.position.set(-400, 200, -300);
  scene.add(fill);

  const grid = new THREE.GridHelper(600, 24, 0xd9d4c8, 0xe6e2d8);
  scene.add(grid);

  // Model is in mm with z up; rotate into three.js y-up.
  const root = new THREE.Group();
  root.rotation.x = -Math.PI / 2;
  scene.add(root);

  // parts that ride in the barrel hang off a pivot on the barrel's axis
  const pivot = new THREE.Group();
  pivot.position.set(0, AXIS.y, AXIS.z);
  root.add(pivot);

  const meshes = {};
  const state = { visible: ALL, highlight: [], explode: 0, tilt: 0, focus: 0, beam: false, flip: false };
  let explodeAnim = null;
  const listeners = [];

  const ready = new Promise((resolve, reject) => {
    new GLTFLoader().load(modelUrl, (gltf) => {
      gltf.scene.traverse((o) => {
        if (!o.isMesh) return;
        const [base, matName] = o.name.split('__');
        const p = PARTS[base];
        if (!p) return;
        const mt = (matName && MATERIALS[matName]) || { color: p.color, opacity: p.opacity };
        o.geometry.computeVertexNormals();
        o.material = new THREE.MeshStandardMaterial({
          color: mt.color, roughness: mt.roughness ?? 0.6, metalness: mt.metalness ?? 0.05,
          emissive: mt.emissive ?? 0x000000, transparent: !!mt.opacity, opacity: mt.opacity ?? 1,
        });
        o.userData.base = o.position.clone();
        o.userData.part = base;
        o.userData.mt = mt;
        (meshes[base] = meshes[base] || []).push(o);
      });
      root.add(gltf.scene);  // vertices are raw OpenSCAD mm, z up; root rotates them to y-up
      for (const [name, list] of Object.entries(meshes)) {
        if (!PARTS[name].tilts) continue;
        for (const m of list) {
          m.geometry.translate(0, -AXIS.y, -AXIS.z);
          // the focus ring screws in and out: centre it on the lens axis so it can turn
          if (PARTS[name].focuses) { m.geometry.translate(-LENS.x, 0, 0); m.userData.base.x += LENS.x; }
          pivot.add(m);
        }
      }
      apply();
      resolve();
    }, undefined, reject);
  });

  function apply() {
    const hl = new Set(state.highlight);
    for (const [name, list] of Object.entries(meshes)) {
      const p = PARTS[name];
      const vis = state.visible.includes(name) && !(p.hideExploded && state.explode > 0.04);
      const dim = hl.size > 0 && !hl.has(name);
      for (const m of list) {
        const mt = m.userData.mt, e = p.explode;
        m.visible = vis;
        m.position.set(m.userData.base.x + e[0] * state.explode, m.userData.base.y + e[1] * state.explode,
                       m.userData.base.z + e[2] * state.explode + (p.focuses ? state.focus : 0));
        if (p.focuses) m.rotation.z = -state.focus / LENS.pitch * 2 * Math.PI;   // one turn per 3 mm, like the thread
        m.material.color.setHex(dim ? 0xc9c5bc : mt.color);
        m.material.emissive.setHex(dim ? 0x000000 : (mt.emissive ?? 0x000000));
        m.material.transparent = dim || !!mt.opacity;
        m.material.opacity = dim ? 0.28 : (mt.opacity ?? 1);
        m.material.depthWrite = !dim && !mt.opacity;
      }
    }
  }

  // ---- light beam and ceiling: where the time lands, and how sharp it is for the lens position
  const beam = new THREE.Group();          // in the pivot's frame, so it tilts with the barrel
  pivot.add(beam);
  const beamMat = new THREE.MeshBasicMaterial({ color: 0xffd28a, transparent: true, opacity: 0.10, side: THREE.DoubleSide, depthWrite: false });
  const beamMesh = new THREE.Mesh(new THREE.BufferGeometry(), beamMat);
  beam.add(beamMesh);
  const ceil = new THREE.Group();          // fixed in the room
  root.add(ceil);
  const ceilZ = AXIS.z + LENS.rL + CEILING;
  const plane = new THREE.Mesh(new THREE.PlaneGeometry(1800, 1500), new THREE.MeshBasicMaterial({ color: 0x2a2d33, side: THREE.DoubleSide }));
  plane.position.set(0, -350, ceilZ + 1);   // a patch of dark ceiling over the clock and in front of it
  ceil.add(plane);
  const texCanvas = document.createElement('canvas');
  texCanvas.width = 512; texCanvas.height = 290;
  const tex = new THREE.CanvasTexture(texCanvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  const imgMesh = new THREE.Mesh(new THREE.BufferGeometry(), new THREE.MeshBasicMaterial({ map: tex, transparent: true, side: THREE.DoubleSide, depthWrite: false, depthTest: false }));
  imgMesh.renderOrder = 2;   // the picture shows through the beam's haze
  ceil.add(imgMesh);
  let beamText = '12:30';

  function drawCeilingImage(o) {
    const c = texCanvas.getContext('2d');
    c.clearRect(0, 0, 512, 290);
    c.fillStyle = 'rgba(255,214,150,0.10)';
    c.fillRect(0, 0, 512, 290);
    c.filter = o.blurPx > 0.25 ? `blur(${Math.min(30, o.blurPx * 3.2).toFixed(1)}px)` : 'none';
    c.fillStyle = '#ffd696';
    c.font = 'bold 150px ui-monospace, Menlo, Consolas, monospace';
    c.textAlign = 'center'; c.textBaseline = 'middle';
    c.fillText(beamText, 256, 150);
    c.filter = 'none';
    tex.needsUpdate = true;
  }
  function updateBeam() {
    beam.visible = ceil.visible = state.beam;
    if (!state.beam) return;
    const o = optics(state.focus, state.tilt);
    const t = state.tilt * Math.PI / 180;
    // lens centre in the pivot frame; image corners: x across (long side), y forward/back
    const lx = LENS.x, lz = LENS.rL + state.focus;
    const L = CEILING / Math.cos(t), hw = o.width / 2, hh = o.height / 2, a = LENS.aperture / 2 * 0.8;
    const corners = [[-1, -1], [1, -1], [1, 1], [-1, 1]];
    // beam: from the lens aperture to the image, as a four-sided frustum (length along the tilted axis;
    // the far ends get clipped visually by the ceiling, close enough to show where the light goes)
    const pos = [];
    const near = corners.map(([sx, sy]) => [lx + sx * a, sy * a, lz]);
    const far = corners.map(([sx, sy]) => {
      // ray from the lens centre through the image corner, in the pivot frame, then out to the ceiling
      const dir = new THREE.Vector3(sx * hw, sy * hh, L).normalize();
      const w = dir.clone().applyAxisAngle(new THREE.Vector3(1, 0, 0), t);   // to room frame
      const k = (CEILING) / w.z;
      return [lx + dir.x * k, dir.y * k, lz + dir.z * k];
    });
    for (let i = 0; i < 4; i++) {
      const j = (i + 1) % 4;
      pos.push(...near[i], ...near[j], ...far[j], ...near[i], ...far[j], ...far[i]);
    }
    beamMesh.geometry.dispose();
    beamMesh.geometry = new THREE.BufferGeometry();
    beamMesh.geometry.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    // the picture on the ceiling: the same corners in the room frame
    const toRoom = (p) => new THREE.Vector3(...p).applyAxisAngle(new THREE.Vector3(1, 0, 0), t).add(new THREE.Vector3(0, AXIS.y, AXIS.z));
    const fc = far.map(toRoom);
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute([...fc[0].toArray(), ...fc[1].toArray(), ...fc[2].toArray(), ...fc[3].toArray()].map((v, i) => i % 3 === 2 ? ceilZ : v), 3));
    // the mirror flips the picture once; the clock's Mirror setting puts it right, so show it the right way round
    // reads upright from in front of the clock; flip = the clock's "Flip projection" (turned 180 degrees)
    g.setAttribute('uv', new THREE.Float32BufferAttribute(state.flip ? [1, 0, 0, 0, 0, 1, 1, 1] : [0, 1, 1, 1, 1, 0, 0, 0], 2));
    g.setIndex([0, 1, 2, 0, 2, 3]);
    imgMesh.geometry.dispose();
    imgMesh.geometry = g;
    drawCeilingImage(o);
  }
  updateBeam();

  function setState(s = {}) {
    if (s.visible) state.visible = s.visible;
    if (s.highlight) state.highlight = s.highlight;
    if (s.tilt !== undefined) { state.tilt = s.tilt; pivot.rotation.x = s.tilt * Math.PI / 180; }
    if (s.focus !== undefined) { state.focus = s.focus; apply(); }
    if (s.beam !== undefined) state.beam = s.beam;
    if (s.flip !== undefined) state.flip = s.flip;
    if (s.text !== undefined) beamText = s.text;
    if (s.tilt !== undefined || s.focus !== undefined || s.beam !== undefined || s.flip !== undefined || s.text !== undefined) updateBeam();
    if (s.camera) camera.position.set(...s.camera);
    if (s.target) controls.target.set(...s.target);
    if (s.explode !== undefined) {
      if (s.animate) explodeAnim = { from: state.explode, to: s.explode, t0: performance.now() };
      else { state.explode = s.explode; explodeAnim = null; }
    }
    apply();
  }

  // Click to pick a part.
  const ray = new THREE.Raycaster(), mouse = new THREE.Vector2();
  let downAt = null;
  renderer.domElement.addEventListener('pointerdown', (ev) => { downAt = [ev.clientX, ev.clientY]; });
  renderer.domElement.addEventListener('pointerup', (ev) => {
    if (!downAt || Math.hypot(ev.clientX - downAt[0], ev.clientY - downAt[1]) > 5) return;
    const r = renderer.domElement.getBoundingClientRect();
    mouse.set(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(mouse, camera);
    const hits = ray.intersectObjects(Object.values(meshes).flat().filter((m) => m.visible), false);
    const name = hits.length ? hits[0].object.userData.part : null;
    listeners.forEach((f) => f(name));
  });

  function resize() {
    const w = container.clientWidth, h = container.clientHeight;
    renderer.setSize(w, h, false);
    renderer.domElement.style.width = w + 'px';
    renderer.domElement.style.height = h + 'px';
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  new ResizeObserver(resize).observe(container);
  resize();

  camera.position.set(300, 250, 390);
  controls.target.set(0, 40, 0);

  renderer.setAnimationLoop(() => {
    if (explodeAnim) {
      const k = Math.min(1, (performance.now() - explodeAnim.t0) / 700);
      const ease = k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
      state.explode = explodeAnim.from + (explodeAnim.to - explodeAnim.from) * ease;
      apply();
      if (k >= 1) explodeAnim = null;
    }
    controls.update();
    renderer.render(scene, camera);
  });

  return { ready, setState, onPick: (f) => listeners.push(f), get explode() { return state.explode; }, get tilt() { return state.tilt; }, get focus() { return state.focus; }, get beam() { return state.beam; }, get flip() { return state.flip; } };
}
