'use strict';
// =====================================================================================
// Lab 1: Self-Attention
// =====================================================================================
const TOKC = ['var(--t0)', 'var(--t1)', 'var(--t2)', 'var(--t3)', 'var(--t4)'];
const ATT_PRESETS = {
  bank: {title: '„Bank“ im Satz „Wir sitzen auf der Bank am Fluss“', q: [0.9, -0.6], names: ['Fluss', 'Geld', 'der'],
    K: [[1.6, 0.4], [-0.4, 1.5], [0.1, -0.3]], V: [[1.8, 0.2], [0.1, 1.9], [0.2, 0.2]]},
  tie: {title: 'Zwei gleich gute Schlüssel', q: [1, 1], names: ['A', 'B', 'C'], K: [[2, 0], [0, 2], [-1, -1]], V: [[2, 0], [0, 2], [-1, -1]]},
  line: {title: 'Schlüssel auf einer Geraden', q: [1, 0], names: ['A', 'B', 'C'], K: [[-1, 1], [0, 0.5], [1, 0]], V: [[-1.5, 1], [0, 1.5], [1.5, -0.5]]},
};
function attInit(p = 'bank') { const P = ATT_PRESETS[p]; return {view: 'one', preset: p, q: P.q.slice(), K: clone(P.K), V: clone(P.V), names: P.names.slice(), T: 1, scaled: true, target: null, shift: [0, 0],
  sent: {words: ['Mia', 'sieht', 'Tom', 'heute'], X: [[1, 0.2], [-0.3, 1], [0.9, -0.4], [-0.8, -0.6]], order: [0, 1, 2, 3], WQ: [[1, 0.5], [-0.5, 1]], WK: [[1, 0], [0.4, 1]], WV: [[1, 0], [0, 1]], pe: false, peA: 1, causal: false, focus: 2},
  dim: {d: 64, scaledOn: false}}; }
const DIMS = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512];
const SCALE_CACHE = {};
function scaleExp(d) { return SCALE_CACHE[d] || (SCALE_CACHE[d] = M.scalingExperiment(d, 8, 300, 11)); }

const attention = registerLab({
  id: 'attention', title: 'Self-Attention', icon: 'α',
  intro: 'Ein Wort sucht im Satz nach passender Information: Seine <b>Query</b> wird mit allen <b>Keys</b> verglichen, die Softmax macht daraus Gewichte, und die Ausgabe ist die gewichtete Mischung der <b>Values</b>. Ziehen Sie Pfeile, ändern Sie Zahlen, Skalierung und Temperatur – alle Werte, Formeln und Bilder werden sofort neu berechnet.',
  init: () => attInit(),
  structural: (a, b) => a.view !== b.view || a.K.length !== b.K.length || a.preset !== b.preset || a.sent.order.join() !== b.sent.order.join(),
  compute(S) {
    const c = S.scaled ? Math.SQRT2 : 1;
    const K = S.K.map(k => M.add(k, S.shift));
    const one = M.attendOne(S.q, K, S.V, {scaleBy: c, T: S.T});
    const W = S.sent, X = W.order.map(i => W.X[i]);
    const P = W.pe ? M.sinusPE(X.length, 2).map(p => M.scale(p, W.peA)) : null;
    const opts = {T: S.T, scale: S.scaled, causal: W.causal, P};
    const sent = M.selfAttention(X, W.WQ, W.WK, W.WV, opts);
    const base = M.selfAttention(W.X, W.WQ, W.WK, W.WV, {...opts, P: W.pe ? M.sinusPE(W.X.length, 2).map(p => M.scale(p, W.peA)) : null});
    // Äquivarianz-Test: Ausgabe jedes Wortes jetzt vs. in Originalreihenfolge
    const equiv = W.order.map((wi, pos) => ({word: W.words[wi], pos, now: sent.O[pos], orig: base.O[wi], dist: M.norm(M.sub(sent.O[pos], base.O[wi]))}));
    return {c, K, one, sent, base, equiv, dim: scaleExp(S.dim.d)};
  },
  quantities(S, R) {
    if (S.view === 'one') return [...S.names.map((n, j) => ({id: 'w' + j, label: `Gewicht w(${n})`, value: R.one.w[j]})), ...S.names.map((n, j) => ({id: 's' + j, label: `Score q·k(${n})`, value: R.one.raw[j]})),
      {id: 'H', label: 'Entropie H (Bit)', value: R.one.H}, {id: 'o1', label: 'Ausgabe o₁', value: R.one.out[0]}, {id: 'o2', label: 'Ausgabe o₂', value: R.one.out[1]}, {id: 'J', label: 'Gradientenstärke ‖J‖', value: R.one.J}];
    if (S.view === 'sent') return S.sent.words.map((w, i) => { const p = S.sent.order.indexOf(i); return {id: 'eq' + i, label: `Abweichung der Ausgabe von „${w}“ zur Originalreihenfolge`, value: R.equiv[p].dist}; })
      .concat(S.sent.words.map((w, i) => { const p = S.sent.order.indexOf(i); return {id: 'o' + i, label: `Ausgabe von „${w}“, 1. Komponente`, value: R.sent.O[p][0]}; }));
    return [{id: 'mr', label: 'mittl. max. Gewicht ohne Skalierung', value: R.dim.raw.maxw}, {id: 'ms', label: 'mittl. max. Gewicht mit Skalierung', value: R.dim.scaled.maxw}, {id: 'var', label: 'Varianz von q·k', value: R.dim.varRaw}, {id: 'Jr', label: 'Gradientenstärke ohne Skalierung', value: R.dim.raw.J}];
  },
  explain(Sb, Rb, Sa, Ra) {
    const out = [];
    if (Sb.view !== Sa.view) return 'Sie haben die Ansicht gewechselt; vergleichen Sie Größen innerhalb einer Ansicht.';
    if (Sa.view === 'one') {
      const ds = Ra.one.scaled.map((x, j) => x - Rb.one.scaled[j]);
      const qch = M.norm(M.sub(Sa.q, Sb.q)) > 1e-9, Tch = Sa.T !== Sb.T, sc = Sa.scaled !== Sb.scaled;
      const kch = Sa.K.map((k, j) => M.norm(M.sub(M.add(k, Sa.shift), M.add(Sb.K[j], Sb.shift))) > 1e-9), vch = Sa.V.map((v, j) => M.norm(M.sub(v, Sb.V[j])) > 1e-9);
      const changed = [qch && 'die Query q', kch.some(Boolean) && 'Keys (' + Sa.names.filter((_, j) => kch[j]).join(', ') + ')', vch.some(Boolean) && 'Values (' + Sa.names.filter((_, j) => vch[j]).join(', ') + ')', Tch && `die Temperatur (${f(Sb.T)} → ${f(Sa.T)})`, sc && 'die Skalierung'].filter(Boolean);
      out.push(`Geändert haben Sie ${changed.length ? changed.join(', ') : 'nichts'}.`);
      if (!qch && !kch.some(Boolean) && !Tch && !sc && vch.some(Boolean)) out.push('Values gehen nicht in die Gewichte ein: \\(w_j\\) hängt nur von \\(q\\), den Keys, der Skalierung und \\(T\\) ab. Deshalb ändert sich nur die Ausgabe \\(o=\\sum_j w_jv_j\\) – sie verschiebt sich um \\(\\sum_j w_j\\,\\Delta v_j\\).');
      const spread = Math.max(...ds) - Math.min(...ds);
      if (!Tch && !sc && Math.max(...ds.map(Math.abs)) > 1e-9 && spread < 1e-9) out.push(`Alle skalierten Scores haben sich um denselben Betrag ${f(ds[0])} verschoben. Die Softmax hängt nur von Differenzen \\(s_j-s_l\\) ab, deshalb bleiben alle Gewichte gleich.`);
      else if (Math.max(...ds.map(Math.abs)) > 1e-9) out.push('Skalierte Scores: ' + Sa.names.map((n, j) => `${n} ${ds[j] >= 0 ? '+' : ''}${f(ds[j])}`).join(', ') + '. Ein Gewicht steigt, wenn sein Score <em>relativ zu den anderen</em> steigt: \\(\\partial w_j/\\partial s_l = (w_j[j{=}l]-w_jw_l)/T\\).');
      if (Tch) out.push(Sa.T < Sb.T ? 'Kleinere Temperatur teilt die Scores durch eine kleinere Zahl: Abstände werden größer, die Verteilung wird spitzer (Entropie sinkt), im Grenzfall \\(T\\to0\\) entsteht \\(\\arg\\max\\).' : 'Größere Temperatur staucht die Abstände der Scores: die Verteilung wird flacher, im Grenzfall \\(T\\to\\infty\\) gleichverteilt.');
      if (qch) { const lb = M.norm(Sb.q), la = M.norm(Sa.q); const cos = lb && la ? M.dot(Sa.q, Sb.q) / (lb * la) : 0; if (Math.abs(cos - 1) < 1e-6 && lb > 0) out.push(`q hat nur die Länge geändert (Faktor ${f(la / lb)}). Das wirkt exakt wie die Temperatur \\(T/${f(la / lb)}\\): \\((\\lambda q)^\\top k_j = \\lambda\\,q^\\top k_j\\).`); }
      out.push(`Entropie ${f(Rb.one.H)} → ${f(Ra.one.H)} Bit (Maximum ${f(Ra.one.Hmax)}).`);
    } else if (Sa.view === 'sent') {
      const perm = Sa.sent.order.join() !== Sb.sent.order.join();
      if (perm) out.push(Sa.sent.pe ? 'Sie haben die Reihenfolge geändert, und Positionsvektoren sind aktiv: Jedes Wort erhält an seiner neuen Position einen anderen Vektor \\(p_t\\), also ändern sich \\(q,k,v\\) – die Ausgaben sind nicht mehr bloß vertauscht.' : 'Sie haben die Reihenfolge geändert, ohne Positionsvektoren. Jedes Wort hat dieselben \\(q,k,v\\) wie vorher, nur in anderen Zeilen; da Softmax und Summe nicht auf die Zeilennummer schauen, erhält jedes Wort exakt dieselbe Ausgabe (Satz 4: \\(\\mathrm{Att}(PX)=P\\,\\mathrm{Att}(X)\\)).');
      if (Sa.sent.pe !== Sb.sent.pe) out.push(Sa.sent.pe ? 'Positionsvektoren hinzugefügt: \\(x_t+p_t\\) hängt jetzt von der Position ab.' : 'Positionsvektoren entfernt.');
      if (Sa.sent.causal !== Sb.sent.causal) out.push(Sa.sent.causal ? 'Kausale Maske: Wort \\(t\\) darf nur \\(1,\\dots,t\\) sehen; die Softmax normiert nur über diese Spalten. Damit wird auch ohne Positionsvektoren die Reihenfolge sichtbar – über die Maske.' : 'Maske entfernt.');
      if (!out.length) out.push('Einbettungen oder Gewichtsmatrizen geändert: \\(Q,K,V\\) und damit alle Scores ändern sich mit.');
    } else {
      out.push(`Bei \\(d=${Sa.dim.d}\\) misst das Experiment Varianz ${f(Ra.dim.varRaw)} für \\(q^\\top k\\) (Satz 3: \\(d\\)). Ohne Skalierung sind die Scores typischerweise \\(\\sqrt d\\)-mal größer, die Softmax wird spitzer und \\(\\lVert J\\rVert\\) kleiner.`);
    }
    return out.join(' ');
  },
  view(root, api) {
    const S0 = api.S;
    const head = h('div', {class: 'row'}, seg([['one', 'Eine Query'], ['sent', 'Ganzer Satz'], ['dim', 'Skalierung & Dimension']], S0.view, v => api.set({view: v}), 'Ansicht'));
    root.append(head);
    if (S0.view === 'one') return attOne(root, api);
    if (S0.view === 'sent') return attSent(root, api);
    return attDim(root, api);
  },
});

