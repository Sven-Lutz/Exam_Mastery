"""B15: integrated learning environment (Lernumgebung/index.html) in a real browser.

A small book with an embedded cash-flow lab covers: navigation and routing, textbook with the lab in place, lab
interaction inside the frame and height reporting, quick checks, practice (numeric check, hints, gated solution,
self-assessment, link back to theory), exam mode, progress persistence across reload, export/import (and rejection of
a foreign file), deletion, theme switch (host and lab), mobile drawer, keyboard, offline (zero requests), CSP, and no
technical competency ids in the visible text. Synthetic math, law and ML chapters run through the real pipeline.
"""
import contextlib, io, json, re, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from exam_mastery import learn_app
from exam_mastery.labs import build as LB

ORD = [0, 100, 180, 190, 210, 230, 250, 270]
COST = [50 + g + x + 2 for g, x in zip([10, 30, 50, 40, 140, 60, 70, 80], [40, 40, 70, 60, 50, 40, 40, 40])]
INV = [200, 500, 300, 140]
ID_RE = re.compile(r'\bkc-[0-9a-f]{10,}\b')


def book():
    sol = lambda ans, steps, hints, rub: {'approach': '', 'steps': steps, 'answer': ans, 'errors': [], 'hints': hints, 'rubric': rub}
    return {
        'meta': {'title': 'Finanzplan', 'course': 'Testkurs', 'chapter_no': 3, 'status_line': 'Vorschau'},
        'kc_labels': {'kc-aaaaaaaaaaaa01': 'Den Finanzbedarf aus einem Zahlungsplan bestimmen', 'kc-aaaaaaaaaaaa02': 'Begriffe der Liquidität unterscheiden'},
        'sections': [
            {'title': 'Grundbegriffe', 'blocks': [
                {'type': 'lead', 'md': 'Liquidität ist nicht Gewinn.', 'kc_ids': ['kc-aaaaaaaaaaaa02']},
                {'type': 'definition', 'term': 'Cashflow', 'md': 'Saldo der Zahlungen einer Periode: \\(CF_t = E_t - A_t\\).', 'prov': 'course', 'src': 'Folie 21', 'kc_ids': ['kc-aaaaaaaaaaaa02']}]},
            {'title': 'Finanzbedarf', 'blocks': [
                {'type': 'text', 'md': 'Der Bedarf ist der tiefste kumulierte Stand.', 'prov': 'course', 'src': 'Folie 22', 'kc_ids': ['kc-aaaaaaaaaaaa01']},
                {'type': 'example', 'title': 'Drei Perioden', 'given': 'Zahlungen -130, -30, 20', 'steps': [['kumuliert -130, -160, -140', 'laufende Summe']], 'result': 'Bedarf 160', 'kc_ids': ['kc-aaaaaaaaaaaa01']}]},
            {'title': 'Interaktive Labs', 'blocks': []}],
        'stages': [{'title': 'Geführte Anwendung', 'level': 2, 'items': [
            {'id': 'a-01', 'prompt': 'Bestellungen 50, 70, 90; Zahlung nach zwei Perioden; Kosten 30; Investition 100. Finanzbedarf?', 'stage_label': 'guided', 'operation': 'CALCULATE',
             'kc_keys': ['kc-aaaaaaaaaaaa01'], 'points': 4, 'evidence_gap': False,
             'solution': sol('Kumuliert -130, -160, -140; Finanzbedarf 160 k€.', [['Periode 1: -130', 'Investition']], ['Wann zahlt der erste Kunde?', 'Laufende Summe bilden.'], [['Cashflows', 3], ['Bedarf', 1]])},
            {'id': 'a-02', 'prompt': 'Erklären Sie den Unterschied zwischen Cashflow und Liquidität.', 'stage_label': 'guided', 'operation': 'EXPLAIN',
             'kc_keys': ['kc-aaaaaaaaaaaa02'], 'points': 2, 'evidence_gap': False,
             'solution': sol('Cashflow ist der Saldo einer Periode, Liquidität die laufende Summe.', [['Definitionen', 'Folie 21']], [], [['Unterschied', 2]])}]},
            {'title': 'Klausur', 'level': 5, 'items': [
            {'id': 'e-01', 'prompt': 'Bestimmen Sie den Finanzbedarf (Prüfungsaufgabe).', 'stage_label': 'exam', 'operation': 'CALCULATE', 'kc_keys': ['kc-aaaaaaaaaaaa01'],
             'points': 6, 'evidence_gap': False, 'solution': sol('Finanzbedarf 280 k€.', [['tiefster Stand -280', 'laufende Summe']], [], [['Rechnung', 4], ['Deutung', 2]])}]}],
        'exam': {'items': [{'id': 'e-01'}], 'total_points': 6, 'subtitle': 'Übungsklausur'},
        'cards': [{'front': 'Was ist der Finanzbedarf?', 'back': 'Der Betrag des tiefsten kumulierten Liquiditätsstandes.'}],
        'figures': {}}


