"""Fachübergreifende Modulschicht (Issue #9): Vertrag, Quellenregeln, Tutor-Export, API-Sperre, Rechenkerne, gerenderte Labore."""
import base64
import math
import json
import random
import shutil
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction as Fr
from pathlib import Path

from exam_mastery.modules import contract as C, sources as S, tutor as TU, tutor_adapter as TA
from exam_mastery.modules.__main__ import build, from_unit

ROOT = Path(__file__).resolve().parents[1]
MODS = {'analysis1_folgen': ROOT / 'modules/analysis1_folgen', 'ent_funding': ROOT / 'modules/ent_funding'}
HAVE_NODE = shutil.which('node') is not None


def node(js_file, expr_calls):
    prog = (f"const M=require({json.dumps(str(js_file))});const C={json.dumps(expr_calls)};"
            "process.stdout.write(JSON.stringify(C.map(([f,a])=>{const g=f.split('.').reduce((o,k)=>o[k],M);return g(...a)})))")
    return json.loads(subprocess.run(['node', '-e', prog], capture_output=True, text=True, check=True).stdout)


class Contract(unittest.TestCase):
    def test_both_contrasting_modules_validate_and_pass_automatic_qc(self):
        for name, d in MODS.items():
            m = C.load(d)
            self.assertEqual(C.validate(m), [], name)
            self.assertEqual(S.validate(m['_sources']), [], name)
            with tempfile.TemporaryDirectory() as t:
                q = build(m, Path(t), None)
            dims = {k: v['status'] for k, v in q['dimensions'].items()}
            for k in ('scope', 'source_validity', 'computation', 'examples', 'tasks', 'lab', 'tutor', 'channels'):
                self.assertEqual(dims[k], 'PASS', (name, k, q['dimensions'][k]))
            self.assertEqual(dims['human_review'], 'PENDING')
            self.assertEqual(dims['didactic_quality'], 'NOT_RATED')
            self.assertEqual(dims['proof_correctness'], 'NOT_VERIFIED')          # nie automatisch PASS
            self.assertIn('NICHT geprüft', q['dimensions']['computation']['evidence'])
            gaps = S.gaps(m)
            self.assertEqual(dims['literature_coverage'], 'FAIL' if gaps else 'PASS', name)

    def test_domains_differ_but_schema_is_identical(self):
        ms = [C.load(d) for d in MODS.values()]
        self.assertEqual({m['domain'] for m in ms}, {'mathematics', 'business'})
        self.assertNotEqual(C.METHODS['mathematics'], C.METHODS['business'])

    def test_contract_rejects_self_assessment_and_missing_parts(self):
        m = C.load(MODS['analysis1_folgen'])
        bad = json.loads(json.dumps({k: v for k, v in m.items()}))
        bad['tasks'][0]['self_assessment'] = True
        bad['tasks'][1].pop('worked')
        bad['kcs'][0]['prerequisites'].append('gibt-es-nicht')
        e = C.validate(bad)
        self.assertTrue(any('self-assessment' in x for x in e) and any('missing worked' in x for x in e) and any('unknown prerequisite' in x for x in e))

    def test_nlp_reference_unit_maps_onto_same_contract(self):
        m = from_unit(ROOT / 'units/nlp_sequence_labeling')
        self.assertEqual(C.validate(m), [])
        self.assertTrue(all(c['ok'] for c in C.run_checks(m)))


class Coverage(unittest.TestCase):
    def test_coverage_requires_passage_for_the_kc_not_just_a_listed_source(self):
        m = C.load(MODS['analysis1_folgen'])
        for s in m['_sources']:
            for p in s.get('passages', []):
                p['kcs'] = [k for k in p.get('kcs', []) if k != 'grenzw']
        self.assertIn('grenzw', [g['kc'] for g in S.gaps(m)])
        self.assertEqual(C.qc(m)['dimensions']['literature_coverage']['status'], 'FAIL')

    def test_ent_formen_gap_is_reported_not_hidden(self):
        self.assertEqual([g['kc'] for g in S.gaps(C.load(MODS['ent_funding']))], ['formen'])


