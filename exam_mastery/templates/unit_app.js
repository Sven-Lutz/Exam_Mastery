(() => {
'use strict';
const U = JSON.parse(document.getElementById('unit-data').textContent);
const MODE = document.body.dataset.mode;
const KEY = 'em-unit-' + U.id, DAY = 864e5, BOX = [0, 1, 3, 7, 16, 35];
const STAGE = {recall: 'Abruf und Selbsterklärung', guided: 'Geführt', worked: 'Durchgerechnetes Beispiel', faded: 'Lückenschritt', hint: 'Mit Hinweisen', independent: 'Selbstständig', error: 'Fehleranalyse', proof: 'Beweis', transfer: 'Transfer'};
const KC_SECTION = Object.fromEntries(Object.entries(U.kc_map || {}).map(([k, m]) => [k, m.sections[0]]));
const seqOf = v => String(v).trim().split(/\s+/).filter(Boolean).map(x => x.toUpperCase().replace(/^0$/, 'O'));
const SUPPORTED_STAGES = ['worked', 'faded'];
const KCS = U.kcs;
const SECTION_KC = {spannen: 'spans', rnn: 'birnn', birnn: 'birnn', attention: 'attention', position: 'position', struktur: 'decoding', prf: 'prf', einheit: 'prf-level', mittelung: 'micro-macro', fallstudie: 'decoding'};
const FORMS = U.exam_forms;
const EXAM = Object.values(FORMS).flat();

// ---------- state: versioned, validated, never silently lost ----------
const blank = () => ({v: 2, attempts: [], exams: [], cards: {}, visited: {}, last: null, predictions: []});
const notices = [];
function valid(s) {
  return s && typeof s === 'object' && Array.isArray(s.attempts) && Array.isArray(s.exams) && s.cards && typeof s.cards === 'object'
    && s.attempts.every(a => a && typeof a.task === 'string' && typeof a.ts === 'number' && typeof a.correct === 'boolean')
    && s.exams.every(e => e && typeof e.ts === 'number' && Array.isArray(e.items));
}
function migrate(s) {
  if (s.v === 2) return s;
  // v1 had no exam forms; its exam results are kept but never counted as delayed evidence.
  return Object.assign(blank(), s, {v: 2, exams: (s.exams || []).map(e => ({...e, form: e.form || 'v1', items: e.items.map(i => ({...i, legacy: true}))})), predictions: []});
}
let storageOK = true;
function load() {
  let raw = null;
  try { raw = localStorage.getItem(KEY); } catch (e) { storageOK = false; notices.push('Dieser Browser erlaubt kein lokales Speichern (z. B. privates Fenster oder gesperrte Website-Daten). Ihr Fortschritt geht beim Schließen verloren; sichern Sie ihn unter „Fortschritt → Exportieren“.'); return blank(); }
  if (!raw) return blank();
  try {
    const s = migrate(JSON.parse(raw));
    if (!valid(s)) throw new Error('schema');
    return Object.assign(blank(), s);
  } catch (e) {
    const backup = KEY + '-beschaedigt-' + Date.now();
    try { localStorage.setItem(backup, raw); } catch (_) { /* ignore */ }
    notices.push(`Der gespeicherte Lernstand war beschädigt und wurde unverändert unter „${backup}“ gesichert. Sie beginnen mit einem leeren Stand.`);
    return blank();
  }
}
let st = load();
function save() {
  if (!storageOK) return false;
  try { localStorage.setItem(KEY, JSON.stringify(st)); return true; }
  catch (e) { storageOK = false; notices.push('Speichern ist fehlgeschlagen (Speicher voll oder gesperrt). Exportieren Sie Ihren Fortschritt.'); render(); return false; }
}
const now = () => Date.now();

// ---------- helpers ----------
const el = (tag, attrs = {}, ...kids) => {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'html') n.innerHTML = v; else if (k.startsWith('on')) n.addEventListener(k.slice(2), v);
    else if (v !== false && v != null) n.setAttribute(k, v === true ? '' : v);
  }
  for (const c of kids.flat()) if (c != null && c !== false) n.append(c.nodeType ? c : document.createTextNode(c));
  return n;
};
const $ = (s, r = document) => r.querySelector(s);
// Typeset only nodes attached to the document: MathJax measures font metrics from the live layout;
// typesetting detached nodes can yield wrongly scaled glyphs (Issue #5).
const tex = node => (window.MathJax && MathJax.typesetPromise && node && node.isConnected) ? MathJax.typesetPromise([node]).catch(() => {}) : Promise.resolve();
const de = (x, d = 4) => x == null ? 'nicht definiert' : Number(x).toFixed(d).replace('.', ',');
const dt = (x, d = 4) => (x < 0 ? '-' : '') + Math.abs(Number(x)).toFixed(d).replace('.', '{,}');
function parseNum(s) {
  s = String(s).trim().replace(/\s/g, '').replace(/\u2212/g, '-').replace(',', '.');
  if (!s) return null;
  const m = s.match(/^(-?\d+(?:\.\d+)?)\/(\d+(?:\.\d+)?)$/);
  if (m) return +m[2] === 0 ? null : {v: +m[1] / +m[2], exact: true};
  if (!/^-?\d+(\.\d+)?$/.test(s)) return null;
  return {v: +s, exact: false, dec: (s.split('.')[1] || '').length};
}
function numOk(input, a) {
  const p = parseNum(input); if (!p) return null;
  const v = a.float, tol = a.tol || 0.0005;
  if (p.exact) return Math.abs(p.v - v) <= 1e-9;
  if (Math.abs(p.v - v) <= tol) return true;
  return p.dec >= 2 && Number(v.toFixed(p.dec)) === p.v;
}
function diagnose(input, a) {
  const p = parseNum(input); if (!p) return null;
  for (const d of a.diagnoses || []) { const q = parseNum(d.value); if (q && Math.abs(q.v - p.v) <= 0.0006) return d.msg; }
  return null;
}
const parseSet = s => String(s).split(/[,;\s]+/).filter(Boolean).map(Number).sort((x, y) => x - y);

// ---------- learner model ----------
// An attempt is "supported" if the learner saw a worked/faded solution path, used a hint, revealed the solution
// or graded themselves. Only first attempts without any support count as unsupported practice evidence.
const supported = a => SUPPORTED_STAGES.includes(a.stage) || a.hints > 0 || !!a.revealed || !!a.self;
function series() {
  const s = {assisted: [], unsupported: [], immediate: [], delayed: [], transfer: []};
  for (const a of st.attempts) (supported(a) ? s.assisted : a.first ? s.unsupported : s.assisted).push(a);
  for (const ex of st.exams) for (const it of ex.items) {
    if (it.legacy) continue;
    (ex.delayed && ex.delayed[it.kc] ? s.delayed : s.immediate).push(it);
    if (it.transfer) s.transfer.push(it);
  }
  return s;
}
function lastActivity(kc, before) {
  const ts = [...st.attempts.filter(a => a.kc === kc && a.ts < before).map(a => a.ts),
    ...st.exams.filter(e => e.ts < before && e.items.some(i => i.kc === kc)).map(e => e.ts)];
  return ts.length ? Math.max(...ts) : null;
}
function kcSessions(kc) {
  return st.exams.filter(e => e.items.some(i => i.kc === kc && !i.legacy)).map(e => {
    const its = e.items.filter(i => i.kc === kc);
    return {ts: e.ts, form: e.form, n: its.length, passed: its.length >= 2 && its.every(i => i.correct), delayed: !!(e.delayed && e.delayed[kc])};
  });
}
const LEVELS = {
  NICHT_GEPRUEFT: ['Nicht geprüft', 'Noch keine Prüfung ohne Hilfe.'],
  LUECKE: ['Lücke', 'In der letzten Prüfung ohne Hilfe nicht alle Aufgaben dieser Kompetenz gelöst.'],
  SOFORT: ['Geprüft (sofort)', 'Ohne Hilfe bestanden, aber weniger als 24 h nach dem Üben – zeigt Kurzzeitleistung.'],
  VERZOEGERT: ['Wahrscheinlich sicher', 'Mindestens 24 h nach dem letzten Üben mit neuen Aufgaben ohne Hilfe bestanden.'],
  BEHALTEN: ['Behalten belegt (≥ 7 Tage)', 'Zwei verzögerte Prüfungen mit unterschiedlichen Aufgaben, mindestens 7 Tage auseinander, beide bestanden.']
};
function kcLevel(kc) {
  const ss = kcSessions(kc);
  if (!ss.length) return 'NICHT_GEPRUEFT';
  const last = ss[ss.length - 1];
  if (!last.passed) return 'LUECKE';
  if (!last.delayed) return 'SOFORT';
  const earlier = ss.slice(0, -1).filter(s => s.passed && s.delayed && s.form !== last.form && last.ts - s.ts >= 7 * DAY);
  return earlier.length ? 'BEHALTEN' : 'VERZOEGERT';
}
function record(task, correct, extra) {
  const first = !st.attempts.some(a => a.task === task.id);
  st.attempts.push({task: task.id, kc: task.kc, stage: task.stage, ts: now(), correct, first, hints: 0, revealed: false, ...extra});
  save();
}
function introduceCards(kc) {
  for (const c of U.cards) if (c.kc === kc && !st.cards[c.key]) st.cards[c.key] = {box: 0, due: now()};
  save();
}
const dueCards = () => U.cards.filter(c => st.cards[c.key] && st.cards[c.key].due <= now());
function nextForm() { const e = st.exams.filter(x => FORMS[x.form]); return e.length && e[e.length - 1].form === 'A' ? 'B' : 'A'; }

// ---------- metrics (same conventions as exam_mastery/seqlab.py; cross-checked by tests) ----------
function spans(tags) {
  const out = []; let cur = null;
  [...tags, 'O'].forEach((t, i) => {
    const typ = t === 'O' ? null : t.slice(2);
    const opens = t.startsWith('B-') || (t.startsWith('I-') && (!cur || cur.typ !== typ));
    if (t === 'O' || opens) { if (cur) out.push(`${cur.s}:${i}:${cur.typ}`); cur = t === 'O' ? null : {s: i, typ}; }
  });
  return new Set(out);
}
function spanCounts(g, p) { const G = spans(g), P = spans(p); let tp = 0; P.forEach(x => G.has(x) && tp++); return {tp, fp: P.size - tp, fn: G.size - tp}; }
function tokenCounts(g, p) {
  let tp = 0, fp = 0, fn = 0;
  g.forEach((gt, i) => { const a = gt === 'O' ? 'O' : gt.slice(2), b = p[i] === 'O' ? 'O' : p[i].slice(2);
    if (a === b) { if (a !== 'O') tp++; return; } if (b !== 'O') fp++; if (a !== 'O') fn++; });
  return {tp, fp, fn};
}
const ratio = (a, b) => b === 0 ? null : a / b;
const prf = c => ({P: ratio(c.tp, c.tp + c.fp), R: ratio(c.tp, c.tp + c.fn), F: ratio(2 * c.tp, 2 * c.tp + c.fp + c.fn),
  H: (c.tp > 0) ? 2 * (c.tp / (c.tp + c.fp)) * (c.tp / (c.tp + c.fn)) / (c.tp / (c.tp + c.fp) + c.tp / (c.tp + c.fn)) : null});
const caseOf = c => c.tp > 0 ? 'i' : c.fp > 0 && c.fn > 0 ? 'ii' : c.fp === 0 && c.fn > 0 ? 'iii' : c.fn === 0 && c.fp > 0 ? 'iv' : 'v';
window.__emMetrics = {spans: t => [...spans(t)], spanCounts, tokenCounts, prf, caseOf};
window.__emModel = {kcLevel, series, supported, nextForm, state: () => st};

// ---------- SVG ----------
const NS = 'http://www.w3.org/2000/svg';
const sv = (tag, attrs = {}, txt) => { const n = document.createElementNS(NS, tag); for (const [k, v] of Object.entries(attrs)) if (v != null) n.setAttribute(k, v); if (txt != null) n.textContent = txt; return n; };
function linkify(root) {
  root.querySelectorAll('[data-link]').forEach(n => {
    const on = v => root.querySelectorAll(`[data-link="${n.dataset.link}"]`).forEach(m => m.classList.toggle('lit', v));
    n.addEventListener('mouseenter', () => on(true)); n.addEventListener('mouseleave', () => on(false));
    n.addEventListener('focus', () => on(true)); n.addEventListener('blur', () => on(false));
  });
}

