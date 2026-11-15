# NLP reference unit v3: review package (Issues #4, #5, #6)

**Status: HUMAN_REVIEW_PENDING.** v1 HUMAN_REJECTED; v2 not releasable. No self-rating. PR #3 stays a draft and is not to be merged.
v2 artefacts are kept unchanged for comparison: `~/Exam_Mastery_Output/reference_units/nlp_sequence_labeling_v2_snapshot/`.

## 1. Entry points (offline, `file://`)

Directory `~/Exam_Mastery_Output/reference_units/nlp_sequence_labeling/`:

| Product | File |
|---|---|
| Learning environment (study cockpit) | `index.html` |
| Textbook | `lehrbuch.html`, `Lehrbuch.pdf` (28 pp.) |
| Workbook | `arbeitsbuch.html`, `Arbeitsbuch.pdf` (9 pp.) |
| Worked solutions | `loesungen.html`, `Musterloesungen.pdf` (6 pp.) |
| Mock exam (forms A and B) | `klausur.html`, `Probeklausur.pdf` (10 pp.) |
| Mock exam solutions | `klausur_loesungen.html`, `Probeklausur_Loesungen.pdf` (7 pp.) |
| Anki deck | `nlp-sequence-labeling.apkg` (34 notes, 34 cards, 3 custom note types, 4 SVG diagrams) |
| Anki intermediate format | `anki_notes.json` (fields, templates, CSS), `anki_import.txt` (TSV) |
| Anki card preview | `anki_preview/index.html` (108 renderings) |

Rebuild:
```
python -m exam_mastery.reference_unit build units/nlp_sequence_labeling --out <dir>
python -m exam_mastery.reference_unit anki-preview units/nlp_sequence_labeling --out <dir>
```

## 2. Corrections: before → after

