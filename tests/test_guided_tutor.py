"""Guided learning (learning/guided.py, EMT.guided): the tutor teaches a missing prerequisite instead of only grading.

Proves: lessons are valid data (checks re-diagnosed, no evidence keys), Python and browser agree on prerequisite
resolution, diagnosed gaps, checks, ladder levels and brief modes; a task solved after guided help is not independent
evidence; evidence and retest items never show a key in guided help or the external-model brief; the optional local
model is loopback-only and its reply is FEEDBACK_UNVERIFIED. Browser runs are offline (no external request, no page error).
"""
import copy
import json
import random
import tempfile
import unittest
from pathlib import Path

from exam_mastery.learning import diagnose as D, guided as G, policy as P, render, tracks as TR
from exam_mastery.learning.experience import validate as validate_unit
from exam_mastery.learning.experience_evidence import EvidenceError, assessment_revision, summarize

ROOT = Path(__file__).resolve().parents[1]
TRACKS = {t['id']: t for t in TR.all_tracks()}
ML, ATT = TRACKS['ml/backprop-track'], TRACKS['ai/attention-track']
UNIT = json.loads((ROOT / 'fixtures/experience_attention_reference.json').read_text(encoding='utf-8'))
T = lambda tr, tid: next(t for t in tr['tasks'] if t['id'] == tid)
NOW = '2026-11-10T10:00:00Z'


def engine_part(brief):
    """The brief without the learner's own inputs (they may contain anything the learner typed)."""
    head, _, rest = brief.partition('Meine bisherigen Versuche'); _, _, tail = rest.partition('Genutzte Hilfen')
    return head + tail


def attempt(tr, tid, ans, t=NOW):
    return {'type': 'attempt', 'task': tid, 'diagnosis': D.diagnose(T(tr, tid), ans), 't': t}


class LessonData(unittest.TestCase):
    def test_track_and_unit_lessons_validate(self):
        for tr in TRACKS.values():
            self.assertEqual(G.validate_lessons(tr), [], tr['id'])
        self.assertEqual(G.validate_lessons(UNIT, 'unit'), [])
        self.assertTrue(validate_unit(UNIT)['valid'])
        self.assertGreaterEqual(len(ML['lessons']), 2); self.assertGreaterEqual(len(ATT['lessons']), 4)

    def test_backward_compatible_without_lessons(self):
        tr = copy.deepcopy(ML); tr.pop('lessons')
        self.assertTrue(TR.validate(tr))
        self.assertEqual([G.lessons_for_task(tr, t) for t in tr['tasks']], [[]] * len(tr['tasks']))
        u = copy.deepcopy(UNIT); u.pop('lessons')
        self.assertTrue(validate_unit(u)['valid'])

    def test_lessons_do_not_move_the_assessment_revision(self):
        u = copy.deepcopy(UNIT); u.pop('lessons')
        self.assertEqual(assessment_revision(u), assessment_revision(UNIT))

    def test_validation_rejects_bad_lessons(self):
        def probs(mut):
            tr = copy.deepcopy(ML); mut(tr['lessons'][1], tr); return G.validate_lessons(tr)
        leak = T(ML, 'ml-similar')['solution'][0]
        self.assertTrue(any('evidence answer key' in p for p in probs(lambda l, tr: l.__setitem__('explain', l['explain'] + ' ' + leak))))
        self.assertTrue(any('not diagnosed as value_not_derivative' in p for p in probs(lambda l, tr: l['check'].__setitem__('expected', 0.9))))
        self.assertTrue(any('not diagnosed as correct' in p for p in probs(lambda l, tr: l.__setitem__('check', dict(l['check'], type='choice', options=[{'value': 'a', 'label': 'a'}], correct='b')))))
        self.assertTrue(any('unknown category' in p for p in probs(lambda l, tr: l['for']['categories'].append('nope'))))
        self.assertTrue(any('not found' in p for p in probs(lambda l, tr: l['taught_in'].append({'kind': 'task', 'ref': 'x', 'label': 'x'}))))
        self.assertTrue(any('reuses a task prompt' in p for p in probs(lambda l, tr: l['check'].__setitem__('prompt', T(tr, 'ml-pre')['prompt']))))
        self.assertTrue(any('cycle' in p for p in probs(lambda l, tr: (l.__setitem__('requires', ['prereq/chain-rule']), tr['lessons'][0].__setitem__('requires', [l['id']])))))
        bad = copy.deepcopy(ML); bad['lessons'][0]['check']['errors'][0]['value'] = bad['lessons'][0]['check']['expected']   # wrong answer collides with the key
        with self.assertRaises(TR.TrackError):
            TR.validate(bad)
        u = copy.deepcopy(UNIT); u['lessons'][0]['taught_in'][0]['ref'] = 'teach/none'
        self.assertFalse(validate_unit(u)['valid'])


