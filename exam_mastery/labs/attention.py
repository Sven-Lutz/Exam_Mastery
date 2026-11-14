"""Lab 'attention' (NLP): scaled dot-product self-attention on a toy sentence, one or two heads, optional causal mask.

Q = X W_Q, K = X W_K, V = X W_V; S = Q K^T / sqrt(d_k); A = row-wise softmax(S) (masked entries -> weight 0); O = A V;
two heads: concat(O_1, O_2) (no output projection W_O in this lab). The browser mirrors these functions
(templates/em_labs.js, EM.models.att*) and is tested against them on random inputs.
"""
import math

from . import build as B

DEFAULT = {'tokens': ['Die', 'Katze', 'jagt', 'sie'],
           'X': [[1, 0, 1, 0], [0, 2, 0, 1], [1, 1, 0, 0], [0, 1, 1, 1]],
           'heads': [{'Wq': [[1, 0], [0, 1], [1, 0], [0, 1]], 'Wk': [[0, 1], [1, 0], [0, 1], [1, 1]], 'Wv': [[1, 0], [0, 1], [1, 1], [0, 0]]},
                     {'Wq': [[0, 1], [1, 0], [0, 0], [1, 1]], 'Wk': [[1, 0], [0, 0], [1, 1], [0, 1]], 'Wv': [[0, 1], [1, 1], [0, 0], [1, 0]]}],
           'query': 0}


class AttError(B.LabError):
    pass


def matmul(A, Bm):
    return [[sum(A[i][k] * Bm[k][j] for k in range(len(Bm))) for j in range(len(Bm[0]))] for i in range(len(A))]


def transpose(A):
    return [list(r) for r in zip(*A)]


def softmax(row, mask=None):
    """Stable softmax; masked entries (mask[j] False) get weight 0."""
    keep = [mask is None or mask[j] for j in range(len(row))]
    mx = max(x for x, k in zip(row, keep) if k)
    e = [math.exp(x - mx) if k else 0.0 for x, k in zip(row, keep)]
    z = sum(e)
    return [x / z for x in e]


def head(X, h, causal=False):
    Q, K, V = matmul(X, h['Wq']), matmul(X, h['Wk']), matmul(X, h['Wv'])
    dk = len(h['Wq'][0]); n = len(X)
    raw = matmul(Q, transpose(K)); S = [[x / math.sqrt(dk) for x in r] for r in raw]
    A = [softmax(S[i], [(not causal) or j <= i for j in range(n)]) for i in range(n)]
    return {'Q': Q, 'K': K, 'V': V, 'raw': raw, 'S': S, 'A': A, 'O': matmul(A, V), 'dk': dk}


def multi(X, heads, causal=False):
    hs = [head(X, h, causal) for h in heads]
    return {'heads': hs, 'concat': [sum((hh['O'][i] for hh in hs), []) for i in range(len(X))]}


def check_data(d):
    try:
        toks, X, heads = list(d['tokens']), [[float(x) for x in r] for r in d['X']], d['heads']
    except (KeyError, TypeError, ValueError):
        raise AttError('Attention-Daten brauchen tokens, X und heads')
    n = len(toks)
    if not 2 <= n <= 6 or len(X) != n:
        raise AttError('2 bis 6 Tokens, X mit einer Zeile je Token')
    dm = len(X[0])
    if not 1 <= dm <= 6 or any(len(r) != dm for r in X):
        raise AttError('X muss n × d mit 1 ≤ d ≤ 6 sein')
    if not 1 <= len(heads) <= 2:
        raise AttError('ein oder zwei Heads')
    out = []
    for h in heads:
        W = {}
        for k in ('Wq', 'Wk', 'Wv'):
            M = [[float(x) for x in r] for r in h[k]]
            if len(M) != dm or not M[0] or len(M[0]) > 4 or any(len(r) != len(M[0]) for r in M):
                raise AttError(f'{k} muss d × d_k mit d_k ≤ 4 sein')
            W[k] = M
        if len(W['Wq'][0]) != len(W['Wk'][0]):
            raise AttError('W_Q und W_K brauchen dieselbe Spaltenzahl d_k')
        out.append(W)
    if any(not math.isfinite(x) or abs(x) > 99 for M in [X] + [W[k] for W in out for k in W] for r in M for x in r):
        raise AttError('Einträge müssen endlich und betragsmäßig < 100 sein')
    return {'tokens': [str(t) for t in toks], 'X': X, 'heads': out}


