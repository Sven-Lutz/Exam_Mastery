"""B21: interactive lab for any finite Markov decision process given by a course (generic, not tied to one subject).

The author role passes the MDP exactly as the sources define it (states, actions, p(s'|s,a), r(s,a), gamma, a policy
to evaluate). Every number of the lab (tasks, missions, prediction, figure) is computed here with labs/models.py; the
browser mirrors the same model (templates/em_labs.js, EM.models.mdp*) and is tested against it.
"""
import math
from html import escape as E

from . import models as M


class MdpError(ValueError):
    pass


def _f(x, d=2):
    s = f'{x:,.{d}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return '0' + s[2:] if s.startswith('-0') and float(x) == 0 else s


def model(spec, gamma=None, policy=None):
    m = spec['model']
    return M.mdp_check({**m['mdp'], 'gamma': m['mdp']['gamma'] if gamma is None else gamma}), dict(policy or m['policy'])


def decision_states(mdp):
    return [s for s in mdp['states'] if len(mdp['actions'][s]) >= 2]


def policy_from_params(spec, params):
    m = spec['model']; pol = dict(m['policy'])
    for i, s in enumerate(m['decision_states']):
        if f'pi{i}' in params:
            pol[s] = params[f'pi{i}']
    return pol


def metrics(spec, params):
    """Same names as the data-* attributes the browser view writes (lab.dataset.*)."""
    mm, _ = model(spec, float(params['gamma']))
    pol = policy_from_params(spec, params); f = spec['model']['focus']
    vpi = M.mdp_eval_exact(mm, pol); vstar = M.mdp_optimal(mm)
    k = int(params.get('k', 0))
    hist = M.mdp_eval_sweeps(mm, pol, k) if params.get('mode', 'eval') == 'eval' else M.mdp_value_iteration(mm, k)
    target = vpi if params.get('mode', 'eval') == 'eval' else vstar
    greedy = M.mdp_greedy(mm, vpi)
    nong = sum(1 for s in greedy if abs(M.mdp_q(mm, vpi, s, greedy[s]) - M.mdp_q(mm, vpi, s, pol[s])) > 1e-9)
    opt = M.mdp_greedy(mm, vstar)
    return {'vpi': vpi[f], 'vstar': vstar[f], 'err': max(abs(hist[-1][s] - target[s]) for s in mm['states']),
            'nonGreedy': nong, 'optSig': '|'.join(opt[s] for s in mm['states'] if s in opt), 'k': k}


def _layout(states):
    n = len(states)
    if n == 1:
        return {states[0]: [320, 150]}
    if n == 2:
        return {states[0]: [170, 150], states[1]: [470, 150]}
    return {s: [round(320 + 230 * math.cos(2 * math.pi * i / n - math.pi), 1), round(150 + 105 * math.sin(2 * math.pi * i / n - math.pi), 1)]
            for i, s in enumerate(states)}


def _vstr(V, states, d=2):
    return ', '.join(f'V({s}) = {_f(V[s], d)}' for s in states)


