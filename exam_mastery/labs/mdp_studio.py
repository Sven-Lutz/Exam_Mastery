"""MDP Studio (B32): a self-contained interactive learning environment for finite MDPs (graph or grid scenarios).
Generic: any course MDP with <= 12 states (graph) or a rectangular grid world can be loaded as a scenario. Everything
is computed in the browser from the declared model (no server, no network); the Python side validates the model and
computes golden reference values with the exact oracle so the E2E tests can compare the UI against independent numbers.

Scenario (JSON):
 graph: {"id","title","kind":"graph","states":[..],"labels":{s:text},"pos":{s:[x,y]},"gamma","policy":{s:a},
         "transitions":[{"s","a","r","next":{s':p}}],"editable":{"rewards":[[s,a]],"probs":[[s,a]]},"threshold":{"state","a","b"},
         "challenges":[{"id","kind":"predict|compare|diagnose|model","q","options":[..],"answer":i,"check":{...},"explain"}]}
 grid:  {"id","title","kind":"grid","cols","rows","walls":["c,r"],"terminals":{"c,r":reward},"noise","living","gamma","start":"c,r",
         "challenges":[...]}
"""
import json
from html import escape as E

from ..design_tokens import TOKENS as T


class StudioError(ValueError):
    pass


def validate(sc):
    if sc.get('kind') == 'grid':
        if not (1 <= sc['cols'] <= 8 and 1 <= sc['rows'] <= 8):
            raise StudioError('grid must be at most 8x8')
        if not 0 <= float(sc['gamma']) < 1 or not 0 <= float(sc.get('noise', 0)) < 1:
            raise StudioError('gamma and noise must lie in [0,1)')
        return sc
    S = sc['states']
    if len(S) != len(set(S)) or not 2 <= len(S) <= 12:
        raise StudioError('2..12 unique states required')
    if not 0 <= float(sc['gamma']) < 1:
        raise StudioError('gamma must lie in [0,1)')
    seen = set()
    for t in sc['transitions']:
        if t['s'] not in S or set(t['next']) - set(S) or (t['s'], t['a']) in seen:
            raise StudioError(f'bad transition {t}')
        seen.add((t['s'], t['a']))
        if abs(sum(float(p) for p in t['next'].values()) - 1) > 1e-9 or any(float(p) < 0 for p in t['next'].values()):
            raise StudioError(f'p(.|{t["s"]},{t["a"]}) is not a distribution')
    for s, a in (sc.get('policy') or {}).items():
        if (s, a) not in seen:
            raise StudioError(f'policy action {a} unavailable in {s}')
    return sc


def golden(sc):
    """Independent exact reference values for the E2E tests (graph scenarios via mdp_oracle)."""
    if sc.get('kind') == 'grid':
        return {}
    from .. import mdp_oracle as O
    m = O.normalise({'states': sc['states'], 'gamma': sc['gamma'], 'transitions': sc['transitions']})
    Vs, pols = O.optimal(m)
    out = {'V_star': {s: float(v) for s, v in Vs.items()}, 'optimal_policies': pols}
    if sc.get('policy'):
        out['V_pi'] = {s: float(v) for s, v in O.evaluate(m, sc['policy']).items()}
    out['VI'] = {k: {s: float(v) for s, v in O.sweeps(m, k)[k].items()} for k in (1, 2, 3, 10)}
    return out


CSS = """
:root{--navy:%(navy)s;--ink:%(ink)s;--muted:%(muted)s;--line:%(line)s;--wash:%(wash)s;--petrol:%(petrol)s;--petrol-l:%(petrol_l)s;
--blue:%(blue)s;--blue-l:%(blue_l)s;--gold:%(gold)s;--gold-l:%(gold_l)s;--coral:%(coral)s;--coral-l:%(coral_l)s;--green:%(green)s;--green-l:%(green_l)s;
--violet:%(violet)s;--violet-l:%(violet_l)s}
*{box-sizing:border-box}body{margin:0;font-family:'Source Sans 3','Helvetica Neue',Arial,sans-serif;color:var(--ink);background:#eef1f4;font-size:15px;line-height:1.45}
header{background:var(--navy);color:#fff;padding:14px 22px;display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between}
header h1{font-size:20px;margin:0}header .sub{opacity:.8;font-size:13px}
nav.sc{display:flex;gap:6px;flex-wrap:wrap}nav.sc button{background:transparent;border:1px solid rgba(255,255,255,.5);color:#fff;border-radius:16px;padding:5px 12px;cursor:pointer;font:inherit;font-size:13px}
nav.sc button[aria-pressed=true]{background:#fff;color:var(--navy);font-weight:700}
nav.md{display:flex;gap:2px;flex-wrap:wrap;background:#fff;border-bottom:1px solid var(--line);padding:0 18px;position:sticky;top:0;z-index:5}
nav.md button{border:none;background:none;padding:11px 12px;font:inherit;font-weight:600;color:var(--muted);cursor:pointer;border-bottom:3px solid transparent}
nav.md button[aria-selected=true]{color:var(--navy);border-bottom-color:var(--petrol)}
nav.md button:focus-visible,button:focus-visible,select:focus-visible,input:focus-visible{outline:3px solid var(--gold);outline-offset:2px}
main{max-width:1180px;margin:0 auto;padding:18px}
.grid2{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:16px}
@media (max-width:860px){.grid2{grid-template-columns:minmax(0,1fr)}}
.card{min-width:0;overflow-wrap:anywhere}.card mjx-container{display:inline-block;max-width:100%;overflow-x:auto;overflow-y:hidden;vertical-align:middle}.card table{display:block;max-width:100%;overflow-x:auto}.kpi{flex-wrap:wrap}
.card{background:#fff;border:1px solid var(--line);border-radius:8px;padding:14px 16px;margin-bottom:14px}
.card h2{font-size:16px;margin:0 0 8px;color:var(--navy)}.card h3{font-size:14px;margin:12px 0 6px;color:var(--navy)}
.lead{border-left:4px solid var(--gold);background:var(--gold-l);padding:10px 14px;border-radius:4px}
.tag{display:inline-block;font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:2px 7px;border-radius:3px;margin-right:6px}
.t-def{background:var(--petrol-l);color:var(--petrol)}.t-ex{background:var(--blue-l);color:var(--blue)}.t-warn{background:var(--coral-l);color:var(--coral)}.t-ok{background:var(--green-l);color:var(--green)}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums;font-size:14px}th{background:var(--navy);color:#fff;text-align:left;padding:5px 8px;font-weight:600}
td{padding:5px 8px;border-bottom:1px solid var(--line)}tr.best td{background:var(--green-l);font-weight:700}tr.chg td{background:var(--gold-l)}
td.num,th.num{text-align:right}
.btns{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}
button.b{background:var(--navy);color:#fff;border:none;border-radius:5px;padding:8px 13px;font:inherit;font-weight:600;cursor:pointer}
button.b.alt{background:#fff;color:var(--navy);border:1.5px solid var(--navy)}button.b.warn{background:var(--coral)}button.b:disabled{opacity:.45;cursor:default}
label.f{display:flex;align-items:center;gap:10px;margin:6px 0;font-weight:600}label.f input[type=range]{flex:1}
input[type=number]{width:84px;padding:4px 6px;border:1px solid var(--line);border-radius:4px;font:inherit}
select{padding:4px 6px;border:1px solid var(--line);border-radius:4px;font:inherit;background:#fff}
.eqs{display:grid;gap:6px;margin:10px 0;padding:10px 12px;background:var(--wash);border-radius:6px;border-left:4px solid #3D3F96;font-size:15px}.eqs b{display:block;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:#3D3F96}
.kpi{display:flex;gap:10px;flex-wrap:wrap}.kpi div{flex:1;min-width:120px;background:var(--wash);border-radius:6px;padding:8px 10px}
.kpi b{display:block;font-size:20px;color:var(--navy)}.kpi span{font-size:12px;color:var(--muted)}
.backup{font-family:'JetBrains Mono',Menlo,monospace;font-size:13px;background:var(--wash);border-radius:6px;padding:10px;white-space:pre-wrap;line-height:1.5}
.msg{padding:9px 12px;border-radius:6px;margin:8px 0}.msg.ok{background:var(--green-l);border-left:4px solid var(--green)}.msg.bad{background:var(--coral-l);border-left:4px solid var(--coral)}
.msg.info{background:var(--blue-l);border-left:4px solid var(--blue)}.err{color:var(--coral);font-weight:700}
.opts label{display:block;border:1px solid var(--line);border-radius:6px;padding:8px 10px;margin:6px 0;cursor:pointer}
.opts label:hover{border-color:var(--petrol)}.steps4{display:flex;gap:6px;margin:6px 0 10px}.steps4 span{flex:1;text-align:center;font-size:12px;font-weight:700;padding:5px;border-radius:4px;background:var(--wash);color:var(--muted)}
.steps4 span.on{background:var(--violet);color:#fff}
svg text{font-family:'Source Sans 3',Arial,sans-serif}.hidden{display:none}
dl.gl{display:grid;grid-template-columns:auto 1fr;gap:4px 12px;margin:0}dl.gl dt{font-weight:700;color:var(--petrol)}dl.gl dd{margin:0}
footer{max-width:1180px;margin:0 auto;padding:6px 18px 30px;color:var(--muted);font-size:12px}
"""
for _k, _v in T.items():
    CSS = CSS.replace(f'%({_k})s', _v)

