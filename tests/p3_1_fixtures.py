"""P3.1 reference fixtures. Positive examples are SYNTHETIC but hand-written and independently checkable
(numbers recomputable, standard textbook results); they are still NOT academically reviewed content."""
import copy
from pathlib import Path

MATH = '''# Lineare Ausgleichsgerade

## Lernziele
- Leiten Sie die Formel für die Steigung der Ausgleichsgeraden her.
- Berechnen Sie die Ausgleichsgerade für gegebene Messpunkte.

Gegeben seien Messpunkte $(x_i, y_i)$, $i = 1, \\dots, n$, nicht alle $x_i$ gleich. Die Ausgleichsgerade $y = a + b x$ minimiert die Summe der quadrierten Residuen $S(a,b) = \\sum_i (y_i - a - b x_i)^2$.

Die Steigung ist $b = S_{xy} / S_{xx}$ mit $S_{xy} = \\sum_i (x_i - \\bar x)(y_i - \\bar y)$ und $S_{xx} = \\sum_i (x_i - \\bar x)^2$; der Achsenabschnitt ist $a = \\bar y - b \\bar x$.

$r$ bezeichnet das Residuum der Ausgleichsgeraden.

$r$ bezeichnet den Rang der Designmatrix.

![Residuenplot](residuenplot.png)
'''
LAW = '''# Kaufpreisanspruch

## Lernziele
- Subsumieren Sie einen Sachverhalt unter den Anspruch auf Kaufpreiszahlung aus § 433 Abs. 2 BGB.

§ 433 Abs. 2 BGB verpflichtet den Käufer, dem Verkäufer den vereinbarten Kaufpreis zu zahlen. Voraussetzung des Anspruchs ist ein wirksamer Kaufvertrag, der durch zwei übereinstimmende Willenserklärungen, Antrag und Annahme, zustande kommt.
'''
ML = '''# Gradientenabstieg

## Lernziele
- Implementieren Sie Gradientenabstieg für die mittlere quadratische Abweichung.

Für $L(w) = \\frac{1}{n} \\lVert y - Xw \\rVert^2$ gilt $\\nabla L(w) = -\\frac{2}{n} X^\\top (y - Xw)$. Ein Schritt des Gradientenabstiegs lautet $w \\leftarrow w - \\eta \\nabla L(w)$ mit Lernrate $\\eta > 0$.
'''


def course(root, kind):
    root = Path(root)
    (root / 'skript.md').write_text({'math': MATH, 'law': LAW, 'ml': ML}[kind], encoding='utf-8')
    return root


def _el(manifest, prefix, kind=None):
    return next(e['element_id'] for e in manifest['elements'] if e['text'].startswith(prefix) and (kind is None or e['kind'] == kind))


def _kc(plan, op):
    return [k['kc_id'] for k in plan['competencies'] if op in k['operations']]


def _rub(*crit):
    return [{'criterion': c, 'points': p, 'evidence_of': e} for c, p, e in crit]


def _sol(sid, iid, steps, answer, rubric, **kw):
    return {'solution_id': sid, 'item_id': iid, 'steps': [{'statement': s, 'justification': j} for s, j in steps],
            'answer': answer, 'alternatives': kw.pop('alternatives', []), 'hint_ladder': kw.pop('hints'),
            'rubric': rubric, 'typical_errors': kw.pop('errors', []), **kw}