class ResearchTrail(unittest.TestCase):
    def test_every_logged_verification_is_complete_and_linked(self):
        from exam_mastery.modules import research as R
        for d in list(MODS.values()) + [ROOT / 'units/nlp_sequence_labeling']:
            ev = R.read_log(d)
            self.assertTrue(ev, d)
            for e in ev:
                if e['step'] == 'verify':
                    self.assertTrue(e['result']['all_found'], (d, e['source']))
                    self.assertEqual(len(e['result']['sha256']), 64)
                    for p in e['result']['phrases']:
                        self.assertLessEqual(len(p['context'] or ''), 240)       # nur kurze Zitate im Repo
            steps = [e['step'] for e in ev]
            self.assertLess(steps.index('need'), steps.index('verify'))
        ent = C.load(MODS['ent_funding']); ids = {s['id'] for s in ent['_sources'] if s['status'] == 'verified'}
        for e in R.read_log(MODS['ent_funding']):
            if e['step'] in ('verify', 'decide', 'integrate'):
                self.assertIn(e['source'], ids)
        self.assertIn('Kerr', R.trace(MODS['ent_funding'], ent) + json.dumps(ent['_sources']))

    def test_nlp_registry_has_verified_urls_for_lafferty_and_su(self):
        u = json.loads((ROOT / 'units/nlp_sequence_labeling/unit.json').read_text(encoding='utf-8'))
        src = {s['id']: s for s in u['sources']}
        self.assertEqual(src['lafferty']['url'], 'https://repository.upenn.edu/cis_papers/159')
        self.assertEqual(src['su']['url'], 'https://arxiv.org/abs/2104.09864')
        self.assertIn('nicht geprüft', src['su']['ref'])


class ContractionCertificate(unittest.TestCase):
    """Zertifikat darf nie „bewiesen“ melden, wenn eine dichte Abtastung (unabhängig, Python) eine Bedingung verletzt."""
    MAPS = {'cos': (math.cos, lambda x: -math.sin(x)), 'lect': (lambda x: 1 / (3 + x), lambda x: -1 / (3 + x) ** 2),
            'sqrt': (lambda x: math.sqrt(3 + 2 * x), lambda x: 1 / math.sqrt(3 + 2 * x)), 'heron': (lambda x: (x + 2 / x) / 2, lambda x: (1 - 2 / x ** 2) / 2),
            'xinv': (lambda x: x + 1 / x, lambda x: 1 - 1 / x ** 2)}

    @unittest.skipUnless(HAVE_NODE, 'node fehlt')
    def test_certificate_sound_against_dense_sampling(self):
        js = ROOT / 'modules/analysis1_folgen/lab/analysis_math.js'
        rng = random.Random(4); cases = []
        for _ in range(300):
            k = rng.choice(list(self.MAPS)); a = round(rng.uniform(-0.5, 4), 2); b = round(a + rng.uniform(0.05, 3), 2)
            cases.append((k, a, b))
        res = node(js, [('certificate', list(c)) for c in cases])
        proven = 0
        for (k, a, b), r in zip(cases, res):
            if not r['ok']:
                continue
            proven += 1
            fn, d = self.MAPS[k]
            xs = [a + (b - a) * i / 2000 for i in range(2001)]
            self.assertTrue(all(a <= fn(x) <= b for x in xs), (k, a, b))
            self.assertLess(max(abs(d(x)) for x in xs), 1, (k, a, b))
            self.assertLessEqual(max(abs(d(x)) for x in xs), r['q'] + 1e-9, (k, a, b))
        self.assertGreater(proven, 10)
        r = node(js, [('certificate', ['cos', 0.5, 1]), ('certificate', ['xinv', 1, 20]), ('certificate', ['cos', -1, 1])])
        self.assertTrue(r[0]['ok']); self.assertFalse(r[1]['ok']); self.assertFalse(r[2]['ok'])


class SourceRules(unittest.TestCase):
    base = {'id': 'x', 'tier': 'extension', 'type': 'paper', 'status': 'verified', 'access_level': 'section', 'citation': 'c', 'url': 'https://example.org',
            'checked_on': '2026-11-15', 'passages': [{'locator': 'S. 1', 'content': 'gelesen'}], 'used_for': ['claim'], 'limits': 'l', 'function': 'f'}

    def check(self, **kw):
        return S.validate([dict(self.base, **kw)])

    def test_rules(self):
        self.assertEqual(self.check(), [])
        self.assertTrue(any('claims need full text' in e for e in self.check(access_level='abstract')))
        self.assertEqual(self.check(access_level='abstract', used_for=['context']), [])
        self.assertTrue(any('without read passage' in e for e in self.check(passages=[])))
        self.assertTrue(any('must not be used' in e for e in self.check(status='unverified')))
        self.assertTrue(any('public URL' in e for e in self.check(access_level='private_course_material')))
        self.assertTrue(any('creator' in e for e in self.check(type='video')))
        self.assertTrue(any('timestamps' in e for e in self.check(timestamps=['03:10'])))

    def test_unverified_candidates_are_never_cited_by_a_kc(self):
        for d in MODS.values():
            m = C.load(d)
            unv = {s['id'] for s in m['_sources'] if s['status'] != 'verified'}
            self.assertTrue(unv, 'Kandidaten werden dokumentiert, nicht verschwiegen')
            for k in m['kcs']:
                self.assertFalse(set(k['sources']) & unv, k['id'])

    def test_plan_is_domain_adapted_and_offline(self):
        a, b = (S.plan(C.load(d)) for d in MODS.values())
        self.assertIn('theorem', ' '.join(a['items'][0]['queries']))
        self.assertIn('journal of finance', ' '.join(q for i in b['items'] for q in i['queries']))
        self.assertIn('keine Netz', a['note'])


