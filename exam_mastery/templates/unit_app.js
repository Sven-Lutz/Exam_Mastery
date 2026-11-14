(() => {
'use strict';
const U = JSON.parse(document.getElementById('unit-data').textContent);
const MODE = document.body.dataset.mode;
const KEY = 'em-unit-' + U.id, DAY = 864e5, BOX = [0, 1, 3, 7, 16, 35];
const STAGE = {worked: 'Durchgerechnetes Beispiel', faded: 'Lückenschritt', hint: 'Mit Hinweisen', independent: 'Selbstständig', error: 'Fehleranalyse', transfer: 'Transfer'};
const KCS = {birnn: 'BiRNN und Abhängigkeitsbereich', prf: 'Precision, Recall, F1', 'prf-edge': 'Grenzfälle (Nenner 0)', 'prf-level': 'Phrasen- vs. Token-Ebene', 'micro-macro': 'Micro- und Macro-Mittelung'};
const SECTION_KC = {rnn: 'birnn', birnn: 'birnn', prf: 'prf', einheit: 'prf-level', mittelung: 'micro-macro'};
const ALL = [...U.tasks, ...U.exam];

// ---------- state (local only; per viewer) ----------
const blank = () => ({v: 1, attempts: [], exams: [], cards: {}, visited: {}, last: null});
let st = blank();
try { st = Object.assign(blank(), JSON.parse(localStorage.getItem(KEY) || '{}')); } catch (e) { /* storage unavailable */ }
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(st)); } catch (e) { /* ignore */ } };
const now = () => Date.now();

// ---------- helpers ----------
const el = (tag, attrs = {}, ...kids) => {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'html') n.innerHTML = v; else if (k.startsWith('on')) n.addEventListener(k.slice(2), v);
    else if (v !== false && v != null) n.setAttribute(k, v === true ? '' : v);
  }
  for (const c of kids.flat()) if (c != null) n.append(c.nodeType ? c : document.createTextNode(c));
  return n;
};
const tex = node => (window.MathJax && MathJax.typesetPromise) ? MathJax.typesetPromise([node]).catch(() => {}) : Promise.resolve();
const de = (x, d = 4) => x == null ? 'undef.' : Number(x).toFixed(d).replace('.', ',');
const dt = (x, d = 3) => Number(x).toFixed(d).replace('.', '{,}');
function parseNum(s) {
  s = String(s).trim().replace(/\s/g, '').replace(',', '.');
  if (!s) return null;
  const m = s.match(/^(-?\d+(?:\.\d+)?)\/(\d+(?:\.\d+)?)$/);
  if (m) return {v: +m[1] / +m[2], exact: true};
  if (!/^-?\d+(\.\d+)?$/.test(s)) return null;
  return {v: +s, exact: false, dec: (s.split('.')[1] || '').length};
}
function numOk(input, a) {
  const p = parseNum(input); if (!p) return null;
  const v = a.float, tol = a.tol || 0.0005;
  if (Math.abs(p.v - v) <= Math.max(1e-9, p.exact ? 1e-9 : tol)) return true;
  if (!p.exact && p.dec >= 2 && Number(v.toFixed(p.dec)) === p.v) return true;
  return false;
}
function diagnose(input, a) {
  const p = parseNum(input); if (!p) return null;
  for (const d of a.diagnoses || []) { const q = parseNum(d.value); if (q && Math.abs(q.v - p.v) <= 0.0006) return d.msg; }
  return null;
}

// ---------- learner model ----------
const kcOf = id => (ALL.find(t => t.id === id) || {}).kc;
function series() {
  const s = {assisted: [], immediate: [], delayed: [], transfer: []};
  for (const a of st.attempts) {
    s.assisted.push(a);
    if (a.stage === 'transfer' && a.first && !a.hints && !a.revealed) s.transfer.push(a);
  }
  for (const ex of st.exams) for (const it of ex.items) (it.delayed ? s.delayed : s.immediate).push(it);
  return s;
}
function lastAssisted(kc) { return Math.max(0, ...st.attempts.filter(a => a.kc === kc).map(a => a.ts)); }
function kcStatus(kc) {
  const items = st.exams.flatMap(e => e.items.map(i => ({...i, ts: e.ts}))).filter(i => i.kc === kc);
  const lastEx = items.length ? Math.max(...items.map(i => i.ts)) : 0;
  const latest = items.filter(i => i.ts === lastEx);
  if (latest.length && latest.every(i => i.correct) && latest.every(i => i.delayed)) return ['GEMEISTERT', 'verzögert und ohne Hilfe gelöst'];
  if (latest.length && latest.every(i => i.correct)) return ['SOFORT_OHNE_HILFE', 'ohne Hilfe gelöst; verzögerte Prüfung steht aus'];
  const att = st.attempts.filter(a => a.kc === kc);
  if (latest.length || att.some(a => !a.correct)) return ['LUECKE', 'Fehler in Übung oder Prüfung'];
  if (att.length) return ['GEUEBT', 'mit Unterstützung geübt'];
  return ['NEU', 'noch nicht bearbeitet'];
}
function record(task, correct, extra) {
  const prev = st.attempts.filter(a => a.task === task.id);
  st.attempts.push({task: task.id, kc: task.kc, stage: task.stage, ts: now(), correct, first: prev.length === 0, ...extra});
  save();
}
function introduceCards(kc) {
  for (const c of U.cards) if (c.kc === kc || (kc === 'prf' && c.kc.startsWith('prf'))) if (!st.cards[c.key]) st.cards[c.key] = {box: 0, due: now()};
  save();
}
const dueCards = () => U.cards.filter(c => st.cards[c.key] && st.cards[c.key].due <= now());

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
const prf = c => ({P: ratio(c.tp, c.tp + c.fp), R: ratio(c.tp, c.tp + c.fn), F: ratio(2 * c.tp, 2 * c.tp + c.fp + c.fn)});
window.__emMetrics = {spans: t => [...spans(t)], spanCounts, tokenCounts, prf};

// ---------- visualisations ----------
const NS = 'http://www.w3.org/2000/svg';
const sv = (tag, attrs = {}, txt) => { const n = document.createElementNS(NS, tag); for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v); if (txt != null) n.textContent = txt; return n; };
const VIZ = {};