// ---------- scene engine: example -> prediction -> mechanism -> counterexample -> verification ----------
// ---------- scene engine v4: tweened steps, play/pause, reduced motion, predictions, print keyframes ----------
const REDUCED = !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) || MODE === 'print';
function lerp(a, b, u) {
  if (typeof a === 'number' && typeof b === 'number') return a + (b - a) * u;
  if (Array.isArray(a) && Array.isArray(b) && a.length === b.length) return a.map((x, i) => lerp(x, b[i], u));
  if (a && b && typeof a === 'object' && typeof b === 'object' && !Array.isArray(a)) { const o = {...b}; for (const k in b) if (k in a) o[k] = lerp(a[k], b[k], u); return o; }
  return b;
}
const ease = u => u < .5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2;
function Scene(root, spec, print) {
  let i = 0, cur = spec.steps[0].v || {}, raf = null, timer = null, playing = false;
  const fig = el('div', {class: 'scene-fig'}), cap = el('div', {class: 'scene-cap', 'aria-live': 'polite'}), eq = el('div', {class: 'scene-eq'});
  const dots = el('div', {class: 'dots', 'aria-hidden': 'true'}), pred = el('div', {class: 'predict'}), extra = el('div', {});
  const back = el('button', {onclick: () => { stop(); go(i - 1, false); }}, '← Zurück'), fwd = el('button', {class: 'primary', onclick: () => { stop(); go(i + 1); }}, 'Weiter →');
  const playB = el('button', {onclick: () => playing ? stop() : play(), 'aria-pressed': 'false'}, '▶ Abspielen');
  const restart = el('button', {onclick: () => { stop(); go(0, false); }}, 'Neu starten');
  const draw = (v, s, u = 1) => spec.legacy ? spec.draw(fig, s, extra) : spec.draw(fig, v, s, extra, u);
  if (print) {
    root.replaceChildren(el('h4', {}, spec.title));
    spec.steps.forEach((s, k) => { if (!s.key) return; const f = el('div', {class: 'scene-fig'}), x = el('div', {});
      (spec.legacy ? spec.draw(f, s, x) : spec.draw(f, s.v || {}, s, x, 1));
      root.append(el('figure', {class: 'keyframe'}, el('div', {class: 'kf-n'}, `${spec.fig || 'Abb.'} – Schritt ${k + 1} von ${spec.steps.length}`), f,
        el('figcaption', {}, el('div', {class: 'scene-cap', html: s.cap}), el('div', {class: 'scene-eq', html: s.eq || ''}),
          s.predict ? el('p', {class: 'q', html: `<b>Erst vorhersagen:</b> ${s.predict.q} <i>(Auflösung: ${s.predict.options[s.predict.correct]})</i>`}) : null))); });
    return;
  }
  root.replaceChildren(el('div', {class: 'scene-head'}, el('span', {class: 'stage'}, 'Erklärung in Schritten'), el('h4', {}, spec.title), spec.question ? el('p', {class: 'scene-q', html: '<b>Leitfrage:</b> ' + spec.question}) : null),
    fig, el('div', {class: 'scene-text'}, cap, eq, pred), extra, el('div', {class: 'ctl'}, back, fwd, playB, restart, dots));
  root.tabIndex = 0;
  root.addEventListener('keydown', e => { if (e.target !== root) return; if (e.key === 'ArrowRight' && !fwd.disabled) { stop(); go(i + 1); } if (e.key === 'ArrowLeft') { stop(); go(i - 1, false); } if (e.key === ' ') { e.preventDefault(); playing ? stop() : play(); } });
  const answered = {};
  function stop() { playing = false; clearTimeout(timer); playB.textContent = '▶ Abspielen'; playB.setAttribute('aria-pressed', 'false'); }
  function play() { playing = true; playB.textContent = '❚❚ Pause'; playB.setAttribute('aria-pressed', 'true'); tick(); }
  function tick() { if (!playing) return; const s = spec.steps[i]; if (i >= spec.steps.length - 1 || (s.predict && !(i in answered))) return stop(); go(i + 1); timer = setTimeout(tick, (spec.steps[i].dur || 900) + 1800); }
  function go(k, animate = true) {
    k = Math.max(0, Math.min(spec.steps.length - 1, k));
    const s = spec.steps[k], from = cur, to = s.v || {};
    i = k; cancelAnimationFrame(raf);
    const dur = (!animate || REDUCED) ? 0 : (s.dur || 900), t0 = performance.now();
    const frame = t => { const u = dur ? Math.min(1, (t - t0) / dur) : 1; draw(lerp(from, to, ease(u)), s, u); if (u < 1) raf = requestAnimationFrame(frame); else { cur = to; linkify(root); } };
    raf = requestAnimationFrame(frame); if (!dur) { draw(to, s, 1); cur = to; }
    cap.innerHTML = s.cap; eq.innerHTML = s.eq || '';
    dots.replaceChildren(...spec.steps.map((_, j) => el('span', {class: j === i ? 'on' : j < i ? 'done' : ''})));
    back.disabled = i === 0; fwd.disabled = i === spec.steps.length - 1;
    pred.replaceChildren();
    if (s.predict) {
      const p = s.predict, res = el('div', {});
      fwd.disabled = !(i in answered);
      pred.append(el('p', {class: 'q', html: '<b>Ihre Vorhersage:</b> ' + p.q}),
        el('div', {class: 'opts'}, p.options.map((o, k2) => el('button', {class: 'opt', html: o, onclick: () => {
          answered[i] = k2; st.predictions.push({scene: spec.id, step: i, choice: k2, correct: k2 === p.correct, ts: now()}); save();
          res.innerHTML = `<p class="fb ${k2 === p.correct ? 'ok' : 'bad'}">${k2 === p.correct ? 'Richtig.' : 'Nicht ganz.'} ${p.explain}</p>`;
          fwd.disabled = i === spec.steps.length - 1; tex(res);
        }}))), res);
      if (i in answered) res.innerHTML = `<p class="fb ${answered[i] === p.correct ? 'ok' : 'bad'}">${p.explain}</p>`;
    }
    tex(root).then(() => linkify(root));
  }
  go(0, false);
}
const C_FW = 'var(--fw)', C_BW = 'var(--bw)', C_W1 = '#2756c4', C_W2 = '#c2410c';
const clamp01 = x => Math.max(0, Math.min(1, x));

// ---- storyboard 1: BiRNN information flow (Washington signed / state) ----
function toyRun(sentence) {
  const E = U.toy.emb, xs = [E.Washington, E[sentence]];
  const step = (a, h, x) => [Math.tanh(a * h[0] + x[0]), Math.tanh(a * h[1] + x[1])];
  const f1 = step(U.toy.a_fw, [0, 0], xs[0]), f2 = step(U.toy.a_fw, f1, xs[1]);
  const b2 = step(U.toy.a_bw, [0, 0], xs[1]), b1 = step(U.toy.a_bw, b2, xs[0]);
  return {xs, f: [f1, f2], b: [b1, b2]};
}
const vec = v => `(${dt(v[0])};\\ ${dt(v[1])})`;
function sceneBirnn() {
  const A = toyRun('signed'), B = toyRun('state');
  const draw = (fig, v) => {
    const svg = sv('svg', {viewBox: '0 0 780 360', class: 'plot', role: 'img'});
    const defs = sv('defs'); [['gW', C_W1], ['gS', C_W2]].forEach(([id, c]) => { const g = sv('linearGradient', {id, x1: 0, x2: 1}); g.append(sv('stop', {offset: 0, 'stop-color': c}), sv('stop', {offset: 1, 'stop-color': c})); defs.append(g); });
    const mk = sv('marker', {id: 'ar4', viewBox: '0 0 8 8', refX: 7, refY: 4, markerWidth: 7, markerHeight: 7, orient: 'auto'}); mk.append(sv('path', {d: 'M0,0L8,4L0,8z', fill: 'var(--mute)'})); defs.append(mk); svg.append(defs);
    const alt = [];
    [['signed', A, 18], ['state', B, 402]].forEach(([w, R, x0]) => {
      svg.append(sv('rect', {x: x0, y: 8, width: 360, height: 344, rx: 14, fill: 'var(--panel)', stroke: 'var(--line)'}));
      svg.append(sv('text', {x: x0 + 16, y: 32, 'font-size': 14, 'font-weight': 600, fill: 'var(--ink)'}, `Satz ${w === 'signed' ? 'A' : 'B'}: „Washington ${w}“`));
      const X = t => x0 + 95 + t * 170, yIn = 312, yF = 230, yB = 150, yL = 72;
      const node = (cx, cy, val, prog, srcs, label, color, hl) => {
        const g = sv('g', {'data-link': label}); const wdt = 150, h = 46;
        g.append(sv('rect', {x: cx - wdt / 2, y: cy - h / 2, width: wdt, height: h, rx: 23, fill: 'var(--panel)', stroke: color, 'stroke-width': hl ? 3.2 : 1.6}));
        // provenance stripes: which inputs this state can depend on (fill grows with computation progress)
        srcs.forEach((c, k) => g.append(sv('rect', {x: cx - wdt / 2 + 14 + k * 10, y: cy - h / 2 + 6, width: 7, height: (h - 12) * prog, rx: 2, fill: c})));
        g.append(sv('text', {x: cx + 12, y: cy - 6, 'text-anchor': 'middle', 'font-size': 11, fill: color}, label.replace('f', '→').replace('b', '←').replace('h', 'h')));
        g.append(sv('text', {x: cx + 12, y: cy + 12, 'text-anchor': 'middle', 'font-size': 12.5, 'font-family': 'var(--mono)', fill: 'var(--ink)'}, prog > 0 ? `(${de(val[0] * prog)}; ${de(val[1] * prog)})` : '?'));
        svg.append(g);
      };
      // edges + travelling pulses
      const pulse = (x1, y1, x2, y2, u, c) => { if (u > 0 && u < 1) svg.append(sv('circle', {cx: x1 + (x2 - x1) * u, cy: y1 + (y2 - y1) * u, r: 6, fill: c, opacity: .9})); };
      for (let t = 0; t < 2; t++) {
        const pf = clamp01(v.fw - t), pb = clamp01(v.bw - (1 - t));
        svg.append(sv('line', {x1: X(t) - 30, y1: yIn - 18, x2: X(t) - 30, y2: yF + 23, stroke: pf > 0 ? C_FW : 'var(--line)', 'stroke-width': pf > 0 ? 2.5 : 1}));
        if (v.bw > 0 || v.showBw) svg.append(sv('line', {x1: X(t) + 30, y1: yIn - 18, x2: X(t) + 30, y2: yB + 23, stroke: pb > 0 ? C_BW : 'var(--line)', 'stroke-width': pb > 0 ? 2.5 : 1}));
        pulse(X(t) - 30, yIn - 18, X(t) - 30, yF + 23, pf * 1.3, t === 0 ? C_W1 : C_W2);
        if (v.bw > 0) pulse(X(t) + 30, yIn - 18, X(t) + 30, yB + 23, pb * 1.3, t === 0 ? C_W1 : C_W2);
      }
      const pf2 = clamp01(v.fw - 1), pb1 = clamp01(v.bw - 1);
      svg.append(sv('line', {x1: X(0) + 75, y1: yF, x2: X(1) - 77, y2: yF, stroke: pf2 > 0 ? C_FW : 'var(--line)', 'stroke-width': 2.5, 'marker-end': 'url(#ar4)'}));
      pulse(X(0) + 75, yF, X(1) - 77, yF, pf2 * 1.3, C_W1);
      if (v.bw > 0 || v.showBw) { svg.append(sv('line', {x1: X(1) - 75, y1: yB, x2: X(0) + 77, y2: yB, stroke: pb1 > 0 ? C_BW : 'var(--line)', 'stroke-width': 2.5, 'marker-end': 'url(#ar4)'})); pulse(X(1) - 75, yB, X(0) + 77, yB, pb1 * 1.3, C_W2); }
      ['Washington', w].forEach((word, t) => {
        svg.append(sv('rect', {x: X(t) - 66, y: yIn - 18, width: 132, height: 38, rx: 8, fill: 'var(--panel)', stroke: t === 0 ? C_W1 : C_W2, 'stroke-width': 2, 'data-link': 'e' + (t + 1)}));
        svg.append(sv('text', {x: X(t), y: yIn, 'text-anchor': 'middle', 'font-size': 14, fill: 'var(--ink)'}, word));
        svg.append(sv('text', {x: X(t), y: yIn + 14, 'text-anchor': 'middle', 'font-size': 11, fill: 'var(--mute)', 'font-family': 'var(--mono)'}, `e=(${R.xs[t].join(', ')})`));
      });
      node(X(0), yF, R.f[0], clamp01(v.fw), [C_W1], 'h1f', C_FW, v.hl === 1);
      node(X(1), yF, R.f[1], clamp01(v.fw - 1), [C_W1, C_W2], 'h2f', C_FW, v.hl === 2);
      if (v.bw > 0 || v.showBw) { node(X(0), yB, R.b[0], clamp01(v.bw - 1), [C_W1, C_W2], 'h1b', C_BW, v.hl === 3); node(X(1), yB, R.b[1], clamp01(v.bw), [C_W2], 'h2b', C_BW, v.hl === 4); }
      if (v.label > 0) {
        const bi = v.bi || 0, sc = R.b[0][1] * bi, txt = bi > .02 ? `${sc > 0 ? 'PER' : 'LOC'} · s = ${sc > 0 ? '+' : '−'}${de(Math.abs(sc))}` : 'gleich in A und B';
        svg.append(sv('rect', {x: X(0) - 82, y: yL - 20, width: 164, height: 36, rx: 8, fill: 'var(--panel)', stroke: 'var(--accent2)', 'stroke-width': 2, opacity: v.label}));
        svg.append(sv('text', {x: X(0), y: yL + 3, 'text-anchor': 'middle', 'font-size': 13, fill: 'var(--accent2)', 'font-weight': 600, opacity: v.label}, 'ŷ₁: ' + txt));
        svg.append(sv('line', {x1: X(0) - 45, y1: yL + 16, x2: X(0) - 45, y2: yF - 23, stroke: 'var(--accent2)', 'stroke-dasharray': '4 3', opacity: v.label}));
        if (bi > 0) svg.append(sv('line', {x1: X(0) + 45, y1: yL + 16, x2: X(0) + 45, y2: yB - 23, stroke: 'var(--accent2)', 'stroke-dasharray': '4 3', opacity: bi}));
      }
      alt.push(`Satz ${w}: Vorwärts ${de(v.fw, 1)} von 2, Rückwärts ${de(v.bw, 1)} von 2`);
    });
    svg.append(sv('text', {x: 20, y: 356, 'font-size': 11, fill: 'var(--mute)'}, 'Farbstreifen im Zustand = Wörter, von denen er abhängen kann (blau: Washington, orange: Wort 2).'));
    svg.setAttribute('aria-label', alt.join('; ')); fig.replaceChildren(svg);
  };
  const steps = [
    {key: true, v: {fw: 0, bw: 0, label: 0, bi: 0}, cap: 'Zwei Sätze, ein mehrdeutiges Wort. Nur Wort 2 unterscheidet sich (orange). Blau und Orange markieren ab jetzt, <em>woher</em> Information in einem Zustand stammen kann.', eq: '<span data-link="e1">\\(e_1=(1,0)\\)</span> in A und B; <span data-link="e2">\\(e_2=(0,1)\\)</span> in A, \\((0,-1)\\) in B.'},
    {v: {fw: 0, bw: 0, label: 0, bi: 0}, cap: 'Das Vorwärts-RNN berechnet gleich \\(h^{\\rightarrow}_1\\) aus \\(h^{\\rightarrow}_0=0\\) und \\(e_1\\).', eq: '\\(h^{\\rightarrow}_1=\\tanh(0{,}5\\cdot h^{\\rightarrow}_0+e_1)\\)',
      predict: {q: 'Wird \\(h^{\\rightarrow}_1\\) in Satz A und Satz B gleich sein?', options: ['gleich', 'verschieden', 'hängt von den Trainingsdaten ab'], correct: 0, explain: 'In der Formel für \\(h^{\\rightarrow}_1\\) kommt \\(e_2\\) nicht vor. Beobachten Sie gleich den Farbstreifen: nur Blau.'}},
    {key: true, dur: 1600, v: {fw: 1, bw: 0, label: 0, bi: 0, hl: 1}, cap: 'Ein Impuls läuft von „Washington“ nach <span data-link="h1f">\\(h^{\\rightarrow}_1\\)</span>. Der Zustand trägt nur einen blauen Streifen – und hat in A und B exakt denselben Wert.', eq: `\\(h^{\\rightarrow}_1=\\tanh\\big((1,0)\\big)=${vec(A.f[0])}\\) in A und B`},
    {key: true, dur: 1600, v: {fw: 2, bw: 0, label: 0, bi: 0, hl: 2}, cap: 'Jetzt fließt Information von \\(h^{\\rightarrow}_1\\) und vom zweiten Wort in <span data-link="h2f">\\(h^{\\rightarrow}_2\\)</span>: zwei Streifen. Erst hier unterscheiden sich die Sätze – im Vorzeichen der zweiten Komponente.', eq: `\\(h^{\\rightarrow}_2=\\tanh\\big(0{,}5\\,h^{\\rightarrow}_1+e_2\\big)=${vec(A.f[1])}\\) bzw. \\(${vec(B.f[1])}\\)`},
    {key: true, dur: 900, v: {fw: 2, bw: 0, label: 1, bi: 0}, cap: '<b>Gegenbeispiel.</b> Der Klassifikator für Wort 1 liest nur <span data-link="h1f">\\(h^{\\rightarrow}_1\\)</span>. Gleiche Eingabe heißt gleiche Ausgabe – für jede Wahl der Gewichte. Einer der beiden Sätze wird zwangsläufig falsch markiert.', eq: '\\(p(y_1\\mid\\text{A})=\\operatorname{softmax}(W_oh^{\\rightarrow}_1+b_o)=p(y_1\\mid\\text{B})\\)'},
    {v: {fw: 2, bw: 0, label: 1, bi: 0, showBw: 1}, cap: 'Was müsste der Zustand an Position 1 zusätzlich enthalten?', eq: '',
      predict: {q: 'Welche Farbe fehlt dem Zustand an Position 1?', options: ['Orange – Information über Wort 2', 'Blau', 'Keine; es fehlt Training'], correct: 0, explain: 'Wir brauchen einen Rechenweg von Wort 2 nach Position 1. Den liefert ein zweites RNN, das von rechts nach links liest.'}},
    {key: true, dur: 1600, v: {fw: 2, bw: 1, label: 1, bi: 0, hl: 4, showBw: 1}, cap: 'Das Rückwärts-RNN beginnt beim letzten Wort: <span data-link="h2b">\\(h^{\\leftarrow}_2\\)</span> trägt nur Orange.', eq: `\\(h^{\\leftarrow}_2=\\tanh(0{,}8\\cdot0+e_2)=${vec(A.b[1])}\\) bzw. \\(${vec(B.b[1])}\\)`},
    {key: true, dur: 1600, v: {fw: 2, bw: 2, label: 1, bi: 0, hl: 3, showBw: 1}, cap: 'Der Impuls läuft nach links: <span data-link="h1b">\\(h^{\\leftarrow}_1\\)</span> trägt Blau <em>und</em> Orange. Das Vorzeichen von Wort 2 ist bei Wort 1 angekommen.', eq: `\\(h^{\\leftarrow}_1=\\tanh\\big(0{,}8\\,h^{\\leftarrow}_2+e_1\\big)=${vec(A.b[0])}\\) bzw. \\(${vec(B.b[0])}\\)`},
    {key: true, dur: 1200, v: {fw: 2, bw: 2, label: 1, bi: 1, showBw: 1}, cap: 'Verketten und bewerten: Mit \\(v=(0,0,0,1)\\) liest der Score genau die zweite Komponente von \\(h^{\\leftarrow}_1\\). Beide Sätze werden richtig markiert.', eq: `\\(s=v^{\\top}[h^{\\rightarrow}_1;h^{\\leftarrow}_1]=${dt(A.b[0][1])}\\ (\\text{A: PER}),\\quad ${dt(B.b[0][1])}\\ (\\text{B: LOC})\\)`},
    {key: true, v: {fw: 2, bw: 2, label: 1, bi: 1, showBw: 1}, cap: '<b>Verallgemeinerung.</b> Die Farbstreifen sind genau die Abhängigkeitsmengen aus Satz 1 und 2: vorwärts \\(\\{1,\\dots,t\\}\\), rückwärts \\(\\{t,\\dots,T\\}\\), verkettet \\(\\{1,\\dots,T\\}\\).', eq: '\\(h^{\\rightarrow}_1=F_1(x_1),\\quad h^{\\leftarrow}_1=G_1(x_1,x_2)\\)'}
  ];
  return {id: 'birnn', fig: 'Abb. 4.1', title: 'Das Washington-Experiment: woher Information in einem Zustand stammt', question: 'Kann ein Tagger „Washington“ richtig markieren, wenn das entscheidende Wort erst danach kommt?', steps, draw};
}

