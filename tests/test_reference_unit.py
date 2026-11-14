import copy
import json
import random
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

from exam_mastery import reference_unit as RU
from exam_mastery import seqlab as S

UNIT = Path(__file__).resolve().parents[1] / 'units' / 'nlp_sequence_labeling'
KEY = 'em-unit-nlp-sequence-labeling'
DAY = 86_400_000


def rand_bio(rng, n, types=('PER', 'LOC', 'ORG')):
    return [rng.choice(['O', 'O', 'O'] + [f'{p}-{t}' for p in 'BI' for t in types]) for _ in range(n)]


class Math(unittest.TestCase):
    def test_count_form_harmonic_mean_and_bounds(self):
        rng = random.Random(1)
        for _ in range(2000):
            c = S.Counts(rng.randint(1, 50), rng.randint(0, 50), rng.randint(0, 50))
            p, r, f = S.precision(c), S.recall(c), S.f1(c)
            self.assertEqual(f, 2 * p * r / (p + r))                                  # Satz 3, TP > 0
            self.assertEqual(f, 1 / ((1 / p + 1 / r) / 2))                             # "Aufwand pro Treffer"
            self.assertTrue(min(p, r) <= f <= max(p, r) and f <= (p + r) / 2 and f <= 2 * min(p, r))   # Satz 4
            self.assertEqual((p + r) / 2 - f, (p - r) ** 2 / (2 * (p + r)))

    def test_tp_zero_cases_exactly_as_in_table(self):
        # (ii) P = R = 0, harmonic form 0/0, count form 0; (iii)/(iv) one ratio undefined; (v) both and count form undefined
        ii = S.Counts(0, 2, 5)
        self.assertEqual((S.precision(ii), S.recall(ii), S.f1(ii)), (0, 0, 0))
        self.assertIsNone(S.precision(S.Counts(0, 0, 3))); self.assertEqual(S.f1(S.Counts(0, 0, 3)), 0)
        self.assertIsNone(S.recall(S.Counts(0, 4, 0))); self.assertEqual(S.f1(S.Counts(0, 4, 0)), 0)
        self.assertIsNone(S.f1(S.Counts(0, 0, 0)))

    def test_micro_f1_equals_accuracy_when_all_labels_pooled(self):  # Satz 5
        rng = random.Random(2)
        labels = ['A', 'B', 'C', 'O']
        for _ in range(300):
            g, p = [rng.choice(labels) for _ in range(40)], [rng.choice(labels) for _ in range(40)]
            per = {k: S.Counts(sum(a == b == k for a, b in zip(g, p)), sum(b == k != a for a, b in zip(g, p)),
                               sum(a == k != b for a, b in zip(g, p))) for k in labels}
            self.assertEqual(S.micro(per)['F1'], Fraction(sum(a == b for a, b in zip(g, p)), 40))

    def test_toy_experiment_forward_state_identical_backward_differs(self):
        u = RU.load(UNIT)
        a, b = RU.toy_states(u, 'signed', 'fw'), RU.toy_states(u, 'state', 'fw')
        self.assertEqual(a[0], b[0])                                                   # Satz 1 at t = 1
        ab, bb = RU.toy_states(u, 'signed', 'bw'), RU.toy_states(u, 'state', 'bw')
        self.assertGreater(ab[0][1], 0); self.assertLess(bb[0][1], 0)                  # scene: PER vs LOC
        self.assertAlmostEqual(ab[0][1], -bb[0][1])


