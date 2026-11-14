/* Exam Mastery interactive labs runtime (em-lab-v1). No dependencies, no eval, no network, text only via textContent.
   The spec is a JSON <script type="application/json" id="em-lab-spec">; expected answers in it were computed by the
   engine's Python reference models (exam_mastery/labs/models.py). The same models are implemented here (EM.models)
   and tested against Python in a real browser. */
(() => {
'use strict';
const EM = window.EM = window.EM || {};
const SVGNS = 'http://www.w3.org/2000/svg';
/* mt(): opt-in formula typesetting for labels. "V_k", "V_{k+1}", "V^π", "γ^k", "10^-3" become real sub-/superscripts
   (HTML: <sub>/<sup>; SVG: <tspan> with dy shift). Plain strings stay plain text, so ids or file names are never touched. */
const MT_RE = /([_^])(\{[^}]*\}|-?\d+|[A-Za-zα-ωΑ-Ω∞*′]+)/g;
const mt = (s) => ({ mt: String(s) });
const mtParts = (s) => { const out = []; let i = 0; for (const m of s.matchAll(MT_RE)) { if (m.index > i) out.push([0, s.slice(i, m.index)]); out.push([m[1] === '_' ? -1 : 1, m[2].replace(/^\{|\}$/g, '')]); i = m.index + m[0].length; } if (i < s.length) out.push([0, s.slice(i)]); return out; };
const fill = (e, text, svg) => {
  if (text === undefined) return;
  if (text instanceof Node) { e.appendChild(text); return; }
  if (!(text && typeof text === 'object' && 'mt' in text)) { e.textContent = String(text); return; }
  if (!svg) { for (const [k, t] of mtParts(text.mt)) e.appendChild(k ? Object.assign(document.createElement(k < 0 ? 'sub' : 'sup'), { textContent: t }) : document.createTextNode(t)); return; }
  let shift = 0; for (const [k, t] of mtParts(text.mt)) { const ts = document.createElementNS(SVGNS, 'tspan'); const want = k < 0 ? 0.3 : k > 0 ? -0.45 : 0;
    if (want !== shift) ts.setAttribute('dy', (want - shift) + 'em'); if (k) ts.setAttribute('class', 'em-mt-s'); shift = want; ts.textContent = t; e.appendChild(ts); } };
const el = (tag, attrs, text) => { const e = document.createElement(tag); for (const [k, v] of Object.entries(attrs || {})) { if (k === 'class') e.className = v; else e.setAttribute(k, v); } fill(e, text, false); return e; };
const sv = (tag, attrs, text) => { const e = document.createElementNS(SVGNS, tag); for (const [k, v] of Object.entries(attrs || {})) e.setAttribute(k, String(v)); fill(e, text, tag === 'text'); if (tag !== 'text' && text && typeof text === 'object' && 'mt' in text) e.textContent = text.mt.replace(/[{}]/g, ''); return e; };
const fmt = (x, d = 2) => { if (x === null || x === undefined || !Number.isFinite(x)) return '–'; const r = Math.round(x * 10 ** d) / 10 ** d; return (Object.is(r, -0) ? 0 : r).toLocaleString(EM_LOC, { useGrouping: EM_LOC === 'de-DE',  maximumFractionDigits: d }); };
const num = (s) => { /* German (2.144,5), English (2,144.5) and plain (2144.5 / -0,25) input */
  let t = String(s).trim().replace(/[\s\u202f\u00a0]/g, '').replace('−', '-');
  if (/^[-+]?[1-9]\d{0,2}(\.\d{3})+(,\d+)?$/.test(t)) t = t.replace(/\./g, '').replace(',', '.');
  else if (/^[-+]?[1-9]\d{0,2}(,\d{3})+(\.\d+)?$/.test(t)) t = t.replace(/,/g, '');
  else if (!/^[-+]?(\d+([.,]\d*)?|[.,]\d+)([eE][-+]?\d+)?$/.test(t)) return NaN;
  return Number(t.replace(',', '.')); };

/* ------------------------------------------------------------ models (mirror of labs/models.py) */
const models = EM.models = {
  cashflow(p) {
    const d = p.delay; if (!(Number.isInteger(d) && d >= 0)) throw new Error('Zahlungsziel muss eine ganze Zahl ≥ 0 sein');
    const T = p.horizon || Math.max(p.orders.length, p.cost.length, p.invest.length); if (!(T > 0)) throw new Error('Horizont muss positiv sein');
    const g = (xs, i) => (i >= 0 && i < xs.length ? Number(xs[i]) : 0);
    const inflow = [], outflow = [], cf = [], bal = []; let s = Number(p.start_cash || 0);
    for (let t = 0; t < T; t++) { inflow.push(g(p.orders, t - d)); outflow.push(g(p.cost, t) + g(p.invest, t)); cf.push(inflow[t] - outflow[t]); s += cf[t]; bal.push(s); }
    let k = 0; for (let t = 1; t < T; t++) if (bal[t] < bal[k]) k = t;
    const m = bal[k]; let fs = null; for (let t = 0; t < T; t++) if (bal[t] < 0) { fs = t + 1; break; }
    let unpaid = 0; for (let t = 0; t < T; t++) if (t + d >= T) unpaid += g(p.orders, t);
    return { inflow, outflow, cf, balance: bal, min_balance: m, min_period: k + 1, final_balance: bal[T - 1], financing_need: Math.max(0, -m), first_shortfall: fs, unpaid_orders: unpaid };
  },
  act: {
    sigmoid: [z => 1 / (1 + Math.exp(-z)), (z, a) => a * (1 - a)],
    tanh: [z => Math.tanh(z), (z, a) => 1 - a * a],
    relu: [z => Math.max(0, z), (z) => (z > 0 ? 1 : 0)],
    linear: [z => z, () => 1],
  },
  mlpForward(p, x, ha, oa) {
    const f = models.act[ha][0], g = models.act[oa][0];
    const z1 = p.W1.map((row, j) => row.reduce((s, w, i) => s + w * x[i], 0) + p.b1[j]);
    const a1 = z1.map(f); const zo = p.W2.reduce((s, v, j) => s + v * a1[j], 0) + p.b2;
    return { z1, a1, zo, y: g(zo) };
  },
  mlpBackward(p, x, t, ha, oa) {
    const fw = models.mlpForward(p, x, ha, oa); const dg = models.act[oa][1], df = models.act[ha][1];
    const dO = (fw.y - t) * dg(fw.zo, fw.y); const dW2 = fw.a1.map(a => dO * a);
    const dH = p.W2.map((v, j) => dO * v * df(fw.z1[j], fw.a1[j])); const dW1 = dH.map(dj => x.map(xi => dj * xi));
    return { forward: fw, loss: 0.5 * (fw.y - t) ** 2, delta_o: dO, delta_h: dH, grad: { W1: dW1, b1: dH.slice(), W2: dW2, b2: dO } };
  },
  mlpStep(p, x, t, lr, ha, oa) {
    const bw = models.mlpBackward(p, x, t, ha, oa), g = bw.grad;
    const q = { W1: p.W1.map((r, j) => r.map((w, i) => w - lr * g.W1[j][i])), b1: p.b1.map((b, j) => b - lr * g.b1[j]), W2: p.W2.map((v, j) => v - lr * g.W2[j]), b2: p.b2 - lr * g.b2 };
    return [q, bw];
  },
  riskMatrix(l, i, classes) {
    if (![l, i].every(v => Number.isInteger(v) && v >= 1 && v <= 5)) throw new Error('Stufen sind ganze Zahlen von 1 bis 5');
    return { score: l * i, class: classes[l - 1][i - 1] };
  },
  /* Van Westendorp PSM (mirror of models.van_westendorp; same knots, counting rules and crossing rule) */
  psmCross: { standard: { pmc: ['tc', 'not_cheap'], opp: ['tc', 'te'], ipp: ['cheap', 'exp'], pme: ['te', 'not_exp'] },
              alternative: { pmc: ['tc', 'exp'], opp: ['tc', 'te'], ipp: ['cheap', 'exp'], pme: ['te', 'cheap'] } },
  psmClean(rows) { const valid = [], invalid = []; rows.forEach((r, i) => { const v = ['tc', 'cheap', 'exp', 'te'].map(k => { const v=r?.[k]; return typeof v==='number' ? v : typeof v==='string' && v.trim() ? Number(v) : NaN; });
    if (v.every(x => Number.isFinite(x) && x > 0) && v[0] <= v[1] && v[1] <= v[2] && v[2] <= v[3]) valid.push({ ...r, tc: v[0], cheap: v[1], exp: v[2], te: v[3] }); else invalid.push(i + 1); }); return { valid, invalid }; },
  psmShares(rows, p) { const n = rows.length; if (!n) throw new Error('keine gültigen Antworten'); const E = 1e-9;
    const c = (k, up) => rows.filter(r => up ? r[k] >= p - E : r[k] <= p + E).length / n; const ch = c('cheap', true), ex = c('exp', false);
    return { tc: c('tc', true), cheap: ch, exp: ex, te: c('te', false), not_cheap: 1 - ch, not_exp: 1 - ex }; },
  psmCrossing(xs, ya, yb) { if (!xs.length || xs.length!==ya.length || xs.length!==yb.length || xs.some((v,i)=>i && xs[i-1]>=v)) throw Error('crossing needs nonempty, increasing aligned knots'); const d = ya.map((a, i) => a - yb[i]); const end = i => { while (i + 1 < xs.length && Math.abs(d[i + 1]) < 1e-10) i++; return i; };
    for (let i=0;i<xs.length;i++) {
      if (Math.abs(d[i])<1e-10) return (xs[i]+xs[end(i)])/2;
      if (i+1<xs.length && Math.abs(d[i+1])>=1e-10 && d[i]*d[i+1]<0) return xs[i]+(xs[i+1]-xs[i])*d[i]/(d[i]-d[i+1]);
    }
    return null; },
  vanWestendorp(rows, method = 'standard', segment = null, teShift = 0) {
    if (!Number.isFinite(teShift)) throw new Error('finite shift required');
    if (!Object.hasOwn(this.psmCross,method)) throw new Error('Konvention unbekannt');
    let sel = rows.filter(r => segment == null || segment === 'all' || r?.group === segment); if (teShift) sel = sel.map(r => ({ ...r, te: (typeof r?.te==='number' || typeof r?.te==='string' && r.te.trim()) ? Number(r.te)+teShift : NaN }));
    const { valid, invalid } = this.psmClean(sel); if (!valid.length) throw new Error('keine gültigen Antworten');
    const set = new Set([0]); valid.forEach(r => ['tc', 'cheap', 'exp', 'te'].forEach(k => set.add(r[k]))); const mx = Math.max(1, ...set); set.add(Math.ceil(mx * 1.1 / 10) * 10);
    const xs = [...set].sort((a, b) => a - b); const cur = { tc: [], cheap: [], exp: [], te: [], not_cheap: [], not_exp: [] };
    xs.forEach(p => { const q = this.psmShares(valid, p); for (const k in cur) cur[k].push(q[k]); });
    const points = {}; for (const [k, [a, b]] of Object.entries(this.psmCross[method])) points[k] = this.psmCrossing(xs, cur[a], cur[b]);
    return { n_valid: valid.length, n_invalid: invalid.length, invalid_rows: invalid, knots: xs, curves: cur, points, method, range_width: points.pme != null && points.pmc != null ? points.pme - points.pmc : null };
  },
  bands: { 1: [0, 0.05], 2: [0.05, 0.30], 3: [0.30, 0.70], 4: [0.70, 0.95], 5: [0.95, 1.0] },
  /* B16 traces for mathematical scenes (mirror of models.mlp_trace, chord_lift, rect_search, cashflow_ledger) */
  mlpTrace(p, x, t, lr, ha = 'sigmoid', oa = 'sigmoid') {
    const bw = this.mlpBackward(p, x, t, ha, oa), fw = bw.forward, g = bw.grad, df = this.act[ha][1], dg = this.act[oa][1];
    const prod = p.W1.map(row => row.map((w, i) => w * x[i]));
    const part = prod.map(row => { let s = 0; return row.map(v => (s += v)); });
    const vprod = p.W2.map((v, j) => v * fw.a1[j]);
    const [q] = this.mlpStep(p, x, t, lr, ha, oa), fa = this.mlpForward(q, x, ha, oa), la = 0.5 * (fa.y - t) ** 2;
    return { x: x.slice(), t, lr, W1: p.W1, b1: p.b1, W2: p.W2, b2: p.b2, prod, part, z1: fw.z1, a1: fw.a1, fprime: fw.z1.map((z, j) => df(z, fw.a1[j])),
      vprod, zo: fw.zo, y: fw.y, err: fw.y - t, gprime: dg(fw.zo, fw.y), loss: bw.loss, delta_o: bw.delta_o, delta_h: bw.delta_h, grad: g, new: q,
      step: { W1: q.W1.map((r, j) => r.map((w, i) => w - p.W1[j][i])), b1: q.b1.map((b, j) => b - p.b1[j]), W2: q.W2.map((v, j) => v - p.W2[j]), b2: q.b2 - p.b2 },
      after: { z1: fa.z1, a1: fa.a1, zo: fa.zo, y: fa.y, loss: la }, dloss: la - bw.loss };
  },
  curve: { r0: 1.0, terms: [[2, 0.0, 0.12], [3, 0.16, 0.0], [5, 0.0, 0.04]] },
  curvePoint(u, c) { c = c || this.curve; const th = 2 * Math.PI * u; let r = c.r0; for (const [k, a, b] of c.terms) r += a * Math.cos(k * th) + b * Math.sin(k * th); return [r * Math.cos(th), r * Math.sin(th)]; },
  curveDeriv(u, c) { c = c || this.curve; const th = 2 * Math.PI * u; let r = c.r0, dr = 0; for (const [k, a, b] of c.terms) { r += a * Math.cos(k * th) + b * Math.sin(k * th); dr += k * (-a * Math.sin(k * th) + b * Math.cos(k * th)); }
    const w = 2 * Math.PI; return [w * (dr * Math.cos(th) - r * Math.sin(th)), w * (dr * Math.sin(th) + r * Math.cos(th))]; },
  chordLift(s, t, c) { const P = this.curvePoint(s, c), Q = this.curvePoint(t, c), M = [(P[0] + Q[0]) / 2, (P[1] + Q[1]) / 2], d = Math.hypot(P[0] - Q[0], P[1] - Q[1]); return { P, Q, M, d, lift: [M[0], M[1], d] }; },
  rectResidual(s, y, c) { const [P, Q, U, V] = [s, ...y].map(z => this.curvePoint(z, c));
    return [P[0] + Q[0] - U[0] - V[0], P[1] + Q[1] - U[1] - V[1], (P[0] - Q[0]) ** 2 + (P[1] - Q[1]) ** 2 - (U[0] - V[0]) ** 2 - (U[1] - V[1]) ** 2]; },
  solve3(A, b) { const M = A.map((r, i) => [...r, b[i]]);
    for (let col = 0; col < 3; col++) { let piv = col; for (let r = col; r < 3; r++) if (Math.abs(M[r][col]) > Math.abs(M[piv][col])) piv = r;
      if (Math.abs(M[piv][col]) < 1e-14) return null; [M[col], M[piv]] = [M[piv], M[col]];
      for (let r = col + 1; r < 3; r++) { const f = M[r][col] / M[col][col]; for (let k = col; k < 4; k++) M[r][k] -= f * M[col][k]; } }
    const x = [0, 0, 0]; for (const r of [2, 1, 0]) { let s = 0; for (let k = r + 1; k < 3; k++) s += M[r][k] * x[k]; x[r] = (M[r][3] - s) / M[r][r]; } return x; },
  rectSearch(s, c, n = 6, iters = 40) {
    const mod = z => ((z % 1) + 1) % 1, P0 = this.curvePoint(s, c), sols = [], seen = new Set();
    const maxAbs = F => Math.max(...F.map(Math.abs));
    for (let a = 0; a < n; a++) for (let b = 0; b < n; b++) for (let k = 0; k < n; k++) {
      let y = [mod(s + (a + .5) / n), mod(s + (b + .25) / n), mod(s + (k + .75) / n)], ok = false;
      for (let it = 0; it < iters; it++) {
        const F = this.rectResidual(s, y, c); if (maxAbs(F) < 1e-13) { ok = true; break; }
        const [t, u, v] = y, Q = this.curvePoint(t, c), U = this.curvePoint(u, c), V = this.curvePoint(v, c), dQ = this.curveDeriv(t, c), dU = this.curveDeriv(u, c), dV = this.curveDeriv(v, c);
        const J = [[dQ[0], -dU[0], -dV[0]], [dQ[1], -dU[1], -dV[1]],
          [-2 * ((P0[0] - Q[0]) * dQ[0] + (P0[1] - Q[1]) * dQ[1]), -2 * ((U[0] - V[0]) * dU[0] + (U[1] - V[1]) * dU[1]), 2 * ((U[0] - V[0]) * dV[0] + (U[1] - V[1]) * dV[1])]];
        let st = this.solve3(J, F.map(f => -f)); if (!st) break;
        const mx = Math.max(...st.map(Math.abs)); if (mx > 0.1) st = st.map(z => z * 0.1 / mx);
        y = y.map((z, i2) => mod(z + st[i2]));
      }
      if (!ok && maxAbs(this.rectResidual(s, y, c)) >= 1e-11) continue;
      const [t, u, v] = y, cd = (z, w) => Math.min(Math.abs(z - w), 1 - Math.abs(z - w));
      if (Math.min(...[[s, t], [s, u], [s, v], [t, u], [t, v], [u, v]].map(([z, w]) => cd(z, w))) < 1e-4) continue;
      const r6 = z => Math.round(z * 1e6) / 1e6, key = [r6(Math.min(u, v)), r6(Math.max(u, v)), r6(t)].join('|'); if (seen.has(key)) continue; seen.add(key);
      const lo = Math.min(u, v), hi = Math.max(u, v), corners = [P0, this.curvePoint(lo, c), this.curvePoint(t, c), this.curvePoint(hi, c)];
      const area = Math.hypot(corners[1][0] - corners[0][0], corners[1][1] - corners[0][1]) * Math.hypot(corners[2][0] - corners[1][0], corners[2][1] - corners[1][1]);
      sols.push({ s, t, u: lo, v: hi, corners, residual: maxAbs(this.rectResidual(s, y, c)), area, key });
    }
    sols.sort((p, q) => (Math.round(q.area * 1e9) - Math.round(p.area * 1e9)) || (p.key < q.key ? -1 : p.key > q.key ? 1 : 0));
    sols.forEach(z => delete z.key); return sols;
  },
  chordTrace(s, t, c) { const L = this.chordLift(s, t, c); if (!this._rc || this._rc.s !== s || this._rc.c !== c) this._rc = { s, c, r: this.rectSearch(s, c)[0] || null }; const R = this._rc.r;
    const rect = R ? { ...R, liftPQ: this.chordLift(R.s, R.t, c).lift, liftUV: this.chordLift(R.u, R.v, c).lift, dPQ: this.chordLift(R.s, R.t, c).d, dUV: this.chordLift(R.u, R.v, c).d, MPQ: this.chordLift(R.s, R.t, c).M, MUV: this.chordLift(R.u, R.v, c).M } : null;
    return { s, t, ...L, rect }; },
  cashTrace(p) { const led = this.cashflowLedger(p), dB = p.delayB ?? p.delay + 1, b = this.cashflow({ ...p, delay: dB });
    return { ...led, delay: p.delay, delayB: dB, alt: b, diff: b.financing_need - led.financing_need, min_index: led.min_period - 1 }; },
  cashflowLedger(p) {
    const r = this.cashflow(p), T = r.cf.length, g = (xs, i) => (i >= 0 && i < xs.length ? Number(xs[i]) : 0), d = p.delay;
    const sales = []; for (let t = 0; t < T; t++) if (g(p.orders, t)) sales.push({ period: t + 1, amount: g(p.orders, t), paid_in: t + 1 + d, within: t + d < T });
    const prev = [Number(p.start_cash || 0), ...r.balance.slice(0, -1)];
    const rows = r.cf.map((cf, t) => ({ period: t + 1, prev: prev[t], inflow: r.inflow[t], cost: g(p.cost, t), invest: g(p.invest, t), cf, balance: r.balance[t], from_sale: (t - d >= 0 && g(p.orders, t - d)) ? t + 1 - d : null }));
    return { ...r, sales, rows };
  },
};

/* ------------------------------------------------------------ progress (observed attempts, this browser only) */
/* B21: finite MDPs (mirror of labs/models.py mdp_*; synchronous sweeps, terminal states = no actions, value 0) */
Object.assign(models, {
  mdpCheck(d) {
    const S = d.states.slice(); if (!S.length || new Set(S).size !== S.length) throw new Error('Zustände müssen eindeutig sein');
    const g = Number(d.gamma); if (!(g >= 0 && g < 1)) throw new Error('γ muss in [0, 1) liegen');
    const A = Object.fromEntries(S.map(s => [s, []])), T = {};
    for (const tr of d.transitions) {
      if (!(tr.s in A)) throw new Error('unbekannter Zustand ' + tr.s); if (A[tr.s].includes(tr.a)) throw new Error('Aktion doppelt: ' + tr.a);
      const nxt = {}; let sum = 0; for (const [k, v] of Object.entries(tr.next)) { const p = Number(v); if (p !== 0) { if (!(k in A) || !(p >= 0)) throw new Error('p(·|' + tr.s + ',' + tr.a + ') ungültig'); nxt[k] = p; sum += p; } }
      if (Math.abs(sum - 1) > 1e-9) throw new Error('p(·|' + tr.s + ',' + tr.a + ') summiert sich zu ' + fmt(sum, 3) + ' statt 1');
      A[tr.s].push(tr.a); T[tr.s + '\u0000' + tr.a] = [Number(tr.r), nxt];
    }
    return { states: S, actions: A, T, gamma: g };
  },
  mdpQ(m, V, s, a) { const [r, nxt] = m.T[s + '\u0000' + a]; let e = 0; for (const [t, p] of Object.entries(nxt)) e += p * V[t]; return r + m.gamma * e; },
  mdpBackupTerms(m, V, s, a) { const [r, nxt] = m.T[s + '\u0000' + a]; const terms = Object.entries(nxt).map(([t, p]) => ({ next: t, p, r, v_next: V[t], term: p * (r + m.gamma * V[t]) })); return { terms, q: terms.reduce((x, y) => x + y.term, 0) }; },
  mdpGreedy(m, V, tol = 1e-9) { const out = {}; for (const s of m.states) { const as = m.actions[s]; if (!as.length) continue; const qs = as.map(a => this.mdpQ(m, V, s, a)); const best = Math.max(...qs); out[s] = as[qs.findIndex(q => q >= best - tol)]; } return out; },
  mdpPi(m, V, s, pi) { if (!m.actions[s].length) return 0; const d = typeof pi[s] === 'object' ? pi[s] : { [pi[s]]: 1 }; let v = 0; for (const [a, w] of Object.entries(d)) v += w * this.mdpQ(m, V, s, a); return v; },
  mdpEvalSweeps(m, pi, k, V0) { let V = V0 ? { ...V0 } : Object.fromEntries(m.states.map(s => [s, 0])); const h = [{ ...V }]; for (let i = 0; i < k; i++) { const W = {}; for (const s of m.states) W[s] = this.mdpPi(m, V, s, pi); V = W; h.push({ ...V }); } return h; },
  mdpValueIteration(m, k) { let V = Object.fromEntries(m.states.map(s => [s, 0])); const h = [{ ...V }]; for (let i = 0; i < k; i++) { const W = {}; for (const s of m.states) W[s] = m.actions[s].length ? Math.max(...m.actions[s].map(a => this.mdpQ(m, V, s, a))) : 0; V = W; h.push({ ...V }); } return h; },
  mdpEvalExact(m, pi) {
    const S = m.states, n = S.length, ix = Object.fromEntries(S.map((s, i) => [s, i]));
    let A = S.map((_, i) => S.map((_, j) => (i === j ? 1 : 0))); const b = S.map(() => 0);
    for (const s of S) { if (!m.actions[s].length) continue; const d = typeof pi[s] === 'object' ? pi[s] : { [pi[s]]: 1 };
      for (const [a, w] of Object.entries(d)) { const [r, nxt] = m.T[s + '\u0000' + a]; b[ix[s]] += w * r; for (const [t, p] of Object.entries(nxt)) A[ix[s]][ix[t]] -= m.gamma * w * p; } }
    for (let c = 0; c < n; c++) { let piv = c; for (let i = c + 1; i < n; i++) if (Math.abs(A[i][c]) > Math.abs(A[piv][c])) piv = i;
      [A[c], A[piv]] = [A[piv], A[c]]; [b[c], b[piv]] = [b[piv], b[c]];
      for (let i = 0; i < n; i++) if (i !== c && A[i][c]) { const f = A[i][c] / A[c][c]; A[i] = A[i].map((x, j) => x - f * A[c][j]); b[i] -= f * b[c]; } }
    return Object.fromEntries(S.map(s => [s, b[ix[s]] / A[ix[s]][ix[s]]]));
  },
  mdpOptimal(m, tol = 1e-12, maxIter = 100000) { let V = Object.fromEntries(m.states.map(s => [s, 0]));
    for (let i = 0; i < maxIter; i++) { const W = {}; for (const s of m.states) W[s] = m.actions[s].length ? Math.max(...m.actions[s].map(a => this.mdpQ(m, V, s, a))) : 0;
      if (Math.max(...m.states.map(s => Math.abs(W[s] - V[s]))) < tol) return W; V = W; } throw new Error('Wertiteration konvergiert nicht'); },
  mdpPolicyIteration(m, pi0, maxIter = 100) { let pi = { ...pi0 }; const out = [];
    for (let i = 0; i < maxIter; i++) { const V = this.mdpEvalExact(m, pi); const Q = Object.fromEntries(m.states.map(s => [s, Object.fromEntries(m.actions[s].map(a => [a, this.mdpQ(m, V, s, a)]))]));
      out.push({ policy: { ...pi }, V, Q }); const g = this.mdpGreedy(m, V); const nw = {};
      for (const s of Object.keys(g)) nw[s] = (typeof pi[s] !== 'object' && Math.abs((Q[s][pi[s]] ?? -Infinity) - Q[s][g[s]]) <= 1e-9) ? pi[s] : g[s];
      if (Object.keys(nw).every(s => nw[s] === pi[s])) return out; pi = nw; }
    throw new Error('Policy-Iteration konvergiert nicht'); },
});

const store = EM.store = {
  key: 'em-progress-v1', ctx: '',   /* ctx: e.g. 'referenz' – keeps attempts in a reference collection apart from a course */
  read() { try { return JSON.parse(localStorage.getItem(this.key) || '{}'); } catch (e) { return {}; } },
  write(d) { try { localStorage.setItem(this.key, JSON.stringify(d)); } catch (e) { /* private mode: nothing is stored */ } },
  record(labId, taskId, kcIds, ev) {
    const d = this.read(); const k = (this.ctx ? this.ctx + '|' : '') + labId + '::' + taskId; const r = d[k] || { lab: labId, task: taskId, kc_ids: kcIds, attempts: 0, hints: 0, solution_viewed: false, correct: false, first_try: null, at: [], ...(this.ctx ? { ctx: this.ctx } : {}) };
    if (ev === 'hint') r.hints++; else if (ev === 'solution') r.solution_viewed = true;
    else if (ev === 'note') { r.notes = (r.notes || 0) + 1; }
    else { r.attempts++; if (ev === 'correct') { if (r.first_try === null) r.first_try = r.attempts === 1; r.correct = true; } }
    r.at.push([new Date().toISOString().slice(0, 16), ev]); d[k] = r; this.write(d); return r;
  },
  status(r) { /* vocabulary of the tutor protocol; never a mastery percentage */
    if (!r || !r.attempts) return r && r.solution_viewed ? 'ASSISTED' : 'NOT_ASSESSED';
    if (r.correct && !r.hints && !r.solution_viewed) return 'INDEPENDENT_PASS';
    if (r.correct) return 'ASSISTED';
    return 'INDEPENDENT_PARTIAL';
  },
  label(r) { return { INDEPENDENT_PASS: 'ohne Hilfe gelöst', ASSISTED: 'mit Hilfe gelöst', INDEPENDENT_PARTIAL: 'begonnen, noch nicht gelöst', NOT_ASSESSED: 'noch nicht bearbeitet' }[this.status(r)]; },
  taskName(t) { if (t === 'predict') return 'Vorhersage'; if (t === 'explain') return 'Eigene Erklärung'; if (t === 'summary') return 'Zusammenfassung'; if (String(t).startsWith('mission:')) return 'Erkundungsauftrag'; return 'Aufgabe'; },
};

/* v0.18 generic labs: mirrors of labs/sequence.py, attention.py, cap_table.py, legal_check.py (tested against Python) */
Object.assign(models, {
  /* safe expression language: numbers, n, a, + - * / ^, sqrt(), abs(), parentheses – parsed and interpreted, never evaluated as code */
  seqParse(src, allowA) {
    if (typeof src !== 'string' || !src.trim() || src.length > 160) throw new Error('Ausdruck fehlt oder ist zu lang');
    const s = src.trimEnd(), toks = []; const re = /\s*(?:(\d+(?:\.\d+)?)|(sqrt|abs|n|a)|([-+*/^()]))/y; let i = 0;
    while (i < s.length) { re.lastIndex = i; const m = re.exec(s); if (!m || re.lastIndex === i) throw new Error('unerlaubtes Zeichen an Position ' + (i + 1));
      toks.push(m[1] ? ['num', Number(m[1])] : m[2] ? ['id', m[2]] : ['op', m[3]]); i = re.lastIndex; }
    let p = 0; const peek = () => toks[p] || ['end', null], is = (k, v) => peek()[0] === k && peek()[1] === v;
    const take = (k, v) => { const t = peek(); if (t[0] !== k || (v !== undefined && t[1] !== v)) throw new Error('Syntaxfehler im Ausdruck'); p++; return t; };
    const expr = (d) => { if (d > 40) throw new Error('Ausdruck zu tief verschachtelt'); let x = term(d); while (is('op', '+') || is('op', '-')) { const o = take('op')[1]; x = [o, x, term(d)]; } return x; };
    const term = (d) => { let x = unary(d); while (is('op', '*') || is('op', '/')) { const o = take('op')[1]; x = [o, x, unary(d)]; } return x; };
    const unary = (d) => { if (is('op', '-')) { take('op'); return ['neg', unary(d + 1)]; } if (is('op', '+')) { take('op'); return unary(d + 1); }
      let x = atom(d); if (is('op', '^')) { take('op'); x = ['^', x, unary(d + 1)]; } return x; };
    const atom = (d) => { const t = peek();
      if (t[0] === 'num') { p++; return ['num', t[1]]; }
      if (t[0] === 'id') { p++; if (t[1] === 'sqrt' || t[1] === 'abs') { take('op', '('); const x = expr(d + 1); take('op', ')'); return [t[1], x]; }
        if (t[1] === 'a' && !allowA) throw new Error('„a“ ist nur in rekursiven Folgen erlaubt'); return ['var', t[1]]; }
      if (is('op', '(')) { take('op'); const x = expr(d + 1); take('op', ')'); return x; }
      throw new Error('Syntaxfehler im Ausdruck'); };
    const ast = expr(0); if (p !== toks.length) throw new Error('Syntaxfehler: unerwartetes Zeichen (Multiplikation bitte mit * schreiben)'); return ast;
  },
  seqEval(ast, n, a = 0) {
    const k = ast[0]; if (k === 'num') return ast[1]; if (k === 'var') return ast[1] === 'n' ? n : a; if (k === 'neg') return -this.seqEval(ast[1], n, a);
    if (k === 'sqrt') { const x = this.seqEval(ast[1], n, a); if (x < 0) throw new Error('Wurzel aus negativer Zahl bei n = ' + n); return Math.sqrt(x); }
    if (k === 'abs') return Math.abs(this.seqEval(ast[1], n, a));
    const x = this.seqEval(ast[1], n, a), y = this.seqEval(ast[2], n, a); let r;
    if (k === '+') r = x + y; else if (k === '-') r = x - y; else if (k === '*') r = x * y;
    else if (k === '/') { if (y === 0) throw new Error('Division durch 0 bei n = ' + n); r = x / y; }
    else { if (x < 0 && y !== Math.floor(y)) throw new Error('negative Basis mit nicht ganzzahligem Exponenten bei n = ' + n); if (x === 0 && y < 0) throw new Error('0 hoch negative Zahl bei n = ' + n);
      r = x ** y; if (!Number.isFinite(r)) throw new Error('Überlauf bei n = ' + n); }
    if (!Number.isFinite(r)) throw new Error('Wert nicht endlich bei n = ' + n); return r;
  },
  seqTerms(d, H) {
    H = Math.trunc(H); if (!(H >= 1 && H <= 2000)) throw new Error('Horizont muss zwischen 1 und 2000 liegen');
    if (d.rec) { const f = this.seqParse(d.rec, true); let a = Number(d.a1); if (!Number.isFinite(a)) throw new Error('a_1 ist keine Zahl'); const out = [a];
      for (let n = 1; n < H; n++) { a = this.seqEval(f, n, a); out.push(a); } return out; }
    const f = this.seqParse(d.expr, false); const out = []; for (let n = 1; n <= H; n++) out.push(this.seqEval(f, n)); return out;
  },
  seqInside(x, L, eps) { return Math.abs(x - L) < eps - 1e-12 * Math.max(1, Math.abs(L), eps); },
  seqFirstIndex(ts, L, eps, view = 'all') {
    const idx = []; for (let n = 1; n <= ts.length; n++) if (view === 'all' || ((n % 2 === 0) === (view === 'even'))) idx.push(n);
    if (!idx.length) return null; const bad = idx.filter(n => !this.seqInside(ts[n - 1], L, eps));
    const N = !bad.length ? idx[0] : idx.find(n => n > bad[bad.length - 1]); if (N === undefined || idx.filter(n => n >= N).length < Math.max(5, Math.ceil(idx.length / 10))) return null; return N;  /* min. last 10 % in the band */
  },
  seqSummary(ts) {
    const tol = 1e-12; let inc = true, dec = true;
    for (let i = 0; i + 1 < ts.length; i++) { const x = ts[i + 1] - ts[i], sc = Math.max(1, Math.abs(ts[i])); if (x < -tol * sc) inc = false; if (x > tol * sc) dec = false; }
    return { mono: inc && dec ? 'const' : inc ? 'inc' : dec ? 'dec' : 'none', min: Math.min(...ts), max: Math.max(...ts), last: ts[ts.length - 1] };
  },
  /* scaled dot-product attention */
  attMatmul(A, B) { return A.map(r => B[0].map((_, j) => r.reduce((s, x, k) => s + x * B[k][j], 0))); },
  attSoftmax(row, mask) { const keep = row.map((_, j) => !mask || mask[j]); let mx = -Infinity; row.forEach((x, j) => { if (keep[j] && x > mx) mx = x; });
    const e = row.map((x, j) => (keep[j] ? Math.exp(x - mx) : 0)); const z = e.reduce((s, x) => s + x, 0); return e.map(x => x / z); },
  attHead(X, h, causal) {
    const Q = this.attMatmul(X, h.Wq), K = this.attMatmul(X, h.Wk), V = this.attMatmul(X, h.Wv), dk = h.Wq[0].length, n = X.length;
    const KT = K[0].map((_, j) => K.map(r => r[j])); const raw = this.attMatmul(Q, KT); const S = raw.map(r => r.map(x => x / Math.sqrt(dk)));
    const A = S.map((r, i) => this.attSoftmax(r, r.map((_, j) => !causal || j <= i)));
    return { Q, K, V, raw, S, A, O: this.attMatmul(A, V), dk };
  },
  attMulti(X, heads, causal) { const hs = heads.map(h => this.attHead(X, h, causal)); return { heads: hs, concat: X.map((_, i) => hs.flatMap(h => h.O[i])) }; },
  /* cap table: rounds with option pool before/after the money, 1x non-participating preference waterfall */
  capRounds(d, mode) {
    const rnd = x => Math.floor(x + 0.5), POOL = 'Optionspool', held = {}; d.founders.forEach(f => { held[f.name] = f.shares; }); held[POOL] = 0;
    const sum = o => Object.values(o).reduce((s, x) => s + x, 0);
    const out = [{ name: 'Gründung', holders: { ...held }, total: sum(held) }];
    for (const r of d.rounds) {
      const S0 = sum(held), pm = mode || r.pool_mode, pct = r.pool_pct, post = r.pre_money + r.investment; let P, price, I;
      if (pm === 'pre') { const q = post / r.pre_money; P = rnd(pct * S0 * q / (1 - pct * q)); price = r.pre_money / (S0 + P); I = rnd(r.investment / price); }
      else { price = r.pre_money / S0; I = rnd(r.investment / price); P = rnd(pct * (S0 + I) / (1 - pct)); }
      held[POOL] += P; held[r.name] = I; const T = S0 + P + I;
      out.push({ name: r.name, price, new_pool: P, inv_shares: I, total: T, pre_money: r.pre_money, investment: r.investment, post_money: post, post_effective: price * T, mode: pm, holders: { ...held } });
    }
    for (const o of out) { o.pct = Object.fromEntries(Object.entries(o.holders).map(([k, v]) => [k, v / o.total])); o.founders_pct = d.founders.reduce((s, f) => s + o.pct[f.name], 0); }
    return out;
  },
  capWaterfall(d, last, exitValue, pref = true) {
    const H = last.holders, inv = Object.fromEntries(d.rounds.map(r => [r.name, r.investment])), E = Math.max(0, Number(exitValue)), pay = Object.fromEntries(Object.keys(H).map(k => [k, 0]));
    if (!pref) { const T = Object.values(H).reduce((s, x) => s + x, 0); return { payout: Object.fromEntries(Object.entries(H).map(([k, v]) => [k, E * v / T])), pref_taken: [] }; }
    let takers = new Set();
    for (;;) {
      let prefs = [...takers].reduce((s, k) => s + inv[k], 0);
      if (prefs >= E) { takers = new Set(Object.keys(inv)); prefs = Object.values(inv).reduce((s, x) => s + x, 0); for (const k of takers) pay[k] = E * inv[k] / prefs; for (const k of Object.keys(H)) if (!takers.has(k)) pay[k] = 0; break; }
      const rest = E - prefs, common = Object.entries(H).filter(([k]) => !takers.has(k)), T = common.reduce((s, [, v]) => s + v, 0);
      const nw = Object.keys(inv).filter(k => !takers.has(k) && rest * H[k] / T < inv[k] - 1e-9);
      if (!nw.length) { for (const k of takers) pay[k] = inv[k]; for (const [k, v] of common) pay[k] = rest * v / T; break; }
      nw.forEach(k => takers.add(k));
    }
    return { payout: pay, pref_taken: d.rounds.map(r => r.name).filter(k => takers.has(k)) };
  },
  /* Prüfungsschema */
  legalOutcome(e) { return e.decision === 'problematisch' ? e.resolution : e.decision; },
  legalResult(els) { for (let i = 0; i < els.length; i++) if (this.legalOutcome(els[i]) === 'nicht_erfuellt') return { positive: false, stop: els[i].id, checked: els.slice(0, i + 1).map(x => x.id) };
    return { positive: true, stop: null, checked: els.map(x => x.id) }; },
  legalProgress(els, committed) { const ids = els.map(e => e.id); if (committed.some((c, i) => ids[i] !== c)) throw new Error('Reihenfolge: Prüfungspunkte werden in der Reihenfolge des Schemas entschieden');
    const need = this.legalResult(els).checked; const done = committed.length >= need.length; return { next: done ? null : ids[committed.length], done }; },
  legalGrade(e, decision, reason) {
    const r = e.reasons.find(x => x.id === reason); if (!['erfuellt', 'nicht_erfuellt', 'problematisch'].includes(decision) || !r) throw new Error('Entscheidung und Begründung wählen');
    const okR = !!r.correct; if (decision === e.decision) return okR ? 'correct' : 'partial';
    if (this.legalOutcome(e) === decision || (decision === 'problematisch' && e.decision !== 'problematisch')) return okR ? 'partial' : 'wrong'; return 'wrong';
  },
});

/* ------------------------------------------------------------ shared components */
function param(container, def, value, onChange) {
  const id = 'p-' + def.id; const row = el('div', { class: 'em-param' });
  const lab = el('label', { for: id }, def.label); const out = el('output', { for: id, class: 'em-val' }, def.type === 'select' ? '' : fmt(value, def.digits ?? 2) + (def.unit ? ' ' + def.unit : ''));
  let input;
  if (def.type === 'select') { input = el('select', { id }); for (const o of def.options) { const op = el('option', { value: o.value }, o.label); if (o.value === value) op.selected = true; input.appendChild(op); } }
  else { input = el('input', { id, type: def.type === 'number' ? 'number' : 'range', min: def.min, max: def.max, step: def.step }); input.value = value; }
  const handler = () => { const v = def.type === 'select' ? input.value : (input.value.trim() === '' ? NaN : Number(input.value));  /* form controls always use a decimal point */ if (def.type !== 'select' && (!Number.isFinite(v) || v < def.min || v > def.max)) { row.classList.add('em-invalid'); out.textContent = 'ungültig (' + def.min + '…' + def.max + ')'; return; } row.classList.remove('em-invalid'); out.textContent = def.type === 'select' ? '' : fmt(v, def.digits ?? 2) + (def.unit ? ' ' + def.unit : ''); onChange(v); };
  input.addEventListener('input', handler); input.addEventListener('change', handler);
  row.append(lab, input, out); container.appendChild(row);
  return { input, set(v) { input.value = v; handler(); }, show(v) { input.value = v; row.classList.remove('em-invalid'); out.textContent = fmt(v, def.digits ?? 2) + (def.unit ? ' ' + def.unit : ''); } };
}

function chart(container, cfg) { /* bars + lines on one axis; cfg: {labels, bars:[{name,values,cls}], lines:[...], marker:{index,value,label}, unit, title} */
  const W = 640, H = 300, L = 58, R = 14, T = 18, B = 40;
  const all = [0, ...cfg.bars.flatMap(b => b.values), ...cfg.lines.flatMap(l => l.values)];
  let lo = Math.min(...all), hi = Math.max(...all); if (hi - lo < 1e-9) { hi += 1; lo -= 1; }
  const raw = (hi - lo) / 4, mag = 10 ** Math.floor(Math.log10(raw)), step = [1, 2, 2.5, 5, 10].map(f => f * mag).find(v => v >= raw);  /* round tick steps */
  lo = Math.floor(lo / step) * step; hi = Math.ceil(hi / step) * step; const ticks = Math.round((hi - lo) / step);
  const n = cfg.labels.length, bw = (W - L - R) / n, y = v => T + (hi - v) / (hi - lo) * (H - T - B), x = i => L + bw * (i + 0.5);
  const s = sv('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': cfg.title, class: 'em-chart' });
  s.appendChild(sv('title', {}, cfg.title));
  for (let k = 0; k <= ticks; k++) { const v = lo + step * k; s.appendChild(sv('line', { x1: L, x2: W - R, y1: y(v), y2: y(v), class: 'em-grid' })); s.appendChild(sv('text', { x: L - 6, y: y(v) + 4, 'text-anchor': 'end', class: 'em-tick' }, fmt(v, Math.max(0, -Math.floor(Math.log10(step)))))); }
  s.appendChild(sv('line', { x1: L, x2: W - R, y1: y(0), y2: y(0), class: 'em-zero' }));
  cfg.labels.forEach((lb, i) => s.appendChild(sv('text', { x: x(i), y: H - B + 16, 'text-anchor': 'middle', class: 'em-tick' }, lb)));
  cfg.bars.forEach((b, bi) => b.values.forEach((v, i) => { const w = bw * 0.62 / cfg.bars.length, x0 = x(i) - bw * 0.31 + bi * w; s.appendChild(sv('rect', { x: x0, y: Math.min(y(v), y(0)), width: w, height: Math.abs(y(v) - y(0)), class: b.cls + (v < 0 ? ' neg' : '') })); }));
  cfg.lines.forEach(l => { s.appendChild(sv('polyline', { points: l.values.map((v, i) => `${x(i)},${y(v)}`).join(' '), class: l.cls })); l.values.forEach((v, i) => s.appendChild(sv('circle', { cx: x(i), cy: y(v), r: 3, class: l.cls + ' dot' }))); });
  if (cfg.marker) { const m = cfg.marker; s.appendChild(sv('line', { x1: x(m.index), x2: x(m.index), y1: y(0), y2: y(m.value), class: 'em-marker' })); const right = x(m.index) > W / 2; s.appendChild(sv('text', { x: right ? x(m.index) - 8 : x(m.index) + 8, y: Math.min(y(m.value) + 16, H - B - 4), 'text-anchor': right ? 'end' : 'start', class: 'em-marker-text' }, m.label)); }
  const legend = el('div', { class: 'em-legend' }); [...cfg.bars, ...cfg.lines].forEach(it => { const sp = el('span', { class: 'em-key ' + it.cls }); legend.append(sp, document.createTextNode(it.name + '  ')); });
  container.replaceChildren(s, legend);
}

