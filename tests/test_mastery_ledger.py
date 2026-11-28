"""Mastery evidence ledger (mastery-ledger-v1) and progress summary (mastery-progress-v1): one derived read model over
every learner store, provenance per event, honest accounting, no scores. Python and the browser mirror
(templates/mastery_ledger.js, running on the tested EMT policy) must produce identical output for identical input."""
import copy
import json
import unittest
from pathlib import Path

from exam_mastery.mastery import ledger as L

from ledger_fixtures import KEY, NOW, catalog, storage

REPO = Path(__file__).resolve().parents[1]
TEMPLATES = REPO / "exam_mastery" / "templates"


class LedgerRules(unittest.TestCase):
    def setUp(self):
        self.cat, self.st = catalog(), storage()
        self.led = L.build_ledger(self.st, self.cat, NOW)
        self.ev = {e["id"]: e for e in self.led["events"]}

    def test_every_store_is_accounted_for(self):
        stores = {s["store"]: s for s in self.led["stores"]}
        self.assertEqual(list(stores), list(L.STORES))
        for s in stores.values():
            self.assertTrue(s["present"])
            self.assertEqual(s["read"], s["included"] + sum(s["excluded"].values()), s)
        self.assertEqual(stores["em-tutor-v1"]["excluded"], {"engine_decision": 1})
        self.assertEqual(stores["em-practice-v1"]["excluded"], {"mirror_duplicate": 2})
        self.assertEqual(len(self.led["events"]), sum(s["included"] for s in stores.values()))

    def test_stores_are_not_changed(self):
        before = json.dumps(self.st, sort_keys=True)
        L.summarize(L.build_ledger(self.st, self.cat, NOW), self.cat)
        self.assertEqual(json.dumps(self.st, sort_keys=True), before)

    def test_empty_explorable_store_and_backprop_history(self):
        prog = L.summarize(self.led, self.cat)
        explorable = [c for c in prog["competencies"] if c["scope"] == "explorable:" + self.cat["units"][0]["unit_id"]]
        self.assertTrue(explorable and all(c["status"] == "NOT_ASSESSED" and sum(c["counts"].values()) == 0 for c in explorable))
        pre = next(c for c in prog["competencies"] if c["scope"] == "workbench:" + KEY and c["competency"] == "prereq/sigmoid-derivative")
        self.assertEqual(pre["status"], "RETAINED_ON_LATER_DAY")
        self.assertEqual(pre["basis"], "production")
        self.assertEqual((pre["counts"]["unassisted"], pre["counts"]["assisted"], pre["counts"]["retries"], pre["counts"]["independent"]), (3, 0, 1, 2))
        self.assertEqual(pre["delayed"]["after_hours"], 25)
        bp = next(c for c in prog["competencies"] if c["scope"] == "workbench:" + KEY and c["competency"] == "ml/backpropagation")
        self.assertEqual((bp["status"], bp["basis"], bp["counts"]["assisted"], bp["counts"]["unassisted"]), ("ASSISTED", "none", 2, 0))
        self.assertEqual((bp["counts"]["hint"], bp["counts"]["tutor"]), (2, 1))
        self.assertIsNone(bp["first_independent"])

    def test_unknown_future_and_unreadable_events_are_kept_but_never_evidence(self):
        unknown = [e for e in self.led["events"] if e["kind"] == "unknown"]
        self.assertEqual({e["type"] for e in unknown}, {"legacy_note", "mystery"})
        self.assertTrue(all("unbekannt" in e["note"] and not e["state_input"] for e in unknown))
        future = [e for e in self.led["events"] if e["t_quality"] == "future"]
        unreadable = [e for e in self.led["events"] if e["t_quality"] == "invalid"]
        self.assertEqual((len(future), len(unreadable)), (1, 1))
        self.assertFalse(future[0]["state_input"] or unreadable[0]["state_input"])
        self.assertIsNone(future[0]["assist"])
        self.assertEqual(self.led["events"][-1]["t_quality"], "invalid")      # undated events sort last

    def test_provenance_fields(self):
        for e in self.led["events"]:
            self.assertEqual(e["id"], f'{e["store"]}#{e["record"]}#{e["list"]}#{e["i"]}')
            self.assertIn(e["product"], ("workbench", "explorable", "motion", "chapter_app"))
            self.assertIn(e["source"], (None, "deterministic", "agent_judgement", "self_report", "unjudged"))
            self.assertIn(e["role"], (None, "practice", "evidence", "retest"))
        tutor = [e for e in self.led["events"] if e["help"] == "tutor"]
        self.assertTrue(tutor and all(e["source"] == "agent_judgement" for e in tutor))
        chapter = [e for e in self.led["events"] if e["record"] == "course/la/ch1"]
        self.assertTrue(all((e["course"], e["chapter"], e["unit"]) == ("la", "ch1", "la-ch1") for e in chapter))
        unverified = self.ev["em-practice-v1#course/la/ch1#policy#0"]
        self.assertEqual((unverified["source"], unverified["state_input"]), ("unjudged", False))
        self.assertNotIn("private text", json.dumps(self.led))                  # answers never enter the ledger
        self.assertTrue(self.ev["em-practice-v1#math/scaled-attention-golden-reference@old-revision#policy#0"]["archived"])
        self.assertIn("ohne Gegenstück", self.ev["em-practice-v1#course/la/ch1#events#2"]["note"])
        self.assertEqual(self.ev["em-learn-v2#chapter:c1#events#2"]["assist"], "assisted")
        self.assertEqual(self.ev["em-learn-v2#chapter:c1#events#3"]["source"], "self_report")

    def test_status_matches_the_policy_on_the_raw_store(self):
        """The ledger-derived state equals policy.kc_status on the original store (rules unchanged)."""
        from exam_mastery.learning import policy as P
        from ledger_fixtures import ML
        raw = [e for e in self.st["em-tutor-v1"]["tracks"][KEY]["events"]
               if e["type"] != "decision" and e["type"] in ("attempt",) + P.ASSIST_EVENTS and e["t"] != "gestern"
               and not e["t"].startswith("2099")]
        prog = L.summarize(self.led, self.cat)
        mine = {c["competency"]: c["status"] for c in prog["competencies"] if c["scope"] == "workbench:" + KEY}
        self.assertEqual(mine, P.kc_status(ML, raw, NOW))

    def test_coverage_per_chapter(self):
        prog = L.summarize(self.led, self.cat)
        att = next(c for c in prog["chapters"] if c["unit"] == "attention")
        self.assertEqual(att["with_production"], ["prereq/sigmoid-derivative"])
        self.assertIn("ml/backpropagation", att["without_production"])
        ch1 = next(c for c in prog["chapters"] if c["unit"] == "la-ch1")
        self.assertEqual((ch1["course"], ch1["chapter"], ch1["with_production"]), ("la", "ch1", []))
        shapes = next(i for i in ch1["items"] if i["competency"] == "attention/shapes")
        self.assertTrue(shapes["attempted"])           # free text attempted, but no production evidence

    def test_empty_storage(self):
        led = L.build_ledger({}, self.cat, NOW)
        self.assertEqual(led["events"], [])
        self.assertTrue(all(not s["present"] and s["read"] == 0 for s in led["stores"]))
        prog = L.summarize(led, self.cat)
        self.assertTrue(all(c["status"] == "NOT_ASSESSED" for c in prog["competencies"]))

    def test_timestamps(self):
        far = 10 ** 15
        self.assertEqual(L.stamp("2026-11-27", far), (L.stamp("2026-11-27T00:00:00Z", far)[0], "date_only"))
        self.assertEqual(L.stamp("2026-11-27T10:00:00+01:00", far)[0], L.stamp("2026-11-27T09:00:00Z", far)[0])
        for bad in ("2026-02-30", "2026-13-01", "2026-11-27T24:00:00Z", "27.11.2026", "", "0000-01-01"):
            self.assertEqual(L.stamp(bad, far), (None, "invalid"), bad)
        self.assertEqual(L.stamp(None, far), (None, "missing"))


class BrowserParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch()
        cls.page = cls.browser.new_page()
        cls.errors = []
        cls.page.on("pageerror", lambda e: cls.errors.append(str(e)))
        cls.page.set_content("<!doctype html><html><body></body></html>")
        for name in ("em_tutor.js", "mastery_ledger.js"):
            cls.page.add_script_tag(path=str(TEMPLATES / name))

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def js(self, storage, cat, now=NOW):
        return self.page.evaluate("([s, c, n]) => { const l = MasteryLedger.buildLedger(s, c, n); return [l, MasteryLedger.summarize(l, c)]; }",
                                  [storage, cat, now])

    def check(self, storage, cat, now=NOW):
        led = L.build_ledger(storage, cat, now)
        prog = L.summarize(led, cat)
        jl, jp = self.js(storage, cat, now)
        self.assertEqual(jl, json.loads(json.dumps(led)))
        self.assertEqual(jp, json.loads(json.dumps(prog)))
        self.assertEqual(self.errors, [])

    def test_parity_full_fixture(self):
        self.check(storage(), catalog())

    def test_parity_empty_and_partial_stores(self):
        cat = catalog()
        self.check({}, cat)
        self.check({"em-practice-v1": {"schema": 1, "units": {cat["units"][0]["unit_id"]: {"events": [], "policy": []}}}}, cat)
        self.check({"em-tutor-v1": {"schema": 1, "tracks": {KEY: {"events": "broken"}}}, "em-motion-v1": None}, cat)

    def test_parity_at_a_later_reference_time(self):
        self.check(storage(), catalog(), "2026-12-24T08:00:00Z")

    def test_parity_timestamps(self):
        for t in ("2026-11-27", "2026-11-27T10:00", "2026-11-27T10:00:00.123456789+02:30", "2026-02-29", "2024-02-29T23:59:59Z",
                  "2026-11-27T10:00:00-05:00", "0099-01-01T00:00:00Z", "x", "2026-11-27T10:00:00 Z"):
            py = L.stamp(t, 10 ** 15)
            js = self.page.evaluate("t => MasteryLedger.stamp(t, 1e15)", t)
            self.assertEqual(list(py), js, t)

    def test_parity_with_generated_histories(self):
        import random
        from ledger_fixtures import ML, _att
        rng = random.Random(20261128)
        cat = catalog()
        tasks = [t for t in ML["tasks"] if t["type"] != "open"]
        from exam_mastery.learning import tracks as TR
        for _ in range(12):
            ev, t0 = [], 1795000000000
            for _ in range(rng.randint(3, 25)):
                t0 += rng.choice([60_000, 3_600_000, 21 * 3_600_000])
                at = L.iso(t0)
                task = rng.choice(tasks)
                kind = rng.random()
                if kind < 0.55:
                    wrong = {s["id"]: "0" for s in task["steps"]} if task["type"] == "steps" else "0"
                    ev.append(_att(task["id"], TR._answer_for(task) if rng.random() < 0.6 else wrong, at))
                elif kind < 0.9:
                    ev.append({"type": rng.choice(["hint", "solution", "tutor", "guided", "support"]), "task": task["id"], "t": at,
                               **({"kc": task["kc_id"]} if rng.random() < 0.3 else {})})
                else:
                    ev.append({"type": "decision", "task": task["id"], "t": at})
            st = copy.deepcopy(storage())
            st["em-tutor-v1"]["tracks"][KEY]["events"] = ev
            self.check(st, cat, L.iso(t0 + rng.choice([0, 30 * 3_600_000])))


if __name__ == "__main__":
    unittest.main()