// ---- storyboard 2: self-attention as geometry ----
function attnRow(q, K, V, scale = true, c = null) {
  const d = q.length, f = c != null ? c : (scale ? 1 / Math.sqrt(d) : 1);
  const e = K.map(k => k.reduce((a, x, i) => a + x * q[i], 0) * f);
  const m = Math.max(...e), ex = e.map(x => Math.exp(x - m)), z = ex.reduce((a, b) => a + b, 0), w = ex.map(x => x / z);
  return {e, w, o: V[0].map((_, j) => V.reduce((a, v, i) => a + w[i] * v[j], 0))};
}
function sceneAttention() {
  const X = [[1, 0], [0, 1], [1, 1]], cols = [C_W1, '#15803d', C_W2], names = ['x₁', 'x₂', 'x₃'];
  const draw = (fig, v) => {
    const svg = sv('svg', {viewBox: '0 0 780 340', class: 'plot', role: 'img'});
    const ox = 70, oy = 290, sc = 150, P = (x, y) => [ox + x * sc, oy - y * sc];
    const arrow = (a, b, c, wdt = 3, op = 1, lab = '', link = '') => { const [x1, y1] = P(...a), [x2, y2] = P(...b); const g = sv('g', {'data-link': link});
      g.append(sv('line', {x1, y1, x2, y2, stroke: c, 'stroke-width': wdt, opacity: op, 'marker-end': 'url(#ar5)'})); if (lab) g.append(sv('text', {x: x2 + 6, y: y2 - 6, 'font-size': 13, fill: c, opacity: op}, lab)); svg.append(g); };
    const defs = sv('defs'), mk = sv('marker', {id: 'ar5', viewBox: '0 0 8 8', refX: 7, refY: 4, markerWidth: 6, markerHeight: 6, orient: 'auto-start-reverse'}); mk.append(sv('path', {d: 'M0,0L8,4L0,8z', fill: 'context-stroke'})); defs.append(mk); svg.append(defs);
    // axes
    svg.append(sv('line', {x1: ox - 20, y1: oy, x2: ox + 1.6 * sc, y2: oy, stroke: 'var(--line2)'}), sv('line', {x1: ox, y1: oy + 20, x2: ox, y2: oy - 1.6 * sc, stroke: 'var(--line2)'}));
    // swapped token order only affects the bar order (geometry is identical)
    const order = v.swap > .5 ? [1, 0, 2] : [0, 1, 2];
    const r = attnRow(X[2], X, X, true, v.c);
    X.forEach((x, j) => arrow([0, 0], x, cols[j], j === 2 ? 3.5 : 2.5, 1, `${names[j]} = (${x.join(', ')})`, 'k' + (j + 1)));
    // projections of q onto keys (dot products)
    if (v.proj > 0) X.forEach((k, j) => { if (j === 2) return; const t = (k[0] * X[2][0] + k[1] * X[2][1]) / (k[0] ** 2 + k[1] ** 2); const [px, py] = P(k[0] * t, k[1] * t), [qx, qy] = P(...X[2]);
      svg.append(sv('line', {x1: qx, y1: qy, x2: qx + (px - qx) * v.proj, y2: qy + (py - qy) * v.proj, stroke: cols[j], 'stroke-dasharray': '4 3', opacity: .8})); });
    // weighted sum tip-to-tail
    if (v.chain > 0) { let p = [0, 0]; X.forEach((x, j) => { const u = clamp01(v.chain * 3 - j); if (u <= 0) return; const q = [p[0] + r.w[j] * x[0] * u, p[1] + r.w[j] * x[1] * u]; arrow(p, q, cols[j], 4, .85); p = q; });
      if (v.chain >= 1) { arrow([0, 0], r.o, 'var(--accent2)', 3, 1, '', 'o'); const [lx, ly] = P(...r.o); svg.append(sv('text', {x: lx + 14, y: ly + 22, 'font-size': 13, 'font-weight': 600, fill: 'var(--accent2)'}, `o₃ = (${de(r.o[0])}; ${de(r.o[1])})`)); } }
    // right panel: energies and softmax bars
    const bx = 430, bw = 300;
    svg.append(sv('text', {x: bx, y: 30, 'font-size': 13, 'font-weight': 600, fill: 'var(--ink)'}, `Anfrage q = x₃ · Skalierung c = ${de(v.c, 3)}`));
    order.forEach((j, row) => { const y = 60 + row * 80;
      svg.append(sv('text', {x: bx, y: y + 14, 'font-size': 13, fill: cols[j]}, names[j]));
      if (v.proj > 0) svg.append(sv('text', {x: bx + 34, y: y + 14, 'font-size': 12, 'font-family': 'var(--mono)', fill: 'var(--mute)', opacity: v.proj}, `e = q·k·c = ${de(r.e[j])}`));
      if (v.soft > 0) { svg.append(sv('rect', {x: bx, y: y + 24, width: bw * r.w[j] * v.soft, height: 22, rx: 4, fill: cols[j], opacity: .85, 'data-link': 'a' + (j + 1)}));
        svg.append(sv('text', {x: bx + bw * r.w[j] * v.soft + 8, y: y + 40, 'font-size': 13, 'font-weight': 600, fill: cols[j]}, `α = ${de(r.w[j])}`)); } });
    if (v.swap > 0) svg.append(sv('text', {x: bx, y: 315, 'font-size': 12, fill: 'var(--accent2)'}, 'x₁ und x₂ vertauscht – o₃ unverändert'));
    svg.setAttribute('aria-label', `Skalierung ${de(v.c, 3)}; Gewichte ${r.w.map(x => de(x, 3)).join(', ')}`);
    fig.replaceChildren(svg);
  };
  const c0 = 1 / Math.sqrt(2), base = attnRow(X[2], X, X, true), sharp = attnRow(X[2], X, X, true, 4);
  const steps = [
    {key: true, v: {c: c0, proj: 0, soft: 0, chain: 0, swap: 0}, cap: 'Drei Token als Pfeile in der Ebene. Mit \\(W_Q=W_K=W_V=I\\) ist jeder Pfeil zugleich Schlüssel und Wert; \\(x_3=(1,1)\\) stellt die Anfrage.', eq: '\\(q=x_3,\\ k_j=v_j=x_j\\)'},
    {v: {c: c0, proj: 0, soft: 0, chain: 0, swap: 0}, cap: 'Ähnlichkeit ist das Skalarprodukt: wie weit \\(q\\) in Richtung \\(k_j\\) zeigt.', predict: {q: 'Welcher Schlüssel bekommt das größte Skalarprodukt mit \\(q=(1,1)\\)?', options: ['\\(x_3\\) selbst', '\\(x_1\\)', 'alle gleich'], correct: 0, explain: '\\(q\\cdot x_1=q\\cdot x_2=1\\), aber \\(q\\cdot x_3=2\\): Der Pfeil zeigt genau in die eigene Richtung und ist länger.'}},
    {key: true, dur: 1400, v: {c: c0, proj: 1, soft: 0, chain: 0, swap: 0}, cap: 'Die gestrichelten Lote zeigen die Projektionen. Skalarprodukt mal \\(c=1/\\sqrt{d_k}\\) ergibt die Energien.', eq: `\\(e_{3j}=q^\\top k_j/\\sqrt2=${base.e.map(x => dt(x)).join(';\\ ')}\\)`},
    {key: true, dur: 1400, v: {c: c0, proj: 1, soft: 1, chain: 0, swap: 0}, cap: 'Die Softmax macht aus Energien Gewichte, die sich zu 1 summieren. Die Reihenfolge bleibt erhalten, die Abstände werden exponentiell betont.', eq: `\\(\\alpha_{3j}=\\dfrac{e^{e_{3j}}}{\\sum_l e^{e_{3l}}}=${base.w.map(x => dt(x)).join(';\\ ')}\\)`},
    {key: true, dur: 2200, v: {c: c0, proj: 1, soft: 1, chain: 1, swap: 0}, cap: 'Die Ausgabe entsteht Pfeil an Pfeil: \\(\\alpha_{31}x_1\\), dann \\(\\alpha_{32}x_2\\), dann \\(\\alpha_{33}x_3\\). <span data-link="o">\\(o_3\\)</span> liegt innerhalb der konvexen Hülle der Werte – ein gewichteter Durchschnitt, kein Auswahlvorgang.', eq: `\\(o_3=\\sum_j\\alpha_{3j}v_j=(${dt(base.o[0])};\\ ${dt(base.o[1])})\\)`},
    {v: {c: c0, proj: 1, soft: 1, chain: 1, swap: 0}, cap: 'Was passiert, wenn die Skalarprodukte größer werden – etwa weil \\(d_k\\) wächst und nicht skaliert wird?', predict: {q: 'Wie verändern sich die Gewichte bei viermal größeren Energien?', options: ['Sie werden spitzer: fast alles Gewicht auf \\(x_3\\)', 'Sie bleiben gleich', 'Sie werden gleichmäßiger'], correct: 0, explain: 'Die Softmax vergrößert Unterschiede exponentiell: \\(e^{4\\Delta}\\) statt \\(e^{\\Delta}\\). Ohne Skalierung wächst \\(\\operatorname{Var}(q^\\top k)\\) mit \\(d_k\\) (Satz 3).'}},
    {key: true, dur: 2000, v: {c: 4, proj: 1, soft: 1, chain: 1, swap: 0}, cap: '<b>Gegenprobe ohne passende Skalierung.</b> Mit \\(c=4\\) liegt fast das ganze Gewicht auf \\(x_3\\); die Softmax nähert sich einem \\(\\arg\\max\\), und ihr Gradient nach den übrigen Energien wird klein. Genau das verhindert \\(1/\\sqrt{d_k}\\).', eq: `\\(\\alpha_{33}=${dt(sharp.w[2])}\\) statt \\(${dt(base.w[2])}\\)`},
    {dur: 1200, v: {c: c0, proj: 1, soft: 1, chain: 1, swap: 0}, cap: 'Zurück zu \\(c=1/\\sqrt2\\). Nun vertauschen wir die Reihenfolge von \\(x_1\\) und \\(x_2\\) im Satz.', predict: {q: 'Ändert sich \\(o_3\\)?', options: ['nein', 'ja'], correct: 0, explain: 'Die Gewichte hängen nur von den Vektoren ab, nicht von ihrer Position in der Folge.'}},
    {key: true, dur: 1500, v: {c: c0, proj: 1, soft: 1, chain: 1, swap: 1}, cap: '<b>Verifikation.</b> Die Balken tauschen die Plätze, der Pfeil \\(o_3\\) bleibt, wo er war. Self-Attention ohne Positionskodierung sieht keine Reihenfolge (Satz 4) – deshalb braucht man Abschnitt 7.', eq: '\\(\\operatorname{Att}(PX)=P\\operatorname{Att}(X)\\)'}
  ];
  return {id: 'attention', fig: 'Abb. 6.1', title: 'Self-Attention als Geometrie: Projektion, Softmax, gewichtete Summe', question: 'Wie entsteht aus drei Vektoren eine neue Darstellung von Token 3 – und warum braucht man \\(1/\\sqrt{d_k}\\) und Positionen?', steps, draw};
}

