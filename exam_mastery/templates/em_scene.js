const EM_LOC = (typeof document !== 'undefined' && document.documentElement.dataset.decimal === '.') ? 'en-US' : 'de-DE';
/* Exam Mastery mathematical scenes (em-scene-v1), part of the lab runtime (em_labs.js). No dependencies, no network.
   A scene is declarative (spec.scene, built and checked by exam_mastery/labs/scenes.py):
     objects  graphic objects with an id and a colour role; the renderer marks them with data-ref
     vars     selections of the learner (e.g. which neuron), substituted into ids and paths as {j} / {J} (= j + 1)
     steps    the explanation: title, text, formula tokens, targets (highlighted objects), reveal, zoom, anim
   Every number a scene shows is read from a trace computed by EM.models (mirror of labs/models.py); the scene never
   computes on its own. Model (EM.models) - animation (renderer.enter) - interaction (player, renderer events) stay
   separate. */
(() => {
'use strict';
const EM = window.EM = window.EM || {};
const SVGNS = 'http://www.w3.org/2000/svg';
const el = (tag, attrs, text) => { const e = document.createElement(tag); for (const [k, v] of Object.entries(attrs || {})) { if (k === 'class') e.className = v; else e.setAttribute(k, v); } if (text !== undefined) e.textContent = String(text); return e; };
const sv = (tag, attrs, text) => { const e = document.createElementNS(SVGNS, tag); for (const [k, v] of Object.entries(attrs || {})) e.setAttribute(k, String(v)); if (text !== undefined) e.textContent = String(text); return e; };
const fmt = (x, d = 3) => { if (x === null || x === undefined || !Number.isFinite(x)) return '–'; const r = Math.round(x * 10 ** d) / 10 ** d; return (Object.is(r, -0) ? 0 : r).toLocaleString(EM_LOC, { useGrouping: EM_LOC === 'de-DE',  minimumFractionDigits: 0, maximumFractionDigits: d }).replace('-', '−'); };  /* typographic minus */
const S = EM.scene = { el, sv, fmt, types: {} };

/* ---------------------------------------------------------------- motion */
let reduced = false;
try { reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) { /* old browser */ }
S.motion = { get reduced() { return reduced; }, set reduced(v) { reduced = !!v; }, speed: 1 };
const ease = k => k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;   /* cubic in-out: calm start and landing */
/* Runs fn(k) for k in [0, 1]. Instant when motion is reduced. Returns a promise; a newer tween on the same key cancels. */
const running = new Map();
S.tween = (key, ms, fn) => new Promise(res => {
  const prev = running.get(key); if (prev) prev.cancel();
  const dur = reduced ? 0 : ms / S.motion.speed;
  if (dur <= 0) { fn(1); res(); return; }
  let stop = false, t0 = null;
  running.set(key, { cancel() { stop = true; fn(1); res(); } });
  const frame = ts => { if (stop) return; if (t0 === null) t0 = ts; const k = Math.min(1, (ts - t0) / dur); fn(ease(k)); if (k < 1) requestAnimationFrame(frame); else { running.delete(key); res(); } };
  requestAnimationFrame(frame);
});
S.lerp = (a, b, k) => a + (b - a) * k;

/* ---------------------------------------------------------------- paths and templates */
S.sub = (s, vars) => String(s).replace(/\{([a-z])\}/g, (_, k) => String(vars[k])).replace(/\{([A-Z])\}/g, (_, k) => String(vars[k.toLowerCase()] + 1));
S.get = (obj, path) => String(path).split('.').reduce((o, k) => (o === null || o === undefined) ? undefined : o[/^\d+$/.test(k) ? Number(k) : k], obj);

/* ---------------------------------------------------------------- formula tokens
   {t: text} plain text | {o: operator} | {s: symbol, sub, sup, ref, role} | {v: path, d: digits, ref, role, unit} */
S.formula = (tokens, trace, vars) => {
  const p = el('p', { class: 'em-f' });
  for (const tk of tokens) {
    if ('t' in tk) { p.appendChild(el('span', { class: 'em-f-t' }, S.sub(tk.t, vars))); continue; }
    if ('o' in tk) { p.appendChild(el('span', { class: 'em-f-o' }, S.sub(tk.o, vars))); continue; }
    const ref = tk.ref ? S.sub(tk.ref, vars) : null;
    const span = el('span', { class: 'em-tok' + (tk.role ? ' r-' + tk.role : '') });
    if (ref) { span.dataset.ref = ref; span.setAttribute('tabindex', '0'); span.setAttribute('role', 'button'); }
    if ('s' in tk) { span.appendChild(document.createTextNode(S.sub(tk.s, vars))); if (tk.sub !== undefined) span.appendChild(el('sub', {}, S.sub(tk.sub, vars))); if (tk.sup !== undefined) span.appendChild(el('sup', {}, S.sub(tk.sup, vars))); }
    else { const path = S.sub(tk.v, vars), v = S.get(trace, path); span.classList.add('em-num'); span.dataset.path = path; span.dataset.val = String(v); span.textContent = (tk.e && Number.isFinite(v) ? (v === 0 ? '0' : v.toExponential(tk.d ?? 1).replace('.', ',').replace(/e([+-])(\d+)/, (_, sg, n) => ' · 10^' + (sg === '-' ? '−' : '') + n)) : fmt(v, tk.d ?? 3)) +(tk.unit ? ' ' + tk.unit : ''); }
    if (ref) span.setAttribute('aria-label', span.textContent + ' – im Bild hervorheben');
    p.appendChild(span);
  }
  return p;
};

/* ---------------------------------------------------------------- player
   cfg: {scene, renderer, trace(): object, vars: {...}, onVars(vars)}  */
S.player = (host, cfg) => {
  const sc = cfg.scene, R = cfg.renderer, vars = { ...cfg.vars };
  const box = el('section', { class: 'em-scene', 'aria-label': sc.title, tabindex: '-1' });
  box.dataset.scene = sc.type;
  const head = el('div', { class: 'em-scene-head' }); head.append(el('h3', {}, sc.title)); if (sc.lead) head.append(el('p', { class: 'em-meta' }, sc.lead));
  const stage = el('div', { class: 'em-stage ds-stage' }), gbox = el('div', { class: 'em-graphic' }), side = el('div', { class: 'em-explain' });
  const count = el('p', { class: 'em-stepcount' }), title = el('h4', { class: 'em-step-title' }), fbox = el('div', { class: 'em-fbox' }), text = el('p', { class: 'em-step-text' });
  const live = el('p', { class: 'em-sr', role: 'status', 'aria-live': 'polite' });
  /* colour key: one entry per mathematical role used by the scene, in the same colour as figure and formula */
  const ROLE = { input: 'Eingabe', weight: 'Gewicht', bias: 'Bias', sum: 'Summe z', activation: 'Aktivierung', output: 'Ausgabe', target: 'Zielwert', loss: 'Verlust', gradient: 'Gradient',
    point_p: 'Punkt P', point_q: 'Punkt Q', point_u: 'zweites Paar', midpoint: 'Mittelpunkt', distance: 'Abstand', lift: 'Bildpunkt', curve: 'Kurve',
    sale: 'Verkauf', term: 'Zahlungsziel', inflow: 'Einzahlung', outflow: 'Auszahlung', invest: 'Investition', balance: 'Liquidität', need: 'Finanzierungsbedarf' };
  const roles = [...new Set((sc.objects || []).map(o => o.role))].filter(r => ROLE[r]);
  const legend = el('p', { class: 'em-legend-roles', 'aria-label': 'Farbschlüssel' });
  roles.forEach(r => { const sp = el('span', { class: 'em-tok r-' + r }); sp.append(el('i'), document.createTextNode(ROLE[r])); legend.appendChild(sp); });
  side.append(count, title, fbox, text, live); if (roles.length) side.append(legend); stage.append(gbox, side);
  const ctl = el('div', { class: 'em-player', role: 'group', 'aria-label': 'Animation steuern' });
  const B = (label, cls, aria) => { const b = el('button', { type: 'button', class: 'em-pbtn ' + (cls || ''), 'aria-label': aria || label }, label); ctl.appendChild(b); return b; };
  const bReset = B('↺ Neustart', '', 'Neustart: zum ersten Schritt'), bBack = B('‹ Zurück', '', 'Einen Schritt zurück'), bPlay = B('▶ Abspielen', 'em-primary', 'Abspielen'), bNext = B('Weiter ›', '', 'Nächster Rechenschritt');
  const spd = el('label', { class: 'em-speed' }); const sel = el('select', { 'aria-label': 'Geschwindigkeit' });
  [['0.5', 'langsam'], ['1', 'normal'], ['2', 'schnell']].forEach(([v, t]) => { const o = el('option', { value: v }, t); if (v === '1') o.selected = true; sel.appendChild(o); });
  spd.append(document.createTextNode('Tempo '), sel); ctl.appendChild(spd);
  const rm = el('label', { class: 'em-rm' }); const rmc = el('input', { type: 'checkbox' }); rmc.checked = reduced; rm.append(rmc, document.createTextNode(' Bewegung reduzieren')); ctl.appendChild(rm);
  const progress = el('ol', { class: 'em-steps-dots', 'aria-label': 'Schritte' });
  const transport = el('div', { class: 'em-transport' }); transport.append(ctl, progress);
  box.append(head, stage, transport); host.appendChild(box);

  let steps = [], i = 0, timer = null, trace = cfg.trace();
  const expand = () => { /* repeat: one step per element of a trace array (e.g. one per period) */
    const out = [];
    for (const st of sc.steps) {
      if (!st.repeat) { out.push({ ...st, vars: {} }); continue; }
      const n = (S.get(trace, st.repeat) || []).length;
      for (let k = 0; k < n; k++) out.push({ ...st, id: st.id + '-' + k, vars: { [st.var || 'k']: k } });
    }
    return out;
  };
  R.mount(gbox, { vars, setVar, box, ...(cfg.ctx || {}) });
  const allVars = st => ({ ...vars, ...(st ? st.vars : {}) });
  const svg = () => gbox.querySelector('svg');
  let baseView = null;
  const zoomTo = (ids, v) => { /* zoom on a part of the figure (viewBox tween); restore when the step has no zoom */
    const s = svg(); if (!s) return; if (!baseView) baseView = s.getAttribute('viewBox').split(/\s+/).map(Number);
    let target = baseView;
    if (ids && ids.length) {
      const bbs = ids.map(id => [...s.querySelectorAll('[data-ref="' + S.sub(id, v) + '"]')]).flat().filter(e => typeof e.getBBox === 'function').map(e => e.getBBox()).filter(b => b.width || b.height);
      if (bbs.length) { const x0 = Math.min(...bbs.map(b => b.x)), y0 = Math.min(...bbs.map(b => b.y)), x1 = Math.max(...bbs.map(b => b.x + b.width)), y1 = Math.max(...bbs.map(b => b.y + b.height));
        const pad = 34, ar = baseView[2] / baseView[3]; let w = Math.max(x1 - x0 + 2 * pad, baseView[2] * .62), h = Math.max(y1 - y0 + 2 * pad, w / ar); w = Math.max(w, h * ar);
        target = [(x0 + x1) / 2 - w / 2, (y0 + y1) / 2 - h / 2, w, h]; }
    }
    const from = s.getAttribute('viewBox').split(/\s+/).map(Number);
    box.dataset.zoomed = target === baseView ? '' : '1';
    return S.tween('zoom', 650, k => s.setAttribute('viewBox', from.map((a, n) => S.lerp(a, target[n], k)).join(' ')));
  };
  const hot = (ref, on) => { box.querySelectorAll('[data-ref="' + ref + '"]').forEach(e => e.classList.toggle('em-hot', on)); };
  const render = (animate) => {
    const st = steps[i], v = allVars(st);
    box.dataset.step = String(i); box.dataset.stepId = st.id;
    const revealed = new Set(); steps.slice(0, i + 1).forEach(s2 => (s2.reveal || []).forEach(r => revealed.add(S.sub(r, allVars(s2)))));
    R.update(trace, v, { step: st, index: i, revealed });
    box.querySelectorAll('.em-graphic [data-ref]').forEach(e => { e.classList.remove('em-target', 'em-hot'); });
    const targets = (st.targets || []).map(r => S.sub(r, v));
    targets.forEach(r => box.querySelectorAll('.em-graphic [data-ref="' + r + '"]').forEach(e => e.classList.add('em-target')));
    box.classList.toggle('em-has-target', targets.length > 0);
    count.textContent = 'Schritt ' + (i + 1) + ' von ' + steps.length;
    title.textContent = S.sub(st.title, v);
    fbox.replaceChildren(...(st.formula ? [S.formula(st.formula, trace, v)] : []), ...((st.formula2 ? [S.formula(st.formula2, trace, v)] : [])));
    text.textContent = S.sub(st.text || '', v);
    live.textContent = title.textContent + '. ' + fbox.textContent;
    [...progress.children].forEach((li, n) => { li.classList.toggle('cur', n === i); li.classList.toggle('past', n < i); });
    bBack.disabled = i === 0; bNext.disabled = i === steps.length - 1;
    zoomTo(st.zoom, v);
    if (animate && R.enter) return R.enter(st, trace, v);
    return Promise.resolve();
  };
  const buildDots = () => progress.replaceChildren(...steps.map((st, n) => { const li = el('li'); const b = el('button', { type: 'button', 'aria-label': 'Schritt ' + (n + 1) + ': ' + S.sub(st.title, allVars(st)) }); b.addEventListener('click', () => { stop(); go(n); }); li.appendChild(b); return li; }));
  const go = (n, animate = true) => { i = Math.max(0, Math.min(steps.length - 1, n)); return render(animate); };
  const stop = () => { if (timer) { clearTimeout(timer); timer = null; } bPlay.textContent = '▶ Abspielen'; bPlay.setAttribute('aria-label', 'Abspielen'); box.dataset.playing = ''; };
  const play = () => {
    if (i >= steps.length - 1) go(0, false);
    bPlay.textContent = '⏸ Pause'; bPlay.setAttribute('aria-label', 'Pause'); box.dataset.playing = '1';
    const tick = () => { if (!box.dataset.playing) return; if (i >= steps.length - 1) { stop(); return; }
      go(i + 1).then(() => { if (box.dataset.playing) timer = setTimeout(tick, (reduced ? 1800 : 2400) / S.motion.speed); }); };
    timer = setTimeout(tick, reduced ? 300 : 500 / S.motion.speed);
  };
  function setVar(k, val) { vars[k] = val; if (cfg.onVars) cfg.onVars(vars); refresh(); }
  const refresh = () => { /* parameters or selections changed: same step, new numbers, no step animation */
    trace = cfg.trace(); const n = steps.length; steps = expand(); if (steps.length !== n) buildDots(); if (i >= steps.length) i = steps.length - 1; render(false); };
  bReset.addEventListener('click', () => { stop(); go(0); box.dispatchEvent(new CustomEvent('em-scene-reset')); });
  bBack.addEventListener('click', () => { stop(); go(i - 1); });
  bNext.addEventListener('click', () => { stop(); go(i + 1); });
  bPlay.addEventListener('click', () => box.dataset.playing ? stop() : play());
  sel.addEventListener('change', () => { S.motion.speed = Number(sel.value); });
  rmc.addEventListener('change', () => { reduced = rmc.checked; box.classList.toggle('em-reduced', reduced); });
  box.addEventListener('keydown', e => { if (e.target.closest('input,select,textarea')) return;
    if (e.key === 'ArrowRight' && !e.target.closest('[data-drag]')) { e.preventDefault(); stop(); go(i + 1); }
    else if (e.key === 'ArrowLeft' && !e.target.closest('[data-drag]')) { e.preventDefault(); stop(); go(i - 1); }
    else if ((e.key === 'Enter' || e.key === ' ') && e.target.classList.contains('em-tok')) { e.preventDefault(); e.target.click(); } });
  /* formula term <-> graphic object: click (or Enter) on a term highlights the object; hovering an object lights the term */
  box.addEventListener('click', e => { const t = e.target.closest('.em-tok[data-ref]'); if (!t) return; const r = t.dataset.ref; const on = !t.classList.contains('em-hot');
    box.querySelectorAll('.em-hot').forEach(x => x.classList.remove('em-hot')); if (on) hot(r, true); box.dataset.hot = on ? r : ''; });
  gbox.addEventListener('pointerover', e => { const g = e.target.closest('[data-ref]'); if (g) fbox.querySelectorAll('.em-tok[data-ref="' + g.dataset.ref + '"]').forEach(x => x.classList.add('em-hot')); });
  gbox.addEventListener('pointerout', e => { const g = e.target.closest('[data-ref]'); if (g && box.dataset.hot !== g.dataset.ref) fbox.querySelectorAll('.em-tok[data-ref="' + g.dataset.ref + '"]').forEach(x => x.classList.remove('em-hot')); });
  steps = expand(); buildDots(); go(0, false);
  return { box, refresh, go, stop, get index() { return i; }, get steps() { return steps; }, get trace() { return trace; }, vars };
};

/* ---------------------------------------------------------------- preview
   A calm, looping miniature of a lab's scene for overview pages. It uses the same renderer and the same model trace as
   the lab (spec defaults), so a preview can never show numbers the lab would not. No interaction; still image when
   motion is reduced; paused while off screen. Returns {stop()}. */
S.previewTrace = (spec) => {
  const m = spec.model, M = window.EM.models, d = Object.fromEntries((spec.params || []).map(p => [p.id, p.default]));
  if (spec.scene.type === 'network') return () => M.mlpTrace(m.init, m.x, m.target, m.lr, m.hidden_act, m.out_act);
  if (spec.scene.type === 'chord') return (t) => M.chordTrace(d.s, t === undefined ? d.t : t);
  if (spec.scene.type === 'cashflow') return () => M.cashTrace({ orders: m.orders, cost: m.cost, invest: m.invest, delay: m.delay, delayB: m.delay + 1, start_cash: m.start_cash || 0, horizon: m.orders.length });
  return null;
};
S.preview = (host, spec) => {
  const type = spec.scene && spec.scene.type, mk = S.types[type], tr0 = mk && S.previewTrace(spec);
  if (!tr0) return { stop() {} };
  const R = mk(), m = spec.model, vars = { j: 0, i: 0 };
  const box = el('div', { class: 'em-preview', 'data-scene': type, 'aria-hidden': 'true' }); host.appendChild(box);
  R.mount(box, { vars, setVar() {}, setParam() {}, box, unit: m.unit || 'k€', acts: () => ({ ha: m.hidden_act || 'sigmoid', oa: m.out_act || 'sigmoid' }) });
  const svg = box.querySelector('svg'); svg.removeAttribute('tabindex'); svg.setAttribute('focusable', 'false');
  let alive = true, visible = true;
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const until = async () => { while (alive && !visible) await wait(400); return alive; };
  const set = (tr, revealed, step) => R.update(tr, vars, { step: step || {}, index: 0, revealed: new Set(revealed) });
  const still = () => { /* reduced motion: the most informative single frame */
    if (type === 'network') set(tr0(), ['a1', 'a2', 'y', 'L', 'z1']);
    else if (type === 'chord') set(tr0(), ['PQ', 'M', 'd', 'X', 'surface', 'rect'], { camera: '3d' });
    else set(tr0(), ['term', 'out', 'balance', 'need']);
  };
  const loops = {
    async network() { const tr = tr0();
      vars.j = 0; set(tr, []); await wait(500);
      for (const j of [0, 1]) { vars.j = j; set(tr, j ? ['z1', 'a1'] : []); if (!await until()) return;
        await R.enter({ anim: { kind: 'flow', edges: ['w' + (j + 1) + '1', 'w' + (j + 1) + '2'] } }, tr, vars); set(tr, j ? ['a1', 'z2'] : ['z1']);
        await R.enter({ anim: { kind: 'act' } }, tr, vars); set(tr, j ? ['a1', 'a2', 'z2'] : ['a1', 'z1']); await wait(500); }
      if (!await until()) return; await R.enter({ anim: { kind: 'flow', edges: ['v1', 'v2'] } }, tr, vars); set(tr, ['a1', 'a2', 'y']); await wait(600);
      set(tr, ['a1', 'a2', 'y', 'L']); await wait(900); if (!await until()) return;
      await R.enter({ anim: { kind: 'back', edges: ['v1', 'w11'] } }, tr, vars); await wait(300);
      await R.enter({ anim: { kind: 'update' } }, tr, vars); set(tr, ['after'], { id: 'after' }); await wait(2200); },
    async chord() { const d = Object.fromEntries((spec.params || []).map(p => [p.id, p.default]));
      set(tr0(d.t), ['PQ', 'M'], { camera: 'top' }); await wait(700); if (!await until()) return;
      await R.enter({ anim: { kind: 'camera', to: '3d' } }, tr0(d.t), vars);
      set(tr0(d.t), ['PQ', 'M', 'd', 'X'], { camera: '3d' }); await R.enter({ anim: { kind: 'lift' } }, tr0(d.t), vars);
      set(tr0(d.t), ['PQ', 'M', 'd', 'X', 'surface'], { camera: '3d' });
      const t0 = performance.now(), dur = 7000;   /* Q travels once around the curve; the image point traces the surface */
      while (alive && performance.now() - t0 < dur) { if (!await until()) return; const k = (performance.now() - t0) / dur, t = ((d.t + k) % 1 + 1) % 1;
        if (Math.abs(t - d.s) > .01 && Math.abs(t - d.s) < .99) set(tr0(Math.round(t * 1000) / 1000), ['PQ', 'M', 'd', 'X', 'surface'], { camera: '3d' }); await wait(50); }
      set(tr0(d.t), ['PQ', 'M', 'd', 'X', 'surface', 'rect'], { camera: '3d' }); await R.enter({ anim: { kind: 'seek' } }, tr0(d.t), vars); await wait(2600);
      await R.enter({ anim: { kind: 'camera', to: 'top' } }, tr0(d.t), vars); },
    async cashflow() { const tr = tr0(), T = tr.cf.length;
      set(tr, [], { vars: { k: -1 } }); await wait(800); if (!await until()) return;
      set(tr, ['term'], { vars: { k: -1 } }); await R.enter({ anim: { kind: 'arcs' } }, tr, vars); set(tr, ['term', 'out'], { vars: { k: -1 } }); await wait(800);
      for (let k = 0; k < T; k++) { if (!await until()) return; set(tr, ['term', 'out'], { vars: { k } }); await R.enter({ anim: { kind: 'period' }, vars: { k } }, tr, vars); await wait(260); }
      set(tr, ['term', 'out', 'balance', 'need'], { vars: { k: T - 1 } }); await wait(3200); },
  };
  if (window.IntersectionObserver) new IntersectionObserver(es => { visible = es.some(e => e.isIntersecting); }).observe(box);
  const run = async () => { while (alive) { if (S.motion.reduced) { still(); return; } try { await loops[type](); } catch (e) { still(); return; } await wait(400); } };
  still(); setTimeout(run, 300);
  return { box, stop() { alive = false; } };
};

/* didactic card of a scene: what becomes visible, which representations are linked, which misconception is addressed */
S.didactics = (host, sc) => {
  const d = sc.didactics; if (!d) return;
  const det = el('details', { class: 'em-didactics em-tool' }); const sm = el('summary', {}, 'Wozu diese Darstellung?'); sm.appendChild(el('small', {}, 'Konzept, Fehlvorstellung, Schlussfolgerung')); det.appendChild(sm);
  const dl = el('dl', { class: 'em-tool-body' });
  [['Was sichtbar wird', d.concept], ['Verbundene Darstellungen', (d.representations || []).join(' ↔ ')], ['Typische Fehlvorstellung', d.misconception], ['Was Sie verändern können', d.manipulate], ['Was Sie vorhersagen können', d.predict], ['Schlussfolgerung', d.conclusion]]
    .filter(([, v]) => v).forEach(([k, v]) => dl.append(el('dt', {}, k), el('dd', {}, v)));
  det.appendChild(dl); host.appendChild(det);
};
})();

