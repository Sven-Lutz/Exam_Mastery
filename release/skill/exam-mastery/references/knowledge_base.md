# Scientific Knowledge & Pedagogy Base (KB-1.1.0)

The engine ships a versioned, machine-readable knowledge base in `exam_mastery/knowledge/`. Use it instead of
re-deriving didactics for every course.

- `exam-mastery kb context <artifact> [--subject <s>]` prints the rules for one product
  (`textbook`, `workbook`, `solutions`, `mock_exam`, `anki`, `lab`, `tutor`, `learn_app`, `adaptive_track`) with evidence
  status, conditions, limits and subject adaptations (`mathematics`, `statistics`, `ml`, `finance`, `law`,
  `information_systems`, `business`). Read this before authoring or reviewing that product; do not paste the whole KB.
- `exam-mastery kb spec <id>` prints one specification: `worked_example_fading`, `error_taxonomy`, `tutor_hints`,
  `assessment_item`, `exam_blueprint`, `anki_card`, `visualization`.
- `exam-mastery kb validate` checks integrity; `exam-mastery kb summary` prints evidence counts and the fingerprint.

Rules for using it:
- Cite the status as it is: `EMPIRICAL_STRONG`, `EMPIRICAL_CONDITIONAL`, `THEORETICAL_MODEL`, `DESIGN_HYPOTHESIS`,
  `UNVALIDATED_FEATURE`, `REJECTED`. A specification is a design hypothesis even when its principles are well supported.
- Claims with basis `fulltext_checked` name the location in the full text; `abstract_checked` claims carry verified abstract snippets.
- Claims with basis `metadata_only` were not checked against the source's text; do not quote numbers from them.
- Never implement a `REJECTED` principle (e.g. learning-style matching).
- The KB covers learning science. It does not replace subject textbooks for course content.
- New findings: add the source to `sources.json`, run `scripts/verify_sources.py`, add or revise the claim with
  `abstract_evidence` snippets, raise the principle `version`, run `kb validate`. Never edit `verification.json` by hand.

## Subject literature and editions (v0.20)
- `exam_mastery/knowledge/subject/<subject>.json` is the verified subject-source register (DOI/ISBN or read primary text, access level,
  allowed use). Use only what `use` permits; never quote effect sizes from sources read at abstract or metadata level.
- To improve a produced chapter without regenerating it, write an edition (`em-edition-v1`) into
  `<course output>/editions/<chapter_id>.json` – ideally from a small build script that computes every number and records
  `numeric_checks`. Publishing applies it deterministically; `publish/edition_report.json` lists every operation.
  Supplements (`prov: supplement`) must cite register ids; self-designed examples (`prov: didactic`, `numeric: true`) must
  name passing checks; lecture content cannot be added; dropped items need a reason; replaced cards keep their key.
- Audit a published learning environment: `python -m exam_mastery.knowledge.audit <Lernumgebung>`.