VIZ.flow = (root, opts = {}) => {
  const words = ['Washington', 'signed', 'the', 'bill', 'on', 'Monday'], T = words.length;
  let dir = opts.dir || 'forward', t = opts.t || 1, timer = null;
  root.append(el('h4', {}, 'Wer sieht was? Abhängigkeitsbereich von \\(h_t\\)'),
    el('p', {class: 'cap'}, 'Wählen Sie eine Richtung und eine Position. Markiert sind genau die Eingaben, von denen der Zustand nach Satz 1 bzw. 2 abhängen kann, und die Rechenkanten, über die diese Information fließt.'));
  const ctl = el('div', {class: 'ctl'});
  const radios = ['forward', 'backward', 'bi'].map(d => el('label', {}, el('input', {type: 'radio', name: 'dir' + root.dataset.n, value: d, checked: d === dir, onchange: () => { dir = d; draw(); }}), ' ', {forward: 'vorwärts', backward: 'rückwärts', bi: 'bidirektional'}[d]));
  const slider = el('input', {type: 'range', min: 1, max: T, value: t, 'aria-label': 'Position t', oninput: e => { t = +e.target.value; draw(); }});
  ctl.append(...radios, el('span', {}, ' t ='), slider,
    el('button', {onclick: () => { t = Math.max(1, t - 1); draw(); }, 'aria-label': 'Schritt zurück'}, '◀'),
    el('button', {onclick: () => { t = Math.min(T, t + 1); draw(); }, 'aria-label': 'Schritt vor'}, '▶'),
    el('button', {onclick: () => { clearInterval(timer); t = 1; draw(); timer = setInterval(() => { if (t >= T) return clearInterval(timer); t++; draw(); }, 900); }}, 'Abspielen'),
    el('button', {onclick: () => { clearInterval(timer); dir = 'forward'; t = 1; radios.forEach(r => r.querySelector('input').checked = r.querySelector('input').value === 'forward'); draw(); }}, 'Zurücksetzen'));
  const svg = sv('svg', {viewBox: '0 0 720 300', role: 'img', class: 'plot'});
  const formula = el('div', {class: 'formula'});
  root.append(ctl, svg, formula);
  function draw() {
    slider.value = t; svg.replaceChildren();
    const x = i => 70 + i * 116, yIn = 262, yF = 180, yB = 110, yOut = 34;
    const dep = new Set(dir === 'forward' ? [...Array(t).keys()].map(i => i + 1) : dir === 'backward' ? [...Array(T - t + 1).keys()].map(i => i + t) : [...Array(T).keys()].map(i => i + 1));
    const fwOn = i => (dir !== 'backward') && i <= t, bwOn = i => (dir !== 'forward') && i >= t;
    const col = on => on ? 'var(--ink)' : 'var(--line)';
    for (let i = 1; i <= T; i++) {
      // edges input -> states
      svg.append(sv('line', {x1: x(i - 1), y1: yIn - 16, x2: x(i - 1) - 14, y2: yF + 16, stroke: fwOn(i) ? 'var(--fw)' : 'var(--line)', 'stroke-width': fwOn(i) ? 2.5 : 1.2}));
      svg.append(sv('line', {x1: x(i - 1), y1: yIn - 16, x2: x(i - 1) + 14, y2: yB + 16, stroke: bwOn(i) ? 'var(--bw)' : 'var(--line)', 'stroke-width': bwOn(i) ? 2.5 : 1.2}));
      if (i < T) {
        svg.append(sv('line', {x1: x(i - 1) + 6, y1: yF, x2: x(i) - 34, y2: yF, stroke: fwOn(i + 1) && dir !== 'backward' ? 'var(--fw)' : 'var(--line)', 'stroke-width': fwOn(i + 1) ? 2.5 : 1.2, 'marker-end': 'url(#a)'}));
        svg.append(sv('line', {x1: x(i) + 6, y1: yB, x2: x(i - 1) + 34, y2: yB, stroke: bwOn(i) && dir !== 'forward' ? 'var(--bw)' : 'var(--line)', 'stroke-width': bwOn(i) ? 2.5 : 1.2, 'marker-end': 'url(#a)'}));
      }
      const isT = i === t;
      svg.append(sv('rect', {x: x(i - 1) - 46, y: yIn - 16, width: 92, height: 30, rx: 6, fill: dep.has(i) ? 'var(--soft)' : 'transparent', stroke: dep.has(i) ? 'var(--accent)' : 'var(--line)', 'stroke-width': dep.has(i) ? 2 : 1}));
      svg.append(sv('text', {x: x(i - 1), y: yIn + 4, 'text-anchor': 'middle', 'font-size': 14, fill: col(true)}, words[i - 1]));
      svg.append(sv('circle', {cx: x(i - 1) - 14, cy: yF, r: 15, fill: fwOn(i) ? 'var(--fw)' : 'var(--panel)', stroke: 'var(--fw)', opacity: dir === 'backward' ? .25 : 1}));
      svg.append(sv('circle', {cx: x(i - 1) + 14, cy: yB, r: 15, fill: bwOn(i) ? 'var(--bw)' : 'var(--panel)', stroke: 'var(--bw)', opacity: dir === 'forward' ? .25 : 1}));
      if (isT) {
        svg.append(sv('rect', {x: x(i - 1) - 40, y: yOut - 16, width: 80, height: 28, rx: 6, fill: 'none', stroke: 'var(--accent2)', 'stroke-width': 2}));
        svg.append(sv('text', {x: x(i - 1), y: yOut + 3, 'text-anchor': 'middle', 'font-size': 13, fill: 'var(--accent2)'}, 'Label y' + t));
        svg.append(sv('line', {x1: x(i - 1), y1: yOut + 12, x2: x(i - 1) + (dir === 'forward' ? -14 : dir === 'backward' ? 14 : 0), y2: dir === 'forward' ? yF - 16 : yB - 16, stroke: 'var(--accent2)', 'stroke-dasharray': '4 3'}));
      }
    }
    const defs = sv('defs'); const mk = sv('marker', {id: 'a', viewBox: '0 0 8 8', refX: 7, refY: 4, markerWidth: 6, markerHeight: 6, orient: 'auto'}); mk.append(sv('path', {d: 'M0,0L8,4L0,8z', fill: 'var(--mute)'})); defs.append(mk); svg.prepend(defs);
    svg.append(sv('text', {x: 6, y: yF + 5, 'font-size': 12, fill: 'var(--fw)'}, 'h→'), sv('text', {x: 6, y: yB + 5, 'font-size': 12, fill: 'var(--bw)'}, 'h←'), sv('text', {x: 6, y: yIn + 4, 'font-size': 12, fill: 'var(--mute)'}, 'x'));
    const idx = [...dep].sort((a, b) => a - b).map(i => 'x_' + i).join(',');
    formula.innerHTML = dir === 'forward' ? `\\(h_${t}^{\\rightarrow}=\\tanh(W h_${t - 1}^{\\rightarrow}+U e_${t}+b)\\) hängt ab von \\(${idx}\\).`
      : dir === 'backward' ? `\\(h_${t}^{\\leftarrow}=\\tanh(W' h_${t + 1}^{\\leftarrow}+U' e_${t}+b')\\) hängt ab von \\(${idx}\\).`
      : `\\(h_${t}^{\\mathrm{bi}}=[h_${t}^{\\rightarrow};h_${t}^{\\leftarrow}]\\) hängt ab von \\(${idx}\\) – dem ganzen Satz.`;
    tex(formula);
    svg.setAttribute('aria-label', `Richtung ${dir}, Position ${t}: abhängig von Eingaben ${[...dep].join(', ')}`);
  }
  draw();
};

