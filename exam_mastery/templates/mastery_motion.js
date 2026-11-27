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
  const varB = ex.variance(b), varNone = ex.variance(0), varOpt = ex.variance(ex.b_opt);
  const pg = fsum(pi.map((q, j) => q * grad[j])), dpi = pi.map((q, j) => alpha * q * (grad[j] - pg));
  const trail = thetas.slice(0, whole + 1).map(t => M.softmax(t)).concat(frac > 0 ? [pi] : []);
  const lo = Math.min(...rewards), hi = Math.max(...rewards), levels = [];
  for (let i = 1; i <= 5; i++) { const level = lo + (hi - lo) * i / 6, seg = levelSegment(rewards, level); if (seg) levels.push({ level, points: seg }); }
  const bSeg = levelSegment(rewards, b);
  let argmax = 0; for (let j = 1; j < 3; j++) if (grad[j] > grad[argmax]) argmax = j;
  return {
    theta, pi, J, grad, grad_shown: grad.map(x => gVis * x), grad_norm: Math.sqrt(fsum(grad.map(x => x * x))), argmax_grad: argmax,
    b, b_opt: ex.b_opt, n, samples, actions, returns, sample_mean: mean, sample_spread: spread,
    var_b: varB, var_none: varNone, var_opt: varOpt, sd_b: Math.sqrt(Math.max(varB, 0)), sd_none: Math.sqrt(Math.max(varNone, 0)),
    var_delta: varB - varNone,
    mean_shift: Math.abs(b) * Math.sqrt(fsum([0, 1, 2].map(j => fsum(pi.map((q, a) => q * score(pi, a)[j])) ** 2))),
    dpi, pi_next: pi.map((q, j) => q + dpi[j]), pi_trail: trail, J_levels: levels, b_line: bSeg ? [{ level: b, points: bSeg }] : [],
    score_rays: [0, 1, 2].map(a => ({ points: [score(pi, a).map(x => -3 * x), score(pi, a).map(x => 3 * x)] })),
    mean_err: n ? Math.sqrt(fsum(mean.map((x, j) => (x - grad[j]) ** 2))) : 0,
    k, alpha, g_vis: gVis, lam, b0
  };
}
function linearMap2d(p) {
  const a = vec(p, 'A', 4, -10, 10), t = num(p, 't', 0, 1), v = vec(p, 'v', 2, -10, 10);
  const m = [(1 - t) + t * a[0], t * a[1], t * a[2], (1 - t) + t * a[3]], ap = (x, y) => [m[0] * x + m[1] * y, m[2] * x + m[3] * y];
  const det = m[0] * m[3] - m[1] * m[2];
  return { M: m, det, e1: ap(1, 0), e2: ap(0, 1), Av: ap(v[0], v[1]), v, square: [ap(0, 0), ap(1, 0), ap(1, 1), ap(0, 1)], t, orientation: det > 1e-12 ? 1 : det < -1e-12 ? -1 : 0 };
}
const MODELS = { softmax_simplex_pg: softmaxSimplexPg, linear_map_2d: linearMap2d };

