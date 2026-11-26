# Tutoring Resource Preservation and Comparison — Research Brief R9 (26 Nov 2026)

**Status:** Research programme, NOT tested learning outcomes or endorsed software. [Issue R9](https://github.com/Sven-Lutz/Exam_Mastery/issues/31) · [Research charter](RESEARCH_FIRST_PROGRAM_20261126.md) · [Resource registry](RESOURCE_IDEA_REGISTRY_20261126.md). Previous owner input on tutor resources must remain explicitly traceable throughout the research project, not be replaced by generic "ChatGPT tutor" language.

## 1. Specific previously considered systems

| Resource | Verified reference / identity | Unique question for Exam Mastery | Caveat |
|---|---|---|---|
| **DeepTutor** | https://github.com/HKUDS/DeepTutor | Can a coherent learning context support dialog, stepwise problem solving, questions, research, visualization, mastery path and reading without proliferating independent engines? | Broad marketed feature set is not proof of educational effect, extensibility, zero paid cost or correctness. |
| **OATutor** | https://github.com/CAHLR/OATutor ; https://www.oatutor.io/ | What do real step-based hints, BKT student modeling, controlled tasks and experiment instrumentation contribute? | BKT estimates require calibrated parameters; do not infer actual mastery from apparent precision. |
| **LMU SMART-RAG** | https://github.com/digillab-lmu/smart-rag | Course-scoped retrieval, hybrid search, persistent memory, concept maps and integration into learning contexts | Exact source citations must be independently checked for entailment, edition and domain-specific authority. |
| **TutorBench** | https://labs.scale.com/leaderboard/tutorbench ; https://arxiv.org/abs/2510.02663 | 1,490 expert-created tutoring scenarios, multimodal student work, evaluation rubrics | The benchmark measures tutor response capability, not longitudinal causal learning gains; audit licensing, distribution, relevance and contamination. |
| **OpenTutor** | https://github.com/zijinz456/OpenTutor | Local-first tutor, adaptive depth, citation, graph and model selection | Own FSRS/flashcards would conflict with native Anki as only scheduler; inspect version, quality, source/licensing. |
| **PAIDEIA** | https://github.com/OPTIMETA/PAIDEIA ; https://github.com/TaewoooPark/PAIDEIA | Exam-drill, weakness mapping, blind mock assessment, error logs, locally inspectable outputs | **Two GitHub identities were found**. Verify lineage and differences before choosing what to evaluate. Do not assume one canonical codebase from name alone. |
| **Education Agent Skills** | https://github.com/GarethManning/education-agent-skills | Retrieve-first gate, progressive hint ladder, teach-back, confidence calibration, error coach, transfer bridge, fading, unassisted checkpoints | Agent skill descriptions are design candidates, not validated instructional efficacy. Compare against existing policy.py and diagnose.py. |
| **ChatGPT Study Mode** | https://help.openai.com/en/articles/11780217-using-study-mode-in-chatgpt | Immediately usable Socratic tutor interaction with learner-controlled help | Check current supported features; do not assume access to local `file://` or automatic synchronization. |
| **ChatGPT Project / portable tutor** | Existing project source policy and `docs/PRODUCT_CONTRACT.md` | Source-aware context pack plus behavioral instructions for a separate tutoring conversation | Do not auto-leak complete answer keys, private data or unsupported claims; provider-dependent features separately validated. |
| **NotebookLM** | https://notebooklm.google.com/ | Source-focused study workflows and source quotation | Verify supported import, quotation, privacy and deep learning vs summary use. |
| **YouLearn** | https://www.youlearn.ai/ | Multimodal source-grounded study conversations | Company claims and UI not learning-effect research. |
| **StudyFetch** | https://www.studyfetch.com/ | Tutor modes and question/scenario generation | Check sourcing, answer leaks, privacy and baseline. |
| **Khanmigo** | https://www.khanacademy.org/khan-labs | Guided Socratic support and instructional scaffolding | Official policies and independent efficacy not identical. |
| **Math Academy** | https://www.mathacademy.com/how-our-ai-works | Prerequisite graph, placement, adaptive sequencing | Requires longitudinal outcomes and implementation details; no automatic portability. |
| **RemNote Guided Learn Mode** | https://www.remnote.com/ | Contextual notes + active study and linked knowledge | Do not create duplicate flashcard scheduler. |
| **Margin Study / Utterseen** | https://marginstudy.app/ ; https://utterseen.com/ | Contextual reading, annotation and permissioned screen-context tutor | Confirm current identity/features, opt-in, data permissions and minimum need. |

Further tutoring comparisons can include question-based tutoring, model tracing, constraint-based modeling, proof-aware tutoring, educational AI frameworks and multimodal interaction—**only when they add a distinct learning mechanism**.

## 2. Tutoring behavior is a verifiable multi-stage system

Tutoring policy is not "always ask a question" or "always withhold the answer". It conditions help on a learner's intent, demonstrated work, ability and explicit request.

1. **Orient:** clarify learning goal and status using existing trusted competence/claim IDs; do not invent personal learner state.
2. **Diagnose:** if suitable, ask the learner to retrieve, predict, articulate a first proof/program step or diagnose a concrete example. Permit productive warm start for novices; avoid unavoidable retrieve-first gates in contexts where they harm learning.
3. **Select support:** none / analogy / contrast / prerequisite / feedback on one step / hint tier / full example / complete requested answer. A tutor must obey explicit requests for a full explanation and explain why it chose scaffolding.
4. **Ground:** quote or link verified official/public source locators and domain-correct numerical/formal verifier results; distinguish tutor hypotheses from validated errors and abstain on unknowns.
5. **Close help loop:** novel independent task without access to the full solution; label observed performance as assisted/unassisted/transfer.
6. **Retest:** later unassisted attempt when feasible; avoid fabricated retention evidence. Native Anki/FSRS remains review scheduler for declarative cards.

Domain-specific tutors may require mathematics proof/counterexample tools, compile/run/test feedback for programming, date-bound statutes and defensible alternative analyses for law, and clinically safe case uncertainty for medicine. Free text alone is not a proof oracle.

## 3. How the tutor fits existing learning products

```
        Canonical knowledge/competency/source records
               |                   |
        Learning UI & Lab       Tutor context pack
        predict / experiment    scoped source excerpts, prior attempts,
        visual transfer         question rubric, hint/answer access policy
               |                   |
               +---- Evidence / Learning Policy ----+
                         |
              delayed unassisted transfer
                         |
     Anki FSRS only for retrieval card scheduling
```

- The tutor is a **feature in the fourth interactive product**, or a portable ChatGPT/Claude tutoring workflow. **Not a fifth core product.**
- Experimental Lab remains for causal exploration, **not another Anki queue**.
- The tutor must **not share full hidden assessment solutions with the student view** except explicit policy-governed reveal. If deployed via a third-party provider, assess actual answer-key exposure to the provider separately.
- Non-LLM adaptive tutor behavior should reuse existing `learning/diagnose.py`, `learning/policy.py`, `em_tutor.js` and source/competency/evidence contracts. Avoid redundant agent orchestration, memory systems or tutors.

## 4. Required benchmarking — compare against direct frontier-model chat

**Compare four arms where feasible**:
A. Direct ChatGPT/Claude/Gemini chat prompt with exactly the same allowed source information.
B. Portable source-aware Socratic tutor prompt with explicit rules, no API integration.
C. Existing deterministic reference with fixed feedback/hint scaffolding.
D. Proposed adaptive tutor grounded in actual evidence and domain verification.

Benchmarks must use:
- Diagnostic response and misconception specificity (not hallucinated diagnoses).
- Feedback correctness and adherence to stated constraints and source passages.
- Adaptive help timing and avoidance of overhelp.
- Learner independence: new unassisted task, transfer, delayed retention, assistance history, explicit user request behavior.
- Different domains (proof, legal subsumption, coding/debugging, data interpretation, practical/CAD reasoning). Proper high-stakes safety boundaries.
- TutorBench (if licensed and actually tested), manually validated expert rubric and unseen holdout cases. Treat agreement on tutor response scoring as different from causal learning.
- Model/provider cost, latency, offline/online burden, privacy and reproducibility.

**Disconfirming tests**:
- Assistant invents cited proposition not supported by the provided source.
- Learner's answer is correct but not identical to key; tutor falsely penalizes.
- Numerical coincidence gives same answer through incorrect reasoning.
- Tutor infers "mastered" from one assisted correct answer.
- Tutor gives away an unseen exam answer or obstructs an explicit request for a full solution.
- Learner receives many hints and performs worse on a delayed independent task.
- Curriculum graph has missing/contradictory prerequisite or source.
- Tutor crosses medical advice or physical safety boundaries.

## 5. Research deliverables and gate

R9 needs a real source-by-source comparative review, verified versions/license/fork lineage, at least one adversarial synthetic scenario per major mechanism, quantified technical cost where measured, and a **reuse/emulate/defer/reject** decision for each. Coordinate with R5 (scientific tutoring), R7 (other resources), R8 (Anki/Obsidian), R6 (architecture). Final human acceptance gate before implementation of any significant new tutoring feature. No unapproved paid APIs, personal learner data, code, private documents or arbitrary scraping.

Current preferred *hypothesis*: first deploy a portable domain-neutral source-grounded tutor protocol within existing ChatGPT sessions; use the existing deterministic experience policy and optional single-provider connector only if a measured gap justifies it. Comparative research must be able to reject this choice.
