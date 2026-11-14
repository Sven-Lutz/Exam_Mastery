"""B19 (v0.19): adaptive learning inside the regular chapter, stage design, evidence labels, negative cases.
The chapter fixture is a published learning environment built from the engine's own fixture book (no course data)."""
import json
import re
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from exam_mastery import learn_app
from exam_mastery.labs import build as B
from exam_mastery.labs import models as M
from exam_mastery.learning import diagnose as D, render, tracks as TR

ENT = TR.all_tracks()[1]


def chapter_fixture(root):
    """A minimal published chapter whose competencies include the finance track's ids (fixture text, not course content)."""
    kc = ENT['kcs'][1]['id']
    model = {'schema': learn_app.SCHEMA, 'course': 'Fixture-Kurs', 'chapter': {'id': 'ch-fix', 'title': 'Liquidität (Fixture)', 'no': 1, 'status': '**Status:** Fixture'},
             'kcs': {kc: 'Finanzierungsbedarf bestimmen'},
             'sections': [{'id': 's1', 'no': '1.1', 'title': 'Finanzplan', 'kc_ids': [kc], 'parts': [{'html': '<p>Fixture-Text.</p>', 'kc_ids': [kc], 'type': 'p'}],
                           'items': [], 'labs': [], 'sources': ['Fixture'], 'cards': []}],
             'labs': [], 'cards': [], 'items': [], 'exam': {'items': [], 'total_points': 0, 'subtitle': ''}, 'materials': [], 'anki': None}
    src = Path(root) / 'v1' / 'Lernumgebung'; src.mkdir(parents=True)
    (src / 'index.html').write_text(learn_app.page(model, 'Fixture · Lernumgebung'), encoding='utf-8')
    (src / 'labs').mkdir()
    s = B.cashflow_spec('ent/cashflow-liquidity', 'Liquidität', [kc], ['Fixture'], **{k: ENT['context']['data'][k] for k in ('orders', 'delay', 'cost', 'invest')})
    (src / 'labs' / 'ent__cashflow-liquidity.json').write_text(json.dumps(s, ensure_ascii=False), encoding='utf-8')
    return src, model


class Republish(unittest.TestCase):
    def test_republish_keeps_content_and_adds_only_matching_tracks(self):
        with tempfile.TemporaryDirectory() as td:
            src, model = chapter_fixture(td)
            out = Path(td) / 'v2' / 'Lernumgebung'
            r = learn_app.republish(src, out, TR.all_tracks())
            self.assertEqual(r['model_calls'], 0); self.assertEqual(r['tracks'], ['lernstrecken/ent__liquidity-track.html'])
            new = json.loads(re.search(r'id="em-course">(.*?)</script>', (out / 'index.html').read_text(encoding='utf-8'), re.S).group(1))
            self.assertEqual(new['sections'], model['sections']); self.assertEqual(new['items'], model['items'])
            self.assertEqual([t['id'] for t in new['tracks']], ['ent/liquidity-track'])
            self.assertTrue((src / 'index.html').exists())   # source untouched
            page = (out / 'lernstrecken' / 'ent__liquidity-track.html').read_text(encoding='utf-8')
            self.assertNotIn('"store_ctx"', page)   # chapter history uses the plain key the progress view reads

    def test_reference_tracks_use_their_own_storage_namespace(self):
        with tempfile.TemporaryDirectory() as td:
            p = render.write(ENT, td, context='referenz')
            self.assertIn('"store_ctx": "referenz"', p.read_text(encoding='utf-8'))


class Evidence(unittest.TestCase):
    def test_domain_check(self):
        t = next(x for x in TR.all_tracks()[0]['tasks'] if x['id'] == 'ml-core')
        d = D.diagnose(t, 'delta_o*v1*fp1*x1/(x1-x1)')
        self.assertEqual(d['result'], 'invalid'); self.assertIn('nicht definiert', d['detail'])


