"""Machine quality gates (catalogue mastery-quality-v1): one positive and one negative synthetic case per gate, the
report schema, the German HTML/Markdown report, build-chapter/quality CLI exit codes and the report link in the Kurse
view (real browser). Synthetic, public-safe data only; no network, no model calls."""
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from exam_mastery.mastery import quality as Q  # noqa: E402

try:
    import pymupdf
    HAVE_PDF = True
except ImportError:  # pragma: no cover
    HAVE_PDF = False
try:
    from playwright.sync_api import sync_playwright
    HAVE_BROWSER = True
except ImportError:  # pragma: no cover
    HAVE_BROWSER = False

PLANE = {"label": "Scherung, t = 1", "parameters": {"matrix": [[2, -1], [1, 1]], "vector": [1, 2]}}


def good_unit():
    """Minimal synthetic unit that satisfies every unit-level gate (not a schema-complete experience unit)."""
    teach = [
        {"id": "teach/why", "section_title": "Warum eine Matrix die Ebene bewegt", "content": "Problem: Wohin gehen Punkte?",
         "competency_ids": ["map/columns"], "claim_ids": ["claim/col"],
         "blocks": [{"type": "definition", "term": "Spalte", "md": "Bild des Basisvektors."},
                    {"type": "derivation"}, {"type": "graphic", "id": "graphic/plane"},
                    {"type": "box", "kind": "pitfall", "md": "Zeilen sind nicht die Bilder."}],
         "derivation": {"title": "Spalten", "given": "A", "result": "A e1 = a1",
                        "steps": [{"statement": "A e1", "justification": "Definition", "claim_ids": ["claim/col"]},
                                  {"statement": "= a1", "justification": "Rechnen", "claim_ids": ["claim/col"]}]}},
        {"id": "teach/example", "section_title": "Ein Zahlenbeispiel", "content": "A = (2 -1; 1 1), x = (1, 2).",
         "competency_ids": ["map/columns"], "claim_ids": ["claim/col"]},
    ]
    stages = ["worked_example", "guided", "independent", "transfer", "exam"]
    tasks = []
    for i, st in enumerate(stages):
        tasks.append({"id": f"task/{st}", "stage": st, "role": "core", "competency_ids": ["map/columns"],
                      "prompt": "Zeigen Sie, dass die erste Spalte das Bild von e1 ist." if st == "independent" else
                      "Berechnen Sie A x für die gegebene Matrix.",
                      "solution": "Man multipliziert die Matrix mit dem Vektor komponentenweise und erhält das Bild "
                                  "als Linearkombination der Spalten; alternativ über die Spaltendarstellung.",
                      "solution_steps": [["A x = x1 a1 + x2 a2", "Linearität"], ["= (0, 3)", "Rechnen"]],
                      "rubric": [{"criterion": "Ansatz", "points": 1}, {"criterion": "Ergebnis, auch zulässig "
                                                                                    "über Spalten", "points": 1}]})
    tasks += [{"id": f"task/error-{k}", "stage": "guided", "role": "contrast", "competency_ids": ["map/columns"],
               "prompt": "Finden Sie den Fehler in der Rechnung.", "solution": "Der Fehler liegt in der Verwechslung "
               "von Zeilen und Spalten; richtig ist die Spaltendarstellung, alternativ komponentenweise.",
               "machine_check": {"type": "numeric", "expected": 3}, "rubric": [{"criterion": "Fehler", "points": 1}]}
              for k in (1, 2)]
    return {
        "schema": "em-experience-v1", "unit_id": "test/quality-good", "title": "Synthetische Gate-Einheit",
        "source_mode": "grounded",
        "sources": [{"id": "lecture/v1", "kind": "lecture", "locator": "Vorlesung 1, Folie 3"},
                    {"id": "own", "kind": "own_derivation", "locator": "Eigene Herleitung"}],
        "claims": [{"id": "claim/col", "text": "Spalten sind Bilder.", "source_refs": ["lecture/v1"],
                    "evidence_status": "verified"}],
        "competencies": [{"id": "map/columns", "operation": "prove", "prerequisites": []}],
        "teaching": teach, "assessments": tasks,
        "cards": [{"key": "map/col-card", "kind": "mechanism", "front": "Warum ist die erste Spalte das Bild von e1?",
                   "answer": "Weil A e1 genau die erste Spalte auswählt.", "context": "Lineare Abbildung der Ebene.",
                   "competency_ids": ["map/columns"], "figure": "graphic/plane-state-0"}],
        "interactions": [{"id": "interaction/plane", "type": "explorable_model", "model_ref": "plane_linear_map",
                          "variants": [PLANE], "prediction_prompt": "Wohin geht e1?", "feedback_rule": "Vergleichen.",
                          "transfer_prompt": "Bauen Sie eine Matrix mit det 0.", "competency_ids": ["map/columns"]}],
        "graphics": [{"id": "graphic/plane", "model_ref": "plane_linear_map", "interaction_id": "interaction/plane",
                      "teaching_id": "teach/why", "assessment_ids": ["task/guided"], "claim_ids": ["claim/col"],
                      "competency_ids": ["map/columns"], "objects": {"a1": "erste Spalte"}, "keyframes": [0],
                      "alt": "Die Ebene vor und nach der Abbildung mit beiden Spalten.",
                      "caption": "Die Spalten von A sind die Bilder der Basisvektoren."}],
        "misconceptions": [{"id": "rows", "competency_ids": ["map/columns"]}],
        "authorship": {"human_status": "HUMAN_REVIEW_PENDING"}, "divergences": [],
    }


