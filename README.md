# Mastery (Exam Mastery)

**University excellence first. Lifelong knowledge and skill mastery next.**

Mastery is a local-first, AI-assisted learning system that transforms lecture slides, literature, exercises and past exams (or a defined skill goal) into a personalized learning environment. We aim for German grade 1.0 exam readiness, deep understanding and independent transfer, not guaranteed grades or a claim of absolute correctness.

Four integrated learning products: a rigorous course companion/textbook, workbook and solutions/exam practice, high-quality Anki cards, and interactive visual explanations, simulations, coding and tutoring. Expert resources are the scholarly foundation; original learning resources add value where needed. Optional Obsidian integration connects long-term knowledge. Languages, technical and practical skills are long-term goals.

## Start here — humans and AI contributors

1. [Vision and decision index](docs/MASTERY_VISION.md)
2. [Contribution guidelines](CONTRIBUTING.md) and [agent instructions](AGENTS.md)
3. [Contributor queue and universal entry prompt](docs/CONTRIBUTOR_QUEUE.md)
4. [Live issues](https://github.com/Sven-Lutz/Exam_Mastery/issues) and [pull requests](https://github.com/Sven-Lutz/Exam_Mastery/pulls)

Pick a free scoped issue, claim it in a comment, work on a fork/branch from the specified base, verify and submit a draft PR. Claude, Codex, Gemini and human contributors use the same contracts. Never merge on the owner's behalf. Public visibility does not itself grant an open-source license; licensing terms remain to be decided.

## What exists today

The legacy engine (v0.21.0-rc1) is imported on main: `exam_mastery/`, `tests/`, `fixtures/`. See [ENGINE_README.md](ENGINE_README.md) and [migration record](docs/migration/IMPORT_RECORD.md).

**Active V1 integration**: [integration/mastery-v1-20261127](https://github.com/Sven-Lutz/Exam_Mastery/tree/integration/mastery-v1-20261127), [PR #50](https://github.com/Sven-Lutz/Exam_Mastery/pull/50). This is the designated current V1 work base unless an issue says otherwise, not a stable release. The current roadmap and complete course delivery contract are [#57](https://github.com/Sven-Lutz/Exam_Mastery/issues/57) and [#58](https://github.com/Sven-Lutz/Exam_Mastery/issues/58).

**Academic release status:** historic human-rejected outputs remain HUMAN_REJECTED. Technical tests, model reviews and a synthetic demo are not proof of learning effectiveness or academic acceptance. See the research [synthesis and ADR](https://github.com/Sven-Lutz/Exam_Mastery/blob/integration/mastery-v1-20261127/docs/research/workstreams/ARCHITECTURE_SYNTHESIS_ADR.md).

## Developer quickstart (documented procedure)

On a clean local checkout with Python 3.12:

```sh
git clone https://github.com/Sven-Lutz/Exam_Mastery.git
cd Exam_Mastery
git switch integration/mastery-v1-20261127
python3.12 -m venv .venv
.venv/bin/python -m pip install -e '.[qa]' pytest
.venv/bin/python -m playwright install chromium
.venv/bin/python -m pytest -q
bin/mastery
```

Follow [V1 synthetic demo instructions](https://github.com/Sven-Lutz/Exam_Mastery/blob/integration/mastery-v1-20261127/docs/MASTERY_V1.md) and the [course import contract](https://github.com/Sven-Lutz/Exam_Mastery/blob/integration/mastery-v1-20261127/docs/COURSE_TO_MASTERY_CONTRACT.md). This quickstart has not been independently executed as part of the contributor documentation PR; report setup failures as issues. For legacy engine usage on main, refer to ENGINE_README.md. Use only synthetic or redistributable inputs for public contributions.

## Research and repository boundaries

See the [vision and research decision index](docs/MASTERY_VISION.md). Research must distinguish full-text evidence, tentative design hypotheses and measured learning outcomes. Prefer reusable verified mechanisms, simple offline learning and resource efficiency.

Public code, tests, reusable templates, synthetic fixtures and documentation are appropriate after inspection. Do not publish raw lecture materials or copyrighted books, private learner data, secrets, private provider logs or bulk course outputs. Preserve existing evidence and follow [migration and retention policy](docs/MIGRATION_AND_RETENTION.md). No unauthorized spending or hidden model calls.
