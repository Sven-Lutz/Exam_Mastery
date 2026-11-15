# Issue #4: corrections to the NLP reference unit (version 2)

Status: **version 1 = HUMAN_REJECTED** (textbook 1/4, maths 0/4, visuals 0/4, learning process 1/4, exam readiness 1/4). **Version 2 = HUMAN_REVIEW_PENDING.** No self-rating. CI success is not acceptance.
Run locally: `python -m exam_mastery.reference_unit build units/nlp_sequence_labeling --out <dir>`, then open `<dir>/index.html` (offline, `file://`).
Screenshots: `review_2026-11-14/before/` (version 1 as rejected) and `review_2026-11-14/after/` (version 2).

## A. Why version 1 failed (diagnosis on the rendered product)

The rendering was **not** the cause: MathJax typesets correctly in the browser and the PDF (`before/rnn_satz1.png`). The causes were in the authoring:

| Observation in v1 (`before/…`) | Cause |
|---|---|
| The chapter opens with abstract definitions (sequence labelling as a map, $\mathcal V^T\to\mathcal L^T$) before any example (`orientierung.png`) | No concrete case first. The learner gets nothing to explain. |
| "Washington" appears as a claim ("muss … identisch vorhersagen") but is never computed (`rnn_satz1.png`) | The central consequence is asserted, not shown. |
| Proofs are run-on paragraphs (`f1_proofs.png`) | No line-by-line justification and no symbol table. |
| The visual is a dependency diagram with a slider beside the text, unconnected to numbers or equations | Illustration, not explanation. No prediction and no counterexample. |
| F1 map clamps P and R to ≥ 0.01 | The boundary cases the text emphasises cannot be shown. |

## B. Defects from Issue #4: before → after

