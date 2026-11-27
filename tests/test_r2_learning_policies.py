"""R2 learning policies: the R1 structural and traceability contract applied to R2.

Passing these checks says nothing about scientific correctness or learning effect;
every policy stays a design hypothesis with learning_evaluation NOT_RUN.
"""
import json
import unittest

import test_r1_learning_policies as r1

R2 = r1.ROOT / "docs" / "research" / "workstreams" / "r2"
R2_REGISTERS = r1.R1_REGISTERS + (R2 / "r2_evidence.json",)
VERIFIERS_POLICY = "R2-POL-14"


class R2PolicyContract(r1.R1PolicyContract):
    POLICY_FILE = R2 / "r2_learning_policies.json"
    REGISTERS = R2_REGISTERS
    REQUIRE_ALL_RULES_REVIEWED = False

    def test_kb_rule_links_point_to_existing_rules(self):
        for p in self.policies:
            for link in p["kb_rule_links"]:
                self.assertIn(link["relation"], r1.RULE_RELATIONS, p["id"])
                if link["relation"] == "new":
                    self.assertTrue(link["rule_id"].startswith(p["id"]), p["id"])
                else:
                    self.assertIn(link["rule_id"], self.rule_ids, "%s links unknown rule %s" % (p["id"], link["rule_id"]))

    def test_r2_covers_its_core_operations(self):
        covered = {op for p in self.policies for op in p["applies_to_operations"]}
        for op in ("formal_proof", "symbolic_procedure", "computational_construction", "empirical_experimental"):
            self.assertIn(op, covered)

    def test_verifier_declaration_policy_exists(self):
        ids = {p["id"] for p in self.policies}
        self.assertIn(VERIFIERS_POLICY, ids)

    def test_open_coverage_gaps_are_declared(self):
        self.assertTrue(self.doc.get("coverage_gaps"))


class R2EvidenceRegister(r1.R1EvidenceRegisters):
    REGISTERS = (R2 / "r2_evidence.json",)


if __name__ == "__main__":
    unittest.main()
