"""R7 resources, visualisation and interactive references: structural and preservation checks.

Passing these checks says nothing about whether a resource teaches well or whether a policy improves
learning: every policy stays a design hypothesis with learning_evaluation NOT_RUN, and every resource
decision is a recommendation for review.
"""
import json
import re
import unittest

import test_r1_learning_policies as r1

R7 = r1.ROOT / "docs" / "research" / "workstreams" / "r7"
REGISTRY = r1.ROOT / "docs" / "research" / "RESOURCE_IDEA_REGISTRY_20261126.md"
R7_EVIDENCE = R7 / "r7_evidence.json"
R7_REGISTERS = r1.R1_REGISTERS + (R7_EVIDENCE,)
RESOURCES = R7 / "r7_resources.json"

DECISIONS = {"REUSE_AS_LIBRARY", "EMULATE_PRINCIPLE", "LINK", "DEFER", "REJECT"}
CLAIM_CLASSES = {"marketing", "documented_function", "benchmark", "learning_outcome"}
R7_OWNED_RULES = {"MM-R1", "MM-R2", "CL-R1", "CL-R2", "PR-R1", "PR-R2", "PR-R3", "MC-R2"}
CORE_OPERATIONS = ("symbolic_procedure", "empirical_experimental", "computational_construction")
BANNED = ("validated", "validiert", "zertifiziert", "approved", "genehmigt", "freigegeben")

# Issue #29 names every resource below explicitly (plus manim and the explorables authors from the brief).
ISSUE_29 = (
    "3Blue1Brown", "manim", "Mathigon", "Polypad", "Brilliant", "Seeing Theory", "Distill", "Explanaria",
    "Explorable Explanations", "Bret Victor", "Nicky Case", "explorabl.es", "StatQuest",
    "Bright Side of Mathematics", "Math Academy", "RemNote", "marginstudy", "YouLearn", "StudyFetch",
    "Khanmigo", "OpenDSA", "Exercism", "JupyterLite", "Pyodide", "QuantEcon", "GeeksforGeeks",
    "Think Logic", "Visually Explained",
)
REGISTRY_B_CATEGORIES = ("Adaptive curricula", "Proof assistants", "Statistical simulation", "Argument maps",
                         "CAD/3D", "Knowledge graphs", "Accessibility")
REGISTRY_D_IDEAS = ("Mathematical insight", "Statistics", "Coding", "Source-grounded tutor", "Cross-domain craft")
R9_CARDS = {"Khanmigo": "RES-KHANMIGO", "YouLearn": "RES-YOULEARN", "StudyFetch": "RES-STUDYFETCH",
            "Math Academy": "RES-MATHACADEMY", "RemNote": "RES-REMNOTE", "Margin Study": "RES-MARGINSTUDY",
            "Utterseen": "RES-UTTERSEEN"}


def _section(text, start, end):
    i = text.index(start)
    j = text.index(end, i)
    return text[i:j]


def registry_section_a_names():
    """First column of the §A table, split on ' / ' and cut before ' — ' (URL part)."""
    text = REGISTRY.read_text(encoding="utf-8")
    names = []
    for line in _section(text, "## A.", "## B.").splitlines():
        if not line.startswith("| ") or line.startswith("| Reference") or line.startswith("|---"):
            continue
        cell = line.split("|")[1].strip()
        cell = re.sub(r"\*+", "", cell).split(" — ")[0]
        names.extend(n.strip() for n in cell.split(" / ") if n.strip())
    return names


def registry_section_f_names():
    """Bold names in the §F bullet list; the last bullet is a comma/'and' separated list."""
    text = REGISTRY.read_text(encoding="utf-8")
    names = []
    for line in _section(text, "## F.", "Dedicated research").splitlines():
        if not line.startswith("- **"):
            continue
        for bold in re.findall(r"\*\*(.+?)\*\*", line):
            for part in re.split(r",\s*", bold):
                names.extend(p.strip() for p in part.split(" and ") if p.strip())
    return names