class Build(unittest.TestCase):
    def test_model_places_lab_by_competency_and_hides_ids(self):
        with tempfile.TemporaryDirectory() as td:
            spec = LB.cashflow_spec('t/cf', 'Liquidität', ['kc-aaaaaaaaaaaa01'], ['Folie 21'], ORD, 5, COST, INV, course='Testkurs')
            LB.render(spec, Path(td) / 'labs')
            m = learn_app.app_model(book(), [{'file': 'Lernumgebung/labs/t__cf.html', 'title': 'Liquidität', 'kc_ids': ['kc-aaaaaaaaaaaa01']}])
            self.assertEqual([s['title'] for s in m['sections']], ['Grundbegriffe', 'Finanzbedarf'])     # lab section not shown as text
            self.assertEqual(m['labs'][0]['section'], 's2'); self.assertEqual(m['labs'][0]['after'], 1)  # after the worked example
            self.assertEqual(m['cards'][0]['section'], 's2')
            self.assertEqual(m['exam']['items'], ['e-01'])
            self.assertTrue(all(i['section'] for i in m['items']))

    def test_lab_without_competency_link_is_not_placed(self):
        m = learn_app.app_model(book(), [{'file': 'Lernumgebung/labs/x.html', 'title': 'Fremd', 'kc_ids': ['kc-zzzzzzzzzzzz']}])
        self.assertEqual(m['labs'], [])


