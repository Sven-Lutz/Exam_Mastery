# B35 – Scientific & cross-domain quality mechanisms: implementation report

Branch `feat/rl-engine-pilot`, baseline `bed6619` (engine 0.23.0rc1), owner rating of V4: **≤ 2.5/5, not released** (Anki 3/5, MDP studio 2/5).
Status of everything below: **TECHNICAL work; ACADEMIC_REVIEW_PENDING; HUMAN_ACCEPTANCE_PENDING.** No self-assigned quality score.
Course-derived content (texts, cards, renderings) lives only in the private edition folder, not in this repository.

## 1. What changed in the engine (all with negative fixtures that fail on the old code)

| Mechanism | Module | What it checks / does | Known V4 defect it catches |
|---|---|---|---|
| Print-clipping repair | `typeset.py` (layout lint) | over-wide display formulas are re-set as aligned blocks broken at top-level relations, then +/−; scaling only as fallback (≥ 0.85); clipped scroll containers FAIL | P1: proof line cut off, textbook p. 49 |
| VI/PI comparison | `labs/mdp_studio.py` | instrumented operation counts (checked against an independent Python count), modelled cost as a separate upper bound, practical stopping rules, separate iterations / accuracy / wall time, declared cost model, data-derived verdict | P1: "fair" comparison mixing estimated and counted cost, oracle vs exact stopping |
| Answerability gate | `answerability.py` | 8 review dimensions on what the question side shows: missing/invisible figure, hidden context, named course examples without definition, no data for a computation, leaked answer, two targets, undefined symbols, convention-dependent counts; notation and example definitions are printed on the card; correctness stays NOT_VERIFIED unless an executable check exists | 7 → after review 8 unanswerable V4 cards the format rules had passed |
| Argument graph + proof audit | `argument_graph.py` | proofs as dependency graphs (rule, assumptions, definitions, dependencies, relation type); A1–A9: unjustified steps, forward references, hidden premises, exact/approximate mixing, numeric test used instead of argument, conclusion reached, counterexamples, undeclared notation; per-step support listed by tier (FORMAL_VERIFIED only from a recorded proof-assistant run, SYMBOLIC_CHECKED/PARTIAL, ANALYTIC_ARGUMENT, NUMERIC_TESTED, MODEL/HUMAN_REVIEWED, UNCHECKED) | compact V4 chains could not show which assumption a step uses |
| Claim evidence registry | `evidence.py` | claim-level access (official course / primary or secondary full text / abstract / metadata / audited author derivation / model inference), quote must occur in the read text, numbers and detail terms beyond the quote FAIL, DOI never supports content, per-claim-type requirements (legal: jurisdiction + version; clinical: date, grade, issuing body; empirical: design; historical: source kind + date; textual: edition + locator); legacy Crossref "VERIFIED" maps to METADATA_ONLY | DQN claim printed as "abstract" had only metadata on record |
| Subject profiles | `profiles.json`, `subject_profiles.py` | operations per objective from bilingual signals (declared operations win), packs activated per (pack, operation), requirements per pack, coverage report LINKED / UNLINKED / MISSING | V4: 33/44 competencies flattened to EXPLAIN, so no proof/calculation could be required |
| Lab task model | `labs/task_model.py`, `labs/mdp_sequences.py` | objective, problem, observable success criterion; answers and feedback computed from the current model; error diagnosis, hint ladder, guided → independent → transfer; steps offered only where truth and typical errors are separable | V4 tasks had fixed answers that became wrong after a model edit |
| Exam timing audit | `exam_quality.py`, `edition.py` | time always printed with calibration status; declared workload model flags distributed minutes, outliers, overload; exam modes (essay/case planning factor; OSCE = no writing model) | both V4 mock exams: "60 Minuten" distributed, workload model ~131/141 min |

## 2. Adversarial review (five separate model reviewers, read-only, narrow mandates)

These are **model reviews, not independent human expert reviews**.

