"""Lernstand page end to end (standard §5.6): the built Mastery app shows one ledger over all stores of the browser,
every statistic answers "Woher?" (rule, events, what it does not measure), no percentage appears anywhere, the timeline
filters by course/chapter/product, the optional Anki statistics need consent and come from a throwaway export, and
both exports carry the derived ledger. Real browser, temporary MASTERY_HOME, no external requests."""
import json
import tempfile
import unittest
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
    HAVE_BROWSER = True
except ImportError:  # pragma: no cover
    HAVE_BROWSER = False
try:
    import anki  # noqa: F401
    HAVE_ANKI = True
except ImportError:  # pragma: no cover
    HAVE_ANKI = False

from ledger_fixtures import KEY, storage

STATS_SECTIONS = "#sources, #competencies, #coverage, #motion-progress, #anki-stats"


@unittest.skipUnless(HAVE_BROWSER and HAVE_ANKI, "playwright and anki required")
class LernstandEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from exam_mastery.mastery import build
        from exam_mastery.mastery.server import start_in_thread
        from test_mastery_anki_stats import _throwaway_exports
        cls.tmp = tempfile.TemporaryDirectory(prefix="mastery-lernstand-")
        cls.home = Path(cls.tmp.name) / "Mastery"
        build(cls.home, log=lambda *_: None)
        cls.anki_files, cls.anki_reviews = _throwaway_exports(cls.tmp.name)
        cls.server, cls.base = start_in_thread(cls.home)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.tmp.cleanup()

    def test_lernstand(self):
        base, errors, external = self.base, [], []
        st = storage()
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            try:
                ctx = browser.new_context(accept_downloads=True)
                pg = ctx.new_page()
                pg.on("pageerror", lambda e: errors.append(str(e)))
                pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
                pg.on("request", lambda r: external.append(r.url) if not r.url.startswith((base, "data:", "blob:")) else None)
                pg.goto(base)
                pg.wait_for_selector('#app[data-ready="1"]')
                pg.evaluate("s => { for (const [k, v] of Object.entries(s)) localStorage.setItem(k, JSON.stringify(v)); }", st)
                pg.goto(base + "#lernstand")
                pg.reload()
                pg.wait_for_selector('#app[data-ready="1"]')
                self.assertTrue(pg.locator("#lernstand").is_visible())

                # Sources: every store accounted for; the explorable mirror is explained.
                for store in ("em-tutor-v1", "em-practice-v1", "em-motion-v1", "em-learn-v2"):
                    self.assertEqual(pg.locator(f'#sources tr[data-store="{store}"]').count(), 1)
                self.assertIn("em-practice-evidence-v1", pg.inner_text("#mirror-note"))
                self.assertIn("mirror_duplicate: 2", pg.inner_text('#sources tr[data-store="em-practice-v1"]'))

                # Per competency: backprop history from the workbench store, the empty explorable store stays honest.
                pre = pg.locator(f'#competencies tr[data-source="workbench"][data-kc="prereq/sigmoid-derivative"]')
                self.assertEqual(pre.get_attribute("data-status"), "RETAINED_ON_LATER_DAY")
                self.assertEqual((pre.get_attribute("data-independent"), pre.get_attribute("data-unassisted")), ("2", "3"))
                self.assertTrue(pre.get_attribute("data-delayed"))
                self.assertIn("nach", pre.inner_text())
                bp = pg.locator('#competencies tr[data-source="workbench"][data-kc="ml/backpropagation"]')
                self.assertEqual((bp.get_attribute("data-status"), bp.get_attribute("data-assisted")), ("ASSISTED", "2"))
                shapes = pg.locator('#competencies tr[data-source="explorable"][data-kc="attention/shapes"]')
                self.assertEqual((shapes.get_attribute("data-status"), shapes.get_attribute("data-unassisted")), ("NOT_ASSESSED", "0"))
                self.assertEqual(pg.locator('#coverage section[data-unit="attention"]').get_attribute("data-with"), "1")

                # Optional Anki statistics: the file picker stays locked until consent.
                self.assertTrue(pg.locator("#anki-file").is_disabled())
                pg.check("#anki-consent")
                pg.set_input_files("#anki-file", str(self.anki_files["apkg_legacy"]))
                pg.wait_for_selector("#anki-stats-label")
                self.assertIn("kein Kompetenznachweis", pg.inner_text("#anki-stats-label"))
                self.assertEqual(pg.locator("#anki-stats-cards tbody tr").count(), 2)
                self.assertNotIn("Privat", pg.inner_text("#anki-stats"))

                # No percentage anywhere on the page; every statistic is a "Woher?" button.
                self.assertNotIn("%", pg.inner_text("#lernstand"))
                bare = pg.evaluate("""sel => { const out = []; for (const root of document.querySelectorAll(sel)) {
                    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT); let n;
                    while ((n = w.nextNode())) if (/^\\d+$/.test(n.textContent.trim()) && !n.parentElement.closest('[data-num]')) out.push(n.parentElement.outerHTML.slice(0, 120)); }
                    return out; }""", STATS_SECTIONS)
                self.assertEqual(bare, [])
                nums = pg.locator("#lernstand [data-num]")
                self.assertGreater(nums.count(), 50)
                whys = set(pg.evaluate("() => [...document.querySelectorAll('#lernstand [data-num]')].map(b => b.dataset.why)"))
                self.assertTrue(all(whys))
                pg.evaluate("() => document.querySelectorAll('#lernstand details').forEach(d => { d.open = true; })")
                for why in sorted(whys):
                    btn = pg.locator(f'#lernstand [data-why="{why}"]').first
                    btn.click()
                    panel = btn.locator("xpath=ancestor::*[contains(@class,'m-card')][1]//*[contains(@class,'m-why')]").first
                    text = panel.inner_text()
                    self.assertIn("Woher?", text, why)
                    self.assertIn("Regel:", text, why)
                    self.assertIn("Was das nicht misst:", text, why)
                indep = pre.locator('[data-why="independent"]')
                indep.click()
                self.assertIn(f"em-tutor-v1#{KEY}#events#2", pg.inner_text("#competencies"))

                # Timeline: every ledger event, filterable by product and chapter, provenance on each entry.
                total = len(pg.evaluate("() => MasteryLedger.buildLedger({'em-tutor-v1': JSON.parse(localStorage.getItem('em-tutor-v1')), 'em-practice-v1': JSON.parse(localStorage.getItem('em-practice-v1')), 'em-motion-v1': JSON.parse(localStorage.getItem('em-motion-v1')), 'em-learn-v2': JSON.parse(localStorage.getItem('em-learn-v2'))}, null).events"))
                self.assertEqual(pg.locator("#timeline-list li[data-id]").count(), total)
                pg.select_option("#tl-product", "motion")
                self.assertEqual(set(pg.evaluate("() => [...document.querySelectorAll('#timeline-list li[data-id]')].map(e => e.dataset.product)")), {"motion"})
                pg.select_option("#tl-product", "")
                pg.select_option("#tl-unit", "attention")
                units = set(pg.evaluate("() => [...document.querySelectorAll('#timeline-list li[data-id]')].map(e => e.dataset.unit)"))
                self.assertEqual(units, {"attention"})
                self.assertIn("Herkunft:", pg.inner_text("#timeline-list"))

                # File export: raw stores (re-importable) plus the derived ledger.
                pg.goto(base + "#sicherung")
                with pg.expect_download() as dl:
                    pg.click("#backup-export")
                exported = json.loads(Path(dl.value.path()).read_text(encoding="utf-8"))
                self.assertEqual(exported["schema"], "mastery-state-v1")
                self.assertEqual(exported["storage"]["em-learn-v2"]["schema"], 2)
                self.assertEqual(exported["derived"]["ledger"]["schema"], "mastery-ledger-v1")
                self.assertEqual(exported["derived"]["progress"]["schema"], "mastery-progress-v1")
                pg.click("#backup-server")
                pg.wait_for_selector("#backup-status[data-saved]", state="attached")
                js_events = exported["derived"]["ledger"]["events"]
            finally:
                browser.close()
        self.assertEqual(errors, [])
        self.assertEqual(external, [])

        # `mastery export`: the server copy rebuilt into the same ledger (Python side), plus the Anki statistics.
        from exam_mastery.mastery import export
        backup = json.loads(Path(export(self.home)).read_text(encoding="utf-8"))
        self.assertEqual(backup["derived"]["ledger"]["schema"], "mastery-ledger-v1")
        self.assertEqual(backup["derived"]["ledger"]["events"], js_events)
        self.assertEqual(backup["derived"]["anki_stats"]["schema"], "mastery-anki-stats-v1")
        self.assertNotIn("private text", json.dumps(backup["derived"]))


if __name__ == "__main__":
    unittest.main()
