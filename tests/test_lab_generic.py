"""v0.18 generic labs: sequence (ε-N), self-attention, cap table, legal case-check scheme.

Python reference models (hand examples, NumPy recomputation, invalid inputs), specs and learning sequences, catalogue
integration, static figures without solution leakage, and in a real browser: JS mirror == Python on random inputs,
results hidden until the learner's own attempt, missions reachable at their witnesses, no horizontal overflow on phones.
"""
import json
import math
import random

import pytest

from exam_mastery.labs import build as B, pedagogy as P
from exam_mastery.labs import sequence as SQ, attention as AT, cap_table as CT, legal_check as LC
from exam_mastery.labs.integrate import catalog_requests, build_chapter_labs

np = pytest.importorskip('numpy')


def specs():
    return {k: getattr(B, k + '_spec')('t/' + k.replace('_', '-'), k, ['kc'], ['Folie 1'], {}, 'Kurs') for k in B.GENERIC}


# ------------------------------------------------------------------ sequence

def test_sequence_parser_and_hand_values():
    assert SQ.terms({'expr': 'n/(n+1)'}, 3) == [0.5, 2 / 3, 0.75]
    assert SQ.terms({'expr': '(-1)^n/n'}, 4) == [-1.0, 0.5, -1 / 3, 0.25]
    assert SQ.terms({'expr': '-2^2+abs(-3)*sqrt(4)'}, 1) == [2.0]          # unary minus binds weaker than ^
    assert SQ.terms({'expr': '2^-1'}, 1) == [0.5]
    r = SQ.terms({'rec': 'sqrt(2+a)', 'a1': 1}, 60)
    assert abs(r[-1] - 2) < 1e-12 and all(x <= y for x, y in zip(r, r[1:]))
    ts = SQ.terms({'expr': 'n/(n+1)'}, 200)
    assert SQ.first_index(ts, 1, 0.1) == 10                                   # |a_9 - 1| = 0.1 exactly (float 0.0999…): outside
    assert SQ.first_index(SQ.terms({'expr': '(-1)^n/n'}, 200), 0, 0.1) == 11
    assert SQ.first_index(SQ.terms({'expr': '(-1)^n'}, 200), 1, 0.1) is None
    assert SQ.first_index(SQ.terms({'expr': '(-1)^n'}, 200), 1, 0.1, 'even') == 2   # even subsequence is constant 1
    assert SQ.summary(ts)['mono'] == 'inc'


@pytest.mark.parametrize('bad', ['', '2n', 'n**2', '__import__("os")', 'exp(n)', 'a+n', '(n', 'sqrt(-n)', '(-2)^(1/n)', '1/(n-1)', 'n;1', 'x' * 200])
def test_sequence_rejects_unsafe_or_invalid(bad):
    with pytest.raises(B.LabError):
        SQ.terms({'expr': bad}, 5)


# ------------------------------------------------------------------ attention

def test_attention_against_numpy():
    rnd = random.Random(2)
    for _ in range(30):
        n, d, dk = rnd.randint(2, 6), rnd.randint(1, 6), rnd.randint(1, 4)
        X = [[rnd.randint(-3, 3) for _ in range(d)] for _ in range(n)]
        h = {k: [[rnd.randint(-2, 2) for _ in range(dk)] for _ in range(d)] for k in ('Wq', 'Wk', 'Wv')}
        for causal in (False, True):
            r = AT.head(X, h, causal)
            Xn = np.array(X, float); Q, K, V = (Xn @ np.array(h[k], float) for k in ('Wq', 'Wk', 'Wv'))
            S = Q @ K.T / math.sqrt(dk)
            if causal:
                S = np.where(np.tril(np.ones((n, n))) > 0, S, -np.inf)
            A = np.exp(S - S.max(1, keepdims=True)); A /= A.sum(1, keepdims=True)
            assert np.allclose(r['A'], A, atol=1e-12) and np.allclose(r['O'], A @ V, atol=1e-12)
            assert all(abs(sum(row) - 1) < 1e-12 for row in r['A'])