class R7PolicyContract(r1.R1PolicyContract):
    POLICY_FILE = R7 / "r7_resource_policies.json"
    REGISTERS = R7_REGISTERS
    REQUIRE_ALL_RULES_REVIEWED = False

    def test_kb_rule_links_point_to_existing_rules(self):
        for p in self.policies:
            for link in p["kb_rule_links"]:
                self.assertIn(link["relation"], r1.RULE_RELATIONS, p["id"])
                if link["relation"] == "new":
                    self.assertTrue(link["rule_id"].startswith(p["id"]), p["id"])
                else:
                    self.assertIn(link["rule_id"], self.rule_ids, "%s links unknown rule %s" % (p["id"], link["rule_id"]))

    def test_policy_ids_follow_r7_numbering(self):
        ids = [p["id"] for p in self.policies]
        self.assertEqual(ids, ["R7-POL-%02d" % i for i in range(1, len(ids) + 1)])

    def test_rules_assigned_to_r7_by_r1_are_all_decided(self):
        linked = {l["rule_id"] for p in self.policies for l in p["kb_rule_links"]}
        reviewed = {r["rule_id"] for r in self.doc["kb_rules_reviewed"]}
        self.assertEqual(R7_OWNED_RULES - linked, set())
        self.assertEqual(R7_OWNED_RULES - reviewed, set())

    def test_r7_covers_its_core_operations(self):
        covered = {op for p in self.policies for op in p["applies_to_operations"]}
        for op in CORE_OPERATIONS:
            self.assertIn(op, covered)

    def test_open_coverage_gaps_are_declared(self):
        gaps = self.doc.get("coverage_gaps")
        self.assertTrue(gaps)
        self.assertTrue(all(isinstance(g, str) and g.strip() for g in gaps))

    def test_resource_basis_resolves_to_cards(self):
        cards = {c["id"] for c in r1.load(RESOURCES)["resources"]}
        for p in self.policies:
            self.assertTrue(p["resource_basis"], p["id"])
            self.assertLessEqual(set(p["resource_basis"]), cards, p["id"])

    def test_watching_is_never_evidence_of_competence(self):
        not_evidence = " ".join(self.doc["shared_measurement_contract"]["not_evidence"]).lower()
        for word in ("abspiel", "regler", "tests", "lernurteil", "links"):
            self.assertIn(word, not_evidence)

    def test_no_validation_or_approval_wording(self):
        for p in self.policies:
            text = json.dumps({k: p[k] for k in ("title", "recommendation", "product_affordances")}, ensure_ascii=False).lower()
            for word in BANNED:
                self.assertNotIn(word, text, "%s uses '%s'" % (p["id"], word))