// ---- storyboard 3: CRF — Viterbi (max) vs forward (sum), score vs probability ----
function sceneViterbi() {
  const L = ['O', 'B-LOC', 'I-LOC'], W = ['in', 'New', 'York'], E = [[2, 0, 0.5], [0.3, 1.0, 1.2], [0, 0.2, 1.5]];
  const ok = (p, c) => !c.startsWith('I-') || (p !== null && p !== 'O' && p.slice(2) === c.slice(2));
  const dp = mode => { const T = [L.map((c, k) => ok(null, c) ? {v: mode === 'max' ? E[0][k] : Math.exp(E[0][k]), bp: null} : null)];
    for (let t = 1; t < 3; t++) T.push(L.map((c, k) => { const prev = T[t - 1].map((x, j) => x && ok(L[j], c) ? j : -1).filter(j => j >= 0); if (!prev.length) return null;
      if (mode === 'max') { const j = prev.reduce((a, b) => T[t - 1][b].v > T[t - 1][a].v ? b : a); return {v: T[t - 1][j].v + E[t][k], bp: j}; }
      return {v: prev.reduce((a, j) => a + T[t - 1][j].v, 0) * Math.exp(E[t][k]), bp: null}; })); return T; };
  const MX = dp('max'), SM = dp('sum'), Z = SM[2].reduce((a, x) => a + (x ? x.v : 0), 0);
  const best = [2]; for (let t = 2; t > 0; t--) best.unshift(MX[t][best[0]].bp);
  const paths = []; for (let a = 0; a < 3; a++) for (let b = 0; b < 3; b++) for (let c = 0; c < 3; c++) { const p = [a, b, c]; if (p.every((k, t) => ok(t ? L[p[t - 1]] : null, L[k]))) paths.push({p, s: p.reduce((s, k, t) => s + E[t][k], 0)}); }
  paths.forEach(x => x.prob = Math.exp(x.s) / Z); paths.sort((a, b) => b.s - a.s);
  const draw = (fig, v) => {
    const svg = sv('svg', {viewBox: '0 0 780 330', class: 'plot', role: 'img'});
    const X = t => 120 + t * 170, Y = k => 50 + k * 72, sumMode = v.mode > .5, T = sumMode ? SM : MX;
    L.forEach((l, k) => svg.append(sv('text', {x: 8, y: Y(k) + 5, 'font-size': 13, fill: 'var(--mute)', 'font-family': 'var(--mono)'}, l)));
    W.forEach((w, t) => svg.append(sv('text', {x: X(t), y: 272, 'text-anchor': 'middle', 'font-size': 15, fill: 'var(--ink)'}, w)));
    for (let t = 1; t < 3; t++) L.forEach((c, k) => L.forEach((p, j) => { const allowed = ok(p, c) && !!T[t - 1][j], shown = clamp01(v.col - t) > 0;
      const isBp = !sumMode && MX[t][k] && MX[t][k].bp === j, back = !sumMode && v.back > 0 && best[t] === k && best[t - 1] === j && v.back * 2 >= (3 - t);
      svg.append(sv('line', {x1: X(t - 1) + 30, y1: Y(j), x2: X(t) - 30, y2: Y(k), stroke: back ? 'var(--ok)' : !allowed ? 'var(--bad)' : (shown && (sumMode || isBp)) ? 'var(--accent)' : 'var(--line2)',
        'stroke-width': back ? 5 : (shown && isBp) ? 2.5 : 1, 'stroke-dasharray': allowed ? '' : '4 3', opacity: allowed ? (shown || back ? 1 : .5) : .7})); }));
    E.forEach((row, t) => row.forEach((e, k) => { const cell = T[t][k], done = clamp01(v.col - t);
      svg.append(sv('rect', {x: X(t) - 30, y: Y(k) - 24, width: 60, height: 48, rx: 8, fill: !cell ? 'var(--soft)' : 'var(--panel)', stroke: (v.back > 0 && best[t] === k && !sumMode) ? 'var(--ok)' : 'var(--line)', 'stroke-width': (v.back > 0 && best[t] === k && !sumMode) ? 2.5 : 1}));
      svg.append(sv('text', {x: X(t), y: Y(k) - 6, 'text-anchor': 'middle', 'font-size': 11, fill: 'var(--mute)', 'font-family': 'var(--mono)'}, `s=${de(e, 1)}`));
      svg.append(sv('text', {x: X(t), y: Y(k) + 13, 'text-anchor': 'middle', 'font-size': 13.5, 'font-weight': 600, 'font-family': 'var(--mono)', fill: sumMode ? 'var(--accent2)' : 'var(--accent)', opacity: done}, !cell ? '—' : sumMode ? `α=${de(cell.v * done, 2)}` : `δ=${de(cell.v * done, 1)}`)); }));
    // right: path probabilities
    const px = 610;
    svg.append(sv('text', {x: px - 40, y: 24, 'font-size': 12.5, 'font-weight': 600, fill: 'var(--ink)'}, v.probs > 0 ? 'p(y | x) aller 13 gültigen Pfade' : (sumMode ? `Z = Σ α₃ = ${de(Z * clamp01(v.col - 2), 2)}` : 'δ: bester Score bis hier')));
    if (v.probs > 0) paths.forEach((x, n) => { const y = 38 + n * 18, isB = x.p.join() === best.join();
      svg.append(sv('rect', {x: px - 40, y, width: 150 * x.prob / paths[0].prob * v.probs * .9, height: 13, rx: 2, fill: isB ? 'var(--ok)' : 'var(--line2)'}));
      svg.append(sv('text', {x: px + 100, y: y + 11, 'font-size': 10.5, 'font-family': 'var(--mono)', fill: 'var(--mute)', opacity: v.probs}, `${x.p.map(k => L[k][0]).join('')} ${de(x.prob, 3)}`)); });
    svg.setAttribute('aria-label', sumMode ? `Forward-Algorithmus, Z ${de(Z, 2)}` : `Viterbi, bester Score ${de(MX[2][2].v, 1)}`);
    fig.replaceChildren(svg);
  };
  const steps = [
    {key: true, v: {col: 0, mode: 0, back: 0, probs: 0}, cap: 'Emissionswerte \\(s_t(\\ell)\\) eines BiRNN für „in New York“. Rot gestrichelt: verbotene Übergänge (I-LOC ohne vorheriges B-/I-LOC). Erlaubte Übergänge haben hier den Wert 0.', eq: '\\(S(x,y)=\\sum_{t}\\big(s_t(y_t)+A_{y_{t-1},y_t}\\big),\\quad A_{\\text{verboten}}=-\\infty\\)'},
    {v: {col: 0, mode: 0, back: 0, probs: 0}, cap: 'Gierig je Wort das Maximum: O, I-LOC, I-LOC – ungültig.', predict: {q: 'Welcher gültige Pfad hat den größten Score?', options: ['O B-LOC I-LOC', 'O B-LOC B-LOC', 'O O O'], correct: 0, explain: 'Scores 4,5 gegen 3,2 und 2,3. Viterbi findet das, ohne alle 27 Pfade aufzuzählen.'}},
    {key: true, dur: 2600, v: {col: 3, mode: 0, back: 0, probs: 0}, cap: '<b>Viterbi, Spalte für Spalte.</b> \\(\\delta_t(\\ell)\\) ist der beste Score eines gültigen Präfixes, das bei Label \\(\\ell\\) endet. Blau: der jeweils beste Vorgänger (Rückzeiger).', eq: '\\(\\delta_t(\\ell)=s_t(\\ell)+\\max_{\\ell\\prime}\\big(\\delta_{t-1}(\\ell\\prime)+A_{\\ell\\prime,\\ell}\\big)\\)'},
    {key: true, dur: 1800, v: {col: 3, mode: 0, back: 1, probs: 0}, cap: `Rückverfolgung ab dem besten Endwert \\(\\delta_3(\\text{I-LOC})=${dt(MX[2][2].v, 1)}\\): O → B-LOC → I-LOC. Der Algorithmus kostet \\(O(T|\\mathcal L|^2)\\) statt \\(|\\mathcal L|^T\\).`, eq: ''},
    {v: {col: 3, mode: 0, back: 1, probs: 0}, cap: 'Score 4,5 ist eine unnormierte Zahl. Wie sicher ist das Modell?', predict: {q: 'Welche Wahrscheinlichkeit \\(p(y^\\ast\\mid x)\\) hat der beste Pfad?', options: ['etwa 0,45', 'fast 1', 'etwa 0,1'], correct: 0, explain: 'Die Wahrscheinlichkeit normiert über <em>alle</em> gültigen Pfade. Mehrere Konkurrenten liegen nur 1,3 bis 2 Score-Punkte dahinter.'}},
    {key: true, dur: 2600, v: {col: 3, mode: 1, back: 0, probs: 0}, cap: `<b>Forward-Algorithmus:</b> dieselbe Rekursion, nur mit Summe statt Maximum und mit \\(e^{\\text{Score}}\\) statt Score. \\(\\alpha_t(\\ell)\\) summiert über alle gültigen Präfixe. Ergebnis: \\(Z=${dt(Z, 2)}\\) – ohne 13 Pfade einzeln aufzuzählen.`, eq: '\\(\\alpha_t(\\ell)=e^{s_t(\\ell)}\\sum_{\\ell\\prime}\\alpha_{t-1}(\\ell\\prime)\\,e^{A_{\\ell\\prime,\\ell}},\\qquad Z(x)=\\sum_{\\ell}\\alpha_T(\\ell)\\)'},
    {key: true, dur: 1600, v: {col: 3, mode: 1, back: 0, probs: 1}, cap: `<b>Score gegen Wahrscheinlichkeit.</b> Der beste Pfad hat \\(S=4{,}5\\), aber nur \\(p=e^{4{,}5}/Z=${dt(paths[0].prob, 4)}\\). Normiert wird die Wahrscheinlichkeit, nie der Score.`, eq: '\\(p(y\\mid x)=\\dfrac{\\exp S(x,y)}{Z(x)},\\qquad Z(x)=\\sum_{y\\prime\\text{ gültig}}\\exp S(x,y\\prime)\\)'},
    {key: true, v: {col: 3, mode: 1, back: 0, probs: 1}, cap: '<b>Gültig ist nicht richtig.</b> Die Regeln schließen nur ungültige Folgen aus. Lägen die Emissionen von „York“ höher bei O, gewänne O B-LOC O – gültig, aber falsch abgegrenzt. Die Fallstudie (Abschnitt 13) zeigt genau solche Fehler.', eq: ''}
  ];
  return {id: 'viterbi', fig: 'Abb. 9.1', title: 'Linear-chain-CRF: bester Pfad (Viterbi) und Wahrscheinlichkeit (Forward)', question: 'Wie findet man die beste gültige Labelfolge – und wie sicher ist sie?', steps, draw};
}

// ---- storyboard 4: span encodings (IO, BIO, BILOU) ----
function sceneSpans() {
  const tok = ['Flüge', 'am', 'Montag', 'Dienstag', 'und', 'Freitag'], gold = [[2, 3], [3, 4], [5, 6]];
  const enc = {IO: ['O', 'O', 'DAY', 'DAY', 'O', 'DAY'], BIO: ['O', 'O', 'B-DAY', 'B-DAY', 'O', 'B-DAY'], BILOU: ['O', 'O', 'U-DAY', 'U-DAY', 'O', 'U-DAY']};
  const decodeIO = [[2, 4], [5, 6]];
  const draw = (fig, v, s) => {
    const svg = sv('svg', {viewBox: '0 0 780 260', class: 'plot', role: 'img'});
    const X = i => 70 + i * 120, scheme = s.scheme || 'IO';
    tok.forEach((w, i) => { svg.append(sv('rect', {x: X(i) - 54, y: 150, width: 108, height: 36, rx: 7, fill: 'var(--panel)', stroke: 'var(--line)'}), sv('text', {x: X(i), y: 173, 'text-anchor': 'middle', 'font-size': 14, fill: 'var(--ink)'}, w)); });
    // gold spans as brackets (top)
    const bracket = (a, b, y, c, op, lab) => { const x1 = X(a) - 50, x2 = X(b - 1) + 50; svg.append(sv('path', {d: `M${x1},${y + 10} L${x1},${y} L${x2},${y} L${x2},${y + 10}`, fill: 'none', stroke: c, 'stroke-width': 3, opacity: op})); if (lab) svg.append(sv('text', {x: (x1 + x2) / 2, y: y - 6, 'text-anchor': 'middle', 'font-size': 12, fill: c, opacity: op}, lab)); };
    gold.forEach(([a, b]) => bracket(a, b, 120, 'var(--ok)', 1, 'DAY'));
    // labels drop in
    tok.forEach((_, i) => { const y = 200 + (1 - v.lab) * 30; svg.append(sv('text', {x: X(i), y: y + 18, 'text-anchor': 'middle', 'font-size': 14, 'font-family': 'var(--sans)', 'font-weight': 600, fill: enc[scheme][i] === 'O' ? 'var(--mute)' : 'var(--accent)', opacity: v.lab}, enc[scheme][i])); });
    // decoded spans (bottom, morphing)
    if (v.dec > 0) { const dec = scheme === 'IO' ? decodeIO : gold; dec.forEach(([a, b]) => { const x1 = X(a) - 50, x2 = X(b - 1) + 50, y = 236;
      svg.append(sv('path', {d: `M${x1},${y - 8} L${x1},${y} L${x2},${y} L${x2},${y - 8}`, fill: 'none', stroke: scheme === 'IO' ? 'var(--bad)' : 'var(--ok)', 'stroke-width': 3, opacity: v.dec})); }); }
    svg.append(sv('text', {x: 16, y: 30, 'font-size': 13, 'font-weight': 600, fill: 'var(--ink)'}, `Kodierung: ${scheme} · Labels für K Typen: ${scheme === 'IO' ? 'K+1' : scheme === 'BIO' ? '2K+1' : '4K+1'}`));
    svg.append(sv('text', {x: 16, y: 52, 'font-size': 12, fill: 'var(--mute)'}, 'oben: Gold-Spannen · Mitte: Wörter · unten: Labels und die daraus zurückgelesenen Spannen'));
    svg.setAttribute('aria-label', `${scheme}: ${enc[scheme].join(' ')}`); fig.replaceChildren(svg);
  };
  const steps = [
    {key: true, scheme: 'IO', v: {lab: 0, dec: 0}, cap: 'Drei Gold-Spannen vom Typ DAY. „Montag“ und „Dienstag“ sind zwei <em>benachbarte</em> Spannen gleichen Typs.', eq: ''},
    {key: true, scheme: 'IO', dur: 1000, v: {lab: 1, dec: 0}, cap: 'IO-Kodierung: jedes Wort einer Spanne bekommt das Typlabel.', eq: '\\(|\\mathcal L|=K+1\\)'},
    {scheme: 'IO', v: {lab: 1, dec: 0}, cap: 'Jetzt lesen wir die Spannen aus den Labels zurück.', predict: {q: 'Erhält man wieder drei Spannen?', options: ['nein – Montag und Dienstag verschmelzen', 'ja'], correct: 0, explain: 'DAY DAY sieht genauso aus wie eine einzige zweiwortige Spanne. Die Grenze ist verloren.'}},
    {key: true, scheme: 'IO', dur: 1200, v: {lab: 1, dec: 1}, cap: '<b>Gegenbeispiel:</b> Rückgelesen entsteht [Montag Dienstag] (rot) – IO ist nicht umkehrbar (Satz A).', eq: ''},
    {key: true, scheme: 'BIO', dur: 1000, v: {lab: 1, dec: 0}, cap: 'BIO markiert jeden Spannenanfang mit B-.', eq: '\\(|\\mathcal L|=2K+1\\)'},
    {key: true, scheme: 'BIO', dur: 1200, v: {lab: 1, dec: 1}, cap: '<b>Verifikation:</b> Jedes B- eröffnet eine neue Spanne; die drei Gold-Spannen kommen exakt zurück.', eq: ''},
    {key: true, scheme: 'BILOU', dur: 1000, v: {lab: 1, dec: 1}, cap: 'BILOU markiert zusätzlich Ende (L-) und Einwortspannen (U-): \\(4K+1\\) Labels. Mehr Grenzinformation, weniger Beispiele je Label – Ratinov &amp; Roth (2009) fanden BILOU in ihrem System besser.', eq: '\\(|\\mathcal L|=4K+1\\)'}
  ];
  return {id: 'spans', fig: 'Abb. 2.1', title: 'Spannen als Labels: was IO verliert und BIO bewahrt', question: 'Kann man aus einem Label pro Wort die Spannen eindeutig zurückgewinnen?', steps, draw};
}

