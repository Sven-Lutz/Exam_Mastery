# Engine import record (2026-11-14)

Source: local repo branch feat/v0.18-learning-engine @ 913db7b (clean tree, 117 commits).

Published as a curated snapshot without history: local commit metadata contains a private author address. Full history stays archived locally.

Excluded (reason): *.diff work diffs and P*/B6/FUNDING acceptance reports (local paths, superseded process docs); docs/p3_*, docs/release/*AUTHORIZATION (real-course diagnostics, local paths); work-skill/, WORK_START.md, scripts/build_review_fixture.py, fixtures/didactic_review_patch.json (local paths); legacy_agent_starter/ (superseded). Engine README/AGENTS kept as ENGINE_README.md and docs/ENGINE_AGENTS.md; bootstrap README/AGENTS unchanged.

Verification: fresh venv (Python 3.12) `pip install -e '.[qa]' pytest && playwright install chromium && pytest -q` → 715 passed, 6 skipped.
SHA-256 of every imported file vs. source: see SHA256SUMS (verified identical).
