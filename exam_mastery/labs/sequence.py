"""Lab 'sequence' (analysis): real sequences a_n, epsilon band around a limit, first index N(eps) on a finite horizon.

Sequences are given in a tiny safe expression language (numbers, n, a, + - * / ^, sqrt(), abs(), parentheses); there is
no eval(). Explicit: a_n = f(n). Recursive: a_1 given, a_{n+1} = f(a_n, n) with 'a' = a_n. The browser mirrors parser and
evaluator (templates/em_labs.js, EM.models.seq*) and is tested against this reference on random inputs.

Everything the lab reports is numerical evidence over the computed horizon n <= H, never a proof of convergence.
"""
import math
import re

from . import build as B

MAX_LEN, MAX_H = 160, 2000
EPS_OPTIONS = ['0.5', '0.2', '0.1', '0.05', '0.02', '0.01', '0.005', '0.002', '0.001']
TOK = re.compile(r'\s*(?:(\d+(?:\.\d+)?)|(sqrt|abs|n|a)|([-+*/^()]))')
DEFAULT = {'expr': 'n/(n+1)', 'limit': 1, 'eps': 0.1, 'horizon': 200, 'label': 'a_n = n/(n+1)',
           'examples': [{'label': 'a_n = (−1)^n/n', 'expr': '(-1)^n/n', 'limit': 0},
                        {'label': 'a_n = (1 + 1/n)^n', 'expr': '(1+1/n)^n', 'limit': 2.718281828459045},
                        {'label': 'a_n = √(n+1) − √n', 'expr': 'sqrt(n+1)-sqrt(n)', 'limit': 0},
                        {'label': 'a_1 = 1, a_{n+1} = √(2 + a_n)', 'rec': 'sqrt(2+a)', 'a1': 1, 'limit': 2},
                        {'label': 'a_n = (−1)^n (nicht konvergent)', 'expr': '(-1)^n', 'limit': 1}]}


class SeqError(B.LabError):
    pass


def parse(src, allow_a=False):
    """Expression -> AST of nested lists (JSON-compatible, identical to the browser parser)."""
    if not isinstance(src, str) or not src.strip() or len(src) > MAX_LEN:
        raise SeqError('Ausdruck fehlt oder ist zu lang')
    toks, i, s = [], 0, src.rstrip()
    while i < len(s):
        m = TOK.match(s, i)
        if not m or m.end() == i:
            raise SeqError(f'unerlaubtes Zeichen an Position {i + 1}')
        toks.append(('num', float(m[1])) if m[1] else ('id', m[2]) if m[2] else ('op', m[3])); i = m.end()
    pos = [0]

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else ('end', None)

    def take(kind, val=None):
        t = peek()
        if t[0] != kind or (val is not None and t[1] != val):
            raise SeqError('Syntaxfehler im Ausdruck')
        pos[0] += 1; return t

    def expr(d):
        if d > 40:
            raise SeqError('Ausdruck zu tief verschachtelt')
        x = term(d)
        while peek() in (('op', '+'), ('op', '-')):
            o = take('op')[1]; x = [o, x, term(d)]
        return x

    def term(d):
        x = unary(d)
        while peek() in (('op', '*'), ('op', '/')):
            o = take('op')[1]; x = [o, x, unary(d)]
        return x

    def unary(d):
        if peek() == ('op', '-'):
            take('op'); return ['neg', unary(d + 1)]
        if peek() == ('op', '+'):
            take('op'); return unary(d + 1)
        x = atom(d)
        if peek() == ('op', '^'):
            take('op'); x = ['^', x, unary(d + 1)]
        return x

    def atom(d):
        t = peek()
        if t[0] == 'num':
            pos[0] += 1; return ['num', t[1]]
        if t[0] == 'id':
            pos[0] += 1
            if t[1] in ('sqrt', 'abs'):
                take('op', '('); x = expr(d + 1); take('op', ')'); return [t[1], x]
            if t[1] == 'a' and not allow_a:
                raise SeqError('„a“ ist nur in rekursiven Folgen erlaubt')
            return ['var', t[1]]
        if t == ('op', '('):
            take('op'); x = expr(d + 1); take('op', ')'); return x
        raise SeqError('Syntaxfehler im Ausdruck')

    ast = expr(0)
    if pos[0] != len(toks):
        raise SeqError('Syntaxfehler: unerwartetes Zeichen (Multiplikation bitte mit * schreiben)')
    return ast