class Tutor(unittest.TestCase):
    def test_export_without_learner_state_invents_nothing_and_hides_keys(self):
        m = C.load(MODS['ent_funding'])
        with tempfile.TemporaryDirectory() as t:
            r = TU.build(m, Path(t))
            ctx = (Path(t) / 'tutor/tutor_context.md').read_text(encoding='utf-8')
            self.assertEqual(r['answer_leak'], [])
            self.assertIn('Kein Lernstand erhoben', ctx)
            for task in m['tasks']:
                self.assertNotIn(task['worked'][:60], ctx)
            self.assertIn('in Projekten nicht verfügbar', (Path(t) / 'tutor/README.md').read_text(encoding='utf-8'))
            self.assertIsNone(json.loads((Path(t) / 'tutor/tutor_context.json').read_text(encoding='utf-8'))['learner_state'])

    def test_real_learner_state_is_summarised_exactly(self):
        m = C.load(MODS['analysis1_folgen'])
        state = {'module': m['id'], 'exported': '2026-11-15T10:00:00Z', 'attempts': [
            {'task': 'AN1', 'kc': 'konv', 'correct': True, 'hints': 0, 'revealed': False}, {'task': 'AN2', 'kc': 'monoton', 'correct': False, 'hints': 2, 'revealed': False}], 'exams': []}
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / 'lernstand.json'; p.write_text(json.dumps(state), encoding='utf-8')
            TU.build(m, Path(t), p)
            ctx = json.loads((Path(t) / 'tutor/tutor_context.json').read_text(encoding='utf-8'))['learner_state']
        self.assertEqual(ctx['per_kc']['konv'], {'attempts': 1, 'correct_unaided': 1, 'with_help': 0, 'errors': []})
        self.assertEqual(ctx['per_kc']['monoton']['errors'], ['AN2'])

    def test_tutor_context_has_no_local_paths(self):
        m = from_unit(ROOT / 'units/nlp_sequence_labeling')
        with tempfile.TemporaryDirectory() as t:
            TU.build(m, Path(t))
            for f in (Path(t) / 'tutor').iterdir():
                self.assertNotIn(str(Path.home()), f.read_text(encoding='utf-8'), f.name)

    def test_shared_instruction_is_module_independent(self):
        txt = TU.SHARED.read_text(encoding='utf-8')
        for word in ('NLP', 'Analysis', 'Attention', 'Start-up', 'Folge'):
            self.assertNotIn(word, txt)
        self.assertLess(len(txt), 4000)

    def test_api_adapter_is_closed_without_consent_budget_and_provider(self):
        calls = []
        p = TA.Policy()
        with self.assertRaises(TA.TutorAPIDisabled):
            TA.ask(p, 'x', {}, 'hi')
        p = TA.Policy(opt_in=True, budget_calls=0)
        with self.assertRaises(TA.TutorAPIDisabled):
            TA.ask(p, 'x', {}, 'hi')
        self.assertEqual(TA.Policy.from_next_action(ROOT / 'NEXT_ACTION.json').budget_calls, 0)
        p = TA.Policy(opt_in=True, budget_calls=1, providers={'fake': lambda msgs: calls.append(msgs) or 'ok'})
        self.assertEqual(TA.ask(p, 'fake', {'learner_state': {'x': 1}}, 'hi'), 'ok')
        self.assertIn('"learner_state": null', calls[0][0]['content'])            # Lernstand nur mit eigener Zustimmung
        with self.assertRaises(TA.TutorAPIDisabled):
            TA.ask(p, 'fake', {}, 'again')