def spec(lab_id, title, kc_ids, sources, data, course='', unit=''):
    """data: {"states":[...], "transitions":[{"s","a","r","next":{s': p}}], "gamma", "policy":{s: a}, "focus": s,
    "labels": {s: long name} (optional)}. All values exactly from the cited sources."""
    try:
        mm = M.mdp_check(data)
    except (KeyError, TypeError, ValueError) as e:
        raise MdpError(f'MDP data invalid: {e}')
    S = mm['states']; pol = dict(data.get('policy') or {})
    for s in S:
        if mm['actions'][s] and pol.get(s) not in mm['actions'][s]:
            raise MdpError(f'policy must choose an available action in state {s}')
    if len(S) > 8:
        raise MdpError('the interactive MDP lab shows at most 8 states')
    dec = decision_states(mm)
    if not dec:
        raise MdpError('the MDP needs at least one state with a choice of actions')
    focus = data.get('focus') if data.get('focus') in S else dec[0]
    g0 = mm['gamma']
    m = {'kind': 'mdp', 'mdp': {'states': S, 'gamma': g0, 'transitions': [dict(t, r=float(t['r'])) for t in data['transitions']]},
         'policy': {s: pol[s] for s in S if mm['actions'][s]}, 'focus': focus, 'decision_states': dec, 'unit': unit,
         'labels': data.get('labels') or {}, 'layout': _layout(S),
         'equations': ['V^π(s) = Σ_a π(a|s) [ r(s,a) + γ Σ_{s′} p(s′|s,a) V^π(s′) ]   (Bellman-Erwartungsgleichung)',
                       'V*(s) = max_a [ r(s,a) + γ Σ_{s′} p(s′|s,a) V*(s′) ]   (Bellman-Optimalitätsgleichung)',
                       'V_{k+1} = T V_k  (synchron: alle Zustände aus V_k);  ‖T U − T V‖_∞ ≤ γ ‖U − V‖_∞',
                       'Q^π(s,a) = r(s,a) + γ Σ_{s′} p(s′|s,a) V^π(s′);  π_neu(s) = argmax_a Q^π(s,a)']}
    params = [{'id': 'gamma', 'label': 'Diskontfaktor γ', 'type': 'range', 'min': 0, 'max': 0.99, 'step': 0.01, 'default': g0, 'digits': 2},
              {'id': 'mode', 'label': 'Verfahren', 'type': 'select', 'default': 'eval',
               'options': [{'value': 'eval', 'label': 'Policy-Bewertung (feste Policy π)'}, {'value': 'opt', 'label': 'Wertiteration (max über Aktionen)'}]},
              {'id': 'k', 'label': 'Anzahl Sweeps k', 'type': 'range', 'min': 0, 'max': 200, 'step': 1, 'default': 0, 'digits': 0}]
    for i, s in enumerate(dec):
        params.append({'id': f'pi{i}', 'label': f'Policy in {s}', 'type': 'select', 'default': pol[s],
                       'options': [{'value': a, 'label': a} for a in mm['actions'][s]]})
    sp = {'schema': 'em-lab-v1', 'id': lab_id, 'version': 1, 'title': title, 'domain': 'decision-making', 'course': course,
          'kc_ids': list(kc_ids), 'model': m, 'params': params,
          'objective': 'Sie können für ein endliches MDP einen Bellman-Backup Term für Term berechnen, Policy-Bewertung und '
                       'Wertiteration ausführen und begründen, warum beide konvergieren, und aus Q-Werten eine bessere Policy ableiten.',
          'prerequisites': ['Erwartungswert einer diskreten Verteilung', 'diskontierter Return G_t = Σ γ^k r_{t+k}', 'Policy π(a|s)'],
          'assumptions': ['Endliches MDP mit bekannten Übergangswahrscheinlichkeiten p(s′|s,a) und erwarteter Belohnung r(s,a) (Planung, kein Lernen aus Daten).',
                          'Zustände ohne Aktion sind terminal und haben den Wert 0.',
                          'Synchrone Sweeps: V_{k+1} wird vollständig aus V_k berechnet; Startwert V_0 = 0.',
                          'Alle Zahlen berechnet das Referenzmodell der Engine; Werte in der Ansicht sind auf zwei Nachkommastellen gerundet.'],
          'sources': list(sources) + ['Referenzmodell: exam_mastery/labs/models.py (mdp_*)',
                                      'Bellman (1957), Dynamic Programming; Puterman (1994), Markov Decision Processes, Kap. 6; Sutton & Barto (2018), Kap. 4'],
          'explanations': ['Die Bellman-Erwartungsgleichung beschreibt eine feste Policy; die Optimalitätsgleichung ersetzt den Mittelwert über π(a|s) durch das Maximum über Aktionen.',
                           'Weil der Bellman-Operator bezüglich der Maximumsnorm eine γ-Kontraktion ist, nähern sich alle Startwerte demselben Fixpunkt; der Fehler schrumpft je Sweep mindestens um den Faktor γ.']}
    seq = _sequence(sp, mm); seq['_explore'] = seq.pop('explore'); seq['_choice'] = seq.pop('choice')
    sp['sequence'] = seq
    sp['tests'] = _tests(sp)
    return sp


