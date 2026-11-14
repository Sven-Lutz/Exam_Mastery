"""B17: shared design system, lab gallery with model-driven previews, plain-language UI, record namespacing.
Browser checks use the real pages (offline, Chromium). Numbers shown by new visual elements are compared with the
Python reference model, like every other number of a scene."""
import json
import re
import tempfile
import unittest
from pathlib import Path

from exam_mastery.labs import build as B
from exam_mastery.labs import scenes as SC

T = Path(B.__file__).resolve().parent.parent / 'templates'
ORD = [0, 100, 180, 190, 210, 230, 250, 270]; COST = [102, 122, 172, 152, 242, 152, 162, 172]; INV = [200, 500, 300, 140]
RAW_ID = re.compile(r'\bkc-[0-9a-f]{6,}\b')


class Static(unittest.TestCase):
    def test_tokens_shared_and_themed(self):
        tok = (T / 'em_tokens.css').read_text()
        for name in ('--font-display', '--fs-0', '--sp-4', '--r-2', '--t-base', '--paper', '--ink', '--accent', '--signal', '--focus', '--ok', '--bad'):
            self.assertIn(name + ':', tok, name)
        self.assertIn('prefers-color-scheme:dark', tok); self.assertIn('[data-theme=dark]', tok)
        with tempfile.TemporaryDirectory() as td:
            h = B.render(B.mlp_spec(), td).read_text()
            self.assertIn('--font-display', h)                     # labs use the shared tokens
        from exam_mastery import learn_app
        self.assertIn("em_tokens.css", Path(learn_app.__file__).read_text())   # and so does the learning environment

    def test_lab_header_has_no_internal_ids_or_versions(self):
        s = B.cashflow_spec('ent/cashflow', 'Liquidität', ['kc-d5d3fd65634ab3'], ['Folie 21'], ORD, 5, COST, INV, course='Test')
        with tempfile.TemporaryDirectory() as td:
            h = B.render(s, td).read_text()
        body = h.split('<div id="em-lab">')[0]
        self.assertIsNone(RAW_ID.search(body)); self.assertNotIn('Version ', body)
        s['kc_labels'] = {'kc-d5d3fd65634ab3': 'Finanzbedarf bestimmen'}
        with tempfile.TemporaryDirectory() as td:
            self.assertIn('Finanzbedarf bestimmen', B.render(s, td).read_text().split('<div id="em-lab">')[0])

    def test_no_inline_style_attributes_in_lab_html(self):   # the CSP pins the stylesheet by hash: inline styles would be blocked
        with tempfile.TemporaryDirectory() as td:
            h = B.render(B.chord_spec(), td).read_text()
        self.assertNotIn(' style="', h.split('<script')[0])

    def test_context_is_written_into_the_page_only_when_given(self):
        with tempfile.TemporaryDirectory() as td:
            a = B.render(B.mlp_spec(), Path(td) / 'a').read_text(); b = B.render(B.mlp_spec(), Path(td) / 'b', context='referenz').read_text()
        self.assertNotIn('"context"', a); self.assertIn('"context": "referenz"', b)


