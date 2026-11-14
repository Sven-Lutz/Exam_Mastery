"""Build interactive labs (schema em-lab-v1) from declarative specs. Deterministic: no model call.

A spec is assembled by a builder (cashflow_spec, mlp_spec, risk_spec) from source data and didactic text.
validate() recomputes every expected answer with labs/models.py and refuses specs whose numbers disagree.
render() writes one self-contained HTML file per lab: inline CSS and JS pinned by a Content-Security-Policy hash,
no network access, a static SVG figure that also serves the PDF, and the model's assumptions and sources.
"""
import base64
import hashlib
import html
import json
import math
import re
from pathlib import Path

from . import models as M

SCHEMA = 'em-lab-v1'
TEMPLATES = Path(__file__).resolve().parent.parent / 'templates'
E = lambda s: html.escape(str(s), quote=True)
# same notation rule as mt() in em_labs.js: V_k, V_{k+1}, V^π, γ^k -> <sub>/<sup>
_MT = re.compile(r'([_^])(\{[^}]*\}|-?\d+|[A-Za-z\u03b1-\u03c9\u0391-\u03a9\u221e*\u2032]+)')
def MT(s):
    return _MT.sub(lambda m: f'<{"sub" if m[1] == "_" else "sup"}>{m[2].strip("{}")}</{"sub" if m[1] == "_" else "sup"}>', E(s))
KINDS = ('cashflow', 'mlp', 'risk', 'van_westendorp', 'chord', 'mdp', 'sequence', 'attention', 'cap_table', 'legal_check')
GENERIC = ('sequence', 'attention', 'cap_table', 'legal_check')   # one module per model in labs/ (spec, check, metrics, pedagogy, static_svg)


def generic(kind):
    import importlib
    return importlib.import_module(f'{__package__}.{kind}')


class LabError(ValueError):
    pass


DECIMAL = {'sep': ','}   # ',' German (2.144,5) or '.' (2144.5); set per chapter from the book's own convention


def _fmt(x, d=0):
    r = round(x, d)
    if DECIMAL['sep'] == '.':
        s = f'{r:.{d}f}'
    else:
        s = f'{r:,.{d}f}'.replace(',', ' ').replace('.', ',').replace(' ', '.')
    return '0' if s in ('-0', '-0,0', '-0.0') else s


# ------------------------------------------------------------------ builders

def cashflow_spec(lab_id, title, kc_ids, sources, orders, delay, cost, invest, start_cash=0, unit='k€', course='', transfer_delay=None):
    base = M.cashflow(orders, delay, cost, invest, start_cash)
    later = M.cashflow(orders, delay + 1, cost, invest, start_cash)
    td = transfer_delay if transfer_delay is not None else max(0, delay - 2)
    tr = M.cashflow(orders, td, cost, invest, start_cash)
    d = 'steigt' if later['financing_need'] > base['financing_need'] else 'sinkt' if later['financing_need'] < base['financing_need'] else 'bleibt gleich'
    return {
        'schema': SCHEMA, 'id': lab_id, 'version': 1, 'title': title, 'domain': 'business_economics', 'course': course,
        'kc_ids': kc_ids, 'objective': 'Sie können aus Zahlungszeitpunkten den kumulierten Liquiditätsverlauf und den Finanzierungsbedarf bestimmen und erklären, warum Zahlungsziele den Bedarf verändern.',
        'prerequisites': ['Unterschied zwischen Auftrag, Rechnung und Zahlung', 'Cashflow = Einzahlungen − Auszahlungen'],
        'model': {'kind': 'cashflow', 'orders': orders, 'delay': delay, 'cost': cost, 'invest': invest, 'start_cash': start_cash, 'unit': unit,
                  'equations': ['Einzahlung(t) = Auftrag(t − Zahlungsziel)', 'Auszahlung(t) = laufende Kosten(t) + Investition(t)',
                                'Cashflow(t) = Einzahlung(t) − Auszahlung(t)', 'Liquidität(t) = Anfangsliquidität + Σ Cashflow bis t',
                                'Finanzierungsbedarf = max(0; −min Liquidität(t))']},
        'params': [
            {'id': 'delay', 'label': 'Zahlungsziel A (Perioden zwischen Auftrag und Zahlung)', 'type': 'range', 'min': 0, 'max': 8, 'step': 1, 'default': delay, 'digits': 0},
            {'id': 'delayB', 'label': 'Zahlungsziel B (Vergleichsszenario)', 'type': 'range', 'min': 0, 'max': 8, 'step': 1, 'default': delay + 1, 'digits': 0},
            {'id': 'start_cash', 'label': 'Anfangsliquidität', 'type': 'number', 'min': 0, 'max': 100000, 'step': 1, 'default': start_cash, 'unit': unit, 'digits': 0},
            {'id': 'horizon', 'label': 'Betrachtungshorizont (Perioden)', 'type': 'range', 'min': 3, 'max': 16, 'step': 1, 'default': len(orders), 'digits': 0}],
        'sequence': {
            'predict': {'question': f'Die Kunden zahlen künftig eine Periode später (Zahlungsziel {delay + 1} statt {delay}). Wie verändert sich der Finanzierungsbedarf?',
                        'options': [{'value': 'steigt', 'label': 'Er steigt.'}, {'value': 'sinkt', 'label': 'Er sinkt.'}, {'value': 'bleibt gleich', 'label': 'Er bleibt gleich.'}],
                        'correct': d, 'change': [{'param': 'delay', 'to': delay}, {'param': 'delayB', 'to': delay + 1}],
                        'result_text': f'Der Finanzierungsbedarf {d}: von {_fmt(base["financing_need"])} {unit} (Szenario A, Zahlungsziel {delay}) auf {_fmt(later["financing_need"])} {unit} (Szenario B, Zahlungsziel {delay + 1}). Vergleichen Sie die beiden Linien im Diagramm.',
                        'explanation': 'Ein späteres Zahlungsziel verschiebt jede Einzahlung nach hinten, die Auszahlungen bleiben, wo sie sind. Bis die Zahlungen eintreffen, müssen mehr Perioden mit Kosten vorfinanziert werden; kein kumulierter Stand kann dadurch steigen, der tiefste Punkt sinkt oder bleibt gleich. In diesem Plan sinkt er. Strikt steigen muss der Bedarf aber nicht: Liegt der Tiefpunkt vor der ersten verschobenen Einzahlung, bleibt er gleich (bei nicht negativen Aufträgen).'},
            'tasks': [
                {'id': 'need', 'title': 'Finanzierungsbedarf ablesen und begründen', 'prompt': f'Ausgangsfall (Zahlungsziel {delay}, Anfangsliquidität {_fmt(start_cash)}): Wie hoch ist der Finanzierungsbedarf in {unit}?',
                 'expected': base['financing_need'], 'tolerance': 0.5, 'unit': unit,
                 'errors': [{'value': -base['final_balance'], 'message': f'Das ist der Betrag des Endsaldos nach Periode {len(orders)}. Der Bedarf ist der tiefste Stand der kumulierten Liquidität (Periode {base["min_period"]}), nicht der Endstand.'},
                            {'value': -base['cf'][0], 'message': 'Das ist nur der Cashflow der ersten Periode. Gesucht ist der tiefste Stand der kumulierten Summe.'}],
                 'hints': ['Gesucht ist kein einzelner Cashflow, sondern ein Stand der kumulierten Liquidität.', 'Suchen Sie in der Zeile „kumuliert“ den kleinsten Wert.', f'Der kleinste kumulierte Wert liegt in Periode {base["min_period"]}.'],
                 'solution': [f'Kumulierte Liquidität: {", ".join(_fmt(v) for v in base["balance"])} {unit}.', f'Tiefster Stand: {_fmt(base["min_balance"])} {unit} in Periode {base["min_period"]}; Finanzierungsbedarf {_fmt(base["financing_need"])} {unit}.',
                              f'Der Endsaldo ({_fmt(base["final_balance"])} {unit}) liegt höher, weil am Ende schon Zahlungen eingehen – wer nur den Endsaldo finanziert, wird vorher zahlungsunfähig.'],
                 'feedback_correct': f'Der Bedarf ist der tiefste kumulierte Stand in Periode {base["min_period"]}.'},
                {'id': 'transfer', 'title': 'Transfer: kürzeres Zahlungsziel', 'prompt': f'Das Start-up vereinbart ein Zahlungsziel von {td} Perioden, sonst bleibt alles gleich. Berechnen Sie den Finanzierungsbedarf in {unit}.',
                 'expected': tr['financing_need'], 'tolerance': 0.5, 'unit': unit,
                 'errors': [{'value': base['financing_need'], 'message': 'Das ist der Bedarf beim alten Zahlungsziel. Verschieben Sie jede Einzahlung um die neue Verzögerung.'},
                            {'value': -tr['final_balance'], 'message': 'Das ist der Endsaldo, nicht der tiefste Stand.'}],
                 'hints': ['Rechnen Sie zuerst die Einzahlungen neu: Ein Auftrag aus Periode t wird jetzt in Periode t + ' + str(td) + ' bezahlt.', 'Bilden Sie Cashflow je Periode und die laufende Summe.', 'Der Bedarf ist der Betrag des kleinsten Wertes der laufenden Summe.'],
                 'solution': [f'Kumulierte Liquidität bei Zahlungsziel {td}: {", ".join(_fmt(v) for v in tr["balance"])} {unit}.', f'Tiefster Stand {_fmt(tr["min_balance"])} {unit} (Periode {tr["min_period"]}); Bedarf {_fmt(tr["financing_need"])} {unit}.'],
                 'feedback_correct': 'Sie können den Bedarf jetzt für ein neues Zahlungsziel selbst bestimmen.'}]},
        'explanations': ['Liquidität und Gewinn sind verschieden: Ein Auftrag erhöht den Umsatz, bringt aber erst mit der Zahlung Geld.',
                         'Zur Begriffsabgrenzung: Der Cashflow ist der Zahlungssaldo einer Periode; die kumulierte Liquidität seine laufende Summe; der Finanzierungsbedarf ist der Betrag ihres tiefsten Standes. „Working Capital“ bezeichnet in der Bilanzanalyse Umlaufvermögen minus kurzfristige Verbindlichkeiten; die Vorlesung meint damit das Kapital, das zwischen Auftrag und Zahlung gebunden ist.'],
        'assumptions': ['Perioden sind gleich lang; alle Werte sind Zahlungen in der Periode.', 'Jeder Auftrag wird vollständig nach dem Zahlungsziel bezahlt; keine Ausfälle, keine Anzahlungen.', 'Keine Abschreibungen (keine Zahlung), keine Zinsen auf den Fehlbetrag.', 'Aufträge nach dem Horizont fehlen; offene Forderungen am Ende werden angezeigt, aber nicht als Einzahlung gezählt.'],
        'sources': sources, 'tests': [{'params': {'delay': delay}, 'financing_need': base['financing_need'], 'min_period': base['min_period'], 'final_balance': base['final_balance']},
                                     {'params': {'delay': delay + 1}, 'financing_need': later['financing_need']}, {'params': {'delay': td}, 'financing_need': tr['financing_need']}],
    }