class Browser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise unittest.SkipTest('playwright not installed')
        cls.tmp = tempfile.TemporaryDirectory(); art = Path(cls.tmp.name) / 'artifacts'
        spec = LB.cashflow_spec('t/cf', 'Liquidität', ['kc-aaaaaaaaaaaa01'], ['Folie 21'], ORD, 5, COST, INV, course='Testkurs')
        LB.render(spec, art / 'Lernumgebung' / 'labs')
        from exam_mastery import typeset
        typeset._assets(art)                       # fonts and MathJax exactly as the publisher installs them
        (art / '1_Lehrbuch.pdf').write_bytes(b'%PDF-1.4\n'); (art / 'anki').mkdir(); (art / 'anki' / 'deck.apkg').write_bytes(b'x')
        cls.index = learn_app.build(book(), art / 'Lernumgebung', labs=[{'file': 'Lernumgebung/labs/t__cf.html', 'title': 'Liquidität', 'kc_ids': ['kc-aaaaaaaaaaaa01']}],
                                    materials=[['Lehrbuch (PDF)', '../1_Lehrbuch.pdf']], anki='../anki/deck.apkg', chapter_id='ch-test')
        cls.pw = sync_playwright().start(); cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.pw.stop(); cls.tmp.cleanup()

    def open(self, route='start', **ctx):
        c = self.browser.new_context(offline=True, accept_downloads=True, **ctx); pg = c.new_page(); errs, reqs = [], []
        pg.on('console', lambda m: errs.append(m.text) if m.type in ('error', 'warning') else None)
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('request', lambda r: reqs.append(r.url) if not r.url.startswith(('file:', 'data:', 'blob:')) else None)
        pg.goto(self.index.as_uri() + '#/' + route); pg.wait_for_selector('#app[data-ready="1"]')
        return c, pg, errs, reqs

    def test_learning_flow_with_embedded_lab(self):
        c, pg, errs, reqs = self.open()
        self.assertIn('Finanzplan', pg.inner_text('.hero'))
        pg.click('text=Kapitel beginnen'); pg.wait_for_timeout(100)
        self.assertIn('#/lernen/s1', pg.url); self.assertIn('Saldo der Zahlungen', pg.inner_text('.reader'))
        pg.click('.pager a[rel=next]'); pg.wait_for_timeout(200)
        self.assertIn('Finanzbedarf', pg.inner_text('.reader h1'))
        frame = pg.frame_locator('#lab-t__cf iframe')
        frame.locator('input[name=pred][value="steigt"]').check(); frame.locator('input[name=conf][value="sure"]').check()
        frame.locator('#phase-predict textarea').fill('weil die Zahlungen später kommen')
        frame.locator('text=Vorhersage festlegen und Simulation öffnen').click()
        self.assertIn('trifft zu', frame.locator('.em-pre .em-feedback').inner_text())
        pg.wait_for_timeout(400)
        self.assertGreater(int(pg.evaluate("parseInt(document.querySelector('iframe.lab-frame').style.height)")), 1000)  # height reported by the lab
        self.assertTrue(frame.locator('nav.em-nav').is_hidden())                                                       # embed mode
        # quick check: reveal and rate
        pg.click('text=Antwort aufdecken'); self.assertIn('tiefsten', pg.inner_text('.quick')); pg.click('.qc-rate >> text=ja')
        # context panel: names, never ids
        self.assertIn('Den Finanzbedarf aus einem Zahlungsplan bestimmen', pg.inner_text('.context'))
        for r in ('start', 'lernen/s1', 'lernen/s2', 'ueben', 'klausur', 'stand', 'tutor', 'material'):
            pg.goto(self.index.as_uri() + '#/' + r); pg.wait_for_timeout(150)
            self.assertIsNone(ID_RE.search(pg.inner_text('body')), r)
        self.assertEqual(errs, []); self.assertEqual(reqs, []); c.close()

    def test_practice_feedback_progress_reload_export_import(self):
        c, pg, errs, reqs = self.open('ueben')
        it = pg.locator('#item-a-01')
        self.assertTrue(it.locator('text=Musterlösung öffnen').is_disabled())                       # no solution before an attempt
        self.assertTrue(it.locator('.self-rate').is_hidden())
        it.locator('input[aria-label="Ihr Endergebnis (Zahl)"]').fill('140'); it.locator('text=Ergebnis prüfen').click()
        self.assertIn('Stimmt mit einem Ergebnis', it.inner_text())                                   # 140 is a stated result (cumulative)
        it.locator('input[aria-label="Ihr Endergebnis (Zahl)"]').fill('999'); it.locator('text=Ergebnis prüfen').click()
        self.assertIn('kommt in der Musterlösung nicht vor', it.inner_text()); self.assertIn('Nachlesen: Finanzbedarf', it.inner_text())
        it.get_by_role('button', name=re.compile('^Hinweis')).click(); self.assertEqual(it.locator('.hints li').count(), 1)
        it.locator('text=Musterlösung öffnen').click(); self.assertIn('Finanzbedarf 160', it.locator('.solution').inner_text())
        it.locator('.self-rate >> text=teilweise').click()
        it2 = pg.locator('#item-a-02'); it2.locator('text=Antwort festhalten').click()
        self.assertIn('eigene Antwort', it2.inner_text())                                              # empty answers are not accepted
        it2.locator('textarea').fill('Cashflow ist ein Saldo, Liquidität eine Summe.'); it2.locator('text=Antwort festhalten').click()
        self.assertFalse(it2.locator('text=Musterlösung öffnen').is_disabled())
        pg.reload(); pg.wait_for_selector('#app[data-ready="1"]')
        self.assertEqual(pg.locator('#item-a-02 textarea').input_value(), 'Cashflow ist ein Saldo, Liquidität eine Summe.')   # draft kept
        pg.goto(self.index.as_uri() + '#/stand'); pg.wait_for_timeout(150)
        txt = pg.inner_text('main')
        self.assertIn('Lösung angesehen', txt); self.assertNotIn('%', txt); self.assertNotIn('INDEPENDENT_PASS', txt)
        with pg.expect_download() as dl:
            pg.click('text=Lernhistorie exportieren')
        data = json.loads(Path(dl.value.path()).read_text())
        self.assertEqual(data['schema'], 'em-learn-export-v1'); n = len(data['learn']['events'])
        pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_selector('#app[data-ready="1"]')
        bad = Path(self.tmp.name) / 'bad.json'; bad.write_text('{"x": 1}')
        pg.set_input_files('#imp', str(bad)); pg.wait_for_timeout(150)
        self.assertIn('abgelehnt', pg.inner_text('#toast'))
        pg.set_input_files('#imp', dl.value.path()); pg.wait_for_timeout(200)
        self.assertEqual(len(pg.evaluate("JSON.parse(localStorage.getItem('em-learn-v2')).events")), n)
        pg.set_input_files('#imp', dl.value.path()); pg.wait_for_timeout(200)                          # re-import does not duplicate
        self.assertEqual(len(pg.evaluate("JSON.parse(localStorage.getItem('em-learn-v2')).events")), n)
        pg.once('dialog', lambda d: d.accept('nein')); pg.click('text=Lernstand löschen')                # wrong confirmation keeps data
        self.assertEqual(len(pg.evaluate("JSON.parse(localStorage.getItem('em-learn-v2')).events")), n)
        self.assertEqual(errs, []); self.assertEqual(reqs, []); c.close()

    def test_exam_mode_and_tutor_briefing(self):
        c, pg, errs, _ = self.open('klausur')
        self.assertEqual(pg.locator('.solution').count(), 0)
        pg.click('text=Klausur beginnen'); pg.wait_for_timeout(100)
        self.assertEqual(pg.locator('.solution').count(), 0)                                         # solutions hidden while working
        pg.fill('.exam-item textarea', 'Bedarf 280')
        pg.once('dialog', lambda d: d.accept()); pg.click('text=Abgeben und Lösungen anzeigen')
        self.assertEqual(pg.locator('.solution').count(), 1)
        pg.locator('.rubric input').first.check()
        self.assertIn('4 von 6 Punkten', pg.inner_text('.score')); self.assertIn('keine offizielle', pg.inner_text('.score'))
        pg.goto(self.index.as_uri() + '#/tutor/s2'); pg.wait_for_timeout(100)
        b = pg.input_value('textarea.brief')
        self.assertIn('Abschnitt 3.2: Finanzbedarf', b); self.assertIn('Folie 22', b); self.assertIsNone(ID_RE.search(b))
        self.assertIn('keine Live-Verbindung', pg.inner_text('main'))
        self.assertEqual(errs, []); c.close()

    def test_theme_mobile_keyboard(self):
        c, pg, errs, _ = self.open('lernen/s2', viewport={'width': 390, 'height': 844}, color_scheme='light')
        self.assertLessEqual(pg.evaluate('document.documentElement.scrollWidth'), 390)
        self.assertFalse(pg.locator('.sidebar').is_visible() and pg.evaluate("getComputedStyle(document.querySelector('.sidebar')).transform") == 'none')
        pg.click('.menu-btn'); pg.wait_for_timeout(300)
        self.assertEqual(pg.get_attribute('.menu-btn', 'aria-expanded'), 'true')
        pg.click('.sidebar >> text=Lernstand'); pg.wait_for_timeout(200)
        self.assertIn('#/stand', pg.url); self.assertEqual(pg.get_attribute('.menu-btn', 'aria-expanded'), 'false')
        pg.goto(self.index.as_uri() + '#/lernen/s2'); pg.wait_for_timeout(300)
        pg.select_option('#theme', 'dark'); pg.wait_for_timeout(300)
        self.assertEqual(pg.get_attribute('html', 'data-theme'), 'dark')
        self.assertNotEqual(pg.evaluate("getComputedStyle(document.body).backgroundColor"), 'rgb(247, 246, 242)')
        self.assertEqual(pg.frame_locator('iframe.lab-frame').locator('html').get_attribute('data-theme'), 'dark')   # lab follows
        pg.reload(); pg.wait_for_selector('#app[data-ready="1"]'); self.assertEqual(pg.get_attribute('html', 'data-theme'), 'dark')   # remembered
        pg.keyboard.press('Tab'); self.assertEqual(pg.evaluate('document.activeElement.className'), 'skip')
        pg.keyboard.press('Enter'); self.assertEqual(pg.evaluate('document.activeElement.id'), 'main')
        self.assertEqual(errs, []); c.close()

    def test_formulas_typeset_on_direct_entry(self):
        # regression: opening a section directly (MathJax still loading) must still render the formula
        c, pg, errs, _ = self.open('lernen/s1')
        pg.wait_for_selector('.reader mjx-container', timeout=15000)
        self.assertNotIn('\\(', pg.inner_text('.reader'))
        self.assertEqual(errs, []); c.close()

    def test_csp_and_no_inline_handlers(self):
        h = self.index.read_text()
        csp = re.search(r'Content-Security-Policy" content="([^"]+)"', h).group(1)
        self.assertIn("default-src 'none'", csp); self.assertIn("connect-src 'none'", csp); self.assertNotIn('unsafe-eval', csp)
        self.assertNotIn("script-src 'self' file: 'unsafe-inline'", csp)
        self.assertIsNone(re.search(r'\son[a-z]+="', h))
        self.assertNotIn('http://', h.replace('http://www.w3.org', '')); self.assertNotIn('https://', h)


