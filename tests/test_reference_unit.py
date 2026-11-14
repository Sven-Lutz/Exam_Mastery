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


def rand_bio(rng, n, types=('PER', 'LOC', 'ORG')):
    return [rng.choice(['O', 'O', 'O'] + [f'{p}-{t}' for p in 'BI' for t in types]) for _ in range(n)]


class Math(unittest.TestCase):
    def test_conlleval_span_reading(self):
        self.assertEqual(S.spans(['O', 'I-LOC', 'I-LOC', 'B-LOC', 'I-PER']), {(1, 3, 'LOC'), (3, 4, 'LOC'), (4, 5, 'PER')})

    def test_count_form_equals_harmonic_mean_and_bounds(self):
        rng = random.Random(1)
        for _ in range(2000):
            c = S.Counts(rng.randint(1, 50), rng.randint(0, 50), rng.randint(0, 50))
            p, r, f = S.precision(c), S.recall(c), S.f1(c)
            self.assertEqual(f, 2 * p * r / (p + r))                          # Satz 3
            self.assertTrue(min(p, r) <= f <= max(p, r))                      # Satz 4
            self.assertTrue(f <= (p + r) / 2 and f <= 2 * min(p, r))
            self.assertEqual((p + r) / 2 - f, (p - r) ** 2 / (2 * (p + r)))

    def test_zero_denominators(self):
        self.assertIsNone(S.precision(S.Counts(0, 0, 3)))
        self.assertEqual(S.f1(S.Counts(0, 0, 3)), 0)
        self.assertIsNone(S.f1(S.Counts(0, 0, 0)))

    def test_micro_f1_equals_accuracy_when_all_labels_pooled(self):  # Satz 5
        rng = random.Random(2)
        labels = ['A', 'B', 'C', 'O']
        for _ in range(300):
            g = [rng.choice(labels) for _ in range(40)]
            p = [rng.choice(labels) for _ in range(40)]
            per = {k: S.Counts(sum(a == b == k for a, b in zip(g, p)), sum(b == k != a for a, b in zip(g, p)),
                               sum(a == k != b for a, b in zip(g, p))) for k in labels}
            self.assertEqual(S.micro(per)['F1'], Fraction(sum(a == b for a, b in zip(g, p)), 40))

    def test_dependence_sets(self):
        self.assertEqual(S.dependence(6, 'forward')[2], {1, 2})
        self.assertEqual(S.dependence(6, 'backward')[2], {2, 3, 4, 5, 6})
        self.assertEqual(S.dependence(6, 'bi')[2], set(range(1, 7)))