function table(container, head, rows, caption) {
  const t = el('table', { class: 'em-table' }); if (caption) t.appendChild(el('caption', {}, caption));
  const tr = el('tr'); head.forEach(h => tr.appendChild(el('th', { scope: 'col' }, h))); t.appendChild(el('thead')).appendChild(tr);
  const tb = el('tbody'); rows.forEach(r => { const row = el('tr'); r.forEach((c, i) => row.appendChild(el(i ? 'td' : 'th', i ? {} : { scope: 'row' }, c))); tb.appendChild(row); }); t.appendChild(tb);
  container.replaceChildren(t);
}

/* Prediction -> run -> explanation (POE). The prediction is locked before the result is shown. */
function predictFlow(container, spec, lab, apply) {
  const p = spec.sequence.predict; const box = el('section', { class: 'em-step em-phase', id: 'phase-predict', 'aria-labelledby': 'pred-h' });
  box.appendChild(el('h2', { id: 'pred-h' }, '1 · Vorhersagen'));
  box.appendChild(el('p', { class: 'em-why' }, 'Legen Sie sich fest, bevor Sie die Simulation sehen. Wer vorher eine Erwartung bildet, bemerkt Widersprüche – genau daran lernt man.'));
  box.appendChild(el('p', { class: 'em-question' }, mt(p.question)));
  const fs = el('fieldset'); fs.appendChild(el('legend', {}, 'Ihre Vorhersage'));
  p.options.forEach(o => { const l = el('label', { class: 'em-choice' }); const r = el('input', { type: 'radio', name: 'pred', value: o.value }); l.append(r, el('span', {}, mt(o.label))); fs.appendChild(l); });
  const conf = el('fieldset', { class: 'em-conf' }); conf.appendChild(el('legend', {}, 'Wie sicher sind Sie?'));
  [['sure', 'sicher'], ['rather', 'eher sicher'], ['guess', 'geraten']].forEach(([v, t]) => { const l = el('label', { class: 'em-pill' }); l.append(el('input', { type: 'radio', name: 'conf', value: v }), el('span', {}, t)); conf.appendChild(l); });
  const why = el('textarea', { rows: 2, 'aria-label': 'Begründung Ihrer Vorhersage', placeholder: 'Warum? Ein Satz genügt.' });
  const go = el('button', { type: 'button', class: 'em-primary' }, 'Vorhersage festlegen und Simulation öffnen');
  const fb = el('div', { class: 'em-feedback', role: 'status', 'aria-live': 'polite', tabindex: '-1' });
  go.addEventListener('click', () => {
    const v = (fs.querySelector('input[name=pred]:checked') || {}).value, c = (conf.querySelector('input[name=conf]:checked') || {}).value;
    if (!v) { fb.textContent = 'Bitte zuerst eine Vorhersage wählen.'; return; }
    if (!c) { fb.textContent = 'Bitte angeben, wie sicher Sie sind – das hilft beim Auswerten Ihrer Vorhersage.'; return; }
    if (why.value.trim().length < 3) { fb.textContent = 'Bitte begründen Sie Ihre Vorhersage kurz – erst dann öffnet sich die Simulation.'; return; }
    fs.disabled = true; conf.disabled = true; why.disabled = true; go.disabled = true;
    [].concat(p.change).forEach(apply); const ok = v === p.correct;
    store.record(spec.id, 'predict', spec.kc_ids, ok ? 'correct' : 'wrong');
    const calib = ok ? (c === 'guess' ? 'Richtig – aber geraten. Prüfen Sie gleich bei „Erklären“, ob Ihre Begründung trägt.' : 'Ihre Erwartung und Ihre Sicherheit passen zusammen.')
                     : (c === 'sure' ? 'Sie waren sich sicher und lagen falsch: Solche Überraschungen bleiben besonders gut haften, wenn Sie jetzt genau hinsehen, wo Ihr Argument kippt.' : 'Ihre Unsicherheit war berechtigt. Schauen Sie, welcher Schritt fehlte.');
    fb.replaceChildren(el('strong', { class: ok ? 'em-ok' : 'em-bad' }, ok ? 'Ihre Vorhersage trifft zu. ' : 'Ihre Vorhersage trifft nicht zu. '), el('span', {}, mt(p.result_text)), el('p', { class: 'em-calib' }, calib));
    lab.dataset.predicted = '1'; lab.dispatchEvent(new CustomEvent('em-predicted')); fb.focus();
  });
  const skip = el('button', { type: 'button', class: 'em-link' }, 'Ohne Vorhersage erkunden (für Wiederholer; wird nicht gewertet)');
  skip.addEventListener('click', () => { lab.hidden = false; skip.remove(); lab.dispatchEvent(new CustomEvent('em-opened')); });
  lab.addEventListener('em-predicted', () => { lab.hidden = false; skip.remove(); lab.dispatchEvent(new CustomEvent('em-opened')); });
  lab.hidden = true;  /* the simulation would reveal the answer; it opens after the prediction is locked */
  box.append(fs, conf, why, go, fb, skip); container.appendChild(box);
}