class Browser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise unittest.SkipTest('playwright not installed')
        cls.tmp = tempfile.TemporaryDirectory(); d = Path(cls.tmp.name)
        cls.nn = B.mlp_spec(); cls.ch = B.chord_spec()
        cls.cf = B.cashflow_spec('ent/cashflow', 'Liquidität', ['kc-cf'], ['Folie 21'], ORD, 5, COST, INV, course='Test')
        items = []
        for s in (cls.nn, cls.ch, cls.cf):
            p = B.render(s, d / 'labs', context='referenz')
            items.append({'spec': s, 'href': 'labs/' + p.name})
        cls.paths = {k: d / 'labs' / (s['id'].replace('/', '__') + '.html') for k, s in (('nn', cls.nn), ('ch', cls.ch), ('cf', cls.cf))}
        cls.gallery = B.gallery(d, items, 'Labor', 'Referenzen', 'Mathematik <em>sehen</em>', 'Drei Experimente.', notes=['Offline.'], version='test')
        cls.pw = sync_playwright().start(); cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.pw.stop(); cls.tmp.cleanup()

    def page(self, path, **ctx):
        ctx.setdefault('offline', True)
        c = self.browser.new_context(**ctx); pg = c.new_page(); errors, requests = [], []
        pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.on('request', lambda r: requests.append(r.url) if not r.url.startswith(('file:', 'data:')) else None)
        pg.goto(path.as_uri()); self.addCleanup(c.close)
        return pg, errors, requests

    def test_gallery_shows_live_model_previews_and_no_progress(self):
        pg, errors, requests = self.page(self.gallery, viewport={'width': 1280, 'height': 900})
        pg.locator('html[data-gallery-ready="1"]').wait_for()
        self.assertEqual(pg.locator('.gx-card').count(), 3)
        self.assertEqual(pg.locator('.gx-fig .em-preview svg').count(), 3)            # every card carries its own scene
        self.assertEqual(pg.locator('#em-progress').count(), 0)                       # an overview is not a course
        txt = pg.inner_text('main'); self.assertNotIn('INDEPENDENT', txt); self.assertIsNone(RAW_ID.search(txt))
        # the preview is the real renderer fed by the lab model: the loss box shows the model's value at some point
        want = SC.trace(self.nn)['loss']
        self.wait_until(lambda: pg.evaluate("[...document.querySelectorAll('.gx-fig[data-preview=\"0\"] .em-lossbox text')].map(t => t.textContent).join('|')").find(
            f'{want:.5f}'.replace('.', ',')) >= 0, 20)
        pg.click('.gx-card >> nth=1'); pg.locator('html[data-em-ready="1"]').wait_for()
        self.assertIn('math__inscribed-rectangle', pg.url)
        self.assertEqual(errors, []); self.assertEqual(requests, [])

    def test_gallery_reduced_motion_is_a_still_frame(self):
        pg, errors, _ = self.page(self.gallery, reduced_motion='reduce')
        pg.locator('html[data-gallery-ready="1"]').wait_for(); pg.wait_for_timeout(700)
        a = pg.inner_html('.gx-fig[data-preview="2"]'); pg.wait_for_timeout(1500); b = pg.inner_html('.gx-fig[data-preview="2"]')
        self.assertEqual(a, b); self.assertEqual(pg.locator('.em-pulse').count(), 0); self.assertEqual(errors, [])

    def test_gallery_mobile_has_no_horizontal_overflow(self):
        pg, errors, _ = self.page(self.gallery, viewport={'width': 375, 'height': 812})
        pg.locator('html[data-gallery-ready="1"]').wait_for()
        self.assertLessEqual(pg.evaluate('document.documentElement.scrollWidth'), 375); self.assertEqual(errors, [])

    def wait_until(self, fn, seconds):
        import time
        end = time.time() + seconds
        while time.time() < end:
            if fn():
                return
            time.sleep(0.1)
        self.fail('condition not reached')

    def open_lab(self, key, **ctx):
        ctx.setdefault('reduced_motion', 'reduce')
        pg, errors, requests = self.page(self.paths[key], **ctx)
        pg.locator('html[data-em-ready="1"]').wait_for(); pg.click('text=Ohne Vorhersage erkunden')
        return pg, errors, requests

    def test_update_deltas_match_the_model(self):
        pg, errors, _ = self.open_lab('nn')
        ids = [s['id'] for s in self.nn['scene']['steps']]
        tr = SC.trace(self.nn)
        pg.locator('.em-steps-dots li button').nth(ids.index('loss')).click()
        self.assertEqual(pg.locator('.em-graphic .em-grad').evaluate_all("es => es.filter(e => getComputedStyle(e.parentNode).opacity !== '0').length"), 0)
        pg.locator('.em-steps-dots li button').nth(ids.index('update')).click(); pg.wait_for_timeout(100)
        fmt = lambda x: ('+' if x > 0 else '') + f'{x:.4f}'.rstrip('0').rstrip('.').replace('.', ',').replace('-', '−')
        for r, val in (('w11', tr['step']['W1'][0][0]), ('w22', tr['step']['W1'][1][1]), ('v1', tr['step']['W2'][0])):
            self.assertEqual(pg.text_content(f'.em-graphic g[data-ref="{r}"] .em-grad'), 'Δ ' + fmt(val), r)
        self.assertEqual(errors, [])

    def test_cashflow_minimum_reason_is_true(self):
        pg, errors, _ = self.open_lab('cf')
        n = pg.locator('.em-steps-dots li').count(); tr = SC.trace(self.cf)
        pg.locator('.em-steps-dots li button').nth(n - 2).click(); pg.wait_for_timeout(100)
        why = pg.text_content('.em-why-min'); k = tr['min_index']
        if why:
            self.assertIn(f'P{k + 1}', why); self.assertLess(tr['cf'][k], 0); self.assertGreater(tr['cf'][k + 1], 0)
        cfs = pg.evaluate("[...document.querySelectorAll('.em-cf')].map(e => e.textContent)")
        self.assertEqual(len(cfs), len(tr['cf']))
        for shown, val in zip(cfs, tr['cf']):
            self.assertEqual(shown, ('+' if val > 0 else '') + f'{val:,.0f}'.replace(',', '.').replace('-', '−'))
        self.assertEqual(errors, [])

    def test_reference_records_are_namespaced_and_keep_legacy_keys(self):
        pg, errors, _ = self.open_lab('nn')
        pg.evaluate("localStorage.setItem('em-progress-v1', JSON.stringify({'ml/backprop-2-2-1::predict': {lab: 'ml/backprop-2-2-1', task: 'predict', kc_ids: [], attempts: 1, hints: 0, solution_viewed: false, correct: true, first_try: true, at: []}}))")
        pg.evaluate('EM.store.record("ml/backprop-2-2-1", "t1", [], "correct")')
        d = pg.evaluate("JSON.parse(localStorage.getItem('em-progress-v1'))")
        self.assertIn('ml/backprop-2-2-1::predict', d)                                  # older records are never touched
        self.assertIn('referenz|ml/backprop-2-2-1::t1', d); self.assertEqual(d['referenz|ml/backprop-2-2-1::t1']['ctx'], 'referenz')
        self.assertEqual(errors, [])

    def test_learning_environment_ignores_reference_records(self):
        src = (T / 'em_app.js').read_text()
        self.assertIn("if (!r.ctx) for (const [t, ev] of r.at || [])", src)

    def test_dark_mode_and_mobile_lab_layout(self):
        pg, errors, _ = self.open_lab('cf', color_scheme='dark', viewport={'width': 390, 'height': 844})
        bg = pg.evaluate("getComputedStyle(document.body).backgroundColor")
        self.assertNotEqual(bg, 'rgb(246, 243, 236)')                                    # dark paper, not the light one
        self.assertLessEqual(pg.evaluate('document.documentElement.scrollWidth'), 390)
        box = pg.locator('.em-graphic svg').bounding_box(); self.assertGreater(box['width'], 330)
        for sel in ('.em-player >> text=Weiter', '.em-player >> text=Zurück', '#p-delay'):
            self.assertTrue(pg.locator(sel).is_visible(), sel)                          # no hidden controls
        self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