def mlp_spec(lab_id='ml/backprop-2-2-1', seed=7, x=(0.5, -1.0), target=0.8, lr=0.5, course='Referenz-Lab Machine Learning'):
    p = M.mlp_init(seed=seed)
    bw = M.mlp_backward(p, list(x), target)
    q = json.loads(json.dumps(p)); q['W2'][0] = round(q['W2'][0] + 0.5, 3)
    after = M.mlp_loss(M.mlp_forward(q, list(x))['y'], target)
    d = 'steigt' if after > bw['loss'] else 'sinkt'
    x0 = [0.0, x[1]]; g0 = M.mlp_backward(p, x0, target)['grad']['W1'][0][0]
    num = lambda v, lo, hi, st=0.01: {'type': 'number', 'min': lo, 'max': hi, 'step': st, 'default': v, 'digits': 3}
    params = [dict(id='x1', label='Eingabe x₁', **num(x[0], -3, 3)), dict(id='x2', label='Eingabe x₂', **num(x[1], -3, 3)), dict(id='t', label='Zielwert t', **num(target, 0, 1)),
              dict(id='lr', label='Lernrate η', **num(lr, 0.001, 5, 0.001)),
              {'id': 'ha', 'label': 'Aktivierung verdeckte Schicht f', 'type': 'select', 'default': 'sigmoid', 'options': [{'value': k, 'label': k} for k in ('sigmoid', 'tanh', 'relu', 'linear')]},
              {'id': 'oa', 'label': 'Aktivierung Ausgabe g', 'type': 'select', 'default': 'sigmoid', 'options': [{'value': k, 'label': k} for k in ('sigmoid', 'linear')]}]
    for k, v in (('w11', p['W1'][0][0]), ('w12', p['W1'][0][1]), ('w21', p['W1'][1][0]), ('w22', p['W1'][1][1]), ('b1', p['b1'][0]), ('b2', p['b1'][1]), ('v1', p['W2'][0]), ('v2', p['W2'][1]), ('c', p['b2'])):
        params.append(dict(id=k, label=f'Parameter {k}', **num(v, -5, 5, 0.001)))
    return {
        'schema': SCHEMA, 'id': lab_id, 'version': 1, 'title': 'Ein neuronales Netz Schritt für Schritt: Vorwärtsrechnung, Backpropagation, Update', 'domain': 'machine_learning', 'course': course,
        'kc_ids': ['ml/forward-pass', 'ml/backpropagation', 'ml/gradient-descent'],
        'objective': 'Sie können für ein 2-2-1-Netz Vorwärtsrechnung, Verlust, Gradienten aller Parameter und einen Gradientenschritt selbst berechnen und den Einfluss von Lernrate und Sättigung erklären.',
        'prerequisites': ['Kettenregel der Differentialrechnung', 'Ableitung der Sigmoidfunktion: σ′(z) = σ(z)(1 − σ(z))'],
        'model': {'kind': 'mlp', 'init': p, 'x': list(x), 'target': target, 'lr': lr, 'hidden_act': 'sigmoid', 'out_act': 'sigmoid', 'seed': seed,
                  'equations': ['z_j = Σ_i w_ji x_i + b_j,  a_j = f(z_j)', 'z_o = Σ_j v_j a_j + c,  ŷ = g(z_o)', 'L = ½ (ŷ − t)²', 'δ_o = (ŷ − t) g′(z_o),  ∂L/∂v_j = δ_o a_j,  ∂L/∂c = δ_o',
                                'δ_j = δ_o v_j f′(z_j),  ∂L/∂w_ji = δ_j x_i,  ∂L/∂b_j = δ_j', 'θ ← θ − η ∂L/∂θ']},
        'params': params,
        'sequence': {
            'predict': {'question': f'Sie erhöhen das Gewicht v1 um 0,5 (von {_fmt(p["W2"][0], 3)} auf {_fmt(q["W2"][0], 3)}). Was passiert mit dem Verlust L?',
                        'options': [{'value': 'steigt', 'label': 'L steigt.'}, {'value': 'sinkt', 'label': 'L sinkt.'}, {'value': 'gleich', 'label': 'L bleibt gleich.'}],
                        'correct': d, 'change': {'param': 'v1', 'to': q['W2'][0]},
                        'result_text': f'L {d}: von {_fmt(bw["loss"], 5)} auf {_fmt(after, 5)}.',
                        'explanation': f'Das Vorzeichen des Gradienten entscheidet: ∂L/∂v1 = δ_o · a₁ = {_fmt(bw["grad"]["W2"][0], 5)}. Ist er negativ, senkt eine Erhöhung von v1 den Verlust (für kleine Änderungen); genau deshalb geht der Gradientenschritt θ − η∂L/∂θ in die richtige Richtung.'},
            'tasks': [
                {'id': 'delta', 'title': 'Ausgabe-Fehlersignal berechnen', 'prompt': 'Berechnen Sie im Ausgangszustand δ_o = (ŷ − t)·σ′(z_o) = ∂L/∂c (auf 4 Nachkommastellen). Nutzen Sie die angezeigten Werte von ŷ und t.',
                 'expected': bw['delta_o'], 'tolerance': 5e-4, 'unit': '',
                 'errors': [{'value': bw['forward']['y'] - target, 'message': 'Das ist nur ŷ − t. Es fehlt der Faktor σ′(z_o) = ŷ(1 − ŷ) aus der Kettenregel.'}],
                 'hints': ['Kettenregel: ∂L/∂z_o = ∂L/∂ŷ · ∂ŷ/∂z_o.', 'Für L = ½(ŷ − t)² gilt ∂L/∂ŷ = ŷ − t; für die Sigmoidfunktion ∂ŷ/∂z_o = ŷ(1 − ŷ).', f'Setzen Sie ŷ = {_fmt(bw["forward"]["y"], 4)} und t = {_fmt(target, 2)} ein.'],
                 'solution': [f'ŷ − t = {_fmt(bw["forward"]["y"] - target, 5)}; ŷ(1 − ŷ) = {_fmt(bw["forward"]["y"] * (1 - bw["forward"]["y"]), 5)}.', f'δ_o = {_fmt(bw["delta_o"], 5)} = ∂L/∂c, weil z_o direkt von c abhängt (∂z_o/∂c = 1).'],
                 'feedback_correct': 'Das ist das Fehlersignal, das rückwärts durch das Netz weitergereicht wird.'},
                {'id': 'update', 'title': 'Einen Gradientenschritt ausführen', 'prompt': f'Berechnen Sie den neuen Bias c nach einem Schritt mit η = {_fmt(lr, 3)} (auf 4 Nachkommastellen).',
                 'expected': p['b2'] - lr * bw['delta_o'], 'tolerance': 5e-4, 'unit': '',
                 'errors': [{'value': p['b2'] + lr * bw['delta_o'], 'message': 'Vorzeichenfehler: Gradientenabstieg geht gegen den Gradienten, c_neu = c − η·∂L/∂c.'}],
                 'hints': ['Die Update-Regel lautet θ_neu = θ − η·∂L/∂θ.', 'Für c ist ∂L/∂c = δ_o.', f'c = {_fmt(p["b2"], 3)}.'],
                 'solution': [f'c_neu = {_fmt(p["b2"], 3)} − {_fmt(lr, 3)} · {_fmt(bw["delta_o"], 5)} = {_fmt(p["b2"] - lr * bw["delta_o"], 5)}.'],
                 'feedback_correct': 'Prüfen Sie mit „Einen Lernschritt ausführen“: Die Tabelle zeigt denselben Wert.'},
                {'id': 'transfer', 'title': 'Transfer: wann verschwindet ein Gradient?', 'prompt': 'Setzen Sie x₁ = 0 (x₂ bleibt). Wie groß ist dann ∂L/∂w11?',
                 'expected': g0, 'tolerance': 1e-9, 'unit': '',
                 'errors': [], 'hints': ['∂L/∂w11 = δ₁ · x₁.', 'Was ergibt ein Produkt, wenn ein Faktor 0 ist?'],
                 'solution': ['∂L/∂w11 = δ₁ · x₁ = δ₁ · 0 = 0. Ein Gewicht, dessen Eingabe 0 ist, erhält in diesem Beispiel kein Lernsignal – es ändert sich durch diesen Datenpunkt nicht.'],
                 'feedback_correct': 'Genau: Ohne Eingabe am Gewicht gibt es keinen Gradienten.'}]},
        'explanations': ['Die Lernrate η skaliert nur die Schrittweite. Zu klein: langsamer Abstieg. Zu groß: der Verlust kann springen oder steigen, weil die lineare Näherung des Gradienten nur lokal gilt.',
                         'Sättigung: Für |z| > 4 ist σ′(z) < 0,018; Gradienten, die durch eine gesättigte Einheit laufen, werden sehr klein (verschwindende Gradienten).'],
        'assumptions': ['Ein einzelner Trainingsdatenpunkt (x, t); quadratischer Verlust L = ½(ŷ − t)².', f'Startgewichte reproduzierbar aus Seed {seed}.', 'Keine Regularisierung, kein Mini-Batch.'],
        'sources': ['Eigenes Referenz-Lab; Gleichungen sind Standard-Kettenregel. Backpropagation geprüft gegen zentrale finite Differenzen.'],
        'tests': [{'params': {}, 'loss': bw['loss'], 'delta_o': bw['delta_o']}],
    }


