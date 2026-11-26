# Exam Mastery — Anki, Obsidian and alternatives: integration research brief (2026-11-26)

**Research candidate / decision pending independent review.** Source audit and vendor-function checks below are preliminary, **not a claim that any choice improves learning in the Exam Mastery product**. Related research issue: [R8](https://github.com/Sven-Lutz/Exam_Mastery/issues/30), resource research [R7](https://github.com/Sven-Lutz/Exam_Mastery/issues/29), and Draft PR #20.

## Executive hypothesis

**Keep Anki as the only external scheduled-retrieval system and optionally Obsidian as a linked, local-first Markdown knowledge workspace.** Exam Mastery is the canonical authoring/evidence/competency authority. No home-grown FSRS, no duplicate Obsidian review algorithm, no mandatory plugins, no paid sync dependency and no replacement app without clear learning + engineering gain.

Why: the current `exam_mastery/learning/experience_anki.py` already generates native `Anki.apkg`, preserving semantic IDs, versioned manifests and publisher integrity. PR #19 tests preserved native Anki notes/revlog/intervals after a controlled reimport. `experience.obsidian_note(unit)` already generates a basic Markdown navigation note. These are **implemented facilities** but not proof of desktop/mobile user acceptance, robust two-way sync or efficacy.

## Option comparison (verify with repeatable acceptance cases)

| Option | Strength / official functionality | Concern for this project | Preliminary disposition |
|---|---|---|---|
| **Anki + native FSRS** | Local decks, .apkg, own notes/templates, scheduling, mobile/web clients; import can update matching notes | Stable note-type field/template IDs, cross-client math/media, schema migrations and reimport conflicts require tests | **Keep default scheduler** |
| RemNote | Integrated notes+flashcards, supports FSRS-6 and Anki/Markdown imports/exports | Replacement of existing tested Anki layer, lock-in/sync/exports and cost/complexity to validate; independent learning advantage not established | **Compare, do not replace by default** |
| Mochi | Markdown cards/notes, selectable FSRS, own archive preserving history | Separate scheduling and migration of already tested native Anki metadata; non-native exports may omit histories | Compare as lightweight alternative |
| Obsidian community FSRS plugins | SRS inside notes, several current variants exist | Second review queue, conflicting scheduling and smaller ecosystem QA guarantee than mature native Anki; migration costs | **Avoid by default** |
| **Obsidian core** | Filesystem Markdown vault; properties, backlinks, Bases, Canvas; official Skills/CLI/headless options | App is not needed to read plain exported Markdown; plugins and live editing expose operational/privacy risks | **Optional workspace, minimal initial setup** |
| Joplin | Open-source Markdown-oriented app, Data API/import/export | App-specific content state and sync API vs direct generated Markdown; duplication | Valid alternative if Obsidian unacceptable |
| Logseq | Outliner/block graph with Markdown/Org and evolving data model | Block-level semantics, evolving storage modes and migration complexity | Research/compare; not automatic default |
| SuperMemo / other dedicated SRS | Potential scheduling/reading models | Existing Anki coverage, portability, workflows and historical-review data loss | Only pursue on evidence of substantive advantage |

Official checks 2026-11-26:
- Anki FSRS: https://docs.ankiweb.net/deck-options.html (FSRS, defaults, Optimize, workload, note compatibility)
- Anki .apkg imports/updates: https://github.com/ankitects/anki/blob/main/docs-site/manual/importing/packaged-decks.mdx (matching note and note type IDs; special migration concerns).
- Anki text imports/updates: https://docs.ankiweb.net/importing/text-files.html (same note/first field, identity, scheduling retained when updated).
- AnkiConnect optional API: https://github.com/ankiultimate/anki-connect (localhost:8765, opt-in API key).
- Obsidian data storage: https://obsidian.md/help/data-storage (Markdown vault + local metadata).
- Obsidian core plugin capabilities: https://obsidian.md/help/plugins (backlinks, properties, Bases, Canvas).
- Obsidian AI/CLI/Headless: https://obsidian.md/help/connectors (official agent skills; CLI requires running desktop app; headless is a separate tool; agent access has privacy implications).
- Obsidian Bases: https://obsidian.md/help/bases (property-filtered views stored in Markdown).
- RemNote FSRS: https://help.remnote.com/en/articles/9124137-the-fsrs-spaced-repetition-algorithm ; exports: https://help.remnote.com/en/articles/7898019-exporting-and-printing-notes .
- Mochi FSRS/export caveat: https://www.mochi.cards/docs/reviewing/fsrs/ (native .mochi carries history, generic Markdown/CSV do not).
- Joplin data API: https://joplinapp.org/help/api/ .
- Obsidian FSRS alternative exemplar: https://community.obsidian.md/plugins/decks .

**Source verification state:** Official product docs provide technical functionality, not independent causal evidence. Test current version before product decisions. Do not infer service pricing, support or permissions without checking.

## Minimum version-one integration: ONE canonical authored model, TWO bounded adapters

```
Exam Mastery local semantic core
  unit_id / knowledge-component / claim / source / assessment / card_id
                    |
              validated build
                    |
         +----------+----------------+
         |                           |
   Anki Adapter                 Markdown adapter
   .apkg + media                generated notes + links
   note IDs / version           stable frontmatter / file IDs
         |                           |
   native Anki desktop          ordinary Markdown folder
   FSRS + reviews               Obsidian optional viewer
         |                           |
   user's review history        user's annotations separate
   ANKI OWNS                    USER OWNS
```

**Three ownership zones:**
1. **Generated / tool-owned:** immutable semantic IDs, source URLs/locators, notation, lesson metadata, card content, linked learning products. Engine may rewrite its own generated content only after hash+version checks.
2. **Application-owned:** Anki revlog/scheduling/collection and Obsidian app configuration; NEVER auto-modify native collections, app settings or journal databases.
3. **Learner-owned:** personal annotation, hypotheses, self-explanation, bookmarks, notes and preferences; never overwritten by a rebuild. Prefer a separate `notes/` workspace linked to generated entries.

### Anki adapter acceptance checklist

- Preserve existing `Anki.apkg` builder, custom HTML/CSS note types and stable semantic GUIDs; tests for title changes, text changes, media changes, note-type field/template ID migrations, additions/removals, reimports.
- Validate **content first**: clear question solvable from prompt, defined conditions and notation, atomic retrieval scope, direct answer + why + source, useful diagrams and contrasts, no ambiguous card fronts and no dense impossible derivation cards.
- Display: real front/back preview, mathematical notation, diagrams, long-word wrapping, light/dark, 320/390px; Anki Desktop and actual mobile client needed before end-user release.
- Use native FSRS; no per-course override automatically set from generated data. Initial Anki defaults are a reasonable non-prescriptive baseline; do not dial desired retention toward 100% as a proxy for excellence. Official docs say higher desired retention increases workload sharply and recommend considering practical review capacity.
- Live updates via **AnkiConnect only if necessary** for measured UX improvement over .apkg import; permit localhost-only, opt-in, API-key support and backup, and avoid direct edits to user collection DB. AnkiConnect requires Anki to be running.
- Automations are safe to generate packages while user is offline, **but active Anki collection imports must be explicit and tested**. Native import options and user edits can create conflicts; make the effect observable before an update.
- For a later bidirectional update, export opt-in non-sensitive review *summaries*, not raw personal collection; avoid publishing learner records to public GitHub.

### Obsidian/Markdown adapter acceptance checklist

- **No Obsidian installation is required for the engine to export Markdown.** A normal directory with `.md` files is a portable format.
- Start with core features only: `[[wikilinks]]`, properties/YAML frontmatter (`em_id`, `competency_ids`, `source_refs`, `version`, `generated`), backlinks, internal links, Bases dashboards; optional Canvas only when a specific causal network warrants it.
- Define stable filenames and redirect rules before automatic renaming. Keep user notes in a distinct editable folder; generated notes are read-only/replaceable by the engine. Do not round-trip arbitrary user edits through generated Markdown.
- Example folder layout, **only a proposal**:

```text
ExamMasteryVault/
  00-Start.md
  10-Courses/                # generated maps
  20-Concepts/               # generated, stable semantic IDs
  30-Sources/                # licensed metadata / citation links only
  40-My-Notes/               # USER-owned, never overwritten
  90-Views/                  # optional .base/Canvas generated views
```

- Use regular files + atomic writes and idempotent hashes. No mandatory Dataview/Templater, Obsidian flashcard plugin, local server, plugin API, cloud account or autonomous vault scraping.
- Research official Obsidian CLI and optional official agent skills **only when** they materially improve reading/editing/search versus filesystem access. Use privacy- and permission-limited scopes.
- Test offline use, file renames, duplicate IDs, wikilink anchors, export/import, changed source versions, recovery of user notes and concurrent edits.
- Manual Obsidian knowledge notes are not automatically correct; generated source/claim evidence remains in the canonical core.

## Reuse-first workflow for end user

1. User places or updates authorized source content in a **private** local course folder (future stage; not during current synthetic research).
2. Engine hashes sources and traces changed knowledge components; unchanged sources → no model request and no output modifications.
3. Engine builds four validated products. Anki deck and optional Markdown view are exports, not new independent data stores/schedulers.
4. User starts studying from the offline app / textbook; Anki Desktop imports the versioned deck after safe review. Regular retention reviews happen in native Anki/FSRS.
5. User can open a generated concept note in Obsidian (or any Markdown reader), add comments in a **separate authored note**, and follow backlinks to source/exercise/app. No duplicate manual copying.
6. When generated content changes, compare semantic IDs/versions, preserve user edits and Anki history, show a clear update diff. Never silently reset schedules.

## Experiments before acceptance

| Test | Observable pass | Failure to challenge |
|---|---|---|
| Anki reimport | Native note/card IDs and review history/due unchanged while content/template updates as expected | changed field IDs, duplicate note, deleted card/review reset, stale media |
| Anki card learning | Independent answerability and retention/transfer on novel tasks | pass shallow Q/A but fail a full derivation/application |
| Obsidian regenerate | Generated links/properties update, user notes unchanged byte-for-byte | two-way edit overwrite, broken backlinks, duplicate note |
| Offline portability | Markdown works without Obsidian, APKG imports in isolated Anki profile | dependency on cloud/plugin |
| Annual maintenance | No extra scheduler, no duplicate metadata store, clear upgrade plan | escalating plugin/API fragmentation |
| Architecture comparison | Measurable UX or quality gain vs baseline `.apkg`+Markdown | added app makes process slower/harder |

## Decision gate

Adopt **Anki + optional Markdown/Obsidian** unless R8 can show another app yields a meaningful, validated improvement with no disproportionate migration and maintenance costs. This is a hypothesis deliberately open to independent falsification. Implementation *after* research gate; until then keep PR #19 unchanged.