def _tests(sp):
    d0 = {p['id']: p['default'] for p in sp['params']}
    mm, pol = model(sp)
    return [{'params': d0, 'vpi': M.mdp_eval_exact(mm, pol), 'vstar': M.mdp_optimal(mm),
             'vi3': M.mdp_value_iteration(mm, 3)[3], 'pe2': M.mdp_eval_sweeps(mm, pol, 2)[2]}]


def _distinct(expected, cands, tol):
    out, seen = [], [expected]
    for v, msg in cands:
        if v is None or not math.isfinite(v) or any(abs(v - w) <= 2 * tol for w in seen):
            continue
        out.append({'value': round(v, 6), 'message': msg}); seen.append(v)
    return out


def _sequence(sp, mm):
    m = sp['model']; S = mm['states']; f = m['focus']; pol = m['policy']; g = mm['gamma']; tol = 0.006
    a = pol[f]; r, nxt = mm['T'][(f, a)]
    # task 1: one synchronous policy-evaluation backup at the focus state, from V_1
    h = M.mdp_eval_sweeps(mm, pol, 2); V1, V2 = h[1], h[2]
    if all(abs(V1[s]) < 1e-12 for s in S):
        h = M.mdp_eval_sweeps(mm, pol, 3); V1, V2 = h[2], h[3]; kk = 2
    else:
        kk = 1
    exp1 = V2[f]
    vi_val = max(M.mdp_q(mm, V1, f, b) for b in mm['actions'][f])
    terms = M.mdp_backup_terms(mm, V1, f, a)['terms']
    nos = r + sum(p * V1[t] for t, p in nxt.items())
    unw = r + g * sum(V1[t] for t in nxt) / len(nxt)
    t1 = {'id': 'backup', 'title': 'Ein Bellman-Backup Term für Term',
          'prompt': f'Policy-Bewertung für π mit γ = {_f(g)}. Nach {kk} Sweep(s) gilt {_vstr(V1, S)}. '
                    f'Berechnen Sie V_{kk + 1}({f}) für die Aktion π({f}) = {a} (2 Nachkommastellen).',
          'expected': round(exp1, 6), 'tolerance': tol, 'unit': m['unit'],
          'errors': _distinct(exp1, [(nos, 'Der Diskontfaktor γ fehlt: Der Wert des Folgezustands zählt nur mit γ.'),
                                      (unw, 'Die Folgezustände wurden gleich gewichtet. Jeder Term wird mit seiner Wahrscheinlichkeit p(s′|s,a) gewichtet.'),
                                      (vi_val, 'Das ist das Maximum über alle Aktionen (Wertiteration). Bei der Policy-Bewertung zählt nur die Aktion der Policy.'),
                                      (V1[f], f'Das ist der alte Wert V_{kk}({f}). Gefragt ist das Ergebnis des nächsten Sweeps.'),
                                      (g * sum(p * V1[t] for t, p in nxt.items()), 'Die unmittelbare Belohnung r(s,a) fehlt.')], tol),
          'hints': [f'V_{kk + 1}({f}) = r({f},{a}) + γ · Σ p(s′|{f},{a}) · V_{kk}(s′).',
                    'Folgezustände: ' + '; '.join(f'p({t}|{f},{a}) = {_f(p)}' for t, p in nxt.items()) + f'; r({f},{a}) = {_f(r)}.',
                    'Terme p · (r + γ V): ' + ' + '.join(f'{_f(x["p"])} · ({_f(r)} + {_f(g)} · {_f(x["v_next"])})' for x in terms) + '.'],
          'solution': [' + '.join(f'{_f(x["p"])} · ({_f(r)} + {_f(g)} · {_f(x["v_next"])})' for x in terms) + f' = {_f(exp1, 3)}.',
                       'Weil sich die Wahrscheinlichkeiten zu 1 addieren, ist das dasselbe wie r + γ · Σ p · V(s′).'],
          'feedback_correct': 'Genau: Ein Backup ist ein Erwartungswert über die Folgezustände, jeder Term mit p gewichtet und mit γ diskontiert.'}
    # task 2: exact value from the linear system
    vpi = M.mdp_eval_exact(mm, pol); k10 = M.mdp_eval_sweeps(mm, pol, 10)[10]
    naive = r / (1 - g) if abs(1 - g) > 1e-9 else None
    t2 = {'id': 'exact', 'title': 'Exakter Wert der Policy',
          'prompt': f'Stellen Sie für π die Bellman-Gleichungen aller Zustände auf (γ = {_f(g)}) und lösen Sie das lineare Gleichungssystem. Wie groß ist V^π({f})?',
          'expected': round(vpi[f], 6), 'tolerance': 0.011, 'unit': m['unit'],
          'errors': _distinct(vpi[f], [(k10[f], 'Das ist der Wert nach 10 Sweeps. Iterieren nähert V^π nur an; das Gleichungssystem liefert den Fixpunkt exakt.'),
                                       (naive, f'r/(1 − γ) gilt nur, wenn man in {f} für immer dieselbe Belohnung erhält. Hier wechselt der Zustand.')], 0.011),
          'hints': ['Für jeden nicht-terminalen Zustand s: V(s) = r(s,π(s)) + γ Σ p(s′|s,π(s)) V(s′).',
                    'Bringen Sie alle V-Terme auf eine Seite: (I − γ P^π) V = r^π.',
                    'Lösen Sie nach V(' + f + ') auf (Einsetzen oder Gauß-Verfahren).'],
          'solution': [_equations(mm, pol), 'Lösung: ' + _vstr(vpi, S) + '.'],
          'feedback_correct': 'Richtig: V^π ist die eindeutige Lösung der Bellman-Erwartungsgleichungen.'}
    # concept item 2: policy improvement at the state where the greedy choice differs most
    Q = {s: {b: M.mdp_q(mm, vpi, s, b) for b in mm['actions'][s]} for s in decision_states(mm)}
    X = max(decision_states(mm), key=lambda s: (max(Q[s].values()) - Q[s][pol[s]], s == f))
    best = max(mm['actions'][X], key=lambda b: (Q[X][b], -mm['actions'][X].index(b)))
    opts = [{'value': b, 'label': f'{b}', 'feedback': f'Q^π({X},{b}) = {_f(Q[X][b])} ist kleiner als Q^π({X},{best}) = {_f(Q[X][best])}.'}
            for b in mm['actions'][X]]
    for o in opts:
        if o['value'] == best:
            o['feedback'] = ''
    if len(opts) < 3:
        opts.append({'value': '__same', 'label': 'Alle Aktionen sind gleich gut; die Policy bleibt.',
                     'feedback': 'Die Q-Werte unterscheiden sich: ' + ', '.join(f'Q^π({X},{b}) = {_f(Q[X][b])}' for b in mm['actions'][X]) + '.'})
    improve = {'id': 'improve', 'type': 'choice', 'title': 'Policy-Verbesserung',
               'prompt': f'Gegeben V^π mit {_vstr(vpi, S)}. Welche Aktion wählt die Policy-Verbesserung (greedy bzgl. Q^π) im Zustand {X}?',
               'options': opts, 'correct': best,
               'explanation': f'Q^π({X},·): ' + ', '.join(f'{b} {_f(Q[X][b])}' for b in mm['actions'][X]) +
                              f'. Greedy ist {best}' + (' – dieselbe Aktion wie π: hier ändert sich nichts.' if best == pol[X] else f'; π wählt bisher {pol[X]}, die neue Policy ist mindestens so gut.')}
    # transfer: the same MDP with a different discount
    gt = 0.5 if abs(g - 0.5) > 0.05 else 0.8
    mt, _ = model(sp, gt); vt = M.mdp_eval_exact(mt, pol)
    t3 = {'id': 'transfer', 'title': 'Transfer: kurzsichtiger Agent',
          'prompt': f'Dieselbe Policy, aber nun γ = {_f(gt)}. Berechnen Sie V^π({f}) neu. Was sagt der Unterschied über den Planungshorizont 1/(1 − γ)?',
          'expected': round(vt[f], 6), 'tolerance': 0.011, 'unit': m['unit'],
          'errors': _distinct(vt[f], [(vpi[f], f'Das ist der Wert für γ = {_f(g)}. Mit kleinerem γ zählen spätere Belohnungen weniger.'),
                                      (vpi[f] * gt / g if g else None, 'Der Wert skaliert nicht proportional zu γ; das Gleichungssystem muss neu gelöst werden.')], 0.011),
          'hints': ['Gleiches Gleichungssystem, nur mit dem neuen γ.', _equations(mt, pol)],
          'solution': ['Lösung: ' + _vstr(vt, S) + '.', f'Effektiver Horizont 1/(1 − γ): {_f(1 / (1 - gt), 1)} statt {_f(1 / (1 - g), 1)} Schritte.'],
          'feedback_correct': 'Richtig. Der kleinere Diskontfaktor verkürzt den effektiven Planungshorizont.'}
    # prediction: gamma falls
    gp = round(max(0.0, g - 0.4), 2) if g >= 0.5 else round(min(0.95, g + 0.4), 2)
    vp = M.mdp_eval_exact(model(sp, gp)[0], pol)[f]; d = vp - vpi[f]
    correct = 'same' if abs(d) < 1e-9 else ('down' if d < 0 else 'up')
    predict = {'question': f'Sie ändern γ von {_f(g)} auf {_f(gp)} und lassen π unverändert. Was passiert mit V^π({f})?',
               'options': [{'value': 'down', 'label': 'Der Wert sinkt.'}, {'value': 'up', 'label': 'Der Wert steigt.'},
                           {'value': 'same', 'label': 'Er bleibt gleich – γ betrifft nur die Rechenzeit.'}],
               'correct': correct, 'change': [{'param': 'gamma', 'to': gp}, {'param': 'k', 'to': 200}],
               'result_text': f'V^π({f}) ändert sich von {_f(vpi[f])} auf {_f(vp)}.',
               'explanation': 'γ gewichtet jeden späteren Schritt: Eine Belohnung k Schritte entfernt zählt γ^k-fach. '
                              'Wie sich V ändert, hängt davon ab, ob die späteren Belohnungen überwiegend positiv oder negativ sind.'}
    # missions (each with a witness; validated by pedagogy.validate)
    d0 = {p['id']: p['default'] for p in sp['params']}
    ex = []
    errs = [metrics(sp, {**d0, 'k': k})['err'] for k in range(0, 201)]
    kmin = next((k for k, e in enumerate(errs) if e < 0.01), None)
    if kmin and kmin > 0:
        ex.append({'id': 'converge', 'title': 'Bis auf 0,01 genau',
                   'prompt': f'Policy-Bewertung mit γ = {_f(g)}: Erhöhen Sie die Zahl der Sweeps, bis der größte Abstand ‖V_k − V^π‖_∞ unter 0,01 liegt.',
                   'hint': 'Der Abstand schrumpft je Sweep mindestens um den Faktor γ.',
                   'success': f'Ab k = {kmin}: Der Fehler fällt geometrisch, wie die Kontraktion ‖V_k − V^π‖_∞ ≤ γ^k ‖V_0 − V^π‖_∞ vorhersagt.',
                   'cond': [{'m': 'err', 'op': '<', 'v': 0.01}, {'p': 'mode', 'op': '==', 'v': 'eval'}, {'p': 'gamma', 'op': '==', 'v': g}],
                   'witness': {'k': kmin}})
    vstar = M.mdp_optimal(mm); opt = M.mdp_greedy(mm, vstar)
    if any(abs(M.mdp_q(mm, vstar, s, opt[s]) - M.mdp_q(mm, vstar, s, pol[s])) > 1e-9 for s in opt):
        ex.append({'id': 'improve', 'title': 'Keine Verbesserung mehr möglich',
                   'prompt': f'Wählen Sie bei γ = {_f(g)} eine Policy, bei der in keinem Zustand eine andere Aktion einen höheren Q^π-Wert hat.',
                   'hint': 'Wechseln Sie in einem Zustand zur Aktion mit dem höchsten Q-Wert und bewerten Sie neu.',
                   'success': 'Diese Policy ist greedy bezüglich ihres eigenen Wertes. Damit erfüllt V^π die Optimalitätsgleichung: π ist optimal.',
                   'cond': [{'m': 'nonGreedy', 'op': '==', 'v': 0}, {'p': 'gamma', 'op': '==', 'v': g}],
                   'witness': {f'pi{i}': opt[s] for i, s in enumerate(m['decision_states'])}})
    sig0 = metrics(sp, d0)['optSig']
    # the largest discount below (else above) the course value at which the optimal policy changes: the threshold
    down = [round(x / 100, 2) for x in range(int(round(g * 100)) - 1, -1, -1)]
    up = [round(x / 100, 2) for x in range(int(round(g * 100)) + 1, 100)]
    wit = next((x for x in down + up if metrics(sp, {**d0, 'gamma': x})['optSig'] != sig0), None)
    if wit is not None:
        ex.append({'id': 'horizon', 'title': 'Der Horizont ändert die beste Entscheidung',
                   'prompt': 'Verändern Sie γ, bis sich die optimale Policy (Pfeile der Wertiteration) in mindestens einem Zustand ändert.',
                   'hint': 'Probieren Sie kleine γ: Ein kurzsichtiger Agent bevorzugt sofortige Belohnung.',
                   'success': f'Zum Beispiel bei γ = {_f(wit)}: Welche Aktion optimal ist, hängt davon ab, wie stark die Zukunft zählt.',
                   'cond': [{'m': 'optSig', 'op': '!=', 'v': sig0}], 'witness': {'gamma': wit}})
    return {'predict': predict, 'tasks': [t1, t2, improve, t3], 'explore': ex,
            'choice': {'id': 'concept', 'type': 'choice', 'title': 'Erwartung oder Maximum?',
                       'prompt': 'Worin unterscheidet sich die Bellman-Optimalitätsgleichung von der Bellman-Erwartungsgleichung?',
                       'options': [{'value': 'max', 'label': 'Statt über π(a|s) zu mitteln, wird über die Aktionen maximiert; über die Folgezustände wird weiter gemittelt.', 'feedback': ''},
                                   {'value': 'maxnext', 'label': 'Auch über die Folgezustände wird maximiert.', 'feedback': 'Den Folgezustand wählt die Umgebung, nicht der Agent: Über s′ bleibt es ein Erwartungswert mit p(s′|s,a).'},
                                   {'value': 'gamma', 'label': 'Die Optimalitätsgleichung kommt ohne Diskontfaktor aus.', 'feedback': 'γ steht in beiden Gleichungen; er bestimmt, wie stark die Zukunft zählt.'},
                                   {'value': 'linear', 'label': 'Beide sind lineare Gleichungssysteme in V.', 'feedback': 'Nur die Erwartungsgleichung ist linear. Das Maximum macht die Optimalitätsgleichung nichtlinear – deshalb löst man sie iterativ.'}],
                       'correct': 'max', 'explanation': 'Der Agent wählt die Aktion (max), die Umgebung den Folgezustand (Erwartungswert). Nur bei fester Policy ist das System linear.'}}


