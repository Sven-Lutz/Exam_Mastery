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
