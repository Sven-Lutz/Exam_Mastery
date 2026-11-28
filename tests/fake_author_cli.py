"""Stand-in for an authoring CLI in tests (provider 'command'): reads the order from stdin and acts according to the
next behaviour in a control file (argv[1]): good | bad_id | limit | crash. Records each call. No model is involved."""
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ctl_path = Path(sys.argv[1])
ctl = json.loads(ctl_path.read_text(encoding="utf-8"))
prompt = sys.stdin.read()
behaviour = ctl["queue"].pop(0) if ctl["queue"] else "good"
ctl.setdefault("calls", []).append({"behaviour": behaviour, "cwd": os.getcwd(), "feedback": "Ergebnis der automatischen" in prompt,
                                    "action_update": "Quellen dieses Kapitels haben sich geändert" in prompt,
                                    "action_revise": "maschinelle Qualitätsbefunde" in prompt,
                                    "env_secret": sorted(k for k in os.environ if re.search("KEY|TOKEN|ANTHROPIC", k))})
ctl_path.write_text(json.dumps(ctl), encoding="utf-8")
if behaviour == "limit":
    print("Error: You've hit your limit · resets 7am")
    sys.exit(1)
if behaviour == "crash":
    sys.exit(2)
draft = Path(os.environ["MASTERY_DRAFT_DIR"])
unit = json.loads((REPO / "fixtures/experience_reference.json").read_text(encoding="utf-8"))
unit["unit_id"] = re.search(r'unit_id "([^"]+)"', prompt).group(1) if behaviour == "good" else "wrong/id"
(draft / "unit.json").write_text(json.dumps(unit, ensure_ascii=False), encoding="utf-8")
(draft / "authoring.json").write_text(json.dumps({"schema": "mastery-authoring-record-v1", "author": {"kind": "x"},
                                                  "verification": [{"claim": "c", "method": "sympy", "result": "ok"}]}),
                                      encoding="utf-8")
print(json.dumps({"status": "done", "note": "fake"}))
