# Product contract (binding; condensed from the owner's master brief of 2026-11-14)

Measure of success: the learner understands, proves, applies, transfers and later reproduces **without help**. Generating files or passing tests is not success. Target: exam-ready mastery (aim 1,0), never promised.

## Decisions already made (do not re-ask)
- **Product-first**: improve the existing engine; usable learning material beats infrastructure, agents and documents.
- **Sources**: official course material sets scope and exam focus, not depth. Depth from standard textbooks, peer-reviewed papers, vetted sites (GeeksforGeeks = accessibility aid, never primary authority). Real bibliographic data only; no invented pages; no copying of protected text/figures. Per knowledge component (KC) an evidence graph: course location → claim → textbook → paper if needed → place in text/visual/task. Labels: OFFIZIELLER_KURSSTOFF, FACHLICHE_ERLÄUTERUNG, VERIFIZIERTE_VERTIEFUNG, FORSCHUNGSBEZUG, OFFENE_UNSICHERHEIT.
- **Writing**: textbook prose; notation before use; scope of every claim; definition/theorem/proof/example/interpretation separated; no filler ("im Wesentlichen" without conditions etc.).
- **Math**: one semantic path LaTeX → checks (SymPy, numeric counterexamples, units) → PDF/web/Anki. Every central derivation: assumptions → start → justified steps → result → interpretation → edge cases → independent check.
- **Visuals**: original, mathematically coupled, progressive disclosure in the spirit of 3Blue1Brown (no copied assets). Per visual: hard claim, mental model, moving variables, formula↔object link, interaction (play/step/reset), static PDF keyframes, misreadings prevented.
- **Learning science as behaviour**: retrieval with feedback after own attempt; worked example → faded steps → hint only → independent → novel transfer, steered by performance; spacing/Anki with stable IDs and preserved history; interleaving of confusable types only; tutor hints after own attempt, full solution only on explicit reveal, grounded in verified solutions; separate unassisted exam mode. **MASTERED only from delayed unassisted evidence.** Assisted, immediate-unassisted, delayed-unassisted and transfer data stored separately. Keep evidence status from `research/lernwissenschaft` (VERIFIZIERT/UNGEPRÜFT/PREPRINT).
- **Outputs per course**: textbook (HTML+PDF), workbook, complete worked solutions with rubric (never "see steps"), mock exams with new tasks, Anki, visuals/labs, offline learning app. The app's start page answers "what do I learn today and how do I begin" (continue / new / due reviews / weaknesses / exam training). PDFs are exports, not the primary UI.
- **Generic**: input is only a course root folder; no hard-coded course names; domain adapters (math, AI/ML/NLP/RL/statistics, CS, law with legal-status date, finance/entrepreneurship) composed from general capabilities and tested on ≥2 contrasting real courses.
- **Operations**: `START <root>`, `CONTINUE`, `UPDATE`, `STATUS`, `STUDY`. Weekly check Sunday evening Europe/Berlin via idempotent launchd job only once authorised. Unchanged course → 0 model calls; changed source → only affected KCs; Anki IDs and learner state stable; atomic publishing; resumable checkpoints.
- **Cost**: measure tokens (incl. cache), calls, retries, time, bytes per *accepted* learning unit. No retry storms, no reviewer chains. No paid calls without an authorised budget; at a limit write a checkpoint and stop.
- **Storage**: dry-run first, keep originals, research, human reviews, provenance, git, learner state, active runs and at least one rejected reference release; measure physically freed bytes.
- **Quality**: one 0–10 rubric (truth, sources, depth, didactics, design/a11y, visuals, tasks/solutions, tutoring/mastery, reliability/offline, efficiency) with K.O. criteria. Internal target ≥9 with evidence; any open K.O. blocks READY_FOR_HUMAN_REVIEW. Final rating is human only.

## Requires the owner
Publishing possibly protected data; ambiguous irreversible deletion; buying credits or exceeding budgets; new access permissions; changing the public project target; academic release.

## Conflict rule
Truth and data safety → independently learnable depth/transfer → learning science/visuals/UX → automation and cost.
