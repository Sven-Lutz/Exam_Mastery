"""R3 learning policies: the R1 structural and traceability contract applied to R3.

Passing these checks says nothing about scientific correctness or learning effect;
every policy stays a design hypothesis with learning_evaluation NOT_RUN.
"""
import json
import unittest

import test_r1_learning_policies as r1

R3 = r1.ROOT / "docs" / "research" / "workstreams" / "r3"
R3_REGISTERS = r1.R1_REGISTERS + (R3 / "r3_evidence.json",)
CORE_OPERATIONS = ("rule_based_contextual", "diagnostic_reasoning", "open_synthesis")
PRACTICE_OPERATIONS = {"rule_based_contextual", "diagnostic_reasoning"}
SIMULATION_BOUNDARY_POLICY = "R3-POL-10"
AMBIGUOUS_GRADING_POLICY = "R3-POL-11"


class R3PolicyContract(r1.R1PolicyContract):
    POLICY_FILE = R3 / "r3_learning_policies.json"
    REGISTERS = R3_REGISTERS
    REQUIRE_ALL_RULES_REVIEWED = False

    def test_kb_rule_links_point_to_existing_rules(self):
        for p in self.policies:
            for link in p["kb_rule_links"]:
                self.assertIn(link["relation"], r1.RULE_RELATIONS, p["id"])
                if link["relation"] == "new":
                    self.assertTrue(link["rule_id"].startswith(p["id"]), p["id"])
                else:
                    self.assertIn(link["rule_id"], self.rule_ids, "%s links unknown rule %s" % (p["id"], link["rule_id"]))

    def test_r3_covers_its_core_operations(self):
        covered = {op for p in self.policies for op in p["applies_to_operations"]}
        for op in CORE_OPERATIONS:
            self.assertIn(op, covered)

    def test_open_coverage_gaps_are_declared(self):
        gaps = self.doc.get("coverage_gaps")
        self.assertTrue(gaps)
        self.assertTrue(all(isinstance(g, str) and g.strip() for g in gaps))

    def test_clinical_and_legal_practice_policies_carry_a_boundary(self):
        for p in self.policies:
            if PRACTICE_OPERATIONS & set(p["applies_to_operations"]):
                b = p.get("practice_boundary")
                self.assertTrue(b, "%s lacks practice_boundary" % p["id"])
                self.assertIn(b["domain"], {"legal", "clinical", "legal_and_clinical"}, p["id"])
                self.assertGreater(len(b["statement"]), 40, p["id"])
                self.assertEqual(b["abstain_reason"], "safety_or_professional_boundary", p["id"])
                self.assertTrue(p["abstain_or_fallback"], p["id"])

    def test_simulation_is_not_real_world_authority(self):
        pol = {p["id"]: p for p in self.policies}
        self.assertIn(SIMULATION_BOUNDARY_POLICY, pol)
        p = pol[SIMULATION_BOUNDARY_POLICY]
        self.assertEqual(p["certainty"]["level"], "normative")
        self.assertEqual(p["practice_boundary"]["domain"], "legal_and_clinical")
        self.assertIn("ABSTAIN", p["tutor_affordance"])

    def test_llm_feedback_on_ambiguous_answers_stays_unverified(self):
        pol = {p["id"]: p for p in self.policies}
        self.assertIn(AMBIGUOUS_GRADING_POLICY, pol)
        self.assertIn("FEEDBACK_UNVERIFIED", pol[AMBIGUOUS_GRADING_POLICY]["recommendation"])
        self.assertIn("LLM-Bewertung (agent_judgement)", self.doc["shared_measurement_contract"]["not_evidence"])

    def test_no_competence_or_certification_wording(self):
        banned = ("validated", "validiert", "zertifiziert", "approved", "praxisreif ist")
        for p in self.policies:
            text = json.dumps({k: p[k] for k in ("title", "recommendation", "product_affordances")}, ensure_ascii=False).lower()
            for word in banned:
                self.assertNotIn(word, text, "%s uses '%s'" % (p["id"], word))


class R3EvidenceRegister(r1.R1EvidenceRegisters):
    REGISTERS = (R3 / "r3_evidence.json",)

    def test_search_log_is_present_and_resolves(self):
        doc = r1.load(self.REGISTERS[0])
        ids = {e["source_id"] for e in doc["entries"]}
        self.assertTrue(doc.get("search_log"))
        for s in doc["search_log"]:
            for f in ("id", "date", "engine", "query", "hits_screened", "included", "excluded_or_note"):
                self.assertIn(f, s, s.get("id"))
            for sid in s["included"]:
                self.assertIn(sid, ids, "%s includes unknown %s" % (s["id"], sid))
        logged = {sid for s in doc["search_log"] for sid in s["included"]}
        self.assertEqual(ids - logged, set(), "entries without a logged search")

    def test_every_entry_names_a_domain(self):
        for e in r1.load(self.REGISTERS[0])["entries"]:
            self.assertIn(e["domain"], {"law", "philosophy", "management", "clinical", "grading"}, e["source_id"])


if __name__ == "__main__":
    unittest.main()