class Verify(unittest.TestCase):
    def test_unit_verifies_and_covers_every_kc_in_both_forms(self):
        u = RU.load(UNIT)
        RU.verify(u)
        for form in u['exam_forms'].values():
            for kc in u['kcs']:
                self.assertGreaterEqual(sum(it['kc'] == kc for it in form), 2, kc)
        self.assertEqual({it['id'] for it in u['exam_forms']['A']} & {it['id'] for it in u['exam_forms']['B']}, set())

    def test_rejects_ambiguous_or_wrong_items(self):
        u = RU.load(UNIT)
        bad = copy.deepcopy(u); bad['tasks'][5]['accept'] = [0, 1]                     # B5-style ambiguity
        self.assertRaises(RU.UnitError, RU.verify, bad)
        bad = copy.deepcopy(u); bad['exam_forms']['B'] = [i for i in bad['exam_forms']['B'] if i['kc'] != 'prf']
        self.assertRaises(RU.UnitError, RU.verify, bad)
        bad = copy.deepcopy(u); bad['text_html'] = bad['text_html'].replace('0{,}5436', '0{,}5463', 1)
        self.assertRaises(RU.UnitError, RU.verify, bad)                                # unverified prose decimal

    def test_anki_guids_stable_and_unique(self):
        a = RU.anki_tsv(RU.load(UNIT))
        self.assertEqual(a, RU.anki_tsv(RU.load(UNIT)))
        guids = [l.split('\t')[0] for l in a.splitlines() if not l.startswith('#')]
        self.assertEqual(len(guids), len(set(guids)))


try:
    from playwright.sync_api import sync_playwright
    HAVE_BROWSER = (RU.NODE / 'mathjax-full/es5/tex-svg-full.js').exists()
except ImportError:
    HAVE_BROWSER = False


