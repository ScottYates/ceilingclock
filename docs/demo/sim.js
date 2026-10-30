// Runs the Ceiling Clock firmware (compiled to WebAssembly) inside this page.
// Every fetch() the clock's own web page makes to /api/... is answered by the firmware
// in WebAssembly instead of a real clock on the network.
(() => {
  const te = new TextEncoder(), td = new TextDecoder();
  let X = null;                       // wasm exports
  const mem = () => new Uint8Array(X.memory.buffer);
  const dv = () => new DataView(X.memory.buffer);
  let out = '';

  // ---- the handful of WASI functions the firmware uses (clock, console output)
  const wasi = {
    environ_sizes_get: (c, s) => { dv().setUint32(c, 0, true); dv().setUint32(s, 0, true); return 0; },
    environ_get: () => 0,
    clock_time_get: (id, _prec, ptr) => {
      const ns = id === 0 ? BigInt(Date.now()) * 1000000n : BigInt(Math.round(performance.now() * 1e6));
      dv().setBigUint64(ptr, ns, true); return 0;
    },
    fd_close: () => 0,
    fd_seek: () => 70,
    fd_fdstat_get: (fd, p) => { const d = dv(); d.setUint8(p, 2); d.setUint16(p + 2, 0, true); d.setBigUint64(p + 8, 0n, true); d.setBigUint64(p + 16, 0n, true); return 0; },
    fd_write: (fd, iovs, n, nw) => {
      const d = dv(); let total = 0;
      for (let i = 0; i < n; i++) {
        const p = d.getUint32(iovs + i * 8, true), l = d.getUint32(iovs + i * 8 + 4, true);
        out += td.decode(mem().subarray(p, p + l)); total += l;
      }
      let k; while ((k = out.indexOf('\n')) >= 0) { console.log('[clock]', out.slice(0, k)); out = out.slice(k + 1); }
      d.setUint32(nw, total, true); return 0;
    },
    proc_exit: (c) => { throw new Error('firmware stopped (' + c + ')'); },
  };
  // ---- local time from the browser's time zone
  const env = {
    js_local_offset: (t) => -new Date(t * 1000).getTimezoneOffset(),
    js_std_offset: (t) => { const y = new Date(t * 1000).getFullYear(); return Math.min(-new Date(y, 0, 1).getTimezoneOffset(), -new Date(y, 6, 1).getTimezoneOffset()); },
    js_mktime: (y, mo, d, h, mi, s) => new Date(y, mo, d, h, mi, s).getTime() / 1000,
  };

  const cstr = (s) => { const b = te.encode(s + '\0'), p = X.sim_alloc(b.length); mem().set(b, p); return p; };
  let auth = '';
  function request(method, target, ctype = '', body = new Uint8Array()) {
    const a = [cstr(method), cstr(target), cstr(ctype), cstr(auth)];
    const bp = X.sim_alloc(Math.max(1, body.length)); mem().set(body, bp);
    const code = X.sim_request(a[0], a[1], a[2], bp, body.length, a[3]);
    let tp = X.sim_resp_type(), te0 = tp; while (mem()[te0]) te0++;
    const type = td.decode(mem().slice(tp, te0));
    const rp = X.sim_resp_body(), rl = X.sim_resp_len();
    const resp = mem().slice(rp, rp + rl);
    a.forEach(X.sim_free); X.sim_free(bp);
    return { code, type, body: resp };
  }

  const ready = (async () => {
    const r = await fetch(new URL('ceilingclock.wasm', document.currentScript ? document.currentScript.src : location.href));
    const { instance } = await WebAssembly.instantiate(await r.arrayBuffer(), { wasi_snapshot_preview1: wasi, env });
    X = instance.exports;
    X._initialize();
    X.sim_setup();
    X.sim_loop(3);                              // first loop() passes start the web server, as on the clock
    setInterval(() => X.sim_loop(4), 25);       // the firmware's loop(), ~160 times a second
  })();
  window.__simReady = ready;

  // ---- answer the page's requests from the firmware
  const realFetch = window.fetch.bind(window);
  window.fetch = async (input, init) => {
    const req = new Request(input, init);
    const url = new URL(req.url);
    if (url.origin !== location.origin || !/^\/(api\/|update$|sim\/)/.test(url.pathname)) return realFetch(input, init);
    await ready;
    const body = new Uint8Array(await req.arrayBuffer());
    let res = request(req.method, url.pathname + url.search, req.headers.get('content-type') || '', body);
    if (res.code === 401) {   // a web password was set: ask like a browser would
      const pw = prompt('This clock has a web password. User is "admin". Password:');
      if (pw !== null) { auth = 'Basic ' + btoa('admin:' + pw); res = request(req.method, url.pathname + url.search, req.headers.get('content-type') || '', body); }
    }
    return new Response(res.body, { status: res.code, headers: { 'Content-Type': res.type || 'text/plain' } });
  };

  // ---- demo controls: fast-forward time, press the clock's buttons, change room light
  async function sim(path) { await ready; return request('POST', path); }
  async function forward(seconds) {
    await ready;
    // move in steps of 2.5 minutes: the firmware treats bigger jumps as a clock correction and
    // would not fire an alarm that falls inside the jump
    for (let left = seconds; left > 0; left -= 150) { request('POST', '/sim/time?add=' + Math.min(150, left)); X.sim_loop(3); }
  }
  function controls() {
    const css = document.createElement('style');
    css.textContent = `#simintro{background:#1f2a1f;border-bottom:1px solid #345234;color:#d9f2d9;font:13px/1.45 system-ui,sans-serif}
#simintro div{max-width:640px;margin:auto;padding:8px 12px}#simintro b{color:#fff}
#simbar{position:fixed;left:0;right:0;bottom:0;z-index:50;background:rgba(24,36,24,.97);border-top:1px solid #345234;color:#d9f2d9;font:13px/1.4 system-ui,sans-serif;box-shadow:0 -6px 20px rgba(0,0,0,.45)}
#simbar .in{max-width:640px;margin:auto;padding:6px 12px 8px}
#simbar summary{cursor:pointer;color:#cfeccf;font-weight:600;padding:2px 0;list-style-position:inside}
#simbar .row{display:flex;gap:5px;flex-wrap:wrap;align-items:center;margin-top:5px}
#simbar .row>span:first-child{min-width:74px;color:#a8d8a8}
#simbar button{background:#2f4a2f;color:#e8ffe8;border:1px solid #446a44;border-radius:7px;padding:5px 8px;font:inherit;cursor:pointer}
#simbar button:active{background:#467046}#simbar input{accent-color:#7cc47c;width:120px}
#simclock{margin-left:auto;font-variant-numeric:tabular-nums;color:#a8d8a8;font-weight:400}
body{padding-bottom:190px}`;
    document.head.appendChild(css);
    const intro = document.createElement('div'); intro.id = 'simintro';
    intro.innerHTML = `<div><b>Live demo:</b> the real clock firmware, running in your browser (WebAssembly). Nothing touches a real clock, and everything resets when you reload. Use the controls at the bottom to fast-forward time and press the clock's buttons. Try: turn on an alarm a few minutes ahead, Save, then press +1 min and watch "Right now".</div>`;
    document.body.prepend(intro);
    const bar = document.createElement('div'); bar.id = 'simbar';
    bar.innerHTML = `<div class="in"><details open><summary>Simulator controls <span id="simclock"></span></summary>
<div class="row"><span>Time</span><button data-f="60">+1 min</button><button data-f="600">+10 min</button><button data-f="3600">+1 hour</button></div>
<div class="row"><span>Top button</span><button data-b="A&ms=150">Press</button><button data-b="A&ms=2300">Hold 2 s</button></div>
<div class="row"><span>Back button</span><button data-b="B&ms=150">Press</button><button data-b="B&ms=3300">Hold 3 s</button></div>
<div class="row"><span>Room light</span>dark <input type="range" min="0" max="4095" value="2000" id="simldr"> bright</div>
</details></div>`;
    document.body.appendChild(bar);
    bar.querySelectorAll('[data-f]').forEach((b) => b.onclick = () => forward(+b.dataset.f));
    bar.querySelectorAll('[data-b]').forEach((b) => b.onclick = () => sim('/sim/button?b=' + b.dataset.b));
    bar.querySelector('#simldr').oninput = (e) => sim('/sim/ldr?v=' + e.target.value);
    const det = bar.querySelector('details');
    det.addEventListener('toggle', () => { document.body.style.paddingBottom = det.open ? '190px' : '44px'; });
    setInterval(async () => {
      await ready;
      const h = JSON.parse(td.decode(request('GET', '/sim/hw').body));
      const d = new Date(h.time * 1000), ahead = h.timeOffset;
      document.getElementById('simclock').textContent = '· clock ' + d.toLocaleString([], { weekday: 'short', hour: 'numeric', minute: '2-digit' }) +
        (ahead ? ' (+' + Math.round(ahead / 60) + ' min)' : '');
    }, 1000);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', controls); else controls();
})();