def gates_of(report):
    return {f["gate"] for f in report["findings"]}


def status(report, gid):
    return next(g["status"] for g in report["gates"] if g["id"] == gid)


class Catalogue(unittest.TestCase):
    def test_catalogue_complete_and_well_formed(self):
        ids = [g["id"] for g in Q.GATES]
        self.assertEqual(len(ids), len(set(ids)))
        products = {g["product"] for g in Q.GATES}
        self.assertEqual(products, {"textbook", "workbook", "anki", "interactive", "pages", "integrity"})
        for g in Q.GATES:
            self.assertIn(g["severity"], Q.SEVERITIES)
            self.assertTrue(g["rule"] and g["fix"] and g["section"])
        self.assertEqual(Q.catalogue()["id"], "mastery-quality-v1")
        self.assertEqual(len(Q.CHECKS), len({fn.__name__ for fn in Q.CHECKS}))

    def test_good_unit_has_no_unit_level_findings(self):
        r = Q.check(good_unit())
        self.assertEqual(r["findings"], [], json.dumps(r["findings"], ensure_ascii=False, indent=1))
        self.assertEqual(r["status"], "NO_MACHINE_FINDINGS")
        self.assertEqual(status(r, "PG-OVERFLOW"), "not_checked")                # no build: honest, not "pass"
        self.assertEqual(status(r, "IA-PERSIST"), "not_checked")

    def test_report_schema(self):
        u = good_unit()
        u["cards"][0].pop("context")
        r = Q.check(u)
        self.assertEqual(set(r), {"schema", "catalogue", "unit_id", "title", "checked_at", "status", "counts", "gates",
                                  "findings", "human_review", "learning_evaluation", "model_calls", "scope"})
        self.assertEqual((r["schema"], r["human_review"], r["learning_evaluation"], r["model_calls"]),
                         ("mastery-quality-report-v1", "HUMAN_REVIEW_PENDING", "NOT_RUN", 0))
        self.assertEqual(set(r["counts"]), set(Q.SEVERITIES))
        self.assertEqual(len(r["gates"]), len(Q.GATES))
        for f in r["findings"]:
            self.assertEqual(set(f), {"gate", "severity", "product", "section", "location", "message", "fix"})
        self.assertEqual(r["status"], "MAJOR_FINDINGS")
        self.assertEqual(r["counts"]["major"], 1)
        json.dumps(r)

    def test_html_and_markdown_report(self):
        u = good_unit()
        u["teaching"][0]["content"] = "Pfad /Users/jemand/kurs <script>"
        r = Q.check(u)
        html, md = Q.to_html(r), Q.to_markdown(r)
        self.assertIn('data-status="BLOCKERS"', html)
        self.assertIn("ersetzt nicht die Abnahme durch den Owner", html)
        self.assertNotIn("<script>", html)
        self.assertIn("INT-PRIVATE-PATHS", md)
        self.assertIn("Blocker", md)
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(sorted(Q.write(r, tmp)), ["quality.html", "quality.json", "quality.md"])
            self.assertEqual(json.loads((Path(tmp) / "quality.json").read_text(encoding="utf-8"))["status"], "BLOCKERS")