def test_attention_invalid():
    for bad in ({'tokens': ['a'], 'X': [[1]], 'heads': [{'Wq': [[1]], 'Wk': [[1]], 'Wv': [[1]]}]},
                {**AT.DEFAULT, 'X': AT.DEFAULT['X'][:3]}, {**AT.DEFAULT, 'heads': AT.DEFAULT['heads'] * 2},
                {**AT.DEFAULT, 'heads': [{**AT.DEFAULT['heads'][0], 'Wk': [[1]] * 4}]}):
        with pytest.raises(B.LabError):
            B.attention_spec('t/a', 'A', ['k'], [], bad)


# ------------------------------------------------------------------ cap table

def test_cap_table_hand_example():
    d = CT.check_data(CT.DEFAULT); R = CT.rounds(d)
    # seed: pool 10 % of post, pre-money: P = .1*1e6*1.25/(1-.125) = 142857; price = 4e6/1142857 = 3.5; I = 285714
    assert (R[1]['new_pool'], R[1]['inv_shares']) == (142857, 285714) and abs(R[1]['price'] - 3.5) < 1e-6
    assert abs(R[1]['founders_pct'] - 0.7) < 1e-6 and abs(R[2]['founders_pct'] - 0.49) < 1e-6
    post = CT.rounds(d, 'post')
    assert post[2]['founders_pct'] > R[2]['founders_pct']                     # a post-money pool also dilutes the investor
    last = R[-1]
    w = CT.waterfall(d, last, 60e6)
    assert w['pref_taken'] == [] and abs(sum(w['payout'].values()) - 60e6) < 1e-6
    w = CT.waterfall(d, last, 3e6)                                            # below total preferences (5 M): pro rata to investments
    assert w['pref_taken'] == ['Seed', 'Serie A'] and abs(w['payout']['Serie A'] - 2.4e6) < 1e-6 and w['payout']['Gründerin A'] == 0
    w = CT.waterfall(d, last, 10e6)
    assert 'Serie A' in w['pref_taken'] and abs(sum(w['payout'].values()) - 10e6) < 1e-6
    for e in (1e6, 7e6, 12e6, 20e6, 40e6):                                    # nobody gets less than with conversion only when better off
        w, p = CT.waterfall(d, last, e), CT.waterfall(d, last, e, False)
        assert abs(sum(w['payout'].values()) - e) < 1e-6 and all(w['payout'][k] >= p['payout'][k] - 1e-6 for k in w['pref_taken'])


@pytest.mark.parametrize('bad', [{'founders': []}, {'rounds': []}, {'rounds': [{'name': 'S', 'pre_money': 0, 'investment': 1}]},
                                 {'rounds': [{'name': 'S', 'pre_money': 1, 'investment': 9, 'pool_pct': .2}]},
                                 {'rounds': [{'name': 'Gründerin A', 'pre_money': 1, 'investment': 1}]}])
def test_cap_table_invalid(bad):
    with pytest.raises(B.LabError):
        B.cap_table_spec('t/c', 'C', ['k'], [], {**CT.DEFAULT, **bad})


# ------------------------------------------------------------------ legal check

def test_legal_scheme_result_order_and_grading():
    els = LC.DEFAULT['elements']
    assert LC.result(els) == {'positive': False, 'stop': 'erfinderisch', 'checked': ['erfindung', 'ausschluss', 'neuheit', 'erfinderisch']}
    assert LC.progress(els, ['erfindung'])['next'] == 'ausschluss'
    assert LC.progress(els, ['erfindung', 'ausschluss', 'neuheit', 'erfinderisch'])['done']
    with pytest.raises(B.LabError):
        LC.progress(els, ['neuheit'])                                          # Gutachtenstil: no skipping
    e = els[2]   # Neuheit: problematisch -> erfüllt
    assert LC.grade(e, 'problematisch', 'r1') == 'correct' and LC.grade(e, 'erfuellt', 'r1') == 'partial' and LC.grade(e, 'nicht_erfuellt', 'r2') == 'wrong'
    pos = [dict(x, decision='erfuellt') for x in els]
    assert LC.result(pos)['positive']