def risk_spec(lab_id, title, kc_ids, sources, course='', classes=None):
    cl = classes or M.LECTURE_CLASSES
    A, B = (2, 5), (5, 2)                                 # same score 10, different cells
    ra, rb = M.risk_matrix(*A, cl), M.risk_matrix(*B, cl)
    corr = 'A' if M.CLASS_RANK[ra['class']] > M.CLASS_RANK[rb['class']] else 'B' if M.CLASS_RANK[rb['class']] > M.CLASS_RANK[ra['class']] else 'gleich'
    ea, eb = M.expected_loss_range(A[0], 400000), M.expected_loss_range(B[0], 10000)
    return {
        'schema': SCHEMA, 'id': lab_id, 'version': 2, 'title': title, 'domain': 'business_economics', 'course': course, 'kc_ids': kc_ids,
        'objective': 'Sie können Risiken mit der Matrix der Vorlesung einstufen und begründen, warum der Punktwert (Produkt zweier Stufen) nur eine Rangheuristik ist – weder die Klasse noch der erwartete Schaden folgen allein aus ihm.',
        'prerequisites': ['Auswirkungs- und Wahrscheinlichkeitsskala mit je fünf Stufen'],
        'model': {'kind': 'risk', 'likelihood': 3, 'impact': 4, 'loss_eur': 50000, 'classes': cl, 'compare': {'likelihood': B[0], 'impact': B[1], 'loss_eur': 10000},
                  'equations': ['Punktwert = Auswirkungsstufe × Wahrscheinlichkeitsstufe (Heuristik der Vorlesung)', 'Klasse = Feld der Matrix (Low, Moderate, High, Critical)',
                                'Erwarteter Schaden = p × Schadenshöhe, p aus dem Wahrscheinlichkeitsband der Stufe']},
        'params': [{'id': 'l', 'label': 'Wahrscheinlichkeit A (Stufe)', 'type': 'range', 'min': 1, 'max': 5, 'step': 1, 'default': 3, 'digits': 0},
                   {'id': 'i', 'label': 'Auswirkung A (Stufe)', 'type': 'range', 'min': 1, 'max': 5, 'step': 1, 'default': 4, 'digits': 0},
                   {'id': 'loss', 'label': 'Schadenshöhe A', 'type': 'number', 'min': 0, 'max': 100000000, 'step': 1000, 'default': 50000, 'unit': '€', 'digits': 0},
                   {'id': 'l2', 'label': 'Wahrscheinlichkeit B (Stufe)', 'type': 'range', 'min': 1, 'max': 5, 'step': 1, 'default': B[0], 'digits': 0},
                   {'id': 'i2', 'label': 'Auswirkung B (Stufe)', 'type': 'range', 'min': 1, 'max': 5, 'step': 1, 'default': B[1], 'digits': 0},
                   {'id': 'loss2', 'label': 'Schadenshöhe B', 'type': 'number', 'min': 0, 'max': 100000000, 'step': 1000, 'default': 10000, 'unit': '€', 'digits': 0}],
        'sequence': {
            'predict': {'question': f'Risiko A: Wahrscheinlichkeit Stufe {A[0]}, Auswirkung Stufe {A[1]}. Risiko B: Wahrscheinlichkeit Stufe {B[0]}, Auswirkung Stufe {B[1]}. Beide haben den Punktwert 10. Welches Risiko stuft die Matrix der Vorlesung höher ein?',
                        'options': [{'value': 'A', 'label': 'Risiko A'}, {'value': 'B', 'label': 'Risiko B'}, {'value': 'gleich', 'label': 'Beide gleich – der Punktwert ist ja gleich.'}],
                        'correct': corr, 'change': [{'param': 'l', 'to': A[0]}, {'param': 'i', 'to': A[1]}, {'param': 'loss', 'to': 400000}],
                        'result_text': f'Risiko A liegt im Feld „{ra["class"]}“, Risiko B im Feld „{rb["class"]}“ – bei gleichem Punktwert 10.',
                        'explanation': 'Die Matrix der Vorlesung ordnet Klassen den Feldern zu, nicht den Produkten: Eine große Auswirkung wiegt dort schwerer als eine hohe Wahrscheinlichkeit kleiner Schäden. Die Stufen sind Rangkategorien (ordinal); ihr Produkt ordnet grob vor, ist aber weder eine Klasse noch ein Erwartungswert in Euro.'},
            'tasks': [
                {'id': 'score', 'title': 'Einstufen wie in der Vorlesung', 'prompt': 'Ein Risiko ist „möglich“ (Stufe 3) und hätte „große“ Auswirkungen (Stufe 4). Welchen Punktwert ergibt die Matrix?',
                 'expected': 12, 'tolerance': 0, 'unit': '', 'errors': [{'value': 7, 'message': 'Die Stufen werden multipliziert, nicht addiert.'}],
                 'hints': ['Die Heuristik der Vorlesung verknüpft die beiden Stufen durch Multiplikation.', 'Stufe 4 mal Stufe 3.'],
                 'solution': [f'4 × 3 = 12; das Feld (Wahrscheinlichkeit 3, Auswirkung 4) ist in der Matrix „{M.risk_matrix(3, 4, cl)["class"]}“ – die Vorlesung nennt es „high“.'],
                 'feedback_correct': 'So stuft die Vorlesung ein.'},
                {'id': 'ev', 'title': 'Transfer: Erwartungswert statt Punktwert', 'prompt': 'Stufe „möglich“ bedeutet laut Vorlesung 30–70 % Eintrittswahrscheinlichkeit. Wie hoch ist der erwartete Schaden höchstens, wenn ein Eintritt 50.000 € kostet (in €)?',
                 'expected': 0.70 * 50000, 'tolerance': 0.5, 'unit': '€', 'errors': [{'value': 0.30 * 50000, 'message': 'Das ist die Untergrenze (30 %). Gefragt ist die Obergrenze.'}, {'value': 600000, 'message': 'Hier wurden Stufen mit Euro multipliziert. Der Erwartungswert verwendet die Wahrscheinlichkeit, nicht die Stufe.'}],
                 'hints': ['Erwarteter Schaden = Wahrscheinlichkeit × Schadenshöhe.', 'Für die Obergrenze nehmen Sie die obere Wahrscheinlichkeit des Bandes.'],
                 'solution': ['0,70 × 50.000 € = 35.000 € (Untergrenze 0,30 × 50.000 € = 15.000 €).'], 'feedback_correct': 'Der Erwartungswert ist ein Betrag in Euro; der Punktwert der Matrix ist nur ein Rang.'}]},
        'explanations': ['Die Stufen der Vorlesung: Wahrscheinlichkeit 1 = unter 5 %, 2 = 5–30 %, 3 = 30–70 %, 4 = 70–95 %, 5 = 95–100 % (Folie 31).',
                         f'Im Lab-Beispiel liegt der erwartete Schaden von A ({_fmt(ea[0])}–{_fmt(ea[1])} € bei 400.000 € Schaden) klar über dem von B ({_fmt(eb[0])}–{_fmt(eb[1])} € bei 10.000 €) – die Schadenshöhe steckt nicht im Punktwert.',
                         'Die Klassen der Felder wurden aus der Abbildung auf Folie 29 abgelesen (Bildauswertung durch den Agenten, nicht menschlich geprüft).'],
        'assumptions': ['Punktwert = Produkt zweier Rangstufen: eine Heuristik zur Priorisierung, kein quantitatives Risikomaß.', 'Klassen der Felder wie in der Matrix der Vorlesung (Folie 29).', 'Der Erwartungswert nutzt die Wahrscheinlichkeitsbänder der Vorlesung und eine frei wählbare Schadenshöhe.'],
        'sources': sources, 'tests': [{'params': {'l': 3, 'i': 4}, 'score': 12}],
    }


PSM_LABEL = {'pmc': 'PMC – Untergrenze', 'opp': 'OPP – „Optimaler Preis“', 'ipp': 'IPP – Indifferenzpreis', 'pme': 'PME – Obergrenze'}


