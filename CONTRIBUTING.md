# Contributing to Mastery

Humans and coding/research agents (Claude Code, Gemini, Codex or others) follow the same workflow. Start with [README](README.md), [vision](docs/MASTERY_VISION.md), [AGENTS](AGENTS.md), and the [live-work entry point](docs/CONTRIBUTOR_QUEUE.md). No private chat history is needed.

## 1. Select and claim work

- Read the current open [issues](https://github.com/Sven-Lutz/Exam_Mastery/issues) and [pull requests](https://github.com/Sven-Lutz/Exam_Mastery/pulls) before choosing. The queue is a dated navigation aid, not a substitute for live state.
- Prefer free, unblocked P0 then P1 then P2 tasks marked READY or explicitly delegated with scope and acceptance criteria. Umbrella contracts, historic feedback and already implemented research are context, not new assignments.
- Inspect issue comments, assignees, relevant PRs and active branches. If uncertain about overlap, propose a narrow independent review instead of duplicating implementation.
- Post a claim comment with scope, planned branch, base SHA, paths or research deliverable, and a checkpoint plan. Do not start until overlapping active claims are ruled out; ask a maintainer when claims conflict. A comment is not an atomic lock. Do not silently take over stale work.
- A contributor without write access forks and submits a PR; never share tokens or request broad permissions. A read-only agent may prepare a referenced report or patch for the human to submit. Follow provider limits; no account pooling or circumvention.

## 2. Work from the correct base

The current V1 integration base is `integration/mastery-v1-20261127` (PR #50). It is a development preview, not an approved product. For implementation/research based on V1 use the issue's named base (normally this integration branch); documentation-only default-branch issues may target main when explicitly indicated. Check live branch heads and record the exact base SHA. The owner alone approves integration/merge to main. Never merge, force-push, delete, rebase shared branches or alter protection/permissions yourself. Do not stack on unrelated unmerged work without agreement.

Example for an external contributor with a fork and a V1 task:

```sh
git clone https://github.com/YOUR-ACCOUNT/Exam_Mastery.git
cd Exam_Mastery
git remote add upstream https://github.com/Sven-Lutz/Exam_Mastery.git
git fetch upstream
git switch -c contrib/issue-62-fulltext upstream/integration/mastery-v1-20261127
git rev-parse HEAD
# implement/research only the claimed scope; stage reviewed files explicitly
git push -u origin contrib/issue-62-fulltext
```

Open a draft PR against the issue's specified upstream branch. Use "Refs #62", not "Closes" for provisional evidence or unaccepted work. External contributors may need a maintainer to help with a non-default target. Do not move other contributors' branches.

## 3. Reproduce before changing

Use declared dependencies only. Python 3.12 is the documented baseline. On a clean disposable checkout:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -e '.[qa]' pytest
.venv/bin/python -m playwright install chromium
.venv/bin/python -m pytest -q
.venv/bin/python -m unittest discover
```

Windows uses .venv/Scripts/python.exe; report platform-specific constraints. For the V1 synthetic example follow [MASTERY_V1.md](https://github.com/Sven-Lutz/Exam_Mastery/blob/integration/mastery-v1-20261127/docs/MASTERY_V1.md). Read the current CLI help and issue-specific run instructions; do not use private courses, personal Anki collections or private Obsidian vaults. A research-only contribution need not run unrelated test suites. Never assert commands ran when they did not.

## 4. Definition of done

- Every contribution must make a clear learning, correctness, safety or resource-efficiency improvement tied to the vision and issue. Reuse existing architecture and research; avoid parallel systems.
- Code: regression test the reported failure where feasible, run relevant tests, document reproduction and remaining failures. UI: inspect the actual rendered result; include synthetic screenshots when rights/privacy allow.
- Research: cite real primary sources with access status, exact locators, method, population, comparison, measured outcome, uncertainty, counterevidence and applicability. Distinguish product capability, hypothesis and measured learning effect. No new global policy without review.
- Learning content: check accuracy, course scope, independent tasks/solutions, notation, render and provenance. Report known errors and unavailable verification. A green CI does not mean learning or academic acceptance.
- Cost: report actual model calls/usage when visible (otherwise unknown), tests, environment and time where measured; no paid APIs without authorization. Use synthetic/redistributable inputs; no copyrighted materials, private student data, secrets, provider logs or mass outputs.
- PR description: linked issue, exact base, changed files, verification commands/results, remaining limits, contribution disclosure (human/AI), and next action. Make a small coherent PR; do not auto-approve or claim human acceptance.

## 5. Continue autonomously, but safely

After submitting a reviewable PR, select the next non-overlapping ready task; a review/verification task is useful when implementation is blocked. Stop at quota/resource limits or when no useful work remains. Checkpoint before the limit: commit only safe scoped changes, push your branch, open/update draft PR, comment the exact tested/unverified state and next steps. Do not consume quota for its own sake.

## Licensing and permissions

This repository is publicly visible, not necessarily openly licensed. The maintainer must settle the project license and contribution terms before broad third-party code acceptance/reuse. Until then do not assume permission to redistribute or incorporate third-party code/content; public-source review and issue feedback are possible, and proposed contributions remain subject to maintainer review. Cite and link external resources rather than copying them. No license is selected by this document.