class PrerequisiteGraph(unittest.TestCase):
    def test_resolution_per_task(self):
        self.assertEqual(G.lessons_for_task(ML, T(ML, 'ml-core')), ['prereq/chain-rule', 'prereq/sigmoid-derivative'])
        self.assertEqual(G.lessons_for_task(ML, T(ML, 'ml-pre')), ['prereq/sigmoid-derivative'])
        # requires come first: the softmax Jacobian needs softmax itself
        self.assertEqual(G.lessons_for_task(ATT, T(ATT, 'att-harder')), ['prereq/softmax-normalisation', 'prereq/softmax-jacobian'])
        exp = next(a for a in UNIT['assessments'] if a['id'] == 'task/backprop-numeric')
        self.assertEqual(G.lessons_for_task(UNIT, exp), ['prereq/softmax-normalisation', 'prereq/softmax-jacobian'])

    def test_diagnosed_gap(self):
        gap = lambda tr, tid, a: G.gap_for(tr, D.diagnose(T(tr, tid), a))
        self.assertEqual(gap(ML, 'ml-core', 'delta_o*v1*x1'), 'prereq/sigmoid-derivative')      # sigmoid derivative missing
        self.assertEqual(gap(ML, 'ml-pre', '0,6'), 'prereq/sigmoid-derivative')
        self.assertEqual(gap(ML, 'ml-core', 'delta_o*x1'), 'prereq/chain-rule')
        self.assertIsNone(gap(ML, 'ml-core', 'delta_o*v1*fp1*x1'))                                 # correct: nothing to teach
        unscaled = next(e['value'] for e in T(ATT, 'att-core')['errors'] if e['category'] == 'missing_scaling')
        self.assertEqual(gap(ATT, 'att-core', repr(unscaled)), 'prereq/sqrt-dk-scaling')
        mc = next(a for a in UNIT['assessments'] if a['id'] == 'task/backprop-numeric')
        self.assertEqual(G.gap_for(UNIT, D.diagnose(dict(mc['machine_check'], id=mc['id'], kc_id='x'), '0,280058')), 'prereq/softmax-jacobian')

    def test_checks_and_ladder(self):
        l = next(l for l in ML['lessons'] if l['id'] == 'prereq/sigmoid-derivative')
        self.assertEqual(G.check(l, '0,09')['result'], 'correct')
        r = G.check(l, '0,9'); self.assertEqual((r['result'], r['error_category']), ('incorrect', 'value_not_derivative')); self.assertIn('σ(z) selbst', r['feedback'])
        self.assertEqual([G.hint_levels(n) for n in range(4)], [[], ['step'], ['orientation', 'step'], ['orientation', 'strategy', 'step']])
        self.assertEqual([G.assist_level(k, 3) for k in (1, 2, 3)], ['hint_1', 'hint_2', 'hint_bottom_out'])
        self.assertEqual([G.brief_mode(r, n) for r, n in [('core', 0), ('core', 1), ('similar', 3), ('transfer', 1), ('retest', 2)]],
                         ['keyless', 'with_reference', 'keyless', 'keyless', 'task_withheld'])


