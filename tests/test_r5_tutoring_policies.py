"""R5 tutoring/measurement policies: same structural contract as R1.

Structure and traceability only; no check here can show that a policy improves learning.
"""
import unittest

from tests.test_r1_learning_policies import R1, R1EvidenceRegisters, R1PolicyContract, ROOT, load

R5 = ROOT / "docs" / "research" / "workstreams" / "r5"
R5_REGISTERS = (R5 / "r5_evidence.json",) + tuple(R1 / n for n in ("r1a_evidence.json", "r1b_evidence.json"))


class R5PolicyContract(R1PolicyContract):
    POLICY_FILE = R5 / "r5_tutoring_policies.json"
    REGISTERS = R5_REGISTERS
    REQUIRE_ALL_RULES_REVIEWED = False

    def test_r5_owned_engine_rules_are_decided(self):
        reviewed = {l["rule_id"] for p in self.policies for l in p["kb_rule_links"]}
        for rule in ("ITS-R1", "ITS-R2", "AI-R1", "AI-R2", "AS-R1", "AS-R2"):
            self.assertIn(rule, reviewed)

    def test_open_research_is_declared(self):
        self.assertTrue(self.doc.get("open_research"))


class R5EvidenceRegister(R1EvidenceRegisters):
    REGISTERS = (R5 / "r5_evidence.json",)


del R1PolicyContract, R1EvidenceRegisters  # avoid re-running the R1 cases under this module

if __name__ == "__main__":
    unittest.main()
