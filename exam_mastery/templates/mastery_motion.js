/* Mastery Motion runtime (offline, no dependencies). Mirror of exam_mastery/motion (Python reference); tests compare
   states and display lists at every keyframe. Core functions are pure (node-testable); mount() builds the scene UI:
   step + scrubbable timeline first, play second; predictions lock the reveal; events go to localStorage em-motion-v1.
   Requires policy_gradient_math.js (EMPolicyGradient) for the softmax policy-gradient model. */
var MasteryMotion = (function () {
'use strict';
const PG = () => (typeof EMPolicyGradient !== 'undefined' ? EMPolicyGradient
  : (typeof require === 'function' ? require('./policy_gradient_math.js') : null));
const SQ3 = Math.sqrt(3) / 2, TRI = [[-SQ3, -0.5], [0, 1], [SQ3, -0.5]];
const DIRS = { E: 0, NE: 45, N: 90, NW: 135, W: 180, SW: 225, S: 270, SE: 315 };
const DIR_ARROW = { E: '→', NE: '↗', N: '↑', NW: '↖', W: '←', SW: '↙', S: '↓', SE: '↘' };
const MAX_SAMPLES = 400, MAX_ITER = 40;

/* ------------------------------------------------------------ models (mirror of motion/models.py) */
function fsum(xs) { let s = 0, c = 0; for (const x of xs) { const y = x - c, t = s + y; c = (t - s) - y; s = t; } return s; }
function num(p, name, lo, hi) { const v = p[name]; if (typeof v !== 'number' || !Number.isFinite(v) || v < lo || v > hi) throw new Error('motion model: parameter ' + name + ' must be a finite number in [' + lo + ', ' + hi + ']'); return v; }
function vec(p, name, n, lo, hi) { const v = p[name]; if (!Array.isArray(v) || v.length !== n) throw new Error('motion model: parameter ' + name + ' must be a list of ' + n + ' numbers'); return v.map(x => num({ [name]: x }, name, lo, hi)); }
const score = (pi, a) => pi.map((p, j) => (j === a ? 1 : 0) - p);
function levelSegment(r, level) {
  const pts = [];
  for (const [i, j] of [[0, 1], [1, 2], [2, 0]]) {
    if (r[i] === r[j]) continue;
    const t = (level - r[i]) / (r[j] - r[i]);
    if (t >= 0 && t <= 1) { const p = [0, 0, 0]; p[i] = 1 - t; p[j] = t; pts.push(p); }
  }
  return pts.length >= 2 ? pts.slice(0, 2) : null;
}
function scoreRays(pi, actions, returns, b) { // only the score lines that carry drawn samples, only as far as they reach
  const rays = [];
  for (let a = 0; a < 3; a++) {
    const cs = returns.filter((_, i) => actions[i] === a).map(r => r - b); if (!cs.length) continue;
    const lo = Math.min(Math.min(...cs), 0), hi = Math.max(Math.max(...cs), 0), pad = 0.08 * (hi - lo), s = score(pi, a);
    rays.push({ action: a, points: [s.map(x => (lo - pad) * x), s.map(x => (hi + pad) * x)] });
  }
  return rays;
}
function softmaxSimplexPg(p) {
  const M = PG(), theta0 = vec(p, 'theta0', 3, -8, 8), rewards = vec(p, 'rewards', 3, -20, 20);
  const sd = num(p, 'noise_sd', 0, 10), alpha = num(p, 'alpha', 0, 10), k = num(p, 'k', 0, MAX_ITER);
  const n = Math.floor(num(p, 'n', 0, MAX_SAMPLES)), seed = p.seed;
  if (!Number.isInteger(seed) || seed < 0 || seed >= 4294967296) throw new Error('motion model: seed must be an unsigned 32-bit integer');
  const b0 = num(p, 'b0', -20, 20), lam = num(p, 'lam', 0, 1), gVis = num(p, 'g_vis', 0, 1);
  const thetas = [theta0], whole = Math.floor(k);
  for (let i = 0; i < Math.min(whole + 1, MAX_ITER); i++) { const t = thetas[thetas.length - 1], g = M.exact(t, rewards, 0).grad; thetas.push(t.map((a, j) => a + alpha * g[j])); }
  const frac = k - whole, base = thetas[whole], next = thetas[Math.min(whole + 1, thetas.length - 1)];
  const theta = frac > 0 ? base.map((a, j) => a + frac * (next[j] - a)) : base.slice();
  const ex = M.exact(theta, rewards, sd), pi = ex.pi, J = ex.J, grad = ex.grad, b = (1 - lam) * b0 + lam * J;
  const draw = M.mulberry32(seed), samples = [], actions = [], returns = [];
  for (let i = 0; i < n; i++) {
    const u = draw(); let a = 2, acc = 0;
    for (let j = 0; j < 3; j++) { acc += pi[j]; if (u < acc) { a = j; break; } }
    const u1 = draw(), u2 = draw(), eps = Math.sqrt(-2 * Math.log(1 - u1)) * Math.cos(2 * Math.PI * u2), ret = rewards[a] + sd * eps;
    actions.push(a); returns.push(ret); samples.push(score(pi, a).map(s => (ret - b) * s));
  }
  let mean = [0, 0, 0], spread = 0;
  if (n) { mean = [0, 1, 2].map(j => fsum(samples.map(s => s[j])) / n); spread = Math.sqrt(fsum(samples.map(s => fsum(s.map((x, j) => (x - mean[j]) ** 2)))) / n); }
  const varB = ex.variance(b), varNone = ex.variance(0), varOpt = ex.variance(ex.b_opt), mass = fsum(pi.map((q, j) => q * ex.weights[j]));
  const pg = fsum(pi.map((q, j) => q * grad[j])), dpi = pi.map((q, j) => alpha * q * (grad[j] - pg));
  const trail = thetas.slice(0, whole + 1).map(t => M.softmax(t)).concat(frac > 0 ? [pi] : []);
  const lo = Math.min(...rewards), hi = Math.max(...rewards), levels = [];
  for (let i = 1; i <= 5; i++) { const level = lo + (hi - lo) * i / 6, seg = levelSegment(rewards, level); if (seg) levels.push({ level, points: seg }); }
  const bSeg = levelSegment(rewards, b);
  let argmax = 0; for (let j = 1; j < 3; j++) if (grad[j] > grad[argmax]) argmax = j;
  return {
    theta, pi, J, grad, grad_shown: grad.map(x => gVis * x), grad_norm: Math.sqrt(fsum(grad.map(x => x * x))), argmax_grad: argmax,
    b, b_opt: ex.b_opt, n, samples, actions, returns, sample_mean: mean, sample_spread: spread,
    var_b: varB, var_none: varNone, var_opt: varOpt, sd_b: Math.sqrt(Math.max(varB, 0)), sd_none: Math.sqrt(Math.max(varNone, 0)), sd_opt: Math.sqrt(Math.max(varOpt, 0)),
    var_delta: varB - varNone,
    b_vs_none: varB > varNone + 1e-12 ? 'größer' : (varB < varNone - 1e-12 ? 'kleiner' : 'gleich'),
    mean_shift: Math.abs(b) * Math.sqrt(fsum([0, 1, 2].map(j => fsum(pi.map((q, a) => q * score(pi, a)[j])) ** 2))),
    dpi, pi_next: pi.map((q, j) => q + dpi[j]), pi_trail: trail, J_levels: levels, b_line: bSeg ? [{ level: b, points: bSeg }] : [],
    score_rays: scoreRays(pi, actions, returns, b), b_weights: pi.map((q, j) => q * ex.weights[j] / mass),
    mean_err: n ? Math.sqrt(fsum(mean.map((x, j) => (x - grad[j]) ** 2))) : 0,
    k, alpha, g_vis: gVis, lam, b0
  };
}
/* linear_map_2d: M(t) = (1 - t) I + t A; columns, test vector, signed area, rank/kernel/image, singular times and the
   readout strings. Python decides rank exactly (rationals of the decimal inputs); here a relative tolerance does, which
   agrees at every keyframe (parity-tested) and lets the scrubber land on a collapse. */
const PEPS = 1e-9, LINE_REACH = 60;
function g2(x) { const r = Math.floor(x * 100 + 0.5) / 100; if (Math.abs(r) < 5e-10) return '0'; return String(r).replace('-', '−').replace('.', ','); }
const par = x => x < -5e-10 ? '(' + g2(x) + ')' : g2(x), pt = q => '(' + g2(q[0]) + '; ' + g2(q[1]) + ')';
function scaleNice(u) {
  const m = Math.max(Math.abs(u[0]), Math.abs(u[1])); let w = u.map(x => x / m);
  for (let k = 1; k <= 12; k++) { const c = w.map(x => x * k); if (c.every(x => Math.abs(x - Math.round(x)) < 1e-7)) { w = c.map(Math.round); break; } }
  const sg = (w[0] !== 0 ? w[0] : w[1]) < 0 ? -1 : 1; return w.map(x => sg * x + 0);
}
function kernelImage(m) {
  const sc = Math.max(1, ...m.map(Math.abs));
  if (Math.abs(m[0] * m[3] - m[1] * m[2]) > PEPS * sc * sc) return { rank: 2, kernel: [], image: [[1, 0], [0, 1]] };
  if (m.every(x => Math.abs(x) <= PEPS)) return { rank: 0, kernel: [[1, 0], [0, 1]], image: [] };
  const row = (Math.abs(m[0]) > PEPS || Math.abs(m[1]) > PEPS) ? [m[0], m[1]] : [m[2], m[3]];
  const col = (Math.abs(m[0]) > PEPS || Math.abs(m[2]) > PEPS) ? [m[0], m[2]] : [m[1], m[3]];
  return { rank: 1, kernel: [scaleNice([row[1], -row[0]])], image: [scaleNice(col)] };
}
function singularTimes(a) {
  const tr = a[0] + a[3], D = a[0] * a[3] - a[1] * a[2], qa = 1 - tr + D, qb = tr - 2, qc = 1;
  if (Math.abs(qa) < 1e-15) { if (Math.abs(qb) < 1e-15) return []; const r = -qc / qb; return r >= 0 && r <= 1 ? [r] : []; }
  const disc = qb * qb - 4 * qa * qc; if (disc < 0) return []; const q = Math.sqrt(disc);
  return [...new Set([(-qb - q) / (2 * qa), (-qb + q) / (2 * qa)])].sort((x, y) => x - y).filter(r => r >= -1e-12 && r <= 1 + 1e-12);
}
function planeTexts(st) {
  const m = st.M, v = st.v, rank = st.rank;
  const ki = rank === 1 ? ['Kern = span' + pt(st.kernel[0]), 'Bild = span' + pt(st.image[0]), '2 = 1 + 1']
    : rank === 0 ? ['Kern = ganze Ebene', 'Bild = {0}', '2 = 2 + 0'] : ['Kern = {0}', 'Bild = ganze Ebene', '2 = 0 + 2'];
  return {
    t_text: g2(st.t), e1_text: pt(st.e1), e2_text: pt(st.e2), Mv_text: pt(st.Mv), Av_text: pt(st.Av), v_text: pt(v),
    Mv_formula: par(v[0]) + '·' + pt(st.e1) + ' + ' + par(v[1]) + '·' + pt(st.e2) + ' = ' + pt(st.Mv),
    Av_formula: par(v[0]) + '·' + pt(st.A_e1) + ' + ' + par(v[1]) + '·' + pt(st.A_e2) + ' = ' + pt(st.Av),
    det_formula: par(m[0]) + '·' + par(m[3]) + ' − ' + par(m[1]) + '·' + par(m[2]) + ' = ' + g2(st.det),
    det_A_text: g2(st.det_A),
    det_A_note: st.det_A < 0 ? 'Weil det A < 0 ist, muss jeder stetige Weg von I nach A durch det = 0: Die Ebene wird unterwegs einmal flach gedrückt.' : st.rank_A < 2 ? 'det A = 0: Am Ende liegt die ganze Ebene auf einer Geraden oder im Nullpunkt.' : 'det A > 0: Die Orientierung bleibt erhalten.',
    orientation_text: st.orientation > 0 ? 'Orientierung erhalten' : st.orientation < 0 ? 'Orientierung umgekehrt (gespiegelt)' : 'Fläche 0: die Ebene ist kollabiert',
    rank_text: 'Rang M = ' + rank, kernel_text: ki[0], image_text: ki[1], dim_text: 'dim Kern + Rang: ' + ki[2]
  };
}
const lineOf = dirs => { if (dirs.length !== 1) return []; const u = dirs[0], k = LINE_REACH / Math.hypot(u[0], u[1]); return [{ points: [[-k * u[0], -k * u[1]], [k * u[0], k * u[1]]] }]; };
function linearMap2d(p) {
  const a = vec(p, 'A', 4, -10, 10), t = num(p, 't', 0, 1), v = vec(p, 'v', 2, -10, 10);
  const m = [(1 - t) + t * a[0], t * a[1], t * a[2], (1 - t) + t * a[3]], ap = (q, x, y) => [q[0] * x + q[1] * y, q[2] * x + q[3] * y];
  const det = m[0] * m[3] - m[1] * m[2], detA = a[0] * a[3] - a[1] * a[2], sc = Math.max(1, ...m.map(Math.abs));
  const ki = kernelImage(m), kA = kernelImage(a);
  const orientation = ki.rank < 2 ? 0 : (det > PEPS * sc * sc ? 1 : -1);
  const st = {
    M: m, A: a, I: [1, 0, 0, 1], t, v, e1: ap(m, 1, 0), e2: ap(m, 0, 1), Mv: ap(m, v[0], v[1]), Av: ap(a, v[0], v[1]),
    A_e1: ap(a, 1, 0), A_e2: ap(a, 0, 1), square: [ap(m, 0, 0), ap(m, 1, 0), ap(m, 1, 1), ap(m, 0, 1)],
    det: ki.rank < 2 ? 0 : det, det_A: kA.rank < 2 ? 0 : detA, orientation,
    rank: ki.rank, kernel: ki.kernel, image: ki.image, rank_A: kA.rank, kernel_A: kA.kernel, image_A: kA.image,
    kernel_line: lineOf(ki.kernel), image_line: lineOf(ki.image), singular_times: singularTimes(a)
  };
  return Object.assign(st, planeTexts(st));
}
const MODELS = { softmax_simplex_pg: softmaxSimplexPg, linear_map_2d: linearMap2d };

/* ------------------------------------------------------------ evaluation, text, display list (mirror of motion/__init__.py) */
const clone = x => JSON.parse(JSON.stringify(x));
/* over: parameter values that replace the defaults before the steps apply (a preset's set, or the learner's edits). */
function paramsAt(scene, index, over) {
  const p = {}; for (const [k, v] of Object.entries(scene.params)) p[k] = clone(v.value);
  if (over) Object.assign(p, clone(over));
  for (const st of scene.steps.slice(0, index + 1)) Object.assign(p, clone(st.set || {}));
  return p;
}
const presetOf = (scene, id) => (scene.presets || []).find(x => x.id === id) || null;
function panelsFor(scene, presetId) { const dom = (presetOf(scene, presetId) || {}).domain || {}; return scene.view.panels.map(p => Object.assign({}, p, { domain: dom[p.id] || p.domain })); }
const evaluate = (scene, params) => MODELS[scene.model](params);
function get(state, ref) { if (Array.isArray(ref) || typeof ref === 'number') return ref; if (!(ref in state)) throw new Error('unknown state quantity ' + ref); return state[ref]; }
function fmt(x, d) { if (typeof x !== 'number' || !Number.isFinite(x)) return '–'; let s = x.toFixed(d); if (Number(s) === 0) s = s.replace(/^-/, ''); return s.replace(/-/g, '−').replace('.', ','); }
function textOf(tpl, state) {
  return tpl.replace(/\{([A-Za-z_][A-Za-z0-9_]*)(?:\.(\d))?(?::(\d))?\}/g, (_, name, idx, dec) => {
    let v = get(state, name); if (idx !== undefined) v = v[Number(idx)];
    if (typeof v === 'string') return v;
    if (dec === undefined && typeof v === 'number' && Number.isInteger(v) && Math.abs(v) < 1e15) return String(v);
    return fmt(v, dec === undefined ? 2 : Number(dec));
  });
}
function frame(panel) {
  const [x0, x1, y0, y1] = panel.domain, s = Math.min(panel.w / (x1 - x0), panel.h / (y1 - y0));
  return [s, panel.x + (panel.w - s * (x1 - x0)) / 2 - s * x0, panel.y + (panel.h - s * (y1 - y0)) / 2 + s * y1];
}
const world = (p, coords) => coords === 'tri3' ? [p[0] * TRI[0][0] + p[1] * TRI[1][0] + p[2] * TRI[2][0], p[0] * TRI[0][1] + p[1] * TRI[1][1] + p[2] * TRI[2][1]] : [p[0], p[1]];
function screen(panel, p, coords) { const [s, ox, oy] = frame(panel), w = world(p, coords || 'xy'); return [ox + s * w[0], oy - s * w[1]]; }
const FONT = 14;
function box(x, y, s, a) { const w = 0.56 * FONT * [...s].length, x0 = a === 'start' ? x : (a === 'middle' ? x - w / 2 : x - w); return [x0, y - 0.8 * FONT, x0 + w, y + 0.25 * FONT]; }
const free = (b, boxes) => boxes.every(c => b[2] <= c[0] || b[0] >= c[2] || b[3] <= c[1] || b[1] >= c[3]);
const LABEL_SPOTS = { point: [[10, -10, 'start'], [10, 22, 'start'], [-10, -10, 'end'], [-10, 22, 'end']], vector: [[8, -6, 'start'], [8, 18, 'start'], [-8, -6, 'end'], [-8, 18, 'end']] };
function display(scene, state, panelList) {
  const panels = Object.fromEntries((panelList || scene.view.panels).map(p => [p.id, p])), out = [], boxes = {};
  for (const obj of scene.objects) {
    const panel = panels[obj.panel], t = obj.token || 'ink', coords = obj.coords || 'xy', o = obj.id, sc = obj.scale === undefined ? 1 : obj.scale;
    const taken = boxes[obj.panel] = boxes[obj.panel] || [];
    const P = p => screen(panel, p, coords), add = (k, geo) => {
      out.push(Object.assign({ o, k, t }, geo));
      if (k === 'text') taken.push(box(geo.x, geo.y, geo.s, geo.a)); else if (k === 'mark') taken.push([geo.x - geo.r, geo.y - geo.r, geo.x + geo.r, geo.y + geo.r]);
    };
    const label = (x, y, text, kind) => { const spots = LABEL_SPOTS[kind]; let pick = spots[0];
      for (const sp of spots) if (free(box(x + sp[0], y + sp[1], text, sp[2]), taken)) { pick = sp; break; }
      add('text', { x: x + pick[0], y: y + pick[1], s: text, a: pick[2] }); };
    switch (obj.type) {
      case 'simplex': {
        const c = [0, 1, 2].map(j => screen(panel, [0, 1, 2].map(a => a === j ? 1 : 0), 'tri3'));
        if (obj.style === 'axes') { const [cx, cy] = screen(panel, [0, 0], 'xy'); for (const [x, y] of c) add('line', { x1: cx, y1: cy, x2: x, y2: y }); }
        else add('poly', { pts: c.flat(), closed: true });
        c.forEach(([x, y], j) => add('text', { x, y: y + (j !== 1 ? 18 : -9), s: obj.labels[j], a: 'middle' }));
        break;
      }
      case 'point': { const [x, y] = P(get(state, obj.at)); add('mark', { x, y, r: obj.size || 6 }); if (obj.label) label(x, y, textOf(obj.label, state), 'point'); break; }
      case 'points': {
        const off = obj.offset !== undefined ? get(state, obj.offset) : null;
        for (const p of get(state, obj.of)) { let q = p.map(v => v * sc); if (off) q = q.map((v, j) => v + off[j]); const [x, y] = P(q); add('mark', { x, y, r: obj.size || 3 }); }
        break;
      }
      case 'vector': {
        const base = get(state, obj.from !== undefined ? obj.from : (coords === 'tri3' ? [0, 0, 0] : [0, 0]));
        const tip = obj.by !== undefined ? base.map((a, j) => a + sc * get(state, obj.by)[j]) : get(state, obj.to);
        const [x1, y1] = P(base), [x2, y2] = P(tip); add('arrow', { x1, y1, x2, y2 });
        if (obj.label) label(x2, y2, textOf(obj.label, state), 'vector');
        break;
      }
      case 'circle': {
        let c = get(state, obj.center); if (obj.scale !== undefined) c = c.map(v => v * sc);
        const r = get(state, obj.radius) * (obj.radius_scale === undefined ? 1 : obj.radius_scale), [s] = frame(panel), f = coords === 'tri3' ? Math.sqrt(1.5) : 1;
        const [x, y] = P(c); add('circle', { x, y, r: r * s * f }); break;
      }
      case 'curve': add('poly', { pts: get(state, obj.points).map(P).flat(), closed: !!obj.closed }); break;
      case 'lines': for (const item of get(state, obj.of)) add('poly', { pts: item.points.map(P).flat(), closed: false }); break;
      case 'polygon': { const orient = obj.orientation ? get(state, obj.orientation) : 1; add('area', { pts: get(state, obj.points).map(P).flat(), neg: orient < 0 }); break; }
      case 'grid': {
        const m = get(state, obj.matrix), [lo, hi] = obj.range || [-4, 4], ap = v => [m[0] * v[0] + m[1] * v[1], m[2] * v[0] + m[3] * v[1]];
        for (let i = Math.trunc(lo); i <= Math.trunc(hi); i++) for (const [a, b] of [[[i, lo], [i, hi]], [[lo, i], [hi, i]]]) { const [x1, y1] = P(ap(a)), [x2, y2] = P(ap(b)); add('line', { x1, y1, x2, y2 }); }
        break;
      }
      case 'bars': {
        const vals = get(state, obj.of), bw = panel.w / vals.length, top = obj.max === undefined ? 1 : obj.max;
        vals.forEach((v, j) => { const bh = Math.max(0, Math.min(1, v / top)) * (panel.h - 24);
          add('rect', { x: panel.x + j * bw + 6, y: panel.y + panel.h - 18 - bh, w: bw - 12, h: bh });
          add('text', { x: panel.x + (j + 0.5) * bw, y: panel.y + panel.h - 4, s: obj.labels[j], a: 'middle' });
          add('text', { x: panel.x + (j + 0.5) * bw, y: panel.y + panel.h - 22 - bh, s: fmt(v, obj.digits === undefined ? 2 : obj.digits), a: 'middle' }); });
        break;
      }
      case 'graph': {
        const nodes = Object.fromEntries(obj.nodes.map(n => [n.id, n])), vals = obj.values ? get(state, obj.values) : null;
        for (const e of obj.edges) { const [x1, y1] = P(nodes[e.from].at), [x2, y2] = P(nodes[e.to].at); add('arrow', { x1, y1, x2, y2 }); }
        obj.nodes.forEach((n, j) => { const [x, y] = P(n.at); add('circle', { x, y, r: 16 }); add('text', { x, y: y + 4, s: vals === null ? n.label : fmt(vals[j], 2), a: 'middle' }); });
        break;
      }
      case 'label': add('text', { x: panel.x + obj.x, y: panel.y + obj.y, s: textOf(obj.text, state), a: obj.anchor || 'start' }); break;
    }
  }
  return out;
}
function directionDeg(scene, state, id) {
  const p = display(scene, state).find(q => q.o === id && q.k === 'arrow');
  if (!p) throw new Error('direction checkpoint needs vector object ' + id);
  const d = Math.atan2(-(p.y2 - p.y1), p.x2 - p.x1) * 180 / Math.PI; return ((d % 360) + 360) % 360;
}
function correctAnswer(scene, state, q) {
  const r = q.correct;
  if (r.rule === 'angle') return { deg: directionDeg(scene, state, r.object), tol_deg: r.tol_deg === undefined ? 27.5 : r.tol_deg };
  const v = get(state, r.of);
  if (r.rule === 'value') return { value: v, tol: r.tol };
  if (r.rule === 'point') return { point: [v[0], v[1]], tol: r.tol };
  if (r.rule === 'argmax') { let m = 0; for (let j = 1; j < v.length; j++) if (v[j] > v[m]) m = j; return r.map[m]; }
  if (r.rule === 'sign') { const tol = r.tol === undefined ? 1e-9 : r.tol, key = Math.abs(v) <= tol ? '0' : v > 0 ? '+' : '-'; return (r.map || { '+': '+', '-': '-', 0: '0' })[key]; }
  if (r.rule === 'index') return r.map[Math.trunc(v)];
  throw new Error('unknown answer rule ' + r.rule);
}
function parseNum(x) { const t = String(x === undefined || x === null ? '' : x).trim().replace(',', '.').replace('−', '-'); return t === '' ? NaN : Number(t); }
function isCorrect(scene, state, q, answer) {
  const want = correctAnswer(scene, state, q);
  if (q.type === 'direction') return Math.abs(((DIRS[answer] - want.deg + 180) % 360 + 360) % 360 - 180) <= want.tol_deg;
  if (q.type === 'number') return Math.abs(parseNum(answer) - want.value) <= want.tol;
  if (q.type === 'point') return Array.isArray(answer) && Math.hypot(parseNum(answer[0]) - want.point[0], parseNum(answer[1]) - want.point[1]) <= want.tol;
  return answer === want;
}
function goalMet(state, g) {
  const left = get(state, g.of), right = g.ref !== undefined ? get(state, g.ref) * (g.factor === undefined ? 1 : g.factor) : g.value;
  return g.op === '<=' ? left <= right : g.op === '>=' ? left >= right : Math.abs(left) <= right;
}
const ease = t => t * t * t * (t * (6 * t - 15) + 10); // smootherstep: gentle start and stop, no overshoot
const easeOf = (scene, j) => ((scene.steps[j] || {}).transition || {}).ease === 'linear' ? (t => t) : ease;
/* State at a real timeline position: integer = keyframe; fractional = transition into the next step (eased unless the
   transition says linear). Parameters named in transition.animate are interpolated (integers floored); all other
   changes apply at the start. */
function paramsAtPosition(scene, pos, over) {
  const i = Math.max(0, Math.min(scene.steps.length - 1, Math.floor(pos + 1e-9))), f = pos - i;
  const a = paramsAt(scene, i, over);
  if (f <= 1e-9 || i >= scene.steps.length - 1) return a;
  const b = paramsAt(scene, i + 1, over), tr = scene.steps[i + 1].transition || {}, anim = tr.animate || [], e = easeOf(scene, i + 1)(f), out = {};
  for (const k of Object.keys(b)) {
    if (anim.includes(k) && typeof b[k] === 'number') { let v = a[k] + (b[k] - a[k]) * e; if ((scene.params[k] || {}).int) v = Math.floor(v + 1e-9); out[k] = v; }
    else if (anim.includes(k) && Array.isArray(b[k])) out[k] = b[k].map((x, j) => a[k][j] + (x - a[k][j]) * e);
    else out[k] = b[k];
  }
  return out;
}
const core = { MODELS, paramsAt, paramsAtPosition, panelsFor, evaluate, display, textOf, fmt, g2, directionDeg, correctAnswer, isCorrect, goalMet, ease, parseNum };

/* ------------------------------------------------------------ SVG (same primitives as motion.primitive_svg) */
const n2 = x => (Math.abs(x) >= 0.005 ? x.toFixed(2).replace(/\.?0+$/, '') : '0');
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const colorOf = (tok, theme) => (theme === 'dark' ? tok.dark : tok.color);
function markSvg(x, y, r, tok, theme, bg) {
  const c = colorOf(tok, theme);
  switch (tok.shape) {
    case 'square': return `<rect x="${n2(x - r)}" y="${n2(y - r)}" width="${n2(2 * r)}" height="${n2(2 * r)}" fill="${c}"/>`;
    case 'diamond': return `<path d="M${n2(x)} ${n2(y - r)}L${n2(x + r)} ${n2(y)}L${n2(x)} ${n2(y + r)}L${n2(x - r)} ${n2(y)}Z" fill="${c}"/>`;
    case 'triangle': return `<path d="M${n2(x)} ${n2(y - r)}L${n2(x + r)} ${n2(y + r)}L${n2(x - r)} ${n2(y + r)}Z" fill="${c}"/>`;
    case 'ring': return `<circle cx="${n2(x)}" cy="${n2(y)}" r="${n2(r)}" fill="none" stroke="${c}" stroke-width="1.4" opacity="0.8"/>`;
    default: return `<circle cx="${n2(x)}" cy="${n2(y)}" r="${n2(r)}" fill="${c}" stroke="${bg || '#ffffff'}" stroke-width="2"/>`;
  }
}
/* Same markup as motion.primitive_svg (Python), for the light or dark stage. */
function primitiveSvg(p, palette, uid, theme, bg) {
  const tok = palette[p.t], c = colorOf(tok, theme), dash = tok.dash ? ` stroke-dasharray="${tok.dash}"` : '';
  switch (p.k) {
    case 'line': return `<line x1="${n2(p.x1)}" y1="${n2(p.y1)}" x2="${n2(p.x2)}" y2="${n2(p.y2)}" stroke="${c}" stroke-width="1" opacity="0.6"${dash}/>`;
    case 'arrow': {
      const dx = p.x2 - p.x1, dy = p.y2 - p.y1, L = Math.hypot(dx, dy); if (L < 1e-6) return '';
      const ux = dx / L, uy = dy / L, h = Math.min(14, 0.45 * L), bx = p.x2 - ux * h, by = p.y2 - uy * h;
      return `<line x1="${n2(p.x1)}" y1="${n2(p.y1)}" x2="${n2(bx)}" y2="${n2(by)}" stroke="${c}" stroke-width="3.5" stroke-linecap="round"${dash}/>` +
        `<path d="M${n2(p.x2)} ${n2(p.y2)}L${n2(bx - uy * h * 0.42)} ${n2(by + ux * h * 0.42)}L${n2(bx + uy * h * 0.42)} ${n2(by - ux * h * 0.42)}Z" fill="${c}"/>`;
    }
    case 'mark': return markSvg(p.x, p.y, p.r, tok, theme, bg);
    case 'circle': return `<circle cx="${n2(p.x)}" cy="${n2(p.y)}" r="${n2(p.r)}" fill="none" stroke="${c}" stroke-width="1.8"${dash || ' stroke-dasharray="4 3"'}/>`;
    case 'poly': return `<${p.closed ? 'polygon' : 'polyline'} points="${p.pts.map(n2).join(' ')}" fill="none" stroke="${c}" stroke-width="2" stroke-linejoin="round"${dash}/>`;
    case 'area': return `<polygon points="${p.pts.map(n2).join(' ')}" fill="${p.neg ? 'url(#' + (uid || 'mm') + '-hatch)' : c}" fill-opacity="0.24" stroke="${c}" stroke-width="2"/>`;
    case 'rect': return `<rect x="${n2(p.x)}" y="${n2(p.y)}" width="${n2(p.w)}" height="${n2(p.h)}" fill="${c}" fill-opacity="0.85"/>`;
    case 'text': return `<text x="${n2(p.x)}" y="${n2(p.y)}" text-anchor="${p.a}" fill="${c}" font-size="${FONT}" font-weight="600" stroke="${bg || '#ffffff'}" stroke-width="4" stroke-linejoin="round" paint-order="stroke">${esc(p.s)}</text>`;
  }
  return '';
}

/* ------------------------------------------------------------ learner store (localStorage em-motion-v1) */
const KEY = 'em-motion-v1';
function readStore() { try { const d = JSON.parse(localStorage.getItem(KEY) || 'null'); if (d && d.schema === 1 && d.scenes && typeof d.scenes === 'object') return d; } catch (e) { /* unavailable */ } return { schema: 1, scenes: {} }; }
function sceneRecord(scene) {
  const store = readStore(); let rec = store.scenes[scene.id];
  if (rec && rec.revision !== scene.revision) { (store.archived = store.archived || {})[scene.id + '@' + rec.revision] = rec; rec = null; }
  if (!rec || !Array.isArray(rec.events)) rec = { revision: scene.revision, events: [] };
  store.scenes[scene.id] = rec;
  return { store, rec };
}
function record(scene, event) {
  const { store, rec } = sceneRecord(scene);
  if (rec.events.length >= 5000) return false;
  rec.events.push(Object.assign({ t: new Date().toISOString() }, event));
  try { localStorage.setItem(KEY, JSON.stringify(store)); return true; } catch (e) { return false; }
}

/* ------------------------------------------------------------ DOM */
function h(tag, attrs, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) { if (v === null || v === undefined || v === false) continue; if (k === 'class') e.className = v; else if (k.startsWith('on')) e.addEventListener(k.slice(2), v); else e.setAttribute(k, v === true ? '' : v); }
  for (const kid of kids.flat()) if (kid !== null && kid !== undefined && kid !== false) e.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  return e;
}
const SVGNS = 'http://www.w3.org/2000/svg';
const reducedMotion = () => typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;

function themeNow() {
  const de = typeof document !== 'undefined' ? document.documentElement : null, t = de && de.dataset ? de.dataset.theme : '';
  if (t === 'dark' || t === 'light') return t;
  return typeof matchMedia === 'function' && matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}
const STAGE = { light: { bg: '#ffffff', ink: '#1b1f2a' }, dark: { bg: '#12161f', ink: '#e6e8ee' } };

function mount(root, scene) {
  const N = scene.steps.length, pal = scene.palette, stage = scene.stage || STAGE, reduce = reducedMotion();
  const termOf = {}; for (const [tid, t] of Object.entries(scene.terms)) for (const o of t.objects) termOf[o] = tid;
  const presets = scene.presets || [];
  let presetId = presets.length ? presets[0].id : null, over = presetId ? clone(presets[0].set) : null, panels = panelsFor(scene, presetId);
  let keyStates = [], keyDisplays = [];
  function rebase() { keyStates = scene.steps.map((_, i) => evaluate(scene, paramsAt(scene, i, over))); keyDisplays = keyStates.map(s => display(scene, s, panels)); }
  rebase();
  const revealed = new Set(), predicted = {}, rk = id => (presetId ? presetId + '/' : '') + id;
  for (const e of sceneRecord(scene).rec.events) {
    if (e.preset === 'custom') continue; // a learner-edited matrix is a fresh round on every visit
    const key = (e.preset ? e.preset + '/' : '') + e.step;
    if (e.type === 'reveal') revealed.add(key);
    if (e.type === 'predict') (predicted[key] = predicted[key] || {})[e.question] = e.answer;
  }
  const tag = () => (presetId ? { preset: presetId } : {});
  let theme = themeNow(), pos = 0, anim = null, playing = false, hoverTerm = null, mode = 'timeline', mission = null, missionParams = null, drag = null;
  root.classList.add('mm-ready'); root.dataset.scene = scene.id; root.dataset.reducedMotion = reduce ? '1' : '0'; root.dataset.theme = theme;
  if (presetId) root.dataset.preset = presetId;
  const fallback = root.querySelector('.mm-fallback'); if (fallback) fallback.hidden = true;

  // stage
  const W = scene.view.width, H = scene.view.height, uid = 'mm-' + scene.id;
  const svg = document.createElementNS(SVGNS, 'svg');
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`); svg.setAttribute('class', 'mm-stage'); svg.setAttribute('role', 'img');
  const descId = 'mm-desc-' + scene.id; svg.setAttribute('aria-labelledby', descId);
  const titles = scene.view.panels.filter(p => p.title).map(p => `<text x="${p.x}" y="${p.y - 8}" class="mm-panel-title">${esc(p.title)}</text>`).join('');
  svg.innerHTML = `<defs></defs><title id="${descId}"></title>` + titles + '<g class="mm-geo"></g><g class="mm-handles"></g>';
  const defs = svg.querySelector('defs'), geo = svg.querySelector('.mm-geo'), handles = svg.querySelector('.mm-handles'), titleEl = svg.querySelector('title');
  function paintDefs() {
    const hatch = colorOf(pal.area, theme);
    defs.innerHTML = `<pattern id="${uid}-hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="7" stroke="${hatch}" stroke-width="2.4"/></pattern>` +
      scene.view.panels.filter(p => p.clip).map(p => `<clipPath id="mm-clip-${scene.id}-${p.id}"><rect x="${p.x}" y="${p.y}" width="${p.w}" height="${p.h}"/></clipPath>`).join('');
  }

  // equation with term bindings (MathJax SVG when available; operators get breathing room)
  const eq = h('p', { class: 'mm-equation', role: 'group', 'aria-label': scene.equation.label + ': ' + scene.equation.segments.map(s => s.text).join('') });
  for (const seg of scene.equation.segments) {
    const op = !seg.term && /^\s*(=|\+|-|−|,|\\quad|\\qquad|\\cdot)\s*$/.test(seg.tex);
    const span = h('span', { class: 'mm-seg' + (seg.term ? ' mm-term' : '') + (op ? ' mm-op' : '') });
    if (seg.svg) { span.innerHTML = seg.svg; const s = span.querySelector('svg'); if (s) s.setAttribute('aria-hidden', 'true'); span.append(h('span', { class: 'mm-sr' }, seg.text)); }
    else span.textContent = seg.text;
    if (seg.term) {
      const t = scene.terms[seg.term], tok = pal[t.token];
      span.dataset.term = seg.term; span.tabIndex = 0; span.setAttribute('role', 'button'); span.setAttribute('aria-pressed', 'false');
      span.title = t.name; span.style.borderBottomStyle = tok.dash ? (tok.dash.startsWith('2') ? 'dotted' : 'dashed') : 'solid';
      const on = () => { hoverTerm = seg.term; draw(); }, off = () => { hoverTerm = null; draw(); };
      span.addEventListener('mouseenter', on); span.addEventListener('mouseleave', off); span.addEventListener('focus', on); span.addEventListener('blur', off);
      span.addEventListener('click', on);
    }
    eq.append(span);
  }
  const legend = h('ul', { class: 'mm-legend' }, Object.entries(scene.terms).map(([tid, t]) => {
    const mk = document.createElementNS(SVGNS, 'svg'); mk.setAttribute('viewBox', '0 0 16 16'); mk.setAttribute('class', 'mm-swatch'); mk.setAttribute('aria-hidden', 'true');
    return h('li', { 'data-term': tid }, mk, t.name);
  }));
  function paintTerms() {
    for (const span of eq.querySelectorAll('.mm-term')) span.style.color = colorOf(pal[scene.terms[span.dataset.term].token], theme);
    for (const li of legend.children) li.querySelector('svg').innerHTML = markSvg(8, 8, 5, pal[scene.terms[li.dataset.term].token], theme, stage[theme].bg);
  }

  // presets and learner-entered values: each starts a new round (predict first again)
  const presetBar = presets.length ? h('div', { class: 'mm-presets', role: 'group', 'aria-label': 'Beispiele' },
    presets.map(pr => h('button', { type: 'button', class: 'mm-opt', 'data-preset': pr.id, 'aria-pressed': 'false', onclick: () => loadPreset(pr.id) }, pr.label))) : null;
  const edits = (scene.edit || []).map(e => {
    const spec = scene.params[e.param];
    const inp = h('input', { type: 'number', class: 'mm-edit-input', min: String(spec.min), max: String(spec.max), step: String(e.step || 0.5), 'data-param': e.param, 'data-index': e.index === undefined ? null : String(e.index), 'aria-label': e.label });
    inp.addEventListener('change', () => {
      const x = parseNum(inp.value);
      if (!Number.isFinite(x) || x < spec.min || x > spec.max) { syncEdits(); return; }
      let val = x; if (e.index !== undefined) { val = paramsAt(scene, 0, over)[e.param].slice(); val[e.index] = x; }
      over = Object.assign({}, over || {}, { [e.param]: val }); newCustomRound(false);
    });
    return { e, inp, el: h('label', { class: 'mm-edit-field' }, h('span', {}, e.label), inp) };
  });
  const editBox = edits.length ? h('fieldset', { class: 'mm-edit' }, h('legend', {}, 'Eigene Werte (neue Runde: erst vorhersagen)'), edits.map(x => x.el)) : null;
  function syncEdits() { const p0 = paramsAt(scene, 0, over); for (const { e, inp } of edits) inp.value = String(e.index === undefined ? p0[e.param] : p0[e.param][e.index]); }
  function markPresets() { if (presetBar) for (const b of presetBar.children) b.setAttribute('aria-pressed', String(b.dataset.preset === presetId)); root.dataset.preset = presetId || ''; }
  function loadPreset(id) {
    stop(); playing = false; play.textContent = 'Abspielen'; if (mode === 'mission') leaveMission();
    presetId = id; over = clone(presetOf(scene, id).set); panels = panelsFor(scene, id); rebase(); syncEdits(); syncMissions(); markPresets(); drawSnaps(); setPos(0);
  }
  function newCustomRound(explore) { // explore: dragging after the reveal keeps the timeline open
    stop(); playing = false; play.textContent = 'Abspielen'; if (mode === 'mission') leaveMission();
    presetId = 'custom';
    for (const k of [...revealed]) if (k.startsWith('custom/')) revealed.delete(k);
    for (const k of Object.keys(predicted)) if (k.startsWith('custom/')) delete predicted[k];
    if (explore) for (const st of scene.steps) if (st.checkpoint) revealed.add('custom/' + st.id);
    rebase(); syncEdits(); syncMissions(); markPresets(); drawSnaps(); setPos(explore ? pos : 0);
  }

  // caption, controls, timeline
  const counter = h('p', { class: 'mm-counter' }), stepTitle = h('h3', { class: 'mm-step-title' }), caption = h('p', { class: 'mm-caption' });
  const live = h('p', { class: 'mm-sr', 'aria-live': 'polite', role: 'status' });
  const back = h('button', { type: 'button', class: 'mm-btn', 'data-action': 'back', onclick: () => go(Math.ceil(pos - 1e-9) - 1) }, '◀ Zurück');
  const next = h('button', { type: 'button', class: 'mm-btn mm-primary', 'data-action': 'next', onclick: () => go(Math.floor(pos + 1e-9) + 1) }, 'Weiter ▶');
  const play = h('button', { type: 'button', class: 'mm-btn mm-secondary', 'data-action': 'play', onclick: () => togglePlay() }, 'Abspielen');
  if (reduce) { play.hidden = true; }
  const scrub = h('input', { type: 'range', class: 'mm-scrub', min: '0', max: String(N - 1), step: '0.01', value: '0', 'aria-label': 'Zeitachse der Szene (ziehen)', 'data-action': 'scrub' });
  scrub.addEventListener('input', () => { stop(); setPos(Math.min(snapped(Number(scrub.value)), maxPos())); });
  scrub.addEventListener('change', () => { const r = Math.round(pos); if (Math.abs(r - pos) < 0.04) setPos(r); });
  const snaps = h('div', { class: 'mm-snaps', 'aria-hidden': 'true' });
  const ticks = h('ol', { class: 'mm-ticks' }, scene.steps.map((st, i) => h('li', { 'data-step': st.id }, h('button', { type: 'button', class: 'mm-tick', onclick: () => go(i), 'aria-label': 'Schritt ' + (i + 1) + ': ' + st.title }, String(i + 1)))));
  const cp = h('div', { class: 'mm-checkpoint', 'aria-live': 'polite' });
  const status = h('p', { class: 'mm-store' }, 'Vorhersagen und Aufträge werden nur in diesem Browser gespeichert (em-motion-v1). Sie sind Lernhandlungen, kein Nachweis von Können, und ändern keinen Kompetenzzustand.');
  const missionBox = h('div', { class: 'mm-missions' });

  root.append(...[
    h('header', { class: 'mm-head' }, h('p', { class: 'mm-eyebrow' }, 'Mastery Motion · Szene'), h('h2', { class: 'mm-title' }, scene.title), h('p', { class: 'mm-claim' }, scene.claim)),
    h('div', { class: 'mm-formula' }, eq, legend), presetBar,
    h('div', { class: 'mm-figure' }, svg, h('div', { class: 'mm-timeline' }, snaps, scrub, ticks), h('div', { class: 'mm-controls' }, back, next, play, counter)),
    h('div', { class: 'mm-layout' }, h('div', { class: 'mm-side' }, stepTitle, caption, cp, live), h('div', { class: 'mm-aside' }, editBox, missionBox)), status].filter(Boolean));

  // snapping: the scrubber lands exactly where a model quantity says something happens (e.g. det M(t) = 0)
  function positionOf(param, value) {
    for (let i = 0; i + 1 < N; i++) {
      const a = paramsAt(scene, i, over)[param], b = paramsAt(scene, i + 1, over)[param], tr = scene.steps[i + 1].transition || {};
      if (tr.ease !== 'linear' || !(tr.animate || []).includes(param) || a === b) continue;
      const f = (value - a) / (b - a); if (f >= -1e-9 && f <= 1 + 1e-9) return i + Math.min(1, Math.max(0, f));
    }
    return null;
  }
  function snapTargets() { if (!scene.snap) return []; return (keyStates[0][scene.snap.to] || []).map(v => ({ value: v, pos: positionOf(scene.snap.param, v) })).filter(x => x.pos !== null); }
  function snapped(p) {
    if (!scene.snap) return p; const val = paramsAtPosition(scene, p, over)[scene.snap.param];
    for (const tg of snapTargets()) if (Math.abs(val - tg.value) < scene.snap.within) return tg.pos;
    return p;
  }
  function drawSnaps() { snaps.replaceChildren(...snapTargets().map(tg => { const m = h('span', { class: 'mm-snap', title: scene.snap.param + ' = ' + g2(tg.value) }); m.style.left = (100 * tg.pos / (N - 1)) + '%'; return m; })); }

  function gate() { for (let j = 1; j < N; j++) if (scene.steps[j].checkpoint && !revealed.has(rk(scene.steps[j].id))) return j; return -1; }
  function maxPos() { const g = gate(); return g < 0 ? N - 1 : g - 1; }
  function changedObjects(i) { // objects whose drawing differs between keyframe i and i+1 -> their terms light up
    if (i + 1 >= N) return new Set(); const a = {}, b = {};
    for (const p of keyDisplays[i]) (a[p.o] = a[p.o] || []).push(p); for (const p of keyDisplays[i + 1]) (b[p.o] = b[p.o] || []).push(p);
    const hidA = new Set(scene.steps[i].hidden || []), hidB = new Set(scene.steps[i + 1].hidden || []), out = new Set();
    for (const o of scene.objects) if (hidA.has(o.id) !== hidB.has(o.id) || JSON.stringify(a[o.id] || []) !== JSON.stringify(b[o.id] || [])) out.add(o.id);
    return out;
  }
  function currentParams() { return mode === 'mission' ? missionParams : paramsAtPosition(scene, pos, over); }
  function dragAllowed() { return !!(scene.drag || []).length && mode === 'timeline' && Math.abs(pos - (N - 1)) < 1e-9 && gate() < 0; }
  function draw() {
    const params = currentParams(), state = evaluate(scene, params), prims = display(scene, state, panels), bg = stage[theme].bg;
    const i = Math.floor(pos + 1e-9), f = pos - i, j = Math.min(N - 1, f > 1e-9 ? i + 1 : i), target = scene.steps[mode === 'mission' ? missionStepIndex() : j];
    const hidA = new Set(scene.steps[mode === 'mission' ? missionStepIndex() : i].hidden || []), hidB = new Set(target.hidden || []), e = f > 1e-9 ? easeOf(scene, j)(f) : 0;
    const focus = new Set(target.focus || []), changing = f > 1e-9 && mode !== 'mission' ? changedObjects(i) : new Set();
    const hoverObjs = new Set(hoverTerm ? scene.terms[hoverTerm].objects : []);
    const groups = {}; for (const p of prims) (groups[p.o] = groups[p.o] || []).push(p);
    const byPanel = {};
    for (const o of scene.objects) {
      const vis = (hidA.has(o.id) ? 0 : 1) * (1 - e) + (hidB.has(o.id) ? 0 : 1) * e; if (vis <= 0.001) continue;
      const dim = hoverTerm ? !hoverObjs.has(o.id) : (focus.size && !focus.has(o.id) && o.type !== 'simplex');
      const cls = 'mm-obj' + (hoverObjs.has(o.id) ? ' mm-hl' : '') + (dim ? ' mm-context' : '');
      const bucket = o.type === 'label' ? o.panel + ':labels' : o.panel; // readouts sit outside the panel clip
      (byPanel[bucket] = byPanel[bucket] || []).push(`<g class="${cls}" data-o="${o.id}" opacity="${(vis * (dim ? 0.3 : 1)).toFixed(3)}">` + (groups[o.id] || []).map(p => primitiveSvg(p, pal, uid, theme, bg)).join('') + '</g>');
    }
    geo.innerHTML = scene.view.panels.map(p => (p.clip ? `<g clip-path="url(#mm-clip-${scene.id}-${p.id})">${(byPanel[p.id] || []).join('')}</g>` : (byPanel[p.id] || []).join('')) + (byPanel[p.id + ':labels'] || []).join('')).join('');
    handles.innerHTML = dragAllowed() ? (scene.drag || []).map((d, k) => { const a = prims.find(p => p.o === d.object && p.k === 'arrow'); return a ? `<circle class="mm-handle" data-drag="${k}" cx="${n2(a.x2)}" cy="${n2(a.y2)}" r="15" fill="${bg}" fill-opacity="0.01" stroke="${colorOf(pal[(scene.objects.find(o => o.id === d.object) || {}).token || 'ink'], theme)}" stroke-width="1.5" stroke-dasharray="3 3"/>` : ''; }).join('') : '';
    const activeTerms = new Set(); for (const o of [...focus, ...changing]) if (termOf[o]) activeTerms.add(termOf[o]); if (hoverTerm) activeTerms.add(hoverTerm);
    for (const span of eq.querySelectorAll('.mm-term')) { const on = activeTerms.has(span.dataset.term); span.classList.toggle('mm-term-on', on); span.setAttribute('aria-pressed', String(span.dataset.term === hoverTerm)); }
    for (const li of legend.children) li.classList.toggle('mm-term-on', activeTerms.has(li.dataset.term));
    titleEl.textContent = scene.title + '. ' + textOf(target.aria, state);
    root.dataset.pos = pos.toFixed(3);
    root.dataset.state = JSON.stringify({ n: state.n, J: state.J, pi: state.pi, t: state.t, det: state.det, rank: state.rank });
    return state;
  }
  function missionStepIndex() { return scene.steps.findIndex(s => s.id === mission.from_step); }
  function arrive() { // at an integer position: caption, counter, checkpoint panel
    const i = Math.round(pos), st = scene.steps[i], state = keyStates[i];
    counter.textContent = 'Schritt ' + (i + 1) + ' von ' + N; stepTitle.textContent = st.title; caption.textContent = textOf(st.caption, state);
    live.textContent = 'Schritt ' + (i + 1) + ': ' + st.title + '. ' + textOf(st.caption, state);
    root.dataset.step = st.id;
    for (const li of ticks.children) { const k = [...ticks.children].indexOf(li); li.classList.toggle('mm-done', k <= i); li.querySelector('button').disabled = k > maxPos(); li.querySelector('button').setAttribute('aria-current', k === i ? 'step' : 'false'); }
    back.disabled = i === 0; renderCheckpoint(i);
  }
  function setPos(p) {
    pos = Math.max(0, Math.min(p, N - 1)); scrub.value = String(pos); draw();
    if (Math.abs(pos - Math.round(pos)) < 1e-9) arrive(); else { cp.replaceChildren(); next.disabled = Math.floor(pos) + 1 > maxPos(); back.disabled = false; }
  }
  function stop() { if (anim) cancelAnimationFrame(anim.raf); anim = null; }
  function go(target, onDone) {
    if (mode === 'mission') leaveMission();
    stop(); target = Math.max(0, Math.min(target, N - 1));
    if (target > maxPos()) { const g = gate(); if (g >= 0 && Math.round(pos) === g - 1) cp.querySelector('input,button')?.focus(); return; }
    const from = pos; if (target === from) { setPos(target); onDone && onDone(); return; }
    const ms = target > from ? ((scene.steps[Math.min(N - 1, Math.floor(from + 1e-9) + 1)].transition || {}).ms || 900) : 500;
    if (reduce || Math.abs(target - from) > 1.0001) { // reduced motion: step only; long jumps (tick buttons) are not animated either
      setPos(target); onDone && onDone(); return;
    }
    const t0 = performance.now();
    const tick = now => { const f = Math.min(1, (now - t0) / ms); setPos(from + (target - from) * f); if (f < 1) anim = { raf: requestAnimationFrame(tick) }; else { anim = null; setPos(target); onDone && onDone(); } };
    anim = { raf: requestAnimationFrame(tick) };
  }
  function togglePlay() {
    if (playing) { playing = false; play.textContent = 'Abspielen'; stop(); return; }
    playing = true; play.textContent = 'Pause';
    const step = () => { if (!playing) return; const i = Math.round(pos); if (i >= maxPos()) { playing = false; play.textContent = 'Abspielen'; return; }
      const linear = ((scene.steps[i + 2] || {}).transition || {}).ease === 'linear'; go(i + 1, () => setTimeout(step, linear ? 30 : 700)); };
    step();
  }
  const pair = v => '(' + g2(parseNum(v[0])) + '; ' + g2(parseNum(v[1])) + ')';
  function describe(q, ans) {
    if (q.type === 'direction') return DIR_ARROW[ans] + ' (' + ans + ')';
    if (q.type === 'choice') { const o = q.options.find(x => x.id === ans); return o ? o.label : String(ans); }
    if (q.type === 'number') return fmt(parseNum(ans), 2);
    if (q.type === 'point') return Array.isArray(ans) ? pair(ans) : '–';
    return { '+': 'positiv', '-': 'negativ', 0: 'null' }[ans] || String(ans);
  }
  function truth(q, state) {
    const w = correctAnswer(scene, state, q);
    if (q.type === 'direction') { const best = Object.keys(DIRS).reduce((b, k) => Math.abs(((DIRS[k] - w.deg + 180) % 360 + 360) % 360 - 180) < Math.abs(((DIRS[b] - w.deg + 180) % 360 + 360) % 360 - 180) ? k : b, 'E'); return DIR_ARROW[best] + ' (' + fmt(w.deg, 0) + '°)'; }
    if (q.type === 'number') return fmt(w.value, 2);
    if (q.type === 'point') return pair(w.point);
    return describe(q, w);
  }
  function renderCheckpoint(i) {
    cp.replaceChildren(); next.disabled = i >= N - 1; next.textContent = 'Weiter ▶';
    const here = scene.steps[i];
    scene.steps.forEach((s, k) => { // feedback where the answer becomes visible (feedback_step), else at the reveal itself
      const c = s.checkpoint; if (!c || (c.feedback_step || s.id) !== here.id || !revealed.has(rk(s.id))) return;
      const state = keyStates[k], pr = predicted[rk(s.id)];
      cp.append(h('div', { class: 'mm-feedback', 'data-feedback': s.id }, h('p', { class: 'mm-eyebrow' }, 'Aufgedeckt'),
        pr ? c.predict.map(q => { const ans = pr[q.id], ok = isCorrect(scene, state, q, ans);
          return h('p', { 'data-correct': String(ok) }, (ok ? '✓ ' : '✗ ') + (c.predict.length > 1 && q.short ? q.short + ': ' : '') + 'Ihre Vorhersage: ' + describe(q, ans) + ' · tatsächlich: ' + truth(q, state)); })
          : h('p', { 'data-correct': 'skipped' }, 'Ohne Vorhersage angesehen – beim nächsten Mal zuerst festlegen, dann prüfen.'),
        h('p', {}, textOf(c.explain, state))));
    });
    if (here.checkpoint && here.checkpoint.feedback_step && here.checkpoint.feedback_step !== here.id && revealed.has(rk(here.id))) {
      const at = scene.steps.findIndex(x => x.id === here.checkpoint.feedback_step) + 1;
      cp.append(h('p', { class: 'mm-note', 'data-pending': here.id }, (predicted[rk(here.id)] ? 'Vorhersage festgehalten. ' : '') + 'Die Auflösung erscheint bei Schritt ' + at + '.'));
    }
    const j = i + 1;
    if (j < N && scene.steps[j].checkpoint && !revealed.has(rk(scene.steps[j].id))) renderPredict(j);
  }
  function renderPredict(j) {
    const st = scene.steps[j], answers = {}, state = keyStates[j];
    next.disabled = true; next.textContent = 'Erst vorhersagen';
    const reveal = h('button', { type: 'button', class: 'mm-btn mm-primary', 'data-action': 'reveal', disabled: true, onclick: () => {
      revealed.add(rk(st.id)); record(scene, Object.assign({ type: 'reveal', step: st.id }, tag())); go(j); } }, 'Aufdecken');
    const commit = h('button', { type: 'button', class: 'mm-btn', 'data-action': 'commit', disabled: true, onclick: () => {
      predicted[rk(st.id)] = Object.assign({}, answers);
      for (const q of st.checkpoint.predict) record(scene, Object.assign({ type: 'predict', step: st.id, question: q.id, answer: answers[q.id], correct: isCorrect(scene, state, q, answers[q.id]) }, tag()));
      commit.disabled = true; skip.disabled = true; commit.textContent = 'Vorhersage festgehalten'; box.querySelectorAll('.mm-q button, .mm-q input').forEach(x => { x.disabled = true; });
      reveal.disabled = false; reveal.focus(); } }, 'Vorhersage festhalten');
    const skip = h('button', { type: 'button', class: 'mm-btn mm-secondary', 'data-action': 'skip', onclick: () => {
      revealed.add(rk(st.id)); record(scene, Object.assign({ type: 'reveal', step: st.id, skipped: true }, tag())); go(j); } }, 'Ohne Vorhersage ansehen');
    const ready = () => { commit.disabled = !st.checkpoint.predict.every(q => answers[q.id] !== undefined && answers[q.id] !== ''); };
    const pick = (q, group, value, btn) => { answers[q.id] = value; for (const b of group.querySelectorAll('button')) b.setAttribute('aria-pressed', String(b === btn)); ready(); };
    const box = h('div', { class: 'mm-predict', 'data-checkpoint': st.id }, h('p', { class: 'mm-eyebrow' }, 'Erst vorhersagen, dann sehen'),
      st.checkpoint.predict.map(q => {
        const group = h('div', { class: 'mm-q-options mm-q-' + q.type, role: 'group', 'aria-label': q.prompt });
        const opts = q.type === 'direction' ? ['NW', 'N', 'NE', 'W', null, 'E', 'SW', 'S', 'SE'].map(d => d ? { id: d, label: DIR_ARROW[d], aria: 'Richtung ' + d } : null)
          : q.type === 'sign' ? [{ id: '+', label: '+ positiv' }, { id: '0', label: '0 null' }, { id: '-', label: '− negativ' }]
          : q.type === 'choice' ? q.options : [];
        for (const o of opts) {
          if (!o) { group.append(h('span', { class: 'mm-q-center', 'aria-hidden': 'true' }, '·')); continue; }
          const b = h('button', { type: 'button', class: 'mm-opt', 'data-answer': o.id, 'aria-pressed': 'false', 'aria-label': o.aria || null }, o.label);
          b.addEventListener('click', () => pick(q, group, o.id, b)); group.append(b);
        }
        if (q.type === 'number') { const inp = h('input', { type: 'text', inputmode: 'decimal', class: 'mm-num', 'aria-label': q.prompt }); inp.addEventListener('input', () => { answers[q.id] = inp.value.trim(); ready(); }); group.append(inp); }
        if (q.type === 'point') {
          const ins = [0, 1].map(k => h('input', { type: 'text', inputmode: 'decimal', class: 'mm-num mm-coord', 'data-coord': String(k), 'aria-label': q.prompt + (k ? ' – zweite Koordinate' : ' – erste Koordinate') }));
          const upd = () => { const xy = ins.map(x => parseNum(x.value)); answers[q.id] = xy.every(Number.isFinite) ? xy : undefined; ready(); };
          ins.forEach(x => x.addEventListener('input', upd)); group.append('(', ins[0], ';', ins[1], ')');
        }
        return h('div', { class: 'mm-q', 'data-question': q.id }, h('p', { class: 'mm-q-prompt' }, q.prompt), group);
      }), h('div', { class: 'mm-row' }, commit, reveal, skip),
      h('p', { class: 'mm-note' }, 'Die Zeitachse bleibt bis zum Aufdecken gesperrt.'));
    cp.append(box);
  }
  // missions (V6): at most three sliders, each tied to a question; checking writes a task_attempt event
  const missionSliders = [];
  function syncMissions() { // slider start values follow the active preset / the learner's values
    for (const { m, s, inp, val } of missionSliders) {
      const raw = Object.assign(paramsAt(scene, scene.steps.findIndex(x => x.id === m.from_step), over), m.fixed || {})[s.param];
      const v = s.index === undefined ? raw : raw[s.index]; inp.value = String(v); val.textContent = fmt(v, 2);
    }
  }
  for (const m of scene.missions || []) {
    const out = h('p', { class: 'mm-mission-status', role: 'status', 'aria-live': 'polite' });
    const sliders = m.sliders.map(s => { const spec = scene.params[s.param];
      const raw = Object.assign(paramsAt(scene, scene.steps.findIndex(x => x.id === m.from_step), over), m.fixed || {})[s.param];
      const start = s.index === undefined ? raw : raw[s.index];
      const inp = h('input', { type: 'range', min: String(spec.min), max: String(spec.max), step: String(s.step || 0.01), 'data-param': s.param, 'aria-label': s.label, value: String(start) });
      const val = h('output', { class: 'mm-val' }, fmt(start, 2));
      inp.addEventListener('input', () => { if (mode !== 'mission') enterMission(m); if (s.index === undefined) missionParams[s.param] = Number(inp.value); else missionParams[s.param][s.index] = Number(inp.value); val.textContent = fmt(Number(inp.value), 2); draw(); });
      missionSliders.push({ m, s, inp, val });
      return { s, inp, val, el: h('label', { class: 'mm-slider' }, s.label + ' ', inp, val) }; });
    const hint = h('p', { class: 'mm-note', hidden: true }, m.hint);
    const box = h('section', { class: 'mm-mission', 'data-mission': m.id }, h('p', { class: 'mm-eyebrow' }, 'Eigener Auftrag'), h('p', {}, m.prompt), sliders.map(x => x.el),
      h('div', { class: 'mm-row' },
        h('button', { type: 'button', class: 'mm-btn', 'data-action': 'mission-start', onclick: () => { enterMission(m); sliders.forEach(x => { const v = x.s.index === undefined ? missionParams[x.s.param] : missionParams[x.s.param][x.s.index]; x.inp.value = String(v); x.val.textContent = fmt(v, 2); }); draw(); } }, 'Auftrag starten'),
        h('button', { type: 'button', class: 'mm-btn mm-primary', 'data-action': 'mission-check', onclick: () => {
          if (mode !== 'mission') enterMission(m); const state = evaluate(scene, missionParams), met = goalMet(state, m.goal);
          record(scene, Object.assign({ type: 'task_attempt', mission: m.id, values: Object.fromEntries(m.sliders.map(s => [s.param + (s.index === undefined ? '' : '.' + s.index), s.index === undefined ? missionParams[s.param] : missionParams[s.param][s.index]])), met }, tag()));
          out.textContent = (met ? '✓ Ziel erreicht. ' : '✗ Noch nicht. ') + (m.feedback ? textOf(m.feedback, state) : '');
          out.dataset.met = String(met); } }, 'Prüfen'),
        h('button', { type: 'button', class: 'mm-btn mm-secondary', onclick: () => { hint.hidden = !hint.hidden; } }, 'Experimentierhilfe'),
        h('button', { type: 'button', class: 'mm-btn mm-secondary', 'data-action': 'mission-leave', onclick: () => { leaveMission(); setPos(pos); } }, 'Zur Zeitachse')), hint, out);
    missionBox.append(box);
  }
  function enterMission(m) { mission = m; mode = 'mission'; const i = missionStepIndex(); missionParams = Object.assign(paramsAt(scene, i, over), clone(m.fixed || {})); root.dataset.mode = 'mission'; }
  function leaveMission() { mode = 'timeline'; mission = null; root.dataset.mode = 'timeline'; }

  // dragging a vector tip (e.g. a column of A) after the reveal: free exploration, snapped to a grid
  svg.addEventListener('pointerdown', e => { const hd = e.target.closest && e.target.closest('.mm-handle'); if (!hd || !dragAllowed()) return; drag = scene.drag[Number(hd.dataset.drag)]; svg.setPointerCapture(e.pointerId); e.preventDefault(); });
  svg.addEventListener('pointermove', e => {
    if (!drag) return;
    const r = svg.getBoundingClientRect(), sx = (e.clientX - r.left) * W / r.width, sy = (e.clientY - r.top) * H / r.height;
    const obj = scene.objects.find(o => o.id === drag.object), [s, ox, oy] = frame(panels.find(p => p.id === obj.panel)), spec = scene.params[drag.param], st = drag.step || 0.25;
    const w = [(sx - ox) / s, (oy - sy) / s].map(x => Math.max(spec.min, Math.min(spec.max, Math.round(x / st) * st)) + 0);
    const cur = paramsAt(scene, 0, over)[drag.param].slice(); if (cur[drag.indices[0]] === w[0] && cur[drag.indices[1]] === w[1]) return;
    cur[drag.indices[0]] = w[0]; cur[drag.indices[1]] = w[1]; over = Object.assign({}, over || {}, { [drag.param]: cur }); newCustomRound(true);
  });
  const release = () => { drag = null; }; svg.addEventListener('pointerup', release); svg.addEventListener('pointercancel', release);

  // light/dark: follows the page (data-theme) or the system setting; colours come from the same palette tokens
  const retheme = () => { const t = themeNow(); if (t === theme) return; theme = t; root.dataset.theme = t; paintDefs(); paintTerms(); draw(); };
  if (typeof matchMedia === 'function') { const mq = matchMedia('(prefers-color-scheme: dark)'); if (mq.addEventListener) mq.addEventListener('change', retheme); }
  if (typeof MutationObserver === 'function') new MutationObserver(retheme).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

  root.addEventListener('keydown', e => {
    const tag = (e.target.tagName || '').toLowerCase(); if (tag === 'input' || tag === 'textarea') return;
    if (e.key === 'ArrowRight' && !next.disabled) { e.preventDefault(); go(Math.floor(pos + 1e-9) + 1); }
    if (e.key === 'ArrowLeft' && !back.disabled) { e.preventDefault(); go(Math.ceil(pos - 1e-9) - 1); }
  });
  root.tabIndex = -1; root.dataset.mode = 'timeline';
  paintDefs(); paintTerms(); syncEdits(); markPresets(); drawSnaps(); setPos(0);
  return { go, setPos: p => { stop(); playing = false; setPos(p); }, loadPreset, state: () => evaluate(scene, currentParams()), get pos() { return pos; }, get theme() { return theme; } };
}
function autoMount() {
  for (const root of document.querySelectorAll('.mm-scene:not(.mm-ready)')) {
    const data = root.querySelector('script.mm-data');
    try { root._motion = mount(root, JSON.parse(data.textContent)); } catch (e) { root.dataset.error = String(e.message || e); }
  }
}
if (typeof document !== 'undefined') { if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', autoMount); else autoMount(); }
return Object.assign({ mount, autoMount, primitiveSvg, KEY, themeNow }, core);
})();
if (typeof module !== 'undefined') module.exports = MasteryMotion;