/* Self-explanation first, then the expert explanation and a reading aid (which key ideas the own text names). */
function explainPhase(container, spec, lab) {
  const p = spec.sequence.predict; const box = el('section', { class: 'em-step em-phase', id: 'phase-explain', 'aria-labelledby': 'exp-h' });
  box.appendChild(el('h2', { id: 'exp-h' }, '3 · Erklären'));
  const locked = el('p', { class: 'em-meta' }, 'Öffnet sich nach Ihrer Vorhersage.'); box.appendChild(locked);
  const body = el('div', { hidden: '' });
  body.appendChild(el('p', { class: 'em-why' }, 'Erst selbst erklären, dann vergleichen: Das eigene Formulieren deckt Lücken auf, die beim Lesen einer fertigen Erklärung verborgen bleiben.'));
  body.appendChild(el('p', { class: 'em-question' }, mt(p.explain_prompt || 'Erklären Sie das Ergebnis mit eigenen Worten.')));
  const ta = el('textarea', { rows: 3, 'aria-label': 'Ihre eigene Erklärung' });
  const cmp = el('button', { type: 'button', class: 'em-primary' }, 'Mit der Erklärung vergleichen');
  const give = el('button', { type: 'button', class: 'em-link' }, 'Ich komme nicht weiter – Erklärung zeigen');
  const out = el('div', { class: 'em-feedback', role: 'status', 'aria-live': 'polite' });
  const reveal = (own) => {
    cmp.disabled = true; give.remove(); ta.disabled = true;
    const head = el('p'); head.append(el('strong', {}, 'Mechanismus: '), el('span', {}, mt(p.explanation)));
    const items = [head];
    if (own && (p.explain_keys || []).length) {
      const t = ta.value.toLowerCase(); const ul = el('ul', { class: 'em-check' });
      p.explain_keys.forEach(k => { const hit = k.terms.some(w => t.includes(w.toLowerCase())); ul.appendChild(el('li', { class: hit ? 'hit' : 'miss' }, (hit ? '✓ ' : '○ ') + k.label)); });
      items.push(el('p', { class: 'em-meta' }, 'Lesehilfe (keine Bewertung): Diese Kernideen kommen in Ihrer Erklärung vor (✓) oder fehlen vielleicht (○). Ergänzen Sie gedanklich, was fehlt.'), ul);
    }
    out.replaceChildren(...items); store.record(spec.id, 'explain', spec.kc_ids, 'note'); box.dataset.done = '1'; EM.refreshPhases();
  };
  cmp.addEventListener('click', () => { if (ta.value.trim().length < 15) { out.textContent = 'Schreiben Sie zuerst ein bis zwei Sätze (mindestens 15 Zeichen).'; return; } reveal(true); });
  give.addEventListener('click', () => reveal(false));
  body.append(ta, el('div', { class: 'em-buttons' }), out); body.querySelector('.em-buttons').append(cmp, give);
  box.appendChild(body); container.appendChild(box);
  lab.addEventListener('em-opened', () => { locked.remove(); body.hidden = false; });
}

/* Exploration missions: checked live against the simulation state (data-* metrics of the lab and the current controls). */
const OPS = { '<': (a, b) => a < b, '<=': (a, b) => a <= b, '==': (a, b) => a === b, '!=': (a, b) => a !== b, '>': (a, b) => a > b, '>=': (a, b) => a >= b };
function readParam(id) { const e = document.getElementById('p-' + id); if (!e) return undefined; return e.tagName === 'SELECT' ? e.value : (e.value.trim() === '' ? undefined : Number(e.value)); }
function holds(cond, lab) {
  return cond.every(c => {
    let a = 'm' in c ? lab.dataset[c.m] : readParam(c.p); let b = 'ref' in c ? lab.dataset[c.ref] : c.v;
    if (a === undefined || a === '' || b === undefined) return false;
    const na = Number(a), nb = Number(b); if (Number.isFinite(na) && Number.isFinite(nb) && typeof c.v !== 'string') { a = na; b = nb; } else { a = String(a); b = String(b); }
    if (c.op === '==' && typeof a === 'number') return Math.abs(a - b) <= 1e-9 * Math.max(1, Math.abs(b));
    return OPS[c.op](a, b);
  });
}
function explorePhase(container, spec, lab) {
  const ms = spec.sequence.explore || []; if (!ms.length) return;
  const box = el('section', { class: 'em-step em-phase', id: 'phase-explore', 'aria-labelledby': 'xpl-h' });
  box.appendChild(el('h2', { id: 'xpl-h' }, '4 · Erkunden'));
  box.appendChild(el('p', { class: 'em-why' }, 'Gezielte Aufträge statt freiem Herumprobieren: Jeder Auftrag ist eine kleine Hypothese, die Sie mit der Simulation prüfen. Der Haken erscheint, sobald der Zustand stimmt.'));
  const live = el('p', { class: 'em-sr', role: 'status', 'aria-live': 'polite' });
  const list = el('ol', { class: 'em-missions' });
  const rows = ms.map(m => { const li = el('li', { class: 'em-mission', 'data-mission': m.id });
    const h = el('div', { class: 'em-mission-h' }); h.append(el('span', { class: 'em-mark', 'aria-hidden': 'true' }, '○'), el('strong', {}, mt(m.title))); li.append(h, el('p', {}, mt(m.prompt)));
    const hb = el('button', { type: 'button', class: 'em-link' }, 'Tipp'); const ht = el('p', { class: 'em-meta', hidden: '' }, mt(m.hint)); hb.addEventListener('click', () => { ht.hidden = false; hb.remove(); store.record(spec.id, 'mission:' + m.id, spec.kc_ids, 'hint'); });
    const ok = el('p', { class: 'em-ok em-mission-ok', hidden: '' }, '✓ ' + m.success); li.append(hb, ht, ok); list.appendChild(li); return [m, li, ok]; });
  const check = () => { rows.forEach(([m, li, ok]) => { if (li.classList.contains('done') || lab.hidden) return; if (holds(m.cond, lab)) { li.classList.add('done'); li.querySelector('.em-mark').textContent = '✓'; ok.hidden = false; live.textContent = 'Auftrag erfüllt: ' + m.title; store.record(spec.id, 'mission:' + m.id, spec.kc_ids, 'correct'); } });
    if (!box.dataset.done && rows.every(([, li]) => li.classList.contains('done'))) box.dataset.done = '1'; EM.refreshPhases(); };
  new MutationObserver(check).observe(lab, { attributes: true });
  lab.addEventListener('input', () => setTimeout(check, 0)); lab.addEventListener('change', () => setTimeout(check, 0)); lab.addEventListener('click', () => setTimeout(check, 0));
  box.append(list, live); container.appendChild(box);
}

/* Consolidation: own summary first, then the takeaways; spaced repetition happens in Anki, not here. */
function summaryPhase(container, spec) {
  const box = el('section', { class: 'em-step em-phase', id: 'phase-summary', 'aria-labelledby': 'sum-h' });
  box.appendChild(el('h2', { id: 'sum-h' }, '7 · Sichern'));
  box.appendChild(el('p', { class: 'em-question' }, mt(spec.sequence.summary_prompt || 'Fassen Sie die Kernidee in einem Satz zusammen.')));
  const ta = el('textarea', { rows: 2, 'aria-label': 'Ihre Zusammenfassung' }); const b = el('button', { type: 'button', class: 'em-primary' }, 'Mit den Kernaussagen vergleichen');
  const out = el('div', { class: 'em-feedback', role: 'status', 'aria-live': 'polite' });
  b.addEventListener('click', () => { if (ta.value.trim().length < 15) { out.textContent = 'Erst ein eigener Satz (mindestens 15 Zeichen) – dann der Vergleich.'; return; }
    ta.disabled = true; b.disabled = true; const ul = el('ul', { class: 'em-take' }); (spec.sequence.takeaways || []).forEach(t => ul.appendChild(el('li', {}, mt(t))));
    const hd = el('p'); hd.appendChild(el('strong', {}, 'Kernaussagen zum Vergleich')); out.replaceChildren(hd, ul, el('p', { class: 'em-meta' }, 'Behalten entsteht durch verteiltes Wiederholen: Die Anki-Karten dieses Kapitels fragen dieselben Ideen in Abständen wieder ab. Ein einmal gelöstes Lab ist noch kein dauerhaftes Wissen.'));
    store.record(spec.id, 'summary', spec.kc_ids, 'note'); box.dataset.done = '1'; EM.refreshPhases(); });
  box.append(ta, b, out); container.appendChild(box);
}

/* Phase navigation with observed completion (never a score). */
const PHASES = [['phase-predict', 'Vorhersagen'], ['lab-h', 'Beobachten'], ['phase-explain', 'Erklären'], ['phase-explore', 'Erkunden'], ['phase-practice', 'Üben'], ['phase-transfer', 'Übertragen'], ['phase-summary', 'Sichern']];
EM.refreshPhases = () => {
  const nav = document.querySelector('.em-phases'); if (!nav) return;
  const lab = document.querySelector('.em-lab');
  const done = { 'phase-predict': !!(lab && lab.dataset.predicted), 'lab-h': !!(lab && !lab.hidden) };
  const total = PHASES.filter(([id]) => document.getElementById(id)).length;
  for (const [id] of PHASES) { const sec = document.getElementById(id); if (sec && sec.dataset.done) done[id] = true; }
  let n = 0; nav.querySelectorAll('a').forEach(a => { const id = a.getAttribute('href').slice(1); const d = !!done[id]; a.classList.toggle('done', d); a.setAttribute('aria-label', a.dataset.label + (d ? ' (erledigt)' : '')); if (d) n++; });
  const bar = nav.querySelector('.em-bar-fill'); if (bar) bar.style.width = Math.round(100 * n / total) + '%';
  const txt = nav.querySelector('.em-phase-count'); if (txt) txt.textContent = n + ' von ' + total + ' Schritten';
};
function phaseNav(root) {
  const nav = el('nav', { class: 'em-phases', 'aria-label': 'Lernschritte' }); const ol = el('ol');
  let n = 0;
  PHASES.forEach(([id, t]) => { const sec = document.getElementById(id); if (!sec) return; n++;
    const h = sec.tagName === 'H2' ? sec : sec.querySelector('h2'); if (h) h.textContent = h.textContent.replace(/^\d+ · /, n + ' · ');   /* consecutive numbers for the blocks this lab uses */
    const li = el('li'); const a = el('a', { href: '#' + id, 'data-label': t }); a.append(el('span', { class: 'em-num' }, String(n)), el('span', {}, t)); li.appendChild(a); ol.appendChild(li); });
  const bar = el('div', { class: 'em-bar' }); bar.appendChild(el('div', { class: 'em-bar-fill' }));
  nav.append(ol, bar, el('p', { class: 'em-phase-count em-meta' }, '')); root.prepend(nav); EM.refreshPhases();
  if (window.IntersectionObserver) { const seen = new Map(); const io = new IntersectionObserver(es => { es.forEach(e => seen.set(e.target.dataset.phaseId, e.isIntersecting ? e.intersectionRatio : 0));
      let best = null, r = 0; for (const [id, v] of seen) if (v > r) { r = v; best = id; } nav.querySelectorAll('a').forEach(a => a.classList.toggle('cur', a.getAttribute('href') === '#' + best)); }, { threshold: [0, .15, .4, .7] });
    PHASES.forEach(([id]) => { let s2 = document.getElementById(id); if (s2 && s2.tagName === 'H2') s2 = s2.parentElement; if (s2) { s2.dataset.phaseId = id; io.observe(s2); } }); }
}

/* Concept item: one choice, diagnostic feedback per wrong option (misconception), explanation after the right answer. */
function choiceTask(container, spec, t, label) {
  const box = el('section', { class: 'em-step em-task', 'data-task': t.id, 'aria-labelledby': 'h-' + t.id });
  box.appendChild(el('h3', { id: 'h-' + t.id }, label + (t.title || 'Konzeptfrage')));
  box.appendChild(el('p', {}, mt(t.prompt)));
  const fs = el('fieldset'); fs.appendChild(el('legend', { class: 'em-sr' }, 'Antwort wählen'));
  t.options.forEach(o => { const l = el('label', { class: 'em-choice' }); l.append(el('input', { type: 'radio', name: 'c-' + t.id, value: o.value }), el('span', {}, mt(o.label))); fs.appendChild(l); });
  const check = el('button', { type: 'button', class: 'em-primary' }, 'Prüfen'); const fb = el('div', { class: 'em-feedback', role: 'status', 'aria-live': 'polite' });
  check.addEventListener('click', () => { const v = (fs.querySelector('input:checked') || {}).value; if (!v) { fb.textContent = 'Bitte eine Antwort wählen.'; return; }
    if (v === t.correct) { fb.replaceChildren(el('strong', { class: 'em-ok' }, 'Richtig. '), el('span', {}, mt(t.explanation || ''))); store.record(spec.id, t.id, spec.kc_ids, 'correct'); box.dataset.done = '1'; fs.disabled = true; check.disabled = true; EM.refreshPhases(); return; }
    const o = t.options.find(x => x.value === v); store.record(spec.id, t.id, spec.kc_ids, 'wrong');
    fb.replaceChildren(el('strong', { class: 'em-bad' }, 'Noch nicht. '), el('span', {}, mt(o.feedback || '')), el('p', { class: 'em-meta' }, 'Wählen Sie neu – die Rückmeldung bezieht sich auf die gewählte Antwort.')); });
  box.append(fs, check, fb); container.appendChild(box);
}

/* Task with numeric answer, tolerance, typical-error diagnosis, hint ladder, solution only on request after an attempt. */
function task(container, spec, t, label) {
  const box = el('section', { class: 'em-step em-task', 'data-task': t.id, 'aria-labelledby': 'h-' + t.id });
  box.appendChild(el('h3', { id: 'h-' + t.id }, (label || '') + (t.title || 'Aufgabe')));
  box.appendChild(el('p', {}, mt(t.prompt)));
  const row = el('div', { class: 'em-answer' }); const inp = el('input', { type: 'text', inputmode: 'decimal', 'aria-label': 'Ihre Antwort' + (t.unit ? ' in ' + t.unit : '') });
  const check = el('button', { type: 'button', class: 'em-primary' }, 'Prüfen'); row.append(inp, el('span', {}, t.unit || ''), check);
  const fb = el('div', { class: 'em-feedback', role: 'status', 'aria-live': 'polite' });
  const hints = el('ol', { class: 'em-hints' }); let shown = 0;
  const hintBtn = el('button', { type: 'button' }, 'Hinweis (' + t.hints.length + ' Stufen)');
  const solBtn = el('button', { type: 'button', disabled: '' }, 'Lösung zeigen'); const sol = el('div', { class: 'em-solution', hidden: '' });
  t.solution.forEach(s => sol.appendChild(el('p', {}, mt(s))));
  hintBtn.addEventListener('click', () => { if (shown < t.hints.length) { hints.appendChild(el('li', {}, mt(t.hints[shown++]))); store.record(spec.id, t.id, spec.kc_ids, 'hint'); } if (shown >= t.hints.length) hintBtn.disabled = true; });
  solBtn.addEventListener('click', () => { sol.hidden = false; store.record(spec.id, t.id, spec.kc_ids, 'solution'); });
  check.addEventListener('click', () => {
    const v = num(inp.value);
    if (!Number.isFinite(v)) { fb.textContent = 'Bitte eine Zahl eingeben (z. B. 2144 oder -0,25).'; return; }
    solBtn.disabled = false;
    const ok = Math.abs(v - t.expected) <= t.tolerance;
    if (ok) { fb.replaceChildren(el('strong', { class: 'em-ok' }, 'Richtig. '), el('span', {}, mt(t.feedback_correct || ''))); store.record(spec.id, t.id, spec.kc_ids, 'correct'); box.dataset.done = '1'; EM.refreshPhases(); return; }
    store.record(spec.id, t.id, spec.kc_ids, 'wrong');
    const hit = (t.errors || []).find(e => Math.abs(v - e.value) <= t.tolerance);
    const sign = Math.sign(v) !== Math.sign(t.expected) && Math.abs(Math.abs(v) - Math.abs(t.expected)) <= t.tolerance;
    fb.replaceChildren(el('strong', { class: 'em-bad' }, 'Noch nicht richtig. '), el('span', {}, mt(hit ? hit.message : sign ? 'Der Betrag stimmt, das Vorzeichen nicht – prüfen Sie, was positiv und was negativ gezählt wird.' : 'Prüfen Sie Ihren Rechenweg; die Hinweise führen schrittweise weiter.')));
  });
  inp.addEventListener('keydown', e => { if (e.key === 'Enter') check.click(); });
  box.append(row, fb, el('div', { class: 'em-buttons' }, undefined), hints, sol); box.querySelector('.em-buttons').append(hintBtn, solBtn);
  container.appendChild(box);
}

/* collapsible tool panel under the scene (progressive disclosure) */
function tool(title, note, open, ...children) {
  const d = el('details', { class: 'em-tool' }); if (open) d.open = true;
  const s = el('summary'); s.append(document.createTextNode(title)); if (note) s.append(el('small', {}, mt(note)));
  const b = el('div', { class: 'em-tool-body' }); b.append(...children.filter(Boolean)); d.append(s, b); return d;
}
const tools = (...ts) => { const w = el('div', { class: 'em-tools' }); w.append(...ts.filter(Boolean)); return w; };

/* ------------------------------------------------------------ lab views */
const views = {};
/* B16: mathematical scene of a lab (spec.scene) with its generic renderer; null when the lab has none */
function scenePlayer(host, spec, type, trace, ctx) {
  if (!spec.scene || !EM.scene || !EM.scene.types[type]) return null;
  const box = el('div', { class: 'em-scene-host' }); host.appendChild(box);
  const vars = Object.fromEntries(Object.entries(spec.scene.vars || {}).map(([k, v]) => [k, v.default]));
  const pl = EM.scene.player(box, { scene: spec.scene, renderer: EM.scene.types[type](), vars, trace, ctx });
  if (spec.scene.status === 'exploration') box.appendChild(el('p', { class: 'em-proofnote' }, 'Numerische Exploration: Die Darstellung zeigt berechnete Beispiele mit Gleitkomma-Restfehler. Sie ist kein Beweis.'));
  EM.scene.didactics(box, spec.scene);
  return pl;
}

