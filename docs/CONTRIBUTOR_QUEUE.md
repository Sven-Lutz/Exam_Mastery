# Contributor queue — start here

Snapshot: 2026-11-28. The [live issues](https://github.com/Sven-Lutz/Exam_Mastery/issues) and [live PRs](https://github.com/Sven-Lutz/Exam_Mastery/pulls) take precedence over this snapshot. This is a lightweight index, not a second task tracker.

## Pick a task

Read [vision](MASTERY_VISION.md), [contribution workflow](../CONTRIBUTING.md), [release contract #58](https://github.com/Sven-Lutz/Exam_Mastery/issues/58) and [roadmap #57](https://github.com/Sven-Lutz/Exam_Mastery/issues/57). Check comments/PRs and claim a free issue. The V1 base is `integration/mastery-v1-20261127` (#50); use the current SHA and the base specified by each issue. Do not use main as the V1 implementation baseline.

| Priority | Issue | Type / deliverable | Queue advice |
|---|---|---|---|
| P0 | [#61](https://github.com/Sven-Lutz/Exam_Mastery/issues/61) | Numerical solution verification | Check if already claimed; independent reproduction first. |
| P1 | [#62](https://github.com/Sven-Lutz/Exam_Mastery/issues/62) | Learning-science full-text audit | READY at creation; research only, separate report. |
| P1 | [#63](https://github.com/Sven-Lutz/Exam_Mastery/issues/63) | Tutor workflow and adoption audit | READY at creation; research only, separate report. |
| P1 | [#64](https://github.com/Sven-Lutz/Exam_Mastery/issues/64) | Explorable learning sequence benchmark + storyboard | READY at creation; separate report, no shared fixture edits. |
| delegated | [#54](https://github.com/Sven-Lutz/Exam_Mastery/issues/54) | Attention academic/visual review | Check existing review/PR before claiming. |
| delegated | [#53](https://github.com/Sven-Lutz/Exam_Mastery/issues/53) | Security and data integrity | Check existing review/PR before claiming. |
| delegated | [#55](https://github.com/Sven-Lutz/Exam_Mastery/issues/55) | Anki feedback / analytics | Existing work may overlap; check PR #56 and current integration. |

The active product stream (#58 and #50) remains separate. PR #59 is Obsidian export work; do not start another implementation of it. Research workstreams #21–#31 have existing reports/PRs, so pick a specific unverified gap rather than rerun the entire programme. Historic NLP issues #4–#10 are quality evidence, not a claim that they are free tasks. #1 migration, #34 product identity, #49, #51, #57, #58 are context/umbrella tasks: do not claim the whole epic. No automatic closure or reassignment.

## Status and prioritization

Use issue-title prefixes [BACKLOG] or [READY] for newly scoped work, existing labels where available, and issue comments/assignees and linked PRs for actual progress. [help wanted](https://github.com/Sven-Lutz/Exam_Mastery/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22) is the live discovery view. A READY title is not a lock: check claims. P0 correctness/security/release blockers precede P1 delivery/research gaps, then P2 improvements and P3 future ideas. Reviews and independent evidence checks can proceed alongside product code with non-overlapping files. Do not promote work to accepted without maintainer review.

## Universal entry prompt

> You are a Mastery contributor. Read README.md, AGENTS.md, CONTRIBUTING.md and the linked vision and queue. Read live issues, comments, active PRs and the specified base. Claim a free highest-value scoped issue, work on an isolated branch or fork, verify against its acceptance criteria, document actual evidence and limits, and submit a draft PR. Repeat for another independent task while useful and within your authorized quota. Never merge, disclose private inputs, invent research or test results, or spend unauthorized credits. If tools or quota are unavailable, leave a safe checkpoint or report for a human.

If onboarding files are not yet on the V1 base, use the current default-branch documentation (or the proposed contributor-readiness branch before its merge) as context. Do not merge that branch into your task just to get instructions.