/* ================================================================ renderers (one per generic scene type)
   Interface: mount(host, ctx) builds the SVG; update(trace, vars, {step, revealed}) draws the current state without
   motion; enter(step, trace, vars) plays the step's animation (returns a promise). Objects carry data-ref. */
(() => {
'use strict';
const S = window.EM.scene, { el, sv, fmt, tween, lerp } = S;
const attr = (e, a) => { for (const [k, v] of Object.entries(a)) e.setAttribute(k, String(v)); return e; };
const show = (e, on) => { if (e) e.classList.toggle('em-off', !on); };
const dot = (layer, cls) => layer.appendChild(sv('circle', { r: 6, class: 'em-pulse ' + cls, cx: -99, cy: -99 }));
/* a marker travelling along straight segments [[x0,y0],[x1,y1]] at once (signals through several edges in parallel) */
const travel = (layer, segs, cls, ms) => { const ds = segs.map(() => dot(layer, cls));
  return tween('travel-' + cls, ms, k => segs.forEach(([a, b], n) => attr(ds[n], { cx: lerp(a[0], b[0], k), cy: lerp(a[1], b[1], k), opacity: k < 1 ? 1 : 0 }))).then(() => ds.forEach(d => d.remove())); };

/* ---------------------------------------------------------------- network: forward, loss, backward, update */
S.types.network = () => {
  const P = { x1: [90, 105], x2: [90, 255], h1: [330, 105], h2: [330, 255], o: [560, 180] };
  let svg, ctx, layer, E = {}, last = null;
  const W = tr => [[tr.W1[0][0], tr.W1[0][1]], [tr.W1[1][0], tr.W1[1][1]]];
  const edges = [['w11', 'x1', 'h1'], ['w12', 'x2', 'h1'], ['w21', 'x1', 'h2'], ['w22', 'x2', 'h2'], ['v1', 'h1', 'o'], ['v2', 'h2', 'o']];
  const wval = (tr, r) => r[0] === 'w' ? tr.W1[+r[1] - 1][+r[2] - 1] : tr.W2[+r[1] - 1];
  const actBox = { x: 478, y: 300, w: 200, h: 84 };
  const ax = z => actBox.x + (z + 6) / 12 * actBox.w, ay = (a, ha) => { const lo = ha === 'tanh' ? -1 : 0, hi = ha === 'relu' || ha === 'linear' ? 6 : 1; return actBox.y + actBox.h - (Math.max(lo, Math.min(hi, a)) - lo) / (hi - lo) * actBox.h; };
  return {
    mount(host, c) {
      ctx = c; svg = sv('svg', { viewBox: '0 -26 720 436', class: 'em-scene-svg', role: 'img', 'aria-label': 'Netz 2-2-1: Eingaben, verdeckte Neuronen, Ausgabe, Verlust' });
      svg.appendChild(sv('title', {}, 'Neuronales Netz mit aktuellen Werten'));
      /* layer captions: where the data flows from and to */
      [['Eingabe', 90], ['Verdeckte Schicht', 330], ['Ausgabe', 560], ['Verlust', 664]].forEach(([t, x]) => svg.appendChild(sv('text', { x, y: -8, 'text-anchor': 'middle', class: 'em-cap' }, t)));
      const gE = svg.appendChild(sv('g')), gN = svg.appendChild(sv('g')); layer = sv('g');
      for (const [r, a, b] of edges) {
        const [x1, y1] = P[a], [x2, y2] = P[b];
        E[r] = gE.appendChild(sv('line', { x1, y1, x2, y2, class: 'em-w', 'data-ref': r }));
        E[r + 'g'] = gE.appendChild(sv('line', { x1, y1, x2, y2, class: 'em-w-ghost em-off' }));
        const f = r[0] === 'v' ? .5 : .3, lx = x1 + (x2 - x1) * f, ly = y1 + (y2 - y1) * f + (r === 'w21' || r === 'w22' || r === 'v2' ? 17 : -9);
        const lab = gE.appendChild(sv('text', { x: lx, y: ly, class: 'em-wlab', 'text-anchor': 'middle', 'data-ref': r, 'data-drag': 'w', tabindex: 0, role: 'slider', 'aria-label': 'Gewicht ' + r + ' (Pfeil hoch/runter oder ziehen)' }));
        E[r + 'l'] = lab;
        E[r + 'h'] = gE.appendChild(sv('polyline', { points: `${x1},${y1} ${x2},${y2}`, class: 'em-hit', 'data-ref': r, 'data-drag': 'w' }));  /* wide invisible grip */
        { const g = gE.appendChild(sv('g', { 'data-ref': r, class: 'em-off' })); E[r + 'dg'] = g;   /* change of this weight in the update */
          E[r + 'd'] = g.appendChild(sv('text', { x: lx, y: ly + (r === 'w21' || r === 'w22' || r === 'v2' ? 16 : -16), class: 'em-grad', 'text-anchor': 'middle' })); }
      }
      const node = (k, label) => { const [x, y] = P[k]; const g = gN.appendChild(sv('g', { 'data-ref': k, class: 'em-nd' + (k[0] === 'h' ? ' em-sel' : '') }));
        g.appendChild(sv('circle', { cx: x, cy: y, r: 31 })); g.appendChild(sv('text', { x, y: y - 4, 'text-anchor': 'middle', class: 'em-nd-t' }, label));
        E[k + 'v'] = g.appendChild(sv('text', { x, y: y + 14, 'text-anchor': 'middle', class: 'em-nd-v' })); return g; };
      node('x1', 'x₁'); node('x2', 'x₂'); E.h1 = node('h1', 'h₁'); E.h2 = node('h2', 'h₂'); node('o', 'ŷ');
      ['h1', 'h2'].forEach((k, j) => { E[k].setAttribute('tabindex', '0'); E[k].setAttribute('role', 'button'); E[k].setAttribute('aria-label', 'Neuron h' + (j + 1) + ' auswählen');
        const pick = () => ctx.setVar('j', j); E[k].addEventListener('click', pick); E[k].addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pick(); } }); });
      const bias = (r, k, dy) => { const [x, y] = P[k]; const g = gN.appendChild(sv('g', { 'data-ref': r, class: 'em-bias' })); g.appendChild(sv('line', { x1: x, y1: y + dy * .55, x2: x, y2: y + dy, class: 'em-bias-l' }));
        E[r] = g.appendChild(sv('text', { x, y: y + dy + (dy < 0 ? -4 : 14), 'text-anchor': 'middle' })); };
      bias('b1', 'h1', -52); bias('b2', 'h2', 52); bias('c', 'o', -56);
      E.z = gN.appendChild(sv('text', { class: 'em-zlab', 'data-ref': 'z' }));
      const lg = gN.appendChild(sv('g', { 'data-ref': 'L', class: 'em-lossbox' }));
      lg.appendChild(sv('rect', { x: 618, y: 140, width: 92, height: 80, rx: 8 })); lg.appendChild(sv('text', { x: 664, y: 162, 'text-anchor': 'middle', class: 'em-nd-t' }, 'Verlust L'));
      E.L = lg.appendChild(sv('text', { x: 664, y: 184, 'text-anchor': 'middle', class: 'em-nd-v' })); E.t = lg.appendChild(sv('text', { x: 664, y: 206, 'text-anchor': 'middle', class: 'em-nd-s', 'data-ref': 't' }));
      gN.appendChild(sv('line', { x1: 591, y1: 180, x2: 618, y2: 180, class: 'em-w em-w-loss' }));
      const ag = gN.appendChild(sv('g', { 'data-ref': 'act', class: 'em-act' })); E.act = ag;
      ag.appendChild(sv('rect', { x: actBox.x - 8, y: actBox.y - 14, width: actBox.w + 16, height: actBox.h + 30, rx: 6, class: 'em-inset' }));
      E.actCurve = ag.appendChild(sv('polyline', { class: 'em-act-curve' })); E.actAxis = ag.appendChild(sv('line', { x1: actBox.x, x2: actBox.x + actBox.w, class: 'em-axis' }));
      E.actName = ag.appendChild(sv('text', { x: actBox.x, y: actBox.y - 2, class: 'em-nd-s' }));
      E.actV = ag.appendChild(sv('line', { class: 'em-act-guide' })); E.actH = ag.appendChild(sv('line', { class: 'em-act-guide' })); E.actPt = ag.appendChild(sv('circle', { r: 5, class: 'em-act-pt', 'data-ref': 'a' }));
      svg.appendChild(layer);
      /* direct manipulation: drag a weight label sideways, or use the arrow keys on it */
      let drag = null;
      /* drag sideways = change the weight; a click without movement on a hidden-layer edge selects neuron and input */
      svg.addEventListener('pointerdown', e => { const t = e.target.closest('[data-drag="w"]'); if (!t) return; drag = { r: t.dataset.ref, x: e.clientX, w: wval(last, t.dataset.ref), moved: false }; t.setPointerCapture(e.pointerId); e.preventDefault(); });
      svg.addEventListener('pointermove', e => { if (!drag) return; if (Math.abs(e.clientX - drag.x) < 3 && !drag.moved) return; drag.moved = true; const k = svg.viewBox.baseVal.width / svg.getBoundingClientRect().width; ctx.setParam(drag.r, Math.round((drag.w + (e.clientX - drag.x) * k * 0.01) * 1000) / 1000); });
      svg.addEventListener('pointerup', () => { if (drag && !drag.moved && drag.r[0] === 'w') { const r = drag.r; drag = null; ctx.setVar('j', +r[1] - 1); ctx.setVar('i', +r[2] - 1); return; } drag = null; });
      svg.addEventListener('keydown', e => { const t = e.target.closest('[data-drag="w"]'); if (!t || !['ArrowUp', 'ArrowDown'].includes(e.key)) return; e.preventDefault(); ctx.setParam(t.dataset.ref, Math.round((wval(last, t.dataset.ref) + (e.key === 'ArrowUp' ? .05 : -.05)) * 1000) / 1000); });
      host.appendChild(svg);
    },
    update(tr, v, { step, revealed }) {
      last = tr; const j = v.j, after = revealed.has('after'), cur = after ? tr.new : tr;
      const w = r => wval(cur, r);
      for (const [r] of edges) { const x = w(r); attr(E[r], { 'stroke-width': 1.2 + Math.min(7, Math.abs(x) * 4) }); E[r].classList.toggle('neg', x < 0);
        E[r + 'l'].textContent = r + ' = ' + fmt(x, 3); attr(E[r + 'g'], { 'stroke-width': 1.2 + Math.min(7, Math.abs(wval(tr, r)) * 4) }); show(E[r + 'g'], after); }
      /* the update made visible: change of every weight (−η·∂L/∂w, from the trace) on the update and comparison steps */
      const showD = !!step && (step.id === 'update' || after);
      for (const [r] of edges) { const dv = r[0] === 'w' ? tr.step.W1[+r[1] - 1][+r[2] - 1] : tr.step.W2[+r[1] - 1]; E[r + 'd'].textContent = 'Δ ' + (dv > 0 ? '+' : '') + fmt(dv, 4); show(E[r + 'dg'], showD); }
      E.x1v.textContent = fmt(tr.x[0], 2); E.x2v.textContent = fmt(tr.x[1], 2);
      const F = after ? tr.after : tr;
      [0, 1].forEach(k => { E['h' + (k + 1) + 'v'].textContent = revealed.has('a' + (k + 1)) || after ? 'a = ' + fmt(F.a1[k], 3) : ''; E['h' + (k + 1)].classList.toggle('em-picked', k === j); });
      E.ov.textContent = revealed.has('y') || after ? fmt(F.y, 4) : '';
      E.b1.textContent = 'b₁ = ' + fmt(cur.b1[0], 3); E.b2.textContent = 'b₂ = ' + fmt(cur.b1[1], 3); E.c.textContent = 'c = ' + fmt(cur.b2, 3);
      E.L.textContent = revealed.has('L') || after ? fmt(after ? tr.after.loss : tr.loss, 5) : '?'; E.t.textContent = 't = ' + fmt(tr.t, 2);
      const zr = revealed.has('z' + (j + 1)) || after; E.z.textContent = zr ? 'z' + '₁₂'[j] + ' = ' + fmt(F.z1[j], 4) : ''; attr(E.z, { x: P['h' + (j + 1)][0] + 40, y: P['h' + (j + 1)][1] + (j ? 44 : -38) });
      /* activation inset of the selected neuron */
      const ha = ctx.acts ? ctx.acts().ha : 'sigmoid', f = window.EM.models.act[ha][0];
      const pts = []; for (let z = -6; z <= 6.001; z += .25) pts.push(ax(z) + ',' + ay(f(z), ha)); attr(E.actCurve, { points: pts.join(' ') });
      const lo = ha === 'tanh' ? -1 : 0; attr(E.actAxis, { y1: ay(lo, ha), y2: ay(lo, ha) });
      E.actName.textContent = 'a = ' + ha + '(z) für h' + (j + 1);
      const z = Math.max(-6, Math.min(6, F.z1[j])), a = F.a1[j], sa = revealed.has('a' + (j + 1)) || after;
      attr(E.actPt, { cx: ax(z), cy: ay(a, ha), opacity: sa ? 1 : 0 }); attr(E.actV, { x1: ax(z), x2: ax(z), y1: ay(lo, ha), y2: ay(a, ha), opacity: sa ? 1 : 0 }); attr(E.actH, { x1: actBox.x, x2: ax(z), y1: ay(a, ha), y2: ay(a, ha), opacity: sa ? 1 : 0 });
    },
    enter(step, tr, v) {
      const a = step.anim; if (!a) return Promise.resolve();
      const seg = r => { const e = edges.find(x => x[0] === S.sub(r, v)); return [P[e[1]], P[e[2]]]; };
      if (a.kind === 'flow') return travel(layer, (a.edges || []).map(seg), 'fw', 900);
      if (a.kind === 'back') { const segs = (a.edges || []).map(r => seg(r).slice().reverse()); return segs.reduce((p, sg) => p.then(() => travel(layer, [sg], 'bw', 600)), travel(layer, [[[664, 180], P.o]], 'bw', 400)); }
      if (a.kind === 'act') { const ha = ctx.acts ? ctx.acts().ha : 'sigmoid', z = Math.max(-6, Math.min(6, tr.z1[v.j])), lo = ha === 'tanh' ? -1 : 0;
        return tween('act', 900, k => { const zz = lerp(-6, z, Math.min(1, k * 1.6)), aa = window.EM.models.act[ha][0](zz); attr(E.actPt, { cx: ax(zz), cy: ay(k < .6 ? lo : aa, ha), opacity: 1 }); attr(E.actV, { x1: ax(zz), x2: ax(zz), y2: ay(k < .6 ? lo : aa, ha) }); }); }
      if (a.kind === 'update') return tween('upd', 1100, k => edges.forEach(([r]) => { const x = lerp(wval(tr, r), wval(tr.new, r), k); attr(E[r], { 'stroke-width': 1.2 + Math.min(7, Math.abs(x) * 4) }); E[r + 'l'].textContent = r + ' = ' + fmt(x, 3); }));
      return Promise.resolve();
    },
  };
};