VIZ.f1map = (root, opts = {}) => {
  let P = opts.P ?? .1, R = opts.R ?? 1, showAM = true;
  root.append(el('h4', {}, 'Die F1-Landschaft: warum das harmonische Mittel Ungleichgewicht bestraft'),
    el('p', {class: 'cap'}, 'Durchgezogen: Linien gleichen F1-Werts. Gestrichelt: Linien gleichen arithmetischen Mittels. Ziehen Sie den Punkt (oder Pfeiltasten). Wo beide Linienscharen auseinanderlaufen, unterscheiden sich die Kennzahlen.'));
  const ctl = el('div', {class: 'ctl'},
    el('button', {onclick: () => set(.1, 1)}, 'Alles markieren'), el('button', {onclick: () => set(.6, .6)}, 'Ausgewogen'), el('button', {onclick: () => set(.95, .3)}, 'Vorsichtig'),
    el('label', {}, el('input', {type: 'checkbox', checked: true, onchange: e => { showAM = e.target.checked; draw(); }}), ' arithmetisches Mittel zeigen'));
  const S = 320, pad = 40, X = p => pad + p * S, Y = r => pad + (1 - r) * S;
  const svg = sv('svg', {viewBox: `0 0 ${S + 2 * pad + 40} ${S + 2 * pad}`, style: 'max-width:440px;touch-action:none', tabindex: 0, role: 'img', class: 'plot'});
  const out = el('div', {class: 'formula'});
  root.append(ctl, el('div', {class: 'grid2'}, svg, out));
  function set(p, r) { P = Math.min(1, Math.max(.01, p)); R = Math.min(1, Math.max(.01, r)); draw(); }
  function draw() {
    svg.replaceChildren();
    svg.append(sv('rect', {x: pad, y: pad, width: S, height: S, fill: 'none', stroke: 'var(--line)'}));
    for (const F of [.2, .4, .6, .8]) {
      let d = ''; for (let k = 0; k <= 200; k++) { const p = F / 2 + (1 - F / 2) * k / 200 + 1e-6; const r = F * p / (2 * p - F); if (r <= 1.0001 && r >= 0) d += (d ? 'L' : 'M') + X(p).toFixed(1) + ',' + Y(r).toFixed(1); }
      svg.append(sv('path', {d, fill: 'none', stroke: 'var(--accent)', 'stroke-width': 1.6}));
      const lp = Math.min(1, F * 1 / (2 * 1 - F)); svg.append(sv('text', {x: X(1) + 4, y: Y(lp) + 4, 'font-size': 11, fill: 'var(--accent)'}, 'F1 = ' + String(F).replace('.', ',')));
      if (showAM) { const a = 2 * F; svg.append(sv('line', {x1: X(Math.max(0, a - 1)), y1: Y(Math.min(1, a)), x2: X(Math.min(1, a)), y2: Y(Math.max(0, a - 1)), stroke: 'var(--accent2)', 'stroke-dasharray': '5 4', 'stroke-width': 1.2})); }
    }
    svg.append(sv('line', {x1: X(0), y1: Y(0), x2: X(1), y2: Y(1), stroke: 'var(--line)', 'stroke-dasharray': '2 3'}));
    svg.append(sv('text', {x: pad + S / 2, y: S + 2 * pad - 8, 'text-anchor': 'middle', 'font-size': 12, fill: 'var(--mute)'}, 'Precision P'));
    const yl = sv('text', {x: 12, y: pad + S / 2, 'text-anchor': 'middle', 'font-size': 12, fill: 'var(--mute)', transform: `rotate(-90 12 ${pad + S / 2})`}, 'Recall R'); svg.append(yl);
    const F = 2 * P * R / (P + R), A = (P + R) / 2;
    svg.append(sv('line', {x1: X(P), y1: Y(R), x2: X(P), y2: Y(0), stroke: 'var(--mute)', 'stroke-dasharray': '2 2'}), sv('line', {x1: X(P), y1: Y(R), x2: X(0), y2: Y(R), stroke: 'var(--mute)', 'stroke-dasharray': '2 2'}));
    svg.append(sv('circle', {cx: X(P), cy: Y(R), r: 9, fill: 'var(--accent2)', stroke: 'var(--panel)', 'stroke-width': 2, style: 'cursor:grab'}));
    svg.setAttribute('aria-label', `P ${de(P, 2)}, R ${de(R, 2)}, F1 ${de(F, 3)}`);
    out.innerHTML = `<p>\\(P=${dt(P, 2)}\\) und \\(R=${dt(R, 2)}\\)</p><p>\\(F_1=\\dfrac{2PR}{P+R}=${dt(F)}\\)</p><p>\\(\\tfrac{P+R}{2}=${dt(A)}\\); Differenz \\(\\tfrac{(P-R)^2}{2(P+R)}=${dt(A - F)}\\)</p><p>Schranke \\(2\\min(P,R)=${dt(2 * Math.min(P, R))}\\)</p>`;
    tex(out);
  }
  const pick = e => { const b = svg.getBoundingClientRect(), k = (S + 2 * pad + 40) / b.width; set(((e.clientX - b.left) * k - pad) / S, 1 - ((e.clientY - b.top) * k - pad) / S); };
  let drag = false;
  svg.addEventListener('pointerdown', e => { drag = true; svg.setPointerCapture(e.pointerId); pick(e); });
  svg.addEventListener('pointermove', e => drag && pick(e)); svg.addEventListener('pointerup', () => drag = false);
  svg.addEventListener('keydown', e => { const s = .02, m = {ArrowLeft: [-s, 0], ArrowRight: [s, 0], ArrowUp: [0, s], ArrowDown: [0, -s]}[e.key]; if (m) { e.preventDefault(); set(P + m[0], R + m[1]); } });
  draw();
};