function tempControl(api, S) {
  const slider = h('input', {type: 'range', min: -3, max: 2.3, step: 0.01, value: Math.log(S.T), 'aria-label': 'Temperatur T (logarithmisch)'});
  const lab = h('b', {}, f(S.T));
  slider.addEventListener('input', () => api.set({T: Math.round(Math.exp(+slider.value) * 100) / 100 || 0.05}));
  return {el: h('label', {class: 'ctl'}, 'Temperatur T ', slider, lab), update(S) { slider.value = Math.log(S.T); lab.textContent = f(S.T); }};
}

function attOne(root, api) {
  const S0 = api.S;
  const presets = h('select', {'aria-label': 'Beispiel'}, Object.entries(ATT_PRESETS).map(([k, p]) => h('option', {value: k, selected: k === S0.preset || null}, p.title)));
  presets.addEventListener('change', () => api.set(st => { const n = attInit(presets.value); n.view = 'one'; n.T = st.T; n.scaled = st.scaled; return n; }));
  const temp = tempControl(api, S0);
  const scaleBox = h('input', {type: 'checkbox', checked: S0.scaled || null});
  scaleBox.addEventListener('change', () => api.set({scaled: scaleBox.checked}));
  const nbtn = h('span', {class: 'row', style: 'margin:0'},
    h('button', {onclick: () => api.set(st => { if (st.K.length >= 5) return st; const j = st.K.length; st.K.push([-1.2 + .3 * j, -1.5]); st.V.push([-1, -1 + .4 * j]); st.names.push('Wort ' + (j + 1)); return st; })}, '+ Token'),
    h('button', {onclick: () => api.set(st => { if (st.K.length <= 2) return st; st.K.pop(); st.V.pop(); st.names.pop(); return st; })}, '− Token'));
  root.append(h('div', {class: 'row'}, presets, nbtn), h('div', {class: 'row'}, temp.el, h('label', {class: 'ctl'}, scaleBox, 'durch \u221Ad\u2096 = \u221A2 teilen'), h('button', {onclick: () => api.reset()}, 'Zurücksetzen')));
  const L = Plane({title: 'Schlüsselraum: Query und Keys', axes: ['Merkmal 1', 'Merkmal 2']}), Rt = Plane({title: 'Werteraum: Values und Ausgabe o', axes: ['Ufer-Bedeutung', 'Finanz-Bedeutung']});
  const fl = h('div', {class: 'formula-live', 'aria-live': 'off'});
  const meters = h('div', {class: 'meters'});
  const tbl = h('table', {class: 'calc'}); const tw = h('div', {class: 'calc-wrap'}, tbl);
  const nums = h('details', {class: 'numbers'}, h('summary', {}, 'Alle Vektoren als Zahlen eingeben'), h('div', {class: 'numgrid'}));
  const stageEl = h('div', {}, h('div', {class: 'planes'}, L.root, Rt.root), fl, meters, tw, nums,
    h('p', {class: 'note'}, 'Tastatur: Tab wählt einen Pfeil, Pfeiltasten verschieben ihn (Umschalt = größere Schritte). Der lila Griff ◆ im Schwerpunkt der Keys verschiebt alle Keys gemeinsam. Der Link in der Adresszeile speichert den exakten Zustand.'));
  root.append(stageEl);
  const setHL = j => { if (j == null) stageEl.removeAttribute('data-hl'); else stageEl.setAttribute('data-hl', j); stageEl.querySelectorAll('.dimmable').forEach(n => n.classList.toggle('hl', n.dataset.j === String(j) || n.dataset.j === 'all')); };
  return function update(S, R) {
    temp.update(S); scaleBox.checked = S.scaled;
    const o = R.one, n = S.K.length, K = R.K;
    // --- Schlüsselraum ---
    const c = L.content; c.replaceChildren();
    const qn = M.norm(S.q);
    if (qn > 0) { const u = M.scale(S.q, 1 / qn); c.append(s('line', {x1: L.X(-u[0] * 5), y1: L.Y(-u[1] * 5), x2: L.X(u[0] * 5), y2: L.Y(u[1] * 5), stroke: 'var(--q)', 'stroke-width': 1, opacity: .25, 'stroke-dasharray': '2 4'})); }
    K.forEach((k, j) => {
      const g = s('g', {class: 'dimmable', 'data-j': j});
      if (o.proj[j].defined) { const p = o.proj[j].vec; g.append(s('line', {x1: L.X(k[0]), y1: L.Y(k[1]), x2: L.X(p[0]), y2: L.Y(p[1]), stroke: TOKC[j], 'stroke-dasharray': '3 3', 'stroke-width': 1.3}),
        s('circle', {cx: L.X(p[0]), cy: L.Y(p[1]), r: 3.2, fill: TOKC[j]})); }
      g.append(L.arrow([0, 0], k, TOKC[j], 2.5));
      c.append(g);
    });
    
    c.append(L.arrow([0, 0], S.q, 'var(--q)', 3.5));
    const ids = ['q', 'shift'];
    L.handle('q', {get: () => S.q, set: v => api.set({q: v}), color: 'var(--q)', label: 'q', aria: 'Query q'});
    K.forEach((k, j) => { ids.push('k' + j); L.handle('k' + j, {get: () => K[j], set: v => api.set(st => { st.K[j] = M.sub(v, st.shift); return st; }), color: TOKC[j], label: 'k' + sub[j + 1] + ' ' + S.names[j], aria: `Key von ${S.names[j]}`}); });
    const cen = M.scale(K.reduce((a, k) => M.add(a, k), [0, 0]), 1 / K.length);
    c.append(s('g', {opacity: .5}, ...K.map(k => s('line', {x1: L.X(cen[0]), y1: L.Y(cen[1]), x2: L.X(k[0]), y2: L.Y(k[1]), stroke: 'var(--t3)', 'stroke-width': 1, 'stroke-dasharray': '1 3'}))));
    L.handle('shift', {get: () => cen, set: v => api.set(st => { st.shift = M.add(st.shift, M.sub(v, cen)).map(x => Math.round(x * 100) / 100); return st; }), color: 'var(--t3)', label: '◆ alle', aria: 'Schwerpunkt aller Keys – verschiebt alle Keys gemeinsam'});
    L.svg.querySelector('[data-id=shift] .dot').setAttribute('r', 4);
    L.only(ids);
    { const qh = L.svg.querySelector('g.handle[data-id=q]'), par = qh.parentNode;  // q immer zuoberst (ohne Fokusverlust)
      if (par.lastChild !== qh && !par.contains(document.activeElement)) par.appendChild(qh); }
    // --- Werteraum ---
    const d = Rt.content; d.replaceChildren();
    if (n >= 3) { const hull = convexHull(S.V); d.append(s('polygon', {points: hull.map(p => `${Rt.X(p[0])},${Rt.Y(p[1])}`).join(' '), fill: 'var(--hull)', stroke: 'var(--accent)', 'stroke-opacity': .3})); }
    else d.append(s('line', {x1: Rt.X(S.V[0][0]), y1: Rt.Y(S.V[0][1]), x2: Rt.X(S.V[1][0]), y2: Rt.Y(S.V[1][1]), stroke: 'var(--accent)', 'stroke-opacity': .35, 'stroke-width': 6}));
    S.V.forEach((v, j) => d.append(s('g', {class: 'dimmable', 'data-j': j}, Rt.arrow([0, 0], v, TOKC[j], 1.6, '', '5 4'))));
    let acc = [0, 0];  // Kette w_j v_j Spitze an Fuß
    o.contrib.forEach((cv, j) => { const nx = M.add(acc, cv); d.append(s('g', {class: 'dimmable', 'data-j': j}, Rt.arrow(acc, nx, TOKC[j], 3))); acc = nx; });
    if (S.target) d.append(s('g', {}, s('circle', {cx: Rt.X(S.target[0]), cy: Rt.Y(S.target[1]), r: 8, fill: 'none', stroke: 'var(--bad)', 'stroke-width': 2}), s('text', {x: Rt.X(S.target[0]) + 10, y: Rt.Y(S.target[1]) + 4, class: 'lbl', fill: 'var(--bad)'}, 'Ziel Z')));
    d.append(s('circle', {cx: Rt.X(o.out[0]), cy: Rt.Y(o.out[1]), r: 6.5, fill: 'var(--q)'}), s('text', {x: Rt.X(o.out[0]) + 9, y: Rt.Y(o.out[1]) - 8, class: 'lbl', fill: 'var(--q)'}, 'o'));
    const vids = [];
    S.V.forEach((v, j) => { vids.push('v' + j); Rt.handle('v' + j, {get: () => S.V[j], set: nv => api.set(st => { st.V[j] = nv; return st; }), color: TOKC[j], label: 'v' + sub[j + 1], aria: `Value von ${S.names[j]}`}); });
    Rt.only(vids);
    // --- Formel synchron ---
    const sc = S.scaled ? '\u221A2' : '1';
    fl.replaceChildren(h('span', {}, 'o = '), ...o.w.flatMap((w, j) => [j ? ' + ' : '', h('span', {class: `t tok-${j} dimmable`, 'data-j': j, style: `color:${TOKC[j]}`}, `${f(w, 3)}·v${sub[j + 1]}`)]), ` = (${f(o.out[0])}; ${f(o.out[1])})`,
      h('br'), h('span', {class: 'note'}, `w = softmax(q·k / (${sc}·T)),  T = ${f(S.T)}`));
    // --- Messgrößen ---
    const jmax = o.w.indexOf(Math.max(...o.w));
    meters.replaceChildren(meter('Entropie H', `${f(o.H)} / ${f(o.Hmax)} Bit`, o.H / o.Hmax, 'Wie gleichmäßig ist die Aufmerksamkeit verteilt?'),
      meter('größtes Gewicht', `${f(o.w[jmax], 3)} (${S.names[jmax]})`, o.w[jmax]), meter('‖q‖', f(qn), null), meter('Gradientenstärke ‖J‖', f(o.J, 3), Math.min(1, o.J / 0.6), 'Frobeniusnorm der Softmax-Jacobi-Matrix bzgl. q·k – klein heißt: Lernen stockt'));
    // --- Rechentabelle ---
    tbl.replaceChildren(h('tr', {}, h('th', {}, 'Token j'), h('th', {}, 'q·kⱼ = q₁kⱼ₁ + q₂kⱼ₂'), h('th', {}, '÷ ' + sc + ' ÷ T'), h('th', {}, 'exp(·−max)'), h('th', {}, 'Gewicht wⱼ'), h('th', {}, 'wⱼ·vⱼ')),
      ...K.map((k, j) => {
        const m = Math.max(...o.scaled.map(x => x / S.T));
        const tr = h('tr', {class: `tok-${j} dimmable`, 'data-j': j, tabindex: 0, onmouseenter: () => setHL(j), onmouseleave: () => setHL(null), onfocus: () => setHL(j), onblur: () => setHL(null)},
          h('td', {}, h('span', {class: 'chip'}, S.names[j])),
          h('td', {class: 'expand', html: `(${f(S.q[0])})(${f(k[0])}) + (${f(S.q[1])})(${f(k[1])}) = <b>${f(o.raw[j])}</b>`}),
          h('td', {}, f(o.scaled[j] / S.T)), h('td', {}, f(Math.exp(o.scaled[j] / S.T - m), 3)),
          h('td', {}, h('span', {class: 'wbar', style: `width:${Math.round(o.w[j] * 90)}px`}), f(o.w[j], 3)), h('td', {}, `(${f(o.contrib[j][0])}; ${f(o.contrib[j][1])})`));
        return tr;
      }), h('tr', {class: 'sum'}, h('td', {}, 'Summe'), h('td', {}), h('td', {}), h('td', {}), h('td', {}, f(o.w.reduce((a, b) => a + b, 0), 3)), h('td', {}, `o = (${f(o.out[0])}; ${f(o.out[1])})`)));
    // --- Zahleneingabe (barrierefrei) ---
    const g = nums.querySelector('.numgrid');
    if (!nums.open || g.childElementCount !== 1 + 2 * n) {
      g.replaceChildren(vecInputs('q', () => api.S.q, v => api.set({q: v})), ...S.K.map((k, j) => vecInputs(`k${sub[j + 1]} (${S.names[j]})`, () => api.S.K[j], v => api.set(st => { st.K[j] = v; return st; }))), ...S.V.map((v, j) => vecInputs(`v${sub[j + 1]} (${S.names[j]})`, () => api.S.V[j], nv => api.set(st => { st.V[j] = nv; return st; }))));
    }
  };
}
/** get() liest den aktuellen Vektor zum Zeitpunkt der Eingabe (keine veralteten Werte aus der Closure) */
function vecInputs(label, get, set) { const v = get(); return h('div', {}, h('span', {style: 'min-width:92px'}, label), numInput(v[0], x => set([x, get()[1]]), label + ' Komponente 1'), numInput(v[1], y => set([get()[0], y]), label + ' Komponente 2')); }
function convexHull(P) {
  const p = P.map(x => x.slice()).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const cr = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lo = [], up = [];
  for (const q of p) { while (lo.length >= 2 && cr(lo[lo.length - 2], lo[lo.length - 1], q) <= 0) lo.pop(); lo.push(q); }
  for (const q of p.slice().reverse()) { while (up.length >= 2 && cr(up[up.length - 2], up[up.length - 1], q) <= 0) up.pop(); up.push(q); }
  return lo.slice(0, -1).concat(up.slice(0, -1));
}
/** Abstand eines Punktes zur konvexen Hülle (0 = innen) */
function hullDist(P, z) {
  const H = convexHull(P);
  if (H.length < 3) { const [a, b] = H.length === 2 ? H : [H[0], H[0]]; return segDist(a, b, z); }
  let inside = true; for (let i = 0; i < H.length; i++) { const a = H[i], b = H[(i + 1) % H.length]; if ((b[0] - a[0]) * (z[1] - a[1]) - (b[1] - a[1]) * (z[0] - a[0]) < 0) inside = false; }
  if (inside) return 0;
  return Math.min(...H.map((a, i) => segDist(a, H[(i + 1) % H.length], z)));
}
function segDist(a, b, z) { const ab = M.sub(b, a), L2 = M.dot(ab, ab); const t = L2 ? Math.max(0, Math.min(1, M.dot(M.sub(z, a), ab) / L2)) : 0; return M.norm(M.sub(z, M.add(a, M.scale(ab, t)))); }

