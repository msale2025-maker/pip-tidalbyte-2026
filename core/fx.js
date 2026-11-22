// Pip's little effects. Runs in the main Streamlit page (st.html with
// unsafe_allow_javascript). Python re-sends __SETTINGS__ on every rerun;
// listeners install once, and apply() picks up new settings.
//   - click sounds + haptics, toggle sparkles, Enter-to-send
//   - focus sounds (white noise, rain, birdsong, ocean, music box), synthesised live
//   - Pip: eyes follow the cursor, tap for hearts + a speech pop
//   - tap empty space for a little snow puff
(function () {
  const W = window;
  W.__pipFx = Object.assign(W.__pipFx || {}, __SETTINGS__);
  if (W.__pipFxReady) { if (W.__pipFxApply) W.__pipFxApply(); return; }
  W.__pipFxReady = true;
  const fx = () => W.__pipFx;
  const rand = (a, b) => a + Math.random() * (b - a);
  const pick = (xs) => xs[Math.floor(Math.random() * xs.length)];

  // =============== audio core ===============
  let ctx = null;
  function audio() {
    if (!ctx) {
      const C = W.AudioContext || W.webkitAudioContext;
      if (!C) return null;
      ctx = new C();
    }
    if (ctx.state === "suspended") ctx.resume().then(() => applyAmbient()).catch(() => {});
    return ctx;
  }
  // browsers only allow sound after a user gesture: wake audio on the first one
  ["pointerdown", "keydown"].forEach((t) => document.addEventListener(t, () => { audio(); applyAmbient(); }, { capture: true, passive: true }));

  function tone(f0, f1, dur, type, gain, delay, dest) {
    const c = audio();
    if (!c) return;
    const t = c.currentTime + (delay || 0);
    const o = c.createOscillator(), g = c.createGain();
    o.type = type;
    o.frequency.setValueAtTime(f0, t);
    if (f1) o.frequency.exponentialRampToValueAtTime(f1, t + dur);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(Math.max(gain, 0.0002), t + 0.012);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g).connect(dest || c.destination);
    o.start(t);
    o.stop(t + dur + 0.03);
  }
  const SOUNDS = {
    pop: (v) => { tone(640, 320, 0.11, "sine", 0.32 * v); tone(1280, 900, 0.05, "triangle", 0.06 * v); },
    tick: (v) => tone(1500, 1000, 0.035, "sine", 0.12 * v),
    on: (v) => { tone(784, 0, 0.14, "triangle", 0.2 * v); tone(1175, 0, 0.22, "triangle", 0.18 * v, 0.07); },
    off: (v) => { tone(880, 0, 0.1, "triangle", 0.16 * v); tone(622, 0, 0.16, "triangle", 0.14 * v, 0.06); },
    send: (v) => [784, 988, 1319].forEach((f, i) => tone(f, 0, 0.22, "triangle", 0.16 * v, i * 0.065)),
    pip: (v) => { tone(1900, 2900, 0.07, "sine", 0.22 * v); tone(2100, 3300, 0.08, "sine", 0.2 * v, 0.11); },
    puff: (v) => tone(900, 1800, 0.08, "sine", 0.07 * v),
  };
  function play(name) {
    const s = fx();
    const v = s.sound ? (s.volume || 0) / 100 : 0;
    if (v > 0) try { SOUNDS[name](v); } catch (e) {}
  }
  function buzz(pattern) {
    if (fx().haptics && navigator.vibrate) try { navigator.vibrate(pattern); } catch (e) {}
  }
  const motionOk = () => !fx().still && !W.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // =============== focus sounds ===============
  let bufs = {};
  function noise(c, kind) {
    if (bufs[kind]) return bufs[kind];
    const n = c.sampleRate * 4, b = c.createBuffer(1, n, c.sampleRate), d = b.getChannelData(0);
    let last = 0;
    for (let i = 0; i < n; i++) {
      const w = Math.random() * 2 - 1;
      if (kind === "brown") { last = (last + 0.02 * w) / 1.02; d[i] = last * 3.5; } else d[i] = w;
    }
    return (bufs[kind] = b);
  }
  let amb = null; // current session: {kind, out, nodes, timers}
  function loopSrc(s, buf) {
    const n = s.c.createBufferSource();
    n.buffer = buf; n.loop = true; n.loopStart = 0; n.start(0, Math.random() * 3);
    s.nodes.push(n);
    return n;
  }
  function filt(c, type, f, q) { const x = c.createBiquadFilter(); x.type = type; x.frequency.value = f; if (q) x.Q.value = q; return x; }
  function gainN(c, v) { const g = c.createGain(); g.gain.value = v; return g; }
  function every(s, minMs, maxMs, fn) {
    const go = () => { if (s.dead) return; try { fn(); } catch (e) {} s.timers.push(setTimeout(go, rand(minMs, maxMs))); };
    s.timers.push(setTimeout(go, rand(minMs, maxMs) * 0.3));
  }
  const BUILD = {
    "White noise": (s) => {
      loopSrc(s, noise(s.c, "white")).connect(filt(s.c, "lowpass", 1300)).connect(gainN(s.c, 0.5)).connect(s.out);
      loopSrc(s, noise(s.c, "brown")).connect(gainN(s.c, 0.35)).connect(s.out);
    },
    Rain: (s) => {
      loopSrc(s, noise(s.c, "white")).connect(filt(s.c, "bandpass", 2600, 0.5)).connect(gainN(s.c, 0.28)).connect(s.out);
      loopSrc(s, noise(s.c, "brown")).connect(filt(s.c, "lowpass", 400)).connect(gainN(s.c, 0.55)).connect(s.out);
      const wb = noise(s.c, "white");
      every(s, 18, 90, () => {  // individual droplets
        const c = s.c, t = c.currentTime, n = c.createBufferSource(), f = filt(c, "bandpass", rand(1800, 6500), 4), g = c.createGain();
        n.buffer = wb; g.gain.setValueAtTime(rand(0.05, 0.25), t); g.gain.exponentialRampToValueAtTime(0.0001, t + rand(0.02, 0.06));
        n.connect(f).connect(g).connect(s.out); n.start(t, Math.random() * 3, 0.08);
      });
    },
    Ocean: (s) => {
      const c = s.c, swell = gainN(c, 0.45), lfo = c.createOscillator(), depth = gainN(c, 0.35);
      lfo.frequency.value = 0.085; lfo.connect(depth).connect(swell.gain); lfo.start(); s.nodes.push(lfo);
      loopSrc(s, noise(c, "brown")).connect(filt(c, "lowpass", 650)).connect(swell).connect(s.out);
      const foam = gainN(c, 0.06), d2 = gainN(c, 0.06);
      lfo.connect(d2).connect(foam.gain);
      loopSrc(s, noise(c, "white")).connect(filt(c, "lowpass", 2200)).connect(foam).connect(s.out);
    },
    Birdsong: (s) => {
      loopSrc(s, noise(s.c, "brown")).connect(filt(s.c, "lowpass", 500)).connect(gainN(s.c, 0.12)).connect(s.out);
      every(s, 1300, 3800, () => {
        const base = rand(2200, 3600), n = Math.floor(rand(2, 6)), style = Math.random();
        for (let i = 0; i < n; i++) {
          if (style < 0.5) tone(base, base * rand(1.15, 1.4), 0.07, "sine", 0.18, i * 0.11, s.out);            // trill
          else tone(base * rand(0.9, 1.1), base * rand(0.7, 1.35), rand(0.12, 0.22), "sine", 0.15, i * 0.24, s.out); // whistle
        }
      });
    },
    "Music box": (s) => {
      const notes = [523.25, 587.33, 659.25, 783.99, 880, 1046.5, 1174.66, 1318.51];
      let i = 2;
      every(s, 420, 820, () => {
        if (Math.random() < 0.15) return; // a little rest
        i = Math.max(0, Math.min(notes.length - 1, i + pick([-2, -1, -1, 1, 1, 2])));
        const f = notes[i];
        tone(f, 0, 1.8, "sine", 0.2, 0, s.out);
        tone(f * 4, 0, 0.25, "sine", 0.03, 0, s.out);
        if (Math.random() < 0.25) tone(notes[Math.max(0, i - 2)] / 2, 0, 2.2, "sine", 0.1, 0, s.out);
      });
    },
  };
  function stopAmbient(s) {
    if (!s) return;
    s.dead = true;
    s.timers.forEach(clearTimeout);
    try { s.out.gain.setTargetAtTime(0.0001, s.c.currentTime, 0.35); } catch (e) {}
    setTimeout(() => { s.nodes.forEach((n) => { try { n.stop(); } catch (e) {} }); try { s.out.disconnect(); } catch (e) {} }, 1800);
  }
  function applyAmbient() {
    const kind = fx().ambient || "Off", vol = ((fx().amb_volume == null ? 40 : fx().amb_volume) / 100) * 0.7;
    if (amb && amb.kind === kind) {  // same sound: just follow the volume slider
      try { amb.out.gain.setTargetAtTime(Math.max(vol, 0.0001), amb.c.currentTime, 0.2); } catch (e) {}
      return;
    }
    stopAmbient(amb); amb = null;
    if (kind === "Off" || !BUILD[kind]) return;
    const c = audio();
    if (!c || c.state !== "running") return; // will retry on the next click
    const out = c.createGain();
    out.gain.value = 0.0001; out.connect(c.destination);
    amb = { kind, c, out, nodes: [], timers: [] };
    BUILD[kind](amb);
    out.gain.setTargetAtTime(Math.max(vol, 0.0001), c.currentTime, 0.6);
  }

  // =============== particles ===============
  function particle(cls, x, y, html) {
    const s = document.createElement("span");
    s.className = cls;
    s.style.left = x + "px"; s.style.top = y + "px";
    if (html) s.innerHTML = html;
    document.body.appendChild(s);
    return s;
  }
  function trackOf(label) {
    for (const el of label.querySelectorAll("div, span")) {
      const r = el.getBoundingClientRect();
      if (r.width >= 24 && r.width <= 64 && r.height >= 10 && r.height <= 32) return r;
    }
    const r = label.getBoundingClientRect();
    return { left: r.left, top: r.top, width: 40, height: r.height };
  }
  function burst(cx, cy, n, cls, dist, colors) {
    for (let i = 0; i < n; i++) {
      const s = particle(cls, cx, cy);
      const size = rand(5, 12);
      s.style.width = s.style.height = size + "px";
      if (colors) s.style.background = colors[i % colors.length];
      const a = (i / n) * Math.PI * 2 + Math.random() * 0.5, d = rand(dist * 0.6, dist);
      const dx = Math.cos(a) * d, dy = Math.sin(a) * d;
      s.animate([
        { transform: "translate(-50%,-50%) scale(.2) rotate(0deg)", opacity: 1 },
        { transform: `translate(calc(-50% + ${dx * 0.7}px), calc(-50% + ${dy * 0.7}px)) scale(1) rotate(60deg)`, opacity: 1, offset: 0.55 },
        { transform: `translate(calc(-50% + ${dx}px), calc(-50% + ${dy + 8}px)) scale(.3) rotate(120deg)`, opacity: 0 },
      ], { duration: rand(650, 900), easing: "cubic-bezier(.2,.7,.3,1)" }).onfinish = () => s.remove();
    }
  }
  const sparkle = (rect) => burst(rect.left + rect.width * 0.75, rect.top + rect.height / 2, 9, "pip-sparkle", 38, fx().colors);

  // =============== toggles ===============
  // Streamlit's switches swallow the native 'change' event, so watch clicks / Space.
  function onToggle(box) {
    const input = box.querySelector('input[role="switch"], input[type="checkbox"]');
    if (!input || input.disabled) return;
    const before = input.checked;
    let tries = 0;
    (function check() {
      const now = box.isConnected ? input.checked : !before;
      if (now === before && tries++ < 10) return setTimeout(check, 25);
      play(now ? "on" : "off");
      buzz(now ? [8, 40, 8] : 6);
      if (now && motionOk()) sparkle(trackOf(input.closest("label") || box));
    })();
  }
  document.addEventListener("click", (e) => {
    const box = e.target.closest && e.target.closest(".stCheckbox");
    if (box && box.querySelector('input[role="switch"], input[type="checkbox"]')) onToggle(box);
  }, true);
  document.addEventListener("keydown", (e) => {
    if (e.key === " " && e.target.matches && e.target.matches('input[role="switch"], input[type="checkbox"]')) onToggle(e.target.closest(".stCheckbox") || e.target.parentElement);
  }, true);

  // =============== buttons, tabs, pills ===============
  document.addEventListener("click", (e) => {
    const b = e.target.closest && e.target.closest("button");
    if (!b || b.disabled) return;
    if (b.closest(".stFormSubmitButton")) { play("send"); buzz(12); }
    else if (b.closest('[data-baseweb="tab"]') || b.getAttribute("role") === "tab") { play("tick"); buzz(4); }
    else if (b.closest(".stButtonGroup, [data-testid='stButtonGroup']")) { play("on"); buzz(8); }
    else if (b.closest(".stButton, .stDownloadButton, .stPopover, [data-testid='stPopover'], [data-testid='stExpandSidebarButton'], [data-testid='stSidebarCollapseButton']")) { play("pop"); buzz(10); }
  }, true);
  document.addEventListener("click", (e) => { if (e.target.closest && e.target.closest("summary")) play("tick"); }, true);

  // =============== Pip: tap for hearts + a speech pop ===============
  const PHRASES = ["Pip!", "Hey!", "Hi hi!", "Peep!", "Boop!", "Pip pip!", "Hehe", "You got this!", "Hello friend!", "One tiny step!", "Tickles!", "Proud of you!"];
  // (built from pieces: Streamlit drops scripts that contain literal SVG tags)
  const LT = String.fromCharCode(60);
  const HEART = LT + 'svg viewBox="0 0 24 22" width="100%" height="100%">' + LT + 'path d="M12 21s-8.5-5.3-10.6-10.1C-.3 6.9 2.3 2 6.6 2 9 2 10.7 3.4 12 5.2 13.3 3.4 15 2 17.4 2c4.3 0 6.9 4.9 5.2 8.9C20.5 15.7 12 21 12 21z"/>' + LT + '/svg>';
  document.addEventListener("click", (e) => {
    const svg = e.target.closest && e.target.closest("svg.pip");
    if (!svg) return;
    const r = svg.getBoundingClientRect();
    play("pip"); buzz([6, 30, 6]);
    const hop = svg.querySelector(".pip-hop");
    if (hop && motionOk()) hop.animate([{ transform: "translateY(0)" }, { transform: "translateY(-14px) scale(1.03,.97)" }, { transform: "translateY(0)" }, { transform: "translateY(-5px)" }, { transform: "translateY(0)" }], { duration: 520, easing: "ease-out" });
    document.querySelectorAll(".pip-say").forEach((x) => x.remove());
    const say = particle("pip-say", r.left + r.width * 0.72, r.top + r.height * 0.08);
    say.textContent = pick(PHRASES);
    say.animate([{ transform: "translate(-10%,-100%) scale(.5)", opacity: 0 }, { transform: "translate(-10%,-100%) scale(1.08)", opacity: 1, offset: 0.18 },
      { transform: "translate(-10%,-100%) scale(1)", opacity: 1, offset: 0.3 }, { transform: "translate(-10%,-110%) scale(1)", opacity: 1, offset: 0.85 },
      { transform: "translate(-10%,-120%) scale(.95)", opacity: 0 }], { duration: 1700, easing: "ease-out" }).onfinish = () => say.remove();
    if (!motionOk()) return;
    for (let i = 0; i < 6; i++) {
      const h = particle("pip-heart", r.left + r.width * rand(0.25, 0.75), r.top + r.height * rand(0.25, 0.5), HEART);
      const sz = rand(12, 22); h.style.width = sz + "px"; h.style.height = sz + "px";
      const dx = rand(-40, 40), up = rand(60, 120), rot = rand(-25, 25);
      h.animate([{ transform: "translate(-50%,-50%) scale(.3)", opacity: 0 }, { transform: `translate(calc(-50% + ${dx * 0.3}px), calc(-50% - ${up * 0.3}px)) scale(1) rotate(${rot}deg)`, opacity: 1, offset: 0.25 },
        { transform: `translate(calc(-50% + ${dx}px), calc(-50% - ${up}px)) scale(.8) rotate(${-rot}deg)`, opacity: 0 }],
        { duration: rand(1000, 1500), delay: i * 70, easing: "ease-out", fill: "backwards" }).onfinish = () => h.remove();
    }
  }, true);

  // =============== Pebble (tidalBYTE's penguin) easter eggs ===============
  // Pebble's picture lives in the footer (hover it to see Pebble peek out); we clone it for cameos.
  function pebbleSrc() { const i = document.querySelector(".pebble-peek img"); return i ? i.src : null; }
  function pebbleImg(cls) {
    const src = pebbleSrc(); if (!src) return null;
    const im = new Image(); im.src = src; im.className = cls; im.alt = ""; document.body.appendChild(im); return im;
  }
  function pebbleSay(x, y, text) {
    const b = particle("pip-say", x, y); b.textContent = text;
    b.animate([{ transform: "translate(-50%,-100%) scale(.5)", opacity: 0 }, { transform: "translate(-50%,-100%) scale(1)", opacity: 1, offset: .15 },
      { transform: "translate(-50%,-110%)", opacity: 1, offset: .85 }, { transform: "translate(-50%,-120%)", opacity: 0 }],
      { duration: 2400, easing: "ease-out" }).onfinish = () => b.remove();
  }
  // 1) type "pebble" in the check-in box: Pebble waddles along the waves
  let walked = false;
  function pebbleWalk() {
    if (walked || !motionOk()) return; walked = true; setTimeout(() => (walked = false), 9000);
    const im = pebbleImg("pebble-walk"); if (!im) return;
    play("pip"); buzz([6, 30, 6]);
    const dist = window.innerWidth + 280;
    const frames = [];
    for (let i = 0; i <= 20; i++) frames.push({ transform: `translateX(${(dist * i) / 20}px) rotate(${i % 2 ? 7 : -7}deg) translateY(${i % 2 ? -6 : 0}px)` });
    im.animate(frames, { duration: 7000, easing: "linear" }).onfinish = () => im.remove();
    setTimeout(() => pebbleSay(window.innerWidth * 0.45, window.innerHeight - 140, "Pebble says hi! Keep going!"), 2600);
  }
  document.addEventListener("input", (e) => {
    const t = e.target;
    if (t instanceof HTMLTextAreaElement && /pebble/i.test(t.value || "")) pebbleWalk();
  }, true);
  // 2) tap Pip 5 times quickly: his best friend Pebble pops up to say hi
  let taps = [];
  document.addEventListener("click", (e) => {
    const svg = e.target.closest && e.target.closest("svg.pip");
    if (!svg) return;
    const now = Date.now(); taps = taps.filter((t) => now - t < 2500); taps.push(now);
    if (taps.length < 5) return;
    taps = [];
    const r = svg.getBoundingClientRect();
    const im = pebbleImg("pebble-pop"); if (!im) return;
    im.style.left = (r.right - 10) + "px"; im.style.top = (r.top + r.height * 0.45) + "px";
    im.animate([{ transform: "translateY(40px) scale(.3)", opacity: 0 }, { transform: "translateY(-8px) scale(1.05)", opacity: 1, offset: .2 },
      { transform: "translateY(0) scale(1)", opacity: 1, offset: .3 }, { transform: "translateY(0) rotate(-6deg)", offset: .5 },
      { transform: "translateY(0) rotate(6deg)", offset: .7 }, { transform: "translateY(30px) scale(.6)", opacity: 0 }],
      { duration: 3200, easing: "ease-out" }).onfinish = () => im.remove();
    pebbleSay(r.right + 40, r.top + r.height * 0.4, "Pebble here! Pip's my best friend!");
  }, true);

  // =============== Pip's eyes follow the cursor ===============
  let mx = -1, my = -1, raf = 0;
  document.addEventListener("pointermove", (e) => {
    mx = e.clientX; my = e.clientY;
    if (raf) return;
    raf = requestAnimationFrame(() => {
      raf = 0;
      const still = fx().still;
      document.querySelectorAll("svg.pip .pip-eyes").forEach((g) => {
        if (still) { g.style.transform = ""; return; }
        const r = g.ownerSVGElement.getBoundingClientRect();
        const dx = (mx - (r.left + r.width / 2)) / (r.width * 1.5), dy = (my - (r.top + r.height * 0.52)) / (r.height * 1.5);
        const k = Math.min(1, Math.hypot(dx, dy));
        const a = Math.atan2(dy, dx);
        g.style.transform = `translate(${(Math.cos(a) * 4.5 * k).toFixed(2)}px, ${(Math.sin(a) * 3.5 * k).toFixed(2)}px)`;
      });
    });
  }, { passive: true });

  // =============== tap empty space: a little snow puff ===============
  document.addEventListener("click", (e) => {
    if (!motionOk()) return;
    const t = e.target;
    if (!t.closest || !t.closest("[data-testid='stMain'], section.main, .main")) return;
    if (t.closest("button, a, input, textarea, label, select, svg.pip, [role='tab'], [data-baseweb], [data-testid='stAudioInput'], .card, .bubble, .tbl-wrap, [data-testid='stExpander'], [data-testid='stJson'], h1, h2, h3, p, li")) return;
    play("puff");
    burst(e.clientX, e.clientY, 8, "pip-snow", 34, fx().colors);
  });

  // =============== Enter sends the check-in, Shift+Enter makes a new line ===============
  document.addEventListener("keydown", (e) => {
    const ta = e.target;
    if (!e.isTrusted || e.key !== "Enter" || e.shiftKey || e.altKey || e.isComposing || e.keyCode === 229) return;
    if (!(ta instanceof HTMLTextAreaElement) || !ta.closest(".stForm, [data-testid='stForm']")) return;
    if (e.metaKey || e.ctrlKey) { play("send"); return; }
    e.preventDefault();
    e.stopImmediatePropagation();
    ta.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", code: "Enter", keyCode: 13, which: 13, ctrlKey: true, metaKey: true, bubbles: true, cancelable: true }));
    play("send");
    buzz(12);
  }, true);

  // =============== Focus timer (pomodoro): focus, short break, every 4th break longer ===============
  // Built with DOM calls (no markup strings: Streamlit drops scripts containing tag-like text).
  SOUNDS.chime = (v) => [784, 988, 1175, 1568].forEach((f, i) => tone(f, 0, 0.5, "sine", 0.18 * v, i * 0.12));
  const T = { preset: [25, 5], mode: "focus", left: 25 * 60, running: false, end: 0, rounds: 0, brk: 5 };
  try { Object.assign(T, JSON.parse(localStorage.getItem("pipTimer") || "{}")); } catch (e) {}
  const save = () => { try { localStorage.setItem("pipTimer", JSON.stringify(T)); } catch (e) {} };
  const mk = (tag, cls, txt) => { const x = document.createElement(tag); if (cls) x.className = cls; if (txt != null) x.textContent = txt; return x; };
  const fmt = (sec) => { sec = Math.max(0, Math.ceil(sec)); return Math.floor(sec / 60) + ":" + String(sec % 60).padStart(2, "0"); };
  const length = () => (T.mode === "focus" ? T.preset[0] : T.brk) * 60;
  const remaining = () => (T.running ? (T.end - Date.now()) / 1000 : T.left);
  let tBtn, tPanel, tTime, tMode, tRing, tStart, tDots, tLbl, tPres, baseTitle = document.title, titled = false;

  function timerNote(text) {
    const r = tBtn.getBoundingClientRect();
    const b = particle("pip-say", r.left + r.width / 2, r.bottom + 54); b.textContent = text;
    b.animate([{ transform: "translate(-50%,-100%) scale(.6)", opacity: 0 }, { transform: "translate(-50%,-100%) scale(1)", opacity: 1, offset: .1 },
      { transform: "translate(-50%,-100%)", opacity: 1, offset: .9 }, { transform: "translate(-50%,-110%)", opacity: 0 }],
      { duration: 4200, easing: "ease-out" }).onfinish = () => b.remove();
  }
  function finish(skipped) {
    if (T.mode === "focus") {
      T.rounds += 1; T.mode = "break"; T.brk = T.rounds % 4 === 0 ? 15 : T.preset[1];
      T.left = T.brk * 60; T.end = Date.now() + T.left * 1000; T.running = true;  // breaks start on their own
      if (!skipped) { play("chime"); buzz([20, 60, 20, 60, 20]); timerNote(T.brk === 15 ? "4 rounds! Take a long 15-minute break." : "Focus round done! Take a little break."); }
    } else {
      T.mode = "focus"; T.left = T.preset[0] * 60; T.running = false;  // the next round waits for you
      if (!skipped) { play("chime"); buzz([20, 60, 20]); timerNote("Break's over. Ready when you are!"); }
    }
    save(); render();
  }
  function toggle() {
    if (T.running) { T.left = remaining(); T.running = false; play("off"); }
    else { T.end = Date.now() + T.left * 1000; T.running = true; play("on"); buzz(10); }
    save(); render();
  }
  function render() {
    if (!tBtn) return;
    const rem = remaining(), pct = Math.min(100, Math.max(0, 100 * (1 - rem / length())));
    tTime.textContent = fmt(rem);
    tMode.textContent = T.mode === "focus" ? "Focus time" : (T.brk === 15 ? "Long break" : "Break time");
    tRing.style.setProperty("--p", pct.toFixed(1));
    tStart.textContent = T.running ? "Pause" : (rem < length() - 1 ? "Resume" : "Start");
    const active = T.running || rem < length() - 1;
    tLbl.textContent = active ? fmt(rem) : "Focus timer";
    tBtn.classList.toggle("running", T.running && T.mode === "focus");
    tBtn.classList.toggle("break", T.mode === "break" && active);
    tPanel.classList.toggle("break", T.mode === "break");
    tPres.querySelectorAll(".pt-pre").forEach((b) => b.classList.toggle("on", +b.dataset.f === T.preset[0]));
    tDots.replaceChildren(...[0, 1, 2, 3].map((i) => mk("i", i < T.rounds % 4 ? "on" : "")));
    if (T.running) { if (!titled) baseTitle = document.title; titled = true; document.title = `${fmt(rem)} · ${T.mode === "focus" ? "Focus" : "Break"} · Pip`; }
    else if (titled) { titled = false; document.title = baseTitle; }
  }
  function placeTimer() {  // sit just left of the Sound button, wherever it is
    const v = document.querySelector(".st-key-vol_corner");
    if (!v || !tBtn) return;
    const r = v.getBoundingClientRect();
    if (!r.width) return;
    tBtn.style.right = Math.round(window.innerWidth - r.left + 8) + "px";
    tBtn.style.top = Math.round(r.top + (r.height - tBtn.offsetHeight) / 2) + "px";
    tPanel.style.top = Math.round(r.bottom + 10) + "px";
  }
  function buildTimer() {
    document.querySelectorAll(".pt-btn, .pt-panel").forEach((x) => x.remove());
    tBtn = mk("button", "pt-btn"); tBtn.type = "button"; tBtn.title = "Focus timer (Pomodoro)";
    tLbl = mk("span", "pt-lbl", "Focus timer"); tBtn.append(mk("span", "pt-ic"), tLbl);
    tPanel = mk("div", "pt-panel"); tPanel.hidden = true;
    tMode = mk("div", "pt-mode"); tRing = mk("div", "pt-ring"); tTime = mk("div", "pt-time"); tRing.append(tTime);
    tPres = mk("div", "pt-presets");
    [[15, 3], [25, 5], [50, 10]].forEach((p) => { const b = mk("button", "pt-pre", p[0] + "/" + p[1]); b.title = p[0] + " min focus, " + p[1] + " min break"; b.type = "button"; b.dataset.f = p[0]; b.dataset.b = p[1]; tPres.append(b); });
    const row = mk("div", "pt-row");
    const reset = mk("button", "pt-small", "Reset"); reset.type = "button";
    tStart = mk("button", "pt-start", "Start"); tStart.type = "button";
    const skip = mk("button", "pt-small", "Skip"); skip.type = "button";
    row.append(reset, tStart, skip);
    tDots = mk("div", "pt-dots");
    tPanel.append(tMode, tRing, tPres, row, tDots, mk("div", "pt-hint", "Minutes of focus / break. Every 4th break is a long one, and Pip chimes when it's time."));
    document.body.append(tBtn, tPanel);
    tBtn.addEventListener("click", () => { tPanel.hidden = !tPanel.hidden; play("pop"); buzz(8); placeTimer(); });
    tStart.addEventListener("click", toggle);
    reset.addEventListener("click", () => { Object.assign(T, { mode: "focus", running: false, rounds: 0 }); T.left = T.preset[0] * 60; play("off"); save(); render(); });
    skip.addEventListener("click", () => { play("tick"); finish(true); });
    tPres.addEventListener("click", (e) => {
      const b = e.target.closest(".pt-pre"); if (!b) return;
      T.preset = [+b.dataset.f, +b.dataset.b]; Object.assign(T, { mode: "focus", running: false }); T.left = T.preset[0] * 60;
      play("tick"); save(); render();
    });
    document.addEventListener("pointerdown", (e) => {
      if (!tPanel.hidden && !tPanel.contains(e.target) && !tBtn.contains(e.target)) tPanel.hidden = true;
    }, true);
    render(); placeTimer();
  }
  setInterval(() => {
    if (!tBtn || !tBtn.isConnected) buildTimer();
    if (T.running && remaining() <= 0) finish(false);
    if (T.running || !tPanel.hidden) render();
    placeTimer();
  }, 250);
  buildTimer();

  W.__pipFxApply = applyAmbient;
  W.__pipAmbKind = () => (amb ? amb.kind + ":" + amb.c.state : "none");
  applyAmbient();
})();
