# Stops and what they mean

| Shown | Meaning | What the user can do |
|---|---|---|
| exit 3, `NOT_CONFIGURED` | no provider set up | SKILL.md step 2 |
| exit 3, `BUDGET_BLOCKED: max_requests reached` | the per-run request limit was hit | start the same folder again to resume, or raise `max_requests_per_run` in the config |
| exit 3, `QUOTA_BLOCKED` / usage limit | the provider's quota is exhausted | wait for the quota to reset, then start again (resumes) |
| `MODEL_UNAVAILABLE` | the configured model is not offered to this account | run setup again with a listed model |
| chapter `ESCALATED_HUMAN_DECISION_REQUIRED` | the engine cannot settle the chapter's order/session or eligibility | the listed `escalations` say what to decide; other chapters are produced anyway |
| `StageGateFailed` | a deterministic check failed (foreign anchor, wrong arithmetic, cited excluded figure, self-certification) | the chapter stops before the next paid call; the evidence is in `stage_gates.json` |
| dossier `coverage: FAIL` | some competencies were not produced or an exam question is unanswered | see `gaps`, `excluded`, `unanswered_questions` |
| dossier `subject_correctness: NOT_TESTED` | normal: no human or independent check yet | have a subject expert review the PDF |

## Exit 4 / AGENT_TURN_REQUIRED (provider `agent`)
- **Meaning:** the run waits for the calling agent. `NEXT.json` names the prompt file and the answer file.
- **What to do:**
  1. Write exactly one JSON answer to the answer file.
  2. Run the same command again; it continues the same run.
- **Note:** a contract repair arrives as a new prompt with its own answer file.

## `visuals --import` rejects statements
| Reason | Fix |
|---|---|
| `numbers not declared` | List every number that occurs in the statement. |
| `uses a failed arithmetic result` | Re-read the figure. |
| `REJECTED_STALE_RENDER` | The slide changed: run `exam-mastery visuals` again and re-read it. |
| `LOW confidence` | Never taught; leave it in the file as a record. |
