// Keeps text in the wiring drawings clear of wires and of other text.
// For every visible <svg> in the page: a label crossed by a line, or overlapping another label, is moved to the
// nearest free spot close to where it was drawn. Short markings (hole numbers, row letters, pin names, + and -)
// that can't move without losing their meaning are hidden instead when something crosses them.
(function () {
  const SHORT = /^(\d{1,2}|[a-jA-O]|[+−-]|G|5V|3V3|TX|RX|RST|[1-9][A-O])$/;
  const OFFS = [[0, 0]];
  for (const d of [6, 10, 14, 18, 24, 30, 38, 46, 56, 68]) OFFS.push([0, -d], [0, d], [d * 1.5, 0], [-d * 1.5, 0], [d, -d], [-d, -d], [d, d], [-d, d]);

  function mat(el, svg) { return svg.getScreenCTM().inverse().multiply(el.getScreenCTM()); }
  function box(t, svg, dx, dy) {
    const b = t.getBBox(), m = mat(t, svg);
    const pts = [[b.x, b.y], [b.x + b.width, b.y], [b.x, b.y + b.height], [b.x + b.width, b.y + b.height]].map(([x, y]) => {
      const p = svg.createSVGPoint(); p.x = x; p.y = y; return p.matrixTransform(m);
    });
    const xs = pts.map(p => p.x), ys = pts.map(p => p.y);
    return { l: Math.min(...xs) + 0.5 + dx, r: Math.max(...xs) - 0.5 + dx, t: Math.min(...ys) + 0.8 + dy, b: Math.max(...ys) - 0.8 + dy };
  }
  const hit = (a, b) => !(a.r <= b.l || b.r <= a.l || a.b <= b.t || b.b <= a.t);

  function run(svg) {
    if (!svg.getBoundingClientRect().width || svg.dataset.decluttered) return;
    svg.dataset.decluttered = '1';
    const vb = svg.viewBox.baseVal;
    const texts = [...svg.querySelectorAll('text')].filter(t => t.textContent.trim());
    // sample every stroked line, polyline and path into points (svg coordinates)
    const lines = [];
    for (const e of svg.querySelectorAll('line,polyline,path')) {
      const cs = getComputedStyle(e);
      if (!cs.stroke || cs.stroke === 'none' || parseFloat(cs.strokeWidth) <= 0 || cs.display === 'none') continue;
      let L = 0; try { L = e.getTotalLength(); } catch (x) { continue; }
      if (!L) continue;
      const m = mat(e, svg), n = Math.max(2, Math.ceil(L / 2)), w = parseFloat(cs.strokeWidth) / 2, pts = [];
      for (let k = 0; k <= n; k++) pts.push(e.getPointAtLength(L * k / n).matrixTransform(m));
      lines.push({ pts, w: w + 2.5, ends: [pts[0], pts[pts.length - 1]] });
    }
    // small drawn parts (resistors, sensors, capacitors, buttons) are obstacles too; big ones (boards, boxes) and
    // the tiny breadboard holes are not
    const parts = [];
    for (const e of svg.querySelectorAll('rect,circle,ellipse,polygon')) {
      const b = e.getBBox(), a = b.width * b.height;
      if (a < 150 || a > 2500 || getComputedStyle(e).display === 'none') continue;
      const m = mat(e, svg), p1 = svg.createSVGPoint(), p2 = svg.createSVGPoint();
      p1.x = b.x; p1.y = b.y; p2.x = b.x + b.width; p2.y = b.y + b.height;
      const q1 = p1.matrixTransform(m), q2 = p2.matrixTransform(m);
      parts.push({ l: Math.min(q1.x, q2.x), r: Math.max(q1.x, q2.x), t: Math.min(q1.y, q2.y), b: Math.max(q1.y, q2.y) });
    }
    const crosses = (bx) => lines.some(ln => {
      // a line that ends right at the label is its own leader: it may touch the box edge but not run through it
      const own = ln.ends.some(p => p.x > bx.l - 8 && p.x < bx.r + 8 && p.y > bx.t - 8 && p.y < bx.b + 8);
      const pad = own ? -2 : ln.w;
      return ln.pts.some(p => p.x > bx.l - pad && p.x < bx.r + pad && p.y > bx.t - pad && p.y < bx.b + pad);
    });
    const placed = [];
    // long labels first: they get first pick of the free space
    const order = texts.map(t => ({ t, s: t.textContent.trim() })).sort((a, b) => ((SHORT.test(a.s) || a.t.classList.contains('silk')) - (SHORT.test(b.s) || b.t.classList.contains('silk'))) || (b.s.length - a.s.length));
    for (const { t, s } of order) {
      const short = SHORT.test(s) || t.classList.contains('silk');
      const base = box(t, svg, 0, 0);
      const under = parts.filter(p => hit(p, base) && (p.r - p.l) * (p.b - p.t) > (base.r - base.l) * (base.b - base.t) * 1.2);   // a part the label sits on stays allowed
      const cand = short ? [[0, 0]] : OFFS;
      let done = false;
      for (const [dx, dy] of cand) {
        const bx = box(t, svg, dx, dy);
        if (bx.l < vb.x || bx.r > vb.x + vb.width || bx.t < vb.y || bx.b > vb.y + vb.height) continue;
        if (crosses(bx) || placed.some(p => hit(p, bx)) || (!short && parts.some(p => !under.includes(p) && hit(p, bx)))) continue;
        if (dx || dy) t.setAttribute('transform', `translate(${dx} ${dy}) ` + (t.getAttribute('transform') || ''));
        placed.push(bx); done = true; break;
      }
      if (!done) {
        if (short) t.style.display = 'none';
        else placed.push(box(t, svg, 0, 0));          // nothing free nearby: leave it where it was
      }
    }
  }
  function all() { document.querySelectorAll('svg').forEach(run); }
  window.declutterSvgs = all;
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', all); else all();
  // layout switches reveal other drawings: tidy them when they appear
  new MutationObserver(() => requestAnimationFrame(all)).observe(document.documentElement, { attributes: true, subtree: true, attributeFilter: ['class', 'hidden', 'style'] });
})();
