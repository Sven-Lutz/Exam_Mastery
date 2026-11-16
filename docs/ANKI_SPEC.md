# Anki authoring, QA and rendering (B32/B33)

## Card model

Every card (`em-book-v1` `cards[]`) carries: `key` (stable semantic key → GUID = hash(course, chapter, key), so edits
keep review history), `kind`, `front`, `answer` (short, checkable, shown first), optional `explanation`, `example`,
`pitfall`, `figure` (+ `figure_side`), `learning_objective`, `kc_ids`, `provenance`, `source`, `difficulty`, `why`.

Kinds: `concept`, `symbol`, `condition`, `fact`, `mechanism`, `compare`, `misconception`, `derivation` (one step of a
derivation, not a formula wall), `math`, `trace` (one algorithm step: a sweep, an improvement), `transfer` (new
numbers, worked answer), `visual` (figure on the front; the figure must not reveal the answer), `cloze` (sparingly).

## Gates

- Semantic card rules (`semantic_checks.card_quality`): C6 list cards need `list_reason`; C7 mechanism/compare/
  misconception cards need explanation, example or pitfall; C8 visual cards have the figure on the front; C9 the
  front must not contain the answer.
- Render gate (`anki_v2.render_lint`) on the final field HTML of **every** card: `|x|` / `\|x\|` never becomes a
  table, balanced math delimiters, no markdown residue, cloze markers only in cloze cards, non-empty answers.
- Package check (`verify_package`): import into a throw-away collection, counts, note types, media, idempotent
  re-import (stable GUIDs). Anki **Desktop** GUI import is a separate manual step (not automated).
- Visual sample: `preview_html` renders cards through Anki's own template engine (pylib), `screenshot` captures
  them in Chromium (light/dark); used for a risk-based gallery.