/* ------------------------------------------------------------ evaluation, text, display list (mirror of motion/__init__.py) */
const clone = x => JSON.parse(JSON.stringify(x));
function paramsAt(scene, index) {
  const p = {}; for (const [k, v] of Object.entries(scene.params)) p[k] = clone(v.value);
  for (const st of scene.steps.slice(0, index + 1)) Object.assign(p, clone(st.set || {}));
  return p;
}
const evaluate = (scene, params) => MODELS[scene.model](params);
function get(state, ref) { if (Array.isArray(ref) || typeof ref === 'number') return ref; if (!(ref in state)) throw new Error('unknown state quantity ' + ref); return state[ref]; }
function fmt(x, d) { if (typeof x !== 'number' || !Number.isFinite(x)) return '–'; let s = x.toFixed(d); if (Number(s) === 0) s = s.replace(/^-/, ''); return s.replace(/-/g, '−').replace('.', ','); }
function textOf(tpl, state) {
  return tpl.replace(/\{([A-Za-z_][A-Za-z0-9_]*)(?:\.(\d))?(?::(\d))?\}/g, (_, name, idx, dec) => {
    let v = get(state, name); if (idx !== undefined) v = v[Number(idx)];
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
function display(scene, state) {
  const panels = Object.fromEntries(scene.view.panels.map(p => [p.id, p])), out = [];
  for (const obj of scene.objects) {
    const panel = panels[obj.panel], t = obj.token || 'ink', coords = obj.coords || 'xy', o = obj.id, sc = obj.scale === undefined ? 1 : obj.scale;
    const P = p => screen(panel, p, coords), add = (k, geo) => out.push(Object.assign({ o, k, t }, geo));
    switch (obj.type) {
      case 'simplex': {
        const c = [0, 1, 2].map(j => screen(panel, [0, 1, 2].map(a => a === j ? 1 : 0), 'tri3'));
        if (obj.style === 'axes') { const [cx, cy] = screen(panel, [0, 0], 'xy'); for (const [x, y] of c) add('line', { x1: cx, y1: cy, x2: x, y2: y }); }
        else add('poly', { pts: c.flat(), closed: true });
        c.forEach(([x, y], j) => add('text', { x, y: y + (j !== 1 ? 18 : -9), s: obj.labels[j], a: 'middle' }));
        break;
      }
      case 'point': { const [x, y] = P(get(state, obj.at)); add('mark', { x, y, r: obj.size || 6 }); if (obj.label) add('text', { x: x + 10, y: y - 10, s: textOf(obj.label, state), a: 'start' }); break; }
      case 'points': {
        const off = obj.offset !== undefined ? get(state, obj.offset) : null;
        for (const p of get(state, obj.of)) { let q = p.map(v => v * sc); if (off) q = q.map((v, j) => v + off[j]); const [x, y] = P(q); add('mark', { x, y, r: obj.size || 3 }); }
        break;
      }
      case 'vector': {
        const base = get(state, obj.from !== undefined ? obj.from : (coords === 'tri3' ? [0, 0, 0] : [0, 0]));
        const tip = obj.by !== undefined ? base.map((a, j) => a + sc * get(state, obj.by)[j]) : get(state, obj.to);
        const [x1, y1] = P(base), [x2, y2] = P(tip); add('arrow', { x1, y1, x2, y2 });
        if (obj.label) add('text', { x: x2 + 8, y: y2 - 6, s: textOf(obj.label, state), a: 'start' });
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
  if (r.rule === 'argmax') { let m = 0; for (let j = 1; j < v.length; j++) if (v[j] > v[m]) m = j; return r.map[m]; }
  if (r.rule === 'sign') { const tol = r.tol === undefined ? 1e-9 : r.tol, key = Math.abs(v) <= tol ? '0' : v > 0 ? '+' : '-'; return (r.map || { '+': '+', '-': '-', 0: '0' })[key]; }
  if (r.rule === 'index') return r.map[Math.trunc(v)];
  throw new Error('unknown answer rule ' + r.rule);
}
function isCorrect(scene, state, q, answer) {
  const want = correctAnswer(scene, state, q);
  if (q.type === 'direction') return Math.abs(((DIRS[answer] - want.deg + 180) % 360 + 360) % 360 - 180) <= want.tol_deg;
  if (q.type === 'number') return Math.abs(Number(String(answer).replace(',', '.').replace('−', '-')) - want.value) <= want.tol;
  return answer === want;
}
function goalMet(state, g) {
  const left = get(state, g.of), right = g.ref !== undefined ? get(state, g.ref) * (g.factor === undefined ? 1 : g.factor) : g.value;
  return g.op === '<=' ? left <= right : g.op === '>=' ? left >= right : Math.abs(left) <= right;
}
const ease = t => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
/* State at a real timeline position: integer = keyframe; fractional = transition into the next step (eased). Parameters
   named in transition.animate are interpolated (integers floored); all other changes apply at the start. */
function paramsAtPosition(scene, pos) {
  const i = Math.max(0, Math.min(scene.steps.length - 1, Math.floor(pos + 1e-9))), f = pos - i;
  const a = paramsAt(scene, i);
  if (f <= 1e-9 || i >= scene.steps.length - 1) return a;
  const b = paramsAt(scene, i + 1), tr = scene.steps[i + 1].transition || {}, anim = tr.animate || [], e = ease(f), out = {};
  for (const k of Object.keys(b)) {
    if (anim.includes(k) && typeof b[k] === 'number') { let v = a[k] + (b[k] - a[k]) * e; if ((scene.params[k] || {}).int) v = Math.floor(v + 1e-9); out[k] = v; }
    else if (anim.includes(k) && Array.isArray(b[k])) out[k] = b[k].map((x, j) => a[k][j] + (x - a[k][j]) * e);
    else out[k] = b[k];
  }
  return out;
}
const core = { MODELS, paramsAt, paramsAtPosition, evaluate, display, textOf, fmt, directionDeg, correctAnswer, isCorrect, goalMet, ease };

/* ------------------------------------------------------------ SVG (same primitives as motion.primitive_svg) */
const n2 = x => (Math.abs(x) >= 0.005 ? x.toFixed(2).replace(/\.?0+$/, '') : '0');
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
function markSvg(x, y, r, tok) {
  const c = tok.color;
  switch (tok.shape) {
    case 'square': return `<rect x="${n2(x - r)}" y="${n2(y - r)}" width="${n2(2 * r)}" height="${n2(2 * r)}" fill="${c}"/>`;
    case 'diamond': return `<path d="M${n2(x)} ${n2(y - r)}L${n2(x + r)} ${n2(y)}L${n2(x)} ${n2(y + r)}L${n2(x - r)} ${n2(y)}Z" fill="${c}"/>`;
    case 'triangle': return `<path d="M${n2(x)} ${n2(y - r)}L${n2(x + r)} ${n2(y + r)}L${n2(x - r)} ${n2(y + r)}Z" fill="${c}"/>`;
    case 'ring': return `<circle cx="${n2(x)}" cy="${n2(y)}" r="${n2(r)}" fill="none" stroke="${c}" stroke-width="1.2" opacity="0.7"/>`;
    default: return `<circle cx="${n2(x)}" cy="${n2(y)}" r="${n2(r)}" fill="${c}" stroke="#ffffff" stroke-width="1.5"/>`;
  }
}
function primitiveSvg(p, palette, uid) {
  const tok = palette[p.t], c = tok.color, dash = tok.dash ? ` stroke-dasharray="${tok.dash}"` : '';
  switch (p.k) {
    case 'line': return `<line x1="${n2(p.x1)}" y1="${n2(p.y1)}" x2="${n2(p.x2)}" y2="${n2(p.y2)}" stroke="${c}" stroke-width="1" opacity="0.55"${dash}/>`;
    case 'arrow': {
      const dx = p.x2 - p.x1, dy = p.y2 - p.y1, L = Math.hypot(dx, dy); if (L < 1e-6) return '';
      const ux = dx / L, uy = dy / L, h = Math.min(11, 0.45 * L), bx = p.x2 - ux * h, by = p.y2 - uy * h;
      return `<line x1="${n2(p.x1)}" y1="${n2(p.y1)}" x2="${n2(bx)}" y2="${n2(by)}" stroke="${c}" stroke-width="3" stroke-linecap="round"${dash}/>` +
        `<path d="M${n2(p.x2)} ${n2(p.y2)}L${n2(bx - uy * h * 0.45)} ${n2(by + ux * h * 0.45)}L${n2(bx + uy * h * 0.45)} ${n2(by - ux * h * 0.45)}Z" fill="${c}"/>`;
    }
    case 'mark': return markSvg(p.x, p.y, p.r, tok);
    case 'circle': return `<circle cx="${n2(p.x)}" cy="${n2(p.y)}" r="${n2(p.r)}" fill="none" stroke="${c}" stroke-width="1.5"${dash || ' stroke-dasharray="4 3"'}/>`;
    case 'poly': return `<${p.closed ? 'polygon' : 'polyline'} points="${p.pts.map(n2).join(' ')}" fill="none" stroke="${c}" stroke-width="1.6" stroke-linejoin="round"${dash}/>`;
    case 'area': return `<polygon points="${p.pts.map(n2).join(' ')}" fill="${p.neg ? 'url(#' + (uid || 'mm') + '-hatch)' : c}" fill-opacity="0.28" stroke="${c}" stroke-width="1.5"/>`;
    case 'rect': return `<rect x="${n2(p.x)}" y="${n2(p.y)}" width="${n2(p.w)}" height="${n2(p.h)}" fill="${c}" fill-opacity="0.8"/>`;
    case 'text': return `<text x="${n2(p.x)}" y="${n2(p.y)}" text-anchor="${p.a}" fill="${c}" font-size="13">${esc(p.s)}</text>`;
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

function mount(root, scene) {
  const N = scene.steps.length, pal = scene.palette, reduce = reducedMotion();
  const objPanel = Object.fromEntries(scene.objects.map(o => [o.id, o.panel]));
  const termOf = {}; for (const [tid, t] of Object.entries(scene.terms)) for (const o of t.objects) termOf[o] = tid;
  const keyStates = scene.steps.map((_, i) => evaluate(scene, paramsAt(scene, i)));
  const keyDisplays = keyStates.map(s => display(scene, s));
  const revealed = new Set(), predicted = {};
  for (const e of sceneRecord(scene).rec.events) {
    if (e.type === 'reveal') revealed.add(e.step);
    if (e.type === 'predict') (predicted[e.step] = predicted[e.step] || {})[e.question] = e.answer;
  }
  let pos = 0, anim = null, playing = false, hoverTerm = null, mode = 'timeline', mission = null, missionParams = null;
  root.classList.add('mm-ready'); root.dataset.scene = scene.id; root.dataset.reducedMotion = reduce ? '1' : '0';
  const fallback = root.querySelector('.mm-fallback'); if (fallback) fallback.hidden = true;

  // stage
  const W = scene.view.width, H = scene.view.height;
  const svg = document.createElementNS(SVGNS, 'svg');
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`); svg.setAttribute('class', 'mm-stage'); svg.setAttribute('role', 'img');
  const descId = 'mm-desc-' + scene.id; svg.setAttribute('aria-labelledby', descId);
  const uid = 'mm-' + scene.id;
  const defs = '<defs><pattern id="' + uid + '-hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="6" stroke="#8c6100" stroke-width="2"/></pattern>' +
    scene.view.panels.filter(p => p.clip).map(p => `<clipPath id="mm-clip-${scene.id}-${p.id}"><rect x="${p.x}" y="${p.y}" width="${p.w}" height="${p.h}"/></clipPath>`).join('') + '</defs>';
  const titles = scene.view.panels.filter(p => p.title).map(p => `<text x="${p.x}" y="${p.y - 8}" class="mm-panel-title">${esc(p.title)}</text>`).join('');
  svg.innerHTML = defs + `<title id="${descId}"></title>` + titles + '<g class="mm-geo"></g>';
  const geo = svg.querySelector('.mm-geo'), titleEl = svg.querySelector('title');

  // equation with term bindings
  const eq = h('p', { class: 'mm-equation', role: 'group', 'aria-label': scene.equation.label + ': ' + scene.equation.segments.map(s => s.text).join('') });
  for (const seg of scene.equation.segments) {
    const span = h('span', { class: 'mm-seg' + (seg.term ? ' mm-term' : '') });
    if (seg.svg) { span.innerHTML = seg.svg; const s = span.querySelector('svg'); if (s) s.setAttribute('aria-hidden', 'true'); span.append(h('span', { class: 'mm-sr' }, seg.text)); }
    else span.textContent = seg.text;
    if (seg.term) {
      const t = scene.terms[seg.term], tok = pal[t.token];
      span.dataset.term = seg.term; span.tabIndex = 0; span.setAttribute('role', 'button'); span.setAttribute('aria-pressed', 'false');
      span.title = t.name; span.style.color = tok.color; span.style.borderBottomStyle = tok.dash ? (tok.dash.startsWith('2') ? 'dotted' : 'dashed') : 'solid';
      const on = () => { hoverTerm = seg.term; draw(); }, off = () => { hoverTerm = null; draw(); };
      span.addEventListener('mouseenter', on); span.addEventListener('mouseleave', off); span.addEventListener('focus', on); span.addEventListener('blur', off);
      span.addEventListener('click', on);
    }
    eq.append(span);
  }
  const legend = h('ul', { class: 'mm-legend' }, Object.entries(scene.terms).map(([tid, t]) => {
    const mk = document.createElementNS(SVGNS, 'svg'); mk.setAttribute('viewBox', '0 0 16 16'); mk.setAttribute('class', 'mm-swatch'); mk.setAttribute('aria-hidden', 'true');
    mk.innerHTML = markSvg(8, 8, 5, pal[t.token]); return h('li', { 'data-term': tid }, mk, t.name);
  }));

  // caption, controls, timeline
  const counter = h('p', { class: 'mm-counter' }), stepTitle = h('h3', { class: 'mm-step-title' }), caption = h('p', { class: 'mm-caption' });
  const live = h('p', { class: 'mm-sr', 'aria-live': 'polite', role: 'status' });
  const back = h('button', { type: 'button', class: 'mm-btn', 'data-action': 'back', onclick: () => go(Math.ceil(pos - 1e-9) - 1) }, '◀ Zurück');
  const next = h('button', { type: 'button', class: 'mm-btn mm-primary', 'data-action': 'next', onclick: () => go(Math.floor(pos + 1e-9) + 1) }, 'Weiter ▶');
  const play = h('button', { type: 'button', class: 'mm-btn mm-secondary', 'data-action': 'play', onclick: () => togglePlay() }, 'Abspielen');
  if (reduce) { play.hidden = true; }
  const scrub = h('input', { type: 'range', class: 'mm-scrub', min: '0', max: String(N - 1), step: '0.01', value: '0', 'aria-label': 'Zeitachse der Szene (ziehen)', 'data-action': 'scrub' });
  scrub.addEventListener('input', () => { stop(); setPos(Math.min(Number(scrub.value), maxPos())); });
  scrub.addEventListener('change', () => { const r = Math.round(pos); if (Math.abs(r - pos) < 0.04) setPos(r); });
  const ticks = h('ol', { class: 'mm-ticks' }, scene.steps.map((st, i) => h('li', { 'data-step': st.id }, h('button', { type: 'button', class: 'mm-tick', onclick: () => go(i), 'aria-label': 'Schritt ' + (i + 1) + ': ' + st.title }, String(i + 1)))));
  const cp = h('div', { class: 'mm-checkpoint', 'aria-live': 'polite' });
  const status = h('p', { class: 'mm-store' }, 'Vorhersagen und Aufträge werden nur in diesem Browser gespeichert (em-motion-v1). Sie sind Lernhandlungen, kein Nachweis von Können, und ändern keinen Kompetenzzustand.');
  const missionBox = h('div', { class: 'mm-missions' });

  root.append(
    h('header', { class: 'mm-head' }, h('p', { class: 'mm-eyebrow' }, 'Mastery Motion · Szene'), h('h2', { class: 'mm-title' }, scene.title), h('p', { class: 'mm-claim' }, scene.claim)),
    h('div', { class: 'mm-formula' }, eq, legend),
    h('div', { class: 'mm-figure' }, svg, h('div', { class: 'mm-timeline' }, scrub, ticks), h('div', { class: 'mm-controls' }, back, next, play, counter)),
    h('div', { class: 'mm-layout' }, h('div', { class: 'mm-side' }, stepTitle, caption, cp, live), missionBox), status);

  function gate() { for (let j = 1; j < N; j++) if (scene.steps[j].checkpoint && !revealed.has(scene.steps[j].id)) return j; return -1; }
  function maxPos() { const g = gate(); return g < 0 ? N - 1 : g - 1; }
  function changedObjects(i) { // objects whose drawing differs between keyframe i and i+1 -> their terms light up
    if (i + 1 >= N) return new Set(); const a = {}, b = {};
    for (const p of keyDisplays[i]) (a[p.o] = a[p.o] || []).push(p); for (const p of keyDisplays[i + 1]) (b[p.o] = b[p.o] || []).push(p);
    const hidA = new Set(scene.steps[i].hidden || []), hidB = new Set(scene.steps[i + 1].hidden || []), out = new Set();
    for (const o of scene.objects) if (hidA.has(o.id) !== hidB.has(o.id) || JSON.stringify(a[o.id] || []) !== JSON.stringify(b[o.id] || [])) out.add(o.id);
    return out;
  }
  function currentParams() { return mode === 'mission' ? missionParams : paramsAtPosition(scene, pos); }
  function draw() {
    const params = currentParams(), state = evaluate(scene, params), prims = display(scene, state);
    const i = Math.floor(pos + 1e-9), f = pos - i, j = Math.min(N - 1, f > 1e-9 ? i + 1 : i), target = scene.steps[mode === 'mission' ? missionStepIndex() : j];
    const hidA = new Set(scene.steps[mode === 'mission' ? missionStepIndex() : i].hidden || []), hidB = new Set(target.hidden || []), e = f > 1e-9 ? ease(f) : 0;
    const focus = new Set(target.focus || []), changing = f > 1e-9 && mode !== 'mission' ? changedObjects(i) : new Set();
    const hoverObjs = new Set(hoverTerm ? scene.terms[hoverTerm].objects : []);
    const groups = {}; for (const p of prims) (groups[p.o] = groups[p.o] || []).push(p);
    const byPanel = {};
    for (const o of scene.objects) {
      const vis = (hidA.has(o.id) ? 0 : 1) * (1 - e) + (hidB.has(o.id) ? 0 : 1) * e; if (vis <= 0.001) continue;
      const dim = hoverTerm ? !hoverObjs.has(o.id) : (focus.size && !focus.has(o.id) && o.type !== 'simplex');
      const cls = 'mm-obj' + (hoverObjs.has(o.id) ? ' mm-hl' : '');
      const bucket = o.type === 'label' ? o.panel + ':labels' : o.panel; // readouts sit outside the panel clip
      (byPanel[bucket] = byPanel[bucket] || []).push(`<g class="${cls}" data-o="${o.id}" opacity="${(vis * (dim ? 0.42 : 1)).toFixed(3)}">` + (groups[o.id] || []).map(p => primitiveSvg(p, pal, uid)).join('') + '</g>');
    }
    geo.innerHTML = scene.view.panels.map(p => (p.clip ? `<g clip-path="url(#mm-clip-${scene.id}-${p.id})">${(byPanel[p.id] || []).join('')}</g>` : (byPanel[p.id] || []).join('')) + (byPanel[p.id + ':labels'] || []).join('')).join('');
    const activeTerms = new Set(); for (const o of [...focus, ...changing]) if (termOf[o]) activeTerms.add(termOf[o]); if (hoverTerm) activeTerms.add(hoverTerm);
    for (const span of eq.querySelectorAll('.mm-term')) { const on = activeTerms.has(span.dataset.term); span.classList.toggle('mm-term-on', on); span.setAttribute('aria-pressed', String(span.dataset.term === hoverTerm)); }
    for (const li of legend.children) li.classList.toggle('mm-term-on', activeTerms.has(li.dataset.term));
    titleEl.textContent = scene.title + '. ' + textOf(target.aria, state);
    root.dataset.pos = pos.toFixed(3); root.dataset.state = JSON.stringify({ n: state.n, J: state.J, pi: state.pi });
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
  function setPos(p) { pos = Math.max(0, Math.min(p, N - 1)); scrub.value = String(pos); draw(); if (Math.abs(pos - Math.round(pos)) < 1e-9) arrive(); else { cp.replaceChildren(); next.disabled = true; } }
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
    const step = () => { if (!playing) return; const i = Math.round(pos); if (i >= maxPos()) { playing = false; play.textContent = 'Abspielen'; return; } go(i + 1, () => setTimeout(step, 700)); };
    step();
  }
  function describe(q, ans, state) {
    if (q.type === 'direction') return DIR_ARROW[ans] + ' (' + ans + ')';
    if (q.type === 'choice') { const o = q.options.find(x => x.id === ans); return o ? o.label : String(ans); }
    if (q.type === 'number') return fmt(Number(String(ans).replace(',', '.').replace('−', '-')), 2);
    return { '+': 'positiv', '-': 'negativ', 0: 'null' }[ans] || String(ans);
  }
  function truth(q, state) {
    const w = correctAnswer(scene, state, q);
    if (q.type === 'direction') { const best = Object.keys(DIRS).reduce((b, k) => Math.abs(((DIRS[k] - w.deg + 180) % 360 + 360) % 360 - 180) < Math.abs(((DIRS[b] - w.deg + 180) % 360 + 360) % 360 - 180) ? k : b, 'E'); return DIR_ARROW[best] + ' (' + fmt(w.deg, 0) + '°)'; }
    if (q.type === 'number') return fmt(w.value, 2);
    return describe(q, w, state);
  }
  function renderCheckpoint(i) {
    cp.replaceChildren(); next.disabled = i >= N - 1; next.textContent = 'Weiter ▶';
    const st = scene.steps[i];
    if (st.checkpoint && revealed.has(st.id) && predicted[st.id]) { // feedback after the reveal
      const state = keyStates[i];
      cp.append(h('div', { class: 'mm-feedback', 'data-feedback': st.id }, h('p', { class: 'mm-eyebrow' }, 'Aufgedeckt'),
        st.checkpoint.predict.map(q => { const ans = predicted[st.id][q.id], ok = isCorrect(scene, state, q, ans);
          return h('p', { 'data-correct': String(ok) }, (ok ? '✓ ' : '✗ ') + 'Ihre Vorhersage: ' + describe(q, ans, state) + ' · tatsächlich: ' + truth(q, state)); }),
        h('p', {}, textOf(st.checkpoint.explain, state))));
    }
    const j = i + 1;
    if (j < N && scene.steps[j].checkpoint && !revealed.has(scene.steps[j].id)) renderPredict(j);
  }
  function renderPredict(j) {
    const st = scene.steps[j], answers = {}, state = keyStates[j];
    next.disabled = true; next.textContent = 'Erst vorhersagen';
    const reveal = h('button', { type: 'button', class: 'mm-btn mm-primary', 'data-action': 'reveal', disabled: true, onclick: () => {
      revealed.add(st.id); record(scene, { type: 'reveal', step: st.id }); go(j); } }, 'Aufdecken');
    const commit = h('button', { type: 'button', class: 'mm-btn', 'data-action': 'commit', disabled: true, onclick: () => {
      predicted[st.id] = Object.assign({}, answers);
      for (const q of st.checkpoint.predict) record(scene, { type: 'predict', step: st.id, question: q.id, answer: answers[q.id], correct: isCorrect(scene, state, q, answers[q.id]) });
      commit.disabled = true; commit.textContent = 'Vorhersage festgehalten'; box.querySelectorAll('.mm-q button, .mm-q input').forEach(x => { x.disabled = true; });
      reveal.disabled = false; reveal.focus(); } }, 'Vorhersage festhalten');
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
        return h('div', { class: 'mm-q', 'data-question': q.id }, h('p', { class: 'mm-q-prompt' }, q.prompt), group);
      }), h('div', { class: 'mm-row' }, commit, reveal),
      h('p', { class: 'mm-note' }, 'Die Zeitachse bleibt bis zum Aufdecken gesperrt.'));
    cp.append(box);
  }
  // missions (V6): at most three sliders, each tied to a question; checking writes a task_attempt event
  for (const m of scene.missions || []) {
    const out = h('p', { class: 'mm-mission-status', role: 'status', 'aria-live': 'polite' });
    const sliders = m.sliders.map(s => { const spec = scene.params[s.param];
      const start = Object.assign(paramsAt(scene, scene.steps.findIndex(x => x.id === m.from_step)), m.fixed || {})[s.param];
      const inp = h('input', { type: 'range', min: String(spec.min), max: String(spec.max), step: String(s.step || 0.01), 'data-param': s.param, 'aria-label': s.label, value: String(start) });
      const val = h('output', { class: 'mm-val' }, fmt(start, 2));
      inp.addEventListener('input', () => { if (mode !== 'mission') enterMission(m); missionParams[s.param] = Number(inp.value); val.textContent = fmt(Number(inp.value), 2); draw(); });
      return { s, inp, val, el: h('label', { class: 'mm-slider' }, s.label + ' ', inp, val) }; });
    const hint = h('p', { class: 'mm-note', hidden: true }, m.hint);
    const box = h('section', { class: 'mm-mission', 'data-mission': m.id }, h('p', { class: 'mm-eyebrow' }, 'Eigener Auftrag'), h('p', {}, m.prompt), sliders.map(x => x.el),
      h('div', { class: 'mm-row' },
        h('button', { type: 'button', class: 'mm-btn', 'data-action': 'mission-start', onclick: () => { enterMission(m); sliders.forEach(x => { x.inp.value = String(missionParams[x.s.param]); x.val.textContent = fmt(missionParams[x.s.param], 2); }); draw(); } }, 'Auftrag starten'),
        h('button', { type: 'button', class: 'mm-btn mm-primary', 'data-action': 'mission-check', onclick: () => {
          if (mode !== 'mission') enterMission(m); const state = evaluate(scene, missionParams), met = goalMet(state, m.goal);
          record(scene, { type: 'task_attempt', mission: m.id, values: Object.fromEntries(m.sliders.map(s => [s.param, missionParams[s.param]])), met });
          out.textContent = (met ? '✓ Ziel erreicht. ' : '✗ Noch nicht. ') + 'Streuung jetzt ' + fmt(Math.sqrt(state.var_b), 3) + ' (kleinstmöglich ' + fmt(Math.sqrt(state.var_opt), 3) + ' bei b = ' + fmt(state.b_opt, 2) + ').';
          out.dataset.met = String(met); } }, 'Prüfen'),
        h('button', { type: 'button', class: 'mm-btn mm-secondary', onclick: () => { hint.hidden = !hint.hidden; } }, 'Experimentierhilfe'),
        h('button', { type: 'button', class: 'mm-btn mm-secondary', 'data-action': 'mission-leave', onclick: () => { leaveMission(); setPos(pos); } }, 'Zur Zeitachse')), hint, out);
    missionBox.append(box);
  }
  function enterMission(m) { mission = m; mode = 'mission'; const i = missionStepIndex(); missionParams = Object.assign(paramsAt(scene, i), clone(m.fixed || {})); root.dataset.mode = 'mission'; }
  function leaveMission() { mode = 'timeline'; mission = null; root.dataset.mode = 'timeline'; }

  root.addEventListener('keydown', e => {
    const tag = (e.target.tagName || '').toLowerCase(); if (tag === 'input' || tag === 'textarea') return;
    if (e.key === 'ArrowRight' && !next.disabled) { e.preventDefault(); go(Math.floor(pos + 1e-9) + 1); }
    if (e.key === 'ArrowLeft' && !back.disabled) { e.preventDefault(); go(Math.ceil(pos - 1e-9) - 1); }
  });
  root.tabIndex = -1; root.dataset.mode = 'timeline';
  setPos(0);
  return { go, setPos, state: () => evaluate(scene, currentParams()), get pos() { return pos; } };
}
function autoMount() {
  for (const root of document.querySelectorAll('.mm-scene:not(.mm-ready)')) {
    const data = root.querySelector('script.mm-data');
    try { root._motion = mount(root, JSON.parse(data.textContent)); } catch (e) { root.dataset.error = String(e.message || e); }
  }
}
if (typeof document !== 'undefined') { if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', autoMount); else autoMount(); }
return Object.assign({ mount, autoMount, primitiveSvg, KEY }, core);
})();
if (typeof module !== 'undefined') module.exports = MasteryMotion;
