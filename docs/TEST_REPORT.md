# Exam Mastery 0.2 — Pre-freeze Test Evidence

**Date:** 2026-10-30. **Test dataset:** `fixtures/synthetic_course/lecture.md` (constructed finance exercise, NOT secret course data). **AI provider:** `fixture` (prewritten synthetic responses), so no real model-scientific validation was performed.

## Executed

- `python -m unittest discover -s tests -v`: 15 tests PASSED.
- Integration: `python -m exam_mastery.cli run --sources fixtures/synthetic_course --out /mnt/data/Exam_Mastery_Engine_demo --producer fixture --reviewer fixture --fixture-dir fixtures/synthetic_responses --dev`: `TECHNICAL_DEMO_ONLY`, all contract checks PASSED.
- `python scripts/browser_smoke.py --run /mnt/data/Exam_Mastery_Engine_demo`: responsive web + Anki template smoke PASSED at 320/390/768/1280 px, light/dark, front/back, no observed overflow. Numerically-driven curve and result rendered, no JS errors.
- `python scripts/pdf_smoke.py --run /mnt/data/Exam_Mastery_Engine_demo`: four-page searchable PDF passed text-boundary check. Human inspection of rendered page 1 found no gross collisions.
- Synthetic lab P=100, shares=20: t=.30 => EPS=3.50, t=.10 => EPS=4.50, both numerically correct.
- Intentionally invalid provenance, false coverage, inconsistent rubrics, missing transfer task, duplicate cards, script injection expression, incorrect numeric reference, bad audit self-approval and low-contrast design fail the expected gates.

## What has *not* been executed

- Authenticated live Claude/Gemini calls and their cross-provider reliability.
- Complete independent field-expert audit of the output material.
- True client import/update on Anki Desktop / mobile, including persistent history.
- Cross-domain *model generation* on real law, mathematics, medicine, humanities, computer science, etc.; open-world routing has been **structurally** tested only.
- Automated multimodal interpretation of PDF/PPTX diagrams or scanned pages.
- Randomized learner outcome or unseen transfer study.
- Fair single-agent baseline comparison.

**Conclusion:** Software pipeline is suitable for a first carefully monitored hidden-course test. The system's scientific quality and generalization are hypotheses, not verified achievements.