def _f(x, d=2):
    return B._fmt(x, d)


def _vec(v, d=2):
    return '(' + '; '.join(_f(x, d) for x in v) + ')'


def tok(m, j):
    return f'„{m["tokens"][j]}“ ({j + 1})'


def spec(lab_id, title, kc_ids, sources, data, course=''):
    data = dict(data or {})
    if 'X' not in data:
        data = {**DEFAULT, **data}
    m = check_data(data)
    n = len(m['tokens']); q0 = int(data.get('query', 0))
    if not 0 <= q0 < n:
        raise AttError('query außerhalb der Tokens')
    r = multi(m['X'], m['heads'])
    row = r['heads'][0]['A'][q0]
    order = sorted(range(n), key=lambda j: -row[j])
    if row[order[0]] - row[order[1]] < 0.01:
        raise AttError('die Abfrage hat kein eindeutiges Maximum (Gewichte fast gleich); andere Daten wählen')
    model = {'kind': 'attention', 'att': m, 'query': q0,
             'equations': ['Q = X W_Q,  K = X W_K,  V = X W_V   (X: n × d, W: d × d_k)',
                           'S = Q K^T / √d_k   (n × n);  A = softmax_Zeile(S);  O = A V   (n × d_v)',
                           'kausale Maske: S_{ij} = −∞ für j > i, also α_{ij} = 0',
                           'Multi-Head: concat(O_1, O_2)  (n × 2 d_v); eine Ausgabeprojektion W_O lässt dieses Lab weg']}
    params = [{'id': 'q', 'label': 'Abfrage (Query-Token)', 'type': 'select', 'default': str(q0),
               'options': [{'value': str(j), 'label': tok(m, j)} for j in range(n)]},
              {'id': 'causal', 'label': 'Kausale Maske', 'type': 'select', 'default': 'nein',
               'options': [{'value': 'nein', 'label': 'aus (Encoder)'}, {'value': 'ja', 'label': 'an (Decoder: nur frühere Tokens)'}]},
              {'id': 'head', 'label': 'Head', 'type': 'select', 'default': '1',
               'options': [{'value': '1', 'label': 'Head 1'}] + ([{'value': '2', 'label': 'Head 2'}, {'value': 'concat', 'label': 'beide (concat)'}] if len(m['heads']) == 2 else [])}]
    sp = {'schema': B.SCHEMA, 'id': lab_id, 'version': 1, 'title': title, 'domain': 'nlp', 'course': course, 'kc_ids': list(kc_ids),
          'model': model, 'params': params,
          'objective': 'Sie können Scaled Dot-Product Self-Attention für einen kurzen Satz von Hand rechnen (Scores, Softmax, gewichtete Summe), '
                       'die Formen aller Matrizen angeben und die Wirkung von Skalierung, kausaler Maske und mehreren Heads erklären.',
          'prerequisites': ['Matrixmultiplikation', 'Skalarprodukt', 'Exponentialfunktion'],
          'assumptions': ['Spielzeug-Einbettungen und Gewichte (kleine ganze Zahlen) statt gelernter Werte; keine Positionskodierung.',
                          'Keine Ausgabeprojektion W_O, kein Residual, keine Normalisierung: nur der Attention-Kern.',
                          'Softmax numerisch stabil (Maximum je Zeile abgezogen); maskierte Einträge erhalten Gewicht 0.'],
          'sources': list(sources) + ['Referenzmodell: exam_mastery/labs/attention.py',
                                      'Vaswani et al. (2017), Attention Is All You Need, Abschnitt 3.2'],
          'explanations': ['Jede Zeile von A ist eine Wahrscheinlichkeitsverteilung über die Tokens: Wie stark fließt der Wert v_j in die Ausgabe von Token i ein.',
                           'Ohne Division durch √d_k wachsen die Skalarprodukte mit d_k; die Softmax wird dann fast ein Argmax und ihre Gradienten verschwinden.']}
    sq = _sequence(sp, m, r, q0, order[0]); sq['_choice'] = sq.pop('choice')
    sp['sequence'] = sq
    sp['tests'] = [{'params': {'q': str(q0), 'causal': 'nein', 'head': '1'}, 'A': r['heads'][0]['A'], 'concat': r['concat']}]
    return sp


