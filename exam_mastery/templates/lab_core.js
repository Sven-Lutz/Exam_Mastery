/* Exam Mastery – Interaktives Labor (Darstellung). Rechnet nichts selbst: alle Größen kommen aus LabMath. */
'use strict';
const M = window.LabMath || {};
const REGISTERED_LABS = [];
function registerLab(lab) { REGISTERED_LABS.push(lab); return lab; }
const UNIT = JSON.parse(document.getElementById('unit-data').textContent);
const LAB = UNIT.lab || {};
const $ = (s, r = document) => r.querySelector(s);
function h(tag, attrs = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === false || v == null) continue;
    if (k.startsWith('on')) n.addEventListener(k.slice(2), v); else if (k === 'html') n.innerHTML = v; else n.setAttribute(k, v === true ? '' : v);
  }
  for (const c of kids.flat(9)) if (c != null && c !== false) n.append(c.nodeType ? c : document.createTextNode(String(c)));
  return n;
}
const SVGNS = 'http://www.w3.org/2000/svg';
function s(tag, attrs = {}, ...kids) { const n = document.createElementNS(SVGNS, tag); for (const [k, v] of Object.entries(attrs)) if (v != null && v !== false) n.setAttribute(k, v); kids.flat(9).forEach(c => c != null && n.append(c.nodeType ? c : document.createTextNode(String(c)))); return n; }
/** Zahlformat deutsch, echtes Minuszeichen; null = undefiniert */
function f(x, d = 2) {
  if (x === null || x === undefined || Number.isNaN(x)) return 'undef.';
  if (x === -Infinity) return '−∞'; if (x === Infinity) return '∞';
  const r = Math.abs(x) < 0.5 * Math.pow(10, -d) ? 0 : x;
  return r.toFixed(d).replace('.', ',').replace('-', '−');
}
const parse = t => { const v = parseFloat(String(t).replace(',', '.').replace('−', '-')); return Number.isFinite(v) ? v : null; };
const clone = o => JSON.parse(JSON.stringify(o));
const sub = ['₀', '₁', '₂', '₃', '₄', '₅', '₆', '₇', '₈', '₉'];
const reduced = () => document.body.classList.contains('reduced') || matchMedia('(prefers-reduced-motion: reduce)').matches;
function toast(msg) { const t = h('div', {class: 'toast', role: 'status'}, msg); document.body.append(t); setTimeout(() => t.remove(), 2200); }
const store = {get(k, d) { try { const v = localStorage.getItem('emlab:' + k); return v ? JSON.parse(v) : d; } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem('emlab:' + k, JSON.stringify(v)); } catch (e) { /* ohne Speicher weiter */ } }};
/** Verweise ins Lehrbuch / Aufgaben / Karten (Produktverknüpfung) */
function links(ref) {
  if (!ref) return document.createDocumentFragment();
  const parts = [];
  if (ref.book) { const sec = ((UNIT.kc_map || {})[ref.book] || {sections: [ref.book]}).sections[0], lbl = 'Lehrbuch ' + (ref.bookLabel || (UNIT.kc_labels || {})[ref.book] || ref.book);
    parts.push(UNIT.book_href === null ? h('span', {}, lbl) : h('a', {href: (UNIT.book_href || 'index.html#learn/{sec}').replace('{sec}', sec)}, lbl)); }
  (ref.tasks || []).forEach(t => parts.push(h('a', {href: `index.html#learn/task-${t}`}, 'Aufgabe ' + t)));
  (ref.cards || []).forEach(c => parts.push(h('span', {}, 'Karte „' + c + '“')));
  if (!parts.length) return document.createDocumentFragment();   // nie „null“ in den DOM schreiben
  return h('div', {class: 'links'}, 'Weiter: ', ...parts.flatMap((p, i) => i ? [' · ', p] : [p]));
}

// ---------- generische Interpolation: jedes Zwischenbild ist ein gültiger Zustand ----------
function lerpState(a, b, u) {
  if (typeof a === 'number' && typeof b === 'number' && Number.isFinite(a) && Number.isFinite(b)) return a + (b - a) * u;
  if (Array.isArray(a) && Array.isArray(b) && a.length === b.length) return a.map((x, i) => lerpState(x, b[i], u));
  if (a && b && typeof a === 'object' && typeof b === 'object' && !Array.isArray(a)) { const o = {}; for (const k of Object.keys(b)) o[k] = k in a ? lerpState(a[k], b[k], u) : b[k]; return o; }
  return u < 1 ? a : b;
}