// ---- scene 2: F1 from counts, with every boundary case ----
function sceneF1() {
  let c = {tp: 6, fp: 2, fn: 4}, free = false;
  const draw = (fig, s, extra) => {
    if (s.c) c = {...s.c}; free = !!s.free;
    const m = prf(c), cs = caseOf(c);
    const svg = sv('svg', {viewBox: '0 0 760 300', class: 'plot', role: 'img'});
    // Venn-like boxes made of unit squares
    const col = (n, x0, y0, color, link) => { const big = n <= 24, sq = big ? 18 : 9, gap = big ? 4 : 3, per = big ? 4 : 9; const g = sv('g', {'data-link': link}); for (let k = 0; k < n; k++) g.append(sv('rect', {x: x0 + (k % per) * (sq + gap), y: y0 + Math.floor(k / per) * (sq + gap), width: sq, height: sq, rx: 2, fill: color})); return g; };
    svg.append(sv('rect', {x: 20, y: 30, width: 270, height: 240, rx: 12, fill: 'none', stroke: 'var(--accent)', 'stroke-width': 2, 'data-link': 'S'}));
    svg.append(sv('rect', {x: 160, y: 50, width: 270, height: 240, rx: 12, fill: 'none', stroke: 'var(--ok)', 'stroke-width': 2, 'stroke-dasharray': '6 4', 'data-link': 'G'}));
    svg.append(sv('text', {x: 28, y: 22, 'font-size': 13, fill: 'var(--accent)', 'font-weight': 600}, 'System-Ausgaben S'));
    svg.append(sv('text', {x: 300, y: 44, 'font-size': 13, fill: 'var(--ok)', 'font-weight': 600}, 'Gold G'));
    svg.append(col(c.fp, 34, 70, 'var(--bad)', 'FP'), col(c.tp, 175, 80, 'var(--accent)', 'TP'), col(c.fn, 330, 80, 'var(--mute)', 'FN'));
    svg.append(sv('text', {x: 34, y: 262, 'font-size': 13, fill: 'var(--bad)', 'data-link': 'FP'}, `FP = ${c.fp}`), sv('text', {x: 175, y: 262, 'font-size': 13, fill: 'var(--accent)', 'data-link': 'TP'}, `TP = ${c.tp}`), sv('text', {x: 330, y: 282, 'font-size': 13, fill: 'var(--mute)', 'data-link': 'FN'}, `FN = ${c.fn}`));
    // P-R square with exact boundary handling
    const X = p => 500 + p * 220, Y = r => 270 - r * 220;
    svg.append(sv('rect', {x: 500, y: 50, width: 220, height: 220, fill: 'none', stroke: 'var(--line)'}));
    for (const F of [.2, .4, .6, .8]) { let d = ''; for (let k = 0; k <= 120; k++) { const p = F / 2 + (1 - F / 2) * k / 120 + 1e-6, r = F * p / (2 * p - F); if (r <= 1.0001) d += (d ? 'L' : 'M') + X(p).toFixed(1) + ',' + Y(r).toFixed(1); } svg.append(sv('path', {d, fill: 'none', stroke: 'var(--line2)', 'stroke-width': 1.2})); }
    svg.append(sv('text', {x: 610, y: 292, 'text-anchor': 'middle', 'font-size': 12, fill: 'var(--mute)'}, 'P'), sv('text', {x: 488, y: 160, 'font-size': 12, fill: 'var(--mute)'}, 'R'));
    svg.append(sv('text', {x: 500, y: 40, 'font-size': 12, fill: 'var(--mute)'}, 'Linien gleichen F1 (0,2 … 0,8)'));
    if (m.P != null && m.R != null) svg.append(sv('circle', {cx: X(m.P), cy: Y(m.R), r: 8, fill: 'var(--accent2)', 'data-link': 'pt'}));
    else svg.append(sv('text', {x: 610, y: 165, 'text-anchor': 'middle', 'font-size': 13, fill: 'var(--bad)'}, m.P == null && m.R == null ? 'P und R nicht definiert' : (m.P == null ? 'P nicht definiert' : 'R nicht definiert') + ' – kein Punkt'));
    svg.setAttribute('aria-label', `TP ${c.tp}, FP ${c.fp}, FN ${c.fn}; Fall ${cs}`);
    fig.replaceChildren(svg);
    const frac = (a, b) => b === 0 ? `\\tfrac{${a}}{0}\\ (\\text{nicht definiert})` : `\\tfrac{${a}}{${b}}=${dt(a / b, 3)}`;
    const table = el('div', {class: 'scene-eq', html: `\\[\\begin{aligned}
P&=\\tfrac{\\mathrm{TP}}{\\mathrm{TP}+\\mathrm{FP}}=${frac(c.tp, c.tp + c.fp)}\\\\
R&=\\tfrac{\\mathrm{TP}}{\\mathrm{TP}+\\mathrm{FN}}=${frac(c.tp, c.tp + c.fn)}\\\\
F_1&=\\tfrac{2\\mathrm{TP}}{2\\mathrm{TP}+\\mathrm{FP}+\\mathrm{FN}}=${frac(2 * c.tp, 2 * c.tp + c.fp + c.fn)}\\\\
\\tfrac{2PR}{P+R}&=${m.H == null ? (cs === 'ii' ? '\\tfrac{0}{0}\\ (\\text{nicht definiert})' : '\\text{nicht anwendbar}') : dt(m.H, 3)}
\\end{aligned}\\]<p class="mute">Fall (${cs}) der Tabelle in Abschnitt 8.</p>`});
    const ctl = el('div', {class: 'ctl'}, ...['tp', 'fp', 'fn'].map(k => el('span', {class: 'stepper'}, k.toUpperCase() + ':',
      el('button', {'aria-label': k + ' minus', disabled: !free, onclick: () => { c[k] = Math.max(0, c[k] - 1); draw(fig, {free: true}, extra); }}, '−'),
      el('b', {}, String(c[k])),
      el('button', {'aria-label': k + ' plus', disabled: !free, onclick: () => { c[k] = Math.min(12, c[k] + 1); draw(fig, {free: true}, extra); }}, '+'))));
    extra.replaceChildren(table, ctl);
    tex(extra).then(() => linkify(fig.parentNode));
  };
  const steps = [
    {key: true, c: {tp: 6, fp: 2, fn: 4}, cap: 'Ein Beispiel. Links die 8 Ausgaben des Systems (blauer Rahmen), rechts die 10 Gold-Entitäten (grün gestrichelt). Die Überlappung sind die <span data-link="TP">6 Treffer</span>; <span data-link="FP">2 falsche Alarme</span>, <span data-link="FN">4 verpasste</span>.', eq: ''},
    {c: {tp: 6, fp: 2, fn: 4}, cap: 'Aufwand pro Treffer, zweimal gemessen: Pro Treffer gab das System \\(8/6\\) Ausgaben ab, und pro Treffer gab es \\(10/6\\) Gold-Entitäten.', eq: '\\(\\tfrac1P=\\tfrac{\\mathrm{TP}+\\mathrm{FP}}{\\mathrm{TP}}=\\tfrac86,\\qquad \\tfrac1R=\\tfrac{\\mathrm{TP}+\\mathrm{FN}}{\\mathrm{TP}}=\\tfrac{10}{6}\\)'},
    {key: true, c: {tp: 6, fp: 2, fn: 4}, cap: 'Mitteln, dann umdrehen: Treffer pro durchschnittlichem Aufwand. Das ist \\(F_1\\) – und die Zählform steht direkt da: doppelte Treffer durch doppelte Treffer plus alle Fehler.', eq: '\\(\\tfrac12\\big(\\tfrac86+\\tfrac{10}6\\big)=\\tfrac{20}{12}\\ \\Rightarrow\\ F_1=\\tfrac{12}{20}=\\tfrac{2\\cdot6}{2\\cdot6+2+4}=0{,}6\\)'},
    {c: {tp: 10, fp: 40, fn: 0}, cap: 'Ein System markiert fast alles: 10 Treffer, 40 falsche Alarme, nichts verpasst.', eq: '',
      predict: {q: 'Welches \\(F_1\\)?', options: ['etwa 0,6 – Mittel aus \\(P=0{,}2\\) und \\(R=1\\)', '\\(1/3\\)', '\\(0{,}2\\)'], correct: 1, explain: '\\(F_1=\\tfrac{20}{20+40+0}=\\tfrac13\\). Das gewöhnliche Mittel (0,6) überschätzt; \\(F_1\\le2P=0{,}4\\).'}},
    {key: true, c: {tp: 10, fp: 40, fn: 0}, cap: 'Der Punkt liegt bei \\(R=1\\) am oberen Rand, aber weit links: Die Linien gleichen \\(F_1\\) biegen sich zu den Achsen, ein Ausreißer in \\(P\\) lässt sich durch \\(R\\) nicht ausgleichen.', eq: ''},
    {key: true, c: {tp: 0, fp: 0, fn: 3}, cap: '<b>Grenzfall (iii):</b> Das System gibt nichts aus. Es gibt keine Ausgabe, über die man einen Anteil bilden könnte – \\(P\\) ist nicht definiert, also gibt es keinen Punkt im Quadrat. \\(F_1\\) über die Zählform ist trotzdem eindeutig 0.', eq: ''},
    {c: {tp: 0, fp: 2, fn: 5}, cap: 'Grenzfall (ii): Keine Treffer, aber Ausgaben und Gold-Entitäten.', eq: '',
      predict: {q: 'Was liefert \\(2PR/(P+R)\\)?', options: ['0', '\\(0/0\\) – keinen Wert', '\\(2/7\\)'], correct: 1, explain: 'Hier ist \\(P=R=0\\), also \\(\\tfrac{2\\cdot0\\cdot0}{0+0}=\\tfrac00\\). Die Zählform liefert \\(\\tfrac0{7}=0\\). Deshalb rechnet man mit der Zählform.'}},
    {key: true, c: {tp: 0, fp: 2, fn: 5}, cap: 'Der Punkt sitzt in der Ecke \\((0,0)\\) – dort ist das harmonische Mittel als Formel nicht definiert, die Zählform schon.', eq: ''},
    {key: true, c: {tp: 0, fp: 0, fn: 0}, cap: '<b>Grenzfall (v):</b> Weder Gold noch Ausgaben. Auch die Zählform ist \\(0/0\\). Jede Zahl wäre eine Konvention (scikit-learn: <code>zero_division</code> = 0, 1 oder NaN) und muss genannt werden.', eq: ''},
    {c: {tp: 3, fp: 1, fn: 2}, free: true, cap: '<b>Jetzt Sie.</b> Verändern Sie TP, FP, FN mit den Tasten (auch auf 0) und beobachten Sie, wann welche Größe undefiniert wird.', eq: ''}
  ];
  return {legacy: true, id: 'f1', title: 'F1 aus Zählungen – inklusive aller Fälle mit Nenner 0', steps, draw};
}

// ---- scene 3: phrase vs token counting ----
function sceneCounter() {
  const tok = ['First', 'Bank', 'of', 'Chicago', 'announced', 'earnings', 'of', '$200,000,000'];
  const gold = ['B-ORG', 'I-ORG', 'I-ORG', 'I-ORG', 'O', 'O', 'O', 'B-MON'];
  const presets = {s1: ['O', 'O', 'O', 'O', 'O', 'O', 'O', 'B-MON'], s2: ['O', 'B-ORG', 'I-ORG', 'I-ORG', 'O', 'O', 'O', 'B-MON'], gold: [...gold], none: Array(8).fill('O')};
  const cycle = ['O', 'B-ORG', 'I-ORG', 'B-MON', 'I-MON'];
  let pred = [...presets.s2], free = false;
  const draw = (fig, s, extra) => {
    if (s.preset) pred = [...presets[s.preset]]; free = !!s.free;
    const row = el('div', {class: 'tokrow', role: 'group', 'aria-label': 'Wörter mit Gold- und System-Label'}, tok.map((w, i) => {
      const typ = x => x === 'O' ? 'O' : x.slice(2), ok = typ(gold[i]) === typ(pred[i]);
      return el(free ? 'button' : 'div', {class: 'tok ' + (pred[i] === 'O' && gold[i] === 'O' ? '' : ok ? 'tp' : 'err'), 'aria-label': `${w}: Gold ${gold[i]}, System ${pred[i]}`,
        onclick: free ? () => { pred[i] = cycle[(cycle.indexOf(pred[i]) + 1) % cycle.length]; draw(fig, {free: true}, extra); } : null},
        el('small', {class: 'g'}, 'Gold ' + gold[i]), w, el('small', {class: 'p'}, s.hide ? '' : 'Sys ' + pred[i]));
    }));
    const tbl = (name, c, show) => { const m = prf(c); return el('table', {}, el('tr', {}, el('th', {colspan: 2}, name)),
      el('tr', {}, el('td', {}, 'TP / FP / FN'), el('td', {}, show ? `${c.tp} / ${c.fp} / ${c.fn}` : '?')),
      el('tr', {}, el('td', {}, 'P'), el('td', {}, show ? de(m.P, 3) : '?')), el('tr', {}, el('td', {}, 'R'), el('td', {}, show ? de(m.R, 3) : '?')),
      el('tr', {}, el('td', {}, 'F1'), el('td', {}, show ? de(m.F, 3) : '?'))); };
    fig.replaceChildren(row, el('div', {class: 'grid2'}, tbl('Phrasen-Ebene (exakte Spannen)', spanCounts(gold, pred), !s.hide), tbl('Token-Ebene (Typ je Wort)', tokenCounts(gold, pred), !s.hide)));
    extra.replaceChildren(free ? el('p', {class: 'mute'}, 'Klicken Sie ein Wort an, um sein System-Label zu wechseln: O → B-ORG → I-ORG → B-MON → I-MON.') : '');
  };
  const steps = [
    {key: true, preset: 'gold', hide: true, cap: 'Folienbeispiel (Vorlesung PDF-S. 21–22). Gold: <code>[First Bank of Chicago]ORG</code> und <code>[$200,000,000]MONEY</code> – zwei Spannen, fünf Entitätswörter.', eq: ''},
    {preset: 's2', hide: true, cap: 'System 2 findet <code>[Bank of Chicago]</code> statt <code>[First Bank of Chicago]</code> und den Geldbetrag.', eq: '',
      predict: {q: 'Welche Zählung bewertet System 2 besser?', options: ['Phrasen-Ebene', 'Token-Ebene', 'beide gleich'], correct: 1, explain: 'Auf Token-Ebene ist nur „First“ verpasst (1 FN). Auf Phrasen-Ebene ist die Bank-Spanne ein FP <em>und</em> die Gold-Spanne ein FN.'}},
    {key: true, preset: 's2', cap: 'System 2: Phrasen \\(F_1=\\tfrac12\\), Token \\(F_1=\\tfrac89\\). Ein falsch gesetzter Spannenanfang kostet auf Phrasen-Ebene zwei Fehler.', eq: '\\(\\text{Phrasen: }\\tfrac{2\\cdot1}{2+1+1}=\\tfrac12,\\qquad \\text{Token: }\\tfrac{2\\cdot4}{8+0+1}=\\tfrac89\\)'},
    {key: true, preset: 's1', cap: 'System 1 findet nur den Geldbetrag. Phrasen \\(F_1=\\tfrac23\\) – <em>besser</em> als System 2 –, Token \\(F_1=\\tfrac13\\). Die Rangfolge der Systeme dreht sich mit der Zähleinheit um.', eq: '\\(\\text{Phrasen: }\\tfrac{2}{2+0+1}=\\tfrac23,\\qquad \\text{Token: }\\tfrac{2}{2+0+4}=\\tfrac13\\)'},
    {preset: 's2', free: true, cap: '<b>Jetzt Sie.</b> Bauen Sie ein System, das auf Phrasen-Ebene \\(F_1=0\\), auf Token-Ebene aber über 0,5 erreicht.', eq: ''}
  ];
  return {legacy: true, id: 'counter', title: 'Dieselbe Vorhersage, zwei Urteile', steps, draw};
}

