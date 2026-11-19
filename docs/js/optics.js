// Projector optics for the 3D view (the live demo has the same numbers in demo/sim.js).
// 121 mm lens (Scott's measured), 130 mm from the projector display at nominal focus; focusMm moves the lens away from it.
// stroke: width of one lit segment (mm), the detail that has to stay sharp. dispW x dispH: the display's face.
export const LENS = { f: 121, nominal: 130, aperture: 45, rL: 78, stroke: 1.0, dispW: 30.2, dispH: 14.2, x: 34, pitch: 3 };
export const CEILING = 1800;   // lens to ceiling, mm (8 ft ceiling, clock on a nightstand)

export function optics(focusMm, tiltDeg, ceiling = CEILING) {
  const v = LENS.nominal + focusMm;
  const sharpAt = 1 / (1 / LENS.f - 1 / v);
  const t = tiltDeg * Math.PI / 180;
  const D = ceiling / Math.cos(t);
  const blurMm = LENS.aperture * Math.abs(D - sharpAt) / sharpAt;
  const pixelMm = LENS.stroke * D / v;
  return { v, sharpAt, D, blurMm, blurPx: blurMm / pixelMm, forward: ceiling * Math.tan(t), width: LENS.dispW * D / v, height: LENS.dispH * D / v,
           verdict: blurMm / pixelMm < 0.5 ? 'sharp' : blurMm / pixelMm < 1.5 ? 'slightly soft' : 'blurry' };
}
