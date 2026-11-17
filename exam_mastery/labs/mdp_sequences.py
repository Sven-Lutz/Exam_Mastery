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
     'method': ['ausgearbeitetes Beispiel', 'teilweise ausgeblendetes Beispiel', 'selbstständige Rechnung', 'Transfer auf einen anderen Zustand'],
     'success': {'criterion': 'Schritte 2–4 ohne Lösungsanzeige korrekt (Toleranz ±0.005), höchstens zwei Hinweise insgesamt.', 'max_hints': 2},
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
     'success': {'criterion': 'Kipppunkt in γ auf ±0.01 gefunden, Belohnungsschwelle auf ±0.05, Vorhersage begründet.', 'max_hints': 3},
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
     'success': {'criterion': 'Beide Vorhersagen richtig oder nach höchstens einem Hinweis korrigiert; Verhältnis aus log-Schranke erklärt.', 'max_hints': 2},
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
const multi = m => m.S.filter(s => m.A[s].length > 1);
const focusS = m => multi(m).includes(st.focus) ? st.focus : multi(m)[0];
const otherS = m => multi(m).find(s => s !== focusS(m)) || m.S.find(s => m.A[s].length && s !== focusS(m)) || focusS(m);
const terms = (m, V, s, a) => { const t = m.T[s + '|' + a]; return Object.entries(t.next).map(([n, p]) => ({n, p, v: V[n]})); };
const errModels = (m, V, s, a) => { const t = m.T[s + '|' + a], T = terms(m, V, s, a), E = T.reduce((x, y) => x + y.p * y.v, 0);
  return {no_gamma: [t.r + E, 'Der Diskont γ fehlt: zukünftige Werte werden mit γ gewichtet.'],
          no_reward: [m.g * E, 'Die Sofortbelohnung r(s,a) fehlt.'],
          uniform_weights: [t.r + m.g * T.reduce((x, y) => x + y.v, 0) / T.length, 'Die Nachfolger wurden gleich gewichtet statt mit p(s′|s,a).'],
          max_successor: [t.r + m.g * Math.max(...T.map(y => y.v)), 'Es wurde der beste Nachfolger genommen; die Umwelt würfelt – also Erwartungswert über p(s′|s,a).']}; };
const qHints = (m, V, s, a) => { const t = m.T[s + '|' + a], T = terms(m, V, s, a);
  return {h_reward: `Sofortbelohnung: r(${label(s)},${a}) = ${fmt(t.r, 3)}.`,
          h_terms: 'Nachfolger: ' + T.map(y => `p = ${fmt(y.p, 2)} → V₁(${label(y.n)}) = ${fmt(y.v, 3)}`).join('; ') + '.',
          h_partial: `Erwartungswert Σ p·V₁ = ${fmt(T.reduce((x, y) => x + y.p * y.v, 0), 4)}; jetzt mit γ = ${fmt(m.g, 2)} multiplizieren und r addieren.`}; };
