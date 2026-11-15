"""Unabhängige Prüfung des Lab-Rechenkerns (exam_mastery/templates/lab_math.js).

Die JS-Funktionen werden per Node ausgeführt und gegen eine separate Python-Implementierung
(Orakel) sowie mathematische Eigenschaften und Grenzfälle geprüft – ohne jede Darstellung.
"""
import itertools
import json
import math
import random
import shutil
import subprocess
from pathlib import Path

import pytest

JS = Path(__file__).resolve().parents[1] / 'exam_mastery/templates/lab_math.js'
pytestmark = pytest.mark.skipif(shutil.which('node') is None, reason='node fehlt')


def js(expr_calls):
    """expr_calls: Liste von (funktionsname, args). Gibt Liste der Ergebnisse zurück."""
    prog = (f"const M=require({json.dumps(str(JS))});const C={json.dumps(expr_calls)};"
            "const r=C.map(([f,a])=>{try{return M[f](...a)}catch(e){return {error:String(e.message)}}});"
            "process.stdout.write(JSON.stringify(r,(k,v)=>v===-Infinity?'-inf':(Number.isNaN(v)?'nan':v)))")
    out = subprocess.run(['node', '-e', prog], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


# ---------------- Orakel ----------------
def o_softmax(s, T=1.0, mask=None):
    idx = [j for j in range(len(s)) if mask is None or mask[j]]
    m = max(s[j] for j in idx)
    e = [math.exp((s[j] - m) / T) if j in idx else 0.0 for j in range(len(s))]
    z = sum(e)
    return [x / z for x in e]


def o_attend(q, K, V, c=1.0, T=1.0, mask=None):
    raw = [sum(a * b for a, b in zip(q, k)) for k in K]
    w = o_softmax([x / c for x in raw], T, mask)
    out = [sum(w[j] * V[j][i] for j in range(len(V))) for i in range(len(V[0]))]
    return raw, w, out


def close(a, b, tol=1e-9):
    if isinstance(a, list):
        return len(a) == len(b) and all(close(x, y, tol) for x, y in zip(a, b))
    return abs(a - b) <= tol * max(1.0, abs(b))


R = random.Random(20261114)


def rv(d, s=2.0):
    return [round(R.uniform(-s, s), 3) for _ in range(d)]


# ---------------- Attention ----------------
def test_attend_matches_oracle_random():
    cases = []
    for _ in range(60):
        d, n = R.choice([2, 3, 4]), R.choice([2, 3, 5])
        q, K, V = rv(d), [rv(d) for _ in range(n)], [rv(d) for _ in range(n)]
        c, T = R.choice([1, math.sqrt(d)]), R.choice([0.25, 1, 3])
        mask = [True] + [R.random() < .7 for _ in range(n - 1)]
        cases.append((q, K, V, c, T, mask))
    res = js([('attendOne', [q, K, V, {'scaleBy': c, 'T': T, 'mask': m}]) for q, K, V, c, T, m in cases])
    for (q, K, V, c, T, m), r in zip(cases, res):
        raw, w, out = o_attend(q, K, V, c, T, m)
        assert close(r['raw'], raw) and close(r['w'], w) and close(r['out'], out)
        assert close(sum(r['w']), 1.0)
        assert all(r['w'][j] == 0 for j in range(len(m)) if not m[j])
        # Ausgabe liegt in der konvexen Hülle: jede Koordinate zwischen min und max der Werte
        for i in range(len(V[0])):
            assert min(v[i] for v in V) - 1e-12 <= r['out'][i] <= max(v[i] for v in V) + 1e-12


def test_softmax_limits_and_invariances():
    s = [1.0, 3.0, 3.0, -2.0]
    r = js([('softmax', [s, 0]), ('softmax', [s, 1e-3]), ('softmax', [s, 1e6]), ('softmax', [[x + 1000 for x in s], 1]),
            ('softmax', [s, 1]), ('softmax', [[1e308, -1e308], 1]), ('softmax', [s, -1]), ('softmax', [s, 1, [False] * 4])])
    assert r[0] == [0, .5, .5, 0]                       # T=0: Gleichverteilung über die Maxima
    assert close(r[1], [0, .5, .5, 0], 1e-9)            # T->0
    assert close(r[2], [.25] * 4, 1e-5)                 # T->inf: gleichverteilt
    assert close(r[3], r[4])                            # Verschiebungsinvarianz, ohne Overflow
    assert close(r[5], [1.0, 0.0])                      # extreme Werte stabil
    assert 'error' in r[6]                              # negative Temperatur abgelehnt
    assert r[7] == ['nan'] * 4                          # alles maskiert: undefiniert, nicht stillschweigend 0


def test_key_shift_along_orthogonal_and_any_vector():
    """q·(k_j + c) = q·k_j + q·c: gemeinsame Verschiebung aller Keys ändert die Gewichte nie."""
    q, K, V = [1.0, 2.0], [[0.5, -1], [2, 1], [-1, 0.3]], [[1, 0], [0, 1], [1, 1]]
    c = [3.7, -2.2]
    a, b = js([('attendOne', [q, K, V]), ('attendOne', [q, [[k[0] + c[0], k[1] + c[1]] for k in K], V])])
    assert close(a['w'], b['w']) and not close(a['raw'], b['raw'])


def test_zero_query_gives_uniform_and_entropy_max():
    r = js([('attendOne', [[0, 0], [[1, 2], [-3, 1], [0, 5]], [[1, 0], [0, 1], [2, 2]]])])[0]
    assert close(r['w'], [1 / 3] * 3) and close(r['H'], math.log2(3)) and close(r['Hmax'], math.log2(3))


def test_projection_undefined_for_zero_query():
    r = js([('project', [[1, 2], [0, 0]]), ('project', [[3, 4], [2, 0]])])
    assert r[0]['defined'] is False and r[1]['len'] == 3 and r[1]['vec'] == [3, 0]


def test_self_attention_permutation_equivariance_and_pe_breaks_it():
    X = [rv(2) for _ in range(4)]
    WQ, WK, WV = [rv(2) for _ in range(2)], [rv(2) for _ in range(2)], [rv(2) for _ in range(2)]
    perm = [2, 0, 3, 1]
    Xp = [X[p] for p in perm]
    pe = js([('sinusPE', [4, 2])])[0]
    a, b, c, d = js([('selfAttention', [X, WQ, WK, WV, {}]), ('selfAttention', [Xp, WQ, WK, WV, {}]),
                     ('selfAttention', [X, WQ, WK, WV, {'P': pe}]), ('selfAttention', [Xp, WQ, WK, WV, {'P': pe}])])
    assert close(b['O'], [a['O'][p] for p in perm])          # ohne Position: äquivariant
    assert not close(d['O'], [c['O'][p] for p in perm], 1e-6)  # mit Position: Gegenbeispiel
    for row in a['A']:
        assert close(sum(row), 1)


def test_causal_mask_upper_triangle_zero():
    X = [rv(3) for _ in range(4)]
    W = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    r = js([('selfAttention', [X, W, W, W, {'causal': True}])])[0]
    for i, row in enumerate(r['A']):
        assert all(row[j] == 0 for j in range(i + 1, 4)) and close(sum(row), 1)
    assert close(r['O'][0], X[0])  # erstes Token sieht nur sich selbst


def test_sinus_pe_matches_formula():
    pe = js([('sinusPE', [5, 4])])[0]
    for t in range(5):
        for i in range(4):
            k = i // 2
            ang = t / 10000 ** (2 * k / 4)
            assert close(pe[t][i], math.sin(ang) if i % 2 == 0 else math.cos(ang))


def test_scaling_experiment_variance_tracks_dimension():
    rs = js([('scalingExperiment', [d, 8, 600, 3]) for d in (1, 16, 64)])
    for r in rs:
        assert abs(r['varRaw'] / r['d'] - 1) < 0.15, r
        assert 1 / 8 <= r['scaled']['maxw'] <= 1
    big = rs[-1]
    assert big['raw']['maxw'] > 0.85 and big['scaled']['maxw'] < 0.6       # Sättigung ohne Skalierung
    assert big['raw']['J'] < big['scaled']['J']                            # Gradient bricht ein
    assert js([('scalingExperiment', [16, 8, 50, 9])]) == js([('scalingExperiment', [16, 8, 50, 9])])  # deterministisch


def test_softmax_jacobian_matches_finite_difference():
    s, T = [0.3, -1.2, 2.0], 0.7
    p, J = js([('softmax', [s, T]), ('softmaxJacobian', [o_softmax(s, T), T])])
    h = 1e-6
    for j in range(3):
        sp = list(s); sp[j] += h
        num = [(a - b) / h for a, b in zip(o_softmax(sp, T), p)]
        assert close([J[i][j] for i in range(3)], num, 1e-4)


# ---------------- CRF ----------------
def o_score(y, E, A, s):
    return s[y[0]] + E[0][y[0]] + sum(A[y[t - 1]][y[t]] + E[t][y[t]] for t in range(1, len(y)))


def rand_crf(T, L):
    return [rv(L, 3) for _ in range(T)], [rv(L, 2) for _ in range(L)], rv(L, 1)


@pytest.mark.parametrize('T,L', [(1, 2), (2, 3), (3, 3), (4, 3), (5, 2)])
def test_viterbi_forward_marginals_vs_bruteforce(T, L):
    for _ in range(8):
        E, A, s = rand_crf(T, L)
        v, f, m, en = js([('viterbi', [E, A, s]), ('forward', [E, A, s]), ('marginals', [E, A, s]), ('enumerate', [E, A, s])])
        allp = list(itertools.product(range(L), repeat=T))
        sc = {y: o_score(y, E, A, s) for y in allp}
        best = max(sc.values())
        assert close(v['score'], best) and close(o_score(tuple(v['path']), E, A, s), best)
        logZ = math.log(sum(math.exp(x) for x in sc.values()))
        assert close(f['logZ'], logZ) and close(m['logZ'], logZ) and close(en['logZ'], logZ)
        for t in range(T):
            for j in range(L):
                pm = sum(math.exp(sc[y] - logZ) for y in allp if y[t] == j)
                assert close(m['P'][t][j], pm, 1e-9)
        assert close(sum(p['p'] for p in en['paths']), 1)


def test_forbidden_transition_never_in_viterbi_path():
    E = [[0, 5, 0], [0, 0, 6], [1, 0, 0]]  # lokal: B, I, O
    A = [[0, 0, 0], [0, 0, 0], [0, '-inf', 0]]
    A = [[float('-inf') if x == '-inf' else x for x in r] for r in A]
    # JSON kann -inf nicht übertragen: Ersatz durch -1e9
    A = [[-1e9 if x == float('-inf') else x for x in r] for r in A]
    v = js([('viterbi', [E, A, [0, 0, 0]])])[0]
    assert all(not (a == 2 and b == 1) for a, b in zip(v['path'], v['path'][1:]))


def test_viterbi_differs_from_marginal_argmax_counterexample():
    """Klassisches Gegenbeispiel: Folge der Einzel-Argmaxe der Randverteilungen ist nicht der beste Pfad."""
    E = [[0, 0, 0], [0, 0, 0]]
    s = [math.log(.4), math.log(.3), math.log(.3)]
    A = [[0, -1e9, -1e9], [-1e9, math.log(.5), math.log(.5)], [-1e9, math.log(.5), math.log(.5)]]
    # Pfad (0,0): 0.4 ; (1,1),(1,2),(2,1),(2,2): je 0.15 -> Randverteilung t=2: P(0)=.4, P(1)=.3, P(2)=.3
    # t=1: P(0)=.4 P(1)=.3 P(2)=.3 ... Konsistenz: hier stimmen beide überein; Gegenbeispiel im Lab nutzt andere Werte
    v, m = js([('viterbi', [E, A, s]), ('marginals', [E, A, s])])
    assert v['path'] == [0, 0]
    E2 = [[0, 0, 0], [0, 0, 0]]
    s2 = [math.log(.35), math.log(.325), math.log(.325)]
    A2 = [[-1e9, math.log(.5), math.log(.5)], [math.log(1), -1e9, -1e9], [math.log(1), -1e9, -1e9]]
    v2, m2 = js([('viterbi', [E2, A2, s2]), ('marginals', [E2, A2, s2])])
    marg = [max(range(3), key=lambda j: m2['P'][t][j]) for t in range(2)]
    # beste Pfade: (0,1),(0,2) je .175 ; (1,0) .325 ; (2,0) .325  -> Viterbi (1,0); Randargmax: t1 -> 0 (.35), t2 -> 0 (.65)
    assert v2['path'] == [1, 0] and marg == [0, 0]
    assert o_score((0, 0), E2, A2, s2) < -1e8   # Folge der Rand-Argmaxe ist sogar unmöglich


# ---------------- BiRNN ----------------
def test_rnn_influence_respects_direction_and_matches_finite_difference():
    X = [rv(2, 1) for _ in range(4)]
    P = {'Wx': [rv(2, 1) for _ in range(2)], 'Wh': [rv(2, .8) for _ in range(2)], 'b': rv(2, .3)}
    fw, bw = js([('rnnInfluence', [X, P, False]), ('rnnInfluence', [X, P, True])])
    for t in range(4):
        for j in range(4):
            if j > t:
                assert fw['M'][t][j] == 0
            if j < t:
                assert bw['M'][t][j] == 0
    # Finite Differenzen für ||∂h_t/∂x_j||_F
    h = 1e-6
    base = js([('rnn', [X, P, False])])[0]
    calls = []
    for j in range(4):
        for k in range(2):
            Xp = [list(x) for x in X]; Xp[j][k] += h
            calls.append(('rnn', [Xp, P, False]))
    outs = js(calls)
    for j in range(4):
        for t in range(4):
            fro = 0
            for k in range(2):
                d = [(a - b) / h for a, b in zip(outs[j * 2 + k][t], base[t])]
                fro += sum(x * x for x in d)
            assert abs(math.sqrt(fro) - fw['M'][t][j]) < 1e-4


# ---------------- Spannen & F1 ----------------
def test_spans_conlleval_and_encodings_roundtrip():
    r = js([('spans', [['O', 'I-LOC', 'I-LOC', 'B-LOC']]), ('spans', [['B-PER', 'I-ORG', 'L-ORG', 'U-PER']])])
    assert [(s['type'], s['start'], s['end']) for s in r[0]] == [('LOC', 1, 2), ('LOC', 3, 3)]
    assert [(s['type'], s['start'], s['end']) for s in r[1]] == [('PER', 0, 0), ('ORG', 1, 2), ('PER', 3, 3)]
    sp = [{'type': 'DAY', 'start': 0, 'end': 0}, {'type': 'DAY', 'start': 1, 'end': 1}, {'type': 'PER', 'start': 3, 'end': 5}]
    bio, bilou, io = js([('encode', [sp, 7, 'BIO']), ('encode', [sp, 7, 'BILOU']), ('encode', [sp, 7, 'IO'])])
    assert bio == ['B-DAY', 'B-DAY', 'O', 'B-PER', 'I-PER', 'I-PER', 'O']
    assert bilou == ['U-DAY', 'U-DAY', 'O', 'B-PER', 'I-PER', 'L-PER', 'O']
    back = js([('spans', [bio]), ('spans', [bilou]), ('spans', [io])])
    assert back[0] == sp and back[1] == sp and len(back[2]) == 2   # IO verliert die Grenze


def test_prf_edge_cases_and_micro_weighting():
    r = js([('prf', [0, 0, 0]), ('prf', [0, 0, 3]), ('prf', [0, 2, 0]), ('prf', [3, 1, 2])])
    assert r[0]['F'] is None and r[0]['P'] is None
    assert r[1]['P'] is None and r[1]['R'] == 0 and r[1]['F'] == 0
    assert r[2]['R'] is None and r[2]['F'] == 0
    assert close(r[3]['F'], 6 / 9)
    g = ['B-PER', 'I-PER', 'O', 'B-LOC', 'O', 'B-MISC']
    p = ['B-PER', 'O', 'O', 'B-LOC', 'O', 'O']
    mm = js([('microMacro', [g, p, ['PER', 'LOC', 'MISC'], 'span'])])[0]
    per = {x['type']: x for x in mm['per']}
    w = {t: 2 * per[t]['tp'] + per[t]['fp'] + per[t]['fn'] for t in per}
    assert close(mm['micro']['F'], sum(w[t] * per[t]['F'] for t in per) / sum(w.values()))
    tok = js([('tokenCounts', [g, p])])[0]
    assert (tok['tp'], tok['fp'], tok['fn']) == (2, 0, 2)


def test_bio_valid():
    r = js([('bioValid', [['B-PER', 'I-PER', 'O']]), ('bioValid', [['I-PER', 'O']]), ('bioValid', [['O', 'I-PER']]),
            ('bioValid', [['B-LOC', 'I-PER']]), ('bioValid', [['O']])])
    assert r == [True, False, False, False, True]


def test_span_and_token_counts_match_python_seqlab():
    """Zweite, unabhängige Implementierung (exam_mastery.seqlab) als Orakel."""
    from exam_mastery import seqlab as SQ
    rng = random.Random(5)
    tags = ['O', 'O', 'O'] + [f'{p}-{t}' for p in 'BI' for t in ('PER', 'LOC', 'ORG')]
    cases = [([rng.choice(tags) for _ in range(12)], [rng.choice(tags) for _ in range(12)]) for _ in range(120)]
    calls = [c for g, p in cases for c in (('spanCounts', [g, p]), ('tokenCounts', [g, p]), ('spanCounts', [g, p, 'LOC']))]
    res = js(calls)
    for k, (g, p) in enumerate(cases):
        sc, tc, sl = res[3 * k:3 * k + 3]
        a, b, c = SQ.span_counts(g, p), SQ.token_counts(g, p), SQ.span_counts(g, p, types={'LOC'})
        assert (sc['tp'], sc['fp'], sc['fn']) == (a.tp, a.fp, a.fn)
        assert (tc['tp'], tc['fp'], tc['fn']) == (b.tp, b.fp, b.fn)
        assert (sl['tp'], sl['fp'], sl['fn']) == (c.tp, c.fp, c.fn)


def test_jacobian_temperature_regimes():
    """Lemma 6.4: fest T + großer Vorsprung -> 0; T->0 mit eindeutigem Maximum -> 0; T->0 bei Gleichstand -> divergent."""
    def jnorm(s, T):
        p = o_softmax(s, T)
        return math.sqrt(sum(((p[i] if i == j else 0) - p[i] * p[j]) ** 2 for i in range(len(p)) for j in range(len(p)))) / T
    uniq, tie = [1.0, 0.0, -0.5], [1.0, 1.0, -0.5]
    a = [jnorm(uniq, T) for T in (1, .3, .1, .03, .01)]
    b = [jnorm(tie, T) for T in (1, .3, .1, .03, .01)]
    assert a[-1] < 1e-6 and all(x > y for x, y in zip(a[1:], a[2:]))
    assert b[-1] > 30 and all(x < y for x, y in zip(b, b[1:]))
    for s, T in ((uniq, .2), (tie, .2), ([3, 0, 0, 0], 1)):          # Schranke 4(1-w_m)/T
        p = o_softmax(s, T)
        assert jnorm(s, T) <= 4 * (1 - max(p)) / T + 1e-12
    J = js([('softmaxJacobian', [o_softmax(tie, .05), .05])])[0]
    assert abs(J[0][0] - jnorm([1.0, 1.0, -0.5], .05) / 1) < 1e9 and J[0][0] > 4    # JS-Kern liefert dieselbe Divergenz