views.cashflow = (root, spec) => {
  let player = null;
  const m = spec.model, st = { delay: m.delay, start_cash: m.start_cash || 0, horizon: m.orders.length, delayB: m.delay + 1, orders: m.orders.slice(), cost: m.cost.slice(), invest: m.invest.slice() };
  const ext = (xs, T, fill) => { const r = xs.slice(0, T); while (r.length < T) r.push(fill(r)); return r; };
  const series = () => ({ orders: ext(st.orders, st.horizon, r => r.length ? r[r.length - 1] : 0), cost: ext(st.cost, st.horizon, r => r.length ? r[r.length - 1] : 0), invest: ext(st.invest, st.horizon, () => 0) });
  const lab = el('section', { class: 'em-lab', 'aria-labelledby': 'lab-h' }); lab.appendChild(el('h2', { id: 'lab-h' }, '2 · Simulation'));
  const pan = el('div', { class: 'em-params' }), chartBox = el('div', { class: 'em-figure' }), kpi = el('div', { class: 'em-kpi', role: 'status', 'aria-live': 'polite' }), timeline = el('p', { class: 'em-timeline' }), tab = el('div', { class: 'em-scroll' });
  const ctrls = {};
  const redraw = () => {
    const s = series(); let a, b;
    try { a = models.cashflow({ ...s, delay: st.delay, start_cash: st.start_cash, horizon: st.horizon }); b = models.cashflow({ ...s, delay: st.delayB, start_cash: st.start_cash, horizon: st.horizon }); }
    catch (e) { kpi.textContent = 'Eingabe ungültig: ' + e.message; return; }
    lab.dataset.need = a.financing_need; lab.dataset.minPeriod = a.min_period; lab.dataset.final = a.final_balance; lab.dataset.needB = b.financing_need;
    chart(chartBox, { title: 'Cashflow je Periode und kumulierte Liquidität (k€)', labels: a.cf.map((_, i) => 'P' + (i + 1)), unit: 'k€',
      bars: [{ name: 'Cashflow je Periode (Szenario A)', values: a.cf, cls: 'em-bar' }],  /* A = baseline, B = changed payment delay */
      lines: [{ name: 'Kumulierte Liquidität A (Zahlungsziel ' + st.delay + ')', values: a.balance, cls: 'em-line-a' }, { name: 'Kumulierte Liquidität B (Zahlungsziel ' + st.delayB + ')', values: b.balance, cls: 'em-line-b' }],
      marker: a.financing_need > 0 ? { index: a.min_period - 1, value: a.min_balance, label: 'Finanzierungsbedarf A: ' + fmt(a.financing_need, 0) + ' k€' } : null });
    kpi.replaceChildren(...[['Finanzierungsbedarf A', fmt(a.financing_need, 0) + ' k€'], ['tiefster Stand A in Periode', String(a.min_period)], ['Endsaldo A', fmt(a.final_balance, 0) + ' k€'], ['erster Engpass A', a.first_shortfall ? 'Periode ' + a.first_shortfall : 'keiner'], ['Finanzierungsbedarf B', fmt(b.financing_need, 0) + ' k€'], ['offene Forderungen A am Ende', fmt(a.unpaid_orders, 0) + ' k€']].map(([k, v]) => { const d = el('div'); d.append(el('span', {}, k), el('strong', {}, v)); return d; }));
    timeline.textContent = 'Zahlungsverzögerung A: ' + s.orders.map((o, i) => o ? 'Auftrag P' + (i + 1) + ' → Zahlung P' + (i + 1 + st.delay) + (i + st.delay >= st.horizon ? ' (nach Horizont)' : '') : '').filter(Boolean).slice(0, 4).join(' · ') + (s.orders.filter(Boolean).length > 4 ? ' · …' : '');
    if (player) player.refresh();
    table(tab, ['Periode', ...a.cf.map((_, i) => String(i + 1))], [['Zahlungseingang', ...a.inflow.map(v => fmt(v, 0))], ['Auszahlungen', ...a.outflow.map(v => fmt(v, 0))], ['Cashflow', ...a.cf.map(v => fmt(v, 0))], ['kumuliert', ...a.balance.map(v => fmt(v, 0))]], 'Szenario A, Werte in k€');
  };
  for (const def of spec.params) ctrls[def.id] = param(pan, def, st[def.id], v => { st[def.id] = v; redraw(); });
  const reset = el('button', { type: 'button' }, 'Zurücksetzen'); reset.addEventListener('click', () => { for (const def of spec.params) ctrls[def.id].set(def.default); });
  const edit = el('details', { class: 'em-edit' }); edit.appendChild(el('summary', {}, 'Zahlenreihen bearbeiten (Aufträge, Kosten, Investitionen)'));
  const grid = el('div', { class: 'em-scroll' }); edit.appendChild(grid);
  const buildGrid = () => { const t = el('table', { class: 'em-table em-input-table' }); const head = el('tr'); head.appendChild(el('th', {}, 'Periode')); const s = series(); s.orders.forEach((_, i) => head.appendChild(el('th', { scope: 'col' }, String(i + 1)))); t.appendChild(head);
    for (const [key, label] of [['orders', 'Aufträge'], ['cost', 'laufende Kosten'], ['invest', 'Investitionen']]) { const tr = el('tr'); tr.appendChild(el('th', { scope: 'row' }, label)); s[key].forEach((v, i) => { const td = el('td'); const inp = el('input', { type: 'number', step: '1', 'aria-label': label + ' Periode ' + (i + 1) }); inp.value = v; inp.addEventListener('change', () => { const x = num(inp.value); if (!Number.isFinite(x) || x < 0) { inp.classList.add('em-invalid'); return; } inp.classList.remove('em-invalid'); st[key] = series()[key]; st[key][i] = x; redraw(); }); td.appendChild(inp); tr.appendChild(td); }); t.appendChild(tr); }
    grid.replaceChildren(t); };
  edit.addEventListener('toggle', buildGrid);
  const sceneHost = el('div');
  const btns = el('div', { class: 'em-buttons' }); btns.appendChild(reset);
  lab.append(sceneHost, kpi, tools(tool('Parameter', 'Zahlungsziel, Anfangsliquidität, Horizont', true, pan, btns, edit), tool('Diagramm und Zahlentabelle', 'Szenario A und B im Vergleich', false, chartBox, timeline, tab)));
  root.appendChild(lab);
  player = scenePlayer(sceneHost, spec, 'cashflow', () => models.cashTrace({ ...series(), delay: st.delay, delayB: st.delayB, start_cash: st.start_cash, horizon: st.horizon }), { unit: m.unit || 'k€' });
  predictFlow(root.querySelector('.em-pre'), spec, lab, ch => ctrls[ch.param].set(ch.to));
  redraw();
};