function attSent(root, api) {
  const S0 = api.S, W0 = S0.sent;
  const temp = tempControl(api, S0);
  const pe = h('input', {type: 'checkbox', checked: W0.pe || null}), causal = h('input', {type: 'checkbox', checked: W0.causal || null});
  pe.addEventListener('change', () => api.set(st => { st.sent.pe = pe.checked; return st; }));
  causal.addEventListener('change', () => api.set(st => { st.sent.causal = causal.checked; return st; }));
  const peA = h('input', {type: 'range', min: 0, max: 2, step: .05, value: W0.peA, 'aria-label': 'Stärke der Positionsvektoren'});
  peA.addEventListener('input', () => api.set(st => { st.sent.peA = +peA.value; return st; }));
  const orderRow = h('div', {class: 'seqrow', 'aria-label': 'Reihenfolge der Wörter'});
  W0.order.forEach((wi, pos) => orderRow.append(h('div', {class: 'tk'}, h('span', {class: `chip tok-${wi}`}, W0.words[wi]), h('small', {}, 'Position ' + (pos + 1)),
    h('div', {}, h('button', {'aria-label': `${W0.words[wi]} nach links`, disabled: pos === 0 || null, onclick: () => api.set(st => { const o = st.sent.order; [o[pos - 1], o[pos]] = [o[pos], o[pos - 1]]; return st; })}, '←'),
      h('button', {'aria-label': `${W0.words[wi]} nach rechts`, disabled: pos === W0.order.length - 1 || null, onclick: () => api.set(st => { const o = st.sent.order; [o[pos + 1], o[pos]] = [o[pos], o[pos + 1]]; return st; })}, '→')))));
  root.append(h('p', {class: 'note', html: 'Jetzt entstehen \\(q_t=x_tW_Q,\\;k_t=x_tW_K,\\;v_t=x_tW_V\\) aus den Wort-Einbettungen. Vertauschen Sie Wörter und beobachten Sie, ob sich die Ausgabe eines Wortes ändert. Hohle Kreise = Ausgabe desselben Wortes in der Originalreihenfolge.'}),
    orderRow, h('div', {class: 'row'}, temp.el, h('label', {class: 'ctl'}, pe, 'Positionsvektoren \\(p_t\\) addieren'), h('label', {class: 'ctl'}, 'Stärke ', peA), h('label', {class: 'ctl'}, causal, 'kausale Maske'),
      h('button', {onclick: () => api.set(st => { st.sent.order = [0, 1, 2, 3]; return st; })}, 'Originalreihenfolge')));
  const L = Plane({title: 'Einbettungen x (Pfeil: + Position)', xr: [-2.5, 2.5], yr: [-2, 2], w: 380}), Rt = Plane({title: 'Ausgaben o je Wort', xr: [-2.5, 2.5], yr: [-2, 2], w: 380});
  const heat = h('div', {}), eq = h('div', {}), mats = h('details', {class: 'numbers'}, h('summary', {}, 'Gewichtsmatrizen W_Q, W_K, W_V bearbeiten'), h('div', {class: 'numgrid'}));
  root.append(h('div', {class: 'planes'}, L.root, Rt.root), h('div', {class: 'planes'}, heat, eq), mats);
  typeset(root);
  const g = mats.querySelector('.numgrid');
  ['WQ', 'WK', 'WV'].forEach(k => g.append(h('div', {style: 'flex-direction:column;align-items:flex-start'}, h('b', {}, k.replace('W', 'W_')),
    ...[0, 1].map(r => h('div', {}, ...[0, 1].map(c => numInput(W0[k][r][c], v => api.set(st => { st.sent[k][r][c] = v; return st; }), `${k} Zeile ${r + 1} Spalte ${c + 1}`)))))));
  return function update(S, R) {
    temp.update(S); const W = S.sent;
    pe.checked = W.pe; causal.checked = W.causal; peA.value = W.peA;
    const c = L.content; c.replaceChildren(); const ids = [];
    W.order.forEach((wi, pos) => {
      const x = W.X[wi], xp = R.sent.Xp[pos];
      if (W.pe) c.append(L.arrow(x, xp, TOKC[wi], 1.5, '', '3 3'), s('circle', {cx: L.X(xp[0]), cy: L.Y(xp[1]), r: 4, fill: TOKC[wi], opacity: .6}));
      ids.push('x' + wi);
      L.handle('x' + wi, {get: () => W.X[wi], set: v => api.set(st => { st.sent.X[wi] = v; return st; }), color: TOKC[wi], label: W.words[wi], aria: `Einbettung von ${W.words[wi]}`});
    });
    L.only(ids);
    const d = Rt.content; d.replaceChildren();
    R.equiv.forEach(e => { const wi = W.order[e.pos];
      d.append(s('circle', {cx: Rt.X(e.orig[0]), cy: Rt.Y(e.orig[1]), r: 9, fill: 'none', stroke: TOKC[wi], 'stroke-width': 2, 'stroke-dasharray': '3 2'}));
      if (e.dist > 1e-9) d.append(s('line', {x1: Rt.X(e.orig[0]), y1: Rt.Y(e.orig[1]), x2: Rt.X(e.now[0]), y2: Rt.Y(e.now[1]), stroke: 'var(--bad)', 'stroke-width': 1.5}));
      d.append(s('circle', {cx: Rt.X(e.now[0]), cy: Rt.Y(e.now[1]), r: 5.5, fill: TOKC[wi]}), s('text', {x: Rt.X(e.now[0]) + 8, y: Rt.Y(e.now[1]) - 7, class: 'lbl', fill: TOKC[wi]}, e.word)); });
    const n = W.order.length;
    const cells = [h('div', {class: 'h'}, 'Query ↓ / Key →'), ...W.order.map(wi => h('div', {class: 'h'}, W.words[wi]))];
    R.sent.A.forEach((row, i) => { cells.push(h('div', {class: 'h'}, W.words[W.order[i]])); row.forEach(a => cells.push(h('div', {style: `background:color-mix(in srgb,var(--accent) ${Math.round(a * 85)}%,transparent);color:${a > .55 ? '#fff' : 'inherit'}`}, f(a, 2)))); });
    heat.replaceChildren(h('h3', {style: 'font-size:14px;margin:6px 0'}, 'Gewichtsmatrix A = softmax(QKᵀ/√2·T)'), h('div', {class: 'heat', style: `grid-template-columns:repeat(${n + 1},minmax(0,1fr))`}, cells));
    const maxd = Math.max(...R.equiv.map(e => e.dist));
    eq.replaceChildren(h('h3', {style: 'font-size:14px;margin:6px 0'}, 'Test: Ändert die Reihenfolge die Ausgabe eines Wortes?'),
      h('table', {class: 'diff'}, h('tr', {}, h('th', {}, 'Wort'), h('th', {}, 'Position'), h('th', {}, '‖o − o_original‖')), R.equiv.map(e => h('tr', {}, h('td', {}, e.word), h('td', {}, e.pos + 1), h('td', {class: e.dist > 1e-9 ? 'down' : ''}, f(e.dist, 4))))),
      h('p', {class: 'verdict ' + (maxd > 1e-9 ? 'bad' : 'ok')}, maxd > 1e-9 ? 'Mindestens ein Wort hat jetzt eine andere Ausgabe: Die Reihenfolge ist sichtbar.' : (W.order.join() === '0,1,2,3' ? 'Originalreihenfolge – vertauschen Sie Wörter.' : 'Jedes Wort hat exakt dieselbe Ausgabe wie vorher: Reihenfolge unsichtbar.')));
  };
}