def test_legal_invalid_and_generic_scheme():
    el = lambda i, dec='erfuellt': {'id': i, 'label': i, 'definition': 'D', 'explanation': 'E', 'decision': dec,
                                    'reasons': [{'id': 'a', 'text': 'x', 'correct': True}, {'id': 'b', 'text': 'y', 'feedback': 'f'}]}
    base = {'question': 'Anspruch?', 'rechtsfolge': 'Anspruch besteht.', 'case': {'facts': ['F'], 'self_designed': True}}
    s = B.legal_check_spec('t/l', 'L', ['k'], [], {**base, 'elements': [el('angebot'), el('annahme'), el('zugang', 'nicht_erfuellt')]})
    assert s['sequence']['predict']['correct'] == 'nein' and any(t['id'] == 'transfer' and t['type'] == 'choice' for t in s['sequence']['tasks'])
    for bad in ([el('a')], [el('a'), el('a')], [el('a'), el('b', 'problematisch')], [el('a'), {**el('b'), 'reasons': [{'id': 'a', 'text': 'x'}, {'id': 'b', 'text': 'y', 'feedback': 'f'}]}]):
        with pytest.raises(B.LabError):
            B.legal_check_spec('t/l', 'L', ['k'], [], {**base, 'elements': bad})


# ------------------------------------------------------------------ specs, catalogue, book blocks

def test_specs_validate_and_learning_sequence():
    for k, s in specs().items():
        B.validate(s); q = s['sequence']
        assert q['tasks'][-1].get('transfer'), k
        for m in q['explore']:
            d0 = P.defaults(s); w = {**d0, **m['witness']}
            assert not P.holds(m['cond'], P.metrics(s, d0), d0) and P.holds(m['cond'], P.metrics(s, w), w), (k, m['id'])
        bad = json.loads(json.dumps(s)); t = next(t for t in bad['sequence']['tasks'] if t['id'] in ('neps', 'score', 'founders', 'result'))
        if 'expected' in t:
            t['expected'] += 1
        else:
            t['correct'] = t['options'][-1]['value'] if t['correct'] != t['options'][-1]['value'] else t['options'][0]['value']
        with pytest.raises(B.LabError):
            B.validate(bad)
    s = specs()
    assert 'selbst konstruiert' in ' '.join(s['legal_check']['sources']) and 'kein Beweis' in ' '.join(s['sequence']['assumptions'])


def test_no_solution_leakage_in_prediction_and_static_figure():
    s = specs()
    assert '10' not in s['sequence']['sequence']['predict']['result_text'] and 'N = ' not in B.static_svg(s['sequence'])
    assert '49' not in B.static_svg(s['cap_table']) and '49' not in s['cap_table']['sequence']['predict']['result_text']
    assert '0,76' not in B.static_svg(s['attention']) and '0,76' not in s['attention']['sequence']['predict']['result_text']
    svg = B.static_svg(s['legal_check'])
    assert 'Erfinderische Tätigkeit' in svg and 'nicht erfüllt: Ende' in svg and 'naheliegend' not in svg


def test_decimal_convention():
    try:
        B.DECIMAL['sep'] = '.'
        s = B.cap_table_spec('t/c', 'C', ['k'], [], {})
        assert '4,000,000' not in json.dumps(s) and '4000000 €' in json.dumps(s, ensure_ascii=False)
    finally:
        B.DECIMAL['sep'] = ','
    assert '4.000.000 €' in json.dumps(B.cap_table_spec('t/c', 'C', ['k'], [], {}), ensure_ascii=False)