@unittest.skipUnless(HAVE_NODE, 'node fehlt')
class MathCores(unittest.TestCase):
    def test_analysis_minN_matches_exact_fractions(self):
        js = ROOT / 'modules/analysis1_folgen/lab/analysis_math.js'
        eps = [0.5, 0.1, 0.05, 0.01, 0.003, 0.001]
        res = node(js, [('minN', ['rational', 2, e]) for e in eps] + [('minN', ['alt', 0, e]) for e in eps])
        for e, r in zip(eps, res[:6]):
            ef = Fr(e).limit_denominator(10 ** 6)
            N = next(n for n in range(1, 10 ** 5) if all(Fr(7, k + 3) < ef for k in range(n, n + 3)))
            self.assertEqual(r['N'], N, e)
        for e, r in zip(eps, res[6:]):
            ef = Fr(e).limit_denominator(10 ** 6)
            self.assertEqual(r['N'], next(n for n in range(1, 10 ** 5) if Fr(3, n) < ef))
        chk = node(js, [('checkN', ['sign', 0, 0.5, 10]), ('checkN', ['rational', 2, 0.01, 697]), ('checkN', ['rational', 2, 0.01, 698])])
        self.assertFalse(chk[0]['ok']); self.assertFalse(chk[1]['ok']); self.assertEqual(chk[1]['n'], 697)
        self.assertTrue(chk[2]['ok'] and chk[2]['proven'])

    def test_venture_core_matches_independent_fraction_solver(self):
        sys.path.insert(0, str(MODS['ent_funding']))
        import checks as E  # noqa: E402
        js = ROOT / 'modules/ent_funding/lab/venture_math.js'
        rng = random.Random(9)
        cases = []
        for _ in range(60):
            s = dict(E.BASE, safe=rng.choice([0, 250000, 500000, 900000]), cap=rng.choice([3e6, 5e6, 8e6]), disc=rng.choice([0, .1, .2, .3]),
                     pre=rng.choice([3e6, 5e6, 8e6, 12e6]), inv=rng.choice([1e6, 2e6, 4e6]), pool=rng.choice([0, .05, .1, .15]), pre2=rng.choice([6e6, 24e6]), inv2=6e6)
            cases.append(s)
        res = node(js, [('simulate', [{**s, 'disc': float(s['disc']), 'pool': float(s['pool'])}]) for s in cases])
        for s, r in zip(cases, res):
            if 'error' in r:
                continue
            p = E.captable({**s, 'disc': Fr(s['disc']).limit_denominator(100), 'pool': Fr(s['pool']).limit_denominator(100), 'cap': int(s['cap']), 'pre': int(s['pre']), 'inv': int(s['inv'])})
            self.assertEqual(r['r1']['regime'], p['regime'], s)
            self.assertAlmostEqual(r['r1']['price'], float(p['price']), places=9)
            self.assertAlmostEqual(r['founderShare'][3], float(p['founder_share_A']), places=12)
            for st in r['stages']:
                self.assertAlmostEqual(sum(x[1] for x in st['share']), 1.0, places=12)
        f = node(js, [('fund', [{'size': 100e6, 'fee': .02, 'years': 10, 'n': 25, 'own': .15, 'k': 0, 'ew': 0, 'er': 40e6, 'carry': .2}])])[0]
        self.assertAlmostEqual(f['tvpi'], 1.4, places=12)


try:
    from playwright.sync_api import sync_playwright
    HAVE_BROWSER = True
except ImportError:
    HAVE_BROWSER = False


