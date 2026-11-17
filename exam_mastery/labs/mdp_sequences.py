"""B35 learning sequences for the MDP studio (any finite MDP scenario; no course-specific numbers).

Each sequence follows the task model (labs/task_model.py): objective, prerequisites, problem, observable success
criterion, guided -> independent -> transfer, every answer/feedback computed by the runtime functions in SEQ_JS from
the CURRENT model (edits in the model view change answers and explanations consistently).

Method labels name the instructional technique; claims about its effectiveness live in the lab learning-design
report with their evidence level, not in the UI.
"""

RUNTIME = {'show_backup', 'q_value', 'backup_max', 'best_action_at', 'gamma_threshold', 'reward_threshold',
           'vi_sweeps_ratio', 'pi_iters_eps', 'q_value_transfer'}

SEQUENCES = [
    {'id': 'A', 'title': 'Bellman-Backup verstehen und selbst rechnen',
     'objective': 'Einen Bellman-Backup Q(s,a) = r(s,a) + γ Σ p(s′|s,a) V(s′) und den Wertiterationsschritt Vₖ₊₁(s) = maxₐ Q(s,a) für ein gegebenes V selbst berechnen und jeden Term deuten.',
     'prerequisites': ['Erwartungswert einer diskreten Verteilung', 'Bedeutung von r(s,a), p(s′|s,a) und γ'],
     'problem': 'Gegeben sind das Modell und die Werte V₁ nach einem Sweep Wertiteration ab V₀ = 0. Wie entsteht daraus V₂ im markierten Zustand?',
     'method': ['ausgearbeitetes Beispiel', 'selbstständige Rechnung mit Hinweisleiter', 'Wertiterationsschritt', 'Transfer auf einen anderen Zustand'],
     'success': {'criterion': 'Schritte A2–A4 korrekt (Toleranz ±0.005), insgesamt höchstens zwei Hinweise und höchstens sechs Prüfversuche.', 'max_hints': 2, 'max_attempts': 6},
     'steps': [
         {'id': 'A1', 'kind': 'worked_example', 'compute': 'show_backup', 'prompt': 'Vollständig vorgerechnet: der Backup der ersten Aktion im markierten Zustand.'},
         {'id': 'A2', 'kind': 'numeric', 'compute': 'q_value', 'tolerance': 0.005, 'prompt': 'Berechnen Sie Q(s,a) für die zweite Aktion mit denselben Werten V₁.',
          'diagnose': ['no_gamma', 'no_reward', 'uniform_weights', 'max_successor'], 'hints': ['h_reward', 'h_terms', 'h_partial']},
         {'id': 'A3', 'kind': 'numeric', 'compute': 'backup_max', 'tolerance': 0.005, 'prompt': 'Berechnen Sie V₂(s) = max_a Q(s,a) im markierten Zustand.',
          'diagnose': ['mean_over_actions', 'no_gamma', 'no_reward'], 'hints': ['h_all_q', 'h_max']},
         {'id': 'A4', 'kind': 'transfer', 'compute': 'q_value_transfer', 'tolerance': 0.005, 'prompt': 'Transfer: Berechnen Sie Q(s,a) für einen anderen Zustand mit V₁.',
          'diagnose': ['no_gamma', 'no_reward', 'uniform_weights', 'max_successor'], 'hints': ['h_reward', 'h_terms']},
     ]},
    {'id': 'B', 'title': 'Wie γ, Belohnungen und Übergänge die optimale Policy bestimmen',
     'objective': 'Vorhersagen und begründen, wie sich die optimale Aktion in einem Zustand mit γ und einer Belohnung ändert, und den Kipppunkt aus dem Vergleich zweier Q*-Werte bestimmen.',
     'prerequisites': ['Bellman-Optimalitätsgleichung', 'Q*(s,a) und gierige Policy'],
     'problem': 'Im markierten Zustand konkurrieren zwei Aktionen. Bei welchem Diskont und bei welcher Belohnung kippt die Entscheidung?',
     'method': ['Vorhersage vor Rückmeldung', 'gezielte Exploration mit Zielwert', 'Begründung aus Q*-Differenz', 'Transfer auf eine geänderte Belohnung'],
     'success': {'criterion': 'Vorhersage B1, Kipppunkt in γ (±0.01) und Belohnungsschwelle (±0.05) gefunden, höchstens drei Hinweise und sechs Prüfversuche.', 'max_hints': 3, 'max_attempts': 6},
     'steps': [
         {'id': 'B1', 'kind': 'predict', 'compute': 'best_action_at', 'prompt': 'Vorhersage: Welche Aktion ist im markierten Zustand bei kleinem Diskont optimal?', 'hints': ['h_short', 'h_compare']},
         {'id': 'B2', 'kind': 'explore', 'compute': 'gamma_threshold', 'tolerance': 0.01, 'prompt': 'Verschieben Sie γ, bis beide Aktionen gleich gut sind, und geben Sie den Kipppunkt ein.', 'hints': ['h_sign', 'h_bisect']},
         {'id': 'B3', 'kind': 'transfer', 'compute': 'reward_threshold', 'tolerance': 0.05, 'prompt': 'Transfer: Ab welcher Belohnung der unterlegenen Aktion wird sie (beim aktuellen γ) optimal?', 'hints': ['h_linear', 'h_bisect']},
     ]},
    {'id': 'C', 'title': 'Wertiteration und Policy Iteration unter klaren Bedingungen vergleichen',
     'objective': 'Iterationszahl, Kosten je Iteration und erreichte Genauigkeit beider Verfahren trennen und vorhersagen, wie eine strengere Genauigkeitsforderung jedes Verfahren beeinflusst.',
     'prerequisites': ['Kontraktion mit Rate γ', 'Abbruchregel der Wertiteration', 'Policy Iteration endet nach endlich vielen Schritten'],
     'problem': 'Die Genauigkeitsforderung wird von ε = 10⁻² auf ε = 10⁻⁶ verschärft. Was passiert mit den Sweeps der Wertiteration und den Iterationen der Policy Iteration?',
     'method': ['Vorhersage vor Rückmeldung', 'Erklärung aus der Kontraktionsschranke', 'Transfer auf anderes γ'],
     'success': {'criterion': 'Alle drei Vorhersagen richtig, höchstens zwei Hinweise und höchstens fünf Prüfversuche (Raten über alle Optionen verfehlt das Kriterium).', 'max_hints': 2, 'max_attempts': 5},
     'steps': [
         {'id': 'C1', 'kind': 'predict', 'compute': 'vi_sweeps_ratio', 'prompt': 'Um welchen Faktor wachsen die VI-Sweeps etwa?', 'hints': ['h_log', 'h_rate']},
         {'id': 'C2', 'kind': 'predict', 'compute': 'pi_iters_eps', 'prompt': 'Was passiert mit der Zahl der Policy-Iterationen?', 'hints': ['h_exact', 'h_finite']},
         {'id': 'C3', 'kind': 'transfer', 'compute': 'vi_sweeps_ratio', 'transfer': True, 'gamma': 0.99, 'prompt': 'Transfer: Dieselbe Frage bei γ = 0.99.', 'hints': ['h_log', 'h_rate']},
     ]},
]

