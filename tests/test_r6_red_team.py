"""R6 red-team review: structural and traceability checks.

These checks keep the red-team findings reproducible and traceable to the frozen
policy index, the engine rules and the programme's critical defects. They cannot
show that a finding is right: the review was written by an agent of the same model
family as the workstream authors and is not an independent human review.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R6 = ROOT / "docs" / "research" / "workstreams" / "r6"
FINDINGS = R6 / "red_team_findings.json"
INDEX = R6 / "policy_index.json"
PRINCIPLES = ROOT / "exam_mastery" / "knowledge" / "principles.json"
REPORT = ROOT / "docs" / "research" / "workstreams" / "RED_TEAM_REVIEW.md"

KINDS = {"universal_rule", "domain_failure", "conflict", "measurement", "architecture", "owner_decision"}
SEVERITIES = {"blocker", "major", "minor"}
REQUIRED = ("id", "kind", "domain", "targets", "scenario", "failure", "severity", "evidence",
            "own_falsifier_catches", "recommended_change", "falsification_test")
REQUIRED_DOMAINS = {"math_proof", "law", "clinical", "code_debugging", "cad_spatial", "craft_or_lab"}
ARCHITECTURES = {"A", "B", "C"}
VERDICTS = {"over_claim", "under_claim", "consistent", "scope_over_generalised", "category_error", "compound_masking"}
CERTAINTY = {"high", "moderate", "low", "very_low", "normative"}
CD = re.compile(r"CD-[1-9][0-9]*")


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


class RedTeamFindings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load(FINDINGS)
        cls.findings = cls.doc["findings"]
        index = load(INDEX)
        cls.policies = {p["id"]: p for p in index["policies"]}
        principles = load(PRINCIPLES)
        cls.rules = {r["id"] for p in principles["principles"] for r in p.get("engine_rules", [])}

    def test_schema_and_required_fields(self):
        self.assertEqual(self.doc["schema"], "mastery-red-team/1")
        self.assertEqual(self.doc.get("learning_evaluation"), "NOT_RUN")
        for f in self.findings:
            for key in REQUIRED:
                self.assertIn(key, f, f"{f.get('id')}: missing {key}")
            self.assertIn(f["kind"], KINDS, f["id"])
            self.assertIn(f["severity"], SEVERITIES, f["id"])
            self.assertIn(f["own_falsifier_catches"], (True, False, "partially"), f["id"])
            self.assertTrue(f["targets"], f"{f['id']}: no targets")
            self.assertTrue(f["evidence"], f"{f['id']}: no evidence locators")
            for key in ("scenario", "failure", "recommended_change", "falsification_test"):
                self.assertTrue(str(f[key]).strip(), f"{f['id']}: empty {key}")

    def test_ids_unique_and_well_formed(self):
        ids = [f["id"] for f in self.findings]
        self.assertEqual(len(ids), len(set(ids)), "duplicate finding ids")
        for i in ids:
            self.assertRegex(i, r"^RT-\d{2,3}$")

    def test_every_target_resolves(self):
        for f in self.findings:
            for t in f["targets"]:
                ok = t in self.policies or t in self.rules or CD.fullmatch(t)
                self.assertTrue(ok, f"{f['id']}: target {t} is neither a policy id, an engine rule id nor a CD-n id")

    def test_cd_targets_exist_in_programme_range(self):
        # PROGRAMME_STATE lives on another branch; the frozen range at review time is CD-1..CD-8.
        for f in self.findings:
            for t in f["targets"]:
                if CD.fullmatch(t):
                    self.assertTrue(1 <= int(t.split("-")[1]) <= 8, f"{f['id']}: unknown {t}")

    def test_each_required_domain_has_a_falsifying_failure(self):
        covered = {f["domain"] for f in self.findings if f["kind"] == "domain_failure"}
        missing = REQUIRED_DOMAINS - covered
        self.assertFalse(missing, f"domains without domain_failure: {sorted(missing)}")

    def test_each_architecture_is_challenged(self):
        covered = {f.get("architecture") for f in self.findings if f["kind"] == "architecture"}
        missing = ARCHITECTURES - covered
        self.assertFalse(missing, f"architectures without finding: {sorted(missing)}")

    def test_owner_decisions_and_conflicts_present(self):
        kinds = {f["kind"] for f in self.findings}
        self.assertTrue(KINDS <= kinds, f"missing kinds: {sorted(KINDS - kinds)}")

    def test_certainty_spot_checks(self):
        checks = self.doc["certainty_spot_checks"]
        self.assertGreaterEqual(len(checks), 12)
        seen = set()
        for c in checks:
            self.assertIn(c["policy"], self.policies, c["policy"])
            self.assertNotIn(c["policy"], seen, f"duplicate spot check {c['policy']}")
            seen.add(c["policy"])
            self.assertEqual(c["stated"], self.policies[c["policy"]]["certainty"], f"{c['policy']}: stated certainty differs from index")
            self.assertIn(c["verdict"], VERDICTS, c["policy"])
            self.assertTrue(c["evidence_checked"], f"{c['policy']}: no evidence checked")
            self.assertTrue(str(c.get("note", "")).strip(), f"{c['policy']}: no note")

    def test_no_self_assigned_quality_or_validation_claims(self):
        # Negations such as 'unvalidierter Klassifikator' or 'not validated' are allowed; positive claims are not.
        text = json.dumps(self.doc, ensure_ascii=False).lower()
        for pattern in (r"(?<!un)(?<!nicht )\bvalidiert", r"(?<!not )\bvalidated", r"quality score", r"qualitätsscore"):
            self.assertIsNone(re.search(pattern, text), f"forbidden wording: {pattern}")

    def test_report_exists_and_covers_sections(self):
        self.assertTrue(REPORT.exists(), "RED_TEAM_REVIEW.md missing")
        text = REPORT.read_text(encoding="utf-8")
        for f in self.findings:
            self.assertIn(f["id"], text, f"{f['id']} not referenced in RED_TEAM_REVIEW.md")
        for heading in ("Methode", "Grenzen", "Fragen an"):
            self.assertIn(heading, text)


if __name__ == "__main__":
    unittest.main()
