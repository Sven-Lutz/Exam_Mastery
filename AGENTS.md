# Agent instructions: Exam Mastery

## External and autonomous contributions

Start with [README](README.md), [CONTRIBUTING](CONTRIBUTING.md), [Mastery vision and decision index](docs/MASTERY_VISION.md), and [contributor queue](docs/CONTRIBUTOR_QUEUE.md). For V1 work use the issue's specified integration base, not stale default-branch product state. The live issue, claims, PRs and current base determine your task; owner-local NEXT_ACTION/checkpoints are only for the owning run, never global assignments. Claim a free scoped issue, work in a separate branch/fork, submit a reviewable draft PR and select another non-overlapping useful task within authorized quota. No agent merges to main; no private inputs or paid calls without authorization. Existing research, acceptance contracts and technical constraints below remain binding where applicable. Resolve conflicts with the maintainer instead of inventing a new vision.


These are persistent project instructions for Claude Code and other coding agents. Read the repository implementation and actual course artifacts before claiming anything is working.

## Mission and priorities

The objective is not document generation for its own sake. Produce **independently usable, book-quality, academically precise learning resources** and a real learning environment that develops deep understanding, independent transfer and long-term retention while preparing for top exam performance. No grade guarantee. A passing test suite is not an academic release.

**Existing human acceptance: FAIL.** Previous NLP output was rejected, and no automation can promote that rejected version to an approved learning product.

Priorities: correctness and user learning > depth and representation > source provenance > interaction/UX > cost efficiency > automation breadth > quantity of output.

## Non-negotiable content standards

- Start from actual lecture sources, learning objectives and past-exam evidence; expand beyond slides using verified standard textbooks, authoritative papers and useful instructional websites (e.g. GeeksforGeeks for selected introductory CS explanations). Do not confuse an accessible tutorial with primary scientific authority.
- Explain *why* each idea matters, define all symbols and assumptions, derive mathematics rigorously, distinguish theorems from heuristics, include limitations, counterexamples, examples and edge cases.
- Write in final textbook prose. No vague LLM filler, no invented focus of a lecturer, no unresolved placeholders masquerading as content.
- Visual explanations should be **original**, mathematically linked and pedagogically valuable. The communicative standard may draw on 3Blue1Brown-style intuition and animation, not copy its assets or claim its endorsement. Favor meaningful vector graphics, plots, animated transitions and interactions where they increase comprehension; never add decoration as a substitute.
- Implement learning science as actual learner workflows, not labels: retrieval practice with feedback, spaced reviews, interleaving when appropriate, worked examples with fading, stepwise hints and delayed *unassisted* competence checks. Calibrate claims to evidence and limitations.
- Separate official source facts, verified external sources, interpretation and uncertainty. Record precise provenance. Respect copyright and licensing.
- Course-adaptive requirements for mathematics, CS/ML, economics/finance and law; never force the same diagram, proof or grading format onto all courses.
- Keep outputs readable in PDF, HTML, Anki and offline interactive contexts; verify mathematical and visual rendering.

## Engineering constraints

- **Use existing code and research**: inventory before redesign. Implement fixes, not only write plans and gates.
- Avoid costly agent committees, repeated scans and broad regeneration. Prefer a strong author pass, targeted independent high-risk verification and deterministic checks. Rebuild only affected units when possible. Track model calls, tokens and human-approved learning outcomes.
- Maintain one canonical implementation, clear module boundaries, reproducible builds and representative end-to-end tests. Do not claim tests ran if they did not.
- GitHub is public. Do not commit raw lecture content, textbooks, learning records, secrets, logs or generated mass artifacts. Follow `docs/MIGRATION_AND_RETENTION.md`.
- Work autonomously on routine decisions; do not ask users to approve each intermediate step. Stop for irreversible ambiguous deletion, unauthorized spending or human academic sign-off.
- Prioritize a **real, independently learnable reference chapter** with strong visuals and mathematics over additional generic engine infrastructure.
- Preserve previously rejected outputs as compact benchmark evidence, not as approved material.

## Required report when doing product work

Give: working artifact entrypoint, implemented changes, evidence and failing checks, measured cost, storage before/after when applicable, commit/PR, precise blockers and whether human acceptance remains pending. Never claim 100% success solely from tools or model reviewers.