def positive_ast(kind, plan, manifest):
    c = plan['chapters'][0]
    base = {'schema': 'em-content-v1', 'course_id': plan['course_id'], 'chapter_id': c['chapter_id'], 'title': c['title'],
            'content_origin': 'SYNTHETIC_REFERENCE_FIXTURE', 'kc_ids': c['kc_ids'], 'blocked_kc_ids': [],
            'sources': [{'source_id': s['source_id'], 'relative_path': s['relative_path'], 'raw_sha256': s['raw_sha256'],
                         'authority': s['authority'], 'status': s['status']} for s in manifest['sources']],
            'learning_objectives': [{'kc_id': k['kc_id'], 'statement': k['statement'], 'operations': k['operations']}
                                    for k in plan['competencies']],
            'prerequisites': [], 'notation': [], 'figures': [], 'open_issues': [], 'relations': [], 'reviews': [],
            'kc_coverage': [], 'release_status': 'DRAFT', 'academic_status': 'ACADEMIC_RELEASE_NOT_TESTED',
            'version': {'ast_version': 1, 'source_fingerprint': {}}}
    mot = {'block_id': 'b-mot', 'kind': 'MOTIVATION', 'kc_ids': c['kc_ids'], 'body': 'Warum dieses Kapitel?', 'source_refs': [],
           'provenance': 'AUTHOR_INFERENCE', 'claim_support_status': 'PENDING_SEMANTIC_REVIEW'}
    if kind == 'math':
        der, calc = _kc(plan, 'DERIVE')[0], _kc(plan, 'CALCULATE')[0]
        p1, p2 = _el(manifest, 'Gegeben seien'), _el(manifest, 'Die Steigung ist')
        res, rank = _el(manifest, '$r$ bezeichnet das Residuum'), _el(manifest, '$r$ bezeichnet den Rang')
        fig = next(e['element_id'] for e in manifest['elements'] if e['kind'] == 'figure')
        nt = next(n['notation_id'] for n in plan['notation_registry'] if n['symbol'] == 'r')
        assume = ['n >= 2 Messpunkte', 'nicht alle x_i gleich (sonst S_xx = 0)', 'Fehlerkriterium: Summe quadrierter vertikaler Abstände']
        blocks = [mot,
                  {'block_id': 'b-model', 'kind': 'MODEL', 'kc_ids': [der, calc], 'title': 'Modell und Kriterium',
                   'body': 'Gerade y = a + b x; minimiert wird S(a,b) = Σ (y_i − a − b x_i)^2 über a, b.', 'assumptions': assume,
                   'source_refs': [p1], 'provenance': 'COURSE_SOURCE', 'claim_support_status': 'PENDING_SEMANTIC_REVIEW'},
                  {'block_id': 'b-der', 'kind': 'DERIVATION', 'kc_ids': [der], 'title': 'Herleitung der Steigung', 'assumptions': assume,
                   'body': 'Notwendige Bedingungen erster Ordnung für das Minimum von S.',
                   'steps': [{'statement': '∂S/∂a = −2 Σ (y_i − a − b x_i) = 0 ⇒ a = ȳ − b x̄',
                              'justification': 'S ist differenzierbar; am Minimum verschwindet der Gradient; Division durch n'},
                             {'statement': '∂S/∂b = −2 Σ x_i (y_i − a − b x_i) = 0',
                              'justification': 'partielle Ableitung nach b, Kettenregel'},
                             {'statement': 'Einsetzen von a: Σ x_i ((y_i − ȳ) − b (x_i − x̄)) = 0',
                              'justification': 'y_i − a − b x_i = (y_i − ȳ) − b (x_i − x̄)'},
                             {'statement': 'Σ x_i (y_i − ȳ) = S_xy und Σ x_i (x_i − x̄) = S_xx',
                              'justification': 'Σ x̄ (y_i − ȳ) = 0 und Σ x̄ (x_i − x̄) = 0, daher darf x_i durch (x_i − x̄) ersetzt werden'},
                             {'statement': 'b = S_xy / S_xx; Minimum, weil die Hesse-Matrix 2·[[n, Σx_i],[Σx_i, Σx_i^2]] positiv definit ist',
                              'justification': 'S_xx > 0 nach Annahme; Determinante 4 n S_xx > 0 und n > 0'}],
                   'source_refs': [p1, p2], 'provenance': 'COURSE_SOURCE', 'claim_support_status': 'PENDING_SEMANTIC_REVIEW'},
                  {'block_id': 'b-ex', 'kind': 'WORKED_EXAMPLE', 'kc_ids': [calc], 'assumptions': assume,
                   'problem': 'Messpunkte (0,1), (1,3), (2,4): Ausgleichsgerade bestimmen.',
                   'steps': [{'statement': 'x̄ = 1, ȳ = 8/3', 'justification': 'arithmetische Mittel'},
                             {'statement': 'S_xy = (−1)(1 − 8/3) + 0 + (1)(4 − 8/3) = 3; S_xx = 2', 'justification': 'Definition S_xy, S_xx'},
                             {'statement': 'b = 3/2, a = 8/3 − 3/2 = 7/6', 'justification': 'b = S_xy/S_xx, a = ȳ − b x̄'}],
                   'result': 'y = 7/6 + 1.5 x', 'interpretation': 'Pro Einheit x steigt der angepasste Wert um 1,5; bei x = 0 liegt er bei 7/6.',
                   'source_refs': [p2], 'provenance': 'COURSE_SOURCE', 'claim_support_status': 'PENDING_SEMANTIC_REVIEW'}]
        items = [
            {'item_id': 'q-explain', 'kc_ids': [der], 'difficulty': 'guided', 'required_operation': 'EXPLAIN', 'points': 2, 'format': 'open',
             'prompt': 'Erklären Sie, warum die Größe S_xx = Σ (x_i − x̄)^2 positiv sein muss, damit die Steigung b eindeutig bestimmt ist.',
             'target': {'kind': 'EXPLANANDUM', 'text': 'S_xx'}, 'given': [], 'provenance': 'AUTHOR_CREATED', 'basis_block_ids': ['b-der'],
             'source_refs': [], 'solution_id': 's-explain', 'actual_operation_review': 'PENDING'},
            {'item_id': 'q-derive', 'kc_ids': [der], 'difficulty': 'standard', 'required_operation': 'DERIVE', 'points': 6, 'format': 'open',
             'prompt': 'Leiten Sie die Formel b = S_xy / S_xx für die Steigung der Ausgleichsgeraden her, ausgehend von der Minimierung von S(a,b) = Σ (y_i − a − b x_i)^2.',
             'target': {'kind': 'STATEMENT', 'text': 'b = S_xy / S_xx'}, 'given': [], 'provenance': 'AUTHOR_CREATED',
             'basis_block_ids': ['b-der'], 'source_refs': [], 'solution_id': 's-derive', 'actual_operation_review': 'PENDING'},
            {'item_id': 'q-calc', 'kc_ids': [calc], 'difficulty': 'transfer', 'required_operation': 'CALCULATE', 'points': 4, 'format': 'open',
             'prompt': 'Gegeben sind die Messpunkte (0,2), (1,3), (3,7). Berechnen Sie Steigung b und Achsenabschnitt a der Ausgleichsgeraden y = a + b x.',
             'target': {'kind': 'QUANTITY', 'text': 'Steigung b und Achsenabschnitt a'}, 'given': ['(0,2), (1,3), (3,7)'],
             'transfer_relation': 'NEW_PARAMETERS', 'variation': {'from_ref': 'b-ex', 'changed': ['Messpunkte', 'ungleiche x-Abstände']},
             'provenance': 'AUTHOR_CREATED', 'basis_block_ids': ['b-ex'], 'source_refs': [], 'solution_id': 's-calc', 'actual_operation_review': 'PENDING'}]
        sols = [
            _sol('s-explain', 'q-explain', [('S_xx ist eine Summe von Quadraten, also ≥ 0', 'Quadrate reeller Zahlen sind nicht negativ'),
                                            ('S_xx = 0 genau dann, wenn alle x_i = x̄', 'eine Summe nichtnegativer Terme ist genau dann 0, wenn alle 0 sind'),
                                            ('bei S_xx > 0 ist b = S_xy/S_xx definiert und eindeutig', 'Division durch eine positive Zahl')],
                 'S_xx > 0 genau dann, wenn nicht alle x_i gleich sind; sonst ist b unbestimmt.',
                 _rub(('Nichtnegativität begründet', 1, 'Verweis auf Summe von Quadraten'), ('Fall S_xx = 0 erkannt', 1, 'alle x_i gleich ⇒ b unbestimmt')),
                 hints=['Woraus besteht S_xx?', 'Wann ist eine Summe von Quadraten null?']),
            _sol('s-derive', 'q-derive', [(s['statement'], s['justification']) for s in blocks[2]['steps']], 'b = S_xy / S_xx, a = ȳ − b x̄',
                 _rub(('Ableitung nach a korrekt und nach a aufgelöst', 2, 'a = ȳ − b x̄'), ('Ableitung nach b korrekt', 1, 'Σ x_i(y_i − a − b x_i) = 0'),
                      ('Umformung auf zentrierte Summen begründet', 2, 'Σ x̄(y_i − ȳ) = 0 genannt'), ('Minimum begründet', 1, 'Hesse-Matrix/Konvexität')),
                 hints=['Setzen Sie beide partiellen Ableitungen null.', 'Lösen Sie die erste Gleichung nach a auf.', 'Nutzen Sie Σ (y_i − ȳ) = 0.'],
                 alternatives=['Matrixform: Normalengleichung X^T X β = X^T y mit X = [1, x]'], errors=['Vorzeichenfehler beim Ableiten']),
            _sol('s-calc', 'q-calc', [('x̄ = 4/3, ȳ = 4', 'Mittelwerte'), ('S_xx = 16/9 + 1/9 + 25/9 = 14/3', 'Definition'),
                                      ('S_xy = (−4/3)(−2) + (−1/3)(−1) + (5/3)(3) = 8', 'Definition'),
                                      ('b = 8/(14/3) = 12/7, a = 4 − (12/7)(4/3) = 12/7', 'Formeln aus b-der')],
                 'b = 12/7 ≈ 1,714; a = 12/7 ≈ 1,714',
                 _rub(('Mittelwerte korrekt', 1, 'x̄ = 4/3, ȳ = 4'), ('S_xx und S_xy korrekt', 2, '14/3 und 8'), ('a und b korrekt', 1, '12/7, 12/7')),
                 hints=['Berechnen Sie zuerst die Mittelwerte.', 'Zentrieren Sie die Daten.'],
                 numeric_checks=[{'expression': '8/(14/3)', 'expected': 12 / 7}, {'expression': '4 - (12/7)*(4/3)', 'expected': 12 / 7}])]
        notation = [{'notation_id': nt, 'symbol': 'r', 'meaning': None, 'status': 'CONFLICT_REVIEW_REQUIRED',
                     'resolution': {'status': 'OPEN', 'evidence_refs': [res, rank]}}]
        figures = [{'figure_id': 'fig-res', 'purpose': 'Residuen visualisieren', 'didactic_rationale': 'Residuen als vertikale Abstände',
                    'source_element_id': fig, 'status': 'OPEN_NOT_GENERATED', 'necessity': 'SUPPLEMENTARY', 'linked_block_ids': []}]
        issues = [{'issue_id': 'oi-fig', 'object_id': 'fig-res', 'code': 'FIGURE_NOT_GENERATED', 'detail': 'Quelldatei fehlt',
                   'element_ids': [fig]}]
    elif kind == 'law':
        kcs = _kc(plan, 'SUBSUME'); p = _el(manifest, '§ 433 Abs. 2 BGB verpflichtet')
        blocks = [mot,
                  {'block_id': 'b-norm', 'kind': 'NORM_STRUCTURE', 'kc_ids': kcs, 'title': 'Aufbau des Anspruchs',
                   'body': 'Anspruchsgrundlage § 433 Abs. 2 BGB; Tatbestand: wirksamer Kaufvertrag (Antrag und Annahme); Rechtsfolge: Kaufpreiszahlung.',
                   'source_refs': [p], 'provenance': 'COURSE_SOURCE', 'claim_support_status': 'PENDING_SEMANTIC_REVIEW'},
                  {'block_id': 'b-sub', 'kind': 'SUBSUMPTION', 'kc_ids': kcs, 'norm_refs': ['§ 433 Abs. 2 BGB'], 'norm_status': 'NOT_VERIFIED',
                   'title': 'Beispielfall: Fahrrad für 300 Euro',
                   'steps': [{'element': 'Obersatz', 'fact': 'V verlangt von K 300 Euro', 'statement': 'V könnte gegen K einen Anspruch auf Zahlung von 300 Euro aus § 433 Abs. 2 BGB haben.', 'justification': 'Gutachtenstil: Hypothese voranstellen'},
                             {'element': 'Antrag', 'fact': 'V bietet K das Fahrrad für 300 Euro an', 'statement': 'Das Angebot ist ein Antrag mit Kaufgegenstand und Preis.', 'justification': 'essentialia negotii bestimmt'},
                             {'element': 'Annahme', 'fact': 'K nimmt an', 'statement': 'K erklärt vorbehaltlos sein Einverständnis.', 'justification': 'übereinstimmende Willenserklärung'},
                             {'element': 'Rechtsfolge', 'fact': 'K hat nicht gezahlt', 'statement': 'Ein wirksamer Kaufvertrag liegt vor; V hat den Anspruch.', 'justification': 'Tatbestand erfüllt, keine Einwendungen ersichtlich'}],
                   'source_refs': [p], 'provenance': 'COURSE_SOURCE', 'claim_support_status': 'PENDING_SEMANTIC_REVIEW'}]
        items = [
            {'item_id': 'q-recall', 'kc_ids': kcs, 'difficulty': 'recall', 'required_operation': 'RECALL', 'points': 2, 'format': 'open',
             'prompt': 'Nennen Sie die Voraussetzungen des Kaufpreisanspruchs aus § 433 Abs. 2 BGB.',
             'target': {'kind': 'TERM', 'text': 'Voraussetzungen des Kaufpreisanspruchs'}, 'given': [], 'provenance': 'AUTHOR_CREATED',
             'basis_block_ids': ['b-norm'], 'source_refs': [], 'solution_id': 's-recall', 'actual_operation_review': 'PENDING'},
            {'item_id': 'q-case', 'kc_ids': kcs, 'difficulty': 'transfer', 'required_operation': 'SUBSUME', 'points': 10, 'format': 'open',
             'prompt': 'Sachverhalt: A bietet B per E-Mail sein gebrauchtes Lehrbuch für 25 Euro an. B antwortet am selben Tag: „Einverstanden.“ '
                       'Nach der Übergabe zahlt B nicht. Hat A gegen B einen Anspruch auf Zahlung von 25 Euro aus § 433 Abs. 2 BGB? Prüfen Sie gutachterlich.',
             'target': {'kind': 'LEGAL_QUESTION', 'text': 'Anspruch auf Zahlung von 25 Euro aus § 433 Abs. 2 BGB'},
             'given': ['A bietet B per E-Mail sein gebrauchtes Lehrbuch für 25 Euro an'], 'transfer_relation': 'NEW_CASE',
             'variation': {'from_ref': 'b-sub', 'changed': ['Kaufgegenstand', 'Erklärungsweg E-Mail', 'Preis']},
             'provenance': 'AUTHOR_CREATED', 'basis_block_ids': ['b-sub'], 'source_refs': [], 'solution_id': 's-case', 'actual_operation_review': 'PENDING'}]
        sols = [
            _sol('s-recall', 'q-recall', [('wirksamer Kaufvertrag', 'Tatbestand des § 433 Abs. 2 BGB'),
                                          ('Vertragsschluss durch Antrag und Annahme', 'zwei übereinstimmende Willenserklärungen')],
                 'Wirksamer Kaufvertrag (Antrag und Annahme); keine rechtshindernden Einwendungen.',
                 _rub(('Kaufvertrag genannt', 1, 'wirksamer Kaufvertrag'), ('Antrag und Annahme genannt', 1, 'zwei Willenserklärungen')),
                 hints=['Welcher Vertrag begründet die Pflicht?', 'Wie kommt ein Vertrag zustande?']),
            _sol('s-case', 'q-case', [('Obersatz: A könnte gegen B einen Anspruch auf 25 Euro aus § 433 Abs. 2 BGB haben.', 'Gutachtenstil'),
                                      ('Antrag: E-Mail des A mit Gegenstand und Preis', 'bestimmter Antrag'),
                                      ('Annahme: „Einverstanden“ am selben Tag', 'rechtzeitige vorbehaltlose Annahme'),
                                      ('Ergebnis: Anspruch besteht; Nichtzahlung ändert daran nichts', 'Nichterfüllung lässt Anspruch unberührt')],
                 'A hat gegen B einen Anspruch auf Zahlung von 25 Euro aus § 433 Abs. 2 BGB.',
                 _rub(('Obersatz korrekt', 2, 'Anspruchsteller, -gegner, Grundlage'), ('Antrag subsumiert', 3, 'Gegenstand und Preis aus dem Sachverhalt'),
                      ('Annahme subsumiert', 3, 'Einverständnis, Rechtzeitigkeit'), ('Ergebnis im Gutachtenstil', 2, 'Schlusssatz')),
                 hints=['Beginnen Sie mit dem Obersatz.', 'Prüfen Sie Antrag und Annahme getrennt.'],
                 errors=['Urteilsstil statt Gutachtenstil', 'Nichtzahlung als Tatbestandsmerkmal behandelt'])]
        notation, figures, issues = [], [], []
    else:
        imp = _kc(plan, 'IMPLEMENT')[0]; p = _el(manifest, 'Für $L(w)')
        blocks = [mot,
                  {'block_id': 'b-alg', 'kind': 'ALGORITHM', 'kc_ids': [imp], 'title': 'Ein Gradientenschritt',
                   'body': 'def gd_step(X, y, w, eta):\n    n = len(y)\n    grad = -2 / n * X.T @ (y - X @ w)\n    return w - eta * grad',
                   'steps': [{'statement': 'Residuum y − Xw berechnen', 'justification': 'geht in den Gradienten ein'},
                             {'statement': 'Gradient −(2/n) Xᵀ(y − Xw)', 'justification': 'Ableitung von (1/n)||y − Xw||^2'},
                             {'statement': 'w − η·grad', 'justification': 'Schritt entgegen dem steilsten Anstieg'}],
                   'source_refs': [p], 'provenance': 'COURSE_SOURCE', 'claim_support_status': 'PENDING_SEMANTIC_REVIEW'}]
        items = [
            {'item_id': 'q-why', 'kc_ids': [imp], 'difficulty': 'guided', 'required_operation': 'EXPLAIN', 'points': 2, 'format': 'open',
             'prompt': 'Erklären Sie, warum im Update w ← w − η ∇L(w) das Minuszeichen steht.',
             'target': {'kind': 'EXPLANANDUM', 'text': 'Minuszeichen'}, 'given': [], 'provenance': 'AUTHOR_CREATED',
             'basis_block_ids': ['b-alg'], 'source_refs': [], 'solution_id': 's-why', 'actual_operation_review': 'PENDING'},
            {'item_id': 'q-impl', 'kc_ids': [imp], 'difficulty': 'transfer', 'required_operation': 'IMPLEMENT', 'points': 6, 'format': 'open',
             'prompt': 'Implementieren Sie in Python eine Funktion gd_step(X, y, w, eta), die einen Schritt des Gradientenabstiegs für '
                       'L(w) = (1/n)·||y − Xw||^2 ausführt, und wenden Sie sie auf X = [[1],[2]], y = [2,4], w = [0], eta = 0.1 an.',
             'target': {'kind': 'ARTIFACT', 'text': 'Funktion gd_step(X, y, w, eta)'}, 'given': ['X = [[1],[2]], y = [2,4], w = [0], eta = 0.1'],
             'transfer_relation': 'NEW_PROBLEM', 'variation': {'from_ref': 'b-alg', 'changed': ['konkrete Daten', 'Funktionsschnittstelle']},
             'provenance': 'AUTHOR_CREATED', 'basis_block_ids': ['b-alg'], 'source_refs': [], 'solution_id': 's-impl', 'actual_operation_review': 'PENDING'}]
        sols = [
            _sol('s-why', 'q-why', [('∇L zeigt in Richtung des steilsten Anstiegs', 'Eigenschaft des Gradienten'),
                                    ('für kleine η > 0 sinkt L entlang −∇L', 'Taylor erster Ordnung: L(w − η∇L) ≈ L(w) − η||∇L||^2')],
                 'Man geht entgegen dem Gradienten, weil L lokal in dieser Richtung am stärksten fällt.',
                 _rub(('Richtung des Gradienten', 1, 'steilster Anstieg'), ('Abstieg begründet', 1, 'Taylor-Argument oder Vorzeichen')),
                 hints=['Wohin zeigt der Gradient?']),
            _sol('s-impl', 'q-impl', [('grad = −(2/2)·Xᵀ(y − X·0) = −(1·2 + 2·4) = −10', 'Formel mit n = 2'),
                                      ('w = 0 − 0.1·(−10) = 1.0', 'Updateschritt')],
                 'gd_step wie in b-alg; Ergebnis w = [1.0]',
                 _rub(('Gradient korrekt implementiert', 3, 'Faktor −2/n und Xᵀ(y − Xw)'), ('Update korrekt', 1, 'w − eta*grad'),
                      ('Anwendung korrekt', 2, 'w = [1.0]')),
                 hints=['Berechnen Sie zuerst das Residuum.', 'Achten Sie auf den Faktor 2/n.'],
                 tests=[{'input': {'X': [[1], [2]], 'y': [2, 4], 'w': [0], 'eta': 0.1}, 'expected': [1.0]},
                        {'input': {'X': [[1], [1]], 'y': [1, 1], 'w': [1], 'eta': 0.5}, 'expected': [1.0]}],
                 numeric_checks=[{'expression': '0 - 0.1*(-(2/2)*(1*2+2*4))', 'expected': 1.0}])]
        notation, figures, issues = [], [], []
    rel = [{'from': a['item_id'], 'to': a['solution_id'], 'type': 'solved_by'} for a in items] + \
          [{'from': a['item_id'], 'to': b, 'type': 'practises_block'} for a in items for b in a['basis_block_ids']]
    return {**base, 'blocks': blocks, 'assessments': items, 'solutions': sols, 'notation': notation, 'figures': figures,
            'open_issues': issues, 'relations': rel}


