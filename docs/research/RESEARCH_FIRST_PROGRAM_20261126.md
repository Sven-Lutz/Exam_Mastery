# Exam Mastery — Research-First Programme (26 November 2026)

**Decision:** Pause new broad platform features and full Golden-Reference production until a research-and-architecture gate. Focused fixes to data integrity/security and existing test maintenance may continue. Existing Draft PR #19 and the local RL pilot remain untouched. **Research and design documents do not imply learning effectiveness or academic acceptance.**

## Why a new programme?

The existing `docs/RESEARCH_FOUNDATION.md` describes 54 bibliographically checked references, 17 principles, 52 claims, seven design specs and only partial full-text checking. The documented evidence matrix includes provisional “IMPLEMENTED” rules whose test evidence is often behavioral compliance, not actual learning gains. Neither the independent pedagogical review nor the proposed learning-effect experiment has been run. This is a useful first research iteration, **not systematic coverage of neuroscience, expertise, domain pedagogy, or high-intensity learning**.

Questions:
1. What is established, disputed, context-dependent, or untested about learning and teaching different *kinds of knowledge and skill*?
2. Which processes actually transfer across subjects, and which require domain-specific mechanisms and independent expert evaluation?
3. What should Exam Mastery observe, prescribe, generate, simulate, grade, defer or explicitly refuse to certify?
4. What is the simplest maintainable architecture justified by those answers?
5. How can a credible evaluator falsify the resulting design before extensive implementation?

## Research principles

- Conduct **systematic scoping followed by prioritized targeted systematic reviews**, not an impossible claim to “all findings in neuroscience”. Record queries, sources/databases, date, screening rules, inclusions, exclusions, missing full texts and coverage gaps. Bibliographic verification does not equal claim verification.
- Prioritize multiple independent syntheses, controlled studies and authentic-domain field evidence; include null and adverse results. Record population, education level, domain, task, intervention, comparator, duration, measured outcomes, effect and uncertainty, bias, moderator, and transfer limitations.
- Use review quality and study-bias assessment appropriately (e.g., PRISMA reporting, AMSTAR 2 for eligible systematic reviews, RoB 2 for applicable randomized studies); do not fabricate scores from abstracts. Treat adapted GRADE-style certainty as a reasoned internal label, not an externally validated guideline.
- Keep *neuroscientific mechanism*, *behavioral learning evidence*, *practical recommendation*, *technical implementation*, and *Exam Mastery efficacy* distinct.
- Learn from expert practice and naturalistic experience, but flag anecdote, selection effects, survivor bias and unmeasured outcomes. Study-maxing is an informal optimization umbrella, not a validated scientific technique.
- Study sustainable intensity, fatigue, sleep, recovery, mental health, physical exercise and opportunity costs without promising universal hour quotas or neurobiological “hacks”.
- Any AI tutor must be evaluated for dependency/offloading and unassisted transfer, not only satisfaction, speed, answer correctness or in-session performance.
- Examine current knowledge base first; reuse and reconcile instead of spawning an unrelated second knowledge base.
- Respect copyright, privacy, safety, licensed materials and special safeguards for medical, chemical and machinery-related hands-on learning.

## Core taxonomy — competencies rather than course-name branches

Each subject combines multiple competency operations. These are hypotheses for investigation, not a final ontology.

