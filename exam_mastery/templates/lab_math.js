/* Exam Mastery – Lab-Mathematikkern (rein, ohne DOM).
 * Jede Darstellung im Lab wird ausschließlich aus diesen Funktionen berechnet.
 * Getestet unabhängig von der Darstellung: tests/test_lab_math.py (Python-Orakel + Eigenschaften).
 */
(function (root) {
  'use strict';
  const NEG = -Infinity;

  // ---------- Vektoren ----------
  const dot = (a, b) => a.reduce((s, x, i) => s + x * b[i], 0);
  const norm = a => Math.sqrt(dot(a, a));
  const add = (a, b) => a.map((x, i) => x + b[i]);
  const sub = (a, b) => a.map((x, i) => x - b[i]);
  const scale = (a, c) => a.map(x => x * c);
  const matvec = (M, x) => M.map(r => dot(r, x));       // M: Zeilen
  const vecmat = (x, M) => M[0].map((_, j) => x.reduce((s, xi, i) => s + xi * M[i][j], 0)); // x^T M

  /** Projektion von a auf die Richtung von b (Skalar und Vektor). b=0 -> null. */
  function project(a, b) {
    const nb = norm(b);
    if (nb === 0) return {len: 0, vec: a.map(() => 0), defined: false};
    const len = dot(a, b) / nb;
    return {len, vec: scale(b, len / nb), defined: true};
  }

  // ---------- Softmax ----------
  /** Numerisch stabile Softmax mit Temperatur T>0 und optionaler Maske (false = ausgeblendet).
   *  T = 0 wird als Grenzwert behandelt: Gleichverteilung über alle Maxima. */
  function softmax(s, T = 1, mask = null) {
    const on = s.map((_, j) => !mask || mask[j]);
    const idx = s.map((_, j) => j).filter(j => on[j]);
    if (!idx.length) return s.map(() => NaN);  // vollständig maskiert: undefiniert
    const m = Math.max(...idx.map(j => s[j]));
    if (T === 0) {
      const top = idx.filter(j => s[j] === m);
      return s.map((_, j) => top.includes(j) ? 1 / top.length : 0);
    }
    if (!(T > 0)) throw new Error('Temperatur muss > 0 sein');
    const e = s.map((x, j) => on[j] ? Math.exp((x - m) / T) : 0);
    const Z = e.reduce((a, b) => a + b, 0);
    return e.map(x => x / Z);
  }
  /** Shannon-Entropie in Bit. */
  const entropy = p => -p.reduce((s, x) => s + (x > 0 ? x * Math.log2(x) : 0), 0);
  /** Jacobi-Matrix der Softmax bzgl. der (unskalierten) Scores bei Temperatur T: (diag(p)-pp^T)/T */
  function softmaxJacobian(p, T = 1) {
    return p.map((pi, i) => p.map((pj, j) => ((i === j ? pi : 0) - pi * pj) / T));
  }
  const frob = M => Math.sqrt(M.reduce((s, r) => s + r.reduce((t, x) => t + x * x, 0), 0));

  // ---------- Attention ----------
  /** Eine Query gegen alle Keys.
   * opts: {scaleBy: Zahl (Teiler, z. B. sqrt(d_k)) , T, mask}
   * Liefert alle Zwischengrößen, damit die Darstellung nichts selbst rechnet. */
  function attendOne(q, K, V, opts = {}) {
    const c = opts.scaleBy || 1, T = opts.T === undefined ? 1 : opts.T;
    const terms = K.map(k => k.map((x, i) => q[i] * x));          // q_i k_ji
    const raw = terms.map(t => t.reduce((a, b) => a + b, 0));      // q·k_j
    const scaled = raw.map(x => x / c);
    const w = softmax(scaled, T, opts.mask || null);
    const contrib = V.map((v, j) => scale(v, w[j]));
    const out = contrib.reduce((a, b) => add(a, b), V[0].map(() => 0));
    return {terms, raw, scaled, w, contrib, out, H: entropy(w), Hmax: Math.log2((opts.mask || K).filter(Boolean).length),
      proj: K.map(k => project(k, q)), J: frob(softmaxJacobian(w, T)) / c};
  }

  /** Volle Self-Attention: X (n×d) Zeilen = Token, W_Q, W_K, W_V (d×d_k), optional kausal, optional Positionsvektoren P. */
  function selfAttention(X, WQ, WK, WV, opts = {}) {
    const Xp = opts.P ? X.map((x, i) => add(x, opts.P[i])) : X;
    const Q = Xp.map(x => vecmat(x, WQ)), K = Xp.map(x => vecmat(x, WK)), V = Xp.map(x => vecmat(x, WV));
    const dk = WK[0].length, c = opts.scale === false ? 1 : Math.sqrt(dk);
    const rows = Q.map((q, i) => attendOne(q, K, V, {scaleBy: c, T: opts.T, mask: opts.causal ? K.map((_, j) => j <= i) : null}));
    return {Xp, Q, K, V, A: rows.map(r => r.w), O: rows.map(r => r.out), rows};
  }

  /** Sinus-Positionskodierung (Vaswani et al. 2017, Abschnitt 3.5). */
  function sinusPE(n, d, base = 10000) {
    return Array.from({length: n}, (_, t) => Array.from({length: d}, (_, i) => {
      const k = Math.floor(i / 2), ang = t / Math.pow(base, 2 * k / d);
      return i % 2 === 0 ? Math.sin(ang) : Math.cos(ang);
    }));
  }

  /** Deterministischer PRNG (mulberry32) + Normalverteilung (Box-Muller) für reproduzierbare Experimente. */
  function rng(seed) {
    let a = seed >>> 0;
    const u = () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
    const n = () => { let x = 0; while (x === 0) x = u(); return Math.sqrt(-2 * Math.log(x)) * Math.cos(2 * Math.PI * u()); };
    return {u, n};
  }
  /** Skalierungsexperiment: m Paare zufälliger q,k ~ N(0, I_d). Liefert Varianz der Rohscores, mittleres max-Gewicht
   *  einer Softmax über n Keys mit/ohne Skalierung und mittlere Jacobi-Norm. */
  function scalingExperiment(d, n = 8, m = 400, seed = 7) {
    const R = rng(seed), vec = () => Array.from({length: d}, R.n);
    let s1 = 0, s2 = 0, cnt = 0;
    const acc = {raw: {maxw: 0, J: 0}, scaled: {maxw: 0, J: 0}};
    for (let r = 0; r < m; r++) {
      const q = vec(), K = Array.from({length: n}, vec), sc = K.map(k => dot(q, k));
      sc.forEach(x => { s1 += x; s2 += x * x; cnt++; });
      for (const [key, c] of [['raw', 1], ['scaled', Math.sqrt(d)]]) {
        const p = softmax(sc.map(x => x / c));
        acc[key].maxw += Math.max(...p) / m;
        acc[key].J += frob(softmaxJacobian(p)) / m;
      }
    }
    const mean = s1 / cnt;
    // eine Beispielziehung (gleicher Seed) zur Anzeige der Softmax mit und ohne Skalierung
    const E = rng(seed + 1), ev = () => Array.from({length: d}, E.n), q0 = ev(), s0 = Array.from({length: n}, () => dot(q0, ev()));
    return {d, n, m, seed, varRaw: s2 / cnt - mean * mean, meanRaw: mean, ...acc,
      example: {raw: s0, wRaw: softmax(s0), wScaled: softmax(s0.map(x => x / Math.sqrt(d)))}};
  }

  // ---------- Lineare-Ketten-CRF ----------
  /** E: T×L Emissionen, A: L×L Übergänge (von→nach), s: Startwerte (L). Scores additiv (Log-Raum). */
  function pathScore(y, E, A, s) {
    let v = s[y[0]] + E[0][y[0]];
    for (let t = 1; t < y.length; t++) v += A[y[t - 1]][y[t]] + E[t][y[t]];
    return v;
  }
  function lse(xs) { const m = Math.max(...xs); return m === NEG ? NEG : m + Math.log(xs.reduce((a, x) => a + Math.exp(x - m), 0)); }
  function viterbi(E, A, s) {
    const T = E.length, L = s.length, d = [s.map((x, j) => x + E[0][j])], bp = [s.map(() => -1)];
    for (let t = 1; t < T; t++) {
      d.push([]); bp.push([]);
      for (let j = 0; j < L; j++) {
        let best = NEG, arg = 0;  // Gleichstand: kleinster Index (deterministisch)
        for (let i = 0; i < L; i++) { const v = d[t - 1][i] + A[i][j]; if (v > best) { best = v; arg = i; } }
        d[t].push(best + E[t][j]); bp[t].push(arg);
      }
    }
    let last = 0; for (let j = 1; j < L; j++) if (d[T - 1][j] > d[T - 1][last]) last = j;
    const path = [last]; for (let t = T - 1; t > 0; t--) path.unshift(bp[t][path[0]]);
    return {delta: d, bp, path, score: d[T - 1][last]};
  }
  function forward(E, A, s) {
    const T = E.length, L = s.length, a = [s.map((x, j) => x + E[0][j])];
    for (let t = 1; t < T; t++) a.push(Array.from({length: L}, (_, j) => lse(a[t - 1].map((x, i) => x + A[i][j])) + E[t][j]));
    return {alpha: a, logZ: lse(a[T - 1])};
  }
  function backward(E, A, s) {
    const T = E.length, L = s.length, b = Array(T); b[T - 1] = s.map(() => 0);
    for (let t = T - 2; t >= 0; t--) b[t] = Array.from({length: L}, (_, i) => lse(b[t + 1].map((x, j) => A[i][j] + E[t + 1][j] + x)));
    return b;
  }
  /** Randverteilungen P(y_t=j | x) über Vorwärts-Rückwärts. */
  function marginals(E, A, s) {
    const f = forward(E, A, s), b = backward(E, A, s);
    return {logZ: f.logZ, alpha: f.alpha, beta: b, P: f.alpha.map((r, t) => r.map((x, j) => Math.exp(x + b[t][j] - f.logZ)))};
  }
  /** Alle L^T Pfade (nur für kleine Gitter) – Referenz für Viterbi und Z. */
  function enumerate(E, A, s) {
    const T = E.length, L = s.length, out = [];
    const rec = (y) => { if (y.length === T) { out.push({y: y.slice(), score: pathScore(y, E, A, s)}); return; } for (let j = 0; j < L; j++) { y.push(j); rec(y); y.pop(); } };
    rec([]);
    const logZ = lse(out.map(o => o.score));
    out.forEach(o => { o.p = Math.exp(o.score - logZ); });
    out.sort((a, b) => b.score - a.score);
    return {paths: out, logZ};
  }
  /** Lokale (unabhängige) Entscheidung: argmax je Position nur aus Emissionen. */
  const localArgmax = E => E.map(r => r.reduce((b, x, j) => x > r[b] ? j : b, 0));

  // ---------- BiRNN (Elman, tanh) mit exakter Abhängigkeitsanalyse ----------
  /** X: T×d Eingaben; Parameter je Richtung {Wx: h×d, Wh: h×h, b: h}. */
  function rnn(X, P, reverse = false) {
    const T = X.length, H = P.b.length, hs = Array(T); let h = Array(H).fill(0);
    const order = reverse ? [...Array(T).keys()].reverse() : [...Array(T).keys()];
    for (const t of order) { h = add(add(matvec(P.Wx, X[t]), matvec(P.Wh, h)), P.b).map(Math.tanh); hs[t] = h; }
    return hs;
  }
  /** Exakte Jacobi-Normen ||∂h_t/∂x_j|| per Vorwärtsableitung (forward-mode, analytisch). */
  function rnnInfluence(X, P, reverse = false) {
    const T = X.length, H = P.b.length, d = X[0].length, hs = rnn(X, P, reverse);
    const order = reverse ? [...Array(T).keys()].reverse() : [...Array(T).keys()];
    const M = Array.from({length: T}, () => Array(T).fill(0));
    for (let j = 0; j < T; j++) {
      // J = ∂h/∂x_j (H×d), propagiert entlang der Laufrichtung
      let J = Array.from({length: H}, () => Array(d).fill(0));
      for (const t of order) {
        const pre = matmul(P.Wh, J);
        if (t === j) for (let a = 0; a < H; a++) for (let b = 0; b < d; b++) pre[a][b] += P.Wx[a][b];
        const g = hs[t].map(x => 1 - x * x);
        J = pre.map((r, a) => r.map(x => g[a] * x));
        M[t][j] = frob(J);
      }
    }
    return {hs, M};
  }
  function matmul(A, B) { return A.map(r => B[0].map((_, j) => r.reduce((s, x, k) => s + x * B[k][j], 0))); }

  // ---------- Spannen & Evaluation ----------
  /** conlleval-Lesart: I-X ohne passenden Vorgänger eröffnet eine Spanne; B-X immer; L/U (BILOU) schließen. */
  function spans(tags) {
    const out = []; let cur = null;
    tags.forEach((tg, i) => {
      const [p, ty] = tg === 'O' ? ['O', null] : [tg.slice(0, 1), tg.slice(2)];
      const cont = cur && cur.type === ty && (p === 'I' || p === 'L');
      if (p === 'O' || !cont || p === 'B' || p === 'U') { if (cur) out.push(cur); cur = null; }
      if (p !== 'O') { if (cont && p !== 'B' && p !== 'U') cur.end = i; else cur = {type: ty, start: i, end: i}; }
      if (cur && (p === 'L' || p === 'U')) { out.push(cur); cur = null; }
    });
    if (cur) out.push(cur);
    return out;
  }
  /** Gültige BIO-Folge: I-X nur nach B-X oder I-X. */
  const bioValid = tags => tags.every((t, i) => !t.startsWith('I-') || (i > 0 && tags[i - 1] !== 'O' && tags[i - 1].slice(2) === t.slice(2)));
  const spanKey = s => `${s.type}:${s.start}-${s.end}`;
  function encode(sp, n, scheme) {
    const t = Array(n).fill('O');
    sp.forEach(s => { for (let i = s.start; i <= s.end; i++) {
      let p = 'I';
      if (scheme === 'BIO') p = i === s.start ? 'B' : 'I';
      if (scheme === 'BILOU') p = s.start === s.end ? 'U' : i === s.start ? 'B' : i === s.end ? 'L' : 'I';
      t[i] = p + '-' + s.type; } });
    return t;
  }
  function prf(tp, fp, fn) {
    const P = tp + fp ? tp / (tp + fp) : null, R = tp + fn ? tp / (tp + fn) : null;
    const den = 2 * tp + fp + fn;
    return {tp, fp, fn, P, R, F: den ? 2 * tp / den : null};  // null = undefiniert (keine Gold- und keine System-Entität)
  }
  function spanCounts(gold, pred, type = null) {
    const f = s => !type || s.type === type;
    const G = new Set(spans(gold).filter(f).map(spanKey)), S = new Set(spans(pred).filter(f).map(spanKey));
    let tp = 0; S.forEach(x => G.has(x) && tp++);
    return prf(tp, S.size - tp, G.size - tp);
  }
  function tokenCounts(gold, pred, type = null) {
    let tp = 0, fp = 0, fn = 0;
    const ty = x => x === 'O' ? null : x.slice(2);
    gold.forEach((g, i) => { const a = ty(g), b = ty(pred[i]);
      const gi = a && (!type || a === type), pi = b && (!type || b === type);
      if (gi && pi && a === b) tp++; else { if (pi) fp++; if (gi) fn++; } });
    return prf(tp, fp, fn);
  }
  function microMacro(gold, pred, types, level = 'span') {
    const cnt = level === 'span' ? spanCounts : tokenCounts;
    const per = types.map(t => ({type: t, ...cnt(gold, pred, t)}));
    const s = per.reduce((a, r) => ({tp: a.tp + r.tp, fp: a.fp + r.fp, fn: a.fn + r.fn}), {tp: 0, fp: 0, fn: 0});
    const defined = per.filter(r => r.F !== null);
    return {per, micro: prf(s.tp, s.fp, s.fn), macro: defined.length ? defined.reduce((a, r) => a + r.F, 0) / defined.length : null};
  }

  const API = {dot, norm, add, sub, scale, matvec, vecmat, matmul, project, softmax, entropy, softmaxJacobian, frob, attendOne, selfAttention,
    sinusPE, rng, scalingExperiment, pathScore, lse, viterbi, forward, backward, marginals, enumerate, localArgmax, rnn, rnnInfluence,
    spans, spanKey, bioValid, encode, prf, spanCounts, tokenCounts, microMacro};
  if (typeof module !== 'undefined' && module.exports) module.exports = API; else root.LabMath = API;
})(typeof window !== 'undefined' ? window : globalThis);
