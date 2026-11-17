# Quality mechanisms (B33) — engine-wide, subject-independent

| Mechanism | Module | What it decides | Evidence it writes |
|---|---|---|---|
| Issue lifecycle | `issue_lifecycle.py` | Gives every open AST issue one of OPEN / RESOLVED / DUPLICATE / REASSIGNED / NOT_APPLICABLE / ACCEPTED_RISK. RESOLVED needs a machine recheck that runs again on every publish; open blockers set the gate to BLOCKED. | `publish/issue_lifecycle.json`, `publish_report.issue_lifecycle` |
| Exam-item mapping audit | `exam_mapping.py` | Classifies items flagged as "outside chapter sources" into: heading/announcement, question of another chapter's source, official example-exam task that is a candidate for this chapter, or practice on another topic. Matching is by page and content, not by file membership. | `issue_lifecycle.json → exam_mapping_audit` |
| Page audit | `chapter_publish._page_kind/_layout_lint` | Builds a page profile: F = figure, B = coloured component, t = text only. Three or more text-only pages in a row inside the core are reported as a monotone stretch. Formula glyphs are black and never count as visuals. | `documents.*.layout_lint.page_audit` |
| Layout lint | `typeset.LAYOUT_LINT_JS` | Reflows inline formulas that are too wide. Reports overflow, broken images and sparse pages. | `layout_lint` |
| Regression guard | `chapter_publish.regression_guard` | Works as a ratchet over defect metrics (numeric/didactic/semantic FAIL, Anki render failures, open blockers, layout FAIL, monotone stretches, items without solution). A metric that gets worse means FAIL, and the baseline is not lowered. A shrinkage of more than 20 % in figures/items/cards means REVIEW. | `editions/<ch>.quality_baseline.json`, `publish_report.regression_guard` |
| Fail-closed edition patch | `edition.py` op `patch` | Corrects exact text in a block, item or figure. The old text must occur exactly once; a reason and the review-finding id are required. | `edition_report.operations` |
| Evidence badge | `typeset._item_html` | Prints OFFICIAL_EXAM_EVIDENCE tasks with their source in the workbook. | PDF/HTML |
| Studio comparison | `labs/mdp_studio.py` mode `compare` | Runs VI and PI on the same model and plots each error to V* on its own axis. Short series are drawn as points, and an exact 0 is labelled. | page |

Calibration note: the page-audit thresholds and the mapping vocabulary rule were calibrated on one course (RL). Validate them on another subject before treating them as general.

## B34 additions (V4 rebuild)

| Mechanism | Module | What it decides | Evidence |
|---|---|---|---|
| Printed slide numbers | `slide_numbers.py` | Maps each PDF page of a slide deck to the number printed on the slide. Only bytes that still match the inventory hash are used, decks with ambiguous file names get no map, and unknown pages stay "PDF-S. n". | `publish_report.slide_numbers` |
| Source levels A/B/C | `typeset.Doc.side` | Puts a level badge and a reference inside every block (A course, B verified supplement, C own derivation "zu Folie n"). The levels are explained on the opener. | PDF/HTML |
| Raw-math gate | `chapter_publish._layout_lint`, `RAW_MATH` | Fails a document if its rendered PDF text contains caret/underscore notation or untypeset TeX. | `layout_lint.raw_math` |
| Type-size audit | same | Reports which text sizes are actually used (share ≥ 1 %). | `layout_lint.type_sizes_main` |
| Several mock exams | `edition` op `exam` with `label`, `typeset.exams` | Builds independent exams with their own item numbers (A1, B1), integrity checks per exam, and a stand-alone booklet each. | PDFs |
| Studio work measure | `labs/mdp_studio.py` compare | Asks for a prediction before showing results, then plots the error against arithmetic operations, so VI and PI are compared on a shared unit. | E2E |
| Anki cognitive chips | `anki_v2.COGNITIVE` | Shows one of seven cognitive demands on every card, with a structured back side and light/dark themes. | deck |

Reliability note: full suites must run from a frozen copy of the code (e.g. `git worktree`). `runtime.py` correctly reports FAIL when engine files change during a run, which was the "flaky" V3 test.
