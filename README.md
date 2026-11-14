# Exam Mastery

**Status: migration in progress — not approved as a learning product.**

Exam Mastery is a local-first system intended to transform course materials into independently usable, academically rigorous learning resources and an evidence-informed learning environment.

> **Important:** The existing local engine has **not yet been migrated** into this repository. Do not interpret the current repository contents as a runnable product or as an academic release. The previous human review rated the NLP material **1/5 overall** and rejected the release.

## Product goal

Support deep understanding, durable retention, independent problem-solving and preparation for top exam performance. This is a target, **not a guaranteed grade**.

The intended output includes:
- A precise textbook with definitions, assumptions, proofs/derivations, worked examples and verified external scholarly references.
- Workbook, complete solutions and realistic exam preparation with unassisted assessment.
- Correct mathematical typesetting and pedagogically useful original visualizations (including interactive, mathematical visual explanations where appropriate).
- A local-first learning environment for retrieval practice, spaced repetition, interleaving, gradual fading of scaffolding, feedback and competence tracking.
- Source provenance separating official lecture content, verified external extensions and uncertainty.
- Incremental, resource-efficient generation across course domains.

## Current release gate

`HUMAN_REJECTED` — the existing generated outputs are **not** approved. Passing automated checks or generating PDFs does not constitute approval.

## Repository boundary

This is a **public code repository**, not a storage destination for private or copyrighted study materials.

**Allowed (after inspection):** source code, tests, reusable templates, architectural decisions, synthetic fixtures, documentation, CI and small redistributable examples.

**Not allowed:** original lecture PDFs without redistribution rights, scanned books, personal notes or study data, credentials, provider logs containing secrets, large course-specific outputs, or unreviewed generated content.

Do not commit the current local project wholesale without a secret/license audit.

## Migration

See [migration and retention policy](docs/MIGRATION_AND_RETENTION.md). The existing Mac-based engine and its Git history must be inventoried and imported with provenance preserved before local duplicates are removed.

## Development

Work should happen through short-lived feature branches and reviewed pull requests. Maintain deterministic tests for correctness, integrity, rendering and offline behaviors. Human acceptance remains mandatory for learning-product release.

**Documentation is not evidence of implementation.** Update this README only when the corresponding code and end-to-end evidence exist.

## Engine

The real engine (v0.21.0-rc1) is imported here: `exam_mastery/`, `tests/`, `fixtures/`. Setup:

```bash
python3.12 -m venv .venv && .venv/bin/pip install -e '.[qa]' pytest
.venv/bin/python -m playwright install chromium
.venv/bin/python -m pytest -q
.venv/bin/exam-mastery <course-folder>
```

Details: `ENGINE_README.md`, import record `docs/migration/IMPORT_RECORD.md`. Status of previously generated learning products: **HUMAN_REJECTED**.
