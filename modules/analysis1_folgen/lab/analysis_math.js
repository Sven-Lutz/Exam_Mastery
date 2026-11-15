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

  // ---------- exakte Endpunkte: kleiner Ausdrucksparser (Zahlen, pi, sqrt, cos, sin, + − * / Klammern) ----------
  // Rationale Ausdrücke (inkl. sqrt von Quadraten) werden exakt als Brüche (BigInt) ausgewertet, alles andere als Gleitkomma
  // plus kanonische Form. Damit lassen sich Randgleichheiten wie f(b) = cos 1 = a rigoros erkennen.
  const gcd = (a, b) => { a = a < 0n ? -a : a; b = b < 0n ? -b : b; while (b) [a, b] = [b, a % b]; return a; };
  const Q = (n, d = 1n) => { if (d === 0n) throw new Error('Division durch 0'); if (d < 0n) { n = -n; d = -d; } const g = gcd(n, d) || 1n; return {n: n / g, d: d / g}; };
  const qadd = (x, y) => Q(x.n * y.d + y.n * x.d, x.d * y.d), qmul = (x, y) => Q(x.n * y.n, x.d * y.d), qdiv = (x, y) => Q(x.n * y.d, x.d * y.n);
  const qcmp = (x, y) => { const v = x.n * y.d - y.n * x.d; return v > 0n ? 1 : v < 0n ? -1 : 0; };
  function isqrt(n) { if (n < 0n) return null; if (n < 2n) return n; let x = BigInt(Math.floor(Math.sqrt(Number(n)))); while (x * x > n) x--; while ((x + 1n) * (x + 1n) <= n) x++; return x * x === n ? x : null; }
  function qsqrt(x) { const a = isqrt(x.n), b = isqrt(x.d); return a !== null && b !== null ? Q(a, b) : null; }
  function decToQ(s) { const m = s.match(/^(\d+)(?:\.(\d+))?$/); if (!m) return null; const frac = m[2] || ''; return Q(BigInt(m[1] + frac), 10n ** BigInt(frac.length)); }
  function parseExpr(src) {
    if (typeof src === 'number') src = String(src);
    const s = String(src).replace(/,/g, '.').replace(/−/g, '-').replace(/π/g, 'pi').replace(/\s+/g, '').toLowerCase();
    let i = 0;
    const peek = () => s[i], eat = c => { if (s[i] === c) { i++; return true; } return false; };
    function num() { const m = s.slice(i).match(/^\d+(\.\d+)?/); if (!m) return null; i += m[0].length; return {v: parseFloat(m[0]), q: decToQ(m[0]), c: String(parseFloat(m[0]))}; }
    function atom() {
      if (eat('(')) { const x = add(); if (!eat(')')) throw new Error('Klammer fehlt'); return {...x, c: '(' + x.c + ')'}; }
      if (eat('-')) { const x = atom(); return {v: -x.v, q: x.q ? Q(-x.q.n, x.q.d) : null, c: '-' + x.c}; }
      for (const fn of ['sqrt', 'cos', 'sin']) if (s.startsWith(fn + '(', i)) { i += fn.length + 1; const x = add(); if (!eat(')')) throw new Error('Klammer fehlt');
        const v = Math[fn](x.v), q = fn === 'sqrt' && x.q ? qsqrt(x.q) : (fn !== 'sqrt' && x.q && x.q.n === 0n ? Q(fn === 'cos' ? 1n : 0n) : null);
        return {v, q, c: `${fn}(${x.c})`}; }
      if (s.startsWith('pi', i)) { i += 2; return {v: Math.PI, q: null, c: 'pi'}; }
      const n = num(); if (n) return n; throw new Error('Ausdruck nicht lesbar');
    }
    function mul() { let x = atom(); for (;;) { if (eat('*')) { const y = atom(); x = {v: x.v * y.v, q: x.q && y.q ? qmul(x.q, y.q) : null, c: x.c + '*' + y.c}; } else if (eat('/')) { const y = atom(); x = {v: x.v / y.v, q: x.q && y.q ? qdiv(x.q, y.q) : null, c: x.c + '/' + y.c}; } else return x; } }
    function add() { let x = mul(); for (;;) { if (eat('+')) { const y = mul(); x = {v: x.v + y.v, q: x.q && y.q ? qadd(x.q, y.q) : null, c: x.c + '+' + y.c}; } else if (peek() === '-') { i++; const y = mul(); x = {v: x.v - y.v, q: x.q && y.q ? qadd(x.q, Q(-y.q.n, y.q.d)) : null, c: x.c + '-' + y.c}; } else return x; } }
    const r = add(); if (i !== s.length) throw new Error('Ausdruck nicht lesbar');
    return r;
  }
  const TOL = 1e-12;
  /** Vergleich x ≥ y (bzw. ≤) rigoros, wo möglich: 'yes' | 'no' | 'unknown' und Art des Nachweises. */
  function geq(x, y) {
    if (x.q && y.q) return {r: qcmp(x.q, y.q) >= 0 ? 'yes' : 'no', how: 'exakt (rationale Arithmetik)'};
    if (x.c === y.c) return {r: 'yes', how: 'exakt (identischer Ausdruck)'};
    if (x.v >= y.v + TOL) return {r: 'yes', how: 'numerisch mit Sicherheitsabstand'};
    if (x.v <= y.v - TOL) return {r: 'no', how: 'numerisch mit Sicherheitsabstand'};
    return {r: 'unknown', how: 'numerisch nicht entscheidbar (Differenz unter 10⁻¹²)'};
  }
  const E = (v, c, q = null) => ({v, c, q});
  /** Beweis-Zertifikat für den Fixpunktsatz auf [a, b] ⊂ ℝ (abgeschlossen ⇒ vollständig).
   *  Bildintervall und sup|f′| folgen aus Monotonie-Lemmata; Endpunkte als Ausdrücke, damit Randgleichheit exakt erkannt wird.
   *  status: 'proven' | 'refuted' | 'inconclusive'. */
  const CERT = {
    cos: (a, b) => (a.v >= 0 && b.v <= Math.PI / 2) ? {img: [E(Math.cos(b.v), `cos(${b.c})`), E(Math.cos(a.v), `cos(${a.c})`, a.q && a.q.n === 0n ? Q(1n) : null)], q: E(Math.sin(b.v), `sin(${b.c})`),
      lemma: 'cos ist auf [0, π/2] fallend ⇒ cos([a,b]) = [cos b, cos a]; |cos′(x)| = sin x ist dort steigend ⇒ sup |f′| = sin b.'} : {why: 'Zertifikat nur für [a, b] ⊂ [0, π/2] (dort cos fallend, |cos′| = sin steigend).'},
    lect: (a, b) => a.v > -3 ? {img: [E(1 / (3 + b.v), `1/(3+${b.c})`, b.q ? qdiv(Q(1n), qadd(Q(3n), b.q)) : null), E(1 / (3 + a.v), `1/(3+${a.c})`, a.q ? qdiv(Q(1n), qadd(Q(3n), a.q)) : null)],
      q: E(1 / ((3 + a.v) ** 2), `1/(3+${a.c})^2`, a.q ? qdiv(Q(1n), qmul(qadd(Q(3n), a.q), qadd(Q(3n), a.q))) : null),
      lemma: 'f(x) = 1/(3+x) ist für x > −3 fallend ⇒ f([a,b]) = [f(b), f(a)]; |f′(x)| = 1/(3+x)² fallend ⇒ sup |f′| = 1/(3+a)².'} : {why: 'Zertifikat nur für a > −3.'},
    sqrt: (a, b) => a.v > -1.5 ? (() => { const ia = a.q ? qadd(Q(3n), qmul(Q(2n), a.q)) : null, ib = b.q ? qadd(Q(3n), qmul(Q(2n), b.q)) : null;
      return {img: [E(Math.sqrt(3 + 2 * a.v), `sqrt(3+2*${a.c})`, ia ? qsqrt(ia) : null), E(Math.sqrt(3 + 2 * b.v), `sqrt(3+2*${b.c})`, ib ? qsqrt(ib) : null)],
        q: E(1 / Math.sqrt(3 + 2 * a.v), `1/sqrt(3+2*${a.c})`, ia && qsqrt(ia) ? qdiv(Q(1n), qsqrt(ia)) : null),
        lemma: 'f(x) = √(3+2x) steigend ⇒ f([a,b]) = [f(a), f(b)]; f′(x) = 1/√(3+2x) > 0 fallend ⇒ sup |f′| = f′(a).'}; })() : {why: 'Zertifikat nur für a > −1,5.'},
    heron: (a, b) => { if (!(a.v > 0)) return {why: 'Zertifikat nur für a > 0.'};
      const fq = x => x.q ? qdiv(qadd(x.q, qdiv(Q(2n), x.q)), Q(2n)) : null, dq = x => x.q ? qdiv(qadd(Q(1n), Q(-1n * 2n * x.q.d * x.q.d, x.q.n * x.q.n)), Q(2n)) : null;
      const fa = E((a.v + 2 / a.v) / 2, `h(${a.c})`, fq(a)), fb = E((b.v + 2 / b.v) / 2, `h(${b.c})`, fq(b));
      const sq2 = E(Math.SQRT2, 'sqrt(2)'), inside = geq(sq2, a).r === 'yes' && geq(b, sq2).r === 'yes';
      const lo = inside ? sq2 : (fa.v <= fb.v ? fa : fb), hi = fa.v >= fb.v ? fa : fb;
      const da = E(Math.abs((1 - 2 / (a.v * a.v)) / 2), `|h'(${a.c})|`, dq(a) ? (qcmp(dq(a), Q(0n)) < 0 ? Q(-dq(a).n, dq(a).d) : dq(a)) : null);
      const db = E(Math.abs((1 - 2 / (b.v * b.v)) / 2), `|h'(${b.c})|`, dq(b) ? (qcmp(dq(b), Q(0n)) < 0 ? Q(-dq(b).n, dq(b).d) : dq(b)) : null);
      return {img: [lo, hi], q: da.v >= db.v ? da : db, lemma: 'f′(x) = (1 − 2/x²)/2 ist für x > 0 steigend ⇒ sup |f′| an einem Rand; f fällt auf (0, √2], steigt auf [√2, ∞) ⇒ Minimum f(√2) = √2, Maximum an einem Rand.'}; },
    xinv: (a, b) => { if (!(a.v > 0)) return {why: 'Zertifikat nur für a > 0.'};
      const fq = x => x.q ? qadd(x.q, qdiv(Q(1n), x.q)) : null;
      const fa = E(a.v + 1 / a.v, `g(${a.c})`, fq(a)), fb = E(b.v + 1 / b.v, `g(${b.c})`, fq(b)), one = E(1, '1', Q(1n));
      const inside = geq(one, a).r === 'yes' && geq(b, one).r === 'yes';
      const dq = x => x.q ? qadd(Q(1n), Q(-x.q.d * x.q.d, x.q.n * x.q.n)) : null, abs = z => z && qcmp(z, Q(0n)) < 0 ? Q(-z.n, z.d) : z;
      const da = E(Math.abs(1 - 1 / (a.v * a.v)), `|g'(${a.c})|`, abs(dq(a))), db = E(Math.abs(1 - 1 / (b.v * b.v)), `|g'(${b.c})|`, abs(dq(b)));
      return {img: [inside ? E(2, '2', Q(2n)) : (fa.v <= fb.v ? fa : fb), fa.v >= fb.v ? fa : fb], q: da.v >= db.v ? da : db,
        lemma: 'f′(x) = 1 − 1/x² steigend ⇒ sup |f′| an einem Rand; f fällt auf (0, 1], steigt auf [1, ∞) ⇒ Minimum f(1) = 2.'}; },
  };
  function certificate(key, aIn, bIn) {
    const steps = [];
    let a, b;
    try { a = parseExpr(aIn); b = parseExpr(bIn); } catch (err) { return {ok: false, status: 'refuted', steps: [{ok: false, text: 'Endpunkte nicht lesbar: ' + err.message + ' (erlaubt: Zahlen, pi, sqrt(), cos(), sin(), + − * /)'}]}; }
    const lt = geq(a, b);
    if (!(Number.isFinite(a.v) && Number.isFinite(b.v)) || lt.r !== 'no') return {ok: false, status: 'refuted', steps: [{ok: false, text: 'Ein abgeschlossenes, beschränktes Intervall [a, b] mit a < b angeben.'}]};
    steps.push({ok: true, text: `[${a.c}, ${b.c}] ist abgeschlossen in ℝ, also vollständig.`});
    const c = CERT[key](a, b);
    if (c.why) return {ok: false, status: 'refuted', steps: steps.concat({ok: false, text: c.why})};
    const lo = geq(c.img[0], a), hi = geq(b, c.img[1]);
    const inv = lo.r === 'yes' && hi.r === 'yes' ? 'yes' : (lo.r === 'no' || hi.r === 'no') ? 'no' : 'unknown';
    steps.push({ok: inv === 'yes', unknown: inv === 'unknown', text: `Invarianz: f([a,b]) = [${c.img[0].c} ≈ ${c.img[0].v.toFixed(6)}, ${c.img[1].c} ≈ ${c.img[1].v.toFixed(6)}] ${inv === 'yes' ? '⊆' : inv === 'no' ? '⊄' : '⊆ ?'} [${a.c}, ${b.c}] – linker Rand: ${lo.how}, rechter Rand: ${hi.how}.`, lemma: c.lemma});
    const one = E(1, '1', Q(1n)), qq = geq(one, c.q), qstrict = qq.r === 'yes' && !(c.q.q ? qcmp(c.q.q, Q(1n)) === 0 : c.q.c === '1');
    const qres = qstrict ? 'yes' : qq.r === 'no' || (c.q.q && qcmp(c.q.q, Q(1n)) >= 0) ? 'no' : 'unknown';
    steps.push({ok: qres === 'yes', unknown: qres === 'unknown', text: `Kontraktionskonstante: q = sup_{[a,b]} |f′| = ${c.q.c} ≈ ${c.q.v.toFixed(6)} ${qres === 'yes' ? '< 1' : qres === 'no' ? '≥ 1' : '< 1 ?'} (${qq.how}); nach dem Mittelwertsatz |f(x) − f(y)| ≤ q|x − y| auf [a, b].`});
    const status = inv === 'yes' && qres === 'yes' ? 'proven' : inv === 'no' || qres === 'no' ? 'refuted' : 'inconclusive';
    return {ok: status === 'proven', status, steps, q: c.q.v, img: [c.img[0].v, c.img[1].v], lemma: c.lemma, a: a.v, b: b.v};
  }
  const API = {SEQ, MAPS, checkN, minN, orbit, lipschitz, aprioriN, stepsTo, certificate, parseExpr};
  if (typeof module !== 'undefined' && module.exports) module.exports = API; else root.AnaMath = API;
})(typeof window !== 'undefined' ? window : globalThis);
