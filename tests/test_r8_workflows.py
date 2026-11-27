"""R8 Anki/Obsidian workflows: R1 policy contract, evidence register and tool-card checks.

Passing these checks says nothing about scientific correctness, product quality or
learning effect. Every policy stays a design hypothesis with learning_evaluation
NOT_RUN; every tool decision is a research recommendation awaiting review. No test
here opens Anki, Obsidian, a collection or a vault.
"""
import json
import re
import unittest

import test_r1_learning_policies as r1

WORKSTREAMS = r1.ROOT / "docs" / "research" / "workstreams"
R8 = WORKSTREAMS / "r8"
R8_EVIDENCE = R8 / "r8_evidence.json"
R8_TOOLS = R8 / "r8_tools.json"
R8_POLICIES = R8 / "r8_workflow_policies.json"
R8_REPORT = WORKSTREAMS / "R8_ANKI_OBSIDIAN_WORKFLOWS.md"
BRIEF = r1.ROOT / "docs" / "research" / "ANKI_OBSIDIAN_TOOLING_RESEARCH_20261126.md"
R8_REGISTERS = r1.R1_REGISTERS + (R8_EVIDENCE,)

DECISIONS = {"ADOPT_DEFAULT", "OPTIONAL_ADAPTER", "LINK", "DEFER", "REJECT"}
ADOPTED = {"ADOPT_DEFAULT", "OPTIONAL_ADAPTER"}
SCHEDULER_ROLES = {"native_anki", "none", "can_modify_anki_scheduling", "second_scheduler"}
SCHEDULING_ROLES = {"can_modify_anki_scheduling", "second_scheduler"}
CLAIM_CLASSES = {"marketing", "documented_function", "benchmark", "learning_outcome"}
CLAIM_TYPES = {"learning_effect", "technical_behaviour", "scheduler_prediction", "privacy_security",
               "product_capability", "measurement_contract"}
LEARNING_CLASSES = {"learning_outcome_experimental", "learning_outcome_quasi_experimental"}
NON_LEARNING_CLASSES = {"benchmark", "technical_documentation", "source_code", "vendor_documentation",
                        "repository_metadata", "algorithm_paper", "observational_log_analysis", "synthesis",
                        "secondary_summary"}
IDENTITY_RESULTS = {"primary_metadata_checked", "unresolved"}
MIGRATION_LEVELS = {"low", "medium", "high", "not_applicable"}

# Named in issue #30 (the issue text is not in the repository, so the list is fixed here).
ISSUE_30_NAMES = ("Anki", "FSRS", ".apkg", "AnkiConnect", "AnkiWeb", "Obsidian core", "Bases", "Canvas",
                  "Obsidian CLI", "Obsidian Headless", "agent skills", "Obsidian community FSRS plugins",
                  "RemNote", "Mochi", "Joplin", "Logseq", "SiYuan", "SuperMemo")
R9_REFS = {"RES-REMNOTE", "RES-MATHACADEMY", "RES-DEEPTUTOR", "RES-OPENTUTOR", "RES-STUDYFETCH"}
REPORT_SECTIONS = ("Kurzfassung", "Methode und Zugang", "Entscheidungsmatrix", "Minimaler praktischer Aufbau",
                   "Identität, Versionierung, Medien und FSRS", "Generierter Obsidian-Bereich und Sidecar",
                   "Backup- und Konfliktpolitik", "Testplan mit Wegwerfprofilen", "Gegenargumente",
                   "Nicht-Ziele", "Risiken", "Was wir nicht behaupten", "Owner-Entscheidungen",
                   "Fragen an Reviewer", "Reproduktion", "Anhang A")


