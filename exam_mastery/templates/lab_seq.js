/* Exam Mastery – Labore 2–4: CRF/Viterbi, BiRNN, Spannen & Evaluation. Nutzt Helfer aus lab_ui.js. */
'use strict';
const NEGINF = -Infinity;
function stepper(val, on, aria, {step = 0.1, forbid = false} = {}) {
  const v = h('span', {class: 'v' + (forbid ? ' forbid' : '')}, forbid ? '−∞' : f(val, 1));
  return h('span', {class: 'cell-step'}, h('button', {'aria-label': aria + ' verringern', disabled: forbid || null, onclick: () => on(Math.round((val - step) * 100) / 100)}, '−'), v,
    h('button', {'aria-label': aria + ' erhöhen', disabled: forbid || null, onclick: () => on(Math.round((val + step) * 100) / 100)}, '+'));
}
const tagChip = (t, cls = '') => h('div', {class: 'tk ' + cls}, t);

// =====================================================================================
// Lab 2: Lineare-Ketten-CRF – Viterbi vs. Vorwärts, Verbote, Randverteilungen
// =====================================================================================
const CRF_LABELS = ['B-PER', 'I-PER', 'O'];
function crfInit() {
  return {words: ['Jan', 'Ullrich', 'gewinnt', 'heute'],
    E: [[1.0, 1.2, 0.6], [0.3, 1.5, 0.2], [-0.5, 0.1, 1.4], [-0.5, -0.2, 1.2]],
    A: [[0, 0, 0], [0, 0, 0], [0, 0, 0]], s: [0, 0, 0], FA: [[false, false, false], [false, false, false], [false, false, false]], Fs: [false, false, false],
    show: 'P', tstep: 4, sel: [1, 1]};
}
const crfEff = S => ({A: S.A.map((r, i) => r.map((x, j) => S.FA[i][j] ? NEGINF : x)), s: S.s.map((x, j) => S.Fs[j] ? NEGINF : x)});
const tagsOf = y => y.map(j => CRF_LABELS[j]);
const crfLab = registerLab({
  id: 'crf', title: 'CRF & Viterbi', icon: 'δ',
  intro: 'Ein Tagger liefert für jedes Wort Label-Scores (Emissionen). Die CRF-Schicht addiert Übergangs-Scores zwischen benachbarten Labels und bewertet so <b>ganze Folgen</b>. Ändern Sie Emissionen und Übergänge, verbieten Sie Übergänge und vergleichen Sie: lokale Entscheidung, besten Pfad (Viterbi, max) und Wahrscheinlichkeiten (Vorwärts, Summe) – kontrolliert gegen alle 81 Pfade.',
  init: crfInit,
  compute(S) {
    const {A, s} = crfEff(S);
    const v = M.viterbi(S.E, A, s), mg = M.marginals(S.E, A, s), en = M.enumerate(S.E, A, s), loc = M.localArgmax(S.E);
    const mm = mg.P.map(r => r.reduce((b, x, j) => x > r[b] ? j : b, 0));
    return {A, s, v, mg, en, loc, mm, pBest: Math.exp(v.score - mg.logZ)};
  },
  quantities(S, R) {
    return [{id: 'pb', label: 'P(bester Pfad)', value: R.pBest}, {id: 'sb', label: 'Score bester Pfad', value: R.v.score}, {id: 'lz', label: 'log Z', value: R.mg.logZ},
      ...S.words.flatMap((w, t) => CRF_LABELS.map((l, j) => ({id: `m${t}${j}`, label: `P(${w} = ${l})`, value: R.mg.P[t][j]})))];
  },
  explain(Sb, Rb, Sa, Ra) {
    const out = [];
    const dE = []; Sa.E.forEach((r, t) => r.forEach((x, j) => { if (x !== Sb.E[t][j]) dE.push(`E(${Sa.words[t]}, ${CRF_LABELS[j]}) ${f(Sb.E[t][j], 1)} → ${f(x, 1)}`); }));
    const dA = []; Sa.A.forEach((r, i) => r.forEach((x, j) => { const fb = Sb.FA[i][j], fa = Sa.FA[i][j]; if (x !== Sb.A[i][j] || fa !== fb) dA.push(`A(${CRF_LABELS[i]}→${CRF_LABELS[j]}) ${fb ? '−∞' : f(Sb.A[i][j], 1)} → ${fa ? '−∞' : f(x, 1)}`); }));
    Sa.s.forEach((x, j) => { if (x !== Sb.s[j] || Sa.Fs[j] !== Sb.Fs[j]) dA.push(`Start→${CRF_LABELS[j]} ${Sb.Fs[j] ? '−∞' : f(Sb.s[j], 1)} → ${Sa.Fs[j] ? '−∞' : f(x, 1)}`); });
    out.push('Änderungen: ' + ([...dE, ...dA].join('; ') || 'keine') + '.');
    out.push('Jeder Pfad hat den Score \\(\\mathrm{score}(y)=\\pi(y_1)+E_1(y_1)+\\sum_{t\\ge2}\\big(A(y_{t-1},y_t)+E_t(y_t)\\big)\\). Eine Änderung an \\(E_t(j)\\) oder \\(A(i,j)\\) verschiebt <em>genau die Pfade</em>, die diesen Knoten bzw. diese Kante benutzen, um denselben Betrag.');
    if (tagsOf(Rb.v.path).join() !== tagsOf(Ra.v.path).join()) out.push(`Der beste Pfad wechselt von ${tagsOf(Rb.v.path).join(' ')} zu ${tagsOf(Ra.v.path).join(' ')}: Der neue Pfad hat nun den höchsten Gesamtscore (${f(Ra.v.score)}).`);
    else out.push('Der beste Pfad bleibt gleich; seine Wahrscheinlichkeit ändert sich, weil sich \\(Z=\\sum_y e^{\\mathrm{score}(y)}\\) über <em>alle</em> Pfade mitbewegt.');
    out.push(`P(bester Pfad): ${f(Rb.pBest, 3)} → ${f(Ra.pBest, 3)}.`);
    return out.join(' ');
  },
  view(root, api) {
    const showSeg = h('span', {});
    const tslider = h('input', {type: 'range', min: 1, max: 4, step: 1, 'aria-label': 'Viterbi bis Position'});
    tslider.addEventListener('input', () => api.set({tstep: +tslider.value}));
    root.append(h('div', {class: 'row'}, showSeg, h('label', {class: 'ctl'}, 'Viterbi bis Wort ', tslider), h('button', {onclick: () => api.reset()}, 'Zurücksetzen')));
    const W = 640, H = 300, cx = t => 80 + t * 165, cy = j => 50 + j * 85;
    const svg = s('svg', {viewBox: `0 0 ${W} ${H}`, class: 'trellis', role: 'group', 'aria-label': 'Gitter (Trellis) der Label-Folgen'});
    const plane = h('div', {class: 'plane'}, h('h3', {}, 'Gitter: jede Spalte ein Wort, jeder Pfad eine Label-Folge'), svg);
    const formula = h('div', {class: 'formula-live'}), meters = h('div', {class: 'meters'}), seqs = h('div', {}), top = h('div', {}), mats = h('div', {class: 'planes'});
    root.append(plane, formula, meters, seqs, mats, top);
    return function update(S, R) {
      showSeg.replaceChildren(seg([['P', 'Wahrscheinlichkeit P(yₜ=j)'], ['delta', 'Viterbi δ (max)'], ['alpha', 'Vorwärts α (log-Summe)']], S.show, v => api.set({show: v}), 'Knotenwerte'));
      tslider.value = S.tstep;
      svg.replaceChildren();
      const T = S.words.length, L = CRF_LABELS.length, ts = S.show === 'delta' ? S.tstep : T;
      S.words.forEach((w, t) => svg.append(s('text', {x: cx(t), y: 18, 'text-anchor': 'middle', 'font-weight': 700, fill: 'var(--ink)'}, w)));
      CRF_LABELS.forEach((l, j) => svg.append(s('text', {x: 8, y: cy(j) + 4, fill: 'var(--mute)'}, l)));
      for (let t = 1; t < T; t++) for (let i = 0; i < L; i++) for (let j = 0; j < L; j++) {
        const forb = R.A[i][j] === NEGINF, bp = S.show === 'delta' && t < ts && R.v.bp[t][j] === i, best = (S.show !== 'delta' || ts === T) && R.v.path[t - 1] === i && R.v.path[t] === j;
        svg.append(s('line', {x1: cx(t - 1) + 34, y1: cy(i), x2: cx(t) - 34, y2: cy(j), class: 'edge' + (bp ? ' bp' : '') + (best ? ' best' : ''), stroke: forb ? 'var(--bad)' : null, 'stroke-dasharray': forb ? '2 5' : null, opacity: forb ? .5 : null}));
      }
      for (let t = 0; t < T; t++) for (let j = 0; j < L; j++) {
        const on = t < ts, p = R.mg.P[t][j];
        const val = S.show === 'P' ? f(p, 2) : S.show === 'delta' ? (on ? f(R.v.delta[t][j], 2) : '?') : f(R.mg.alpha[t][j], 2);
        const best = (S.show !== 'delta' || ts === T) && R.v.path[t] === j, sel = S.sel[0] === t && S.sel[1] === j;
        const g = s('g', {class: 'node' + (best ? ' best' : ''), tabindex: 0, role: 'button', 'aria-label': `${S.words[t]} als ${CRF_LABELS[j]}: Emission ${f(S.E[t][j], 1)}, Wert ${val}. Auswählen zeigt die Rechnung.`, transform: `translate(${cx(t)},${cy(j)})`},
          s('rect', {x: -34, y: -24, width: 68, height: 48, rx: 9, fill: S.show === 'P' ? `color-mix(in srgb,var(--accent) ${Math.round(p * 80)}%,var(--panel))` : 'var(--panel)', stroke: sel ? 'var(--accent)' : null, 'stroke-width': sel ? 3 : null}),
          s('text', {y: -6, 'text-anchor': 'middle', 'font-weight': 700, fill: S.show === 'P' && p > .55 ? '#fff' : 'var(--ink)'}, val),
          s('text', {y: 13, 'text-anchor': 'middle', 'font-size': 11, fill: S.show === 'P' && p > .55 ? '#fff' : 'var(--mute)'}, 'E=' + f(S.E[t][j], 1)));
        const pick = () => api.set({sel: [t, j]});
        g.addEventListener('click', pick); g.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pick(); } if (e.key === '+' || e.key === '-') { e.preventDefault(); api.set(st => { st.E[t][j] = Math.round((st.E[t][j] + (e.key === '+' ? .1 : -.1)) * 100) / 100; return st; }); } });
        svg.append(g);
      }
      // Rechnung für den gewählten Knoten
      const [t, j] = S.sel;
      if (S.show === 'P') formula.innerHTML = `P(y<sub>${t + 1}</sub> = ${CRF_LABELS[j]} | x) = exp(α<sub>${t + 1}</sub>(${CRF_LABELS[j]}) + β<sub>${t + 1}</sub>(${CRF_LABELS[j]}) − log Z) = exp(${f(R.mg.alpha[t][j])} + ${f(R.mg.beta[t][j])} − ${f(R.mg.logZ)}) = <b>${f(R.mg.P[t][j], 3)}</b><br><span class="note">α: alle Pfadanfänge bis hierher, β: alle Pfadenden ab hier – zusammen alle Pfade durch diesen Knoten. Knoten anklicken oder mit Enter wählen; + / − ändert seine Emission.</span>`;
      else if (t === 0) formula.innerHTML = `${S.show === 'alpha' ? 'α' : 'δ'}₁(${CRF_LABELS[j]}) = π(${CRF_LABELS[j]}) + E₁(${CRF_LABELS[j]}) = ${f(R.s[j], 1)} + ${f(S.E[0][j], 1)} = <b>${f(R.s[j] + S.E[0][j])}</b>`;
      else {
        const prev = S.show === 'alpha' ? R.mg.alpha[t - 1] : R.v.delta[t - 1];
        const terms = CRF_LABELS.map((l, i) => `${f(prev[i])} ${R.A[i][j] === NEGINF ? '+ (−∞)' : (R.A[i][j] < 0 ? '− ' + f(-R.A[i][j], 1) : '+ ' + f(R.A[i][j], 1))}`);
        const op = S.show === 'alpha' ? 'log Σ exp' : 'max';
        const inner = CRF_LABELS.map((_, i) => prev[i] + R.A[i][j]);
        const agg = S.show === 'alpha' ? M.lse(inner) : Math.max(...inner);
        formula.innerHTML = `${S.show === 'alpha' ? 'α' : 'δ'}<sub>${t + 1}</sub>(${CRF_LABELS[j]}) = E<sub>${t + 1}</sub>(${CRF_LABELS[j]}) + ${op}<sub>i</sub>[ ${S.show === 'alpha' ? 'α' : 'δ'}<sub>${t}</sub>(i) + A(i, ${CRF_LABELS[j]}) ] = ${f(S.E[t][j], 1)} + ${op}( ${terms.join(' , ')} ) = ${f(S.E[t][j], 1)} + ${f(agg)} = <b>${f(S.E[t][j] + agg)}</b>`
          + (S.show !== 'alpha' && S.show !== 'P' ? '' : '') + `<br><span class="note">${S.show === 'alpha' ? 'Summe über alle Vorgänger (in Log-Form): zählt jeden Pfad bis hierher.' : 'Maximum über alle Vorgänger: merkt sich nur den besten Pfad bis hierher (Rückzeiger gestrichelt).'} Knoten anklicken oder mit Enter wählen; + / − ändert seine Emission.</span>`;
      }
      const brute = R.en.logZ;
      meters.replaceChildren(meter('Score bester Pfad', f(R.v.score), null), meter('log Z (Vorwärts)', f(R.mg.logZ, 4), null), meter('log Z (alle 81 Pfade)', f(brute, 4), null, 'Kontrolle durch vollständige Aufzählung'),
        meter('P(bester Pfad)', f(R.pBest, 3), R.pBest));
      const row = (name, y, note) => { const tg = tagsOf(y), ok = M.bioValid(tg);
        return h('div', {}, h('div', {class: 'row', style: 'margin:4px 0 0'}, h('b', {style: 'min-width:220px;font-size:14px'}, name), h('span', {class: 'badge ' + (ok ? 'ok' : 'bad')}, ok ? 'gültiges BIO' : 'ungültiges BIO'), h('span', {class: 'note'}, note)),
          h('div', {class: 'seqrow'}, tg.map((x, k) => h('div', {class: 'tk' + (x.startsWith('I-') && (k === 0 || tg[k - 1] === 'O' || tg[k - 1].slice(2) !== x.slice(2)) ? ' bad' : '')}, S.words[k], h('small', {}, x))))); };
      seqs.replaceChildren(row('Lokal (nur Emissionen)', R.loc, 'argmax je Wort, Übergänge ignoriert'), row('Viterbi (bester Pfad)', R.v.path, 'argmax über ganze Folgen'), row('Je Position wahrscheinlichstes Label', R.mm, 'argmax der Randverteilungen'));
      // Matrizen bearbeiten
      const em = h('table', {class: 'matrix'}, h('tr', {}, h('th', {}, 'Emission E'), ...CRF_LABELS.map(l => h('th', {}, l))),
        S.words.map((w, t) => h('tr', {}, h('th', {}, w), CRF_LABELS.map((l, j) => h('td', {}, stepper(S.E[t][j], v => api.set(st => { st.E[t][j] = v; return st; }), `Emission ${w} ${l}`))))));
      const tr = h('table', {class: 'matrix'}, h('tr', {}, h('th', {}, 'von ↓ / nach →'), ...CRF_LABELS.map(l => h('th', {}, l))),
        h('tr', {}, h('th', {}, 'Start π'), CRF_LABELS.map((l, j) => h('td', {}, stepper(S.s[j], v => api.set(st => { st.s[j] = v; return st; }), `Start nach ${l}`, {forbid: S.Fs[j]}),
          h('label', {class: 'note', style: 'display:block'}, h('input', {type: 'checkbox', checked: S.Fs[j] || null, onchange: e => api.set(st => { st.Fs[j] = e.target.checked; return st; })}), ' verbieten')))),
        CRF_LABELS.map((li, i) => h('tr', {}, h('th', {}, li), CRF_LABELS.map((lj, j) => h('td', {}, stepper(S.A[i][j], v => api.set(st => { st.A[i][j] = v; return st; }), `Übergang ${li} nach ${lj}`, {forbid: S.FA[i][j]}),
          h('label', {class: 'note', style: 'display:block'}, h('input', {type: 'checkbox', checked: S.FA[i][j] || null, onchange: e => api.set(st => { st.FA[i][j] = e.target.checked; return st; })}), ' verbieten'))))));
      mats.replaceChildren(h('div', {class: 'calc-wrap'}, em), h('div', {class: 'calc-wrap'}, tr));
      const best = R.en.paths.slice(0, 6);
      top.replaceChildren(h('h3', {style: 'font-size:14px;margin:10px 0 4px'}, 'Die sechs besten von 81 Pfaden (vollständige Aufzählung zur Kontrolle)'),
        h('table', {class: 'calc'}, h('tr', {}, h('th', {}, 'Folge'), h('th', {}, 'Score'), h('th', {}, 'P(y | x) = e^score / Z')),
          best.map(p => h('tr', {}, h('td', {}, tagsOf(p.y).join(' '), M.bioValid(tagsOf(p.y)) ? '' : h('span', {class: 'badge bad', style: 'margin-left:6px'}, 'ungültig')), h('td', {}, f(p.score)), h('td', {}, f(p.p, 3))))));
    };
  },
});
const sameTags = (a, b) => a.join() === b.join();
crfLab.path = [
  {id: 'r1', title: 'Jedes Wort für sich', story: 'Alle Übergänge sind 0. Die lokale Entscheidung ergibt <code>I-PER I-PER O O</code> – eine Personen-Spanne, die mit <code>I</code> beginnt.',
    setup: () => crfInit(),
    predict: {q: 'Solange alle Übergänge 0 sind: Kann Viterbi etwas anderes liefern als die lokale Entscheidung?', options: ['Nein – der Score zerfällt in unabhängige Summanden je Wort.', 'Ja – Viterbi bevorzugt automatisch gültige Folgen.', 'Ja, wenn die Emissionen knapp sind.'], correct: 0},
    task: 'Ändern Sie bei Übergängen = 0 eine Emission so, dass sich die lokale Entscheidung ändert, und vergleichen Sie mit Viterbi.',
    goal: (S, R) => S.A.flat().every(x => x === 0) && !S.FA.flat().some(Boolean) && !S.Fs.some(Boolean) && S.s.every(x => x === 0) && sameTags(R.v.path, R.loc) && !sameTags(R.loc, [1, 1, 2, 2]),
    reveal: 'Mit \\(A\\equiv0\\) ist \\(\\mathrm{score}(y)=\\sum_tE_t(y_t)\\); das Maximum einer Summe unabhängiger Terme ist die Summe der Maxima. Viterbi = lokale Entscheidung. Die CRF-Schicht wirkt <em>nur</em> über die Übergänge.', links: {book: 'decoding', bookLabel: '§9'}},
  {id: 'r2', title: 'Verbotene Übergänge', story: 'In BIO darf <code>I-PER</code> nur nach <code>B-PER</code> oder <code>I-PER</code> stehen. Verbieten Sie die Übergänge, die das verletzen.',
    setup: () => crfInit(),
    task: 'Setzen Sie „Start → I-PER“ und „O → I-PER“ auf −∞. Erreichen Sie eine gültige Viterbi-Folge.',
    goal: (S, R) => S.Fs[1] && S.FA[2][1] && M.bioValid(tagsOf(R.v.path)),
    reveal: 'Ein Pfad mit verbotener Kante hat Score \\(-\\infty\\) und Wahrscheinlichkeit 0 – Viterbi kann ihn nie wählen. Beachten Sie: Gewählt wird nicht „die lokale Folge mit repariertem ersten Label“, sondern der beste <em>gültige</em> Pfad, hier <code>B-PER I-PER O O</code>. Prüfen Sie in der Tabelle: Alle ungültigen Folgen haben P = 0.', links: {book: 'decoding', bookLabel: '§9'}},
  {id: 'r3', title: 'Viterbi Schritt für Schritt', story: 'Ansicht „Viterbi δ“. \\(\\delta_t(j)\\) ist der Score des besten Pfades, der an Position \\(t\\) in Label \\(j\\) endet.',
    setup: S => { S.show = 'delta'; S.tstep = 1; S.sel = [1, 1]; return S; },
    predict: {q: 'Wie viele Additionen braucht Viterbi für \\(T\\) Wörter und \\(L\\) Labels ungefähr?', options: ['\\(T\\cdot L^2\\)', '\\(L^T\\)', '\\(T^L\\)'], correct: 0},
    task: 'Schieben Sie „Viterbi bis Wort“ von 1 bis 4 und wählen Sie Knoten an, um die max-Rechnung zu sehen.', goal: S => S.show === 'delta' && S.tstep === 4,
    reveal: 'Jeder Knoten prüft \\(L\\) Vorgänger: \\(\\delta_t(j)=E_t(j)+\\max_i[\\delta_{t-1}(i)+A(i,j)]\\). Das sind \\(T\\cdot L^2\\) Schritte statt \\(L^T\\) Pfade (hier 36 statt 81; bei 9 Labels und 30 Wörtern \\(2430\\) statt \\(\\approx4\\cdot10^{28}\\)). Möglich, weil der Score nur von <em>benachbarten</em> Labels abhängt (Markov-Annahme).', links: {book: 'decoding', bookLabel: '§9'}},
  {id: 'r4', title: 'Summe statt Maximum', story: 'Für das Training braucht die CRF \\(P(y\\mid x)=e^{\\mathrm{score}(y)}/Z\\) mit \\(Z=\\sum_{y\'}e^{\\mathrm{score}(y\')}\\).',
    setup: S => { S.show = 'alpha'; S.sel = [3, 2]; return S; },
    task: 'Ändern Sie in der Ansicht „Vorwärts α“ eine Emission und vergleichen Sie log Z (Vorwärts) mit log Z (alle 81 Pfade).', goal: (S) => S.show === 'alpha' && JSON.stringify(S.E) !== JSON.stringify(crfInit().E),
    reveal: 'Der Vorwärts-Algorithmus ist Viterbi mit \\(\\max\\) ersetzt durch \\(\\log\\sum\\exp\\): \\(\\alpha_t(j)=E_t(j)+\\log\\sum_ie^{\\alpha_{t-1}(i)+A(i,j)}\\), \\(\\log Z=\\log\\sum_je^{\\alpha_T(j)}\\). Beide Zahlen stimmen exakt überein – das ist die Kontrolle. Das Distributivgesetz \\(a+\\max(b,c)=\\max(a+b,a+c)\\) gilt genauso für \\(\\log\\sum\\exp\\).', links: {book: 'decoding', bookLabel: '§9'}},
  {id: 'r5', title: 'Bester Pfad ≠ beste Einzelentscheidungen', story: 'Ansicht „Wahrscheinlichkeit“: Jeder Knoten zeigt \\(P(y_t=j\\mid x)\\) – summiert über alle Pfade durch diesen Knoten.',
    setup: S => { const n = crfInit(); n.show = 'P'; n.Fs[1] = true; n.FA[2][1] = true; return n; },
    task: 'Konstruieren Sie einen Zustand, in dem die Folge der je Position wahrscheinlichsten Labels <b>nicht</b> der Viterbi-Pfad ist.', goal: (S, R) => !sameTags(R.mm, R.v.path),
    reveal: 'Viterbi maximiert die Wahrscheinlichkeit der <em>ganzen Folge</em>; der Randverteilungs-Argmax maximiert die erwartete Zahl richtiger Einzel-Labels. Beide Kriterien unterscheiden sich – und die Folge der Rand-Argmaxe kann sogar eine verbotene Kante enthalten (Wahrscheinlichkeit 0 als Ganzes!). Für NER mit gültigen Spannen deshalb Viterbi.', links: {book: 'decoding', bookLabel: '§9'}},
];
crfLab.challenges = [
  {id: 'k-soft', title: 'Weiche Strafe', level: 'mittel', goal: 'Machen Sie die Viterbi-Folge gültig, <b>ohne</b> zu verbieten und ohne Emissionen zu ändern – nur mit endlichen Übergangs- und Start-Scores.', constraint: 'Emissionen wie zu Beginn, keine −∞.',
    setup: () => crfInit(),
    check: (S, R) => { const okC = JSON.stringify(S.E) === JSON.stringify(crfInit().E) && !S.FA.flat().some(Boolean) && !S.Fs.some(Boolean); const v = M.bioValid(tagsOf(R.v.path)); return {done: okC && v, progress: okC ? (v ? 1 : .3) : 0, msg: okC ? `Viterbi: ${tagsOf(R.v.path).join(' ')}` : 'Bedingung verletzt – „Starten“.'}; },
    hints: ['Das erste Wort wählt I-PER, weil E(Jan, I-PER) = 1,2 > E(Jan, B-PER) = 1,0. Was kostet es, mit I-PER zu <em>beginnen</em>?', 'Ein negativer Start-Score für I-PER senkt alle Pfade, die mit I-PER beginnen, um denselben Betrag.', 'Start → I-PER ≤ −0,3 genügt hier. Warum genau mehr als 0,2?'],
    success: 'Eine weiche Strafe reicht, sobald sie den Emissionsvorsprung übersteigt: Start→I-PER muss kleiner als \\(-(1{,}2-1{,}0)=-0{,}2\\) sein. Gelernte CRFs erhalten genau solche stark negativen Übergänge aus den Daten – praktisch verboten, formal endlich.', links: {book: 'decoding'}},
  {id: 'k-sure', title: 'Gewissheit', level: 'mittel', goal: 'Bringen Sie \\(P(\\text{bester Pfad})\\ge 0{,}6\\) – nur über Übergänge und Verbote.', constraint: 'Emissionen unverändert.',
    setup: () => crfInit(),
    check: (S, R) => { const okC = JSON.stringify(S.E) === JSON.stringify(crfInit().E); return {done: okC && R.pBest >= .6, progress: R.pBest / .6, msg: `P(bester Pfad) = ${f(R.pBest, 3)}`}; },
    hints: ['\\(P\\) steigt, wenn konkurrierende Pfade Score verlieren. Welche Pfade sind die stärksten Konkurrenten (Tabelle)?', 'Verbote entfernen viele Pfade aus \\(Z\\) auf einmal.', 'Verbieten Sie alle in BIO unmöglichen Übergänge und belohnen Sie B-PER → I-PER.'],
    success: 'Wahrscheinlichkeit ist relativ: \\(P(y^*)=1/\\sum_ye^{\\mathrm{score}(y)-\\mathrm{score}(y^*)}\\). Jede Verkleinerung eines Konkurrenten-Scores erhöht \\(P(y^*)\\), auch wenn \\(\\mathrm{score}(y^*)\\) gleich bleibt.', links: {book: 'decoding'}},
  {id: 'k-mm', title: 'Die Randverteilungs-Falle', level: 'Transfer', goal: 'Finden Sie einen Zustand, in dem die Folge der Rand-Argmaxe eine <b>ungültige</b> BIO-Folge ist, obwohl alle ungültigen Übergänge verboten sind.', constraint: 'Start→I-PER und O→I-PER verboten.',
    setup: () => { const n = crfInit(); n.Fs[1] = true; n.FA[2][1] = true; return n; },
    check: (S, R) => { const okC = S.Fs[1] && S.FA[2][1]; const bad = !M.bioValid(tagsOf(R.mm)); return {done: okC && bad, progress: okC ? (sameTags(R.mm, R.v.path) ? .2 : .6) + (bad ? .4 : 0) : 0, msg: `Rand-Argmaxe: ${tagsOf(R.mm).join(' ')}`}; },
    hints: ['Sie brauchen an einer Position \\(t\\) „O“ als wahrscheinlichstes Label und an \\(t+1\\) „I-PER“.', 'Machen Sie an Position 2 die Labels O und B-PER fast gleich wahrscheinlich – aber verteilt auf viele Pfade für O.', 'Versuchen Sie: Ullrich mit E(B-PER) ≈ E(O) und I-PER schwach; gewinnt mit hohem I-PER.'],
    success: 'Jedes einzelne Label ist das wahrscheinlichste an seiner Position, die Folge als Ganzes hat aber Wahrscheinlichkeit 0. Randverteilungen „wissen“ nichts voneinander – deshalb dekodiert man strukturierte Ausgaben mit Viterbi.', links: {book: 'decoding'}},
  {id: 'k-imp', title: 'Verbotenes erzwingen?', level: 'Transfer', goal: 'Bringen Sie Viterbi dazu, einen Pfad mit dem verbotenen Übergang O → I-PER zu wählen – mit beliebig großen Emissionen.', constraint: 'O → I-PER bleibt verboten.',
    setup: () => { const n = crfInit(); n.FA[2][1] = true; return n; },
    check: (S, R) => ({done: false, progress: 0, msg: `Viterbi: ${tagsOf(R.v.path).join(' ')}`}),
    impossible: {q: 'Warum gelingt das nie?', options: ['Jeder Pfad mit dieser Kante hat Score \\(-\\infty\\); jeder Pfad ohne sie hat einen endlichen Score und ist damit besser.', 'Emissionen sind auf ±10 begrenzt.', 'Viterbi prüft Übergänge nur zwischen den ersten beiden Wörtern.'], correct: 0,
      applies: S => S.FA[2][1], notApplicable: 'Der Übergang ist gerade nicht verboten.', why: {1: 'Es gibt keine Begrenzung – auch \\(10^6\\) ist endlich und verliert gegen \\(-\\infty\\) nicht.', 2: 'Viterbi prüft an jeder Position alle \\(L^2\\) Übergänge.'}},
    hints: ['Was ist \\(x+(-\\infty)\\) für endliches \\(x\\)?', 'Gibt es immer mindestens einen Pfad mit endlichem Score?'],
    success: 'Solange mindestens ein Pfad endlichen Score hat (hier: alles O), verliert jeder Pfad mit −∞-Kante. Gegenbeispiel-Denken: Wäre auch Start → O usw. verboten, könnte <em>jeder</em> Pfad −∞ haben – dann ist \\(Z=0\\) und \\(P\\) undefiniert.', links: {book: 'decoding'}},
];

