/* Analysis 1 – Rechenkern des Folgen-Labors (rein, ohne DOM). Getestet in tests/test_modules.py gegen Python (fractions). */
(function (root) {
  'use strict';
  // Folgen mit bekanntem Grenzwert und, wo möglich, exakter Formel für das kleinste N(ε)
  const SEQ = {
    rational: {label: 'aₙ = (2n−1)/(n+3)', a: n => (2 * n - 1) / (n + 3), lim: 2, err: n => 7 / (n + 3),
      Nmin: e => Math.max(1, Math.floor(7 / e - 3) + 1), why: '|aₙ − 2| = 7/(n+3) < ε ⟺ n > 7/ε − 3'},
    alt: {label: 'aₙ = (−1)ⁿ·3/n', a: n => (n % 2 ? -3 : 3) / n, lim: 0, err: n => 3 / n, Nmin: e => Math.floor(3 / e) + 1, why: '|aₙ| = 3/n < ε ⟺ n > 3/ε'},
    sandwich: {label: 'aₙ = √(n+4)/(n+1)', a: n => Math.sqrt(n + 4) / (n + 1), lim: 0, err: n => Math.sqrt(n + 4) / (n + 1), Nmin: null, why: 'monoton fallend für n ≥ 1; N durch Suche'},
    sign: {label: 'aₙ = (−1)ⁿ (divergent)', a: n => (n % 2 ? -1 : 1), lim: null, err: null, Nmin: null, why: 'zwei Häufungspunkte ±1'},
    sinn: {label: 'aₙ = sin(n)/n', a: n => Math.sin(n) / n, lim: 0, err: n => Math.abs(Math.sin(n) / n), Nmin: null, why: 'nicht monoton: N nur durch Schranke 1/n sicher'},
  };
  /** Prüft „∀ n ≥ N: |aₙ − a| < ε“ auf einem Horizont; liefert erstes Gegenbeispiel. Exakte Aussage nur mit Formel. */
  function checkN(key, a, eps, N, horizon = 5000) {
    const s = SEQ[key];
    for (let n = N; n <= N + horizon; n++) if (!(Math.abs(s.a(n) - a) < eps)) return {ok: false, n, value: s.a(n)};
    return {ok: true, proven: !!(s.Nmin && a === s.lim && N >= s.Nmin(eps)), horizon};
  }
  /** Kleinstes N mit Gültigkeit auf dem Horizont (Suche von hinten); bei Formel exakt. */
  function minN(key, a, eps, horizon = 20000) {
    const s = SEQ[key];
    if (s.Nmin && a === s.lim) return {N: s.Nmin(eps), exact: true};
    let last = 0;
    for (let n = 1; n <= horizon; n++) if (!(Math.abs(s.a(n) - a) < eps)) last = n;
    return last >= horizon - 1 ? {N: null, exact: false} : {N: last + 1, exact: false};
  }
  // Rekursionen aₙ₊₁ = f(aₙ)
  const MAPS = {
    heron: {label: 'f(x) = (x + 2/x)/2 (Heron/Newton für √2)', f: x => (x + 2 / x) / 2, df: x => (1 - 2 / (x * x)) / 2, fix: [Math.SQRT2, -Math.SQRT2], dom: [-3, 3]},
    cos: {label: 'f(x) = cos x', f: Math.cos, df: x => -Math.sin(x), fix: [0.7390851332151607], dom: [-0.5, 1.6]},
    lect: {label: 'f(x) = 1/(3 + x)', f: x => 1 / (3 + x), df: x => -1 / ((3 + x) ** 2), fix: [(-3 + Math.sqrt(13)) / 2], dom: [-0.5, 1.2]},
    sqrt: {label: 'f(x) = √(3 + 2x)', f: x => Math.sqrt(3 + 2 * x), df: x => 1 / Math.sqrt(3 + 2 * x), fix: [3], dom: [-1.5, 5]},
    xinv: {label: 'f(x) = x + 1/x (kontraktiv, keine Kontraktion)', f: x => x + 1 / x, df: x => 1 - 1 / (x * x), fix: [], dom: [0.5, 12]},
  };
  function orbit(key, a1, n = 40) { const m = MAPS[key], out = [a1]; for (let i = 1; i < n; i++) { const v = m.f(out[i - 1]); if (!Number.isFinite(v)) break; out.push(v); } return out; }
  /** Lipschitz-Konstante auf [lo, hi] durch dichte Abtastung von |f'| (Näherung; exakte Werte stehen im Lehrtext). */
  function lipschitz(key, lo, hi, k = 4000) { const m = MAPS[key]; let q = 0; for (let i = 0; i <= k; i++) { const x = lo + (hi - lo) * i / k; q = Math.max(q, Math.abs(m.df(x))); } return q; }
  /** A-priori-Schranke aus dem Fixpunktsatz: |aₙ − a| ≤ qⁿ⁻¹/(1−q)·|a₂ − a₁|; kleinstes n für Toleranz tol. */
  function aprioriN(q, d1, tol) { if (!(q < 1)) return null; let n = 1; while (Math.pow(q, n - 1) / (1 - q) * d1 > tol) n++; return n; }
  function stepsTo(key, a1, tol, limit) { const o = orbit(key, a1, 200); const i = o.findIndex(v => Math.abs(v - limit) <= tol); return i < 0 ? null : i + 1; }

  /** Beweis-Zertifikat für den Fixpunktsatz auf einem abgeschlossenen Intervall [a, b] ⊂ ℝ (vollständig).
   *  Nur analytisch begründete Formeln (Monotonie von f und |f'| auf dem Intervall), keine Abtastung.
   *  Liefert die einzelnen Beweisschritte; jede Bedingung muss mit Sicherheitsabstand erfüllt sein. */
  const TOL = 1e-12;
  const CERT = {
    cos: (a, b) => { if (!(a >= 0 && b <= Math.PI / 2)) return {ok: false, why: 'Zertifikat nur für [a, b] ⊂ [0, π/2] (dort cos fallend, |cos′| = sin steigend).'};
      return {img: [Math.cos(b), Math.cos(a)], q: Math.sin(b), lemma: 'cos ist auf [0, π/2] fallend ⇒ cos([a,b]) = [cos b, cos a]; |cos′(x)| = sin x ist dort steigend ⇒ sup |f′| = sin b.'}; },
    lect: (a, b) => { if (!(a > -3)) return {ok: false, why: 'Zertifikat nur für a > −3.'};
      return {img: [1 / (3 + b), 1 / (3 + a)], q: 1 / ((3 + a) ** 2), lemma: 'f(x) = 1/(3+x) ist für x > −3 fallend ⇒ f([a,b]) = [f(b), f(a)]; |f′(x)| = 1/(3+x)² fallend ⇒ sup |f′| = 1/(3+a)².'}; },
    sqrt: (a, b) => { if (!(a > -1.5)) return {ok: false, why: 'Zertifikat nur für a > −1,5.'};
      return {img: [Math.sqrt(3 + 2 * a), Math.sqrt(3 + 2 * b)], q: 1 / Math.sqrt(3 + 2 * a), lemma: 'f(x) = √(3+2x) steigend ⇒ f([a,b]) = [f(a), f(b)]; f′(x) = 1/√(3+2x) > 0 fallend ⇒ sup |f′| = f′(a).'}; },
    heron: (a, b) => { if (!(a > 0)) return {ok: false, why: 'Zertifikat nur für a > 0.'};
      const f = MAPS.heron.f, df = MAPS.heron.df, r = Math.SQRT2;
      return {img: [a <= r && r <= b ? r : Math.min(f(a), f(b)), Math.max(f(a), f(b))], q: Math.max(Math.abs(df(a)), Math.abs(df(b))),
        lemma: 'f′(x) = (1 − 2/x²)/2 ist für x > 0 steigend ⇒ sup |f′| wird an einem Randpunkt angenommen; f fällt auf (0, √2], steigt auf [√2, ∞) ⇒ Minimum f(√2) = √2, Maximum an einem Rand.'}; },
    xinv: (a, b) => { if (!(a > 0)) return {ok: false, why: 'Zertifikat nur für a > 0.'};
      const f = MAPS.xinv.f, df = MAPS.xinv.df;
      return {img: [a <= 1 && 1 <= b ? 2 : Math.min(f(a), f(b)), Math.max(f(a), f(b))], q: Math.max(Math.abs(df(a)), Math.abs(df(b))),
        lemma: 'f′(x) = 1 − 1/x² steigend ⇒ sup |f′| an einem Rand; f fällt auf (0, 1], steigt auf [1, ∞) ⇒ Minimum f(1) = 2.'}; },
  };
  function certificate(key, a, b) {
    const steps = [];
    if (!(Number.isFinite(a) && Number.isFinite(b) && a < b)) return {ok: false, steps: [{ok: false, text: 'Ein abgeschlossenes, beschränktes Intervall [a, b] mit a < b angeben.'}]};
    steps.push({ok: true, text: `[${a}, ${b}] ist abgeschlossen in ℝ, also vollständig.`});
    const c = CERT[key](a, b);
    if (c.ok === false) return {ok: false, steps: steps.concat({ok: false, text: c.why})};
    const inv = c.img[0] >= a + TOL && c.img[1] <= b - TOL;
    steps.push({ok: inv, text: `Invarianz: f([a,b]) = [${c.img[0].toFixed(6)}, ${c.img[1].toFixed(6)}] ${inv ? '⊆' : '⊄'} [${a}, ${b}].`, lemma: c.lemma});
    const qok = c.q < 1 - TOL;
    steps.push({ok: qok, text: `Kontraktionskonstante: q = sup_{[a,b]} |f′| = ${c.q.toFixed(6)} ${qok ? '< 1' : '≥ 1'}; nach dem Mittelwertsatz |f(x) − f(y)| ≤ q|x − y| auf [a, b].`});
    return {ok: inv && qok, steps, q: c.q, img: c.img, lemma: c.lemma};
  }
  const API = {SEQ, MAPS, checkN, minN, orbit, lipschitz, aprioriN, stepsTo, certificate};
  if (typeof module !== 'undefined' && module.exports) module.exports = API; else root.AnaMath = API;
})(typeof window !== 'undefined' ? window : globalThis);