| Defect | v2 (before) | v3 (after) | Evidence |
|---|---|---|---|
| **B1 P0**: problem and solution do not match | Prompt asks d=100, d_h=128, K=4; answer field "Ihr Zug – d=50, d_h=64, drei Typen"; `solution` answers 15 623 (the follow-up) | **W1** (worked, d=100/128/K=4 → 60 937, full solution without a placeholder) and **B1** (exercise, d=50/64/K=3 → 15 623) are separate IDs, each with its own `givens`. The verifier rejects a check that does not match the givens, and it rejects "siehe Schritte". | `test_rejects_v2_b1_problem_solution_mismatch` rebuilds the v2 case and fails it |
| **B6 P1**: micro weight | "Micro gewichtet MISC mit 7 von 162 Gold-Entitäten" | $D=(190, 130, 10)$; $w_{\text{MISC}}=10/330$; a new sub-question (c) asks for the weight, with a diagnosis for 7/162. Textbook §12 derives $F_1^{\text{micro}}=\sum_k D_k/\sum_l D_l\cdot F_{1,k}$ and separates support-weighted macro. Card `micro-macro/gewicht`. | `test_micro_weight_is_d_k_not_support` (200 random cases, exact); SymPy identity in `MATH_AUDIT.md` |
| **Anki P0** | 15 Basic Q/A lines in a TSV (`#notetype:Basic`), no `.apkg`, no explanation or source fields | `.apkg` built with the Anki library. Three note types: Concept, Math & Diagram, Cloze. 13 fields (StableID … Version). Designed CSS with dark/mobile variants, no JS or network. Back: canonical answer, *why*, example, common mistake, diagram, source. Over-broad cards rewritten with conditions, e.g. `birnn/latenz` "im Standardaufbau", `birnn/softmax-unabhaengig` "wenn … einzeln per Softmax". | `before/v2_anki_import.txt` vs. `after/anki_*.png` |
| **Anki updates** | – | Stable GUID, notetype, field and template IDs. Disposable collection: import → 5 reviews → reimport with changed text and CSS gives **34 updated, 0 conflicting, 0 duplicates**; reps, due, ivl and type unchanged; card IDs identical; CSS updated. Found while building it: random field IDs made Anki mark every note "conflicting" on update; now fixed. | `AnkiPackage::test_reimport_keeps_history_and_updates_content_and_style` |
| **Layout P1** | One 32-page PDF mixing textbook, tasks and solutions; forced page break before every section | Five separate products; flowing layout with headings kept with their text; lined answer space only in workbook and exam | `before/v2_pdf_all_pages.png` vs. `after/*_pages.png` |
| **Formula rendering (#5)** | The giant glyphs reported by the owner could not be reproduced in v2 (Chromium **and** WebKit). They match the v1 bug `.viz svg{width:100%}`. | MathJax typesets only nodes attached to the document. The test checks the inline formula height in Chromium and WebKit at 1280 px and 390 px. | `test_formula_glyphs_sane_in_chromium_and_webkit`; `before/orientierung_webkit.png` |
| **Depth P1** | Two topics of the chapter | **All six lecture parts** (NER, span encodings, taggers/window, RNN/BiRNN, self-attention, position information, deep architectures, label dependencies) plus evaluation and an end-to-end **NER case study**. Seven theorems plus Satz A with proofs. Layers marked exam core / deep / research. | `CURRICULUM_MAP.md` |
| **Sources P1** | 11 references, partly unused | Each research claim is tied to a passage that was actually read. Examples: Ratinov & Roth 2009 pp. 148/150 (BILOU > BIO; greedy comparable to Viterbi); Andor et al. 2016 abstract p. 2442; Lample et al. 2016 p. 263; Vaswani et al. §3.2.1/fn. 1, §3.5; SLP3 pages checked in the local PDF. | `units/nlp_sequence_labeling/src/sources.json` |

Errors found by recomputation while writing v3, all fixed:
- My first case study claimed that Viterbi also repairs "Berlin ." It cannot: `B-LOC I-LOC` is valid.
- In the second case-study draft the repair did not change the score at all, because conlleval already reads `O I-ORG` as an ORG span. The case was rebuilt so that the repair changes the decoded spans (New/B-LOC York/I-ORG), and the insight is now in the text.
- AT1: 0.7518 → 0.7517.
- A generator wrote TeX in non-raw Python strings, so `\r`/`\t` became control characters. The verifier now rejects control characters.

## 3. Learning environment

Cockpit: today / continue / review / weaknesses / exam / competence level. Six step-by-step explanation scenes:
- Washington BiRNN
- self-attention, with a permutation counterexample
- Viterbi lattice
- F1 from counts, including all zero cases
- phrase vs. token counting
- micro vs. macro

Every scene follows: example → blocking prediction → mechanism → counterexample → verification. Equation terms link to diagram parts; the PDF shows numbered key frames.

Learning flow and learner model:
- worked example → faded step → hints only after the learner's own attempt → independent task → error analysis → transfer;
- exam forms A/B with 2 items per competency and transfer items;
- competence levels need delayed evidence on new items;
- assisted and unassisted data are kept separate;
- reduced motion is respected; keyboard navigation works;
- corrupt state is backed up; invalid imports are rejected.

## 4. Checks run

- `reference_unit.verify`: 128 values recomputed, including every decimal in text, solutions and cards. The structural rules cover:
  - givens ↔ reference computation;
  - no placeholders;
  - exactly one correct option;
  - no reuse of practice tasks in exams;
  - every competency has a section, task, scene, sources, ≥ 2 cards and ≥ 2 exam items per form;
  - card rules from `exam_mastery/knowledge/specs.json` (`anki_card`).
- `tests/test_reference_unit.py`: 25 passed. These include:
  - property tests for theorems 1–7;
  - JS ↔ Python metric parity;
  - learner-model state transitions;
  - persistence;
  - mobile layout;
  - glyphs in two engines;
  - the real Anki reimport test.
- The full regression suite was run once (result in the PR comment).
- Visual inspection of every PDF page (contact sheets), close-ups of the theorem pages, app screenshots (Chromium, WebKit mobile) and 108 card renderings. This found and fixed: forced page breaks, an attention scene with labels covered by arcs, a cloze card that revealed the pattern through its sibling gaps, a clipped diagram caption, and a wrong BIO diagram.
- **Not checked:**
  - the real Anki desktop and AnkiMobile apps (card HTML was produced by the Anki library and rendered in Chromium/WebKit; this is a simulation);
  - independent expert review;
  - learning effect.

## 5. Cost

- Engine provider calls: **0**.
- Claude Code session: the token count is not exposed to the session and was **not measured**. "0 engine calls" does not mean 0 tokens.

## 6. Remaining risks

- **Academic:**
  - the depth and wording of the newly written sections 1–3 and 6–9 have not been reviewed by an expert;
  - Lafferty et al. 2001 is cited from secondary sources (page range not checked);
  - Su et al. 2024 is cited only for the rotation property, which is proved here.
- **Technical:**
  - notetype IDs are set by SQL in the build collection. The import test confirms it works with Anki 26.09.3; other Anki versions are not tested.
- **Product:**
  - the unit is still hand-authored with unit-specific scenes; it is no evidence that the engine generalises.
