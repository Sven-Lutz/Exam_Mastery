"""Build r6/policy_index.json: one frozen snapshot of every workstream policy file at a pinned commit.

Run from a checkout that has the research branches fetched:  python3 build_policy_index.py [out.json]
The index is an input for the R6 synthesis and red team, not a source of truth; the workstream files are.
"""
import json
import subprocess
import sys
from pathlib import Path

SOURCES = [  # (workstream, branch, policy file)
    ("R1", "research/r1-learning-science-20261127", "docs/research/workstreams/r1/r1_learning_policies.json"),
    ("R2", "research/r2-formal-quantitative-20261127", "docs/research/workstreams/r2/r2_learning_policies.json"),
    ("R3", "research/r3-contextual-reasoning-20261127", "docs/research/workstreams/r3/r3_learning_policies.json"),
    ("R4", "research/r4-embodied-20261127", "docs/research/workstreams/r4/r4_learning_policies.json"),
    ("R5", "research/r5-tutoring-measurement-20261127", "docs/research/workstreams/r5/r5_tutoring_policies.json"),
    ("R7", "research/r7-resources-20261127", "docs/research/workstreams/r7/r7_resource_policies.json"),
    ("R8", "research/r8-anki-workflows-20261127", "docs/research/workstreams/r8/r8_workflow_policies.json"),
    ("R9", "research/r9-tutoring-resources-20261127", "docs/research/workstreams/r9/r9_tutor_policies.json"),
]
KEEP = ("id", "title", "applies_to_operations", "context", "recommendation", "abstain_or_fallback", "observable",
        "independent_outcome", "failure_modes", "falsifier", "status", "implementation_status", "learning_evaluation")


def git(*args):
    return subprocess.check_output(("git",) + args, text=True)


def main(out):
    index = {"schema": "mastery-policy-index/1", "note": "frozen snapshot for R6; workstream files are authoritative",
             "sources": [], "policies": []}
    for ws, branch, path in SOURCES:
        ref = "origin/" + branch
        try:
            sha = git("rev-parse", ref).strip()
            doc = json.loads(git("show", "%s:%s" % (sha, path)))
        except subprocess.CalledProcessError:
            index["sources"].append({"workstream": ws, "branch": branch, "file": path, "commit": None, "missing": True})
            continue
        index["sources"].append({"workstream": ws, "branch": branch, "file": path, "commit": sha,
                                 "policies": len(doc["policies"]), "coverage_gaps": doc.get("coverage_gaps") or doc.get("open_research")})
        for p in doc["policies"]:
            row = {k: p.get(k) for k in KEEP}
            row.update(workstream=ws, certainty=p["certainty"]["level"],
                       evidence=[e["source_id"] for e in p.get("evidence", [])],
                       products=sorted((p.get("product_affordances") or {}).keys()))
            index["policies"].append(row)
    Path(out).write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return index


if __name__ == "__main__":
    idx = main(sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).with_name("policy_index.json")))
    print(len(idx["policies"]), "policies;", [(s["workstream"], s.get("policies")) for s in idx["sources"]])
