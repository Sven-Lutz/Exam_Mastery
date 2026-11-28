"""Deepened attention unit (V1CONTENT): every new number and derivation is recomputed on an independent route.

Checks certify arithmetic, symbolic identities and publication identity. They do not replace the pending human
subject review ("Fachprüfung erforderlich"); no quality score is assigned here.
"""
import copy
import json
import math
from itertools import product
from pathlib import Path

import numpy as np
import pytest

from exam_mastery.learning import diagnose as D
from exam_mastery.learning import experience as ex

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'fixtures/experience_attention_reference.json'

ORIGINAL = {
    'teaching': ['teach/motivation', 'teach/shapes', 'teach/softmax', 'teach/stability', 'teach/gradient', 'teach/scaling',
                 'teach/counterexample', 'teach/worked', 'teach/convex', 'teach/mask', 'teach/experiment'],
    'assessments': ['task/dimensions', 'task/guided-numeric', 'task/fresh-numeric', 'task/shift-proof', 'task/jacobian', 'task/variance',
                    'task/correlated-transfer', 'task/mask-debug', 'task/permutation', 'task/inverse'],
    'mathematics': ['att.shapes', 'att.score', 'att.operator', 'att.softmax', 'att.shift', 'att.jacobian', 'att.variance', 'att.output', 'att.logratio'],
    'competencies': ['attention/shapes', 'attention/softmax', 'attention/scaling', 'attention/aggregation', 'attention/masking', 'attention/transfer'],
    'claims': ['claim/operator', 'claim/stability', 'claim/scaling', 'claim/geometry', 'claim/mask'],
}
ORIGINAL_CARDS = ['attention/shape-score', 'attention/shape-value', 'attention/softmax-axis', 'attention/shift', 'attention/overflow', 'attention/jacobian',
                  'attention/variance-premise', 'attention/sqrt', 'attention/correlation', 'attention/value-change', 'attention/convex', 'attention/mask-empty',
                  'attention/mask-one', 'attention/cosine', 'attention/permutation', 'attention/nonidentifiability']


def unit():
    return json.loads(FIXTURE.read_text(encoding='utf-8'))


U = unit()
TASK = {t['id']: t for t in U['assessments']}
TEACH = {t['id']: t for t in U['teaching']}
NEW_TEACH = [t for t in TEACH if t not in ORIGINAL['teaching']]
NEW_TASKS = [t for t in TASK if t not in ORIGINAL['assessments']]


def de(x, d=6):
    s = f'{float(x):.{d}f}'
    if float(s) == 0:
        s = s.lstrip('-')
    return s.replace('-', '−').replace('.', ',')


def softmax_rows(Z, mask=None):
    Z = np.asarray(Z, float)
    if mask is not None:
        Z = np.where(mask, Z, -np.inf)
    E = np.exp(Z - Z.max(axis=-1, keepdims=True))
    return E / E.sum(axis=-1, keepdims=True)


def attention(Q, K, V, mask=None):
    return softmax_rows(Q @ K.T / math.sqrt(Q.shape[1]), mask) @ V


REF = dict(Q=np.array([[1, 0], [0, 1.]]), K=np.array([[1, 0], [0, 1], [-1, 0.]]), V=np.array([[2, 0], [0, 2], [2, 2.]]))


# ------------------------------------------------------------------ structure and identity

def test_unit_valid_and_original_ids_kept():
    r = ex.validate(U)
    assert r['valid'], r['errors']
    assert U['unit_id'] == 'math/scaled-attention-golden-reference'
    for section, ids in ORIGINAL.items():
        have = [x['id'] for x in U[section]]
        assert [i for i in have if i in ids] == ids, section          # all kept, original order preserved
    assert [c['key'] for c in U['cards']][:16] == ORIGINAL_CARDS
    assert U['authorship']['human_status'] == 'NOT_APPROVED'
    assert U['authorship']['historical_status'] == 'HUMAN_REJECTED remains unchanged'


def test_new_claims_are_not_self_verified_and_cite_real_sections():
    old = set(ORIGINAL['claims'])
    for c in U['claims']:
        if c['id'] not in old:
            assert c['evidence_status'] == 'unverified', c['id']
    loc = next(s for s in U['sources'] if s['id'] == 'paper/vaswani-2017')['locator']
    for section in ('§3.2.1', '§3.2.2', '§3.2.3', '§3.5', 'Tabelle 1', 'Fußnote 4'):
        assert section in loc