def ev(ast, n, a=0.0):
    k = ast[0]
    if k == 'num':
        return ast[1]
    if k == 'var':
        return float(n) if ast[1] == 'n' else a
    if k == 'neg':
        return -ev(ast[1], n, a)
    if k == 'sqrt':
        x = ev(ast[1], n, a)
        if x < 0:
            raise SeqError(f'Wurzel aus negativer Zahl bei n = {n}')
        return math.sqrt(x)
    if k == 'abs':
        return abs(ev(ast[1], n, a))
    x, y = ev(ast[1], n, a), ev(ast[2], n, a)
    if k == '+':
        r = x + y
    elif k == '-':
        r = x - y
    elif k == '*':
        r = x * y
    elif k == '/':
        if y == 0:
            raise SeqError(f'Division durch 0 bei n = {n}')
        r = x / y
    else:
        if x < 0 and y != math.floor(y):
            raise SeqError(f'negative Basis mit nicht ganzzahligem Exponenten bei n = {n}')
        if x == 0 and y < 0:
            raise SeqError(f'0 hoch negative Zahl bei n = {n}')
        try:
            r = x ** y
        except OverflowError:
            raise SeqError(f'Überlauf bei n = {n}')
    if not math.isfinite(r):
        raise SeqError(f'Wert nicht endlich bei n = {n}')
    return r


def terms(d, H):
    """[a_1, ..., a_H]."""
    H = int(H)
    if not 1 <= H <= MAX_H:
        raise SeqError(f'Horizont muss zwischen 1 und {MAX_H} liegen')
    if d.get('rec'):
        f = parse(d['rec'], True); a = float(d['a1']); out = [a]
        if not math.isfinite(a):
            raise SeqError('a_1 ist keine Zahl')
        for n in range(1, H):
            a = ev(f, n, a); out.append(a)
        return out
    f = parse(d['expr'])
    return [ev(f, n) for n in range(1, H + 1)]


def inside(x, L, eps):
    """|x - L| < eps, conservatively: values within rounding error of the band edge count as outside."""
    return abs(x - L) < eps - 1e-12 * max(1.0, abs(L), eps)


def first_index(ts, L, eps, view='all'):
    """Smallest N (1-based, in the chosen subsequence) such that every computed term with n >= N lies in the band;
    None when the last computed term of the subsequence is outside."""
    idx = [n for n in range(1, len(ts) + 1) if view == 'all' or (n % 2 == 0) == (view == 'even')]
    if not idx:
        return None
    bad = [n for n in idx if not inside(ts[n - 1], L, eps)]
    N = idx[0] if not bad else next((n for n in idx if n > bad[-1]), None)
    if N is None or sum(1 for n in idx if n >= N) < max(5, math.ceil(len(idx) / 10)):
        return None   # a tail of a few in-band terms at the very end is no evidence: at least the last 10 % (min. 5 terms)
    return N


def summary(ts):
    tol = 1e-12
    dif = [ts[i + 1] - ts[i] for i in range(len(ts) - 1)]
    inc = all(x >= -tol * max(1, abs(y)) for x, y in zip(dif, ts)); dec = all(x <= tol * max(1, abs(y)) for x, y in zip(dif, ts))
    return {'mono': 'const' if inc and dec else 'inc' if inc else 'dec' if dec else 'none', 'min': min(ts), 'max': max(ts), 'last': ts[-1]}


def check_data(d):
    d = {**d}
    if not d.get('expr') and not d.get('rec'):
        raise SeqError('Folge braucht "expr" (explizit) oder "rec" mit "a1" (rekursiv)')
    if d.get('rec') and 'a1' not in d:
        raise SeqError('rekursive Folge braucht a1')
    try:
        d['limit'] = float(d['limit'])
    except (KeyError, TypeError, ValueError):
        raise SeqError('Grenzwert-Kandidat "limit" fehlt')
    terms(d, int(d.get('horizon', 200)))
    return d