class UnitGates(unittest.TestCase):
    """Negative case per unit-level gate (the positive case is test_good_unit_has_no_unit_level_findings)."""

    def assertFinds(self, unit, gid, severity=None, **kw):
        r = Q.check(unit, **kw)
        hits = [f for f in r["findings"] if f["gate"] == gid]
        self.assertTrue(hits, f"{gid} not found: {gates_of(r)}")
        if severity:
            self.assertEqual({f["severity"] for f in hits}, {severity})
        self.assertEqual(status(r, gid), "fail")
        return hits

    def test_chain(self):
        u = good_unit()
        u["teaching"][0]["blocks"] = [b for b in u["teaching"][0]["blocks"] if b.get("kind") != "pitfall"]
        u["teaching"][0]["section_title"] = "Spalten"
        u["teaching"][0]["content"] = "Text."
        u["misconceptions"] = []
        u["assessments"] = [a for a in u["assessments"] if a["role"] != "contrast"]
        msg = self.assertFinds(u, "TB-CHAIN")[0]["message"]
        self.assertIn("(1) Warum", msg)
        self.assertIn("(6) Fehlvorstellung", msg)
        self.assertNotIn("(2)", msg)
        u = good_unit()
        u["teaching"] = [t for t in u["teaching"] if t["id"] != "teach/why"]
        u["assessments"][0].pop("solution_steps")                              # worked example without reasons
        self.assertIn("(4) Herleitung/Beweis", self.assertFinds(u, "TB-CHAIN")[0]["message"])

    def test_proof(self):
        u = good_unit()
        u["teaching"][0].pop("derivation")
        u["sources"][0]["locator"] = "Vorlesung Lineare Algebra"
        self.assertFinds(u, "TB-PROOF")
        u["claims"][0]["source_refs"] = ["own"]                                  # own derivation mark suffices
        self.assertNotIn("TB-PROOF", gates_of(Q.check(u)))

    def test_figure(self):
        u = good_unit()
        u["graphics"][0]["caption"] = "Ebene"
        u["teaching"][0]["blocks"] = [b for b in u["teaching"][0]["blocks"] if b["type"] != "graphic"]
        msg = self.assertFinds(u, "TB-FIGURE")[0]["message"]
        self.assertIn("Aussage", msg)
        self.assertIn("graphic-Block", msg)

    def test_locator(self):
        u = good_unit()
        u["sources"][0]["locator"] = "Vorlesung Lineare Algebra, WS"
        self.assertFinds(u, "TB-LOCATOR")
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "packet.json").write_text(json.dumps({"sources": [{"kind": "lecture_slides", "pages": [
                {"n": 1}, {"n": 2}, {"n": 3}]}]}), encoding="utf-8")
            u = good_unit()
            u["divergences"] = []
            self.assertNotIn("TB-LOCATOR", gates_of(Q.check(u, chapter_dir=tmp)))
            u["sources"][0]["locator"] = "Vorlesung 1, Folien 3–9"
            self.assertIn("nicht vor", self.assertFinds(u, "TB-LOCATOR", chapter_dir=tmp)[0]["message"])

    def test_divergence(self):
        u = good_unit()
        u.pop("divergences")
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFinds(u, "TB-DIVERGENCE", "minor", chapter_dir=tmp)
            (Path(tmp) / "authoring.json").write_text(json.dumps({"divergences": []}), encoding="utf-8")
            self.assertNotIn("TB-DIVERGENCE", gates_of(Q.check(u, chapter_dir=tmp)))
        u["teaching"][1]["content"] += " Die Folienform weicht in der Notation ab."
        with tempfile.TemporaryDirectory() as tmp:
            self.assertNotIn("TB-DIVERGENCE", gates_of(Q.check(u, chapter_dir=tmp)))

    def test_stages(self):
        u = good_unit()
        u["assessments"] = [a for a in u["assessments"] if a.get("stage") != "transfer"]
        self.assertIn("Transfer", self.assertFinds(u, "WB-STAGES")[0]["message"])

    def test_solution(self):
        u = good_unit()
        a = u["assessments"][2]
        a["solution"], a["solution_steps"], a["rubric"] = "x = 3.", None, [{"criterion": "Ergebnis", "points": 1}]
        msgs = " ".join(f["message"] for f in self.assertFinds(u, "WB-SOLUTION"))
        self.assertIn("zu knapp", msgs)
        self.assertIn("Kein Prüfvermerk", msgs)

    def test_alt_routes(self):
        u = good_unit()
        for a in u["assessments"]:
            a["solution"] = a["solution"].replace("alternativ", "dann")
            a["rubric"] = [{"criterion": "Ansatz", "points": 1}, {"criterion": "Ergebnis", "points": 1}]
        self.assertFinds(u, "WB-ALT-ROUTES", "minor")

    def test_find_error(self):
        u = good_unit()
        u["assessments"] = [a for a in u["assessments"] if a["id"] != "task/error-2"]
        self.assertIn("Nur 1", self.assertFinds(u, "WB-FIND-ERROR")[0]["message"])

    def test_proof_production(self):
        u = good_unit()
        for a in u["assessments"]:
            if a["stage"] != "worked_example":
                a["prompt"] = "Welche Aussage ist richtig?"
        self.assertFinds(u, "WB-PROOF-PRODUCTION")

    def test_card_lint(self):
        u = good_unit()
        u["cards"][0]["front"] = "Was? Und warum?"
        self.assertFinds(u, "AN-LINT", "blocker")

    def test_deflist(self):
        u = good_unit()
        u["cards"].append({"key": "map/def", "kind": "concept", "front": "Was ist eine lineare Abbildung?",
                           "answer": "Additiv und homogen.", "context": "Kapitel 1.", "competency_ids": ["map/columns"]})
        hits = self.assertFinds(u, "AN-DEFLIST")
        self.assertEqual({h["location"] for h in hits}, {"Karte map/def"})
        u["cards"][0]["kind"] = "fact"                                         # 2 of 2 concept/fact cards
        self.assertIn("Kartensatz", {h["location"] for h in self.assertFinds(u, "AN-DEFLIST")})
        u = good_unit()
        u["cards"][0]["answer"] = "a; b; c; d"
        self.assertFinds(u, "AN-DEFLIST")

    def test_context(self):
        u = good_unit()
        u["cards"][0]["context"] = " "
        self.assertFinds(u, "AN-CONTEXT")

    def test_visual(self):
        u = good_unit()
        u["cards"][0].pop("figure")
        self.assertFinds(u, "AN-VISUAL")

    def test_identity(self):
        u = good_unit()
        u["cards"].append(copy.deepcopy(u["cards"][0]))
        self.assertIn("Doppelte", self.assertFinds(u, "AN-IDENTITY", "blocker")[0]["message"])
        with tempfile.TemporaryDirectory() as tmp:
            ch, build = Path(tmp), Path(tmp) / "build"
            (build / ".em-state").mkdir(parents=True)
            (ch / "build-record.json").write_text(json.dumps({"unit_id": "test/old"}), encoding="utf-8")
            (build / ".em-state" / "anki-0.json").write_text(json.dumps({"unit_id": "test/old"}), encoding="utf-8")
            (build / "anki_report.json").write_text(json.dumps({"update_delta": {"retirement_candidates": ["x/y"]}}),
                                                    encoding="utf-8")
            hits = self.assertFinds(good_unit(), "AN-IDENTITY", build_dir=build, chapter_dir=ch)
            self.assertEqual(sorted(h["severity"] for h in hits), ["blocker", "blocker", "minor"])

    def test_scene_and_motion_rules(self):
        u = good_unit()
        u["interactions"][0]["model_ref"] = "scaled_dot_product_attention"
        self.assertIn("Keine Mastery-Motion-Szene", self.assertFinds(u, "IA-SCENE")[0]["message"])
        from exam_mastery.motion import embed
        scene = embed.scene_for_interaction(good_unit()["interactions"][0])
        broken = copy.deepcopy(scene)
        broken["missions"], broken["terms"] = [], {}
        for st in broken["steps"]:
            st.pop("checkpoint", None)
        orig = embed.scene_for_interaction
        embed.scene_for_interaction = lambda i: broken
        try:
            msg = self.assertFinds(good_unit(), "IA-MOTION-RULES")[0]["message"]
        finally:
            embed.scene_for_interaction = orig
        for rule in ("V3", "V4", "V6"):
            self.assertIn(rule, msg)

    def test_persist(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "Interaktiv" / "index.html"
            page.parent.mkdir()
            page.write_text("<html>ohne Speicher</html>", encoding="utf-8")
            self.assertFinds(good_unit(), "IA-PERSIST", build_dir=tmp)
            page.write_text('<script>localStorage em-practice-v1 "attempt" "hint" "solution_reveal"</script>',
                            encoding="utf-8")
            self.assertEqual(status(Q.check(good_unit(), build_dir=tmp), "IA-PERSIST"), "pass")

    def test_review_and_learning_eval(self):
        u = good_unit()
        u["authorship"]["human_status"] = "APPROVED"
        self.assertFinds(u, "INT-REVIEW", "blocker")
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "authoring.json").write_text(json.dumps({"learning_effect": "IMPROVED", "divergences": []}),
                                                      encoding="utf-8")
            self.assertFinds(good_unit(), "INT-LEARNING-EVAL", "blocker", chapter_dir=tmp)
            (Path(tmp) / "authoring.json").write_text(json.dumps({"learning_effect": "NOT_RUN", "divergences": []}),
                                                      encoding="utf-8")
            self.assertEqual(Q.check(good_unit(), chapter_dir=tmp)["findings"], [])

    def test_tutor_keys(self):
        u = good_unit()
        u["assessments"][3]["role"] = "transfer"
        u["assessments"][3]["machine_check"] = {"type": "numeric", "expected": 0.12345}
        u["assessments"][1]["hints"] = ["Das Ergebnis ist 0,1235."]
        self.assertFinds(u, "INT-TUTOR-KEYS", "blocker")
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "Interaktiv" / "index.html"
            page.parent.mkdir()
            data = {"assessments": [{"id": "t", "role": "retest", "solution": "x"}]}
            page.write_text('<script type="application/json" id="em-interactive-data">' + json.dumps(data) +
                            '</script>', encoding="utf-8")
            hits = self.assertFinds(good_unit(), "INT-TUTOR-KEYS", build_dir=tmp)
            self.assertIn("Interaktiv", hits[0]["location"])

    def test_private_paths(self):
        u = good_unit()
        u["sources"][0]["locator"] = "file:///Users/someone/Kurs/folien.pdf, Folie 3"
        self.assertFinds(u, "INT-PRIVATE-PATHS", "blocker")