function attDim(root, api) {
  const S0 = api.S;
  const sl = h('input', {type: 'range', min: 0, max: DIMS.length - 1, step: 1, value: DIMS.indexOf(S0.dim.d), 'aria-label': 'Dimension d_k'});
  const lab = h('b', {}, S0.dim.d);
  sl.addEventListener('input', () => api.set(st => { st.dim.d = DIMS[+sl.value]; return st; }));
  root.append(h('p', {class: 'note', html: 'Reproduzierbares Experiment (Seed 11): 300 Ziehungen von \\(q\\) und 8 Keys mit unabhängigen \\(\\mathcal N(0,1)\\)-Komponenten. Wie verhalten sich Scores, Softmax und Gradient, wenn die Dimension \\(d_k\\) wächst?'}),
    h('div', {class: 'row'}, h('label', {class: 'ctl'}, 'Dimension d\u2096 = ', lab, sl)));
  const meters = h('div', {class: 'meters'}), chart = h('div', {}), ex = h('div', {class: 'planes'});
  root.append(meters, ex, chart);
  typeset(root);
  const all = DIMS.map(scaleExp);
  return function update(S, R) {
    lab.textContent = S.dim.d; sl.value = DIMS.indexOf(S.dim.d);
    const r = R.dim;
    meters.replaceChildren(meter('Varianz von q·k (gemessen)', f(r.varRaw, 1), null, 'Satz 3 sagt: d'), meter('Satz 3 sagt', f(r.d, 0), null),
      meter('max. Gewicht ohne Skalierung', f(r.raw.maxw, 3), r.raw.maxw), meter('max. Gewicht mit √d', f(r.scaled.maxw, 3), r.scaled.maxw),
      meter('‖J‖ ohne / mit Skalierung', `${f(r.raw.J, 3)} / ${f(r.scaled.J, 3)}`, null));
    const bars = (w, title) => h('div', {class: 'plane', style: 'padding:6px 10px'}, h('h3', {style: 'padding:0'}, title), ...w.map((x, j) => h('div', {class: 'row', style: 'margin:2px 0'}, h('span', {style: 'width:28px;font-size:12px'}, 'k' + sub[j + 1]), h('span', {class: 'wbar', style: `--c:var(--accent);width:${Math.round(x * 220)}px`}), h('span', {style: 'font-size:12px'}, f(x, 3)))));
    ex.replaceChildren(bars(r.example.wRaw, 'Eine Ziehung: softmax(q·k)'), bars(r.example.wScaled, 'Dieselbe Ziehung: softmax(q·k / √d)'));
    // Diagramm max. Gewicht über log2 d
    const W = 560, H = 200, X = i => 40 + i * (W - 60) / (DIMS.length - 1), Y = v => H - 26 - v * (H - 46);
    const svg = s('svg', {viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': 'Mittleres maximales Gewicht in Abhängigkeit von d mit und ohne Skalierung'});
    [0, .25, .5, .75, 1].forEach(v => svg.append(s('line', {x1: 40, x2: W - 20, y1: Y(v), y2: Y(v), class: 'gl', stroke: 'var(--grid)'}), s('text', {x: 34, y: Y(v) + 4, 'text-anchor': 'end', 'font-size': 11, fill: 'var(--mute)'}, f(v, 2))));
    DIMS.forEach((dd, i) => svg.append(s('text', {x: X(i), y: H - 8, 'text-anchor': 'middle', 'font-size': 11, fill: 'var(--mute)'}, dd)));
    for (const [key, col, name] of [['raw', 'var(--t1)', 'ohne Skalierung'], ['scaled', 'var(--t0)', 'mit 1/√d']]) {
      svg.append(s('polyline', {points: all.map((a, i) => `${X(i)},${Y(a[key].maxw)}`).join(' '), fill: 'none', stroke: col, 'stroke-width': 2.5}));
      all.forEach((a, i) => svg.append(s('circle', {cx: X(i), cy: Y(a[key].maxw), r: a.d === S.dim.d ? 6 : 3, fill: col})));
      svg.append(s('text', {x: X(DIMS.length - 1) - 4, y: Y(all[all.length - 1][key].maxw) + (key === 'raw' ? -8 : 16), 'text-anchor': 'end', 'font-size': 12, fill: col, 'font-weight': 600}, name));
    }
    svg.append(s('line', {x1: 40, x2: W - 20, y1: Y(1 / 8), y2: Y(1 / 8), stroke: 'var(--mute)', 'stroke-dasharray': '4 4'}), s('text', {x: W - 20, y: Y(1 / 8) - 4, 'text-anchor': 'end', 'font-size': 11, fill: 'var(--mute)'}, 'gleichverteilt: 1/8'));
    chart.replaceChildren(h('h3', {style: 'font-size:14px;margin:10px 0 4px'}, 'Mittleres größtes Gewicht über d\u2096 (Achse logarithmisch)'), svg);
  };
}

// ---- geführter Weg & Challenges: Self-Attention ----
const near = (a, b, t = 1e-6) => Math.abs(a - b) <= t;
attention.path = [
  {id: 'a1', title: 'Wonach sucht „Bank“?', story: 'Im Satz <i>„Wir sitzen auf der Bank am Fluss“</i> soll das Wort <b>Bank</b> erkennen, dass es um ein Ufer geht. Seine Query \\(q\\) wird mit jedem Key verglichen: \\(s_j=q^\\top k_j=\\lVert q\\rVert\\,\\lVert k_j\\rVert\\cos\\theta_j\\) – die gestrichelte Linie zeigt die Projektion von \\(k_j\\) auf die Richtung von \\(q\\).',
    setup: () => { const n = attInit('bank'); return n; },
    predict: {q: 'Sie drehen \\(q\\) zum Key von <b>Geld</b>. Was passiert mit der Ausgabe \\(o\\)?', options: ['Sie wandert in Richtung der Finanz-Bedeutung (Value von Geld).', 'Sie bleibt gleich – die Values haben sich ja nicht geändert.', 'Sie wandert aus dem grauen Bereich hinaus.'], correct: 0},
    task: 'Drehen Sie \\(q\\) so, dass <b>Geld</b> das größte Gewicht bekommt.', goal: (S, R) => S.view === 'one' && S.names[1] === 'Geld' && R.one.w.indexOf(Math.max(...R.one.w)) === 1,
    reveal: 'Das größte Gewicht erhält der Key mit der längsten Projektion auf \\(q\\). Die Values bleiben fest, aber die <em>Mischung</em> ändert sich: \\(o=\\sum_j w_jv_j\\) wandert zum Value von „Geld“. Kontext entscheidet so über die Bedeutung.', links: {book: 'attention', bookLabel: '§6', tasks: ['AT1'], cards: ['Self-Attention: Rechenweg']}},
  {id: 'a2', title: 'Länge ist Schärfe', story: 'Die Richtung von \\(q\\) entscheidet, <em>wen</em> Bank bevorzugt. Was bewirkt die <em>Länge</em>?',
    setup: S => { const n = attInit('bank'); n.q = [1, 0.25]; return n; },
    predict: {q: 'Sie verlängern \\(q\\) auf das Dreifache, ohne die Richtung zu ändern. Die Entropie …', options: ['… sinkt: die Verteilung wird spitzer.', '… steigt: mehr Wörter werden berücksichtigt.', '… bleibt gleich: nur die Richtung zählt.'], correct: 0},
    task: 'Verlängern Sie \\(q\\) auf mindestens \\(\\lVert q\\rVert\\ge 3\\) bei (nahezu) gleicher Richtung wie \\((1;\\,0{,}25)\\).', goal: (S, R) => S.view === 'one' && M.norm(S.q) >= 3 && Math.abs(Math.atan2(S.q[1], S.q[0]) - Math.atan2(.25, 1)) < .05,
    reveal: 'Weil \\((\\lambda q)^\\top k_j=\\lambda\\,q^\\top k_j\\), multipliziert die Verlängerung alle Scores mit \\(\\lambda\\). Das ist <b>exakt</b> dieselbe Wirkung wie Temperatur \\(T/\\lambda\\). Ein Netz kann über die Länge seiner Queries also selbst steuern, wie scharf es auswählt.', links: {book: 'attention', bookLabel: '§6', tasks: ['AT1']}},
  {id: 'a3', title: 'Nur Unterschiede zählen', story: 'Der lila Griff ◆ im Schwerpunkt verschiebt <b>alle</b> Keys um denselben Vektor \\(c\\). Damit ändert sich jeder Score: \\(q^\\top(k_j+c)=q^\\top k_j+q^\\top c\\).',
    setup: () => attInit('bank'),
    predict: {q: 'Sie verschieben alle Keys gemeinsam weit nach rechts oben. Die Gewichte …', options: ['… ändern sich nicht.', '… wandern zum Key, der danach am weitesten rechts liegt.', '… werden gleichmäßiger, weil alle Keys länger werden.'], correct: 0},
    task: 'Verschieben Sie alle Keys gemeinsam um mindestens 1,5 Einheiten (Griff ◆).', goal: S => S.view === 'one' && M.norm(S.shift) >= 1.5,
    reveal: 'Alle Scores ändern sich um <em>denselben</em> Betrag \\(q^\\top c\\). Die Softmax ist verschiebungsinvariant: \\(\\frac{e^{s_j+a}}{\\sum_l e^{s_l+a}}=\\frac{e^{s_j}}{\\sum_l e^{s_l}}\\). Achtung, Gegenbeispiel: Verschieben Sie nur <em>einen</em> Key, ändert sich alles. In der Implementierung nutzt man dieselbe Invarianz, um \\(\\max_l s_l\\) abzuziehen und Überläufe zu vermeiden (Spalte „exp(·−max)“).', links: {book: 'attention', bookLabel: '§6', tasks: ['AT1']}},
  {id: 'a4', title: 'Gleichgültigkeit erzeugen', story: 'Wann verteilt ein Wort seine Aufmerksamkeit völlig gleichmäßig? Die naheliegende Antwort \\(q=0\\) ist richtig – aber es gibt mehr.',
    setup: () => { const n = attInit('line'); n.q = [1, 0.4]; return n; },
    task: 'Erreichen Sie \\(H\\ge 0{,}995\\,H_{\\max}\\) mit \\(T=1\\) und \\(\\lVert q\\rVert\\ge 1\\). Sie dürfen auch die Keys bewegen.', goal: (S, R) => S.view === 'one' && near(S.T, 1, 1e-9) && M.norm(S.q) >= 1 && R.one.H >= .995 * R.one.Hmax,
    reveal: 'Gleichverteilung heißt: alle Scores gleich, also \\(q^\\top(k_i-k_j)=0\\) für alle Paare – \\(q\\) steht senkrecht auf allen <em>Differenzen</em> der Keys. In 2D geht das mit \\(q\\neq0\\) nur, wenn alle Keys auf einer Geraden liegen, die senkrecht zu \\(q\\) verläuft (dann sind alle Projektionen gleich lang). In hohen Dimensionen ist das viel leichter möglich.', links: {book: 'attention', bookLabel: '§6'}},
  {id: 'a5', title: 'Was die Ausgabe nie kann', story: 'Die Gewichte sind nichtnegativ und summieren sich zu 1. Was folgt daraus für \\(o\\)?',
    setup: () => { const n = attInit('bank'); n.target = [2.2, 1.6]; return n; },
    predict: {q: 'Kann \\(o\\) den rot markierten Punkt \\(Z\\) erreichen, wenn Sie nur \\(q\\), die Keys und \\(T\\) ändern?', options: ['Nein – \\(o\\) bleibt immer in der grauen Fläche (konvexe Hülle der Values).', 'Ja, mit sehr kleiner Temperatur.', 'Ja, wenn \\(q\\) lang genug ist.'], correct: 0},
    task: 'Versuchen Sie es: Bringen Sie \\(o\\) so nah wie möglich an \\(Z\\), ohne Values zu bewegen. Ziel ist erreicht, wenn \\(o\\) den Rand der Hülle berührt (Abstand < 0,05).', goal: (S, R) => S.view === 'one' && !!S.target && hullDist(S.V, R.one.out) < 1e-9 && boundaryDist(S.V, R.one.out) < .05,
    reveal: 'Mit \\(w_j\\ge0\\), \\(\\sum_jw_j=1\\) ist \\(o\\) eine <b>Konvexkombination</b> der Values und liegt in deren konvexer Hülle. Punkte außerhalb sind unerreichbar – egal welche Query, Keys oder Temperatur. Der Rand wird nur im Grenzfall erreicht, wenn einige Gewichte gegen 0 gehen. Gegenmittel im Transformer: die Ausgabeprojektion \\(W_O\\) und die Residualverbindung verlassen diese Hülle.', links: {book: 'attention', bookLabel: '§6'}},
  {id: 'a6', title: 'Warum durch \\(\\sqrt{d_k}\\) teilen?', story: 'Wechseln Sie zur Ansicht <b>Skalierung &amp; Dimension</b>. Echte Modelle nutzen \\(d_k=64\\) oder mehr.',
    setup: S => { S.view = 'dim'; S.dim.d = 2; return S; },
    predict: {q: 'Ohne Skalierung, bei \\(d_k=256\\): Wie sieht die Softmax über 8 zufällige Keys typischerweise aus?', options: ['Fast one-hot: ein Gewicht nahe 1.', 'Fast gleichverteilt: alle nahe 1/8.', 'Wie bei \\(d_k=2\\) – Zufall ist Zufall.'], correct: 0},
    task: 'Stellen Sie \\(d_k=256\\) ein und vergleichen Sie beide Balkendiagramme und \\(\\lVert J\\rVert\\).', goal: S => S.view === 'dim' && S.dim.d >= 256,
    reveal: 'Die gemessene Varianz von \\(q^\\top k\\) wächst wie \\(d_k\\) (Satz 3). Ohne Skalierung liegen die Scores typischerweise \\(\\sqrt{d_k}\\)-fach auseinander, die Softmax sättigt, und ihre Jacobi-Matrix \\(\\operatorname{diag}(w)-ww^\\top\\) wird fast null: Gradienten verschwinden. Teilen durch \\(\\sqrt{d_k}\\) hält die Varianz bei 1. Grenzen: Das setzt unabhängige Komponenten mit Varianz 1 voraus – trainierte Projektionen erfüllen das nicht exakt (Vaswani et al. 2017, §3.2.1, Fußnote zur Varianz).', links: {book: 'attention', bookLabel: '§6, Satz 3', tasks: ['AT1']}},
  {id: 'a7', title: 'Self-Attention sieht keine Reihenfolge', story: 'Ansicht <b>Ganzer Satz</b>: „Mia sieht Tom heute“. Wer sieht wen? Ein RNN wüsste es aus der Reihenfolge.',
    setup: S => { S.view = 'sent'; S.sent.order = [0, 1, 2, 3]; S.sent.pe = false; S.sent.causal = false; return S; },
    predict: {q: 'Sie vertauschen „Mia“ und „Tom“. Ändert sich die Ausgabe von „Tom“?', options: ['Nein, sie ist exakt gleich – nur ihre Zeile wandert.', 'Ja, weil Tom jetzt vorn steht.', 'Nur die Gewichtsmatrix ändert sich, nicht die Ausgabe von Tom, aber die von „sieht“.'], correct: 0},
    task: 'Vertauschen Sie Wörter (ohne Positionsvektoren) und dann schalten Sie Positionsvektoren ein, bis ein Wort eine andere Ausgabe hat als in der Originalreihenfolge.', goal: (S, R) => S.view === 'sent' && S.sent.pe && S.sent.order.join() !== '0,1,2,3' && Math.max(...R.equiv.map(e => e.dist)) > .05,
    reveal: '<b>Satz 4:</b> \\(\\mathrm{Att}(PX)=P\\,\\mathrm{Att}(X)\\). Ohne Positionsinformation ist Self-Attention eine Mengenoperation: „Mia sieht Tom“ und „Tom sieht Mia“ liefern für jedes Wort dieselbe Ausgabe. Erst \\(x_t+p_t\\) (oder eine kausale Maske, oder RoPE) macht die Position sichtbar – Ihr Gegenbeispiel ist der Beweis, dass die Annahme „gleiche Eingabevektoren“ in Satz 4 wesentlich ist.', links: {book: 'position', bookLabel: '§7, Satz 4', tasks: ['AT2']}},
];
function boundaryDist(V, z) { const H = convexHull(V); return Math.min(...H.map((a, i) => segDist(a, H[(i + 1) % H.length], z))); }
attention.challenges = [
  {id: 'c-spot', title: 'Scheinwerfer', level: 'leicht', goal: 'Bringen Sie mindestens 80 % des Gewichts auf <b>der</b> – das Wort, das eigentlich nichts beiträgt.', constraint: '\\(T=1\\), Skalierung an, \\(\\lVert q\\rVert\\le 3\\); Keys nicht bewegen.',
    setup: () => attInit('bank'),
    check: (S, R) => { const okC = S.view === 'one' && near(S.T, 1, 1e-9) && S.scaled && M.norm(S.q) <= 3 + 1e-9 && S.preset === 'bank' && JSON.stringify(S.K) === JSON.stringify(ATT_PRESETS.bank.K) && !S.shift[0] && !S.shift[1];
      const w = R.one.w[2] || 0; return {done: okC && w >= .8, progress: w / .8, msg: okC ? `w(der) = ${f(w, 3)}` : 'Bedingung verletzt – „Starten“ stellt sie wieder her.'}; },
    hints: ['Der Key von „der“ ist kurz und zeigt nach rechts unten. Welche Richtung von \\(q\\) bevorzugt ihn gegenüber den langen Keys?', 'Es zählt nicht \\(s_{der}\\) allein, sondern der <em>Abstand</em> zu den anderen Scores. Suchen Sie eine Richtung, in der die beiden langen Keys negative Projektionen haben.', 'Probieren Sie \\(q=(-1{,}4;\\,-2)\\): beide langen Keys liegen dann „hinter“ \\(q\\). Mehr als etwa 88 % sind unter diesen Bedingungen nicht möglich – warum?'],
    success: 'Gelöst. Nicht die Größe des eigenen Scores entscheidet, sondern sein Vorsprung: \\(w_j=1/\\sum_l e^{(s_l-s_j)/T}\\). Ein kurzer Key gewinnt, wenn alle anderen Keys stark negative Projektionen auf \\(q\\) haben.', links: {book: 'attention', tasks: ['AT1']}},
  {id: 'c-uniform', title: 'Gleichgültig, aber nicht leer', level: 'mittel', goal: 'Machen Sie die Verteilung gleichmäßig (\\(H\\ge 0{,}999\\,H_{\\max}\\)) mit \\(\\lVert q\\rVert\\ge 2\\).', constraint: '\\(T=1\\). Keys dürfen bewegt werden.',
    setup: () => attInit('bank'),
    check: (S, R) => { const ok = S.view === 'one' && near(S.T, 1, 1e-9) && M.norm(S.q) >= 2; const r = R.one.H / R.one.Hmax; return {done: ok && r >= .999, progress: r, msg: `H/H_max = ${f(r, 4)}${ok ? '' : ' (Bedingung: T = 1, ‖q‖ ≥ 2)'}`}; },
    hints: ['Gleichverteilung ⇔ alle Scores gleich ⇔ alle Keys haben dieselbe Projektion auf \\(q\\).', 'Alle Keys müssen auf einer Geraden senkrecht zu \\(q\\) liegen.', 'Stellen Sie \\(q=(2;0)\\) und setzen Sie alle Keys auf \\(x_1=1\\) (beliebige \\(x_2\\)).'],
    success: 'Gleichverteilt bei langer Query: \\(q\\perp(k_i-k_j)\\) für alle Paare. Lehre: Hohe Entropie heißt nicht „Query ist bedeutungslos“, sondern „die Keys unterscheiden sich nicht in der Richtung, nach der gefragt wird“.', links: {book: 'attention'}},
  {id: 'c-target', title: 'Punktlandung', level: 'mittel', goal: 'Bringen Sie die Ausgabe \\(o\\) auf den Zielpunkt \\(Z=(1;\\,1)\\) (Abstand < 0,05) – nur über \\(q\\) und \\(T\\).', constraint: 'Keys und Values bleiben wie im Bank-Beispiel.',
    setup: () => { const n = attInit('bank'); n.target = [1, 1]; return n; },
    check: (S, R) => { const fixed = S.preset === 'bank' && JSON.stringify(S.V) === JSON.stringify(ATT_PRESETS.bank.V) && JSON.stringify(S.K) === JSON.stringify(ATT_PRESETS.bank.K) && !S.shift[0] && !S.shift[1]; const d = S.target ? M.norm(M.sub(R.one.out, S.target)) : 9; return {done: S.view === 'one' && fixed && d < .05, progress: 1 - Math.min(1, d / 1.5), msg: `Abstand ‖o − Z‖ = ${f(d, 3)}`}; },
    hints: ['\\(Z\\) liegt zwischen den Values von Fluss und Geld. Sie brauchen ungefähr gleich große Gewichte auf beiden.', 'Gleich große Scores für Fluss und Geld: \\(q\\perp(k_{Fluss}-k_{Geld})\\).', 'Die Richtung \\((1{,}9;\\,1{,}1)\\) ist ein Ausgangspunkt; danach mit Temperatur oder Länge das Gewicht von „der“ verringern.'],
    success: 'Gelöst – eine Punktlandung braucht zwei Stellgrößen: die Richtung von \\(q\\) bestimmt das <em>Verhältnis</em> der Gewichte von Fluss und Geld, Länge bzw. Temperatur bestimmen, wie viel Gewicht „der“ noch erhält.', links: {book: 'attention'}},
  {id: 'c-impossible', title: 'Unerreichbar?', level: 'Transfer', goal: 'Bringen Sie \\(o\\) auf \\(Z=(2{,}2;\\,1{,}6)\\) – oder begründen Sie, warum das nicht geht.', constraint: 'Values bleiben fest.',
    setup: () => { const n = attInit('bank'); n.target = [2.2, 1.6]; return n; },
    check: (S, R) => { const d = S.target ? M.norm(M.sub(R.one.out, S.target)) : 9; return {done: false, progress: 1 - Math.min(1, d / 2.5), msg: `Abstand ‖o − Z‖ = ${f(d, 3)}`}; },
    impossible: {q: 'Warum ist \\(Z\\) unerreichbar?', options: ['\\(o=\\sum_j w_jv_j\\) mit \\(w_j\\ge0,\\ \\sum_j w_j=1\\) liegt immer in der konvexen Hülle der Values; \\(Z\\) liegt außerhalb.', 'Die Temperatur lässt sich nicht klein genug einstellen.', 'Die Query ist auf den sichtbaren Bereich beschränkt.'], correct: 0,
      applies: S => S.view === 'one' && !!S.target && hullDist(S.V, S.target) > 1e-6, notApplicable: 'Hier liegt das Ziel innerhalb der Hülle (oder es gibt keins) – dann ist es erreichbar.',
      why: {1: 'Selbst \\(T\\to0\\) konzentriert das Gewicht nur auf die größten Scores: \\(o\\) wird ein einzelner Value (eindeutiges Maximum) oder der Mittelwert der gleichauf liegenden Values – beides liegt in der Hülle.', 2: 'Auch eine beliebig lange Query ändert nur die Gewichte, nicht deren Eigenschaften \\(w_j\\ge0,\\ \\sum w_j=1\\).'}},
    hints: ['Wohin kommt \\(o\\) im Extremfall \\(T\\to0\\)?', 'Welche Werte können Softmax-Gewichte annehmen, welche nie?', 'Graue Fläche = alle Konvexkombinationen der Values.'],
    success: 'Richtig begründet: Softmax-Gewichte bilden eine Wahrscheinlichkeitsverteilung, also ist \\(o\\) eine Konvexkombination. Erreichen würde man \\(Z\\) nur mit negativen Gewichten oder Gewichten, deren Summe größer als 1 ist. Genau deshalb folgen im Transformer eine lineare Abbildung \\(W_O\\) und eine Residualverbindung.', links: {book: 'attention'}},
  {id: 'c-sat', title: 'Sättigung messen', level: 'mittel', goal: 'Finden Sie das kleinste \\(d_k\\), bei dem das mittlere größte Gewicht <b>ohne</b> Skalierung über 0,8 liegt.', constraint: 'Ansicht „Skalierung &amp; Dimension“.',
    setup: S => { S.view = 'dim'; S.dim.d = 1; return S; },
    check: (S, R) => { const first = DIMS.find(d => scaleExp(d).raw.maxw > .8); return {done: S.view === 'dim' && S.dim.d === first, progress: S.view === 'dim' ? Math.min(1, R.dim.raw.maxw / .8) : 0, msg: S.view === 'dim' ? `d = ${S.dim.d}: max. Gewicht ${f(R.dim.raw.maxw, 3)}` : ''}; },
    hints: ['Bewegen Sie den Regler schrittweise nach rechts und beobachten Sie die orange Kurve.', 'Achten Sie auf das <em>kleinste</em> \\(d\\) – danach steigt die Kurve weiter.'],
    success: 'Schon bei moderaten Dimensionen kippt die unskalierte Softmax in Richtung one-hot, weil die Standardabweichung der Scores \\(\\sqrt{d_k}\\) beträgt. Mit Skalierung bleibt das größte Gewicht über alle \\(d_k\\) nahezu gleich – genau das sagt Satz 3 voraus.', links: {book: 'attention', bookLabel: 'Satz 3'}},
  {id: 'c-order', title: 'Gegenbeispiel bauen', level: 'Transfer', goal: 'Konstruieren Sie einen Zustand, in dem ein Wort nach einer Vertauschung eine um mindestens 0,3 andere Ausgabe hat – <b>ohne</b> Positionsvektoren.', constraint: 'Ansicht „Ganzer Satz“, Positionsvektoren aus.',
    setup: S => { S.view = 'sent'; S.sent.pe = false; S.sent.causal = false; S.sent.order = [0, 1, 2, 3]; return S; },
    check: (S, R) => { const ok = S.view === 'sent' && !S.sent.pe; const m = S.view === 'sent' ? Math.max(...R.equiv.map(e => e.dist)) : 0; return {done: ok && m >= .3, progress: m / .3, msg: ok ? `größte Abweichung ${f(m, 3)}` : 'Positionsvektoren müssen aus sein.'}; },
    hints: ['Ohne Positionsvektoren gilt Satz 4 – es sei denn, eine andere Komponente schaut auf die Position.', 'Welche Option in der Steuerleiste hängt von der Position ab, ohne Vektoren zu addieren?', 'Die kausale Maske lässt Wort \\(t\\) nur \\(1..t\\) sehen.'],
    success: 'Mit kausaler Maske hängt die Menge der sichtbaren Wörter von der Position ab: Satz 4 gilt nicht mehr, obwohl keine Positionsvektoren addiert werden. Decoder-Modelle können deshalb Reihenfolge teilweise schon über die Maske erkennen – Satz 4 setzt voraus, dass die Softmax über <em>alle</em> Positionen läuft.', links: {book: 'position', tasks: ['AT2']}},
];

