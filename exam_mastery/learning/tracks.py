"""Three adaptive reference tracks (schema em-track-v1): machine learning, finance, mathematics (argument).

Every expected answer and every value in a bug library is computed here from labs/models.py (or plain geometry),
never typed in. validate() re-diagnoses each task's expected answer (must be 'correct') and each bug (must yield its
category), so a wrong sample solution or an unreachable error category fails the build.

Competency types (3.2): declarative, conceptual, procedural, derivation, argument, problem_solving, transfer,
prerequisite. Existing stable ids are kept (ml/backpropagation, kc-d5d3fd65634ab3, math/inscribed-rectangle ...);
prerequisite competencies that had no id get one in the 'prereq/' namespace.
"""
import math

from ..labs import build as B
from ..labs import models as M
from . import diagnose as D

SCHEMA = 'em-track-v1'
f = B._fmt


def _r(x, d=4):
    return round(x, d)


# ------------------------------------------------------------------ A. machine learning: backpropagation

ML_VARS = ['delta_o', 'v1', 'v2', 'a1', 'a2', 'x1', 'x2', 'fp1', 'fp2']
ML_DEFS = {'fp1': 'a1*(1-a1)', 'fp2': 'a2*(1-a2)'}


def _ml_bugs(j, i):
    """Bug library for dL/dw_ji (j hidden unit, i input). Each entry: wrong expression -> error category."""
    o = 3 - j
    return [{'expr': f'delta_o*v{j}*fp{j}', 'category': 'missing_input_factor'},
            {'expr': f'delta_o*v{j}*x{i}', 'category': 'missing_activation_derivative'},
            {'expr': f'delta_o*v{j}*fp{j}*a{j}', 'category': 'activation_instead_of_input'},
            {'expr': f'delta_o*fp{j}*x{i}', 'category': 'missing_downstream_weight'},
            {'expr': f'delta_o*v{o}*fp{o}*x{i}', 'category': 'wrong_path'},
            {'expr': f'delta_o*a{j}', 'category': 'output_weight_formula'},
            {'expr': f'delta_o*x{i}', 'category': 'chain_incomplete'}]