def vw_spec(lab_id, title, kc_ids, sources, course='', rows=None, data_label=None):
    """Van Westendorp lab. rows default to the SYNTHETIC demo set; every number shown is computed by M.van_westendorp."""
    if rows is not None or data_label is not None:
        raise LabError('reference PSM uses declared synthetic defaults; own data stay local to browser')
    if not kc_ids or not sources:
        raise LabError('PSM requires course competencies and method source anchors')
    synthetic = True
    rows = M.psm_synthetic()
    data_label = data_label or 'SYNTHETISCHE Übungsdaten (240 erfundene Antworten, zwei Segmente A und B) – keine Befragungsergebnisse der Vorlesung'
    base = M.van_westendorp(rows, 'standard')
    shift = 10
    moved = M.van_westendorp(rows, 'standard', te_shift=shift)
    ch = {k for k in base['points'] if abs(moved['points'][k] - base['points'][k]) > 0.005}
    opts = {'all': ['opp', 'ipp', 'pmc', 'pme'], 'opp_pme': ['opp', 'pme'], 'pme': ['pme'], 'none': []}
    correct = next((k for k, v in opts.items() if set(v) == ch), None)
    if correct != 'opp_pme' or not all(moved['points'][k] > base['points'][k] for k in ch):
        raise LabError(f'prediction options do not cover the computed change {sorted(ch)}')
    # task 1: share 'too expensive' at 40 EUR for five answers
    t1 = [{'tc': 10, 'cheap': 15, 'exp': 20, 'te': v} for v in (30, 40, 40, 50, 60)]
    sh = M.psm_shares(t1, 40)['te'] * 100
    strict = sum(1 for r in t1 if r['te'] < 40) / 5 * 100; rev = sum(1 for r in t1 if r['te'] >= 40) / 5 * 100
    # task 2: crossing by linear interpolation between two price points
    x2 = M.psm_crossing([40, 50], [0.30, 0.10], [0.15, 0.35])
    # task 3 (transfer): acceptable range of segment B
    rb = M.van_westendorp(rows, 'standard', segment='B'); rba = M.van_westendorp(rows, 'alternative', segment='B')
    f = lambda x: _fmt(M._round2(x), 2)  # match JS locale display: half-up cents
    pts = base['points']
    return {
        'schema': SCHEMA, 'id': lab_id, 'version': 1, 'title': title, 'domain': 'business_economics', 'course': course, 'kc_ids': kc_ids,
        'objective': 'Sie können aus den vier Van-Westendorp-Fragen die Kurven bilden, die vier Preispunkte als Schnittpunkte bestimmen und begründen, warum der „optimale Preis“ der Methode kein umsatz- oder gewinnoptimaler Preis ist.',
        'prerequisites': ['Die vier Fragen der Methode (Vorlesung)', 'Anteile und kumulierte Häufigkeiten'],
        'model': {'kind': 'van_westendorp', 'rows': rows, 'data_label': data_label, 'synthetic': synthetic, 'data_origin': 'SYNTHETIC_DEMO_NOT_LECTURE_RESULTS' if synthetic else 'PROVIDED_ROWS_PROVENANCE_UNVERIFIED',
                  'method': 'standard', 'segments': sorted({r.get('group') for r in rows if r.get('group')}),
                  'equations': ['zu billig(p) = Anteil mit Antwort „zu billig“ ≥ p (fallend)', 'günstig(p) = Anteil mit Antwort „günstig“ ≥ p (fallend)',
                                'teuer(p) = Anteil mit Antwort „teuer“ ≤ p (steigend)', 'zu teuer(p) = Anteil mit Antwort „zu teuer“ ≤ p (steigend)',
                                'nicht günstig = 1 − günstig; nicht teuer = 1 − teuer',
                                'Standard: PMC = zu billig ∩ nicht günstig; OPP = zu billig ∩ zu teuer; IPP = günstig ∩ teuer; PME = zu teuer ∩ nicht teuer',
                                'Alternative: PMC = zu billig ∩ teuer; PME = zu teuer ∩ günstig (OPP, IPP unverändert)']},
        'params': [{'id': 'segment', 'label': 'Segment', 'type': 'select', 'default': 'all', 'options': [{'value': 'all', 'label': 'alle Befragten'}] + [{'value': g, 'label': 'Segment ' + g} for g in sorted({r.get('group') for r in rows if r.get('group')})]},
                   {'id': 'method', 'label': 'Konvention der Grenzpunkte', 'type': 'select', 'default': 'standard', 'options': [{'value': 'standard', 'label': 'Standard (wie Folie 24)'}, {'value': 'alternative', 'label': 'Praxisvariante'}]},
                   {'id': 'te_shift', 'label': 'Alle „zu teuer“-Antworten verschieben um', 'type': 'range', 'min': 0, 'max': 30, 'step': 1, 'default': 0, 'unit': '€', 'digits': 0},
                   {'id': 'probe', 'label': 'Preis prüfen', 'type': 'range', 'min': 0, 'max': base['knots'][-1], 'step': 0.5, 'default': round(pts['opp'] * 2) / 2, 'unit': '€', 'digits': 1}],
        'sequence': {
            'predict': {'question': f'Alle Befragten nennen ihre Grenze „zu teuer“ um {shift} € höher; die anderen drei Antworten bleiben gleich. Welche Preispunkte verschieben sich (Standardkonvention)?',
                        'options': [{'value': 'all', 'label': 'Alle vier Preispunkte'}, {'value': 'opp_pme', 'label': 'Nur OPP und PME'}, {'value': 'pme', 'label': 'Nur PME, die Obergrenze'}, {'value': 'none', 'label': 'Keiner – es ändert sich nur eine von vier Fragen'}],
                        'correct': correct, 'change': [{'param': 'te_shift', 'to': shift}],
                        'result_text': f'OPP steigt von {f(pts["opp"])} € auf {f(moved["points"]["opp"])} €, PME von {f(pts["pme"])} € auf {f(moved["points"]["pme"])} €; IPP ({f(pts["ipp"])} €) und PMC ({f(pts["pmc"])} €) bleiben gleich.',
                        'explanation': 'Jeder Preispunkt ist der Schnitt zweier Kurven. Nur OPP (zu billig ∩ zu teuer) und PME (zu teuer ∩ nicht teuer) enthalten die Kurve „zu teuer“. IPP und PMC hängen an anderen Fragen und bewegen sich deshalb nicht.'},
            'tasks': [
                {'id': 'share', 'title': 'Eine Kurve punktweise bilden', 'prompt': 'Fünf Befragte nennen als „zu teuer“: 30 €, 40 €, 40 €, 50 €, 60 €. Welcher Anteil empfindet einen Preis von 40 € als zu teuer (in %)?',
                 'expected': sh, 'tolerance': 0.5, 'unit': '%',
                 'errors': [{'value': strict, 'message': 'Wer 40 € als „zu teuer“ nennt, empfindet 40 € bereits als zu teuer – die Grenze zählt mit (≤, nicht <).'},
                            {'value': rev, 'message': 'Das ist die Gegenrichtung. „Zu teuer“ steigt mit dem Preis: Gezählt werden Antworten ≤ 40 €.'}],
                 'hints': ['„Zu teuer“ ist eine steigende Kurve: Bei Preis p zählen alle, deren Grenze bei p oder darunter liegt.', 'Zählen Sie die Antworten ≤ 40 € und teilen Sie durch 5.'],
                 'solution': [f'Antworten ≤ 40 €: 30, 40, 40 → 3 von 5 = {_fmt(sh, 0)} %.'], 'feedback_correct': 'So entsteht jeder Punkt der Kurve.'},
                {'id': 'cross', 'title': 'Schnittpunkt durch Interpolation', 'prompt': 'Bei 40 € gilt: zu billig 30 %, zu teuer 15 %. Bei 50 €: zu billig 10 %, zu teuer 35 %. Wo schneiden sich die Kurven bei linearer Interpolation (in €)?',
                 'expected': x2, 'tolerance': 0.05, 'unit': '€',
                 'errors': [{'value': 45, 'message': '45 € ist die Mitte des Intervalls. Der Schnitt liegt dort, wo der Abstand der Kurven auf null fällt: 15 Punkte Vorsprung schrumpfen um 40 Punkte auf 10 €.'}],
                 'hints': ['Der Abstand zu billig − zu teuer beträgt bei 40 € +15 Punkte, bei 50 € −25 Punkte.', 'Er ändert sich um 40 Punkte auf 10 €; null wird nach 15/40 des Intervalls erreicht.'],
                 'solution': [f'40 € + 10 € × 15/40 = {f(x2)} €. Dieser Schnitt ist der OPP.'], 'feedback_correct': 'Genau so berechnet das Lab alle vier Preispunkte.'},
                {'id': 'range', 'title': 'Transfer: Preisbereich eines Segments', 'prompt': 'Nach „Zurücksetzen“: Wählen Sie im Lab Segment B und die Standardkonvention. Wie breit ist der akzeptable Preisbereich PME − PMC (in €, auf 0,1 € genau)?',
                 'expected': rb['range_width'], 'tolerance': 0.1, 'unit': '€',
                 'errors': [{'value': rba['range_width'], 'message': 'Das ist die Breite nach der Praxisvariante. Gefragt ist die Standardkonvention mit den invertierten Kurven.'},
                            {'value': base['range_width'], 'message': 'Das ist der Bereich aller Befragten. Gefragt ist nur Segment B.'}],
                 'hints': ['Stellen Sie Segment B ein und lesen Sie PMC und PME in der Kennzahlenleiste ab.', 'Bilden Sie die Differenz PME − PMC.'],
                 'solution': [f'Segment B: PME {f(rb["points"]["pme"])} € − PMC {f(rb["points"]["pmc"])} € = {f(rb["range_width"])} €.'],
                 'feedback_correct': 'Segmente mit anderer Zahlungsbereitschaft haben eigene Preisbereiche; ein Durchschnitt über alle verdeckt das.'}]},
        'explanations': [
            'Folie 24 der Vorlesung stellt die vier Fragen und zwei Diagramme: links die Rohkurven, rechts mit invertierten Mittelkurven. Dort liegt der „Optimale Preis“ am Schnitt von „zu niedrig“ und „zu hoch“, der Indifferenzpreis am Schnitt der beiden Mittelkurven. Das entspricht der Standardkonvention dieses Labs (Bildauswertung durch den Agenten, nicht menschlich geprüft).',
            'Zuordnung der Fragen der Folie: „adequate, but still attractive“ = günstig; „high, but still acceptable“ = teuer; „first price … too high“ = zu teuer; „doubts concerning the quality“ = zu billig.',
            'Die Preisachse der Folie ist nicht gleichabständig (5, 8, 10, 13 … 45, 63 €). Abstände und Steigungen dort lassen sich nicht direkt vergleichen; das Lab zeichnet eine lineare Achse.',
            'Der „optimale Preis“ ist ein historischer Methodenname: Dort halten sich die Anteile „zu billig“ und „zu teuer“ die Waage. Die Methode misst Preiswahrnehmung, keine Kaufmengen; Umsatz oder Gewinn kann sie ohne weitere Daten nicht optimieren.'],
        'assumptions': [data_label + '.', 'Gültig ist eine Antwort nur mit 0 < zu billig ≤ günstig ≤ teuer ≤ zu teuer; ungültige Antworten werden gezählt und ausgeschlossen.',
                        'Kurven werden an allen beobachteten Antwortpreisen ausgewertet und dazwischen linear verbunden (Darstellungskonvention, keine stetige Nachfragefunktion).',
                        'Am Preis p wird die Grenze mitgezählt (≥ bzw. ≤; Toleranz 1e-9 Euro). Zusatzknoten: 0 und aufgerundetes 110%-Maximum.',
                        'Bei Gleichheit über mehrere Knoten wird deren Intervallmitte berichtet: Rechenkonvention, keine eindeutige Schätzung. Nicht gegen die Implementierung des R-Pakets nachgerechnet.'],
        'sources': sources, 'tests': [{'params': {'method': 'standard'}, 'points': base['points']}, {'params': {'method': 'alternative'}, 'points': M.van_westendorp(rows, 'alternative')['points']}],
    }


# ------------------------------------------------------------------ validation