VIZ.counter = (root, opts = {}) => {
  const tok = ['First', 'Bank', 'of', 'Chicago', 'announced', 'earnings', 'of', '$200,000,000'];
  const gold = ['B-ORG', 'I-ORG', 'I-ORG', 'I-ORG', 'O', 'O', 'O', 'B-MON'];
  const presets = {s1: ['O', 'O', 'O', 'O', 'O', 'O', 'O', 'B-MON'], s2: ['O', 'B-ORG', 'I-ORG', 'I-ORG', 'O', 'O', 'O', 'B-MON'], none: Array(8).fill('O'), gold: [...gold]};
  const cycle = ['O', 'B-ORG', 'I-ORG', 'B-MON', 'I-MON'];
  let pred = [...presets[opts.preset || 's2']];
  root.append(el('h4', {}, 'Zählmaschine: dieselbe Vorhersage, zwei Zähleinheiten'),
    el('p', {class: 'cap'}, 'Klicken Sie auf ein Wort, um sein System-Label zu wechseln (O → B-ORG → I-ORG → B-MON → I-MON). Oben das Gold-Label. Die Tabellen zählen live nach den Konventionen dieses Kapitels.'));
  const ctl = el('div', {class: 'ctl'}, ...Object.entries({s1: 'System 1 (Folie)', s2: 'System 2 (Folie)', none: 'nichts vorhergesagt', gold: 'perfekt'}).map(([k, v]) => el('button', {onclick: () => { pred = [...presets[k]]; draw(); }}, v)));
  const row = el('div', {role: 'group', 'aria-label': 'Wörter mit Labels'}), tables = el('div', {class: 'grid2'});
  root.append(ctl, row, tables);
  function table(name, c) {
    const m = prf(c);
    return el('table', {}, el('tr', {}, el('th', {colspan: 2}, name)),
      el('tr', {}, el('td', {}, 'TP / FP / FN'), el('td', {}, `${c.tp} / ${c.fp} / ${c.fn}`)),
      el('tr', {}, el('td', {}, 'Precision'), el('td', {}, m.P == null ? '0/0 undefiniert' : de(m.P, 3))),
      el('tr', {}, el('td', {}, 'Recall'), el('td', {}, m.R == null ? '0/0 undefiniert' : de(m.R, 3))),
      el('tr', {}, el('td', {}, 'F1 = 2TP/(2TP+FP+FN)'), el('td', {}, m.F == null ? '0/0 (Konvention)' : de(m.F, 3))));
  }
  function draw() {
    row.replaceChildren(...tok.map((w, i) => {
      const typ = s => s === 'O' ? 'O' : s.slice(2), ok = typ(gold[i]) === typ(pred[i]);
      return el('button', {class: 'tok ' + (pred[i] === 'O' && gold[i] === 'O' ? '' : ok ? 'tp' : 'err'), 'aria-label': `${w}: Gold ${gold[i]}, System ${pred[i]}`, onclick: () => { pred[i] = cycle[(cycle.indexOf(pred[i]) + 1) % cycle.length]; draw(); }},
        el('small', {class: 'g'}, gold[i]), w, el('small', {class: 'p'}, pred[i]));
    }));
    tables.replaceChildren(table('Phrasen-Ebene (exakte Spannen)', spanCounts(gold, pred)), table('Token-Ebene (Typ je Wort)', tokenCounts(gold, pred)));
  }
  draw();
};

VIZ.micromacro = (root, opts = {}) => {
  let misc = opts.misc ?? 1;
  const base = {PER: [45, 5, 5], LOC: [30, 10, 10], ORG: [20, 15, 15]};
  root.append(el('h4', {}, 'Micro gegen Macro: was eine seltene Klasse bewirkt'),
    el('p', {class: 'cap'}, 'MISC hat 10 Gold-Entitäten und 4 falsche Vorhersagen. Verändern Sie, wie viele davon erkannt werden. Macro reagiert stark, Micro kaum.'));
  const slider = el('input', {type: 'range', min: 0, max: 10, value: misc, 'aria-label': 'erkannte MISC-Entitäten', oninput: e => { misc = +e.target.value; draw(); }});
  const lab = el('span', {});
  root.append(el('div', {class: 'ctl'}, 'MISC erkannt:', slider, lab));
  const svg = sv('svg', {viewBox: '0 0 560 200', role: 'img', class: 'plot'}); root.append(svg);
  function draw() {
    lab.textContent = `${misc} von 10`;
    const cls = {...base, MISC: [misc, 4, 10 - misc]};
    const f = Object.fromEntries(Object.entries(cls).map(([k, [tp, fp, fn]]) => [k, prf({tp, fp, fn}).F]));
    const tot = Object.values(cls).reduce((a, c) => a.map((x, i) => x + c[i]), [0, 0, 0]);
    const micro = prf({tp: tot[0], fp: tot[1], fn: tot[2]}).F, macro = Object.values(f).reduce((a, b) => a + b, 0) / 4;
    svg.replaceChildren();
    const W = 400, x0 = 70, yb = i => 14 + i * 34;
    Object.entries(f).forEach(([k, v], i) => { svg.append(sv('text', {x: 4, y: yb(i) + 15, 'font-size': 13, fill: 'var(--ink)'}, k), sv('rect', {x: x0, y: yb(i), width: W * v, height: 20, fill: k === 'MISC' ? 'var(--accent2)' : 'var(--accent)', rx: 3}), sv('text', {x: x0 + W * v + 6, y: yb(i) + 15, 'font-size': 12, fill: 'var(--mute)'}, de(v, 3))); });
    for (const [name, v, c] of [['Micro', micro, 'var(--ok)'], ['Macro', macro, 'var(--bad)']]) {
      svg.append(sv('line', {x1: x0 + W * v, y1: 6, x2: x0 + W * v, y2: 150, stroke: c, 'stroke-width': 2.5}), sv('text', {x: x0 + W * v + (name === 'Micro' ? 4 : -4), y: name === 'Micro' ? 172 : 190, 'text-anchor': name === 'Micro' ? 'start' : 'end', 'font-size': 12.5, fill: c}, `${name}-F1 ${de(v, 3)}`));
    }
    svg.setAttribute('aria-label', `Micro-F1 ${de(micro, 3)}, Macro-F1 ${de(macro, 3)}`);
  }
  draw();
};