| Learning operation | Illustrative contexts | Plausible learning/assessment mechanisms to evaluate |
|---|---|---|
| Recall / recognition / discrimination | anatomy, statutes, chemical symbols, economics concepts | retrieval, contextual recall, spacing, contrasting confusables |
| Symbolic procedure / quantitative modelling | algebra, statistics, finance, physics | worked examples, dimensional checks, variations, independent calculations |
| Formal proof / argument construction | analysis, theoretical CS, philosophy | proof comprehension vs validation vs construction, counterexamples, argument maps |
| Rule-based contextual reasoning | law, tax, regulatory policy | case analysis, issue spotting, subsumption, counterfactual fact changes, dated authority |
| Diagnostic reasoning under uncertainty | medicine, debugging, troubleshooting | competing hypotheses, missing evidence, calibrated decisions, case variation, safe escalation |
| Empirical and experimental inference | chemistry, biology, materials, statistics | hypotheses, controls, measurement uncertainty, virtual labs, replication and interpretation |
| Computational construction | algorithms, software engineering, numerical methods | tracing, Parsons, implement/run/debug/test/benchmark, code review |
| Spatial / design / engineering synthesis | CAD, geometry, mechanical engineering, woodworking | sketch, model, constraints, assembly, verification, design review |
| Perceptual, embodied and psychomotor performance | surgery, cooking, baking, woodworking, laboratory work | demonstration, supervised physical practice, calibrated external feedback, safety |
| Open-ended critical/creative synthesis | philosophy, entrepreneurship, economics, research | argument critique, divergent alternatives, evidence appraisal, original design decisions |
| Self-regulation and expertise management | intensive study across subjects | planning, monitoring, reflection, environment, recovery, delayed independent tests |

**Design restriction:** No universal “one topic = one flashcard + one PDF + one simulation” policy. The four *product containers* remain, but components may legitimately be not applicable, with a justified fallback.

## Seven research workstreams (research only, not code implementation)

**R0 — Evidence Integrity & Research Methodology:** Audit every existing KB claim against full text where accessible; systematic search protocol; risk-of-bias and applicability register; contradictions and missing domains; evidence taxonomy.

**R1 — Cognitive Science, Neuroscience & Sustainable High-Intensity Study:** Retrieval, spacing, interleaving, self-explanation, feedback, CLT, productive failure, metacognition, sleep, stress, exercise, fatigue, deliberate practice and sustainable effort; distinguish neural correlates from instructional causality.

**R2 — Formal, Quantitative and Computational Mastery:** Mathematics proof comprehension/validation/construction, statistics and economics modelling, finance, programming, algorithms, debugging and software engineering; develop independently testable competence tasks and proof/counterexample checks.

**R3 — Legal, Interpretive and Clinical Reasoning:** Law (subsumption and dated legal sources), philosophy/argumentation, clinical reasoning/diagnostic calibration, management and decision cases. High-stakes clinical decisions require professional oversight; simulated case performance is not clinical competence.

**R4 — Embodied, Experimental, Design and Craft Learning:** Mechanics, CAD/3D, materials, chemistry/biology laboratories, cooking, baking and carpentry; distinguish simulated knowledge from measured physical skill and safety certification. Review transfer from simulated to actual tools.

**R5 — AI Tutoring, Adaptation, Learning Measurement & Technical Feasibility:** Human tutors/ITS/GenAI, cognitive offloading, BKT/DKT calibration, assistance vs independent mastery, privacy and retention, multimodal tool limits, actual APIs and offline constraints; recommend or reject components by evaluation evidence.

**R6 — Adversarial Synthesis, Domain Transfer & Architecture:** Begin substantive synthesis only after provisional R0–R5 outputs. Challenge cross-domain claims, compare at least three architectural alternatives, measure complexity/opportunity cost, specify testable boundaries and final research-to-code contract.

Agents may work in parallel on R0–R5; the architecture integrator reviews provisional results and R6 independently challenges them. Each substantive report needs a second independent critic not identical to the original author.

## Required outputs for every research workstream

A versioned report in `docs/research/workstreams/` with:
1. Explicit research questions, exact query strings and search timestamps, database/tool coverage and screening log.
2. Primary-source evidence table, accessible full-text quotation/section or honest access limitation, study design, risk of bias and external validity.
3. Competing models and at least three explicit disconfirming/null/negative observations if available; if not, document missing evidence without manufacturing it.
4. A **mechanism → learner action → system affordance → observable → independent outcome → failure mode** map.
5. One concrete worked learning case and one *hard* counterexample/transfer case using synthetic material.
6. Cross-domain transfer conditions and explicit NOT_APPLICABLE decisions.
7. Technology candidates with evidence status, dependencies, accessibility, safety and cost.
8. A prioritized gap list and a section titled “What we cannot claim”.

