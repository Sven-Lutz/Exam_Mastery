/* Analysis 1 – Folgen-Labor: ε-Streifen und Spinnwebdiagramm. Nutzt lab_core.js (h, s, f, Plane, seg, meter, registerLab). */
'use strict';
const A = window.AnaMath;
const SEQKEYS = Object.keys(A.SEQ), MAPKEYS = Object.keys(A.MAPS);
function anaInit() { return {view: 'eps', seq: 'rational', a: 2, logEps: Math.log10(0.1), N: 10, plot: 'values', map: 'heron', a1: 2, n: 12, ia: null, ib: null}; }
const EPS = S => Math.round(Math.pow(10, S.logEps) * 1e6) / 1e6;
const anaLab = registerLab({
  id: 'folgen', title: 'Folgen & Grenzwerte',
  intro: 'Konvergenz heißt: Für <b>jedes</b> ε gibt es ein N, ab dem <b>alle</b> Glieder im ε-Streifen um a liegen. Wählen Sie ε, schlagen Sie ein N vor und lassen Sie es prüfen – das Labor sucht das erste Gegenbeispiel. Im Spinnwebdiagramm sehen Sie, warum Rekursionen konvergieren oder nicht.',
  init: anaInit,
  structural: (a, b) => a.view !== b.view,
  compute(S) {
    const eps = EPS(S), seq = A.SEQ[S.seq];
    const chk = A.checkN(S.seq, S.a, eps, S.N), mn = A.minN(S.seq, S.a, eps);
    const m = A.MAPS[S.map], orb = A.orbit(S.map, S.a1, S.n);
    const lo = Math.min(...orb.slice(1)), hi = Math.max(...orb.slice(1));
    const q = orb.length > 2 ? A.lipschitz(S.map, Math.min(lo, hi), Math.max(lo, hi)) : NaN;
    const lim = m.fix.length ? m.fix.reduce((b, x) => Math.abs(x - orb[orb.length - 1]) < Math.abs(b - orb[orb.length - 1]) ? x : b) : null;
    const cert = S.ia === null || S.ib === null ? null : A.certificate(S.map, S.ia, S.ib);
    const startIn = cert && S.a1 >= S.ia && S.a1 <= S.ib;
    // Diagramm-Horizont: wichtige Ereignisse (N, kleinstes N, Gegenbeispiel) müssen sichtbar sein
    const keyN = Math.max(S.N, mn.N || 0, chk.ok ? 0 : chk.n);
    const nmax = Math.min(20000, Math.max(120, Math.ceil(keyN * 1.15)));
    const step = Math.max(1, Math.floor(nmax / 400)), ns = new Set();
    for (let n = 1; n <= nmax; n += (n < 60 ? 1 : step)) ns.add(n);
    [S.N, mn.N, chk.ok ? null : chk.n, S.N - 1].forEach(n => n && n >= 1 && n <= nmax && ns.add(n));
    const P = [...ns].sort((x, y) => x - y).map(n => [n, seq.a(n)]);
    return {eps, pts: P, nmax, chk, mn, orb, q, lim, err: lim === null ? null : Math.abs(orb[orb.length - 1] - lim), cert, startIn};
  },
  quantities(S, R) { return S.view === 'eps' ? [{id: 'mn', label: 'kleinstes N(ε)', value: R.mn.N ?? NaN}, {id: 'eps', label: 'ε', value: R.eps}] :
    [{id: 'err', label: `Fehler nach ${S.n} Schritten`, value: R.err ?? NaN}, {id: 'q', label: 'Lipschitz-Schätzung q auf dem Orbit', value: R.q}, {id: 'last', label: 'letztes Glied', value: R.orb[R.orb.length - 1]}]; },
  explain(Sb, Rb, Sa, Ra) {
    if (Sa.view === 'eps') {
      const o = [];
      if (Ra.eps < Rb.eps) o.push(`ε verkleinert (${f(Rb.eps, 4)} → ${f(Ra.eps, 4)}): Der Streifen wird schmaler, also braucht man mindestens dasselbe, meist ein größeres N. Genau deshalb steht in der Definition „∀ε ∃N“ – N darf von ε abhängen, nicht umgekehrt.`);
      if (Ra.eps > Rb.eps) o.push('ε vergrößert: Jedes N, das für das kleinere ε funktioniert, funktioniert weiter (Streifen wird breiter).');
      if (Sa.a !== Sb.a) o.push('Sie haben den Kandidaten a geändert. Bei falschem a gibt es ab einem kleinen ε kein N mehr – Gegenbeispiel-Index im Bild.');
      o.push(`Kleinstes N: ${Rb.mn.N ?? '–'} → ${Ra.mn.N ?? 'keins'}${Ra.mn.exact ? ' (exakt aus der Formel ' + A.SEQ[Sa.seq].why + ')' : ''}.`);
      return o.join(' ');
    }
    const o = [];
    if (Sa.a1 !== Sb.a1) o.push(`Startwert ${f(Sb.a1)} → ${f(Sa.a1)}. Eine Rekursion konvergiert gegen einen Fixpunkt a = f(a), wenn sie in einem Bereich bleibt, in dem |f′| ≤ q < 1 (Kontraktion).`);
    if (Sa.map !== Sb.map) o.push('Andere Abbildung: Entscheidend ist die Steigung von f in der Nähe des Fixpunkts (Spinnweb: flach ⇒ Treppe zieht sich zusammen).');
    o.push(`Lipschitz-Schätzung auf dem Orbit: ${f(Rb.q, 3)} → ${f(Ra.q, 3)}.`);
    return o.join(' ');
  },
  view(root, api) {
    const S0 = api.S;
    root.append(h('div', {class: 'row'}, seg([['eps', 'ε-Streifen'], ['web', 'Rekursion (Spinnweb)']], S0.view, v => api.set({view: v}), 'Ansicht')));
    return S0.view === 'eps' ? epsView(root, api) : webView(root, api);
  },
});
function epsView(root, api) {
  const S0 = api.S;
  const sel = h('select', {'aria-label': 'Folge'}, SEQKEYS.map(k => h('option', {value: k, selected: k === S0.seq || null}, A.SEQ[k].label)));
  sel.addEventListener('change', () => api.set(st => { st.seq = sel.value; st.a = A.SEQ[sel.value].lim ?? 0; return st; }));
  const eps = h('input', {type: 'range', min: -3, max: 0, step: 0.01, 'aria-label': 'ε (logarithmisch)'}), epsL = h('b', {});
  eps.addEventListener('input', () => api.set({logEps: +eps.value}));
  const plotSegHolder = h('span', {});
  const Ni = h('input', {class: 'num', type: 'text', inputmode: 'numeric', 'aria-label': 'Vorschlag N'});
  Ni.addEventListener('change', () => { const v = parseInt(Ni.value, 10); if (v >= 1) api.set({N: v}); });
  const ai = h('input', {class: 'num', type: 'text', inputmode: 'decimal', 'aria-label': 'Kandidat a'});
  ai.addEventListener('change', () => { const v = parse(ai.value); if (v !== null) api.set({a: v}); });
  root.append(h('div', {class: 'row'}, sel, h('label', {class: 'ctl'}, 'ε = ', epsL, eps), h('label', {class: 'ctl'}, 'Kandidat a = ', ai), h('label', {class: 'ctl'}, 'mein N = ', Ni),
    h('button', {onclick: () => api.set(st => { st.N = Math.max(1, st.N - 1); return st; })}, 'N − 1'), h('button', {onclick: () => api.set(st => { st.N += 1; return st; })}, 'N + 1')),
    h('div', {class: 'row'}, plotSegHolder));
  const svgWrap = h('div', {class: 'plane'}), verdict = h('div', {}), fl = h('div', {class: 'formula-live'}), meters = h('div', {class: 'meters'});
  root.append(svgWrap, verdict, fl, meters);
  return function update(S, R) {
    eps.value = S.logEps; epsL.textContent = f(R.eps, 4); Ni.value = S.N; ai.value = f(S.a, 3); sel.value = S.seq;
    plotSegHolder.replaceChildren(seg([['values', 'Werte aₙ'], ['dist', 'Abstand |aₙ − a| (log)']], S.plot || 'values', v => api.set({plot: v}), 'Darstellung'));
    const W = 760, H = 300, nmax = R.nmax, dist = S.plot === 'dist' && S.a !== null;
    const val = y => dist ? Math.log10(Math.max(1e-12, Math.abs(y - S.a))) : y;
    const ys = R.pts.map(p => val(p[1])), lo = Math.min(...ys, dist ? Math.log10(R.eps) - 0.5 : S.a - R.eps) - (dist ? 0 : 0.2), hi = Math.max(...ys, dist ? Math.log10(R.eps) + 0.5 : S.a + R.eps) + (dist ? 0 : 0.2);
    const X = n => 40 + (n - 1) / (nmax - 1) * (W - 60), Y = y => H - 24 - (y - lo) / (hi - lo) * (H - 44);
    const svg = s('svg', {viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': `Folge bis n = ${nmax}, ε = ${f(R.eps, 4)}, N = ${S.N}`});
    if (dist) svg.append(s('rect', {x: X(S.N), y: Y(Math.log10(R.eps)), width: Math.max(0, X(nmax) - X(S.N)), height: Math.max(0, Y(lo) - Y(Math.log10(R.eps))), fill: 'color-mix(in srgb,var(--ok) 15%,transparent)'}),
      s('line', {x1: 40, x2: W - 20, y1: Y(Math.log10(R.eps)), y2: Y(Math.log10(R.eps)), stroke: 'var(--ok)', 'stroke-dasharray': '4 3'}), s('text', {x: W - 22, y: Y(Math.log10(R.eps)) - 5, 'text-anchor': 'end', 'font-size': 11, fill: 'var(--ok)'}, 'ε'));
    else svg.append(s('rect', {x: X(S.N), y: Y(S.a + R.eps), width: Math.max(0, X(nmax) - X(S.N)), height: Math.max(1.5, Y(S.a - R.eps) - Y(S.a + R.eps)), fill: 'color-mix(in srgb,var(--ok) 25%,transparent)'}),
      s('line', {x1: 40, x2: W - 20, y1: Y(S.a), y2: Y(S.a), stroke: 'var(--ok)', 'stroke-dasharray': '4 3'}));
    const vline = (n, col, txt, dy, dash) => n && n <= nmax ? svg.append(s('line', {x1: X(n), x2: X(n), y1: 10, y2: H - 20, stroke: col, 'stroke-width': 2, 'stroke-dasharray': dash || null}), s('text', {x: X(n) + (X(n) > W - 160 ? -4 : 4), y: dy, fill: col, 'font-size': 12, 'font-weight': 700, 'text-anchor': X(n) > W - 160 ? 'end' : 'start'}, txt)) : null;
    vline(R.mn.N, 'var(--ok)', `kleinstes N = ${R.mn.N}`, 34, '5 3');
    vline(S.N, 'var(--accent)', `Ihr N = ${S.N}`, 18);
    R.pts.forEach(([n, y]) => { const inside = Math.abs(y - S.a) < R.eps, bad = !R.chk.ok && n === R.chk.n;
      svg.append(s('circle', {cx: X(n), cy: Y(val(y)), r: bad ? 6 : 2.4, fill: n < S.N ? 'var(--mute)' : inside ? 'var(--ok)' : 'var(--bad)', stroke: bad ? 'var(--bad)' : null, 'stroke-width': bad ? 2 : null})); });
    if (!R.chk.ok) { const right = X(R.chk.n) > W - 200; svg.append(s('text', {x: X(R.chk.n) + (right ? -8 : 8), y: Y(val(R.chk.value)) + 18, 'text-anchor': right ? 'end' : 'start', 'font-size': 12, fill: 'var(--bad)', 'font-weight': 700}, `Gegenbeispiel n = ${R.chk.n}`)); }
    [lo, hi].forEach(v => svg.append(s('text', {x: 4, y: Y(v) + 4, 'font-size': 11, fill: 'var(--mute)'}, dist ? '10^' + f(v, 1) : f(v, 2))));
    [1, Math.round(nmax / 2), nmax].forEach(n => svg.append(s('text', {x: X(n), y: H - 6, 'text-anchor': 'middle', 'font-size': 11, fill: 'var(--mute)'}, 'n = ' + n)));
    svgWrap.replaceChildren(h('h3', {}, S.plot === 'dist' ? `Abstand |aₙ − a| (logarithmisch), n = 1 … ${R.nmax} · grün: unter ε ab N` : `Glieder aₙ, n = 1 … ${R.nmax} · grüner Streifen: (a − ε, a + ε) ab N`), svg);
    verdict.replaceChildren(R.chk.ok ? h('p', {class: 'verdict ok', html: R.chk.proven ? `Für alle n ≥ ${S.N} gilt |aₙ − a| &lt; ε – <b>bewiesen</b> mit ${A.SEQ[S.seq].why}.` : `Bis n = ${S.N + R.chk.horizon} kein Gegenbeispiel gefunden. Das ist <b>kein Beweis</b> – dafür braucht es eine Abschätzung für alle n.`}) :
      h('p', {class: 'verdict bad', html: `Gegenbeispiel: n = ${R.chk.n} ≥ N mit |aₙ − a| = ${f(Math.abs(R.chk.value - S.a), 4)} ≥ ε. Dieses N reicht nicht.`}));
    const sq = A.SEQ[S.seq];
    fl.innerHTML = `Definition: ∀ε&gt;0 ∃N ∀n≥N: |aₙ − a| &lt; ε &nbsp;·&nbsp; ${sq.label}${sq.why ? ' &nbsp;·&nbsp; ' + sq.why : ''}`;
    meters.replaceChildren(meter('kleinstes N(ε)', R.mn.N === null ? 'keins' : String(R.mn.N), null, R.mn.exact ? 'exakt' : 'Suche bis n = 20 000'), meter('Ihr N', String(S.N), null), meter('Status', R.chk.ok ? (R.chk.proven ? 'bewiesen' : 'nur getestet') : 'widerlegt', null));
  };
}
function webView(root, api) {
  const S0 = api.S;
  const sel = h('select', {'aria-label': 'Abbildung'}, MAPKEYS.map(k => h('option', {value: k, selected: k === S0.map || null}, A.MAPS[k].label)));
  sel.addEventListener('change', () => api.set(st => { st.map = sel.value; st.a1 = {heron: 2, cos: 1, lect: 0, sqrt: 0, xinv: 1}[sel.value]; return st; }));
  const a1 = h('input', {type: 'range', min: -3, max: 6, step: 0.05, 'aria-label': 'Startwert a₁'}), a1L = h('b', {});
  a1.addEventListener('input', () => api.set({a1: +a1.value}));
  const nn = h('input', {type: 'range', min: 2, max: 60, step: 1, 'aria-label': 'Anzahl Glieder'}), nL = h('b', {});
  nn.addEventListener('input', () => api.set({n: +nn.value}));
  const ia = h('input', {class: 'num', type: 'text', inputmode: 'decimal', 'aria-label': 'Intervall linker Rand a'}), ib = h('input', {class: 'num', type: 'text', inputmode: 'decimal', 'aria-label': 'Intervall rechter Rand b'});
  ia.addEventListener('change', () => api.set({ia: parse(ia.value)})); ib.addEventListener('change', () => api.set({ib: parse(ib.value)}));
  root.append(h('div', {class: 'row'}, sel, h('label', {class: 'ctl'}, 'a₁ = ', a1L, a1), h('label', {class: 'ctl'}, 'Glieder ', nL, nn)),
    h('div', {class: 'row'}, h('b', {}, 'Beweisversuch: Intervall [a, b] = ['), ia, ',', ib, h('b', {}, ']')));
  const plane = h('div', {class: 'plane'}), tbl = h('div', {class: 'calc-wrap'}), meters = h('div', {class: 'meters'}), tiers = h('div', {class: 'planes', style: 'grid-template-columns:repeat(auto-fit,minmax(220px,1fr))'});
  root.append(plane, tiers, meters, tbl);
  return function update(S, R) {
    a1.value = S.a1; a1L.textContent = f(S.a1); nn.value = S.n; nL.textContent = S.n; sel.value = S.map;
    if (document.activeElement !== ia) ia.value = S.ia === null ? '' : String(S.ia); if (document.activeElement !== ib) ib.value = S.ib === null ? '' : String(S.ib);
    const tier = (title, cls, body) => h('div', {class: 'plane', style: 'padding:8px 12px'}, h('h3', {style: 'padding:0'}, title), h('div', {class: 'verdict ' + cls}, ...body));
    tiers.replaceChildren(
      tier('1 · Simulation', R.err !== null && R.err < 1e-6 ? 'ok' : '', [h('p', {}, R.err === null ? 'Kein Fixpunkt der Abbildung: Die Folge kann nicht gegen einen Fixpunkt konvergieren.' : `Nach ${S.n} Gliedern Abstand ${R.err.toExponential(2)} zum Fixpunkt.`), h('p', {class: 'note'}, 'Zeigt nur, was bei diesem Startwert in endlich vielen Schritten passiert.')]),
      tier('2 · Indiz', '', [h('p', {}, `max |f′| auf den Punkten des Orbits ≈ ${f(R.q, 3)}`), h('p', {class: 'note'}, 'Abtastung endlich vieler Punkte – keine Schranke für alle x, kein Beweis.')]),
      tier('3 · Beweis (Fixpunktsatz)', R.cert ? (R.cert.ok && R.startIn ? 'ok' : 'bad') : '', R.cert ? [h('ul', {}, R.cert.steps.map(st => h('li', {}, (st.ok ? '✓ ' : '✗ ') + st.text, st.lemma ? h('div', {class: 'note'}, 'Begründung: ' + st.lemma) : null))),
        h('p', {}, R.startIn ? '✓ Startwert a₁ liegt in [a, b].' : '✗ Startwert a₁ liegt nicht in [a, b] – der Satz sagt dann nichts über diese Folge.'),
        h('p', {html: R.cert.ok && R.startIn ? '<b>Bewiesen:</b> eindeutiger Fixpunkt in [a, b], Konvergenz für jeden Start in [a, b], |aₙ − a| ≤ qⁿ⁻¹/(1 − q)·|a₂ − a₁|.' : '<b>Kein Beweis</b> mit diesem Intervall.'}),
        h('p', {class: 'note'}, 'Zahlen mit Sicherheitsabstand 10⁻¹²; ein Rand, der genau getroffen wird, ist numerisch nicht zertifizierbar – Intervall etwas größer wählen.')] : [h('p', {}, 'Geben Sie ein Intervall [a, b] ein. Bewiesen ist erst, wenn f([a, b]) ⊆ [a, b] und sup |f′| < 1 auf [a, b] analytisch gezeigt sind.')]));
    const m = A.MAPS[S.map], o = R.orb, xs = o.concat(m.dom), lo = Math.min(...xs.filter(Number.isFinite)) - .2, hi = Math.max(...xs.filter(Number.isFinite)) + .2;
    const W = 420, X = x => 30 + (x - lo) / (hi - lo) * (W - 40), Y = y => W - 20 - (y - lo) / (hi - lo) * (W - 40);
    const svg = s('svg', {viewBox: `0 0 ${W} ${W}`, role: 'img', 'aria-label': 'Spinnwebdiagramm'});
    svg.append(s('line', {x1: X(lo), y1: Y(lo), x2: X(hi), y2: Y(hi), stroke: 'var(--mute)', 'stroke-dasharray': '3 3'}));
    if (R.cert && S.ib > S.ia) svg.append(s('rect', {x: X(S.ia), y: Y(S.ib), width: X(S.ib) - X(S.ia), height: Y(S.ia) - Y(S.ib), fill: R.cert.ok ? 'color-mix(in srgb,var(--ok) 14%,transparent)' : 'color-mix(in srgb,var(--bad) 10%,transparent)', stroke: R.cert.ok ? 'var(--ok)' : 'var(--bad)'}));
    const pts = []; for (let i = 0; i <= 300; i++) { const x = lo + (hi - lo) * i / 300, y = m.f(x); if (Number.isFinite(y) && y > lo - 5 && y < hi + 5) pts.push(`${X(x)},${Y(Math.max(lo - .5, Math.min(hi + .5, y)))}`); }
    svg.append(s('polyline', {points: pts.join(' '), fill: 'none', stroke: 'var(--accent)', 'stroke-width': 2}));
    let path = `M${X(o[0])},${Y(lo)}`; for (let i = 0; i < o.length - 1; i++) path += ` L${X(o[i])},${Y(o[i + 1])} L${X(o[i + 1])},${Y(o[i + 1])}`;
    svg.append(s('path', {d: path, fill: 'none', stroke: 'var(--t1)', 'stroke-width': 1.4}));
    m.fix.forEach(x => { if (x > lo && x < hi) svg.append(s('circle', {cx: X(x), cy: Y(x), r: 5, fill: 'var(--ok)'}), s('text', {x: X(x) + 7, y: Y(x) + 14, 'font-size': 11, fill: 'var(--ok)'}, 'Fixpunkt ' + f(x, 4))); });
    svg.append(s('text', {x: X(hi) - 4, y: Y(hi) + 14, 'text-anchor': 'end', 'font-size': 11, fill: 'var(--mute)'}, 'y = x'));
    plane.replaceChildren(h('h3', {}, 'Spinnweb: senkrecht zu f, waagrecht zur Diagonale'), svg);
    meters.replaceChildren(meter('letztes Glied', f(o[o.length - 1], 6), null), meter('Abstand zum Fixpunkt', R.err === null ? 'kein Fixpunkt' : f(R.err, 8), null),
      meter('Indiz: max |f′| auf dem Orbit', f(R.q, 3), Math.min(1, R.q), 'Abtastung – kein Beweis'));
    tbl.replaceChildren(h('table', {class: 'calc'}, h('tr', {}, h('th', {}, 'n'), h('th', {}, 'aₙ'), h('th', {}, 'aₙ₊₁ − aₙ'), h('th', {}, R.lim === null ? '' : '|aₙ − a|')),
      o.slice(0, 12).map((v, i) => h('tr', {}, h('td', {}, i + 1), h('td', {}, f(v, 10)), h('td', {}, i + 1 < o.length ? f(o[i + 1] - v, 10) : ''), h('td', {}, R.lim === null ? '' : f(Math.abs(v - R.lim), 10))))));
  };
}
anaLab.path = [
  {id: 'f1', title: 'Den Streifen lesen', story: 'aₙ = (2n−1)/(n+3) nähert sich 2. Für ε = 0,1: Ab welchem N liegen <em>alle</em> Glieder im Streifen?', setup: () => anaInit(),
    predict: {q: 'Sie halbieren ε. Was passiert mit dem kleinsten N?', options: ['Es wird etwa doppelt so groß.', 'Es halbiert sich.', 'Es bleibt gleich.'], correct: 0},
    task: 'Stellen Sie ε = 0,05 ein und finden Sie das kleinste N, das bewiesen funktioniert.', goal: (S, R) => S.view === 'eps' && S.seq === 'rational' && Math.abs(R.eps - 0.05) < 0.002 && R.chk.proven && S.N === R.mn.N,
    reveal: '|aₙ − 2| = 7/(n+3) < ε ⟺ n > 7/ε − 3. Für ε = 0,05: n > 137, also N = 138. Halbiert man ε, verdoppelt sich 7/ε: N wächst etwa wie 1/ε. In der Definition steht deshalb ∀ε ∃N – N ist eine Funktion von ε.', links: {book: 'konv'}},
  {id: 'f2', title: 'Getestet ist nicht bewiesen', story: 'aₙ = sin(n)/n. Hier kennt das Labor keine Formel für N, sondern sucht nur Gegenbeispiele.', setup: S => { S.view = 'eps'; S.seq = 'sinn'; S.a = 0; S.logEps = -2; S.N = 50; return S; },
    task: 'Finden Sie ein N, für das bis zum Horizont kein Gegenbeispiel existiert, und überlegen Sie, warum das trotzdem kein Beweis ist.', goal: (S, R) => S.view === 'eps' && S.seq === 'sinn' && R.chk.ok,
    reveal: 'Ein endlicher Test kann nur widerlegen. Der Beweis braucht eine Schranke für alle n: |sin(n)/n| ≤ 1/n < ε für n > 1/ε. Damit ist N = ⌊1/ε⌋ + 1 sicher – oft größer als das kleinste N, aber garantiert.', links: {book: 'konv'}},
  {id: 'f3', title: 'Divergenz formal', story: 'aₙ = (−1)ⁿ springt zwischen −1 und 1.', setup: S => { S.view = 'eps'; S.seq = 'sign'; S.a = 0; S.logEps = Math.log10(0.5); S.N = 10; return S; },
    predict: {q: 'Gibt es für ε = 0,5 einen Kandidaten a und ein N, sodass alle Glieder ab N im Streifen liegen?', options: ['Nein, für kein a.', 'Ja, für a = 0.', 'Ja, für a = 1 und großes N.'], correct: 0},
    task: 'Setzen Sie den Kandidaten a = 1 (einer der beiden Werte, also der „beste“ Versuch) und beobachten Sie das Gegenbeispiel.', goal: (S, R) => S.view === 'eps' && S.seq === 'sign' && Math.abs(S.a - 1) < 1e-9 && R.eps <= 0.5 + 1e-9 && !R.chk.ok,
    reveal: 'Verneinung: ∃ε>0 ∀N ∃n≥N: |aₙ − a| ≥ ε. Mit ε = 1/2: Für jedes a liegt mindestens eines der Glieder ±1 mindestens 1 von a entfernt… genauer: |1 − a| + |−1 − a| ≥ 2, also ist eines ≥ 1 > ε. Beide Werte kommen unendlich oft vor.', links: {book: 'konv'}},
  {id: 'f4', title: 'Monoton und beschränkt', story: 'Heron/Newton: aₙ₊₁ = (aₙ + 2/aₙ)/2 mit a₁ = 2 (Lebl, Beispiel 2.2.8).', setup: S => { S.view = 'web'; S.map = 'heron'; S.a1 = 2; S.n = 8; return S; },
    predict: {q: 'Welcher Grenzwert ergibt sich für den Startwert a₁ = −1?', options: ['−√2', '√2', 'keiner – die Folge divergiert'], correct: 0},
    task: 'Wählen Sie einen negativen Startwert.', goal: (S, R) => S.view === 'web' && S.map === 'heron' && S.a1 < 0 && R.lim !== null && R.lim < 0,
    reveal: 'Für a₁ > 0 gilt aₙ ≥ √2 ab n = 2 (AM-GM) und aₙ₊₁ ≤ aₙ: monoton und beschränkt ⇒ konvergent (Satz 2.14), Grenzwert löst a = (a + 2/a)/2, also a² = 2. Die Wahl der Wurzel legt erst das Vorzeichen des Startwerts fest – der Grenzübergang allein liefert nur a² = 2.', links: {book: 'monoton'}},
  {id: 'f5', title: 'Kontraktion – und ein Gegenbeispiel', story: 'f(x) = x + 1/x verkleinert Abstände echt: |f(x) − f(y)| < |x − y| für x, y ≥ 1. Reicht das?', setup: S => { S.view = 'web'; S.map = 'xinv'; S.a1 = 1; S.n = 30; return S; },
    task: 'Lassen Sie 60 Glieder laufen und beobachten Sie q und den letzten Wert.', goal: (S, R) => S.view === 'web' && S.map === 'xinv' && S.n >= 60,
    reveal: 'Es gibt kein q < 1 mit |f(x) − f(y)| ≤ q|x − y|: f′(x) = 1 − 1/x² → 1. Und f hat keinen Fixpunkt (x + 1/x = x unmöglich); aₙ² wächst um mehr als 2 je Schritt. Der Fixpunktsatz braucht eine echte Kontraktion <em>und</em> Vollständigkeit (Lebl, Satz 7.6.2: „The words complete and contraction are necessary“).', links: {book: 'kontraktion'}},
];
anaLab.challenges = [
  {id: 'g-minN', title: 'Genau das kleinste N', level: 'leicht', goal: 'aₙ = (2n−1)/(n+3), ε = 0,01: Stellen Sie das kleinste N ein.', setup: () => { const n = anaInit(); n.logEps = -2; n.N = 100; return n; },
    check: (S, R) => ({done: S.view === 'eps' && S.seq === 'rational' && Math.abs(R.eps - .01) < 1e-9 && S.N === R.mn.N, progress: S.view === 'eps' && R.chk.ok ? .6 : .2, msg: R.chk.ok ? 'gültig – ist es auch das kleinste?' : 'noch zu klein'}),
    hints: ['Lösen Sie 7/(n+3) < 0,01 nach n auf.', 'n > 697.'], success: 'N = 698: Für n = 697 ist 7/700 = 0,01 nicht kleiner als ε. Strenge Ungleichungen entscheiden über den Rand.', links: {book: 'konv'}},
  {id: 'g-noN', title: 'Kein N für (−1)ⁿ', level: 'Transfer', goal: '(−1)ⁿ, ε = 0,5: Finden Sie a und N – oder begründen Sie, warum es keine gibt.', setup: () => { const n = anaInit(); n.seq = 'sign'; n.a = 0; n.logEps = Math.log10(0.5); return n; },
    check: (S, R) => ({done: false, progress: 0, msg: R.chk.ok ? '' : `Gegenbeispiel bei n = ${R.chk.n}`}),
    impossible: {q: 'Warum gibt es kein Paar (a, N)?', options: ['Beide Werte ±1 kommen nach jedem N vor und haben Abstand 2 > 2ε = 1; ein Streifen der Breite 1 kann nicht beide enthalten.', 'Weil ε zu klein gewählt ist – mit ε = 0,9 klappt es.', 'Weil die Folge unbeschränkt ist.'], correct: 0,
      applies: S => S.seq === 'sign' && Math.abs(EPS(S) - 0.5) < 0.01, notApplicable: 'Bedingung: Folge (−1)ⁿ, ε = 0,5.', why: {1: 'Auch mit ε = 0,9 hat der Streifen Breite 1,8 < 2. Erst ε > 1 enthält beide – aber Konvergenz verlangt ALLE ε.', 2: '(−1)ⁿ ist beschränkt. Beschränkt reicht nicht für Konvergenz (Satz 2.4 gilt nur in eine Richtung).'}},
    hints: ['Wie breit ist der Streifen?', 'Wie weit liegen die beiden Werte auseinander?'], success: 'Genau das ist die Verneinung der Definition mit ε = 1/2. Gleichzeitig ein Beispiel dafür, dass „beschränkt“ nicht „konvergent“ impliziert.', links: {book: 'konv'}},
  {id: 'g-fast', title: 'Quadratisch schnell', level: 'mittel', goal: 'Erreichen Sie mit der Heron-Abbildung einen Abstand < 10⁻¹⁰ zu √2 mit höchstens 6 Gliedern.', setup: S => { S.view = 'web'; S.map = 'heron'; S.a1 = 5; S.n = 4; return S; },
    check: (S, R) => ({done: S.view === 'web' && S.map === 'heron' && S.n <= 6 && R.err !== null && R.err < 1e-10, progress: R.err ? Math.min(1, -Math.log10(R.err + 1e-17) / 10) : 0, msg: R.err === null ? '' : `Abstand ${R.err.toExponential(2)}`}),
    hints: ['Der Fehler erfüllt eₙ₊₁ = eₙ²/(2aₙ).', 'Ein Startwert nahe √2 hilft – z. B. 1,5.'], success: 'Quadratische Konvergenz: Die Zahl korrekter Stellen verdoppelt sich ungefähr je Schritt (eₙ₊₁ = eₙ²/(2aₙ)). Vergleichen Sie mit cos: dort schrumpft der Fehler nur um den Faktor ≈ |sin a| ≈ 0,67 je Schritt.', links: {book: 'monoton'}},
  {id: 'g-contr', title: 'Kontraktion beweisen', level: 'Transfer', goal: 'Beweisen Sie für f(x) = cos x und a₁ = 1 die Konvergenz mit dem Fixpunktsatz: Geben Sie ein abgeschlossenes Intervall [a, b] an, das f in sich abbildet, auf dem sup |f′| < 1 gilt und das a₁ enthält.', constraint: 'Simulation und Abtastung zählen nicht; nur das Zertifikat (Stufe 3).',
    setup: S => { S.view = 'web'; S.map = 'cos'; S.a1 = 1; S.n = 30; S.ia = null; S.ib = null; return S; },
    check: (S, R) => { const ok = S.view === 'web' && S.map === 'cos' && S.a1 === 1 && R.cert && R.cert.ok && R.startIn;
      return {done: !!ok, progress: !R.cert ? 0 : (R.cert.steps.filter(x => x.ok).length + (R.startIn ? 1 : 0)) / (R.cert.steps.length + 1), msg: !R.cert ? 'Noch kein Intervall angegeben.' : R.cert.steps.filter(x => !x.ok).map(x => x.text).join(' ') || (R.startIn ? '' : 'a₁ liegt nicht im Intervall.')}; },
    hints: ['cos ist auf [0, π/2] fallend: Das Bild von [a, b] ist [cos b, cos a].', 'Wählen Sie b = 1 (dann enthält das Intervall a₁ = 1) und a so, dass cos 1 ≥ a und cos a ≤ 1.', 'Mit [0,5; 1] gilt cos([0,5; 1]) ≈ [0,5403; 0,8776] und q = sin 1 ≈ 0,8415.'],
    success: 'Bewiesen: [a, b] ist abgeschlossen (vollständig), f([a, b]) ⊆ [a, b] folgt aus der Monotonie von cos, und sup |f′| = sin b < 1 folgt aus der Monotonie von sin – nicht aus Abtastung. Erst damit liefert der Fixpunktsatz (Lebl, Satz 7.6.2) Existenz, Eindeutigkeit und die a-priori-Schranke. Die Simulation zeigt nur, dass es bei diesem Start „so aussieht“.', links: {book: 'kontraktion'}},
  {id: 'g-xinv', title: 'Warum kein Intervall funktioniert', level: 'Transfer', goal: 'Finden Sie für f(x) = x + 1/x ein Intervall [a, b] mit Zertifikat – oder begründen Sie, warum es keines gibt.', setup: S => { S.view = 'web'; S.map = 'xinv'; S.a1 = 1; S.ia = 1; S.ib = 20; return S; },
    check: () => ({done: false, progress: 0, msg: ''}),
    impossible: {q: 'Warum scheitert jedes Intervall [a, b] mit a > 0?', options: ['Es gilt f(b) = b + 1/b > b: Das Bild ragt immer über den rechten Rand hinaus, also ist kein [a, b] invariant (und f hat keinen Fixpunkt).', 'Weil sup |f′| immer ≥ 1 ist.', 'Weil das Intervall nicht vollständig ist.'], correct: 0,
      applies: S => S.map === 'xinv', notApplicable: 'Bedingung: Abbildung x + 1/x.', why: {1: 'Falsch: Auf [1, b] ist sup |f′| = 1 − 1/b² < 1. Die Schranke allein reicht nicht – es fehlt die Invarianz.', 2: 'Abgeschlossene Intervalle in ℝ sind vollständig.'}},
    hints: ['Vergleichen Sie f(b) mit b.'], success: 'Auf jedem [1, b] ist f sogar eine Kontraktion im Sinne der Lipschitz-Schranke (q = 1 − 1/b² < 1), aber f bildet [1, b] nicht in sich ab. Der Fixpunktsatz braucht beide Voraussetzungen – das Gegenbeispiel trennt sie sauber.', links: {book: 'kontraktion'}},
];
