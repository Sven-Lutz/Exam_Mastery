(() => {
'use strict';
const U = JSON.parse(document.getElementById('unit-data').textContent);
const MODE = document.body.dataset.mode;
const KEY = 'em-unit-' + U.id, DAY = 864e5, BOX = [0, 1, 3, 7, 16, 35];
const STAGE = {guided: 'Geführt', worked: 'Durchgerechnetes Beispiel', faded: 'Lückenschritt', hint: 'Mit Hinweisen', independent: 'Selbstständig', error: 'Fehleranalyse', transfer: 'Transfer'};
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
function Scene(root, spec, print) {
  let i = 0;
  const fig = el('div', {class: 'scene-fig'}), cap = el('div', {class: 'scene-cap', 'aria-live': 'polite'}), eq = el('div', {class: 'scene-eq'});
  const dots = el('div', {class: 'dots', 'aria-hidden': 'true'}), pred = el('div', {class: 'predict'}), extra = el('div', {});
  const back = el('button', {onclick: () => go(i - 1)}, '← Zurück'), fwd = el('button', {class: 'primary', onclick: () => go(i + 1)}, 'Weiter →');
  const restart = el('button', {onclick: () => go(0)}, 'Neu starten');
  root.replaceChildren(el('div', {class: 'scene-head'}, el('span', {class: 'stage'}, 'Erklärung in Schritten'), el('h4', {}, spec.title)),
    fig, el('div', {class: 'scene-text'}, cap, eq, pred), extra, el('div', {class: 'ctl'}, back, fwd, restart, dots));
  root.tabIndex = 0;
  root.addEventListener('keydown', e => { if (e.target !== root) return; if (e.key === 'ArrowRight' && !fwd.disabled) go(i + 1); if (e.key === 'ArrowLeft') go(i - 1); });
  const answered = {};
  function go(k) {
    i = Math.max(0, Math.min(spec.steps.length - 1, k));
    const s = spec.steps[i];
    spec.draw(fig, s, extra);
    cap.innerHTML = s.cap; eq.innerHTML = s.eq || '';
    dots.replaceChildren(...spec.steps.map((_, j) => el('span', {class: j === i ? 'on' : j < i ? 'done' : ''})));
    dots.setAttribute('aria-label', `Schritt ${i + 1} von ${spec.steps.length}`);
    back.disabled = i === 0; fwd.disabled = i === spec.steps.length - 1;
    pred.replaceChildren();
    if (s.predict) {
      const p = s.predict, res = el('div', {});
      fwd.disabled = !(i in answered);
      pred.append(el('p', {class: 'q', html: '<b>Ihre Vorhersage:</b> ' + p.q}),
        el('div', {class: 'opts'}, p.options.map((o, k) => el('button', {class: 'opt', html: o, onclick: () => {
          answered[i] = k; st.predictions.push({scene: spec.id, step: i, choice: k, correct: k === p.correct, ts: now()}); save();
          res.innerHTML = `<p class="fb ${k === p.correct ? 'ok' : 'bad'}">${k === p.correct ? 'Richtig.' : 'Nicht ganz.'} ${p.explain}</p>`;
          fwd.disabled = i === spec.steps.length - 1; tex(res);
        }}))), res);
      if (i in answered) res.innerHTML = `<p class="fb ${answered[i] === p.correct ? 'ok' : 'bad'}">${p.explain}</p>`;
    }
    tex(root).then(() => linkify(root));
  }
  if (print) {
    root.replaceChildren(el('h4', {}, spec.title));
    spec.steps.forEach((s, k) => {
      if (!s.key) return;
      const f = el('div', {class: 'scene-fig'}), x = el('div', {});
      spec.draw(f, s, x);
      root.append(el('div', {class: 'keyframe'}, el('div', {class: 'kf-n'}, `Bild ${k + 1}`), f, el('div', {class: 'scene-cap', html: s.cap}), el('div', {class: 'scene-eq', html: s.eq || ''}),
        s.predict ? el('p', {class: 'q', html: `<b>Vorhersage vor dem Weiterlesen:</b> ${s.predict.q} <i>(Auflösung: ${s.predict.options[s.predict.correct]})</i>`}) : null));
    });
    return;
  }
  go(0);
}

// ---- scene 1: the Washington experiment ----
function toyRun(sentence) {
  const E = U.toy.emb, xs = [E.Washington, E[sentence]];
  const step = (a, h, x) => [Math.tanh(a * h[0] + x[0]), Math.tanh(a * h[1] + x[1])];
  const f1 = step(U.toy.a_fw, [0, 0], xs[0]), f2 = step(U.toy.a_fw, f1, xs[1]);
  const b2 = step(U.toy.a_bw, [0, 0], xs[1]), b1 = step(U.toy.a_bw, b2, xs[0]);
  return {xs, f: [f1, f2], b: [b1, b2]};
}
const vec = v => `(${dt(v[0])};\\ ${dt(v[1])})`;
const vtxt = v => `(${de(v[0])}; ${de(v[1])})`;
function sceneBirnn() {
  const A = toyRun('signed'), B = toyRun('state');
  const draw = (fig, s) => {
    const svg = sv('svg', {viewBox: '0 0 760 330', class: 'plot', role: 'img', 'aria-label': s.alt || ''});
    [['signed', A, 20], ['state', B, 400]].forEach(([w, R, x0]) => {
      svg.append(sv('rect', {x: x0, y: 8, width: 340, height: 314, rx: 12, fill: 'var(--panel)', stroke: 'var(--line)'}));
      svg.append(sv('text', {x: x0 + 14, y: 30, 'font-size': 14, 'font-weight': 600, fill: 'var(--ink)'}, `Satz ${w === 'signed' ? 'A' : 'B'}: „Washington ${w}“`));
      const X = t => x0 + 90 + t * 170, yIn = 285, yF = 205, yB = 130, yL = 60;
      ['Washington', w].forEach((word, t) => {
        const diff = t === 1;
        svg.append(sv('rect', {x: X(t) - 62, y: yIn - 18, width: 124, height: 34, rx: 7, fill: diff ? 'var(--soft)' : 'transparent', stroke: diff ? 'var(--accent2)' : 'var(--line)', 'data-link': 'e' + (t + 1)}));
        svg.append(sv('text', {x: X(t), y: yIn - 1, 'text-anchor': 'middle', 'font-size': 14, fill: 'var(--ink)'}, word));
        svg.append(sv('text', {x: X(t), y: yIn + 13, 'text-anchor': 'middle', 'font-size': 11, fill: 'var(--mute)', 'font-family': 'var(--mono)'}, `e=(${R.xs[t].join(', ')})`));
        const showF = s.fw > t, showB = s.bw && s.bw > (1 - t);
        svg.append(sv('line', {x1: X(t) - 30, y1: yIn - 18, x2: X(t) - 30, y2: yF + 20, stroke: showF ? 'var(--fw)' : 'var(--line)', 'stroke-width': showF ? 2.5 : 1}));
        if (s.bw !== undefined) svg.append(sv('line', {x1: X(t) + 30, y1: yIn - 18, x2: X(t) + 30, y2: yB + 20, stroke: showB ? 'var(--bw)' : 'var(--line)', 'stroke-width': showB ? 2.5 : 1}));
        const nodeF = sv('g', {'data-link': `h${t + 1}f`});
        nodeF.append(sv('rect', {x: X(t) - 70, y: yF - 20, width: 140, height: 40, rx: 20, fill: showF ? 'var(--fw-bg)' : 'var(--panel)', stroke: 'var(--fw)', 'stroke-width': s.hl === `h${t + 1}f` ? 3.5 : 1.5}));
        nodeF.append(sv('text', {x: X(t), y: yF - 4, 'text-anchor': 'middle', 'font-size': 11, fill: 'var(--fw)'}, `h${t + 1}→`));
        nodeF.append(sv('text', {x: X(t), y: yF + 12, 'text-anchor': 'middle', 'font-size': 12, 'font-family': 'var(--mono)', fill: 'var(--ink)'}, showF ? vtxt(R.f[t]) : '?'));
        svg.append(nodeF);
        if (s.bw !== undefined) {
          const nodeB = sv('g', {'data-link': `h${t + 1}b`});
          nodeB.append(sv('rect', {x: X(t) - 70, y: yB - 20, width: 140, height: 40, rx: 20, fill: showB ? 'var(--bw-bg)' : 'var(--panel)', stroke: 'var(--bw)', 'stroke-width': s.hl === `h${t + 1}b` ? 3.5 : 1.5}));
          nodeB.append(sv('text', {x: X(t), y: yB - 4, 'text-anchor': 'middle', 'font-size': 11, fill: 'var(--bw)'}, `h${t + 1}←`));
          nodeB.append(sv('text', {x: X(t), y: yB + 12, 'text-anchor': 'middle', 'font-size': 12, 'font-family': 'var(--mono)', fill: 'var(--ink)'}, showB ? vtxt(R.b[t]) : '?'));
          svg.append(nodeB);
        }
      });
      // recurrent arrows
      if (s.fw > 1) svg.append(sv('path', {d: `M${X(0) + 70},${yF} L${X(1) - 72},${yF}`, stroke: 'var(--fw)', 'stroke-width': 2.5, 'marker-end': 'url(#ar)'}));
      if (s.bw > 1) svg.append(sv('path', {d: `M${X(1) - 70},${yB} L${X(0) + 72},${yB}`, stroke: 'var(--bw)', 'stroke-width': 2.5, 'marker-end': 'url(#ar)'}));
      // label box for position 1
      const sc = R.b[0][1], lab = s.label === 'fw' ? 'gleich in A und B' : s.label === 'bi' ? `${sc > 0 ? 'PER' : 'LOC'} · s = ${sc > 0 ? '+' : '−'}${de(Math.abs(sc))}` : '';
      if (lab) {
        svg.append(sv('rect', {x: X(0) - 78, y: yL - 18, width: 156, height: 32, rx: 7, fill: 'none', stroke: 'var(--accent2)', 'stroke-width': 2}));
        svg.append(sv('text', {x: X(0), y: yL + 3, 'text-anchor': 'middle', 'font-size': 12.5, fill: 'var(--accent2)', 'font-weight': 600}, 'y₁: ' + lab));
        svg.append(sv('line', {x1: X(0) - 45, y1: yL + 14, x2: X(0) - 45, y2: yF - 20, stroke: 'var(--accent2)', 'stroke-dasharray': '4 3'}));
        if (s.label === 'bi') svg.append(sv('line', {x1: X(0) + 45, y1: yL + 14, x2: X(0) + 45, y2: yB - 20, stroke: 'var(--accent2)', 'stroke-dasharray': '4 3'}));
      }
    });
    const defs = sv('defs'), mk = sv('marker', {id: 'ar', viewBox: '0 0 8 8', refX: 7, refY: 4, markerWidth: 7, markerHeight: 7, orient: 'auto'});
    mk.append(sv('path', {d: 'M0,0L8,4L0,8z', fill: 'var(--mute)'})); defs.append(mk); svg.prepend(defs);
    fig.replaceChildren(svg);
  };
  const steps = [
    {key: true, fw: 0, cap: 'Zwei Sätze, ein mehrdeutiges Wort. Satz A meint die Person, Satz B den Bundesstaat. Unter jedem Wort steht seine Einbettung \\(e_t\\). Nur Wort 2 ist verschieden (orange).', eq: '<span data-link="e1">\\(e_1=(1,0)\\)</span> in beiden Sätzen; <span data-link="e2">\\(e_2=(0,1)\\)</span> in A, \\((0,-1)\\) in B.', alt: 'Zwei Sätze, Einbettungen sichtbar'},
    {fw: 0, cap: 'Das Vorwärts-RNN berechnet zuerst \\(h^{\\rightarrow}_1\\) aus \\(h^{\\rightarrow}_0=0\\) und \\(e_1\\).', eq: '\\(h^{\\rightarrow}_1=\\tanh(0{,}5\\cdot h^{\\rightarrow}_0+e_1)\\)',
      predict: {q: 'Wird \\(h^{\\rightarrow}_1\\) in Satz A und Satz B gleich sein?', options: ['gleich', 'verschieden', 'hängt von den Trainingsdaten ab'], correct: 0, explain: 'In der Formel für \\(h^{\\rightarrow}_1\\) kommt \\(e_2\\) nicht vor. Nur \\(e_1\\) geht ein, und das ist in beiden Sätzen \\((1,0)\\).'}},
    {key: true, fw: 1, hl: 'h1f', cap: '<span data-link="h1f">\\(h^{\\rightarrow}_1\\)</span> ist in beiden Sätzen exakt derselbe Vektor.', eq: `\\[\\begin{aligned}h^{\\rightarrow}_1&=\\tanh\\big(0{,}5\\cdot(0,0)+(1,0)\\big)=(\\tanh 1,\\ \\tanh 0)\\\\&=${vec(A.f[0])}\\quad\\text{in A und B}\\end{aligned}\\]`, alt: 'Vorwärtszustand 1 in beiden Sätzen gleich'},
    {key: true, fw: 2, hl: 'h2f', cap: 'Erst bei Position 2 liest das Vorwärts-RNN das unterschiedliche Wort. <span data-link="h2f">\\(h^{\\rightarrow}_2\\)</span> unterscheidet sich im Vorzeichen der zweiten Komponente.', eq: `\\[\\begin{aligned}\\text{A: }h^{\\rightarrow}_2&=\\tanh\\big(0{,}5\\cdot${vec(A.f[0])}+(0,1)\\big)=${vec(A.f[1])}\\\\ \\text{B: }h^{\\rightarrow}_2&=\\tanh\\big(0{,}5\\cdot${vec(B.f[0])}+(0,-1)\\big)=${vec(B.f[1])}\\end{aligned}\\]`},
    {key: true, fw: 2, label: 'fw', cap: '<b>Gegenbeispiel zur Intuition „das RNN kennt den Satz“.</b> Der Klassifikator für Wort 1 erhält nur <span data-link="h1f">\\(h^{\\rightarrow}_1\\)</span>. Weil seine Eingabe in A und B identisch ist, ist auch seine Ausgabe identisch – für <em>jede</em> Wahl der Gewichte. Mindestens einer der beiden Sätze wird falsch markiert.', eq: '\\(p(y_1\\mid\\text{A})=\\operatorname{softmax}(W_oh^{\\rightarrow}_1+b_o)=p(y_1\\mid\\text{B})\\)'},
    {fw: 2, label: 'fw', cap: 'Was müsste die Darstellung von Wort 1 enthalten, damit A → PER und B → LOC möglich wird?', eq: '',
      predict: {q: 'Was fehlt \\(h^{\\rightarrow}_1\\)?', options: ['Information über Wort 2', 'mehr Trainingsdaten', 'eine größere Dimension \\(d_h\\)'], correct: 0, explain: 'Daten und Dimension ändern nichts daran, dass \\(e_2\\) nicht in \\(h^{\\rightarrow}_1\\) eingeht. Man braucht einen Rechenweg von Wort 2 zu Position 1.'}},
    {key: true, fw: 2, bw: 1, hl: 'h2b', cap: 'Ein zweites RNN liest von rechts. Es beginnt bei Wort 2: <span data-link="h2b">\\(h^{\\leftarrow}_2\\)</span> hängt nur von \\(e_2\\) ab.', eq: `\\[\\text{A: }h^{\\leftarrow}_2=\\tanh\\big(0{,}8\\cdot0+(0,1)\\big)=${vec(A.b[1])},\\qquad \\text{B: }${vec(B.b[1])}\\]`},
    {key: true, fw: 2, bw: 2, hl: 'h1b', cap: 'Dann Position 1: <span data-link="h1b">\\(h^{\\leftarrow}_1\\)</span> mischt \\(e_1\\) mit dem Zustand von rechts. Das Vorzeichen von Wort 2 erreicht damit Wort 1.', eq: `\\[\\begin{aligned}\\text{A: }h^{\\leftarrow}_1&=\\tanh\\big(0{,}8\\cdot${vec(A.b[1])}+(1,0)\\big)=${vec(A.b[0])}\\\\ \\text{B: }h^{\\leftarrow}_1&=\\tanh\\big(0{,}8\\cdot${vec(B.b[1])}+(1,0)\\big)=${vec(B.b[0])}\\end{aligned}\\]`},
    {key: true, fw: 2, bw: 2, label: 'bi', cap: 'Verketten und klassifizieren. Mit \\(v=(0,0,0,1)\\) liest der Score genau die zweite Komponente von \\(h^{\\leftarrow}_1\\): positiv in A, negativ in B. Beide Sätze werden richtig markiert.', eq: `\\[s=v^{\\top}\\big[h^{\\rightarrow}_1;h^{\\leftarrow}_1\\big]=\\begin{cases}${dt(A.b[0][1])}&\\text{A: PER}\\\\${dt(B.b[0][1])}&\\text{B: LOC}\\end{cases}\\]`},
    {key: true, fw: 2, bw: 2, label: 'bi', cap: '<b>Überprüfung am Satz.</b> Was die Zahlen zeigen, gilt allgemein: \\(h^{\\rightarrow}_t\\) ist eine Funktion von \\(x_1,\\dots,x_t\\) (Satz 1), \\(h^{\\leftarrow}_t\\) von \\(x_t,\\dots,x_T\\) (Satz 2). Für \\(t=1,T=2\\): \\(h^{\\rightarrow}_1=F_1(x_1)\\), \\(h^{\\leftarrow}_1=G_1(x_1,x_2)\\).', eq: '\\(\\{1\\}\\cup\\{1,2\\}=\\{1,2\\}\\): erst die Verkettung sieht beide Wörter.'}
  ];
  return {id: 'birnn', title: 'Das Washington-Experiment: was ein Zustand sehen kann', steps, draw};
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
  return {id: 'f1', title: 'F1 aus Zählungen – inklusive aller Fälle mit Nenner 0', steps, draw};
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
  return {id: 'counter', title: 'Dieselbe Vorhersage, zwei Urteile', steps, draw};
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
  return {id: 'micromacro', title: 'Was eine seltene Klasse mit Micro und Macro macht', steps, draw};
}
// ---- scene 5: self-attention as soft lookup, then permutation counterexample ----
function attnRow(q, K, V, scale = true) {
  const d = q.length, e = K.map(k => k.reduce((a, x, i) => a + x * q[i], 0) / (scale ? Math.sqrt(d) : 1));
  const m = Math.max(...e), ex = e.map(x => Math.exp(x - m)), z = ex.reduce((a, b) => a + b, 0), w = ex.map(x => x / z);
  return {e, w, o: V[0].map((_, j) => V.reduce((a, v, i) => a + w[i] * v[j], 0))};
}
function sceneAttention() {
  const words = ['x₁', 'x₂', 'x₃'], X = [[1, 0], [0, 1], [1, 1]];
  const draw = (fig, s) => {
    const order = s.perm || [0, 1, 2], Xp = order.map(i => X[i]), qi = s.q ?? 2;
    const r = attnRow(Xp[qi], Xp, Xp, s.scale !== false);
    const svg = sv('svg', {viewBox: '0 0 760 270', class: 'plot', role: 'img', 'aria-label': `Gewichte ${r.w.map(x => de(x, 3)).join(', ')}`});
    const X0 = i => 130 + i * 250, boxTop = 180;
    // arcs first, so that all labels are drawn on top of them
    if (s.show >= 2) order.forEach((src, i) => svg.append(sv('path', {d: `M${X0(i)},${boxTop} C${X0(i)},${boxTop - 60} ${X0(qi)},${boxTop - 90} ${X0(qi)},66`, fill: 'none', stroke: 'var(--accent2)', 'stroke-width': 1 + 14 * r.w[i], opacity: .55})));
    order.forEach((src, i) => {
      const isQ = i === qi;
      svg.append(sv('rect', {x: X0(i) - 85, y: boxTop, width: 170, height: 76, rx: 10, fill: isQ ? 'var(--fw-bg)' : 'var(--panel)', stroke: isQ ? 'var(--fw)' : 'var(--line)', 'stroke-width': isQ ? 2.5 : 1.2, 'data-link': 'k' + (i + 1)}));
      svg.append(sv('text', {x: X0(i), y: boxTop + 22, 'text-anchor': 'middle', 'font-size': 15, fill: 'var(--ink)'}, `${words[src]} = (${X[src].join(', ')})`));
      svg.append(sv('text', {x: X0(i), y: boxTop + 42, 'text-anchor': 'middle', 'font-size': 11.5, fill: 'var(--mute)'}, isQ ? 'Anfrage, Schlüssel, Wert' : 'Schlüssel und Wert'));
      if (s.show >= 1) svg.append(sv('text', {x: X0(i), y: boxTop + 64, 'text-anchor': 'middle', 'font-size': 12.5, fill: 'var(--ink)', 'font-family': 'var(--mono)'}, `e = ${de(r.e[i], 4)}`));
      if (s.show >= 2) {
        const lx = X0(i) + (i === qi ? 0 : (i < qi ? 40 : -40)), ly = i === qi ? 130 : 150;
        svg.append(sv('rect', {x: lx - 58, y: ly - 15, width: 116, height: 22, rx: 6, fill: 'var(--panel)', stroke: 'var(--accent2)', 'stroke-width': .8}));
        svg.append(sv('text', {x: lx, y: ly + 1, 'text-anchor': 'middle', 'font-size': 13, fill: 'var(--accent2)', 'font-weight': 600, 'data-link': 'a' + (i + 1)}, `α = ${de(r.w[i], 4)}`));
      }
    });
    if (s.show >= 3) {
      svg.append(sv('rect', {x: X0(qi) - 100, y: 26, width: 200, height: 40, rx: 8, fill: 'var(--panel)', stroke: 'var(--accent2)', 'stroke-width': 2, 'data-link': 'o'}));
      svg.append(sv('text', {x: X0(qi), y: 51, 'text-anchor': 'middle', 'font-size': 14, fill: 'var(--accent2)', 'font-weight': 600}, `o = (${de(r.o[0], 4)}; ${de(r.o[1], 4)})`));
    }
    fig.replaceChildren(svg);
  };
  const base = attnRow(X[2], X, X), raw = attnRow(X[2], X, X, false);
  const steps = [
    {key: true, show: 0, cap: 'Drei Token als Vektoren. Mit \\(W_Q=W_K=W_V=I\\) ist jedes Token zugleich Anfrage, Schlüssel und Wert. Wir berechnen die Ausgabe für Token 3, die Anfrage \\(q_3=(1,1)\\).', eq: ''},
    {key: true, show: 1, cap: 'Ähnlichkeit: Skalarprodukt mit jedem Schlüssel, geteilt durch \\(\\sqrt{d_k}=\\sqrt2\\).', eq: `\\(e_{3j}=q_3^\\top k_j/\\sqrt2=${base.e.map(x => dt(x)).join(';\\ ')}\\)`},
    {show: 1, cap: 'Gleich wird die Softmax angewandt.', eq: '',
      predict: {q: 'Welches Token bekommt das größte Gewicht?', options: ['Token 3 selbst', 'alle gleich', 'Token 1'], correct: 0, explain: '\\(q_3\\) hat mit \\(k_3=(1,1)\\) das größte Skalarprodukt (2 gegenüber 1). Die Softmax erhält die Reihenfolge der Energien.'}},
    {key: true, show: 2, cap: 'Softmax: <span data-link="a3">\\(\\alpha_{33}\\)</span> ist das größte Gewicht. Die Gewichte summieren sich zu 1 – die Ausgabe ist ein Durchschnitt der Werte, kein Auswahlvorgang.', eq: `\\(\\alpha_{3\\cdot}=(${base.w.map(x => dt(x)).join(';\\ ')})\\)`},
    {key: true, show: 3, cap: 'Gewichtete Summe der Werte: die neue Darstellung <span data-link="o">\\(o_3\\)</span> von Token 3 ist eine Mischung aller drei Token.', eq: `\\(o_3=\\sum_j\\alpha_{3j}v_j=(${dt(base.o[0])};\\ ${dt(base.o[1])})\\)`},
    {show: 3, scale: false, cap: '<b>Gegenprobe ohne Skalierung.</b> Energien 1, 1, 2: Die Softmax wird spitzer. Bei großen \\(d_k\\) wachsen die Energien mit (Satz 3), und die Softmax nähert sich einem harten \\(\\arg\\max\\).', eq: `\\(\\alpha_{33}=${dt(raw.w[2])}\\) statt \\(${dt(base.w[2])}\\)`},
    {show: 3, perm: [1, 0, 2], cap: 'Jetzt vertauschen wir Token 1 und 2. Token 3 steht weiter an Position 3.', eq: '',
      predict: {q: 'Ändert sich \\(o_3\\)?', options: ['nein', 'ja, weil sich die Reihenfolge geändert hat', 'nur die Gewichte, nicht die Ausgabe'], correct: 0, explain: 'Die Gewichte wandern mit den Token mit, die gewichtete Summe bleibt dieselbe (Satz 4). Self-Attention ohne Positionskodierung sieht keine Reihenfolge.'}},
    {key: true, show: 3, perm: [1, 0, 2], cap: '<b>Verifikation.</b> \\(o_3\\) ist exakt gleich – die Reihenfolge der anderen Token ist für Self-Attention unsichtbar. Genau deshalb braucht man Positionskodierungen (Abschnitt 7).', eq: `\\(o_3=(${dt(base.o[0])};\\ ${dt(base.o[1])})\\) vor und nach der Vertauschung`}
  ];
  return {id: 'attention', title: 'Self-Attention als weiche Suche', steps, draw};
}

// ---- scene 6: Viterbi repairs an invalid greedy sequence ----
function sceneViterbi() {
  const L = ['O', 'B-LOC', 'I-LOC'], W = ['in', 'New', 'York'], E = [[2, 0, 0.5], [0.3, 1.0, 1.2], [0, 0.2, 1.5]];
  const allowed = (p, c) => !c.startsWith('I-') || (p !== null && p !== 'O' && p.slice(2) === c.slice(2));
  const greedyPath = E.map(r => r.indexOf(Math.max(...r)));
  function vit() { let best = L.map((c, k) => allowed(null, c) ? {s: E[0][k], p: [k]} : null);
    for (let t = 1; t < E.length; t++) best = L.map((c, k) => { let b = null; best.forEach((x, j) => { if (x && allowed(L[j], c)) { const v = x.s + E[t][k]; if (!b || v > b.s) b = {s: v, p: [...x.p, k]}; } }); return b; });
    return best.filter(Boolean).reduce((a, b) => b.s > a.s ? b : a); }
  const V = vit();
  const draw = (fig, s) => {
    const svg = sv('svg', {viewBox: '0 0 760 280', class: 'plot', role: 'img'});
    const X = t => 150 + t * 230, Y = k => 60 + k * 80;
    L.forEach((l, k) => svg.append(sv('text', {x: 20, y: Y(k) + 5, 'font-size': 14, fill: 'var(--mute)', 'font-family': 'var(--mono)'}, l)));
    W.forEach((w, t) => svg.append(sv('text', {x: X(t), y: 270, 'text-anchor': 'middle', 'font-size': 15, fill: 'var(--ink)'}, w)));
    if (s.edges) for (let t = 1; t < 3; t++) L.forEach((c, k) => L.forEach((p, j) => { const ok = allowed(p, c);
      svg.append(sv('line', {x1: X(t - 1) + 34, y1: Y(j), x2: X(t) - 34, y2: Y(k), stroke: ok ? 'var(--line2)' : 'var(--bad)', 'stroke-width': ok ? 1 : 1.5, 'stroke-dasharray': ok ? '' : '4 3', opacity: ok ? 1 : .8})); }));
    const path = s.path === 'greedy' ? greedyPath : s.path === 'viterbi' ? V.p : null;
    if (path) for (let t = 1; t < 3; t++) svg.append(sv('line', {x1: X(t - 1) + 34, y1: Y(path[t - 1]), x2: X(t) - 34, y2: Y(path[t]), stroke: s.path === 'greedy' ? 'var(--bad)' : 'var(--ok)', 'stroke-width': 4}));
    E.forEach((row, t) => row.forEach((v, k) => { const on = path && path[t] === k;
      svg.append(sv('rect', {x: X(t) - 34, y: Y(k) - 20, width: 68, height: 40, rx: 8, fill: on ? (s.path === 'greedy' ? 'var(--bw-bg)' : 'var(--fw-bg)') : 'var(--panel)', stroke: on ? 'var(--ink)' : 'var(--line)', 'stroke-width': on ? 2 : 1}));
      svg.append(sv('text', {x: X(t), y: Y(k) + 5, 'text-anchor': 'middle', 'font-size': 14, 'font-family': 'var(--mono)', fill: 'var(--ink)'}, de(v, 1))); }));
    if (s.edges) svg.append(sv('text', {x: 400, y: 20, 'text-anchor': 'middle', 'font-size': 12, fill: 'var(--bad)'}, 'rot gestrichelt: verbotene Übergänge (… → I-LOC ohne vorheriges B-/I-LOC)'));
    fig.replaceChildren(svg);
  };
  const gs = greedyPath.reduce((a, k, t) => a + E[t][k], 0);
  const steps = [
    {key: true, cap: 'Emissionswerte \\(s_t(\\ell)\\) eines BiRNN für „in New York“: je Wort und Label eine Zahl. Höher heißt: passender.', eq: ''},
    {path: 'greedy', cap: 'Gierige Dekodierung nimmt je Wort das Maximum.', eq: '',
      predict: {q: 'Ist die gierige Folge gültiges BIO?', options: ['nein', 'ja'], correct: 0, explain: '<code>O I-LOC I-LOC</code>: Ein I-LOC darf nicht auf O folgen.'}},
    {key: true, path: 'greedy', cap: `Gierig: <code>${greedyPath.map(k => L[k]).join(' ')}</code> mit Score ${de(gs, 1)} – höchster Score, aber ungültig.`, eq: ''},
    {key: true, edges: true, cap: 'Das CRF bewertet ganze Pfade: Emissionen plus Übergänge. Verbotene Übergänge (rot) haben den Wert \\(-\\infty\\), erlaubte hier 0.', eq: '\\(\\operatorname{score}(y)=\\sum_t s_t(y_t)+A_{y_{t-1},y_t}\\)'},
    {key: true, edges: true, path: 'viterbi', cap: `Viterbi findet den besten <em>erlaubten</em> Pfad: <code>${V.p.map(k => L[k]).join(' ')}</code> mit Score ${de(V.s, 1)}. Er gibt bei „New“ das schwächere B-LOC (1,0 statt 1,2) in Kauf, weil nur so ein gültiger Pfad durch York/I-LOC führt.`, eq: `\\(2+1{,}0+1{,}5=${dt(V.s, 1)}\\)`},
    {edges: true, path: 'viterbi', cap: '<b>Grenze.</b> Die Regeln verbieten nur ungültige Folgen. Eine gültige, aber falsche Folge – etwa <code>B-LOC I-LOC</code> über „Berlin .“ – bleibt erlaubt; das zeigt die Fallstudie (Abschnitt 13).', eq: ''}
  ];
  return {id: 'viterbi', title: 'Viterbi: der beste gültige Pfad', steps, draw};
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
const SCENES = {birnn: sceneBirnn, f1: sceneF1, counter: sceneCounter, micromacro: sceneMicroMacro, attention: sceneAttention, viterbi: sceneViterbi};
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
    if (a.type === 'num' || a.type === 'set') wrap.append(el('input', {type: 'text', id, inputmode: a.type === 'set' ? 'text' : 'decimal', placeholder: a.type === 'set' ? 'z. B. 1, 2, 3' : 'Bruch (2/7) oder Dezimalzahl', autocomplete: 'off', enterkeyhint: 'done'}));
    else if (a.type === 'choice') wrap.append(el('div', {role: 'radiogroup', id, 'aria-label': a.label}, a.options.map((o, k) => el('label', {class: 'radio'}, el('input', {type: 'radio', name: id, value: k}), ' ', el('span', {html: o})))));
    else wrap.append(el('textarea', {id, rows: 5, placeholder: 'Ihr Beweis bzw. Ihre Begründung'}));
    return wrap;
  });
  box.append(...inputs);
  if (ctx.exam) return box;
  const fb = el('div', {}), hintBox = el('div', {}), sol = el('div', {class: 'sol', hidden: true, html: `<b>Musterlösung.</b> ${task.solution}` + (task.rubric ? '<p class="mute">Bewertung: ' + task.rubric.join(' · ') + '</p>' : '')});
  const hasHints = (task.hints || []).length > 0;
  const bHint = el('button', {disabled: true, onclick: () => { if (hintsShown < task.hints.length) { hintBox.append(el('p', {class: 'fb hint', html: 'Hinweis: ' + task.hints[hintsShown++]})); tex(hintBox); } bHint.disabled = hintsShown >= task.hints.length; }}, 'Hinweis');
  const bSol = el('button', {onclick: () => { if (!tries().length && !confirm('Lösung ansehen, ohne es versucht zu haben? Die Aufgabe zählt dann als unterstützt.')) return; revealed = true; sol.hidden = false; tex(sol); if (!tries().length) record(task, false, {revealed: true, hints: hintsShown}); }}, 'Lösung anzeigen');
  const bCheck = el('button', {class: 'primary', onclick: check}, task.answers[0].type === 'self' ? 'Abgeben' : 'Prüfen');
  box.append(el('div', {class: 'ctl'}, bCheck, hasHints ? bHint : null, bSol), fb, hintBox, sol);
  if (hasHints) box.append(el('p', {class: 'mute small'}, 'Hinweise werden nach Ihrem ersten eigenen Versuch freigeschaltet.'));
  box.addEventListener('keydown', e => { if (e.key === 'Enter' && e.target.tagName === 'INPUT' && e.target.type === 'text') check(); });
  function check() {
    const msgs = []; let all = true;
    task.answers.forEach((a, i) => {
      const id = `${task.id}-a${i}`;
      if (a.type === 'num') { const v = $(`#${id}`, box).value, ok = numOk(v, a); if (ok === null) { all = false; msgs.push(['bad', `${a.label}: bitte eine Zahl oder einen Bruch eingeben.`]); return; } all &&= ok; msgs.push(ok ? ['ok', `${a.label}: richtig.`] : ['bad', `${a.label}: noch nicht. ` + (diagnose(v, a) || 'Schreiben Sie die Zwischenwerte einzeln auf und vergleichen Sie mit der Definition.')]); }
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
  }
  const rest = U.tasks.filter(t => !U.text_html.includes(`data-task="${t.id}"`));
  if (rest.length) { toc.append(el('a', {href: '#learn/weitere'}, 'Weitere Aufgaben')); main.append(el('h2', {id: 'weitere'}, 'Weitere Aufgaben'), ...rest.map(t => renderTask(t))); }
  main.append(el('div', {class: 'card hero', style: 'margin-top:30px'}, el('h3', {}, 'Abschluss'), el('p', {}, `Prüfung ohne Hilfe, Form ${nextForm()}. Nach mindestens 24 h ohne Üben folgt die andere Form – erst sie zählt für „wahrscheinlich sicher“.`), el('button', {class: 'primary', onclick: () => go('exam')}, 'Zur Prüfung')));
  mountScenes(main, false);
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
const sectionOf = id => { const sec = sections().find(x => x.innerHTML.includes(`data-task="${id}"`)); return sec ? sec.dataset.title : 'Weitere Aufgaben'; };
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
  m.append(el('h2', {}, 'Literatur'), el('ol', {class: 'refs'}, U.sources.map(s => el('li', {}, s.ref, s.doi ? ` doi:${s.doi}` : s.url ? ` ${s.url}` : ''))));
}
function taskBlock(t, withSolution) {
  const b = el('div', {class: 'task'}, el('header', {}, el('span', {class: 'stage'}, STAGE[t.stage] || ''), el('b', {}, `${t.id} · ${t.title}`), el('span', {class: 'mute small'}, KCS[t.kc])), el('div', {html: t.prompt}));
  if (t.steps && (!withSolution || t.stage === 'worked')) b.append(el('ol', {class: 'steps'}, t.steps.map(x => el('li', {class: x.blank ? 'blank' : ''}, el('span', {html: x.s}), el('span', {class: 'why', html: x.why})))));
  if (!withSolution) {
    t.answers.filter(a => a.type === 'choice').forEach(a => b.append(el('p', {html: a.label + ':'}), el('ol', {type: 'a'}, a.options.map(o => el('li', {html: o})))));
    if (t.stage !== 'worked') b.append(el('div', {class: 'space', style: `height:${t.stage === 'transfer' ? 70 : 40}mm`}));
    return b;
  }
  b.append(el('div', {class: 'sol', html: '<b>Lösung.</b> ' + t.solution}));
  const diags = t.answers.flatMap(a => (a.diagnoses || []).map(d => a.type === 'choice' ? `Option ${'abcdefg'[+d.value]}: ${d.msg}` : `Antwort ${d.value}: ${d.msg}`));
  if (diags.length) b.append(el('p', {class: 'mute', html: '<b>Typische Fehler.</b> ' + diags.join(' · ')}));
  if (t.rubric) b.append(el('p', {class: 'mute', html: '<b>Bewertung.</b> ' + t.rubric.join(' · ')}));
  return b;
}
function bookArbeitsbuch(m, sol) {
  m.append(el('p', {}, sol ? 'Zu jeder Aufgabe des Arbeitsbuchs: vollständige Lösung, typische Fehler mit Diagnose und Bewertungsschema.' : 'Die Aufgaben sind nach Abschnitten des Lehrbuchs geordnet und gestuft: durchgerechnet → Lückenschritt → mit Hinweisen → selbstständig → Fehleranalyse → Transfer. Hinweise stehen am Ende; schlagen Sie sie erst nach einem eigenen Versuch nach.'));
  let cur = null;
  for (const t of U.tasks) { const sec = sectionOf(t.id); if (sec !== cur) { m.append(el('h2', {}, sec)); cur = sec; } m.append(taskBlock(t, sol)); }
  if (!sol) m.append(el('h2', {}, 'Hinweise'), el('dl', {}, U.tasks.filter(t => (t.hints || []).length).flatMap(t => [el('dt', {}, t.id), el('dd', {html: t.hints.join(' · ')})])));
}
function bookKlausur(m, sol) {
  const pts = x => x.answers.length * 2;
  m.append(el('h2', {}, 'Aufbau'), el('p', {}, 'Zwei gleichwertige, voneinander unabhängige Formen A und B mit neuen Daten (keine Aufgabe des Arbeitsbuchs wird wiederverwendet). Je Kompetenz zwei Aufgaben, davon eine Transferaufgabe bei sieben der neun Kompetenzen. Bewertung: 2 Punkte je Teilantwort. Offizielle Angaben zu Dauer und Hilfsmitteln der Klausur liegen nicht vor; die Form ist ohne Hilfsmittel gedacht.'),
    el('table', {}, el('tr', {}, el('th', {}, 'Kompetenz'), el('th', {}, 'Form A'), el('th', {}, 'Form B')), Object.entries(KCS).map(([k, l]) => el('tr', {}, el('td', {}, l), ...['A', 'B'].map(f => el('td', {}, FORMS[f].filter(x => x.kc === k).map(x => x.id + (x.transfer ? ' (T)' : '')).join(', ')))))));
  for (const [f, items] of Object.entries(FORMS)) {
    m.append(el('h2', {}, `Form ${f}` + (sol ? ' – Lösungen' : '')), el('p', {class: 'mute small'}, `Summe: ${items.reduce((a, x) => a + pts(x), 0)} Punkte.`));
    items.forEach(x => { const b = el('div', {class: 'task'}, el('header', {}, el('b', {}, `${x.id}`), el('span', {class: 'mute small'}, `${KCS[x.kc]}${x.transfer ? ' · Transfer' : ''} · ${pts(x)} P.`)), el('div', {html: x.prompt}));
      x.answers.filter(a => a.type === 'choice').forEach(a => b.append(el('ol', {type: 'a'}, a.options.map((o, k) => el('li', {html: o + (sol && k === a.correct ? ' <b>✓</b>' : '')})))));
      if (sol) b.append(el('div', {class: 'sol', html: '<b>Lösung.</b> ' + x.solution})); else b.append(el('div', {class: 'space', style: 'height:28mm'}));
      m.append(b); });
  }
}
function book() {
  const m = el('main', {class: 'print-' + PART}); app.replaceChildren(m); titlePage(m);
  ({lehrbuch: () => bookLehrbuch(m), arbeitsbuch: () => bookArbeitsbuch(m, false), loesungen: () => bookArbeitsbuch(m, true), klausur: () => bookKlausur(m, false), klausur_loesungen: () => bookKlausur(m, true)})[PART]();
  mountScenes(m, true);
  const done = () => { document.body.dataset.ready = '1'; };
  const wait = () => window.MathJax && MathJax.startup && MathJax.startup.promise ? MathJax.startup.promise.then(() => MathJax.typesetPromise([m])).then(done, done) : setTimeout(wait, 50);
  wait();
}

if (MODE === 'print') book();
else { render(); (function w() { if (window.MathJax && MathJax.startup && MathJax.startup.promise) MathJax.startup.promise.then(() => tex(app)).then(() => { document.body.dataset.ready = '1'; }); else setTimeout(w, 50); })(); }
})();