const RT = {
  show_backup: m => { const s = focusS(m), a = m.A[s][0], V = V1of(m); return {show: `<p>Zustand <b>${label(s)}</b>, Aktion <b>${a}</b>, Werte V₁:</p><div class="backup">${backupText(m, V, s, a)}</div>`}; },
  q_value: m => { const s = focusS(m), a = m.A[s][1], V = V1of(m); const em = errModels(m, V, s, a);
    return {truth: q(m, V, s, a), ask: `Q(${label(s)}, ${a}) mit V₁ = ?`, diag: em, hints: qHints(m, V, s, a), explain: `<div class="backup">${backupText(m, V, s, a)}</div>`}; },
  q_value_transfer: m => { const s = otherS(m), a = m.A[s][m.A[s].length - 1], V = V1of(m);
    return {truth: q(m, V, s, a), ask: `Q(${label(s)}, ${a}) mit V₁ = ?`, diag: errModels(m, V, s, a), hints: qHints(m, V, s, a), explain: `<div class="backup">${backupText(m, V, s, a)}</div>`}; },
  backup_max: m => { const s = focusS(m), V = V1of(m), Q = m.A[s].map(a => [a, q(m, V, s, a)]), best = Q.reduce((x, y) => y[1] > x[1] ? y : x);
    return {truth: best[1], ask: `V₂(${label(s)}) = ?`,
      diag: {mean_over_actions: [Q.reduce((x, y) => x + y[1], 0) / Q.length, 'Über Aktionen wird maximiert, nicht gemittelt – gemittelt wird nur unter einer festen stochastischen Policy.'],
             ...Object.fromEntries(Object.entries(errModels(m, V, s, best[0])).filter(([k]) => k !== 'uniform_weights' && k !== 'max_successor'))},
      hints: {h_all_q: 'Alle Q-Werte: ' + Q.map(([a, v]) => `Q(${a}) = ${fmt(v, 4)}`).join(', ') + '.', h_max: 'V₂ ist der größte dieser Werte.'},
      explain: `V₂(${label(s)}) = max(${Q.map(x => fmt(x[1], 4)).join(', ')}) = ${fmt(best[1], 4)}, gierige Aktion: <b>${best[0]}</b>.`}; },
  best_action_at: m => { const s = focusS(m), g = 0.1, mm = {...m, g}, o = optimal(mm), Q = m.A[s].map(a => [a, q(mm, o.V, s, a)]);
    return {choices: m.A[s], truth: o.pol[s], ask: `Optimale Aktion in ${label(s)} bei γ = 0.1?`,
      hints: {h_short: 'Bei kleinem γ zählt fast nur die Sofortbelohnung r(s,a).', h_compare: 'Vergleichen Sie r(s,a) der Aktionen: ' + m.A[s].map(a => `${a}: ${fmt(m.T[s + '|' + a].r, 2)}`).join(', ') + '.'},
      explain: `Bei γ = 0.1: ${Q.map(([a, v]) => `Q*(${label(s)},${a}) = ${fmt(v, 3)}`).join(', ')}. Optimal ist ${o.pol[s]}.`}; },
  gamma_threshold: m => { const s = focusS(m), at = g => optimal({...m, g}).pol[s]; let flip = null;
    for (let i = 1; i <= 98; i++) if (at((i - 1) / 100) !== at(i / 100)) { let a = (i - 1) / 100, b = i / 100; const pa = at(a);
      for (let j = 0; j < 40; j++) { const c = (a + b) / 2; if (at(c) === pa) a = c; else b = c; } flip = (a + b) / 2; break; }
    return {truth: flip, ask: `Kipppunkt γ in ${label(s)} = ?`, none: flip === null ? `In ${label(s)} ändert sich die optimale Aktion für γ ∈ [0, 0.98] nicht – wählen Sie einen anderen Zustand.` : null,
      hints: {h_sign: 'Links des Kipppunkts ist eine Aktion besser, rechts die andere: Beobachten Sie die gewählte Aktion beim Schieben.', h_bisect: flip === null ? '' : `Der Kipppunkt liegt zwischen ${fmt(Math.floor(flip * 100) / 100, 2)} und ${fmt(Math.ceil(flip * 100) / 100, 2)}.`},
      explain: flip === null ? '' : `Bei γ ≈ ${fmt(flip, 3)} sind ${at(flip - 0.005)} und ${at(flip + 0.005)} gleich gut: Größeres γ gewichtet die späteren Belohnungen stärker.`}; },
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
      hints: {h_log: 'Der Fehler schrumpft je Sweep um den Faktor γ: Für ε braucht man etwa log(1/ε)/log(1/γ) Sweeps.', h_rate: (() => { const d1 = norm(sweep(mm, zeros(mm)), zeros(mm)); return `Schranke für die Abbruchregel: k ≈ log(ε(1−γ) / (2γ·‖V₁−V₀‖)) / log γ mit ‖V₁−V₀‖ = ${fmt(d1, 3)} – setzen Sie beide ε ein; der Startterm ist nicht klein.`; })()},
      explain: `Gemessen: ${k2} Sweeps (ε = 10⁻²) gegen ${k6} Sweeps (ε = 10⁻⁶), Faktor ${fmt(r, 2)}. Die Sweeps wachsen linear in log(1/ε) – nicht in 1/ε.`}; },
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
  const input = step.kind === 'worked_example' ? r.show + '<div class="btns"><button class="b" id="sq-next">Verstanden – weiter</button></div>'
    : r.none ? `<p class="msg info">${r.none}</p>`
    : r.choices ? `<div class="opts" role="radiogroup">${r.choices.map(c => `<label><input type="radio" name="sqc" value="${c}"> ${c}</label>`).join('')}</div><div class="btns"><button class="b" id="sq-check">Prüfen</button>${hl.length ? '<button class="b alt" id="sq-hint">Hinweis</button>' : ''}</div>`
    : `${step.compute === 'gamma_threshold' ? `<label class="f">γ = <input type="range" min="0" max="0.98" step="0.005" value="${st.sqg ?? 0.5}" id="sq-g"><output>${fmt(st.sqg ?? 0.5, 3)}</output></label><p>Optimal in ${label(focusS(m))} bei diesem γ: <b>${optimal({...m, g: st.sqg ?? 0.5}).pol[focusS(m)]}</b></p>` : ''}<label class="f">${r.ask} <input id="sq-in" inputmode="decimal" size="10" aria-label="Antwort"></label><div class="btns"><button class="b" id="sq-check">Prüfen</button>${hl.length ? '<button class="b alt" id="sq-hint">Hinweis</button>' : ''}</div>`;
  const shown = hl.slice(0, p.shown[step.id] || 0).map(h => `<p class="msg info">Hinweis: ${r.hints[h]}</p>`).join('');
  return `<div class="grid2"><div class="card"><div class="btns">${S.map(x => `<button class="b ${x.id === sq.id ? '' : 'alt'}" data-seq="${x.id}">${x.id}: ${x.title}</button>`).join('')}</div>
  <h2>${sq.title}</h2><p><b>Lernziel:</b> ${sq.objective}</p><p><b>Vorkenntnisse:</b> ${sq.prerequisites.join(' · ')}</p><p><b>Problem:</b> ${sq.problem}</p>
  <p class="msg info"><b>Erfolgskriterium:</b> ${sq.success.criterion} <span id="sq-status">${done ? (p.hints <= sq.success.max_hints ? '– <b>erreicht</b>' : `– alle Schritte gelöst, aber ${p.hints} Hinweise (> ${sq.success.max_hints}): Sequenz später wiederholen.`) : ''}</span></p>
  <div class="steps4">${sq.steps.map((s, j) => `<span class="${j === p.i ? 'on' : ''}">${s.id}${p.solved[s.id] ? ' ✓' : ''}</span>`).join('')}</div>
  <h3>Schritt ${step.id}${step.kind === 'transfer' ? ' (Transfer)' : ''}</h3><p>${step.prompt}</p>${input}${shown}<div id="sq-fb">${p.fb}</div>
  <p class="sub">Methode: ${sq.method.join(' → ')}</p></div><div class="card">${draw(V1of(m), null, focusS(m))}<p class="sub">Markierter Zustand: ${label(focusS(m))} (im Graph wählbar). Gezeigt: V₁.</p></div></div>`; }