@unittest.skipUnless(HAVE_PDF, "pymupdf not installed")
class PageGates(unittest.TestCase):
    def pdf(self, build, pages):
        """pages: list of callables(page) drawing onto a fresh A4 page."""
        doc = pymupdf.open()
        for draw in pages:
            draw(doc.new_page(width=595, height=842))
        Path(build).mkdir(parents=True, exist_ok=True)
        doc.save(Path(build) / "Lehrbuch.pdf")

    @staticmethod
    def body(page, n=40, y0=80):
        for k in range(n):
            page.insert_text((70, y0 + 16 * k), "Fließtext einer Zeile mit ausreichend vielen Wörtern.", fontsize=10.5)

    def check(self, *pages):
        with tempfile.TemporaryDirectory() as tmp:
            self.pdf(tmp, pages)
            return [(g, w, m) for g, w, m in Q.check_pdf(Path(tmp) / "Lehrbuch.pdf", "Lehrbuch")]

    def test_clean_document(self):
        self.assertEqual(self.check(self.body, self.body, self.body), [])

    def test_overflow_text_and_objects(self):
        def wide(page):
            self.body(page, 10)
            page.insert_text((540, 300), "zu breite Formel x + y + z", fontsize=10.5)
        found = self.check(self.body, wide, self.body)
        self.assertEqual([g for g, *_ in found], ["PG-OVERFLOW"])
        self.assertIn("S. 2", found[0][1])

        def cut(page):
            self.body(page, 10)
            page.draw_rect(pymupdf.Rect(500, 400, 640, 420), color=(0, 0, 0), fill=(0, 0, 0))
        self.assertIn("PG-OVERFLOW", [g for g, *_ in self.check(self.body, cut, self.body)])

        def offpage(page):  # print-engine fragment entirely outside the page: invisible, not a finding
            self.body(page, 40)
            page.draw_rect(pymupdf.Rect(100, -400, 300, -380), color=(0, 0, 0), fill=(0, 0, 0))
        self.assertEqual(self.check(self.body, offpage, self.body), [])

    def test_orphan_heading(self):
        def orphan(page):
            self.body(page, 38)
            page.insert_text((70, 760), "Abschnitt über Spalten", fontsize=16)
        self.assertEqual([g for g, *_ in self.check(self.body, orphan, self.body)], ["PG-ORPHAN-HEADING"])

        def fine(page):
            self.body(page, 20)
            page.insert_text((70, 420), "Abschnitt über Spalten", fontsize=16)
            self.body(page, 15, y0=450)
        self.assertEqual(self.check(self.body, fine, self.body), [])

    def test_near_empty(self):
        def rest(page):
            self.body(page, 2)
        self.assertEqual([g for g, *_ in self.check(self.body, rest, self.body)], ["PG-NEAR-EMPTY"])

        def short_section(page):  # starts with a heading: a short section, not a spill-over
            page.insert_text((70, 80), "Kurzer Abschnitt", fontsize=16)
            self.body(page, 2, y0=110)
        self.assertEqual(self.check(self.body, short_section, self.body), [])

    def test_links(self):
        def link(page):
            self.body(page)
            page.insert_link({"kind": pymupdf.LINK_GOTO, "from": pymupdf.Rect(70, 70, 200, 90), "page": 1,
                              "to": pymupdf.Point(0, 0)})
        self.assertEqual(self.check(self.body, link, self.body), [])
        with tempfile.TemporaryDirectory() as tmp:
            self.pdf(tmp, [self.body, link, self.body])
            doc = pymupdf.open(Path(tmp) / "Lehrbuch.pdf")
            xref = doc[1].get_links()[0]["xref"]
            doc.xref_set_key(xref, "A", "<</S/GoTo/D(fehlt)>>")                # named target that does not exist
            doc.save(Path(tmp) / "x.pdf")
            found = Q.check_pdf(Path(tmp) / "x.pdf", "Lehrbuch")
        self.assertIn("PG-LINKS", [g for g, *_ in found])

    def test_font_floor(self):
        def tiny(page):
            self.body(page)
            page.insert_text((70, 70), "Achse", fontsize=4.5)
        found = self.check(self.body, tiny, self.body)
        self.assertEqual([g for g, *_ in found], ["PG-FONT-FLOOR"])
        self.assertIn("4.5 pt", found[0][2])

    def test_private_path_in_pdf(self):
        def path(page):
            self.body(page)
            page.insert_text((70, 60), "/Users/jemand/Kurs/folien.pdf", fontsize=10)
        self.assertIn("INT-PRIVATE-PATHS", [g for g, *_ in self.check(self.body, path, self.body)])

    def test_gate_pages_in_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.pdf(tmp, [self.body, lambda p: self.body(p, 2), self.body])
            r = Q.check(good_unit(), build_dir=tmp)
        self.assertEqual(status(r, "PG-NEAR-EMPTY"), "fail")
        self.assertEqual(status(r, "PG-OVERFLOW"), "pass")


