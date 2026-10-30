// Projector optics for the 3D view (the live demo has the same numbers in demo/sim.js).
// 100 mm lens, 106 mm from the LCD at nominal focus; focusMm moves the lens away from the LCD.
export const LENS = { f: 100, nominal: 106, aperture: 46, rL: 47, pixel: 0.36, lcdW: 30, lcdH: 17 };
export const CEILING = 1800;   // lens to ceiling, mm (8 ft ceiling, clock on a nightstand)

export function optics(focusMm, tiltDeg, ceiling = CEILING) {
  const v = LENS.nominal + focusMm;
  const sharpAt = 1 / (1 / LENS.f - 1 / v);
  const t = tiltDeg * Math.PI / 180;
  const D = ceiling / Math.cos(t);
  const blurMm = LENS.aperture * Math.abs(D - sharpAt) / sharpAt;
  const pixelMm = LENS.pixel * D / v;
  return { v, sharpAt, D, blurMm, blurPx: blurMm / pixelMm, forward: ceiling * Math.tan(t), width: LENS.lcdW * D / v, height: LENS.lcdH * D / v,
           verdict: blurMm / pixelMm < 0.5 ? 'sharp' : blurMm / pixelMm < 1.5 ? 'slightly soft' : 'blurry' };
}