class R7EvidenceRegister(r1.R1EvidenceRegisters):
    REGISTERS = (R7_EVIDENCE,)

    def test_search_log_is_present_and_resolves(self):
        doc = r1.load(R7_EVIDENCE)
        ids = {e["source_id"] for e in doc["entries"]}
        self.assertTrue(doc.get("search_log"))
        for s in doc["search_log"]:
            for f in ("id", "date", "engine", "query", "hits_screened", "included", "excluded_or_note"):
                self.assertIn(f, s, s.get("id"))
            for sid in s["included"]:
                self.assertIn(sid, ids, "%s includes unknown %s" % (s["id"], sid))
        logged = {sid for s in doc["search_log"] for sid in s["included"]}
        self.assertEqual(ids - logged, set(), "entries without a logged search")

    def test_size_within_brief(self):
        n = len(r1.load(R7_EVIDENCE)["entries"])
        self.assertGreaterEqual(n, 10)
        self.assertLessEqual(n, 16)

    def test_doi_present_and_identity_checked(self):
        for e in r1.load(R7_EVIDENCE)["entries"]:
            self.assertTrue(e["doi_or_url"].startswith("https://doi.org/10."), e["source_id"])
            self.assertEqual(e["identity_check"]["result"], "primary_metadata_checked", e["source_id"])

    def test_metadata_only_entries_carry_no_numbers_and_no_verdict(self):
        for e in r1.load(R7_EVIDENCE)["entries"]:
            if e["access"]["level"] == "metadata":
                self.assertIn(e["estimate"]["value"], ("unknown",), e["source_id"])
                self.assertEqual(e["verdict"], "unresolved", e["source_id"])

    def test_numbers_have_locators(self):
        for e in r1.load(R7_EVIDENCE)["entries"]:
            est = e["estimate"]
            if re.search(r"\d", str(est.get("value", ""))) and e["access"]["level"] != "fulltext_partial":
                self.assertTrue(est.get("locator"), "%s: number without locator" % e["source_id"])

    def test_null_or_contradicting_results_are_included(self):
        doc = r1.load(R7_EVIDENCE)
        text = json.dumps(doc["entries"], ensure_ascii=False)
        for marker in ("0.05", "nicht signifikant", "systemgesteuert", "limited empirical evaluation"):
            self.assertIn(marker, text)