def _equations(mm, pol):
    g = mm['gamma']; out = []
    for s in mm['states']:
        if not mm['actions'][s]:
            continue
        r, nxt = mm['T'][(s, pol[s])]
        out.append(f'V({s}) = {_f(r)} + {_f(g)} · (' + ' + '.join(f'{_f(p)} · V({t})' for t, p in nxt.items()) + ')')
    return '; '.join(out) + '.'


def pedagogy(spec):
    """Learning sequence pieces for pedagogy.add (DR-1.2)."""
    q = spec['sequence'].pop('_choice', None) or _sequence(spec, model(spec)[0])['choice']
    return {'explain_prompt': 'Erklären Sie, warum sich V^π so verändert, wenn γ kleiner wird.',
            'explain_keys': [{'label': 'spätere Belohnungen zählen γ^k-fach', 'terms': ['γ^k', 'gamma^k', 'gewicht', 'diskont', 'später', 'zukunft']},
                             {'label': 'Vorzeichen der späteren Belohnungen entscheidet', 'terms': ['positiv', 'negativ', 'vorzeichen', 'strafe']},
                             {'label': 'kürzerer Planungshorizont 1/(1 − γ)', 'terms': ['horizont', '1/(1', 'kurzsichtig', 'schritte']}],
            'explore': spec['sequence'].pop('_explore', []),
            'choice': q,
            'takeaways': ['Ein Bellman-Backup ist ein Erwartungswert: Σ_{s′} p(s′|s,a) · (r + γ V(s′)); die Policy bestimmt die Aktion, die Umgebung den Folgezustand.',
                          'Policy-Bewertung löst ein lineares Gleichungssystem; Iterieren nähert es geometrisch an (Kontraktion mit Faktor γ).',
                          'Die Optimalitätsgleichung ersetzt den Mittelwert über π durch das Maximum über Aktionen; greedy bzgl. V^π verbessert jede Policy.'],
            'summary_prompt': 'Fassen Sie in einem Satz zusammen, wie ein Bellman-Backup aus V_k den Wert V_{k+1} macht.',
            'transfer_id': 'transfer'}


