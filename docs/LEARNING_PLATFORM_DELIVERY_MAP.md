# Exam Mastery — capability delivery map (20 November 2026)

**Status: executable roadmap, NOT evidence of implementation.**
This maps research and owner's decisions to actual engine capability, independent acceptance and first release gates. It supplements `docs/PRODUCT_CONTRACT.md` and `docs/TARGET_ARCHITECTURE.md`; it does not replace them or create an additional user-facing product.

## Non-negotiable product boundary

Exactly four user-facing learning products, produced from one semantic learning representation:
1. **Lehrbuch** — academic depth, intuition, notation, complete derivations, scientific evidence, explanatory figures.
2. **Arbeitsbuch** — worked examples, deliberate practice, transfer, full worked solutions and rubrics in one product.
3. **Anki** — answerable cards, stable note IDs, safe reimport, Anki/FSRS the only scheduling system.
4. **Interaktiv** — visual storytelling, experiments, source-grounded tutor, adaptive practice, code tracing/debugging/execution where appropriate.

Obsidian is an optional linked knowledge view, *not* a fifth product or independent scheduler. PDFs are exports from a common semantic model rather than the primary representation.

**Until explicit owner authorization:** only synthetic, redistributable cross-domain fixtures; no lecture files, proprietary content, real student data or paid model calls in the public repository. Early exam deadlines require incremental milestones, not bypassed academic release gates.

## Research-to-capability traceability

*Product references are inspirations for specific workflows, not evidence that the product itself causes better learning. Empirical effectiveness of Exam Mastery remains untested.*

| Ref / approach | Desired capability | Current repository basis | Next implementation gate | Order |
|---|---|---|---|---|
| Math Academy / mastery & prerequisites | Structured knowledge prerequisite graph, separate memory and competence evidence, targeted practice | `learning/experience.py`, legacy `learning/policy.py`, `learning/diagnose.py` | Stable cross-domain competency IDs; adaptive decisions explain observed evidence and uncertainty; no fabricated `MASTERED` | P0 |
| marginstudy / contextual active reading | In-place annotation, own questions, revisit misunderstandings | Semantic teaching IDs and offline HTML renderer | Text anchor remains stable through regenerated pages; notes stay local, can be exported/imported safely | P1 |
| YouLearn / source-grounded tutoring | Tutor attached to sources, explanations and attempts, stepwise hints | Source→claim links, legacy tutor brief, attempts/hints evidence | Source citations on answers, explicit limitations, no unsolicited solution; blind dialog tests | P0/P1 |
| StudyFetch / diverse mini-apps | Domain-specific explorable simulations, exercises and coding challenges | Trusted `interactive_reference.MODELS`, offline HTML | Every interaction includes validated model, prediction, manipulation, feedback and transfer; browser tests | P0 |
| Brilliant, Mathigon, 3Blue1Brown / visual intuition | Story-led mathematical derivation and explorable explanation | Stepwise proof model, basic scenes | Linked visual object ↔ formula ↔ control, meaningful states, keyframe fallback, expert UX review | P0 |
| RemNote / learning notes + cards | Source-aware notes and Anki navigation; targeted re-teach after errors | Anki v2, Obsidian note, semantic IDs | Reimport note identity; no duplicated scheduler; wrong-card follow-ups grounded in competency graph | P0/P1 |
| Anki / FSRS, retrieval practice | Correct, atomic, answerable cards with durable review history | `experience_anki.py`, `anki_v2.py` | Cross-client rendering, card answerability reviews, stable GUID/reimport; no self-written FSRS | P0 |
| Obsidian / linked knowledge work | Backlinked notes, stable provenance and optional exported navigation | `experience.obsidian_note` | Incremental updates avoid overwriting authored notes; roundtrip contract decided before sync | P1 |
| Exercism, JupyterLite, Pyodide / coding | Implement algorithms, test/debug code, reason about correctness/complexity | Parsons order and deterministic traces | Sandboxed executable tasks, tests + counterexamples; browser/runner isolation and resource limits | P1 |
| Utterseen / screen-context support | Optional context-aware explanations for editors and documents | Not implemented | Permissioned on-demand context with redaction, no automatic private-screen capture | P2 |
| Seeing Theory / statistical simulation | Parameterized sampling and distribution experiments | Generic interaction contract only | Deterministic numerical oracle and statistically valid interpretation | P1 |
| Research-informed reading | Correct provenance for textbook claims and external papers | `claims`, `sources`, schema validation | Independent citation verification, provenance labels, license checks, temporal limitations | P0 |
| Spaced retrieval, ICAP, worked examples | Actual cognitive tasks and evidence of help dependence, not feature labels | Legacy policy, new evidence ledger | Observed attempts and delayed unassisted transfer distinguished from assisted work | P0 |
| Adaptive authoring / generative mini-apps | AI proposes declarative lesson specs, not arbitrary code run in a lesson | Experience JSON contract, trusted model registry | Allowlisted components, schema validation, sandbox, expert approval | P1 |