function seqCheck(m) {
  const sq = D.sequences.find(x => x.id === st.seq), p = st.sp[sq.id], step = sq.steps[p.i], r = RT[step.compute](m, step);
  let ok = false, why = '';
  if (r.choices) { const c = document.querySelector('input[name=sqc]:checked'); if (!c) return; ok = c.value === r.truth; why = ok ? '' : `Ihre Wahl: ${c.value}.`; }
  else { const x = parseNum($('sq-in').value); if (x === null) { p.fb = '<p class="msg bad">Bitte eine Zahl eingeben (Dezimalpunkt oder -komma).</p>'; render(); return; }
    ok = Math.abs(x - r.truth) <= step.tolerance;
    if (!ok) { const hit = Object.entries(r.diag || {}).find(([k, [v]]) => (step.diagnose || []).includes(k) && Math.abs(x - v) <= step.tolerance);
      why = hit ? `Diagnose: ${hit[1][1]}` : 'Kein typisches Fehlermuster erkannt – prüfen Sie die Rechnung Term für Term.'; } }
  if (ok) { p.solved[step.id] = true; p.fb = `<p class="msg ok">Richtig.</p><p>${r.explain}</p>${p.i + 1 < sq.steps.length ? '<div class="btns"><button class="b" id="sq-next">Weiter</button></div>' : ''}`; }
  else p.fb = `<p class="msg bad">Noch nicht. ${why}</p><p class="sub">Nutzen Sie einen Hinweis und rechnen Sie weiter – die Lösung wird nicht sofort gezeigt.</p>`;
  render(); }
"""
