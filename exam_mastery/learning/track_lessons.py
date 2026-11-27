"""Prerequisite micro-lessons (schema em-lesson-v1, see guided.py) for the reference tracks and the attention unit.

Every number in an example or check is computed here, never typed in; guided.validate_lessons re-diagnoses each
check (expected answer -> correct, each wrong answer -> its category) and rejects a lesson that contains an answer key
of an evidence task. Content status: own derivations, standard calculus; not independently reviewed
(HUMAN_REVIEW_PENDING like the tracks themselves).
"""
import math

from ..labs import build as B

f = B._fmt
P4 = lambda v: f(v, 4)


def _softmax(z):
    m = max(z); e = [math.exp(x - m) for x in z]; s = sum(e)
    return [x / s for x in e]


# ------------------------------------------------------------------ machine learning: backpropagation

def ml_lessons():
    a, a_chk = 0.8, 0.9
    w0 = 2.0; u0 = 2 * w0 - 1                       # chain-rule check: L = (2w - 1)^2 at w = 2
    return [
        {'id': 'prereq/chain-rule', 'title': 'Kettenregel: Ableitungen entlang eines Weges',
         'explain': 'Hängt eine Größe L über Zwischengrößen von w ab, ist ∂L/∂w das Produkt der lokalen Ableitungen '
                    'entlang dieses Weges. Jedes Glied beantwortet: Wie stark ändert sich die nächste Größe, wenn die '
                    'vorige ein wenig wächst? Fehlt ein Glied, fehlt ein Faktor.',
         'formula': 'L(u(w)) ⇒ dL/dw = dL/du · du/dw',
         'example': ['L = (3w + 1)². Zwischengröße u = 3w + 1, also L = u².',
                     'Äußeres Glied: dL/du = 2u. Inneres Glied: du/dw = 3.',
                     'An der Stelle w = 1: u = 4, dL/dw = 2 · 4 · 3 = 24.',
                     'Im Netz ist es dieselbe Rechnung, nur mit mehr Gliedern: L → ŷ → z_o → a₁ → z₁ → w₁₁.'],
         'check': {'type': 'numeric', 'prompt': f'L = (2w − 1)². Wie groß ist dL/dw an der Stelle w = {f(w0)}?',
                   'expected': 2 * u0 * 2, 'tolerance': 1e-6,
                   'errors': [{'value': 2 * u0, 'category': 'inner_derivative_missing',
                               'feedback': f'{f(2 * u0)} ist nur das äußere Glied dL/du = 2u. Es fehlt das innere Glied du/dw = 2.'},
                              {'value': u0 ** 2, 'category': 'value_not_derivative',
                               'feedback': f'{f(u0 ** 2)} ist der Wert von L, nicht seine Steigung.'}],
                   'explain': f'u = 2·{f(w0)} − 1 = {f(u0)}; dL/dw = 2u · 2 = {f(4 * u0)}.'},
         'for': {'kcs': ['ml/backpropagation'], 'categories': ['chain_incomplete', 'missing_downstream_weight', 'output_weight_formula', 'wrong_path']},
         'taught_in': [{'kind': 'worked_example', 'ref': 'ml/backpropagation', 'label': 'Durchgerechnet: ∂L/∂v₁ und der Schritt nach innen'},
                       {'kind': 'external', 'label': 'Lehrbuch der Einheit, Abschnitt Backpropagation (Kettenregel über mehrere Wege)'}]},
        {'id': 'prereq/sigmoid-derivative', 'title': 'Ableitung der Sigmoidfunktion',
         'explain': 'Die Sigmoidfunktion σ(z) = 1/(1 + e^(−z)) hat eine Ableitung, die sich durch ihren eigenen Wert '
                    'ausdrücken lässt. Backpropagation braucht deshalb nur die Aktivierung a = σ(z) aus der '
                    'Vorwärtsrechnung – das ist das Glied σ′(z₁) in der Kette.',
         'formula': 'σ′(z) = σ(z)·(1 − σ(z)) = a·(1 − a)',
         'example': ['σ(z) = (1 + e^(−z))^(−1). Kettenregel: σ′(z) = e^(−z) / (1 + e^(−z))².',
                     'Weil e^(−z) / (1 + e^(−z)) = 1 − σ(z) ist, folgt σ′(z) = σ(z)·(1 − σ(z)).',
                     f'Zahlen: a = σ(z) = {f(a, 1)} ⇒ σ′(z) = {f(a, 1)} · {f(1 - a, 1)} = {f(a * (1 - a), 2)}.',
                     'Am steilsten bei a = 0,5 (σ′ = 0,25); nahe 0 oder 1 wird die Steigung klein.'],
         'check': {'type': 'numeric', 'prompt': f'Ein Neuron hat die Aktivierung a = σ(z) = {f(a_chk, 1)}. Wie groß ist σ′(z)?',
                   'expected': round(a_chk * (1 - a_chk), 6), 'tolerance': 0.0005,
                   'errors': [{'value': a_chk, 'category': 'value_not_derivative',
                               'feedback': f'{f(a_chk, 1)} ist σ(z) selbst, nicht die Steigung. Setzen Sie a in a·(1 − a) ein.'},
                              {'value': round(1 - a_chk, 6), 'category': 'one_minus_only',
                               'feedback': f'{f(1 - a_chk, 1)} ist nur 1 − a. Die Ableitung ist das Produkt a·(1 − a).'},
                              {'value': round(a_chk ** 2, 6), 'category': 'squared',
                               'feedback': f'{f(a_chk ** 2, 2)} = a². Gesucht ist a·(1 − a), nicht a·a.'}],
                   'explain': f'σ′(z) = {f(a_chk, 1)} · (1 − {f(a_chk, 1)}) = {f(a_chk * (1 - a_chk), 2)}: nahe der Sättigung ist die Steigung klein.'},
         'for': {'kcs': ['ml/backpropagation'], 'categories': ['sigmoid_derivative_unknown', 'missing_activation_derivative', 'wrong_activation_derivative']},
         'taught_in': [{'kind': 'worked_example', 'ref': 'prereq/sigmoid-derivative', 'label': 'Durchgerechnet: σ′ aus σ'},
                       {'kind': 'task', 'ref': 'ml-pre2', 'label': 'Übung zur Voraussetzung mit neuer Zahl'}]},
    ]


