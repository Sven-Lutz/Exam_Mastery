# NLP reference unit v4: changes for Issue #7

**Status:** v4 `HUMAN_REVIEW_PENDING`; v1–v3 `HUMAN_REJECTED`. This is not a self-approval. PR #3 stays a draft.
**Open offline:** `~/Exam_Mastery_Output/reference_units/nlp_sequence_labeling/index.html`. The same folder holds `Lehrbuch.pdf`, `Arbeitsbuch.pdf`, `Musterloesungen.pdf`, `Probeklausur.pdf`, `Probeklausur_Loesungen.pdf`, the Anki deck `nlp-sequence-labeling.apkg` and the card preview `anki_preview/index.html`.
**Before/after images:** `docs/reference_unit/review_v4/{before,after}/`.

| Finding in #7 | v3 (before) | v4 (after) |
|---|---|---|
| 1 CI red (WebKit missing) | Only `chromium` was installed | `playwright install --with-deps chromium webkit`. The rendering test is unchanged. |
| 2 Workbook thin | 14 tasks: 1 worked, 2 faded, 5 independent | **41 tasks**: 5 worked, 3 faded, 14 independent, 4 proofs, 3 error analyses (including code reading), 9 transfer, plus recall and self-explanation. Every competency has 2–7 tasks. There are backward-fading series (W1 → W1F → B1; AT0 → AT1 → AT2; C0 → C1 → C2/C3). New answer type: BIO/BILOU label sequences, with a diagnosis that names the first deviating word. Every task has a full solution, a rubric and its competency. |
| 3 Literature not navigable | 0 links; research in one sentence | Every source marker links to the bibliography, which links on to the DOI or URL, in the app and in the PDF. **Five research windows** (method, finding, limits, implications), each based only on passages actually read: Ratinov & Roth pp. 148–150, Lample p. 260/263, Vaswani §3.2.1 with its "We suspect", Andor p. 2442, Manning 2006. Lafferty 2001 is marked as not read in full. |
| 4 Visuals static | No scene for spans, position reused the attention scene, end states only | New **tweened scene engine** with play/pause, step, reset, keyboard control, `prefers-reduced-motion` and a blocking prediction step. It drives four rebuilt storyboards, each with a guiding question: **span encoding** (new: IO merges spans, BIO separates them); **BiRNN** (information pulses and colour stripes showing where a state can get information from); **attention as geometry** (projections, softmax temperature, vectors added tip-to-tail, permutation counterexample); **CRF** (Viterbi δ table, backtrace, forward α with $Z=200{,}27$, probability bars for all 13 valid paths). A test checks that a real intermediate frame is drawn. The textbook (§7) also gains a worked example "shift as rotation". |
| 5 Anki design 0/4 | `<b>Warum</b>{{Why}}` ran together ("WarumNicht") | New templates (v2.0.0): a header line with course, chapter and competency; a type badge (concept, formula, cloze, mini case, find the error, research); the answer as a highlighted block; "Why", "Example" and "Common mistake" as separate labelled blocks; diagram; source footer. Colour by family (models, structure, metrics) in light and dark. Two new self-made diagrams (attention geometry, CRF path probabilities). **43 cards** (v3: 34). |
| 6 CRF card wrong | "Score … globally normalized" | Split into **unnormalized score** (`decoding/crf-score`, with the start convention $y_0$) and **probability** (`decoding/crf-prob`, $Z$ over valid paths). New cards: Forward vs Viterbi, mini case $p=0{,}4495$, and find-the-error on micro weights. All cards were checked against the textbook. |
| 7 Maths didactics | Identities without development | CRF section: score (9.1) vs probability (9.2), numbers in the text ($S=4{,}5$, $Z\approx200{,}2664$, $p\approx0{,}4495$). Worked examples with intermediate results: Viterbi table, forward algorithm, attention with value vectors, sinusoid shift. New proof tasks R1, AT3, PO3, P3. |
| 8 Design | Many small blocks, uneven rhythm | Research windows and worked examples as distinct box types, captions on the key frames ("Abb. 6.1 – Schritt k"), numbered equations, flowing print layout. Mobile layout (390 px) checked in Chromium and WebKit. |

**Errors found while working (all fixed):**
- **Anki update path.**
  - The new fields I planned first (CardKind/Family) would have left existing v3 notes with empty fields; Anki marked them "conflicting".
  - Instead, family and type now travel via tags, which the template uses as CSS classes (`{{Tags}}`), so the schema is unchanged.
  - Two cards had changed note type, which also produced conflicts.
  - `anki_identity.json` now freezes the note type of every published card; the verifier rejects type changes and silent removals.
- **Verifier catches:**
  - two rounding errors in AT0 (1.3395/1.3210, not 1.3396/1.3208);
  - a misplaced brace in AT4;
  - an AT2 diagnosis that was actually the correct answer.
- **Other:**
  - numbered equations overflowed on mobile (MathJax `min-width`);
  - the CRF scene showed edges leaving an invalid start cell as allowed;
  - the label "O" looked like "0" in the monospace font.

**Checks actually run:**
- Verifier: 178 recomputed values. Rules include givens, placeholders, ambiguity, practice/exam overlap, competency coverage, card rules, identity lock and balanced TeX braces.
- `tests/test_reference_unit.py`: **27 passed**. This includes the real upgrade **v3 deck → v4 deck** in a disposable Anki collection with Anki's default options: 0 conflicts, review history kept, CRF card updated.
- 180 card renderings: 15 example cards × front/back × light/dark/mobile × Chromium/WebKit. No overflow, no raw TeX.
- Visual check of every PDF page and of the scenes.

**Not checked:**
- the real Anki desktop and AnkiMobile apps;
- an expert review;
- learning effect.

**Cost:** 0 engine calls. Claude Code session tokens are not measurable from inside the session.

**Remaining limits:**
- The exam forms (A/B) and the cockpit were not substantially reworked; #7 did not assess them.
- The unit is still hand-authored and is no evidence that the engine generalizes.
