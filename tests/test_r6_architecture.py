"""R6 architecture synthesis and ADR: structural and traceability checks.

These checks keep the research-to-architecture contract honest. They cannot show that the
proposed architecture is right or that anything improves learning: the decision stays
PROPOSED until the owner decides, and every policy remains a design hypothesis with
learning_evaluation NOT_RUN.
"""
import importlib.util
import json
import re
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
WS = ROOT / "docs" / "research" / "workstreams"
R6 = WS / "r6"
ADR_MD = WS / "ARCHITECTURE_SYNTHESIS_ADR.md"
ADR = R6 / "adr.json"
ONTOLOGY = R6 / "skill_ontology_v1.json"
OBSERVATION = R6 / "observation_contract_v1.json"
INDEX = R6 / "policy_index.json"


def _charter_operations():
    """The operation set the R1 policy test uses (single source of the charter taxonomy)."""
    spec = importlib.util.spec_from_file_location("r1_policy_contract", HERE / "test_r1_learning_policies.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return set(module.OPERATIONS)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


POLICY_ID = re.compile(r"\bR[0-9]-POL-[A-Z]?[0-9]{2}\b")
RATINGS = {"favourable", "mixed", "unfavourable"}
R2_POL_14_VERIFIERS = {
    "algebraic_oracle_cas", "numeric_single_value", "proof_assistant", "visible_unit_tests",
    "hidden_or_property_tests", "human_rubric", "comparative_judgement", "llm_judgement", "none",
    "state_oracle", "runtime_invariant_assertion", "operation_counter", "principle_key",
}
R5_POL_01_STATES = {"NOT_ASSESSED", "ASSISTED", "INDEPENDENT_PASS", "RETEST_DUE",
                    "RETAINED_AFTER_ELAPSED_TIME", "INSUFFICIENT_EVIDENCE"}
ASSIST_LEVELS = {"none", "hint_n", "hint_bottom_out", "solution_seen", "tutor", "unknown"}
SOURCES = {"deterministic", "human_rubric", "external_assessment", "agent_judgement", "self_report"}
NEVER_EVIDENCE = {"agent_judgement", "self_report", "practice_log", "scheduler_statistic", "benchmark_score", "exposure"}


def _walk(node, path=""):
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _walk(value, path + "/" + str(key))
            yield path + "/" + str(key), key, value
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from _walk(value, "%s[%d]" % (path, i))


class R6ArchitectureContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.adr = load(ADR)
        cls.ontology = load(ONTOLOGY)
        cls.observation = load(OBSERVATION)
        cls.index_ids = {p["id"] for p in load(INDEX)["policies"]}
        cls.md = ADR_MD.read_text(encoding="utf-8")

    # --- decision status -------------------------------------------------------------
    def test_decision_status_is_proposed_never_accepted(self):
        decision = self.adr["proposed_decision"]
        self.assertEqual(decision["status"], "PROPOSED")
        self.assertIsNone(decision["decided_by"])
        for doc in (self.adr, self.ontology, self.observation):
            for path, key, value in _walk(doc):
                if key == "status" and isinstance(value, str):
                    self.assertNotIn("ACCEPTED", value.upper(), path)
                    self.assertNotIn("APPROVED", value.upper(), path)
                    self.assertNotIn("VALIDATED", value.upper(), path)
        self.assertIn("Entscheidungsstatus: PROPOSED", self.md)

    # --- JSON structure --------------------------------------------------------------
    def test_adr_structure(self):
        for key in ("decision_question", "inputs", "drivers", "criteria", "options", "assessments",
                    "proposed_decision", "rejected_options", "cannot_claim", "migration_path",
                    "minimum_credible_system", "gates", "owner_decisions", "p4_integration_plan",
                    "red_team_reconciliation"):
            self.assertIn(key, self.adr)
        option_ids = {o["id"] for o in self.adr["options"]}
        self.assertTrue({"A", "B", "C"} <= option_ids, "charter options A, B, C must be compared")
        self.assertIn(self.adr["proposed_decision"]["option"], option_ids)
        rejected = {r["option"] for r in self.adr["rejected_options"]}
        self.assertNotIn(self.adr["proposed_decision"]["option"], rejected)
        self.assertEqual(rejected | {self.adr["proposed_decision"]["option"]}, option_ids)
        for r in self.adr["rejected_options"]:
            self.assertTrue(r["reasons"], r["option"])
            self.assertTrue(r["reconsider_if"].strip(), r["option"])
        self.assertTrue(self.adr["cannot_claim"])

    def test_every_option_is_assessed_on_every_criterion_with_locators_and_unknowns(self):
        criteria = {c["id"] for c in self.adr["criteria"]}
        for name in ("learning_relevance", "verification_coverage", "technology_complexity", "operability",
                     "offline", "security", "authoring_cost", "maintainability"):
            self.assertIn(name, criteria)
        cells = {(a["option"], a["criterion"]) for a in self.adr["assessments"]}
        for o in self.adr["options"]:
            for c in criteria:
                self.assertIn((o["id"], c), cells)
        for a in self.adr["assessments"]:
            self.assertIn(a["rating"], RATINGS, a)
            self.assertTrue(a["reason"].strip(), a)
            self.assertTrue(a["locators"], a)
            self.assertTrue(a["unknowns"], a)

    def test_no_criterion_has_a_numeric_score(self):
        for a in self.adr["assessments"]:
            for path, key, value in _walk(a):
                self.assertNotIn("score", str(key).lower(), path)
                self.assertNotIsInstance(value, (int, float), path)
            for key, value in a.items():
                self.assertNotIn("score", key.lower())
                self.assertNotIsInstance(value, (bool, int, float), key)
        for c in self.adr["criteria"]:
            self.assertFalse([k for k in c if "score" in k.lower() or "weight" in k.lower()])

    def test_owner_decisions_have_blocks_and_default(self):
        allowed = set(self.adr["owner_decision_block_values"])
        gate_ids = {g["id"] for g in self.adr["gates"]}
        self.assertTrue(gate_ids <= allowed)
        ids = [d["id"] for d in self.adr["owner_decisions"]]
        self.assertEqual(len(ids), len(set(ids)))
        for d in self.adr["owner_decisions"]:
            self.assertIsInstance(d.get("blocks"), list, d["id"])
            self.assertTrue(d["blocks"], d["id"])
            self.assertTrue(set(d["blocks"]) <= allowed, d["id"])
            self.assertIsInstance(d.get("default"), str, d["id"])
            self.assertTrue(d["default"].strip(), d["id"])
            self.assertTrue(d["source"], d["id"])
            self.assertIn(d["id"], self.md, "owner decision missing in the report")
        for top in self.adr["top_owner_decisions"]:
            self.assertIn(top, ids)

    def test_gates_are_falsifiable_and_consistent_with_owner_decisions(self):
        blocks = {d["id"]: set(d["blocks"]) for d in self.adr["owner_decisions"]}
        for g in self.adr["gates"]:
            self.assertTrue(g["pass_criteria"], g["id"])
            self.assertTrue(g["fails_if"].strip(), g["id"])
            for od in g["blocked_by_owner_decisions"]:
                self.assertIn(g["id"], blocks[od], (g["id"], od))
        for od, gates in blocks.items():
            for gate in gates & {g["id"] for g in self.adr["gates"]}:
                gate_doc = next(g for g in self.adr["gates"] if g["id"] == gate)
                self.assertIn(od, gate_doc["blocked_by_owner_decisions"], (od, gate))

    # --- traceability ----------------------------------------------------------------
    def test_every_referenced_policy_id_exists_in_the_index(self):
        texts = {"md": self.md, "adr": json.dumps(self.adr, ensure_ascii=False),
                 "ontology": json.dumps(self.ontology, ensure_ascii=False),
                 "observation": json.dumps(self.observation, ensure_ascii=False)}
        for name, text in texts.items():
            found = set(POLICY_ID.findall(text))
            self.assertTrue(found, name)
            unknown = found - self.index_ids
            self.assertFalse(unknown, "%s references unknown policies %s" % (name, sorted(unknown)))

    # --- ontology --------------------------------------------------------------------
    def test_ontology_operations_equal_the_charter_taxonomy(self):
        operations = _charter_operations()
        self.assertEqual(set(self.ontology["operations"]), operations)
        self.assertEqual({o["id"] for o in self.ontology["operation_details"]}, operations)
        for ct in self.ontology["competence_types"]:
            self.assertTrue(set(ct["operations"]) <= operations, ct["id"])
        ct_ids = {ct["id"] for ct in self.ontology["competence_types"]}
        verifiers = set(self.ontology["verifier_classes"])
        for o in self.ontology["operation_details"]:
            self.assertTrue(set(o["competence_types"]) <= ct_ids, o["id"])
            self.assertTrue(set(o["default_verifier_classes"]) <= verifiers, o["id"])
        for verb, target in self.ontology["engine_operation_mapping"]["map"].items():
            self.assertIn(target["operation"], operations | {"by_context"}, verb)

    def test_ontology_states_verifiers_assistance_and_boundary(self):
        self.assertEqual(set(self.ontology["observable_states"]), R5_POL_01_STATES)
        self.assertTrue(R2_POL_14_VERIFIERS <= set(self.ontology["verifier_classes"]))
        llm = next(v for v in self.ontology["verifier_class_details"] if v["id"] == "llm_judgement")
        self.assertEqual(llm["competence_evidence"], "never")
        self.assertEqual({a["id"] for a in self.ontology["assistance_levels"]}, ASSIST_LEVELS)
        for a in self.ontology["assistance_levels"]:
            self.assertEqual(a["counts_for_state"], a["id"] == "none", a["id"])
        for e in self.ontology["evidence_kinds"]:
            if e["id"] in NEVER_EVIDENCE:
                self.assertEqual(e["counts_as_competence"], "never", e["id"])
        boundary = {b["policy"] for b in self.ontology["practice_certification_boundary"]}
        self.assertTrue({"R4-POL-01", "R3-POL-10"} <= boundary)
        self.assertEqual(self.ontology["phase_mapping"]["final_exam_week"], "assessment_preparation")
        self.assertTrue(all(m["optional"] for m in self.ontology["modes"]))
        self.assertEqual(set(self.ontology["product_containers"]["values"]), {"textbook", "workbook", "anki", "interactive"})

    # --- observation contract --------------------------------------------------------
    def test_observation_contract(self):
        names = {f["name"] for f in self.observation["fields"]}
        for required in ("learner_ref", "actor", "event_type", "t", "time_quality", "assist_level", "source",
                         "item.role", "item.new_for_learner", "verifier.class", "provenance.content_revision"):
            self.assertIn(required, names)
        changing = {e["id"] for e in self.observation["event_types"] if e["changes_state"] != "never"}
        self.assertEqual(changing, {"attempt", "external_assessment"})
        never = set(self.observation["state_derivation"]["never_changes_state"])
        self.assertTrue({"agent_judgement", "self_report", "scheduler_statistic", "benchmark_score"} <= never)
        assist = next(f for f in self.observation["fields"] if f["name"] == "assist_level")
        self.assertEqual(set(assist["semantics"].replace(" ", "").split("|")), ASSIST_LEVELS)
        source = next(f for f in self.observation["fields"] if f["name"] == "source")
        self.assertEqual(set(source["semantics"].replace(" ", "").split("|")), SOURCES)
        roles = self.ontology["item_roles"]
        self.assertFalse(set(roles["practice"]) & set(roles["evidence"]))
        self.assertTrue({"similar", "transfer", "retest"} <= set(roles["evidence"]))
        for p in (self.observation["elapsed_time_semantics"]["retention_state_min_elapsed"],
                  self.observation["elapsed_time_semantics"]["retention_claim_min_delay"]):
            self.assertEqual(p["status"], "provisional_product_parameter")
        self.assertGreaterEqual(len(self.observation["adversarial_fixtures"]), 9)

    # --- report ----------------------------------------------------------------------
    def test_report_sections_and_hygiene(self):
        for heading in ("## 2. Synthese", "### 2.6 Was keine Architektur behaupten darf", "## 3. Architecture Decision Record",
                        "## 6. Minimum Credible System", "## 7. Phasen-Gates", "## 8. OWNER_DECISIONS_REQUIRED",
                        "## 9. P4-Integrationsplan", "## 12. Antwort auf den Red-Team-Review"):
            self.assertIn(heading, self.md)
        for path in (ADR_MD, ADR, ONTOLOGY, OBSERVATION):
            text = path.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"/Users/|/home/|C:\\\\Users", path.name)
        self.assertNotRegex(self.md, r"\.pdf S\. ?[0-9]", "no lecture file/page references")


if __name__ == "__main__":
    unittest.main()