views.mlp = (root, spec) => {
  let player = null, guided = null;
  const m = spec.model; const init = JSON.parse(JSON.stringify(m.init));
  const st = { p: JSON.parse(JSON.stringify(init)), x: m.x.slice(), t: m.target, lr: m.lr, ha: m.hidden_act, oa: m.out_act, losses: [] };
  const lab = el('section', { class: 'em-lab', 'aria-labelledby': 'lab-h' }); lab.appendChild(el('h2', { id: 'lab-h' }, '2 · Netz untersuchen'));
  const pan = el('div', { class: 'em-params' }), net = el('div', { class: 'em-figure' }), eqs = el('div', { class: 'em-eqs', role: 'status', 'aria-live': 'polite' }), grads = el('div', { class: 'em-scroll' }), lossBox = el('div', { class: 'em-figure' }), warn = el('p', { class: 'em-warn' });
  const ctrls = {};
  const flat = () => [['w11', st.p.W1[0][0]], ['w12', st.p.W1[0][1]], ['w21', st.p.W1[1][0]], ['w22', st.p.W1[1][1]], ['b1', st.p.b1[0]], ['b2', st.p.b1[1]], ['v1', st.p.W2[0]], ['v2', st.p.W2[1]], ['c', st.p.b2]];
  const setP = (k, v) => { const map = { w11: ['W1', 0, 0], w12: ['W1', 0, 1], w21: ['W1', 1, 0], w22: ['W1', 1, 1], b1: ['b1', 0], b2: ['b1', 1], v1: ['W2', 0], v2: ['W2', 1] }; if (k === 'c') st.p.b2 = v; else { const [a, i, j] = map[k]; if (j === undefined) st.p[a][i] = v; else st.p[a][i][j] = v; } };
  const EDGE = { w11: 'x1-h1', w12: 'x2-h1', w21: 'x1-h2', w22: 'x2-h2', v1: 'h1-o', v2: 'h2-o' }, NODE = { b1: 'h1', b2: 'h2', c: 'o' };
  const drawNet = (fw, target, fk) => {
    const s = sv('svg', { viewBox: '0 0 520 260', role: 'img', 'aria-label': 'Netzarchitektur 2-2-1 mit aktuellen Werten' + (fk ? '; hervorgehoben: ' + fk : ''), class: 'em-net' + (fk ? ' em-net-focus' : '') }); s.appendChild(sv('title', {}, 'Netzarchitektur 2-2-1'));
    const P = { x1: [60, 70], x2: [60, 190], h1: [260, 70], h2: [260, 190], o: [450, 130] };
    const edge = (a, b, w, lbl, ly) => { const [x1, y1] = P[a], [x2, y2] = P[b]; const on = fk && EDGE[fk] === a + '-' + b; s.appendChild(sv('line', { x1, y1, x2, y2, class: 'em-edge ' + (w >= 0 ? 'pos' : 'neg') + (on ? ' em-on' : fk ? ' em-dim' : ''), 'stroke-width': on ? 6 : 1 + Math.min(6, Math.abs(w) * 3) })); s.appendChild(sv('text', { x: x1 + (x2 - x1) * 0.3, y: y1 + (y2 - y1) * 0.3 + ly, class: 'em-edge-label' + (fk && !on ? ' em-dim' : ''), 'text-anchor': 'middle' }, lbl + '=' + fmt(w, 3))); };  /* near the source: crossing edges keep apart */
    edge('x1', 'h1', st.p.W1[0][0], 'w11', -6); edge('x2', 'h1', st.p.W1[0][1], 'w12', -6); edge('x1', 'h2', st.p.W1[1][0], 'w21', 14); edge('x2', 'h2', st.p.W1[1][1], 'w22', 14); edge('h1', 'o', st.p.W2[0], 'v1', -6); edge('h2', 'o', st.p.W2[1], 'v2', 14);
    const node = (k, top, bot) => { const [x, y] = P[k]; const on = fk && (NODE[fk] === k || (EDGE[fk] || '').split('-').includes(k)); s.appendChild(sv('circle', { cx: x, cy: y, r: 30, class: 'em-node' + (on ? ' em-on' : '') })); s.appendChild(sv('text', { x, y: y - 3, 'text-anchor': 'middle', class: 'em-node-t' }, top)); s.appendChild(sv('text', { x, y: y + 13, 'text-anchor': 'middle', class: 'em-node-s' }, bot)); };
    node('x1', 'x₁', fmt(st.x[0], 2)); node('x2', 'x₂', fmt(st.x[1], 2)); node('h1', 'a₁', fmt(fw.a1[0], 3)); node('h2', 'a₂', fmt(fw.a1[1], 3)); node('o', 'ŷ', fmt(fw.y, 3));
    (target || net).replaceChildren(s);
  };
  const redraw = () => {
    const bw = models.mlpBackward(st.p, st.x, st.t, st.ha, st.oa), fw = bw.forward, g = bw.grad;
    lab.dataset.loss = bw.loss; lab.dataset.y = fw.y; lab.dataset.gradB2 = g.b2;
    drawNet(fw); if (player) player.refresh(); if (guided) guided.refresh(bw);
    const L = [
      ['Vorwärts, verdeckte Schicht', `z₁ = w11·x₁ + w12·x₂ + b1 = ${fmt(st.p.W1[0][0], 3)}·${fmt(st.x[0], 2)} + ${fmt(st.p.W1[0][1], 3)}·${fmt(st.x[1], 2)} + ${fmt(st.p.b1[0], 3)} = ${fmt(fw.z1[0], 4)};  a₁ = ${st.ha}(z₁) = ${fmt(fw.a1[0], 4)}`],
      ['', `z₂ = w21·x₁ + w22·x₂ + b2 = ${fmt(fw.z1[1], 4)};  a₂ = ${st.ha}(z₂) = ${fmt(fw.a1[1], 4)}`],
      ['Vorwärts, Ausgabe', `z_o = v1·a₁ + v2·a₂ + c = ${fmt(fw.zo, 4)};  ŷ = ${st.oa}(z_o) = ${fmt(fw.y, 4)}`],
      ['Verlust', `L = ½(ŷ − t)² = ½(${fmt(fw.y, 4)} − ${fmt(st.t, 2)})² = ${fmt(bw.loss, 6)}`],
      ['Rückwärts, Ausgabe', `δ_o = (ŷ − t)·g′(z_o) = ${fmt(bw.delta_o, 6)}`],
      ['Rückwärts, verdeckt', `δ₁ = δ_o·v1·f′(z₁) = ${fmt(bw.delta_h[0], 6)};  δ₂ = δ_o·v2·f′(z₂) = ${fmt(bw.delta_h[1], 6)}`],
    ];
    eqs.replaceChildren(...L.map(([h, t]) => { const p = el('p'); if (h) p.appendChild(el('span', { class: 'em-eq-h' }, h + ': ')); p.appendChild(el('code', {}, t)); return p; }));
    const gl = [['w11', g.W1[0][0]], ['w12', g.W1[0][1]], ['w21', g.W1[1][0]], ['w22', g.W1[1][1]], ['b1', g.b1[0]], ['b2', g.b1[1]], ['v1', g.W2[0]], ['v2', g.W2[1]], ['c', g.b2]];
    const cur = Object.fromEntries(flat());
    const fd = (k) => { const e = 1e-6, set = (q, v) => { const m2 = { w11: ['W1', 0, 0], w12: ['W1', 0, 1], w21: ['W1', 1, 0], w22: ['W1', 1, 1], b1: ['b1', 0], b2: ['b1', 1], v1: ['W2', 0], v2: ['W2', 1] }; if (k === 'c') q.b2 = v; else { const [a, i, j] = m2[k]; if (j === undefined) q[a][i] = v; else q[a][i][j] = v; } };
      const qa = JSON.parse(JSON.stringify(st.p)), qb = JSON.parse(JSON.stringify(st.p)); set(qa, cur[k] + e); set(qb, cur[k] - e);
      return (models.mlpBackward(qa, st.x, st.t, st.ha, st.oa).loss - models.mlpBackward(qb, st.x, st.t, st.ha, st.oa).loss) / (2 * e); };
    let maxdev = 0; const rowsG = gl.map(([k, d]) => { const n = fd(k); maxdev = Math.max(maxdev, Math.abs(n - d)); return [k, fmt(cur[k], 4), fmt(d, 6), fmt(n, 6), fmt(cur[k] - st.lr * d, 4)]; });
    table(grads, ['Parameter', 'Wert θ', '∂L/∂θ (Kettenregel)', 'Prüfung: finite Differenz', 'nach Schritt θ − η·∂L/∂θ'], rowsG, 'Gradienten mit Kettenregel, numerisch geprüft (größte Abweichung ' + maxdev.toExponential(1).replace('.', EM_LOC === 'de-DE' ? ',' : '.') + '); Update mit η = ' + fmt(st.lr, 3));
    lab.dataset.fdMaxDev = maxdev;
    const sat = fw.z1.map((z, j) => (st.ha === 'sigmoid' || st.ha === 'tanh') && Math.abs(z) > 4 ? 'a' + (j + 1) : null).filter(Boolean);
    warn.textContent = sat.length ? 'Sättigung bei ' + sat.join(', ') + ': |z| > 4, die Ableitung der Aktivierung ist fast 0 – die Gradienten der zugehörigen Gewichte verschwinden nahezu.' : '';
    const hist = st.losses.concat([bw.loss]);
    chart(lossBox, { title: 'Verlust über die Lernschritte', labels: hist.map((_, i) => String(i)), bars: [], lines: [{ name: 'Verlust L', values: hist, cls: 'em-line-a' }] });
  };
  const defs = spec.params; for (const def of defs) { const get = def.id.startsWith('x') ? st.x[+def.id[1] - 1] : def.id === 't' ? st.t : def.id === 'lr' ? st.lr : def.id === 'ha' ? st.ha : def.id === 'oa' ? st.oa : Object.fromEntries(flat())[def.id];
    ctrls[def.id] = param(pan, def, get, v => { if (def.id === 'x1' || def.id === 'x2') st.x[+def.id[1] - 1] = v; else if (def.id === 't') st.t = v; else if (def.id === 'lr') st.lr = v; else if (def.id === 'ha') st.ha = v; else if (def.id === 'oa') st.oa = v; else setP(def.id, v); redraw(); }); }
  const syncCtrls = () => { for (const [k, v] of flat()) if (ctrls[k]) ctrls[k].show(Math.round(v * 1000) / 1000); };  /* display only: the model keeps full precision */
  const step = () => { const [q, bw] = models.mlpStep(st.p, st.x, st.t, st.lr, st.ha, st.oa); st.losses.push(bw.loss); st.p = q; syncCtrls(); redraw(); lab.dataset.lastDelta = Number(lab.dataset.loss) - bw.loss; lab.dataset.steps = st.losses.length; };
  let timer = null;
  const bStep = el('button', { type: 'button', class: 'em-primary' }, 'Einen Lernschritt ausführen'), bAuto = el('button', { type: 'button' }, 'Automatisch (20 Schritte)'), bReset = el('button', { type: 'button' }, 'Zurücksetzen');
  bStep.addEventListener('click', step);
  bAuto.addEventListener('click', () => { if (timer) return; let k = 0; bAuto.disabled = true; timer = setInterval(() => { step(); if (++k >= 20) { clearInterval(timer); timer = null; bAuto.disabled = false; } }, 120); });
  bReset.addEventListener('click', () => { if (timer) { clearInterval(timer); timer = null; bAuto.disabled = false; } st.p = JSON.parse(JSON.stringify(init)); st.losses = []; for (const def of defs) ctrls[def.id].set(def.default); delete lab.dataset.steps; redraw(); });
  const buttons = el('div', { class: 'em-buttons' }); buttons.append(bStep, bAuto, bReset);
  const sceneHost = el('div'); const all = tool('Alle Gleichungen und Gradienten', 'neun Parameter auf einen Blick', !spec.scene, spec.scene ? null : net, eqs, grads); all.classList.add('em-alleq');
  lab.append(sceneHost, tools(tool('Lernschritte und Parameter', 'Gewichte, Eingaben, Lernrate, Aktivierung', true, buttons, warn, pan), tool('Verlust über die Lernschritte', '', false, lossBox), all)); root.appendChild(lab);
  const clampSet = (k, v) => { const d = defs.find(x => x.id === k); if (d) ctrls[k].set(Math.max(d.min, Math.min(d.max, v))); };
  player = scenePlayer(sceneHost, spec, 'network', () => models.mlpTrace(st.p, st.x, st.t, st.lr, st.ha, st.oa), { setParam: clampSet, acts: () => ({ ha: st.ha, oa: st.oa }) });
  if (player) all.open = false; else all.open = true;
  /* v0.18 Guided / Explore: two views of the same model. Guided shows one parameter with its connection, term, value,
     gradient and effect on the loss; Explore shows the full parameter matrix and all equations. */
  const h = (tag, attrs, ...kids) => { const e = el(tag, attrs); for (const c of kids) if (c !== null && c !== undefined) e.append(c instanceof Node ? c : String(c)); return e; };
  const q = (() => { try { return new URLSearchParams(location.search); } catch (e) { return new URLSearchParams(''); } })();
  const SYM = { w11: 'w₁₁', w12: 'w₁₂', w21: 'w₂₁', w22: 'w₂₂', b1: 'b₁', b2: 'b₂', v1: 'v₁', v2: 'v₂', c: 'c' };
  const dAct = (name, z, a) => name === 'sigmoid' ? a * (1 - a) : name === 'tanh' ? 1 - a * a : name === 'relu' ? (z > 0 ? 1 : 0) : 1;
  let fk = Object.keys(SYM).includes(q.get('focus')) ? q.get('focus') : 'w11';
  const gp = h('section', { class: 'em-guided ds-stage', 'aria-label': 'Geführte Ansicht: ein Parameter im Fokus' }); let lastStep = null;
  const pick = h('div', { class: 'em-pick', role: 'radiogroup', 'aria-label': 'Parameter wählen' });
  const gNet = h('div', { class: 'em-figure em-gnet' }), card = h('div', { class: 'em-gcard', role: 'status', 'aria-live': 'polite' }), gCtl = h('div', { class: 'em-params' });
  const pickBtns = Object.entries(SYM).map(([k, lbl]) => { const b = h('button', { type: 'button', role: 'radio', class: 'em-pickb', 'data-p': k }, lbl); b.addEventListener('click', () => { fk = k; guided.refresh(); }); pick.appendChild(b); return b; });
  gp.append(h('p', { class: 'em-meta' }, 'Wählen Sie einen Parameter. Sichtbar werden nur seine Verbindung, sein Term in der Kettenregel, sein Wert, sein Gradient und seine Wirkung auf den Verlust.'), pick, gNet, card, gCtl);
  guided = { refresh(bwIn) {
    const bw = bwIn || models.mlpBackward(st.p, st.x, st.t, st.ha, st.oa), fw = bw.forward, g = bw.grad;
    pickBtns.forEach(b => b.setAttribute('aria-checked', String(b.dataset.p === fk)));
    drawNet(fw, gNet, fk);
    const cur = Object.fromEntries(flat()); const j = fk === 'c' ? 0 : +fk[fk.length - (fk[0] === 'w' ? 2 : 1)]; const i = fk[0] === 'w' ? +fk[2] : 0;
    const gv = { w11: g.W1[0][0], w12: g.W1[0][1], w21: g.W1[1][0], w22: g.W1[1][1], b1: g.b1[0], b2: g.b1[1], v1: g.W2[0], v2: g.W2[1], c: g.b2 }[fk];
    const fpj = j ? dAct(st.ha, fw.z1[j - 1], fw.a1[j - 1]) : 0, sub = n => '₀₁₂₃₄₅₆₇₈₉'[n];
    let term, vals;
    if (fk[0] === 'w') { term = `∂L/∂${SYM[fk]} = δ_o · v${sub(j)} · f′(z${sub(j)}) · x${sub(i)}`; vals = `${fmt(bw.delta_o, 4)} · ${fmt(st.p.W2[j - 1], 3)} · ${fmt(fpj, 4)} · ${fmt(st.x[i - 1], 2)}`; }
    else if (fk[0] === 'b') { term = `∂L/∂${SYM[fk]} = δ_o · v${sub(j)} · f′(z${sub(j)})`; vals = `${fmt(bw.delta_o, 4)} · ${fmt(st.p.W2[j - 1], 3)} · ${fmt(fpj, 4)}`; }
    else if (fk[0] === 'v') { term = `∂L/∂${SYM[fk]} = δ_o · a${sub(j)}`; vals = `${fmt(bw.delta_o, 4)} · ${fmt(fw.a1[j - 1], 4)}`; }
    else { term = '∂L/∂c = δ_o'; vals = fmt(bw.delta_o, 4); }
    const dh = 0.1, p2 = JSON.parse(JSON.stringify(st.p)); const set2 = (k, v) => { const map = { w11: ['W1', 0, 0], w12: ['W1', 0, 1], w21: ['W1', 1, 0], w22: ['W1', 1, 1], b1: ['b1', 0], b2: ['b1', 1], v1: ['W2', 0], v2: ['W2', 1] }; if (k === 'c') p2.b2 = v; else { const [a, x, y] = map[k]; if (y === undefined) p2[a][x] = v; else p2[a][x][y] = v; } };
    set2(fk, cur[fk] + dh); const L2 = models.mlpBackward(p2, st.x, st.t, st.ha, st.oa).loss;
    const sp = (c, t) => h('span', { class: c }, t);
    const colTerm = () => { const p = h('p', { class: 'em-gterm' }); const parts = term.split(/(δ_o|v[₁₂]|f′\(z[₁₂]\)|x[₁₂]|a[₁₂])/); for (const x of parts) { if (!x) continue; p.append(/^δ/.test(x) ? sp('d', x) : /^v/.test(x) ? sp('w', x) : /^f′/.test(x) ? sp('a', x) : /^x/.test(x) ? sp('x', x) : /^a/.test(x) ? sp('a', x) : x); } return p; };
    const stepInfo = lastStep && lastStep.k === fk ? h('div', { class: 'em-gstep', 'aria-label': 'Letzter Lernschritt' },
      h('span', {}, SYM[fk]), h('span', { class: 'up' }, fmt(lastStep.before, 4) + ' → ' + fmt(lastStep.after, 4) + '  (Δ ' + fmt(lastStep.after - lastStep.before, 4) + ')'),
      h('span', {}, 'L'), h('span', { class: 'up' }, fmt(lastStep.Lb, 5) + ' → ' + fmt(lastStep.La, 5))) : null;
    card.replaceChildren(...[
      colTerm(), h('p', { class: 'em-gvals' }, '= ' + vals + ' = ', h('strong', {}, fmt(gv, 6))),
      h('dl', { class: 'em-gdl' }, h('dt', {}, 'Wert'), h('dd', {}, SYM[fk] + ' = ' + fmt(cur[fk], 4)), h('dt', {}, 'Gradient'), h('dd', {}, fmt(gv, 6)),
        h('dt', {}, 'Wirkung'), h('dd', {}, `${SYM[fk]} + 0,1 ändert L um ${fmt(L2 - bw.loss, 6)} (lineare Näherung ${fmt(gv * dh, 6)})`),
        h('dt', {}, 'Ein Schritt'), h('dd', {}, `${SYM[fk]} ← ${fmt(cur[fk], 4)} − ${fmt(st.lr, 3)} · ${fmt(gv, 6)} = ${fmt(cur[fk] - st.lr * gv, 4)}`)), stepInfo].filter(Boolean));
    lab.dataset.focus = fk; lab.dataset.focusGrad = gv;
  } };
  /* guided controls: the selected parameter and the learning rate only */
  const gDefs = () => defs.filter(d => d.id === fk || d.id === 'lr');
  const rebuildG = () => { gCtl.replaceChildren(); for (const def of gDefs()) param(gCtl, Object.assign({}, def, { id: 'g-' + def.id }), def.id === 'lr' ? st.lr : Object.fromEntries(flat())[def.id], v => { ctrls[def.id].set(v); }); const sb = h('button', { type: 'button', class: 'em-primary' }, 'Lernschritt ausführen'); sb.addEventListener('click', () => { const before = Object.fromEntries(flat())[fk], Lb = models.mlpBackward(st.p, st.x, st.t, st.ha, st.oa).loss; step(); lastStep = { k: fk, before, after: Object.fromEntries(flat())[fk], Lb, La: models.mlpBackward(st.p, st.x, st.t, st.ha, st.oa).loss }; rebuildG(); guided.refresh(); }); gCtl.appendChild(h('div', { class: 'em-buttons' }, sb)); };
  const _ref = guided.refresh; guided.refresh = (bw) => { _ref(bw); if (!gCtl.dataset.p || gCtl.dataset.p !== fk) { gCtl.dataset.p = fk; rebuildG(); } };
  const tPar = lab.querySelector('.em-tools > .em-tool');
  const mb = h('div', { class: 'em-modes', role: 'tablist', 'aria-label': 'Ansicht' });
  const setMode = (mo) => { lab.dataset.mode = mo; gp.hidden = mo !== 'guided'; if (tPar) tPar.hidden = mo === 'guided'; all.hidden = mo === 'guided'; sceneNote.hidden = mo !== 'guided'; mb.querySelectorAll('button').forEach(b => { b.setAttribute('aria-selected', String(b.dataset.m === mo)); b.tabIndex = b.dataset.m === mo ? 0 : -1; }); if (mo === 'guided') guided.refresh(); };
  for (const [mo, lbl, hint] of [['guided', 'Geführt', 'ein Parameter im Fokus'], ['explore', 'Erkunden', 'alle Parameter und Gleichungen']]) { const b = h('button', { type: 'button', role: 'tab', 'data-m': mo, class: 'em-modeb' }, h('strong', {}, lbl), h('small', {}, hint)); b.addEventListener('click', () => setMode(mo)); mb.appendChild(b); }
  mb.addEventListener('keydown', e => { if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') { const nx = lab.dataset.mode === 'guided' ? 'explore' : 'guided'; setMode(nx); mb.querySelector(`[data-m=${nx}]`).focus(); } });
  const sceneNote = h('p', { class: 'em-meta' }, 'Alle neun Parameter, Eingaben, Aktivierungen und die vollständigen Gleichungen finden Sie in der Ansicht „Erkunden“.'); gp.appendChild(sceneNote);
  lab.insertBefore(mb, lab.children[1]); lab.insertBefore(gp, mb.nextSibling);
  setMode(q.get('mode') === 'explore' ? 'explore' : 'guided');
  predictFlow(root.querySelector('.em-pre'), spec, lab, ch => ctrls[ch.param].set(ch.to));
  redraw();
};

views.chord = (root, spec) => {
  let player = null; const st = Object.fromEntries(spec.params.map(d => [d.id, d.default]));
  const lab = el('section', { class: 'em-lab', 'aria-labelledby': 'lab-h' }); lab.appendChild(el('h2', { id: 'lab-h' }, '2 · Konstruktion untersuchen'));
  const pan = el('div', { class: 'em-params' }), sceneHost = el('div'), kpi = el('div', { class: 'em-kpi', role: 'status', 'aria-live': 'polite' }), rect = el('div', { class: 'em-scroll' });
  const ctrls = {};
  const pt = p => '(' + fmt(p[0], 3) + '; ' + fmt(p[1], 3) + ')';
  const redraw = () => {
    const tr = models.chordTrace(st.s, st.t);
    Object.assign(lab.dataset, { d: tr.d, mx: tr.M[0], my: tr.M[1], rectArea: tr.rect ? tr.rect.area : '', residual: tr.rect ? tr.rect.residual : '' });
    kpi.replaceChildren(...[['P', pt(tr.P)], ['Q', pt(tr.Q)], ['Mittelpunkt M', pt(tr.M)], ['Abstand d', fmt(tr.d, 4)], ['Raumpunkt', '(' + tr.lift.map(v => fmt(v, 3)).join('; ') + ')']].map(([k, v]) => { const d = el('div'); d.append(el('span', {}, k), el('strong', {}, v)); return d; }));
    if (tr.rect) table(rect, ['Ecke', 'Parameter', 'x', 'y'], [['P', tr.rect.s, ...tr.rect.corners[0]], ['U', tr.rect.u, ...tr.rect.corners[1]], ['Q*', tr.rect.t, ...tr.rect.corners[2]], ['V', tr.rect.v, ...tr.rect.corners[3]]].map(([n, u, x, y]) => [n, fmt(u, 4), fmt(x, 4), fmt(y, 4)]),
      'Numerisch gefundenes Rechteck durch P (Restfehler ' + tr.rect.residual.toExponential(1).replace('.', EM_LOC === 'de-DE' ? ',' : '.') + ', Fläche ' + fmt(tr.rect.area, 4) + ')');
    else rect.replaceChildren(el('p', { class: 'em-meta' }, 'Für diese Lage von P hat die Suche kein Rechteck gefunden. Das beweist nicht, dass es keines gibt.'));
    if (player) player.refresh();
  };
  for (const def of spec.params) ctrls[def.id] = param(pan, def, st[def.id], v => { st[def.id] = v; redraw(); });
  const reset = el('button', { type: 'button' }, 'Zurücksetzen'); reset.addEventListener('click', () => { for (const def of spec.params) ctrls[def.id].set(def.default); });
  const buttons = el('div', { class: 'em-buttons' }); buttons.appendChild(reset);
  lab.append(sceneHost, kpi, tools(tool('Parameter', 'Lage von P und Q auf der Kurve', true, pan, buttons), tool('Gefundenes Rechteck', 'Ecken und Restfehler', false, rect))); root.appendChild(lab);
  player = scenePlayer(sceneHost, spec, 'chord', () => models.chordTrace(st.s, st.t), { setParam: (k, v) => ctrls[k].set(Math.max(0, Math.min(0.999, v))) });
  predictFlow(root.querySelector('.em-pre'), spec, lab, ch => ctrls[ch.param].set(ch.to));
  redraw();
};

views.risk = (root, spec) => {
  const m = spec.model, st = { l: m.likelihood, i: m.impact, loss: m.loss_eur, l2: m.compare.likelihood, i2: m.compare.impact, loss2: m.compare.loss_eur };
  const lab = el('section', { class: 'em-lab', 'aria-labelledby': 'lab-h' }); lab.appendChild(el('h2', { id: 'lab-h' }, '2 · Matrix und Erwartungswert'));
  const pan = el('div', { class: 'em-params' }), grid = el('div', { class: 'em-figure' }), kpi = el('div', { class: 'em-kpi', role: 'status', 'aria-live': 'polite' });
  const ctrls = {};
  const redraw = () => {
    let a, b; try { a = models.riskMatrix(st.l, st.i, m.classes); b = models.riskMatrix(st.l2, st.i2, m.classes); } catch (e) { kpi.textContent = e.message; return; }
    lab.dataset.score = a.score; lab.dataset.cls = a.class; lab.dataset.scoreB = b.score; lab.dataset.clsB = b.class;
    const RANK = { Low: 1, Moderate: 2, High: 3, Critical: 4 }; lab.dataset.rank = RANK[a.class]; lab.dataset.rankB = RANK[b.class];
    lab.dataset.eHi = models.bands[st.l][1] * st.loss; lab.dataset.eHiB = models.bands[st.l2][1] * st.loss2;
    const s = sv('svg', { viewBox: '0 0 380 360', role: 'img', 'aria-label': 'Risikomatrix 5 mal 5, Risiko A und B markiert', class: 'em-matrix' }); s.appendChild(sv('title', {}, 'Risikomatrix'));
    for (let li = 1; li <= 5; li++) for (let im = 1; im <= 5; im++) { const r = models.riskMatrix(li, im, m.classes); const x = 50 + (im - 1) * 62, y = 20 + (5 - li) * 62; s.appendChild(sv('rect', { x, y, width: 60, height: 60, class: 'em-cell c-' + r.class.toLowerCase() })); s.appendChild(sv('text', { x: x + 30, y: y + 36, 'text-anchor': 'middle', class: 'em-cell-t' }, li * im)); }
    const mark = (l, i, t) => { const x = 50 + (i - 1) * 62 + 30, y = 20 + (5 - l) * 62 + 30; s.appendChild(sv('circle', { cx: x, cy: y, r: 22, class: 'em-mark' })); s.appendChild(sv('text', { x, y: y - 12, 'text-anchor': 'middle', class: 'em-mark-t' }, t)); };
    mark(st.l, st.i, 'A'); mark(st.l2, st.i2, 'B');
    s.appendChild(sv('text', { x: 205, y: 352, 'text-anchor': 'middle', class: 'em-tick' }, 'Auswirkung (Stufe 1–5) →')); s.appendChild(sv('text', { x: 14, y: 175, transform: 'rotate(-90 14 175)', 'text-anchor': 'middle', class: 'em-tick' }, 'Wahrscheinlichkeit (Stufe 1–5) →'));
    grid.replaceChildren(s);
    const ea = models.bands[st.l].map(p => p * st.loss), eb = models.bands[st.l2].map(p => p * st.loss2);
    kpi.replaceChildren(...[['Risiko A: Punktwert', a.score + ' (' + a.class + ')'], ['Risiko B: Punktwert', b.score + ' (' + b.class + ')'], ['A: erwarteter Schaden', fmt(ea[0], 0) + ' – ' + fmt(ea[1], 0) + ' €'], ['B: erwarteter Schaden', fmt(eb[0], 0) + ' – ' + fmt(eb[1], 0) + ' €']].map(([k, v]) => { const d = el('div'); d.append(el('span', {}, k), el('strong', {}, v)); return d; }));
  };
  for (const def of spec.params) ctrls[def.id] = param(pan, def, st[def.id], v => { st[def.id] = def.type === 'number' ? v : Math.round(v); redraw(); });
  const reset = el('button', { type: 'button' }, 'Zurücksetzen'); reset.addEventListener('click', () => { for (const def of spec.params) ctrls[def.id].set(def.default); });
  lab.append(pan, el('div', { class: 'em-buttons' }), grid, kpi); lab.querySelector('.em-buttons').appendChild(reset); root.appendChild(lab);
  predictFlow(root.querySelector('.em-pre'), spec, lab, ch => ctrls[ch.param].set(ch.to));
  redraw();
};

views.van_westendorp = (root, spec) => {
  const m = spec.model, st = { segment: 'all', method: m.method || 'standard', te_shift: 0, probe: spec.params.find(p => p.id === 'probe').default }; let rows = m.rows.slice(), dataLabel = m.data_label;
  const NAME = { tc: 'zu billig', cheap: 'günstig', exp: 'teuer', te: 'zu teuer', not_cheap: 'nicht günstig', not_exp: 'nicht teuer' };
  const PT = { pmc: 'PMC – Untergrenze', opp: 'OPP – „Optimaler Preis“', ipp: 'IPP – Indifferenzpreis', pme: 'PME – Obergrenze' };
  const lab = el('section', { class: 'em-lab', 'aria-labelledby': 'lab-h' }); lab.appendChild(el('h2', { id: 'lab-h' }, '2 · Kurven und Preispunkte'));
  const warn = el('p', { class: 'em-warn' }); const pan = el('div', { class: 'em-params' }), fig = el('div', { class: 'em-figure' }), kpi = el('div', { class: 'em-kpi', role: 'status', 'aria-live': 'polite' }), probe = el('p', { class: 'em-timeline' }), tab = el('div', { class: 'em-scroll' });
  const ctrls = {};
  const draw = (r) => {
    /* drawn at the real container width so that 11px text stays 11px on a phone */
    const W = Math.round(Math.max(320, Math.min(720, fig.clientWidth || 640))), H = W < 480 ? 300 : 340, L = 40, R = 10, T = 64, B = 40, xs = r.knots, hi = xs[xs.length - 1];
    const x = v => L + v / hi * (W - L - R), y = v => T + (1 - v) * (H - T - B);
    const s = sv('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': 'Van-Westendorp-Kurven mit Preispunkten', class: 'em-chart' }); s.appendChild(sv('title', {}, 'Van-Westendorp-Kurven'));
    for (let k = 0; k <= 10; k += 2) { s.appendChild(sv('line', { x1: L, x2: W - R, y1: y(k / 10), y2: y(k / 10), class: 'em-grid' })); s.appendChild(sv('text', { x: L - 6, y: y(k / 10) + 4, 'text-anchor': 'end', class: 'em-tick' }, k * 10 + ' %')); }
    const step = [5, 10, 20, 25, 50, 100, 200, 500].find(v => hi / v <= (W < 480 ? 6 : 10)); for (let v = 0; v <= hi + 1e-9; v += step) s.appendChild(sv('text', { x: x(v), y: H - B + 15, 'text-anchor': 'middle', class: 'em-tick' }, fmt(v, 0)));
    s.appendChild(sv('text', { x: W - R, y: H - 6, 'text-anchor': 'end', class: 'em-tick' }, 'Preis (€)'));
    const P = r.points; if (P.pmc != null && P.pme != null) s.appendChild(sv('rect', { x: x(P.pmc), y: T, width: Math.max(0, x(P.pme) - x(P.pmc)), height: H - T - B, class: 'em-band' }));
    for (const k of Object.keys(NAME)) s.appendChild(sv('polyline', { points: xs.map((v, i) => `${x(v)},${y(r.curves[k][i])}`).join(' '), class: 'em-psm em-psm-' + k }));
    /* labels in a header band above the plot (one row per point), anchored away from the edges: no overlap with curves */
    ['pmc', 'opp', 'ipp', 'pme'].forEach((k, i) => { if (P[k] == null) return; const px = x(P[k]), ty = 12 + i * 13, right = px > W * 0.6;
      s.appendChild(sv('line', { x1: px, x2: px, y1: ty + 3, y2: H - B, class: 'em-pt' }));
      s.appendChild(sv('text', { x: right ? px - 4 : px + 4, y: ty, 'text-anchor': right ? 'end' : 'start', class: 'em-pt-t' }, k.toUpperCase() + ' ' + fmt(P[k], 2) + ' €')); });
    if (st.probe <= hi) s.appendChild(sv('line', { x1: x(st.probe), x2: x(st.probe), y1: T, y2: H - B, class: 'em-marker' }));
    const legend = el('div', { class: 'em-legend' }); for (const k of Object.keys(NAME)) { legend.append(el('span', { class: 'em-key em-psm-key em-psm-' + k }), document.createTextNode(NAME[k] + '  ')); }
    fig.replaceChildren(s, legend);
  };
  let lastW = 0; if (window.ResizeObserver) new ResizeObserver(() => { const w = fig.clientWidth; if (w && Math.abs(w - lastW) > 8) { lastW = w; redraw(); } }).observe(fig);
  const redraw = () => {
    let r; try { r = models.vanWestendorp(rows, st.method, st.segment, st.te_shift); } catch (e) { kpi.textContent = 'Eingabe ungültig: ' + e.message; fig.replaceChildren(); tab.replaceChildren(); probe.textContent='Keine gültige Auswertung'; return; }
    for (const k of ['pmc', 'opp', 'ipp', 'pme']) lab.dataset[k] = r.points[k] == null ? '' : r.points[k];
    lab.dataset.width = r.range_width; lab.dataset.nValid = r.n_valid;
    warn.textContent = 'Daten: ' + dataLabel + '. Gültig ' + r.n_valid + (r.n_invalid ? ', ausgeschlossen ' + r.n_invalid + ' (Zeilen ' + r.invalid_rows.slice(0, 8).join(', ') + (r.n_invalid > 8 ? ' …' : '') + ')' : ', keine ausgeschlossen') + '.';
    draw(r);
    kpi.replaceChildren(...['pmc', 'opp', 'ipp', 'pme'].map(k => { const d = el('div'); d.append(el('span', {}, PT[k]), el('strong', {}, r.points[k] == null ? 'kein Schnitt' : fmt(r.points[k], 2) + ' €')); return d; }),
      (() => { const d = el('div'); d.append(el('span', {}, 'akzeptabler Bereich PME − PMC'), el('strong', {}, r.range_width == null ? '–' : fmt(r.range_width, 2) + ' €')); return d; })());
    const sel = rows.filter(q => st.segment === 'all' || q.group === st.segment).map(q => st.te_shift ? { ...q, te: Number(q.te) + st.te_shift } : q);
    const q = models.psmShares(models.psmClean(sel).valid, st.probe);
    probe.textContent = 'Bei ' + fmt(st.probe, 1) + ' €: zu billig ' + fmt(q.tc * 100, 1) + ' % · günstig ' + fmt(q.cheap * 100, 1) + ' % · teuer ' + fmt(q.exp * 100, 1) + ' % · zu teuer ' + fmt(q.te * 100, 1) + ' %' + (st.probe < (r.points.pmc ?? -1) ? ' → unter der Untergrenze' : st.probe > (r.points.pme ?? Infinity) ? ' → über der Obergrenze' : ' → im akzeptablen Bereich');
    table(tab, ['Preispunkt', 'Schnitt der Kurven', 'Preis'], ['pmc', 'opp', 'ipp', 'pme'].map(k => [PT[k], models.psmCross[st.method][k].map(c => NAME[c]).join(' ∩ '), r.points[k] == null ? '–' : fmt(r.points[k], 2) + ' €']), st.method === 'standard' ? 'Standardkonvention (Komplementkurven)' : 'Praxisvariante');
  };
  for (const def of spec.params) ctrls[def.id] = param(pan, def, st[def.id], v => { st[def.id] = v; redraw(); });
  const reset = el('button', { type: 'button' }, 'Zurücksetzen'); reset.addEventListener('click', () => { rows = m.rows.slice(); dataLabel = m.data_label; ctrls.segment.input.replaceChildren(...spec.params.find(d=>d.id==='segment').options.map(o=>el('option',{value:o.value},o.label))); for (const def of spec.params) ctrls[def.id].set(def.default); });
  const edit = el('details', { class: 'em-edit' }); edit.appendChild(el('summary', {}, 'Eigene Antworten einfügen (CSV: zu_billig;guenstig;teuer;zu_teuer[;segment])'));
  const ta = el('textarea', { rows: 5, 'aria-label': 'Eigene Antworten als CSV' }); const use = el('button', { type: 'button' }, 'Übernehmen'); const msg = el('p', { class: 'em-meta', role: 'status' });
  use.addEventListener('click', () => {
    const lines = ta.value.split(/\r?\n/).map(v=>v.trim()).filter(Boolean);
    if(lines.length>1001) { msg.textContent='Maximal 1.000 Datenzeilen im interaktiven Lab.'; return; }
    if(/^(zu_billig|too_cheap)[;\t]/i.test(lines[0]||'')) lines.shift();
    const out = [];
    for(const t of lines) {
      const f=t.split(/[;\t]/).map(v=>v.trim());
      if(f.length<4) { msg.textContent='Jede Zeile braucht vier Preise, getrennt durch Semikolon oder Tab.'; return; }
      out.push({tc:num(f[0]),cheap:num(f[1]),exp:num(f[2]),te:num(f[3]),group:f[4]||'eigen'});
    }
    const clean=models.psmClean(out);
    if(!clean.valid.length) { msg.textContent='Keine gültige Antwort; bisheriger Datensatz bleibt erhalten.'; return; }
    rows = out; dataLabel = 'EIGENE Daten aus diesem Browser (' + out.length + ' Zeilen; Herkunft und Repräsentativität ungeprüft)';
    const segmentSelect=ctrls.segment.input; segmentSelect.replaceChildren(el('option',{value:'all'},'alle Befragten'),...([...new Set(out.map(r=>r.group))].filter(g=>g!=='all').sort().map(g=>el('option',{value:g},'Segment '+g))));
    ctrls.segment.set('all'); msg.textContent=out.length+' Zeilen übernommen; ungültige Zeilen werden gezählt und ausgeschlossen. Lernaufgaben beziehen sich weiterhin auf die Ausgangsdaten (Zurücksetzen).'; redraw(); });
  edit.append(ta, use, msg);
  lab.append(warn, pan, el('div', { class: 'em-buttons' }), fig, kpi, probe, tab, edit); lab.querySelector('.em-buttons').appendChild(reset); root.appendChild(lab);
  predictFlow(root.querySelector('.em-pre'), spec, lab, ch => ctrls[ch.param].set(ch.to));
  redraw();
};

/* B21: finite MDP lab – state graph, Bellman backup inspector (term by term), own calculation with diagnosis,
   sweep stepper (policy evaluation / value iteration), convergence plot with the contraction bound, editable model. */
views.mdp = (root, spec) => {
  const M0 = spec.model, L = M0.layout, dec = M0.decision_states, unit = M0.unit ? ' ' + M0.unit : '';
  const base = JSON.parse(JSON.stringify(M0.mdp));
  const shown = new Set(); const st = { gamma: M0.mdp.gamma, mode: 'eval', k: 0, sel: M0.focus, data: JSON.parse(JSON.stringify(M0.mdp)), pol: { ...M0.policy }, edited: false };
  const lab = el('section', { class: 'em-lab em-mdp', 'aria-labelledby': 'lab-h' }); lab.appendChild(el('h2', { id: 'lab-h' }, '2 · Simulation'));
  const pan = el('div', { class: 'em-params' }), graph = el('div', { class: 'em-figure em-mdp-graph' }), kpi = el('div', { class: 'em-kpi', role: 'status', 'aria-live': 'polite' });
  const insp = el('div', { class: 'em-mdp-inspect' }), conv = el('div', { class: 'em-figure' }), vals = el('div', { class: 'em-scroll' }), editBox = el('div', { class: 'em-scroll' }), msg = el('p', { class: 'em-meta', role: 'status' });
  const ctrls = {}; let m = null;
  const fm = (x, d = 2) => fmt(x, d).replace('-', '\u2212'), fp = (x, d = 2) => (x < 0 && fm(x, d) !== '0' ? '(' + fm(x, d) + ')' : fm(x, d));  /* typographic minus; negative factors in parentheses */
  const lbl = s => (M0.labels && M0.labels[s]) ? M0.labels[s] : s;
  const hist = () => (st.mode === 'eval' ? models.mdpEvalSweeps(m, st.pol, Math.max(st.k + 1, 1)) : models.mdpValueIteration(m, Math.max(st.k + 1, 1)));
  /* one backup = (procedure, γ, k, state, policy, model); its result stays hidden until the learner has calculated it or asks for it */
  const bkey = () => [st.mode, st.gamma, st.k, st.sel, JSON.stringify(st.pol), JSON.stringify(st.data)].join('|');
  const bucket = (v, lo, hi) => 'em-mdp-b' + (hi - lo < 1e-12 ? 2 : Math.min(4, Math.floor(5 * (v - lo) / (hi - lo))));  /* CSP: classes, no inline style */
  const drawGraph = (V, Vn, greedy) => {
    const xs = m.states.map(q => L[q][0]), ys = m.states.map(q => L[q][1]); const vx = Math.min(...xs) - 150, vy = Math.min(...ys) - 110, vw = Math.max(...xs) - Math.min(...xs) + 300, vh = Math.max(...ys) - Math.min(...ys) + 185;
    const svg = sv('svg', { viewBox: `${vx} ${vy} ${vw} ${vh}`, role: 'img', 'aria-label': 'Zustandsgraph: Zustände, Übergänge der gewählten Aktionen, aktuelle Werte V_k' });
    svg.appendChild(sv('title', {}, 'MDP mit den Übergängen der gewählten Aktionen und den Werten V' + st.k));
    const defs = sv('defs'); const mk = sv('marker', { id: 'mdp-ah2', viewBox: '0 0 10 10', refX: 9, refY: 5, markerWidth: 7, markerHeight: 7, orient: 'auto-start-reverse' }); mk.appendChild(sv('path', { d: 'M0,0 L10,5 L0,10 z', class: 'em-mdp-ahead' })); defs.appendChild(mk); svg.appendChild(defs);
    const vs = m.states.map(s => V[s]); const lo = Math.min(...vs), hi = Math.max(...vs);
    for (const s of m.states) {
      for (const a of m.actions[s]) {
        const used = st.mode === 'eval' ? st.pol[s] === a : greedy[s] === a; const isSel = s === st.sel;
        if (!used && !isSel) continue;
        const [r, nxt] = m.T[s + '\u0000' + a]; const [x1, y1] = L[s];
        for (const [t, p] of Object.entries(nxt)) {
          const cls = 'em-mdp-edge' + (used ? ' used' : ' alt') + (isSel ? ' sel' : ''); const lab_ = a + ': p = ' + fmt(p, 2) + ', r = ' + fm(r);
          if (t === s) { const g = sv('g', { class: cls }); g.appendChild(sv('path', { d: `M${x1 - 14},${y1 - 34} C${x1 - 40},${y1 - 95} ${x1 + 40},${y1 - 95} ${x1 + 14},${y1 - 34}`, 'marker-end': 'url(#mdp-ah2)' }));
            if (used) g.appendChild(sv('text', { x: x1, y: y1 - 86, 'text-anchor': 'middle' }, lab_)); svg.appendChild(g); continue; }
          const [x2, y2] = L[t]; const dx = x2 - x1, dy = y2 - y1, d = Math.hypot(dx, dy) || 1, ox = -dy / d * 16, oy = dx / d * 16;
          const sx = x1 + dx / d * 36 + ox, sy = y1 + dy / d * 36 + oy, ex = x2 - dx / d * 38 + ox, ey = y2 - dy / d * 38 + oy;
          const g = sv('g', { class: cls }); g.appendChild(sv('line', { x1: sx, y1: sy, x2: ex, y2: ey, 'marker-end': 'url(#mdp-ah2)' }));
          if (used) g.appendChild(sv('text', { x: (sx + ex) / 2 + ox, y: (sy + ey) / 2 + oy + 4, 'text-anchor': 'middle' }, lab_)); svg.appendChild(g);
        }
      }
    }
    for (const s of m.states) {
      const [x, y] = L[s]; const g = sv('g', { class: 'em-mdp-state' + (s === st.sel ? ' sel' : '') + (m.actions[s].length ? '' : ' term'), tabindex: 0, role: 'button', 'aria-label': 'Zustand ' + lbl(s) + ' auswählen, V = ' + fmt(V[s], 2) });
      g.appendChild(sv('circle', { cx: x, cy: y, r: 34, class: bucket(V[s], lo, hi) }));
      g.appendChild(sv('text', { x, y: y - 4, 'text-anchor': 'middle', class: 'em-mdp-name' }, s));
      g.appendChild(sv('text', { x, y: y + 14, 'text-anchor': 'middle', class: 'em-mdp-v' }, fm(V[s])));
      g.appendChild(sv('text', { x, y: y + 54, 'text-anchor': 'middle', class: 'em-mdp-next' }, mt('V_{' + (st.k + 1) + '} = ' + (s === st.sel && !shown.has(bkey()) ? '?' : fm(Vn[s])))));
      const pick = () => { st.sel = s; redraw(); }; g.addEventListener('click', pick); g.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pick(); } });
      svg.appendChild(g);
    }
    graph.replaceChildren(svg, el('p', { class: 'em-meta' }, mt('Zahl im Kreis: V_' + st.k + '(s), darunter V_{' + (st.k + 1) + '}(s) nach dem nächsten Sweep. Pfeile: ' + (st.mode === 'eval' ? 'Aktion der Policy π' : 'greedy Aktion bezüglich V_' + st.k) + '; beim ausgewählten Zustand zusätzlich alle Aktionen (gestrichelt). Klick auf einen Zustand öffnet seinen Bellman-Backup.')));
  };
  const own = { box: null };
  const drawInspector = (V, greedy) => {
    const s = st.sel, open = shown.has(bkey()); insp.replaceChildren();
    insp.appendChild(el('h3', {}, mt('Bellman-Backup für ' + lbl(s) + ': von V_{' + st.k + '} zu V_{' + (st.k + 1) + '}')));
    if (!m.actions[s].length) { insp.appendChild(el('p', {}, s + ' ist terminal: V(' + s + ') = 0 in jedem Sweep.')); return; }
    const rows = m.actions[s].map(a => { const b = models.mdpBackupTerms(m, V, s, a);
      const used = st.mode === 'eval' ? st.pol[s] === a : greedy[s] === a;
      return [a + (used ? (st.mode === 'eval' ? '  ← π' : '  ← max') : ''), b.terms.map(x => fmt(x.p, 2) + ' · (' + fm(x.r) + ' + ' + fmt(m.gamma, 2) + ' · ' + fp(x.v_next) + ')').join(' + '), open ? fm(b.q, 3) : '?']; });
    const t = el('div', { class: 'em-scroll' }); table(t, ['Aktion a', mt('Σ_{s′} p(s′|s,a) · (r(s,a) + γ · V_{' + st.k + '}(s′))'), mt('Q_{' + st.k + '}(s,a)')], rows, st.mode === 'eval' ? 'Policy-Bewertung: Es zählt nur die Aktion der Policy π.' : 'Wertiteration: Es zählt das Maximum über alle Aktionen.');
    const res = st.mode === 'eval' ? models.mdpPi(m, V, s, st.pol) : Math.max(...m.actions[s].map(a => models.mdpQ(m, V, s, a)));
    const resP = el('p', { class: 'em-mdp-result' }, mt('V_{' + (st.k + 1) + '}(' + s + ') = ' + (open ? fm(res, 3) + unit : '?')));
    insp.append(t, resP);
    if (!open) { const rv = el('button', { type: 'button', class: 'em-link' }, 'Ohne eigene Rechnung aufdecken'); rv.addEventListener('click', () => { shown.add(bkey()); store.record(spec.id, 'own-backup', spec.kc_ids, 'solution'); redraw(); }); resP.appendChild(document.createTextNode(' ')); resP.appendChild(rv); }
    /* own calculation before looking: diagnosis of the typical errors (same classes as the workbook tasks) */
    const a = st.mode === 'eval' ? st.pol[s] : greedy[s]; const [r, nxt] = m.T[s + '\u0000' + a];
    const det = el('details', { class: 'em-mdp-own' }); if (!open) det.open = true; det.appendChild(el('summary', {}, mt('Selbst rechnen: V_{' + (st.k + 1) + '}(' + s + ') eingeben und prüfen lassen')));
    const inp = el('input', { type: 'text', inputmode: 'decimal', 'aria-label': 'Ihr Wert für V_' + (st.k + 1) + '(' + s + ')' }); const go = el('button', { type: 'button', class: 'em-primary' }, 'Prüfen'); const fb = el('div', { class: 'em-feedback', role: 'status', 'aria-live': 'polite' });
    const errs = [[r + Object.entries(nxt).reduce((x, [t2, p]) => x + p * V[t2], 0), 'Der Diskontfaktor γ fehlt.'],
      [r + m.gamma * Object.keys(nxt).reduce((x, t2) => x + V[t2], 0) / Object.keys(nxt).length, 'Die Folgezustände wurden gleich gewichtet statt mit p(s′|s,a).'],
      [Math.max(...m.actions[s].map(b => models.mdpQ(m, V, s, b))), 'Das ist das Maximum über alle Aktionen (Wertiteration); hier zählt nur die Aktion der Policy.'],
      [Math.min(...m.actions[s].map(b => models.mdpQ(m, V, s, b))), 'Das ist der kleinste Q-Wert. Die Wertiteration nimmt das Maximum.'],
      [V[s], 'Das ist der alte Wert V_' + st.k + '(' + s + ').'], [m.gamma * Object.entries(nxt).reduce((x, [t2, p]) => x + p * V[t2], 0), 'Die unmittelbare Belohnung r(s,a) fehlt.']];
    go.addEventListener('click', () => { const v = num(inp.value); if (!Number.isFinite(v)) { fb.textContent = 'Bitte eine Zahl eingeben.'; return; }
      if (Math.abs(v - res) <= 0.006) { fb.replaceChildren(el('strong', { class: 'em-ok' }, 'Richtig. '), document.createTextNode('V_' + (st.k + 1) + '(' + s + ') = ' + fmt(res, 3) + '.')); store.record(spec.id, 'own-backup', spec.kc_ids, 'correct'); lab.dataset.ownOk = String(Number(lab.dataset.ownOk || 0) + 1); shown.add(bkey()); redraw(); return; }
      store.record(spec.id, 'own-backup', spec.kc_ids, 'wrong'); const hit = errs.find(([w]) => Math.abs(w - res) > 0.012 && Math.abs(v - w) <= 0.006);
      fb.replaceChildren(el('strong', { class: 'em-bad' }, 'Noch nicht. '), document.createTextNode(hit ? hit[1] : 'Vergleichen Sie Ihre Terme mit der Tabelle oben: p · (r + γ · V(s′)) für jeden Folgezustand.')); });
    inp.addEventListener('keydown', e => { if (e.key === 'Enter') go.click(); });
    const row = el('div', { class: 'em-answer' }); row.append(inp, el('span', {}, M0.unit || ''), go); det.append(el('p', { class: 'em-meta' }, open ? 'Weiter: Wählen Sie einen anderen Zustand oder den nächsten Sweep und rechnen Sie erneut.' : 'Die Tabelle zeigt die Terme; die Q-Werte und das Ergebnis erscheinen, sobald Ihre Rechnung stimmt.'), row, fb); insp.appendChild(det);
  };
  const drawConv = (target) => {
    const K = Math.max(30, st.k + 5), h = st.mode === 'eval' ? models.mdpEvalSweeps(m, st.pol, K) : models.mdpValueIteration(m, K);
    const e = h.map(V => Math.max(...m.states.map(s => Math.abs(V[s] - target[s])))); const e0 = e[0] || 1;
    const W = 600, H = 220, l = 50, r = 12, t = 14, b = 34, lo = Math.max(-6, Math.floor(Math.log10(Math.max(Math.min(...e, e0 * m.gamma ** K), 1e-12))) - 0.3), hiL = Math.log10(Math.max(e0, 1e-6)) + 0.3;
    const X = i => l + (W - l - r) * i / K, Y = v => t + (hiL - Math.max(lo, Math.log10(Math.max(v, 1e-12)))) / (hiL - lo) * (H - t - b);
    const svg = sv('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': 'Fehler ‖V_k − V‖∞ je Sweep, logarithmisch, mit Schranke γ^k ‖V_0 − V‖∞' });
    svg.appendChild(sv('title', {}, 'Konvergenz: Fehler je Sweep (log) und Kontraktionsschranke'));
    for (let p = Math.ceil(lo); p <= Math.floor(hiL); p++) { svg.appendChild(sv('line', { x1: l, x2: W - r, y1: Y(10 ** p), y2: Y(10 ** p), class: 'em-grid' })); svg.appendChild(sv('text', { x: l - 6, y: Y(10 ** p) + 4, 'text-anchor': 'end', class: 'em-axis' }, mt('10^' + p))); }
    svg.appendChild(sv('polyline', { points: e.map((v, i) => X(i) + ',' + Y(v)).join(' '), class: 'em-mdp-err' }));
    svg.appendChild(sv('polyline', { points: e.map((_, i) => X(i) + ',' + Y(e0 * m.gamma ** i)).join(' '), class: 'em-mdp-bound' }));
    svg.appendChild(sv('circle', { cx: X(st.k), cy: Y(e[st.k]), r: 5, class: 'em-mdp-now' }));
    svg.appendChild(sv('text', { x: l, y: H - 8, class: 'em-axis' }, 'Sweep k (0 … ' + K + ')'));
    conv.replaceChildren(svg, el('p', { class: 'em-meta' }, mt('Durchgezogen: Fehler ‖V_k − ' + (st.mode === 'eval' ? 'V^π' : 'V^*') + '‖_∞ (logarithmisch). Gestrichelt: Kontraktionsschranke γ^k ‖V_0 − ' + (st.mode === 'eval' ? 'V^π' : 'V^*') + '‖_∞. Die Fehlerkurve liegt nie über der Schranke.'))); return e[st.k];
  };
  const drawEdit = () => {
    const t = el('table', { class: 'em-table em-input-table' }); const hd = el('tr'); ['s', 'a', 'r(s,a)', ...m.states.map(s => 'p(' + s + '|s,a)')].forEach(h => hd.appendChild(el('th', { scope: 'col' }, h))); t.appendChild(hd);
    st.data.transitions.forEach((tr, i) => { const row = el('tr'); row.append(el('th', { scope: 'row' }, tr.s), el('td', {}, tr.a));
      const cell = (val, set, lab_) => { const td = el('td'); const inp = el('input', { type: 'number', step: '0.05', 'aria-label': lab_ }); inp.value = val; inp.addEventListener('change', () => { const x = num(inp.value); if (!Number.isFinite(x)) { inp.classList.add('em-invalid'); return; } inp.classList.remove('em-invalid'); set(x); st.edited = true; redraw(); }); td.appendChild(inp); return td; };
      row.appendChild(cell(tr.r, x => { st.data.transitions[i].r = x; }, 'Belohnung r(' + tr.s + ',' + tr.a + ')'));
      m.states.forEach(s2 => row.appendChild(cell(tr.next[s2] || 0, x => { st.data.transitions[i].next[s2] = x; }, 'p(' + s2 + '|' + tr.s + ',' + tr.a + ')')));
      t.appendChild(row); });
    editBox.replaceChildren(t);
  };
  const redraw = () => {
    try { m = models.mdpCheck({ ...st.data, gamma: st.gamma }); msg.textContent = st.edited ? 'Eigenes Modell aktiv. Die Aufgaben unten beziehen sich weiterhin auf die Ausgangsdaten (Zurücksetzen).' : ''; }
    catch (e) { msg.textContent = 'Modell ungültig: ' + e.message + ' – die Anzeige zeigt den letzten gültigen Stand.'; if (!m) return; }
    const h = hist(), V = h[st.k], Vn = h[st.k + 1]; const vpi = models.mdpEvalExact(m, st.pol), vstar = models.mdpOptimal(m);
    const greedyK = models.mdpGreedy(m, V), gpi = models.mdpGreedy(m, vpi), opt = models.mdpGreedy(m, vstar);
    drawGraph(V, Vn, greedyK); drawInspector(V, greedyK);
    const err = drawConv(st.mode === 'eval' ? vpi : vstar);
    const nong = Object.keys(gpi).filter(s => Math.abs(models.mdpQ(m, vpi, s, gpi[s]) - models.mdpQ(m, vpi, s, st.pol[s])) > 1e-9).length;
    Object.assign(lab.dataset, { vpi: vpi[M0.focus], vstar: vstar[M0.focus], err, nonGreedy: nong, optSig: m.states.filter(s => s in opt).map(s => opt[s]).join('|'), k: st.k });
    kpi.replaceChildren(...[['Sweep k', String(st.k)], ['Fehler ‖V_k − ' + (st.mode === 'eval' ? 'V^π' : 'V^*') + '‖_∞', fmt(err, 4)], ['V^π(' + M0.focus + '), exakt', fmt(vpi[M0.focus], 2) + unit], ['V^*(' + M0.focus + ')', fmt(vstar[M0.focus], 2) + unit],
      ['verbesserbare Zustände', nong ? String(nong) : '0 · π ist optimal'], ['Horizont 1/(1 − γ)', fmt(1 / (1 - m.gamma), 1) + ' Schritte']].map(([a, b]) => { const d = el('div'); d.append(el('span', {}, mt(a)), el('strong', {}, b)); return d; }));
    table(vals, ['Zustand', mt('V_{' + st.k + '}'), mt('V^π (exakt)'), mt('V^*'), mt('greedy bzgl. V^π'), 'optimal'], m.states.map(s => [lbl(s), fm(V[s], 3), fm(vpi[s], 3), fm(vstar[s], 3), gpi[s] || '–', opt[s] || '–']), mt('Werte und Aktionen; V^π aus dem linearen Gleichungssystem (I − γP^π)V = r^π'));
  };
  for (const def of spec.params) { const id = def.id; const v0 = id === 'gamma' ? st.gamma : id === 'mode' ? st.mode : id === 'k' ? st.k : st.pol[dec[Number(id.slice(2))]];
    ctrls[id] = param(pan, def, v0, v => { if (id === 'gamma') st.gamma = v; else if (id === 'mode') st.mode = v; else if (id === 'k') st.k = Math.round(v); else st.pol[dec[Number(id.slice(2))]] = v; redraw(); }); }
  const step = (d, lbl_) => { const b = el('button', { type: 'button' }, lbl_); b.addEventListener('click', () => ctrls.k.set(Math.max(0, Math.min(200, st.k + d)))); return b; };
  const toEnd = el('button', { type: 'button' }, 'Bis ‖ΔV‖ < 0,001'); toEnd.addEventListener('click', () => { const h = st.mode === 'eval' ? models.mdpEvalSweeps(m, st.pol, 200) : models.mdpValueIteration(m, 200); let k = 1; while (k < 200 && Math.max(...m.states.map(s => Math.abs(h[k][s] - h[k - 1][s]))) >= 0.001) k++; ctrls.k.set(k); });
  const reset = el('button', { type: 'button' }, 'Zurücksetzen'); reset.addEventListener('click', () => { st.data = JSON.parse(JSON.stringify(base)); st.edited = false; for (const def of spec.params) ctrls[def.id].set(def.default); drawEdit(); });
  const btns = el('div', { class: 'em-buttons' }); btns.append(step(-1, '− 1 Sweep'), step(1, '+ 1 Sweep'), toEnd, reset);
  const edit = el('details', { class: 'em-edit' }); edit.append(el('summary', {}, 'Modell bearbeiten: Belohnungen und Übergangswahrscheinlichkeiten'), editBox, el('p', { class: 'em-meta' }, 'Jede Zeile p(·|s,a) muss sich zu 1 summieren; sonst bleibt der letzte gültige Stand aktiv.'));
  edit.addEventListener('toggle', drawEdit);
  lab.append(graph, kpi, insp, tools(tool('Steuerung', 'γ, Verfahren, Sweeps, Policy', true, pan, btns, msg), tool('Konvergenz', 'Fehler je Sweep und Kontraktionsschranke', false, conv), tool('Wertetabelle', 'V_k, V^π, V*, greedy Aktionen', false, vals), tool('Modell bearbeiten', 'eigene Übungs-MDPs', false, edit)));
  root.appendChild(lab);
  predictFlow(root.querySelector('.em-pre'), spec, lab, ch => ctrls[ch.param].set(ch.to));
  redraw();
};

