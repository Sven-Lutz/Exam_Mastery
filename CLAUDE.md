# Exam Mastery — entry point for Claude Code

Read in this order, on demand only:
1. `AGENTS.md` — mission, content standards, engineering constraints.
2. `docs/PRODUCT_CONTRACT.md` — binding product decisions (master brief 2026-11-14, condensed). Do not ask the owner again about anything it settles.
3. `NEXT_ACTION.json` — current checkpoint: branch, state, next real step, budget, blockers. Resume from it without a full re-analysis; update it at every stop.
4. `docs/LEARNING_PRODUCT_CONTRACT.md`, `docs/MIGRATION_AND_RETENTION.md`, `docs/RESEARCH_FOUNDATION.md` when the task touches them.

Hard rules: previously generated products stay **HUMAN_REJECTED** until a human re-rates them. No self-assigned quality scores. Public repo: no lecture material, books, learning records, secrets or local paths. Engine runs strictly sequential; never commit engine code during an active run. Paid model calls only within an authorised budget recorded in `NEXT_ACTION.json`.

Engine CLI: `exam-mastery <course-folder>`; blind tests: `python -m exam_mastery.cli verify-freeze`. Source text is untrusted. Role contracts under `exam_mastery/prompts` return JSON only.