class EvidenceIntegrity(unittest.TestCase):
    def test_solved_after_guided_help_is_not_independent(self):
        ev = [attempt(ML, 'ml-core', 'delta_o*v1*x1'),
              {'type': 'guided', 'task': 'ml-core', 'lesson': 'prereq/sigmoid-derivative', 'kc': 'prereq/sigmoid-derivative', 'step': 'lesson',
               'assist_level': 'prereq_lesson', 'source': 'deterministic', 't': NOW},
              attempt(ML, 'ml-core', 'delta_o*v1*fp1*x1')]
        self.assertTrue(P.helped(ev, 'ml-core', 2))
        self.assertEqual(P.kc_status(ML, ev, NOW)['ml/backpropagation'], 'ASSISTED')
        self.assertEqual(P.kc_evidence_basis(ML, ev)['ml/backpropagation'], 'none')
        self.assertEqual(P.decide(ML, ev)['rule'], 'RF')
        # the lesson names the competency it teaches: a prerequisite task right after it is assisted too (CD-9)
        ev2 = ev + [attempt(ML, 'ml-pre2', '0,21', '2026-11-10T10:05:00Z')]
        self.assertEqual(P.kc_status(ML, ev2, NOW)['prereq/sigmoid-derivative'], 'ASSISTED')
        # ... but not after the help window
        ev3 = ev + [attempt(ML, 'ml-pre2', '0,21', '2026-11-11T12:00:00Z')]
        self.assertNotEqual(P.kc_status(ML, ev3, '2026-11-11T13:00:00Z')['prereq/sigmoid-derivative'], 'ASSISTED')

    def test_lesson_check_is_not_an_attempt(self):
        ev = [{'type': 'guided', 'task': 'ml-pre', 'lesson': 'prereq/sigmoid-derivative', 'step': 'check', 'result': 'correct', 't': NOW}]
        self.assertEqual(P.kc_status(ML, ev, NOW)['prereq/sigmoid-derivative'], 'NOT_ASSESSED')

    def test_practice_log_counts_guided_help(self):
        rev = assessment_revision(UNIT); at = '2026-11-10T10:00:00Z'
        log = lambda evs: {'schema': 'em-practice-evidence-v1', 'unit_id': UNIT['unit_id'], 'assessment_revision': rev, 'events': evs}
        s = summarize(log([{'type': 'attempt', 'task_id': 'task/backprop-numeric', 'at': at, 'response_chars': 8},
                           {'type': 'guided_help', 'task_id': 'task/backprop-numeric', 'at': at, 'lesson_id': 'prereq/softmax-jacobian'},
                           {'type': 'attempt', 'task_id': 'task/backprop-numeric', 'at': at, 'response_chars': 8}]), UNIT)
        a = s['assessments']['task/backprop-numeric']
        self.assertEqual((a['status'], a['assisted_attempts'], a['guided_helps']), ('ASSISTED_ATTEMPT_UNVERIFIED', 1, 1))
        with self.assertRaises(EvidenceError):   # help before an own attempt is rejected by the strict log
            summarize(log([{'type': 'guided_help', 'task_id': 'task/backprop-numeric', 'at': at, 'lesson_id': 'x'}]), UNIT)

    def test_no_lesson_contains_an_evidence_key(self):
        for c in list(TRACKS.values()) + [UNIT]:
            for l in c.get('lessons', []):
                self.assertEqual(G.leaks(c, G.lesson_text(l)), [], l['id'])
        self.assertTrue(G.leaks(ML, 'x ' + T(ML, 'ml-retest')['expected_expr']))


