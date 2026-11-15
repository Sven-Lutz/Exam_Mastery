/* Entrepreneurship – Labor „Finanzierungsrunden & Fondslogik“. Nutzt lab_core.js. */
'use strict';
const VM = window.VentureMath;
const HC = {'Gründer 1': 'var(--t0)', 'Gründer 2': 'var(--t4)', Pool: 'var(--mute)', SAFE: 'var(--t3)', 'Seed-Investor': 'var(--t1)', 'Serie-A-Investor': 'var(--t2)'};
function ventInit() { return {view: 'cap', founders: [600000, 400000], pool0: 0, safe: 500000, cap: 5000000, disc: 0.2, pre: 8000000, inv: 2000000, pool: 0.1, pre2: 24000000, inv2: 6000000,
  f: {size: 100e6, fee: 0.02, years: 10, n: 25, own: 0.15, k: 1, ew: 2e9, er: 0, carry: 0.2}}; }
const eur = x => x === null || x === undefined || Number.isNaN(x) ? '–' : (Math.abs(x) >= 1e9 ? f(x / 1e9, 2) + ' Mrd. €' : Math.abs(x) >= 1e6 ? f(x / 1e6, 2) + ' Mio. €' : f(x / 1e3, 0) + ' Tsd. €');
const pct = x => f(100 * x, 1) + ' %';
const ventLab = registerLab({
  id: 'runden', title: 'Finanzierungsrunden & Fondslogik',
  intro: 'Wer besitzt nach SAFE, Seed und Serie A wie viel – und was ist es wert? Verändern Sie Cap, Rabatt, Bewertungen, Optionspool und Investitionsbeträge; alle Anteile werden aus denselben Gleichungen neu berechnet. Die zweite Ansicht zeigt, warum Wagniskapitalfonds nur in Unternehmen mit sehr großem Potenzial investieren.',
  init: ventInit,
  structural: (a, b) => a.view !== b.view,
  compute(S) { return {sim: VM.simulate(S), fd: VM.fund(S.f)}; },
  quantities(S, R) { if (R.sim.error) return [];
    return [{id: 'fs', label: 'Gründeranteil nach Serie A', value: R.sim.founderShare[3]}, {id: 'fv', label: 'Wert der Gründeranteile nach Serie A', value: R.sim.founderValue[3]},
      {id: 'safe', label: 'SAFE-Anteil nach Seed', value: R.sim.stages[2].share.find(x => x[0] === 'SAFE')[1]}, {id: 'tvpi', label: 'Fonds: Netto-Multiple (TVPI)', value: R.fd.tvpi}]; },
  explain(Sb, Rb, Sa, Ra) {
    if (Ra.sim.error || Rb.sim.error) return 'Ungültiger Zustand: ' + (Ra.sim.error || Rb.sim.error);
    const o = [];
    const a = Rb.sim, b = Ra.sim;
    if (a.r1.regime !== b.r1.regime) o.push(`Der SAFE wandelt jetzt über ${b.r1.regime === 'cap' ? 'den Cap' : Sa.disc > 0 ? 'den Rabatt' : 'den Rundenpreis'}: Es gilt jeweils der niedrigere Umwandlungspreis (Cap-Preis ${eur(b.r1.priceCap)} je Anteil vs. Rabattpreis ${eur((1 - Sa.disc) * b.r1.price)}).`);
    if (Sa.pool !== Sb.pool) o.push('Der Ziel-Pool wird vor der Runde geschaffen und ist in der Pre-Money-Bewertung enthalten („Option Pool Shuffle“): Die Verwässerung tragen die Altgesellschafter, nicht der neue Investor.');
    if (Sa.pre2 !== Sb.pre2) o.push(`Pre-Money der Serie A: ${eur(Sb.pre2)} → ${eur(Sa.pre2)}. Der Gründeranteil sinkt mit jeder Runde, aber der Wert hängt vom Preis ab: Wert = Anteile × Preis je Anteil.`);
    o.push(`Gründeranteil nach Serie A ${pct(a.founderShare[3])} → ${pct(b.founderShare[3])}; Wert ${eur(a.founderValue[3])} → ${eur(b.founderValue[3])}.`);
    if (b.founderShare[3] < a.founderShare[3] && b.founderValue[3] > a.founderValue[3]) o.push('Gegenbeispiel zu „Verwässerung = Geldverlust“: Anteil sinkt, Wert steigt.');
    return o.join(' ');
  },
  view(root, api) {
    root.append(h('div', {class: 'row'}, seg([['cap', 'Kapitalisierungstabelle'], ['fund', 'Fondslogik']], api.S.view, v => api.set({view: v}), 'Ansicht')));
    return api.S.view === 'cap' ? capView(root, api) : fundView(root, api);
  },
});
function field(label, get, set, aria, fmt = v => f(v, 0)) {
  const i = h('input', {class: 'num', type: 'text', inputmode: 'decimal', 'aria-label': aria || label, style: 'width:110px'});
  i.addEventListener('change', () => { const v = parse(i.value.replace(/\./g, '').replace(/\s/g, '')); if (v !== null) set(v); });
  return {el: h('label', {class: 'ctl'}, label, i), up: S => { if (document.activeElement !== i) i.value = fmt(get(S)); }};
}
function capView(root, api) {
  const F = [
    field('SAFE-Betrag €', S => S.safe, v => api.set({safe: v})), field('Post-Money-Cap €', S => S.cap, v => api.set({cap: v})),
    field('Rabatt %', S => S.disc * 100, v => api.set({disc: v / 100}), 'Rabatt in Prozent'),
    field('Seed Pre-Money €', S => S.pre, v => api.set({pre: v})), field('Seed-Investition €', S => S.inv, v => api.set({inv: v})),
    field('Pool-Ziel nach Seed %', S => S.pool * 100, v => api.set({pool: v / 100}), 'Pool-Ziel in Prozent'),
    field('Serie A Pre-Money €', S => S.pre2, v => api.set({pre2: v})), field('Serie-A-Investition €', S => S.inv2, v => api.set({inv2: v}))];
  const sl = h('input', {type: 'range', min: 2e6, max: 40e6, step: 5e5, 'aria-label': 'Serie A Pre-Money (Schieberegler)'});
  sl.addEventListener('input', () => api.set({pre2: +sl.value}));
  root.append(h('div', {class: 'numgrid'}, F.map(x => h('div', {}, x.el))), h('div', {class: 'row'}, h('label', {class: 'ctl'}, 'Serie A Pre-Money ', sl), h('button', {onclick: () => api.reset()}, 'Zurücksetzen')));
  const chart = h('div', {class: 'plane'}), meters = h('div', {class: 'meters'}), fl = h('div', {class: 'formula-live'}), tbl = h('div', {class: 'calc-wrap'});
  root.append(chart, fl, meters, tbl);
  return function update(S, R) {
    F.forEach(x => x.up(S)); sl.value = S.pre2;
    if (R.sim.error) { chart.replaceChildren(h('p', {class: 'verdict bad'}, R.sim.error)); return; }
    const st = R.sim.stages, W = 760, H = 270, bw = 120;
    const svg = s('svg', {viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': 'Anteile je Gesellschafter in vier Phasen'});
    st.forEach((g, i) => { let y = 20; const x = 40 + i * 180;
      g.share.forEach(([name, sh]) => { const hh = sh * 200; if (hh > 0.2) { svg.append(s('rect', {x, y, width: bw, height: hh, fill: HC[name], opacity: .85}, s('title', {}, `${name}: ${pct(sh)}`))); if (hh > 14) svg.append(s('text', {x: x + 6, y: y + 13, 'font-size': 11, fill: '#fff', 'font-weight': 600}, `${name.replace('-Investor', '')} ${pct(sh)}`)); } y += hh; });
      svg.append(s('text', {x, y: 238, 'font-size': 11, fill: 'var(--ink)', 'font-weight': 600}, g.label.length > 22 ? g.label.slice(0, 22) + '…' : g.label),
        s('text', {x, y: 254, 'font-size': 11, fill: 'var(--mute)'}, R.sim.founderValue[i] === null ? '' : 'Gründerwert ' + eur(R.sim.founderValue[i]))); });
    chart.replaceChildren(h('h3', {}, 'Anteile je Phase (Fläche = 100 %) und Wert der Gründeranteile'), svg);
    const r = R.sim.r1;
    fl.innerHTML = `SAFE wandelt über <b>${r.regime === 'cap' ? 'den Cap' : S.disc > 0 ? 'den Rabatt' : 'den Rundenpreis (ohne Rabatt)'}</b>: Cap-Aktien x = S₀·A/(C − A) = ${f(r.xCap, 0)}; Rundenpreis = Pre-Money / Aktien vor Investition = ${eur(S.pre)} / ${f(r.D, 0)} = ${f(r.price, 4)} €; Rabattpreis = ${f((1 - S.disc) * r.price, 4)} €, Cap-Preis = ${f(r.priceCap, 4)} € (vor Pool-Effekt der Cap-Variante). Seed-Investor: I/(V + I) = ${pct(S.inv / (S.pre + S.inv))}.`;
    meters.replaceChildren(meter('Gründer nach Seed', pct(R.sim.founderShare[2]), R.sim.founderShare[2]), meter('Gründer nach Serie A', pct(R.sim.founderShare[3]), R.sim.founderShare[3]),
      meter('Preis je Anteil Seed → A', `${f(r.price, 3)} € → ${f(R.sim.price2, 3)} €`, null), meter('Runde', S.pre2 >= S.pre + S.inv ? 'Up-Round' : 'Down-Round', null));
    tbl.replaceChildren(h('table', {class: 'calc'}, h('tr', {}, h('th', {}, 'Gesellschafter'), ...st.map(g => h('th', {}, g.label))),
      ['Gründer 1', 'Gründer 2', 'Pool', 'SAFE', 'Seed-Investor', 'Serie-A-Investor'].map(nm => h('tr', {}, h('td', {}, h('span', {class: 'chip', style: `--c:${HC[nm]}`}, nm)),
        ...st.map(g => { const e = g.holders.find(x => x[0] === nm); return h('td', {}, e ? `${f(e[1], 0)} (${pct(e[1] / g.total)})` : '–'); }))),
      h('tr', {class: 'sum'}, h('td', {}, 'Summe'), ...st.map(g => h('td', {}, f(g.total, 0))))));
  };
}
function fundView(root, api) {
  const F = [field('Fondsgröße €', S => S.f.size, v => api.set(st => { st.f.size = v; return st; })), field('Unternehmen', S => S.f.n, v => api.set(st => { st.f.n = Math.max(1, Math.round(v)); return st; })),
    field('Anteil bei Exit %', S => S.f.own * 100, v => api.set(st => { st.f.own = v / 100; return st; })), field('Gewinner (Anzahl)', S => S.f.k, v => api.set(st => { st.f.k = Math.max(0, Math.round(v)); return st; })),
    field('Exitwert Gewinner €', S => S.f.ew, v => api.set(st => { st.f.ew = v; return st; })), field('Exitwert übrige €', S => S.f.er, v => api.set(st => { st.f.er = v; return st; }))];
  root.append(h('p', {class: 'note'}, 'Vereinfachung: gleiche Tickets, ein Anteil bei Exit für alle, 2 % Verwaltungsgebühr p. a. über 10 Jahre, 20 % Carry auf den Gewinn über der Fondsgröße. Eigene Rechnung, keine Marktdaten.'),
    h('div', {class: 'numgrid'}, F.map(x => h('div', {}, x.el))));
  const meters = h('div', {class: 'meters'}), fl = h('div', {class: 'formula-live'}), bars = h('div', {class: 'plane', style: 'padding:8px 12px'});
  root.append(fl, meters, bars);
  return function update(S, R) {
    F.forEach(x => x.up(S)); const d = R.fd, ff = S.f;
    fl.innerHTML = `Brutto-Rückfluss = Anteil × (k·Exit<sub>Gewinner</sub> + (n − k)·Exit<sub>Rest</sub>) = ${pct(ff.own)} × (${ff.k}·${eur(ff.ew)} + ${ff.n - ff.k}·${eur(ff.er)}) = <b>${eur(d.gross)}</b>; Netto-Multiple ${f(d.tvpi, 2)}×. Ein einzelner Exit zahlt den Fonds zurück ab ${eur(d.needWinner)} = Fondsgröße / Anteil.`;
    meters.replaceChildren(meter('Gebühren (10 J.)', eur(d.fees), null), meter('investierbar', eur(d.investable), null), meter('Netto an Investoren', eur(d.net), null), meter('Netto-Multiple', f(d.tvpi, 2) + '×', Math.min(1, d.tvpi / 3)), meter('Anteil der Gewinner am Rückfluss', pct(d.share), d.share));
    bars.replaceChildren(h('h3', {style: 'padding:0'}, 'Woher der Rückfluss kommt'), h('div', {class: 'row'}, h('span', {style: 'width:140px'}, 'Gewinner'), h('span', {class: 'wbar', style: `--c:var(--ok);width:${Math.round(d.share * 400)}px`}), pct(d.share)),
      h('div', {class: 'row'}, h('span', {style: 'width:140px'}, 'übrige Beteiligungen'), h('span', {class: 'wbar', style: `--c:var(--mute);width:${Math.round((1 - d.share) * 400)}px`}), pct(1 - d.share)));
  };
}
ventLab.path = [
  {id: 'v1', title: 'Was ein Post-Money-Cap verspricht', story: 'SAFE über 500 Tsd. € mit Post-Money-Cap 5 Mio. €. Laut YC-Leitfaden ist der verkaufte Anteil Betrag / Cap.', setup: () => ventInit(),
    predict: {q: 'Welchen Anteil hält der SAFE direkt vor der Seed-Runde (wie umgewandelt)?', options: ['10 %', '9,1 %', '20 %'], correct: 0},
    task: 'Prüfen Sie in der Tabelle die Spalte „nach SAFE“.', goal: (S, R) => S.view === 'cap' && !R.sim.error && Math.abs(R.sim.stages[1].share.find(x => x[0] === 'SAFE')[1] - S.safe / S.cap) < 1e-9,
    reveal: 'x/(S₀ + x) = A/C ⇔ x = S₀·A/(C − A). Mit 1 Mio. Gründeraktien: x = 111 111, Anteil exakt 10 %. Danach wird der SAFE in der Seed-Runde verwässert wie alle anderen (Leitfaden S. 2, Note #2).', links: {}},
  {id: 'v2', title: 'Cap oder Rabatt?', story: 'Der SAFE erhält den günstigeren Preis: Cap-Preis oder Rundenpreis minus Rabatt.', setup: () => ventInit(),
    task: 'Senken Sie die Seed-Pre-Money so weit, dass der Rabatt statt des Caps greift.', goal: (S, R) => S.view === 'cap' && !R.sim.error && R.sim.r1.regime === 'discount',
    reveal: 'Der Rabatt greift, wenn (1 − d)·Rundenpreis < Cap-Preis – also bei niedriger Bewertung der Runde. Bei hoher Bewertung schützt der Cap den Frühinvestor. Beide Klauseln begrenzen den Preis nach oben, an verschiedenen Stellen.', links: {}},
  {id: 'v3', title: 'Verwässerung ist nicht Wertverlust', story: 'Die Kapitelüberschrift lautet „Verwässerung bedeutet, dass die Gründer Geld verlieren“. Stimmt das immer?', setup: () => ventInit(),
    predict: {q: 'Up-Round mit Serie A Pre-Money 24 Mio. €: Was passiert mit dem Wert der Gründeranteile?', options: ['Er steigt, obwohl der Anteil sinkt.', 'Er sinkt, weil der Anteil sinkt.', 'Er bleibt gleich.'], correct: 0},
    task: 'Machen Sie aus der Serie A eine Down-Round (Pre-Money unter der Seed-Post-Money) und vergleichen Sie.', goal: (S, R) => S.view === 'cap' && !R.sim.error && S.pre2 < S.pre + S.inv,
    reveal: 'Wert = Anteile × Preis. In einer Up-Round steigt der Preis stärker, als der Anteil sinkt; der Gründerwert wächst. In einer Down-Round sinkt der Preis – erst hier verlieren die Gründer Wert (auf Papier). Die Aussage gilt also nur bei Down-Rounds bzw. wenn der Preis nicht steigt.', links: {}},
  {id: 'v4', title: 'Warum nur riesige Märkte', story: 'Fondslogik: 100 Mio. €, 25 Beteiligungen, 15 % Anteil bei Exit.', setup: S => { S.view = 'fund'; return S; },
    predict: {q: 'Wie groß muss ein einzelner Exit sein, um allein den Fonds zurückzuzahlen?', options: ['ca. 667 Mio. €', '100 Mio. €', '4 Mio. €'], correct: 0},
    task: 'Setzen Sie die Zahl der Gewinner auf 0 und die übrigen Exits auf 40 Mio. €: Wie hoch ist das Multiple?', goal: (S, R) => S.view === 'fund' && S.f.k === 0 && S.f.er >= 40e6,
    reveal: 'Fondsgröße / Anteil = 100 Mio. € / 0,15 ≈ 667 Mio. €. 25 solide Exits zu 40 Mio. € bringen nur 150 Mio. € brutto (1,4× netto nach Carry). Wenige Ausreißer tragen die Rendite – deshalb prüfen VCs zuerst das Potenzial, nicht die Überlebenswahrscheinlichkeit.', links: {}},
];
ventLab.challenges = [
  {id: 'w-major', title: 'Mehrheit halten', level: 'mittel', goal: 'Gründer halten nach der Serie A mindestens 50 %. Verändern Sie nur Cap, Pool und Pre-Money-Bewertungen.', setup: () => ventInit(),
    check: (S, R) => ({done: !R.sim.error && S.safe === 500000 && S.inv === 2e6 && S.inv2 === 6e6 && R.sim.founderShare[3] >= .5, progress: R.sim.error ? 0 : R.sim.founderShare[3] / .5, msg: R.sim.error || `Gründer nach Serie A: ${pct(R.sim.founderShare[3])}`}),
    hints: ['Jeder Investor erhält I/(V + I). Höhere Pre-Money senkt seinen Anteil.', 'Der Pool kommt vor der Runde und belastet nur die Altgesellschafter.'], success: 'Gründeranteil = Produkt der Restanteile aller Runden. Hebel: Bewertungen (Investoranteil I/(V+I)), Pool-Größe (Shuffle) und Cap.', links: {}},
  {id: 'w-cap', title: 'Cap schlägt Rabatt', level: 'leicht', goal: 'Stellen Sie einen Zustand her, in dem der Cap greift und der SAFE nach Seed mehr als 9 % hält.', setup: () => ventInit(),
    check: (S, R) => { if (R.sim.error) return {done: false, progress: 0, msg: R.sim.error}; const sh = R.sim.stages[2].share.find(x => x[0] === 'SAFE')[1]; return {done: R.sim.r1.regime === 'cap' && sh > .09, progress: sh / .09, msg: `SAFE nach Seed ${pct(sh)} (${R.sim.r1.regime})`}; },
    hints: ['Der Anteil nach Seed = (A/C) × (1 − Seed-Anteil) × (Pool-Effekt).', 'Kleinerer Cap oder kleinerer Pool.'], success: 'Ein niedriger Cap legt den Anteil des Frühinvestors fest – Verwässerung durch die Preisrunde trifft ihn trotzdem (Leitfaden: „The safes are like their own round“).', links: {}},
  {id: 'w-fund', title: 'Den Fonds 3× zurückzahlen', level: 'mittel', goal: 'Erreichen Sie ein Netto-Multiple ≥ 3 mit höchstens einem Gewinner und Exitwert der übrigen = 0.', setup: S => { S.view = 'fund'; S.f.ew = 1e9; return S; },
    check: (S, R) => ({done: S.view === 'fund' && S.f.k <= 1 && S.f.er === 0 && R.fd.tvpi >= 3, progress: R.fd.tvpi / 3, msg: `Multiple ${f(R.fd.tvpi, 2)}×`}),
    hints: ['Netto = Brutto − 20 % des Gewinns über der Fondsgröße.', 'Brutto 3,5 × Fonds ergibt netto 3×.'], success: 'Für 3× netto braucht es brutto 350 Mio. € (Carry auf 250 Mio. Gewinn = 50 Mio.): bei 15 % Anteil ein Exit von ≈ 2,33 Mrd. €. Das ist die „Power-Law“-Logik in Zahlen.', links: {}},
  {id: 'w-imp', title: 'Mehr Anteil durch höheren Cap?', level: 'Transfer', goal: 'Ein Gründer möchte, dass der SAFE-Investor <em>weniger</em> erhält, und erhöht deshalb den Cap. Kann der Investor dadurch trotzdem mehr Anteile bekommen?', setup: () => ventInit(),
    check: () => ({done: false, progress: 0, msg: ''}),
    impossible: {q: 'Kann ein höherer Cap zu mehr SAFE-Anteilen führen?', options: ['Nein: Unter dem Cap sinkt der Anteil A/C; greift der Rabatt, hängt der Anteil nicht vom Cap ab. Der Investor erhält das Maximum beider – ein höherer Cap kann ihn nie besserstellen.', 'Ja, wenn der Rabatt hoch ist.', 'Ja, bei einer Down-Round.'], correct: 0,
      applies: () => true, notApplicable: '', why: {1: 'Der Rabattanteil ist unabhängig vom Cap; max(Cap-Anteil, Rabatt-Anteil) kann bei steigendem Cap nur fallen oder gleich bleiben.', 2: 'Auch dann: Der Cap-Anteil fällt mit C, der Rabattanteil ist von C unabhängig.'}},
    hints: ['Welche der beiden Varianten hängt vom Cap ab?'], success: 'Monotonie-Argument: Anteil = max(f_Cap(C), f_Rabatt), f_Cap fällt in C. Damit ist „höherer Cap“ für Gründer nie schlechter – aber oft wirkungslos, wenn der Rabatt greift.', links: {}},
];