def norm(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def norm_url(url):
    return url.strip().rstrip("/").rstrip(".,;)").rstrip("/").lower()


def brief_options():
    text = BRIEF.read_text(encoding="utf-8")
    block = text.split("## Option comparison", 1)[1].split("\n## ", 1)[0]
    rows = [l for l in block.splitlines() if l.startswith("| ") and not l.startswith("| Option")]
    return [r.strip("|").split("|")[0].strip().strip("*").strip() for r in rows]


def brief_urls():
    text = BRIEF.read_text(encoding="utf-8")
    block = text.split("Official checks", 1)[1].split("**Source verification state", 1)[0]
    return {norm_url(u) for u in re.findall(r"https?://[^\s;|)]+", block)}


class R8PolicyContract(r1.R1PolicyContract):
    POLICY_FILE = R8_POLICIES
    REGISTERS = R8_REGISTERS
    REQUIRE_ALL_RULES_REVIEWED = False

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.r8_entries = {e["source_id"]: e for e in r1.load(R8_EVIDENCE)["entries"]}

    def test_kb_rule_links_point_to_existing_rules(self):
        for p in self.policies:
            for link in p["kb_rule_links"]:
                self.assertIn(link["relation"], r1.RULE_RELATIONS, p["id"])
                if link["relation"] == "new":
                    self.assertTrue(link["rule_id"].startswith(p["id"]), p["id"])
                else:
                    self.assertIn(link["rule_id"], self.rule_ids, "%s links unknown rule %s" % (p["id"], link["rule_id"]))

    def test_policy_ids_are_r8(self):
        for p in self.policies:
            self.assertRegex(p["id"], r"^R8-POL-\d{2}$")

    def test_sp_r1_is_kept(self):
        links = {(l["rule_id"], l["relation"]) for p in self.policies for l in p["kb_rule_links"]}
        self.assertFalse({("SP-R1", "replaces"), ("SP-R1", "contradicts")} & links)
        self.assertTrue(any(rule == "SP-R1" for rule, _ in links))

    def test_evidence_edges_declare_claim_type(self):
        for p in self.policies:
            for e in p["evidence"]:
                self.assertIn(e.get("supports_claim_type"), CLAIM_TYPES, "%s/%s" % (p["id"], e["source_id"]))

    def test_benchmarks_never_support_a_learning_effect(self):
        for p in self.policies:
            for e in p["evidence"]:
                entry = self.r8_entries.get(e["source_id"])
                if entry is not None and entry["evidence_class"] == "benchmark":
                    self.assertNotEqual(e["supports_claim_type"], "learning_effect", p["id"])
                if e["relation"] == "supports" and e["supports_claim_type"] == "learning_effect" and entry is not None:
                    self.assertTrue(entry["may_support_learning_effect"],
                                    "%s uses %s (%s) as learning evidence" % (p["id"], e["source_id"], entry["evidence_class"]))

    def test_expected_policy_themes_are_present(self):
        joined = json.dumps(self.policies, ensure_ascii=False)
        for needle in ("einzige Scheduler", "GUID", "Notiztyp-ID", "Wegwerf", "Sidecar", "Obsidian",
                       "Eigentumszonen", "Benchmark", "Desired Retention", "AnkiConnect", "eigene Karten"):
            self.assertIn(needle, joined, "no policy covers '%s'" % needle)

    def test_no_policy_builds_a_scheduler(self):
        for p in self.policies:
            text = (p["recommendation"] + json.dumps(p["product_affordances"], ensure_ascii=False)).lower()
            for banned in ("eigener scheduler wird", "intervall berechnet die engine", "fälligkeiten berechnet die engine"):
                self.assertNotIn(banned, text, p["id"])

    def test_coverage_gaps_conflicts_and_engine_findings(self):
        self.assertTrue(self.doc["coverage_gaps"])
        ids = {p["id"] for p in self.policies}
        for cr in self.doc["conflict_resolution"]:
            self.assertLessEqual(set(cr["between"]), ids, cr["id"])
        for f in self.doc["engine_findings"]:
            self.assertIn(f["policy"], ids, f["id"])
            self.assertTrue(f["locator"].strip() and f["finding"].strip(), f["id"])

    def test_no_validation_wording(self):
        banned = ("validated", "validiert", "zertifiziert", "approved", "nachgewiesen wirksam")
        for p in self.policies:
            blob = json.dumps({k: p[k] for k in ("title", "recommendation", "product_affordances")}, ensure_ascii=False).lower()
            for word in banned:
                self.assertNotIn(word, blob, "%s uses '%s'" % (p["id"], word))


class R8EvidenceRegister(r1.R1EvidenceRegisters):
    REGISTERS = (R8_EVIDENCE,)

    def test_search_log_is_present_and_resolves(self):
        doc = r1.load(R8_EVIDENCE)
        ids = {e["source_id"] for e in doc["entries"]}
        self.assertTrue(doc.get("search_log"))
        for s in doc["search_log"]:
            for f in ("id", "date", "engine", "query", "hits_screened", "included", "excluded_or_note"):
                self.assertIn(f, s, s.get("id"))
            for sid in s["included"]:
                self.assertIn(sid, ids, "%s includes unknown %s" % (s["id"], sid))
        logged = {sid for s in doc["search_log"] for sid in s["included"]}
        self.assertEqual(ids - logged, set(), "entries without a logged search")

    def test_failed_searches_are_logged(self):
        doc = r1.load(R8_EVIDENCE)
        self.assertTrue(any(not s["included"] for s in doc["search_log"]), "no failed or empty search recorded")

    def test_evidence_class_controls_learning_support(self):
        for e in r1.load(R8_EVIDENCE)["entries"]:
            cls = e["evidence_class"]
            self.assertIn(cls, LEARNING_CLASSES | NON_LEARNING_CLASSES, e["source_id"])
            self.assertIsInstance(e["may_support_learning_effect"], bool, e["source_id"])
            if cls in NON_LEARNING_CLASSES:
                self.assertFalse(e["may_support_learning_effect"], e["source_id"])

    def test_identity_checked_or_declared_unresolved(self):
        for e in r1.load(R8_EVIDENCE)["entries"]:
            self.assertIn(e["identity_check"]["result"], IDENTITY_RESULTS, e["source_id"])
            self.assertTrue(e["identity_check"]["method"].strip(), e["source_id"])
            if e["identity_check"]["result"] == "unresolved":
                self.assertFalse(e["may_support_learning_effect"], e["source_id"])


class R8ToolCards(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.doc = r1.load(R8_TOOLS)
        cls.cards = cls.doc["tools"]
        cls.evidence = {e["source_id"]: e for e in r1.load(R8_EVIDENCE)["entries"]}
        cls.names = []
        cls.urls = set()
        for c in cls.cards:
            cls.names.append(norm(c["name"]))
            cls.names.extend(norm(a) for a in c.get("aliases", []))
            cls.urls.add(norm_url(c["official_url"]))
            cls.urls.update(norm_url(u) for u in c.get("other_urls", []))
        for e in cls.evidence.values():
            cls.urls.add(norm_url(e["doi_or_url"]))
            cls.urls.add(norm_url(e["access"]["url"].split(" ")[0]))

    def has_name(self, name):
        n = norm(name)
        return any(n in x for x in self.names)

    def test_brief_options_preserved(self):
        options = brief_options()
        self.assertGreaterEqual(len(options), 8)
        for name in options:
            self.assertTrue(self.has_name(name), "brief option missing: %s" % name)

    def test_brief_urls_preserved(self):
        urls = brief_urls()
        self.assertGreaterEqual(len(urls), 10)
        for url in urls:
            self.assertIn(url, self.urls, "brief URL missing: %s" % url)

    def test_issue_30_options_preserved(self):
        for name in ISSUE_30_NAMES:
            self.assertTrue(self.has_name(name), "issue #30 option missing: %s" % name)

    def test_r9_cross_references(self):
        refs = {c["r9_ref"] for c in self.cards if c.get("r9_ref")}
        self.assertEqual(refs, R9_REFS)

    def test_ids_unique(self):
        ids = [c["id"] for c in self.cards]
        self.assertEqual(len(ids), len(set(ids)))

    def test_cards_complete(self):
        for c in self.cards:
            for f in ("id", "name", "category", "official_url", "owner", "licence", "version_or_activity",
                      "access_date", "identity_verified", "source_ids", "capabilities", "local_first_privacy_sync",
                      "history_preservation", "migration_burden", "scheduler_role", "ad1_conflict", "decision",
                      "tested_workflow", "origin"):
                self.assertIn(f, c, "%s lacks %s" % (c.get("id"), f))
            self.assertRegex(c["access_date"], r"^\d{4}-\d{2}-\d{2}$")
            self.assertIsInstance(c["identity_verified"]["value"], bool, c["id"])
            self.assertTrue(c["identity_verified"]["method"].strip(), c["id"])
            self.assertIn(c["migration_burden"]["level"], MIGRATION_LEVELS, c["id"])
            self.assertTrue(c["migration_burden"]["reason"].strip(), c["id"])
            self.assertTrue(c["origin"], c["id"])
            self.assertTrue(c["tested_workflow"].startswith("NOT_RUN"), c["id"])
            for sid in c["source_ids"]:
                self.assertIn(sid, self.evidence, "%s cites unknown source %s" % (c["id"], sid))

    def test_each_card_has_decision_reason_and_opportunity_cost(self):
        for c in self.cards:
            d = c["decision"]
            self.assertIn(d["value"], DECISIONS, c["id"])
            self.assertGreater(len(d["reason"]), 30, c["id"])
            self.assertTrue(d["opportunity_cost"].strip(), c["id"])
            self.assertTrue(d["revisit_if"].strip(), c["id"])

    def test_adopted_cards_introduce_no_second_scheduler(self):
        native = [c for c in self.cards if c["scheduler_role"] == "native_anki"]
        self.assertEqual(len(native), 1)
        self.assertEqual(native[0]["decision"]["value"], "ADOPT_DEFAULT")
        for c in self.cards:
            self.assertIn(c["scheduler_role"], SCHEDULER_ROLES, c["id"])
            if c["decision"]["value"] in ADOPTED:
                self.assertNotIn(c["scheduler_role"], SCHEDULING_ROLES, c["id"])

    def test_second_schedulers_are_not_adopted(self):
        for c in self.cards:
            if c["scheduler_role"] == "second_scheduler":
                self.assertIn(c["decision"]["value"], {"DEFER", "REJECT"}, c["id"])

    def test_every_claim_is_classified_with_locator_and_source(self):
        for c in self.cards:
            self.assertTrue(c["capabilities"], c["id"])
            for claim in c["capabilities"]:
                self.assertIn(claim["class"], CLAIM_CLASSES, c["id"])
                self.assertTrue(claim["locator"].strip(), c["id"])
                self.assertTrue(claim["text"].strip(), c["id"])
                self.assertIn(claim["source_id"], self.evidence, c["id"])

    def test_benchmark_or_marketing_never_supports_learning(self):
        for c in self.cards:
            for claim in c["capabilities"]:
                if claim["supports_learning_effect"]:
                    self.assertEqual(claim["class"], "learning_outcome", "%s: %s" % (c["id"], claim["text"][:60]))
                    self.assertTrue(self.evidence[claim["source_id"]]["may_support_learning_effect"], c["id"])
                if self.evidence[claim["source_id"]]["evidence_class"] == "benchmark":
                    self.assertFalse(claim["supports_learning_effect"], c["id"])

    def test_no_local_paths_or_secrets_in_r8_files(self):
        files = list(R8.glob("*.json")) + [R8_REPORT]
        for f in files:
            if not f.exists():
                continue
            text = f.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"/Users/[a-z]|/private/tmp|/home/[a-z]", f.name)
            self.assertNotRegex(text, r"sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}", f.name)


class R8Report(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.text = R8_REPORT.read_text(encoding="utf-8")

    def test_required_sections_present(self):
        for s in REPORT_SECTIONS:
            self.assertIn(s, self.text, "report lacks section '%s'" % s)

    def test_implementation_prompt_is_gated(self):
        appendix = self.text.split("Anhang A", 1)[1]
        self.assertIn("Owner", appendix)
        self.assertRegex(appendix, r"(?i)erst nach|nur nach|only after")
        self.assertIn("Wegwerf", appendix)

    def test_every_tool_appears_in_the_matrix(self):
        for c in r1.load(R8_TOOLS)["tools"]:
            self.assertIn(c["id"], self.text, c["id"])

    def test_report_does_not_claim_validation(self):
        lowered = self.text.lower()
        for word in ("ist validiert", "wurde validiert", "approved", "zertifiziert"):
            self.assertNotIn(word, lowered)


if __name__ == "__main__":
    unittest.main()