def test_new_teaching_has_worked_example_or_derivation_and_new_competencies_are_practised():
    assert set(NEW_TEACH) == {'teach/variance-limits', 'teach/backprop', 'teach/mask-numerics', 'teach/equivariance', 'teach/multihead', 'teach/complexity'}
    for tid in NEW_TEACH:
        t = TEACH[tid]
        assert t.get('derivation') or 'beispiel' in t['content'].lower(), tid
    for comp in ('attention/backprop', 'attention/multihead'):
        assert any(comp in TASK[t]['competency_ids'] for t in NEW_TASKS)
        assert any(comp in c['competency_ids'] for c in U['cards'])
    flawed = [t for t in NEW_TASKS if t.startswith('task/flawed-')]
    assert len(flawed) == 3 and all(TASK[t]['prompt'].startswith(('Prüfen Sie', 'Ein Review')) for t in flawed)


def test_new_cards_ask_for_principles_not_definitions():
    for c in U['cards'][16:]:
        assert c['kind'] in ('math', 'mechanism', 'condition', 'compare', 'misconception'), c['key']
        assert c['front'].startswith(('Wie', 'Warum', 'Was', 'Wann', 'Welche', 'Zwischen', 'Durch', 'Ab')), c['key']


# ------------------------------------------------------------------ backpropagation through attention

def _grads(Q, K, V, G, mask=None):
    d = Q.shape[1]; A = softmax_rows(Q @ K.T / math.sqrt(d), mask)
    gA = G @ V.T; gZ = A * (gA - (A * gA).sum(1, keepdims=True))
    return gZ, gZ @ K / math.sqrt(d), gZ.T @ Q / math.sqrt(d), A.T @ G


@pytest.mark.parametrize('seed', range(6))
def test_backprop_formulas_against_finite_differences(seed):
    rng = np.random.default_rng(seed)
    m, n, d, p = rng.integers(1, 4, size=4) + 1
    Q, K, V, G = rng.normal(size=(m, d)), rng.normal(size=(n, d)), rng.normal(size=(n, p)), rng.normal(size=(m, p))
    mask = rng.random((m, n)) < 0.7; mask[:, 0] = True
    L = lambda Q_, K_, V_: float((attention(Q_, K_, V_, mask) * G).sum())
    _, gQ, gK, gV = _grads(Q, K, V, G, mask)
    for X, g, f in ((Q, gQ, lambda X_: L(X_, K, V)), (K, gK, lambda X_: L(Q, X_, V)), (V, gV, lambda X_: L(Q, K, X_))):
        fd = np.zeros_like(X)
        for idx in np.ndindex(X.shape):
            E = np.zeros_like(X); E[idx] = 1e-6
            fd[idx] = (f(X + E) - f(X - E)) / 2e-6
        assert np.allclose(fd, g, atol=1e-7)


def test_backprop_score_gradient_exact_sympy():
    import sympy as sp
    z = sp.symbols('z1:4', real=True); g = sp.symbols('g1:4', real=True)
    den = sum(sp.exp(x) for x in z); a = [sp.exp(x) / den for x in z]
    L = sum(gi * ai for gi, ai in zip(g, a))
    for ell in range(3):
        formula = a[ell] * (g[ell] - sum(aj * gj for aj, gj in zip(a, g)))
        assert sp.simplify(sp.diff(L, z[ell]) - formula) == 0
    # dL/dQ = dL/dZ K / sqrt(d) for one query, two keys, d = 2, symbolic entries
    q = sp.symbols('q1:3', real=True); k = sp.Matrix(2, 2, sp.symbols('k1:5', real=True)); v = sp.symbols('v1:3', real=True)
    zz = [sum(q[r] * k[j, r] for r in range(2)) / sp.sqrt(2) for j in range(2)]
    den = sum(sp.exp(x) for x in zz); aa = [sp.exp(x) / den for x in zz]
    O = sum(aj * vj for aj, vj in zip(aa, v))                        # L = O (G = 1, p = 1)
    gZ = [aa[j] * (v[j] - O) for j in range(2)]                      # g_j = v_j, <a, g> = O
    for r in range(2):
        formula = sum(gZ[j] * k[j, r] for j in range(2)) / sp.sqrt(2)
        pt = {s: sp.Rational(c, 7) for s, c in zip(list(q) + list(k) + list(v), (3, -5, 2, 9, -4, 1, 6, -8))}
        assert abs(sp.N((sp.diff(O, q[r]) - formula).subs(pt), 30)) < sp.Float('1e-25')