class Fixtures(unittest.TestCase):
    """The same environment for other subjects: synthetic math, law and ML chapters through the real pipeline."""
    def test_math_law_ml_chapters_render(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest('playwright not installed')
        from test_b6_5_chapter_publish import synthetic_run
        with tempfile.TemporaryDirectory() as td:
            runs = {kind: synthetic_run(kind, Path(td))[0] for kind in ('math', 'law', 'ml')}   # publishing uses Chromium itself
            with sync_playwright() as p:
              b = p.chromium.launch(); n = 0
              for kind, out in runs.items():
                for idx in sorted(out.glob('chapters/*/publish/artifacts/Lernumgebung/index.html')):
                    pg = b.new_page(); errs = []
                    pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
                    pg.goto(idx.as_uri() + '#/lernen/s1'); pg.wait_for_selector('#app[data-ready="1"]')
                    self.assertTrue(pg.inner_text('.reader').strip(), (kind, idx))
                    self.assertIsNone(ID_RE.search(pg.inner_text('body')), (kind, idx))
                    pg.goto(idx.as_uri() + '#/ueben'); pg.wait_for_timeout(100)
                    self.assertGreaterEqual(pg.locator('article.item').count(), 1, (kind, idx))
                    self.assertEqual(errs, [], (kind, idx)); pg.close(); n += 1
              b.close()
            self.assertGreaterEqual(n, 3)


if __name__ == '__main__':
    unittest.main()