| # | Before (v1) | After (v2) | Evidence |
|---|---|---|---|
| 1 Maths/visual P0 | Satz 1 as a paragraph proof. Washington only claimed. | **Washington experiment**: a concrete 2-dimensional RNN computed by hand in both sentences (embeddings → $h^{\rightarrow}_1=(0.7616; 0)$ identical → counterexample "for every weight choice" → backward pass $h^{\leftarrow}_1=(0.7616; \pm0.5436)$ → score ±0.5436 → PER/LOC). Two blocking predictions. Hover links equation terms to diagram nodes. Then Satz 1 as an aligned induction with a justification per line. | `after/birnn_predict.png`, `birnn_counterexample.png`, `birnn_bi.png`, `rnn_satz1.png`; `test_prediction_blocks_until_answered`, `test_toy_experiment…` |
| 1 Maths | $F_1=2PR/(P+R)$ stated, count form proved | $F_1$ **derived** as "hits per average effort": $1/P$ = outputs per hit, $1/R$ = gold per hit, mean, reciprocal → count form. Every step is justified. | `after/f1_proofs.png`; SymPy identity in `MATH_AUDIT.md` #5 |
| 2 F1 boundaries P1 | `Math.max(.01, p)`: P = 0 and R = 0 cannot be shown; undefined ratios are not distinguished | F1 scene works on **integer counts** including 0. P/R are shown as exact fractions or "nicht definiert". The point is drawn on the boundary (0,0) or omitted with a reason. The case (i)–(v) table also states that $2PR/(P+R)$ is undefined for **every** TP = 0. | `after/f1_case_iii.png`; `test_f1_scene_free_mode_reaches_zero_boundaries` (cases v, iii, ii), `test_js_metrics_match_python` (P/R/F/H definedness per case) |
| 3 Mastery P0 | `GEMEISTERT` from the latest delayed item(s), possibly one item; KC `prf` had no exam item | Two **parallel exam forms A/B**, each with 2 items for every one of the 5 KCs (incl. `prf`) and a transfer item for birnn, prf and prf-level. Levels: *Nicht geprüft → Lücke / Geprüft (sofort) → Wahrscheinlich sicher* (passed ≥ 24 h after the last activity, all KC items correct) *→ Behalten belegt* (two delayed passes on **different forms** ≥ 7 days apart). Labelled as evidence, not a guarantee. | `test_mastery_levels_require_delayed_new_items_and_retention` (6 state transitions), `test_unit_verifies_and_covers_every_kc_in_both_forms`, `after/progress.png` |
| 4 Series P1 | Every practice attempt counted as "assisted" | `supported(a)` = worked/faded stage, a hint used, a solution revealed or self-graded. Only an unsupported **first** attempt counts as "erster Versuch ohne Hilfe". Exam data is separate (`exams[]`, never in `attempts[]`). | `test_series_classification`, `test_exam_flow_alternates_forms_and_records_delay` |
| 5 B5 ambiguity P1 | "Which error?" with two equivalent options, `accept: [0, 1]` | The student's **lists** are given (TP/FP/FN). Exactly one option is correct ("[München]ORG fehlt in ihrer FP-Liste"); each wrong option has a diagnosis. The verifier now **rejects** `accept` and duplicate options. | `test_hints_after_attempt_diagnosis_and_unique_b5`, `test_rejects_ambiguous_or_wrong_items` |
| 6 Math validation P1 | 10 prose claims + answer values; reports suggested more | Verifier: 71 checks, incl. **every decimal in prose and solutions** against recomputation or a declared input. Proofs are audited separately with SymPy and stated assumptions; what is not machine-checkable is named. Claims corrected in v2: Satz 2 "tatsächlich von jedem $x_s$" (wrong in general, counterexample $W'=0$). | `MATH_AUDIT.md`; `verification.json` → `scope` |
| 7 Depth/sources P1 | Dense, abstract text; page references missing | Rewritten as a storyline (experiment → theorem → limits). Lecture pages given as PDF pages (3 page errors from v2 drafting corrected against the extracted slide text). SLP3 with printed page numbers (§4.9 p. 112–114, §4.9.1 p. 114–115, §9.5.4 p. 241, §14.4.2 p. 313–314, §18.5 p. 414–419) checked in the local PDF. Lecture versus extension is marked per block. | `text.html`, sources view |
| 8 Illustration vs explanation P1 | Slider widgets | 4 **scenes** with the storyboard *example → prediction → mechanism → counterexample → verification*. Captions and equations change per step; numbers are computed at runtime (no hand-typed values). The PDF shows the same scenes as numbered key frames. | `after/*.png`; PDF key frames in sections 1, 7, 9 and 10 |
| 9 Reliability P1 | Write failures silently caught | State schema v2 with validation and migration of v1. Corrupt state is backed up under its own key with a visible notice. Unavailable storage shows a warning. Invalid imports are rejected and leave the state unchanged. | `test_persistence_corrupt_state_and_invalid_import` (reload on `file://`, corrupt JSON, invalid import), `test_mobile_no_horizontal_scroll` |
| 10 Generalisation P1 | — | Unchanged and stated: the unit is **hand-authored** with course-specific scenes and `seqlab.py`. It is not evidence that the engine can produce such units. Scaling stays deferred until a human accepts this unit. | — |

## C. Rendering checks run on the final build

- Desktop 1280 px and mobile 390 px:
  - no horizontal page scroll in 6 views;
  - no overflowing display equation on mobile (0 of all);
  - no console errors.
- PDF (32 pages A4):
  - all text spans inside the margins;
  - justification columns of the aligned proofs fully visible after the fix (`satz4` page inspected);
  - key frames readable.
  - Two defects were found and fixed during this check: clipped justifications, and FP squares overflowing their box.

## D. Cost

- Engine provider calls: **0**.
- The work was done in one Claude Code session. Its token use is not exposed to the session, so it was **not measured**.
- No budget was used and no run was started.

## E. What still needs a human

- Expert review of mathematical correctness, visual communication and the quality of new tasks (Issue #4 C). Not replaced by this document.
- Learning effect: not measured. No claim is made.