class ChapterCliAndView(unittest.TestCase):
    """build-chapter / quality exit codes on an imported synthetic course; the Kurse view links the report."""

    @classmethod
    def setUpClass(cls):
        from course_fixture import make_course
        from exam_mastery.mastery import courses as C
        cls.C = C
        cls.tmp = tempfile.TemporaryDirectory(prefix="mastery-quality-")
        base = Path(cls.tmp.name)
        cls.home = base / "Mastery"
        C.import_course(make_course(base / "Kurs"), title="Entscheidungsprobleme", home=cls.home, log=lambda *_: None)
        C.make_packet("kurs", "04-policy-gradient", cls.home, log=lambda *_: None)
        cls.chdir = cls.home / "courses/kurs/chapters/04-policy-gradient"
        cls.unit = json.loads((REPO / "fixtures/experience_reference.json").read_text(encoding="utf-8"))
        cls.unit["unit_id"] = "course/kurs/04-policy-gradient"
        (cls.chdir / "authoring.json").write_text(json.dumps({"schema": "mastery-authoring-record-v1",
                                                              "author": {"kind": "human"}}), encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def cli(self, *args):
        return subprocess.run([sys.executable, "-m", "exam_mastery.mastery", "--home", str(self.home), *args],
                              cwd=REPO, capture_output=True, text=True, timeout=600,
                              env={**os.environ, "PYTHONPATH": str(REPO)})

    def write_unit(self, unit):
        (self.chdir / "unit.json").write_text(json.dumps(unit, ensure_ascii=False), encoding="utf-8")

    def test_1_exit_codes_and_report(self):
        self.write_unit(self.unit)
        run = self.cli("build-chapter", "kurs", "04-policy-gradient")
        self.assertEqual(run.returncode, 0, run.stderr)                     # major findings only: exit 0
        self.assertIn("Qualitätsprüfung (mastery-quality-v1): 0 Blocker", run.stdout)
        report = json.loads((self.chdir / "build/quality.json").read_text(encoding="utf-8"))
        self.assertEqual((report["unit_id"], report["status"]), (self.unit["unit_id"], "MAJOR_FINDINGS"))
        self.assertEqual(status(report, "PG-OVERFLOW"), "pass")             # built PDFs were measured
        self.assertTrue((self.chdir / "build/quality.html").is_file())
        lib = json.loads((self.home / "library.json").read_text(encoding="utf-8"))
        entry = next(u for u in lib["units"] if u["slug"] == "kurs-04-policy-gradient")
        self.assertEqual(entry["quality"]["report"], "courses/kurs/chapters/04-policy-gradient/build/quality.html")
        bad = copy.deepcopy(self.unit)
        bad["teaching"][0]["content"] += " Siehe /Users/jemand/Kurs."
        self.write_unit(bad)
        run = self.cli("quality", "kurs", "04-policy-gradient")             # no rebuild, report refreshed
        self.assertEqual(run.returncode, 3, run.stdout)
        self.assertIn("INT-PRIVATE-PATHS", run.stdout)
        run = self.cli("build-chapter", "kurs", "04-policy-gradient")
        self.assertEqual(run.returncode, 3, run.stdout + run.stderr)
        self.assertIn("Blocker gefunden", run.stderr)
        run = self.cli("build-chapter", "kurs", "04-policy-gradient", "--allow-blockers")
        self.assertEqual(run.returncode, 0, run.stderr)
        run = self.cli("quality", "kurs", "04-policy-gradient", "--json", "--allow-blockers")
        data = json.loads(run.stdout)
        where = {f["location"].split(" S.")[0] for f in data["findings"] if f["gate"] == "INT-PRIVATE-PATHS"}
        self.assertEqual(data["counts"]["blocker"], len([f for f in data["findings"] if f["severity"] == "blocker"]))
        self.assertTrue({"unit.json", "Lehrbuch", "Interaktiv/index.html"} <= where, where)   # source and products
        self.write_unit(self.unit)
        self.assertEqual(self.cli("build-chapter", "kurs", "04-policy-gradient").returncode, 0)
        st = {c["id"]: c for c in self.C.course_status("kurs", self.home)["chapters"]}["04-policy-gradient"]
        self.assertEqual(st["quality"]["status"], "MAJOR_FINDINGS")
        self.assertTrue(st["quality"]["current"])

    @unittest.skipUnless(HAVE_BROWSER, "playwright not installed")
    def test_2_kurse_view_links_report(self):
        from exam_mastery.mastery.server import ALLOWED, start_in_thread
        self.write_unit(self.unit)
        self.C.build_chapter("kurs", "04-policy-gradient", self.home, log=lambda *_: None)
        server, base = start_in_thread(self.home, import_base=Path(self.tmp.name))
        errors, external = [], []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
                try:
                    pg = browser.new_page()
                    pg.on("pageerror", lambda e: errors.append(str(e)))
                    pg.on("request", lambda r: external.append(r.url) if not r.url.startswith((base, "data:")) else None)
                    pg.goto(base + "#kurse")
                    pg.wait_for_selector('#app[data-ready="1"]')
                    row = 'tr[data-chapter="04-policy-gradient"]'
                    line = pg.inner_text(row + " .m-quality")
                    self.assertIn("Maschinelle Qualitätsprüfung", line)
                    self.assertIn("0 Blocker", line)
                    self.assertEqual(pg.get_attribute(row + " .m-quality", "data-quality"), "MAJOR_FINDINGS")
                    href = pg.get_attribute(row + ' a[data-quality-report="04-policy-gradient"]', "href")
                    self.assertEqual(href, "courses/kurs/chapters/04-policy-gradient/build/quality.html")
                    self.assertIsNotNone(ALLOWED.match("/" + href))
                    pg.click(row + ' a[data-quality-report="04-policy-gradient"]')
                    pg.wait_for_selector("#quality-status")
                    self.assertIn("Qualitätsbericht", pg.title())
                    self.assertEqual(pg.get_attribute("#quality-status", "data-status"), "MAJOR_FINDINGS")
                    self.assertGreater(pg.locator("tr[data-gate-status]").count(), 20)
                finally:
                    browser.close()
        finally:
            server.shutdown()
            server.server_close()
        self.assertEqual(errors, [])
        self.assertEqual(external, [])


if __name__ == "__main__":
    unittest.main()