class Verify(unittest.TestCase):
    def test_unit_verifies(self):
        r = RU.verify(RU.load(UNIT))
        self.assertTrue(r['ok'])
        self.assertGreaterEqual(len(r['checked']), 20)

    def test_fails_closed_on_wrong_stored_number(self):
        u = RU.load(UNIT)
        bad = copy.deepcopy(u)
        bad['tasks'][3]['answers'][0]['diagnoses'][0]['value'] = '1/3'   # equals the correct span F1
        with self.assertRaises(RU.UnitError):
            RU.verify(bad)
        bad = copy.deepcopy(u)
        bad['tasks'][1]['steps'][2]['s'] = bad['tasks'][1]['steps'][2]['s']
        bad['text_html'] += '<div class="task-ref" data-task="Z9"></div>'
        with self.assertRaises(RU.UnitError):
            RU.verify(bad)

    def test_anki_guids_stable_and_unique(self):
        u = RU.load(UNIT)
        a, b = RU.anki_tsv(u), RU.anki_tsv(RU.load(UNIT))
        self.assertEqual(a, b)
        guids = [l.split('\t')[0] for l in a.splitlines() if not l.startswith('#')]
        self.assertEqual(len(guids), len(set(guids)))
        self.assertIn('#guid column:1', a)


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

    def page(self, hash_=''):
        pg = self.browser.new_page(viewport={'width': 1200, 'height': 900})
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
        pg.goto((self.out / 'index.html').as_uri() + hash_)
        pg.wait_for_function('document.body.dataset.ready === "1"', timeout=30000)
        return pg, errs

    def test_home_offers_today_and_no_errors(self):
        pg, errs = self.page()
        self.assertIn('Heute lernen', pg.inner_text('main'))
        self.assertTrue(pg.locator('button.primary').first.is_visible())
        self.assertEqual(errs, [])
        pg.close()

    def test_js_metrics_match_python_reference(self):
        pg, _ = self.page()
        rng = random.Random(3)
        for _ in range(150):
            g, p = rand_bio(rng, 12), rand_bio(rng, 12)
            js = pg.evaluate('([g,p]) => [__emMetrics.spanCounts(g,p), __emMetrics.tokenCounts(g,p)]', [g, p])
            sc, tc = S.span_counts(g, p), S.token_counts(g, p)
            self.assertEqual(js[0], {'tp': sc.tp, 'fp': sc.fp, 'fn': sc.fn}, (g, p))
            self.assertEqual(js[1], {'tp': tc.tp, 'fp': tc.fp, 'fn': tc.fn}, (g, p))
        pg.close()

    def test_hints_after_attempt_and_diagnosis(self):
        pg, errs = self.page('#learn/einheit')
        task = pg.locator('#task-B4')
        hint = task.get_by_role('button', name='Hinweis')
        self.assertTrue(hint.is_disabled())
        task.locator('#B4-a0').fill('2/5')
        task.locator('#B4-a1').fill('3/4')
        task.get_by_role('button', name='Prüfen').click()
        text = task.inner_text()
        self.assertIn('FP und ein FN', text.replace('<em>', ''))      # diagnosis of the type error
        self.assertIn('Das ist die Precision', text)
        self.assertFalse(hint.is_disabled())
        self.assertTrue(task.locator('.sol').is_hidden())
        task.locator('#B4-a0').fill('1/3'); task.locator('#B4-a1').fill('0,667')
        task.get_by_role('button', name='Prüfen').click()
        self.assertTrue(task.locator('.sol').is_visible())
        state = json.loads(pg.evaluate("localStorage.getItem('em-unit-nlp-sequence-labeling')"))
        self.assertEqual([a['correct'] for a in state['attempts'] if a['task'] == 'B4'], [False, True])
        self.assertEqual(errs, [])
        pg.close()

    def test_mastery_only_from_delayed_unassisted_exam(self):
        pg, _ = self.page('#exam')
        answers = {'X1-a0': '2/7', 'X1-a1': '1/2', 'X2-a0': '0,8', 'X2-a1': '0.7921', 'X3-a0': '204009', 'X4-a0': '1,2,3'}

        def take_exam():
            for k, v in answers.items():
                pg.locator('#' + k).fill(v)
            pg.locator('input[name="X5-a0"][value="2"]').check()
            pg.locator('input[name="X6-a0"][value="1"]').check()
            pg.get_by_role('button', name='Abgeben').click()
            self.assertIn('6 von 6 richtig', pg.inner_text('main'))

        pg.evaluate("""() => { const k='em-unit-nlp-sequence-labeling'; const s={v:1,attempts:[],exams:[],cards:{},visited:{},last:null};
          for (const kc of ['birnn','prf-edge','prf-level','micro-macro']) s.attempts.push({task:'B1',kc,stage:'worked',ts:Date.now()-60000,correct:true,first:true});
          localStorage.setItem(k, JSON.stringify(s)); }""")
        pg.reload(); pg.wait_for_function('document.body.dataset.ready === "1"')
        take_exam()
        pg.goto(pg.url.split('#')[0] + '#progress')
        self.assertNotIn('GEMEISTERT', pg.inner_text('table'))            # immediate exam: not mastery
        self.assertIn('SOFORT_OHNE_HILFE', pg.inner_text('table'))
        pg.evaluate("""() => { const k='em-unit-nlp-sequence-labeling'; const s=JSON.parse(localStorage.getItem(k));
          s.attempts.forEach(a => a.ts -= 3*864e5); s.exams.forEach(e => e.ts -= 3*864e5); localStorage.setItem(k, JSON.stringify(s)); }""")
        pg.goto(pg.url.split('#')[0] + '#exam'); pg.reload(); pg.wait_for_function('document.body.dataset.ready === "1"')
        take_exam()
        state = json.loads(pg.evaluate("localStorage.getItem('em-unit-nlp-sequence-labeling')"))
        self.assertEqual(len(state['exams']), 2)
        self.assertTrue(all(i['delayed'] for i in state['exams'][1]['items']))
        self.assertFalse(any(a.get('stage') == 'exam' for a in state['attempts']))   # exam data stored separately
        pg.goto(pg.url.split('#')[0] + '#progress')
        self.assertIn('GEMEISTERT', pg.inner_text('table'))
        pg.close()

    def test_flow_visual_reacts(self):
        pg, _ = self.page('#learn/rnn')
        svg = pg.locator('.viz[data-viz=flow] svg.plot')
        before = svg.get_attribute('aria-label')
        pg.locator('.viz[data-viz=flow] input[value=bi]').check()
        self.assertIn('1, 2, 3, 4, 5, 6', svg.get_attribute('aria-label'))
        self.assertNotEqual(before, svg.get_attribute('aria-label'))
        pg.close()