def test_backprop_worked_example_and_problem_numbers():
    gZ1, gQ1, _, _ = _grads(REF['Q'], REF['K'], REF['V'], np.array([[1, 0], [0, 0.]]))
    text = TEACH['teach/backprop']['content']
    for x in list(gZ1[0]) + list(gQ1[0]):
        assert de(x) in text
    assert abs(gZ1[0].sum()) < 1e-15 and not gQ1[1].any()
    gZ2, gQ2, _, gV2 = _grads(REF['Q'], REF['K'], REF['V'], np.array([[0, 1], [0, 0.]]))
    sol = TASK['task/backprop-numeric']['solution']
    for x in list(gZ2[0]) + list(gQ2[0]) + list(gV2[:, 1]):
        assert de(x) in sol
    a = softmax_rows(REF['Q'] @ REF['K'].T / math.sqrt(2))[0]
    chk = TASK['task/backprop-numeric']['machine_check']
    assert chk['expected'] == pytest.approx(gZ2[0][2], abs=1e-6)
    wrong = {e['category']: e['value'] for e in chk['errors']}
    assert wrong['attention/softmax-normaliser-ignored'] == pytest.approx(a[2] * 2, abs=1e-6)
    assert wrong['attention/softmax-diagonal-only'] == pytest.approx(a[2] * (1 - a[2]) * 2, abs=1e-6)


def test_flawed_jacobian_counterexample():
    h = 1e-6
    fd = (1 / (1 + math.exp(h)) - 1 / (1 + math.exp(-h))) / (2 * h)
    assert fd == pytest.approx(-0.25, abs=1e-9)
    rng = np.random.default_rng(3)
    for _ in range(5):
        a = softmax_rows(rng.normal(size=4))
        J = np.diag(a) - np.outer(a, a)
        assert np.allclose(J.sum(1), 0) and (np.diag(a * (1 - a)).sum(1) > 0).all()


# ------------------------------------------------------------------ variance limits

def test_variance_general_bounds_and_flawed_derivation_counterexample():
    # d = 2: q = (q1, -q1), k = (k1, k1) with fair signs -> q.k = 0 always, components centred, variance one
    vals = [q1 * k1 + (-q1) * k1 for q1, k1 in product([-1, 1], repeat=2)]
    assert vals == [0, 0, 0, 0]
    for comp in ([q1 for q1, _ in product([-1, 1], repeat=2)], [-q1 for q1, _ in product([-1, 1], repeat=2)]):
        assert sum(comp) == 0 and sum(x * x for x in comp) / len(comp) == 1
    # upper bound d^2 is attained by identical products; d by independent signs (exact enumeration, d = 3)
    d = 3
    same = [d * x * y for x, y in product([-1, 1], repeat=2)]
    assert sum(s * s for s in same) / 4 == d * d
    indep = [sum(a * b for a, b in zip(q, k)) for q in product([-1, 1], repeat=d) for k in product([-1, 1], repeat=d)]
    assert sum(s * s for s in indep) / len(indep) == d


def test_conditional_row_variance_and_shared_key_mean():
    q, sigma = np.array([2.0, -1.0, 0.5]), 1.5
    # keys with independent symmetric components +-sigma: exact enumeration of Var(q.k | q)
    scores = [float(q @ (sigma * np.array(s))) for s in product([-1, 1], repeat=3)]
    assert np.mean(np.square(scores)) - np.mean(scores) ** 2 == pytest.approx(sigma ** 2 * float(q @ q))
    rng = np.random.default_rng(1); U_ = rng.normal(size=(5, 3)); mu = np.array([3.0, -2.0, 7.0])
    assert np.allclose(softmax_rows(q @ (U_ + mu).T), softmax_rows(q @ U_.T))


# ------------------------------------------------------------------ masking numerics

def test_mask_padding_task_and_misconception_values():
    Z = np.array([[0, 1, 2], [1, 0, 1], [2, 1, 0.]]); v = np.array([10, 1, 3.])
    M = np.tril(np.ones((3, 3), bool)) & np.array([False, True, True])
    assert not M[0].any() and M[1].tolist() == [False, True, False] and M[2].tolist() == [False, True, True]
    A = softmax_rows(Z[1:], M[1:])
    o3 = float(A[1] @ v)
    causal = softmax_rows(Z[2]); after = np.where(M[2], causal, 0)
    chk = TASK['task/mask-padding']['machine_check']
    assert chk['expected'] == pytest.approx(o3, abs=1e-6)
    wrong = {e['category']: e['value'] for e in chk['errors']}
    assert wrong['attention/padding-mask-ignored'] == pytest.approx(float(causal @ v), abs=1e-6)
    assert wrong['attention/mask-after-softmax'] == pytest.approx(float(after @ v), abs=1e-6)
    sol = TASK['task/mask-padding']['solution']
    for x in (A[1][1], A[1][2], o3, causal @ v, after @ v):
        assert de(x) in sol
    # right-padding example in the teaching text
    t3 = softmax_rows([0, 1, 5.], [True, True, False])
    assert de(t3[0]) in TEACH['teach/mask-numerics']['content'] and de(t3[1]) in TEACH['teach/mask-numerics']['content']


