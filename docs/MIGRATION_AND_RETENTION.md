# Migration and retention policy

## Scope and non-negotiable safeguards

This repository is **public**. Import the existing working code rather than starting over, but never publish source documents, licensed books, private study records, passwords, .env values, private keys, provider traces with secrets or embedded tokens.

The repository is currently only a bootstrap. **Do not remove the only local copy of any source file.**

### Ordered migration procedure (for the Mac operator)

1. **Pause local generation** safely and save resumable run metadata. Inventory canonical and duplicate `Exam_Mastery_Studio` clones, their realpaths, branches, commits, uncommitted work, stashes, worktrees, running jobs and external input/output dependencies.
2. Collect source-of-truth research, product/learning science specifications, test evidence and learning-material acceptance decisions. Record what is implemented versus merely planned.
3. Compare local Git history to the newly initialized GitHub repository, inspect licenses and redistribution rights, run a secret/content audit over **tracked files and history**, and identify generated or oversized data. Never blindly `git push --mirror`, `git push --all`, `git add -A` or upload all locally tracked files into a public repository.
4. For clean history, preserve actual provenance by a carefully reviewed branch import (prefer a PR). If history contains sensitive or copyrighted information, publish a **sanitized source snapshot** with a documented local archival record and no unsafe history.
5. Import all essential executable source, shared configuration, templates, deterministic tests, migration/maintenance scripts, setup docs and reusable synthetic fixtures. Add effective `.gitignore` rules, pre-commit and CI checks. Do not publish large course outputs.
6. Verify from a **fresh clone** that the project installs, runs supported tests and can create a small output from synthetic/redistributable fixtures. Reproduce key commits and compare SHA-256 manifests of intended tracked files.
7. Move to **one** canonical local development checkout if local execution is needed. Keep course originals and working output in documented, separate, private locations outside this public Git repo.
8. Inventory local storage with sizes, hashes, ownership, reference checks, current jobs and rollback dependencies. Retain the latest human-rejected benchmark as a compact evidence bundle. Delete only verified redundant checkouts, derived outputs, stale caches and obsolete test runs after recovery testing. Do not delete unsynced changes, unreferenced-but-unique research, original inputs, approved releases, active or resumable runs.
9. Record physical disk usage before/after (`df`, `du` where meaningful; consider APFS clones and hardlinks). Do not count Trash/quarantine on the same disk as freed space. Maintain an auditable cleanup manifest.
10. Enforce retention/low-disk rules in the engine and repeat the setup and restoration smoke test once cleanup is finished.

## Desired end state

- One canonical, reviewed GitHub codebase; protected `main` where supported.
- One minimal Mac checkout **only if needed for local development/execution**.
- Original private course files and personal study data stored outside GitHub.
- Derived runs/output subject to retention and size budgets.
- Permanent source provenance, learning-science decisions and human rejection records.
- No automated claim of academic quality based on CI success.

## Release acceptance

Existing rejected material remains `HUMAN_REJECTED`. New candidate releases require precise mathematics, genuine book-level exposition, substantive source-grounded depth, instructive original visuals, complete worked solutions, an effective learning flow and explicit human acceptance. Automated technical checks are necessary but insufficient.

## Stop conditions

Stop destructive cleanup if file ownership, source uniqueness, rights, secrets, Git integrity, restart dependencies or recovery status is uncertain. Document the blocker with a specific file-level resolution; do not silently overwrite or delete.