/* v0.18 generic labs. Shared rule: a result the learner is asked to work out (N(ε), a softmax row, the founders' share,
   the reference decision of a legal element) stays hidden ("?") until the learner has committed an own answer or
   explicitly asks to see it; the reveal is recorded as help in the learning record. */
const kv = (pairs) => pairs.map(([a, b]) => { const d = el('div'); d.append(el('span', {}, mt(a)), el('strong', {}, b)); return d; });
const fmS = (x, d = 3) => fmt(x, d).replace('-', '−');
const fmtF = (x, d = 2) => (Number.isFinite(x) ? (Math.abs(x) < 0.5 * 10 ** -d ? 0 : x).toLocaleString(EM_LOC, { useGrouping: EM_LOC === 'de-DE', minimumFractionDigits: d, maximumFractionDigits: d }) : '–');  /* fixed decimals (money) */

views.sequence = (root, spec) => {
  const M0 = spec.model, ex = M0.examples, shown = new Set();
  const st = { data: { ...ex[0] }, eps: Number(spec.params.find(p => p.id === 'eps').default), view: 'all', H: spec.params.find(p => p.id === 'horizon').default, own: false };
  const lab = el('section', { class: 'em-lab em-seq', 'aria-labelledby': 'lab-h' }); lab.appendChild(el('h2', { id: 'lab-h' }, '2 · Folge und ε-Band'));
  const head = el('p', { class: 'em-seq-label' }), fig = el('div', { class: 'em-figure' }), kpi = el('div', { class: 'em-kpi', role: 'status', 'aria-live': 'polite' });
  const pan = el('div', { class: 'em-params' }), msg = el('p', { class: 'em-meta', role: 'status' }), tab = el('div', { class: 'em-scroll' }), own = el('div', { class: 'em-own' });
  const ctrls = {}; let ts = [], N = null, sm = null;
  const key = () => JSON.stringify([st.data, st.eps, st.view, st.H]);
  const epsLabel = e => fmt(e, Math.max(0, -Math.floor(Math.log10(e) + 1e-9)));
  const compute = () => { ts = models.seqTerms(st.data, st.H); N = models.seqFirstIndex(ts, Number(st.data.limit), st.eps, st.view); sm = models.seqSummary(ts); };
  const draw = (open) => {
    const W = Math.round(Math.max(320, Math.min(760, fig.clientWidth || 640))), Hh = W < 480 ? 260 : 300, l = 54, r = 12, t = 14, b = 34;
    const L = Number(st.data.limit), K = Math.min(ts.length, W < 480 ? 40 : 80); const vis = ts.slice(0, K).map((v, i) => [i + 1, v]).filter(([n]) => st.view === 'all' || ((n % 2 === 0) === (st.view === 'even')));
    let lo = Math.min(L - st.eps, ...vis.map(x => x[1])), hi = Math.max(L + st.eps, ...vis.map(x => x[1])); if (hi - lo < 1e-9) { hi += 1; lo -= 1; } const pad = (hi - lo) * 0.08; lo -= pad; hi += pad;
    const X = n => l + (W - l - r) * (n - 1) / Math.max(1, K - 1), Y = v => t + (hi - v) / (hi - lo) * (Hh - t - b);
    const s = sv('svg', { viewBox: `0 0 ${W} ${Hh}`, role: 'img', 'aria-label': 'Folgenglieder a_n mit ε-Band um den Grenzwert-Kandidaten', class: 'em-chart' }); s.appendChild(sv('title', {}, 'Folgenglieder und ε-Band'));
    for (let k = 0; k <= 4; k++) { const v = lo + (hi - lo) * k / 4; s.appendChild(sv('line', { x1: l, x2: W - r, y1: Y(v), y2: Y(v), class: 'em-grid' })); s.appendChild(sv('text', { x: l - 6, y: Y(v) + 4, 'text-anchor': 'end', class: 'em-tick' }, fmt(v, 2))); }
    s.appendChild(sv('rect', { x: l, y: Y(L + st.eps), width: W - l - r, height: Math.max(1, Y(L - st.eps) - Y(L + st.eps)), class: 'em-seq-band' }));
    s.appendChild(sv('line', { x1: l, x2: W - r, y1: Y(L), y2: Y(L), class: 'em-seq-limit' }));
    const step = [1, 2, 5, 10, 20, 50].find(v => K / v <= (W < 480 ? 6 : 10)) || 50; for (let n = 1; n <= K; n += (n === 1 && step > 1 ? step - 1 : step)) s.appendChild(sv('text', { x: X(n), y: Hh - b + 16, 'text-anchor': 'middle', class: 'em-tick' }, String(n)));
    s.appendChild(sv('text', { x: W - r, y: Hh - 4, 'text-anchor': 'end', class: 'em-tick' }, 'n'));
    if (open && N !== null && N <= K) { s.appendChild(sv('line', { x1: X(N), x2: X(N), y1: t, y2: Hh - b, class: 'em-marker' })); s.appendChild(sv('text', { x: X(N) + 5, y: t + 12, class: 'em-marker-text' }, 'N = ' + N)); }
    vis.forEach(([n, v]) => s.appendChild(sv('circle', { cx: X(n), cy: Y(Math.max(lo, Math.min(hi, v))), r: W < 480 ? 2.6 : 3.2, class: 'em-seq-pt' + (open ? (models.seqInside(v, L, st.eps) ? ' in' : ' out') : '') })));
    const legend = el('p', { class: 'em-meta' }, mt('Punkte: a_n für n = 1 … ' + K + (ts.length > K ? ' (gerechnet wird bis H = ' + ts.length + ')' : '') + '. Band: a ± ε. ' + (open ? 'Blau: im Band, orange: außerhalb.' : 'Färbung und N erscheinen nach Ihrer eigenen Vorhersage.')));
    fig.replaceChildren(s, legend);
  };
  let lastW = 0; if (window.ResizeObserver) new ResizeObserver(() => { const w = fig.clientWidth; if (w && Math.abs(w - lastW) > 8) { lastW = w; redraw(); } }).observe(fig);
  const ownBox = (open) => {
    const ok_ = key() + '|' + open; if (own.dataset.k === ok_) return; own.dataset.k = ok_;   /* keep the learner's typing across redraws */
    own.replaceChildren(); if (open) return;
    own.appendChild(el('p', { class: 'em-question' }, mt('Ihre Vorhersage: Ab welchem Index N liegen alle Glieder ' + (st.view === 'all' ? '' : '(der Teilfolge) ') + 'im Band |a_n − a| < ' + epsLabel(st.eps) + '?')));
    const inp = el('input', { type: 'text', inputmode: 'numeric', 'aria-label': 'Ihre Vorhersage für N(ε)' }); const go = el('button', { type: 'button', class: 'em-primary' }, 'Vorhersage festlegen');
    const fb = el('div', { class: 'em-feedback', role: 'status', 'aria-live': 'polite' }); const rv = el('button', { type: 'button', class: 'em-link' }, 'Ohne eigene Vorhersage aufdecken');
    go.addEventListener('click', () => { const v = num(inp.value); if (!Number.isInteger(v) || v < 1) { fb.textContent = 'Bitte eine ganze Zahl ≥ 1 eingeben.'; return; }
      const ok = N !== null && v === N; store.record(spec.id, 'own-N', spec.kc_ids, ok ? 'correct' : 'wrong'); shown.add(key()); st.lastGuess = v; redraw(); });
    inp.addEventListener('keydown', e => { if (e.key === 'Enter') go.click(); });
    rv.addEventListener('click', () => { store.record(spec.id, 'own-N', spec.kc_ids, 'solution'); shown.add(key()); st.lastGuess = null; redraw(); });
    const row = el('div', { class: 'em-answer' }); row.append(inp, go); own.append(row, fb, rv);
  };
  const redraw = () => {
    try { compute(); msg.textContent = ''; } catch (e) { msg.textContent = 'Folge ungültig: ' + e.message; return; }
    const open = shown.has(key()), L = Number(st.data.limit);
    head.replaceChildren(el('strong', {}, mt(st.data.label || ('a_n = ' + st.data.expr))), document.createTextNode(' · Kandidat a = ' + fmt(L, 4) + ' · ε = ' + epsLabel(st.eps) + ' · H = ' + st.H));
    lab.dataset.N = N === null ? -1 : N; lab.dataset.found = N === null ? 0 : 1;
    draw(open); ownBox(open);
    const MONO = { inc: 'monoton wachsend', dec: 'monoton fallend', const: 'konstant', none: 'nicht monoton' };
    const nTxt = !open ? '?' : N === null ? 'kein N im Horizont' : String(N);
    kpi.replaceChildren(...kv([['N(ε) im Horizont', nTxt], ['Monotonie (n ≤ H)', MONO[sm.mono]], ['kleinstes / größtes a_n', fmS(sm.min) + ' / ' + fmS(sm.max)], ['a_H (n = ' + st.H + ')', fmS(sm.last, 5)]]));
    if (open && st.lastGuess != null) kpi.appendChild(kv([['Ihre Vorhersage', String(st.lastGuess) + (st.lastGuess === N ? ' ✓' : ' – Lab: ' + nTxt)]])[0]);
    const rowsIdx = [...new Set([1, 2, 3, 4, 5, ...(open && N ? [N - 1, N, N + 1] : []), st.H - 1, st.H])].filter(n => n >= 1 && n <= st.H && (st.view === 'all' || ((n % 2 === 0) === (st.view === 'even')))).sort((a, b) => a - b);
    table(tab, open ? ['n', mt('a_n'), mt('|a_n − a|'), 'im Band?'] : ['n', mt('a_n')], rowsIdx.map(n => open ? [String(n), fmS(ts[n - 1], 6), fmS(Math.abs(ts[n - 1] - L), 6), models.seqInside(ts[n - 1], L, st.eps) ? 'ja' : 'nein'] : [String(n), fmS(ts[n - 1], 6)]),
      open ? 'Ausgewählte Glieder mit Abstand zum Kandidaten' : 'Erste und letzte berechnete Glieder (Abstände erscheinen nach Ihrer Vorhersage)');
  };
  /* example picker and own sequence */
  const exRow = el('div', { class: 'em-param' }); const exSel = el('select', { id: 'seq-ex' }); ex.forEach((x, i) => exSel.appendChild(el('option', { value: String(i) }, x.label)));
  exRow.append(el('label', { for: 'seq-ex' }, 'Beispielfolge'), exSel, el('output', {}, '')); pan.appendChild(exRow);
  for (const def of spec.params) ctrls[def.id] = param(pan, def, def.id === 'eps' ? def.default : def.id === 'view' ? st.view : st.H, v => { if (def.id === 'eps') st.eps = Number(v); else if (def.id === 'view') st.view = v; else st.H = Math.round(v); redraw(); });
  const edit = el('details', { class: 'em-edit' }); edit.appendChild(el('summary', {}, 'Eigene Folge eingeben (erlaubt: Zahlen, n, + − * / ^, sqrt( ), abs( ), Klammern)'));
  const kind = el('select', { 'aria-label': 'Art der Folge' }); [['expr', 'explizit: a_n = f(n)'], ['rec', 'rekursiv: a_{n+1} = f(a_n), a = a_n']].forEach(([v, t]) => kind.appendChild(el('option', { value: v }, t.replace(/[{}_]/g, ''))));
  const fx = el('input', { type: 'text', 'aria-label': 'Ausdruck', placeholder: 'z. B. (-1)^n/n oder sqrt(2+a)' }), a1 = el('input', { type: 'text', inputmode: 'decimal', 'aria-label': 'Startwert a_1', placeholder: 'a_1 (nur rekursiv)' }), lim = el('input', { type: 'text', inputmode: 'decimal', 'aria-label': 'Grenzwert-Kandidat a', placeholder: 'Kandidat a' });
  const use = el('button', { type: 'button' }, 'Übernehmen'); const emsg = el('p', { class: 'em-meta', role: 'status' });
  use.addEventListener('click', () => { const L = num(lim.value); const d = kind.value === 'rec' ? { rec: fx.value, a1: num(a1.value), limit: L } : { expr: fx.value, limit: L };
    if (!Number.isFinite(L)) { emsg.textContent = 'Bitte einen Grenzwert-Kandidaten a als Zahl angeben.'; return; }
    try { models.seqTerms(d, 50); } catch (e) { emsg.textContent = 'Nicht übernommen: ' + e.message; return; }
    d.label = kind.value === 'rec' ? 'a_1 = ' + a1.value + ', a_{n+1} = ' + fx.value : 'a_n = ' + fx.value; st.data = d; emsg.textContent = 'Eigene Folge aktiv. Die Aufgaben unten beziehen sich weiterhin auf die Ausgangsfolge.'; redraw(); });
  const g = el('div', { class: 'em-seq-edit' }); g.append(kind, fx, a1, lim, use); edit.append(g, emsg);
  exSel.addEventListener('change', () => { st.data = { ...ex[Number(exSel.value)] }; redraw(); });
  const reset = el('button', { type: 'button' }, 'Zurücksetzen'); reset.addEventListener('click', () => { exSel.value = '0'; st.data = { ...ex[0] }; for (const def of spec.params) ctrls[def.id].set(def.default); });
  const note = el('p', { class: 'em-proofnote' }, 'Numerische Evidenz: Geprüft werden nur die berechneten Glieder a_1 … a_H. Das Lab zeigt keinen Beweis – über n > H sagt es nichts.');
  lab.append(head, fig, own, kpi, note, tools(tool('Steuerung', 'ε, Teilfolge, Horizont, Beispiele', true, pan, el('div', { class: 'em-buttons' }, reset), msg), tool('Gliedertabelle', 'a_n und Abstand zum Kandidaten', false, tab), tool('Eigene Folge', 'sicherer Ausdrucksparser, kein eval', false, edit)));
  root.appendChild(lab);
  predictFlow(root.querySelector('.em-pre'), spec, lab, ch => ctrls[ch.param].set(ch.to));
  redraw();
};

