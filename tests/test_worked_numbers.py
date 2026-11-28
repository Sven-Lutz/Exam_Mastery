import json
from pathlib import Path
import tempfile
import unittest

from exam_mastery.learning import experience, experience_books
from exam_mastery.mastery import quality


class WorkedNumbers(unittest.TestCase):
    def setUp(self):
        repo = Path(__file__).resolve().parents[1]
        self.unit = json.loads((repo / "fixtures/experience_binomial_reference.json").read_text())
        self.task = self.unit["assessments"][0]
        self.task["machine_check"] = {"type": "numeric", "expected": 25}

    def test_wrong_printed_value_blocks_artifact_with_correct_answer_key(self):
        self.task["solution"] = "Bei a=2 und b=3 beträgt die Quadratfläche 24."
        self.assertFalse(experience.validate(self.unit)["valid"])
        report = quality.check(self.unit)
        self.assertTrue(any(f["severity"] == "blocker" and f["gate"] == "WB-NUMERIC" for f in report["findings"]))
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                experience_books.publish(self.unit, td)
            self.assertFalse((Path(td) / "Arbeitsbuch.pdf").exists())

    def coverage(self):
        rows = quality.check(self.unit)["worked_coverage"]
        return next(r for r in rows if r["task"] == self.task["id"])

    def test_bound_intermediate_result_and_changed_task_parameters(self):
        scene = self.unit["interactions"][0]
        variant = scene["variants"][1]
        self.task["solution_oracle"] = {"interaction": scene["id"], "variant": variant["label"]}
        self.task["solution_steps"] = [["ab = 6", "Produkt der verschiedenen Seiten."]]
        self.task["solution"] = "Quadratfläche = 25"
        results = self.coverage()
        self.assertEqual(results["counts"], {"CHECKED": 2, "BLOCKER": 0, "UNVERIFIED": 1})
        self.task["solution_steps"][0][0] = "ab = 5"
        self.assertFalse(experience.validate(self.unit)["valid"])
        self.assertEqual(self.coverage()["counts"]["BLOCKER"], 1)
        variant["parameters"]["a"] = 4
        self.assertEqual(self.coverage()["counts"]["BLOCKER"], 2)

    def test_rounded_exact_symbolic_and_unverifiable(self):
        cases = [
            ("1 / 3 ≈ 0,33", "CHECKED"), ("1 / 3 = 0.33", "BLOCKER"),
            ("1 / 3 ≈ 0.34", "BLOCKER"), ("1 / 0 = 0", "BLOCKER"),
            ("Polynomidentität: (a-b)^2 = a^2-2*a*b+b^2", "CHECKED"),
            ("Polynomidentität: (a-b)^2 = a^2+2*a*b+b^2", "BLOCKER"),
            ("Polynomidentität: a/a = 1", "UNVERIFIED"),
            ("Damit folgt die Behauptung aus dem Zwischenwertsatz.", "UNVERIFIED"),
            ("Der Irrtum wäre: 2 + 2 = 5.", "UNVERIFIED"),
            ("Für a=-2 und b=3 ist die Quadratfläche 1.", "UNVERIFIED"),
        ]
        for text, status in cases:
            with self.subTest(text=text):
                self.task["solution"] = text
                self.assertEqual(self.coverage()["counts"][status], 1)

    def test_unresolved_reference_fails_closed(self):
        self.task["solution_oracle"] = {"interaction": "unknown", "variant": "unknown"}
        self.assertFalse(experience.validate(self.unit)["valid"])
        self.assertEqual(self.coverage()["counts"]["BLOCKER"], 1)