/* ---------------------------------------------------------------- chord lift: pairs of curve points -> 3-D */
S.types.chord = () => {
  let svg, ctx, E = {}, last = null, cam = { yaw: 0, elev: 90 }, rectK = 0, liftK = 1;
  const C = [360, 292], K = 126, N = 360, ZK = .62;
  const M = () => window.EM.models;
  const pr = (x, y, z) => { const cy = Math.cos(cam.yaw * Math.PI / 180), sy = Math.sin(cam.yaw * Math.PI / 180), ce = Math.cos(cam.elev * Math.PI / 180), se = Math.sin(cam.elev * Math.PI / 180);
    const xr = x * cy - y * sy, yr = x * sy + y * cy; return [C[0] + K * xr, C[1] - K * (yr * se + z * ce * ZK) + (90 - cam.elev) * .9]; };
  const P2 = p => pr(p[0], p[1], 0);
  const poly = pts => pts.map(p => p.map(n => n.toFixed(1)).join(',')).join(' ');
  const nearest = (cx, cy) => { let best = 0, bd = 1e18; for (let n = 0; n < 720; n++) { const u = n / 720, q = P2(M().curvePoint(u)), d = (q[0] - cx) ** 2 + (q[1] - cy) ** 2; if (d < bd) { bd = d; best = u; } } return Math.round(best * 1000) / 1000; };
  const draw = () => {
    const tr = last; if (!tr) return;
    const cur = []; for (let n = 0; n <= N; n++) cur.push(P2(M().curvePoint(n / N))); attr(E.curve, { points: poly(cur) });
    const pl = [[-1.6, -1.6], [1.6, -1.6], [1.6, 1.6], [-1.6, 1.6], [-1.6, -1.6]].map(p => pr(p[0], p[1], 0)); attr(E.plane, { points: poly(pl) });
    const zt = [pr(-1.6, -1.6, 0), pr(-1.6, -1.6, 2.6)]; attr(E.zaxis, { x1: zt[0][0], y1: zt[0][1], x2: zt[1][0], y2: zt[1][1] }); attr(E.zlab, { x: zt[1][0] + 6, y: zt[1][1] + 4 });
    /* surface of all unordered pairs: lines of constant s, coloured by height d */
    E.surf.replaceChildren(); const G = 24, H = 48;
    for (let a = 0; a < G; a++) { const pts = []; for (let b = 0; b <= H; b++) { const L = M().chordLift(a / G, b / H); pts.push(pr(L.lift[0], L.lift[1], L.lift[2])); } E.surf.appendChild(sv('polyline', { points: poly(pts) })); }
    const r = tr.rect, useRect = rectK > 0 && r;
    const tt = useRect ? lerpParam(tr.t, r.t, rectK) : tr.t;
    const L = M().chordLift(tr.s, tt), Pp = P2(L.P), Qp = P2(L.Q), Mp = P2(L.M), Xp = pr(L.M[0], L.M[1], L.d * liftK);
    attr(E.P, { cx: Pp[0], cy: Pp[1] }); attr(E.Q, { cx: Qp[0], cy: Qp[1] }); attr(E.PQ, { x1: Pp[0], y1: Pp[1], x2: Qp[0], y2: Qp[1] });
    attr(E.Pl, { x: Pp[0] + 10, y: Pp[1] - 8 }); attr(E.Ql, { x: Qp[0] + 10, y: Qp[1] - 8 }); attr(E.M, { cx: Mp[0], cy: Mp[1] }); attr(E.Ml, { x: Mp[0] + 9, y: Mp[1] + 16 });
    attr(E.d, { x1: Mp[0], y1: Mp[1], x2: Xp[0], y2: Xp[1] }); attr(E.X, { cx: Xp[0], cy: Xp[1] }); attr(E.Xl, { x: Xp[0] + 10, y: Xp[1] - 6 });
    attr(E.dl, { x: (Mp[0] + Xp[0]) / 2 - 8, y: (Mp[1] + Xp[1]) / 2, 'text-anchor': 'end' });
    if (r) { const c = r.corners.map(P2); attr(E.rect, { points: poly(c.concat([c[0]])) }); const U = c[1], V = c[3]; attr(E.U, { cx: U[0], cy: U[1] }); attr(E.V, { cx: V[0], cy: V[1] }); attr(E.UV, { x1: U[0], y1: U[1], x2: V[0], y2: V[1] });
      attr(E.Ul, { x: U[0] + 10, y: U[1] - 8 }); attr(E.Vl, { x: V[0] + 10, y: V[1] - 8 }); const Y = pr(r.MUV[0], r.MUV[1], r.dUV); attr(E.Y, { cx: Y[0], cy: Y[1] }); const Mu = P2(r.MUV); attr(E.dUV, { x1: Mu[0], y1: Mu[1], x2: Y[0], y2: Y[1] }); }
  };
  function lerpParam(a, b, k) { let d = b - a; if (d > .5) d -= 1; if (d < -.5) d += 1; return ((a + d * k) % 1 + 1) % 1; }
  return {
    mount(host, c) {
      ctx = c; svg = sv('svg', { viewBox: '0 0 720 470', class: 'em-scene-svg', role: 'img', tabindex: 0, 'data-drag': 'cam', 'aria-label': 'Geschlossene Kurve, Punktpaar und sein Bild im Raum (Pfeiltasten drehen die Ansicht)' });
      svg.appendChild(sv('title', {}, 'Sehnen-Lift: Punktpaar → (Mittelpunkt, Abstand)'));
      E.plane = svg.appendChild(sv('polyline', { class: 'em-plane', 'data-ref': 'plane' }));
      E.zaxis = svg.appendChild(sv('line', { class: 'em-axis', 'data-ref': 'zaxis' })); E.zlab = svg.appendChild(sv('text', { class: 'em-nd-s', 'data-ref': 'zaxis' }, 'Höhe = Abstand d'));
      E.surf = svg.appendChild(sv('g', { class: 'em-surf', 'data-ref': 'surface' }));
      E.curve = svg.appendChild(sv('polyline', { class: 'em-curve', 'data-ref': 'curve' }));
      E.rect = svg.appendChild(sv('polyline', { class: 'em-rect', 'data-ref': 'rect' }));
      E.UV = svg.appendChild(sv('line', { class: 'em-chord em-chord2', 'data-ref': 'UV' })); E.dUV = svg.appendChild(sv('line', { class: 'em-dist em-chord2', 'data-ref': 'UV' }));
      E.PQ = svg.appendChild(sv('line', { class: 'em-chord', 'data-ref': 'PQ' }));
      E.d = svg.appendChild(sv('line', { class: 'em-dist', 'data-ref': 'd' })); E.dl = svg.appendChild(sv('text', { class: 'em-lab r-distance', 'data-ref': 'd' }, 'd'));
      E.M = svg.appendChild(sv('circle', { r: 5, class: 'em-pt r-midpoint', 'data-ref': 'M' })); E.Ml = svg.appendChild(sv('text', { class: 'em-lab r-midpoint', 'data-ref': 'M' }, 'M'));
      E.X = svg.appendChild(sv('circle', { r: 7, class: 'em-pt r-lift', 'data-ref': 'X' })); E.Xl = svg.appendChild(sv('text', { class: 'em-lab r-lift', 'data-ref': 'X' }, 'Bildpunkt'));
      E.Y = svg.appendChild(sv('circle', { r: 11, class: 'em-pt em-ring', 'data-ref': 'Y' }));
      E.U = svg.appendChild(sv('circle', { r: 6, class: 'em-pt r-point_u', 'data-ref': 'U' })); E.Ul = svg.appendChild(sv('text', { class: 'em-lab r-point_u', 'data-ref': 'U' }, 'U'));
      E.V = svg.appendChild(sv('circle', { r: 6, class: 'em-pt r-point_u', 'data-ref': 'V' })); E.Vl = svg.appendChild(sv('text', { class: 'em-lab r-point_u', 'data-ref': 'V' }, 'V'));
      const handle = (k, lab) => { const h = svg.appendChild(sv('circle', { r: 9, class: 'em-pt em-handle r-point_' + k.toLowerCase(), 'data-ref': k, 'data-drag': k, tabindex: 0, role: 'slider', 'aria-label': 'Punkt ' + k + ' auf der Kurve verschieben (Pfeiltasten oder ziehen)' }));
        E[k + 'l'] = svg.appendChild(sv('text', { class: 'em-lab r-point_' + k.toLowerCase(), 'data-ref': k }, lab)); return h; };
      E.P = handle('P', 'P'); E.Q = handle('Q', 'Q');
      let drag = null;
      const toSvg = e => { const b = svg.getBoundingClientRect(), vb = svg.viewBox.baseVal; return [vb.x + (e.clientX - b.left) / b.width * vb.width, vb.y + (e.clientY - b.top) / b.height * vb.height]; };
      svg.addEventListener('pointerdown', e => { const h = e.target.closest('[data-drag="P"],[data-drag="Q"]'); drag = h ? { k: h.dataset.drag } : (cam.elev < 89 ? { cam: [e.clientX, e.clientY, cam.yaw, cam.elev] } : null); if (drag) { svg.setPointerCapture(e.pointerId); e.preventDefault(); } });
      svg.addEventListener('pointermove', e => { if (!drag) return; if (drag.k) { const [x, y] = toSvg(e); ctx.setParam(drag.k === 'P' ? 's' : 't', nearest(x, y)); }
        else { cam.yaw = drag.cam[2] + (e.clientX - drag.cam[0]) * .4; cam.elev = Math.max(8, Math.min(90, drag.cam[3] - (e.clientY - drag.cam[1]) * .3)); draw(); } });
      svg.addEventListener('pointerup', () => { drag = null; });
      svg.addEventListener('keydown', e => { const h = e.target.closest('[data-drag="P"],[data-drag="Q"]');
        if (h && ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) { e.preventDefault(); const k = h.dataset.drag === 'P' ? 's' : 't', d = (e.key === 'ArrowUp' || e.key === 'ArrowRight') ? .005 : -.005; ctx.setParam(k, Math.round((((last[k] + d) % 1) + 1) % 1 * 1000) / 1000); return; }
        if (e.target === svg && ['ArrowLeft', 'ArrowRight'].includes(e.key)) { e.preventDefault(); cam.yaw += e.key === 'ArrowLeft' ? -10 : 10; draw(); } });
      host.appendChild(svg);
    },
    update(tr, v, { step, revealed }) {
      last = tr; const three = step.camera === '3d';
      if (!S.tweening) { cam = three ? { yaw: cam.elev < 89 ? cam.yaw : -32, elev: cam.elev < 89 ? cam.elev : 30 } : { yaw: 0, elev: 90 }; }
      rectK = revealed.has('rect') ? 1 : 0; liftK = 1;
      const on = { PQ: revealed.has('PQ'), M: revealed.has('M'), d: revealed.has('d'), X: revealed.has('X'), surface: revealed.has('surface'), rect: revealed.has('rect'), plane: three, zaxis: three };
      for (const [k, list] of Object.entries({ PQ: ['PQ'], M: ['M', 'Ml'], d: ['d', 'dl'], X: ['X', 'Xl'], surface: ['surf'], rect: ['rect', 'U', 'V', 'UV', 'Ul', 'Vl', 'Y', 'dUV'], plane: ['plane'], zaxis: ['zaxis', 'zlab'] })) list.forEach(n => show(E[n], on[k]));
      svg.dataset.cam = three ? '3d' : 'top'; draw();
    },
    enter(step, tr, v) {
      const a = step.anim; if (!a) return Promise.resolve();
      if (a.kind === 'camera') { const to = a.to === '3d' ? { yaw: -32, elev: 30 } : { yaw: 0, elev: 90 }, from = { ...cam }; S.tweening = true;
        return tween('cam', 1400, k => { cam = { yaw: lerp(from.yaw, to.yaw, k), elev: lerp(from.elev, to.elev, k) }; draw(); }).then(() => { S.tweening = false; }); }
      if (a.kind === 'lift') return tween('lift', 1100, k => { liftK = k; draw(); });
      if (a.kind === 'seek') return tween('seek', 1600, k => { rectK = k; draw(); });
      return Promise.resolve();
    },
  };
};

