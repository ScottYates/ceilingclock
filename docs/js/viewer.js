import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { PARTS, ALL } from './parts.js?v=20261030d';

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
        if (!o.isMesh || !PARTS[o.name]) return;
        const p = PARTS[o.name];
        o.geometry.computeVertexNormals();
        o.material = new THREE.MeshStandardMaterial({
          color: p.color, roughness: 0.6, metalness: 0.05,
          transparent: !!p.opacity, opacity: p.opacity ?? 1,
        });
        o.userData.base = o.position.clone();
        meshes[o.name] = o;
      });
      root.add(gltf.scene);  // vertices are raw OpenSCAD mm, z up; root rotates them to y-up
      apply();
      resolve();
    }, undefined, reject);
  });

  function apply() {
    const hl = new Set(state.highlight);
    for (const [name, m] of Object.entries(meshes)) {
      const p = PARTS[name];
      m.visible = state.visible.includes(name);
      const e = p.explode;
      m.position.set(m.userData.base.x + e[0] * state.explode, m.userData.base.y + e[1] * state.explode, m.userData.base.z + e[2] * state.explode);
      const dim = hl.size > 0 && !hl.has(name);
      m.material.color.setHex(dim ? 0xc9c5bc : p.color);
      m.material.transparent = dim || !!p.opacity;
      m.material.opacity = dim ? 0.28 : (p.opacity ?? 1);
      m.material.depthWrite = !dim;
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
    const hits = ray.intersectObjects(Object.values(meshes).filter((m) => m.visible), false);
    const name = hits.length ? hits[0].object.name : null;
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

  camera.position.set(400, 380, 600);
  controls.target.set(0, 130, 0);

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