views.attention = (root, spec) => {
  const M0 = spec.model, A0 = M0.att, n = A0.tokens.length, shown = new Set();
  const st = { q: Number(spec.params.find(p => p.id === 'q').default), causal: false, head: '1' };
  const lab = el('section', { class: 'em-lab em-att', 'aria-labelledby': 'lab-h' }); lab.appendChild(el('h2', { id: 'lab-h' }, '2 · Self-Attention Schritt für Schritt'));
  const pan = el('div', { class: 'em-params' }), toks = el('p', { class: 'em-att-tokens' }), shapes = el('p', { class: 'em-meta em-att-shapes' }), mats = el('div', { class: 'em-att-grid' }), own = el('div', { class: 'em-own' }), bars = el('div', { class: 'em-figure' }), outB = el('div', { class: 'em-scroll' });
  const ctrls = {}; const tl = j => A0.tokens[j] + ' (' + (j + 1) + ')';
  const key = (h) => [st.q, st.causal, h].join('|');
  const mtab = (title, M, opt = {}) => { const box = el('div', { class: 'em-scroll em-att-m' }); const head = [mt(title), ...(opt.cols || M[0].map((_, j) => String(j + 1)))];
    const t = el('table', { class: 'em-table' }); const hr = el('tr'); head.forEach(h => hr.appendChild(el('th', { scope: 'col' }, h))); t.appendChild(el('thead')).appendChild(hr); const tb = el('tbody');
    M.forEach((r, i) => { const tr = el('tr', i === st.q && opt.hl ? { class: 'em-att-q' } : {}); tr.appendChild(el('th', { scope: 'row' }, opt.rows ? opt.rows[i] : String(i + 1)));
      r.forEach((x, j) => tr.appendChild(el('td', {}, opt.cell ? opt.cell(x, i, j) : fmS(x, opt.d ?? 2)))); tb.appendChild(tr); });
    t.appendChild(tb); box.appendChild(t); return box; };
  const ownBox = (h, A, raw, unmasked) => {
    own.replaceChildren(); if (shown.has(key(h))) return;
    own.appendChild(el('p', { class: 'em-question' }, mt('Selbst rechnen (Head ' + (h + 1) + '): die Softmax-Zeile von „' + tl(st.q) + '“ – ' + n + ' Gewichte α_{' + (st.q + 1) + 'j}, getrennt durch Semikolon, je 2 Nachkommastellen.')));
    const inp = el('input', { type: 'text', 'aria-label': 'Ihre Gewichte, getrennt durch Semikolon', placeholder: Array(n).fill('0,00').join('; ') }); const go = el('button', { type: 'button', class: 'em-primary' }, 'Prüfen');
    const fb = el('div', { class: 'em-feedback', role: 'status', 'aria-live': 'polite' }); const rv = el('button', { type: 'button', class: 'em-link' }, 'Ohne eigene Rechnung aufdecken');
    go.addEventListener('click', () => { const v = inp.value.split(/[;\s]+/).filter(Boolean).map(num);
      if (v.length !== n || v.some(x => !Number.isFinite(x))) { fb.textContent = 'Bitte genau ' + n + ' Zahlen eingeben, getrennt durch Semikolon.'; return; }
      const near = (ref) => ref.every((x, j) => Math.abs(x - v[j]) <= 0.011);
      if (near(A[st.q])) { store.record(spec.id, 'own-softmax', spec.kc_ids, 'correct'); shown.add(key(h)); redraw(); return; }
      store.record(spec.id, 'own-softmax', spec.kc_ids, 'wrong'); const s = v.reduce((a, b) => a + b, 0);
      fb.replaceChildren(el('strong', { class: 'em-bad' }, 'Noch nicht. '), document.createTextNode(
        near(models.attSoftmax(raw[st.q], A[st.q].map((_, j) => !st.causal || j <= st.q))) ? 'Das ist die Softmax der unskalierten Scores – erst durch √d_k teilen.'
          : (st.causal && near(unmasked)) ? 'Das ist die Zeile ohne Maske. Spätere Tokens erhalten Gewicht 0, die übrigen werden neu normiert.'
          : Math.abs(s - 1) > 0.03 ? 'Die Gewichte einer Zeile müssen sich zu 1 summieren (Ihre Summe: ' + fmt(s, 2) + ').'
          : 'Prüfen Sie e^{s_j} je Spalte und die Normierung durch die Zeilensumme.')); });
    inp.addEventListener('keydown', e => { if (e.key === 'Enter') go.click(); });
    rv.addEventListener('click', () => { store.record(spec.id, 'own-softmax', spec.kc_ids, 'solution'); shown.add(key(h)); redraw(); });
    const row = el('div', { class: 'em-answer' }); row.append(inp, go); own.append(row, fb, rv);
  };
  const redraw = () => {
    const r = models.attMulti(A0.X, A0.heads, st.causal), r0 = models.attMulti(A0.X, A0.heads, false);
    const hs = st.head === 'concat' ? [0, 1] : [Number(st.head) - 1]; const h = hs[0], H = r.heads[h], dk = H.dk, dv = H.V[0].length, d = A0.X[0].length;
    toks.replaceChildren(...A0.tokens.map((t, j) => el('span', { class: 'em-att-tok' + (j === st.q ? ' q' : '') }, t)));
    shapes.replaceChildren(document.createTextNode('Formen: '), el('span', {}, mt('X ' + n + '×' + d + ' · W_Q, W_K ' + d + '×' + dk + ' · W_V ' + d + '×' + dv + ' · Q, K ' + n + '×' + dk + ' · V ' + n + '×' + dv + ' · S, A ' + n + '×' + n + ' · O ' + n + '×' + dv + (A0.heads.length === 2 ? ' · concat(O_1, O_2) ' + n + '×' + (2 * dv) : ''))));
    const open = hs.every(k => shown.has(key(k)));
    const rows = A0.tokens.map((_, i) => tl(i)), cols = A0.tokens.map((_, j) => tl(j));
    mats.replaceChildren(mtab('X', A0.X, { rows, d: 0 }), mtab('Q = X W_Q', H.Q, { rows, hl: true }), mtab('K = X W_K', H.K, { rows }), mtab('V = X W_V', H.V, { rows }),
      mtab('S = Q K^T / √' + dk, H.S, { rows, cols, hl: true, cell: (x, i, j) => (st.causal && j > i ? '−∞' : fmS(x, 3)) }),
      mtab('A = softmax(S)', H.A, { rows, cols, hl: true, cell: (x, i) => (i === st.q && !shown.has(key(h)) ? '?' : fmt(x, 3)) }));
    const hOwn = hs.find(k => !shown.has(key(k))) ?? h; ownBox(hOwn, r.heads[hOwn].A, r.heads[hOwn].raw, r0.heads[hOwn].A[st.q]);
    /* weights of the query row as bars (after the own calculation) */
    const W = 560, bh = 26, s = sv('svg', { viewBox: `0 0 ${W} ${n * bh + 10}`, role: 'img', 'aria-label': 'Gewichte der Abfragezeile', class: 'em-chart' }); s.appendChild(sv('title', {}, 'Attention-Gewichte von ' + tl(st.q)));
    A0.tokens.forEach((t, j) => { const y = 4 + j * bh; s.appendChild(sv('text', { x: 118, y: y + 17, 'text-anchor': 'end', class: 'em-tick' }, tl(j)));
      const a = H.A[st.q][j]; if (shown.has(key(h))) { s.appendChild(sv('rect', { x: 126, y: y + 4, width: Math.max(1, a * (W - 200)), height: bh - 10, class: 'em-att-bar' })); s.appendChild(sv('text', { x: 132 + a * (W - 200), y: y + 17, class: 'em-tick' }, fmt(a, 3))); }
      else s.appendChild(sv('text', { x: 130, y: y + 17, class: 'em-tick' }, '?')); });
    bars.replaceChildren(s, el('p', { class: 'em-meta' }, mt('Gewichte α_{' + (st.q + 1) + 'j} von „' + tl(st.q) + '“ in Head ' + (h + 1) + (st.causal ? ' (mit Maske)' : '') + '.')));
    const O = st.head === 'concat' ? r.concat : H.O;
    outB.replaceChildren(mtab(st.head === 'concat' ? 'concat(O_1, O_2)' : 'O = A V', O, { rows, hl: true, cell: (x, i) => (i === st.q && !open ? '?' : fmS(x, 3)) }));
    lab.dataset.q = st.q;
  };
  for (const def of spec.params) ctrls[def.id] = param(pan, def, def.default, v => { if (def.id === 'q') st.q = Number(v); else if (def.id === 'causal') st.causal = v === 'ja'; else st.head = v; redraw(); });
  const wt = el('div', { class: 'em-att-grid' }); A0.heads.forEach((hh, k) => { wt.append(mtab('W_Q (Head ' + (k + 1) + ')', hh.Wq, { d: 0 }), mtab('W_K (Head ' + (k + 1) + ')', hh.Wk, { d: 0 }), mtab('W_V (Head ' + (k + 1) + ')', hh.Wv, { d: 0 })); });
  lab.append(toks, shapes, pan, mats, own, bars, tools(tool('Ausgabe', 'O = A V bzw. concat der Heads', true, outB), tool('Gewichtsmatrizen', 'W_Q, W_K, W_V je Head', false, wt)));
  root.appendChild(lab);
  predictFlow(root.querySelector('.em-pre'), spec, lab, ch => ctrls[ch.param].set(ch.to));
  redraw();
};