# ------------------------------------------------------------------ lab spec

def _f(x, d=3):
    return B._fmt(x, d)


def _eps(e):
    return B._fmt(float(e), max(0, -math.floor(math.log10(float(e)) + 1e-9)))


def model_data(spec):
    return spec['model']['seq']


def metrics(spec, params):
    d = model_data(spec); H = int(params.get('horizon', d['horizon']))
    N = first_index(terms(d, H), d['limit'], float(params['eps']), params.get('view', 'all'))
    return {'N': -1 if N is None else N, 'found': 0 if N is None else 1}


def _near(e0):
    vals = [float(x) for x in EPS_OPTIONS]
    return min(vals, key=lambda v: abs(math.log(v / e0)))


def spec(lab_id, title, kc_ids, sources, data, course=''):
    data = dict(data or {})
    if not (data.get('expr') or data.get('rec')):
        data = {**DEFAULT, **data}
    d = check_data(data)
    H = int(d.get('horizon', 200)); L = d['limit']; e0 = _near(float(d.get('eps', 0.1)))
    ts = terms(d, H); N0 = first_index(ts, L, e0)
    if N0 is None or N0 < 2:
        raise SeqError('Für das gewählte ε liegt im Horizont kein (sinnvolles) N vor; ε, Horizont oder Grenzwert anpassen')
    label = d.get('label') or ('a_n = ' + d['expr'] if d.get('expr') else f'a_1 = {d["a1"]}, a_(n+1) = {d["rec"]}')
    seq = {k: d[k] for k in ('expr', 'rec', 'a1') if k in d}
    seq.update(limit=L, horizon=H, label=label)
    exs = [{'label': label, **{k: d[k] for k in ('expr', 'rec', 'a1') if k in d}, 'limit': L}]
    for x in d.get('examples') or []:
        try:
            check_data({**x, 'horizon': 50}); exs.append(x)
        except B.LabError:
            continue
    m = {'kind': 'sequence', 'seq': seq, 'examples': exs,
         'equations': ['a_n → a  ⇔  für jedes ε > 0 gibt es ein N mit |a_n − a| < ε für alle n ≥ N',
                       'N(ε) im Lab: kleinster Index, ab dem alle berechneten Glieder a_N, …, a_H im ε-Band liegen',
                       'Teilfolgen: (a_{2k}) und (a_{2k−1}); konvergiert (a_n), so konvergiert jede Teilfolge gegen denselben Grenzwert']}
    params = [{'id': 'eps', 'label': 'Bandbreite ε', 'type': 'select', 'default': _key(e0),
               'options': [{'value': v, 'label': 'ε = ' + _eps(v)} for v in EPS_OPTIONS]},
              {'id': 'view', 'label': 'Folge oder Teilfolge', 'type': 'select', 'default': 'all',
               'options': [{'value': 'all', 'label': 'alle Glieder a_n'}, {'value': 'even', 'label': 'gerade Indizes a_{2k}'},
                           {'value': 'odd', 'label': 'ungerade Indizes a_{2k−1}'}]},
              {'id': 'horizon', 'label': 'Horizont H (berechnete Glieder)', 'type': 'range', 'min': 20, 'max': MAX_H, 'step': 10,
               'default': min(MAX_H, max(20, int(round(H / 10)) * 10)), 'digits': 0}]
    sp = {'schema': B.SCHEMA, 'id': lab_id, 'version': 1, 'title': title, 'domain': 'analysis', 'course': course, 'kc_ids': list(kc_ids),
          'model': m, 'params': params,
          'objective': 'Sie können die ε-N-Definition des Grenzwerts an einer konkreten Folge anwenden, N(ε) von Hand bestimmen '
                       'und unterscheiden, was eine Rechnung über endlich viele Glieder zeigt und was nur ein Beweis zeigen kann.',
          'prerequisites': ['Betrag und Ungleichungen', 'Folgen a_n als Funktionen ℕ → ℝ'],
          'assumptions': ['Alle Glieder werden in Gleitkommaarithmetik bis zum Horizont H berechnet; über n > H sagt das Lab nichts.',
                          'N(ε) im Lab ist numerische Evidenz über endlich viele Glieder, kein Beweis der Konvergenz.',
                          'Werte, die nur durch Rundung knapp im Band liegen (Abstand ε bis auf 10^-12), zählen als außerhalb.',
                          'Ein N wird nur gemeldet, wenn mindestens die letzten 10 % der berechneten Glieder (mindestens 5) im Band liegen.',
                          'Monotonie und Schranken werden nur auf den berechneten Gliedern geprüft.'],
          'sources': list(sources) + ['Referenzmodell: exam_mastery/labs/sequence.py (Parser ohne eval, ε-Band, N(ε))',
                                      'Forster, Analysis 1, §4 (Konvergenz von Folgen)'],
          'explanations': ['Je kleiner ε, desto später beginnt in der Regel der Teil der Folge, der ganz im Band liegt; wie schnell N(ε) wächst, verrät die Konvergenzgeschwindigkeit.',
                           'Ein Beweis braucht ein N(ε) für jedes ε > 0, meist als Formel aus der Ungleichung |a_n − a| < ε; das Lab prüft nur endlich viele Fälle.']}
    sq = _sequence(sp, ts, e0, N0); sq['_explore'] = sq.pop('explore'); sq['_choice'] = sq.pop('choice')
    sp['sequence'] = sq
    sp['tests'] = [{'params': {p['id']: p['default'] for p in params}, 'N': N0, 'a5': ts[4] if len(ts) >= 5 else None}]
    return sp