@unittest.skipUnless(HAVE_BROWSER, 'playwright fehlt')
class RenderedLabs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(); cls.out = {}
        for name, d in MODS.items():
            o = Path(cls.tmp.name) / name; build(C.load(d), o, None); cls.out[name] = o
        cls.pw = sync_playwright().start(); cls.b = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.b.close(); cls.pw.stop(); cls.tmp.cleanup()

    def open(self, name, lab, state=None, vw=1300):
        ctx = self.b.new_context(viewport={'width': vw, 'height': 900}); self.addCleanup(ctx.close)
        pg = ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        h = f'#lab={lab}' + ('&s=' + base64.b64encode(json.dumps(state).encode()).decode() if state else '')
        pg.goto((self.out[name] / 'labor.html').as_uri() + h); pg.wait_for_function('document.body.dataset.ready === "1"', timeout=30000)
        self.addCleanup(lambda: self.assertEqual(errs, []))
        return pg

    def state(self, pg):
        m = pg.evaluate('location.hash').split('s=')[1]
        return json.loads(base64.b64decode(m + '=' * (-len(m) % 4)).decode())

    def test_analysis_minimal_N_challenge_and_proof_vs_test(self):
        pg = self.open('analysis1_folgen', 'folgen')
        st = self.state(pg); st.update(logEps=-2, N=698)
        pg2 = self.open('analysis1_folgen', 'folgen', st)
        pg2.get_by_role('tab', name='Challenges').click()
        self.assertEqual(pg2.locator('.chal.solved[data-id="g-minN"]').count(), 1)
        self.assertIn('bewiesen', pg2.locator('p.verdict').inner_text())
        st.update(seq='sinn', a=0, N=200)
        self.assertIn('kein Beweis', self.open('analysis1_folgen', 'folgen', st).locator('p.verdict').inner_text())
        st.update(seq='rational', a=2, N=697)
        self.assertIn('n = 697', self.open('analysis1_folgen', 'folgen', st).locator('p.verdict').inner_text())

    def test_analysis_cobweb_counterexample(self):
        pg = self.open('analysis1_folgen', 'folgen')
        st = self.state(pg); st.update(view='web', map='xinv', a1=1, n=60)
        pg = self.open('analysis1_folgen', 'folgen', st)
        self.assertIn('kein Fixpunkt', pg.locator('.meters').inner_text())

    def test_venture_majority_challenge_and_discount_switch(self):
        pg = self.open('ent_funding', 'runden')
        st = self.state(pg); st.update(cap=20e6, pool=0, pre=40e6, pre2=40e6)
        pg = self.open('ent_funding', 'runden', st)
        pg.get_by_role('tab', name='Challenges').click()
        self.assertEqual(pg.locator('.chal.solved[data-id="w-major"]').count(), 1)
        st = self.state(self.open('ent_funding', 'runden')); st.update(pre=5e6)
        self.assertIn('den Rabatt', self.open('ent_funding', 'runden', st).locator('.formula-live').inner_text())

    def test_contraction_challenge_requires_certificate_not_simulation(self):
        st = self.state(self.open('analysis1_folgen', 'folgen')); st.update(view='web', map='cos', a1=1, n=60, ia=None, ib=None)
        pg = self.open('analysis1_folgen', 'folgen', st); pg.get_by_role('tab', name='Challenges').click()
        self.assertEqual(pg.locator('.chal.solved[data-id="g-contr"]').count(), 0)          # konvergiert numerisch, aber kein Beweis
        self.assertIn('kein Beweis', pg.locator('.lab-stage').inner_text())
        st.update(ia=0.6, ib=0.9)                                                              # a₁ = 1 nicht im Intervall
        pg = self.open('analysis1_folgen', 'folgen', st); pg.get_by_role('tab', name='Challenges').click()
        self.assertEqual(pg.locator('.chal.solved[data-id="g-contr"]').count(), 0)
        st.update(ia=0.5, ib=1)
        pg = self.open('analysis1_folgen', 'folgen', st); pg.get_by_role('tab', name='Challenges').click()
        self.assertEqual(pg.locator('.chal.solved[data-id="g-contr"]').count(), 1)
        self.assertIn('Bewiesen', pg.locator('.lab-stage').inner_text())

    def test_key_event_N698_visible_in_plot(self):
        st = self.state(self.open('analysis1_folgen', 'folgen')); st.update(logEps=-2, N=697, plot='dist')
        svg = self.open('analysis1_folgen', 'folgen', st).locator('.plane svg').first.inner_html()
        self.assertIn('kleinstes N = 698', svg); self.assertIn('Gegenbeispiel n = 697', svg); self.assertIn('Ihr N = 697', svg)

    def test_no_null_or_undefined_text_anywhere(self):
        for name, lab in (('analysis1_folgen', 'folgen'), ('ent_funding', 'runden')):
            pg = self.open(name, lab)
            for tab in ('Entdecken', 'Challenges', 'Hypothese'):
                pg.get_by_role('tab', name=tab).click()
                if tab == 'Challenges':
                    for b in pg.get_by_role('button', name='Hinweis').all():
                        b.click()
                txt = pg.inner_text('body')
                self.assertNotRegex(txt, r'\bnull\b|\bundefined\b|NaN', (name, tab))

    def test_labs_have_no_flashcard_ui_and_fit_mobile(self):
        for name, lab in (('analysis1_folgen', 'folgen'), ('ent_funding', 'runden')):
            pg = self.open(name, lab, vw=390)
            self.assertLessEqual(pg.evaluate('document.documentElement.scrollWidth'), 392, name)
            body = pg.inner_text('body')
            for w in ('Karteikarte', 'fällig', 'Wiederholen', 'Leitner'):
                self.assertNotIn(w, body)


if __name__ == '__main__':
    unittest.main()