def test_catalogue_and_chapter_build(tmp_path):
    kcs = [{'kc_id': 'k1', 'statement': 'Konvergenz von Folgen mit der ε-N-Definition nachweisen', 'source_anchor_ids': ['e1']},
           {'kc_id': 'k2', 'statement': 'Explain scaled dot-product self-attention in a Transformer', 'source_anchor_ids': ['e2']},
           {'kc_id': 'k3', 'statement': 'Pre-Money- und Post-Money-Bewertung sowie Verwässerung berechnen', 'source_anchor_ids': ['e3']},
           {'kc_id': 'k4', 'statement': 'Patentfähigkeit einer Erfindung prüfen (Neuheit, erfinderische Tätigkeit)', 'source_anchor_ids': ['e4']},
           {'kc_id': 'k5', 'statement': 'Folgen von Fehlentscheidungen abschätzen; AIDA: Attention, Interest; Bewertung von Projekten', 'source_anchor_ids': ['e5']}]
    reqs = catalog_requests(kcs)
    assert {r['model']: r['kc_ids'] for r in reqs} == {'sequence': ['k1'], 'attention': ['k2'], 'cap_table': ['k3'], 'legal_check': ['k4']}
    assert catalog_requests(kcs[4:]) == []
    rep, blocks = build_chapter_labs(reqs, tmp_path, 'Kurs', lambda r: 'Folie 3', ['k1', 'k2', 'k3', 'k4'])
    assert [r['status'] for r in rep] == ['BUILT'] * 4, rep
    assert all('<svg' in b['svg'] for b in blocks)
    own = [{'model': 'sequence', 'lab_id': 'a/f', 'title': 'F', 'kc_ids': ['k1'], 'data': {'expr': 'sqrt(n+1)-sqrt(n)', 'limit': 0, 'eps': 0.1, 'horizon': 500}},
           {'model': 'sequence', 'lab_id': 'a/bad', 'title': 'B', 'kc_ids': ['k1'], 'data': {'expr': 'eval(1)', 'limit': 0}}]
    rep, _ = build_chapter_labs(own, tmp_path, 'Kurs', lambda r: 'x', ['k1'])
    assert [r['status'] for r in rep] == ['BUILT', 'NOT_AVAILABLE']


# ------------------------------------------------------------------ browser

@pytest.fixture(scope='module')
def browser():
    pw = pytest.importorskip('playwright.sync_api')
    try:
        ctx = pw.sync_playwright().start(); b = ctx.chromium.launch()
    except Exception as e:
        pytest.skip(f'chromium unavailable: {e}')
    yield b
    b.close(); ctx.stop()


@pytest.fixture(scope='module')
def pages(tmp_path_factory):
    d = tmp_path_factory.mktemp('labs'); s = specs()
    return s, {k: B.render(v, d) for k, v in s.items()}


def _open(browser, path, **kw):
    pg = browser.new_page(**kw); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
    pg.goto(path.resolve().as_uri()); pg.wait_for_selector('html[data-em-ready="1"]', state='attached', timeout=10000)
    return pg, errs


def _rand_expr(rnd, depth=0):
    if depth > 2 or rnd.random() < .3:
        return rnd.choice(['n', str(rnd.randint(1, 5)), '1.5', '(n+1)'])
    op = rnd.choice(['+', '-', '*', '/', '^', 'sqrt', 'abs', 'neg'])
    if op == 'sqrt':
        return f'sqrt({_rand_expr(rnd, depth + 1)}+n)'
    if op == 'abs':
        return f'abs({_rand_expr(rnd, depth + 1)})'
    if op == 'neg':
        return f'-{_rand_expr(rnd, depth + 1)}'
    if op == '^':
        return f'({_rand_expr(rnd, depth + 1)})^{rnd.choice(["2", "-1", "0.5", "(1/n)", "n"])}'
    return f'({_rand_expr(rnd, depth + 1)}{op}{_rand_expr(rnd, depth + 1)})'