def _sequence(sp, m, r, q0, jstar):
    h = r['heads'][0]; n = len(m['tokens']); dk = h['dk']; tol = 0.006
    qv, kv = h['Q'][q0], h['K'][jstar]
    s_exp = h['S'][q0][jstar]; raw = h['raw'][q0][jstar]
    t1 = {'id': 'score', 'title': 'Ein Attention-Score',
          'prompt': f'Head 1: q = Zeile {q0 + 1} von Q = {_vec(qv)}, k = Zeile {jstar + 1} von K = {_vec(kv)}, d_k = {dk}. Berechnen Sie den skalierten Score s = q · k / √d_k.',
          'expected': round(s_exp, 6), 'tolerance': tol,
          'errors': _distinct(s_exp, [(raw, 'Das ist das unskalierte Skalarprodukt. Teilen Sie durch √d_k.'), (raw / dk, 'Geteilt wird durch √d_k, nicht durch d_k.')], tol),
          'hints': ['Skalarprodukt: Summe der Produkte der Komponenten.', f'q · k = {_f(raw)}; dann durch √{dk} = {_f(math.sqrt(dk), 3)} teilen.'],
          'solution': [' + '.join(f'{_f(a)} · {_f(b)}' for a, b in zip(qv, kv)) + f' = {_f(raw)};  {_f(raw)} / √{dk} = {_f(s_exp, 3)}.'],
          'feedback_correct': 'Richtig.'}
    row, srow = h['A'][q0], h['S'][q0]
    unscaled = softmax(h['raw'][q0])[jstar]
    lin = srow[jstar] / sum(srow) if all(x > 0 for x in srow) else None
    t2 = {'id': 'alpha', 'title': 'Ein Softmax-Gewicht',
          'prompt': f'Scores der Zeile {q0 + 1} (Head 1, ohne Maske): ' + ', '.join(f's_{j + 1} = {_f(x, 3)}' for j, x in enumerate(srow)) +
                    f'. Berechnen Sie das Gewicht α = softmax(s)_{jstar + 1}, mit dem {tok(m, q0)} auf {tok(m, jstar)} achtet.',
          'expected': round(row[jstar], 6), 'tolerance': tol,
          'errors': _distinct(row[jstar], [(unscaled, 'Das ist die Softmax der unskalierten Scores.'), (lin, 'Softmax normiert e^{s_j}, nicht die Scores selbst.'),
                                           (1 / n, 'Gleichverteilung 1/n: Die Scores unterscheiden sich, also auch die Gewichte.')], tol),
          'hints': ['α_j = e^{s_j} / Σ_k e^{s_k}.', 'e-Werte: ' + ', '.join(_f(math.exp(x), 3) for x in srow) + '.'],
          'solution': [f'e^{{{_f(srow[jstar], 3)}}} / ({" + ".join(_f(math.exp(x), 3) for x in srow)}) = {_f(row[jstar], 3)}.'],
          'feedback_correct': 'Richtig: Die Gewichte einer Zeile sind positiv und summieren sich zu 1.'}
    hc = head(m['X'], m['heads'][0], True)
    tq = max(1, min(n - 1, q0 if q0 >= 1 else 1))
    a_c, a_u = hc['A'][tq][0], h['A'][tq][0]
    t3 = {'id': 'causal', 'title': 'Transfer: kausale Maske',
          'prompt': f'Decoder-Variante mit kausaler Maske (Token i sieht nur Tokens j ≤ i). Wie groß ist in Head 1 das Gewicht, mit dem {tok(m, tq)} auf {tok(m, 0)} achtet?',
          'expected': round(a_c, 6), 'tolerance': tol,
          'errors': _distinct(a_c, [(a_u, 'Das ist das Gewicht ohne Maske. Mit Maske fallen spätere Tokens weg, die übrigen Gewichte werden neu normiert.'),
                                    (1 / (tq + 1), 'Gleichverteilung über die sichtbaren Tokens stimmt nur bei gleichen Scores.')], tol),
          'hints': [f'Sichtbar sind nur die Tokens 1 … {tq + 1}.', 'Softmax nur über die sichtbaren Scores: ' + ', '.join(_f(x, 3) for x in h['S'][tq][:tq + 1]) + '.'],
          'solution': [f'α = {_f(a_c, 3)} (ohne Maske {_f(a_u, 3)}).'], 'feedback_correct': 'Richtig: Die Maske entfernt Spalten, die Zeile wird neu normiert.'}
    choice = {'id': 'scale', 'type': 'choice', 'title': 'Warum √d_k?',
              'prompt': 'Warum teilt man die Scores durch √d_k?',
              'options': [{'value': 'var', 'label': 'Damit die Varianz der Skalarprodukte nicht mit d_k wächst; sonst wird die Softmax fast ein Argmax mit winzigen Gradienten.', 'feedback': ''},
                          {'value': 'sum1', 'label': 'Damit sich die Gewichte jeder Zeile zu 1 summieren.', 'feedback': 'Das leistet die Softmax selbst, mit oder ohne Skalierung.'},
                          {'value': 'pos', 'label': 'Damit alle Scores positiv werden.', 'feedback': 'Division durch eine positive Zahl ändert kein Vorzeichen.'},
                          {'value': 'order', 'label': 'Damit sich die Reihenfolge der Gewichte ändert.', 'feedback': 'Eine positive Skalierung erhält die Reihenfolge; sie ändert nur, wie spitz die Verteilung ist.'}],
              'correct': 'var', 'explanation': 'Bei unabhängigen Komponenten mit Varianz 1 hat q · k die Varianz d_k; √d_k bringt sie zurück auf 1.'}
    predict = {'question': f'Head 1, ohne Maske: Auf welches Token achtet {tok(m, q0)} am stärksten?',
               'options': [{'value': str(j), 'label': tok(m, j)} for j in range(n)], 'correct': str(jstar),
               'change': [{'param': 'q', 'to': str(q0)}, {'param': 'causal', 'to': 'nein'}],
               'result_text': f'Das größte Gewicht erhält {tok(m, jstar)}. Wie groß es ist, rechnen Sie in der Simulation selbst aus.',
               'explanation': 'Das Gewicht hängt am Score q_i · k_j: Entscheidend ist, wie gut die Abfrage von Token i zum Schlüssel von Token j passt – nicht die Bedeutung der Wörter und nicht die Position.'}
    return {'predict': predict, 'tasks': [t1, t2, t3], 'choice': choice}