// =====================================================================================
// Lab 3: BiRNN – wer beeinflusst wen? (exakte Jacobi-Normen, kontrafaktische Wörter)
// =====================================================================================
const VOCAB = {Washington: [1, 0.2], signed: [0, 1], state: [0, -1], the: [0.1, 0.1], bill: [0.3, 0.5], university: [-0.2, -0.9], said: [0.1, 0.9], a: [0, 0]};
function rnnInit() {
  return {words: ['Washington', 'signed', 'the', 'bill'], emb: clone(VOCAB), fw: {wx: [0.8, 0.3], wh: 0.5, b: 0}, bw: {wx: [0.2, 1.2], wh: 0.9, b: 0}, uf: 0.3, ub: 1.0, c: -0.3, bwOn: true, focus: 0};
}
const rnnP = d => ({Wx: [d.wx.slice()], Wh: [[d.wh]], b: [d.b]});
const rnnLab = registerLab({
  id: 'birnn', title: 'BiRNN', icon: '⇄',
  intro: 'Ist „Washington“ eine Person oder ein Ort? Das entscheidet oft erst das <b>nächste</b> Wort. Tauschen Sie Wörter aus, ändern Sie Rückkopplungen und schalten Sie die Rückwärts-Richtung ab. Die Matrizen zeigen exakt, welches Wort welchen Zustand beeinflusst \\((\\lVert\\partial h_t/\\partial x_j\\rVert)\\).',
  init: rnnInit,
  compute(S) {
    const X = S.words.map(w => S.emb[w]);
    const F = M.rnnInfluence(X, rnnP(S.fw), false), B = M.rnnInfluence(X, rnnP(S.bw), true);
    const ub = S.bwOn ? S.ub : 0;
    const z = F.hs.map((hf, t) => S.uf * hf[0] + ub * B.hs[t][0] + S.c);
    const C = F.M.map((r, t) => r.map((x, j) => Math.sqrt((S.uf * x) ** 2 + (ub * B.M[t][j]) ** 2)));  // Einfluss auf den Score z_t
    return {X, F, B, z, C, dec: z[0] > 0 ? 'PER' : 'LOC'};
  },
  quantities(S, R) { return [{id: 'z1', label: `Score z₁ für „${S.words[0]}“ (> 0: PER)`, value: R.z[0]}, ...S.words.map((w, j) => ({id: 'c' + j, label: `Einfluss von Wort ${j + 1} auf z₁`, value: R.C[0][j]})), ...S.words.map((w, t) => ({id: 'hb' + t, label: `h←(${t + 1})`, value: R.B.hs[t][0]}))]; },
  explain(Sb, Rb, Sa, Ra) {
    const out = [];
    const ch = Sa.words.map((w, j) => w !== Sb.words[j] ? j : -1).filter(j => j >= 0);
    if (ch.length) out.push(`Geändert: Wort ${ch.map(j => j + 1).join(', ')}. Der Vorwärtszustand \\(\\overrightarrow h_t\\) hängt nur von \\(x_1..x_t\\) ab, der Rückwärtszustand \\(\\overleftarrow h_t\\) nur von \\(x_t..x_T\\).`);
    if (ch.length && Math.min(...ch) > 0) out.push(Sa.bwOn ? `Weil Wort ${Math.min(...ch) + 1} rechts von Wort 1 steht, erreicht die Änderung \\(z_1\\) ausschließlich über \\(\\overleftarrow h_1\\) (${f(Rb.B.hs[0][0], 3)} → ${f(Ra.B.hs[0][0], 3)}).` : 'Die Rückwärtsrichtung ist aus: Eine Änderung rechts von Wort 1 kann \\(z_1\\) nicht erreichen.');
    if (Sa.bw.wh !== Sb.bw.wh || Sa.fw.wh !== Sb.fw.wh) out.push('Die Rückkopplung \\(w_h\\) ist der Faktor, mit dem Information pro Schritt weitergegeben wird: \\(\\partial h_t/\\partial h_{t\\pm1}=(1-h_t^2)\\,w_h\\). Über \\(k\\) Schritte multiplizieren sich \\(k\\) solcher Faktoren – kleine \\(|w_h|\\) oder gesättigte tanh lassen den Einfluss exponentiell schrumpfen.');
    if (Sa.bwOn !== Sb.bwOn) out.push(Sa.bwOn ? 'Rückwärtsrichtung eingeschaltet: \\(z_t\\) sieht jetzt den ganzen Satz.' : 'Rückwärtsrichtung aus: das Modell ist ein reines Vorwärts-RNN – kausal, aber blind für rechten Kontext.');
    out.push(`\\(z_1\\): ${f(Rb.z[0], 3)} → ${f(Ra.z[0], 3)} (Entscheidung ${Rb.dec} → ${Ra.dec}).`);
    return out.join(' ');
  },
  view(root, api) {
    const ctl = h('div', {}), chain = h('div', {class: 'plane'}), mats = h('div', {class: 'planes'}), fl = h('div', {class: 'formula-live'});
    root.append(ctl, chain, fl, mats);
    const sl = (label, get, set, min, max, step = .05) => { const i = h('input', {type: 'range', min, max, step, value: get(api.S), 'aria-label': label}); const v = h('b', {}, f(get(api.S))); i.addEventListener('input', () => api.set(st => { set(st, +i.value); return st; })); return {el: h('label', {class: 'ctl'}, label + ' ', i, v), up: S => { i.value = get(S); v.textContent = f(get(S)); }}; };
    const sliders = [sl('w_h vorwärts', S => S.fw.wh, (S, x) => { S.fw.wh = x; }, -1.5, 1.5), sl('w_h rückwärts', S => S.bw.wh, (S, x) => { S.bw.wh = x; }, -1.5, 1.5), sl('Bias rückwärts', S => S.bw.b, (S, x) => { S.bw.b = x; }, -3, 3),
      sl('u vorwärts', S => S.uf, (S, x) => { S.uf = x; }, -2, 2), sl('u rückwärts', S => S.ub, (S, x) => { S.ub = x; }, -2, 2)];
    const bw = h('input', {type: 'checkbox'}); bw.addEventListener('change', () => api.set({bwOn: bw.checked}));
    ctl.append(h('div', {class: 'row'}, ...api.S.words.map((w, j) => { const sel = h('select', {'aria-label': `Wort ${j + 1}`}, Object.keys(VOCAB).map(k => h('option', {value: k, selected: k === w || null}, k))); sel.addEventListener('change', () => api.set(st => { st.words[j] = sel.value; return st; })); sel.dataset.j = j; return sel; })),
      h('div', {class: 'row'}, h('label', {class: 'ctl'}, bw, 'Rückwärts-RNN aktiv'), ...sliders.map(x => x.el), h('button', {onclick: () => api.reset()}, 'Zurücksetzen')));
    return function update(S, R) {
      bw.checked = S.bwOn; sliders.forEach(x => x.up(S)); ctl.querySelectorAll('select').forEach(sel => { sel.value = S.words[+sel.dataset.j]; });
      const W = 640, H = 250, x = t => 90 + t * 150, col = v => `color-mix(in srgb,${v >= 0 ? 'var(--t0)' : 'var(--t1)'} ${Math.round(Math.min(1, Math.abs(v)) * 75)}%,var(--panel))`;
      const svg = s('svg', {viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': 'Ketten der Vorwärts- und Rückwärtszustände mit Score je Wort'});
      [['h→', 60], ['h←', 125], ['z', 195]].forEach(([l, y]) => svg.append(s('text', {x: 8, y: y + 5, fill: 'var(--mute)', 'font-weight': 600}, l)));
      S.words.forEach((w, t) => {
        svg.append(s('text', {x: x(t), y: 20, 'text-anchor': 'middle', 'font-weight': 700, fill: 'var(--ink)'}, w));
        if (t) svg.append(s('line', {x1: x(t - 1) + 34, y1: 60, x2: x(t) - 38, y2: 60, stroke: 'var(--fw)', 'stroke-width': 1 + 3 * Math.min(1, Math.abs(S.fw.wh)), 'marker-end': ''}), s('text', {x: (x(t - 1) + x(t)) / 2, y: 52, 'text-anchor': 'middle', 'font-size': 11, fill: 'var(--fw)'}, '→'));
        if (t && S.bwOn) svg.append(s('line', {x1: x(t) - 34, y1: 125, x2: x(t - 1) + 38, y2: 125, stroke: 'var(--bw)', 'stroke-width': 1 + 3 * Math.min(1, Math.abs(S.bw.wh))}), s('text', {x: (x(t - 1) + x(t)) / 2, y: 117, 'text-anchor': 'middle', 'font-size': 11, fill: 'var(--bw)'}, '←'));
        const cell = (y, v, on = true) => s('g', {}, s('rect', {x: x(t) - 34, y: y - 18, width: 68, height: 36, rx: 8, fill: on ? col(v) : 'var(--bg)', stroke: 'var(--line)'}), s('text', {x: x(t), y: y + 5, 'text-anchor': 'middle', 'font-variant-numeric': 'tabular-nums', fill: 'var(--ink)'}, on ? f(v, 2) : 'aus'));
        svg.append(cell(60, R.F.hs[t][0]), cell(125, R.B.hs[t][0], S.bwOn), cell(195, R.z[t]));
        if (t === 0) svg.append(s('text', {x: x(0), y: 235, 'text-anchor': 'middle', 'font-weight': 700, fill: R.dec === 'PER' ? 'var(--t0)' : 'var(--t1)'}, R.dec === 'PER' ? '→ Person' : '→ Ort'));
      });
      chain.replaceChildren(h('h3', {}, 'Zustände (Farbe: Vorzeichen und Betrag) und Score z = u→·h→ + u←·h← + c'), svg);
      fl.innerHTML = `z₁ = ${f(S.uf)}·${f(R.F.hs[0][0], 3)} + ${f(S.bwOn ? S.ub : 0)}·${f(R.B.hs[0][0], 3)} ${S.c < 0 ? '− ' + f(-S.c) : '+ ' + f(S.c)} = <b>${f(R.z[0], 3)}</b> ⇒ ${R.dec === 'PER' ? 'Person' : 'Ort'}<br><span class="note">h←₁ = tanh(w_x·x₁ + w_h·h←₂ + b) = tanh(${f(S.bw.wx[0])}·${f(R.X[0][0])} + ${f(S.bw.wx[1])}·${f(R.X[0][1])} + ${f(S.bw.wh)}·${f(R.B.hs[1][0], 3)} + ${f(S.bw.b)}) – die Zukunft kommt nur über h←₂ herein.</span>`;
      const heat = (title, Mx, note) => { const n = S.words.length, cells = [h('div', {class: 'h'}, 'Zustand ↓ / Wort →'), ...S.words.map((w, j) => h('div', {class: 'h'}, (j + 1) + ' ' + w))];
        Mx.forEach((r, t) => { cells.push(h('div', {class: 'h'}, `t=${t + 1}`)); r.forEach(v => cells.push(h('div', {style: `background:color-mix(in srgb,var(--accent) ${Math.round(Math.min(1, v) * 85)}%,transparent);color:${v > .6 ? '#fff' : 'inherit'}`}, v === 0 ? '0' : f(v, 2)))); });
        return h('div', {}, h('h3', {style: 'font-size:14px;margin:6px 0'}, title), h('div', {class: 'heat', style: `grid-template-columns:repeat(${n + 1},minmax(0,1fr))`}, cells), h('p', {class: 'note'}, note)); };
      mats.replaceChildren(heat('Vorwärts: ‖∂h→ₜ/∂xⱼ‖', R.F.M, 'Oberhalb der Diagonale exakt 0: Zukunft unsichtbar.'), heat(S.bwOn ? 'Rückwärts: ‖∂h←ₜ/∂xⱼ‖' : 'Rückwärts (aus)', S.bwOn ? R.B.M : R.B.M.map(r => r.map(() => 0)), 'Unterhalb der Diagonale exakt 0: Vergangenheit unsichtbar.'),
        heat('Score: ‖∂zₜ/∂xⱼ‖', R.C, 'Mit beiden Richtungen hängt jedes zₜ vom ganzen Satz ab.'));
    };
  },
});
rnnLab.path = [
  {id: 'b1', title: 'Vorwärts sieht nur die Vergangenheit', story: '„Washington signed …“ (Person) gegen „Washington state …“ (Ort). Schalten Sie zuerst die Rückwärts-Richtung ab.',
    setup: () => { const n = rnnInit(); n.bwOn = false; return n; },
    predict: {q: 'Ohne Rückwärts-RNN: Sie ersetzen „signed“ durch „state“. Was passiert mit der Entscheidung für Wort 1?', options: ['Nichts – \\(\\overrightarrow h_1\\) hängt nur von \\(x_1\\) ab.', 'Sie kippt zu „Ort“.', 'Sie wird unsicherer, kippt aber nicht.'], correct: 0},
    task: 'Rückwärts aus, ersetzen Sie Wort 2 durch „state“.', goal: S => !S.bwOn && S.words[0] === 'Washington' && S.words[1] === 'state',
    reveal: '<b>Satz 1:</b> \\(\\overrightarrow h_t=f(x_1,\\dots,x_t)\\). Die Vorwärts-Matrix ist eine untere Dreiecksmatrix: oberhalb der Diagonale steht exakt 0, nicht „wenig“. Ein Vorwärts-Tagger kann die Ambiguität an Position 1 nicht auflösen.', links: {book: 'birnn', bookLabel: '§5', tasks: ['B2']}},
  {id: 'b2', title: 'Rückwärts bringt die Zukunft', story: 'Jetzt mit Rückwärts-RNN.',
    setup: () => rnnInit(),
    predict: {q: 'Mit Rückwärts-RNN: „signed“ → „state“. Über welchen Zustand erreicht die Änderung \\(z_1\\)?', options: ['Nur über \\(\\overleftarrow h_1\\) (via \\(\\overleftarrow h_2\\)).', 'Über \\(\\overrightarrow h_1\\) und \\(\\overleftarrow h_1\\).', 'Direkt über \\(x_2\\).'], correct: 0},
    task: 'Lassen Sie die Entscheidung für „Washington“ durch ein anderes Wort 2 kippen.', goal: (S, R) => S.bwOn && S.words[0] === 'Washington' && S.words[1] !== 'signed' && R.dec === 'LOC',
    reveal: '<b>Satz 2:</b> \\([\\overrightarrow h_t;\\overleftarrow h_t]\\) hängt vom ganzen Satz ab. Preis: Man muss den Satz <em>vollständig</em> kennen, bevor ein Label feststeht – für Streaming ungeeignet. Beobachten Sie: Mit „signed“ ist \\(\\lVert\\partial z_1/\\partial x_2\\rVert\\) sehr klein (tanh gesättigt), mit „state“ groß. Einfluss ist zustandsabhängig.', links: {book: 'birnn', bookLabel: '§5', tasks: ['B2']}},
  {id: 'b3', title: 'Erinnerung verblasst', story: 'Wie stark wirkt Wort 4 noch auf \\(\\overleftarrow h_1\\)? Jeder Schritt multipliziert mit \\((1-h^2)\\,w_h\\).',
    setup: () => { const n = rnnInit(); n.words[1] = 'state'; return n; },
    task: 'Verkleinern Sie \\(w_h\\) rückwärts, bis der Einfluss von Wort 4 auf \\(\\overleftarrow h_1\\) unter 0,01 fällt.', goal: (S, R) => S.bwOn && R.B.M[0][3] < .01,
    reveal: '\\(\\frac{\\partial \\overleftarrow h_1}{\\partial x_4}=\\prod_{t=1}^{3}(1-\\overleftarrow h_t^2)\\,w_h\\cdot(1-\\overleftarrow h_4^2)\\,w_x\\). Bei \\(|w_h|<1\\) schrumpft das geometrisch – verschwindende Gradienten. LSTM/GRU umgehen das mit additiven Zellzuständen; bei Attention ist jedes Wort in einem Schritt erreichbar.', links: {book: 'birnn', bookLabel: '§5'}},
];
rnnLab.challenges = [
  {id: 'n-imp', title: 'Nur vorwärts umstimmen', level: 'Transfer', goal: 'Rückwärts aus. Lassen Sie die Entscheidung für Wort 1 kippen – indem Sie <b>nur Wörter 2–4</b> tauschen.', constraint: 'Wort 1 = Washington, Rückwärts aus, Parameter fest.',
    setup: () => { const n = rnnInit(); n.bwOn = false; return n; },
    check: (S, R) => ({done: false, progress: 0, msg: `Entscheidung: ${R.dec}`}),
    impossible: {q: 'Warum geht das nicht?', options: ['\\(z_1\\) hängt ohne Rückwärts-RNN nur von \\(\\overrightarrow h_1=f(x_1)\\) ab; Wörter 2–4 kommen darin nicht vor.', 'Die Vokabelliste ist zu klein.', 'tanh ist gesättigt.'], correct: 0, applies: S => !S.bwOn && S.words[0] === 'Washington', notApplicable: 'Bedingung nicht erfüllt (Rückwärts aus, Wort 1 = Washington).',
      why: {1: 'Kein Wort an Position 2–4 kann wirken – auch ein beliebiger Vektor nicht: Die Ableitung ist exakt 0.', 2: 'Sättigung macht Einfluss klein, aber nicht exakt 0. Hier ist er strukturell 0.'}},
    hints: ['Schauen Sie in die Vorwärts-Matrix, Zeile t=1.'],
    success: 'Strukturelle Unabhängigkeit (exakt 0) ist etwas anderes als schwacher Einfluss. Das ist der Kern von Satz 1 – und der Grund für bidirektionale Encoder in der Sequenzmarkierung.', links: {book: 'birnn', tasks: ['B2']}},
  {id: 'n-far', title: 'Fernwirkung', level: 'mittel', goal: 'Bringen Sie den Einfluss von Wort 4 auf \\(z_1\\) auf mindestens 0,3.', constraint: 'Wörter frei, Parameter frei.',
    setup: () => { const n = rnnInit(); n.words[1] = 'state'; return n; },
    check: (S, R) => ({done: R.C[0][3] >= .3, progress: R.C[0][3] / .3, msg: `‖∂z₁/∂x₄‖ = ${f(R.C[0][3], 3)}`}),
    hints: ['Der Weg führt über drei Rückkopplungen \\(w_h\\) – machen Sie \\(|w_h|\\) groß.', 'Gesättigte Zustände (|h| nahe 1) blockieren. Bias und Wortwahl so, dass die h-Werte mittelgroß bleiben.', 'w_h rückwärts ≈ 1,4, u rückwärts ≈ 2, Wörter mit kleinen Einbettungen (the, a).'],
    success: 'Fernwirkung braucht Faktoren \\(|(1-h^2)w_h|\\) nahe 1 auf dem ganzen Weg – zu groß führt zu Sättigung, zu klein zum Verschwinden. Dieses Balanceproblem motivierte LSTMs.', links: {book: 'birnn'}},
  {id: 'n-sat', title: 'Gesättigt', level: 'Transfer', goal: 'Machen Sie \\(z_1\\) unempfindlich für Wort 2 (\\(\\lVert\\partial z_1/\\partial x_2\\rVert<0{,}02\\)), obwohl \\(w_h\\) rückwärts \\(\\ge 0{,}9\\) und \\(u\\) rückwärts \\(\\ge1\\).', constraint: 'Rückwärts an.',
    setup: () => { const n = rnnInit(); n.words[1] = 'state'; return n; },
    check: (S, R) => { const ok = S.bwOn && S.bw.wh >= .9 && S.ub >= 1; return {done: ok && R.C[0][1] < .02, progress: ok ? Math.min(1, .02 / Math.max(R.C[0][1], 1e-9)) : 0, msg: `‖∂z₁/∂x₂‖ = ${f(R.C[0][1], 4)}${ok ? '' : ' (Bedingung verletzt)'}`}; },
    hints: ['\\(\\partial\\overleftarrow h_1/\\partial \\overleftarrow h_2=(1-\\overleftarrow h_1^2)w_h\\). Wann ist der erste Faktor fast 0?', 'Ein großer Bias treibt alle Zustände in die Sättigung.'],
    success: 'Gesättigte tanh-Einheiten leiten nichts weiter: \\(1-h^2\\approx0\\). Starke Rückkopplung allein garantiert keinen Informationsfluss – ein Gegenbeispiel zur naiven Lesart „großes \\(w_h\\) = langes Gedächtnis“.', links: {book: 'birnn'}},
];

// =====================================================================================
// Lab 4: Spannen & Evaluation – BIO/BILOU, exakter Spannenvergleich, Token vs. Spanne, Micro/Macro
// =====================================================================================
const SP_WORDS = ['Angela', 'Merkel', 'besuchte', 'am', 'Montag', 'Paris', 'und', 'die', 'Vereinten', 'Nationen'];
const SP_GOLD = ['B-PER', 'I-PER', 'O', 'O', 'O', 'B-LOC', 'O', 'O', 'B-ORG', 'I-ORG'];
const SP_CYCLE = ['O', 'B-PER', 'I-PER', 'B-LOC', 'I-LOC', 'B-ORG', 'I-ORG'];
const SP_TYPES = ['PER', 'LOC', 'ORG'];
const TYPEC = {PER: 'var(--t0)', LOC: 'var(--t2)', ORG: 'var(--t3)'};
function spInit() { return {words: SP_WORDS.slice(), gold: SP_GOLD.slice(), pred: ['B-PER', 'I-PER', 'O', 'O', 'O', 'B-LOC', 'O', 'O', 'B-ORG', 'O'], edit: 'pred', level: 'span'}; }
const spanLab = registerLab({
  id: 'spans', title: 'Spannen & F1', icon: 'F',
  intro: 'Klicken Sie Wörter an, um Labels der <b>Vorhersage</b> (oder des Golds) zu ändern. Spannen werden wie von <code>conlleval</code> gelesen und nur bei <em>exakter</em> Übereinstimmung von Grenzen und Typ gezählt. Vergleichen Sie Spannen- mit Token-Zählung und Micro- mit Macro-Mittelung.',
  init: spInit,
  compute(S) {
    const G = M.spans(S.gold), P = M.spans(S.pred), gk = new Set(G.map(M.spanKey)), pk = new Set(P.map(M.spanKey));
    const span = M.microMacro(S.gold, S.pred, SP_TYPES, 'span'), tok = M.microMacro(S.gold, S.pred, SP_TYPES, 'token');
    const enc = ['IO', 'BIO', 'BILOU'].map(sc => { const e = M.encode(G, S.gold.length, sc), back = M.spans(e); return {sc, e, ok: JSON.stringify(back.map(M.spanKey)) === JSON.stringify(G.map(M.spanKey))}; });
    return {G, P, gk, pk, span, tok, enc};
  },
  quantities(S, R) { return [{id: 'sf', label: 'Spannen-F1 (micro)', value: R.span.micro.F ?? NaN}, {id: 'tf', label: 'Token-F1 (micro)', value: R.tok.micro.F ?? NaN}, {id: 'sp', label: 'Spannen-Präzision', value: R.span.micro.P ?? NaN}, {id: 'sr', label: 'Spannen-Recall', value: R.span.micro.R ?? NaN}, {id: 'ma', label: 'Spannen-F1 (macro)', value: R.span.macro ?? NaN}]; },
  explain(Sb, Rb, Sa, Ra) {
    const a = Rb.span.micro, b = Ra.span.micro;
    const out = [`Spannen-Zählung: TP ${a.tp}→${b.tp}, FP ${a.fp}→${b.fp}, FN ${a.fn}→${b.fn}.`];
    if (b.fp > a.fp && b.fn > a.fn && b.tp < a.tp) out.push('Eine ehemals richtige Spanne ist jetzt falsch begrenzt oder typisiert: Das kostet <em>doppelt</em> – sie zählt als FP (die neue, falsche Spanne) und als FN (die verfehlte Gold-Spanne).');
    out.push('\\(F_1=\\frac{2\\,\\mathrm{TP}}{2\\,\\mathrm{TP}+\\mathrm{FP}+\\mathrm{FN}}\\): ' + `${f(a.F, 3)} → ${f(b.F, 3)}.`);
    const ta = Rb.tok.micro, tb = Ra.tok.micro;
    out.push(`Token-Zählung zum Vergleich: ${f(ta.F, 3)} → ${f(tb.F, 3)} – Teiltreffer werden dort teilweise belohnt.`);
    return out.join(' ');
  },
  view(root, api) {
    const ctl = h('div', {class: 'row'}), sent = h('div', {class: 'plane', style: 'padding:8px 10px'}), stats = h('div', {class: 'planes'}), fl = h('div', {class: 'formula-live'}), enc = h('div', {});
    root.append(ctl, sent, fl, stats, enc);
    return function update(S, R) {
      ctl.replaceChildren(seg([['pred', 'Vorhersage bearbeiten'], ['gold', 'Gold bearbeiten']], S.edit, v => api.set({edit: v}), 'Bearbeitungsmodus'),
        h('button', {onclick: () => api.set(st => { st.pred = st.gold.slice(); return st; })}, 'Vorhersage = Gold'), h('button', {onclick: () => api.set(st => { st.pred = st.pred.map(() => 'O'); return st; })}, 'Alles O'), h('button', {onclick: () => api.reset()}, 'Zurücksetzen'));
      const n = S.words.length, W = 760, cw = W / n;
      const svg = s('svg', {viewBox: `0 0 ${W} 150`, role: 'img', 'aria-label': 'Gold- und Systemspannen über dem Satz'});
      const bar = (sp, y, kind) => { const ok = kind === 'gold' ? R.pk.has(M.spanKey(sp)) : R.gk.has(M.spanKey(sp));
        return s('g', {}, s('rect', {x: sp.start * cw + 4, y, width: (sp.end - sp.start + 1) * cw - 8, height: 14, rx: 6, fill: TYPEC[sp.type], opacity: ok ? .9 : .35, stroke: ok ? 'var(--ok)' : 'var(--bad)', 'stroke-width': 2, 'stroke-dasharray': ok ? null : '4 3'}),
          s('text', {x: sp.start * cw + 10, y: y + 11, 'font-size': 10, 'font-weight': 700, fill: ok ? '#fff' : 'var(--ink)'}, sp.type + (ok ? ' ✓' : kind === 'gold' ? ' FN' : ' FP'))); };
      svg.append(s('text', {x: 2, y: 12, 'font-size': 11, fill: 'var(--mute)'}, 'Gold'));
      R.G.forEach(sp => svg.append(bar(sp, 16, 'gold')));
      S.words.forEach((w, i) => svg.append(s('text', {x: i * cw + cw / 2, y: 62, 'text-anchor': 'middle', 'font-size': 13, 'font-weight': 600, fill: 'var(--ink)'}, w),
        s('text', {x: i * cw + cw / 2, y: 80, 'text-anchor': 'middle', 'font-size': 10, fill: 'var(--mute)', 'font-family': 'monospace'}, S.gold[i]),
        s('text', {x: i * cw + cw / 2, y: 96, 'text-anchor': 'middle', 'font-size': 10, fill: S.pred[i] === S.gold[i] ? 'var(--ok)' : 'var(--bad)', 'font-family': 'monospace', 'font-weight': 700}, S.pred[i])));
      svg.append(s('text', {x: 2, y: 116, 'font-size': 11, fill: 'var(--mute)'}, 'System'));
      R.P.forEach(sp => svg.append(bar(sp, 120, 'pred')));
      const btns = h('div', {class: 'seqrow'}, S.words.map((w, i) => { const cur = S[S.edit][i];
        return h('button', {class: 'tk', 'aria-label': `${w}: ${S.edit === 'pred' ? 'Vorhersage' : 'Gold'} ${cur}. Klicken für nächstes Label.`, onclick: () => api.set(st => { const a = st[st.edit]; a[i] = SP_CYCLE[(SP_CYCLE.indexOf(a[i]) + 1) % SP_CYCLE.length]; return st; })}, w, h('small', {}, cur)); }));
      sent.replaceChildren(svg, h('p', {class: 'note', style: 'margin:4px 0'}, `Klick auf ein Wort: nächstes ${S.edit === 'pred' ? 'Vorhersage' : 'Gold'}-Label (O → B-PER → I-PER → B-LOC → I-LOC → B-ORG → I-ORG).`), btns);
      const m = R.span.micro;
      fl.innerHTML = `Spannen (micro): P = ${m.tp}/(${m.tp}+${m.fp}) = ${f(m.P, 3)}, R = ${m.tp}/(${m.tp}+${m.fn}) = ${f(m.R, 3)}, F₁ = 2·${m.tp}/(2·${m.tp}+${m.fp}+${m.fn}) = <b>${f(m.F, 3)}</b>`;
      const table = (title, mm) => h('div', {}, h('h3', {style: 'font-size:14px;margin:6px 0'}, title), h('table', {class: 'calc'}, h('tr', {}, ['Typ', 'TP', 'FP', 'FN', 'P', 'R', 'F₁', 'Gewicht 2TP+FP+FN'].map(x => h('th', {}, x))),
        mm.per.map(r => h('tr', {}, h('td', {}, h('span', {class: 'chip', style: `--c:${TYPEC[r.type]}`}, r.type)), h('td', {}, r.tp), h('td', {}, r.fp), h('td', {}, r.fn), h('td', {}, f(r.P, 2)), h('td', {}, f(r.R, 2)), h('td', {}, f(r.F, 3)), h('td', {}, 2 * r.tp + r.fp + r.fn))),
        h('tr', {class: 'sum'}, h('td', {}, 'Micro'), h('td', {}, mm.micro.tp), h('td', {}, mm.micro.fp), h('td', {}, mm.micro.fn), h('td', {}, f(mm.micro.P, 2)), h('td', {}, f(mm.micro.R, 2)), h('td', {}, f(mm.micro.F, 3)), h('td', {})),
        h('tr', {}, h('td', {}, 'Macro'), h('td', {colspan: 5, class: 'note', style: 'text-align:left'}, 'Mittel der definierten F₁-Werte'), h('td', {}, f(mm.macro, 3)), h('td', {}))));
      stats.replaceChildren(h('div', {class: 'calc-wrap'}, table('Spannen-Zählung (conlleval)', R.span)), h('div', {class: 'calc-wrap'}, table('Token-Zählung', R.tok)));
      enc.replaceChildren(h('h3', {style: 'font-size:14px;margin:10px 0 4px'}, 'Gold-Spannen in drei Kodierungen – und zurückgelesen'),
        ...R.enc.map(e => h('div', {class: 'row', style: 'margin:2px 0'}, h('b', {style: 'width:60px'}, e.sc), h('code', {style: 'white-space:normal'}, e.e.join(' ')), h('span', {class: 'badge ' + (e.ok ? 'ok' : 'bad')}, e.ok ? 'umkehrbar' : 'Information verloren'))));
    };
  },
});
spanLab.path = [
  {id: 's1', title: 'Fast richtig ist falsch', story: 'Gold: [Angela Merkel]PER. Das System erkennt nur [Angela]PER.',
    setup: () => { const n = spInit(); n.pred = SP_GOLD.slice(); return n; },
    predict: {q: 'Sie ändern „Merkel“ in der Vorhersage zu O. Wie ändern sich die Spannen-Zählwerte für PER?', options: ['TP −1, FP +1, FN +1', 'TP −1, FN +1', 'nichts – der Anfang stimmt'], correct: 0},
    task: 'Setzen Sie in der Vorhersage „Merkel“ auf O.', goal: S => S.pred[0] === 'B-PER' && S.pred[1] === 'O',
    reveal: 'Spannen zählen nur bei exakt gleichen Grenzen und Typ. [Angela]PER ist eine <em>falsche</em> Spanne (FP), und [Angela Merkel]PER wurde verfehlt (FN). Ein Grenzfehler kostet also doppelt.', links: {book: 'prf', bookLabel: '§10', tasks: ['S1']}},
  {id: 's2', title: 'Token-Zählung ist großzügiger', story: 'Wie viel F₁ „verdient“ ein System, das jede Spanne nur halb trifft?',
    setup: () => { const n = spInit(); n.pred = SP_GOLD.slice(); return n; },
    task: 'Erzeugen Sie eine Vorhersage, bei der Token-F₁ mindestens 0,3 über Spannen-F₁ liegt.', goal: (S, R) => (R.tok.micro.F ?? 0) - (R.span.micro.F ?? 0) >= .3,
    reveal: 'Die Zähleinheit verändert die Kennzahl erheblich – und kann Rangfolgen zwischen Systemen umdrehen. CoNLL-Auswertung zählt Spannen; Token-F₁ überschätzt Systeme mit Grenzfehlern.', links: {book: 'prf-level', bookLabel: '§11'}},
  {id: 's3', title: 'Wenn nichts da ist', story: 'Ein System, das gar nichts vorhersagt.',
    setup: () => spInit(),
    predict: {q: 'Alles O: Was ist die Präzision?', options: ['undefiniert (0/0)', '0', '1'], correct: 0},
    task: 'Setzen Sie die Vorhersage auf „Alles O“.', goal: S => S.pred.every(x => x === 'O'),
    reveal: 'Ohne Systemspannen ist \\(P=0/0\\) undefiniert, \\(R=0\\), und \\(F_1=2\\cdot0/(0+0+\\mathrm{FN})=0\\) ist trotzdem definiert, weil Gold-Spannen existieren. Die Zählform \\(F_1=2\\mathrm{TP}/(2\\mathrm{TP}+\\mathrm{FP}+\\mathrm{FN})\\) ist nur undefiniert, wenn es weder Gold- noch Systemspannen gibt.', links: {book: 'prf-edge', bookLabel: '§10'}},
  {id: 's4', title: 'Micro gegen Macro', story: 'Micro summiert die Zählwerte aller Typen, Macro mittelt die F₁-Werte der Typen.',
    setup: () => { const n = spInit(); n.pred = SP_GOLD.slice(); return n; },
    task: 'Erzeugen Sie \\(|\\text{Micro}-\\text{Macro}|\\ge0{,}2\\) bei Spannen-Zählung.', goal: (S, R) => R.span.macro !== null && R.span.micro.F !== null && Math.abs(R.span.micro.F - R.span.macro) >= .2,
    reveal: 'Micro-\\(F_1\\) ist ein gewichtetes Mittel der Typ-\\(F_1\\) mit Gewichten \\(2\\mathrm{TP}_k+\\mathrm{FP}_k+\\mathrm{FN}_k\\) (letzte Tabellenspalte) – häufige Typen dominieren. Macro gibt jedem Typ gleiches Gewicht und bestraft Fehler bei seltenen Typen stärker.', links: {book: 'micro-macro', bookLabel: '§12'}},
  {id: 's5', title: 'IO verliert Grenzen', story: 'Bearbeiten Sie jetzt das <b>Gold</b>.',
    setup: S => { S.edit = 'gold'; return S; },
    task: 'Ändern Sie das Gold so, dass die IO-Kodierung nicht mehr umkehrbar ist.', goal: (S, R) => !R.enc[0].ok,
    reveal: '<b>Satz A:</b> BIO ist auf gültigen Folgen umkehrbar, IO nicht: Zwei <em>benachbarte</em> Spannen gleichen Typs werden in IO zu einer. BILOU markiert zusätzlich Ende und Einzel-Token-Spannen.', links: {book: 'spans', bookLabel: '§2, Satz A', tasks: ['S1']}},
];
spanLab.challenges = [
  {id: 'f-half', title: 'Halbe Treffer', level: 'mittel', goal: 'Spannen-F₁ = 0, aber Token-F₁ ≥ 0,6.', setup: () => { const n = spInit(); n.pred = SP_GOLD.slice(); return n; },
    check: (S, R) => { const sf = R.span.micro.F ?? 0, tf = R.tok.micro.F ?? 0; return {done: sf === 0 && tf >= .6, progress: (sf === 0 ? .5 : 0) + Math.min(.5, tf / 1.2), msg: `Spannen-F₁ ${f(sf, 3)}, Token-F₁ ${f(tf, 3)}`}; },
    hints: ['Jede Gold-Spanne muss verfehlt werden, aber möglichst viele Tokens sollen den richtigen Typ behalten.', 'Bei einer Ein-Wort-Spanne (Paris) gibt es keinen „halben“ Treffer – die müssen Sie opfern oder falsch typisieren?', 'Verschieben Sie Grenzen: [Angela]PER [Merkel]PER statt [Angela Merkel]PER.'],
    success: 'Zwei Spannen statt einer (B-PER B-PER) behalten alle Token-Typen, treffen aber keine Gold-Spanne. Deshalb meldet man für NER Spannen-F₁.', links: {book: 'prf-level'}},
  {id: 'f-prec', title: 'Präzise, aber blind', level: 'leicht', goal: 'P = 1 und R ≤ 0,4 (Spannen).', setup: () => { const n = spInit(); n.pred = SP_GOLD.slice(); return n; },
    check: (S, R) => { const m = R.span.micro; return {done: m.P === 1 && m.R !== null && m.R <= .4, progress: (m.P === 1 ? .5 : 0) + (m.R !== null && m.R <= .4 ? .5 : 0), msg: `P = ${f(m.P, 2)}, R = ${f(m.R, 2)}`}; },
    hints: ['Präzision bestraft nur falsche Vorhersagen, nicht fehlende.'], success: 'Ein vorsichtiges System sagt wenig, aber richtig: hohe Präzision, niedriger Recall. \\(F_1\\) als harmonisches Mittel wird vom kleineren Wert dominiert.', links: {book: 'prf'}},
  {id: 'f-macro', title: 'Seltenes zählt', level: 'mittel', goal: 'Micro-F₁ ≥ 0,7, Macro-F₁ ≤ 0,55 (Spannen).', setup: () => { const n = spInit(); n.pred = SP_GOLD.slice(); return n; },
    check: (S, R) => { const mi = R.span.micro.F ?? 0, ma = R.span.macro ?? 1; return {done: mi >= .7 && ma <= .55, progress: Math.min(1, (mi >= .7 ? .5 : mi / 1.4) + (ma <= .55 ? .5 : 0)), msg: `Micro ${f(mi, 3)}, Macro ${f(ma, 3)}`}; },
    hints: ['Mit nur drei Gold-Spannen ist das schwer. Bearbeiten Sie auch das Gold: mehr PER-Spannen machen PER zum „häufigen“ Typ.', 'Fehler bei einem Typ mit wenig Gewicht senken Macro stark, Micro kaum.'],
    success: 'Häufige Typen dominieren Micro-F₁. Macro-F₁ deckt auf, dass ein seltener Typ schlecht erkannt wird – wichtig, wenn gerade seltene Entitäten (z. B. Krankheiten) zählen.', links: {book: 'micro-macro'}},
];