def _sequence(sp, ts, e0, N0):
    d = model_data(sp); L = d['limit']; H = d['horizon']; lab = d['label']
    k = 5 if len(ts) >= 6 else 2
    t0 = {'id': 'term', 'title': 'Ein Glied ausrechnen',
          'prompt': f'{lab}. Berechnen Sie a_{k} (3 Nachkommastellen).',
          'expected': round(ts[k - 1], 6), 'tolerance': 0.0006,
          'errors': _distinct(ts[k - 1], [(ts[k - 2], f'Das ist a_{k - 1}: Der Index ist um eins verschoben.'),
                                          (ts[k], f'Das ist a_{k + 1}: Der Index ist um eins verschoben.')], 0.0006),
          'hints': ['Setzen Sie n = ' + str(k) + ' ein' + (' bzw. rechnen Sie die Rekursion von a_1 aus Schritt für Schritt.' if d.get('rec') else '.'),
                    'Erste Glieder: ' + ', '.join(f'a_{i + 1} = {_f(ts[i])}' for i in range(min(k - 1, 3))) + '.'],
          'solution': [f'a_{k} = {_f(ts[k - 1], 4)}.'], 'feedback_correct': 'Richtig.'}
    e0s = _eps(e0)
    t1 = {'id': 'neps', 'title': 'N(ε) von Hand bestimmen',
          'prompt': f'{lab}, Grenzwert-Kandidat a = {_f(L)}. Bestimmen Sie für ε = {e0s} den kleinsten Index N, ab dem |a_n − a| < ε für alle n ≥ N gilt.',
          'expected': N0, 'tolerance': 0.4,
          'errors': _distinct(N0, [(N0 - 1, f'Bei n = {N0 - 1} ist |a_n − a| = {_f(abs(ts[N0 - 2] - L), 4)} – das ist nicht kleiner als ε. Prüfen Sie den Grenzfall mit „<“.'),
                                   (N0 + 1, f'Schon ab n = {N0} liegen alle Glieder im Band. Gesucht ist der kleinste solche Index.')], 0.4),
          'hints': ['Schreiben Sie |a_n − a| als Ausdruck in n und lösen Sie die Ungleichung |a_n − a| < ε nach n auf.',
                    f'Kontrolle am Rand: |a_{N0 - 1} − a| = {_f(abs(ts[N0 - 2] - L), 4)}.'],
          'solution': [f'|a_{N0 - 1} − a| = {_f(abs(ts[N0 - 2] - L), 4)} ≥ ε, aber |a_n − a| < ε für alle berechneten n ≥ {N0} (bis n = {H}). Also N(ε) = {N0}.'],
          'feedback_correct': 'Richtig. Beachten Sie: Die Rechnung im Lab bestätigt das nur bis zum Horizont; die Ungleichung zeigt es für alle n.'}
    # transfer: a ten times smaller band
    vals = [float(x) for x in EPS_OPTIONS]
    e1 = next((v for v in vals if v <= e0 / 5 and first_index(ts, L, v) is not None), None)
    if e1 is None:
        e1 = next((v for v in vals if v < e0 and first_index(ts, L, v) is not None), None)
    if e1 is None:
        raise SeqError('kein kleineres ε mit N im Horizont; Horizont vergrößern')
    N1 = first_index(ts, L, e1)
    t2 = {'id': 'transfer', 'title': 'Transfer: kleineres ε',
          'prompt': f'Dieselbe Folge, nun ε = {_eps(e1)}. Wie groß ist N(ε)? Vergleichen Sie mit N = {N0} für ε = {e0s}: Was verrät das Verhältnis über die Konvergenzgeschwindigkeit?',
          'expected': N1, 'tolerance': 0.4,
          'errors': _distinct(N1, [(round(N0 * e0 / e1), 'N(ε) wächst nicht automatisch proportional zu 1/ε; das hängt davon ab, wie schnell |a_n − a| fällt.'),
                                   (N0, 'Das ist N für das größere ε. Ein schmaleres Band beginnt in der Regel später.')], 0.4),
          'hints': ['Gleiche Ungleichung |a_n − a| < ε, nur mit dem neuen ε.', f'Kontrolle: |a_{N1 - 1} − a| = {_f(abs(ts[N1 - 2] - L), 5)}.' if N1 > 1 else 'Schon a_1 liegt im Band.'],
          'solution': [f'N(ε) = {N1}' + (f' (|a_{N1 - 1} − a| = {_f(abs(ts[N1 - 2] - L), 5)} ≥ ε).' if N1 > 1 else '.'),
                       f'Verhältnis {B._fmt(N1 / N0, 1)} bei ε-Verhältnis {B._fmt(e0 / e1, 0)}: daran sieht man, wie schnell |a_n − a| gegen 0 geht.'],
          'feedback_correct': 'Richtig.'}
    choice = {'id': 'proof', 'type': 'choice', 'title': 'Was zeigt das Lab?',
              'prompt': f'Das Lab findet für ε = {e0s} den Index N = {N0}: Alle berechneten Glieder bis n = {H} liegen im Band. Was folgt daraus?',
              'options': [{'value': 'proof', 'label': 'Die Folge konvergiert gegen a; das ist bewiesen.',
                           'feedback': 'Die Rechnung prüft endlich viele Glieder und ein einziges ε. Konvergenz verlangt ein N für jedes ε > 0 und alle n ≥ N.'},
                          {'value': 'evidence', 'label': 'Es ist numerische Evidenz für einen Kandidaten; ein Beweis braucht eine Abschätzung |a_n − a| < ε für alle n ≥ N(ε) und jedes ε.', 'feedback': ''},
                          {'value': 'nothing', 'label': 'Gar nichts – numerische Rechnungen sind für Grenzwerte wertlos.',
                           'feedback': 'Rechnungen liefern gute Kandidaten für a und N(ε) und decken Fehler auf; nur beweisen können sie die Aussage für alle n nicht.'},
                          {'value': 'bounded', 'label': 'Die Folge ist monoton, weil sie im Band bleibt.',
                           'feedback': 'Im Band zu bleiben sagt nichts über Monotonie: (−1)^n/n bleibt im Band und springt ständig.'}],
              'correct': 'evidence', 'explanation': 'Das Lab ist ein Mikroskop für die Definition, kein Beweisverfahren.'}
    # prediction: band shrinks to e1
    ratio = N1 / N0
    corr = 'same' if N1 == N0 else ('down' if N1 < N0 else 'small' if ratio < 3 else 'mid' if ratio <= 30 else 'big')
    label = {'same': 'N bleibt gleich', 'down': 'N wird kleiner', 'small': 'N wächst höchstens etwa auf das Dreifache',
             'mid': 'N wächst etwa auf das 3- bis 30-Fache', 'big': 'N wächst auf mehr als das 30-Fache'}[corr]
    predict = {'question': f'{lab}, Kandidat a = {_f(L)}. Was passiert mit N(ε), wenn ε von {e0s} auf {_eps(e1)} sinkt?',
               'options': [{'value': 'same', 'label': 'N bleibt gleich.'}, {'value': 'down', 'label': 'N wird kleiner.'},
                           {'value': 'small', 'label': 'N wächst, aber höchstens etwa auf das Dreifache.'},
                           {'value': 'mid', 'label': 'N wächst etwa auf das 3- bis 30-Fache.'},
                           {'value': 'big', 'label': 'N wächst auf mehr als das 30-Fache.'}],
               'correct': corr, 'change': [{'param': 'eps', 'to': _key(e1)}],
               'result_text': f'Zutreffend ist: {label}. Die genauen Werte von N(ε) bestimmen Sie gleich selbst (Simulation und Aufgaben).',
               'explanation': 'Wie stark N(ε) wächst, hängt davon ab, wie schnell |a_n − a| fällt: wie 1/n (Faktor ≈ 1/ε-Verhältnis), wie 1/√n (quadratisch mehr) oder geometrisch (nur wenige Indizes mehr).'}
    ex = []
    cand = [(float(v), first_index(ts, L, float(v))) for v in EPS_OPTIONS]
    cand = [(v, n) for v, n in cand if n is not None and n > N0]
    if cand:
        v, n = max(cand, key=lambda c: c[1])
        ex.append({'id': 'deep', 'title': 'So schmal wie möglich',
                   'prompt': f'Wählen Sie das ε aus der Liste, für das innerhalb des Horizonts noch ein N gefunden wird und N am größten ist.',
                   'hint': 'Verkleinern Sie ε schrittweise und beobachten Sie, ab wann kein N mehr gefunden wird.',
                   'success': f'ε = {_eps(v)} mit N = {n}. Für noch kleinere ε reicht der Horizont nicht – ein Grund mehr, warum Rechnen keinen Beweis ersetzt.',
                   'cond': [{'m': 'N', 'op': '==', 'v': n}, {'m': 'found', 'op': '==', 'v': 1}], 'witness': {'eps': _key(v)}})
    for vw in ('even', 'odd'):
        n = first_index(ts, L, e0, vw)
        if n is not None and n < N0 - 1:
            ex.append({'id': 'sub' + vw, 'title': 'Eine Teilfolge ist schneller im Band',
                       'prompt': f'Bei ε = {e0s}: Finden Sie eine Teilfolge (gerade oder ungerade Indizes), deren N(ε) kleiner ist als {N0}.',
                       'hint': 'Schalten Sie zwischen geraden und ungeraden Indizes um.',
                       'success': f'Die {"geraden" if vw == "even" else "ungeraden"} Glieder liegen schon ab n = {n} im Band. Konvergieren beide Teilfolgen gegen dasselbe a, konvergiert die Folge.',
                       'cond': [{'m': 'N', 'op': '<', 'v': N0}, {'m': 'found', 'op': '==', 'v': 1}, {'p': 'eps', 'op': '==', 'v': _key(e0)}],
                       'witness': {'view': vw}})
            break
    return {'predict': predict, 'tasks': [t0, t1, t2], 'explore': ex, 'choice': choice}