// ---------- 2D-Ebene mit ziehbaren Pfeilen (Maus, Touch, Tastatur) ----------
function Plane({title, xr = [-2.5, 2.5], yr = [-2, 2], w = 420, axes = ['x₁', 'x₂']}) {
  const hgt = Math.round(w * (yr[1] - yr[0]) / (xr[1] - xr[0]));
  const X = x => (x - xr[0]) / (xr[1] - xr[0]) * w, Y = y => hgt - (y - yr[0]) / (yr[1] - yr[0]) * hgt;
  const inv = (px, py) => [xr[0] + px / w * (xr[1] - xr[0]), yr[0] + (hgt - py) / hgt * (yr[1] - yr[0])];
  const grid = s('g', {});
  for (let x = Math.ceil(xr[0]); x <= xr[1]; x++) grid.append(s('line', {class: x ? 'gl' : 'ax', x1: X(x), x2: X(x), y1: 0, y2: hgt}));
  for (let y = Math.ceil(yr[0]); y <= yr[1]; y++) grid.append(s('line', {class: y ? 'gl' : 'ax', y1: Y(y), y2: Y(y), x1: 0, x2: w}));
  grid.append(s('text', {x: w - 6, y: hgt - 8, 'text-anchor': 'end', class: 'lbl', fill: 'var(--mute)', 'font-size': 11}, axes[0] + ' →'), s('text', {x: 8, y: 16, class: 'lbl', fill: 'var(--mute)', 'font-size': 11}, '↑ ' + axes[1]));
  const content = s('g', {}), handles = s('g', {});
  const svg = s('svg', {viewBox: `0 0 ${w} ${hgt}`, role: 'group', 'aria-label': title}, grid, content, handles);
  const root = h('div', {class: 'plane'}, h('h3', {}, title), svg);
  const H = {};
  function arrow(from, to, color, width = 2.5, cls = '', dash) {
    const x1 = X(from[0]), y1 = Y(from[1]), x2 = X(to[0]), y2 = Y(to[1]), L = Math.hypot(x2 - x1, y2 - y1);
    const g = s('g', {class: cls});
    if (L < 1) return g;
    const ux = (x2 - x1) / L, uy = (y2 - y1) / L, a = Math.min(11, L * .45), bx = x2 - ux * a, by = y2 - uy * a;
    g.append(s('line', {x1, y1, x2: bx, y2: by, stroke: color, 'stroke-width': width, 'stroke-dasharray': dash || null, 'stroke-linecap': 'round'}),
      s('polygon', {points: `${x2},${y2} ${bx - uy * a * .45},${by + ux * a * .45} ${bx + uy * a * .45},${by - ux * a * .45}`, fill: color}));
    return g;
  }
  /** Ziehbarer Punkt; get() liefert Koordinaten, set(v) übernimmt neue */
  function handle(id, {get, set, color, label, aria}) {
    let g = H[id];
    if (!g) {
      g = s('g', {class: 'handle', tabindex: 0, role: 'slider', 'data-id': id},
        s('circle', {class: 'hit', r: 16}), s('circle', {class: 'ring', r: 9}), s('circle', {class: 'dot', r: 5.5}), s('text', {class: 'lbl', x: 9, y: -9}));
      H[id] = g; handles.append(g);
      const snap = v => Math.round(v * 20) / 20;
      g.addEventListener('pointerdown', e => { e.preventDefault(); g.setPointerCapture(e.pointerId); g.classList.add('drag'); g.focus({preventScroll: true}); });
      g.addEventListener('pointermove', e => { if (!g.hasPointerCapture(e.pointerId)) return; const r = svg.getBoundingClientRect(); const p = inv((e.clientX - r.left) / r.width * w, (e.clientY - r.top) / r.height * hgt); g._set([snap(Math.max(xr[0], Math.min(xr[1], p[0]))), snap(Math.max(yr[0], Math.min(yr[1], p[1])))]); });
      g.addEventListener('pointerup', e => { g.classList.remove('drag'); g.releasePointerCapture(e.pointerId); });
      g.addEventListener('keydown', e => {
        const st = e.shiftKey ? .5 : .1, d = {ArrowLeft: [-st, 0], ArrowRight: [st, 0], ArrowUp: [0, st], ArrowDown: [0, -st]}[e.key];
        if (!d) return; e.preventDefault(); const v = g._get(); g._set([Math.round((v[0] + d[0]) * 100) / 100, Math.round((v[1] + d[1]) * 100) / 100]);
      });
    }
    g._get = get; g._set = set;
    const v = get();
    g.setAttribute('transform', `translate(${X(v[0])},${Y(v[1])})`);
    g.querySelector('.dot').setAttribute('fill', color); g.querySelector('.lbl').setAttribute('fill', color); g.querySelector('.lbl').textContent = label;
    g.setAttribute('aria-label', `${aria} = (${f(v[0])}; ${f(v[1])}). Pfeiltasten verschieben um 0,1, mit Umschalt um 0,5.`);
    g.setAttribute('aria-valuetext', `(${f(v[0])}; ${f(v[1])})`);
    g.style.display = '';
    return g;
  }
  function only(ids) { Object.keys(H).forEach(k => { if (!ids.includes(k)) H[k].style.display = 'none'; }); }
  return {root, svg, content, X, Y, inv, arrow, handle, only, w, h: hgt};
}