def static_svg(spec):
    """State graph with the policy's transitions and V^π (initial state of the lab; also used in the PDF)."""
    mm, pol = model(spec); m = spec['model']; L = m['layout']; V = M.mdp_eval_exact(mm, pol)
    xs, ys = [L[q][0] for q in mm['states']], [L[q][1] for q in mm['states']]
    vx, vy, vw, vh = min(xs) - 150, min(ys) - 110, max(xs) - min(xs) + 300, max(ys) - min(ys) + 200   # tight box, as in the live view
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vx:.0f} {vy:.0f} {vw:.0f} {vh:.0f}" role="img" aria-label="Zustandsgraph des MDP mit der Policy π">'
         f'<title>MDP: Zustände, Übergänge der Policy π und Werte V^π (γ = {_f(mm["gamma"])})</title>',
         '<defs><marker id="mdp-ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#1f5f8b"/></marker></defs>']
    for st in mm['states']:
        if not mm['actions'][st]:
            continue
        a = pol[st]; r, nxt = mm['T'][(st, a)]; (x1, y1) = L[st]
        for t, p in nxt.items():
            (x2, y2) = L[t]
            if t == st:
                s.append(f'<path d="M{x1 - 14},{y1 - 34} C{x1 - 40},{y1 - 95} {x1 + 40},{y1 - 95} {x1 + 14},{y1 - 34}" fill="none" stroke="#1f5f8b" stroke-width="2" marker-end="url(#mdp-ah)"/>'
                         f'<text x="{x1}" y="{y1 - 86}" text-anchor="middle" font-size="12" fill="#1f5f8b">{E(a)}: p = {_f(p)}, r = {_f(r)}</text>')
                continue
            dx, dy = x2 - x1, y2 - y1; d = math.hypot(dx, dy) or 1; ox, oy = -dy / d * 16, dx / d * 16
            sx, sy, ex_, ey = x1 + dx / d * 36 + ox, y1 + dy / d * 36 + oy, x2 - dx / d * 38 + ox, y2 - dy / d * 38 + oy
            s.append(f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{ex_:.1f}" y2="{ey:.1f}" stroke="#1f5f8b" stroke-width="2" marker-end="url(#mdp-ah)"/>'
                     f'<text x="{(sx + ex_) / 2 + ox:.1f}" y="{(sy + ey) / 2 + oy + 4:.1f}" text-anchor="middle" font-size="12" fill="#1f5f8b">{E(a)}: p = {_f(p)}, r = {_f(r)}</text>')
    for st in mm['states']:
        x, y = L[st]; term = not mm['actions'][st]
        s.append(f'<circle cx="{x}" cy="{y}" r="34" fill="{"#eef1f4" if term else "#f6efe2"}" stroke="#334" stroke-width="{1 if term else 2}"/>'
                 f'<text x="{x}" y="{y + 5}" text-anchor="middle" font-size="14" font-weight="700" fill="#223">{E(st)}</text>'
                 f'<text x="{x}" y="{y + 56}" text-anchor="middle" font-size="13" fill="#223">V<tspan dy="-0.45em" font-size="0.75em">π</tspan><tspan dy="0.45em"> = {_f(V[st])}</tspan></text>')
    s.append(f'<text x="{vx + 12:.0f}" y="{vy + vh - 10:.0f}" font-size="11" fill="#5b6876">Pfeile: Übergänge der Aktion π(s) mit p(s′|s,a) und r(s,a) · Werte exakt aus dem Gleichungssystem, γ = {_f(mm["gamma"])}</text></svg>')
    return ''.join(s)
