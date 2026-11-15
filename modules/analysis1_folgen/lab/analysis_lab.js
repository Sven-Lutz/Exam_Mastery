/* Analysis 1 – Folgen-Labor: ε-Streifen und Spinnwebdiagramm. Nutzt lab_core.js (h, s, f, Plane, seg, meter, registerLab). */
'use strict';
const A = window.AnaMath;
const SEQKEYS = Object.keys(A.SEQ), MAPKEYS = Object.keys(A.MAPS);
function anaInit() { return {view: 'eps', seq: 'rational', a: 2, logEps: Math.log10(0.1), N: 10, map: 'heron', a1: 2, n: 12}; }
const EPS = S => Math.round(Math.pow(10, S.logEps) * 1e6) / 1e6;
const anaLab = registerLab({
  id: 'folgen', title: 'Folgen & Grenzwerte',
  intro: 'Konvergenz heißt: Für <b>jedes</b> ε gibt es ein N, ab dem <b>alle</b> Glieder im ε-Streifen um a liegen. Wählen Sie ε, schlagen Sie ein N vor und lassen Sie es prüfen – das Labor sucht das erste Gegenbeispiel. Im Spinnwebdiagramm sehen Sie, warum Rekursionen konvergieren oder nicht.',
  init: anaInit,
  structural: (a, b) => a.view !== b.view,
  compute(S) {
    const eps = EPS(S), seq = A.SEQ[S.seq];
    const pts = Array.from({length: 120}, (_, i) => [i + 1, seq.a(i + 1)]);
    const chk = A.checkN(S.seq, S.a, eps, S.N), mn = A.minN(S.seq, S.a, eps);
    const m = A.MAPS[S.map], orb = A.orbit(S.map, S.a1, S.n);
    const lo = Math.min(...orb.slice(1)), hi = Math.max(...orb.slice(1));
    const q = orb.length > 2 ? A.lipschitz(S.map, Math.min(lo, hi), Math.max(lo, hi)) : NaN;
    const lim = m.fix.length ? m.fix.reduce((b, x) => Math.abs(x - orb[orb.length - 1]) < Math.abs(b - orb[orb.length - 1]) ? x : b) : null;
    return {eps, pts, chk, mn, orb, q, lim, err: lim === null ? null : Math.abs(orb[orb.length - 1] - lim)};
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
  const Ni = h('input', {class: 'num', type: 'text', inputmode: 'numeric', 'aria-label': 'Vorschlag N'});
  Ni.addEventListener('change', () => { const v = parseInt(Ni.value, 10); if (v >= 1) api.set({N: v}); });
  const ai = h('input', {class: 'num', type: 'text', inputmode: 'decimal', 'aria-label': 'Kandidat a'});
  ai.addEventListener('change', () => { const v = parse(ai.value); if (v !== null) api.set({a: v}); });
  root.append(h('div', {class: 'row'}, sel, h('label', {class: 'ctl'}, 'ε = ', epsL, eps), h('label', {class: 'ctl'}, 'Kandidat a = ', ai), h('label', {class: 'ctl'}, 'mein N = ', Ni),
    h('button', {onclick: () => api.set(st => { st.N = Math.max(1, st.N - 1); return st; })}, 'N − 1'), h('button', {onclick: () => api.set(st => { st.N += 1; return st; })}, 'N + 1')));
  const svgWrap = h('div', {class: 'plane'}), verdict = h('div', {}), fl = h('div', {class: 'formula-live'}), meters = h('div', {class: 'meters'});
  root.append(svgWrap, verdict, fl, meters);
  return function update(S, R) {
    eps.value = S.logEps; epsL.textContent = f(R.eps, 4); Ni.value = S.N; ai.value = f(S.a, 3); sel.value = S.seq;
    const W = 760, H = 300, nmax = 120, ys = R.pts.map(p => p[1]), lo = Math.min(...ys, S.a - R.eps) - 0.2, hi = Math.max(...ys, S.a + R.eps) + 0.2;
    const X = n => 40 + (n - 1) / (nmax - 1) * (W - 60), Y = y => H - 24 - (y - lo) / (hi - lo) * (H - 44);
    const svg = s('svg', {viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': `Folge, ε-Streifen um a = ${f(S.a)} und N = ${S.N}`});
    svg.append(s('rect', {x: X(Math.min(S.N, nmax)), y: Y(S.a + R.eps), width: Math.max(0, X(nmax) - X(Math.min(S.N, nmax))), height: Math.max(1, Y(S.a - R.eps) - Y(S.a + R.eps)), fill: 'color-mix(in srgb,var(--ok) 18%,transparent)'}),
      s('line', {x1: 40, x2: W - 20, y1: Y(S.a), y2: Y(S.a), stroke: 'var(--ok)', 'stroke-dasharray': '4 3'}),
      s('line', {x1: X(Math.min(S.N, nmax)), x2: X(Math.min(S.N, nmax)), y1: 10, y2: H - 20, stroke: 'var(--accent)', 'stroke-width': 2}),
      s('text', {x: X(Math.min(S.N, nmax)) + 4, y: 20, fill: 'var(--accent)', 'font-size': 12, 'font-weight': 700}, `N = ${S.N}`));
    R.pts.forEach(([n, y]) => { const inside = Math.abs(y - S.a) < R.eps, bad = !R.chk.ok && n === R.chk.n;
      svg.append(s('circle', {cx: X(n), cy: Y(y), r: bad ? 6 : 2.6, fill: n < S.N ? 'var(--mute)' : inside ? 'var(--ok)' : 'var(--bad)', stroke: bad ? 'var(--bad)' : null, 'stroke-width': bad ? 2 : null})); });
    [lo, S.a, hi].forEach(v => svg.append(s('text', {x: 4, y: Y(v) + 4, 'font-size': 11, fill: 'var(--mute)'}, f(v, 2))));
    svgWrap.replaceChildren(h('h3', {}, 'Glieder aₙ, n = 1 … 120 · grüner Streifen: (a − ε, a + ε) ab N'), svg);
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
  root.append(h('div', {class: 'row'}, sel, h('label', {class: 'ctl'}, 'a₁ = ', a1L, a1), h('label', {class: 'ctl'}, 'Glieder ', nL, nn)));
  const plane = h('div', {class: 'plane'}), tbl = h('div', {class: 'calc-wrap'}), meters = h('div', {class: 'meters'});
  root.append(plane, meters, tbl);
  return function update(S, R) {
    a1.value = S.a1; a1L.textContent = f(S.a1); nn.value = S.n; nL.textContent = S.n; sel.value = S.map;
    const m = A.MAPS[S.map], o = R.orb, xs = o.concat(m.dom), lo = Math.min(...xs.filter(Number.isFinite)) - .2, hi = Math.max(...xs.filter(Number.isFinite)) + .2;
    const W = 420, X = x => 30 + (x - lo) / (hi - lo) * (W - 40), Y = y => W - 20 - (y - lo) / (hi - lo) * (W - 40);
    const svg = s('svg', {viewBox: `0 0 ${W} ${W}`, role: 'img', 'aria-label': 'Spinnwebdiagramm'});
    svg.append(s('line', {x1: X(lo), y1: Y(lo), x2: X(hi), y2: Y(hi), stroke: 'var(--mute)', 'stroke-dasharray': '3 3'}));
    const pts = []; for (let i = 0; i <= 300; i++) { const x = lo + (hi - lo) * i / 300, y = m.f(x); if (Number.isFinite(y) && y > lo - 5 && y < hi + 5) pts.push(`${X(x)},${Y(Math.max(lo - .5, Math.min(hi + .5, y)))}`); }
    svg.append(s('polyline', {points: pts.join(' '), fill: 'none', stroke: 'var(--accent)', 'stroke-width': 2}));
    let path = `M${X(o[0])},${Y(lo)}`; for (let i = 0; i < o.length - 1; i++) path += ` L${X(o[i])},${Y(o[i + 1])} L${X(o[i + 1])},${Y(o[i + 1])}`;
    svg.append(s('path', {d: path, fill: 'none', stroke: 'var(--t1)', 'stroke-width': 1.4}));
    m.fix.forEach(x => { if (x > lo && x < hi) svg.append(s('circle', {cx: X(x), cy: Y(x), r: 5, fill: 'var(--ok)'}), s('text', {x: X(x) + 7, y: Y(x) + 14, 'font-size': 11, fill: 'var(--ok)'}, 'Fixpunkt ' + f(x, 4))); });
    svg.append(s('text', {x: X(hi) - 4, y: Y(hi) + 14, 'text-anchor': 'end', 'font-size': 11, fill: 'var(--mute)'}, 'y = x'));
    plane.replaceChildren(h('h3', {}, 'Spinnweb: senkrecht zu f, waagrecht zur Diagonale'), svg);
    meters.replaceChildren(meter('letztes Glied', f(o[o.length - 1], 6), null), meter('Abstand zum Fixpunkt', R.err === null ? 'kein Fixpunkt' : f(R.err, 8), null),
      meter('q = max |f′| auf dem Orbit', f(R.q, 3), Math.min(1, R.q), 'q < 1 auf einem abgeschlossenen, invarianten Intervall ⇒ Kontraktion'));
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
    task: 'Versuchen Sie verschiedene a. Ziel: Sie haben mindestens drei Kandidaten a getestet (Hypothese-Tab optional).', goal: (S, R) => S.view === 'eps' && S.seq === 'sign' && !R.chk.ok && Math.abs(S.a) > 0.4,
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
  {id: 'g-contr', title: 'Kontraktion nachweisen', level: 'mittel', goal: 'Finden Sie für f(x) = cos x einen Startwert, sodass die Lipschitz-Schätzung auf dem Orbit unter 0,75 liegt und die Folge auf 10⁻⁶ genau konvergiert ist.', setup: S => { S.view = 'web'; S.map = 'cos'; S.a1 = 1; S.n = 40; return S; },
    check: (S, R) => ({done: S.view === 'web' && S.map === 'cos' && R.q < .75 && R.err !== null && R.err < 1e-6, progress: R.q < .75 ? .5 + (R.err < 1e-6 ? .5 : 0) : .2, msg: `q ≈ ${f(R.q, 3)}`}),
    hints: ['q hängt vom Bereich ab, den der Orbit durchläuft: |cos′| = |sin x|.', 'Startwerte nahe dem Fixpunkt 0,739 halten |sin x| klein; mehr Glieder senken den Fehler.'], success: 'Auf einem Intervall [c, d] ⊂ [0, 1] mit cos([c, d]) ⊂ [c, d] ist q = max |sin x| < 1 – Kontraktion auf einem vollständigen Raum ⇒ eindeutiger Fixpunkt (Lebl Satz 7.6.2). q hängt vom Intervall ab: Je enger um den Fixpunkt, desto besser die Schranke.', links: {book: 'kontraktion'}},
];
