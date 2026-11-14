# Exam Mastery didactic rule set, version DR-1.0 (2026-11)

These rules turn learning research into checkable product decisions. Every rule names:
- its evidence (verified bibliographic record; strength as stated in the cited review);
- the product decision it drives;
- how the engine checks it (`lint` = deterministic check in `exam_mastery/didactic_rules.py`, `prompt` = authoring
  instruction only, `review` = needs a human or model review).

Strength labels:
- **robust**: replicated across many studies and rated high in reviews.
- **moderate**: reliable, with known boundary conditions.
- **context**: depends on domain, task or prior knowledge.

## Evidence base (bibliographic records checked in Nov 2026; full texts not all read)
- Roediger & Karpicke (2006), *Test-enhanced learning*. Psychological Science 17(3), 249–255.
  - Testing beats restudying on delayed tests (2 days, 1 week).
  - Restudying wins at 5 minutes, and learners overrate restudying.
- Dunlosky, Rawson, Marsh, Nathan & Willingham (2013), *Improving students' learning with effective learning techniques*.
  Psychological Science in the Public Interest 14(1), 4–58.
  - High utility: practice testing, distributed practice.
  - Moderate utility: elaborative interrogation, self-explanation, interleaving.
  - Low utility: rereading, highlighting, summarisation.
- Cepeda, Pashler, Vul, Wixted & Rohrer (2006), *Distributed practice in verbal recall tasks*. Psychological Bulletin 132(3), 354–380.
  - Spacing benefits verbal material in most studies.
  - For intellectual skills (e.g. maths computation), only about a third of studies showed a benefit (context).
- Sweller (1988), *Cognitive load during problem solving*. Cognitive Science 12(2), 257–285.
  - Means-ends problem solving consumes capacity needed for schema acquisition; this is the basis of the worked-example effect.
- Renkl & Atkinson (2003), *Structuring the transition from example study to problem solving*. Educational Psychologist 38(1), 15–22.
  - Fade worked-example steps gradually into independent problem solving.
- Kalyuga, Ayres, Chandler & Sweller (2003), *The expertise reversal effect*. Educational Psychologist 38(1), 23–31.
  - Guidance that helps novices can hinder learners with prior knowledge.
- Chi, Bassok, Lewis, Reimann & Glaser (1989), *Self-explanations*. Cognitive Science 13(2), 145–183.
  - Students who explain the steps of worked examples to themselves learn more.
- Rohrer & Taylor (2007), *The shuffling of mathematics problems improves learning*. Instructional Science 35, 481–498.
  - Mixed practice trains learners to recognise which method a problem needs.
- Hattie & Timperley (2007), *The power of feedback*. Review of Educational Research 77(1), 81–112.
  - Feedback works when it addresses the task, the process and the next step, not the person.
- Mayer: multimedia principles (coherence, signalling, spatial and temporal contiguity, segmenting), from secondary
  summaries of Mayer (2009) and Mayer (2017, J. Computer Assisted Learning).
  - Effect sizes differ between sources; boundary condition: stronger for learners with low prior knowledge.
- Biggs (1996), *Enhancing teaching through constructive alignment*. Higher Education 32, 347–364.
  - Intended outcomes, learning activities and assessment use the same verbs.
- Wozniak (1999), *Effective learning: Twenty rules of formulating knowledge* (SuperMemo; practitioner source, not peer-reviewed).
  - Minimum information principle.
  - Cloze for beginners.
  - Avoid sets and enumerations.

## Rules