// ---- scene 4: micro vs macro ----
function sceneMicroMacro() {
  let misc = 1, free = false;
  const base = {PER: [45, 5, 5], LOC: [30, 10, 10], ORG: [20, 15, 15]};
  const draw = (fig, s, extra) => {
    if (s.misc !== undefined) misc = s.misc; free = !!s.free;
    const cls = {...base, MISC: [misc, 4, 10 - misc]};
    const f = Object.fromEntries(Object.entries(cls).map(([k, [tp, fp, fn]]) => [k, prf({tp, fp, fn}).F]));
    const tot = Object.values(cls).reduce((a, c) => a.map((x, i) => x + c[i]), [0, 0, 0]);
    const micro = prf({tp: tot[0], fp: tot[1], fn: tot[2]}).F, macro = Object.values(f).reduce((a, b) => a + b, 0) / 4;
    const svg = sv('svg', {viewBox: '0 0 620 220', class: 'plot', role: 'img', 'aria-label': `MISC erkannt ${misc}: Micro ${de(micro, 3)}, Macro ${de(macro, 3)}`});
    const W = 420, x0 = 70, yb = k => 18 + k * 36;
    Object.entries(f).forEach(([k, v], i) => { const n = cls[k][0] + cls[k][2];
      svg.append(sv('text', {x: 4, y: yb(i) + 15, 'font-size': 13, fill: 'var(--ink)'}, k), sv('rect', {x: x0, y: yb(i), width: W * v, height: 22, fill: k === 'MISC' ? 'var(--accent2)' : 'var(--accent)', rx: 3}),
        sv('text', {x: x0 + W + 8, y: yb(i) + 15, 'font-size': 12, fill: 'var(--mute)'}, `F1 ${de(v, 3)} · ${n} Gold`)); });
    for (const [name, v, c, y] of [['Micro', micro, 'var(--ok)', 182], ['Macro', macro, 'var(--bad)', 204]]) {
      svg.append(sv('line', {x1: x0 + W * v, y1: 8, x2: x0 + W * v, y2: 160, stroke: c, 'stroke-width': 3}), sv('text', {x: x0 + W * v, y, 'text-anchor': 'middle', 'font-size': 13, fill: c, 'font-weight': 600}, `${name}-F1 ${de(v, 3)}`));
    }
    fig.replaceChildren(svg);
    extra.replaceChildren(free ? el('div', {class: 'ctl'}, 'MISC erkannt:', el('input', {type: 'range', min: 0, max: 10, value: misc, 'aria-label': 'erkannte MISC-Entitäten', oninput: e => { misc = +e.target.value; draw(fig, {free: true}, extra); }}), ` ${misc} von 10`) : '');
  };
  const at = k => { const cls = {...base, MISC: [k, 4, 10 - k]}; const fs = Object.values(cls).map(([tp, fp, fn]) => prf({tp, fp, fn}).F);
    const tot = Object.values(cls).reduce((a, c) => a.map((x, i) => x + c[i]), [0, 0, 0]); return {micro: prf({tp: tot[0], fp: tot[1], fn: tot[2]}).F, macro: fs.reduce((a, b) => a + b, 0) / 4}; };
  const lo = at(1), hi = at(10);
  const steps = [
    {key: true, misc: 1, cap: `Das Beispiel aus Abschnitt 10: MISC hat nur 10 von 135 Gold-Entitäten und wird schlecht erkannt. Micro (grün) und Macro (rot) liegen ${de(lo.micro - lo.macro, 3)} auseinander.`, eq: ''},
    {misc: 1, cap: 'Angenommen, das System erkennt alle 10 MISC-Entitäten (bei weiterhin 4 Fehlalarmen).', eq: '',
      predict: {q: 'Welche Kennzahl steigt stärker?', options: ['Micro-F1', 'Macro-F1', 'beide gleich stark'], correct: 1, explain: 'MISC hat bei Macro ein Viertel des Gewichts, bei Micro nur den Anteil seiner Entitäten (10 von 135).'}},
    {key: true, misc: 10, cap: `MISC vollständig erkannt: Macro steigt um ${de(hi.macro - lo.macro, 3)}, Micro nur um ${de(hi.micro - lo.micro, 3)}.`, eq: ''},
    {misc: 1, free: true, cap: '<b>Jetzt Sie.</b> Verschieben Sie den Regler und beobachten Sie die beiden Linien.', eq: ''}
  ];
  return {legacy: true, id: 'micromacro', title: 'Was eine seltene Klasse mit Micro und Macro macht', steps, draw};
}
// ---- case study panel ----
function caseStudy(root) {
  const C = U.case, Lb = C.labels;
  const allowed = (p, c) => !c.startsWith('I-') || (p !== null && p !== 'O' && p.slice(2) === c.slice(2));
  const emis = snt => snt.emissions.map(row => Lb.map(l => +(row[l] || 0)));
  const greedy = E => E.map(r => Lb[r.indexOf(Math.max(...r))]);
  const viterbi = E => { let best = Lb.map((c, k) => allowed(null, c) ? {s: E[0][k], p: [c]} : null);
    for (let t = 1; t < E.length; t++) best = Lb.map((c, k) => { let b = null; best.forEach((x, j) => { if (x && allowed(Lb[j], c)) { const v = x.s + E[t][k]; if (!b || v > b.s) b = {s: v, p: [...x.p, c]}; } }); return b; });
    return best.filter(Boolean).reduce((a, b) => b.s > a.s ? b : a).p; };
  let mode = 'greedy';
  const body = el('div', {});
  const tabs = el('div', {class: 'ctl', role: 'tablist'}, ['greedy', 'viterbi'].map(m => el('button', {role: 'tab', 'aria-selected': m === mode ? 'true' : 'false', onclick: () => { mode = m; draw(); }}, m === 'greedy' ? 'Gierige Dekodierung' : 'Viterbi mit BIO-Regeln')));
  root.append(el('h4', {}, 'Fallstudie: drei Sätze, zwei Dekodierungen'), tabs, body);
  function draw() {
    tabs.querySelectorAll('button').forEach(b => b.setAttribute('aria-selected', b.textContent.startsWith(mode === 'greedy' ? 'Gierig' : 'Viterbi') ? 'true' : 'false'));
    let G = [], P = [];
    const rows = C.sentences.map(snt => { const p = mode === 'greedy' ? greedy(emis(snt)) : viterbi(emis(snt)); G = G.concat(snt.gold, ['O']); P = P.concat(p, ['O']);
      return el('div', {class: 'tokrow'}, snt.tokens.map((w, i) => { const ty = x => x === 'O' ? 'O' : x.slice(2), ok = snt.gold[i] === p[i];
        return el('div', {class: 'tok ' + (snt.gold[i] === 'O' && p[i] === 'O' ? '' : ok ? 'tp' : 'err')}, el('small', {class: 'g'}, 'Gold ' + snt.gold[i]), w, el('small', {class: 'p'}, 'Sys ' + p[i])); })); });
    const sc = spanCounts(G, P), tc = tokenCounts(G, P), a = prf(sc), b = prf(tc);
    body.replaceChildren(...rows, el('table', {}, el('tr', {}, el('th', {}, ''), el('th', {}, 'TP / FP / FN'), el('th', {}, 'P'), el('th', {}, 'R'), el('th', {}, 'F1')),
      el('tr', {}, el('td', {}, 'Phrasen'), el('td', {}, `${sc.tp} / ${sc.fp} / ${sc.fn}`), el('td', {}, de(a.P, 4)), el('td', {}, de(a.R, 4)), el('td', {}, de(a.F, 4))),
      el('tr', {}, el('td', {}, 'Token'), el('td', {}, `${tc.tp} / ${tc.fp} / ${tc.fn}`), el('td', {}, de(b.P, 4)), el('td', {}, de(b.R, 4)), el('td', {}, de(b.F, 4)))),
      el('p', {class: 'mute small'}, 'Grün umrandet: Label stimmt; rot: Label weicht vom Gold ab. Spannen werden nach der conlleval-Konvention gelesen.'));
    body.dataset.mode = mode; body.dataset.spanF1 = a.F;
  }
  draw();
}
const SCENES = {birnn: sceneBirnn, f1: sceneF1, counter: sceneCounter, micromacro: sceneMicroMacro, attention: sceneAttention, viterbi: sceneViterbi, spans: sceneSpans};
function mountScenes(scope, print) { scope.querySelectorAll('.scene[data-scene]').forEach(n => Scene(n, SCENES[n.dataset.scene](), print)); scope.querySelectorAll('.casestudy').forEach(n => { n.replaceChildren(); caseStudy(n); }); }

// ---------- tasks ----------
function renderTask(task, ctx = {}) {
  const box = el('div', {class: 'task', id: 'task-' + task.id});
  let hintsShown = 0, revealed = false;
  const tries = () => st.attempts.filter(a => a.task === task.id);
  box.append(el('header', {}, el('span', {class: 'stage'}, STAGE[task.stage] || ''), el('b', {}, `${task.id} · ${task.title}`)), el('div', {html: task.prompt}));
  const expert = task.stage === 'worked' && st.attempts.some(a => a.kc === task.kc && a.first && a.correct && !supported(a));
  if (task.steps) {
    const ol = el('ol', {class: 'steps'}, task.steps.map(s => el('li', {class: s.blank ? 'blank' : ''}, el('span', {html: s.s}), el('span', {class: 'why', html: s.why}))));
    if (expert && !ctx.print) box.append(el('details', {}, el('summary', {}, 'Ausgearbeitete Schritte (eingeklappt: Sie haben diese Kompetenz schon ohne Hilfe gelöst)'), ol)); else box.append(ol);
  }
  if (ctx.print) return box;
  const inputs = task.answers.map((a, i) => {
    const wrap = el('div', {class: 'ans'}), id = `${task.id}-a${i}`;
    wrap.append(el('label', {for: id, html: a.label + ':'}));
    if (a.type === 'seq') wrap.append(el('input', {type: 'text', id, class: 'wide', placeholder: 'Labels mit Leerzeichen, z. B. O B-CITY I-CITY', autocomplete: 'off', spellcheck: 'false'}));
    else if (a.type === 'num' || a.type === 'set') wrap.append(el('input', {type: 'text', id, inputmode: a.type === 'set' ? 'text' : 'decimal', placeholder: a.type === 'set' ? 'z. B. 1, 2, 3' : 'Bruch (2/7) oder Dezimalzahl', autocomplete: 'off', enterkeyhint: 'done'}));
    else if (a.type === 'choice') wrap.append(el('div', {role: 'radiogroup', id, 'aria-label': a.label}, a.options.map((o, k) => el('label', {class: 'radio'}, el('input', {type: 'radio', name: id, value: k}), ' ', el('span', {html: o})))));
    else wrap.append(el('textarea', {id, rows: 5, placeholder: 'Ihr Beweis bzw. Ihre Begründung'}));
    return wrap;
  });
  box.append(...inputs);
  if (ctx.exam) return box;
  const fb = el('div', {}), hintBox = el('div', {}), sol = el('div', {class: 'sol', hidden: true}, ...solutionBlocks(task));
  const hasHints = (task.hints || []).length > 0;
  const bHint = el('button', {disabled: true, onclick: () => { if (hintsShown < task.hints.length) { hintBox.append(el('p', {class: 'fb hint', html: 'Hinweis: ' + task.hints[hintsShown++]})); tex(hintBox); } bHint.disabled = hintsShown >= task.hints.length; }}, 'Hinweis');
  const bSol = el('button', {onclick: () => { if (!tries().length && !confirm('Lösung ansehen, ohne es versucht zu haben? Die Aufgabe zählt dann als unterstützt.')) return; revealed = true; sol.hidden = false; tex(sol); if (!tries().length) record(task, false, {revealed: true, hints: hintsShown}); }}, 'Lösung anzeigen');
  const bCheck = el('button', {class: 'primary', onclick: check}, task.answers[0].type === 'self' ? 'Abgeben' : 'Prüfen');
  box.append(el('div', {class: 'ctl'}, bCheck, hasHints ? bHint : null, bSol), fb, hintBox, sol, labLink(task));
  if (hasHints) box.append(el('p', {class: 'mute small'}, 'Hinweise werden nach Ihrem ersten eigenen Versuch freigeschaltet.'));
  box.addEventListener('keydown', e => { if (e.key === 'Enter' && e.target.tagName === 'INPUT' && e.target.type === 'text') check(); });
  function check() {
    const msgs = []; let all = true;
    task.answers.forEach((a, i) => {
      const id = `${task.id}-a${i}`;
      if (a.type === 'num') { const v = $(`#${id}`, box).value, ok = numOk(v, a); if (ok === null) { all = false; msgs.push(['bad', `${a.label}: bitte eine Zahl oder einen Bruch eingeben.`]); return; } all &&= ok; msgs.push(ok ? ['ok', `${a.label}: richtig.`] : ['bad', `${a.label}: noch nicht. ` + (diagnose(v, a) || 'Schreiben Sie die Zwischenwerte einzeln auf und vergleichen Sie mit der Definition.')]); }
      else if (a.type === 'seq') { const got = seqOf($(`#${id}`, box).value), want = a.value; const ok = JSON.stringify(got) === JSON.stringify(want); all &&= ok;
        const pos = want.findIndex((w, k) => got[k] !== w);
        msgs.push(ok ? ['ok', 'richtig.'] : ['bad', got.length !== want.length ? `noch nicht: Sie haben ${got.length} Labels für ${want.length} Wörter angegeben.` : `noch nicht: erste Abweichung bei Wort ${pos + 1} (${got[pos]}). Prüfen Sie dort Spannenanfang und Typ.`]); }
      else if (a.type === 'set') { const ok = JSON.stringify(parseSet($(`#${id}`, box).value)) === JSON.stringify(a.value); all &&= ok; msgs.push(ok ? ['ok', 'richtig.'] : ['bad', 'noch nicht – welche Eingaben erreichen den Zustand über die Rekursion?']); }
      else if (a.type === 'choice') { const c = box.querySelector(`input[name="${id}"]:checked`); if (!c) { all = false; msgs.push(['bad', 'bitte eine Option wählen.']); return; } const k = +c.value, ok = k === a.correct; all &&= ok; msgs.push(ok ? ['ok', 'richtig.'] : ['bad', 'noch nicht. ' + (((a.diagnoses || []).find(d => +d.value === k) || {}).msg || '')]); }
      else all = null;
    });
    if (all === null) { sol.hidden = false; tex(sol); fb.replaceChildren(el('p', {class: 'fb'}, 'Vergleichen Sie mit der Musterlösung und bewerten Sie sich selbst:'), el('div', {class: 'ctl'}, ...[['vollständig', true], ['teilweise', false], ['nicht gelöst', false]].map(([l, ok]) => el('button', {onclick: () => { record(task, ok, {hints: hintsShown, revealed: true, self: l}); fb.append(el('p', {class: 'mute'}, 'Gespeichert als unterstützte Übung (Selbstbewertung).')); }}, l)))); return; }
    record(task, all, {hints: hintsShown, revealed});
    fb.replaceChildren(...msgs.map(([c, m]) => el('p', {class: 'fb ' + c, html: m})));
    if (hasHints && hintsShown < task.hints.length) bHint.disabled = false;
    if (all) { sol.hidden = false; introduceCards(task.kc); }
    tex(box);
  }
  return box;
}