def ml_track():
    spec = B.mlp_spec(); m = spec['model']; p, x, t, lr = m['init'], m['x'], m['target'], m['lr']
    bw = M.mlp_backward(p, x, t); fw = bw['forward']
    g11 = bw['grad']['W1'][0][0]
    # transfer: tanh hidden layer, new input and target
    xt, tt = [1.0, 0.5], 0.2
    bt = M.mlp_backward(p, xt, tt, 'tanh', 'sigmoid'); ft = bt['forward']
    fp_tanh = 1 - ft['a1'][0] ** 2; fp_sig_wrong = ft['a1'][0] * (1 - ft['a1'][0])
    d_o = bt['delta_o']; g12 = bt['grad']['W1'][0][1]
    w11_new = p['W1'][0][0] - lr * g11
    cats = {
        'sigmoid_derivative_unknown': {'kind': 'prerequisite', 'label': 'Ableitung der Sigmoidfunktion',
                                       'feedback': 'Ihre Zahl passt zu σ(z) selbst (oder zu 1 − σ(z), σ²), nicht zu σ′(z). Die Ableitung der Sigmoidfunktion ist σ′(z) = σ(z)·(1 − σ(z)).',
                                       'support': {'type': 'worked_example', 'ref': 'prereq/sigmoid-derivative'}},
        'missing_input_factor': {'kind': 'slip', 'label': 'Faktor x₁ fehlt',
                                 'feedback': 'Ihr Ausdruck enthält δ_o, v₁ und σ′(z₁) – diese drei Glieder stimmen. Es fehlt das letzte Glied der Kette: Wie stark ändert sich z₁, wenn w₁₁ wächst? Schauen Sie, was im Bild am Gewicht w₁₁ ankommt.',
                                 'visual': {'kind': 'network_path', 'edges': ['x1-h1', 'h1-o'], 'nodes': ['x1', 'h1', 'o'], 'term': 'x1', 'missing': 'x1'}},
        'missing_activation_derivative': {'kind': 'misconception', 'label': 'Ableitung der Aktivierung fehlt',
                                          'feedback': 'Der Weg zurück führt durch die Aktivierung a₁ = σ(z₁). Wer sie überspringt, behandelt das Neuron wie linear. Welches Glied der Kette gehört zu diesem Schritt von z₁ nach a₁?',
                                          'visual': {'kind': 'network_path', 'edges': ['x1-h1', 'h1-o'], 'nodes': ['h1'], 'term': 'fp1', 'missing': 'fp1'},
                                          'support': {'type': 'worked_example', 'ref': 'ml/backpropagation'}},
        'activation_instead_of_input': {'kind': 'misconception', 'label': 'a₁ statt x₁ als Eingang',
                                        'feedback': 'a₁ ist der Ausgang von Neuron 1; er multipliziert erst das nächste Gewicht v₁. Welches Signal kommt am Gewicht w₁₁ an?',
                                        'visual': {'kind': 'network_path', 'edges': ['x1-h1'], 'nodes': ['x1', 'h1'], 'term': 'x1', 'missing': 'x1'}},
        'missing_downstream_weight': {'kind': 'slip', 'label': 'Gewicht v₁ fehlt',
                                      'feedback': 'Der Fehler am Ausgang erreicht Neuron 1 nur über ein Gewicht. Welches, und fehlt es in Ihrer Kette?',
                                      'visual': {'kind': 'network_path', 'edges': ['h1-o'], 'nodes': ['h1', 'o'], 'term': 'v1', 'missing': 'v1'}},
        'wrong_path': {'kind': 'misconception', 'label': 'falscher Pfad im Netz',
                       'feedback': 'Ihr Ausdruck folgt dem Pfad über Neuron 2. w₁₁ führt aber in Neuron 1: Nur Größen auf dem Weg x₁ → Neuron 1 → Ausgabe gehören in die Kette.',
                       'visual': {'kind': 'network_path', 'edges': ['x1-h1', 'h1-o'], 'nodes': ['x1', 'h1', 'o'], 'term': 'path'}},
        'output_weight_formula': {'kind': 'misconception', 'label': 'Formel der Ausgabeschicht verwendet',
                                  'feedback': 'δ_o·a₁ ist der Gradient des Ausgabegewichts v₁. Für ein Gewicht der verdeckten Schicht muss der Fehler zuerst durch v₁ und σ′ zurück.',
                                  'visual': {'kind': 'network_path', 'edges': ['h1-o'], 'nodes': ['h1', 'o'], 'term': 'path'},
                                  'support': {'type': 'worked_example', 'ref': 'ml/backpropagation'}},
        'chain_incomplete': {'kind': 'misconception', 'label': 'Kette unvollständig',
                             'feedback': 'Zwischen Ausgang und w₁₁ liegen zwei Glieder: das Gewicht v₁ und die Aktivierung σ′(z₁). Beide fehlen.',
                             'visual': {'kind': 'network_path', 'edges': ['x1-h1', 'h1-o'], 'nodes': ['x1', 'h1', 'o'], 'term': 'path'},
                             'support': {'type': 'worked_example', 'ref': 'ml/backpropagation'}},
        'wrong_activation_derivative': {'kind': 'misconception', 'label': 'Ableitung der falschen Aktivierung',
                                        'feedback': 'Hier ist die verdeckte Aktivierung tanh, nicht sigmoid. tanh′(z) = 1 − tanh²(z) = 1 − a², nicht a(1 − a).',
                                        'visual': {'kind': 'network_path', 'edges': [], 'nodes': ['h1'], 'term': 'fp1'},
                                        'support': {'type': 'worked_example', 'ref': 'prereq/sigmoid-derivative'}},
        'update_direction': {'kind': 'misconception', 'label': 'Schritt in Gradientenrichtung',
                             'feedback': 'Gradientenabstieg geht gegen den Gradienten: θ − η·∂L/∂θ. Mit + steigt der Verlust.',
                             'visual': {'kind': 'network_path', 'edges': ['x1-h1'], 'nodes': [], 'term': 'update'}},
        'missing_learning_rate': {'kind': 'slip', 'label': 'Lernrate vergessen', 'feedback': 'Der Gradient wird vor dem Abziehen mit der Lernrate η multipliziert.',
                                  'visual': {'kind': 'network_path', 'edges': ['x1-h1'], 'nodes': [], 'term': 'update'}},
    }
    P = lambda v: f(v, 4)
    tasks = [
        {'id': 'ml-pre', 'role': 'diagnostic', 'kc_id': 'prereq/sigmoid-derivative', 'type': 'numeric', 'title': 'Voraussetzung: Ableitung der Sigmoidfunktion',
         'prompt': 'Für ein z gilt σ(z) = 0,6. Wie groß ist σ′(z)?', 'expected': 0.24, 'tolerance': 0.0005,
         'errors': [{'value': 0.6, 'category': 'sigmoid_derivative_unknown'}, {'value': 0.4, 'category': 'sigmoid_derivative_unknown'}, {'value': 0.36, 'category': 'sigmoid_derivative_unknown'}],
         'hints': ['Die Sigmoidfunktion hat eine Ableitung, die sich durch ihren eigenen Wert ausdrücken lässt.', 'σ′(z) = σ(z)·(1 − σ(z)).'],
         'solution': ['σ′(z) = 0,6 · (1 − 0,6) = 0,6 · 0,4 = 0,24.'], 'prereq_retry': 'ml-pre2'},
        {'id': 'ml-pre2', 'role': 'prereq_retry', 'kc_id': 'prereq/sigmoid-derivative', 'type': 'numeric', 'title': 'Voraussetzung, neue Zahl',
         'prompt': 'Jetzt gilt σ(z) = 0,3. Wie groß ist σ′(z)?', 'expected': 0.21, 'tolerance': 0.0005,
         'errors': [{'value': 0.3, 'category': 'sigmoid_derivative_unknown'}, {'value': 0.7, 'category': 'sigmoid_derivative_unknown'}, {'value': 0.09, 'category': 'sigmoid_derivative_unknown'}],
         'hints': ['Dieselbe Formel wie im Beispiel.'], 'solution': ['σ′(z) = 0,3 · 0,7 = 0,21.']},
        {'id': 'ml-core', 'role': 'core', 'kc_id': 'ml/backpropagation', 'type': 'expression', 'title': 'Gradient ∂L/∂w₁₁ herleiten',
         'prompt': 'Leiten Sie ∂L/∂w₁₁ als Produkt her. Verwenden Sie δ_o = (ŷ − t)·g′(z_o) für den Fehler am Ausgang und schreiben Sie σ′(z₁) als f′(z1) oder a1(1−a1).',
         'variables': ML_VARS, 'defs': ML_DEFS, 'expected_expr': 'delta_o*v1*fp1*x1', 'bugs': _ml_bugs(1, 1),
         'symbols': [['δ_o', 'delta_o'], ['v₁', 'v1'], ['v₂', 'v2'], ['a₁', 'a1'], ['a₂', 'a2'], ['x₁', 'x1'], ['x₂', 'x2'], ['f′(z₁)', "f'(z1)"], ['f′(z₂)', "f'(z2)"]],
         'hints': ['Gehen Sie den Weg von L zurück bis w₁₁: L → ŷ → z_o → a₁ → z₁ → w₁₁.', 'Jedes Glied liefert einen Faktor: δ_o, dann ∂z_o/∂a₁ = v₁, dann ∂a₁/∂z₁ = f′(z₁), dann ∂z₁/∂w₁₁.', 'z₁ = w₁₁·x₁ + w₁₂·x₂ + b₁ – wonach ändert sich z₁, wenn w₁₁ wächst?'],
         'solution': ['∂L/∂w₁₁ = δ_o · v₁ · f′(z₁) · x₁.', f'Mit den Werten des Labs: {P(bw["delta_o"])} · {P(p["W2"][0])} · {P(fw["a1"][0] * (1 - fw["a1"][0]))} · {P(x[0])} = {f(g11, 6)}.'],
         'similar': 'ml-similar', 'visual': {'kind': 'network_path', 'edges': ['x1-h1', 'h1-o'], 'nodes': ['x1', 'h1', 'o']},
         'reference_value': g11},
        {'id': 'ml-similar', 'role': 'similar', 'kc_id': 'ml/backpropagation', 'type': 'expression', 'title': 'Ähnliche Aufgabe ohne Hinweise: ∂L/∂w₂₂',
         'prompt': 'Jetzt für das Gewicht von x₂ in Neuron 2: Schreiben Sie ∂L/∂w₂₂ als Produkt.',
         'variables': ML_VARS, 'defs': ML_DEFS, 'expected_expr': 'delta_o*v2*fp2*x2',
         'bugs': [{'expr': b['expr'].replace('v1', 'V').replace('v2', 'v1').replace('V', 'v2').replace('fp1', 'F').replace('fp2', 'fp1').replace('F', 'fp2').replace('a1', 'A').replace('a2', 'a1').replace('A', 'a2').replace('x1', 'x2'), 'category': b['category']} for b in _ml_bugs(1, 1)],
         'symbols': [['δ_o', 'delta_o'], ['v₁', 'v1'], ['v₂', 'v2'], ['a₁', 'a1'], ['a₂', 'a2'], ['x₁', 'x1'], ['x₂', 'x2'], ['f′(z₁)', "f'(z1)"], ['f′(z₂)', "f'(z2)"]],
         'hints': [], 'solution': ['∂L/∂w₂₂ = δ_o · v₂ · f′(z₂) · x₂.'], 'visual': {'kind': 'network_path', 'edges': ['x2-h2', 'h2-o'], 'nodes': ['x2', 'h2', 'o']}},
        {'id': 'ml-transfer', 'role': 'transfer', 'kc_id': 'ml/backpropagation', 'type': 'steps', 'title': 'Transfer: andere Aktivierung, andere Eingabe',
         'prompt': f'Dasselbe Netz, aber die verdeckte Schicht nutzt tanh (Ausgabe weiterhin sigmoid). Eingabe x = ({f(xt[0], 1)}; {f(xt[1], 1)}), Ziel t = {f(tt, 1)}. '
                   f'Vorwärts ergibt sich a₁ = {P(ft["a1"][0])}, ŷ = {P(ft["y"])}; v₁ = {P(p["W2"][0])}. Berechnen Sie schrittweise (4 Nachkommastellen):',
         'steps': [
             {'id': 'delta_o', 'label': 'δ_o = (ŷ − t)·ŷ(1 − ŷ)', 'expected': _r(d_o), 'tolerance': 0.0006, 'errors': [{'value': _r(ft['y'] - tt), 'category': 'missing_activation_derivative'}]},
             {'id': 'fp1', 'label': 'f′(z₁) für tanh', 'expected': _r(fp_tanh), 'tolerance': 0.0006, 'errors': [{'value': _r(fp_sig_wrong), 'category': 'wrong_activation_derivative'}]},
             {'id': 'grad', 'label': '∂L/∂w₁₂', 'expected': _r(g12, 5), 'tolerance': 0.0003,
              'errors': [{'value': _r(d_o * p['W2'][0] * fp_sig_wrong * xt[1], 5), 'category': 'wrong_activation_derivative'},
                         {'value': _r(d_o * p['W2'][0] * fp_tanh, 5), 'category': 'missing_input_factor'}], 'default_category': 'unclassified'}],
         'hints': ['Die Kette ist dieselbe wie bei w₁₁; nur f′ und der Eingang ändern sich.'],
         'solution': [f'δ_o = ({P(ft["y"])} − {f(tt, 1)})·{P(ft["y"])}·(1 − {P(ft["y"])}) = {P(d_o)}.', f'tanh′(z₁) = 1 − a₁² = {P(fp_tanh)}.',
                      f'∂L/∂w₁₂ = δ_o·v₁·f′(z₁)·x₂ = {f(g12, 5)}.'],
         'visual': {'kind': 'network_path', 'edges': ['x2-h1', 'h1-o'], 'nodes': ['x2', 'h1', 'o']}},
        {'id': 'ml-harder', 'role': 'harder', 'kc_id': 'ml/gradient-descent', 'type': 'numeric', 'title': 'Anspruchsvoller: der Gradientenschritt',
         'prompt': f'Zurück zum Ausgangsnetz: w₁₁ = {f(p["W1"][0][0], 3)}, ∂L/∂w₁₁ = {f(g11, 6)}, η = {f(lr, 1)}. Welchen Wert hat w₁₁ nach einem Schritt? (4 Nachkommastellen) – und sinkt der Verlust dadurch?',
         'expected': _r(w11_new, 6), 'tolerance': 0.00006,
         'errors': [{'value': _r(p['W1'][0][0] + lr * g11, 6), 'category': 'update_direction'}, {'value': _r(p['W1'][0][0] - g11, 6), 'category': 'missing_learning_rate'}],
         'hints': ['θ ← θ − η·∂L/∂θ.'], 'solution': [f'w₁₁ ← {f(p["W1"][0][0], 3)} − {f(lr, 1)}·{f(g11, 6)} = {f(w11_new, 6)}.', 'Gegen den Gradienten: Für kleine η sinkt der Verlust.']},
        {'id': 'ml-retest', 'role': 'retest', 'kc_id': 'ml/backpropagation', 'type': 'expression', 'title': 'Spätere Prüfung: ∂L/∂w₂₁',
         'prompt': 'Ohne Hilfen: Schreiben Sie ∂L/∂w₂₁ (Gewicht von x₁ in Neuron 2) als Produkt.',
         'variables': ML_VARS, 'defs': ML_DEFS, 'expected_expr': 'delta_o*v2*fp2*x1', 'bugs': [{'expr': 'delta_o*v2*fp2', 'category': 'missing_input_factor'}, {'expr': 'delta_o*v2*x1', 'category': 'missing_activation_derivative'}],
         'symbols': [['δ_o', 'delta_o'], ['v₂', 'v2'], ['a₂', 'a2'], ['x₁', 'x1'], ['f′(z₂)', "f'(z2)"]], 'hints': [], 'solution': ['∂L/∂w₂₁ = δ_o · v₂ · f′(z₂) · x₁.']},
        {'id': 'ml-why', 'role': 'open', 'kc_id': 'ml/backpropagation', 'type': 'open', 'title': 'In eigenen Worten',
         'prompt': 'Warum ist der Gradient von w₁₁ null, wenn x₁ = 0 ist? Begründen Sie in zwei Sätzen.', 'hints': [], 'solution': []},
    ]
    return {
        'schema': SCHEMA, 'id': 'ml/backprop-track', 'version': 1, 'domain': 'machine_learning', 'lab': 'ml/backprop-2-2-1',
        'title': 'Wie ein Netz aus einem Fehler lernt – adaptiv', 'objective': 'Sie können den Gradienten eines Gewichts der verdeckten Schicht mit der Kettenregel herleiten, berechnen und für einen Gradientenschritt nutzen.',
        'kcs': [{'id': 'prereq/sigmoid-derivative', 'type': 'prerequisite', 'label': 'Ableitung der Sigmoidfunktion'},
                {'id': 'ml/forward-pass', 'type': 'procedural', 'label': 'Vorwärtsrechnung'},
                {'id': 'ml/backpropagation', 'type': 'derivation', 'label': 'Gradienten mit der Kettenregel herleiten'},
                {'id': 'ml/gradient-descent', 'type': 'procedural', 'label': 'Gradientenschritt'}],
        'context': {'values': {'delta_o': bw['delta_o'], 'v1': p['W2'][0], 'v2': p['W2'][1], 'a1': fw['a1'][0], 'a2': fw['a1'][1], 'x1': x[0], 'x2': x[1], 'w11': p['W1'][0][0], 'g11': g11, 'loss': bw['loss'], 'y': fw['y'], 't': t},
                    'equations': m['equations']},
        'categories': cats, 'tasks': tasks, 'flow': ['ml-pre', 'ml-core', 'ml-similar', 'ml-transfer', 'ml-harder'],
        'worked_examples': {
            'prereq/sigmoid-derivative': {'title': 'Durchgerechnet: σ′ aus σ', 'steps': ['σ(z) = 1/(1 + e^(−z)).', 'Ableiten: σ′(z) = e^(−z)/(1 + e^(−z))² = σ(z)·(1 − σ(z)).', 'Beispiel σ(z) = 0,8: σ′(z) = 0,8·0,2 = 0,16.', 'Für tanh gilt analog tanh′(z) = 1 − tanh²(z).']},
            'ml/backpropagation': {'title': 'Durchgerechnet: ∂L/∂v₁ und der Schritt nach innen', 'steps': ['Ausgabegewicht: ∂L/∂v₁ = δ_o · a₁, denn z_o = v₁a₁ + v₂a₂ + c.', 'Eine Schicht tiefer: ∂L/∂a₁ = δ_o · v₁, dann ∂L/∂z₁ = δ_o · v₁ · f′(z₁) =: δ₁.', 'Gewicht der verdeckten Schicht: ∂L/∂w₁₂ = δ₁ · x₂, denn ∂z₁/∂w₁₂ = x₂.']}},
        'anki_tags': ['em::lernstrecke::backprop'], 'sources': spec['sources'] + ['Lab ml/backprop-2-2-1 (gleiche Parameter)'],
        'source_status': 'Referenz-Fixture (keine Vorlesung); Gleichungen Standard-Kettenregel, unabhängig geprüft mit sympy und finiten Differenzen.',
    }