function mountViz(scope, print) {
  let n = 0;
  scope.querySelectorAll('.viz[data-viz]').forEach(v => {
    v.dataset.n = n++; v.replaceChildren();
    if (print && v.dataset.viz === 'flow') {
      v.append(el('h4', {}, 'Abhängigkeitsbereich von \\(h_3\\) in drei Richtungen (statische Schlüsselbilder der interaktiven Grafik)'));
      for (const dir of ['forward', 'backward', 'bi']) { const d = el('div', {class: 'frame', 'data-n': n++}); v.append(d); VIZ.flow(d, {dir, t: 3}); d.querySelector('h4').remove(); d.querySelector('.cap').remove(); }
      return;
    }
    VIZ[v.dataset.viz](v, print ? {preset: 's2', P: .1, R: 1, misc: 1} : {});
  });
}

// ---------- tasks ----------
function renderTask(task, ctx = {}) {
  const box = el('div', {class: 'task', id: 'task-' + task.id});
  const tries = () => st.attempts.filter(a => a.task === task.id);
  let hintsShown = 0, revealed = false;
  box.append(el('header', {}, el('span', {class: 'stage'}, STAGE[task.stage] || ''), el('b', {}, task.id + ' · ' + task.title)));
  box.append(el('div', {html: task.prompt}));
  const expert = task.stage === 'worked' && st.attempts.some(a => a.kc === task.kc && a.first && a.correct && a.task !== task.id);
  if (task.steps) {
    const ol = el('ol', {class: 'steps'}, task.steps.map(s => el('li', {class: s.blank ? 'blank' : ''}, el('span', {html: s.s}), el('span', {class: 'why', html: s.why}))));
    if (expert && !ctx.print) box.append(el('details', {}, el('summary', {}, 'Ausgearbeitete Schritte (eingeklappt, weil Sie diese Kompetenz schon selbstständig gelöst haben)'), ol));
    else box.append(ol);
  }
  if (ctx.print) {
    box.append(el('p', {class: 'mute'}, 'Lösung: Teil „Musterlösungen“.'));
    return box;
  }
  const inputs = task.answers.map((a, i) => {
    const wrap = el('div', {class: 'ans'}), id = `${task.id}-a${i}`;
    wrap.append(el('label', {for: id, html: a.label + ':'}));
    if (a.type === 'num' || a.type === 'set') wrap.append(el('input', {type: 'text', id, inputmode: 'decimal', placeholder: a.type === 'set' ? 'z. B. 1,2,3' : 'Bruch oder Dezimalzahl', autocomplete: 'off'}));
    else if (a.type === 'choice') wrap.append(el('div', {role: 'radiogroup', id}, a.options.map((o, k) => el('label', {style: 'display:block'}, el('input', {type: 'radio', name: id, value: k}), ' ', el('span', {html: o})))));
    else wrap.append(el('textarea', {id, rows: 5, style: 'width:100%;font:inherit', placeholder: 'Ihr Beweis bzw. Ihre Begründung'}));
    return wrap;
  });
  box.append(...inputs);
  const fb = el('div', {}), hintBox = el('div', {}), sol = el('div', {class: 'sol', hidden: true, html: `<b>Musterlösung.</b> ${task.solution}` + (task.rubric ? '<p class="mute">Bewertung: ' + task.rubric.join(' · ') + '</p>' : '')});
  const bHint = el('button', {disabled: true, onclick: () => { if (hintsShown < task.hints.length) { hintBox.append(el('p', {class: 'fb', html: '💡 ' + task.hints[hintsShown++]})); tex(hintBox); } if (hintsShown >= task.hints.length) bHint.disabled = true; }}, 'Hinweis');
  const bSol = el('button', {onclick: () => { if (!tries().length && !confirm('Lösung ansehen, ohne es versucht zu haben? Die Aufgabe zählt dann als unterstützt.')) return; revealed = true; sol.hidden = false; tex(sol); if (!tries().length) record(task, false, {revealed: true, hints: hintsShown}); }}, 'Lösung anzeigen');
  const bCheck = el('button', {class: 'primary', onclick: check}, task.answers[0].type === 'self' ? 'Abgeben' : 'Prüfen');
  box.append(el('div', {class: 'ctl'}, bCheck, (task.hints || []).length ? bHint : null, bSol), fb, hintBox, sol);
  if (!(task.hints || []).length) bHint.remove();
  if ((task.hints || []).length) box.append(el('p', {class: 'mute', style: 'font-size:14px'}, 'Hinweise werden nach Ihrem ersten eigenen Versuch freigeschaltet.'));
  function check() {
    const msgs = []; let all = true;
    task.answers.forEach((a, i) => {
      const id = `${task.id}-a${i}`;
      if (a.type === 'num') { const v = $(`#${id}`, box).value; const ok = numOk(v, a); if (ok === null) { all = false; msgs.push(['bad', `${a.label}: bitte eine Zahl oder einen Bruch eingeben.`]); return; } all &&= ok; msgs.push(ok ? ['ok', `${a.label}: richtig.`] : ['bad', `${a.label}: noch nicht. ` + (diagnose(v, a) || 'Rechnen Sie die Zählungen TP, FP, FN noch einmal einzeln auf.')]); }
      else if (a.type === 'set') { const v = $(`#${id}`, box).value.split(/[,;\s]+/).filter(Boolean).map(Number).sort((x, y) => x - y); const ok = JSON.stringify(v) === JSON.stringify(a.value); all &&= ok; msgs.push(ok ? ['ok', 'richtig.'] : ['bad', 'noch nicht – welche Eingaben erreichen den Zustand über die Rekursion?']); }
      else if (a.type === 'choice') { const c = box.querySelector(`input[name="${id}"]:checked`); if (!c) { all = false; msgs.push(['bad', 'bitte eine Option wählen.']); return; } const k = +c.value, ok = (task.accept || [a.correct]).includes(k); all &&= ok; msgs.push(ok ? ['ok', 'richtig.'] : ['bad', 'noch nicht. ' + ((a.diagnoses || []).find(d => +d.value === k) || {}).msg || '']); }
      else { all = null; }
    });
    if (all === null) { sol.hidden = false; tex(sol); fb.replaceChildren(el('p', {class: 'fb'}, 'Vergleichen Sie mit der Musterlösung und bewerten Sie sich selbst:'), el('div', {class: 'ctl'}, ...[['vollständig', true], ['teilweise', false], ['nicht gelöst', false]].map(([l, ok]) => el('button', {onclick: () => { record(task, ok, {hints: hintsShown, revealed: true, self: l}); fb.append(el('p', {class: 'mute'}, 'Gespeichert (zählt als unterstützte Übung).')); }}, l)))); return; }
    record(task, all, {hints: hintsShown, revealed});
    fb.replaceChildren(...msgs.map(([c, m]) => el('p', {class: 'fb ' + c, html: m})));
    if ((task.hints || []).length && hintsShown < task.hints.length) bHint.disabled = false;
    if (all) { sol.hidden = false; introduceCards(task.kc); }
    tex(box);
  }
  return box;
}
const $ = (s, r = document) => r.querySelector(s);

