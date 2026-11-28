import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

import markdown
import yaml

from exam_mastery.mastery import MasteryError
from exam_mastery.mastery.knowledge import export_course
from exam_mastery.mastery.courses import COURSE_SCHEMA

REPO = Path(__file__).resolve().parents[1]


class KnowledgeExport(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.home = Path(temp.name).resolve()
        self.course = self.home / "courses/test"
        self.chapter = self.course / "chapters/01-test"
        self.chapter.mkdir(parents=True)
        self.record = {"schema": COURSE_SCHEMA, "slug": "test", "title": "Geometrie",
                       "chapters": [{"id": "01-test", "title": "Identität"}]}
        (self.course / "course.json").write_text(json.dumps(self.record))
        self.unit = json.loads((REPO / "fixtures/experience_binomial_reference.json").read_text())
        self.unit["teaching"][0]["blocks"] = [
            {"type": "definition", "id": "def/area", "term": "Fläche", "md": "Produkt positiver Seitenlängen."}]
        self.save()

    def save(self):
        (self.chapter / "unit.json").write_text(json.dumps(self.unit))

    def export(self):
        return export_course("test", self.home).parent

    def test_parser_graph_updates_and_source_changes(self):
        folder = self.export()
        personal = folder.parent / "Mastery-Notizen/Mein Beweis.md"
        personal.write_text("Eigene Herleitung")
        before = {p.name: p.stat().st_ino for p in folder.glob("*.md")}
        self.assertEqual(folder, self.export())
        for p in folder.glob("*.md"):
            self.assertEqual(before[p.name], p.stat().st_ino)
            content = p.read_text()
            if content.startswith("---"):
                _, props, body = content.split("---\n", 2)
                self.assertTrue(yaml.safe_load(props)["em_generated"])
                self.assertIn("<h1>", markdown.markdown(body))
                for dest in re.findall(r"\[\[([^|\]]+)\|", body):
                    self.assertTrue((folder / (dest + ".md")).is_file(), dest)
        self.unit["title"] = "Neuer Titel"
        self.unit["teaching"][0]["blocks"][0]["term"] = "Rechteckfläche"
        self.unit["sources"][0]["locator"] += " / Fassung B"
        self.save()
        folder = self.export()
        self.assertEqual(set(before), {p.name for p in folder.glob("*.md")})
        self.assertIn("Fassung B", next(folder.glob("Quelle-*.md")).read_text())
        self.assertIn("Rechteckfläche", next(folder.glob("Definition-*.md")).read_text())
        self.assertEqual(personal.read_text(), "Eigene Herleitung")
        concept = next(folder.glob("Kompetenz-*.md"))
        inode = concept.stat().st_ino
        self.unit["sources"][0]["locator"] += " / Seite 2"
        self.save()
        self.export()
        self.assertEqual(concept.stat().st_ino, inode)

    def test_conflicts_and_missing_references_block_publication(self):
        folder = self.export()
        source = next(folder.glob("Quelle-*.md"))
        source.write_text("Manuelle Ergänzung")
        with self.assertRaisesRegex(MasteryError, "Exportkonflikt"):
            self.export()
        self.assertEqual(source.read_text(), "Manuelle Ergänzung")
        self.assertEqual(len(list((folder.parent / "Konflikte").glob("*.conflict"))), 1)
        old = (folder / ".mastery-manifest.json").read_bytes()
        self.unit["claims"][0]["source_refs"] = ["absent"]
        self.save()
        with self.assertRaisesRegex(MasteryError, "referen|source_refs"):
            self.export()
        self.assertEqual(old, (folder / ".mastery-manifest.json").read_bytes())

    def test_process_interruption_leaves_complete_generation(self):
        folder = self.export()
        old = (folder / ".mastery-manifest.json").read_bytes()
        self.unit["title"] = "Wiederaufnahme"
        self.save()
        script = ("import os,sys; from exam_mastery.mastery import knowledge_publish as p; "
                  "from exam_mastery.mastery.knowledge import export_course; "
                  "p._install=lambda *args: os._exit(17); export_course('test',sys.argv[1])")
        result = subprocess.run([sys.executable, "-c", script, str(self.home)], cwd=REPO)
        self.assertEqual(result.returncode, 17)
        self.assertEqual(old, (folder / ".mastery-manifest.json").read_bytes())
        self.export()
        self.assertIn("Wiederaufnahme", next(folder.glob("Kapitel-*.md")).read_text())

    def test_planned_chapter_identity_and_equation_gate(self):
        unit = self.chapter / "unit.json"
        unit.unlink()
        folder = self.export()
        planned = next(folder.glob("Kapitel-*.md"))
        self.save()
        self.export()
        self.assertTrue(planned.is_file())
        original = (folder / ".mastery-manifest.json").read_bytes()
        check = self.unit["teaching"][1]["derivation"]["steps"][0]["math_check"]
        check["rhs"] = "a^2+b^2"
        self.save()
        with self.assertRaises(MasteryError):
            self.export()
        self.assertEqual((folder / ".mastery-manifest.json").read_bytes(), original)
