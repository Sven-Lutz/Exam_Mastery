# Authoring standard (what the engine's model roles are instructed to produce)

The binding texts are the role prompts in the engine (`exam_mastery/prompts/chapter_*.txt`). Summary:

**Textbook chapter** - motivation, precise definitions, assumptions, worked examples with justified steps, explicit
misconceptions, limits of a model. Subject-adaptive: proofs/derivations and shape checks for maths and ML; algorithm,
invariants and complexity for CS; norm structure, Tatbestandsmerkmale and Gutachtenstil subsumption for law;
assumptions, units and interpretation for economics/finance. No padding.

**Provenance on every block** - `COURSE_SOURCE` (with source element anchors), `AUTHOR_INFERENCE` (didactic
explanation), `VERIFIED_SUPPLEMENT` (only with an allowed external reference). Course numbers must appear in the
cited source text (checked). Competencies in a text-only scope never use the slide's figure.

**Workbook** - original items, progressive difficulty, each tied to competencies and cognitive operations
(recall, explain, calculate, apply, transfer); at least one transfer item where the operation calls for it.

**Solutions** - written by a separate role from the items: full method, every calculation step (re-computed by the
engine), code or legal subsumption where relevant, a marking scheme.

**Official exam questions** - each one is answered from the course sources or marked `SOURCE_MISSING`; never answered
from memory. Diagram questions get a source-grounded figure with verbatim labels.

**Review** - a semantic review and a risk review by the model, at most one revision round. These are model checks,
not independent certification.