def chord_spec(lab_id='math/inscribed-rectangle', course='Referenz-Lab Mathematik', s=0.0, t=0.42):
    """B16 reference: pairs of points on a closed curve -> (midpoint, distance) in 3-D; numerical rectangle search."""
    L = M.chord_lift(s, t); near = M.chord_lift(s, round(s + 0.01, 3)); P, Q = L['P'], L['Q']
    R = M.rect_search(s)[0]
    d2 = (P[0] - Q[0]) ** 2 + (P[1] - Q[1]) ** 2
    pt = lambda a: f'({_fmt(a[0], 3)}; {_fmt(a[1], 3)})'
    rng = lambda i, lab, v: {'id': i, 'label': lab, 'type': 'range', 'min': 0, 'max': 0.999, 'step': 0.001, 'default': v, 'digits': 3}
    return {
        'schema': SCHEMA, 'id': lab_id, 'version': 1, 'title': 'Rechtecke auf einer Kurve: vom Punktpaar zum Punkt im Raum', 'domain': 'mathematics', 'course': course,
        'kc_ids': ['math/chord-lift', 'math/inscribed-rectangle'],
        'objective': 'Sie können ein Punktpaar einer Kurve als Punkt (Mittelpunkt, Abstand) im Raum darstellen, begründen, warum zwei Paare mit gleichem Bildpunkt ein Rechteck bilden, und numerische Exploration von einem Beweis unterscheiden.',
        'prerequisites': ['Mittelpunkt und Abstand zweier Punkte', 'Diagonalen-Eigenschaften von Parallelogramm und Rechteck', 'Parameterdarstellung einer Kurve'],
        'model': {'kind': 'chord', 'curve': M.CURVE,
                  'equations': ['γ(u) = r(u)·(cos 2πu, sin 2πu)', 'M = (P + Q)/2,  d = |P − Q|', '{P, Q} ↦ (Mₓ, M_y, d)',
                                'Rechteck ⇔ zwei verschiedene Paare mit gleichem Bildpunkt (gleiche Mitte, gleich lange Diagonalen)']},
        'params': [rng('s', 'Lage von P auf der Kurve (Parameter s)', s), rng('t', 'Lage von Q auf der Kurve (Parameter t)', t)],
        'sequence': {
            'predict': {'question': 'Sie ziehen Q bis dicht an P heran. Wo landet dann der Raumpunkt (Mₓ, M_y, d)?',
                        'options': [{'value': 'kurve', 'label': 'Dicht über der Kurve selbst – d geht gegen 0.'}, {'value': 'oben', 'label': 'Ganz oben – d wird am größten.'},
                                    {'value': 'zentrum', 'label': 'Über dem Mittelpunkt der Kurve.'}],
                        'correct': 'kurve', 'change': [{'param': 't', 'to': round(s + 0.01, 3)}],
                        'result_text': f'd sinkt auf {_fmt(near["d"], 3)}; der Raumpunkt liegt fast auf dem Kurvenpunkt P = {pt(near["P"])}.',
                        'explanation': 'Für Q → P geht der Mittelpunkt gegen P und der Abstand gegen 0: Der Bildpunkt nähert sich dem Kurvenpunkt in der Ebene. Deshalb ist die Kurve der Rand der Fläche aller Paare.'},
            'tasks': [
                {'id': 'height', 'title': 'Höhe des Raumpunkts berechnen', 'prompt': f'Startpaar: P = {pt(P)}, Q = {pt(Q)}. Berechnen Sie die Höhe d des Raumpunkts (3 Nachkommastellen).',
                 'expected': L['d'], 'tolerance': 5e-4, 'unit': '',
                 'errors': [{'value': L['d'] / 2, 'message': 'Das ist der halbe Abstand. Die Höhe ist die volle Sehnenlänge |P − Q|.'},
                            {'value': d2, 'message': 'Das ist d². Es fehlt die Wurzel.'}],
                 'hints': ['d = |P − Q| ist die Länge der Sehne.', 'd = √((Pₓ − Qₓ)² + (P_y − Q_y)²).', f'(Pₓ − Qₓ)² + (P_y − Q_y)² = {_fmt(d2, 4)}.'],
                 'solution': [f'd = √{_fmt(d2, 4)} = {_fmt(L["d"], 4)}.', f'Der Raumpunkt ist ({_fmt(L["M"][0], 3)}; {_fmt(L["M"][1], 3)}; {_fmt(L["d"], 3)}).'],
                 'feedback_correct': 'Genau: Die Höhe ist die Länge der Sehne.'},
                {'id': 'transfer', 'title': 'Transfer: der Kreis', 'prompt': 'Auf dem Einheitskreis liegen P und Q genau gegenüber (Durchmesser). Welche Höhe d hat ihr Raumpunkt?',
                 'expected': 2.0, 'tolerance': 1e-3, 'unit': '',
                 'errors': [{'value': 1.0, 'message': 'Das ist der Radius. Die Sehne ist hier ein Durchmesser.'}],
                 'hints': ['Gegenüberliegende Punkte: Die Sehne geht durch den Mittelpunkt.', 'Ein Durchmesser ist doppelt so lang wie der Radius.'],
                 'solution': ['d = 2. Jedes Durchmesser-Paar landet im selben Raumpunkt (0; 0; 2).',
                              'Je zwei Durchmesser haben gleiche Mitte und gleiche Länge – sie sind die Diagonalen eines Rechtecks. Ein Kreis hat unendlich viele einbeschriebene Rechtecke.'],
                 'feedback_correct': 'Und weil alle Durchmesser-Paare denselben Raumpunkt treffen, enthält der Kreis unendlich viele Rechtecke.'}]},
        'explanations': ['Gleiche Mitte der Diagonalen ergibt ein Parallelogramm; gleich lange Diagonalen machen daraus ein Rechteck.',
                         'Die numerische Suche (Newton-Verfahren) findet Beispiele. Ob jede geschlossene Kurve ein Rechteck enthält, ist eine Aussage über alle Kurven und braucht einen Beweis.'],
        'assumptions': ['Glatte, sternförmige Referenzkurve (Parameter im Modell); keine Kurve aus einer Vorlesung.',
                        'Numerische Exploration mit Gleitkomma-Arithmetik; Restfehler werden angezeigt.'],
        'sources': ['Eigenes Referenzmodell (exam_mastery/labs/models.py)', 'Idee: 3Blue1Brown, Inscribed rectangle problem (3blue1brown.com, Lektion inscribed-rect-v2); eigene Umsetzung'],
        'tests': [{'params': {'s': s, 't': t}, 'd': L['d']}, {'params': {'s': s}, 'rect_area': R['area']}],
    }


def validate(spec):
    """Structure, parameter bounds and every number recomputed with the reference models. Raises LabError."""
    p = []
    for k in ('schema', 'id', 'version', 'title', 'kc_ids', 'objective', 'model', 'params', 'sequence', 'assumptions', 'sources'):
        if k not in spec:
            p.append(f'missing {k}')
    if p:
        raise LabError('; '.join(p))
    if spec['schema'] != SCHEMA or spec['model'].get('kind') not in KINDS:
        raise LabError('unknown schema or model kind')
    if not re.fullmatch(r'[a-z0-9][a-z0-9/_-]{2,80}', spec['id']):
        raise LabError('lab id must be a stable lower-case key')
    for d in spec['params']:
        if d['type'] in ('range', 'number') and not (d['min'] <= d['default'] <= d['max'] and d['step'] > 0):
            raise LabError(f"param {d['id']}: default outside bounds")
        if d['type'] == 'select' and d['default'] not in [o['value'] for o in d['options']]:
            raise LabError(f"param {d['id']}: default not an option")
    pr = spec['sequence']['predict']
    if pr['correct'] not in [o['value'] for o in pr['options']]:
        raise LabError('prediction: correct answer is not an option')
    for ch in (pr['change'] if isinstance(pr['change'], list) else [pr['change']]):
        if ch['param'] not in [d['id'] for d in spec['params']]:
            raise LabError('prediction changes an unknown parameter')
    for t in spec['sequence']['tasks']:
        if t.get('type') == 'choice':
            continue          # concept items are checked by pedagogy.validate
        if not (isinstance(t['expected'], (int, float)) and math.isfinite(t['expected'])) or t['tolerance'] < 0 or not t['hints'] or not t['solution']:
            raise LabError(f"task {t['id']}: expected/tolerance/hints/solution invalid")
        for e in t.get('errors') or []:
            if abs(e['value'] - t['expected']) <= t['tolerance']:
                raise LabError(f"task {t['id']}: a diagnosed error value equals the expected answer")
    from . import pedagogy as P
    try:
        P.validate(spec)
    except P.PedagogyError as e:
        raise LabError(str(e))
    m = spec['model']
    if m['kind'] == 'cashflow':
        for case in spec.get('tests') or []:
            r = M.cashflow(m['orders'], case['params'].get('delay', m['delay']), m['cost'], m['invest'], m.get('start_cash', 0))
            for k in ('financing_need', 'min_period', 'final_balance'):
                if k in case and not math.isclose(r[k], case[k], abs_tol=1e-9):
                    raise LabError(f'test case mismatch {k}: {r[k]} vs {case[k]}')
    elif m['kind'] == 'mlp':
        g = M.mlp_backward(m['init'], m['x'], m['target'], m['hidden_act'], m['out_act'])['grad']
        n = M.mlp_numeric_grad(m['init'], m['x'], m['target'], hidden_act=m['hidden_act'], out_act=m['out_act'])
        flat = lambda d: [*sum(d['W1'], []), *d['b1'], *d['W2'], d['b2']]
        if max(abs(a - b) for a, b in zip(flat(g), flat(n))) > 1e-6:
            raise LabError('backpropagation disagrees with finite differences')
    elif m['kind'] == 'van_westendorp':
        expected_spec = vw_spec(spec['id'], spec['title'], spec['kc_ids'], spec['sources'], spec.get('course', ''))
        if m['rows'] != expected_spec['model']['rows'] or not m.get('synthetic') or m.get('data_label') != expected_spec['model']['data_label']:
            raise LabError('reference PSM synthetic data cannot be relabelled or substituted')
        if spec['sequence']['predict'] != expected_spec['sequence']['predict']:
            raise LabError('PSM prediction disagrees with reference model')
        if spec['sequence']['tasks'] != expected_spec['sequence']['tasks']:
            raise LabError('PSM task answers or feedback disagree with reference model')
        for case in spec.get('tests') or []:
            r = M.van_westendorp(m['rows'], case['params'].get('method', 'standard'))
            for k, v in case['points'].items():
                if not math.isclose(r['points'][k], v, abs_tol=1e-9):
                    raise LabError(f'test case mismatch {k}')
        if m.get('data_origin') not in ('SYNTHETIC_DEMO_NOT_LECTURE_RESULTS', 'PROVIDED_ROWS_PROVENANCE_UNVERIFIED') or not spec['kc_ids'] or not spec['sources']:
            raise LabError('PSM needs a declared data origin, course competencies and source anchors')
        if m.get('synthetic') and 'SYNTHETISCH' not in ' '.join(spec['assumptions']):
            raise LabError('synthetic data must be declared as such in the assumptions')
    elif m['kind'] == 'chord':
        for case in spec.get('tests') or []:
            if 'd' in case and not math.isclose(M.chord_lift(case['params']['s'], case['params']['t'])['d'], case['d'], abs_tol=1e-12):
                raise LabError('chord test case mismatch')
            if 'rect_area' in case:
                r = M.rect_search(case['params']['s'])
                if not r or not math.isclose(r[0]['area'], case['rect_area'], abs_tol=1e-9) or M.rect_check(r[0]['corners']) > 1e-9 or r[0]['residual'] > 1e-11:
                    raise LabError('rectangle search does not reproduce a verified rectangle')
    elif m['kind'] == 'mdp':
        from . import mdp as MDP
        try:
            ref = MDP.spec(spec['id'], spec['title'], spec['kc_ids'], [], {**m['mdp'], 'policy': m['policy'], 'focus': m['focus'], 'labels': m.get('labels')},
                           spec.get('course', ''), m.get('unit', ''))
        except MDP.MdpError as e:
            raise LabError(str(e))
        own = [t for t in spec['sequence']['tasks'] if t['id'] in ('backup', 'exact', 'improve', 'transfer')]
        if [{k: v for k, v in t.items() if k != 'transfer'} for t in own] != ref['sequence']['tasks'] or spec['sequence']['predict']['correct'] != ref['sequence']['predict']['correct']:
            raise LabError('MDP tasks or prediction disagree with the reference model')
        mm, pol = MDP.model(spec)
        for case in spec.get('tests') or []:
            for key, fn in (('vpi', lambda: M.mdp_eval_exact(mm, pol)), ('vstar', lambda: M.mdp_optimal(mm)), ('vi3', lambda: M.mdp_value_iteration(mm, 3)[3]),
                            ('pe2', lambda: M.mdp_eval_sweeps(mm, pol, 2)[2])):
                got = fn()
                if key in case and any(not math.isclose(got[s], case[key][s], abs_tol=1e-9) for s in mm['states']):
                    raise LabError(f'MDP test case mismatch {key}')
    elif m['kind'] in GENERIC:
        generic(m['kind']).check(spec)
    elif m['kind'] == 'risk':
        cl = m['classes']
        if len(cl) != 5 or any(len(r) != 5 or set(r) - set(M.CLASS_RANK) for r in cl) or M.risk_matrix(3, 4, cl)['score'] != 12:
            raise LabError('risk class table must be 5x5 with classes Low/Moderate/High/Critical')
    from . import scenes as SC
    try:
        SC.validate(spec)
    except SC.SceneError as e:
        raise LabError(str(e))
    return True