def _distinct(expected, cands, tol):
    out, seen = [], [expected]
    for v, msg in cands:
        if v is None or not math.isfinite(v) or any(abs(v - w) <= 2 * tol for w in seen):
            continue
        out.append({'value': round(v, 6), 'message': msg}); seen.append(v)
    return out


def pedagogy(spec):
    return {'explain_prompt': 'Erklären Sie, warum gerade dieses Token das größte Gewicht erhält.',
            'explain_keys': [{'label': 'Skalarprodukt Query · Key', 'terms': ['skalar', 'query', 'key', 'q ·', 'q·k', 'passt']},
                             {'label': 'Softmax verstärkt den größten Score', 'terms': ['softmax', 'exponent', 'e^']},
                             {'label': 'gelernte Projektionen, nicht Wortbedeutung', 'terms': ['w_q', 'w_k', 'projektion', 'gewicht', 'matrix']}],
            'explore': [], 'choice': spec['sequence'].pop('_choice'),
            'takeaways': ['Self-Attention: Jedes Token bildet eine Abfrage q, vergleicht sie per Skalarprodukt mit allen Schlüsseln k und mittelt die Werte v mit Softmax-Gewichten.',
                          'Formen: X n × d, Q und K n × d_k, S und A n × n, O n × d_v; zwei Heads ergeben n × 2 d_v.',
                          'Die kausale Maske setzt Gewichte auf spätere Tokens auf 0; die Zeile wird neu normiert.'],
            'summary_prompt': 'Fassen Sie in einem Satz zusammen, wie aus X die Ausgabe O eines Attention-Heads entsteht.',
            'transfer_id': 'causal'}