def test_ieee_claims_about_masks():
    with np.errstate(invalid='ignore'):
        row = np.full(3, -np.inf)
        assert np.isnan(np.exp(row - row.max())).all()                  # empty row with -inf -> NaN
        assert math.isnan(float('nan') * 0.0)                             # NaN * 0 = NaN
        e = np.exp(np.array([0, 0, 1000.]) - 1000.0); e[2] = 0           # mask after softmax, renormalise
        assert e.sum() == 0.0 and np.isnan(e / e.sum()).all()
    row = np.full(3, -1e9)
    assert np.allclose(np.exp(row - row.max()) / 3, 1 / 3)              # finite substitute -> silently uniform
    with np.errstate(over='ignore'):
        assert np.isneginf(np.float16(-1e9)) and float(np.finfo(np.float16).max) == 65504
    z = np.array([0.3, -1.2, 2.0, 0.4]); allowed = np.array([True, False, True, True])
    full = softmax_rows(z); renorm = np.where(allowed, full, 0) / np.where(allowed, full, 0).sum()
    assert np.allclose(renorm, softmax_rows(z, allowed))               # algebraic equivalence in the flawed-mask task


# ------------------------------------------------------------------ permutation equivariance

def test_equivariance_and_causal_counterexample():
    rng = np.random.default_rng(5)
    X = rng.normal(size=(5, 4)); Wq, Wk, Wv = rng.normal(size=(3, 4, 3))
    f = lambda X_, mask=None: attention(X_ @ Wq, X_ @ Wk, X_ @ Wv, mask)
    P = np.eye(5)[[3, 0, 4, 1, 2]]
    assert np.allclose(f(P @ X), P @ f(X))
    S = rng.normal(size=(5, 5))
    assert np.allclose(softmax_rows(P @ S @ P.T), P @ softmax_rows(S) @ P.T)
    C = np.tril(np.ones((5, 5), bool))
    assert np.allclose(f(P @ X, P @ C @ P.T > 0), P @ f(X, C))           # mask permuted along: equivariant
    assert not np.allclose(f(P @ X, C), P @ f(X, C))                    # fixed causal mask: not equivariant
    one = lambda x, causal=False: attention(np.c_[x], np.c_[x], np.c_[x], np.tril(np.ones((2, 2), bool)) if causal else None)[:, 0]
    sol = TASK['task/equivariance-proof']['solution']
    assert one([2, 0], True).tolist() == [2, 1]
    assert de(one([0, 2], True)[1]) in sol and de(one([2, 0])[0]) in sol
    assert np.allclose(one([0, 2]), one([2, 0])[::-1]) and not np.allclose(one([0, 2]), one([2, 0]))


# ------------------------------------------------------------------ multi-head and cost

def test_multihead_concat_equals_sum_and_parameter_count():
    rng = np.random.default_rng(9); n, dm, h = 6, 8, 4; dk = dm // h
    X = rng.normal(size=(n, dm)); W = rng.normal(size=(h, 3, dm, dk)); WO = rng.normal(size=(h * dk, dm))
    heads = [attention(X @ W[i, 0], X @ W[i, 1], X @ W[i, 2]) for i in range(h)]
    assert np.allclose(np.hstack(heads) @ WO, sum(heads[i] @ WO[i * dk:(i + 1) * dk] for i in range(h)))
    for dm_, h_ in ((512, 8), (512, 16), (768, 12)):
        dk_ = dm_ // h_
        assert 3 * h_ * dm_ * dk_ + h_ * dk_ * dm_ == 4 * dm_ ** 2
    assert TASK['task/multihead-dims']['machine_check']['expected'] == 4 * 512 ** 2 == 1048576
    assert '1 048 576' in TEACH['teach/multihead']['content'] and '786 432' in TASK['task/multihead-dims']['solution']