# ------------------------------------------------------------------ static figure (SVG; used in the lab page, PDF and print)

def static_svg(spec):
    m = spec['model']
    if m['kind'] in GENERIC:
        return generic(m['kind']).static_svg(spec)
    if m['kind'] == 'mdp':
        from . import mdp as MDP
        return MDP.static_svg(spec)
    if m['kind'] == 'cashflow':
        r = M.cashflow(m['orders'], m['delay'], m['cost'], m['invest'], m.get('start_cash', 0))
        vals = r['cf'] + r['balance'] + [0]; lo, hi = min(vals), max(vals)
        raw = (hi - lo) / 4 or 1; mag = 10 ** math.floor(math.log10(raw)); step = next(f * mag for f in (1, 2, 2.5, 5, 10) if f * mag >= raw)
        lo, hi = math.floor(lo / step) * step, math.ceil(hi / step) * step; nt = round((hi - lo) / step)
        W, H, L, R, T, B = 640, 300, 58, 14, 18, 40; n = len(r['cf']); bw = (W - L - R) / n
        y = lambda v: T + (hi - v) / (hi - lo) * (H - T - B); x = lambda i: L + bw * (i + .5)
        s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="Cashflow und kumulierte Liquidität"><title>Cashflow je Periode und kumulierte Liquidität ({E(m.get("unit", ""))})</title>',
             f'<line x1="{L}" x2="{W - R}" y1="{y(0):.1f}" y2="{y(0):.1f}" stroke="#5b6876"/>']
        for k in range(nt + 1):
            v = lo + step * k
            s.append(f'<text x="{L - 6}" y="{y(v) + 4:.1f}" text-anchor="end" font-size="11" fill="#5b6876">{_fmt(v)}</text>')
        for i, v in enumerate(r['cf']):
            s.append(f'<rect x="{x(i) - bw * .3:.1f}" y="{min(y(v), y(0)):.1f}" width="{bw * .6:.1f}" height="{abs(y(v) - y(0)):.1f}" fill="{"#c98a7c" if v < 0 else "#7f9db6"}"/>')
            s.append(f'<text x="{x(i):.1f}" y="{H - B + 16}" text-anchor="middle" font-size="11" fill="#5b6876">P{i + 1}</text>')
        s.append('<polyline fill="none" stroke="#1f5f8b" stroke-width="2.5" points="' + ' '.join(f'{x(i):.1f},{y(v):.1f}' for i, v in enumerate(r['balance'])) + '"/>')
        k = r['min_period'] - 1
        s.append(f'<line x1="{x(k):.1f}" x2="{x(k):.1f}" y1="{y(0):.1f}" y2="{y(r["min_balance"]):.1f}" stroke="#a8362f" stroke-width="2" stroke-dasharray="3 3"/>')
        right = x(k) > W / 2
        s.append(f'<text x="{x(k) - 8 if right else x(k) + 8:.1f}" y="{min(y(r["min_balance"]) + 16, H - B - 4):.1f}" text-anchor="{"end" if right else "start"}" font-size="12" font-weight="700" fill="#a8362f">Finanzierungsbedarf {_fmt(r["financing_need"])} {E(m.get("unit", ""))} (P{r["min_period"]})</text>')
        s.append(f'<text x="{L}" y="{H - 6}" font-size="11" fill="#5b6876">Balken: Cashflow je Periode · Linie: kumulierte Liquidität ({E(m.get("unit", ""))})</text></svg>')
        return ''.join(s)
    if m['kind'] == 'mlp':
        fw = M.mlp_forward(m['init'], m['x'], m['hidden_act'], m['out_act']); p = m['init']
        P = {'x1': (60, 70), 'x2': (60, 190), 'h1': (260, 70), 'h2': (260, 190), 'o': (450, 130)}
        s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 260" role="img" aria-label="Netz 2-2-1 im Ausgangszustand"><title>Netz 2-2-1 im Ausgangszustand</title>']
        for a, b, w, lab in (('x1', 'h1', p['W1'][0][0], 'w11'), ('x2', 'h1', p['W1'][0][1], 'w12'), ('x1', 'h2', p['W1'][1][0], 'w21'), ('x2', 'h2', p['W1'][1][1], 'w22'), ('h1', 'o', p['W2'][0], 'v1'), ('h2', 'o', p['W2'][1], 'v2')):
            (x1, y1), (x2, y2) = P[a], P[b]
            s.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{"#1f5f8b" if w >= 0 else "#b0602a"}" stroke-width="{1 + min(6, abs(w) * 3):.1f}"/><text x="{(x1 + x2) / 2}" y="{(y1 + y2) / 2 - 6}" font-size="11" text-anchor="middle" fill="#5b6876">{lab}={_fmt(w, 3)}</text>')
        for k, t, v in (('x1', 'x₁', m['x'][0]), ('x2', 'x₂', m['x'][1]), ('h1', 'a₁', fw['a1'][0]), ('h2', 'a₂', fw['a1'][1]), ('o', 'ŷ', fw['y'])):
            cx, cy = P[k]
            s.append(f'<circle cx="{cx}" cy="{cy}" r="30" fill="#fff" stroke="#16263a" stroke-width="1.5"/><text x="{cx}" y="{cy - 3}" text-anchor="middle" font-size="14" font-weight="700">{t}</text><text x="{cx}" y="{cy + 13}" text-anchor="middle" font-size="11" fill="#5b6876">{_fmt(v, 3)}</text>')
        return ''.join(s) + '</svg>'
    if m['kind'] == 'van_westendorp':
        return _vw_svg(spec)
    if m['kind'] == 'chord':
        return _chord_svg(spec)
    cl = m['classes']; col = {'Low': '#d9ecd9', 'Moderate': '#f6e7b8', 'High': '#f3c9a6', 'Critical': '#e9a6a0'}
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 380 360" role="img" aria-label="Risikomatrix 5 mal 5"><title>Risikomatrix: Punktwert = Auswirkung × Wahrscheinlichkeit</title>']
    for li in range(1, 6):
        for im in range(1, 6):
            r = M.risk_matrix(li, im, cl); x, y = 50 + (im - 1) * 62, 20 + (5 - li) * 62
            s.append(f'<rect x="{x}" y="{y}" width="60" height="60" fill="{col[r["class"]]}" stroke="#fff" stroke-width="2"/><text x="{x + 30}" y="{y + 36}" text-anchor="middle" font-size="13">{li * im}</text>')
    s.append('<text x="205" y="352" text-anchor="middle" font-size="11" fill="#5b6876">Auswirkung (Stufe 1–5) →  Farbe: Low · Moderate · High · Critical</text><text x="14" y="175" transform="rotate(-90 14 175)" text-anchor="middle" font-size="11" fill="#5b6876">Wahrscheinlichkeit (Stufe 1–5) →</text></svg>')
    return ''.join(s)


def _chord_svg(spec):
    d = {p['id']: p['default'] for p in spec['params']}
    L, R = M.chord_lift(d['s'], d['t']), (M.rect_search(d['s']) or [None])[0]
    X = lambda p: f'{200 + 120 * p[0]:.1f},{200 - 120 * p[1]:.1f}'
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" role="img" aria-label="Kurve, Punktpaar und gefundenes Rechteck (Draufsicht)"><title>Kurve mit Punktpaar P, Q und einem numerisch gefundenen Rechteck</title>',
         '<polyline fill="none" stroke="#16263a" stroke-width="2" points="' + ' '.join(X(M.curve_point(n / 240)) for n in range(241)) + '"/>']
    if R:
        s.append('<polygon fill="#b0602a22" stroke="#b0602a" stroke-width="1.5" points="' + ' '.join(X(c) for c in R['corners']) + '"/>')
    s.append(f'<line stroke="#1f5f8b" stroke-width="2" x1="{X(L["P"]).split(",")[0]}" y1="{X(L["P"]).split(",")[1]}" x2="{X(L["Q"]).split(",")[0]}" y2="{X(L["Q"]).split(",")[1]}"/>')
    for k, p in (('P', L['P']), ('Q', L['Q']), ('M', L['M'])):
        x, y = X(p).split(',')
        s.append(f'<circle cx="{x}" cy="{y}" r="5" fill="#1f5f8b"/><text x="{float(x) + 8:.1f}" y="{float(y) - 6:.1f}" font-size="13" font-weight="700">{k}</text>')
    s.append(f'<text x="10" y="390" font-size="11" fill="#5b6876">d = |P − Q| = {_fmt(L["d"], 3)} · Rechteck: numerisch gefunden (Exploration, kein Beweis)</text></svg>')
    return ''.join(s)


