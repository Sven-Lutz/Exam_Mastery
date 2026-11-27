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


SEARCH_LOG_FIELDS = ("batch", "date", "engine", "query", "hits_screened", "included", "excluded_or_note")
FIRST_BATCH5_POLICY = 17


class R2Batch5Contract(unittest.TestCase):
    """Batch 5 (algorithms, quantitative problem solving): search log and traceability."""

    @classmethod
    def setUpClass(cls):
        cls.register = r1.load(R2 / "r2_evidence.json")
        cls.policy_doc = r1.load(R2 / "r2_learning_policies.json")
        cls.entry_ids = {e["source_id"] for e in cls.register["entries"]}
        cls.batch5_policies = [p for p in cls.policy_doc["policies"]
                               if int(p["id"].rsplit("-", 1)[1]) >= FIRST_BATCH5_POLICY]
        cls.batch5_sources = {sid for s in cls.register.get("search_log", []) if s.get("batch") == 5
                              for sid in s.get("included", [])}

    def test_search_log_entries_are_complete(self):
        log = self.register.get("search_log", [])
        self.assertTrue(log)
        for s in log:
            for f in SEARCH_LOG_FIELDS:
                self.assertIn(f, s, s.get("query"))
            self.assertTrue(s["query"].strip() and s["engine"].strip())
            self.assertIsInstance(s["hits_screened"], int)
            self.assertTrue(s["excluded_or_note"].strip(), s["query"])
            for sid in s["included"]:
                self.assertIn(sid, self.entry_ids, "search log includes unregistered source %s" % sid)

    def test_batch5_sources_are_used_or_declared(self):
        cited = {e["source_id"] for p in self.policy_doc["policies"] for e in p["evidence"]}
        gaps = " ".join(self.policy_doc["coverage_gaps"])
        for sid in self.batch5_sources:
            self.assertTrue(sid in cited or sid in gaps, "batch-5 source %s neither cited nor declared" % sid)

    def test_batch5_policies_address_all_products_and_cite_batch5(self):
        self.assertTrue(self.batch5_policies)
        for p in self.batch5_policies:
            self.assertEqual(set(p["product_affordances"]), r1.PRODUCTS, p["id"])
            self.assertTrue({e["source_id"] for e in p["evidence"]} & self.batch5_sources, p["id"])


if __name__ == "__main__":
    unittest.main()