// ---------- v5: Kurzschlüssel vs. ausführliche Lösung; Verknüpfung ins Labor ----------
function labHref(lab, item) { return `labor.html#lab=${lab}` + (item ? `&ziel=${item}` : ''); }
function labLink(t) { return t.lab ? el('p', {class: 'lab-link'}, el('a', {href: labHref(t.lab.lab, t.lab.item)}, '⚗ Im Labor ausprobieren: ' + t.lab.label)) : null; }
function solutionBlocks(t) {
  const out = [el('div', {class: 'sol key', html: `<b>${t.worked ? 'Bewertungsschlüssel (kurz).' : 'Lösung.'}</b> ${t.solution}`})];
  if (t.worked) out.push(el('div', {class: 'sol worked', html: '<b>Ausführliche Lösung.</b> ' + t.worked}));
  if (t.rubric) out.push(el('p', {class: 'mute', html: '<b>Bewertung.</b> ' + t.rubric.join(' · ')}));
  return out;
}
function labRefs(scope, print) {
  scope.querySelectorAll('.lab-ref').forEach(n => { const m = (U.lab || {})[n.dataset.kc]; if (!m) return n.remove();
    n.replaceChildren(el('div', {class: 'lab-card'}, el('b', {}, print ? 'Im Interaktiven Labor (labor.html) – ' + ({attention: 'Self-Attention', crf: 'CRF & Viterbi', birnn: 'BiRNN', spans: 'Spannen & F1'}[m.lab]) : '⚗ Selbst erforschen im Interaktiven Labor'),
      el('ul', {}, m.items.map(([id, label]) => el('li', {}, print ? label : el('a', {href: labHref(m.lab, id)}, label)))),
      el('p', {class: 'mute small'}, 'Erst vorhersagen, dann verändern, dann die Begründung lesen. Jede Station ist mit einem Satz dieses Abschnitts verknüpft.'))); });
}

// ---------- citations: every provenance marker links into the bibliography ----------
const SOURCE_MATCH = [['SLP3', 'slp3'], ['Ratinov', 'ratinov'], ['Lample', 'lample'], ['Vaswani', 'vaswani'], ['Andor', 'andor'], ['Lafferty', 'lafferty'], ['Huang', 'huang'],
  ['Opitz', 'opitz'], ['Manning', 'manning'], ['scikit', 'sklearn'], ['Tjong', 'conll'], ['CoNLL', 'conll'], ['Su et al', 'su'], ['Schuster', 'schuster'], ['Folie', 'kurs'], ['PDF-S', 'kurs'], ['Vorlesung', 'kurs']];
function linkCitations(scope) {
  scope.querySelectorAll('.prov').forEach(n => { if (n.querySelector('a')) return; const m = SOURCE_MATCH.find(([k]) => n.textContent.includes(k)); if (!m) return;
    const a = el('a', {href: '#ref-' + m[1], class: 'cite'}); while (n.firstChild) a.append(n.firstChild); n.append(a); });
  scope.querySelectorAll('a.cite').forEach(a => a.addEventListener('click', e => { const t = document.getElementById(a.getAttribute('href').slice(1)); if (t) { e.preventDefault(); t.scrollIntoView({block: 'center'}); t.classList.add('flash-ref'); setTimeout(() => t.classList.remove('flash-ref'), 1600); } }));
}
function bibliography() {
  return el('ol', {class: 'refs'}, U.sources.map(s => el('li', {id: 'ref-' + s.id}, el('span', {class: 'prov', 'data-kind': s.kind}), ' ', s.ref, ' ',
    s.doi ? el('a', {href: 'https://doi.org/' + s.doi, target: '_blank', rel: 'noopener'}, 'doi:' + s.doi) : s.url ? el('a', {href: s.url, target: '_blank', rel: 'noopener'}, s.url) : null)));
}
// ---------- views ----------
const app = document.getElementById('app');
function topbar(cur) {
  const nav = [['home', 'Heute'], ['learn', 'Lernen'], ['review', `Wiederholen (${dueCards().length})`], ['exam', 'Prüfung'], ['progress', 'Fortschritt'], ['sources', 'Quellen']];
  return el('header', {class: 'top'}, el('span', {class: 'brand'}, 'Exam Mastery'), el('span', {class: 'mute'}, U.course),
    el('nav', {'aria-label': 'Hauptnavigation'}, nav.map(([k, l]) => el('button', {'aria-current': k === cur ? 'page' : false, onclick: () => go(k)}, l))));
}
const noticeBar = () => notices.length ? el('div', {class: 'notice', role: 'alert'}, notices.map(n => el('p', {}, n))) : null;
function go(v, arg) { location.hash = v + (arg ? '/' + arg : ''); }
window.addEventListener('hashchange', render);
const sections = () => [...el('div', {html: U.text_html}).querySelectorAll('section')];

function nextStep() {
  const due = dueCards().length;
  if (due) return {t: `${due} Karte${due > 1 ? 'n' : ''} wiederholen`, d: 'Zuerst kurz abrufen – aktives Erinnern stärkt das Behalten mehr als erneutes Lesen.', a: () => go('review')};
  const unread = sections().find(s => !st.visited[s.dataset.id]);
  if (unread) return {t: `Weiter: ${unread.dataset.title}`, d: 'Text, Experiment und Aufgaben stehen zusammen.', a: () => go('learn', unread.dataset.id)};
  const open = U.tasks.find(t => !st.attempts.some(a => a.task === t.id && a.correct));
  if (open) return {t: `Aufgabe ${open.id}: ${open.title}`, d: STAGE[open.stage], a: () => go('learn', 'task-' + open.id)};
  return {t: `Prüfung ohne Hilfe (Form ${nextForm()})`, d: 'Neue Aufgaben ohne Hinweise. Für „wahrscheinlich sicher“ zählt nur eine Prüfung mindestens 24 h nach dem letzten Üben.', a: () => go('exam')};
}

function home() {
  const n = nextStep(), weak = Object.keys(KCS).filter(k => kcLevel(k) === 'LUECKE');
  return [topbar('home'), el('main', {}, noticeBar(), el('h1', {}, U.title), el('p', {class: 'lead mute'}, U.subtitle),
    el('div', {class: 'cards'},
      el('div', {class: 'card hero'}, el('h3', {}, 'Heute lernen'), el('p', {}, n.d), el('button', {class: 'primary', onclick: n.a}, n.t)),
      el('div', {class: 'card'}, el('h3', {}, 'Interaktives Labor'), el('p', {}, 'Self-Attention, CRF/Viterbi, BiRNN, Spannen & F1: frei experimentieren, Hypothesen prüfen, Challenges lösen.'), el('a', {class: 'btn', href: 'labor.html'}, 'Labor öffnen')),
      el('div', {class: 'card'}, el('h3', {}, 'Fortsetzen'), el('p', {}, st.last ? 'Zurück zur letzten Stelle.' : 'Mit dem Washington-Experiment beginnen.'), el('button', {onclick: () => go('learn', st.last || 'orientierung')}, 'Öffnen')),
      el('div', {class: 'card'}, el('h3', {}, 'Wiederholen'), el('p', {}, `${dueCards().length} fällig · ${Object.keys(st.cards).length} von ${U.cards.length} Karten aktiv`), el('button', {onclick: () => go('review')}, 'Öffnen')),
      el('div', {class: 'card'}, el('h3', {}, 'Schwächen'), el('p', {}, weak.length ? weak.map(k => KCS[k]).join(' · ') : 'Keine aus Prüfungen bekannt.'), weak.length ? el('button', {onclick: () => go('learn', Object.keys(SECTION_KC).find(s => SECTION_KC[s] === weak[0]))}, 'Gezielt üben') : null),
      el('div', {class: 'card'}, el('h3', {}, 'Prüfung'), el('p', {}, `Form ${nextForm()} · 10 neue Aufgaben, 2 je Kompetenz, ohne Hilfe.`), el('button', {onclick: () => go('exam')}, 'Starten')),
      el('div', {class: 'card'}, el('h3', {}, 'Kompetenzstand'), el('p', {}, Object.keys(KCS).map(k => `${KCS[k]}: ${LEVELS[kcLevel(k)][0]}`).join(' · ')), el('button', {onclick: () => go('progress')}, 'Details'))),
    el('p', {class: 'mute small'}, `Status: ${U.status} Fortschritt liegt nur in diesem Browser${storageOK ? '' : ' – Speichern ist derzeit nicht möglich'}.`))];
}

function learn(anchor) {
  const toc = el('aside', {class: 'toc', 'aria-label': 'Inhalt'}), main = el('main', {}), secs = sections();
  for (const s of secs) {
    const kc = SECTION_KC[s.dataset.id], lv = kc ? kcLevel(kc) : null;
    toc.append(el('a', {href: '#learn/' + s.dataset.id, 'data-id': s.dataset.id}, el('span', {class: 'kc lv-' + (lv || 'none'), title: lv ? LEVELS[lv][0] : ''}), s.dataset.title));
    main.append(el('h2', {id: s.dataset.id}, s.dataset.title));
    s.querySelectorAll('.task-ref').forEach(r => r.replaceWith(renderTask(U.tasks.find(x => x.id === r.dataset.task))));
    main.append(...s.childNodes);
    const more = U.tasks.filter(t => KC_SECTION[t.kc] === s.dataset.id && !U.text_html.includes(`data-task="${t.id}"`));
    if (more.length) main.append(el('h3', {class: 'more-tasks'}, `Weitere Übungen zu ${KCS[more[0].kc]}`), ...more.map(t => renderTask(t)));
  }
  const rest = U.tasks.filter(t => !U.text_html.includes(`data-task="${t.id}"`) && !KC_SECTION[t.kc]);
  if (rest.length) { toc.append(el('a', {href: '#learn/weitere'}, 'Weitere Aufgaben')); main.append(el('h2', {id: 'weitere'}, 'Weitere Aufgaben'), ...rest.map(t => renderTask(t))); }
  toc.append(el('a', {href: '#learn/literatur'}, 'Literatur')); main.append(el('h2', {id: 'literatur'}, 'Literatur'), bibliography());
  main.append(el('div', {class: 'card hero', style: 'margin-top:30px'}, el('h3', {}, 'Abschluss'), el('p', {}, `Prüfung ohne Hilfe, Form ${nextForm()}. Nach mindestens 24 h ohne Üben folgt die andere Form – erst sie zählt für „wahrscheinlich sicher“.`), el('button', {class: 'primary', onclick: () => go('exam')}, 'Zur Prüfung')));
  mountScenes(main, false); labRefs(main, false); linkCitations(main);
  setTimeout(() => {
    const target = anchor && document.getElementById(anchor); if (target) target.scrollIntoView();
    const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { const id = e.target.id; st.visited[id] = 1; st.last = id; if (SECTION_KC[id]) introduceCards(SECTION_KC[id]); save(); toc.querySelectorAll('a').forEach(a => a.classList.toggle('cur', a.dataset.id === id)); } }), {rootMargin: '0px 0px -70% 0px'});
    main.querySelectorAll('h2[id]').forEach(h => io.observe(h));
  });
  tex(main);
  return [topbar('learn'), noticeBar(), el('div', {class: 'layout'}, toc, main)];
}

function review() {
  const q = dueCards(), m = el('main', {}, el('h1', {}, 'Wiederholen'));
  if (!q.length) m.append(el('p', {}, Object.keys(st.cards).length ? 'Nichts fällig. Nächste Karte: ' + new Date(Math.min(...Object.values(st.cards).map(c => c.due))).toLocaleString('de-DE') : 'Karten werden aktiv, sobald Sie den zugehörigen Abschnitt lesen oder eine Aufgabe lösen.'));
  else {
    const c = q[0], isCloze = c.type === 'cloze';
    const front = isCloze ? c.cloze.replace(/\{\{c\d::(.*?)\}\}/g, '<span class="cloze">[…]</span>') : c.prompt;
    const ans = isCloze ? c.cloze.replace(/\{\{c\d::(.*?)\}\}/g, '<span class="cloze-a">$1</span>') : c.answer;
    const back = el('div', {hidden: true}, el('hr'), el('p', {class: 'canon', html: ans}), el('p', {html: '<b>Warum:</b> ' + c.why}),
      c.example ? el('p', {html: '<b>Beispiel:</b> ' + c.example}) : null, c.mistake ? el('p', {html: '<b>Häufiger Fehler:</b> ' + c.mistake}) : null,
      c.diagram ? el('img', {src: 'media/' + c.diagram, alt: 'Diagramm zur Karte', class: 'carddiag'}) : null, el('p', {class: 'mute small', html: 'Quelle: ' + c.source}), el('div', {class: 'ctl'},
      el('button', {onclick: () => grade(false)}, 'Nicht gewusst'), el('button', {class: 'primary', onclick: () => grade(true)}, 'Gewusst')));
    m.append(el('p', {class: 'mute'}, `${q.length} fällig. Erst selbst antworten, dann aufdecken.`), el('div', {class: 'flash'}, el('p', {class: 'pill'}, KCS[c.kc] || c.kc), el('p', {html: front}),
      el('button', {onclick: e => { back.hidden = false; e.target.remove(); tex(back); }}, 'Antwort zeigen'), back));
    function grade(ok) { const s = st.cards[c.key]; s.box = ok ? Math.min(BOX.length - 1, s.box + 1) : 0; s.due = now() + BOX[s.box] * DAY + (ok ? 0 : 10 * 60e3); save(); render(); }
  }
  m.append(el('p', {class: 'mute small'}, `Abstände ${BOX.join(' / ')} Tage (Leitner-Kästen). Das ist eine einfache, offene Regel – kein nachgewiesen optimaler Plan. Für Anki: anki_import.txt mit stabilen GUIDs.`));
  tex(m); return [topbar('review'), noticeBar(), m];
}