def _vw_svg(spec):
    m = spec['model']; r = M.van_westendorp(m['rows'], m.get('method', 'standard'))
    xs, c, P = r['knots'], r['curves'], r['points']
    W, H, L, R, T, B = 640, 376, 46, 14, 64, 66; hi = xs[-1]
    x = lambda v: L + v / hi * (W - L - R); y = lambda v: T + (1 - v) * (H - T - B)
    step = next(s for s in (5, 10, 20, 25, 50, 100, 200, 500) if hi / s <= 10)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="Van-Westendorp-Kurven und Preispunkte"><title>Van-Westendorp-Kurven ({E(m["data_label"])})</title>']
    for k in range(0, 11, 2):
        s.append(f'<line x1="{L}" x2="{W - R}" y1="{y(k / 10):.1f}" y2="{y(k / 10):.1f}" stroke="#d7dde3"/><text x="{L - 6}" y="{y(k / 10) + 4:.1f}" text-anchor="end" font-size="11" fill="#5b6876">{k * 10} %</text>')
    v = 0
    while v <= hi + 1e-9:
        s.append(f'<text x="{x(v):.1f}" y="{H - B + 15}" text-anchor="middle" font-size="11" fill="#5b6876">{_fmt(v)}</text>'); v += step
    if P['pmc'] is not None and P['pme'] is not None:
        s.append(f'<rect x="{x(P["pmc"]):.1f}" y="{T}" width="{x(P["pme"]) - x(P["pmc"]):.1f}" height="{H - T - B}" fill="#1f5f8b" opacity=".07"/>')
    style = {'tc': ('#2e7d6b', ''), 'cheap': ('#1f5f8b', ''), 'exp': ('#b0602a', ''), 'te': ('#a8362f', ''), 'not_cheap': ('#1f5f8b', '5 4'), 'not_exp': ('#b0602a', '5 4')}
    name = {'tc': 'zu billig', 'cheap': 'günstig', 'exp': 'teuer', 'te': 'zu teuer', 'not_cheap': 'nicht günstig', 'not_exp': 'nicht teuer'}
    for k, (col, dash) in style.items():
        s.append(f'<polyline fill="none" stroke="{col}" stroke-width="2"' + (f' stroke-dasharray="{dash}"' if dash else '') + ' points="' + ' '.join(f'{x(a):.1f},{y(b):.1f}' for a, b in zip(xs, c[k])) + '"/>')
    for i, k in enumerate(('pmc', 'opp', 'ipp', 'pme')):
        if P[k] is not None:
            s.append(f'<line x1="{x(P[k]):.1f}" x2="{x(P[k]):.1f}" y1="{15 + i * 13}" y2="{H - B}" stroke="#16263a" stroke-dasharray="2 3"/><text x="{x(P[k]) - 4 if x(P[k]) > W * .6 else x(P[k]) + 4:.1f}" y="{12 + i * 13}" text-anchor="{'end' if x(P[k]) > W * .6 else 'start'}" font-size="11" font-weight="700" fill="#16263a">{k.upper()} {_fmt(M._round2(P[k]), 2)} €</text>')
    lx = L
    for k, (col, dash) in style.items():
        s.append(f'<line x1="{lx}" x2="{lx + 18}" y1="{H - 26}" y2="{H - 26}" stroke="{col}" stroke-width="2"' + (f' stroke-dasharray="{dash}"' if dash else '') + f'/><text x="{lx + 22}" y="{H - 22}" font-size="11" fill="#5b6876">{name[k]}</text>'); lx += 96
    s.append(f'<text x="{L}" y="{H - 6}" font-size="11" fill="#a8362f">Preis (€) · SYNTHETISCHE Daten · keine Vorlesungsergebnisse · Standard</text></svg>')
    return ''.join(s)


# ------------------------------------------------------------------ HTML

def _sha(s):
    return "'sha256-" + base64.b64encode(hashlib.sha256(s.encode()).digest()).decode() + "'"


def page(title, body, scripts=(), course='', fonts=None, extra_js=()):
    """One self-contained page. fonts: relative folder with the local woff2 files (optional; system fonts otherwise)."""
    css = (TEMPLATES / 'em_tokens.css').read_text(encoding='utf-8') + (TEMPLATES / 'em_labs.css').read_text(encoding='utf-8')
    if fonts:
        from .. import typeset
        css = typeset.font_css(fonts) + css
    js = ([(TEMPLATES / n).read_text(encoding='utf-8') for n in ('em_scene.js', 'em_labs.js')] if 'labs' in scripts else []) + list(extra_js)
    csp = ("default-src 'none'; img-src data:; font-src 'self' file: data:; style-src " + _sha(css) + "; script-src " + (' '.join(_sha(j) for j in js) or "'none'") +
           "; base-uri 'none'; form-action 'none'")
    return (f'<!doctype html><html lang="de" data-decimal="{E(DECIMAL["sep"])}"><head>'
            '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<meta http-equiv="Content-Security-Policy" content="{csp}"><meta name="referrer" content="no-referrer">'
            f'<title>{E(title)}</title><style>{css}</style></head><body><a class="em-skip" href="#main">Zum Inhalt</a>'
            f'<main id="main" class="em-shell">{body}</main>' + ''.join(f'<script>{j}</script>' for j in js) + '</body></html>')


def _kc_chips(spec):
    """Competency names for learners; internal ids are never shown (a lab without names shows none)."""
    labels = spec.get('kc_labels') or {}
    names = [labels[k] for k in spec['kc_ids'] if labels.get(k) and labels[k] != k]
    return ''.join(f'<span class="ds-chip">{E(n)}</span>' for n in names)


def render(spec, out_dir, back_link='../index.html', context=None, fonts=None, back_label='Übersicht'):
    """context: namespace of the learning records (e.g. 'referenz'), so that a reference collection never shows up as
    course progress; None keeps the course key (the learning environment of a chapter reads it)."""
    validate(spec)
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    name = spec['id'].replace('/', '__') + '.html'
    svg = static_svg(spec)
    page_spec = dict(spec, context=context) if context else spec
    data = json.dumps(page_spec, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    sc = spec.get('scene') or {}
    lead = (sc.get('didactics') or {}).get('concept') or spec['objective']
    pre = spec.get('prerequisites') or []
    chips = _kc_chips(spec)
    body = (f'<nav class="em-nav"><a href="{E(back_link)}">← {E(back_label)}</a><span>{E(spec.get("course", ""))}</span></nav>'
            f'<header class="em-head"><div class="em-eyebrow">Interaktives Experiment</div><h1>{E(spec["title"])}</h1>'
            f'<p class="em-head-side">{E(lead)}' + (f'<span class="em-kcs">{chips}</span>' if chips else '') + '</p></header>'
            f'<details class="em-objective"><summary>Lernziel und Voraussetzungen</summary><p><strong>Lernziel.</strong> {E(spec["objective"])}</p>'
            + (f'<p><strong>Voraussetzungen.</strong> {MT("; ".join(pre))}</p>' if pre else '') + '</details>'
            f'<noscript><p class="em-bad">JavaScript ist deaktiviert: Es gilt die statische Darstellung unten.</p></noscript>'
            f'<div id="em-lab"></div><script type="application/json" id="em-lab-spec">{data}</script>'
            '<section class="em-appendix" aria-labelledby="apx-h"><h2 id="apx-h" class="em-apx-h">Modell, Annahmen und Quellen</h2><div class="em-appendix-grid">'
            '<section class="em-notes"><h3>Modellgleichungen</h3><ul>' + ''.join(f'<li class="em-eq">{MT(q)}</li>' for q in spec['model'].get('equations', [])) + '</ul>'
            '<h3 class="em-apx-sub">Annahmen</h3><ul>' + ''.join(f'<li>{MT(a)}</li>' for a in spec['assumptions']) + '</ul>' +
            ''.join(f'<p class="em-meta">{MT(x)}</p>' for x in spec.get('explanations', [])) +
            '<h3 class="em-apx-sub">Quellen</h3><ul>' + ''.join(f'<li>{E(s)}</li>' for s in spec['sources']) + '</ul></section>'
            f'<section class="em-static{" em-static-live" if spec.get("scene") else ""}"><h3>Statische Darstellung (Ausgangszustand, auch im PDF)</h3>{svg}</section></div></section>')
    (out / name).write_text(page(spec['title'], body, ('labs',), fonts=fonts), encoding='utf-8')
    (out / (name[:-5] + '.svg')).write_text(svg, encoding='utf-8')
    (out / (name[:-5] + '.json')).write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding='utf-8')
    return out / name


def environment(out_dir, title, course, docs, labs, notes=(), context=''):
    """Start page of a local lab collection: documents, labs, observed attempts of exactly these labs (this browser only)."""
    out = Path(out_dir)
    rows = ''.join(f'<li><a href="{E(h)}">{E(t)}</a></li>' for t, h in docs)
    lrows = ''.join(f'<li><a href="{E(h)}">{E(t)}</a></li>' for t, h, k in labs)
    names = {h.split('/')[-1][:-5].replace('__', '/'): t for t, h, k in labs}
    body = (f'<nav class="em-nav"><span>Exam Mastery</span><span>{E(course)}</span></nav><header class="em-head"><div class="em-eyebrow">Lernumgebung</div><h1>{E(title)}</h1>'
            '<p class="em-head-side">Läuft lokal und offline, ohne Server und ohne Netzwerkzugriff.</p></header>'
            + (f'<section class="em-step"><h2>Lesen und üben</h2><ul>{rows}</ul></section>' if rows else '')
            + (f'<section class="em-step"><h2>Interaktive Experimente</h2><ul>{lrows}</ul><p class="em-meta">Jedes Experiment: erst vorhersagen, dann beobachten, erklären und übertragen.</p></section>' if lrows else '')
            + f'<section class="em-step"><h2>Ihre bisherigen Versuche</h2><div id="em-progress" data-context="{E(context)}" data-labs="{E(json.dumps(names, ensure_ascii=False)) if labs else "null"}"><p class="em-meta">Wird geladen …</p></div>'
            '<p class="em-meta">Gespeichert nur in diesem Browser, nichts verlässt den Rechner. „Ohne Hilfe gelöst“ heißt: richtig ohne Hinweis und ohne Lösung – '
            'eine Beobachtung, keine Aussage über dauerhaftes Behalten. Dafür sind Wiederholung mit Abstand (Anki) und spätere Prüfung da.</p></section>'
            + (''.join(f'<p class="em-meta">{E(n)}</p>' for n in notes)))
    (out / 'index.html').write_text(page(title, body, ('labs',)), encoding='utf-8')
    return out / 'index.html'


GALLERY_JS = ("(()=>{const d=JSON.parse(document.getElementById('em-gallery').textContent);"
              "document.querySelectorAll('[data-preview]').forEach(f=>{const s=d[+f.dataset.preview];if(s&&window.EM&&EM.scene)EM.scene.preview(f,s);});"
              "document.documentElement.dataset.galleryReady='1';})();")


def _steps(spec):
    sc = spec.get('scene') or {}
    return sum(len(spec['model'].get('orders') or []) if st.get('repeat') else 1 for st in sc.get('steps') or [])