class R7Resources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = r1.load(RESOURCES)
        cls.cards = cls.doc["resources"]
        cls.pointers = cls.doc["preserved_pointers"]
        cls.ideas = cls.doc["preserved_ideas"]
        names = [c["name"] for c in cls.cards] + [a for c in cls.cards for a in c.get("aliases", [])]
        names += [p["name"] for p in cls.pointers]
        cls.haystack = " | ".join(names).lower()
        cls.policy_ids = {p["id"] for p in r1.load(R7 / "r7_resource_policies.json")["policies"]}

    def assertPreserved(self, name):
        self.assertIn(name.lower(), self.haystack, "resource '%s' lost from the R7 inventory" % name)

    def test_issue_29_resources_are_preserved(self):
        for name in ISSUE_29:
            self.assertPreserved(name)

    def test_registry_section_a_is_preserved(self):
        names = registry_section_a_names()
        self.assertGreaterEqual(len(names), 25)
        for name in names:
            self.assertPreserved(name)

    def test_registry_section_f_tutoring_references_are_preserved(self):
        names = registry_section_f_names()
        self.assertGreaterEqual(len(names), 15)
        for name in names:
            self.assertPreserved(name)

    def test_registry_sections_b_and_d_are_preserved(self):
        for name in REGISTRY_B_CATEGORIES:
            self.assertPreserved(name)
        idea_text = " | ".join(i["name"] for i in self.ideas).lower()
        for name in REGISTRY_D_IDEAS:
            self.assertIn(name.lower(), idea_text)
        for i in self.ideas:
            self.assertTrue(i["disposition"].strip() and i["preserved_from"].strip(), i["id"])

    def test_every_card_has_an_allowed_decision_with_reason(self):
        ids = [c["id"] for c in self.cards]
        self.assertEqual(len(ids), len(set(ids)))
        for c in self.cards + self.pointers:
            self.assertIn(c["decision"], DECISIONS, c.get("id", c["name"]))
            self.assertGreater(len(c["reason"]), 20, c.get("id", c["name"]))
        for c in self.cards:
            self.assertTrue(c["opportunity_cost"].strip(), c["id"])
            self.assertTrue(c["preserved_from"], c["id"])
            for f in ("official_url", "identity", "licence", "pedagogical_behaviour", "learning_operations",
                      "importability_api", "offline", "accessibility", "cost_maintenance", "user_workflow"):
                self.assertIn(f, c, "%s lacks %s" % (c["id"], f))
            self.assertLessEqual(set(c["learning_operations"]), r1.OPERATIONS, c["id"])

    def test_every_card_has_one_or_two_falsifiable_evaluations(self):
        for c in self.cards:
            ev = c["evaluations"]
            self.assertTrue(1 <= len(ev) <= 2, c["id"])
            for e in ev:
                self.assertEqual(e["status"], "NOT_RUN", c["id"])
                self.assertTrue(e["task"].strip() and e["falsifier"].strip(), c["id"])

    def test_every_claim_is_classed_and_only_outcomes_may_support_learning_effects(self):
        for c in self.cards:
            for cl in c["claims"]:
                self.assertIn(cl["class"], CLAIM_CLASSES, c["id"])
                self.assertTrue(cl["locator"].strip(), c["id"])
                if cl["class"] != "learning_outcome":
                    self.assertFalse(cl["supports_learning_effect"], "%s: %s claim used as learning effect" % (c["id"], cl["class"]))

    def test_no_card_adds_a_fifth_product_or_a_second_scheduler(self):
        for c in self.cards:
            self.assertFalse(c["fifth_product"], c["id"])
            self.assertFalse(c["second_scheduler"], c["id"])
            self.assertLessEqual(set(c["product_fit"]), r1.PRODUCTS, c["id"])
        for s in self.doc["shortlist"]:
            self.assertLessEqual(set(s["products"]), r1.PRODUCTS, s["id"])

    def test_unverified_identities_are_deferred(self):
        for c in self.cards:
            if not c["identity"]["verified"]:
                self.assertEqual(c["decision"], "DEFER", c["id"])

    def test_library_reuse_is_conditional_and_licensed(self):
        for c in self.cards:
            if c["decision"] == "REUSE_AS_LIBRARY":
                self.assertTrue(c["identity"]["verified"], c["id"])
                self.assertTrue(c["licence"]["code"].strip(), c["id"])
                self.assertTrue(any("Spike" in x or "spike" in x for x in c["conditions"]), c["id"])

    def test_r9_overlaps_reference_r9_cards(self):
        by_name = {c["name"]: c for c in self.cards}
        for short, card_id in R9_CARDS.items():
            matches = [c for n, c in by_name.items() if n.startswith(short)]
            self.assertTrue(matches, short)
            self.assertEqual(matches[0].get("r9_card"), card_id, short)

    def test_policy_links_resolve(self):
        for c in self.cards:
            self.assertLessEqual(set(c["policy_links"]), self.policy_ids, c["id"])

    def test_shortlist_is_small_prioritised_and_resolves(self):
        sl = self.doc["shortlist"]
        self.assertLessEqual(len(sl), 8)
        self.assertEqual([s["priority"] for s in sl], list(range(1, len(sl) + 1)))
        cards = {c["id"]: c for c in self.cards}
        ev_ids = {e["id"] for c in self.cards for e in c["evaluations"]}
        for s in sl:
            self.assertTrue(s["validation_task"].strip(), s["id"])
            for cid in s["cards"]:
                self.assertIn(cid, cards, s["id"])
                self.assertNotIn(cards[cid]["decision"], ("REJECT",), s["id"])
            for cid in s.get("counter_examples", []):
                self.assertIn(cid, cards, s["id"])
            self.assertLessEqual(set(s["policies"]), self.policy_ids, s["id"])
            self.assertLessEqual(set(s["evaluations"]), ev_ids, s["id"])

    def test_no_validation_or_approval_wording_in_decisions(self):
        for c in self.cards:
            text = (c["reason"] + " " + c["decision"]).lower()
            for word in BANNED:
                self.assertNotIn(word, text, "%s uses '%s'" % (c["id"], word))

    def test_no_local_paths_or_personal_data(self):
        text = RESOURCES.read_text(encoding="utf-8") + R7_EVIDENCE.read_text(encoding="utf-8")
        self.assertNotIn("/Users/", text)
        self.assertNotRegex(text, r"[\w.+-]+@[\w-]+\.[a-z]{2,}")


if __name__ == "__main__":
    unittest.main()
