"""R4 learning policies: the R1 structural and traceability contract applied to R4.

Passing these checks says nothing about scientific correctness or learning effect;
every policy stays a design hypothesis with learning_evaluation NOT_RUN. The extra
checks enforce the R4 certification boundary: the product never certifies physical,
laboratory or safety competence and never infers it from app data.
"""
import unittest

import test_r1_learning_policies as r1

R4 = r1.ROOT / "docs" / "research" / "workstreams" / "r4"
R4_REGISTERS = r1.R1_REGISTERS + (R4 / "r4_evidence.json",)
R4_CORE_OPERATIONS = ("embodied_psychomotor", "spatial_design", "empirical_experimental")
BOUNDARY_OPERATIONS = {"embodied_psychomotor", "empirical_experimental"}
TWO_TRACK_POLICY = "R4-POL-01"
SAFETY_POLICY = "R4-POL-13"
SEARCH_LOG_FIELDS = ("batch", "date", "engine", "query", "hits_screened", "included", "excluded_or_note")


class R4PolicyContract(r1.R1PolicyContract):
    POLICY_FILE = R4 / "r4_learning_policies.json"
    REGISTERS = R4_REGISTERS
    REQUIRE_ALL_RULES_REVIEWED = False

    def test_kb_rule_links_point_to_existing_rules(self):
        for p in self.policies:
            for link in p["kb_rule_links"]:
                self.assertIn(link["relation"], r1.RULE_RELATIONS, p["id"])
                if link["relation"] == "new":
                    self.assertTrue(link["rule_id"].startswith(p["id"]), p["id"])
                else:
                    self.assertIn(link["rule_id"], self.rule_ids, "%s links unknown rule %s" % (p["id"], link["rule_id"]))

    def test_r4_covers_its_core_operations(self):
        covered = {op for p in self.policies for op in p["applies_to_operations"]}
        for op in R4_CORE_OPERATIONS:
            self.assertIn(op, covered)

    def test_open_coverage_gaps_are_declared(self):
        self.assertTrue(self.doc.get("coverage_gaps"))

    def test_policies_address_all_four_products(self):
        for p in self.policies:
            self.assertEqual(set(p["product_affordances"]), r1.PRODUCTS, p["id"])
            for text in p["product_affordances"].values():
                self.assertTrue(text.strip(), p["id"])

    def test_physical_and_lab_policies_declare_certification_boundary(self):
        for p in self.policies:
            if not BOUNDARY_OPERATIONS & set(p["applies_to_operations"]):
                continue
            cb = p.get("certification_boundary")
            self.assertIsInstance(cb, dict, "%s lacks certification_boundary" % p["id"])
            self.assertIs(cb.get("product_certifies_physical_competence"), False, p["id"])
            self.assertIs(cb.get("product_certifies_safety"), False, p["id"])
            self.assertEqual(cb.get("physical_evidence_source"), "external_human_rated_only", p["id"])
            self.assertGreater(len(cb.get("statement", "")), 40, p["id"])

    def test_real_world_practice_logging_is_described(self):
        for p in self.policies:
            if BOUNDARY_OPERATIONS & set(p["applies_to_operations"]):
                self.assertTrue(p.get("real_world_logging", "").strip(), p["id"])

    def test_two_track_and_safety_policies_exist(self):
        ids = {p["id"] for p in self.policies}
        self.assertIn(TWO_TRACK_POLICY, ids)
        self.assertIn(SAFETY_POLICY, ids)
        safety = next(p for p in self.policies if p["id"] == SAFETY_POLICY)
        self.assertEqual(safety["certainty"]["level"], "normative")

    def test_competence_tracks_forbid_promotion_from_app_data(self):
        tracks = self.doc["competence_tracks"]
        for key in ("A_knowledge", "B_physical_execution", "C_certification_and_safety", "rule"):
            self.assertTrue(tracks.get(key, "").strip(), key)
        contract = self.doc["shared_measurement_contract"]
        self.assertIn("external_assessment", contract["track_b_evidence"])
        self.assertTrue(contract["not_evidence"])


class R4EvidenceRegister(r1.R1EvidenceRegisters):
    REGISTERS = (R4 / "r4_evidence.json",)


class R4SearchLogAndTraceability(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.register = r1.load(R4 / "r4_evidence.json")
        cls.policy_doc = r1.load(R4 / "r4_learning_policies.json")
        cls.entry_ids = {e["source_id"] for e in cls.register["entries"]}

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

    def test_every_registered_source_is_used_or_declared(self):
        cited = {e["source_id"] for p in self.policy_doc["policies"] for e in p["evidence"]}
        gaps = " ".join(self.policy_doc["coverage_gaps"])
        for sid in self.entry_ids:
            self.assertTrue(sid in cited or sid in gaps, "R4 source %s neither cited nor declared" % sid)

    def test_contradicting_or_null_evidence_is_registered(self):
        relations = {e["relation"] for p in self.policy_doc["policies"] for e in p["evidence"]}
        self.assertIn("contradicts", relations)
        self.assertIn("qualifies", relations)


if __name__ == "__main__":
    unittest.main()