JS = r"""
const D = JSON.parse(document.getElementById('studio-data').textContent);
const fmt = (x, d=3) => (Math.abs(x) < 5e-13 ? 0 : x).toFixed(d);        // course format: decimal point
let sc, st;                                                                  // scenario, state
const $ = id => document.getElementById(id);
function model(s) {                                                          // normalise to {S, A{s:[a]}, T{s|a:{r,next}}, g}
  if (s.kind === 'grid') {
    const S = [], A = {}, T = {}, key = (c, r) => c + ',' + r, walls = new Set(s.walls || []);
    const D4 = {N:[0,1], E:[1,0], S:[0,-1], W:[-1,0]}, perp = {N:'EW', S:'EW', E:'NS', W:'NS'};
    for (let r = 1; r <= s.rows; r++) for (let c = 1; c <= s.cols; c++) if (!walls.has(key(c, r))) S.push(key(c, r));
    S.push('Ende');
    const mv = (k, d) => { const [c, r] = k.split(',').map(Number); const n = key(c + D4[d][0], r + D4[d][1]);
      return (S.includes(n) && n !== 'Ende') ? n : k; };
    for (const k of S) { A[k] = [];
      if (k === 'Ende') continue;
      if (k in s.terminals) { A[k] = ['Exit']; T[k + '|Exit'] = {r: +s.terminals[k], next: {'Ende': 1}}; continue; }
      for (const d of 'NESW') { const nx = {}; const add = (t, p) => nx[t] = (nx[t] || 0) + p;
        add(mv(k, d), 1 - s.noise); for (const q of perp[d]) add(mv(k, q), s.noise / 2);
        A[k].push(d); T[k + '|' + d] = {r: +(s.living || 0), next: nx}; } }
    return {S, A, T, g: +st.gamma};
  }
  const A = {}, T = {}; s.states.forEach(x => A[x] = []);
  for (const t of st.transitions) { A[t.s].push(t.a); T[t.s + '|' + t.a] = {r: +t.r, next: Object.fromEntries(Object.entries(t.next).map(([k, v]) => [k, +v]))}; }
  return {S: s.states, A, T, g: +st.gamma};
}
const q = (m, V, s, a) => { const t = m.T[s + '|' + a]; let x = t.r; for (const [n, p] of Object.entries(t.next)) x += m.g * p * V[n]; return x; };
function evaluate(m, pol) {                                                  // exact linear solve (Gauss-Jordan)
  const n = m.S.length, idx = Object.fromEntries(m.S.map((s, i) => [s, i])), M = m.S.map(() => Array(n + 1).fill(0));
  m.S.forEach((s, i) => { M[i][i] = 1; if (!m.A[s].length) return; const t = m.T[s + '|' + pol[s]]; M[i][n] += t.r;
    for (const [k, p] of Object.entries(t.next)) M[i][idx[k]] -= m.g * p; });
  for (let c = 0; c < n; c++) { let p = c; for (let r = c; r < n; r++) if (Math.abs(M[r][c]) > Math.abs(M[p][c])) p = r;
    [M[c], M[p]] = [M[p], M[c]]; for (let r = 0; r < n; r++) if (r !== c && M[r][c] !== 0) { const f = M[r][c] / M[c][c]; for (let j = c; j <= n; j++) M[r][j] -= f * M[c][j]; } }
  return Object.fromEntries(m.S.map((s, i) => [s, M[i][n] / M[i][i]]));
}
function sweep(m, V, pol) { const W = {}; for (const s of m.S) W[s] = !m.A[s].length ? 0 : pol ? q(m, V, s, pol[s]) : Math.max(...m.A[s].map(a => q(m, V, s, a))); return W; }
const greedy = (m, V, prev) => Object.fromEntries(m.S.filter(s => m.A[s].length).map(s => { const qs = m.A[s].map(a => q(m, V, s, a)), b = Math.max(...qs);
  return [s, prev && Math.abs(q(m, V, s, prev[s]) - b) < 1e-12 ? prev[s] : m.A[s][qs.findIndex(x => Math.abs(x - b) < 1e-12)]]; }));
const norm = (U, V) => Math.max(...Object.keys(U).map(k => Math.abs(U[k] - V[k])));
const zeros = m => Object.fromEntries(m.S.map(s => [s, 0]));
function optimal(m) { let pol = Object.fromEntries(m.S.filter(s => m.A[s].length).map(s => [s, m.A[s][0]])), V;
  for (let i = 0; i < 200; i++) { V = evaluate(m, pol); const np = greedy(m, V, pol); if (JSON.stringify(np) === JSON.stringify(pol)) return {V, pol}; pol = np; } return {V, pol}; }
const label = s => (sc.labels && sc.labels[s]) || s;

/* ---------- drawing ---------- */
function heat(v, lo, hi) { if (v >= 0) { const t = Math.min(1, v / (hi || 1)) * .85; return `rgb(${255 - t * 160},${255 - t * 86},${255 - t * 89})`; }
  const t = Math.min(1, v / (lo || -1)) * .85; return `rgb(${255 - t * 26},${255 - t * 117},${255 - t * 131})`; }
function drawGraph(V, pol, focus) {
  const m = model(sc), W = sc.w || 560, H = sc.h || 320, P = sc.pos || {}, svg = [];
  const xy = s => P[s] || [80 + 400 * (m.S.indexOf(s) / Math.max(1, m.S.length - 1)), 160];
  // B33: label placement with collision avoidance (first free candidate position wins; states are obstacles too)
  const boxes = m.S.map(s => { const [x, y] = xy(s); return [x - 34, y - 34, x + 34, y + 34]; });
  const hit = (b) => boxes.some(o => b[0] < o[2] && b[2] > o[0] && b[1] < o[3] && b[3] > o[1]);
  const place = (x, y, txt, size) => { const w = txt.length * size * .58 + 4, h = size + 3;
    for (const [dx, dy] of [[0, 0], [0, -14], [0, 14], [18, 0], [-18, 0], [0, -26], [0, 26], [26, -14], [-26, 14]]) {
      const b = [x + dx - w / 2, y + dy - h + 2, x + dx + w / 2, y + dy + 2]; if (!hit(b)) { boxes.push(b); return [x + dx, y + dy]; } }
    boxes.push([x - w / 2, y - h + 2, x + w / 2, y + 2]); return [x, y]; };
  svg.push(`<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10z" fill="#0B6E6E"/></marker>
    <marker id="ac" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10z" fill="#B53A2C"/></marker></defs>`);
  for (const s of m.S) for (const [ai, a] of m.A[s].entries()) {
    const [x, y] = xy(s), on = pol && pol[s] === a, t = m.T[s + '|' + a];
    const ang = (-90 + (ai - (m.A[s].length - 1) / 2) * 52) * Math.PI / 180, AP = (sc.apos || {})[s + '|' + a];
    const ax = AP ? AP[0] : x + Math.cos(ang) * 58, ay = AP ? AP[1] : y + Math.sin(ang) * 58;
    svg.push(`<line x1="${x}" y1="${y}" x2="${ax}" y2="${ay}" stroke="${on ? '#B53A2C' : '#16263D'}" stroke-width="${on ? 3 : 1.4}"/>`);
    const atxt = `${a} · r=${fmt(t.r, 1)}`, [lx, ly] = place(ax, AP && AP[1] > y ? ay + 20 : ay - 11, atxt, 12.5);
    svg.push(`<circle cx="${ax}" cy="${ay}" r="6.5" fill="${on ? '#B53A2C' : '#16263D'}"/><text x="${lx}" y="${ly}" font-size="12.5" text-anchor="middle" font-weight="700" fill="${on ? '#B53A2C' : '#16263D'}" paint-order="stroke" stroke="#fff" stroke-width="3">${a} · r=${fmt(t.r, 1)}</text>`);
    for (const [n, p] of Object.entries(t.next)) { const [nx, ny] = xy(n); const dx = nx - ax, dy = ny - ay, L = Math.hypot(dx, dy) || 1;
      if (n === s) { const dx0 = x - ax, dy0 = y - ay, L0 = Math.hypot(dx0, dy0) || 1, ex = x - dx0 / L0 * 34, ey = y - dy0 / L0 * 34, mx = (ax + ex) / 2 + dy0 / L0 * 26, my = (ay + ey) / 2 - dx0 / L0 * 26;
        svg.push(`<path d="M${ax},${ay} Q${mx},${my} ${ex},${ey}" fill="none" stroke="${on ? '#B53A2C' : '#0B6E6E'}" stroke-dasharray="${on ? '' : '4 3'}" stroke-width="${on ? 2 : 1.3}" marker-end="url(#${on ? 'ac' : 'ar'})"/>`);
        const [qx, qy] = place(mx, my, `p=${fmt(p, 2)}`, 11.5);
        svg.push(`<text x="${qx}" y="${qy}" font-size="11.5" font-weight="700" text-anchor="middle" paint-order="stroke" stroke="#fff" stroke-width="3" fill="${on ? '#B53A2C' : '#0B6E6E'}">p=${fmt(p, 2)}</text>`); continue; }
      const ex = nx - dx / L * 34, ey = ny - dy / L * 34, mx = (ax + ex) / 2 - dy / L * 18, my = (ay + ey) / 2 + dx / L * 18;
      svg.push(`<path d="M${ax},${ay} Q${mx},${my} ${ex},${ey}" fill="none" stroke="${on ? '#B53A2C' : '#0B6E6E'}" stroke-dasharray="${on ? '' : '4 3'}" stroke-width="${on ? 2 : 1.3}" marker-end="url(#${on ? 'ac' : 'ar'})"/>`);
      const [qx, qy] = place(mx, my, `p=${fmt(p, 2)}`, 11.5);
      svg.push(`<text x="${qx}" y="${qy}" font-size="11.5" font-weight="700" paint-order="stroke" stroke="#fff" stroke-width="3" fill="${on ? '#B53A2C' : '#0B6E6E'}" text-anchor="middle">p=${fmt(p, 2)}</text>`); } }
  for (const s of m.S) { const [x, y] = xy(s), term = !m.A[s].length;
    svg.push(`<circle cx="${x}" cy="${y}" r="32" fill="${focus === s ? '#FBF2DE' : '#E2F0F0'}" stroke="${focus === s ? '#8A5A00' : '#0B6E6E'}" stroke-width="${focus === s ? 3.5 : 2}" ${term ? 'stroke-dasharray="4 3"' : ''}/>`);
    svg.push(`<text x="${x}" y="${y - 3}" font-size="13.5" font-weight="800" text-anchor="middle" fill="#16263D">${label(s)}</text>`);
    if (V) svg.push(`<text x="${x}" y="${y + 15}" font-size="12.5" text-anchor="middle" fill="#24578F" font-weight="700" data-v="${s}">V=${fmt(V[s], 2)}</text>`); }
  return `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Zustandsgraph mit Aktionen, Übergangswahrscheinlichkeiten und Werten">${svg.join('')}</svg>`;
}
function drawGrid(V, pol, focus) {
  const C = sc.cols, R = sc.rows, s = 78, pad = 26, walls = new Set(sc.walls || []), out = [];
  const vals = Object.entries(V || {}).filter(([k]) => k !== 'Ende').map(([, v]) => v), lo = Math.min(0, ...vals), hi = Math.max(0, ...vals);
  const arr = {N: [0, -1], E: [1, 0], S: [0, 1], W: [-1, 0]};
  for (let r = R; r >= 1; r--) for (let c = 1; c <= C; c++) { const k = c + ',' + r, x = pad + (c - 1) * s, y = 6 + (R - r) * s;
    if (walls.has(k)) { out.push(`<rect x="${x}" y="${y}" width="${s}" height="${s}" fill="#16263D"/>`); continue; }
    out.push(`<rect x="${x}" y="${y}" width="${s}" height="${s}" fill="${V ? heat(V[k], lo, hi) : '#fff'}" stroke="${focus === k ? '#8A5A00' : '#CBD3DC'}" stroke-width="${focus === k ? 4 : 1}" data-cell="${k}" tabindex="0" role="button" aria-label="Zelle ${k}"/>`);
    if (k in sc.terminals) out.push(`<rect x="${x + 4}" y="${y + 4}" width="${s - 8}" height="${s - 8}" fill="none" stroke="#16263D" stroke-width="2"/>`);
    if (V) out.push(`<text x="${x + s / 2}" y="${y + s / 2 + 18}" font-size="14" font-weight="800" text-anchor="middle" fill="#16263D" data-v="${k}">${fmt(V[k], 2)}</text>`);
    if (pol && pol[k] && pol[k] !== 'Exit') { const [dx, dy] = arr[pol[k]], cx = x + s / 2, cy = y + s / 2 - 8;
      out.push(`<line x1="${cx - dx * 12}" y1="${cy - dy * 12}" x2="${cx + dx * 14}" y2="${cy + dy * 14}" stroke="#16263D" stroke-width="3" marker-end="url(#ag)"/>`); } }
  for (let c = 1; c <= C; c++) out.push(`<text x="${pad + (c - .5) * s}" y="${6 + R * s + 16}" font-size="12" text-anchor="middle" fill="#556273">${c}</text>`);
  for (let r = 1; r <= R; r++) out.push(`<text x="${12}" y="${6 + (R - r + .5) * s + 4}" font-size="12" text-anchor="middle" fill="#556273">${r}</text>`);
  return `<svg viewBox="0 0 ${pad + C * s + 6} ${R * s + 28}" width="100%" role="img" aria-label="Gitterwelt mit Wert-Heatmap und Policy-Pfeilen"><defs><marker id="ag" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10z" fill="#16263D"/></marker></defs>${out.join('')}</svg>`;
}
const draw = (V, pol, f) => sc.kind === 'grid' ? drawGrid(V, pol, f) : drawGraph(V, pol, f);
function plot(series, ylab, xlab = 'Sweep k') {                                               // log residual plot
  const W = 520, H = 200, L = 46, B = 26, all = series.flatMap(s => s.v).filter(v => v > 0); if (!all.length) return '';
  const lo = Math.floor(Math.log10(Math.min(...all))), hi = Math.ceil(Math.log10(Math.max(...all))), n = Math.max(...series.map(s => s.v.length));
  const X = i => L + 14 + i / Math.max(1, n - 1) * (W - L - 38), Y = v => 10 + (hi - Math.log10(v)) / Math.max(1, hi - lo) * (H - B - 10), out = [];
  for (let e = lo; e <= hi; e++) out.push(`<line x1="${L}" x2="${W - 10}" y1="${Y(10 ** e)}" y2="${Y(10 ** e)}" stroke="#E4E8EC"/><text x="${L - 4}" y="${Y(10 ** e) + 4}" font-size="10" text-anchor="end" fill="#556273">1e${e}</text>`);
  series.forEach((s, j) => { const pts = s.v.map((v, i) => v > 0 ? `${X(i)},${Y(v)}` : null).filter(Boolean);
    if (s.v.length <= 12) {                 // B33: few iterations -> points, never a line that suggests a continuum
      s.v.forEach((v, i) => { if (v > 0) out.push(`<circle cx="${X(i)}" cy="${Y(v)}" r="5" fill="${s.c}"/>` + (v <= 1e-12 ? `<text x="${X(i) - 8}" y="${Y(v) - 8}" font-size="11" text-anchor="end" fill="${s.c}" font-weight="700">exakt 0</text>` : `<text x="${X(i) + 8}" y="${Y(v) + 4}" font-size="11" fill="${s.c}">${v.toExponential(2)}</text>`)); });
      out.push(`<text x="${W - 12}" y="${16 + j * 14}" text-anchor="end" font-size="11" fill="${s.c}" font-weight="700">${s.n}</text>`); return; }
    out.push(`<polyline points="${pts.join(' ')}" fill="none" stroke="${s.c}" stroke-width="2.2" ${s.dash ? 'stroke-dasharray="6 4"' : ''}/><text x="${W - 12}" y="${16 + j * 14}" text-anchor="end" font-size="11" fill="${s.c}" font-weight="700">${s.n}</text>`); });
  out.push(`<text x="${(W + L) / 2}" y="${H - 4}" font-size="11" text-anchor="middle" fill="#556273">${xlab}</text><text x="12" y="${H / 2}" font-size="11" fill="#556273" transform="rotate(-90 12 ${H / 2})" text-anchor="middle">${ylab}</text>`);
  return `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Konvergenzverlauf, logarithmisch">${out.join('')}</svg>`;
}
function backupText(m, V, s, a) { const t = m.T[s + '|' + a]; let parts = [], sum = t.r;
  for (const [n, p] of Object.entries(t.next)) { parts.push(`${fmt(p, 2)}·${fmt(V[n], 3)}`); sum += m.g * p * V[n]; }
  return `Q(${label(s)}, ${a}) = r + γ·Σ p·V(s')\n          = ${fmt(t.r, 2)} + ${fmt(m.g, 2)}·(${parts.join(' + ')})\n          = ${fmt(sum, 4)}`; }

/* ---------- views ---------- */
const MODES = [['start', 'Start'], ['model', 'Modell'], ['policy', 'Policy-Explorer'], ['vi', 'Wertiteration'], ['pi', 'Policy Iteration'], ['compare', 'VI vs. PI'], ['gamma', 'Diskont γ'], ['tasks', 'Aufgaben']];
function reset(keepModel) {
  if (!keepModel) st = {mode: st && st.mode, gamma: +sc.gamma, transitions: JSON.parse(JSON.stringify(sc.transitions || []))};
  const m = model(sc); st.policy = Object.fromEntries(m.S.filter(s => m.A[s].length).map(s => [s, (sc.policy && sc.policy[s]) || m.A[s][0]]));
  st.V = zeros(m); st.k = 0; st.res = []; st.vhist = [st.V]; st.pi = {pol: {...st.policy}, phase: 'evaluate', iter: 0, log: [], done: false};
  st.focus = m.S.find(s => m.A[s].length > 1) || m.S[0]; st.task = 0; st.stage = 0; st.err = ''; st.cmpPred = null;
}
function setScenario(i) { sc = D.scenarios[i]; reset(false);
  document.querySelectorAll('nav.sc button').forEach((b, j) => b.setAttribute('aria-pressed', i === j)); render(); }
function setMode(id) { st.mode = id; document.querySelectorAll('nav.md button').forEach(b => b.setAttribute('aria-selected', b.dataset.m === id)); render(); }
function render() { const m = model(sc), v = $('view'); v.innerHTML = ({start, model: modelView, policy, vi, pi, compare, gamma, tasks})[st.mode || 'start'](m); bind(m); if (window.MathJax && MathJax.typeset) MathJax.typeset(); }
function start(m) {
  return `<div class="grid2"><div><div class="card"><h2>${sc.title}</h2><p class="lead">${sc.intro || ''}</p>
  <h3>So arbeiten Sie mit dem Studio</h3><ol><li><b>Modell</b>: Zustände, Aktionen, Belohnungen und Übergänge ansehen (und begrenzt verändern).</li>
  <li><b>Policy-Explorer</b>: eine Policy wählen und sehen, welche Werte \\(V^\\pi\\) und \\(Q^\\pi\\) daraus folgen.</li>
  <li><b>Wertiteration</b> und <b>Policy Iteration</b>: Schritt für Schritt rechnen, jeden Bellman-Backup nachprüfen.</li>
  <li><b>Diskont γ</b>: Wann kippt die optimale Policy?</li><li><b>Aufgaben</b>: erst vorhersagen, dann simulieren, dann erklären.</li></ol></div></div>
  <div><div class="card">${draw(null, null, st.focus)}</div><div class="card"><h2>Begriffe</h2><dl class="gl">
  <dt>Zustand s</dt><dd>Lage des Systems${sc.kind === 'grid' ? ' (Zelle)' : ''}</dd><dt>Aktion a</dt><dd>Wahl des Agenten im Zustand</dd>
  <dt>p(s′|s,a)</dt><dd>Wahrscheinlichkeit, nach a in s′ zu landen</dd><dt>r(s,a)</dt><dd>erwartete Sofortbelohnung</dd>
  <dt>γ</dt><dd>Diskontfaktor in [0, 1): Gewicht einer Belohnung einen Schritt später</dd><dt>\\(V^\\pi(s)\\)</dt><dd>erwarteter diskontierter Ertrag ab s unter Policy π</dd>
  <dt>\\(Q^\\pi(s,a)\\)</dt><dd>dasselbe, wenn zuerst a gewählt wird</dd></dl></div></div></div>`; }
function modelView(m) {
  const rows = sc.kind === 'grid' ? '' : m.S.flatMap(s => m.A[s].map(a => { const t = m.T[s + '|' + a], ed = (sc.editable || {});
    const er = (ed.rewards || []).some(([x, y]) => x === s && y === a), ep = (ed.probs || []).some(([x, y]) => x === s && y === a);
    const nx = Object.entries(t.next).map(([n, p]) => ep ? `${label(n)}: <input type="number" step="0.05" min="0" max="1" value="${p}" data-p="${s}|${a}|${n}" aria-label="p(${n}|${s},${a})">` : `${label(n)}: ${fmt(p, 2)}`).join(' · ');
    return `<tr><td>${label(s)}</td><td>${a}</td><td class="num">${er ? `<input type="number" step="0.5" min="-20" max="20" value="${t.r}" data-r="${s}|${a}" aria-label="r(${s},${a})">` : fmt(t.r, 2)}</td><td>${nx}</td></tr>`; })).join('');
  return `<div class="grid2"><div class="card"><h2>Das Modell</h2>${sc.kind === 'grid'
    ? `<p>Gitter ${sc.cols}×${sc.rows}; Rauschen ${fmt(sc.noise, 2)}: Die gewählte Richtung gelingt mit ${fmt(1 - sc.noise, 2)}, je ${fmt(sc.noise / 2, 2)} weicht der Agent nach links oder rechts ab; gegen eine Wand bleibt er stehen. Ausgänge: ${Object.entries(sc.terminals).map(([k, v]) => k + ' (' + fmt(+v, 0) + ')').join(', ')}; Living reward ${fmt(+sc.living || 0, 2)}.</p>`
    : `<table><thead><tr><th>Zustand</th><th>Aktion</th><th class="num">r(s,a)</th><th>Übergänge p(s′|s,a)</th></tr></thead><tbody>${rows}</tbody></table>
       <p class="err" id="err">${st.err || ''}</p><div class="btns"><button class="b alt" id="apply">Änderungen prüfen und übernehmen</button><button class="b warn" id="reset">Auf Kursmodell zurücksetzen</button></div>`}
  <label class="f">γ = <input type="range" min="0" max="0.99" step="0.01" value="${st.gamma}" id="g" aria-label="Diskontfaktor"><output id="gv">${fmt(st.gamma, 2)}</output></label></div>
  <div class="card">${draw(null, st.policy, st.focus)}<p class="msg info">Gestrichelt: Übergänge (Umwelt würfelt). Rot: von der aktuellen Policy gewählte Aktion. Doppelt umrandet: Ausgang/Endzustand.</p></div></div>`; }
function qtable(m, V, pol, prev) {
  return `<table><thead><tr><th>Zustand</th>${'<th>Aktion</th><th class="num">Q(s,a)</th>'}<th>Policy</th></tr></thead><tbody>${m.S.filter(s => m.A[s].length).flatMap(s => {
    const qs = m.A[s].map(a => q(m, V, s, a)), b = Math.max(...qs);
    return m.A[s].map((a, i) => `<tr class="${Math.abs(qs[i] - b) < 1e-9 ? 'best' : ''}${prev && prev[s] !== pol[s] && pol[s] === a ? ' chg' : ''}"><td>${i ? '' : label(s)}</td><td>${a}</td><td class="num" data-q="${s}|${a}">${fmt(qs[i], 3)}</td><td>${pol[s] === a ? '◀ gewählt' : ''}</td></tr>`); }).join('')}</tbody></table>`; }
function policy(m) {
  const V = evaluate(m, st.policy), sel = m.S.filter(s => m.A[s].length > 1 && (sc.kind !== 'grid')).map(s => `<label class="f">${label(s)}: <select data-pol="${s}" aria-label="Aktion in ${label(s)}">${m.A[s].map(a => `<option ${st.policy[s] === a ? 'selected' : ''}>${a}</option>`).join('')}</select></label>`).join('');
  const better = greedy(m, V, st.policy), imp = Object.keys(better).filter(s => better[s] !== st.policy[s]);
  return `<div class="grid2"><div class="card"><h2>Policy wählen, Werte ablesen</h2>${sc.kind === 'grid' ? '<p>Klicken Sie eine Zelle an und wählen Sie ihre Richtung:</p>' + `<label class="f">Zelle ${st.focus}: <select data-pol="${st.focus}">${(m.A[st.focus] || []).map(a => `<option ${st.policy[st.focus] === a ? 'selected' : ''}>${a}</option>`).join('')}</select></label>` : sel}
  <div class="kpi">${m.S.filter(s => s !== 'Ende').slice(0, 6).map(s => `<div><b data-vpi="${s}">${fmt(V[s], 3)}</b><span>\\(V^\\pi\\)(${label(s)})</span></div>`).join('')}</div>
  <h3>Q-Werte unter dieser Policy</h3>${qtable(m, V, st.policy)}
  <p class="msg ${imp.length ? 'bad' : 'ok'}" id="imp">${imp.length ? `Verbesserbar in ${imp.map(label).join(', ')}: dort hat eine andere Aktion ein größeres Q. Genau das nutzt der Verbesserungsschritt der Policy Iteration.` : 'Keine Aktion hat ein größeres Q als die gewählte: Die Policy erfüllt die Bellman-Optimalitätsgleichung und ist optimal.'}</p></div>
  <div class="card">${draw(V, st.policy, st.focus)}<h3>Bellman-Backup im markierten Zustand</h3><div class="backup" id="bk">${m.A[st.focus] && m.A[st.focus].length ? backupText(m, V, st.focus, st.policy[st.focus]) : '—'}</div></div></div>`; }
function vi(m) {
  const V = st.V, pol = greedy(m, V), res = st.res;
  return `<div class="grid2"><div class="card"><h2>Wertiteration Sweep für Sweep</h2><p>\\(V_{k+1}(s) = \\max_a \\big( r(s,a) + \\gamma \\sum_{s'} p(s'\\mid s,a) V_k(s') \\big)\\), synchron: rechts stehen nur Werte des vorigen Sweeps.</p>
  <div class="btns"><button class="b" id="sw">Ein Sweep</button><button class="b alt" id="sw10">10 Sweeps</button><button class="b alt" id="conv">Bis Residuum &lt; 10⁻⁶</button><button class="b warn" id="vr">Zurück auf V₀ = 0</button></div>
  <div class="kpi"><div><b id="kk">${st.k}</b><span>Sweeps k</span></div><div><b id="rr">${res.length ? res[res.length - 1].toExponential(2) : '—'}</b><span>Residuum ‖V_k − V_{k−1}‖∞</span></div>
  <div><b id="bd">${res.length && m.g > 0 ? (m.g / (1 - m.g) * res[res.length - 1]).toExponential(2) : '—'}</b><span>Schranke γ/(1−γ)·Residuum für ‖V_k − V*‖∞</span></div></div>
  <h3>Verlauf</h3>${plot([{n: 'Residuum', v: res, c: '#0B6E6E'}, {n: 'Schranke', v: res.map(r => m.g / (1 - m.g) * r), c: '#B53A2C', dash: 1}], 'log-Skala')}
  <table><thead><tr><th>k</th>${m.S.filter(s => s !== 'Ende').slice(0, 6).map(s => `<th class="num">${label(s)}</th>`).join('')}</tr></thead><tbody>${st.vhist.slice(-6).map((W, i, a) => `<tr><td>${st.k - a.length + 1 + i}</td>${m.S.filter(s => s !== 'Ende').slice(0, 6).map(s => `<td class="num">${fmt(W[s], 3)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>
  <div class="card">${draw(V, pol, st.focus)}<h3>Backup im markierten Zustand (${label(st.focus)})</h3><div class="backup" id="bk">${(m.A[st.focus] || []).map(a => backupText(m, st.vhist[Math.max(0, st.vhist.length - 2)], st.focus, a)).join('\n') || '—'}</div>
  <p class="msg info">Pfeile/rote Aktionen = gierige Policy zu \\(V_k\\). Beobachten Sie: Die Policy steht oft fest, lange bevor die Werte konvergieren.</p></div></div>`; }
function pi(m) {
  const P = st.pi, V = P.V || zeros(m);
  return `<div class="grid2"><div class="card"><h2>Policy Iteration</h2><div class="steps4"><span class="${P.phase === 'evaluate' ? 'on' : ''}">1 Bewerten</span><span class="${P.phase === 'improve' ? 'on' : ''}">2 Verbessern</span><span class="${P.done ? 'on' : ''}">Stopp</span></div>
  <p>${P.done ? '<b>Konvergiert:</b> Der Verbesserungsschritt ändert keine Aktion mehr. Gleichstände bleiben bei der alten Aktion – sonst könnte die Iteration zwischen gleich guten Policies pendeln.' : P.phase === 'evaluate' ? 'Nächster Schritt: <b>Bewerten</b> – das lineare Gleichungssystem \\(V = r_\\pi + \\gamma P_\\pi V\\) exakt lösen.' : 'Nächster Schritt: <b>Verbessern</b> – in jedem Zustand die Aktion mit größtem \\(Q^\\pi\\) wählen.'}</p>
  <div class="btns"><button class="b" id="pstep" ${P.done ? 'disabled' : ''}>${P.phase === 'evaluate' ? 'Bewerten' : 'Verbessern'}</button><button class="b warn" id="preset">Neu starten</button>
  ${sc.kind === 'grid' ? '' : `<label class="f">Start: ${m.S.filter(s => m.A[s].length > 1).map(s => `<select data-p0="${s}">${m.A[s].map(a => `<option ${P.pol[s] === a ? 'selected' : ''}>${a}</option>`).join('')}</select>`).join(' ')}</label>`}</div>
  ${P.V ? qtable(m, V, P.pol, P.prev) : ''}<h3>Protokoll</h3><ol id="plog">${P.log.map(x => `<li>${x}</li>`).join('')}</ol></div>
  <div class="card">${draw(P.V || null, P.pol, st.focus)}</div></div>`; }
function compare(m) {
  // B34: both algorithms on the same model, measured against V* AND against the arithmetic they cost. A VI sweep is
  // sum_s sum_a |succ(s,a)| multiply-adds; a PI step is an exact solve (~n^3/3 for Gauss) plus one improvement sweep.
  const o = optimal(m), S = m.S.filter(s => m.A[s].length), nA = S.reduce((x, s) => x + m.A[s].length, 0), n = m.S.length;
  const sweepOps = S.reduce((x, s) => x + m.A[s].reduce((y, a) => y + Object.keys(m.T[s + '|' + a].next).length, 0), 0);
  const solveOps = Math.round(n * n * n / 3 + n * n);
  let V = zeros(m); const vi = [], viW = []; let k = 0, kPol = null, w = 0;
  while (k < 400) { V = sweep(m, V); k++; w += sweepOps; const e = norm(V, o.V); vi.push(e); viW.push(w); const g = greedy(m, V);
    if (kPol === null && S.every(s => q(m, o.V, s, g[s]) >= q(m, o.V, s, o.pol[s]) - 1e-9)) kPol = k; if (e < 1e-6) break; }
  let pol = {...st.policy}; const pe = [], peW = [], rows = []; w = 0;
  for (let it = 1; it <= 50; it++) { const Vp = evaluate(m, pol), e = norm(Vp, o.V); w += solveOps + sweepOps; pe.push(Math.max(e, 1e-12)); peW.push(w);
    const np = greedy(m, Vp, pol), ch = S.filter(s => np[s] !== pol[s]);
    rows.push(`<tr><td>${it}</td><td class="num">${e < 1e-12 ? '0' : e.toExponential(2)}</td><td class="num">${w}</td><td>${ch.length ? ch.map(s => `${label(s)}: ${pol[s]} → ${np[s]}`).join(', ') : 'keine → Stopp'}</td></tr>`);
    if (!ch.length) break; pol = np; }
  const pred = st.cmpPred, viWork = viW[viW.length - 1], piWork = peW[peW.length - 1];
  const ask = `<div class="card"><h2>Erst vorhersagen</h2><p>Beide Verfahren lösen dasselbe MDP (γ = ${fmt(m.g, 2)}, ${n} Zustände, ${nA} Zustand-Aktion-Paare). Welches braucht <b>weniger Rechenoperationen</b>, bis es \\(V^*\\) erreicht hat (VI: Fehler &lt; 10⁻⁶)?</p>
    <div class="btns"><button class="b alt" data-cmp="vi">Wertiteration</button><button class="b alt" data-cmp="pi">Policy Iteration</button><button class="b alt" data-cmp="eq">etwa gleich</button></div>
    <p class="msg info">Tipp: Zählen Sie nicht Iterationen. Ein VI-Sweep kostet hier ${sweepOps} Multiplikationen, eine PI-Iteration ein Gleichungssystem (≈ ${solveOps}) plus einen Verbesserungssweep (${sweepOps}).</p></div>`;
  if (!pred) return `<div class="grid2">${ask}<div class="card">${draw(null, null, st.focus)}</div></div>`;
  const win = viWork < piWork ? 'vi' : 'pi', right = pred === win;
  return `<div class="grid2"><div class="card"><h2>Wertiteration und Policy Iteration im Vergleich</h2>
  <p class="msg ${right ? 'ok' : 'bad'}" id="cmp-verdict">${right ? 'Ihre Vorhersage stimmt.' : 'Ihre Vorhersage stimmt nicht.'} Hier braucht <b>${win === 'vi' ? 'die Wertiteration' : 'die Policy Iteration'}</b> weniger Operationen (${Math.min(viWork, piWork)} gegen ${Math.max(viWork, piWork)}).</p>
  <div class="eqs"><div><b>VI-Sweep</b> \\(V_{k+1}(s) = \\max_a \\big[r(s,a) + \\gamma \\sum_{s'} p(s'\\mid s,a) V_k(s')\\big]\\)</div><div><b>PI-Iteration</b> \\((I - \\gamma P_\\pi) V^\\pi = r_\\pi\\) lösen, dann \\(\\pi \\leftarrow \\arg\\max_a Q^\\pi(s,a)\\)</div></div>
  <div class="kpi"><div><b id="cmp-vi">${k}</b><span>VI-Sweeps bis Fehler &lt; 10⁻⁶ (je ${sweepOps} Operationen)</span></div><div><b id="cmp-vipol">${kPol ?? '—'}</b><span>kleinstes k, ab dem die gierige Policy zu V<sub>k</sub> optimal ist</span></div>
  <div><b id="cmp-pi">${pe.length}</b><span>PI-Iterationen (je ≈ ${solveOps + sweepOps} Operationen)</span></div>
  <div><b id="cmp-work-vi">${viWork}</b><span>Operationen VI gesamt</span></div><div><b id="cmp-work-pi">${piWork}</b><span>Operationen PI gesamt</span></div></div>
  <h3>Fehler über der geleisteten Arbeit</h3>${plotXY([{n: 'Wertiteration', x: viW, v: vi, c: '#0B6E6E'}, {n: 'Policy Iteration', x: peW, v: pe, c: '#B53A2C'}], 'Fehler ‖V − V*‖∞ (log)', 'Rechenoperationen (Multiplikationen, kumuliert)')}
  <p class="msg info">Jetzt teilen beide Kurven eine Achse mit derselben Einheit, und der Vergleich ist fair. Bei wenigen Zuständen ist das Gleichungssystem billig und PI gewinnt oft; je mehr Zustände, desto teurer wird \\(n^3\\). Die VI-Policy ist oft lange vor den Werten optimal (Spalte k).</p>
  <h3>Reflexion</h3><p>Setzen Sie im Modell γ = 0.99 und vergleichen Sie erneut: Welche Zahl wächst stark, welche kaum? Begründen Sie mit der Kontraktionsrate γ.</p>
  <div class="btns"><button class="b warn" id="cmp-again">Neu vorhersagen</button></div></div>
  <div class="card"><h3>Protokoll der Policy Iteration</h3><table><thead><tr><th>Iteration</th><th class="num">‖V<sup>π</sup> − V*‖<sub>∞</sub></th><th class="num">Operationen kumuliert</th><th>Policy-Änderungen</th></tr></thead><tbody>${rows.join('')}</tbody></table>
  ${draw(o.V, o.pol, st.focus)}</div></div>`; }
function plotXY(series, ylab, xlab) {                               // B34: shared x axis only when the unit is shared (work)
  const W = 520, H = 210, L = 46, B = 28, all = series.flatMap(s => s.v).filter(v => v > 0), xs = series.flatMap(s => s.x);
  const lo = Math.floor(Math.log10(Math.min(...all))), hi = Math.ceil(Math.log10(Math.max(...all))), xmax = Math.max(...xs);
  const X = x => L + 10 + x / xmax * (W - L - 30), Y = v => 10 + (hi - Math.log10(v)) / Math.max(1, hi - lo) * (H - B - 10), out = [];
  for (let e = lo; e <= hi; e++) out.push(`<line x1="${L}" x2="${W - 10}" y1="${Y(10 ** e)}" y2="${Y(10 ** e)}" stroke="#E4E8EC"/><text x="${L - 4}" y="${Y(10 ** e) + 4}" font-size="10" text-anchor="end" fill="#556273">1e${e}</text>`);
  for (const t of [0, .25, .5, .75, 1]) out.push(`<text x="${X(t * xmax)}" y="${H - B + 14}" font-size="10" text-anchor="middle" fill="#556273">${Math.round(t * xmax)}</text>`);
  series.forEach((s, j) => { const pts = s.v.map((v, i) => `${X(s.x[i])},${Y(Math.max(v, 1e-12))}`);
    if (s.v.length > 12) out.push(`<polyline points="${pts.join(' ')}" fill="none" stroke="${s.c}" stroke-width="2.2"/>`);
    else s.v.forEach((v, i) => out.push(`<circle cx="${X(s.x[i])}" cy="${Y(Math.max(v, 1e-12))}" r="5" fill="${s.c}"/>` + (v <= 1e-12 ? `<text x="${X(s.x[i])}" y="${Y(1e-12) - 9}" font-size="11" text-anchor="middle" fill="${s.c}" font-weight="700">exakt 0</text>` : '')));
    out.push(`<text x="${W - 12}" y="${16 + j * 14}" text-anchor="end" font-size="11" fill="${s.c}" font-weight="700">${s.n} ${s.v.length > 12 ? '—' : '●'}</text>`); });
  out.push(`<text x="${(W + L) / 2}" y="${H - 2}" font-size="11" text-anchor="middle" fill="#556273">${xlab}</text><text x="12" y="${H / 2}" font-size="11" fill="#556273" transform="rotate(-90 12 ${H / 2})" text-anchor="middle">${ylab}</text>`);
  return `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Fehler über Rechenaufwand, logarithmisch">${out.join('')}</svg>`;
}
function gamma(m) {
  if (sc.kind === 'grid') return `<div class="card"><h2>Diskont im Gitter</h2><label class="f">γ = <input type="range" min="0" max="0.99" step="0.01" value="${st.gamma}" id="g"><output>${fmt(st.gamma, 2)}</output></label>${draw(optimal(m).V, optimal(m).pol)}<p class="msg info">Kleines γ: Nur nahe Belohnungen zählen, entfernte Zellen haben kaum Wert. Großes γ: Werte breiten sich weit aus.</p></div>`;
  const th = sc.threshold, G = [], pols = [];
  for (let i = 0; i <= 98; i++) { const g = i / 100, mm = {...m, g}; const o = optimal(mm); G.push(g); pols.push(JSON.stringify(o.pol)); }
  const segs = []; pols.forEach((p, i) => { if (!segs.length || segs[segs.length - 1].p !== p) segs.push({p, from: G[i]}); });
  let exact = null;
  if (th) { const diff = g => { const mm = {...m, g}, o = optimal(mm); return q(mm, o.V, th.state, th.a) - q(mm, o.V, th.state, th.b); };
    let a = 0, b = .99; if (diff(a) * diff(b) < 0) { for (let i = 0; i < 60; i++) { const c = (a + b) / 2; if (diff(a) * diff(c) <= 0) b = c; else a = c; } exact = (a + b) / 2; } }
  const W = 560, X = g => 20 + g * (W - 40) / .99;
  const bars = segs.map((sg, i) => { const to = i + 1 < segs.length ? segs[i + 1].from : .99, P = JSON.parse(sg.p);
    return `<rect x="${X(sg.from)}" y="20" width="${X(to) - X(sg.from)}" height="34" fill="${['#E2F0F0', '#FBF2DE', '#E8F0F8', '#EEEBF7'][i % 4]}" stroke="#CBD3DC"/><text x="${(X(sg.from) + X(to)) / 2}" y="42" font-size="12" text-anchor="middle" font-weight="700" fill="#16263D">${Object.entries(P).map(([s, a]) => label(s) + ': ' + a).join(', ')}</text>`; }).join('');
  const cur = optimal(m);
  return `<div class="grid2"><div class="card"><h2>Wann kippt die optimale Policy?</h2><label class="f">γ = <input type="range" min="0" max="0.99" step="0.01" value="${st.gamma}" id="g" aria-label="Diskontfaktor"><output>${fmt(st.gamma, 2)}</output></label>
  <svg viewBox="0 0 ${W} 90" width="100%" role="img" aria-label="Regime der optimalen Policy über γ">${bars}<line x1="${X(m.g)}" x2="${X(m.g)}" y1="12" y2="62" stroke="#B53A2C" stroke-width="3"/>${[0, .25, .5, .75, .99].map(t => `<text x="${X(t)}" y="78" font-size="11" text-anchor="middle" fill="#556273">${t}</text>`).join('')}</svg>
  ${th ? `<p class="msg ok" id="thr">Numerisch gefundene Schwelle: γ ≈ <b>${exact === null ? '—' : fmt(exact, 4)}</b>${sc.threshold.exact ? ` · exakter Wert aus dem Lehrbuch: <b>${sc.threshold.exact}</b> ≈ ${fmt(eval(sc.threshold.exact), 4)}` : ''}. Genau an der Schwelle sind beide Aktionen gleich gut (Gleichstand); beide Policies sind dann optimal.</p>` : ''}
  <h3>Optimale Werte bei diesem γ</h3><div class="kpi">${m.S.map(s => `<div><b>${fmt(cur.V[s], 3)}</b><span>V*(${label(s)})</span></div>`).join('')}</div></div>
  <div class="card">${draw(cur.V, cur.pol, th ? th.state : st.focus)}${th ? `<h3>Vergleich in ${label(th.state)}</h3><div class="backup">${backupText(m, cur.V, th.state, th.a)}\n${backupText(m, cur.V, th.state, th.b)}</div>` : ''}</div></div>`; }
function tasks(m) {
  const T = sc.challenges || []; if (!T.length) return '<div class="card">Keine Aufgaben für dieses Szenario.</div>';
  const t = T[st.task], stage = st.stage;
  return `<div class="grid2"><div class="card"><h2>Aufgabe ${st.task + 1} von ${T.length}: ${t.title}</h2><div class="steps4"><span class="${stage === 0 ? 'on' : ''}">Vorhersagen</span><span class="${stage === 1 ? 'on' : ''}">Erkunden</span><span class="${stage === 2 ? 'on' : ''}">Erklären</span><span class="${stage === 3 ? 'on' : ''}">Prüfen</span></div>
  <p><b>${t.q}</b></p><div class="opts" role="radiogroup">${t.options.map((o, i) => `<label><input type="radio" name="opt" value="${i}" ${st.choice === i ? 'checked' : ''} ${stage ? 'disabled' : ''}> ${o}</label>`).join('')}</div>
  <div class="btns">${stage === 0 ? '<button class="b" id="commit">Vorhersage festlegen</button>' : ''}${stage === 1 ? '<button class="b" id="simulate">Simulation ausführen</button>' : ''}${stage >= 2 ? `<button class="b alt" id="next">Nächste Aufgabe</button>` : ''}</div>
  <div id="fb">${stage >= 2 ? `<p class="msg ${st.choice === t.answer ? 'ok' : 'bad'}">${st.choice === t.answer ? 'Ihre Vorhersage stimmt.' : 'Ihre Vorhersage stimmt nicht – das ist der interessante Fall: Woran lag es?'} Richtig: <b>${t.options[t.answer]}</b></p><p>${t.explain}</p>${t.transfer ? `<p class="msg info"><b>Transfer:</b> ${t.transfer}</p>` : ''}` : ''}</div></div>
  <div class="card" id="simbox">${stage >= 2 ? simulate(m, t) : '<p class="msg info">Legen Sie sich zuerst fest. Wer vorher eine Erwartung bildet, bemerkt Widersprüche – genau daran lernt man.</p>'}</div></div>`; }
function simulate(m, t) { const c = t.check || {}, mm = {...m, g: c.gamma !== undefined ? c.gamma : m.g};
  if (c.type === 'vpi') { const V = evaluate(mm, c.policy); return `<h3>Rechnung</h3>${draw(V, c.policy)}<div class="backup">${Object.entries(c.policy).map(([s, a]) => backupText(mm, V, s, a)).join('\n')}</div>`; }
  if (c.type === 'vi') { let V = zeros(mm); const h = [V]; for (let k = 0; k < c.k; k++) { V = sweep(mm, V); h.push(V); }
    return `<h3>${c.k} Sweeps Wertiteration (γ = ${fmt(mm.g, 2)})</h3>${draw(V, greedy(mm, V))}<table><thead><tr><th>k</th>${mm.S.filter(s => s !== 'Ende').slice(0, 6).map(s => `<th class="num">${label(s)}</th>`).join('')}</tr></thead><tbody>${h.map((W, i) => `<tr><td>${i}</td>${mm.S.filter(s => s !== 'Ende').slice(0, 6).map(s => `<td class="num">${fmt(W[s], 3)}</td>`).join('')}</tr>`).slice(-6).join('')}</tbody></table>`; }
  if (c.type === 'opt') { const o = optimal(mm); return `<h3>Optimale Policy bei γ = ${fmt(mm.g, 2)}</h3>${draw(o.V, o.pol)}<p>${Object.entries(o.pol).filter(([s]) => !c.show || c.show.includes(s)).map(([s, a]) => `${label(s)}: <b>${a}</b>`).join(' · ')}</p>`; }
  return ''; }

function bind(m) {
  document.querySelectorAll('[data-pol]').forEach(el => el.onchange = () => { st.policy[el.dataset.pol] = el.value; render(); });
  document.querySelectorAll('[data-cell]').forEach(el => { const go = () => { st.focus = el.dataset.cell; render(); }; el.onclick = go; el.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') go(); }; });
  const g = $('g'); if (g) g.oninput = () => { st.gamma = +g.value; const mm = model(sc); st.V = zeros(mm); st.k = 0; st.res = []; st.vhist = [st.V]; st.pi = {pol: {...st.policy}, phase: 'evaluate', iter: 0, log: [], done: false}; render(); };
  if ($('apply')) $('apply').onclick = () => { const tr = JSON.parse(JSON.stringify(st.transitions));
    document.querySelectorAll('[data-r]').forEach(el => { const [s, a] = el.dataset.r.split('|'); tr.find(t => t.s === s && t.a === a).r = +el.value; });
    document.querySelectorAll('[data-p]').forEach(el => { const [s, a, n] = el.dataset.p.split('|'); tr.find(t => t.s === s && t.a === a).next[n] = +el.value; });
    for (const t of tr) { const sum = Object.values(t.next).reduce((x, y) => x + +y, 0);
      if (Object.values(t.next).some(p => p < 0 || p > 1) || Math.abs(sum - 1) > 1e-9) { st.err = `Ungültig: Die Wahrscheinlichkeiten für (${label(t.s)}, ${t.a}) summieren sich zu ${fmt(sum, 3)} statt 1.`; render(); return; }
      if (Math.abs(t.r) > 20) { st.err = 'Belohnungen sind auf [−20, 20] begrenzt.'; render(); return; } }
    st.transitions = tr; st.err = ''; reset(true); render(); };
  if ($('reset')) $('reset').onclick = () => { reset(false); render(); };
  const doSweep = n => { const mm = model(sc); for (let i = 0; i < n; i++) { const W = sweep(mm, st.V); st.res.push(norm(W, st.V)); st.V = W; st.k++; st.vhist.push(W); if (st.res[st.res.length - 1] === 0) break; } render(); };
  if ($('sw')) $('sw').onclick = () => doSweep(1); if ($('sw10')) $('sw10').onclick = () => doSweep(10);
  if ($('conv')) $('conv').onclick = () => { const mm = model(sc); let n = 0; while (n < 2000) { const W = sweep(mm, st.V); const r = norm(W, st.V); st.res.push(r); st.V = W; st.k++; st.vhist.push(W); n++; if (r < 1e-6) break; } render(); };
  if ($('vr')) $('vr').onclick = () => { const mm = model(sc); st.V = zeros(mm); st.k = 0; st.res = []; st.vhist = [st.V]; render(); };
  document.querySelectorAll('[data-p0]').forEach(el => el.onchange = () => { st.pi.pol[el.dataset.p0] = el.value; st.pi.V = null; st.pi.phase = 'evaluate'; st.pi.done = false; st.pi.log = []; render(); });
  if ($('pstep')) $('pstep').onclick = () => { const P = st.pi, mm = model(sc);
    if (P.phase === 'evaluate') { P.V = evaluate(mm, P.pol); P.iter++; P.prev = null; P.log.push(`Bewertung ${P.iter}: ${mm.S.filter(s => s !== 'Ende').slice(0, 6).map(s => label(s) + ' = ' + fmt(P.V[s], 3)).join(', ')}`); P.phase = 'improve'; }
    else { const np = greedy(mm, P.V, P.pol), ch = Object.keys(np).filter(s => np[s] !== P.pol[s]); P.prev = P.pol;
      if (!ch.length) { P.done = true; P.log.push('Verbesserung: keine Änderung → optimal (Stoppkriterium).'); }
      else { P.log.push(`Verbesserung: ${ch.map(s => `${label(s)}: ${P.pol[s]} → ${np[s]}`).join(', ')}`); P.pol = np; P.phase = 'evaluate'; } }
    render(); };
  document.querySelectorAll('[data-cmp]').forEach(el => el.onclick = () => { st.cmpPred = el.dataset.cmp; render(); });
  if ($('cmp-again')) $('cmp-again').onclick = () => { st.cmpPred = null; render(); };
  if ($('preset')) $('preset').onclick = () => { st.pi = {pol: {...st.policy}, phase: 'evaluate', iter: 0, log: [], done: false}; render(); };
  if ($('commit')) $('commit').onclick = () => { const c = document.querySelector('input[name=opt]:checked'); if (!c) { alert('Bitte zuerst eine Vorhersage wählen.'); return; } st.choice = +c.value; st.stage = 1; render(); };
  if ($('simulate')) $('simulate').onclick = () => { st.stage = 2; render(); };
  if ($('next')) $('next').onclick = () => { st.task = (st.task + 1) % sc.challenges.length; st.stage = 0; st.choice = null; render(); };
}
document.querySelector('nav.sc').innerHTML = D.scenarios.map((s, i) => `<button aria-pressed="false" data-i="${i}">${s.title}</button>`).join('');
document.querySelectorAll('nav.sc button').forEach(b => b.onclick = () => { setScenario(+b.dataset.i); setMode(st.mode || 'start'); });
document.querySelector('nav.md').innerHTML = MODES.map(([id, t]) => `<button role="tab" data-m="${id}" aria-selected="false">${t}</button>`).join('');
document.querySelectorAll('nav.md button').forEach(b => b.onclick = () => setMode(b.dataset.m));
window.studio = {model: () => model(sc), evaluate, optimal, sweep, state: () => st};
setScenario(0); setMode('start');
"""


def page(scenarios, title, course, back_link='../index.html', mathjax='../../assets/tex-svg-full.js'):
    for s in scenarios:
        validate(s)
    data = json.dumps({'scenarios': scenarios}, ensure_ascii=False).replace('</', '<\\/')
    return (f'<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{E(title)}</title><style>{CSS}</style>'
            '<script>window.MathJax={tex:{inlineMath:[["\\\\(","\\\\)"]]},svg:{fontCache:"global"}};</script>'
            f'<script src="{E(mathjax)}" async></script></head><body>'
            f'<header><div><h1>{E(title)}</h1><div class="sub">{E(course)} · alle Rechnungen im Browser, exakt aus dem Modell</div></div><nav class="sc" aria-label="Szenario"></nav></header>'
            f'<nav class="md" role="tablist" aria-label="Arbeitsmodus"></nav><main id="view" aria-live="polite"></main>'
            f'<footer><a href="{E(back_link)}">← Zur Lernumgebung</a> · Zahlen im Kursformat (Dezimalpunkt). Modelle aus der Vorlesung bzw. als selbst entworfene Übung gekennzeichnet.</footer>'
            f'<script type="application/json" id="studio-data">{data}</script><script>{JS}</script></body></html>')