def _key(v):
    return next(x for x in EPS_OPTIONS if math.isclose(float(x), v))


def _distinct(expected, cands, tol):
    out, seen = [], [expected]
    for v, msg in cands:
        if v is None or not math.isfinite(v) or any(abs(v - w) <= 2 * tol for w in seen):
            continue
        out.append({'value': round(v, 6), 'message': msg}); seen.append(v)
    return out


def pedagogy(spec):
    s = spec['sequence']
    return {'explain_prompt': 'Erklären Sie, warum N(ε) sich so verändert hat, und was das über die Folge aussagt.',
            'explain_keys': [{'label': 'schmaleres Band → späterer Einstieg', 'terms': ['schmal', 'kleiner', 'später', 'band']},
                             {'label': 'Geschwindigkeit, mit der |a_n − a| fällt', 'terms': ['schnell', 'langsam', '1/n', 'geschwind', 'abstand']},
                             {'label': 'nur endlich viele Glieder geprüft', 'terms': ['endlich', 'horizont', 'beweis', 'numerisch']}],
            'explore': s.pop('_explore', []), 'choice': s.pop('_choice'),
            'takeaways': ['a_n → a heißt: Zu jedem ε > 0 gibt es ein N, ab dem alle Glieder im ε-Band um a liegen.',
                          'Wie schnell N(ε) wächst, beschreibt die Konvergenzgeschwindigkeit.',
                          'Endlich viele berechnete Glieder sind Evidenz, kein Beweis; der Beweis löst |a_n − a| < ε allgemein nach n auf.'],
            'summary_prompt': 'Fassen Sie in einem Satz zusammen, was N(ε) bedeutet und was das Lab davon zeigen kann.',
            'transfer_id': 'transfer'}


