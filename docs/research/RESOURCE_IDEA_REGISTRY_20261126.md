# Exam Mastery — Reference, Idea & Resource Registry (2026-11-26)

**Scope:** Preserve and evaluate all previously considered resources, not copy their products. This is a **research inventory**, NOT endorsement, validated learning effectiveness, license clearance or a finished implementation plan. Related [R7 issue](https://github.com/Sven-Lutz/Exam_Mastery/issues/28) and [research charter](RESEARCH_FIRST_PROGRAM_20261126.md).

## Guardrails
- Preserve the full 4-product vision (Lehrbuch, Arbeitsbuch, Anki, Interaktiv). Obsidian optional, not a fifth product; FSRS scheduling stays in Anki. Relevant examples and decks previously supplied by owner were illustrative, not new test fixtures.
- Assess each reference along *learning operation*, *evidence for its educational mechanism*, *design contribution*, *technical approach*, *license/reuse constraints*, *access/offline and maintenance cost*, *falsifiable Exam Mastery experiment*.
- Differentiate **product marketing**, user reports, descriptive examples, independently evaluated educational outcomes, and software library readiness.
- No resource gets integrated just because it looks elegant. Design inspirations do not confer copyright or library license; do not copy brand/media/assets, content or proprietary systems.
- Include *rejection/deferral reasons* in the registry. Do not suppress earlier ideas as new alternatives emerge.

## A. Previous references retained for research

| Reference | What to study | Target competency/experience | Evidence and feasibility status |
|---|---|---|---|
| 3Blue1Brown — https://www.3blue1brown.com/ | Narrative mathematical animation, intuition → formalism and careful scene progression | conceptual/quantitative; original visual storytelling | **Design inspiration**, no copy or learning-effect assertion |
| Mathigon / Polypad — https://mathigon.org/ ; https://mathigon.io/polypad/ | Manipulable objects, guided discovery and parameter controls; inspect JS embedding API/license | spatial/math | Official API documented, embedded third-party script not automatically offline-licensed |
| Brilliant — https://brilliant.org/ | Short guided discovery and deliberate intervention; distinguish proprietary workflows from evidence | formal/visual | **Competitive inspiration**; inspect actual mechanisms, access and license |
| Seeing Theory — https://seeing-theory.brown.edu/ | Probabilistic simulation, visual-to-statistical correspondence | statistics, probability | Public exemplar; code availability and permission need explicit review |
| Distill — https://distill.pub/ | Interactive scientific publishing, explanations tied to diagrams and graphs | AI/ML research | Reference for quality of exposition, not proven learning efficacy |
| Explanaria — https://explanaria.github.io/ | Open-source explorable animated mathematics; inspect implementation/test/maintainability | mathematics/geometry | Public source, technical reuse only after license/maintenance audit |
| Explorable Explanations — https://explorabl.es/ | Design patterns for prediction→manipulation→feedback→counterexample | cross-domain | Curated examples; vary in evidence and implementation |
| StatQuest — https://statquest.org/ | Expository ordering, intuition and statistical precision | statistics, ML | Explanatory inspiration; no content reuse assumption |
| Bright Side of Mathematics — https://www.youtube.com/@brightsideofmaths | Stepwise university mathematics and rigor | formal reasoning | Teaching reference; verify precise materials before citing |
| Think Logic / Visually Explained | Worked mathematical/visual reasoning as previously suggested | formal/visual | **Candidate identification and link verification still required**, do not guess official URLs |
| Math Academy — https://www.mathacademy.com/how-our-ai-works | Knowledge graph, diagnostic placement, task selection, prerequisite structure, FIRe claims | adaptive quantitative mastery | Product description **not independent validation**; compare against existing policy/Anki |
| RemNote — https://www.remnote.com/ | Note/card links, in-context retrieval, cross-platform data flow | knowledge/retrieval | Product and export docs exist; detailed alternatives audit in R8 |
| marginstudy | Anchored annotations and contextual active reading | study notes/contextual recall | **Unverified reference**, confirm exact project and current availability |
| YouLearn — https://www.youlearn.ai/ | Source-grounded tutor conversations | context-grounded explanation | Product hypothesis, research/test before recommending |
| StudyFetch — https://www.studyfetch.com/ | Generated diverse mini-apps and study aids | adaptive mini-apps | Product inspiration, evaluate actual independent learning value |
| Khanmigo — https://www.khanacademy.org/khan-labs | Guided/guardrailed tutor style | guided reasoning | Tutor behavior reference, not universal evidence |
| OpenDSA — https://opendsa.org/ | Algorithm visualizations embedded in textbook and automatically assessed exercises | algorithms and data structures | Official open-source courseware; evaluate content/API/license and integration costs |
| Exercism — https://exercism.org/ | Authentic implementation/debugging tasks, test-driven feedback, mentorship | coding proficiency | Official task model; compare with Parsons and tracing |
| JupyterLite — https://jupyterlite.readthedocs.io/ | Browser-native notebooks, Pyodide/Xeus kernels, offline/static deployment | coding/scientific computing | Evaluate security, browser asset size and actual offline profile; no automatic arbitrary-code guarantee |
| Pyodide — https://pyodide.org/ | Python-in-browser execution | programming/lab | Isolated browser runtime differs from secure untrusted code service |
| QuantEcon — https://quantecon.org/ | Proof/model/code linkage and reproducible computational economics | finance/economics/statistics | Candidate, verify domain/technical suitability |
| GeeksforGeeks — https://www.geeksforgeeks.org/ | Accessible programming tutorials, example progression | introductory CS | Supporting teaching reference, not primary academic authority |
| Obsidian — https://obsidian.md/ | Markdown vault, backlinks, Bases, Canvas, command tools | knowledge navigation | Optional export target, no extra scheduler; see R8 |
| Anki — https://apps.ankiweb.net/ | Retrieval practice, reviewed content, native scheduling | recall/retention | Existing native APKG adapter and FSRS; see R8 |
| Utterseen / screen-context companions | Permission-based in-situ study assistance | contextual learning | **Unverified/low priority**; privacy/security and necessity review first |

## B. Required additional comparative discovery

Evaluate related but not yet shortlisted practices/projects only when they could displace an existing component or contribute a missing **learning mechanism**. Candidate categories:
- Adaptive curricula, intelligent tutoring and validated educational authoring tools.
- Proof assistants/interactive theorem environments (Lean, Coq, Isabelle, proof-game interfaces), numerical verification and maths editors.
- Statistical simulation and scientific notebooks.
- Argument maps, jurisprudential case practice, medical simulation and experimental/psychomotor skills.
- CAD/3D constraints, physical design verification and computer-aided skill practice.
- Knowledge graphs, source annotations, semantic Markdown and offline search.
- Accessibility, mathematical typography and meaningful visual interaction frameworks.

## C. Reference evaluation card (one per shortlisted resource)

1. Name, canonical URL, publisher/version/date, what was **actually opened or tried**.
2. Learning problem, knowledge mode and task operation. Learner activity: observe/derive/predict/manipulate/retrieve/build/transfer.
3. Learning-science citation for the underlying method, if available; **no assumption that the product is validated**.
4. Instructional UX: entry point, scaffold, formula-object connection, explanation, error recovery, freedom, transfer.
5. Technical feasibility: interface/API, source/license, local deployment/offline, accessibility, responsive assets, data export.
6. Duplication risk with existing Exam Mastery; dependency footprint, maintenance, security and platform longevity.
7. Three executable/observable acceptance tests, a synthetic demo and a falsification case.
8. Decision: **REUSE AS LIBRARY / EMULATE PRINCIPLE / LINK AS RESOURCE / DEFER / REJECT**. State why.

## D. Recommended early evaluation exercises

- **Mathematical insight:** Compare independent 3B1B-style narrated explanation, Mathigon-like manipulable model and static illustrated proof on the same binomial/Attention competency. Check new transfer tasks, not play duration.
- **Statistics:** Reproduce a simple stochastic sampling inference with Seeing Theory-like repeated simulation and verified numerical oracle; ask learner to explain why one sample does not prove a population claim.
- **Coding:** Compare Parsons/tracing, Exercism-like write/test, and OpenDSA-like structure manipulation on a search/data-structure skill. Include adversarial correctness and complexity questions.
- **Source-grounded tutor:** Challenge a Socratic response with ambiguous references, incorrect student attempts, contradictory sources and independent delayed test.
- **Cross-domain craft:** For CAD versus physical woodworking, separate simulations/checklists from measured real-world accuracy.

## E. Explicit quality criteria

Favor educational correctness, independent transfer, epistemic humility, low opportunity cost and interoperable local assets. **No new tool is a requirement** absent a demonstrated improvement over the existing book/workbook/Anki/interactive pipeline. The final shortlist should keep a short core, not a collection of installed products.

## Source leads verified 2026-11-26

- Mathigon Polypad API: https://mathigon.io/polypad/
- Seeing Theory: https://seeing-theory.brown.edu/
- Distill: https://distill.pub/about/
- Explanaria: https://explanaria.github.io/
- Math Academy: https://www.mathacademy.com/how-our-ai-works
- OpenDSA: https://opendsa.org/home/about
- Exercism practice exercise model: https://exercism.org/docs/building/tracks/practice-exercises
- JupyterLite: https://jupyterlite.readthedocs.io/
- R8 covers official Anki and Obsidian technical sources.