# ------------------------------------------------------------------ B. finance: liquidity planning (chapter 7 data)

ENT_DATA = {'orders': [0.0, 100.0, 180.0, 190.0, 210.0, 230.0, 250.0, 270.0], 'delay': 5,
            'cost': [102.0, 122.0, 172.0, 152.0, 242.0, 152.0, 162.0, 172.0], 'invest': [200.0, 500.0, 300.0, 140.0]}
CONTRAST = {'orders': [0, 0, 100, 100, 100, 100], 'delay': 1, 'cost': [40] * 6, 'invest': [50]}


def ent_track(data=None, kc_ids=('kc-d5d3fd65634ab3', 'kc-33639d91c4dfa2'), sources=('07 Business Planning & Effectuation.pdf S. 21',)):
    d = data or ENT_DATA
    cf = lambda **k: M.cashflow(**{**dict(orders=d['orders'], delay=d['delay'], cost=d['cost'], invest=d['invest']), **k})
    base, start500, tr, re4 = cf(), cf(start_cash=500), cf(delay=3), cf(delay=4)
    con = M.cashflow(**CONTRAST)
    assert con['final_balance'] > 0 > con['min_balance'], 'contrast data must have a positive end and a negative trough'
    kc_need, kc_plan = kc_ids[0], kc_ids[1]
    pre = [-120, -60, 90, 150]; pre2 = [-80, -40, 70, 100]
    cs = lambda xs, k: sum(xs[:k])
    cats = {
        'period_vs_cumulative': {'kind': 'prerequisite', 'label': 'Periodenwert statt kumulierter Stand',
                                 'feedback': 'Ihre Zahl ist der Cashflow einer einzelnen Periode. Die Liquidität ist die laufende Summe aller Cashflows bis zu diesem Zeitpunkt.',
                                 'support': {'type': 'worked_example', 'ref': 'prereq/cumulative-sum'}, 'visual': {'kind': 'cash', 'show': ['bars', 'running']}},
        'end_balance_vs_minimum': {'kind': 'misconception', 'label': 'Endsaldo statt Tiefpunkt',
                                   'feedback': 'Ihre Zahl ist der Stand am Ende des Planungszeitraums. Geld braucht das Unternehmen aber am tiefsten Punkt: Wer nur den Endsaldo finanziert, ist vorher zahlungsunfähig.',
                                   'visual': {'kind': 'cash', 'show': ['running', 'trough', 'end']},
                                   'contrast': {'type': 'contrast', 'ref': 'trough_vs_end'}},
        'start_cash_ignored': {'kind': 'slip', 'label': 'Anfangsbestand nicht berücksichtigt', 'feedback': 'Die Anfangsliquidität verschiebt die ganze kumulierte Kurve nach oben. Ihre Zahl ist der Bedarf ohne Anfangsbestand.',
                               'visual': {'kind': 'cash', 'show': ['running', 'trough']}},
        'old_delay': {'kind': 'slip', 'label': 'altes Zahlungsziel', 'feedback': 'Das ist der Bedarf beim alten Zahlungsziel. Verschieben Sie jede Einzahlung um das neue Zahlungsziel und bilden Sie die laufende Summe neu.',
                      'visual': {'kind': 'cash', 'show': ['bars', 'running', 'trough']}},
        'off_by_one_period': {'kind': 'slip', 'label': 'eine Periode zu früh', 'feedback': 'Das ist der Stand eine Periode zu früh. Zählen Sie die Perioden bis einschließlich der gefragten.',
                              'visual': {'kind': 'cash', 'show': ['bars', 'running']}},
        'overgeneralised_strict': {'kind': 'misconception', 'label': 'Aussage zu stark verallgemeinert',
                                   'feedback': 'Später eingehende Zahlungen können den Bedarf nicht senken (bei nicht-negativen Aufträgen). Er muss aber nicht strikt steigen: Liegt der Tiefpunkt, bevor die betroffene Zahlung ohnehin eingegangen wäre, bleibt er gleich.',
                                   'visual': {'kind': 'cash', 'show': ['running', 'trough', 'compare']}},
        'direction_confused': {'kind': 'misconception', 'label': 'Richtung verwechselt', 'feedback': 'Ein späteres Zahlungsziel nimmt Einzahlungen aus frühen Perioden heraus; jeder kumulierte Stand wird kleiner oder bleibt gleich. Sinken kann der Bedarf dadurch nicht.',
                               'visual': {'kind': 'cash', 'show': ['running', 'compare']}},
    }
    tasks = [
        {'id': 'cf-pre', 'role': 'diagnostic', 'kc_id': 'prereq/cumulative-sum', 'type': 'numeric', 'title': 'Voraussetzung: kumulierte Liquidität',
         'prompt': f'Cashflows je Periode in k€: P1 {pre[0]}, P2 {pre[1]}, P3 +{pre[2]}, P4 +{pre[3]}. Anfangsbestand 0. Wie hoch ist die kumulierte Liquidität am Ende von P3?',
         'expected': cs(pre, 3), 'tolerance': 0.5, 'unit': 'k€',
         'errors': [{'value': pre[2], 'category': 'period_vs_cumulative'}, {'value': cs(pre, 2), 'category': 'off_by_one_period'}],
         'hints': ['Liquidität am Ende von P3 = Summe der Cashflows P1 bis P3.'], 'solution': [f'{pre[0]} + ({pre[1]}) + {pre[2]} = {cs(pre, 3)} k€.'],
         'prereq_retry': 'cf-pre2', 'cash': {'cf': pre}},
        {'id': 'cf-pre2', 'role': 'prereq_retry', 'kc_id': 'prereq/cumulative-sum', 'type': 'numeric', 'title': 'Voraussetzung, neue Zahlen',
         'prompt': f'Cashflows in k€: P1 {pre2[0]}, P2 {pre2[1]}, P3 +{pre2[2]}, P4 +{pre2[3]}. Wie hoch ist die kumulierte Liquidität am Ende von P3?',
         'expected': cs(pre2, 3), 'tolerance': 0.5, 'unit': 'k€', 'errors': [{'value': pre2[2], 'category': 'period_vs_cumulative'}, {'value': cs(pre2, 2), 'category': 'off_by_one_period'}],
         'hints': [], 'solution': [f'{pre2[0]} + ({pre2[1]}) + {pre2[2]} = {cs(pre2, 3)} k€.'], 'cash': {'cf': pre2}},
        {'id': 'cf-core', 'role': 'core', 'kc_id': kc_need, 'type': 'numeric', 'title': 'Maximaler Finanzierungsbedarf',
         'prompt': f'Kapitel 7, Start-up-Plan: Kunden zahlen {d["delay"]} Perioden nach dem Auftrag, Anfangsliquidität 0. Wie hoch ist der maximale Finanzierungsbedarf in k€?',
         'expected': base['financing_need'], 'tolerance': 0.5, 'unit': 'k€',
         'errors': [{'value': -base['final_balance'], 'category': 'end_balance_vs_minimum'}, {'value': -base['cf'][0], 'category': 'period_vs_cumulative'}],
         'hints': ['Gesucht ist ein Stand der kumulierten Liquidität, kein einzelner Cashflow.', 'Welcher kumulierte Stand ist der kleinste?'],
         'solution': [f'Kumulierte Liquidität: {", ".join(f(v) for v in base["balance"])} k€.', f'Tiefster Stand {f(base["min_balance"])} k€ in Periode {base["min_period"]}; Bedarf {f(base["financing_need"])} k€.',
                      f'Der Endsaldo ({f(base["final_balance"])} k€) liegt höher, weil am Ende schon Zahlungen eingehen.'],
         'similar': 'cf-similar', 'cash': {'model': {**d}}},
        {'id': 'cf-contrast', 'role': 'contrast', 'kc_id': kc_need, 'type': 'numeric', 'title': 'Kontrast: Endsaldo positiv – trotzdem Bedarf?',
         'prompt': f'Ein anderes Projekt: Aufträge {", ".join(str(v) for v in CONTRAST["orders"])} k€ je Periode, Zahlungsziel 1 Periode, laufende Kosten 40 k€ je Periode, Investition 50 k€ in P1. '
                   f'Am Ende steht ein Plus von {f(con["final_balance"])} k€. Wie hoch ist der Finanzierungsbedarf?',
         'expected': con['financing_need'], 'tolerance': 0.5, 'unit': 'k€',
         'errors': [{'value': 0, 'category': 'end_balance_vs_minimum'}, {'value': con['final_balance'], 'category': 'end_balance_vs_minimum'}],
         'hints': [], 'solution': [f'Kumuliert: {", ".join(f(v) for v in con["balance"])} k€.', f'Tiefpunkt {f(con["min_balance"])} k€ in P{con["min_period"]}: Bedarf {f(con["financing_need"])} k€, obwohl der Endsaldo positiv ist.'],
         'cash': {'model': CONTRAST}},
        {'id': 'cf-similar', 'role': 'similar', 'kc_id': kc_need, 'type': 'numeric', 'title': 'Ähnliche Aufgabe ohne Hinweise: mit Anfangsbestand',
         'prompt': 'Gleicher Plan, aber das Start-up hat 500 k€ Anfangsliquidität. Wie hoch ist der Finanzierungsbedarf jetzt?',
         'expected': start500['financing_need'], 'tolerance': 0.5, 'unit': 'k€',
         'errors': [{'value': base['financing_need'], 'category': 'start_cash_ignored'}, {'value': -start500['final_balance'], 'category': 'end_balance_vs_minimum'}],
         'hints': [], 'solution': [f'Jeder Stand liegt 500 k€ höher; Tiefpunkt {f(start500["min_balance"])} k€; Bedarf {f(start500["financing_need"])} k€.'], 'cash': {'model': {**d, 'start_cash': 500}}},
        {'id': 'cf-transfer', 'role': 'transfer', 'kc_id': kc_plan, 'type': 'numeric', 'title': 'Transfer: anderes Zahlungsziel',
         'prompt': 'Das Start-up verhandelt ein Zahlungsziel von 3 statt 5 Perioden (Anfangsliquidität 0). Wie hoch ist der Finanzierungsbedarf?',
         'expected': tr['financing_need'], 'tolerance': 0.5, 'unit': 'k€',
         'errors': [{'value': base['financing_need'], 'category': 'old_delay'}, {'value': -tr['final_balance'], 'category': 'end_balance_vs_minimum'}],
         'hints': ['Verschieben Sie jede Einzahlung: Auftrag in Periode t wird in t + 3 bezahlt.'],
         'solution': [f'Kumuliert bei Zahlungsziel 3: {", ".join(f(v) for v in tr["balance"])} k€.', f'Tiefpunkt {f(tr["min_balance"])} k€ in P{tr["min_period"]}; Bedarf {f(tr["financing_need"])} k€.'],
         'cash': {'model': {**d, 'delay': 3}}},
        {'id': 'cf-harder', 'role': 'harder', 'kc_id': kc_plan, 'type': 'choice', 'title': 'Anspruchsvoller: Was gilt allgemein?',
         'prompt': 'Alle Aufträge sind nicht negativ, sonst ändert sich nichts. Das Zahlungsziel wird um eine Periode verlängert. Welche Aussage über den Finanzierungsbedarf gilt in jedem solchen Plan?',
         'options': [{'value': 'strict', 'label': 'Er steigt immer.', 'category': 'overgeneralised_strict'},
                     {'value': 'weak', 'label': 'Er steigt oder bleibt gleich; sinken kann er nicht.'},
                     {'value': 'down', 'label': 'Er kann auch sinken, je nach Plan.', 'category': 'direction_confused'}],
         'correct': 'weak', 'hints': [], 'solution': ['Jeder kumulierte Stand verliert höchstens Einzahlungen, also sinkt jeder Stand oder bleibt gleich; damit sinkt der Tiefpunkt oder bleibt gleich.',
                                                      'Gleich bleibt er zum Beispiel, wenn der Tiefpunkt vor der ersten Einzahlung liegt oder die Anfangsliquidität alles deckt.'],
         'cash': {'model': {**d}, 'compare_delay': d['delay'] + 1}},
        {'id': 'cf-retest', 'role': 'retest', 'kc_id': kc_need, 'type': 'numeric', 'title': 'Spätere Prüfung: Zahlungsziel 4',
         'prompt': 'Ohne Hilfen: Gleicher Plan, Zahlungsziel 4 Perioden, Anfangsliquidität 0. Finanzierungsbedarf in k€?',
         'expected': re4['financing_need'], 'tolerance': 0.5, 'unit': 'k€', 'errors': [{'value': -re4['final_balance'], 'category': 'end_balance_vs_minimum'}],
         'hints': [], 'solution': [f'Tiefpunkt {f(re4["min_balance"])} k€ in P{re4["min_period"]}; Bedarf {f(re4["financing_need"])} k€.'], 'cash': {'model': {**d, 'delay': 4}}},
        {'id': 'cf-why', 'role': 'open', 'kc_id': kc_plan, 'type': 'open', 'title': 'In eigenen Worten',
         'prompt': 'Erklären Sie einer Gründerin in zwei Sätzen, warum ein positiver Endsaldo nicht bedeutet, dass sie keine Finanzierung braucht.', 'hints': [], 'solution': []},
    ]
    return {
        'schema': SCHEMA, 'id': 'ent/liquidity-track', 'version': 1, 'domain': 'business_economics', 'lab': 'ent/cashflow-liquidity',
        'title': 'Warum Wachstum Geld kostet – adaptiv', 'objective': 'Sie können aus Zahlungsströmen die kumulierte Liquidität und den maximalen Finanzierungsbedarf bestimmen und vom Endsaldo unterscheiden.',
        'kcs': [{'id': 'prereq/cumulative-sum', 'type': 'prerequisite', 'label': 'Kumulierte Liquidität als laufende Summe'},
                {'id': kc_need, 'type': 'conceptual', 'label': 'Maximaler Finanzierungsbedarf (Tiefpunkt, nicht Endsaldo)'},
                {'id': kc_plan, 'type': 'transfer', 'label': 'Zahlungsziele im Liquiditätsplan'}],
        'context': {'base': base, 'data': d, 'contrast': con},
        'categories': cats, 'tasks': tasks, 'flow': ['cf-pre', 'cf-core', 'cf-similar', 'cf-transfer', 'cf-harder'],
        'worked_examples': {'prereq/cumulative-sum': {'title': 'Durchgerechnet: laufende Summe', 'steps': ['Cashflows: −50, −30, +40, +60 k€.', 'Ende P1: −50. Ende P2: −50 − 30 = −80. Ende P3: −80 + 40 = −40. Ende P4: −40 + 60 = +20.', 'Jeder Stand ist der vorige Stand plus der Cashflow der Periode.']}},
        'contrasts': {'trough_vs_end': {'title': 'Tiefpunkt und Endsaldo nebeneinander', 'rows': [['Tiefpunkt', 'kleinster kumulierter Stand im Zeitraum', 'bestimmt, wie viel Geld beschafft werden muss'], ['Endsaldo', 'Stand am Ende des Zeitraums', 'sagt, ob der Plan am Ende im Plus ist']],
                                         'example': f'Im Kapitel-7-Plan: Tiefpunkt {f(base["min_balance"])} k€ (P{base["min_period"]}), Endsaldo {f(base["final_balance"])} k€. Der Bedarf ist {f(base["financing_need"])} k€, nicht {f(-base["final_balance"])} k€.'}},
        'anki_tags': ['em::lernstrecke::liquiditaet'], 'sources': list(sources) + ['Lab ent/cashflow-liquidity (gleiches Modell)'],
        'source_status': 'Zahlen aus Kapitel 7 der Vorlesung (Quelle S. 21); Modellannahmen wie im Lab.',
        'assumptions': ['Jeder Auftrag wird vollständig nach dem Zahlungsziel bezahlt; Aufträge nicht negativ.', 'Keine Zinsen auf den Fehlbetrag; Aufträge nach dem Horizont zählen nicht.'],
    }


