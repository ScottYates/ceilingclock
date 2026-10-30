import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { PARTS, ALL, MATERIALS } from './parts.js?v=20261030p';

// createViewer(container) -> { ready: Promise, setState({visible, highlight, explode, camera, target}), onPick }
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

  const meshes = {};
  const state = { visible: ALL, highlight: [], explode: 0 };
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
        m.position.set(m.userData.base.x + e[0] * state.explode, m.userData.base.y + e[1] * state.explode, m.userData.base.z + e[2] * state.explode);
        m.material.color.setHex(dim ? 0xc9c5bc : mt.color);
        m.material.emissive.setHex(dim ? 0x000000 : (mt.emissive ?? 0x000000));
        m.material.transparent = dim || !!mt.opacity;
        m.material.opacity = dim ? 0.28 : (mt.opacity ?? 1);
        m.material.depthWrite = !dim && !mt.opacity;
      }
    }
  }

  function setState(s = {}) {
    if (s.visible) state.visible = s.visible;
    if (s.highlight) state.highlight = s.highlight;
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

  return { ready, setState, onPick: (f) => listeners.push(f), get explode() { return state.explode; } };
}