## Scientific anchor points

- Dunlosky et al. (2013), *Improving Students' Learning With Effective Learning Techniques*, DOI: 10.1177/1529100612453266.
- Chi & Wylie (2014), *The ICAP Framework*, DOI: 10.1080/00461520.2014.965823.
- Bastani et al. (2025), *Generative AI without guardrails can harm learning*, DOI: 10.1073/pnas.2422633122.
- Kestin et al. (2025), *AI tutoring outperforms in-class active learning*, DOI: 10.1038/s41598-025-97652-6.

Interpret results within studied contexts. Consumer-product feature lists are **not** independent efficacy studies. Examine primary studies and relevant limitations before implementing a pedagogical claim. Evidence classification for existing mechanisms remains in `docs/learning_design_evidence_matrix.json`.

## Delivery sequence and release criteria

1. **Engine integrity**: validate all inputs before publishing; checkpoint/resume; fail closed on unmanaged/changed content; coherent releases. Never equate technical pass with academic approval.
2. **Learning evidence and didactics**: attempt before hint/solution; differentiate observation from grading, assistance from independence, immediate results from delayed retention; reuse `policy.py`, do not duplicate tutor logic.
3. **Premium content/rendering**: proof-level derivation, book-quality typography, original explanatory visuals, consistent accessible UI, genuine worked solutions, answerable Anki.
4. **Interactivity and coding**: registry of verified model/visual components, formative experiments; secure programming runner and algorithm tasks after threat model and sandbox tests.
5. **Cross-domain holdouts**: synthetic mathematics/CS/statistics + contrasting legal/financial cases; hold back original course materials until generic engine is approved.
6. **Later course production**: owner authorizes official sources; use verified official documents for *scope* and independent research for depth; avoid public redistribution, prioritize first exam dates.

All milestones require runnable artifact, exact commit, automated test results and separate academic/human findings. A successful CI workflow alone is not a successful learning product.

## Immediate technical debt and decisions

- PR #11 is the existing four-product baseline, unapproved.
- PR #12 adds fail-closed publisher preflight (successful CI prior to integration).
- PR #13 starts attempt-first practice, local version-bound evidence and CLI audit. Until CI and review pass, code is experimental.
- Current publisher group is **not filesystem-atomic**; a crash may leave a coherent subset. Treat this as an open blocking reliability limitation.
- No durable learning record import yet; explicit browser export is the current privacy-preserving first step.
- Real free-text mathematical/proof grading is absent; do **not** derive competence or mastery from raw typing or self-report.
- No comparison to unconstrained ChatGPT baseline has yet been performed. The evaluation protocol remains NOT_RUN.

**Change control:** When a feature is implemented, update this map with its precise test/PR evidence. Do not mark something DONE from documentation, generated text, green synthetic-only tests, or an agent's self-evaluation alone.

## Engineering evidence update — 26 November 2026

Integration branch from PR #18 adds explicit journal-based process-interruption
recovery, renderer/template/font dependency cache invalidation and a workbook
pagination correction. Synthetic math/CS/finance reference runs and actual Anki
backend reimport tests cover these changes. Durable learner-state import, exclusive
publisher locking, full-group atomic visibility, academic writing/visual quality and
human acceptance remain open. Details: `ENGINEERING_RECOVERY_20261126.md`.