// ---------- views ----------
const app = document.getElementById('app');
function topbar(cur) {
  const nav = [['home', 'Heute'], ['learn', 'Lernen'], ['review', `Wiederholen (${dueCards().length})`], ['exam', 'Prüfung'], ['progress', 'Fortschritt'], ['sources', 'Vertiefen']];
  return el('header', {class: 'top'}, el('span', {class: 'brand'}, 'Exam Mastery'), el('span', {class: 'mute'}, U.course),
    el('nav', {'aria-label': 'Hauptnavigation'}, nav.map(([k, l]) => el('button', {'aria-current': k === cur ? 'page' : false, onclick: () => go(k)}, l))));
}
function go(v, arg) { location.hash = v + (arg ? '/' + arg : ''); }
window.addEventListener('hashchange', route);

function sections() { const d = el('div', {html: U.text_html}); return [...d.querySelectorAll('section')]; }

function nextStep() {
  const due = dueCards().length;
  if (due) return {t: `${due} Karte${due > 1 ? 'n' : ''} fällig`, d: 'Kurzer Abruf zuerst: Erinnern stärkt das Behalten mehr als Wiederlesen.', a: () => go('review')};
  const open = U.tasks.find(t => !st.attempts.some(a => a.task === t.id && a.correct));
  const secs = sections();
  const unread = secs.find(s => !st.visited[s.dataset.id]);
  if (unread) return {t: `Weiter: ${unread.dataset.title}`, d: 'Theorie, Visualisierung und Aufgaben stehen direkt zusammen.', a: () => go('learn', unread.dataset.id)};
  if (open) return {t: `Aufgabe ${open.id}: ${open.title}`, d: STAGE[open.stage], a: () => go('learn', 'task-' + open.id)};
  const last = st.exams.length ? st.exams[st.exams.length - 1].ts : 0;
  return {t: 'Prüfung ohne Hilfe', d: last ? 'Für „gemeistert“ zählt nur eine Prüfung mindestens 24 h nach der letzten Übung.' : 'Neue Aufgaben, keine Hinweise, keine Lösungen bis zur Abgabe.', a: () => go('exam')};
}

function home() {
  const n = nextStep(), weak = Object.keys(KCS).filter(k => kcStatus(k)[0] === 'LUECKE');
  const m = el('main', {}, el('h1', {}, U.title), el('p', {class: 'lead mute'}, U.subtitle),
    el('div', {class: 'cards'},
      el('div', {class: 'card hero'}, el('h3', {}, 'Heute lernen'), el('p', {}, n.d), el('button', {class: 'primary', onclick: n.a}, n.t)),
      el('div', {class: 'card'}, el('h3', {}, 'Fortsetzen'), el('p', {}, st.last ? 'Zurück zur letzten Stelle.' : 'Mit der Orientierung beginnen.'), el('button', {onclick: () => go('learn', st.last || 'orientierung')}, 'Öffnen')),
      el('div', {class: 'card'}, el('h3', {}, 'Fällige Wiederholungen'), el('p', {}, `${dueCards().length} fällig · ${Object.keys(st.cards).length} von ${U.cards.length} Karten aktiv`), el('button', {onclick: () => go('review')}, 'Wiederholen')),
      el('div', {class: 'card'}, el('h3', {}, 'Schwächen'), el('p', {}, weak.length ? weak.map(k => KCS[k]).join(' · ') : 'Noch keine erkannt.'), weak.length ? el('button', {onclick: () => go('learn', Object.keys(SECTION_KC).find(s => SECTION_KC[s] === weak[0]) || 'prf')}, 'Gezielt üben') : null),
      el('div', {class: 'card'}, el('h3', {}, 'Prüfungsmodus'), el('p', {}, 'Neue Aufgaben ohne Tutor. Ergebnisse werden getrennt von der Übung gespeichert.'), el('button', {onclick: () => go('exam')}, 'Starten')),
      el('div', {class: 'card'}, el('h3', {}, 'Vertiefen'), el('p', {}, 'Lehrbuch- und Forschungsquellen mit Rolle im Kapitel.'), el('button', {onclick: () => go('sources')}, 'Quellen'))),
    el('p', {class: 'mute', style: 'font-size:14px;font-family:var(--sans)'}, `Status: ${U.status}. Fortschritt liegt nur in diesem Browser.`));
  return [topbar('home'), m];
}