class Browser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        from exam_mastery.learning.interactive_reference import render_html
        cls.td = tempfile.TemporaryDirectory(); cls.out = Path(cls.td.name)
        for t in TRACKS.values():
            render.write(t, cls.out / 'l', lab_href='../labs/x.html')
        (cls.out / 'i.html').write_text(render_html(UNIT), encoding='utf-8')
        cls.pw = sync_playwright().start(); cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.pw.stop(); cls.td.cleanup()

    def open(self, rel, events=None, w=1280):
        ctx = self.browser.new_context(viewport={'width': w, 'height': 900}); pg = ctx.new_page()
        self.errors, self.requests = [], []
        pg.on('pageerror', lambda e: self.errors.append(str(e)))
        pg.on('request', lambda r: self.requests.append(r.url) if not r.url.startswith(('file:', 'data:', 'blob:')) else None)
        pg.goto((self.out / rel).as_uri())
        if rel.endswith('i.html'):
            pg.wait_for_selector('.assessment .guide-panel', state='attached'); return pg
        pg.wait_for_selector('html[data-em-ready="1"]', state='attached')
        if events is not None:
            sk = pg.evaluate('EMT.storeKey')
            pg.evaluate('([k, ev]) => localStorage.setItem("em-tutor-v1", JSON.stringify({schema: 1, tracks: {[k]: {events: ev}}}))', [sk, events])
            pg.reload(); pg.wait_for_selector('html[data-em-ready="1"]', state='attached')
        return pg

    def events(self, pg):
        return [e for e in pg.evaluate('EMT.store.events(EMT.storeKey)') if e['type'] != 'decision']

    def test_js_python_parity(self):
        pg = self.open('l/ml__backprop-track.html'); r = random.Random(7)
        for c in list(TRACKS.values()) + [UNIT]:
            tasks = c.get('tasks') or c['assessments']
            for t in tasks:
                self.assertEqual(pg.evaluate('([c,t]) => EMT.guided.lessonsForTask(c,t)', [c, t]), G.lessons_for_task(c, t), t['id'])
                spec = dict(t.get('machine_check') or t, id=t['id'], kc_id=t.get('kc_id', 'x'))
                if spec.get('type') not in ('numeric', 'expression', 'choice'):
                    continue
                answers = ([repr(e['value']) for e in spec.get('errors', [])] + [b['expr'] for b in spec.get('bugs', [])]
                           + [o['value'] for o in spec.get('options', [])] + [TR._answer_for(spec) if 'kc_id' in t else repr(spec['expected'])])
                for a in answers:
                    d = D.diagnose(spec, a)
                    self.assertEqual(pg.evaluate('([c,d]) => EMT.guided.gapFor(c,d)', [c, d]), G.gap_for(c, d), (t['id'], a))
            for l in c.get('lessons', []):
                q = l['check']
                answers = ([repr(q['expected']), repr(-q['expected']), str(r.uniform(-2, 2)), 'abc'] + [repr(e['value']) for e in q.get('errors', [])]
                           if q['type'] == 'numeric' else [o['value'] for o in q['options']] + ['nope'])
                for a in answers:
                    js, py = pg.evaluate('([l,a]) => EMT.guided.checkLesson(l,a)', [l, a]), G.check(l, a)
                    self.assertEqual((js['result'], js['error_category'], js['feedback']), (py['result'], py['error_category'], py['feedback']), (l['id'], a))
            self.assertEqual(pg.evaluate('c => EMT.guided.evidenceKeys(c)', c), G.evidence_keys(c))
        for n in range(6):
            self.assertEqual(pg.evaluate('n => EMT.guided.hintLevels(n)', n), G.hint_levels(n))
            for k in range(1, n + 1):
                self.assertEqual(pg.evaluate('([k,n]) => EMT.guided.assistLevel(k,n)', [k, n]), G.assist_level(k, n))
        for role in ('diagnostic', 'core', 'contrast', 'harder', 'similar', 'transfer', 'retest', 'open'):
            for n in (0, 1, 2):
                self.assertEqual(pg.evaluate('([r,n]) => EMT.guided.briefMode(r,n)', [role, n]), G.brief_mode(role, n))
        ev = [attempt(ML, 'ml-core', 'delta_o*v1*x1'), {'type': 'guided', 'task': 'ml-core', 'lesson': 'prereq/sigmoid-derivative', 'kc': 'prereq/sigmoid-derivative', 'step': 'lesson', 't': NOW},
              attempt(ML, 'ml-core', 'delta_o*v1*fp1*x1'), attempt(ML, 'ml-pre2', '0,21', '2026-11-10T10:05:00Z')]
        self.assertEqual(pg.evaluate('([tr,ev]) => EMT.kcStatus(tr,ev,"2026-11-10T11:00:00Z")', [ML, ev]), P.kc_status(ML, ev, '2026-11-10T11:00:00Z'))
        self.assertEqual(pg.evaluate('([tr,ev]) => EMT.kcEvidenceBasis(tr,ev)', [ML, ev]), P.kc_evidence_basis(ML, ev))
        self.assertEqual(self.errors, [])

    def test_backprop_sigmoid_gap_is_taught_then_back_to_task(self):
        pg = self.open('l/ml__backprop-track.html'); g = lambda k: pg.get_attribute('#wb', 'data-' + k)
        pg.fill('#ans', '0,24'); pg.click('#check'); pg.click('#next')
        self.assertEqual(g('task'), 'ml-core')
        self.assertEqual(pg.locator('#guide .wb-chip').all_inner_texts(), ['Kettenregel: Ableitungen entlang eines Weges', 'Ableitung der Sigmoidfunktion'])
        pg.fill('#ans', 'delta_o*v1*x1'); pg.click('#check')                       # sigmoid derivative missing in the chain
        self.assertEqual(g('category'), 'missing_activation_derivative')
        self.assertTrue(pg.locator('#guide-offer').is_visible()); self.assertIn('Ableitung der Sigmoidfunktion', pg.inner_text('#guide-offer'))
        self.assertFalse(any(e['type'] == 'guided' for e in self.events(pg)))     # offered, not forced: nothing logged yet
        pg.click('#guide-learn')
        lesson = pg.inner_text('.wb-lesson')
        for part in ('σ′(z) = σ(z)·(1 − σ(z))', 'Durchgerechnet', 'Kurze Kontrolle'):
            self.assertIn(part, lesson)
        pg.fill('#guide-ans', '0,9'); pg.click('#guide-check')
        self.assertEqual(pg.get_attribute('.wb-lesson', 'data-check'), 'incorrect'); self.assertIn('σ(z) selbst', pg.inner_text('#guide-fb'))
        pg.fill('#guide-ans', '0,09'); pg.click('#guide-check')
        self.assertEqual(pg.get_attribute('.wb-lesson', 'data-check'), 'correct')
        pg.click('#guide-back')
        self.assertEqual(pg.evaluate('document.activeElement.id'), 'ans'); self.assertEqual(g('task'), 'ml-core')
        guided = [e for e in self.events(pg) if e['type'] == 'guided']
        self.assertEqual([(e['step'], e['assist_level'], e['source']) for e in guided],
                         [('lesson', 'prereq_lesson', 'deterministic'), ('check', 'prereq_check', 'deterministic'), ('check', 'prereq_check', 'deterministic')])
        self.assertTrue(all(e['task'] == 'ml-core' and e['lesson'] == 'prereq/sigmoid-derivative' for e in guided))
        # external-model bridge: compact brief with gap and lesson; labelled; no evidence key; logged as tutor help
        pg.locator('.wb-tutor summary').click()
        self.assertIn('nicht offline', pg.inner_text('.wb-tutor [data-external]'))
        pg.click('#tutor-brief'); brief = pg.inner_text('#tutor-brief-out')
        self.assertIn('Du bist mein Tutor', brief); self.assertIn('Vermutete Lücke', brief)
        self.assertIn('Bereits gezeigte Voraussetzungs-Lektion: Ableitung der Sigmoidfunktion', brief)
        self.assertIn('NUR für den Tutor', brief)                                   # practice task after own attempts
        self.assertEqual(G.leaks(ML, engine_part(brief)), [])
        tut = [e for e in self.events(pg) if e['type'] == 'tutor'][-1]
        self.assertEqual((tut['assist_level'], tut['source'], tut['channel']), ('tutor', 'agent_judgement', 'copy'))
        pg.fill('#ans', 'delta_o*v1*fp1*x1'); pg.click('#check')
        self.assertEqual((g('result'), g('rule')), ('correct', 'RF'))              # solved with help -> similar task next
        self.assertEqual(pg.get_attribute('[data-kc="ml/backpropagation"]', 'data-status'), 'ASSISTED')
        self.assertEqual(self.requests, []); self.assertEqual(self.errors, [])

    def test_attention_ladder_scaling_gap_and_explicit_solution(self):
        pg = self.open('l/ai__attention-track.html'); g = lambda k: pg.get_attribute('#wb', 'data-' + k)
        pg.fill('#ans', str(T(ATT, 'att-pre')['expected']).replace('.', ',')); pg.click('#check'); pg.click('#next')
        self.assertEqual(g('task'), 'att-core')
        labels = []
        for _ in range(3):
            labels.append(pg.inner_text('#hint')); pg.click('#hint')
        self.assertEqual(labels, ['Hinweis 1/3 · Orientierung', 'Hinweis 2/3 · Strategie', 'Hinweis 3/3 · Konkreter Schritt'])
        self.assertTrue(pg.locator('#hint').is_disabled())
        hints = [e for e in self.events(pg) if e['type'] == 'hint']
        self.assertEqual([(e['ladder'], e['assist_level'], e['before_attempt']) for e in hints],
                         [('orientation', 'hint_1', True), ('strategy', 'hint_2', True), ('step', 'hint_bottom_out', True)])
        unscaled = next(e['value'] for e in T(ATT, 'att-core')['errors'] if e['category'] == 'missing_scaling')
        pg.fill('#ans', repr(unscaled)); pg.click('#check')
        self.assertIn('√d_k', pg.inner_text('#guide-offer')); pg.click('#guide-learn')
        pg.check('#guide-ch1'); pg.click('#guide-check'); self.assertIn('Varianz', pg.inner_text('#guide-fb'))   # 25: by d_k
        pg.check('#guide-ch0'); pg.click('#guide-check'); self.assertEqual(pg.get_attribute('.wb-lesson', 'data-check'), 'correct')
        pg.click('#guide-back')
        self.assertTrue(pg.locator('.wb-solution').is_hidden())
        pg.click('#sol')                                                             # explicit request only
        self.assertTrue(pg.locator('.wb-solution').is_visible())
        sol = [e for e in self.events(pg) if e['type'] == 'solution']
        self.assertEqual([(e['assist_level'], e['source']) for e in sol], [('solution_seen', 'deterministic')])
        pg.fill('#ans', str(T(ATT, 'att-core')['expected'])); pg.click('#check')
        self.assertEqual((g('result'), g('rule')), ('correct', 'RF'))
        self.assertEqual(pg.get_attribute('[data-kc="attention/scaled-weights"]', 'data-status'), 'ASSISTED')
        self.assertEqual(self.requests, []); self.assertEqual(self.errors, [])

    def test_retest_and_evidence_items_never_show_keys(self):
        t0 = '2026-11-01T09:00:00Z'
        done = [attempt(ML, tid, TR._answer_for(T(ML, tid)) if T(ML, tid)['type'] != 'steps' else {s['id']: repr(s['expected']) for s in T(ML, tid)['steps']}, t0) for tid in ML['flow']]
        pg = self.open('l/ml__backprop-track.html', done)
        self.assertEqual(pg.get_attribute('#wb', 'data-task'), 'ml-retest')
        rt = T(ML, 'ml-retest')
        self.assertEqual(pg.locator('#sol').count(), 0); self.assertEqual(pg.locator('#hint').count(), 0)
        self.assertNotIn(rt['solution'][0], pg.inner_text('main'))   # page data holds it for offline checking; never displayed
        pg.click('#guide-stuck')                                                     # teaches the prerequisite, not the item
        self.assertEqual(pg.locator('.wb-lesson').count(), 1)
        self.assertEqual(G.leaks(ML, pg.inner_text('#guide')), [])
        pg.locator('.wb-tutor summary').click(); pg.click('#tutor-brief'); brief = pg.inner_text('#tutor-brief-out')
        self.assertIn('zurückgehalten', brief); self.assertNotIn(rt['prompt'], brief)
        self.assertNotIn(rt['expected_expr'], brief); self.assertNotIn(rt['solution'][0], brief); self.assertNotIn('NUR für den Tutor', brief)
        self.assertEqual(G.leaks(ML, engine_part(brief)), [])
        # the item counts as assisted now
        pg.fill('#ans', rt['expected_expr']); pg.click('#check')
        ev = pg.evaluate('EMT.store.events(EMT.storeKey)'); i = max(k for k, e in enumerate(ev) if e['type'] == 'attempt')
        self.assertTrue(pg.evaluate('([tr,ev,i]) => EMT.assisted(tr,ev,i)', [ML, ev, i]))
        # similar (evidence role): keyless brief
        pg2 = self.open('l/ml__backprop-track.html', [attempt(ML, 'ml-pre', '0,24'), {'type': 'hint', 'task': 'ml-core', 'level': 1, 't': NOW}, attempt(ML, 'ml-core', 'delta_o*v1*fp1*x1')])
        self.assertEqual(pg2.get_attribute('#wb', 'data-task'), 'ml-similar')
        pg2.fill('#ans', 'delta_o*v2*x2'); pg2.click('#check')
        pg2.locator('.wb-tutor summary').click(); pg2.click('#tutor-brief'); b2 = pg2.inner_text('#tutor-brief-out')
        self.assertIn('Keine Musterlösung im Paket', b2); self.assertNotIn(T(ML, 'ml-similar')['solution'][0], b2)
        self.assertEqual(self.requests, []); self.assertEqual(self.errors, [])

    def test_local_endpoint_is_opt_in_loopback_and_unverified(self):
        pg = self.open('l/ml__backprop-track.html')
        pg.locator('.wb-tutor summary').click()
        self.assertTrue(pg.locator('#tutor-local').is_hidden())                    # off by default
        self.assertFalse(pg.evaluate('EMT.guided.localEndpointOk("https://api.openai.com/v1/chat/completions")'))
        self.assertFalse(pg.evaluate('EMT.guided.localEndpointOk("http://user:pw@127.0.0.1:8/x")'))
        pg.click('#llm-toggle')
        pg.check('#llm-on'); pg.fill('#llm-url', 'https://api.openai.com/v1/chat/completions'); pg.click('#llm-save')
        self.assertIn('127.0.0.1', pg.inner_text('#llm-status')); self.assertTrue(pg.locator('#tutor-local').is_hidden())
        seen = []
        pg.route('http://127.0.0.1:11434/**', lambda route: (seen.append(json.loads(route.request.post_data)), route.fulfill(
            status=200, headers={'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json'},
            body=json.dumps({'choices': [{'message': {'content': '[HINT 1/3] Welcher Faktor gehört zum Schritt von z₁ nach a₁?'}}]}))))
        pg.fill('#llm-url', 'http://127.0.0.1:11434/v1/chat/completions'); pg.click('#llm-save')
        self.assertTrue(pg.locator('#tutor-local').is_visible())
        pg.click('#tutor-local'); pg.wait_for_selector('#tutor-local-out .wb-badge')
        out = pg.inner_text('#tutor-local-out')
        self.assertIn('FEEDBACK_UNVERIFIED', out); self.assertIn('[HINT 1/3]', out)
        self.assertIn('Du bist mein Tutor', seen[0]['messages'][0]['content'])
        tut = [e for e in self.events(pg) if e['type'] == 'tutor'][-1]
        self.assertEqual((tut['channel'], tut['source']), ('local_endpoint', 'agent_judgement'))
        self.assertTrue(all(u.startswith('http://127.0.0.1:11434/') for u in self.requests), self.requests)
        self.assertNotIn('attempt', [e['type'] for e in self.events(pg)])          # a model reply never becomes an attempt
        self.assertEqual(self.errors, [])

    def test_explorable_task_teaches_prerequisite(self):
        pg = self.open('i.html')
        a = pg.locator('.assessment[data-task-id="task/backprop-numeric"]')
        self.assertEqual(a.locator('.guide-chip').all_inner_texts(), ['Softmax: aus Scores werden Gewichte', 'Ableitung einer Softmax-Zeile'])
        a.locator('textarea').fill('0,280058'); a.locator('.submit-attempt').click()      # normaliser ignored
        self.assertIn('Ableitung einer Softmax-Zeile', a.locator('.guide-offer').inner_text())
        a.locator('.guide-learn').click()
        a.locator('#guide-task-backprop-numeric-ans').fill('0'); a.locator('#guide-task-backprop-numeric-check').click()
        self.assertIn('gemeinsamen Nenner', a.locator('.wb-lesson-fb').inner_text())
        a.locator('#guide-task-backprop-numeric-ans').fill('-0,18'); a.locator('#guide-task-backprop-numeric-check').click()
        self.assertEqual(a.locator('.wb-lesson').get_attribute('data-check'), 'correct')
        self.assertEqual(a.locator('.wb-lesson-src a').first.get_attribute('href'), '#teaching-teach-gradient')
        a.locator('#guide-task-backprop-numeric-back').click()
        self.assertIn('retry-attempt', pg.evaluate('document.activeElement.className'))
        # the worked misconception example contains the corrected number: opening it is help too
        a.locator('.misconception-example details summary').click()
        pg.wait_for_function("JSON.parse(localStorage.getItem('em-practice-v1')).units[" + json.dumps(UNIT['unit_id']) + "].events.length === 3")
        rec = json.loads(pg.evaluate("localStorage.getItem('em-practice-v1')"))['units'][UNIT['unit_id']]
        self.assertEqual([e['type'] for e in rec['events']], ['attempt', 'guided_help', 'guided_help'])
        s = summarize({'schema': 'em-practice-evidence-v1', 'unit_id': UNIT['unit_id'], 'assessment_revision': assessment_revision(UNIT), 'events': rec['events']}, UNIT)
        self.assertEqual(s['assessments']['task/backprop-numeric']['guided_helps'], 2)
        self.assertEqual([(e['type'], e.get('step')) for e in rec['policy']][:4], [('attempt', None), ('guided', 'lesson'), ('guided', 'check'), ('guided', 'check')])
        # brief of this practice task: gap + lesson shown; transfer task brief stays keyless
        a.locator('.tutor-panel summary').click(); a.locator('.tutor-button').click()
        tb = a.locator('.tutor-brief').inner_text()
        self.assertIn('Bereits gezeigte Voraussetzungs-Lektion: Ableitung einer Softmax-Zeile', tb); self.assertIn('Vermutete Lücke', tb)
        tr = pg.locator('.assessment[data-task-id="task/complexity"]')
        tr.locator('textarea').fill('1000'); tr.locator('.submit-attempt').click()
        tr.locator('.tutor-panel summary').click(); tr.locator('.tutor-button').click()
        b = tr.locator('.tutor-brief').inner_text(); task = next(x for x in UNIT['assessments'] if x['id'] == 'task/complexity')
        self.assertIn('Keine Musterlösung im Paket', b); self.assertNotIn(task['solution'][:60], b)
        self.assertEqual(self.requests, []); self.assertEqual(self.errors, [])


if __name__ == '__main__':
    unittest.main()