def test_js_mirrors_python(browser, pages):
    s, p = pages; pg, errs = _open(browser, p['sequence']); rnd = random.Random(7); worst = 0.0
    for _ in range(150):
        e = _rand_expr(rnd); L = rnd.uniform(-2, 2); eps = rnd.choice([.5, .1, .01]); view = rnd.choice(['all', 'even', 'odd'])
        try:
            py = SQ.terms({'expr': e}, 60); pye = None
        except B.LabError as x:
            py, pye = None, str(x)
        js = pg.evaluate('a=>{try{const t=EM.models.seqTerms({expr:a[0]},60);return {t,N:EM.models.seqFirstIndex(t,a[1],a[2],a[3]),m:EM.models.seqSummary(t).mono}}catch(e){return {err:e.message}}}', [e, L, eps, view])
        if py is None:
            assert js.get('err') == pye, (e, js, pye); continue
        assert 'err' not in js, (e, js)
        worst = max(worst, max(abs(a - b) / max(1, abs(b)) for a, b in zip(js['t'], py)))
        assert js['N'] == SQ.first_index(py, L, eps, view) and js['m'] == SQ.summary(py)['mono'], e
    assert worst < 1e-12, worst
    assert pg.evaluate('()=>EM.models.seqTerms({rec:"sqrt(2+a)",a1:1},30)') == SQ.terms({'rec': 'sqrt(2+a)', 'a1': 1}, 30)
    for _ in range(25):
        n, d, dk = rnd.randint(2, 6), rnd.randint(1, 6), rnd.randint(1, 4)
        X = [[rnd.randint(-3, 3) for _ in range(d)] for _ in range(n)]
        H = [{k: [[rnd.randint(-2, 2) for _ in range(dk)] for _ in range(d)] for k in ('Wq', 'Wk', 'Wv')} for _ in range(rnd.randint(1, 2))]
        c = rnd.random() < .5; js = pg.evaluate('a=>EM.models.attMulti(a[0],a[1],a[2])', [X, H, c]); py = AT.multi(X, H, c)
        assert np.allclose(js['concat'], py['concat'], atol=1e-12) and all(np.allclose(a['A'], b['A'], atol=1e-12) for a, b in zip(js['heads'], py['heads']))
    for _ in range(40):
        d = {'founders': [{'name': f'F{i}', 'shares': rnd.randint(1, 10) * 100000} for i in range(rnd.randint(1, 3))],
             'rounds': [{'name': f'R{i}', 'pre_money': rnd.randint(1, 40) * 5e5, 'investment': rnd.randint(1, 20) * 2.5e5, 'pool_pct': rnd.choice([0, .05, .1, .15]),
                         'pool_mode': rnd.choice(['pre', 'post'])} for i in range(rnd.randint(1, 3))]}
        try:
            d = CT.check_data(d)
        except B.LabError:
            continue
        mode = rnd.choice([None, 'pre', 'post']); ex = rnd.uniform(0, 3e7); pref = rnd.random() < .7
        js = pg.evaluate('a=>{const R=EM.models.capRounds(a[0],a[1]);return {R,w:EM.models.capWaterfall(a[0],R[R.length-1],a[2],a[3])}}', [d, mode, ex, pref])
        R = CT.rounds(d, mode); w = CT.waterfall(d, R[-1], ex, pref)
        assert [o['holders'] for o in js['R']] == [o['holders'] for o in R]
        assert w['pref_taken'] == js['w']['pref_taken'] and all(abs(w['payout'][k] - js['w']['payout'][k]) < 1e-6 for k in w['payout'])
    els = LC.DEFAULT['elements']
    for _ in range(40):
        E = [dict(e, decision=rnd.choice(LC.DECISIONS), resolution=rnd.choice(['erfuellt', 'nicht_erfuellt'])) for e in els[:rnd.randint(2, 5)]]
        com = [e['id'] for e in E][:rnd.randint(0, len(E))]
        js = pg.evaluate('a=>({r:EM.models.legalResult(a[0]),p:EM.models.legalProgress(a[0],a[1]),g:a[0].map(e=>EM.models.legalGrade(e,"problematisch",e.reasons[0].id))})', [E, com])
        assert js['r'] == LC.result(E) and js['p'] == LC.progress(E, com) and js['g'] == [LC.grade(e, 'problematisch', e['reasons'][0]['id']) for e in E]
    assert pg.evaluate('()=>{try{EM.models.seqParse("alert(1)");return "ok"}catch(e){return "err"}}') == 'err'
    assert not errs, errs
    pg.close()