function learn(anchor) {
  const toc = el('aside', {class: 'toc'}), main = el('main', {}), secs = sections();
  for (const s of secs) {
    const kc = SECTION_KC[s.dataset.id], col = kc ? {GEMEISTERT: 'var(--ok)', SOFORT_OHNE_HILFE: 'var(--accent)', LUECKE: 'var(--bad)', GEUEBT: 'var(--accent2)'}[kcStatus(kc)[0]] : null;
    toc.append(el('a', {href: '#learn/' + s.dataset.id, 'data-id': s.dataset.id}, el('span', {class: 'kc', style: col ? `background:${col}` : ''}), s.dataset.title));
    main.append(el('h2', {id: s.dataset.id}, s.dataset.title));
    s.querySelectorAll('.task-ref').forEach(r => { const t = U.tasks.find(x => x.id === r.dataset.task); r.replaceWith(renderTask(t)); });
    main.append(...s.childNodes);
  }
  const rest = U.tasks.filter(t => !U.text_html.includes(`data-task="${t.id}"`));
  if (rest.length) { toc.append(el('a', {href: '#learn/arbeitsbuch'}, 'Weitere Aufgaben')); main.append(el('h2', {id: 'arbeitsbuch'}, 'Weitere Aufgaben'), ...rest.map(t => renderTask(t))); }
  main.append(el('div', {class: 'card hero', style: 'margin-top:30px'}, el('h3', {}, 'Abschluss'), el('p', {}, 'Wenn alle Aufgaben gelöst sind: Prüfung ohne Hilfe – heute für den Sofort-Check, nach mindestens 24 h für „gemeistert“.'), el('button', {class: 'primary', onclick: () => go('exam')}, 'Zur Prüfung')));
  mountViz(main, false);
  setTimeout(() => {
    const target = anchor && document.getElementById(anchor); if (target) target.scrollIntoView();
    const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { const id = e.target.id; st.visited[id] = 1; st.last = id; if (SECTION_KC[id]) introduceCards(SECTION_KC[id]); save(); toc.querySelectorAll('a').forEach(a => a.classList.toggle('cur', a.dataset.id === id)); } }), {rootMargin: '0px 0px -70% 0px'});
    main.querySelectorAll('h2[id]').forEach(h => io.observe(h));
  });
  tex(main);
  return [topbar('learn'), el('div', {class: 'layout'}, toc, main)];
}

function review() {
  const q = dueCards(), m = el('main', {}, el('h1', {}, 'Wiederholen'));
  if (!q.length) { m.append(el('p', {}, Object.keys(st.cards).length ? 'Nichts fällig. Nächste Karte: ' + new Date(Math.min(...Object.values(st.cards).map(c => c.due))).toLocaleString('de-DE') : 'Karten werden aktiv, sobald Sie den zugehörigen Abschnitt lesen.')); }
  else {
    const c = q[0], card = el('div', {class: 'flash'}, el('p', {class: 'pill'}, KCS[c.kc] || c.kc), el('p', {html: c.front}));
    const back = el('div', {hidden: true}, el('hr'), el('p', {html: c.back}), el('div', {class: 'ctl'},
      el('button', {onclick: () => grade(false)}, 'Nicht gewusst'), el('button', {class: 'primary', onclick: () => grade(true)}, 'Gewusst')));
    card.append(el('button', {onclick: e => { back.hidden = false; e.target.remove(); tex(back); }}, 'Antwort zeigen'), back);
    m.append(el('p', {class: 'mute'}, `${q.length} fällig. Erst selbst antworten, dann aufdecken.`), card);
    function grade(ok) { const s = st.cards[c.key]; s.box = ok ? Math.min(BOX.length - 1, s.box + 1) : 0; s.due = now() + BOX[s.box] * DAY + (ok ? 0 : 10 * 60e3); save(); route(); }
  }
  m.append(el('p', {class: 'mute', style: 'font-size:14px'}, 'Abstände: ' + BOX.join(' / ') + ' Tage (Leitner-Kästen; transparent, keine Optimalitätsgarantie). Export für Anki: anki_import.txt mit stabilen GUIDs.'));
  tex(m); return [topbar('review'), m];
}

function exam() {
  const m = el('main', {}, el('h1', {}, 'Prüfung ohne Hilfe'));
  const kcs = [...new Set(U.exam.map(x => x.kc))];
  const delayedFor = kc => now() - lastAssisted(kc) >= DAY && lastAssisted(kc) > 0;
  m.append(el('p', {}, 'Keine Hinweise, keine Lösungen bis zur Abgabe, neue Aufgaben. Geben Sie zu jeder Antwort an, wie sicher Sie sind.'),
    el('p', {class: 'mute'}, 'Verzögert (zählt für „gemeistert“): ' + kcs.map(k => `${KCS[k]}: ${delayedFor(k) ? 'ja' : 'nein'}`).join(' · ')));
  const items = U.exam.map(x => {
    const t = renderTask({...x, stage: '', hints: [], title: KCS[x.kc]}, {}); t.querySelectorAll('.ctl, .sol, p.mute').forEach(n => n.remove());
    const conf = el('select', {'aria-label': 'Sicherheit'}, ['50', '70', '90', '100'].map(v => el('option', {value: v}, v + ' %')));
    t.append(el('div', {class: 'ans'}, 'Sicherheit:', conf)); t._conf = conf; return t;
  });
  m.append(...items, el('button', {class: 'primary', onclick: submit}, 'Abgeben'));
  function submit() {
    const res = U.exam.map((x, i) => {
      const box = items[i]; let ok = true;
      x.answers.forEach((a, k) => { const id = `${x.id}-a${k}`;
        if (a.type === 'num') ok &&= !!numOk($(`#${id}`, box).value, a);
        else if (a.type === 'set') ok &&= JSON.stringify($(`#${id}`, box).value.split(/[,;\s]+/).filter(Boolean).map(Number).sort((p, q) => p - q)) === JSON.stringify(a.value);
        else if (a.type === 'choice') { const c = box.querySelector(`input[name="${id}"]:checked`); ok &&= !!c && +c.value === a.correct; } });
      return {id: x.id, kc: x.kc, correct: ok, conf: +box._conf.value, delayed: delayedFor(x.kc)};
    });
    st.exams.push({ts: now(), items: res});
    for (const r of res) if (!r.correct) for (const c of U.cards) if (c.kc === r.kc) st.cards[c.key] = {box: 0, due: now()};
    save();
    const acc = res.filter(r => r.correct).length / res.length, conf = res.reduce((a, r) => a + r.conf, 0) / res.length / 100;
    m.replaceChildren(el('h1', {}, 'Auswertung'), el('p', {class: 'lead'}, `${res.filter(r => r.correct).length} von ${res.length} richtig.`),
      el('p', {}, `Kalibrierung: mittlere Sicherheit ${Math.round(conf * 100)} % gegenüber ${Math.round(acc * 100)} % richtig` + (conf - acc > .15 ? ' – Sie überschätzen sich.' : acc - conf > .15 ? ' – Sie unterschätzen sich.' : ' – gut kalibriert.')),
      ...U.exam.map((x, i) => el('div', {class: 'task'}, el('header', {}, el('b', {}, `${x.id} ${res[i].correct ? '✓' : '✗'}`), el('span', {class: 'mute'}, KCS[x.kc] + ` · Sicherheit ${res[i].conf} %`)), el('div', {html: x.prompt}), el('div', {class: 'sol', html: '<b>Lösung.</b> ' + x.solution}))),
      el('p', {}, res.some(r => !r.correct) ? 'Die Karten der fehlerhaften Kompetenzen sind jetzt fällig.' : 'Alle richtig. Wiederholen Sie die Prüfung frühestens in 24 h ohne zwischenzeitliche Übung, um „gemeistert“ zu belegen.'),
      el('button', {class: 'primary', onclick: () => go('home')}, 'Zur Tagesansicht'));
    tex(m); scrollTo(0, 0);
  }
  tex(m); return [topbar('exam'), m];
}