def test_complexity_numbers():
    text, sol = TEACH['teach/complexity']['content'], TASK['task/complexity']['solution']
    assert '134 217 728' in text and 8 * 4096 ** 2 == 134217728 and round(134217728 * 2 / 1e6) == 268 and '268 MB' in text
    assert '201 326 592' in sol and 12 * 4096 ** 2 == 201326592 and '805 306 368' in sol and round(201326592 * 4 / 1e6) == 805
    assert TASK['task/complexity']['machine_check']['expected'] == 2 * 768
    n, d = 1536, 768
    assert 2 * n ** 2 * d == 4 * n * d ** 2                              # crossover n = 2d exactly
    assert (4096 / 1024) ** 2 == 16


# ------------------------------------------------------------------ deterministic misconception wiring

def test_machine_checks_diagnose_their_categories():
    for t in U['assessments']:
        chk = t.get('machine_check')
        if not chk:
            continue
        task = {**chk, 'id': t['id'], 'kc_id': t['competency_ids'][0]}
        assert D.diagnose(task, repr(chk['expected']))['result'] == 'correct', t['id']
        for e in chk.get('errors', []):
            assert D.diagnose(task, repr(e['value']))['error_category'] == e['category'], (t['id'], e)
    ids = {m['id'] for m in U['misconceptions']}
    assert ids == {'attention/softmax-normaliser-ignored', 'attention/softmax-diagonal-only', 'attention/mask-after-softmax', 'attention/padding-mask-ignored'}


# ------------------------------------------------------------------ publication: gates, books, Anki identity

def test_anki_identities_survive_deepening_and_reimport(tmp_path):
    pytest.importorskip('anki')
    from anki.collection import Collection, ImportAnkiPackageRequest, ImportAnkiPackageOptions
    from exam_mastery.learning import experience_anki as bridge
    old = copy.deepcopy(U); old['cards'] = [c for c in old['cards'] if c['key'] in ORIGINAL_CARDS]
    out = tmp_path / 'products'
    first = bridge.publish(old, out)
    col = Collection(str(tmp_path / 'isolated.anki2'))

    def load():
        col.import_anki_package(ImportAnkiPackageRequest(package_path=str(out / 'Anki.apkg'), options=ImportAnkiPackageOptions(
            merge_notetypes=True, update_notes=1, with_scheduling=False, with_deck_configs=False)))
    try:
        load()
        before = {col.get_note(nid)['Key']: (nid, col.get_note(nid).guid) for nid in col.find_notes('')}
        assert set(before) == set(ORIGINAL_CARDS) and first['notes'] == 16
        second = bridge.publish(U, out)
        assert sorted(second['update_delta']['new']) == sorted(c['key'] for c in U['cards'][16:])
        assert not second['update_delta']['automatic_deletion']
        load()
        after = {col.get_note(nid)['Key']: (nid, col.get_note(nid).guid) for nid in col.find_notes('')}
        assert len(after) == len(U['cards'])
        for key, ident in before.items():
            assert after[key] == ident, key                                # same note id and GUID
        third = bridge.publish(U, out)
        assert third['status'] == 'UNCHANGED'
    finally:
        col.close()


def test_full_four_product_build_and_unchanged_rebuild(tmp_path):
    from exam_mastery.learning.experience_pipeline import build
    import pymupdf
    first = build(U, tmp_path)
    assert first['academic_status'] == 'HUMAN_REVIEW_PENDING' and first['model_calls'] == 0
    products = [tmp_path / p for p in first['products'].values()]
    mtimes = [p.stat().st_mtime_ns for p in products]
    second = build(U, tmp_path)
    assert second['publication']['status'] == 'UNCHANGED'
    assert mtimes == [p.stat().st_mtime_ns for p in products]
    with pymupdf.open(tmp_path / 'Lehrbuch.pdf') as pdf:
        text = ''.join(page.get_text() for page in pdf)
    for title in ('Gradienten durch den ganzen Attention-Kopf', 'Kausale Maske, Padding', 'Permutationen: was Self-Attention',
                  'Mehrere Köpfe: Teilräume', 'Was quadratische Kosten', 'Was die Varianzrechnung'):
        assert title in text.replace('\n', ' ').replace('‐ ', '').replace('-\n', ''), title
    assert 'FACHLICH NICHT UNABHÄNGIG GEPRÜFT' in text
    with pymupdf.open(tmp_path / 'Arbeitsbuch.pdf') as pdf:
        work = ''.join(page.get_text() for page in pdf)
    assert 'Prüfen Sie diese Herleitung' in work.replace('\n', ' ')