def gallery(out_dir, items, title, kicker, headline, lede, notes=(), version='', fonts=None, tracks=()):
    """Overview page of a lab collection that shows the experiments themselves: every card carries a live miniature of
    its scene, driven by the lab's own model and defaults (EM.scene.preview). items: [{'spec', 'href', 'title'?, 'teaser'?}].
    Course-neutral; nothing here is about a particular subject. No learning progress: an overview is not a course."""
    out = Path(out_dir)
    specs = [it['spec'] for it in items]
    cards = []
    for n, it in enumerate(items):
        sp = it['spec']; sc = sp.get('scene') or {}; did = sc.get('didactics') or {}
        facts = [f'{_steps(sp)} Schritte'] if sc.get('steps') else []
        if sc.get('status') == 'exploration':
            facts.append('numerische Exploration')
        cls = 'gx-card gx-feature' if n == 0 else 'gx-card'
        cards.append(f'<article class="{cls}"><a class="gx-link" href="{E(it["href"])}" aria-label="{E((it.get("title") or sp["title"]) + " – Experiment öffnen")}"></a>'
                     f'<div class="gx-fig ds-stage" data-preview="{n}"></div><div class="gx-text">'
                     f'<div class="ds-kicker ds-eyebrow"><span>Experiment {n + 1:02d}</span><span>{E(sp.get("course", ""))}</span></div>'
                     f'<h2>{E(it.get("title") or sp["title"])}</h2><p>{E(it.get("teaser") or did.get("concept") or sp["objective"])}</p>'
                     + (f'<p class="gx-manip"><span>Sie verändern</span>{E(did["manipulate"])}</p>' if did.get('manipulate') else '')
                     + f'<div class="gx-foot"><span>{E(" · ".join(facts))}</span><span class="gx-go">Experiment öffnen <span aria-hidden="true">→</span></span></div></div></article>')
    phases = [('Vorhersagen', 'Sie legen sich fest, bevor die Simulation läuft – Widersprüche werden sichtbar.'),
              ('Beobachten', 'Schritt für Schritt: Formel und Bild sind gekoppelt, jede Zahl hat ihren Ort.'),
              ('Erklären', 'Erst mit eigenen Worten, dann der Vergleich mit dem Mechanismus.'),
              ('Übertragen', 'Gezielte Aufträge und Aufgaben in einer neuen Situation.')]
    data = json.dumps(specs, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    body = (f'<nav class="em-nav"><span>Exam Mastery · Labor</span><span>{E(kicker)}</span></nav>'
            f'<header class="gx-hero"><h1>{headline}</h1><p class="gx-lede">{E(lede)}</p></header>'
            f'<section class="gx-grid" aria-label="Experimente">{"".join(cards)}</section>'
            + (('<section class="gx-band gx-tracks" aria-labelledby="gx-tr"><h2 id="gx-tr" class="gx-h2">Adaptive Lernstrecken</h2>'
                '<p class="gx-sub">Dieselben Modelle als Lernweg: Die Engine prüft jede Antwort, erkennt typische Fehler und wählt die nächste Aufgabe nach offen gelegten Regeln.</p><div class="gx-tgrid">'
                + ''.join(f'<a class="gx-track" href="{E(t["href"])}"><span class="gx-tdom">{E(t["domain"])}</span><strong>{E(t["title"])}</strong><span>{E(t["case"])}</span></a>' for t in tracks)
                + '</div></section>') if tracks else '')
            + '<section class="gx-band" aria-labelledby="gx-how"><h2 id="gx-how" class="ds-eyebrow">So ist jedes Experiment aufgebaut</h2><ol class="gx-phases">'
            + ''.join(f'<li><span class="gx-n">{i + 1}</span><strong>{E(t)}</strong><p>{E(x)}</p></li>' for i, (t, x) in enumerate(phases)) + '</ol></section>'
            '<section class="gx-band gx-trust" aria-labelledby="gx-trust"><h2 id="gx-trust" class="ds-eyebrow">Worauf Sie sich verlassen können</h2><ul>'
            + ''.join(f'<li>{E(x)}</li>' for x in notes) + '</ul></section>'
            f'<footer class="gx-footer"><span>Exam Mastery {E(version)}</span><span>Läuft lokal und offline · keine Daten verlassen den Rechner</span></footer>'
            f'<script type="application/json" id="em-gallery">{data}</script>')
    css_extra = GALLERY_CSS
    html_ = page(title, body, ('labs',), fonts=fonts, extra_js=(GALLERY_JS,))
    html_ = html_.replace('<style>', '<style>' + css_extra, 1)
    # the extra CSS changes the style hash: recompute the CSP for the final style block
    m = re.search(r'<style>(.*?)</style>', html_, re.S)
    html_ = re.sub(r"style-src '[^']+'", "style-src " + _sha(m.group(1)), html_, count=1)
    (out / 'index.html').write_text(html_, encoding='utf-8')
    return out / 'index.html'


GALLERY_CSS = """
.gx-h2{font:600 var(--fs-4)/1.2 var(--font-display);margin:0 0 var(--sp-2)}.gx-sub{font:var(--fs-2)/1.55 var(--font-text);color:var(--ink-2);margin:0 0 var(--sp-5);max-width:66ch}
.gx-tgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,18rem),1fr));gap:var(--sp-4)}
.gx-track{display:flex;flex-direction:column;gap:var(--sp-2);padding:var(--sp-4) var(--sp-5);border:var(--hair) solid var(--rule-strong);border-left:4px solid var(--accent);border-radius:var(--r-2);background:var(--surface);color:var(--ink);text-decoration:none;font:var(--fs-1)/1.5 var(--font-ui)}
.gx-track:hover{border-color:var(--accent)}.gx-track strong{font:600 var(--fs-3)/1.25 var(--font-display)}.gx-tdom{color:var(--signal);font-weight:600;font-size:var(--fs-0)}.gx-track span:last-child{color:var(--ink-2)}
.gx-hero{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,.85fr);gap:var(--sp-5) var(--sp-7);align-items:end;margin:var(--sp-7) 0 var(--sp-7)}
.gx-hero h1{font:600 var(--fs-6)/1.02 var(--font-display);letter-spacing:-.025em;margin:0;text-wrap:balance}
.gx-hero h1 em{font-style:italic;font-weight:400;color:var(--signal)}
.gx-lede{font:var(--fs-3)/1.5 var(--font-text);color:var(--ink-2);margin:0;max-width:44ch}
.gx-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:var(--sp-5)}
.gx-card{position:relative;display:flex;flex-direction:column;background:var(--plate);border:var(--hair) solid var(--rule-strong);border-radius:var(--r-3);overflow:hidden;box-shadow:var(--shadow-1);transition:box-shadow var(--t-base) var(--ease),border-color var(--t-base),transform var(--t-base) var(--ease)}
.gx-card:hover{box-shadow:var(--shadow-2);border-color:var(--ink);transform:translateY(-2px)}
.gx-card:focus-within{outline:3px solid var(--focus);outline-offset:3px}
.gx-link{position:absolute;inset:0;z-index:2;border-radius:var(--r-3)}.gx-link:focus-visible{outline:none}
.gx-feature{grid-column:1/-1;display:grid;grid-template-columns:minmax(0,1.5fr) minmax(300px,1fr)}
.gx-fig{display:flex;align-items:center;justify-content:center;padding:var(--sp-4);border-bottom:var(--hair) solid var(--rule);min-height:260px}
.gx-feature .gx-fig{border-bottom:0;border-right:var(--hair) solid var(--rule);min-height:420px;padding:var(--sp-5)}
.gx-fig .em-preview{width:100%}
.gx-text{display:flex;flex-direction:column;gap:var(--sp-3);padding:var(--sp-5) var(--sp-5) var(--sp-4);flex:1}
.gx-feature .gx-text{padding:var(--sp-6);justify-content:center}
.gx-text h2{font:600 var(--fs-4)/1.15 var(--font-display);margin:0;letter-spacing:-.01em;text-wrap:balance}
.gx-feature .gx-text h2{font-size:clamp(1.8rem,2.6vw,2.3rem)}
.gx-text p{margin:0;font:var(--fs-2)/1.55 var(--font-text);color:var(--ink-2)}
.gx-manip{font-family:var(--font-ui)!important;font-size:var(--fs-0)!important;border-left:2px solid var(--signal);padding-left:10px}
.gx-manip span{display:block;font-weight:700;letter-spacing:0;text-transform:none;font-size:var(--fs-xs);color:var(--muted)}
.gx-foot{margin-top:auto;padding-top:var(--sp-3);display:flex;justify-content:space-between;gap:var(--sp-3);flex-wrap:wrap;border-top:var(--hair) solid var(--rule);font:600 var(--fs-0)/1.3 var(--font-ui);color:var(--muted)}
.gx-go{color:var(--ink)}.gx-card:hover .gx-go{color:var(--accent)}
.gx-band{margin:var(--sp-8) 0 0;border-top:var(--hair) solid var(--ink);padding-top:var(--sp-4)}
.gx-band h2{margin:0 0 var(--sp-5)}
.gx-phases{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:var(--sp-5)}
.gx-phases li{display:flex;flex-direction:column;gap:6px}.gx-phases strong{font:600 var(--fs-3)/1.2 var(--font-display)}.gx-phases p{margin:0;color:var(--ink-2);font-size:var(--fs-1)}
.gx-n{font:600 var(--fs-0) var(--font-ui);color:var(--signal);font-variant-numeric:tabular-nums}
.gx-trust ul{margin:0;padding:0;list-style:none;display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:var(--sp-3) var(--sp-5)}
.gx-trust li{font:var(--fs-2)/1.5 var(--font-text);color:var(--ink-2);padding-left:18px;position:relative}.gx-trust li::before{content:"";position:absolute;left:0;top:.65em;width:8px;height:8px;border-radius:50%;background:var(--ok)}
.gx-footer{display:flex;justify-content:space-between;gap:var(--sp-3);flex-wrap:wrap;margin-top:var(--sp-8);padding-top:var(--sp-3);border-top:var(--hair) solid var(--rule);font-size:var(--fs-0);color:var(--muted)}
@media (max-width:980px){.gx-hero{grid-template-columns:1fr;margin:var(--sp-6) 0}.gx-feature{grid-template-columns:1fr}.gx-feature .gx-fig{border-right:0;border-bottom:var(--hair) solid var(--rule);min-height:0}.gx-phases{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:680px){.gx-grid{grid-template-columns:1fr}.gx-fig{min-height:0;padding:var(--sp-2)}.gx-phases{grid-template-columns:1fr}.gx-text{padding:var(--sp-4)}.gx-feature .gx-text{padding:var(--sp-4)}}
"""


# B14: every builder returns a spec with the full learning sequence (pedagogy.py)
def _with_sequence(fn):
    def wrap(*a, **k):
        from . import pedagogy, scenes
        return scenes.add(pedagogy.add(fn(*a, **k)))
    wrap.__name__, wrap.__doc__ = fn.__name__, fn.__doc__
    return wrap


def mdp_spec(lab_id, title, kc_ids, sources, data, course='', unit=''):
    from . import mdp as MDP
    try:
        return MDP.spec(lab_id, title, kc_ids, sources, data, course, unit)
    except MDP.MdpError as e:
        raise LabError(str(e))


cashflow_spec, mlp_spec, risk_spec, vw_spec, chord_spec, mdp_spec = (_with_sequence(f) for f in (cashflow_spec, mlp_spec, risk_spec, vw_spec, chord_spec, mdp_spec))


def _generic_builder(kind):
    def fn(lab_id, title, kc_ids, sources, data=None, course=''):
        try:
            return generic(kind).spec(lab_id, title, kc_ids, sources, data, course)
        except (KeyError, TypeError, ValueError) as e:
            raise e if isinstance(e, LabError) else LabError(f'{kind}: {e}')
    fn.__name__ = f'{kind}_spec'
    return _with_sequence(fn)


sequence_spec, attention_spec, cap_table_spec, legal_check_spec = (_generic_builder(k) for k in GENERIC)