function progress() {
  const s = series(), m = el('main', {}, el('h1', {}, 'Fortschritt'));
  const rate = arr => arr.length ? `${arr.filter(a => a.correct).length}/${arr.length} richtig` : 'keine Daten';
  m.append(el('div', {class: 'meter'}, el('span', {}, 'Übung mit Unterstützung: ' + rate(s.assisted)), el('span', {}, 'Sofort ohne Hilfe: ' + rate(s.immediate)), el('span', {}, 'Verzögert ohne Hilfe: ' + rate(s.delayed)), el('span', {}, 'Transfer, erster Versuch ohne Hinweis: ' + rate(s.transfer))),
    el('p', {class: 'mute'}, 'Die vier Reihen werden getrennt gespeichert. „Gemeistert“ entsteht nur aus der verzögerten Prüfung ohne Hilfe, nie aus Übungsleistung.'),
    el('table', {}, el('tr', {}, el('th', {}, 'Kompetenz'), el('th', {}, 'Status'), el('th', {}, 'Begründung')), Object.entries(KCS).map(([k, l]) => { const [a, b] = kcStatus(k); return el('tr', {}, el('td', {}, l), el('td', {}, a), el('td', {}, b)); })),
    el('div', {class: 'ctl'}, el('button', {onclick: () => { const b = new Blob([JSON.stringify(st, null, 1)], {type: 'application/json'}); const a = el('a', {href: URL.createObjectURL(b), download: `lernstand-${U.id}.json`}); a.click(); }}, 'Lernstand exportieren'),
      el('label', {class: 'btn'}, 'Importieren', el('input', {type: 'file', accept: 'application/json', class: 'sr', onchange: async e => { try { st = Object.assign(blank(), JSON.parse(await e.target.files[0].text())); save(); route(); } catch (err) { alert('Datei nicht lesbar.'); } }}))));
  return [topbar('progress'), m];
}

function sources() {
  const m = el('main', {}, el('h1', {}, 'Vertiefen und Quellen'), el('p', {}, 'Jede Quelle ist mit ihrer Rolle gekennzeichnet. Kursunterlagen bestimmen Umfang und Prüfungsbezug, Lehrbücher Definitionen und Herleitungen, Forschungsarbeiten Vertiefung; Preprints und Blogbeiträge sind als solche markiert.'));
  m.append(el('ol', {}, U.sources.map(s => el('li', {}, el('span', {class: 'prov', 'data-kind': s.kind}), ' ', s.ref, ' ', s.doi ? el('a', {href: 'https://doi.org/' + s.doi}, 'doi:' + s.doi) : s.url ? el('a', {href: s.url}, s.url) : null))));
  return [topbar('sources'), m];
}

function route() {
  const [v, arg] = (location.hash.slice(1) || 'home').split('/');
  const view = {home, learn, review, exam, progress, sources}[v] || home;
  app.replaceChildren(...view(arg)); if (v !== 'learn') tex(app);
}

// ---------- print book ----------
function book() {
  const m = el('main', {}, el('h1', {}, U.title), el('p', {class: 'lead'}, U.subtitle), el('p', {class: 'mute'}, 'Lehrbuch · Arbeitsbuch · Musterlösungen · Probeprüfung. ' + U.status));
  for (const s of sections()) {
    m.append(el('h2', {}, s.dataset.title));
    s.querySelectorAll('.task-ref').forEach(r => r.replaceWith(renderTask(U.tasks.find(x => x.id === r.dataset.task), {print: true})));
    m.append(...s.childNodes);
  }
  const rest = U.tasks.filter(t => !U.text_html.includes(`data-task="${t.id}"`));
  if (rest.length) m.append(el('h2', {}, 'Weitere Aufgaben'), ...rest.map(t => renderTask(t, {print: true})));
  m.append(el('h2', {}, 'Musterlösungen'), ...U.tasks.map(t => el('div', {class: 'task'}, el('b', {}, `${t.id} · ${t.title}`), el('div', {html: t.solution}), t.rubric ? el('p', {class: 'mute', html: 'Bewertung: ' + t.rubric.join(' · ')}) : null)));
  m.append(el('h2', {}, 'Probeprüfung (ohne Hilfsmittel)'), ...U.exam.map(x => el('div', {class: 'task'}, el('b', {}, x.id), el('div', {html: x.prompt}))));
  m.append(el('h2', {}, 'Lösungen der Probeprüfung'), ...U.exam.map(x => el('div', {class: 'task'}, el('b', {}, x.id), el('div', {html: x.solution}))));
  m.append(el('h2', {}, 'Literatur'), el('ol', {}, U.sources.map(s => el('li', {}, s.ref, s.doi ? ' doi:' + s.doi : s.url ? ' ' + s.url : ''))));
  app.replaceChildren(m); mountViz(m, true);
  const done = () => { document.body.dataset.ready = '1'; };
  const wait = () => window.MathJax && MathJax.typesetPromise ? MathJax.typesetPromise([m]).then(done, done) : setTimeout(wait, 50);
  wait();
}

if (MODE === 'print') book(); else { route(); const ready = () => { document.body.dataset.ready = '1'; }; (function w() { if (window.MathJax && MathJax.typesetPromise) MathJax.startup.promise.then(() => tex(app)).then(ready); else setTimeout(w, 50); })(); }
})();