class Browser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.td = tempfile.TemporaryDirectory(); src, _ = chapter_fixture(cls.td.name)
        cls.out = Path(cls.td.name) / 'v2' / 'Lernumgebung'; learn_app.republish(src, cls.out, TR.all_tracks())
        cls.ref = Path(cls.td.name) / 'ref'; render.write(TR.all_tracks()[0], cls.ref, context='referenz'); B.render(B.mlp_spec(), cls.ref / 'labs', context='referenz')
        cls.pw = sync_playwright().start(); cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.pw.stop(); cls.td.cleanup()

    def ctx(self, **kw):
        c = self.browser.new_context(**kw); self.errors = []; self.reqs = []; return c

    def page(self, c, url):
        pg = c.new_page(); pg.on('pageerror', lambda e: self.errors.append(str(e)))
        pg.on('request', lambda r: self.reqs.append(r.url) if not r.url.startswith(('file:', 'data:', 'blob:', 'about:')) else None)
        pg.goto(url); return pg

    def track_frame(self, pg):
        pg.wait_for_selector('iframe[data-track]')
        f = next(f for f in pg.frames if 'ent__liquidity-track' in f.url); f.wait_for_selector('html[data-em-ready="1"]', state='attached'); return f

    def test_full_learning_flow_inside_the_chapter(self):
        """Section 14: concept opened -> prerequisite checked -> plausible error -> error type -> mechanism -> focused
        visual -> new task without help -> transfer -> stored state -> later retrieval offered."""
        c = self.ctx(); pg = self.page(c, (self.out / 'index.html').as_uri() + '#/lernen/s1')
        f = self.track_frame(pg); g = lambda k: f.get_attribute('#wb', 'data-' + k)
        self.assertEqual(g('task'), 'cf-pre')
        f.fill('#ans', '90'); f.click('#check'); self.assertEqual((g('rule'), g('category')), ('RA', 'period_vs_cumulative'))
        self.assertEqual(f.locator('[data-support=worked_example]').count(), 1)
        f.click('#next'); f.fill('#ans', '-50'); f.click('#check'); self.assertEqual(g('rule'), 'RP'); f.click('#next')
        f.fill('#ans', '2136'); f.click('#check'); self.assertEqual((g('rule'), g('category')), ('RC1', 'end_balance_vs_minimum'))
        self.assertEqual(f.locator('.wb-trough').count(), 1); self.assertIn('Bedarf = ?', f.inner_text('.wb-figure'))
        self.assertIn('Numerisch geprüft', f.inner_text('.wb-evid'))
        self.assertIn('Finanzierungsbedarf nicht der Endsaldo', f.inner_text('.wb-card'))   # the actual review card, not just a tag
        f.fill('#ans', str(T(ENT, 'cf-core')['expected'])); f.click('#check'); self.assertEqual((g('result'), g('rule')), ('correct', 'RD'))
        f.click('#next'); self.assertEqual(g('task'), 'cf-transfer'); self.assertEqual(f.locator('#hint').count(), 1)
        f.fill('#ans', str(T(ENT, 'cf-transfer')['expected'])); f.click('#check'); self.assertEqual(g('result'), 'correct')
        # stored and visible in the chapter's progress view
        pg.goto((self.out / 'index.html').as_uri() + '#/stand'); pg.wait_for_timeout(300)
        txt = pg.inner_text('main'); self.assertIn('Lernstrecke: ' + ENT['title'], txt); self.assertIn('heute ohne Hilfe gelöst', txt)
        self.assertNotRegex(txt.split('Lernstrecke:')[1][:400], r'\d+ ?%')
        # later retrieval: the same history two days later offers the retest, without hints or solution shown
        pg.goto((self.out / 'index.html').as_uri() + '#/lernen/s1'); f = self.track_frame(pg)
        ev = f.evaluate("EMT.store.events('ent/liquidity-track')")
        old = (datetime.now(timezone.utc) - timedelta(days=2)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        for e in ev: e['t'] = old
        f.evaluate("ev => { const d = EMT.store.read(); d.tracks['ent/liquidity-track'].events = ev; EMT.store.write(d); }", ev)
        pg.reload(); f = self.track_frame(pg)
        self.assertEqual(f.get_attribute('[data-kc="' + ENT['kcs'][1]['id'] + '"]', 'data-status'), 'RETEST_DUE')
        self.assertEqual(f.get_attribute('#wb', 'data-task'), 'cf-harder')   # unsolved flow task first; retest stays available
        self.assertEqual(self.errors, []); self.assertEqual(self.reqs, [])

    def test_negative_cases(self):
        c = self.ctx(); pg = self.page(c, (self.out / 'lernstrecken' / 'ent__liquidity-track.html').as_uri())
        pg.wait_for_selector('html[data-em-ready="1"]', state='attached'); g = lambda k: pg.get_attribute('#wb', 'data-' + k)
        pg.fill('#ans', '-90'); pg.click('#check'); pg.click('#next')
        # unknown cause: no category claimed
        pg.fill('#ans', '1234'); pg.click('#check'); self.assertEqual((g('category'), g('rule')), ('unclassified', 'RU'))
        self.assertIn('Ursache unbekannt', pg.inner_text('.wb-evid'))
        # solution seen, then correct: counted as assisted, never as independent
        pg.click('#sol'); pg.fill('#ans', str(T(ENT, 'cf-core')['expected'])); pg.click('#check')
        self.assertEqual(g('rule'), 'RF')
        self.assertEqual(pg.get_attribute('[data-kc="' + ENT['kcs'][1]['id'] + '"]', 'data-status'), 'ASSISTED')
        # open answer stays unverified
        st = pg.evaluate("t => EMT.diagnose(t, 'Weil vorher Geld fehlt.')", T(ENT, 'cf-why'))
        self.assertEqual((st['result'], st['evidence']), ('unverified', 'UNVERIFIED'))
        self.assertEqual(self.errors, [])

    def test_expression_evidence_is_not_called_symbolic(self):
        c = self.ctx(); pg = self.page(c, (self.ref / 'ml__backprop-track.html').as_uri()); pg.wait_for_selector('html[data-em-ready="1"]', state='attached')
        pg.fill('#ans', '0,24'); pg.click('#check'); pg.click('#next'); pg.fill('#ans', 'delta_o*v1*a1*(1-a1)'); pg.click('#check')
        t = pg.inner_text('.wb-evid'); self.assertIn('kein symbolischer Beweis', t); self.assertIn('Bekannter Fehler', t)
        self.assertEqual(pg.locator('.wb-figure.ds-stage .wb-edge.miss').count(), 1)

    def test_stage_design_and_dark_mode(self):
        for scheme in ('light', 'dark'):
            c = self.ctx(color_scheme=scheme, viewport={'width': 390, 'height': 844}); pg = self.page(c, (self.ref / 'ml__backprop-track.html').as_uri())
            pg.wait_for_selector('html[data-em-ready="1"]', state='attached')
            bg = pg.evaluate("getComputedStyle(document.querySelector('.wb-figure')).backgroundColor")
            self.assertIn(bg, ('rgb(17, 25, 35)', 'rgb(14, 21, 30)'))   # the stage is dark in both modes
            self.assertLessEqual(pg.evaluate('document.documentElement.scrollWidth'), 391)
            small = pg.evaluate("[...document.querySelectorAll('svg text')].filter(t => parseFloat(getComputedStyle(t).fontSize) < 12).length")
            self.assertEqual(small, 0)

    def test_lab_guided_step_and_explore_check(self):
        c = self.ctx(viewport={'width': 1440, 'height': 900}); pg = self.page(c, (self.ref / 'labs' / 'ml__backprop-2-2-1.html').as_uri())
        pg.wait_for_selector('html[data-em-ready="1"]', state='attached'); pg.locator('text=Ohne Vorhersage erkunden').first.click()
        p = B.mlp_spec()['model']; q, _ = M.mlp_step(p['init'], p['x'], p['target'], p['lr'])
        pg.click('.em-guided .em-primary')
        self.assertIn(B._fmt(q['W1'][0][0], 4), pg.inner_text('.em-gstep'))   # before -> after of w11, from the same model
        pg.click('.em-modeb[data-m=explore]')
        self.assertLess(float(pg.get_attribute('.em-lab', 'data-fd-max-dev')), 1e-6)
        self.assertEqual(self.errors, [])


def T(tr, tid):
    return next(t for t in tr['tasks'] if t['id'] == tid)


if __name__ == '__main__':
    unittest.main()