# ------------------------------------------------------------------ C. mathematics: argument with a missing premise

def math_track():
    spec = B.chord_spec()
    P, Q, U = (2.0, 1.0), (-2.0, 3.0), (1.0, 4.0)
    Mx, My = (P[0] + Q[0]) / 2, (P[1] + Q[1]) / 2
    V = (2 * Mx - U[0], 2 * My - U[1])
    dPQ, dUV = math.dist(P, Q), math.dist(U, V)
    assert abs(dPQ - dUV) < 1e-12, 'similar task must yield a rectangle'
    cats = {
        'diagonal_bisection_overclaimed': {'kind': 'prerequisite', 'label': 'Viereckssätze: Diagonalen',
                                           'feedback': 'Halbieren die Diagonalen einander, folgt nur: Parallelogramm. Für ein Rechteck braucht es zusätzlich gleich lange Diagonalen.',
                                           'support': {'type': 'worked_example', 'ref': 'prereq/quadrilateral-diagonals'}, 'visual': {'kind': 'quad', 'show': ['parallelogram']}},
        'missing_premise_equal_diagonals': {'kind': 'misconception', 'label': 'Voraussetzung „gleich lang“ fehlt',
                                            'feedback': 'Mit demselben Mittelpunkt allein halbieren sich die Diagonalen – das ergibt ein Parallelogramm, nicht notwendig ein Rechteck. Welche zusätzliche Eigenschaft der Diagonalen macht aus einem Parallelogramm ein Rechteck – und ist sie hier gegeben?',
                                            'visual': {'kind': 'quad', 'show': ['parallelogram', 'compare_rect']},
                                            'contrast': {'type': 'contrast', 'ref': 'parallelogram_vs_rectangle'}},
        'missing_premise_midpoint': {'kind': 'misconception', 'label': 'Voraussetzung „gleicher Mittelpunkt“ fehlt',
                                     'feedback': 'Gleich lange Sehnen allein bilden kein Viereck mit sich halbierenden Diagonalen. Erst der gemeinsame Mittelpunkt macht PUQV zum Parallelogramm.',
                                     'visual': {'kind': 'quad', 'show': ['no_common_midpoint']}},
        'degenerate_case_ignored': {'kind': 'slip', 'label': 'Sonderfall gleiche Paare', 'feedback': 'Sind die Paare gleich ({P, Q} = {U, V}), gibt es nur zwei Punkte und kein Viereck. Die Verschiedenheit gehört zur Voraussetzung.',
                                    'visual': {'kind': 'quad', 'show': ['degenerate']}},
        'unjustified_premise': {'kind': 'misconception', 'label': 'nicht gegebene Voraussetzung', 'feedback': 'Dass die Sehnen senkrecht stehen, ist nicht gegeben und wird nicht gebraucht. Mit dieser Annahme bewiesen Sie nur einen Sonderfall (Quadrat).',
                                'visual': {'kind': 'quad', 'show': ['square']}},
        'unnecessary_assumption': {'kind': 'slip', 'label': 'unnötige Annahme', 'feedback': 'Konvexität wird für diesen Schritt nicht gebraucht: Das Argument gilt für vier beliebige Punkte. Mit der Annahme wäre die Aussage nur für konvexe Kurven gezeigt.',
                                   'visual': {'kind': 'quad', 'show': ['rect']}},
        'reflection_error': {'kind': 'slip', 'label': 'Spiegelung am Mittelpunkt', 'feedback': 'V ist die Spiegelung von U am Mittelpunkt M: V = 2M − U. Ihre Zahl passt zu U − M oder M − U.', 'visual': {'kind': 'quad', 'show': ['reflection']}},
        'half_chord': {'kind': 'slip', 'label': 'halbe Sehne', 'feedback': 'Das ist der halbe Abstand. Die Höhe d des Raumpunkts ist die volle Sehnenlänge |PQ|.', 'visual': {'kind': 'quad', 'show': ['rect']}},
        'incomplete_classification': {'kind': 'slip', 'label': 'unvollständig klassifiziert', 'feedback': 'Richtig, es ist ein Rechteck – aber die senkrechten Diagonalen machen es zusätzlich zur Raute, also zum Quadrat.', 'visual': {'kind': 'quad', 'show': ['square']}},
        'rhombus_confused': {'kind': 'misconception', 'label': 'Raute und Rechteck verwechselt', 'feedback': 'Senkrechte Diagonalen allein ergeben eine Raute; gleich lange Diagonalen machen ein Rechteck. Hier gilt beides.', 'visual': {'kind': 'quad', 'show': ['square']}},
    }
    tasks = [
        {'id': 'm-pre', 'role': 'diagnostic', 'kc_id': 'prereq/quadrilateral-diagonals', 'type': 'choice', 'title': 'Voraussetzung: Diagonalen eines Vierecks',
         'prompt': 'Die Diagonalen eines Vierecks halbieren einander. Was folgt daraus sicher?',
         'options': [{'value': 'parallelogram', 'label': 'Es ist ein Parallelogramm.'}, {'value': 'rectangle', 'label': 'Es ist ein Rechteck.', 'category': 'diagonal_bisection_overclaimed'},
                     {'value': 'rhombus', 'label': 'Es ist eine Raute.', 'category': 'diagonal_bisection_overclaimed'}],
         'correct': 'parallelogram', 'hints': ['Zeichnen Sie zwei Strecken mit gleichem Mittelpunkt, aber verschiedener Länge.'], 'solution': ['Sich halbierende Diagonalen kennzeichnen genau die Parallelogramme.'], 'prereq_retry': 'm-pre2'},
        {'id': 'm-pre2', 'role': 'prereq_retry', 'kc_id': 'prereq/quadrilateral-diagonals', 'type': 'choice', 'title': 'Voraussetzung, zweite Frage',
         'prompt': 'Ein Parallelogramm hat gleich lange Diagonalen. Was ist es?',
         'options': [{'value': 'rectangle', 'label': 'Ein Rechteck.'}, {'value': 'rhombus', 'label': 'Eine Raute.', 'category': 'diagonal_bisection_overclaimed'}, {'value': 'square', 'label': 'Immer ein Quadrat.', 'category': 'diagonal_bisection_overclaimed'}],
         'correct': 'rectangle', 'hints': [], 'solution': ['Ein Parallelogramm mit gleich langen Diagonalen ist ein Rechteck (nicht notwendig ein Quadrat).']},
        {'id': 'm-core', 'role': 'core', 'kc_id': 'math/inscribed-rectangle', 'type': 'constraints', 'title': 'Beweisschritt: Welche Voraussetzungen braucht das Argument?',
         'prompt': 'Behauptung: „Haben zwei Punktpaare {P, Q} und {U, V} der Kurve denselben Raumpunkt (Mₓ, M_y, d), dann ist PUQV ein Rechteck.“ Wählen Sie genau die Voraussetzungen, auf die sich der Beweis stützen muss.',
         'premises': [{'id': 'mid', 'label': 'PQ und UV haben denselben Mittelpunkt M.'}, {'id': 'len', 'label': 'PQ und UV sind gleich lang (d).'},
                      {'id': 'distinct', 'label': 'Die Paare sind verschieden: {P, Q} ≠ {U, V}.'}, {'id': 'convex', 'label': 'Die Kurve ist konvex.'},
                      {'id': 'perp', 'label': 'PQ und UV stehen senkrecht aufeinander.'}],
         'constraints': [{'id': 'C-mid', 'kind': 'requires', 'premise': 'mid', 'category': 'missing_premise_midpoint'},
                         {'id': 'C-len', 'kind': 'requires', 'premise': 'len', 'category': 'missing_premise_equal_diagonals'},
                         {'id': 'C-distinct', 'kind': 'requires', 'premise': 'distinct', 'category': 'degenerate_case_ignored'},
                         {'id': 'C-perp', 'kind': 'forbids', 'premise': 'perp', 'category': 'unjustified_premise'},
                         {'id': 'C-convex', 'kind': 'forbids', 'premise': 'convex', 'category': 'unnecessary_assumption'}],
         'expected_set': ['distinct', 'len', 'mid'],
         'hints': ['Was folgt aus dem gemeinsamen Mittelpunkt allein?', 'Welche Eigenschaft unterscheidet ein Rechteck von einem beliebigen Parallelogramm?'],
         'solution': ['Gleicher Mittelpunkt ⇒ die Diagonalen PQ und UV halbieren einander ⇒ Parallelogramm.', 'Gleiche Länge d ⇒ gleich lange Diagonalen ⇒ Rechteck.', 'Verschiedene Paare ⇒ vier Punkte, also überhaupt ein Viereck. Konvexität und Senkrechtstehen werden nicht gebraucht.'],
         'similar': 'm-similar', 'visual': {'kind': 'quad', 'show': ['rect']}},
        {'id': 'm-contrast', 'role': 'contrast', 'kc_id': 'math/inscribed-rectangle', 'type': 'choice', 'title': 'Kontrast: gleicher Mittelpunkt, verschiedene Länge',
         'prompt': 'P = (3; 1), Q = (−3; −1), U = (1; 2), V = (−1; −2). Beide Sehnen haben den Mittelpunkt (0; 0). Ist PUQV ein Rechteck?',
         'options': [{'value': 'para', 'label': 'Nein: |PQ| = √40, |UV| = √20 – nur ein Parallelogramm.'}, {'value': 'rect', 'label': 'Ja, der gemeinsame Mittelpunkt genügt.', 'category': 'missing_premise_equal_diagonals'}],
         'correct': 'para', 'hints': [], 'solution': ['Die Diagonalen halbieren sich, sind aber verschieden lang: Parallelogramm, kein Rechteck.'], 'quad': {'P': [3, 1], 'Q': [-3, -1], 'U': [1, 2], 'V': [-1, -2]}},
        {'id': 'm-similar', 'role': 'similar', 'kc_id': 'math/inscribed-rectangle', 'type': 'steps', 'title': 'Ähnliche Aufgabe ohne Hinweise: das vierte Eck',
         'prompt': f'P = ({f(P[0])}; {f(P[1])}), Q = ({f(Q[0])}; {f(Q[1])}), U = ({f(U[0])}; {f(U[1])}). Die Sehne UV soll denselben Mittelpunkt wie PQ haben. Berechnen Sie M und V; prüfen Sie dann, ob PUQV ein Rechteck ist (|PQ|² und |UV|²).',
         'steps': [{'id': 'mx', 'label': 'Mₓ', 'expected': Mx, 'tolerance': 1e-6}, {'id': 'my', 'label': 'M_y', 'expected': My, 'tolerance': 1e-6},
                   {'id': 'vx', 'label': 'Vₓ', 'expected': V[0], 'tolerance': 1e-6, 'errors': [{'value': U[0] - Mx, 'category': 'reflection_error'}, {'value': Mx - U[0], 'category': 'reflection_error'}]},
                   {'id': 'vy', 'label': 'V_y', 'expected': V[1], 'tolerance': 1e-6, 'errors': [{'value': U[1] - My, 'category': 'reflection_error'}, {'value': My - U[1], 'category': 'reflection_error'}]},
                   {'id': 'pq2', 'label': '|PQ|²', 'expected': dPQ ** 2, 'tolerance': 1e-6}, {'id': 'uv2', 'label': '|UV|²', 'expected': dUV ** 2, 'tolerance': 1e-6}],
         'hints': [], 'solution': [f'M = ({f(Mx)}; {f(My)}), V = 2M − U = ({f(V[0])}; {f(V[1])}).', f'|PQ|² = {f(dPQ ** 2)} = |UV|²: gleich lange, sich halbierende Diagonalen ⇒ Rechteck.'],
         'quad': {'P': list(P), 'Q': list(Q), 'U': list(U), 'V': list(V)}},
        {'id': 'm-transfer', 'role': 'transfer', 'kc_id': 'math/inscribed-rectangle', 'type': 'choice', 'title': 'Transfer: eine zusätzliche Bedingung',
         'prompt': 'Zwei Sehnen haben denselben Mittelpunkt, sind gleich lang und stehen senkrecht aufeinander. Was ist das Viereck aus ihren Endpunkten genau?',
         'options': [{'value': 'square', 'label': 'Ein Quadrat.'}, {'value': 'rect', 'label': 'Ein Rechteck, mehr lässt sich nicht sagen.', 'category': 'incomplete_classification'},
                     {'value': 'rhombus', 'label': 'Eine Raute, aber kein Rechteck.', 'category': 'rhombus_confused'}],
         'correct': 'square', 'hints': [], 'solution': ['Halbierend + gleich lang ⇒ Rechteck; halbierend + senkrecht ⇒ Raute; beides ⇒ Quadrat.'], 'quad': {'P': [2, 0], 'Q': [-2, 0], 'U': [0, 2], 'V': [0, -2]}},
        {'id': 'm-harder', 'role': 'harder', 'kc_id': 'math/chord-lift', 'type': 'steps', 'title': 'Anspruchsvoller: den Raumpunkt eines Paares berechnen',
         'prompt': 'P = (1,160; 0,000), Q = (−0,799; 0,439) auf der Kurve des Labs. Berechnen Sie den Raumpunkt (Mₓ, M_y, d) mit d = |PQ| (3 Nachkommastellen).',
         'steps': [{'id': 'mx', 'label': 'Mₓ', 'expected': round((1.160 - 0.799) / 2, 4), 'tolerance': 0.0006}, {'id': 'my', 'label': 'M_y', 'expected': round(0.439 / 2, 4), 'tolerance': 0.0006},
                   {'id': 'd', 'label': 'd', 'expected': round(math.dist((1.160, 0.0), (-0.799, 0.439)), 4), 'tolerance': 0.0006,
                    'errors': [{'value': round(math.dist((1.160, 0.0), (-0.799, 0.439)) / 2, 4), 'category': 'half_chord'}]}],
         'hints': [], 'solution': [f'M = ({f((1.160 - 0.799) / 2, 4)}; {f(0.439 / 2, 4)}), d = √((1,160 + 0,799)² + 0,439²) = {f(math.dist((1.160, 0.0), (-0.799, 0.439)), 4)}.']},
        {'id': 'm-retest', 'role': 'retest', 'kc_id': 'math/inscribed-rectangle', 'type': 'choice', 'title': 'Spätere Prüfung',
         'prompt': 'Ohne Hilfen: Zwei verschiedene Sehnen halbieren einander und sind gleich lang. Was bilden ihre vier Endpunkte?',
         'options': [{'value': 'rect', 'label': 'Ein Rechteck.'}, {'value': 'para', 'label': 'Nur ein Parallelogramm.', 'category': 'missing_premise_equal_diagonals'}, {'value': 'square', 'label': 'Ein Quadrat.', 'category': 'unjustified_premise'}],
         'correct': 'rect', 'hints': [], 'solution': ['Rechteck: sich halbierende, gleich lange Diagonalen.']},
        {'id': 'm-why', 'role': 'open', 'kc_id': 'math/inscribed-rectangle', 'type': 'open', 'title': 'In eigenen Worten',
         'prompt': 'Schreiben Sie den Beweisschritt in zwei bis drei Sätzen auf: von „gleicher Raumpunkt“ zu „Rechteck“.', 'hints': [], 'solution': []},
    ]
    return {
        'schema': SCHEMA, 'id': 'math/rectangle-argument-track', 'version': 1, 'domain': 'mathematics', 'lab': 'math/inscribed-rectangle',
        'title': 'Vom Raumpunkt zum Rechteck – ein Beweisschritt, adaptiv', 'objective': 'Sie können begründen, welche Voraussetzungen aus zwei Sehnen ein Rechteck machen, und fehlende oder unnötige Voraussetzungen erkennen.',
        'kcs': [{'id': 'prereq/quadrilateral-diagonals', 'type': 'prerequisite', 'label': 'Vierecke über ihre Diagonalen erkennen'},
                {'id': 'math/inscribed-rectangle', 'type': 'argument', 'label': 'Beweisschritt: gleicher Raumpunkt ⇒ Rechteck'},
                {'id': 'math/chord-lift', 'type': 'procedural', 'label': 'Raumpunkt eines Punktpaares berechnen'}],
        'context': {}, 'categories': cats, 'tasks': tasks, 'flow': ['m-pre', 'm-core', 'm-similar', 'm-transfer', 'm-harder'],
        'worked_examples': {'prereq/quadrilateral-diagonals': {'title': 'Durchgerechnet: Diagonalen und Vierecksarten', 'steps': ['Diagonalen halbieren einander ⇔ Parallelogramm.', 'Zusätzlich gleich lang ⇔ Rechteck. Zusätzlich senkrecht ⇔ Raute. Beides ⇔ Quadrat.', 'Beispiel: (2;1), (−1;2), (−2;−1), (1;−2): Diagonalen halbieren sich in (0;0), beide haben Länge √20 ⇒ Rechteck.']}},
        'contrasts': {'parallelogram_vs_rectangle': {'title': 'Parallelogramm und Rechteck nebeneinander', 'rows': [['Parallelogramm', 'Diagonalen halbieren einander', 'Längen beliebig'], ['Rechteck', 'Diagonalen halbieren einander', 'und sind gleich lang']],
                                                     'example': 'Gleicher Raumpunkt heißt: gleicher Mittelpunkt UND gleiche Höhe d. Die Höhe d ist genau die Länge – sie macht aus dem Parallelogramm das Rechteck.'}},
        'anki_tags': ['em::lernstrecke::rechteck'], 'sources': spec['sources'],
        'source_status': 'Referenz-Fixture (keine Vorlesung); elementare Vierecksgeometrie, exakt geprüft.',
    }


