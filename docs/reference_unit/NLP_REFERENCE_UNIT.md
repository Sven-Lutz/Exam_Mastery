# NLP reference unit: BiRNN tagging and its evaluation

Status: **version 1 of this unit HUMAN_REJECTED on 2026-11-14 (Issue #4: 1/4, 0/4, 0/4, 1/4, 1/4)**. Version 2: HUMAN_REVIEW_PENDING, see `ISSUE4_CORRECTIONS.md`. The engine baseline stays HUMAN_REJECTED (1/5). The sections below describe version 1 and are kept as history.
Built 2026-11-14 from `units/nlp_sequence_labeling/` with `python -m exam_mastery.reference_unit build`.

## 1. Why the old engine could not deliver (root causes, with evidence)

| Defect in the rejected run (`course-0e03a5f311fb/ch-20261113T185317Z-22ffdf83`) | Root cause in the engine |
|---|---|
| No precision/recall/F1 and no BiRNN at all, although slides 20–22 and 78–80 teach them (0 occurrences in `kapitel.html`) | The planner created no competency for them. They were added only by a human scope decision (`scope_decisions.json`, 2026-11-13), and the follow-up run `…202333Z-e4b68e53` stopped at `AGENT_TURN_REQUIRED` and was never finished. |
| Visuals 0/4: no own figure, 64 source images moved to a separate PDF | The author contract (`prompts/chapter_author.txt`) allows only `SOURCE_ASSET_REUSED`, `REDRAW_FROM_SOURCE_SPEC` (tree/columns/flows) or `OPEN_NOT_GENERATED`. Labs are limited to four hard-coded models (cashflow, risk, mlp, mdp), so a sequence-labelling or metric visual could not be expressed. |
| Derivations 0/4, sources 1/4 | The contract binds every claim to slide elements ("never answer from memory"). External depth is allowed only from a fixed `allowed_external_refs` list. No textbook was retrieved for this chapter, so terse slides became terse text. |
| Tasks/solutions 1/4 | Assessment and solutions are separate model calls. They see neither the learner's misconceptions nor a reference computation, and no numeric answer is recomputed deterministically. |
| UI 1/4 | `Lernumgebung/index.html` lists products. Theory, figure, task, feedback and progress are not in one flow. |

**Located factual errors in the baseline (checked against the slides; whether either is the "critical error" of the human rating is unknown):**
1. §19.7: "Ein RNN- oder Self-Attention-Zustand hängt dagegen von der ganzen Eingabe ab". This is wrong for the (unidirectional) RNN, whose state depends only on x₁…xₜ (slides 60, 76, 78; SLP3 §14.4.2, Eq. 14.16). This is exactly the point that motivates the BiRNN, which the baseline omits.
2. §19.7: the baseline "corrects" the slide's "Label bias" for autoregressive models as a confusion with exposure bias. That correction is itself wrong: locally normalised step-wise models do suffer from label bias (Lafferty et al. 2001; Andor et al. 2016). Slide 84 is right.
3. Lecture slide 17 itself tags Boston/New York City as `B-COMP`/`I-COMP` in the BIO column; slide 18 corrects this to CITY. The baseline did not copy the slip (noted for completeness).

## 2. What the new unit contains (verified)

- **Textbook** (`text.html`, about 2,200 words for the three requested competencies):
  - Definitions with domains.
  - Satz 1 (left dependence, induction proof) and Satz 2 (BiRNN dependence, with an explicit derivative argument).
  - BiRNN limits: causality; conditionally independent outputs → CRF; label bias versus exposure bias, correctly attributed.
  - Satz 3 (count form, aligned proof) and Satz 4 (harmonic-mean bounds incl. F₁ ≤ 2·min(P,R)).
  - Zero-denominator table.
  - Phrase versus token level on the lecture's own example (numbers recomputed).
  - Micro versus macro with a worked example, Satz 5 (micro-F1 = accuracy under stated conditions), and the two macro-F1 definitions.
  - Misconceptions and an integrating summary.
  - Every block is tagged Kurs / Lehrbuch / Forschung / Vertiefung / Erläuterung.
- **Sources** (11), each checked on 2026-11-14:
  - SLP3 sections were read in the local PDF (§4.9, §4.9.1, §9.5.4, §14.4.2, §18.5).
  - DOIs and pages were checked via Crossref; the arXiv preprints via the arXiv API.
  - The Manning blog post and the scikit-learn 1.9.1 docs were fetched.
  - The Lafferty et al. 2001 page range could not be verified and is omitted.
  - Preprints and the blog post are marked as such.
- **Visuals** (original SVG, all interactive, with static keyframes in the PDF):
  1. Dependence cone of hₜ: forward/backward/bi, slider, step, play, reset, live formula.
  2. F1 landscape: iso-F1 curves versus iso-mean lines, draggable point, live bound 2·min(P,R).
  3. Counting machine: clickable BIO tags on the slide example, live phrase and token tables.
  4. Micro versus macro bars with a slider for the rare class.
- **Workbook**: B1 worked → B2 faded step → B3 hints → B4 independent → B5 error analysis → B6/B7 transfer (incl. a proof task). Every task has a full solution and a rubric. Wrong answers that match a known misconception get a targeted diagnosis.
- **Exam mode**: six new tasks with no hints or solutions until submission, a confidence rating per item, and calibration feedback. Wrong competencies put their cards back into review.
- **Learner model**: four separately stored series (assisted, immediate unassisted, delayed unassisted, transfer). `GEMEISTERT` only from an exam ≥ 24 h after the last practice of that competency, all correct.
- **Spacing/Anki**: Leitner intervals 0/1/3/7/16/35 days, shown openly. `anki_import.txt` with stable SHA-256 GUIDs (`#guid column:1`), so re-imports update cards instead of duplicating them.
- **PDF**: textbook + workbook + solutions + mock exam + references (24 pages A4), printed from the same renderer as the web app, so content and figures cannot diverge.

## 3. Verification actually run

- `reference_unit.verify`: 10 prose numbers, 23 answer values, the B2 step values and every diagnosis (must differ from the correct answer) are recomputed with exact fractions (`exam_mastery/seqlab.py`). It fails closed (a wrong stored value blocks the build). **Limit:** free-text solutions are not parsed. Five slips in them (B1 solution text, two diagnosis values, B2 and X2 rounding) were found by manual recomputation during writing, not by the verifier.
- `tests/test_reference_unit.py` (13 tests):
  - property tests for Satz 3, 4 and 5 on 2,000/300 random cases;
  - JS metrics equal to the Python reference on 150 random BIO pairs;
  - browser flows: hints locked until first attempt, diagnosis shown, solution hidden until correct; immediate exam ≠ mastery, delayed exam = mastery; exam data separate; visual reacts.
- Visual inspection of real screenshots (desktop 1200 px, mobile 390 px) and PDF pages. Found and fixed: MathJax SVGs scaled by a figure rule, mobile horizontal overflow (grid item width), clipped plot labels. Now `scrollWidth` = 390 on all 9 views.
- **Not done:** independent human subject review; learner effect measurement (no claim of learning gains).

## 4. Cost

| | Rejected baseline (NLP) | New reference unit |
|---|---|---|
| Engine provider calls | 19 (5 author, 5 assessment, 3 solutions, 3 semantic review, 2 revision, 1 risk) | 0 |
| Prompt / answer volume | 3.95 MB / 0.64 MB (≈ 1.0 M / 0.16 M tokens at 4 bytes/token, **estimate**; tokens were never metered) | written in one Claude Code session; session token use not visible to the tool, **not measured** |
| Human-accepted units | 0 | pending review |

### Minimal call plan for the next real production run (not authorised; budget 0)
One chapter, agent or API provider, strictly sequential:
1. `chapter_author`: one call. Input is only the slide elements of the requested competencies plus retrieved textbook excerpts (about 25–35 k input tokens instead of about 55 k per call today). Output is a unit in this repository's `unit.json` + `text.html` format (about 12–16 k tokens).
2. **Deterministic** `reference_unit.verify`: no call. Numeric mismatches go back as a precise list.
3. `risk_review`: one targeted call on the claims tagged FORSCHUNG/VERTIEFUNG and on the proofs (about 15 k in / 3 k out).
4. `revision`: at most one call, only on a K.O. finding from step 2 or 3.

Expected cost: **3–4 calls, about 70–90 k input + 20–25 k output tokens** per chapter, compared with 19 calls / about 1.2 M tokens (estimate) for the rejected baseline. Hard stop at 4 calls per chapter. A checkpoint is written in `NEXT_ACTION.json`.

Engine changes this plan needs (not yet implemented):
- an author contract that emits the unit format;
- retrieval of textbook excerpts per competency;
- a visual-spec vocabulary beyond the four lab models (the four visual components here are the first entries).
