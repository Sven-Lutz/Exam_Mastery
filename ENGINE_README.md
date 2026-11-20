# Exam Mastery 0.4 — incremental one-path runtime

Run `./start "/any/local/lecture/root"`. No subject parameter, source folder convention, separate URL list or manual phase calls. The user-facing command is “Starte Exam Mastery mit `/any/local/lecture/root`.” Outputs are placed outside sources in Studio/runs_v0_4/course-*/<run-id>/ (fallback ~/Exam_Mastery_v04_Output). Originals and engine bytes are checked before/after.

The default backend is the installed, authenticated Codex CLI through its documented non-interactive interface. No Claude or Gemini installation is required. Python dependencies live in Studio/.runtime-v0_4; `requirements-tested.txt` records the installed library versions. Providers implement ask/fingerprint; role logic does not call vendor CLIs directly. Optional Claude/Gemini adapters retain diagnostics but are not required for acceptance. Content-only calls disable shell, app, skill/plugin features, use read-only execution and are checked for unexpected tool events. Credentials are not printed; model processing is not offline.

## Corpus and curriculum

All local files are inventoried recursively, including unknown formats and metadata. Supported extraction includes PDF/PPTX/DOCX, text/Markdown/HTML, CSV/TSV/XLSX, source code and Jupyter. Foreign code is read, never executed. Images are source evidence; unsafe/unavailable rendering is recorded as a gap. Public root-reference URLs are all attempted, without the former 30-URL ceiling; nested page links are inventoried without unbounded crawling. DNS/IP pinning, redirect revalidation, TLS, no credentials/proxies and per-source resource limits remain. Completed fetches have a per-run journal for reproducible recovery.

The complete SQLite corpus index contains every extracted segment, hash and source relation plus FTS search. Sources are split without dropping characters. Transport units are bounded (18,000 source characters, at most four visual page identities); they are not imposed curriculum units. A Course Architect infers competencies and a Learning Designer chooses methods and retrieval eligibility from real evidence. Competence-driven retrieval supplies relevant evidence from other transport units. Every primary segment is processed independently of retrieval ranking. Extraction caches are content-addressed; completed unit caches are bound to engine identity and every stage validates canonical input/output hashes.

Roles: Course Architect → Researcher → Learning Designer → Professor/Author → Assessment Engineer → independent Solutions Engineer → Flashcard Engineer → Web Lab Engineer → Book Designer → separate domain and pedagogy auditors → export/technical QA → hierarchical course audit. A bounded declarative correction can address severe findings, followed by re-audit. It cannot modify source or engine code. Final source and competence coverage is explicit. Numeric solutions and safe simulations have independent arithmetic checks; this does not prove every scientific claim.

## Products and quality

START.html links the course book, exercises, worked solutions, Anki and unit web labs. Artifacts include learning_package.pdf plus separate Lehrbuch.pdf, Aufgaben.pdf and Loesungen.pdf; responsive HTML with independent practice and feedback; rendered source-grounded table/flow figures; justified numeric/quiz labs or explicit no-lab rationale; Basic Anki TSV/templates and APKG. Anki GUIDs, field/template identities and export timestamps are stable for retained note IDs. Update reports never silently delete omitted notes. Unchanged content units keep identities; resegmented/changed source units can require migration and reported retirement review.

PDF pages are rasterized, source/competency contracts checked, browser reflow and interactions executed, images checked, and real Anki imports/updates tested in disposable collections. Eight review dimensions separate source, scientific, didactic, exam, Anki, publishing, reliability and generalization evidence. No real user collection is touched. No arbitrary generated JS or source code is executed. Numeric feedback preserves a fixed prediction target while learners explore other parameters.

Technical PASS is not scientific release. Separate contexts of one model family are not independent external verification. All materials remain reviewable drafts; high-stakes/current facts and unprocessed visuals are not silently certified. Universal academic excellence and learning efficacy require separate empirical evaluation. Rendering limits, native Anki GUI/mobile support and richer card mechanisms must be reported, not assumed.

## Diagnostics and resume