function numInput(val, onset, aria) {
  const i = h('input', {class: 'num', type: 'text', inputmode: 'decimal', value: f(val), 'aria-label': aria});
  i.addEventListener('change', () => { const v = parse(i.value); if (v === null) { i.value = 'Zahl?'; return; } onset(v); });
  return i;
}
function seg(options, cur, on, label) {
  return h('div', {class: 'seg', role: 'group', 'aria-label': label}, options.map(([k, l]) => h('button', {'aria-pressed': String(k === cur), onclick: () => on(k)}, l)));
}
function meter(label, val, frac, title) {
  return h('div', {class: 'm', title: title || ''}, h('span', {}, label), h('b', {}, val), frac == null ? null : h('div', {class: 'meter-bar'}, h('i', {style: `width:${Math.max(0, Math.min(1, frac)) * 100}%`})));
}

// =====================================================================================
// Shell: Bühne (freies Experiment, immer sichtbar) + Seitenleiste (Entdecken / Challenges / Hypothese)
// =====================================================================================
function Shell(lab) {
  const saved = (() => { const m = location.hash.match(/s=([^&]+)/); if (m && location.hash.includes('lab=' + lab.id)) { try { return JSON.parse(decodeURIComponent(escape(atob(m[1])))); } catch (e) { /* ungültiger Link */ } } return null; })();
  let S = saved || lab.init();
  let R = lab.compute(S);
  const progress = store.get(lab.id, {steps: {}, chal: {}, preds: {}, hints: {}, log: []});
  const stage = h('div', {class: 'lab-stage'}), side = h('div', {class: 'side'});
  const ziel = (location.hash.match(/ziel=([\w-]+)/) || [])[1];
  let panel = ziel && lab.challenges.some(c => c.id === ziel) ? 'chal' : 'path', anim = null, hyp = null;
  const api = {
    get S() { return S; }, get R() { return R; },
    set(patch, opts = {}) {
      const next = typeof patch === 'function' ? patch(clone(S)) : Object.assign(clone(S), patch);
      if (opts.animate && !reduced()) return animate(next);
      const structural = lab.structural ? lab.structural(S, next) : false;
      S = next; refresh(structural);
    },
    reset() { animate(lab.init()); },
    rerender() { stage.replaceChildren(); view = lab.view(stage, api); refresh(); },
  };
  function animate(target) {
    cancelAnimationFrame(anim); const from = clone(S), t0 = performance.now(), dur = 650;
    const structural = JSON.stringify(Object.keys(from)) !== JSON.stringify(Object.keys(target)) || lab.structural?.(from, target);
    if (structural || reduced()) { S = target; refresh(true); return; }
    const step = now => { const u = Math.min(1, (now - t0) / dur), e = u < .5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2; S = lerpState(from, target, e); refresh(); if (u < 1) anim = requestAnimationFrame(step); else { S = target; refresh(); } };
    anim = requestAnimationFrame(step);
  }
  let view = lab.view(stage, api);
  function refresh(rebuild) {
    if (rebuild && lab.structural) { stage.replaceChildren(); view = lab.view(stage, api); }
    R = lab.compute(S);
    view(S, R);
    updateSide();
    const enc = btoa(unescape(encodeURIComponent(JSON.stringify(S))));
    history.replaceState(null, '', `#lab=${lab.id}&s=${enc}`);
  }
  // ----- Seitenleiste -----
  const tabs = h('div', {class: 'tabs', role: 'tablist'}), body = h('div', {});
  const TABS = [['path', 'Entdecken'], ['chal', 'Challenges'], ['hyp', 'Hypothese']];
  function drawTabs() { tabs.replaceChildren(...TABS.map(([k, l]) => h('button', {role: 'tab', 'aria-selected': String(panel === k), onclick: () => { panel = k; drawTabs(); drawPanel(); }}, l))); }
  side.append(tabs, body);
  const live = [];  // Elemente, die bei jeder Änderung aktualisiert werden
  function drawPanel() {
    live.length = 0; body.replaceChildren();
    if (panel === 'path') drawPath(); else if (panel === 'chal') drawChallenges(); else drawHyp();
    updateSide();
  }
  function save() { store.set(lab.id, progress); }
  function drawPath() {
    body.append(h('p', {class: 'note'}, 'Geführter Weg: Jede Station stellt eine Frage, lässt Sie zuerst vorhersagen und dann am Modell selbst handeln. Die Bühne links bleibt jederzeit frei bedienbar.'));
    lab.path.forEach((st, i) => {
      const done = !!progress.steps[st.id], box = h('div', {class: 'step' + (done ? ' done' : ''), 'data-id': st.id});
      const goalEl = h('div', {class: 'goal-state no'});
      const rev = h('div', {});
      const showReveal = () => { rev.replaceChildren(h('div', {class: 'reveal', html: st.reveal}), links(st.links)); typeset(rev); };
      box.append(h('h4', {}, `${i + 1}. ${st.title}`), h('div', {class: 'story', html: st.story}));
      if (st.setup) box.append(h('button', {onclick: () => { api.set(st.setup(clone(S)), {animate: true}); }}, 'Ausgangslage herstellen'));
      if (st.predict) {
        const pr = progress.preds[st.id];
        const opts = h('div', {class: 'pred-opts'}), fb = h('div', {});
        const paint = () => { opts.querySelectorAll('button').forEach((b, k) => { b.className = progress.preds[st.id] === undefined ? '' : (k === st.predict.correct ? 'sel-ok' : (k === progress.preds[st.id] ? 'sel-bad' : '')); }); };
        st.predict.options.forEach((o, k) => opts.append(h('button', {html: o, onclick: () => { if (progress.preds[st.id] !== undefined) return; progress.preds[st.id] = k; save(); paint(); fb.replaceChildren(h('p', {class: 'note', html: (k === st.predict.correct ? '<b>Treffer.</b> ' : '<b>Noch nicht.</b> ') + 'Prüfen Sie es jetzt selbst – die Begründung folgt nach dem Experiment.'})); }})));
        box.append(h('div', {class: 'todo'}, h('b', {}, 'Vorhersage: '), h('span', {html: st.predict.q}), opts, fb));
        if (pr !== undefined) setTimeout(paint);
      }
      box.append(h('div', {class: 'todo', html: '<b>Experiment:</b> ' + st.task}), goalEl, rev);
      live.push(() => {
        const ok = st.goal(S, R);
        goalEl.className = 'goal-state ' + (ok || done ? 'ok' : 'no');
        goalEl.textContent = ok ? '✓ Ziel erreicht' : (progress.steps[st.id] ? '✓ früher erreicht' : '○ Ziel noch nicht erreicht');
        if (ok && !progress.steps[st.id]) {
          if (st.predict && progress.preds[st.id] === undefined) { goalEl.textContent = '✓ Ziel erreicht – geben Sie oben noch Ihre Vorhersage ab, dann folgt die Erklärung.'; return; }
          progress.steps[st.id] = Date.now(); save(); box.classList.add('done'); showReveal();
        }
      });
      if (done) showReveal();
      body.append(box);
    });
  }
  function drawChallenges() {
    body.append(h('p', {class: 'note'}, 'Challenges haben ein überprüfbares Ziel. Hinweise kommen gestuft; die fachliche Rückmeldung erklärt, warum Ihre Lösung funktioniert – oder warum ein Ziel unerreichbar ist.'));
    lab.challenges.forEach(c => {
      const box = h('div', {class: 'chal' + (progress.chal[c.id] ? ' solved' : ''), 'data-id': c.id});
      const bar = h('i', {style: 'width:0'}), msg = h('div', {class: 'note'}), out = h('div', {}), hints = h('div', {});
      const nh = () => progress.hints[c.id] || 0;
      const drawHints = () => hints.replaceChildren(...c.hints.slice(0, nh()).map((t, k) => h('div', {class: 'hint', html: `<b>Hinweis ${k + 1}:</b> ${t}`})));
      const win = () => { out.replaceChildren(h('div', {class: 'reveal', html: c.success}), links(c.links)); typeset(out); };
      box.append(h('h4', {}, h('span', {}, c.title), h('span', {class: 'badge' + (progress.chal[c.id] ? ' ok' : '')}, progress.chal[c.id] ? 'gelöst' : c.level || '')),
        h('p', {html: c.goal}), c.constraint ? h('p', {class: 'note', html: 'Bedingung: ' + c.constraint}) : document.createDocumentFragment(),
        h('div', {class: 'row'}, h('button', {onclick: () => { api.set(c.setup(clone(S)), {animate: true}); }}, 'Starten'),
          h('button', {onclick: () => { if (nh() < c.hints.length) { progress.hints[c.id] = nh() + 1; save(); drawHints(); typeset(hints); } }}, 'Hinweis'),
          c.impossible ? h('button', {onclick: () => impossible(c, out, box)}, 'Ich halte das für unmöglich') : null),
        h('div', {class: 'prog'}, bar), msg, hints, out);
      drawHints();
      if (progress.chal[c.id]) win();
      live.push(() => {
        const r = c.check(S, R);
        bar.style.width = Math.round(Math.max(0, Math.min(1, r.progress || 0)) * 100) + '%';
        msg.innerHTML = r.msg || '';
        if (r.done && !progress.chal[c.id]) { progress.chal[c.id] = Date.now(); save(); box.classList.add('solved'); box.querySelector('.badge').className = 'badge ok'; box.querySelector('.badge').textContent = 'gelöst'; win(); }
      });
      body.append(box);
    });
  }
  function impossible(c, out, box) {
    const q = c.impossible;
    const opts = h('div', {class: 'pred-opts'});
    q.options.forEach((o, k) => opts.append(h('button', {html: o, onclick: () => {
      opts.querySelectorAll('button').forEach((b, j) => b.className = j === q.correct ? 'sel-ok' : (j === k ? 'sel-bad' : ''));
      if (q.applies(S, R) && k === q.correct) { progress.chal[c.id] = Date.now(); save(); box.classList.add('solved'); out.append(h('div', {class: 'reveal', html: c.success}), links(c.links)); typeset(out); }
      else if (!q.applies(S, R)) out.append(h('div', {class: 'verdict bad', html: q.notApplicable}));
      else out.append(h('div', {class: 'verdict bad', html: q.why[k] || 'Diese Begründung trägt nicht.'}));
    }})));
    out.replaceChildren(h('div', {class: 'todo'}, h('b', {}, 'Begründen Sie: '), q.q, opts));
    typeset(out);
  }
  function drawHyp() {
    const qs = lab.quantities(S, R);
    const sel = h('select', {'aria-label': 'Größe'}, qs.map(q => h('option', {value: q.id}, q.label)));
    const dir = h('select', {'aria-label': 'Vorhersage'}, [['up', 'steigt'], ['down', 'sinkt'], ['same', 'bleibt gleich']].map(([v, l]) => h('option', {value: v}, l)));
    const why = h('textarea', {placeholder: 'Meine Begründung (z. B. „weil q·k₂ wächst, während die anderen Scores gleich bleiben …“)', 'aria-label': 'Begründung'});
    const out = h('div', {}), state = h('p', {class: 'note'});
    const fix = h('button', {class: 'primary', onclick: () => { hyp = {S: clone(S), R: lab.compute(clone(S)), q: sel.value, dir: dir.value, why: why.value.trim(), ts: Date.now()}; state.innerHTML = '<b>Festgehalten.</b> Verändern Sie jetzt das Modell auf der Bühne und drücken Sie dann „Prüfen“.'; }}, 'Hypothese festhalten');
    const chk = h('button', {onclick: () => {
      if (!hyp) { state.textContent = 'Erst eine Hypothese festhalten.'; return; }
      const qb = lab.quantities(hyp.S, hyp.R).find(x => x.id === hyp.q), qa = lab.quantities(S, R).find(x => x.id === hyp.q);
      if (!qb || !qa) { out.replaceChildren(h('div', {class: 'verdict bad'}, 'Die Größe existiert im neuen Zustand nicht mehr (Struktur geändert).')); return; }
      const d = qa.value - qb.value, tol = 1e-6 * Math.max(1, Math.abs(qb.value)), obs = Math.abs(d) <= tol ? 'same' : d > 0 ? 'up' : 'down';
      const word = {up: 'steigt', down: 'sinkt', same: 'bleibt gleich'};
      const ok = obs === hyp.dir;
      const rows = lab.quantities(hyp.S, hyp.R).map(x => { const y = lab.quantities(S, R).find(z => z.id === x.id); if (!y) return null; const dd = y.value - x.value;
        return h('tr', {}, h('td', {}, x.label), h('td', {}, f(x.value, 3)), h('td', {}, f(y.value, 3)), h('td', {class: dd > 1e-9 ? 'up' : dd < -1e-9 ? 'down' : ''}, (dd > 0 ? '+' : '') + f(dd, 3))); });
      out.replaceChildren(h('div', {class: 'verdict ' + (ok ? 'ok' : 'bad'), html: `<b>${ok ? 'Bestätigt' : 'Widerlegt'}:</b> ${qa.label} ${word[obs]} (${f(qb.value, 3)} → ${f(qa.value, 3)}); vorhergesagt: ${word[hyp.dir]}.`}),
        h('div', {class: 'reveal', html: '<b>Ursache.</b> ' + lab.explain(hyp.S, hyp.R, S, R)}),
        h('table', {class: 'diff'}, h('tr', {}, h('th', {}, 'Größe'), h('th', {}, 'vorher'), h('th', {}, 'nachher'), h('th', {}, 'Δ')), rows));
      progress.log.unshift({lab: lab.id, q: hyp.q, dir: hyp.dir, obs, why: hyp.why, ts: Date.now()}); progress.log = progress.log.slice(0, 30); save();
      typeset(out);
    }}, 'Prüfen');
    body.append(h('div', {class: 'hyp'}, h('p', {class: 'note'}, 'Formulieren Sie eine Vermutung, halten Sie den Zustand fest, verändern Sie das Modell und lassen Sie die Vermutung prüfen. Die Rückmeldung zerlegt die Änderung in ihre mathematischen Ursachen.'),
      h('div', {class: 'row'}, 'Wenn ich das Modell verändere, ', sel, dir), why, h('div', {class: 'row'}, fix, chk), state, out,
      progress.log.length ? h('details', {}, h('summary', {}, `Protokoll (${progress.log.length})`), h('ul', {class: 'note'}, progress.log.map(l => h('li', {}, `${new Date(l.ts).toLocaleString('de-DE')}: ${l.q} – vorhergesagt ${l.dir}, beobachtet ${l.obs}${l.why ? ' – „' + l.why + '“' : ''}`)))) : null));
  }
  function updateSide() { live.forEach(fn => fn()); }
  drawTabs(); drawPanel(); refresh();
  if (ziel) setTimeout(() => { const n = side.querySelector(`[data-id="${ziel}"]`); if (n) { n.scrollIntoView({block: 'center'}); n.classList.add('target'); } }, 50);
  return {stage, side, api};
}
function typeset(node) {
  const go = () => { if (!node.isConnected) return setTimeout(go, 30); if (window.MathJax && MathJax.typesetPromise) MathJax.typesetPromise([node]).catch(() => {}); else setTimeout(go, 100); };
  setTimeout(go, 0);
}

