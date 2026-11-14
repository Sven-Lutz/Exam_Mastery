"""Connect diagnosed errors to Anki without a second scheduler.

Exam Mastery diagnoses; Anki schedules. The bridge writes a small deck of retrieval cards (understanding and
application, not definitions lists) through the existing anki_v2.build_deck, so identities are stable
(GUID = hash('referenz', 'lernstrecken', key)) and re-imports update notes in place, keeping scheduling and history.
Each card carries the tags em::lernstrecke::<track> and em::fehler::<category>. After a diagnosed error the workbench
names the tag; the learner can review exactly those cards in Anki (Browse: tag:em::fehler::end_balance_vs_minimum, or a
filtered deck). Exam Mastery never writes to the learner's collection.
"""
from .. import anki_v2

COURSE, CHAPTER, DECK = 'referenz', 'lernstrecken', 'Exam Mastery::Lernstrecken'

CARDS = [
    {'key': 'backprop/hidden-weight-gradient', 'kind': 'math', 'front': 'Woraus besteht ∂L/∂w₁₁ für ein Gewicht der verdeckten Schicht eines 2-2-1-Netzes?',
     'answer': 'δ_o · v₁ · f′(z₁) · x₁', 'explanation': 'Ein Faktor je Glied der Kette L → ŷ → z_o → a₁ → z₁ → w₁₁.', 'pitfall': 'x₁ vergessen: ∂z₁/∂w₁₁ = x₁ ist das letzte Glied.',
     'tags': ['lernstrecke::backprop', 'fehler::missing_input_factor', 'fehler::chain_incomplete']},
    {'key': 'backprop/zero-input', 'kind': 'mechanism', 'front': 'Warum ändert ein Gradientenschritt w₁₁ nicht, wenn x₁ = 0 ist?',
     'answer': 'Weil ∂L/∂w₁₁ den Faktor x₁ enthält und damit null ist.', 'tags': ['lernstrecke::backprop', 'fehler::missing_input_factor']},
    {'key': 'backprop/activation-derivative', 'kind': 'condition', 'front': 'Welche Ableitung steht in der Kette, wenn die verdeckte Schicht tanh statt sigmoid nutzt?',
     'answer': 'tanh′(z) = 1 − a² statt a(1 − a).', 'tags': ['lernstrecke::backprop', 'fehler::wrong_activation_derivative', 'fehler::missing_activation_derivative']},
    {'key': 'backprop/output-vs-hidden', 'kind': 'compare', 'front': 'Worin unterscheidet sich ∂L/∂v₁ von ∂L/∂w₁₁?',
     'answer': '∂L/∂v₁ = δ_o·a₁; ∂L/∂w₁₁ = δ_o·v₁·f′(z₁)·x₁ – der Fehler muss erst durch v₁ und f′ zurück.', 'tags': ['lernstrecke::backprop', 'fehler::output_weight_formula']},
    {'key': 'backprop/update-direction', 'kind': 'math', 'front': 'w = 0,4, ∂L/∂w = 0,2, η = 0,5: Welchen Wert hat w nach einem Schritt?',
     'answer': '0,3 (θ − η·∂L/∂θ).', 'pitfall': 'Plus statt minus: Der Verlust steigt.', 'tags': ['lernstrecke::backprop', 'fehler::update_direction']},
    {'key': 'liquidity/need-vs-end', 'kind': 'misconception', 'front': 'Warum ist der Finanzierungsbedarf nicht der Endsaldo der Liquiditätsplanung?',
     'answer': 'Bedarf ist der Betrag des tiefsten kumulierten Standes; davor wäre das Unternehmen sonst zahlungsunfähig.',
     'example': 'Kapitel 7: Tiefpunkt −2.144 k€ (P7), Endsaldo −2.136 k€.', 'source': '07 Business Planning & Effectuation.pdf S. 21',
     'tags': ['lernstrecke::liquiditaet', 'fehler::end_balance_vs_minimum']},
    {'key': 'liquidity/positive-end', 'kind': 'math', 'front': 'Cashflows −90, −40, −40, +60, +60, +60 k€: Wie hoch ist der Finanzierungsbedarf trotz positivem Endsaldo?',
     'answer': '170 k€ (Tiefpunkt nach Periode 3).', 'tags': ['lernstrecke::liquiditaet', 'fehler::end_balance_vs_minimum', 'fehler::period_vs_cumulative']},
    {'key': 'liquidity/later-payment', 'kind': 'condition', 'front': 'Was passiert mit dem Finanzierungsbedarf, wenn Kunden eine Periode später zahlen (Aufträge nicht negativ)?',
     'answer': 'Er steigt oder bleibt gleich; sinken kann er nicht.', 'explanation': 'Gleich bleibt er etwa, wenn der Tiefpunkt vor der ersten betroffenen Einzahlung liegt.',
     'tags': ['lernstrecke::liquiditaet', 'fehler::overgeneralised_strict', 'fehler::direction_confused']},
    {'key': 'rectangle/premises', 'kind': 'condition', 'front': 'Welche zwei Eigenschaften zweier verschiedener Sehnen machen ihre Endpunkte zu einem Rechteck?',
     'answer': 'Gleicher Mittelpunkt und gleiche Länge.', 'pitfall': 'Nur gleicher Mittelpunkt ergibt ein Parallelogramm.',
     'tags': ['lernstrecke::rechteck', 'fehler::missing_premise_equal_diagonals', 'fehler::diagonal_bisection_overclaimed']},
    {'key': 'rectangle/fourth-corner', 'kind': 'math', 'front': 'Sehne PQ hat den Mittelpunkt M = (0; 2), U = (1; 4). Wo liegt V, damit UV denselben Mittelpunkt hat?',
     'answer': 'V = 2M − U = (−1; 0).', 'tags': ['lernstrecke::rechteck', 'fehler::reflection_error']},
]


def review_tags(track):
    """category -> anki tag, only for categories that have at least one card."""
    have = {t for c in CARDS for t in c['tags']}
    return {cid: f'em::fehler::{cid}' for cid in track['categories'] if f'fehler::{cid}' in have}


def review_cards(track):
    """category -> the cards that train it (front and key only; the answer stays in Anki)."""
    out = {}
    for cid in track['categories']:
        cs = [{'key': c['key'], 'front': c['front']} for c in CARDS if f'fehler::{cid}' in c['tags']]
        if cs:
            out[cid] = cs
    return out


def build(out_dir, state_dir=None):
    return anki_v2.build_deck(CARDS, DECK, COURSE, CHAPTER, out_dir, state_dir=state_dir)