| ID | Rule (product decision) | Evidence | Check |
|---|---|---|---|
| T1 | Every chapter opens with orientation (why it matters, where it sits in the course) and closes with an integrating summary that relates concepts to each other, not a list of headings. | Mayer signalling; Biggs | lint: `ORIENTATION_AND_SUMMARY` |
| T2 | Explain mechanisms: every core concept gets *what*, *why/under which conditions*, *consequence*. A definition alone does not teach. | Chi 1989; Dunlosky (elaborative interrogation, moderate) | review + lint `DEFINITION_ONLY_SECTION` |
| T3 | Choose the form by content: comparison table for parallel concepts, process for sequences, worked example for procedures, case for judgement, misconception box for known errors. No fixed Problem→Steps→Result scheme for everything. | Mayer (coherence, signalling) | lint: `FORM_MONOTONY` (no single block kind above 45 % of the blocks; schematic problem/steps/result in at most 35 % of them) |
| T4 | Quantitative procedures: one fully worked example, then a faded example with the decisive steps left open, then independent problems; vary surface features. | Sweller 1988; Renkl & Atkinson 2003 | lint: `WORKED_EXAMPLE_FADING` for chapters with CALCULATE competencies |
| T5 | Do not repeat what learners with prior knowledge already know in every block; put definitions once and refer back. | Kalyuga et al. 2003 | lint: `REDUNDANT_BLOCKS` (near-duplicate text) |
| T6 | Learner text speaks about the subject, never about the production process: no "the permitted text", "the lecture states", "laut Folie", "model", "engine". Provenance goes into the source line, not into the prose. | Mayer coherence | lint: `META_LANGUAGE` (blocking) |
| T7 | One language per product (course language decides). Technical terms of the source language appear once, at first use, in parentheses. | coherence | lint: `MIXED_LANGUAGE` |
| T8 | Figures only with didactic function, labelled, next to the text that uses them; data figures only from documented data. | Mayer contiguity, coherence | lint: `FIGURE_HAS_SOURCE`, `FIGURE_REFERENCED` |
| A1 | Every intended outcome is practised and assessed with the same operation verb (explain → explain, calculate → calculate). | Biggs 1996 | lint: `ALIGNMENT` (each producible competency has ≥1 item with its operation) |
| A2 | Workbook progression: recall → guided application → independent application → transfer → exam-type, interleaving earlier topics in the later sets. | Rohrer & Taylor 2007 (context: maths); Dunlosky (interleaving moderate) | lint: `PROGRESSION` |
| A3 | Every item is self-contained: all values, units and assumptions stated; one unambiguous task per sub-question. | assessment validity | lint: `ITEM_SELF_CONTAINED` (no reference to "the slide"/"the figure" without data) |
| A4 | Solutions show the reasoning, units, rounding rule, a rubric whose points sum to the item points, and at least one typical error with its correction. | Hattie & Timperley 2007 | lint: `SOLUTION_COMPLETE`, `RUBRIC_SUM` |
| A5 | A mock exam contains only items with complete solutions and points, no evidence-gap items, covers the chapter's main operations, is labelled as self-designed, and states no invented official duration or grading scheme. | Biggs; integrity | lint: `EXAM_INTEGRITY` (blocking) |
| C1 | A card asks for one retrievable piece of knowledge (minimum information); the front is a precise question, not an essay assignment. | Wozniak 1999; Roediger & Karpicke 2006 | lint: `CARD_FRONT` (≤ 30 words, one question mark, no "Erklären Sie … Gehen Sie insbesondere") |
| C2 | Back: direct answer first (≤ 35 words), then optional explanation, example, pitfall, source. | Hattie & Timperley; Wozniak | lint: `CARD_BACK` |
| C3 | Enumerations become several cards or one cloze with ≤ 3 gaps; no gaps in unstructured prose. | Wozniak (avoid sets, cloze) | lint: `CLOZE_SHAPE` |
| C4 | Cards for knowledge that must be available without lookup: definitions, distinctions, conditions, formula meaning, mechanisms, key numbers that carry meaning. Procedures, cases and long derivations go to the workbook. | Dunlosky; Cepeda (spacing works best for verbal/declarative material) | prompt |
| C5 | Card identity = course-independent semantic key (chapter slug + concept key), never a generated item number; text edits keep the identity. | update integrity | lint: `CARD_IDENTITY` |
| Q1 | Quality claims come from checks that actually ran; model or agent review is labelled as such and never as independent validation. | integrity | dossier |

## Limits of the evidence (stated, not hidden)
- Most testing and spacing studies use verbal or declarative material. Benefits for complex problem solving are smaller
  and less consistent (Cepeda et al. 2006).
- Interleaving evidence is strongest in mathematics.
- The expertise-reversal effect means no single level of guidance is right for every learner. The products therefore
  offer both full worked examples and faded versions.
- Multimedia effect sizes vary between reviews, so no number is used as a target.

## DR-1.1 – Semantische Konsistenz (seit v0.13)

Automatisch geprüft (`semantic_checks.py`). FAIL blockiert, REVIEW verlangt eine gezielte Prüfung und gilt nie als PASS.

| Regel | Fehlerklasse | Entscheidung |
|---|---|---|
| S1 | Zählaussage im Text passt nicht zur Tabelle | FAIL; ohne prüfbare Tabelle REVIEW |
| S2 | Statistischer Schluss ohne Stichprobe, Test oder Intervall | FAIL, außer ausdrücklich eingeschränkt |
| S3 | Ursache einer Quellen-Inkonsistenz oder eines Musters behauptet | FAIL neben dokumentierter Inkonsistenz, sonst REVIEW |
| S4 | Begriff in Tabelle oder Text für ein anderes Konzept benutzt | FAIL |
| S5 | Norm als erfüllt behandelt ohne Tatsachen oder Annahmen; Verbot ohne Ausnahme | FAIL bzw. REVIEW |
| S6 | Zahl auf einer Karte, die das Lehrbuch nicht nennt | REVIEW |
| C6 | Karte verlangt ≥ 4 Elemente ohne Begründung (`list_reason`) | FAIL |
| C7 | Zusammenhangs-, Vergleichs- oder Denkfehler-Karte ohne Erklärung | FAIL |
| C8 | „Abbildung“-Karte ohne Abbildung auf der Vorderseite | FAIL |
| C9 | Vorderseite enthält die Antwort | FAIL |

Grenzen: Die Regeln erkennen Muster. Sie prüfen nicht, ob eine Aussage fachlich wahr ist, und ersetzen keine Begutachtung.