/* ---------------------------------------------------------------- cash flow as a process along the time axis */
S.types.cashflow = () => {
  let svg, E = {}, last = null, drawn = null, unit = 'k€';
  const X0 = 112, X1 = 744, lane = { sale: [24, 112], pay: [148, 226], out: [244, 346], bal: [372, 492] };
  const xc = (i, T) => X0 + (i + .5) * (X1 - X0) / T;
  const draw = (tr, prog, ghost) => {
    const T = tr.cf.length, cw = (X1 - X0) / T, bw = Math.min(34, cw * .56);
    const mx = Math.max(1, ...tr.sales.map(s => s.amount), ...tr.rows.map(r => r.cost + r.invest)), hs = 84 / mx;  /* one scale for all money lanes */
    E.cols.replaceChildren(); E.sales.replaceChildren(); E.arcs.replaceChildren(); E.pays.replaceChildren(); E.outs.replaceChildren(); E.ticks.replaceChildren();
    for (let i = 0; i < T; i++) { E.cols.appendChild(sv('rect', { x: X0 + i * cw + 1, y: 24, width: cw - 2, height: 474, class: 'em-col', 'data-ref': 'col' + (i + 1) }));
      E.ticks.appendChild(sv('text', { x: xc(i, T), y: 512, 'text-anchor': 'middle', class: 'em-tick' }, 'P' + (i + 1))); }
    const sh = ghost ? ghost.shift : 0;
    tr.sales.forEach(s => { const i = s.period - 1, h = s.amount * hs, x = xc(i, T);
      E.sales.appendChild(sv('rect', { x: x - bw / 2, y: lane.sale[1] - h, width: bw, height: h, class: 'em-tok-sale', 'data-ref': 'sale' + s.period }));
      if (cw > 30) E.sales.appendChild(sv('text', { x, y: lane.sale[1] - h - 4, 'text-anchor': 'middle', class: 'em-amt' }, fmt(s.amount, 0)));
      const pi = lerp(i + (ghost ? ghost.from : tr.delay), i + tr.delay, sh), xp = X0 + (pi + .5) * cw, inside = pi < T - 1e-9;
      const xe = inside ? xp : X1 + 8;
      E.arcs.appendChild(sv('path', { d: `M${x},${lane.sale[1] + 2} C${x},${lane.sale[1] + 40} ${xe},${lane.pay[0] - 46} ${xe},${lane.pay[0] - 2}`, class: 'em-arc' + (inside ? '' : ' em-late'), 'data-ref': 'term' }));
      if (inside) { E.pays.appendChild(sv('rect', { x: xp - bw / 2, y: lane.pay[1] - h, width: bw, height: h, class: 'em-tok-pay', 'data-ref': 'in' + (Math.round(pi) + 1) })); if (cw > 30) E.pays.appendChild(sv('text', { x: xp, y: lane.pay[1] - h - 4, 'text-anchor': 'middle', class: 'em-amt' }, fmt(s.amount, 0))); }
    });
    tr.rows.forEach((r, i) => { const x = xc(i, T); let y = lane.out[0];
      for (const [k, cls, ref] of [['cost', 'em-tok-cost', 'cost'], ['invest', 'em-tok-inv', 'inv']]) { const h = r[k] * hs; E.outs.appendChild(sv('rect', { x: x - bw / 2, y, width: bw, height: h, class: cls, 'data-ref': ref + (i + 1) })); y += h; }
      /* every period has an inflow object (height 0 when nothing arrives), so a formula term always has its figure */
      if (!E.pays.querySelector('[data-ref="in' + (i + 1) + '"]')) E.pays.appendChild(sv('rect', { x: x - bw / 2, y: lane.pay[1] - .01, width: bw, height: .01, class: 'em-tok-pay em-empty', 'data-ref': 'in' + (i + 1) })); });
    /* cumulative balance, built period by period */
    const bal = ghost ? tr.balance.map((b, i) => lerp(ghost.bal[i] ?? b, b, sh)) : tr.balance;
    const lo = Math.min(0, ...bal, ...tr.alt.balance), hi = Math.max(0, ...bal, ...tr.alt.balance), yb = v => lane.bal[1] - (v - lo) / ((hi - lo) || 1) * (lane.bal[1] - lane.bal[0]);
    attr(E.zero, { x1: X0, x2: X1, y1: yb(0), y2: yb(0) }); attr(E.zl, { x: X0 - 6, y: yb(0) + 4 });
    const n = Math.max(0, Math.min(T, prog)), pts = bal.slice(0, n).map((b, i) => [xc(i, T), yb(b)]);
    attr(E.line, { points: pts.map(p => p.join(',')).join(' ') });
    E.dots.replaceChildren(...pts.map((p, i) => sv('circle', { cx: p[0], cy: p[1], r: 4, class: 'em-bal-dot', 'data-ref': 'bal' + (i + 1) })));
    const area = pts.length ? [[pts[0][0], yb(0)], ...pts.map(([x, y]) => [x, Math.max(y, yb(0))]), [pts[pts.length - 1][0], yb(0)]] : [];
    attr(E.area, { points: area.map(p => p.join(',')).join(' ') });
    attr(E.alt, { points: tr.alt.balance.map((b, i) => [xc(i, T), yb(b)].join(',')).join(' ') });
    const k = tr.min_index, mx2 = xc(k, T); attr(E.need, { x1: mx2, x2: mx2, y1: yb(0), y2: yb(tr.balance[k]) }); attr(E.needl, { x: mx2 + (k > T / 2 ? -10 : 10), y: (yb(0) + yb(tr.balance[k])) / 2, 'text-anchor': k > T / 2 ? 'end' : 'start' });
    E.needl.textContent = 'Finanzierungsbedarf ' + fmt(tr.financing_need, 0) + ' ' + unit;
    /* cash flow of each computed period above the curve: the curve falls while it is negative and turns where it changes sign */
    E.cfs.replaceChildren(...tr.cf.slice(0, n).map((c, i) => sv('text', { x: xc(i, T), y: lane.bal[0] - 6, 'text-anchor': 'middle', class: 'em-cf ' + (c < 0 ? 'neg' : 'pos'), 'data-ref': 'bal' + (i + 1) }, (c > 0 ? '+' : '') + fmt(c, 0))));
    const turn = k + 1 < T && tr.cf[k] < 0 && tr.cf[k + 1] > 0;
    E.why.textContent = turn ? 'Bis P' + (k + 1) + ' Cashflow < 0, ab P' + (k + 2) + ' > 0: die Kurve wendet' : '';
    attr(E.why, { x: mx2 + (k > T / 2 ? -10 : 10), y: (yb(0) + yb(tr.balance[k])) / 2 + 18, 'text-anchor': k > T / 2 ? 'end' : 'start' });
    E.terml.textContent = 'Zahlungsziel z = ' + tr.delay + (tr.delay === 1 ? ' Periode' : ' Perioden');
  };
  return {
    mount(host, c) {
      unit = c.unit || unit; svg = sv('svg', { viewBox: '0 0 760 522', class: 'em-scene-svg', role: 'img', 'aria-label': 'Geschäftsvorgänge entlang der Zeitachse und kumulierte Liquidität' });
      svg.appendChild(sv('title', {}, 'Cashflow als Prozess'));
      E.cols = svg.appendChild(sv('g'));
      [['Verkauf|Rechnung', lane.sale, 'sale'], ['Zahlungs-|eingang', lane.pay, 'pay'], ['Aus-|zahlungen', lane.out, 'out'], ['Liquidität|kumuliert', lane.bal, 'bal']].forEach(([t, l, r]) => {
        { const tt = svg.appendChild(sv('text', { x: 4, y: l[0] + 14, class: 'em-lane-t' })); t.split('|').forEach((w, n) => tt.appendChild(sv('tspan', { x: 4, dy: n ? 15 : 0 }, w))); } const g = svg.appendChild(sv('g', { 'data-ref': 'lane-' + r, class: 'em-lane' })); g.appendChild(sv('rect', { x: X0, y: l[0], width: X1 - X0, height: l[1] - l[0], class: 'em-lane-bg' })); g.appendChild(sv('line', { x1: X0, x2: X1, y1: l[1], y2: l[1], class: 'em-axis' })); });
      E.sales = svg.appendChild(sv('g')); E.arcs = svg.appendChild(sv('g', { class: 'em-arcs' })); E.pays = svg.appendChild(sv('g')); E.outs = svg.appendChild(sv('g'));
      E.terml = svg.appendChild(sv('text', { x: X1, y: lane.pay[0] + 12, 'text-anchor': 'end', class: 'em-lab r-term', 'data-ref': 'term' }));
      E.zero = svg.appendChild(sv('line', { class: 'em-zero' })); E.zl = svg.appendChild(sv('text', { 'text-anchor': 'end', class: 'em-tick' }, '0'));
      E.area = svg.appendChild(sv('polygon', { class: 'em-deficit', 'data-ref': 'deficit' }));
      E.alt = svg.appendChild(sv('polyline', { class: 'em-bal-alt', 'data-ref': 'alt' }));
      E.line = svg.appendChild(sv('polyline', { class: 'em-bal', 'data-ref': 'balance' })); E.dots = svg.appendChild(sv('g'));
      E.need = svg.appendChild(sv('line', { class: 'em-need', 'data-ref': 'need' })); E.needl = svg.appendChild(sv('text', { class: 'em-lab r-need', 'data-ref': 'need' }));
      E.cfs = svg.appendChild(sv('g')); E.why = svg.appendChild(sv('text', { class: 'em-why-min', 'data-ref': 'need' }));
      E.ticks = svg.appendChild(sv('g')); host.appendChild(svg);
    },
    update(tr, v, { step, revealed }) {
      const T = tr.cf.length, prog = revealed.has('balance') ? T : (step.vars && 'k' in step.vars ? step.vars.k + 1 : 0);
      const changed = drawn && drawn.delay !== tr.delay && drawn.T === T;
      if (changed && !S.motion.reduced) { const ghost = { from: drawn.delay, bal: drawn.balance, shift: 0 }; const tr0 = tr;
        tween('cash-shift', 900, k => { ghost.shift = k; draw(tr0, prog, ghost); }); }
      else draw(tr, prog, null);
      drawn = { delay: tr.delay, T, balance: tr.balance.slice() }; last = tr;
      const vis = { arcs: revealed.has('term'), pays: revealed.has('term'), outs: revealed.has('out'), need: revealed.has('need'), needl: revealed.has('need'), why: revealed.has('need'), alt: revealed.has('alt'), terml: revealed.has('term') };
      for (const [k, on] of Object.entries(vis)) show(E[k], on);
      svg.dataset.progress = String(prog);
    },
    enter(step, tr, v) {
      const a = step.anim; if (!a) return Promise.resolve();
      if (a.kind === 'arcs') { const ps = [...E.arcs.querySelectorAll('path')]; ps.forEach(p => { const L = p.getTotalLength(); p.style.strokeDasharray = L; p.style.strokeDashoffset = L; });
        return tween('arcs', 1300, k => ps.forEach(p => { p.style.strokeDashoffset = String(p.getTotalLength() * (1 - k)); })).then(() => ps.forEach(p => { p.style.strokeDasharray = ''; p.style.strokeDashoffset = ''; })); }
      if (a.kind === 'period') { const k = step.vars.k, T = tr.cf.length; const g = [...svg.querySelectorAll('[data-ref="in' + (k + 1) + '"],[data-ref="cost' + (k + 1) + '"],[data-ref="inv' + (k + 1) + '"]')];
        g.forEach(e => e.classList.add('em-flash')); const d = svg.querySelector('[data-ref="bal' + (k + 1) + '"]');
        return tween('per', 650, q => { if (d) attr(d, { r: 4 + 5 * Math.sin(Math.PI * q) }); }).then(() => g.forEach(e => e.classList.remove('em-flash'))); }
      return Promise.resolve();
    },
  };
};
})();
