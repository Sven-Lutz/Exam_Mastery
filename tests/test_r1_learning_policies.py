"""R1 learning policies: structural and traceability checks.

These checks keep the research-to-policy contract honest. They cannot show that
a policy is scientifically right or that it improves learning: every policy is
a design hypothesis with learning_evaluation NOT_RUN until a real evaluation exists.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R1 = ROOT / "docs" / "research" / "workstreams" / "r1"
KB = ROOT / "exam_mastery" / "knowledge"

OPERATIONS = {
    "recall_discrimination", "symbolic_procedure", "formal_proof", "rule_based_contextual",
    "diagnostic_reasoning", "empirical_experimental", "computational_construction", "spatial_design",
    "embodied_psychomotor", "open_synthesis", "self_regulation",
}
CERTAINTY = {"high", "moderate", "low", "very_low", "normative"}
RELATIONS = {"supports", "qualifies", "contradicts", "context_only"}
ACCESS = {"metadata", "abstract", "fulltext_partial", "fulltext_claim_review"}
RULE_RELATIONS = {"retains", "refines", "replaces", "contradicts", "new"}
PRODUCTS = {"textbook", "workbook", "anki", "interactive"}
REQUIRED = ("id", "title", "applies_to_operations", "context", "recommendation", "product_affordances",
            "abstain_or_fallback", "parameters", "evidence", "certainty", "observable", "independent_outcome",
            "failure_modes", "falsifier", "kb_rule_links", "status", "implementation_status", "learning_evaluation")


def load(name):
    return json.loads((R1 / name).read_text(encoding="utf-8"))


class R1PolicyContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load("r1_learning_policies.json")
        cls.policies = cls.doc["policies"]
        kb_sources = json.loads((KB / "sources.json").read_text(encoding="utf-8"))
        kb_sources = kb_sources["sources"] if isinstance(kb_sources, dict) else kb_sources
        cls.kb_ids = {s["id"] for s in kb_sources}
        cls.r1_entries = {}
        for reg in ("r1a_evidence.json", "r1b_evidence.json"):
            for e in load(reg)["entries"]:
                cls.r1_entries.setdefault(e["source_id"], e)
        principles = json.loads((KB / "principles.json").read_text(encoding="utf-8"))["principles"]
        cls.rule_ids = {r["id"] for p in principles for r in p.get("engine_rules", [])}

    def test_operation_taxonomy_is_the_charter_taxonomy(self):
        self.assertEqual(set(self.doc["operations"]), OPERATIONS)

    def test_ids_unique_and_fields_present(self):
        ids = [p["id"] for p in self.policies]
        self.assertEqual(len(ids), len(set(ids)))
        for p in self.policies:
            for f in REQUIRED:
                self.assertIn(f, p, "%s lacks %s" % (p.get("id"), f))
                self.assertNotIn(p[f], ("", None), "%s.%s empty" % (p["id"], f))

    def test_no_policy_claims_validation_it_does_not_have(self):
        for p in self.policies:
            self.assertEqual(p["status"], "design_hypothesis", p["id"])
            self.assertEqual(p["learning_evaluation"], "NOT_RUN", p["id"])
            self.assertIn(p["implementation_status"], {"not_implemented", "partially_implemented_unverified"}, p["id"])

    def test_operations_and_products_are_known(self):
        for p in self.policies:
            self.assertTrue(p["applies_to_operations"], p["id"])
            self.assertLessEqual(set(p["applies_to_operations"]), OPERATIONS, p["id"])
            for na in p.get("not_applicable_operations", []):
                self.assertIn(na["operation"], OPERATIONS, p["id"])
                self.assertTrue(na["reason"].strip(), p["id"])
            self.assertLessEqual(set(p["product_affordances"]), PRODUCTS, p["id"])

    def test_every_operation_is_covered_or_explicitly_deferred(self):
        covered = {op for p in self.policies for op in p["applies_to_operations"]}
        deferred = {d["operation"]: d for d in self.doc.get("deferred_operations", [])}
        for op in OPERATIONS:
            self.assertTrue(op in covered or op in deferred, "operation %s neither covered nor deferred" % op)
        for d in deferred.values():
            self.assertTrue(d["reason"].strip() and d["owner_workstream"].strip())

    def test_evidence_edges_resolve_and_carry_locators(self):
        for p in self.policies:
            if p["certainty"]["level"] != "normative":
                self.assertTrue(any(e["relation"] == "supports" for e in p["evidence"]), p["id"])
            for e in p["evidence"]:
                self.assertIn(e["relation"], RELATIONS, p["id"])
                self.assertTrue(e["locator"].strip(), "%s: edge to %s without locator" % (p["id"], e["source_id"]))
                self.assertTrue(e["source_id"] in self.kb_ids or e["source_id"] in self.r1_entries,
                                "%s cites unknown source %s" % (p["id"], e["source_id"]))

    def test_certainty_is_reasoned_and_high_needs_independent_sources(self):
        for p in self.policies:
            c = p["certainty"]
            self.assertIn(c["level"], CERTAINTY, p["id"])
            self.assertTrue(c["reasons"], p["id"])
            for sub in c.get("sub_claims", []):
                self.assertIn(sub["level"], CERTAINTY, p["id"])
                self.assertTrue(sub["claim"].strip(), p["id"])
            if c["level"] == "high":
                supporting = {e["source_id"] for e in p["evidence"] if e["relation"] == "supports"}
                self.assertGreaterEqual(len(supporting), 2, "%s: high certainty from one source" % p["id"])

    def test_numbers_are_provisional_product_parameters(self):
        for p in self.policies:
            for par in p["parameters"]:
                self.assertEqual(par["status"], "provisional_product_parameter", p["id"])
                self.assertTrue(par["rationale"].strip(), p["id"])

    def test_abstention_falsifier_and_failure_modes_exist(self):
        for p in self.policies:
            self.assertTrue(p["abstain_or_fallback"], p["id"])
            self.assertTrue(p["failure_modes"], p["id"])
            self.assertGreater(len(p["falsifier"]), 20, p["id"])

    def test_kb_rule_links_point_to_existing_rules(self):
        for p in self.policies:
            for link in p["kb_rule_links"]:
                self.assertIn(link["relation"], RULE_RELATIONS, p["id"])
                if link["relation"] != "new":
                    self.assertIn(link["rule_id"], self.rule_ids, "%s links unknown rule %s" % (p["id"], link["rule_id"]))

    def test_every_existing_engine_rule_is_reviewed(self):
        reviewed = {l["rule_id"] for p in self.policies for l in p["kb_rule_links"]}
        reviewed |= {r["rule_id"] for r in self.doc.get("kb_rules_out_of_r1_scope", [])}
        missing = sorted(self.rule_ids - reviewed)
        self.assertEqual(missing, [], "engine rules without an R1 decision: %s" % missing)


class R1EvidenceRegisters(unittest.TestCase):
    def test_entries_are_complete_and_honest_about_access(self):
        for reg in ("r1a_evidence.json", "r1b_evidence.json"):
            doc = load(reg)
            self.assertEqual(doc["schema"], "r1-evidence/1")
            ids = [e["source_id"] for e in doc["entries"]]
            self.assertEqual(len(ids), len(set(ids)), "%s duplicate ids" % reg)
            for e in doc["entries"]:
                for f in ("source_id", "citation", "doi_or_url", "source_type", "access", "design", "inference",
                          "verdict"):
                    self.assertIn(f, e, "%s/%s lacks %s" % (reg, e.get("source_id"), f))
                self.assertIn(e["access"]["level"], ACCESS, e["source_id"])
                if e["access"]["level"] in ("fulltext_partial", "fulltext_claim_review"):
                    self.assertTrue(e["access"].get("sections_read"), "%s: full text without sections" % e["source_id"])
                est = e.get("estimate")
                if isinstance(est, dict) and est.get("value") not in (None, "", "unknown"):
                    self.assertTrue(est.get("metric"), "%s: number without metric" % e["source_id"])


if __name__ == "__main__":
    unittest.main()