# ------------------------------------------------------------------ AI: scaled dot-product attention

def attention_lessons():
    ex = _softmax([1, 0]); chk = [0, 1, 1]; a_chk = _softmax(chk)[0]
    al = [0.6, 0.3, 0.1]
    zm = [0, 0, 3]; after = _softmax(zm)[0]
    return [
        {'id': 'prereq/softmax-normalisation', 'title': 'Softmax: aus Scores werden Gewichte',
         'explain': 'Softmax macht aus beliebigen Scores positive Gewichte mit Summe eins: erst jeden Eintrag '
                    'exponentieren, dann durch die Summe der Exponentialwerte teilen. Direktes Teilen der Scores '
                    'scheitert, sobald ein Score negativ oder null ist.',
         'formula': 'α_j = e^(z_j) / Σ_ℓ e^(z_ℓ)',
         'example': ['z = (1; 0).', f'e¹ = {P4(math.e)}, e⁰ = 1, Summe {P4(math.e + 1)}.',
                     f'α = ({P4(ex[0])}; {P4(ex[1])}); beide positiv, Summe eins.'],
         'check': {'type': 'numeric', 'prompt': 'Eine Zeile hat die Logits z = (0; 1; 1). Wie groß ist α₁? (4 Nachkommastellen)',
                   'expected': round(a_chk, 6), 'tolerance': 0.0005,
                   'errors': [{'value': 0.0, 'category': 'linear_normalisation',
                               'feedback': 'Sie haben die Scores direkt geteilt (0/2). Softmax teilt Exponentialwerte: e⁰ / (e⁰ + e¹ + e¹).'},
                              {'value': 1.0, 'category': 'missing_normalisation',
                               'feedback': '1 = e⁰ ist der Zähler allein. Teilen Sie durch die Summe aller Exponentialwerte der Zeile.'}],
                   'explain': f'α₁ = 1 / (1 + 2e) = 1 / {P4(1 + 2 * math.e)} = {P4(a_chk)}.'},
         'for': {'kcs': ['attention/scaled-weights', 'attention/shift-scale', 'attention/masking'], 'categories': ['linear_normalisation', 'missing_normalisation']},
         'taught_in': [{'kind': 'worked_example', 'ref': 'prereq/softmax-normalisation', 'label': 'Durchgerechnet: Softmax einer Zeile'},
                       {'kind': 'task', 'ref': 'att-pre2', 'label': 'Übung zur Voraussetzung mit neuen Zahlen'}]},
        {'id': 'prereq/sqrt-dk-scaling', 'title': 'Warum durch √d_k teilen?', 'requires': ['prereq/softmax-normalisation'],
         'explain': 'Ein Skalarprodukt q·k aus d_k unabhängigen Komponenten mit Mittelwert 0 und Varianz 1 hat die '
                    'Varianz d_k, also die Standardabweichung √d_k. Teilen durch √d_k bringt die Scores auf '
                    'Standardabweichung 1 – sonst wird Softmax bei großem d_k fast zu einem Maximum.',
         'formula': 'Var(q·k) = Σ_i Var(q_i·k_i) = d_k  ⇒  z = q·k / √d_k hat Varianz 1',
         'example': ['d_k = 64: Die Scores streuen mit √64 = 8.',
                     f'Ohne Skalierung stehen sich typische Scores 8 und 0 gegenüber: e⁸ ≈ {f(math.exp(8), 0)} gegen 1 – fast alles Gewicht auf einem Key.',
                     f'Mit Skalierung 1 und 0: e¹ ≈ {f(math.e, 2)} gegen 1 – die Zeile bleibt weich, Gradienten bleiben brauchbar.'],
         'check': {'type': 'choice', 'prompt': 'Es gilt d_k = 25. Durch welche Zahl wird jeder Score vor Softmax geteilt?',
                   'options': [{'value': '5', 'label': '5'},
                               {'value': '25', 'label': '25', 'category': 'scaled_by_dk',
                                'feedback': 'Teilen durch d_k = 25 drückt die Varianz auf 1/25: Die Gewichte würden zu flach. Der Faktor ist √d_k.'},
                               {'value': '1', 'label': 'gar nicht (1)', 'category': 'missing_scaling',
                                'feedback': 'Ohne Teilen streuen die Scores mit √25 = 5: Die Gewichte würden zu spitz.'}],
                   'correct': '5', 'explain': '√25 = 5: Dann hat q·k / 5 die Standardabweichung 1.'},
         'for': {'kcs': ['attention/scaled-weights'], 'categories': ['missing_scaling', 'scaled_by_dk']},
         'taught_in': [{'kind': 'worked_example', 'ref': 'attention/scaled-weights', 'label': 'Durchgerechnet: von S zu A'},
                       {'kind': 'external', 'label': 'Vaswani et al. (2017), §3.2.1, Fußnote 4'}]},
        {'id': 'prereq/softmax-jacobian', 'title': 'Ableitung einer Softmax-Zeile', 'requires': ['prereq/softmax-normalisation'],
         'explain': 'Alle Gewichte einer Zeile teilen sich denselben Nenner D = Σ_r e^(z_r). Erhöht man ein z_ℓ, wächst '
                    'D, und alle anderen Gewichte schrumpfen. Die Quotientenregel liefert deshalb zwei Fälle: auf der '
                    'Diagonale und daneben.',
         'formula': '∂α_j/∂z_ℓ = α_j(δ_jℓ − α_ℓ): α_j(1 − α_j) für j = ℓ, −α_j·α_ℓ für j ≠ ℓ',
         'example': ['Quotientenregel: (u/D)′ = (u′·D − u·D′) / D².',
                     'j = ℓ: u = e^(z_j), u′ = D′ = e^(z_j) ⇒ α_j − α_j² = α_j(1 − α_j).',
                     'j ≠ ℓ: u′ = 0, D′ = e^(z_ℓ) ⇒ −α_j·α_ℓ (nur der Nenner wirkt).',
                     'Zahlen α = (0,5; 0,3; 0,2): ∂α₁/∂z₁ = 0,5 · 0,5 = 0,25; ∂α₁/∂z₂ = −0,5 · 0,3 = −0,15.'],
         'check': {'type': 'numeric', 'prompt': f'Eine Zeile hat die Gewichte α = ({f(al[0], 1)}; {f(al[1], 1)}; {f(al[2], 1)}). Wie groß ist ∂α₂/∂z₁?',
                   'expected': round(-al[1] * al[0], 6), 'tolerance': 0.0005,
                   'errors': [{'value': 0.0, 'category': 'offdiag_zero',
                               'feedback': 'z₁ steht nicht im Zähler von α₂, aber im gemeinsamen Nenner: Der Eintrag ist −α₂α₁, nicht null.'},
                              {'value': round(al[1] * al[0], 6), 'category': 'jacobian_sign',
                               'feedback': 'Der Betrag stimmt, das Vorzeichen nicht: Der Nenner-Term geht mit Minus ein.'},
                              {'value': round(al[1] * (1 - al[1]), 6), 'category': 'diagonal_formula_offdiag',
                               'feedback': 'α₂(1 − α₂) gilt nur für ∂α₂/∂z₂, nicht für einen Eintrag neben der Diagonale.'}],
                   'explain': f'∂α₂/∂z₁ = −α₂·α₁ = −{f(al[1], 1)} · {f(al[0], 1)} = {f(-al[1] * al[0], 2).replace("-", "−")}.'},
         'for': {'kcs': ['attention/softmax-gradient'], 'categories': ['normaliser_ignored', 'diagonal_only', 'jacobian_sign', 'missing_weight_factor', 'offdiag_zero', 'diagonal_formula_offdiag']},
         'taught_in': [{'kind': 'worked_example', 'ref': 'attention/softmax-gradient', 'label': 'Durchgerechnet: Gradient durch Softmax mit zwei Keys'}]},
        {'id': 'prereq/masked-softmax', 'title': 'Maske vor der Normierung', 'requires': ['prereq/softmax-normalisation'],
         'explain': 'Ein maskierter Key bekommt vor Softmax das Logit −∞: e^(−∞) = 0 fällt aus Zähler und Nenner. '
                    'Normiert wird also nur über die erlaubten Keys; ihre Gewichte summieren sich wieder zu eins.',
         'formula': 'α_j = e^(z_j) / Σ_(ℓ erlaubt) e^(z_ℓ), α_j = 0 für maskierte j',
         'example': ['z = (2; 0; 9), Key 3 maskiert.', f'Erlaubt sind Keys 1–2: α = softmax(2; 0) = ({P4(_softmax([2, 0])[0])}; {P4(_softmax([2, 0])[1])}; 0).',
                     'Wer erst über alle drei normiert und dann α₃ = 0 setzt, erhält Gewichte mit Summe weit unter eins.'],
         'check': {'type': 'numeric', 'prompt': 'Logits z = (0; 0; 3), Key 3 ist maskiert. Wie groß ist α₁? (4 Nachkommastellen)',
                   'expected': 0.5, 'tolerance': 0.0005,
                   'errors': [{'value': round(after, 6), 'category': 'mask_after_softmax',
                               'feedback': 'Sie haben über alle drei Keys normiert. Der maskierte Key fällt vor Softmax heraus: Normiert wird nur über Keys 1 und 2.'}],
                   'explain': 'Nur Keys 1 und 2 zählen: α₁ = e⁰ / (e⁰ + e⁰) = 0,5.'},
         'for': {'kcs': ['attention/masking'], 'categories': ['mask_ignored', 'mask_after_softmax']},
         'taught_in': [{'kind': 'worked_example', 'ref': 'attention/masking', 'label': 'Durchgerechnet: Maske vor Softmax'}]},
    ]


