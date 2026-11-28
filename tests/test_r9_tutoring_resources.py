"""R9 tutoring resources: R1 policy contract, evidence register and resource-card checks.

Passing these checks says nothing about scientific correctness, tutor quality or
learning effect. Every policy stays a design hypothesis with learning_evaluation
NOT_RUN; every resource decision is a research recommendation awaiting review.
"""
import json
import re
import unittest

import test_r1_learning_policies as r1

R9 = r1.ROOT / "docs" / "research" / "workstreams" / "r9"
WORKSTREAMS = r1.ROOT / "docs" / "research" / "workstreams"
REGISTRY_MD = r1.ROOT / "docs" / "research" / "TUTORING_RESOURCE_REGISTRY_20261126.md"
R9_EVIDENCE = R9 / "r9_evidence.json"
R9_REGISTERS = r1.R1_REGISTERS + (R9_EVIDENCE,)
R9_DOCS = ("TUTORING_RESOURCE_COMPARISON.md", "TUTOR_BEHAVIORAL_CONTRACT.md",
           "TUTOR_EVALUATION_PROTOCOL.md", "TUTOR_ADOPTION_DECISION.md")

CLAIM_CLASSES = {"marketing", "documented_function", "benchmark", "learning_outcome"}
DECISIONS = {"reuse", "adapt", "emulate", "defer", "reject"}
TYPED_OUTPUTS = {"HINT", "CHECK_STEP", "FEEDBACK_UNVERIFIED", "ERROR_HYPOTHESIS", "SOLUTION_REVEAL", "ABSTAIN"}
CLAIM_TYPES = {"learning_effect", "tutor_behaviour", "grounding_reliability", "measurement_gap", "architecture"}
LEARNING_CLASSES = {"learning_outcome_experimental", "learning_outcome_quasi_experimental"}
NON_LEARNING_CLASSES = {"benchmark", "system_description", "grounding_audit", "design_study", "synthesis",
                        "neurophysiological_small_n"}
PRACTICE_OPERATIONS = {"rule_based_contextual", "diagnostic_reasoning"}
BOUNDARY_DOMAINS = {"legal", "clinical", "legal_and_clinical", "physical_safety", "legal_clinical_and_physical"}

# Named in issue #31 (the issue text is not in the repository, so the list is fixed here).
ISSUE_31_NAMES = ("DeepTutor", "OATutor", "SMART-RAG", "TutorBench", "MathTutorBench", "OpenTutor", "PAIDEIA",
                  "Education Agent Skills", "ChatGPT Study Mode", "ChatGPT Project", "NotebookLM", "YouLearn",
                  "StudyFetch", "Khanmigo", "Math Academy", "RemNote", "Margin Study", "Utterseen")
ISSUE_31_URLS = ("https://github.com/HKUDS/DeepTutor", "https://github.com/CAHLR/OATutor",
                 "https://github.com/digillab-lmu/smart-rag", "https://labs.scale.com/leaderboard/tutorbench",
                 "https://github.com/zijinz456/OpenTutor", "https://github.com/OPTIMETA/PAIDEIA",
                 "https://github.com/TaewoooPark/PAIDEIA", "https://github.com/GarethManning/education-agent-skills")