@unittest.skipUnless(HAVE_BROWSER, 'playwright and MathJax runtime required')
class Browser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name)
        RU.build(UNIT, cls.out, pdf=False)
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.pw.stop(); cls.tmp.cleanup()

    def setUp(self):
        self.ctx = self.browser.new_context(viewport={'width': 1200, 'height': 900})

    def tearDown(self):
        self.ctx.close()

    def open(self, hash_='', state=None, raw=None):
        pg = self.ctx.new_page()
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
        url = (self.out / 'index.html').as_uri()
        if state is not None or raw is not None:
            pg.goto(url)
            pg.evaluate('([k, v]) => localStorage.setItem(k, v)', [KEY, raw if raw is not None else json.dumps(state)])
        pg.goto(url + hash_)
        if state is not None or raw is not None:
            pg.reload()
        pg.wait_for_function('document.body.dataset.ready === "1"', timeout=30000)
        return pg, errs

    def stored(self, pg):
        return json.loads(pg.evaluate(f"localStorage.getItem('{KEY}')"))

    # --- metrics parity and visual boundary handling ---
    def test_js_metrics_match_python(self):
        pg, _ = self.open()
        rng = random.Random(3)
        for _ in range(150):
            g, p = rand_bio(rng, 12), rand_bio(rng, 12)
            js = pg.evaluate('([g,p]) => [__emMetrics.spanCounts(g,p), __emMetrics.tokenCounts(g,p)]', [g, p])
            sc, tc = S.span_counts(g, p), S.token_counts(g, p)
            self.assertEqual(js, [{'tp': sc.tp, 'fp': sc.fp, 'fn': sc.fn}, {'tp': tc.tp, 'fp': tc.fp, 'fn': tc.fn}])
        for tp, fp, fn, case in [(3, 1, 2, 'i'), (0, 2, 5, 'ii'), (0, 0, 3, 'iii'), (0, 4, 0, 'iv'), (0, 0, 0, 'v')]:
            r = pg.evaluate('c => [__emMetrics.prf(c), __emMetrics.caseOf(c)]', {'tp': tp, 'fp': fp, 'fn': fn})
            self.assertEqual(r[1], case)
            c = S.Counts(tp, fp, fn)
            for key, ref in (('P', S.precision(c)), ('R', S.recall(c)), ('F', S.f1(c))):
                self.assertEqual(r[0][key] is None, ref is None, (case, key))
            self.assertIsNone(r[0]['H']) if tp == 0 else None                           # 2PR/(P+R) undefined for TP = 0

    def test_f1_scene_free_mode_reaches_zero_boundaries(self):
        pg, errs = self.open('#learn/prf')
        sc = pg.locator('.scene[data-scene=f1]')
        for _ in range(12):
            if sc.locator('.opt').count():
                sc.locator('.opt').nth(1).click()
            nxt = sc.get_by_role('button', name='Weiter →')
            if nxt.is_disabled():
                break
            nxt.click()
        for k in ('tp', 'fp', 'fn'):
            for _ in range(13):
                sc.get_by_role('button', name=k + ' minus').click()
        svg = sc.locator('svg.plot')
        self.assertIn('Fall v', svg.get_attribute('aria-label'))
        self.assertIn('P und R nicht definiert', sc.inner_text())
        sc.get_by_role('button', name='fn plus').click()                               # case (iii)
        self.assertIn('P nicht definiert', sc.inner_text())
        sc.get_by_role('button', name='fp plus').click()                               # case (ii): point at (0, 0)
        self.assertEqual(sc.locator('circle').count(), 1)
        self.assertEqual(errs, [])

    def test_prediction_blocks_until_answered(self):
        pg, _ = self.open('#learn/rnn')
        sc = pg.locator('.scene[data-scene=birnn]')
        sc.get_by_role('button', name='Weiter →').click()
        self.assertTrue(sc.get_by_role('button', name='Weiter →').is_disabled())
        sc.locator('.opt').nth(1).click()                                               # wrong prediction
        self.assertIn('Nicht ganz', sc.inner_text())
        self.assertFalse(sc.get_by_role('button', name='Weiter →').is_disabled())
        self.assertEqual(self.stored(pg)['predictions'][0]['correct'], False)

    # --- tasks, hints, B5 ---
    def test_hints_after_attempt_diagnosis_and_unique_b5(self):
        pg, errs = self.open('#learn/einheit')
        t = pg.locator('#task-B4')
        self.assertTrue(t.get_by_role('button', name='Hinweis').is_disabled())
        t.locator('#B4-a0').fill('2/5'); t.locator('#B4-a1').fill('3/4')
        t.get_by_role('button', name='Prüfen').click()
        self.assertIn('FP und FN', t.inner_text()); self.assertIn('Das ist die Precision', t.inner_text())
        self.assertFalse(t.get_by_role('button', name='Hinweis').is_disabled())
        b5 = pg.locator('#task-B5')
        b5.locator('input[name="B5-a0"][value="1"]').check(); b5.get_by_role('button', name='Prüfen').click()
        self.assertIn('noch nicht', b5.inner_text())
        b5.locator('input[name="B5-a0"][value="0"]').check(); b5.get_by_role('button', name='Prüfen').click()
        self.assertIn('richtig', b5.inner_text())
        self.assertEqual(errs, [])

    # --- learner-model state transitions (reproducible, seeded states) ---
    def att(self, task, kc, stage, ts, correct=True, first=True, hints=0, revealed=False):
        return {'task': task, 'kc': kc, 'stage': stage, 'ts': ts, 'correct': correct, 'first': first, 'hints': hints, 'revealed': revealed}

    def test_series_classification(self):
        now = 1_800_000_000_000
        st = {'v': 2, 'attempts': [self.att('B1', 'birnn', 'worked', now), self.att('B4', 'prf-level', 'independent', now),
                                   self.att('B6', 'micro-macro', 'transfer', now, hints=1), self.att('B3', 'prf-edge', 'hint', now, revealed=True),
                                   self.att('B4', 'prf-level', 'independent', now + 1, first=False)],
              'exams': [], 'cards': {}, 'visited': {}, 'last': None, 'predictions': []}
        pg, _ = self.open('', st)
        s = pg.evaluate('() => { const s = __emModel.series(); return {a: s.assisted.map(x => x.task), u: s.unsupported.map(x => x.task)}; }')
        self.assertEqual(s['u'], ['B4'])                                                # only the unaided first attempt
        self.assertEqual(sorted(s['a']), ['B1', 'B3', 'B4', 'B6'])

    def exam(self, ts, form, delayed, correct=True, kcs=None):
        u = RU.load(UNIT)
        items = [{'id': it['id'], 'kc': it['kc'], 'correct': correct if (kcs is None or it['kc'] in kcs) else True, 'conf': 90, 'transfer': bool(it.get('transfer'))}
                 for it in u['exam_forms'][form]]
        return {'ts': ts, 'form': form, 'delayed': {k: delayed for k in u['kcs']}, 'items': items}

    def levels(self, st):
        pg, _ = self.open('', st)
        return pg.evaluate('() => Object.fromEntries(["birnn","prf","prf-edge","prf-level","micro-macro"].map(k => [k, __emModel.kcLevel(k)]))')

    def test_mastery_levels_require_delayed_new_items_and_retention(self):
        base = {'v': 2, 'attempts': [], 'cards': {}, 'visited': {}, 'last': None, 'predictions': []}
        t0 = 1_800_000_000_000
        self.assertEqual(set(self.levels({**base, 'exams': []}).values()), {'NICHT_GEPRUEFT'})
        self.assertEqual(set(self.levels({**base, 'exams': [self.exam(t0, 'A', False)]}).values()), {'SOFORT'})
        lv = self.levels({**base, 'exams': [self.exam(t0, 'A', False), self.exam(t0 + 2 * DAY, 'B', True, correct=False, kcs={'prf'})]})
        self.assertEqual(lv['prf'], 'LUECKE'); self.assertEqual(lv['birnn'], 'VERZOEGERT')
        lv = self.levels({**base, 'exams': [self.exam(t0, 'A', True), self.exam(t0 + 3 * DAY, 'B', True)]})
        self.assertEqual(set(lv.values()), {'VERZOEGERT'})                              # < 7 days apart
        lv = self.levels({**base, 'exams': [self.exam(t0, 'A', True), self.exam(t0 + 8 * DAY, 'A', True)]})
        self.assertEqual(set(lv.values()), {'VERZOEGERT'})                              # same form twice: no retention claim
        lv = self.levels({**base, 'exams': [self.exam(t0, 'A', True), self.exam(t0 + 8 * DAY, 'B', True)]})
        self.assertEqual(set(lv.values()), {'BEHALTEN'})

    def test_exam_flow_alternates_forms_and_records_delay(self):
        pg, _ = self.open('#exam')
        self.assertIn('Form A', pg.inner_text('h1'))
        pg.get_by_role('button', name='Abgeben').click()
        st = self.stored(pg)
        self.assertEqual(st['exams'][0]['form'], 'A')
        self.assertFalse(any(st['exams'][0]['delayed'].values()))                       # no prior activity: not delayed
        self.assertEqual(st['attempts'], [])                                            # exam data kept separate
        pg.goto(pg.url.split('#')[0] + '#exam'); pg.reload(); pg.wait_for_function('document.body.dataset.ready === "1"')
        self.assertIn('Form B', pg.inner_text('h1'))

    # --- persistence ---
    def test_persistence_corrupt_state_and_invalid_import(self):
        pg, _ = self.open('#learn/einheit')
        t = pg.locator('#task-B4'); t.locator('#B4-a0').fill('1/3'); t.locator('#B4-a1').fill('2/3'); t.get_by_role('button', name='Prüfen').click()
        pg.reload(); pg.wait_for_function('document.body.dataset.ready === "1"')
        self.assertEqual(len(self.stored(pg)['attempts']), 1)                           # survives reload (file://)
        pg2, _ = self.open('', raw='{not json')
        self.assertIn('beschädigt', pg2.inner_text('main'))
        keys = pg2.evaluate('() => Object.keys(localStorage)')
        self.assertTrue(any(k.startswith(KEY + '-beschaedigt-') for k in keys))
        pg2.goto(pg2.url.split('#')[0] + '#progress')
        pg2.set_input_files('input[type=file]', files=[{'name': 'x.json', 'mimeType': 'application/json', 'buffer': b'{"attempts": 5}'}])
        pg2.wait_for_timeout(200)
        self.assertIn('Import abgelehnt', pg2.inner_text('main'))

    def test_mobile_no_horizontal_scroll(self):
        ctx = self.browser.new_context(viewport={'width': 390, 'height': 844})
        pg = ctx.new_page()
        for h in ('', '#learn/rnn', '#learn/prf', '#learn/einheit', '#exam', '#progress'):
            pg.goto((self.out / 'index.html').as_uri() + h); pg.wait_for_function('document.body.dataset.ready === "1"'); pg.wait_for_timeout(200)
            self.assertLessEqual(pg.evaluate('document.documentElement.scrollWidth'), 390, h)
        ctx.close()
