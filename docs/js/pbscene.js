// Studio scene for the perfboard pictures and the 3D view on perfboard.html: soft room lighting, a key light
// with soft shadows, and a green self-healing cutting mat with a 10 mm grid. Models are in mm, z up (as built
// by hardware/pb_model.py); they are turned here so z is three.js's y.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

export const v = (x, y, z) => new THREE.Vector3(x, z, -y);       // model mm (z up) -> three

function matTexture() {
  const c = document.createElement('canvas'); c.width = c.height = 2048;
  const g = c.getContext('2d');
  g.fillStyle = '#2a5444'; g.fillRect(0, 0, 2048, 2048);
  const px = 2048 / 200;                                    // the canvas is 200 mm square
  for (let mm = 0; mm <= 200; mm += 10) {
    const major = mm % 50 === 0;
    g.strokeStyle = major ? 'rgba(220,235,225,.30)' : 'rgba(210,230,220,.13)';
    g.lineWidth = major ? 2.4 : 1.4;
    g.beginPath(); g.moveTo(mm * px, 0); g.lineTo(mm * px, 2048); g.stroke();
    g.beginPath(); g.moveTo(0, mm * px); g.lineTo(2048, mm * px); g.stroke();
  }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(3, 3); t.anisotropy = 8;
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

export function makeStudio(canvas, { width, height, preserve = false, shadows = true } = {}) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: preserve });
  renderer.setPixelRatio(1);
  renderer.setSize(width, height, false);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.shadowMap.enabled = shadows;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#e9e6df');
  const pm = new THREE.PMREMGenerator(renderer);
  scene.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 0.75;

  const key = new THREE.DirectionalLight('#fff6ea', 2.2);
  key.position.copy(v(-60, -90, 160)); key.target.position.copy(v(35, 20, 0));
  key.castShadow = shadows;
  key.shadow.mapSize.set(4096, 4096);
  Object.assign(key.shadow.camera, { left: -130, right: 130, top: 130, bottom: -130, near: 10, far: 500 });
  key.shadow.bias = -0.0004; key.shadow.normalBias = 0.04; key.shadow.radius = 4;
  scene.add(key, key.target);
  const fill = new THREE.DirectionalLight('#dfe8ff', 0.55);
  fill.position.copy(v(140, 60, 90)); scene.add(fill);

  const mat = new THREE.Mesh(new THREE.PlaneGeometry(600, 600),
    new THREE.MeshStandardMaterial({ map: matTexture(), roughness: 0.92, metalness: 0 }));
  mat.rotation.x = -Math.PI / 2; mat.receiveShadow = true;
  scene.add(mat);

  const camera = new THREE.PerspectiveCamera(28, width / height, 1, 3000);
  let model = null;
  const loader = new GLTFLoader();

  async function load(url, floorZ = 0) {
    const gltf = await loader.loadAsync(url);
    if (model) scene.remove(model);
    model = gltf.scene;
    model.rotation.x = -Math.PI / 2;                       // z up -> y up
    model.traverse(o => {
      if (o.isMesh) {
        o.castShadow = o.receiveShadow = true;
        const m = o.material; if (m) { m.envMapIntensity = 1; m.side = THREE.FrontSide; }
      }
    });
    scene.add(model);
    mat.position.y = floorZ;
    return model;
  }

  function look(cam, target, fov = 28) {
    camera.fov = fov; camera.position.copy(v(...cam)); camera.lookAt(v(...target)); camera.updateProjectionMatrix();
  }

  function render() { renderer.render(scene, camera); }
  function setModel(m) { if (model && model !== m) scene.remove(model); model = m; }
  return { renderer, scene, camera, load, look, render, mat, key, setModel, get model() { return model; } };
}