def _enter(pg, sel, value):
    pg.fill(sel, value); pg.press(sel, 'Enter')


def test_results_hidden_until_own_attempt(browser, pages):
    s, p = pages
    pg, errs = _open(browser, p['sequence']); pg.click('text=Ohne Vorhersage erkunden')
    assert pg.inner_text('.em-kpi div:first-child strong') == '?'
    _enter(pg, '.em-own input', '7')                                          # any committed prediction reveals, with comparison
    assert pg.inner_text('.em-kpi div:first-child strong') == '10' and 'Lab: 10' in pg.inner_text('.em-kpi')
    pg.select_option('#p-eps', '0.02'); assert pg.inner_text('.em-kpi div:first-child strong') == '?'   # new question, hidden again
    pg.close(); assert not errs, errs
    pg, errs = _open(browser, p['attention']); pg.click('text=Ohne Vorhersage erkunden')
    row = AT.head(s['attention']['model']['att']['X'], s['attention']['model']['att']['heads'][0])['A'][0]
    assert '?' in pg.inner_text('.em-att-grid')
    _enter(pg, '.em-own input', '; '.join('0,25' for _ in row)); assert 'Noch nicht' in pg.inner_text('.em-own')
    _enter(pg, '.em-own input', '; '.join(f'{x:.2f}'.replace('.', ',') for x in row))
    assert pg.locator('.em-own').inner_text() == '' and '0,76' in pg.inner_text('.em-att-grid')
    pg.close(); assert not errs, errs
    pg, errs = _open(browser, p['cap_table']); pg.click('text=Ohne Vorhersage erkunden')
    assert pg.inner_text('.em-kpi div:first-child strong') == '?'
    _enter(pg, '.em-own input', '60'); assert 'Optionspools fehlen' in pg.inner_text('.em-own')
    _enter(pg, '.em-own input', '49,0'); assert pg.inner_text('.em-kpi div:first-child strong') == '49 %'
    pg.close(); assert not errs, errs
    pg, errs = _open(browser, p['legal_check']); pg.click('text=Ohne Vorhersage erkunden')
    assert 'erscheint' in pg.inner_text('.em-legal-result') and pg.locator('.em-legal-card.off').count() == 4
    picks = {'erfindung': ('erfuellt', 'r1'), 'ausschluss': ('erfuellt', 'r1'), 'neuheit': ('erfuellt', 'r2'), 'erfinderisch': ('problematisch', 'r2')}
    for i, (eid, (dv, rv)) in enumerate(picks.items()):
        assert 'erscheint' in pg.inner_text('.em-legal-result')             # no overall result before every needed element
        card = f'[data-el="{eid}"]'
        pg.click(card + ' >> text=Entscheidung festlegen'); assert 'Bitte Entscheidung' in pg.inner_text(card)
        pg.check(f'{card} input[value="{dv}"]'); pg.check(f'{card} input[name="r-{eid}"][value="{rv}"]'); pg.click(card + ' >> text=Entscheidung festlegen')
        assert 'Referenz' in pg.inner_text(card)
    assert 'Mosaik' in pg.inner_text('[data-el="neuheit"]')                   # feedback on the wrong justification
    assert 'nicht patentfähig' in pg.inner_text('.em-legal-result') and 'Nicht mehr zu prüfen' in pg.inner_text('[data-el="gewerblich"]')
    pg.close(); assert not errs, errs


