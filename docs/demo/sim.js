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
  // ---- the one thing the page supplies besides the clock itself: web requests for podcast feeds
  const env = {
    // the firmware reads a podcast feed: a synchronous request, so the browser's cross-origin
    // rules apply (the real clock has no such limit). Anything that doesn't look like a feed is
    // left to the player, so a radio stream is never downloaded here.
    js_http_get: (u, buf, max) => {
      const url = cstrAt(u);
      if (!/rss|feed|xml|podcast|atom/i.test(url)) return 0;
      try {
        const x = new XMLHttpRequest();
        x.open('GET', url, false);
        x.overrideMimeType('text/plain; charset=x-user-defined');
        x.send();
        if (x.status !== 200) return -1;
        const t = x.responseText, n = Math.min(t.length, max), m = mem();
        for (let i = 0; i < n; i++) m[buf + i] = t.charCodeAt(i) & 255;
        return n;
      } catch (e) { note('Your browser blocked reading that feed (it only lets a page read other sites that allow it). The real clock reads any feed. In the demo, try the sample podcast, or a direct MP3 or radio stream URL.'); return -1; }
    },
  };
  const cstrAt = (p) => { let e = p; const m = mem(); while (m[e]) e++; return td.decode(m.slice(p, e)); };

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
    setVisitorTimeZone();
    setInterval(() => X.sim_loop(4), 25);       // the firmware's loop(), ~160 times a second
  })();
  window.__simReady = ready;

  // ---- the demo starts in the visitor's time zone. The firmware works out local time itself, with the
  // ESP32's own date code, from its time zone setting (a POSIX TZ string), exactly as the real clock does.
  const NAMED_TZ = {
    'EST5EDT,M3.2.0,M11.1.0': ['America/New_York', 'America/Detroit', 'America/Toronto', 'America/Indiana/Indianapolis', 'America/Kentucky/Louisville'],
    'CST6CDT,M3.2.0,M11.1.0': ['America/Chicago', 'America/Winnipeg', 'America/Menominee', 'America/Indiana/Knox'],
    'MST7MDT,M3.2.0,M11.1.0': ['America/Denver', 'America/Edmonton', 'America/Boise'],
    'MST7': ['America/Phoenix'],
    'PST8PDT,M3.2.0,M11.1.0': ['America/Los_Angeles', 'America/Vancouver'],
    'AKST9AKDT,M3.2.0,M11.1.0': ['America/Anchorage', 'America/Juneau'],
    'HST10': ['Pacific/Honolulu'],
    'GMT0BST,M3.5.0/1,M10.5.0': ['Europe/London', 'Europe/Dublin'],
    'CET-1CEST,M3.5.0,M10.5.0/3': ['Europe/Paris', 'Europe/Berlin', 'Europe/Madrid', 'Europe/Rome', 'Europe/Amsterdam', 'Europe/Brussels',
      'Europe/Vienna', 'Europe/Stockholm', 'Europe/Oslo', 'Europe/Copenhagen', 'Europe/Warsaw', 'Europe/Prague', 'Europe/Zurich', 'Europe/Budapest'],
    'EET-2EEST,M3.5.0/3,M10.5.0/4': ['Europe/Athens', 'Europe/Helsinki', 'Europe/Kyiv', 'Europe/Kiev', 'Europe/Bucharest', 'Europe/Sofia',
      'Europe/Riga', 'Europe/Tallinn', 'Europe/Vilnius'],
    'UTC0': ['UTC', 'Etc/UTC'],
  };
  function browserPosixTz() {
    let name = '';
    try { name = Intl.DateTimeFormat().resolvedOptions().timeZone; } catch (e) {}
    for (const [tz, names] of Object.entries(NAMED_TZ)) if (names.includes(name)) return tz;
    // Any other zone: this year's offsets and changeovers, written as a POSIX rule.
    const east = (ms) => -new Date(ms).getTimezoneOffset();   // minutes east of UTC
    const y = new Date().getFullYear(), t0 = Date.UTC(y, 0, 1), H = 3600000;
    const changes = [];
    for (let t = t0; t < Date.UTC(y + 1, 0, 1); t += H) {
      if (east(t + H) === east(t)) continue;
      let lo = t, hi = t + H;                                   // the minute it changes
      while (hi - lo > 60000) { const m = lo + Math.floor((hi - lo) / 120000) * 60000; if (east(m) === east(t)) lo = m; else hi = m; }
      changes.push({ at: hi, from: east(t), to: east(hi) });
    }
    const off = (m) => { const p = -m, a = Math.abs(p); return (p < 0 ? '-' : '') + Math.floor(a / 60) + (a % 60 ? ':' + String(a % 60).padStart(2, '0') : ''); };
    if (changes.length !== 2) return 'STD' + off(east(Date.now()));
    const rule = (c) => {                                       // as local time before the change: Mm.w.d/hh:mm
      const w = new Date(c.at + c.from * 60000), d = w.getUTCDate();
      const last = new Date(Date.UTC(w.getUTCFullYear(), w.getUTCMonth() + 1, 0)).getUTCDate();
      const week = d + 7 > last ? 5 : Math.ceil(d / 7);
      return `M${w.getUTCMonth() + 1}.${week}.${w.getUTCDay()}/${w.getUTCHours()}:${String(w.getUTCMinutes()).padStart(2, '0')}`;
    };
    const [on, offc] = changes[0].to > changes[0].from ? changes : [changes[1], changes[0]];
    return `STD${off(on.from)}DST${off(on.to)},${rule(on)},${rule(offc)}`;
  }
  function setVisitorTimeZone() {
    const tz = browserPosixTz();
    const cur = request('GET', '/api/config');
    if (cur.code !== 200) return;
    const c = JSON.parse(td.decode(cur.body));
    if (c.tz === tz) return;
    c.tz = tz;
    request('POST', '/api/config', 'application/json', te.encode(JSON.stringify(c)));
  }

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
  function note(t) { const n = document.getElementById('simnote'); if (n) { n.textContent = t; n.style.display = t ? 'block' : 'none'; } }

  // ---- sound: play what the simulated speaker is playing (files from the clock's storage, streams from the web)
  const player = new Audio();
  window.__simPlayer = player;
  let soundOn = true, lastSeq = -1, playingStream = false, needTap = false;
  const blobs = {};
  player.onerror = () => { if (playingStream) request('POST', '/sim/streamfail'); };
  function syncSound(a) {
    if (!soundOn || !a.playing) { if (!player.paused) player.pause(); return; }
    player.volume = Math.min(1, a.vol / 21);
    if (a.seq !== lastSeq) {
      lastSeq = a.seq;
      playingStream = !!a.url;
      if (a.url) player.src = a.url;
      else {
        if (!blobs[a.file]) { const r = request('GET', '/sim/file?path=' + encodeURIComponent(a.file)); blobs[a.file] = URL.createObjectURL(new Blob([r.body], { type: r.type })); }
        player.src = blobs[a.file];
      }
      player.play().then(() => { needTap = false; note(''); }).catch(() => { needTap = true; note('Click anywhere on the page to let it play sound.'); });
    } else if (player.paused && !needTap) player.play().catch(() => {});
  }
  document.addEventListener('click', () => { if (needTap && soundOn) { needTap = false; player.play().then(() => note('')).catch(() => {}); } }, true);

  // ---- projector optics: how sharp and where the time lands for a given focus and tilt (100 mm lens)
  function optics(focusMm, tiltDeg) {
    const v = 106 + focusMm;                          // lens to the projector's LED display
    const sharpAt = 1 / (1 / 100 - 1 / v);            // where the image is sharp, mm
    const D = 1800 / Math.cos(tiltDeg * Math.PI / 180);   // lens to ceiling along the beam (8 ft ceiling)
    const blur = 46 * Math.abs(D - sharpAt) / sharpAt;    // blur spot on the ceiling, mm
    const pixel = 1.0 * D / v;                            // one segment's stroke (about 1 mm) on the ceiling, mm
    return { sharpAt, D, blurPx: blur / pixel, forward: 1800 * Math.tan(tiltDeg * Math.PI / 180), width: 30 * D / v };
  }
  let focus = 0, tilt = 0;
  function applyOptics() {
    const o = optics(focus, tilt), c = document.getElementById('ceil');
    if (c) {
      c.style.filter = o.blurPx > 0.25 ? `blur(${Math.min(14, o.blurPx * 1.6).toFixed(1)}px)` : '';
      c.style.transform = tilt ? `perspective(520px) rotateX(${(-tilt * 0.9).toFixed(1)}deg)` : '';
    }
    const q = o.blurPx < 0.5 ? 'sharp' : o.blurPx < 1.5 ? 'slightly soft' : 'blurry';
    document.getElementById('simoptics').textContent = `Sharp at ${(o.sharpAt / 1000).toFixed(2)} m, ceiling ${(o.D / 1000).toFixed(2)} m away: ${q}. ` +
      `Image ${Math.round(o.width / 10)} cm wide` + (tilt ? `, ${Math.round(o.forward / 10)} cm forward.` : '.');
  }
  async function useSample() {
    await ready;
    const c = JSON.parse(td.decode(request('GET', '/api/config').body));
    const url = new URL('sample-feed.xml', location.href).href;
    if (!c.alarms.length) c.alarms.push({ enabled: true, hour: 7, minute: 0, days: 62, skipNext: false, label: 'Podcast', sound: '/sounds/beep.wav', volume: 12, rampSec: 10, snoozeMin: 9, maxRingMin: 30 });
    c.alarms[0].stream = url;
    request('POST', '/api/config', 'application/json', te.encode(JSON.stringify(c)));
    if (typeof load === 'function') await load();
    note('Alarm 1 now plays the sample podcast. Open it and press "Ring now", or fast-forward to its time.');
  }
  async function forward(seconds) {
    await ready;
    // move in steps of 2.5 minutes: the firmware treats bigger jumps as a clock correction and
    // would not fire an alarm that falls inside the jump
    for (let left = seconds; left > 0; left -= 150) { request('POST', '/sim/time?add=' + Math.min(150, left)); X.sim_loop(3); }
  }
  // the front display: four TM1637 segment bytes (bit 0x80 of digit 2 is the colon)
  // Unlit segments are barely visible, as on a real module.
  function segs(g, col) {
    const off = '#130808';
    const P = [[4, 0, 26, 5], [27, 3, 5, 22], [27, 30, 5, 22], [4, 51, 26, 5], [0, 30, 5, 22], [0, 3, 5, 22], [4, 25.5, 26, 5]];
    const dig = (x, m) => P.map((p, i) => `<rect x="${x + p[0]}" y="${4 + p[1]}" width="${p[2]}" height="${p[3]}" rx="2" fill="${(m >> i) & 1 ? col : off}"/>`).join('');
    return dig(14, g[0]) + dig(52, g[1]) + `<circle cx="99" cy="22" r="3" fill="${g[1] & 0x80 ? col : off}"/><circle cx="99" cy="40" r="3" fill="${g[1] & 0x80 ? col : off}"/>` + dig(114, g[2]) + dig(152, g[3]);
  }
  function controls() {
    const css = document.createElement('style');
    css.textContent = `#simintro{background:#1f2a1f;border-bottom:1px solid #345234;color:#d9f2d9;font:13px/1.45 system-ui,sans-serif}
#simintro .in{max-width:640px;margin:auto;padding:8px 12px;display:flex;gap:10px;align-items:flex-start}#simintro b{color:#fff}
#simintro .txt{flex:1}#simintro.hidden .txt .more{display:none}
#simintro button{flex:none;background:#2f4a2f;color:#e8ffe8;border:1px solid #446a44;border-radius:7px;padding:3px 9px;font:600 13px system-ui,sans-serif;cursor:pointer}
#simbar{position:fixed;left:0;right:0;bottom:0;z-index:50;background:#182418;border-top:1px solid #345234;color:#d9f2d9;font:13px/1.4 system-ui,sans-serif;box-shadow:0 -6px 20px rgba(0,0,0,.45)}
#simbar .in{max-width:640px;margin:auto;padding:6px 12px 8px}
#simbar .hd{display:flex;align-items:center;gap:10px;color:#cfeccf;font-weight:600;padding:2px 0}
#simbar .hd #simtoggle{margin-left:8px;font-weight:600}
#simbar.hidden .body{display:none}
#simbar .body{max-height:50vh;overflow-y:auto;overscroll-behavior:contain}
#simbar .srow{display:flex;gap:5px;flex-wrap:wrap;align-items:center;margin-top:5px}
#simbar .srow>span:first-child{min-width:74px;color:#a8d8a8}
#simbar button{background:#2f4a2f;color:#e8ffe8;border:1px solid #446a44;border-radius:7px;padding:5px 8px;font:inherit;cursor:pointer}
#simbar button:active{background:#467046}#simbar input{accent-color:#7cc47c;width:120px}
#simbar .simled{display:inline-block;width:9px;height:9px;border-radius:50%;background:#203020;margin-right:6px;vertical-align:0}#simbar .simled.on{background:#7dff6a;box-shadow:0 0 8px #7dff6a}
#simbar .hint{color:#a8d8a8;font-size:12px}#simbar .srow b{color:#fff}#simfront{background:#070404;border-radius:5px;padding:2px 4px}
#simclock{margin-left:auto;font-variant-numeric:tabular-nums;color:#a8d8a8;font-weight:400}`;
    document.head.appendChild(css);
    const intro = document.createElement('div'); intro.id = 'simintro';
    intro.innerHTML = `<div class="in"><div class="txt"><b>Live demo</b><span class="more">: the real clock firmware, running in your browser (WebAssembly). Nothing touches a real clock, and everything resets when you reload. Use the controls at the bottom to fast-forward time and press the clock's buttons. Try: press <b>Alarm 1</b> below and watch the front display in the controls and the switch on the page, or set an alarm a few minutes ahead and press +1 min. Sounds really play. "Use sample podcast" makes the first alarm play a podcast; switch the internet off to hear the backup sound take over.</span></div><button id="simintrotoggle" aria-expanded="true">Hide</button></div>`;
    {
      const setIntro = (h) => {
        intro.classList.toggle('hidden', h);
        const t = intro.querySelector('#simintrotoggle');
        t.textContent = h ? 'Show' : 'Hide'; t.setAttribute('aria-expanded', String(!h));
        try { localStorage.setItem('ceilingclock-demo-intro', h ? 'hidden' : 'shown'); } catch (e) {}
      };
      intro.querySelector('#simintrotoggle').onclick = () => setIntro(!intro.classList.contains('hidden'));
      let h = false; try { h = localStorage.getItem('ceilingclock-demo-intro') === 'hidden'; } catch (e) {}
      setIntro(h);
    }
    document.body.prepend(intro);
    const bar = document.createElement('div'); bar.id = 'simbar';
    bar.innerHTML = `<div class="in"><div class="hd">Simulator controls <span id="simclock"></span><button id="simtoggle" aria-expanded="true">Hide</button></div><div class="body">
<div class="srow"><span>Time</span><button data-f="60">+1 min</button><button data-f="600">+10 min</button><button data-f="3600">+1 hour</button></div>
<div class="srow"><span>Front display</span><svg id="simfront" viewBox="0 0 200 60" width="160" height="48" role="img" aria-label="Front display"></svg><span id="simdisp" class="hint"></span></div>
<div class="srow"><span>Alarm buttons</span><button data-b="1&ms=150"><i class="simled" id="simled0"></i>Alarm 1: <b id="simal0">off</b></button><button data-b="2&ms=150"><i class="simled" id="simled1"></i>Alarm 2: <b id="simal1">off</b></button></div>
<div class="srow"><span></span><span class="hint">Press: switch that alarm on (front display: 1 on, then its time) or off (1 oF). While an alarm rings: stop it. Holding longer does the same as a press. The dot is the button's light: like on the real clock, it lights only for a moment after a change, while that alarm rings, or when you press Snooze.</span></div>
<div class="srow"><span>Snooze (top)</span><button data-b="A&ms=150">Press</button><button data-b="A&ms=2300">Hold 2 s</button></div>
<div class="srow"><span></span><span class="hint">While ringing: press snoozes (SnoZ, then when it rings again); hold 2 s stops (StoP). Otherwise a press shows which alarms are on (AL12, AL1-, AL-2, AL--) and the time on the ceiling.</span></div>
<div class="srow"><span>Side button</span><button data-b="B&ms=150">Press</button><button data-b="B&ms=3300">Hold 3 s</button></div>
<div class="srow"><span></span><span class="hint">Press: front display on or off (d on / d oF). Hold 3 s: ceiling projection on or off (P on / P oF). On the real clock, holding on to 10 s forgets the Wi-Fi and restarts in setup mode (rSEt).</span></div>
<div class="srow"><span>Room light</span>dark <input type="range" min="0" max="4095" value="2000" id="simldr"> bright</div>
<div class="srow"><span>Internet</span><button id="simnet">On</button><label style="display:inline-flex;gap:4px;align-items:center"><input type="checkbox" id="simsound" checked style="width:auto;margin:0"> Play sounds</label><button id="simsample">Use sample podcast</button></div>
<div class="srow"><span>Lens focus</span>down <input type="range" min="-5" max="5" step="0.5" value="0" id="simfocus"> up</div>
<div class="srow"><span>Tilt</span>-5° <input type="range" min="-5" max="30" step="5" value="0" id="simtilt"> 30° <b id="simtiltv" style="color:#e8ffe8">0°</b></div>
<div class="srow" style="color:#a8d8a8" id="simoptics"></div>
<div id="simnote" style="display:none;margin-top:6px;color:#ffe2a8"></div>
</div></div>`;
    document.body.appendChild(bar);
    // Hide/show the controls; the page keeps just enough room at the bottom to scroll everything above the bar
    const fit = () => { document.body.style.paddingBottom = (bar.offsetHeight + 16) + 'px'; };
    const setHidden = (h) => {
      bar.classList.toggle('hidden', h);
      const t = bar.querySelector('#simtoggle');
      t.textContent = h ? 'Show' : 'Hide'; t.setAttribute('aria-expanded', String(!h));
      try { localStorage.setItem('ceilingclock-demo-bar', h ? 'hidden' : 'shown'); } catch (e) {}
      fit();
    };
    bar.querySelector('#simtoggle').onclick = () => setHidden(!bar.classList.contains('hidden'));
    let startHidden = false;
    try { startHidden = localStorage.getItem('ceilingclock-demo-bar') === 'hidden'; } catch (e) {}
    setHidden(startHidden);
    if (window.ResizeObserver) new ResizeObserver(fit).observe(bar); else window.addEventListener('resize', fit);
    bar.querySelectorAll('[data-f]').forEach((b) => b.onclick = () => forward(+b.dataset.f));
    // Presses queue up so quick double presses both count; the page catches up right after each one
    let presses = Promise.resolve();
    bar.querySelectorAll('[data-b]').forEach((b) => b.onclick = () => {
      const ms = +(b.dataset.b.split('ms=')[1] || 150);
      presses = presses.then(async () => {
        await sim('/sim/button?b=' + b.dataset.b);
        await new Promise((r) => setTimeout(r, ms + 80));
        if (typeof window.poll === 'function') window.poll();
      });
    });
    bar.querySelector('#simldr').oninput = (e) => sim('/sim/ldr?v=' + e.target.value);
    let netOn = true;
    bar.querySelector('#simnet').onclick = (e) => { netOn = !netOn; e.target.textContent = netOn ? 'On' : 'Off (test the backup sound)'; sim('/sim/net?ok=' + (netOn ? 1 : 0)); };
    bar.querySelector('#simsound').onchange = (e) => { soundOn = e.target.checked; if (!soundOn) player.pause(); else lastSeq = -1; };
    bar.querySelector('#simsample').onclick = useSample;
    bar.querySelector('#simfocus').oninput = (e) => { focus = +e.target.value; applyOptics(); };
    bar.querySelector('#simtilt').oninput = (e) => { tilt = +e.target.value; document.getElementById('simtiltv').textContent = tilt + '°'; applyOptics(); };
    applyOptics();
    setInterval(async () => {
      await ready;
      const h = JSON.parse(td.decode(request('GET', '/sim/hw').body));
      syncSound(h.audio);
      (h.alarmLeds || []).forEach((v, i) => { const e = document.getElementById('simled' + i); if (e) e.classList.toggle('on', v > 0); });
      if (h.front) {
        const col = `rgba(255,74,53,${0.6 + 0.4 * h.front.bright / 7})`;  // dimmer at low brightness, never muddy
        document.getElementById('simfront').innerHTML = segs(h.front.on ? h.front.segs : [0, 0, 0, 0], col);
        document.getElementById('simdisp').textContent = h.front.on ? '' : 'off (dark)';
      }
      try {
        const st = JSON.parse(td.decode(request('GET', '/api/state').body));
        for (let i = 0; i < 2; i++) { const e = document.getElementById('simal' + i); if (e) e.textContent = st.alarmsOn >> i & 1 ? 'on' : 'off'; }
      } catch (e) {}
      const d = new Date(h.time * 1000), ahead = h.timeOffset;
      document.getElementById('simclock').textContent = '· clock ' + d.toLocaleString([], { weekday: 'short', hour: 'numeric', minute: '2-digit' }) +
        (ahead ? ' (+' + Math.round(ahead / 60) + ' min)' : '');
    }, 200);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', controls); else controls();
})();