def unit_attention_lessons():
    """Lessons of the attention experience unit (fixtures/experience_attention_reference.json, key `lessons`): the
    same checks, linked to the unit's misconceptions and teaching sections instead of track categories."""
    by = {l['id']: l for l in attention_lessons()}
    out = []
    for lid, comps, mis, sections in [
            ('prereq/softmax-normalisation', ['attention/softmax'], [], [('teach/softmax', 'Abschnitt „Aus beliebigen Scores werden relative Gewichte“')]),
            ('prereq/softmax-jacobian', ['attention/backprop'], ['attention/softmax-normaliser-ignored', 'attention/softmax-diagonal-only'],
             [('teach/gradient', 'Abschnitt „Wie aus großen Score-Abständen schwache Gradienten werden“'), ('teach/backprop', 'Abschnitt „Gradienten durch den ganzen Attention-Kopf“')]),
            ('prereq/masked-softmax', ['attention/masking'], ['attention/mask-after-softmax', 'attention/padding-mask-ignored'],
             [('teach/mask', 'Abschnitt „Maskieren heißt aus der Normalisierung ausschließen“')])]:
        l = dict(by[lid]); l['for'] = {'competencies': comps, 'misconceptions': mis}
        l['taught_in'] = [{'kind': 'section', 'ref': r, 'label': lbl} for r, lbl in sections]
        out.append(l)
    return out