Each model attempt retains redacted request, full stdout/stderr, actual process return code, timeout/duration, raw events and parsed result under provider_evidence/<role>/attempt-*/. Failed contracts remain separate. Checkpoints are written atomically; prior checkpoints/statuses are archived. Repeating the same one-path command automatically resumes a failed/interrupted run only when source, engine, provider and output hashes match. Successful roles are not rerun merely because JSON object keys changed. Changed sources or engine create a new versioned run; identical units can reuse validated cache entries. A course file lock prevents concurrent writers. Failure never implies GO.

## Work integration

A personal v0.4 skill maps the natural-language one-path request to this runtime and reads the resulting status/reports. A programmatic ChatGPT Work model-call API is not assumed or simulated. The supported, actually executable alternative is Codex CLI automation; Work can invoke it when approved local process/file access is available. A Work UI task must be practically verified before claiming that specific UI path passed. If Work cannot reach the Mac, use this single local start with the same root argument.

Official references: https://learn.chatgpt.com/docs/non-interactive-mode ; https://learn.chatgpt.com/docs/build-skills ; https://learn.chatgpt.com/docs/enterprise/chatgpt-work-local-security . Actual test/acceptance evidence lives under Studio/reports/v0_4_sprint/.

## Final acceptance: explicit numeric prediction target

Numeric lab specifications require `numeric.prediction_target`, a finite slider-reachable value different from `default`. The production prompt, source-based auditors, browser and executed QA use this same fixed comparison. Existing note identities and the one-path `start <root>` interface are unchanged. This working candidate is not a release: native Desktop/mobile and independent external subject review require separate evidence. See the Studio `reports/v0_4_1_final_acceptance/` report.

## Mathematical & Visual Quality candidate v0.5

See `docs/MATHEMATICAL_VISUAL_SPECIFICATION.md`. Canonical offline TeX records, vector scientific figures, operation-specific reading patterns and actual cross-media geometry gates extend the existing publishers. Legacy author contracts remain readable but receive no advanced-mathematics validation claim. The one-path interface remains unchanged. Dedicated dependencies are installed by `scripts/SETUP_MATH_RUNTIME.sh` outside the Documents source tree; no previous environment is modified. Native Anki clients, historical migration and independent external review remain separate mandatory gates. This is a working candidate, not a released freeze.

## Source-free Experience prototype (draft)

The new experience layer is validated with synthetic cross-domain fixtures **before any lecture inputs**. It creates an actual **single offline interactive HTML**, not fake textbook or Anki output:

```bash
python -m exam_mastery.cli experience validate fixtures/experience_reference.json
python -m exam_mastery.cli experience render fixtures/experience_reference.json --out /tmp/em-reference
# Open /tmp/em-reference/Interaktiv/index.html
```

Supported deterministic exploratory models: lower-bound binary search and finite discounted returns. The player requires a numerical prediction before revealing its stepwise trace, uses verified Python reference calculations, and unlocks solutions only after an independent answer attempt. Browser code runs offline without network access or LLMs; it **does not execute learner code**, certify scientific accuracy, or provide a secure coding sandbox. Other domains remain contract-valid but require their own tested renderers. Obsidian is an optional Markdown view and Anki remains the only repetition scheduler.

The same checked synthetic unit may also be exported through the **existing** Anki engine: `python -m exam_mastery.cli experience anki fixtures/experience_reference.json --out /tmp/em-reference`. Only `Anki.apkg` is user-visible; the incremental, stable-identity metadata resides in a hidden state folder. Exports never modify a learner's Anki collection; imported scheduling remains Anki/FSRS's responsibility. Do not interpret a successful export as proof of card quality.

Two **consolidated PDF** products from the same canonical unit now reuse the existing MathJax/Chromium typesetter (not a second rendering engine):

```bash
python -m exam_mastery.cli experience books fixtures/experience_reference.json --out /tmp/em-reference
```

The workbook contains both tasks and complete solutions in distinct sections; there is no separate solution or mock-exam file. Outputs are exactly `Lehrbuch.pdf` and `Arbeitsbuch.pdf`, with hidden incremental integrity state. The source-free fixture is a technical test, not proof of book-level scientific depth. Existing outputs with unknown provenance or manual modifications are never overwritten.