def check(spec):
    m = spec['model']
    ref = B.attention_spec(spec['id'], spec['title'], spec['kc_ids'], [], {**m['att'], 'query': m['query']})
    strip = lambda ts: [{k: v for k, v in t.items() if k != 'transfer'} for t in ts]
    if strip(spec['sequence']['tasks']) != strip(ref['sequence']['tasks']) or spec['sequence']['predict']['correct'] != ref['sequence']['predict']['correct']:
        raise AttError('Attention-Lab: Aufgaben oder Vorhersage weichen vom Referenzmodell ab')
    r = multi(m['att']['X'], m['att']['heads'])
    for case in spec.get('tests') or []:
        if any(abs(a - b) > 1e-9 for ra, rb in zip(r['heads'][0]['A'], case['A']) for a, b in zip(ra, rb)):
            raise AttError('Attention-Lab: Testfall stimmt nicht')


def static_svg(spec):
    """Data flow with explicit shapes (no attention weights: those are the learner's to compute)."""
    m = spec['model']['att']; n = len(m['tokens']); d = len(m['X'][0]); dk = len(m['heads'][0]['Wq'][0]); dv = len(m['heads'][0]['Wv'][0])
    W, H = 640, 300
    box = lambda x, y, w, t1, t2, fill='#f6efe2': (f'<rect x="{x}" y="{y}" width="{w}" height="50" rx="6" fill="{fill}" stroke="#334"/>'
                                                   f'<text x="{x + w / 2}" y="{y + 21}" text-anchor="middle" font-size="13" font-weight="700" fill="#223">{t1}</text>'
                                                   f'<text x="{x + w / 2}" y="{y + 39}" text-anchor="middle" font-size="11" fill="#5b6876">{t2}</text>')
    arr = lambda x1, y1, x2, y2: f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#1f5f8b" stroke-width="2" marker-end="url(#at-ah)"/>'
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="Datenfluss der Self-Attention mit Formen">'
         '<title>Scaled Dot-Product Self-Attention: Datenfluss und Formen</title>',
         '<defs><marker id="at-ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#1f5f8b"/></marker></defs>',
         f'<text x="20" y="22" font-size="12" fill="#223">Satz: {" · ".join(B.E(t) for t in m["tokens"])}</text>',
         box(20, 120, 90, 'X', f'{n} × {d}', '#dcebf5'),
         box(160, 40, 100, 'Q = X W_Q', f'{n} × {dk}'), box(160, 120, 100, 'K = X W_K', f'{n} × {dk}'), box(160, 200, 100, 'V = X W_V', f'{n} × {dv}'),
         box(310, 80, 130, 'S = QKᵀ/√d_k', f'{n} × {n}'), box(310, 160, 130, 'A = softmax(S)', f'{n} × {n}, Zeilensumme 1'),
         box(490, 160, 130, 'O = A V', f'{n} × {dv}' + (f' · concat: {n} × {2 * dv}' if len(m['heads']) == 2 else ''), '#dcebf5'),
         arr(110, 135, 158, 70), arr(110, 145, 158, 145), arr(110, 155, 158, 220), arr(260, 65, 308, 100), arr(260, 145, 308, 110),
         arr(375, 130, 375, 158), arr(440, 185, 488, 185), arr(260, 225, 488, 195),
         f'<text x="20" y="{H - 12}" font-size="11" fill="#5b6876">d = {d}, d_k = {dk}, {len(m["heads"])} Head(s); kausale Maske optional: S_ij = −∞ für j &gt; i</text></svg>']
    return ''.join(s)
