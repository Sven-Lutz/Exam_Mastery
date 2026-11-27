"""Course import on a second, contrasting domain: a proof-heavy mathematics course laid out the way German math
departments ship it (generated, public-safe fixture; no real course material).

Covers what the first (applied-ML) course never exercised: decks named 'Folien n' (trailing number, title only on the
title page, title-page number differing from the file name), a long script with a PDF outline next to the decks (split
into sections and attached by content in course order, unmatched sections become chapters, back matter ignored),
'Loesungsvorschlag n' answering 'Uebungsblatt n' but not 'Tutorium n', download copy suffixes '(1)', URL-encoded names
('Loesungsvorschlag_202' = 'Loesungsvorschlag 2'), weekly sheet series aligned monotonically, TeX text extraction
artefacts ('Vektorr¨aume', '1 ̸ = −1', 'x 7→ y', ligatures), theorem-based competency proposals, and packets that only
carry the chapter's script pages."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

TOPICS = {
    "gruppen": ("Gruppen und K¨orper", ["Gruppe Gruppenaxiome neutrales Element inverses Element assoziativ",
                                             "K¨orper Addition Multiplikation kommutativ distributiv Primk¨orper"]),
    "vektor": ("Vektorr¨aume und Basen", ["Vektorraum Untervektorraum Linearkombination Erzeugendensystem",
                                               "Basis linear unabh¨angig Dimension Basiserg¨anzungssatz"]),
    "abb": ("Lineare Abbildungen", ["lineare Abbildung Kern Bild Rang injektiv surjektiv Isomorphismus",
                                    "Homomorphiesatz Dimensionsformel Kern Bild Rang Abbildungsmatrix"]),
    "det": ("Determinanten", ["Determinante Permutation Signum alternierend multilinear Leibniz",
                              "Determinantenmultiplikationssatz Cramersche Regel Entwicklung Laplace"]),
}


def _pdf(path, pages, landscape=True, toc=None):
    import pymupdf
    doc = pymupdf.open()
    w, h = (842, 595) if landscape else (595, 842)
    for title, lines in pages:
        page = doc.new_page(width=w, height=h)
        page.insert_text((40, 60), title, fontsize=22)
        y = 110
        for line in lines:
            page.insert_text((50, y), line, fontsize=12)
            y += 20
    if toc:
        doc.set_toc(toc)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(path)
    doc.close()


def make_math_course(root):
    root = Path(root)
    deck = lambda no, key, extra=(): [(f"Vorlesung {no}: {TOPICS[key][0]}", ["Datum"]),  # noqa: E731
                                      ("Wiederholung", TOPICS[key][1]),
                                      (TOPICS[key][0].split()[0], list(TOPICS[key][1]) + list(extra))]
    _pdf(root / "Slides" / "Folien 1.pdf", deck(1, "gruppen", ["In jedem K¨orper gilt 1 ̸= 0 und 0 · x = 0."]))
    _pdf(root / "Slides" / "Folien 2.pdf", deck(2, "vektor", ["Begriﬀe: Basis, Dimension"]))
    _pdf(root / "Slides" / "Folien 3.pdf", deck(5, "abb", [
        "Satz 9.21 (Dimensionsformel) F¨ur lineares Φ : V → W gilt dim V = dim Kern Φ + Rang Φ.",
        "Satz 9.11 F¨ur lineare Abbildungen gilt: Φ injektiv genau dann, wenn Kern Φ = {0}.",
        "Abbildung x 7→ Ax"]))
    script = [("LINEARE ALGEBRA", ["Skript zur Vorlesung"]), ("Inhaltsverzeichnis", ["1 Gruppen 2", "2 Vektorr¨aume 6"])]
    for key in ("gruppen", "vektor", "abb", "det"):
        for i in range(4):
            script.append((TOPICS[key][0], [f"{line} Absatz {i}" for line in TOPICS[key][1]] * 3))
    script.append(("Literatur", ["Lehrbuch der linearen Algebra", "Gruppen Vektorr¨aume Abbildungen Determinanten"]))
    toc = [[1, "I Grundlagen", 3], [2, "Gruppen und Körper", 3], [2, "Vektorräume", 7],
           [1, "II Abbildungen", 11], [2, "Lineare Abbildungen", 11], [2, "Determinanten", 15], [1, "Literatur", 19]]
    _pdf(root / "Vorlesungsskript.pdf", script, landscape=False, toc=toc)
    sheets = {1: "gruppen", 2: "vektor", 3: "abb", 4: "det"}
    for no, key in sheets.items():
        name = f"Uebungsblatt {no} (1).pdf" if no == 1 else f"Uebungsblatt {no}.pdf"
        _pdf(root / "Übungsblätter" / name, [("Lineare Algebra I", ["Aufgabe 1 (4 Punkte) Zeigen Sie:"] + TOPICS[key][1])],
             landscape=False)
        _pdf(root / "Tutorium" / f"Tutorium {no}.pdf", [("Lineare Algebra I", ["Aufgabe 1 Zeigen Sie:"] + TOPICS[key][1])],
             landscape=False)
    _pdf(root / "Übungsblätter" / "Loesungsvorschlag 1.pdf", [("Lineare Algebra I", ["Lösung Aufgabe 1"] + TOPICS["gruppen"][1])],
         landscape=False)
    _pdf(root / "Übungsblätter" / "Loesungsvorschlag_202.pdf", [("Lineare Algebra I", ["Lösung Aufgabe 1"] + TOPICS["vektor"][1])],
         landscape=False)


class MathCourseImport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from exam_mastery.mastery import courses as C
        cls.C = C
        cls.tmp = tempfile.TemporaryDirectory(prefix="em-math-course-")
        base = Path(cls.tmp.name)
        cls.home = base / "home" / "Mastery"
        cls.src = base / "home" / "Studium" / "LA"
        make_math_course(cls.src)
        cls.s = C.import_course(cls.src, slug="la", title="Lineare Algebra", home=cls.home, base=base / "home",
                                log=lambda *_: None)
        cls.course = json.loads((cls.home / "courses" / "la" / "course.json").read_text(encoding="utf-8"))
        cls.files = {Path(f["rel_path"]).name: f for f in cls.course["files"]}
        cls.ch = {c["id"]: c for c in cls.course["chapters"]}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_split_number_and_text_repair(self):
        C = self.C
        self.assertEqual(C.split_number("Folien 12"), (12, "Folien"))
        self.assertEqual(C.split_number("Uebungsblatt 1 (1)"), (1, "Uebungsblatt"))
        self.assertEqual(C.split_number("Loesungsvorschlag 10"), (10, "Loesungsvorschlag"))
        self.assertEqual(C.split_number("05 - Actor Critic"), (5, "Actor Critic"))
        self.assertEqual(C.split_number("Klausur 2024")[0], None)            # a year is not a lecture number
        self.assertEqual(C.split_number("Guided Diffusion 2")[0], None)      # a topic title keeps no trailing number
        self.assertEqual(C.clean_pdf_text("Vektorr¨aume, ¨ Aquivalenz, Begriﬀe, 1 ̸ = −1, x 7→ y"),
                         "Vektorräume, Äquivalenz, Begriffe, 1 ≠ −1, x ↦ y")
        self.assertEqual(C.title_page([{"title": "Vorlesung 19: Lineare Abbildungen, Darstellende Matrizen"}]),
                         (19, "Lineare Abbildungen, Darstellende Matrizen"))

    def test_decks_numbered_titled_and_mismatch_reported(self):
        decks = [c for c in self.course["chapters"] if c["number"] is not None]
        self.assertEqual([c["id"] for c in decks], ["01-gruppen-und-koerper", "02-vektorraeume-und-basen",
                                                    "03-lineare-abbildungen"])
        self.assertEqual(self.files["Folien 1.pdf"]["title"], "Gruppen und Körper")
        self.assertEqual(self.files["Folien 1.pdf"]["title_basis"], "Titelseite")
        codes = [w["code"] for w in self.course["warnings"]]
        self.assertNotIn("UNNUMBERED_LECTURE", codes)
        mism = [w for w in self.course["warnings"] if w["code"] == "LECTURE_NUMBER_MISMATCH"]
        self.assertEqual([w["provenance"][0]["rel_path"] for w in mism], ["Slides/Folien 3.pdf"])

    def test_script_split_by_outline_in_course_order(self):
        script = self.files["Vorlesungsskript.pdf"]
        self.assertEqual([s["title"] for s in script["sections"]],
                         ["Gruppen und Körper", "Vektorräume", "Lineare Abbildungen", "Determinanten"])
        self.assertNotIn("x-vorlesungsskript", self.ch)                     # no 297-page monster chapter
        fid = script["file_id"]
        self.assertEqual(self.ch["01-gruppen-und-koerper"]["source_pages"][fid], [[3, 6]])
        self.assertEqual(self.ch["03-lineare-abbildungen"]["source_pages"][fid], [[11, 14]])
        self.assertIn("Skriptabschnitt „Lineare Abbildungen“", self.ch["03-lineare-abbildungen"]["attach_basis"][fid])
        self.assertEqual(self.ch["x-determinanten"]["source_pages"][fid], [[15, 18]])   # no deck: own chapter
        self.assertFalse(any("Literatur" in c["title"] for c in self.course["chapters"]))  # back matter ignored
        self.assertIn("SCRIPT_SPLIT", [w["code"] for w in self.course["warnings"]])

    def test_solutions_follow_their_series_and_sheets_run_in_order(self):
        missing = sorted(Path(w["provenance"][0]["rel_path"]).name for w in self.course["warnings"]
                         if w["code"] == "EXERCISE_WITHOUT_SOLUTION")
        self.assertEqual(missing, ["Tutorium 1.pdf", "Tutorium 2.pdf", "Tutorium 3.pdf", "Tutorium 4.pdf",
                                   "Uebungsblatt 3.pdf", "Uebungsblatt 4.pdf"])
        by = {f["file_id"]: Path(f["rel_path"]).name for f in self.course["files"]}
        where = {by[x]: c["id"] for c in self.course["chapters"] for x in c["exercises"] + c["solutions"]}
        self.assertEqual(where["Uebungsblatt 1 (1).pdf"], "01-gruppen-und-koerper")
        self.assertEqual(where["Loesungsvorschlag 1.pdf"], "01-gruppen-und-koerper")
        self.assertEqual(where["Loesungsvorschlag_202.pdf"], where["Uebungsblatt 2.pdf"])
        self.assertEqual(where["Uebungsblatt 3.pdf"], "03-lineare-abbildungen")
        self.assertEqual(where["Uebungsblatt 4.pdf"], "x-determinanten")
        order = [c["id"] for c in self.course["chapters"]]
        seq = [order.index(where[f"Tutorium {n}.pdf"]) for n in range(1, 5)]
        self.assertEqual(seq, sorted(seq))
        self.assertIn("Reihenfolge der Serie", self.ch["03-lineare-abbildungen"]["attach_basis"][
            next(k for k, v in by.items() if v == "Uebungsblatt 3.pdf")])

    def test_theorem_competencies_and_clean_text(self):
        comp = [c["text"] for c in self.ch["03-lineare-abbildungen"]["competencies_proposed"]]
        self.assertEqual(comp[0], "Satz 9.21 (Dimensionsformel)")
        self.assertTrue(any(c.startswith("Satz 9.11: ") for c in comp))
        self.assertFalse(any(c.startswith(("Vorlesung", "Wiederholung")) for c in comp))
        pages = self.C._pages(self.home / "courses" / "la", self.files["Folien 1.pdf"])
        text = " ".join(p["text"] for p in pages)
        self.assertIn("Körper", text)
        self.assertNotIn("¨", text)

    def test_packet_carries_only_the_chapter_script_pages_and_merge_unions_ranges(self):
        res = self.C.make_packet("la", "03-lineare-abbildungen", home=self.home, log=lambda *_: None)
        packet = json.loads(Path(res["packet"]).read_text(encoding="utf-8"))
        script = next(s for s in packet["sources"] if s["rel_path"] == "Vorlesungsskript.pdf")
        self.assertEqual([p["n"] for p in script["pages"]], [11, 12, 13, 14])
        self.assertEqual(script["selection"], "Skriptabschnitte: S. 11–14")
        fid = self.files["Vorlesungsskript.pdf"]["file_id"]
        self.C.set_overrides("la", {"chapters": {"x-determinanten": {"merge_into": "03-lineare-abbildungen"}}},
                                 self.home)
        course = json.loads((self.home / "courses" / "la" / "course.json").read_text(encoding="utf-8"))
        merged = {c["id"]: c for c in course["chapters"]}["03-lineare-abbildungen"]
        self.assertEqual(merged["source_pages"][fid], [[11, 14], [15, 18]])


if __name__ == "__main__":
    unittest.main()