Do not invent numerical effect sizes, bibliographic details, consensus or independent validation.

## Architectural decision gate: research before major new features

R6 must compare at least:
- **A:** reusable generic teaching templates + expert-authored subject modules;
- **B:** declarative competence/learning-operation graph + evidence-conditioned policy engine + verified domain adapters;
- **C:** agent-generated per-topic experiences with constrained tool execution and independent auditors.

Assess each on learning validity, inspectability, coverage, safety, authoring cost, local/offline operation, testability, runtime/agent complexity, maintainability, extensibility and migration from PR #19. Hybrids are allowed, but each extra layer needs a concrete necessity.

Deliver:
- Competency/skill ontology v1 with knowledge modes, operations, prerequisites, interactions, verifiers and acceptable uncertainty.
- Evidence-to-policy decision matrix with abstentions, learner-context moderators and traceable rule versions.
- Canonical semantic learning-object contracts vs target-specific presentation details.
- A genuine cross-domain holdout evaluation protocol: **math proof, law reasoning, medicine/biology case, software debugging, CAD/motor craft**. Each includes unassisted transfer and suitable safety criteria.
- Transparent definition of what browser/PDF/Anki can establish and what requires real practice, independent assessors, instrumentation or longer-term learning studies.
- Architecture Decision Record, rejected alternatives and a prioritized *minimum buildable research-backed slice*.
- Independent critique and owner approval gate before major implementation; no automatic merge to main.

## Evidence seed pool — leads to verify, NOT completed reviews

- Koedinger, Corbett & Perfetti (2012), Knowledge–Learning–Instruction: https://doi.org/10.1111/j.1551-6709.2012.01245.x
- 2026 school-classroom meta-analysis, retrieval/spacing/interleaving: https://link.springer.com/article/10.1007/s10648-026-10225-5
- 2025 mathematics spacing/retrieval meta-analysis: https://eric.ed.gov/?id=EJ1478558
- Sleep and memory formation review (2025): https://doi.org/10.1152/physrev.00054.2024
- Sleep restriction and memory formation meta-analysis (2024): https://pubmed.ncbi.nlm.nih.gov/39427809/
- Medical clinical-reasoning systematic review: https://pmc.ncbi.nlm.nih.gov/articles/PMC12758103/
- Mathematics proof skills, 2025 empirical study: https://link.springer.com/article/10.1007/s10763-025-10621-3
- CS debugging interventions review: https://doi.org/10.1145/3690652
- Engineering design and spatial skills (2026): https://doi.org/10.1115/1.4070965
- Argument mapping in higher education (2025): https://doi.org/10.1111/hequ.70063
- AI university-scale RCT (Oct 2026 working paper): https://iza.org/publications/dp/18989/the-effects-of-course-integrated-ai-tutoring-on-student-performance-and-engagement-a-randomized-university-trial
- GenAI in STEM, bias-adjusted 2026 synthesis: https://doi.org/10.1007/s10462-026-11665-9
- Existing project-specific KB, research, rejection and architecture documents are mandatory inputs.

## Release and autonomy

This research programme may be conducted without user course materials, paid model/API calls, private learner records or code changes. Agents should create separate reviewable research branches/PRs, not modify the approved technical baseline or merge to main. Actual assignment/execution by Codex or Claude must be initiated through those agent products; GitHub issues are research briefs, not proof that a worker has started.

**Gate:** RESEARCH_SYNTHESIS_PENDING. Neither perfect neuroscience coverage nor optimal learning efficacy can be declared; aim for a traceable, competitively reviewed, falsifiable and extensible scientific foundation.