views.cap_table = (root, spec) => {
  const M0 = spec.model, d = M0.cap, POOL = 'Optionspool', shown = new Set();
  const st = { poolmode: 'data', exit: spec.params.find(p => p.id === 'exit').default, pref: 'ja' };
  const lab = el('section', { class: 'em-lab em-cap', 'aria-labelledby': 'lab-h' }); lab.appendChild(el('h2', { id: 'lab-h' }, '2 · Cap Table und Exit'));
  const pan = el('div', { class: 'em-params' }), fig = el('div', { class: 'em-figure' }), kpi = el('div', { class: 'em-kpi', role: 'status', 'aria-live': 'polite' }), own = el('div', { class: 'em-own' });
  const tab = el('div', { class: 'em-scroll' }), rtab = el('div', { class: 'em-scroll' }), wtab = el('div', { class: 'em-scroll' }); const ctrls = {};
  const eur = x => fmt(x, 0) + ' €', pc = (x, k = 1) => fmt(100 * x, k) + ' %';
  const names = [...d.founders.map(f => f.name), POOL, ...d.rounds.map(r => r.name)];
  const redraw = () => {
    const R = models.capRounds(d, st.poolmode === 'data' ? null : st.poolmode), k = Math.min(2, R.length - 1), open = shown.has(st.poolmode);
    const w = models.capWaterfall(d, R[R.length - 1], st.exit, st.pref === 'ja'), wp = models.capWaterfall(d, R[R.length - 1], st.exit, false);
    lab.dataset.founders2 = Math.round(R[k].founders_pct * 1e9) / 1e9; lab.dataset.prefTaken = w.pref_taken.length;
    const hid = (i) => i === k && !open;   /* the whole round whose founders' share is asked stays hidden: shares, quotas, bar, price, new shares */
    const hide = (i) => hid(i); const price = x => fmtF(x, x >= 0.01 ? 2 : 4) + ' €';
    /* stacked bars per round */
    const W = Math.round(Math.max(320, Math.min(720, fig.clientWidth || 640))), Hh = 250, l = 40, t = 10, ph = 200, gap = (W - l - 10) / R.length, bw = Math.min(110, gap * 0.6);
    const s = sv('svg', { viewBox: `0 0 ${W} ${Hh}`, role: 'img', 'aria-label': 'Anteile nach jeder Runde, gestapelt', class: 'em-chart' }); s.appendChild(sv('title', {}, 'Cap Table je Runde'));
    for (let p = 0; p <= 100; p += 25) { const y = t + ph * (1 - p / 100); s.appendChild(sv('line', { x1: l, x2: W - 10, y1: y, y2: y, class: 'em-grid' })); s.appendChild(sv('text', { x: l - 4, y: y + 4, 'text-anchor': 'end', class: 'em-tick' }, p + ' %')); }
    R.forEach((o, i) => { const x = l + gap * i + (gap - bw) / 2; let y = t + ph;
      if (hid(i)) { s.appendChild(sv('rect', { x, y: t, width: bw, height: ph, class: 'em-cap-pool em-cap-hidden' })); s.appendChild(sv('text', { x: x + bw / 2, y: t + ph / 2, 'text-anchor': 'middle', class: 'em-cap-t' }, '?')); s.appendChild(sv('text', { x: x + bw / 2, y: t + ph + 18, 'text-anchor': 'middle', class: 'em-tick' }, o.name)); return; }
      names.forEach((nm, c) => { const p = o.pct[nm] || 0; if (p <= 0) return; const h = ph * p; y -= h;
        const cls = 'em-cap-' + (d.founders.some(f => f.name === nm) ? 'f' + Math.min(c, 4) : nm === POOL ? 'pool' : 'i' + Math.min(c - d.founders.length - 1, 3));
        s.appendChild(sv('rect', { x, y, width: bw, height: h, class: cls }));
        if (h > 15 && bw > 44) s.appendChild(sv('text', { x: x + bw / 2, y: y + h / 2 + 4, 'text-anchor': 'middle', class: 'em-cap-t' }, pc(p, 0))); });
      s.appendChild(sv('text', { x: x + bw / 2, y: t + ph + 18, 'text-anchor': 'middle', class: 'em-tick' }, o.name)); });
    const legend = el('div', { class: 'em-legend' }); names.forEach((nm, c) => { legend.append(el('span', { class: 'em-key em-cap-' + (d.founders.some(f => f.name === nm) ? 'f' + Math.min(c, 4) : nm === POOL ? 'pool' : 'i' + Math.min(c - d.founders.length - 1, 3)) }), document.createTextNode(nm + '  ')); });
    fig.replaceChildren(s, legend);
    /* ownership table */
    const cell = (o, i, nm) => (o.holders[nm] == null ? '–' : hid(i) ? '?' : fmt(o.holders[nm], 0) + ' (' + pc(o.pct[nm]) + ')');
    const rows = names.map(nm => [nm, ...R.map((o, i) => cell(o, i, nm))]);
    rows.push(['Gründer zusammen', ...R.map((o, i) => (hid(i) ? '?' : pc(o.founders_pct)))], ['Summe Anteile', ...R.map((o, i) => (hid(i) ? '?' : fmt(o.total, 0)))]);
    table(tab, ['Gesellschafter', ...R.map(o => 'nach ' + o.name)], rows, 'Anteile (Quote), voll verwässert' + (open ? '' : ' – „?“: Runde ' + R[k].name + ' erscheint nach Ihrer eigenen Rechnung'));
    const rr = R.slice(1), ri = i => i + 1;   /* transposed: one column per round, so the table stays narrow */
    table(rtab, ['', ...rr.map(o => o.name)], [['Pre-Money', ...rr.map(o => eur(o.pre_money))], ['Investment', ...rr.map(o => eur(o.investment))],
      ['neuer Pool', ...rr.map((o, i) => pc(d.rounds[i].pool_pct, 0) + (o.mode === 'pre' ? ' vor dem Geld' : ' nach dem Geld'))], ['Post-Money (nominal)', ...rr.map(o => eur(o.post_money))],
      ['Preis je Anteil', ...rr.map((o, i) => (hid(ri(i)) ? '?' : price(o.price)))], ['neue Pool-Anteile', ...rr.map((o, i) => (hid(ri(i)) ? '?' : fmt(o.new_pool, 0)))],
      ['Investoren-Anteile', ...rr.map((o, i) => (hid(ri(i)) ? '?' : fmt(o.inv_shares, 0)))], ['Preis × alle Anteile', ...rr.map((o, i) => (hid(ri(i)) ? '?' : eur(o.post_effective)))]], 'Eingaben und Ergebnisse je Runde');
    const L = R[R.length - 1];
    table(wtab, ['Gesellschafter', 'Anteil', 'pro rata', 'Auszahlung', 'Wahl'], names.map(nm => [nm, pc(L.pct[nm]), eur(wp.payout[nm]), eur(w.payout[nm]), w.pref_taken.includes(nm) ? 'Präferenz' : d.rounds.some(r => r.name === nm) ? (st.pref === 'ja' ? 'Wandlung' : '–') : 'Stammanteile']),
      'Exit zu ' + eur(st.exit) + (st.pref === 'ja' ? ', 1x nicht-partizipierende Präferenz (pari passu)' : ', alle pro rata'));
    if (!open && k === R.length - 1) wtab.replaceChildren(el('p', { class: 'em-meta' }, 'Erst nach Ihrer eigenen Rechnung oben sichtbar: Die Exit-Verteilung verrät die Anteile nach ' + R[k].name + '. Wer die Präferenz zieht, zeigt die Kennzahl oben.'));
    const fsum = d.founders.reduce((a, f) => a + w.payout[f.name], 0);
    kpi.replaceChildren(...kv([['Gründer nach ' + R[k].name, open ? pc(R[k].founders_pct) : '?'], ['Preis je Anteil ' + R[1].name, hid(1) ? '?' : price(R[1].price)], ['Exit: an die Gründer', open || k < R.length - 1 ? eur(fsum) : '?'], ['Präferenz gezogen', w.pref_taken.length ? w.pref_taken.join(', ') : 'niemand']]));
    const ok_ = st.poolmode + '|' + open; if (own.dataset.k !== ok_) { own.dataset.k = ok_; own.replaceChildren(); }
    if (!open && !own.firstChild) { own.appendChild(el('p', { class: 'em-question' }, 'Selbst rechnen: Welchen Anteil halten die Gründer zusammen nach ' + R[k].name + '? (in %, 1 Nachkommastelle)'));
      const inp = el('input', { type: 'text', inputmode: 'decimal', 'aria-label': 'Gründeranteil in Prozent' }), go = el('button', { type: 'button', class: 'em-primary' }, 'Prüfen'), fb = el('div', { class: 'em-feedback', role: 'status', 'aria-live': 'polite' }), rv = el('button', { type: 'button', class: 'em-link' }, 'Ohne eigene Rechnung aufdecken');
      go.addEventListener('click', () => { const v = num(inp.value); if (!Number.isFinite(v)) { fb.textContent = 'Bitte eine Zahl eingeben (z. B. 48,5).'; return; }
        if (Math.abs(v - 100 * R[k].founders_pct) <= 0.06) { store.record(spec.id, 'own-founders', spec.kc_ids, 'correct'); shown.add(st.poolmode); redraw(); return; }
        store.record(spec.id, 'own-founders', spec.kc_ids, 'wrong'); let naive = 1; R.slice(1, k + 1).forEach(o => { naive *= 1 - o.investment / o.post_money; });
        fb.replaceChildren(el('strong', { class: 'em-bad' }, 'Noch nicht. '), document.createTextNode(Math.abs(v - 100 * naive) <= 0.06 ? 'Das ist das Produkt (1 − Investment/Post-Money): Die Optionspools fehlen.' : Math.abs(v - 100 * R[k - 1].founders_pct) <= 0.06 ? 'Das ist der Anteil vor dieser Runde.' : 'Gründeranteile = Summe der Gründeranteile / alle Anteile nach der Runde (Tabelle).')); });
      inp.addEventListener('keydown', e => { if (e.key === 'Enter') go.click(); });
      rv.addEventListener('click', () => { store.record(spec.id, 'own-founders', spec.kc_ids, 'solution'); shown.add(st.poolmode); redraw(); });
      const row = el('div', { class: 'em-answer' }); row.append(inp, el('span', {}, '%'), go); own.append(row, fb, rv); }
  };
  let lastW = 0; if (window.ResizeObserver) new ResizeObserver(() => { const w = fig.clientWidth; if (w && Math.abs(w - lastW) > 8) { lastW = w; redraw(); } }).observe(fig);
  for (const def of spec.params) ctrls[def.id] = param(pan, def, st[def.id], v => { st[def.id] = def.id === 'exit' ? Number(v) : v; redraw(); });
  const reset = el('button', { type: 'button' }, 'Zurücksetzen'); reset.addEventListener('click', () => { for (const def of spec.params) ctrls[def.id].set(def.default); });
  lab.append(fig, own, kpi, tools(tool('Steuerung', 'Pool-Zeitpunkt, Exit, Präferenz', true, pan, el('div', { class: 'em-buttons' }, reset)), tool('Cap Table', 'Anteile und Quoten je Runde', true, tab), tool('Runden', 'Preis, neue Anteile, Post-Money', false, rtab), tool('Exit-Wasserfall', 'Präferenz oder Wandlung', false, wtab)));
  root.appendChild(lab);
  predictFlow(root.querySelector('.em-pre'), spec, lab, ch => ctrls[ch.param].set(ch.to));
  redraw();
};

views.legal_check = (root, spec) => {
  const M0 = spec.model, els = M0.elements, ref = models.legalResult(els), st = { committed: [], hilfs: 'nein', picks: {} };
  const DEC = [['erfuellt', 'erfüllt'], ['nicht_erfuellt', 'nicht erfüllt'], ['problematisch', 'problematisch (ausführlich erörtern)']], LBL = Object.fromEntries(DEC);
  const lab = el('section', { class: 'em-lab em-legal', 'aria-labelledby': 'lab-h' }); lab.appendChild(el('h2', { id: 'lab-h' }, '2 · Prüfung Merkmal für Merkmal'));
  const caseBox = el('section', { class: 'em-legal-case', 'aria-label': 'Sachverhalt' }); caseBox.appendChild(el('h3', {}, 'Sachverhalt: ' + (M0.case.title || '')));
  if (M0.case.self_designed) caseBox.appendChild(el('p', { class: 'em-warn' }, 'Selbst konstruierter Übungsfall (fiktiv, vereinfacht; keine Rechtsberatung).'));
  const ol = el('ol'); M0.case.facts.forEach(f => ol.appendChild(el('li', {}, f))); caseBox.append(ol, el('p', { class: 'em-question' }, M0.question));
  const list = el('ol', { class: 'em-legal-list' }), res = el('div', { class: 'em-legal-result', role: 'status', 'aria-live': 'polite' }), pan = el('div', { class: 'em-params' }); const ctrls = {};
  const card = (e, i) => {
    const li = el('li', { class: 'em-legal-card', 'data-el': e.id }); const done = st.committed.includes(e.id);
    const stopI = ref.checked.length - 1, after = !ref.positive && i > stopI;
    let prog; try { prog = models.legalProgress(els, st.committed); } catch (x) { prog = { next: null, done: false }; }
    const next = prog.next === e.id || (prog.done && after && st.hilfs === 'ja' && st.committed.length === i);
    li.appendChild(el('h3', {}, (i + 1) + '. ' + e.label + (e.norm ? ' (' + e.norm + ')' : '') + (after && prog.done ? ' – hilfsgutachtlich' : '')));
    if (after && prog.done && st.hilfs !== 'ja' && !done) { li.classList.add('off'); li.appendChild(el('p', { class: 'em-meta' }, prog.done ? 'Nicht mehr zu prüfen: Die Prüfung endet beim ersten nicht erfüllten Merkmal.' : 'Wird geprüft, sobald die vorigen Punkte entschieden sind.')); return li; }
    if (!done && !next) { li.classList.add('off'); li.appendChild(el('p', { class: 'em-meta' }, 'Wird geprüft, sobald die vorigen Punkte entschieden sind (Reihenfolge des Schemas).')); return li; }
    li.appendChild(el('p', { class: 'em-meta' }, 'Obersatz: Fraglich ist, ob „' + e.label + '“ vorliegt.'));
    const df = el('p'); df.append(el('strong', {}, 'Definition: '), document.createTextNode(e.definition)); li.appendChild(df);
    const fs = el('fieldset'); fs.appendChild(el('legend', {}, 'Ihre Entscheidung'));
    DEC.forEach(([v, t]) => { const l = el('label', { class: 'em-pill' }); const r = el('input', { type: 'radio', name: 'd-' + e.id, value: v }); if (st.picks[e.id] && st.picks[e.id][0] === v) r.checked = true; l.append(r, el('span', {}, t)); fs.appendChild(l); });
    const fr = el('fieldset'); fr.appendChild(el('legend', {}, 'Tragende Begründung (Subsumtion)'));
    e.reasons.forEach(r => { const l = el('label', { class: 'em-choice' }); const x = el('input', { type: 'radio', name: 'r-' + e.id, value: r.id }); if (st.picks[e.id] && st.picks[e.id][1] === r.id) x.checked = true; l.append(x, el('span', {}, r.text)); fr.appendChild(l); });
    const fb = el('div', { class: 'em-feedback', role: 'status', 'aria-live': 'polite' }); li.append(fs, fr);
    if (done) { fs.disabled = true; fr.disabled = true; const [dv, rv] = st.picks[e.id]; const g = models.legalGrade(e, dv, rv); const rr = e.reasons.find(x => x.id === rv);
      const o = models.legalOutcome(e);
      fb.append(el('strong', { class: g === 'correct' ? 'em-ok' : g === 'partial' ? 'em-warn' : 'em-bad' }, g === 'correct' ? 'Stimmt. ' : g === 'partial' ? 'Teilweise. ' : 'Nicht zutreffend. '),
        document.createTextNode('Referenz: ' + LBL[e.decision] + (e.decision === 'problematisch' ? ' → Ergebnis der Erörterung: ' + LBL[o] : '') + '. ' + e.explanation));
      if (!rr.correct) fb.appendChild(el('p', { class: 'em-meta' }, 'Zu Ihrer Begründung: ' + rr.feedback));
      if (g === 'partial' && dv !== e.decision) fb.appendChild(el('p', { class: 'em-meta' }, e.decision === 'problematisch' ? 'Das Ergebnis stimmt, aber hier liegt ein Schwerpunkt: Im Gutachten ist dieser Punkt ausführlich zu erörtern.' : 'Dieser Punkt ist unproblematisch und kann im Gutachten kurz festgestellt werden.'));
      li.classList.add('done'); li.appendChild(fb); return li; }
    const go = el('button', { type: 'button', class: 'em-primary' }, 'Entscheidung festlegen');
    go.addEventListener('click', () => { const dv = (fs.querySelector('input:checked') || {}).value, rv = (fr.querySelector('input:checked') || {}).value;
      if (!dv || !rv) { fb.textContent = 'Bitte Entscheidung und Begründung wählen – erst dann gibt es die Rückmeldung.'; return; }
      try { models.legalProgress(els, [...st.committed, e.id]); } catch (x) { fb.textContent = x.message; return; }
      st.picks[e.id] = [dv, rv]; st.committed.push(e.id); const g = models.legalGrade(e, dv, rv);
      store.record(spec.id, 'element:' + e.id, spec.kc_ids, g === 'correct' ? 'correct' : 'wrong'); render(); const nx = list.querySelector('[data-el="' + e.id + '"]'); if (nx) nx.scrollIntoView({ block: 'nearest' }); });
    li.append(go, fb); return li;
  };
  const render = () => {
    list.replaceChildren(...els.map(card));
    let prog; try { prog = models.legalProgress(els, st.committed.slice(0, ref.checked.length)); } catch (x) { prog = { done: false }; }
    lab.dataset.committed = st.committed.length; lab.dataset.done = prog.done ? 1 : 0;
    if (!prog.done) { res.replaceChildren(el('p', { class: 'em-meta' }, 'Gesamtergebnis: erscheint, sobald alle nötigen Prüfungspunkte entschieden sind (bisher entschieden: ' + st.committed.length + ').')); return; }
    const stopE = els.find(x => x.id === ref.stop);
    res.replaceChildren(el('h3', {}, 'Ergebnis'), el('p', { class: ref.positive ? 'em-ok' : 'em-bad' }, ref.positive ? M0.rechtsfolge : M0.negative + ' Die Prüfung endet bei „' + stopE.label + '“.'),
      el('p', { class: 'em-meta' }, 'Ihre Entscheidungen: ' + st.committed.map(id => { const e = els.find(x => x.id === id); return e.label + ': ' + LBL[st.picks[id][0]]; }).join(' · ')));
  };
  for (const def of spec.params) ctrls[def.id] = param(pan, def, st[def.id], v => { st.hilfs = v; render(); });
  const reset = el('button', { type: 'button' }, 'Neu beginnen'); reset.addEventListener('click', () => { st.committed = []; st.picks = {}; render(); });
  lab.append(caseBox, list, res, tools(tool('Einstellungen', 'Hilfsgutachten, neu beginnen', false, pan, el('div', { class: 'em-buttons' }, reset))));
  root.appendChild(lab);
  predictFlow(root.querySelector('.em-pre'), spec, lab, ch => ctrls[ch.param].set(ch.to));
  render();
};

/* ------------------------------------------------------------ boot */
EM.progress = (box) => {
  let names = null; try { names = JSON.parse(box.dataset.labs || 'null'); } catch (e) { names = null; }   /* {lab id: title} of this page */
  const d = store.read(); const rows = Object.values(d).filter(r => !names || r.lab in names).filter(r => (r.ctx || '') === store.ctx);
  if (!rows.length) { box.replaceChildren(el('p', { class: 'em-meta' }, 'Noch keine Versuche in diesem Browser.')); return; }
  table(box, ['Lab', 'Schritt', 'Versuche', 'Hilfen', 'Stand'], rows.map(r => [names && names[r.lab] || r.lab, store.taskName(r.task), String(r.attempts), String(r.hints + (r.solution_viewed ? 1 : 0)), store.label(r)]), 'Beobachtete Versuche in diesem Browser');
  const clear = el('button', { type: 'button' }, 'Lernstand in diesem Browser löschen'); clear.addEventListener('click', () => { try { localStorage.removeItem(store.key); } catch (e) { } EM.progress(box); }); box.appendChild(clear);
};
EM.boot = () => {
  const specEl = document.getElementById('em-lab-spec');
  if (!specEl) { const pb = document.getElementById('em-progress'); if (pb) { store.ctx = pb.dataset.context || ''; EM.progress(pb); } document.documentElement.dataset.emReady = '1'; return; }
  const spec = JSON.parse(specEl.textContent); store.ctx = spec.context || '';
  const root = document.getElementById('em-lab'); root.appendChild(el('div', { class: 'em-pre' }));
  try { views[spec.model.kind](root, spec); }
  catch (e) { root.replaceChildren(el('p', { class: 'em-bad', role: 'alert' }, 'Das Lab konnte nicht gestartet werden: ' + e.message + '. Die statische Darstellung unten bleibt gültig.')); return; }
  const lab = root.querySelector('.em-lab'); const post = el('div', { class: 'em-post' }); root.appendChild(post);
  const ph = spec.sequence.phases || ['predict', 'observe', 'explain', 'explore', 'practice', 'transfer', 'summary'];
  if (ph.includes('explain')) explainPhase(post, spec, lab); if (ph.includes('explore')) explorePhase(post, spec, lab);
  const tasks = spec.sequence.tasks, practice = tasks.filter(t => !t.transfer), transfer = tasks.filter(t => t.transfer);
  const sec = (id, title, why) => { const s = el('section', { class: 'em-phase em-group', id }); s.appendChild(el('h2', {}, title)); if (why) s.appendChild(el('p', { class: 'em-why' }, why)); post.appendChild(s); return s; };
  const pr = sec('phase-practice', '5 · Üben', 'Erst rechnen, dann Hilfe holen: Die Hinweise kommen gestuft, die Lösung erst nach einem eigenen Versuch.');
  practice.forEach((t, k) => (t.type === 'choice' ? choiceTask : task)(pr, spec, t, 'Aufgabe ' + (k + 1) + ': '));
  if (transfer.length) { const tr = sec('phase-transfer', '6 · Übertragen', 'Dieselbe Idee in einer neuen Situation: Hier zeigt sich, ob Sie das Prinzip verstanden haben – nicht nur die Zahlen dieses Beispiels.'); transfer.forEach(t => (t.type === 'choice' ? choiceTask : task)(tr, spec, t, '')); }
  const groupDone = () => { for (const id of ['phase-practice', 'phase-transfer']) { const s = document.getElementById(id); if (s && !s.dataset.done && [...s.querySelectorAll('.em-task')].every(b => b.dataset.done)) s.dataset.done = '1'; } };
  new MutationObserver(() => { groupDone(); EM.refreshPhases(); }).observe(post, { attributes: true, subtree: true, attributeFilter: ['data-done'] });
  if (ph.includes('summary') && (spec.sequence.takeaways || []).length) summaryPhase(post, spec);
  phaseNav(root); lab.addEventListener('em-opened', () => EM.refreshPhases());
  document.documentElement.dataset.emReady = '1';
};
/* B15: embed mode (inside the learning environment): theme from the host, height reported to the host (data only) */
(() => {
  let q; try { q = new URLSearchParams(location.search); } catch (e) { return; }
  const th = q.get('theme'); if (th === 'dark' || th === 'light') document.documentElement.dataset.theme = th;
  if (q.get('embed') !== '1' || window.parent === window) return;
  document.documentElement.classList.add('em-embed');
  window.addEventListener('message', e => { const d = e.data; if (e.source === window.parent && d && d.em === 'theme' && (d.theme === 'dark' || d.theme === 'light')) document.documentElement.dataset.theme = d.theme; });
  let last = 0; const report = () => { const h = Math.ceil(document.documentElement.scrollHeight); if (Math.abs(h - last) > 2) { last = h; window.parent.postMessage({ em: 'height', h }, '*'); } };
  if (window.ResizeObserver) new ResizeObserver(report).observe(document.body); window.addEventListener('load', report); setTimeout(report, 200);
})();
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', EM.boot); else EM.boot();
})();