def norm(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def norm_url(url):
    return url.strip().rstrip("/").lower()


class R9PolicyContract(r1.R1PolicyContract):
    POLICY_FILE = R9 / "r9_tutor_policies.json"
    REGISTERS = R9_REGISTERS
    REQUIRE_ALL_RULES_REVIEWED = False

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.r9_entries = {e["source_id"]: e for e in r1.load(R9_EVIDENCE)["entries"]}
        cls.resource_ids = {c["id"] for c in r1.load(R9 / "r9_resources.json")["resources"]}

    def test_kb_rule_links_point_to_existing_rules(self):
        for p in self.policies:
            for link in p["kb_rule_links"]:
                self.assertIn(link["relation"], r1.RULE_RELATIONS, p["id"])
                if link["relation"] == "new":
                    self.assertTrue(link["rule_id"].startswith(p["id"]), p["id"])
                else:
                    self.assertIn(link["rule_id"], self.rule_ids, "%s links unknown rule %s" % (p["id"], link["rule_id"]))

    def test_policy_ids_are_r9(self):
        for p in self.policies:
            self.assertRegex(p["id"], r"^R9-POL-\d{2}$")

    def test_typed_outputs_match_r5_pol_06(self):
        self.assertEqual(set(self.doc["typed_outputs"]["types"]), TYPED_OUTPUTS)
        self.assertIn("safety_or_professional_boundary", self.doc["typed_outputs"]["abstain_reasons"])

    def test_cross_workstream_edges_are_declared(self):
        declared = {sid for reg in self.doc["cross_workstream_registers"] for sid in reg["source_ids"]}
        for reg in self.doc["cross_workstream_registers"]:
            self.assertTrue(reg["branch"].strip() and reg["path"].strip())
        for p in self.policies:
            for e in p.get("cross_workstream_evidence", []):
                self.assertIn(e["source_id"], declared, p["id"])
                self.assertIn(e["relation"], r1.RELATIONS, p["id"])
                self.assertTrue(e["locator"].strip(), p["id"])
        self.assertFalse(declared & set(self.r9_entries), "R5 sources must not be duplicated in the R9 register")

    def test_benchmarks_never_support_a_learning_effect(self):
        for p in self.policies:
            for e in p["evidence"]:
                if e["source_id"] in self.r9_entries:
                    self.assertIn(e.get("supports_claim_type"), CLAIM_TYPES, "%s/%s" % (p["id"], e["source_id"]))
                if e["relation"] == "supports" and e.get("supports_claim_type") == "learning_effect":
                    entry = self.r9_entries.get(e["source_id"])
                    if entry is not None:
                        self.assertTrue(entry["may_support_learning_effect"],
                                        "%s uses %s (%s) as learning evidence" % (p["id"], e["source_id"], entry["evidence_class"]))

    def test_practice_operations_carry_a_boundary(self):
        for p in self.policies:
            if PRACTICE_OPERATIONS & set(p["applies_to_operations"]):
                b = p.get("practice_boundary")
                self.assertTrue(b, "%s lacks practice_boundary" % p["id"])
                self.assertIn(b["domain"], BOUNDARY_DOMAINS, p["id"])
                self.assertGreater(len(b["statement"]), 40, p["id"])
                self.assertEqual(b["abstain_reason"], "safety_or_professional_boundary", p["id"])

    def test_resource_links_resolve(self):
        for p in self.policies:
            self.assertTrue(p["resource_links"], p["id"])
            for rid in p["resource_links"]:
                self.assertIn(rid, self.resource_ids, p["id"])

    def test_expected_policy_themes_are_present(self):
        text = {p["id"]: json.dumps(p, ensure_ascii=False) for p in self.policies}
        joined = " ".join(text.values())
        for needle in ("temporal_status", "ohne API", "SOLUTION_REVEAL", "Frontier-Chat", "verzögert",
                       "Benchmark", "Emulation", "keyless"):
            self.assertIn(needle, joined, "no policy covers '%s'" % needle)

    def test_explicit_solution_request_is_honoured(self):
        p = {x["id"]: x for x in self.policies}["R9-POL-03"]
        self.assertIn("ausdrückliche Anforderung der vollständigen Lösung wird immer erfüllt", p["recommendation"])

    def test_coverage_gaps_and_conflicts_declared(self):
        self.assertTrue(self.doc["coverage_gaps"])
        ids = {p["id"] for p in self.policies}
        for cr in self.doc["conflict_resolution"]:
            self.assertLessEqual(set(cr["between"]), ids, cr["id"])

    def test_no_validation_wording(self):
        banned = ("validated", "validiert", "zertifiziert", "approved", "nachgewiesen wirksam")
        for p in self.policies:
            blob = json.dumps({k: p[k] for k in ("title", "recommendation", "product_affordances")}, ensure_ascii=False).lower()
            for word in banned:
                self.assertNotIn(word, blob, "%s uses '%s'" % (p["id"], word))


class R9EvidenceRegister(r1.R1EvidenceRegisters):
    REGISTERS = (R9_EVIDENCE,)

    def test_search_log_is_present_and_resolves(self):
        doc = r1.load(R9_EVIDENCE)
        ids = {e["source_id"] for e in doc["entries"]}
        self.assertTrue(doc.get("search_log"))
        for s in doc["search_log"]:
            for f in ("id", "date", "engine", "query", "hits_screened", "included", "excluded_or_note"):
                self.assertIn(f, s, s.get("id"))
            for sid in s["included"]:
                self.assertIn(sid, ids, "%s includes unknown %s" % (s["id"], sid))
        logged = {sid for s in doc["search_log"] for sid in s["included"]}
        self.assertEqual(ids - logged, set(), "entries without a logged search")

    def test_evidence_class_controls_learning_support(self):
        for e in r1.load(R9_EVIDENCE)["entries"]:
            cls = e["evidence_class"]
            self.assertIn(cls, LEARNING_CLASSES | NON_LEARNING_CLASSES, e["source_id"])
            self.assertIsInstance(e["may_support_learning_effect"], bool, e["source_id"])
            if cls in NON_LEARNING_CLASSES:
                self.assertFalse(e["may_support_learning_effect"], e["source_id"])

    def test_identity_checked(self):
        for e in r1.load(R9_EVIDENCE)["entries"]:
            self.assertEqual(e["identity_check"]["result"], "primary_metadata_checked", e["source_id"])
            self.assertTrue(e["identity_check"]["method"].strip(), e["source_id"])


class R9ResourceCards(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.doc = r1.load(R9 / "r9_resources.json")
        cls.cards = cls.doc["resources"]
        cls.names = []
        cls.urls = set()
        for c in cls.cards:
            cls.names.append(norm(c["name"]))
            cls.names.extend(norm(a) for a in c.get("aliases", []))
            cls.urls.add(norm_url(c["official_url"]))
            cls.urls.update(norm_url(u) for u in c.get("other_urls", []))

    def has_name(self, name):
        n = norm(name)
        return any(n in x for x in self.names)

    def test_issue_31_resources_preserved(self):
        for name in ISSUE_31_NAMES:
            self.assertTrue(self.has_name(name), "issue #31 resource missing: %s" % name)
        for url in ISSUE_31_URLS:
            self.assertIn(norm_url(url), self.urls, url)

    def test_registry_resources_preserved(self):
        rows = [l for l in REGISTRY_MD.read_text(encoding="utf-8").splitlines() if l.startswith("| **")]
        self.assertGreaterEqual(len(rows), 15)
        for row in rows:
            cells = [c.strip() for c in row.strip("|").split("|")]
            label = cells[0].strip("* ")
            for part in label.split(" / "):
                self.assertTrue(self.has_name(part), "registry resource missing: %s" % part)
            for url in re.findall(r"https?://[^\s;|)]+", cells[1]):
                self.assertIn(norm_url(url), self.urls, "registry URL missing: %s" % url)

    def test_ids_unique(self):
        ids = [c["id"] for c in self.cards]
        self.assertEqual(len(ids), len(set(ids)))

    def test_cards_complete(self):
        for c in self.cards:
            for f in ("id", "name", "official_url", "owner", "licence", "access_date", "identity_verified", "category",
                      "mechanisms", "claims", "offline_local_first", "privacy_data_flow", "cost_model",
                      "anki_fsrs_redundancy", "risks", "decision", "tested_workflow"):
                self.assertIn(f, c, "%s lacks %s" % (c.get("id"), f))
            self.assertRegex(c["access_date"], r"^\d{4}-\d{2}-\d{2}$")
            self.assertIsInstance(c["identity_verified"]["value"], bool, c["id"])
            self.assertTrue(c["identity_verified"]["method"].strip(), c["id"])
            self.assertTrue(c["mechanisms"] and set(c["mechanisms"]) <= set(range(1, 10)), c["id"])
            self.assertTrue(c["claims"], c["id"])

    def test_each_card_has_decision_reason_and_opportunity_cost(self):
        for c in self.cards:
            d = c["decision"]
            self.assertIn(d["value"], DECISIONS, c["id"])
            self.assertGreater(len(d["reason"]), 30, c["id"])
            self.assertTrue(d["opportunity_cost"].strip(), c["id"])

    def test_every_claim_is_classified_with_locator(self):
        for c in self.cards:
            for claim in c["claims"]:
                self.assertIn(claim["class"], CLAIM_CLASSES, c["id"])
                self.assertTrue(claim["locator"].strip(), c["id"])
                self.assertTrue(claim["text"].strip(), c["id"])

    def test_marketing_or_benchmark_never_supports_learning(self):
        for c in self.cards:
            for claim in c["claims"]:
                if claim["supports_learning_effect"]:
                    self.assertEqual(claim["class"], "learning_outcome", "%s: %s" % (c["id"], claim["text"][:60]))

    def test_second_scheduler_is_never_reused(self):
        for c in self.cards:
            if c["anki_fsrs_redundancy"].startswith(("Konflikt", "Direkter Konflikt")):
                self.assertIn(c["decision"]["value"], {"emulate", "defer", "reject"}, c["id"])

    def test_paideia_identity_resolved(self):
        card = next(c for c in self.cards if c["id"] == "RES-PAIDEIA")
        urls = {norm_url(card["official_url"])} | {norm_url(u) for u in card["other_urls"]}
        self.assertIn(norm_url("https://github.com/OPTIMETA/PAIDEIA"), urls)
        self.assertIn(norm_url("https://github.com/TaewoooPark/PAIDEIA"), urls)
        self.assertIn("1216957019", card["identity_verified"]["method"])
        self.assertIn("301", card["identity_verified"]["method"])

    def test_no_local_paths_or_secrets_in_r9_files(self):
        files = list(R9.glob("*.json")) + [WORKSTREAMS / d for d in R9_DOCS if (WORKSTREAMS / d).exists()]
        for f in files:
            text = f.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"/Users/|/private/tmp|/home/[a-z]", f.name)
            self.assertNotRegex(text, r"sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}", f.name)

    def test_r9_docs_exist_and_separate_facts_from_hypotheses(self):
        for d in R9_DOCS:
            text = (WORKSTREAMS / d).read_text(encoding="utf-8")
            for marker in ("Fakt", "Hypothese", "Designentscheidung", "Nicht belegt"):
                self.assertIn(marker, text, "%s lacks marker %s" % (d, marker))


if __name__ == "__main__":
    unittest.main()