| Reviewer | Critical | Major | Status |
|---|---|---|---|
| Mathematical correctness | 1 (counterexample for "bounded rewards" violated other assumptions; assumption not necessary) | 4 (hidden Markov-policy assumption, conditioning on null events, incomplete step premises) | fixed in the reference argument; all card numbers confirmed |
| Source evidence | 0 | AlphaZero access level overstated; Littman opinion stated as fact; 5 rule loopholes (compounds, quote vs whole abstract, locator numbers, years, numbers in formulas) | fixed; **semantic support (does the statement mean what the quote says) is not machine-checkable** and is declared as such |
| Anki answerability | 4 BLOCK the gate had passed (named examples without definition, figure without figure) | 6 FIX (two targets etc.) | gate extended (example registry, two-target rule, figure cues); cards rewritten |
| Lab task validity | 4 (wrong answer graded right when an error model is within tolerance; grid worlds hollow out sequences A/B; hint teaching the wrong bin) | criteria not evaluated by code, tie-breaking artefacts | fixed with separability selection, strict tipping points, affine hint, attempt counting |
| Cross-domain generality | – | packs recognised only 4/42 objectives outside German STEM; essay/OSCE/humanities false positives | bilingual signals, context-gated tokens, 3 new packs; see §3 |

## 3. Cross-domain evidence (what is and is not shown)

| Discipline | Material | Mechanisms run | Result |
|---|---|---|---|
| RL (development) | V4 products | all | calibration only |
| Analysis 1 | deck; own reference proof (convergent ⇒ bounded) | answerability, argument graph | gate: 0 blocking; graph audit exposed 2 over-strict rules (fixed) |
| Entrepreneurship | deck; subject source records | answerability, evidence | 4 blocking cards confirmed by hand; 16/22 source uses metadata-only |
| Patent law | book, deck, source records | profiles, answerability, evidence, exam audit | legal pack activated; 6 component gaps; legal sources lack stored quote, jurisdiction, validity date |
| NLP (holdout, consumed) | deck, never used in development | answerability + reader | reader failed on current Anki format; 5 false-positive blocks → fixed; holdout consumed |
| 9+ further disciplines (corpus) | 42 calibration objectives (reviewer), 24 holdout objectives (consumed) | subject profiles | calibration 4/42 → 40/42; holdout 24/24 lenient, 2/24 extra packs (1 real false positive) |

**Not tested with real course material:** medicine, chemistry, biology, physics, sports science, humanities, engineering. Support for them must not be claimed. Both holdouts are consumed (`fixtures/cross_domain/HOLDOUT_LOG.md`); the next generality claim needs a new, independently written holdout.

## 4. Known limits and open risks

- Answer correctness and source fidelity of cards are NOT_VERIFIED except where an executable check exists.
- The evidence registry checks lexical consistency only; meaning needs review.
- The argument audit checks structure and premises; validity of each IMPLICATION step is not machine-verified (no proof assistant run).
- The exam workload model is an unvalidated heuristic; no timed solves (student or independent) exist.
- Lab: effectiveness is not measured; success criteria are observable in the UI, not validated against learning outcomes.
- Signals are regex-based (DE/EN); other languages are not supported.
- `test_p0_resource_budget` interrupt test is timing-sensitive under parallel load (3/3 green in isolation).

## 5. RL V5 candidate (regular production path)

Edition `v5` (private) → `chapter_publish` into run `ch-20261118T000000Z-v5` with the engine installed from the committed tree.
Gates on the real build: textbook, workbook and both mock exams PASS (no raw TeX, no overflow, nothing clipped; the
former p. 49 formula is broken into aligned lines); Anki gate 0 blocking (117 PASS / 1 WARN), note identities unchanged;
MDP studio: no JS errors in Chromium and WebKit, sequences A–C start in all three lecture scenarios.
Two earlier V5 runs failed: the raw-math gate caught TeX without delimiters coming from the argument fixture, and visual
review caught a step-numbering inconsistency between the 7-step derivation and the 11-step matrix; both fixed at the source.
Final full test suite: 945 passed, 7 skipped, 0 failed.