def test_missions_and_mobile(browser, pages):
    s, p = pages
    for k in ('sequence', 'cap_table'):
        for m in s[k]['sequence']['explore']:
            pg, errs = _open(browser, p[k]); pg.click('text=Ohne Vorhersage erkunden')
            for pid, v in m['witness'].items():
                sel = '#p-' + pid
                if pg.evaluate('s => document.querySelector(s).tagName', sel) == 'SELECT':
                    pg.select_option(sel, str(v))
                else:
                    pg.fill(sel, str(v)); pg.dispatch_event(sel, 'input')
            pg.wait_for_timeout(30)
            assert 'done' in pg.get_attribute(f'[data-mission="{m["id"]}"]', 'class'), (k, m['id'])
            pg.close(); assert not errs, errs
    for k in p:
        pg, errs = _open(browser, p[k], viewport={'width': 390, 'height': 844}, color_scheme='dark')
        pg.click('text=Ohne Vorhersage erkunden'); pg.evaluate("document.querySelectorAll('details').forEach(d=>d.open=true)"); pg.wait_for_timeout(80)
        assert pg.evaluate('document.documentElement.scrollWidth') <= 390, k
        pg.close(); assert not errs, errs


TABLES_JS = '''()=>[...document.querySelectorAll('.em-lab table')].filter(t=>t.offsetParent).map(t=>{const p=t.parentElement,cs=getComputedStyle(p);
  return {sw:p.scrollWidth,cw:p.clientWidth,ox:cs.overflowX,right:p.getBoundingClientRect().right,cap:(t.caption||{}).textContent||''}})'''


def test_cap_table_hides_the_whole_asked_round_and_formats_prices(browser, pages):
    s, p = pages; R = CT.rounds(CT.check_data(CT.DEFAULT)); k = 2
    secret = [B._fmt(R[k]['total'], 0), B._fmt(R[k]['inv_shares'], 0), B._fmt(R[k]['holders'][CT.POOL], 0), '49', B._fmt(R[k]['price'], 2)]
    for w in (1280, 390):
        pg, errs = _open(browser, p['cap_table'], viewport={'width': w, 'height': 900}); pg.click('text=Ohne Vorhersage erkunden')
        pg.evaluate("document.querySelectorAll('details').forEach(d=>d.open=true)"); pg.wait_for_timeout(80)
        txt = pg.inner_text('.em-lab') + ' '.join(pg.eval_on_selector_all('.em-lab [aria-label], .em-lab title', 'es=>es.map(e=>(e.getAttribute("aria-label")||"")+e.textContent)'))
        for v in secret:
            assert v not in txt, (w, v)
        assert '3,50 €' in txt and '3,5000' not in txt and '7,84' not in txt
        for t in pg.evaluate(TABLES_JS):                                     # no clipped tables: fits, or a real scroll container inside the viewport
            assert t['sw'] <= t['cw'] + 1 or t['ox'] in ('auto', 'scroll'), (w, t)
            assert t['right'] <= w + 1, (w, t)
            if w == 1280:
                assert t['sw'] <= t['cw'] + 1, t
        pg.click('text=Ohne eigene Rechnung aufdecken'); pg.wait_for_timeout(50)
        txt = pg.inner_text('.em-lab')
        assert B._fmt(R[k]['total'], 0) in txt and '7,84 €' in txt and '49 %' in txt
        pg.close(); assert not errs, errs
    assert '3,50 €' in json.dumps(s['cap_table']['sequence']['tasks'], ensure_ascii=False) and '3,5000' not in json.dumps(s['cap_table'], ensure_ascii=False)
    assert B._fmt(R[k]['total'], 0) not in B.static_svg(s['cap_table'])


def test_no_clipped_tables_in_any_new_lab(browser, pages):
    s, p = pages
    for key in ('sequence', 'attention', 'legal_check'):
        for w in (1280, 390):
            pg, errs = _open(browser, p[key], viewport={'width': w, 'height': 900}); pg.click('text=Ohne Vorhersage erkunden')
            pg.evaluate("document.querySelectorAll('details').forEach(d=>d.open=true)"); pg.wait_for_timeout(80)
            for t in pg.evaluate(TABLES_JS):
                assert (t['sw'] <= t['cw'] + 1 or t['ox'] in ('auto', 'scroll')) and t['right'] <= w + 1, (key, w, t)
            pg.close(); assert not errs, errs