SEQ_JS = r"""
/* ---------- B35 learning sequences: every truth, hint and explanation is computed from the current model ---------- */
const parseNum = x => { const t = String(x || '').trim().replace(/\s/g, '').replace(/,(?=\d+$)/, '.'); return t === '' || isNaN(+t) ? null : +t; };
const V1of = m => sweep(m, zeros(m));
const V2of = m => sweep(m, sweep(m, zeros(m)));
const TOL = 0.005;
// B35 review: a step is only usable if the truth is clearly separated from every error model (>= 3 x tolerance);
// otherwise a wrong method would be graded 'right'. Candidates: every (state, action, V1|V2), best separation wins.
const sep = (m, V, s, a) => { const t = q(m, V, s, a); return Math.min(...Object.values(errModels(m, V, s, a)).map(([v]) => Math.abs(v - t))); };
const pickQ = (m, skip) => { let best = null;
  for (const [nm, V] of [['V₁', V1of(m)], ['V₂', V2of(m)]]) for (const s of m.S) for (const a of m.A[s]) { if (skip && skip(s, a)) continue;
    const d = sep(m, V, s, a); if (!best || d > best.d + 1e-12) best = {s, a, V, nm, d}; } return best && best.d >= 3 * TOL ? best : null; };
const uniqDiag = (truth, diag) => Object.fromEntries(Object.entries(diag).filter(([k, [v]]) => Math.abs(v - truth) > 2 * TOL &&
  Object.entries(diag).every(([k2, [v2]]) => k2 === k || Math.abs(v2 - v) > 2 * TOL)));
const multi = m => m.S.filter(s => m.A[s].length > 1);
const focusS = m => multi(m).includes(st.focus) ? st.focus : (multi(m)[0] || m.S.find(s => m.A[s].length));
const otherS = m => multi(m).find(s => s !== focusS(m)) || m.S.find(s => m.A[s].length && s !== focusS(m)) || focusS(m);
const terms = (m, V, s, a) => { const t = m.T[s + '|' + a]; return Object.entries(t.next).map(([n, p]) => ({n, p, v: V[n]})); };
const errModels = (m, V, s, a) => { const t = m.T[s + '|' + a], T = terms(m, V, s, a), E = T.reduce((x, y) => x + y.p * y.v, 0);
  return {no_gamma: [t.r + E, 'Der Diskont γ fehlt: zukünftige Werte werden mit γ gewichtet.'],
          no_reward: [m.g * E, 'Die Sofortbelohnung r(s,a) fehlt.'],
          uniform_weights: [t.r + m.g * T.reduce((x, y) => x + y.v, 0) / T.length, 'Die Nachfolger wurden gleich gewichtet statt mit p(s′|s,a).'],
          max_successor: [t.r + m.g * Math.max(...T.map(y => y.v)), 'Es wurde der beste Nachfolger genommen; die Umwelt würfelt – also Erwartungswert über p(s′|s,a).']}; };
const qHints = (m, V, s, a, nm = 'V₁') => { const t = m.T[s + '|' + a], T = terms(m, V, s, a);
  return {h_reward: `Sofortbelohnung: r(${label(s)},${a}) = ${fmt(t.r, 3)}.`,
          h_terms: 'Nachfolger: ' + T.map(y => `p = ${fmt(y.p, 2)} → ${nm}(${label(y.n)}) = ${fmt(y.v, 3)}`).join('; ') + '.',
          h_partial: `Erwartungswert Σ p·${nm} = ${fmt(T.reduce((x, y) => x + y.p * y.v, 0), 4)}; jetzt mit γ = ${fmt(m.g, 2)} multiplizieren und r addieren.`}; };
const RT = {
  show_backup: m => { const s = focusS(m), a = m.A[s][0], V = V1of(m); return {show: `<p>Zustand <b>${label(s)}</b>, Aktion <b>${a}</b>, Werte V₁:</p><div class="backup">${backupText(m, V, s, a)}</div>`}; },
  q_value: m => { const b = pickQ(m); if (!b) return {none: 'Dieses Modell trennt richtige und typische falsche Rechnungen nicht deutlich genug – wählen Sie ein anderes Szenario.'};
    st.seqA = b; const t = q(m, b.V, b.s, b.a);
    return {truth: t, ask: `Q(${label(b.s)}, ${b.a}) mit ${b.nm} = ?`, diag: uniqDiag(t, errModels(m, b.V, b.s, b.a)), hints: qHints(m, b.V, b.s, b.a, b.nm),
      explain: `<div class="backup">${backupText(m, b.V, b.s, b.a)}</div>`}; },
  q_value_transfer: m => { const a0 = st.seqA; const b = pickQ(m, (s, a) => a0 && s === a0.s); if (!b) return {none: 'Kein zweiter Zustand mit eindeutig prüfbarer Rechnung.'};
    const t = q(m, b.V, b.s, b.a);
    return {truth: t, ask: `Q(${label(b.s)}, ${b.a}) mit ${b.nm} = ?`, diag: uniqDiag(t, errModels(m, b.V, b.s, b.a)), hints: qHints(m, b.V, b.s, b.a, b.nm),
      explain: `<div class="backup">${backupText(m, b.V, b.s, b.a)}</div>`}; },
  backup_max: m => { const s = (st.seqA || pickQ(m) || {s: focusS(m)}).s, V = (st.seqA || {}).V || V1of(m), nm = (st.seqA || {}).nm || 'V₁';
    const Q = m.A[s].map(a => [a, q(m, V, s, a)]), best = Q.reduce((x, y) => y[1] > x[1] ? y : x), t = best[1];
    const diag = {mean_over_actions: [Q.reduce((x, y) => x + y[1], 0) / Q.length, 'Über Aktionen wird maximiert, nicht gemittelt – gemittelt wird nur unter einer festen stochastischen Policy.'],
                  ...Object.fromEntries(Object.entries(errModels(m, V, s, best[0])).filter(([k]) => k === 'no_gamma' || k === 'no_reward'))};
    return {truth: t, ask: `Nächster Wert in ${label(s)}: max_a Q(${label(s)}, a) mit ${nm} = ?`, diag: uniqDiag(t, diag),
      hints: {h_all_q: 'Alle Q-Werte: ' + Q.map(([a, v]) => `Q(${a}) = ${fmt(v, 4)}`).join(', ') + '.', h_max: 'Gesucht ist der größte dieser Werte.'},
      explain: `max(${Q.map(x => fmt(x[1], 4)).join(', ')}) = ${fmt(t, 4)}, gierige Aktion: <b>${best[0]}</b>.`}; },
  best_action_at: m => { const g = 0.1, mm = {...m, g}, o = optimal(mm);
    const gap = s => { const Q = m.A[s].map(a => q(mm, o.V, s, a)).sort((x, y) => y - x); return Q.length > 1 ? Q[0] - Q[1] : 0; };
    const s = multi(m).reduce((x, y) => (x === null || gap(y) > gap(x) ? y : x), null);
    if (s === null || gap(s) < 1e-6) return {none: 'Bei γ = 0.1 hat kein Zustand eine eindeutig beste Aktion (Gleichstand) – Vorhersage hier nicht sinnvoll.'};
    st.seqB = s; const Q = m.A[s].map(a => [a, q(mm, o.V, s, a)]), best = Q.reduce((x, y) => y[1] > x[1] ? y : x)[0];
    return {choices: m.A[s], truth: best, ask: `Optimale Aktion in ${label(s)} bei γ = 0.1?`,
      hints: {h_short: 'Bei kleinem γ zählt fast nur, was in den nächsten ein, zwei Schritten passiert.', h_compare: 'Q*-Werte bei γ = 0.1 stehen in der Erklärung nach der Prüfung; vergleichen Sie vorher r(s,a) und die direkten Nachfolger.'},
      explain: `Bei γ = 0.1: ${Q.map(([a, v]) => `Q*(${label(s)},${a}) = ${fmt(v, 4)}`).join(', ')}. Optimal ist ${best}.`}; },
  gamma_threshold: m => {
    const strict = (s, g) => { const mm = {...m, g}, o = optimal(mm), Q = m.A[s].map(a => [a, q(mm, o.V, s, a)]).sort((x, y) => y[1] - x[1]);
      return Q.length > 1 && Q[0][1] - Q[1][1] > 1e-7 ? Q[0][0] : null; };
    const flipIn = s => { let prev = null, pg = null;
      for (let i = 0; i <= 98; i++) { const g = i / 100, b = strict(s, g); if (b === null) continue;
        if (prev !== null && b !== prev) { let lo = pg, hi = g; for (let j = 0; j < 40; j++) { const c = (lo + hi) / 2, x = strict(s, c); if (x === prev) lo = c; else hi = c; } return {g: (lo + hi) / 2, from: prev, to: b}; }
        prev = b; pg = g; } return null; };
    const cand = [st.seqB, ...multi(m)].filter(Boolean); let s = null, f = null;
    for (const x of cand) { f = flipIn(x); if (f) { s = x; break; } }
    if (!f) return {none: 'In keinem Zustand kippt die beste Aktion für γ ∈ [0, 0.98] (strikt, ohne Gleichstände) – wählen Sie ein anderes Szenario.'};
    return {truth: f.g, ask: `Kipppunkt γ in ${label(s)} (zwischen ${f.from} und ${f.to}) = ?`, state: s,
      hints: {h_sign: `Links des Kipppunkts ist ${f.from} strikt besser, rechts ${f.to}: Beobachten Sie die angezeigte beste Aktion beim Schieben.`, h_bisect: 'Halbieren Sie das Intervall, in dem die angezeigte Aktion wechselt, bis es kürzer als 0.01 ist.'},
      explain: `Bei γ ≈ ${fmt(f.g, 3)} sind ${f.from} und ${f.to} gleich gut: Größeres γ gewichtet spätere Belohnungen stärker.`}; },
  reward_threshold: m => { const s = focusS(m), o = optimal(m), alt = m.A[s].find(a => a !== o.pol[s]), key = s + '|' + alt, r0 = m.T[key].r;
    const at = r => { const T2 = {...m.T, [key]: {...m.T[key], r}}; return optimal({...m, T: T2}).pol[s] === alt; };
    let a = r0, b = r0 + 1; while (!at(b) && b < r0 + 200) b += Math.max(1, b - r0);
    for (let j = 0; j < 50; j++) { const c = (a + b) / 2; if (at(c)) b = c; else a = c; }
    return {truth: b, ask: `Ab welcher Belohnung r(${label(s)},${alt}) wird ${alt} optimal (γ = ${fmt(m.g, 2)})?`,
      hints: {h_linear: `Erhöhen Sie r(${label(s)},${alt}) gedanklich: Q*(${label(s)},${alt}) wächst mindestens um denselben Betrag.`, h_bisect: `Aktuell: r = ${fmt(r0, 2)}; die Schwelle liegt zwischen ${fmt(Math.floor(b), 0)} und ${fmt(Math.ceil(b), 0)}.`},
      explain: `Ab r ≈ ${fmt(b, 3)} ist Q*(${label(s)},${alt}) mindestens so groß wie Q* der bisherigen Aktion ${o.pol[s]}.`}; },
  vi_sweeps_ratio: (m, step) => { const g = step && step.gamma ? step.gamma : m.g, mm = {...m, g};
    const sweeps = eps => { const thr = eps * (1 - g) / (2 * g); let V = zeros(mm), d = Infinity, k = 0; while (d >= thr && k < 20000) { const W = sweep(mm, V); d = norm(W, V); V = W; k++; } return k; };
    const k2 = sweeps(1e-2), k6 = sweeps(1e-6), r = k6 / k2, bins = ['etwa gleich (× 1)', 'etwa × 2', 'etwa × 3', 'mehr als × 4'];
    const truth = r < 1.4 ? bins[0] : r < 2.5 ? bins[1] : r < 3.6 ? bins[2] : bins[3];
    return {choices: bins, truth, ask: `γ = ${fmt(g, 2)}: Sweeps bei ε = 10⁻⁶ im Verhältnis zu ε = 10⁻²?`,
      hints: {h_log: 'Der Abstand ‖V_{k+1} − V_k‖ schrumpft je Sweep mindestens um den Faktor γ; die Abbruchschwelle ist ε(1−γ)/(2γ) – die Sweep-Zahl ist also affin (nicht proportional) in log(1/ε).', h_rate: (() => { const d1 = norm(sweep(mm, zeros(mm)), zeros(mm)); return `Schranke für die Abbruchregel: k ≈ log(ε(1−γ) / (2γ·‖V₁−V₀‖)) / log γ mit ‖V₁−V₀‖ = ${fmt(d1, 3)} – setzen Sie beide ε ein; der Startterm ist nicht klein.`; })()},
      explain: `Gemessen: ${k2} Sweeps (ε = 10⁻²) gegen ${k6} Sweeps (ε = 10⁻⁶), Faktor ${fmt(r, 2)}. Die Sweeps wachsen affin in log(1/ε) – ein fester Anteil kommt vom Startabstand und von (1−γ)/(2γ).`}; },
  pi_iters_eps: m => { let pol = {...st.policy}, it = 0; while (it < 100) { const V = evaluate(m, pol); it++; const np = greedy(m, V, pol); if (m.S.every(s => !m.A[s].length || np[s] === pol[s])) break; pol = np; }
    const ch = ['bleibt gleich', 'wächst etwas', 'wächst stark'];
    return {choices: ch, truth: ch[0], ask: 'Policy Iteration bei ε = 10⁻⁶ statt 10⁻²?',
      hints: {h_exact: 'Policy Iteration bewertet jede Policy exakt (Gleichungssystem) – ε kommt im Verfahren gar nicht vor.', h_finite: 'Sie stoppt, wenn sich die Policy nicht mehr ändert; das hängt nicht von ε ab.'},
      explain: `Policy Iteration endet hier nach ${it} Iterationen – unabhängig von ε, weil jede Bewertung exakt ist (bis auf Rundung).`}; },
};
function seqView(m) {
  const S = (D.sequences || []); if (!S.length) return '<div class="card">Keine Lernsequenzen.</div>';
  const sq = S.find(x => x.id === st.seq) || S[0]; st.seq = sq.id; const sp = st.sp = st.sp || {}; const p = sp[sq.id] = sp[sq.id] || {i: 0, hints: 0, solved: {}, shown: {}, fb: ''};
  const step = sq.steps[p.i], r = RT[step.compute](m, step), hl = Object.keys(r.hints || {}).filter(h => (step.hints || []).includes(h));
  const done = sq.steps.every(s => s.kind === 'worked_example' || p.solved[s.id]);
  if (r.none && step.kind !== 'worked_example') p.solved[step.id] = p.solved[step.id] || false;
  const input = step.kind === 'worked_example' ? r.show + '<div class="btns"><button class="b" id="sq-next">Verstanden – weiter</button></div>'
    : r.none ? `<p class="msg info">${r.none}</p>`
    : r.choices ? `<div class="opts" role="radiogroup">${r.choices.map(c => `<label><input type="radio" name="sqc" value="${c}"> ${c}</label>`).join('')}</div><div class="btns"><button class="b" id="sq-check">Prüfen</button>${hl.length ? '<button class="b alt" id="sq-hint">Hinweis</button>' : ''}</div>`
    : `${step.compute === 'gamma_threshold' ? `<label class="f">γ = <input type="range" min="0" max="0.98" step="0.005" value="${st.sqg ?? 0.5}" id="sq-g"><output>${fmt(st.sqg ?? 0.5, 3)}</output></label><p>Beste Aktion in ${label(r.state)} bei diesem γ: <b>${optimal({...m, g: st.sqg ?? 0.5}).pol[r.state]}</b></p>` : ''}<label class="f">${r.ask} <input id="sq-in" inputmode="decimal" size="10" aria-label="Antwort"></label><div class="btns"><button class="b" id="sq-check">Prüfen</button>${hl.length ? '<button class="b alt" id="sq-hint">Hinweis</button>' : ''}</div>`;
  const shown = hl.slice(0, p.shown[step.id] || 0).map(h => `<p class="msg info">Hinweis: ${r.hints[h]}</p>`).join('');
  return `<div class="grid2"><div class="card"><div class="btns">${S.map(x => `<button class="b ${x.id === sq.id ? '' : 'alt'}" data-seq="${x.id}">${x.id}: ${x.title}</button>`).join('')}</div>
  <h2>${sq.title}</h2><p><b>Lernziel:</b> ${sq.objective}</p><p><b>Vorkenntnisse:</b> ${sq.prerequisites.join(' · ')}</p><p><b>Problem:</b> ${sq.problem}</p>
  <p class="msg info"><b>Erfolgskriterium:</b> ${sq.success.criterion} <span id="sq-status">${done ? (p.hints <= sq.success.max_hints && (p.attempts || 0) <= (sq.success.max_attempts || 99) ? '– <b>erreicht</b>' : `– alle Schritte gelöst, aber ${p.hints} Hinweise / ${p.attempts || 0} Versuche (Grenzen ${sq.success.max_hints} / ${sq.success.max_attempts}): Sequenz später wiederholen.`) : ''}</span></p>
  <div class="steps4">${sq.steps.map((s, j) => `<span class="${j === p.i ? 'on' : ''}">${s.id}${p.solved[s.id] ? ' ✓' : ''}</span>`).join('')}</div>
  <h3>Schritt ${step.id}${step.kind === 'transfer' ? ' (Transfer)' : ''}</h3><p>${step.prompt}</p>${input}${shown}<div id="sq-fb">${p.fb}</div>
  <p class="sub">Methode: ${sq.method.join(' → ')}</p></div><div class="card">${draw(V1of(m), null, focusS(m))}<p class="sub">Markierter Zustand: ${label(focusS(m))} (im Graph wählbar). Gezeigt: V₁.</p></div></div>`; }
function seqCheck(m) {
  const sq = D.sequences.find(x => x.id === st.seq), p = st.sp[sq.id], step = sq.steps[p.i], r = RT[step.compute](m, step);
  let ok = false, why = ''; p.attempts = (p.attempts || 0) + 1;
  if (r.choices) { const c = document.querySelector('input[name=sqc]:checked'); if (!c) return; ok = c.value === r.truth; why = ok ? '' : `Ihre Wahl: ${c.value}.`; }
  else { const x = parseNum($('sq-in').value); if (x === null) { p.fb = '<p class="msg bad">Bitte eine Zahl eingeben (Dezimalpunkt oder -komma).</p>'; render(); return; }
    ok = Math.abs(x - r.truth) <= step.tolerance;
    if (!ok) { const hit = Object.entries(r.diag || {}).find(([k, [v]]) => (step.diagnose || []).includes(k) && Math.abs(x - v) <= step.tolerance);
      why = hit ? `Diagnose: ${hit[1][1]}` : 'Kein typisches Fehlermuster erkannt – prüfen Sie die Rechnung Term für Term.'; } }
  if (ok) { p.solved[step.id] = true; p.fb = `<p class="msg ok">Richtig.</p><p>${r.explain}</p>${p.i + 1 < sq.steps.length ? '<div class="btns"><button class="b" id="sq-next">Weiter</button></div>' : ''}`; }
  else p.fb = `<p class="msg bad">Noch nicht. ${why}</p><p class="sub">Nutzen Sie einen Hinweis und rechnen Sie weiter – die Lösung wird nicht sofort gezeigt.</p>`;
  render(); }
"""