def check(spec):
    m = spec['model']; d = m['seq']
    ref = B.sequence_spec(spec['id'], spec['title'], spec['kc_ids'], [], {**d, 'eps': float(next(p for p in spec['params'] if p['id'] == 'eps')['default'])})
    strip = lambda ts: [{k: v for k, v in t.items() if k != 'transfer'} for t in ts]
    if strip(spec['sequence']['tasks']) != strip(ref['sequence']['tasks']) or spec['sequence']['predict']['correct'] != ref['sequence']['predict']['correct']:
        raise SeqError('Folgen-Lab: Aufgaben oder Vorhersage weichen vom Referenzmodell ab')
    for case in spec.get('tests') or []:
        if metrics(spec, case['params'])['N'] != case['N']:
            raise SeqError('Folgen-Lab: Testfall N(ε) stimmt nicht')


def static_svg(spec):
    d = model_data(spec); eps = float(next(p for p in spec['params'] if p['id'] == 'eps')['default'])
    K = min(60, d['horizon']); ts = terms(d, K); L = d['limit']
    W, H, l, r, t, b = 640, 300, 56, 14, 16, 38
    lo, hi = min(ts + [L - eps]), max(ts + [L + eps])
    if hi - lo < 1e-9:
        hi += 1; lo -= 1
    pad = (hi - lo) * 0.08; lo -= pad; hi += pad
    X = lambda n: l + (W - l - r) * (n - 1) / max(1, K - 1); Y = lambda v: t + (hi - v) / (hi - lo) * (H - t - b)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="Folgenglieder mit ε-Band">'
         f'<title>Folge {B.E(d["label"])}: Glieder a_1 bis a_{K}, ε-Band um a = {_f(L)}</title>',
         f'<rect x="{l}" y="{Y(L + eps):.1f}" width="{W - l - r}" height="{Y(L - eps) - Y(L + eps):.1f}" fill="#dcebf5" stroke="none"/>',
         f'<line x1="{l}" x2="{W - r}" y1="{Y(L):.1f}" y2="{Y(L):.1f}" stroke="#1f5f8b" stroke-dasharray="5 4"/>']
    for k in range(5):
        v = lo + (hi - lo) * k / 4
        s.append(f'<text x="{l - 6}" y="{Y(v) + 4:.1f}" text-anchor="end" font-size="11" fill="#5b6876">{_f(v, 2)}</text>')
    for n in range(1, K + 1, max(1, K // 6)):
        s.append(f'<text x="{X(n):.1f}" y="{H - b + 16}" text-anchor="middle" font-size="11" fill="#5b6876">{n}</text>')
    for n, v in enumerate(ts, 1):
        s.append(f'<circle cx="{X(n):.1f}" cy="{Y(v):.1f}" r="3" fill="#1f5f8b"/>')
    s.append(f'<text x="{l}" y="{H - 6}" font-size="11" fill="#5b6876">n → · Band: a ± ε mit ε = {_eps(eps)} · N(ε) bestimmen Sie im Lab selbst</text></svg>')
    return ''.join(s)