def negative(ast_, case, manifest):
    """(a)-(i) mutations of the positive math AST."""
    a = copy.deepcopy(ast_); it = {x['item_id']: x for x in a['assessments']}
    if case == 'a_unsolvable':
        it['q-calc'].update(prompt='Berechnen Sie die gesuchte Größe.', target=None, given=[])
    elif case == 'b_derive_by_define':
        it['q-derive'].update(prompt='Definieren Sie die Steigung b = S_xy / S_xx der Ausgleichsgeraden.')
    elif case == 'c_transfer_label':
        it['q-explain'].update(prompt='Definieren Sie die Größe S_xx.', required_operation='DEFINE', difficulty='transfer',
                               transfer_relation='NEW_PARAMETERS', variation={'from_ref': 'b-der', 'changed': ['nichts Relevantes']})
    elif case == 'd_motivation_only':
        for x in a['assessments']:
            x['basis_block_ids'] = ['b-mot']
        a['relations'] = [r for r in a['relations'] if r['type'] == 'solved_by']
    elif case == 'e_invented_anchor':
        a['blocks'][2]['source_refs'] = ['el-0000000000000000']
    elif case == 'f_essential_image':
        a['figures'][0].update(status='SOURCE_ASSET_REUSED', necessity='ESSENTIAL', linked_block_ids=['b-der'],
                               caption='Residuen', alt_text='Plot', review_status='UNREVIEWED')
    elif case == 'g_notation':
        a['notation'][0].update(meaning='Residuum bzw. Rang der Designmatrix', status='CONSISTENT', resolution=None)
    elif case == 'h_self_release':
        a['blocks'][2]['claim_support_status'] = 'MODEL_REVIEWED_SUPPORTED'
        a['blocks'][3]['claim_support_status'] = 'ACADEMIC_VERIFIED'
        a['academic_status'] = 'ACADEMIC_VERIFIED'
        a['reviews'] = [{'review_id': 'rv-fake', 'reviewer_kind': 'TEST_FIXTURE', 'reviewer_id': 'fake', 'provider': 'fake',
                         'assertion_id': 'b-model', 'evidence_refs': ['x'], 'verdict': 'SUPPORTED', 'timestamp': 1, 'build_id': 'b'}]
    return a