function exam() {
  const form = nextForm(), items = FORMS[form];
  const m = el('main', {}, el('h1', {}, `Prüfung ohne Hilfe – Form ${form}`));
  const delayed = kc => { const t = lastActivity(kc, now()); return t != null && now() - t >= DAY; };
  m.append(el('p', {}, 'Keine Hinweise, keine Lösungen bis zur Abgabe. Zwei Aufgaben je Kompetenz; eine davon ist bei drei Kompetenzen eine Transferaufgabe. Geben Sie zu jeder Antwort an, wie sicher Sie sind.'),
    el('table', {}, el('tr', {}, el('th', {}, 'Kompetenz'), el('th', {}, 'zählt als verzögert?')), Object.keys(KCS).map(k => el('tr', {}, el('td', {}, KCS[k]), el('td', {}, delayed(k) ? 'ja (≥ 24 h seit letzter Aktivität)' : 'nein')))));
  const boxes = items.map(x => {
    const t = renderTask({...x, stage: '', hints: [], title: KCS[x.kc] + (x.transfer ? ' · Transfer' : '')}, {exam: true});
    const conf = el('select', {'aria-label': 'Sicherheit'}, ['50', '70', '90', '100'].map(v => el('option', {value: v}, v + ' %')));
    t.append(el('div', {class: 'ans'}, el('label', {}, 'Sicherheit:'), conf)); t._conf = conf; return t;
  });
  m.append(...boxes, el('button', {class: 'primary', onclick: submit}, 'Abgeben'));
  function submit() {
    const res = items.map((x, i) => {
      const box = boxes[i]; let ok = true;
      x.answers.forEach((a, k) => { const id = `${x.id}-a${k}`;
        if (a.type === 'num') ok &&= !!numOk($(`#${id}`, box).value, a);
        else if (a.type === 'set') ok &&= JSON.stringify(parseSet($(`#${id}`, box).value)) === JSON.stringify(a.value);
        else if (a.type === 'seq') ok &&= JSON.stringify(seqOf($(`#${id}`, box).value)) === JSON.stringify(a.value);
        else if (a.type === 'choice') { const c = box.querySelector(`input[name="${id}"]:checked`); ok &&= !!c && +c.value === a.correct; } });
      return {id: x.id, kc: x.kc, correct: ok, conf: +box._conf.value, transfer: !!x.transfer};
    });
    const del = Object.fromEntries(Object.keys(KCS).map(k => [k, delayed(k)]));
    st.exams.push({ts: now(), form, delayed: del, items: res});
    for (const r of res) if (!r.correct) for (const c of U.cards) if (c.kc === r.kc) st.cards[c.key] = {box: 0, due: now()};
    save();
    const acc = res.filter(r => r.correct).length / res.length, conf = res.reduce((a, r) => a + r.conf, 0) / res.length / 100;
    m.replaceChildren(el('h1', {}, 'Auswertung'), el('p', {class: 'lead'}, `${res.filter(r => r.correct).length} von ${res.length} richtig (Form ${form}).`),
      el('p', {}, `Kalibrierung: mittlere Sicherheit ${Math.round(conf * 100)} %, richtig ${Math.round(acc * 100)} %` + (conf - acc > .15 ? ' – Sie überschätzen sich.' : acc - conf > .15 ? ' – Sie unterschätzen sich.' : ' – stimmig.')),
      el('table', {}, el('tr', {}, el('th', {}, 'Kompetenz'), el('th', {}, 'Ergebnis'), el('th', {}, 'Stand')), Object.keys(KCS).map(k => { const r = res.filter(x => x.kc === k); return el('tr', {}, el('td', {}, KCS[k]), el('td', {}, `${r.filter(x => x.correct).length}/${r.length}`), el('td', {}, LEVELS[kcLevel(k)][0])); })),
      ...items.map((x, i) => el('div', {class: 'task'}, el('header', {}, el('b', {}, `${x.id} ${res[i].correct ? '✓' : '✗'}`), el('span', {class: 'mute'}, `${KCS[x.kc]} · Sicherheit ${res[i].conf} %`)), el('div', {html: x.prompt}), el('div', {class: 'sol', html: '<b>Lösung.</b> ' + x.solution}))),
      el('p', {}, res.some(r => !r.correct) ? 'Die Karten der Kompetenzen mit Fehlern sind jetzt fällig.' : `Alle richtig. Machen Sie Form ${nextForm()} frühestens in 24 h, ohne vorher zu üben.`),
      el('button', {class: 'primary', onclick: () => go('home')}, 'Zur Tagesansicht'));
    tex(m); scrollTo(0, 0);
  }
  tex(m); return [topbar('exam'), noticeBar(), m];
}

function progress() {
  const s = series(), m = el('main', {}, el('h1', {}, 'Fortschritt'));
  const rate = arr => arr.length ? `${arr.filter(a => a.correct).length}/${arr.length} richtig` : 'keine Daten';
  m.append(el('div', {class: 'meter'}, el('span', {}, 'Übung mit Unterstützung: ' + rate(s.assisted)), el('span', {}, 'Erster Versuch ohne Hilfe: ' + rate(s.unsupported)),
      el('span', {}, 'Prüfung sofort: ' + rate(s.immediate)), el('span', {}, 'Prüfung verzögert: ' + rate(s.delayed)), el('span', {}, 'Transferaufgaben in Prüfungen: ' + rate(s.transfer))),
    el('p', {class: 'mute'}, 'Die Reihen werden getrennt geführt. Kompetenzstufen entstehen nur aus Prüfungen ohne Hilfe; eine Stufe beruht auf zwei Aufgaben je Prüfung und ist ein Beleg, keine Garantie.'),
    el('table', {}, el('tr', {}, el('th', {}, 'Kompetenz'), el('th', {}, 'Stufe'), el('th', {}, 'Bedeutung')), Object.entries(KCS).map(([k, l]) => { const lv = kcLevel(k); return el('tr', {'data-kc': k}, el('td', {}, l), el('td', {class: 'lv'}, LEVELS[lv][0]), el('td', {}, LEVELS[lv][1])); })),
    el('div', {class: 'ctl'}, el('button', {onclick: () => { const b = new Blob([JSON.stringify(st, null, 1)], {type: 'application/json'}); el('a', {href: URL.createObjectURL(b), download: `lernstand-${U.id}.json`}).click(); }}, 'Lernstand exportieren'),
      el('label', {class: 'btn'}, 'Importieren', el('input', {type: 'file', accept: 'application/json', class: 'sr', onchange: async e => { const msg = $('#import-msg'); try { const s = migrate(JSON.parse(await e.target.files[0].text())); if (!valid(s)) throw new Error('schema'); st = Object.assign(blank(), s); save(); render(); } catch (err) { msg.textContent = 'Import abgelehnt: Die Datei ist kein gültiger Lernstand. Ihr bisheriger Stand ist unverändert.'; } }})), el('span', {id: 'import-msg', role: 'status'})));
  return [topbar('progress'), noticeBar(), m];
}

function sources() {
  const m = el('main', {}, el('h1', {}, 'Quellen und Vertiefung'), el('p', {}, 'Kursunterlagen bestimmen Umfang und Prüfungsbezug, das Lehrbuch Definitionen und Herleitungen, Forschungsarbeiten die Vertiefung. Preprints und Blogbeiträge sind gekennzeichnet.'));
  m.append(el('ol', {}, U.sources.map(s => el('li', {}, el('span', {class: 'prov', 'data-kind': s.kind}), ' ', s.ref, ' ', s.doi ? el('a', {href: 'https://doi.org/' + s.doi}, 'doi:' + s.doi) : s.url ? el('a', {href: s.url}, s.url) : null))));
  return [topbar('sources'), noticeBar(), m];
}

function render() {
  const [v, arg] = (location.hash.slice(1) || 'home').split('/');
  const view = {home, learn, review, exam, progress, sources}[v] || home;
  app.replaceChildren(...view(arg).filter(Boolean)); tex(app).then(() => linkify(app));
}

// ---------- print products: one model, five purpose-built documents ----------
const PART = document.body.dataset.part || 'lehrbuch';
const PART_TITLE = {lehrbuch: 'Lehrbuch', arbeitsbuch: 'Arbeitsbuch', loesungen: 'Musterlösungen zum Arbeitsbuch', klausur: 'Probeklausur', klausur_loesungen: 'Probeklausur – Lösungen und Bewertung'};
const sectionOf = id => { const t = U.tasks.find(x => x.id === id); const secs = sections(); const sec = secs.find(x => x.innerHTML.includes(`data-task="${id}"`)) || secs.find(x => x.dataset.id === KC_SECTION[t.kc]); return sec ? sec.dataset.title : 'Weitere Aufgaben'; };
const sectionIndex = id => { const t = U.tasks.find(x => x.id === id); const secs = sections(); const i = secs.findIndex(x => x.innerHTML.includes(`data-task="${id}"`)); return i >= 0 ? i : secs.findIndex(x => x.dataset.id === KC_SECTION[t.kc]); };
function titlePage(m) {
  m.append(el('div', {class: 'titlepage'}, el('p', {class: 'kicker'}, `${U.course} · Kapitel ${U.chapter}`), el('h1', {}, U.title), el('p', {class: 'lead'}, PART_TITLE[PART]),
    el('p', {class: 'mute small'}, `Fassung ${U.version}. ${U.status}`)));
}
function bookLehrbuch(m) {
  for (const s of sections()) {
    m.append(el('h2', {}, s.dataset.title));
    s.querySelectorAll('.task-ref').forEach(r => { const t = U.tasks.find(x => x.id === r.dataset.task); r.replaceWith(el('p', {class: 'xref'}, `→ Arbeitsbuch, Aufgabe ${t.id}: ${t.title}`)); });
    m.append(...s.childNodes);
  }
  m.append(el('h2', {id: 'literatur'}, 'Literatur'), bibliography()); linkCitations(m);
}
function taskBlock(t, withSolution) {
  const b = el('div', {class: 'task'}, el('header', {}, el('span', {class: 'stage'}, STAGE[t.stage] || ''), el('b', {}, `${t.id} · ${t.title}`), el('span', {class: 'mute small'}, KCS[t.kc])), el('div', {html: t.prompt}));
  if (t.steps && (!withSolution || t.stage === 'worked')) b.append(el('ol', {class: 'steps'}, t.steps.map(x => el('li', {class: x.blank ? 'blank' : ''}, el('span', {html: x.s}), el('span', {class: 'why', html: x.why})))));
  if (!withSolution) {
    t.answers.filter(a => a.type === 'choice').forEach(a => b.append(el('p', {html: a.label + ':'}), el('ol', {type: 'a'}, a.options.map(o => el('li', {html: o})))));
    if (t.stage !== 'worked') b.append(el('div', {class: 'space', style: `height:${t.stage === 'transfer' ? 62 : 36}mm`}));
    if ((t.hints || []).length) b.append(el('details', {class: 'hints-inline', open: true}, el('summary', {}, 'Gestufte Hinweise – erst nach eigenem Versuch lesen'), el('ol', {}, t.hints.map(x => el('li', {html: x})))));
    if (t.lab) b.append(el('p', {class: 'mute small'}, '⚗ Experiment dazu: ' + t.lab.label));
    return b;
  }
  b.append(...solutionBlocks(t));
  const diags = t.answers.flatMap(a => (a.diagnoses || []).map(d => a.type === 'choice' ? `Option ${'abcdefg'[+d.value]}: ${d.msg}` : `Antwort ${d.value}: ${d.msg}`));
  if (diags.length) b.append(el('p', {class: 'mute', html: '<b>Typische Fehler.</b> ' + diags.join(' · ')}));
  return b;
}
function bookArbeitsbuch(m, sol) {
  m.append(el('p', {}, sol ? 'Zu jeder Aufgabe: Bewertungsschlüssel (kurz) bzw. vollständige Lösung, ausführliche Herleitung wo vorhanden, typische Fehler mit Diagnose und Bewertungsschema.' : 'Die Aufgaben sind nach Abschnitten des Lehrbuchs geordnet und gestuft: durchgerechnet → Lückenschritt → mit Hinweisen → selbstständig → Fehleranalyse → Transfer. Gestufte Hinweise stehen direkt unter jeder Aufgabe; lesen Sie sie erst nach einem eigenen Versuch. Zu vielen Aufgaben gibt es ein passendes Experiment im Interaktiven Labor.'));
  let cur = null;
  const ORDER = ['recall', 'worked', 'guided', 'faded', 'hint', 'independent', 'error', 'proof', 'transfer'];
  const tasks = [...U.tasks].sort((a, b) => (sectionIndex(a.id) - sectionIndex(b.id)) || (ORDER.indexOf(a.stage) - ORDER.indexOf(b.stage)));
  for (const t of tasks) { const sec = sectionOf(t.id); if (sec !== cur) { m.append(el('h2', {}, sec)); cur = sec; } m.append(taskBlock(t, sol)); }
}
function bookKlausur(m, sol) {
  const pts = x => x.answers.length * 2;
  m.append(el('h2', {}, 'Aufbau'), el('p', {}, 'Zwei gleichwertige, voneinander unabhängige Formen A und B mit neuen Daten (keine Aufgabe des Arbeitsbuchs wird wiederverwendet). Je Kompetenz zwei Aufgaben, davon eine Transferaufgabe bei sieben der neun Kompetenzen. Bewertung: 2 Punkte je Teilantwort. Offizielle Angaben zu Dauer und Hilfsmitteln der Klausur liegen nicht vor; die Form ist ohne Hilfsmittel gedacht.'),
    el('table', {}, el('tr', {}, el('th', {}, 'Kompetenz'), el('th', {}, 'Form A'), el('th', {}, 'Form B')), Object.entries(KCS).map(([k, l]) => el('tr', {}, el('td', {}, l), ...['A', 'B'].map(f => el('td', {}, FORMS[f].filter(x => x.kc === k).map(x => x.id + (x.transfer ? ' (T)' : '')).join(', ')))))));
  for (const [f, items] of Object.entries(FORMS)) {
    m.append(el('h2', {}, `Form ${f}` + (sol ? ' – Lösungen' : '')), el('p', {class: 'mute small'}, `Summe: ${items.reduce((a, x) => a + pts(x), 0)} Punkte.`));
    items.forEach(x => { const b = el('div', {class: 'task'}, el('header', {}, el('b', {}, `${x.id}`), el('span', {class: 'mute small'}, `${KCS[x.kc]}${x.transfer ? ' · Transfer' : ''} · ${pts(x)} P.`)), el('div', {html: x.prompt}));
      x.answers.filter(a => a.type === 'choice').forEach(a => b.append(el('ol', {type: 'a'}, a.options.map((o, k) => el('li', {html: o + (sol && k === a.correct ? ' <b>✓</b>' : '')})))));
      if (sol) b.append(...solutionBlocks(x)); else b.append(el('div', {class: 'space', style: 'height:28mm'}));
      m.append(b); });
  }
}
function book() {
  const m = el('main', {class: 'print-' + PART}); app.replaceChildren(m); titlePage(m);
  ({lehrbuch: () => bookLehrbuch(m), arbeitsbuch: () => bookArbeitsbuch(m, false), loesungen: () => bookArbeitsbuch(m, true), klausur: () => bookKlausur(m, false), klausur_loesungen: () => bookKlausur(m, true)})[PART]();
  mountScenes(m, true); labRefs(m, true);
  const done = () => { document.body.dataset.ready = '1'; };
  const wait = () => window.MathJax && MathJax.startup && MathJax.startup.promise ? MathJax.startup.promise.then(() => MathJax.typesetPromise([m])).then(done, done) : setTimeout(wait, 50);
  wait();
}

if (MODE === 'print') book();
else { render(); (function w() { if (window.MathJax && MathJax.startup && MathJax.startup.promise) MathJax.startup.promise.then(() => tex(app)).then(() => { document.body.dataset.ready = '1'; }); else setTimeout(w, 50); })(); }
})();