def all_tracks(ent_data=None):
    from .anki_bridge import review_cards, review_tags
    out = [ml_track(), ent_track(ent_data), math_track()]
    for t in out:
        t['review_tags'] = review_tags(t); t['review_cards'] = review_cards(t)
    return out


# ------------------------------------------------------------------ validation

class TrackError(ValueError):
    pass


def _answer_for(task):
    t = task['type']
    if t == 'numeric':
        return repr(task['expected'])
    if t == 'expression':
        return task['expected_expr']
    if t == 'steps':
        return {s['id']: repr(s['expected']) for s in task['steps']}
    if t == 'choice':
        return task['correct']
    if t == 'constraints':
        return task['expected_set']
    return 'x'


def validate(track):
    """Every expected answer must diagnose as correct, every bug value as its own category, every flow id must exist."""
    probs = []
    ids = {t['id'] for t in track['tasks']}
    for tid in track['flow']:
        if tid not in ids:
            probs.append(f'flow: unknown task {tid}')
    for t in track['tasks']:
        if t['kc_id'] not in {k['id'] for k in track['kcs']}:
            probs.append(f'{t["id"]}: kc {t["kc_id"]} not declared')
        for ref in ('prereq_retry', 'similar'):
            if t.get(ref) and t[ref] not in ids:
                probs.append(f'{t["id"]}: {ref} -> unknown task')
        if t['type'] == 'open':
            continue
        d = D.diagnose(t, _answer_for(t))
        if d['result'] != 'correct':
            probs.append(f'{t["id"]}: expected answer diagnosed as {d["result"]}')
        bugs = []
        if t['type'] == 'numeric':
            bugs = [(repr(e['value']), e['category']) for e in t.get('errors', [])]
        elif t['type'] == 'expression':
            bugs = [(b['expr'], b['category']) for b in t.get('bugs', [])]
        elif t['type'] == 'choice':
            bugs = [(o['value'], o['category']) for o in t['options'] if o.get('category')]
        for ans, cat in bugs:
            got = D.diagnose(t, ans)['error_category']
            if got != cat:
                probs.append(f'{t["id"]}: bug {ans!r} diagnosed as {got}, expected {cat}')
        for cid in _cats_of(t):
            if cid not in track['categories'] and cid not in ('sign_error', 'unit_scale', 'rounding', 'constant_factor', 'unclassified'):
                probs.append(f'{t["id"]}: category {cid} not defined')
    for cid, c in track['categories'].items():
        for key in ('support', 'contrast'):
            s = c.get(key)
            if s and s['type'] == 'worked_example' and s['ref'] not in track['worked_examples']:
                probs.append(f'category {cid}: worked example {s["ref"]} missing')
            if s and s['type'] == 'contrast' and s['ref'] not in track.get('contrasts', {}):
                probs.append(f'category {cid}: contrast {s["ref"]} missing')
    if probs:
        raise TrackError('; '.join(probs))
    return True


def _cats_of(t):
    out = [e['category'] for e in t.get('errors', [])] + [b['category'] for b in t.get('bugs', [])] + [o['category'] for o in t.get('options', []) if o.get('category')]
    out += [c['category'] for c in t.get('constraints', [])]
    for s in t.get('steps', []):
        out += [e['category'] for e in s.get('errors', [])]
    return out
