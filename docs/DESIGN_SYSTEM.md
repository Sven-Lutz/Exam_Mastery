# Editorial design system (B32/B33)

One set of semantic tokens drives the typesetter (`typeset.py`, PDF + HTML), the figure kit (`figure_kit.py`), the
MDP Studio (`labs/mdp_studio.py`) and the Anki templates (`anki_v2.py`). Source of truth: `exam_mastery/design_tokens.py`.
`tests/test_b32_quality_reset.py::TokenDrift` fails if a renderer drifts from the token values.

## Semantic colour roles (never decoration)

| Role | Token | Used for | Non-colour cue |
|---|---|---|---|
| structure | navy `#1B2A41` | headings, rules, navigation, axes, part headers | weight, size |
| formal | petrol `#0F6E73` | definition, theorem, model | label "DEFINITION"/"SATZ", left rule |
| example | blue `#2F5D8A` | worked example, algorithm, computed numbers | top rule, numbered steps |
| intuition | gold `#8C6416` | intuition, research window | label + icon, framed box |
| warning | coral `#C8483A` | misconception, counterexample, pitfall | ✗/✓ columns, label |
| check | green `#2E7D4F` | takeaway, correct answer | ✓ label |
| practice | violet `#5B4B9A` | active recall, transfer, exercises | dashed border, "?" label |

All roles reach ≥ 4.5:1 contrast on white and ≥ 4.0:1 on their own tint (tested). Gold was darkened from
`#A8781E` (3.9:1) after the test exposed white-on-gold research headers below WCAG AA.
Heatmaps use a symmetric coral–white–petrol scale and **always print the value in the cell**.

## Typography

Serif body (Source Serif 4, 10.6 pt, line height 1.5, measure ≈ 34 em), sans for structure (Source Sans 3),
mono for algorithm traces. Formula minimum 9.5 pt; MathJax SVG for both HTML and PDF.

## Components (book model block types)

`definition`, `theorem`, `proof` (numbered steps with justification column), `example` (given → steps → result),
`intuition`, `research` (question / finding / link to the derivation / limits / provenance status), `misconception`
(wrong vs. right columns), `takeaway`, `recall`, `compare` (two-column), `algorithm`, `figure`, `figtext`
(image–text composition), `box` (note/limit/pitfall), `lab`, `summary`. Every block carries provenance
(`course`, `interpretation`, `didactic`, `supplement`) which the margin column shows.

## Macro layout rules

- Main column + 40 mm margin column (sources, provenance). Stand-alone figures span **both** columns and scale to the
  measure (max 118 mm high); figures inside `figtext` stay in a half column unless their aspect ratio exceeds 1.45,
  then the unit is stacked (text, full-width figure), so labels never shrink below legibility.
- Chapter opener spans both columns; roadmap tiles never break across pages.
- Workbook: task items never split; **solutions may split**, but the rubric block (heading + table) is kept together,
  so no rubric is stranded on its own page. Solutions part comes last.

## Layout lint (runs on every PDF)

`typeset.LAYOUT_LINT_JS` + `chapter_publish._layout_lint`, reported per document in `publish_report.json`:
- inline formulas wider than their text block are reflowed into scaled display formulas (listed);
- overflow beyond the page width and broken images → `FAIL`;
- near-empty pages (cover excluded) → `WARN` with page numbers.
