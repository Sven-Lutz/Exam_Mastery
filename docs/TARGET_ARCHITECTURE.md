# Exam Mastery — Zielarchitektur v1.0

**Stand:** 30.10.2026 · **Status:** Architekturentscheidung und Implementierungsvertrag; **kein** bereits validiertes Produktionssystem.

## 0. Produktversprechen und Grenzen

Exam Mastery verwandelt die Materialien eines Kurses in ein fachlich korrektes, quellengebundenes, didaktisch begründetes und qualitätsgeprüftes *Learning Experience Package*: Lehrbuch, Aufgaben mit Lösungen und Rubrics, Anki, bedarfsorientierte interaktive Labs, Prüfungssimulation und optional Tutor.

- **Nicht garantiert:** fehlerfreie KI-Outputs, perfekte Noten, allgemeine Lernwirksamkeit ohne empirische Prüfung.
- **Nicht Ziel:** ein weiterer Summarizer, ein PDF-Generator mit aufgesetztem Agentenschwarm oder eine eigene Anki-Scheduling-Plattform.
- **Verantwortung:** Offizielle Vorlesungsanforderungen erhalten Vorrang hinsichtlich Stoffgrenze und Prüfungsziel. Externe sachliche Korrekturen, didaktische Erweiterungen und Unsicherheit sind getrennt und genau belegt.
- **Wiederverwendung:** Die vorhandene NLP-/Attention-Lab-Implementierung und deren numerische Tests, die NO-GO-Audits und bestehende Lernfassungen sind Regression Assets, keine wegzuwerfenden Experimente.

## 1. Architekturprinzip

**Control Plane** (Workflow Engine, Gate Policies, Routing) != **Knowledge Plane** (Quellen und Claims) != **Production Plane** (Spezialisten, Renderers) != **Learning Plane** (Lernender, Tutor, Interaktionen).

```text
Course Inputs (PDF/PPTX/Code/Exams/Images/Notes)
  → Ingestion & Provenance (structural + multimodal)
  → Course Architect (learning objectives, skill routing, risk)
  → Source/Claim/Competency Graph (versioned, transparent)
  → Learning Experience Plan (teaching + practice + interaction + assessment)
      ├─ Textbook author / Visual explainer / Book designer
      ├─ Assessment engineer / Solution verifier
      ├─ Flashcard learning engineer / Anki frontend engineer
      └─ Interaction designer / Web-Lab engineer
  → Independent domain/learning/technical auditors
  → Policy gates (deterministic blocking; human for unresolved high-risk)
  → Renderer adapters (web HTML/JS; Anki HTML/CSS; print PDF)
  → Product release (all versions linked)
  → Learner practice → unassisted transfer evidence → change requests
```

**Control Plane:** Der Course Architect schlägt eine Konfiguration vor; die Workflow Engine führt sie entlang einer überprüfbaren Dependency-DAG aus. LLMs können keine Qualitätsgates durch Selbstbescheinigung umgehen.

## 2. Datenvertrag — semantisch statt dokumentzentriert

Jedes Lernobjekt erhält eine unveränderliche ID und referenziert nachprüfbare Vorgänger. Mindestobjekte:

| Objekt | Pflichtfelder | Zweck |
|---|---|---|
| `SourceAsset` | id, version/hash, course, kind, locator, rights, captured_at | Original unverändert und konkret referenzierbar |
| `Claim` | id, proposition, evidence_refs, type=official/external/correction/uncertain, status | Aussagenbeleg und Änderungsfolgen |
| `Competency` | id, action_verb, subject, prerequisites, source_refs, exam_scope, expected_evidence | messbare Lernziele, keine reine Themenliste |
| `LearningUnit` | id, claims, competencies, teaching_blocks, misconception_ids, version | fachlicher Gegenstand unabhängig von Formaten |
| `AssessmentItem` | id, competency_ids, required_operations, prompt, solution, scoring_rubric, transfer_level | tatsächliche Prüfung einer Kompetenz |
| `FlashcardSpec` | note_id, competency_ids, retrieval_prompt, answer, explanation, media_refs, source_refs, template_type | Anki-Note, nicht ein Abschnitt als Karte |
| `InteractionSpec` | id, target_competency, model, controls, prediction, feedback, transfer, reference_fixtures, fallback | Learning Lab mit prüfbarem Verhalten |
| `DesignAsset` | id, meaning, alt_text, source_refs, target_variants | didaktisch begründete Abbildungen und Diagramme |
| `ReleaseEvidence` | version, claims_check, subject_review, pedagogy_review, assessment_review, runtime_tests, known_limits | differenzierte Freigabe |

**Wichtig:** Der gemeinsame Kern ist kein kanonischer Lehrbuchtext. Lehrbuch, Anki und Lab sind eigenständig entwickelte, aber über IDs, Claims und Kompetenzen konsistente Lernprodukte. Graphrelationen können zunächst in versionierten JSON/YAML/Markdown-Dateien statt einer Graphdatenbank liegen.

## 3. Course Architect / adaptive Konfiguration

Input: offizielle Lernziele, Foliensätze (inkl. Diagrammen), Übungsunterlagen, Altprüfungen, Softwareartefakte, Lernniveau. Output: `CourseBlueprint` mit:

- Multi-label `knowledge_modes`: formal reasoning, legal reasoning, computational, clinical, empirical, economic, conceptual, interpretative, practical.
- Prüfungsoperationen: prove, calculate, derive, debug, classify, compare, argue, subsume, diagnose, design.
- Risk/verification profile: z.B. klinische Sicherheit, aktualitätsabhängiges Recht, numerische Referenzlösung.
- Required prior knowledge + teaching depth, learner interaction design, assessment families.
- Skill routing und `NOT_NEEDED`-Entscheidungen: kein Labor, wenn kein Lerneffekt erwartet wird; keine Anki-Karte für ungeeignetes Wissen.
- Benötigte Fachgutachter und beabsichtigte Tests.

**Routing-Regel:** Nicht `if course==math`, sondern anhand der zu leistenden Wissensoperationen, Quellenanforderungen und Risiken. Hybride Lehrveranstaltungen aktivieren mehrere Skill Packs.

## 4. Agentenregister — Verantwortungen statt Agentenspektakel

Agenten werden als versionierte Verträge (Eingabe, Ausgabe, Tools, Qualitätsanforderung, Eskalation) implementiert. Eine Rolle kann auf einem Modell ausgeführt werden; mehrere Rollen müssen nicht simultan laufen.

| Rolle | Kategorie | Kernverantwortung | Aktivierung |
|---|---|---|---|
| Course Architect | planner | Blueprint und Produktions-DAG | pro neuer Quelle / Kursänderung |
| Source Forensics Engineer | expert/tool | Folienbilder, Formeln, Tabellen und Layout interpretieren | bei Ingestion |
| Research & Evidence Agent | research | Aussagenquellen und externe Ergänzungen | quellenabhängig |
| Subject Expert / Professor | author | wissenschaftliche Lehre, formale Argumente | pro Lernsegment |
| Learning Scientist | planner/reviewer | Scaffolding, Vorwissen, Erklärungen, Fehlkonzepte | pro Lernsegment |
| Textbook Author | author | vollständiges Manuskript | für Buchprodukte |
| Assessment & Rubric Engineer | author | Transferaufgaben, Lösungen, Teilpunkte | für Prüfungsprodukte |
| Flashcard Learning Engineer | author | was abrufen, welcher Kartentyp, Erklärung | für Anki |
| Anki Frontend Engineer | frontend | HTML/CSS, Templates, Clients, Import/Update | für Anki |
| Visual Explanation Designer | designer | semantische Diagramme, Abbildungen | bei visuell relevantem Inhalt |
| Interaction Designer | designer | Aktionen, Feedback, Transfer, Lernmechanismus | bei sinnvollen Interaktionen |
| Web Lab Engineer | frontend | TS/HTML/CSS/SVG, Simulationen, UI state | bei Labs/Web |
| Editorial / Book Designer | designer | Typografie, Print-Layout, Seitensysteme | bei Büchern |
| Publishing Engineer | tool/workflow | Renderer, Builds, Format-/Asset-Pipeline | bei Releases |
| Domain Auditor | independent reviewer | fachliche Wahrheit, Beweise, Normen, Datierungen | vor fachlicher Freigabe |
| Pedagogy & Assessment Auditor | independent reviewer | Überforderung, Alignment, Transfer, Rubrics | vor didaktischer Freigabe |
| Frontend / Accessibility Auditor | independent reviewer/tool | echte Browser-/Anki-Clienttests, a11y, Security | vor Product Release |
| Adaptive Tutor | runtime agent | Hilfestufen, Feedback, keine ungefragte Lösung | nur im Lernbetrieb |
| Prompt Engineer | meta | systematische Promptfehler beheben, Regression | bedarfsgetrieben |
| Skill Engineer | meta | neue überprüfbare Fähigkeiten als Skills | bedarfsgetrieben |
| Evaluation Engineer | meta | Blindtests, Baselines, Validität, Holdouts | kontinuierlich bei Produktänderungen |

**Default:** Architektur + Evidence + Subject + Assessment + Independent QA; Produktspezialisten nur für tatsächlich verlangte Medien. Parallelisierung nur für unabhängige Teilaufgaben. `Prompt Engineer` ist keine Pflichtstation jeder Vorlesung.

## 5. HTML/CSS/JavaScript-Kompetenz — zwei verschiedene Targets

### Web/Lab Runtime

- Bevorzugt TypeScript + modularer Komponentenansatz, semantisches HTML, CSS Design Tokens, SVG / Canvas nur bei echtem Mehrwert; offlinefähiger Betrieb als Ziel, nicht pauschal vorausgesetzt.
- Jede Interaktion hat ein testbares wissenschaftliches Modell, zulässige Parameterbereiche, deterministische Fixtures, Fehlermeldungen, Reset, Zugänglichkeit, eine nichtinteraktive Fallback-Erklärung und optional datensparsames Feedback.
- `LearningInteraction` enthält Lernhandlung: predict (wenn sinnvoll), manipulate, observe, explain, transfer und formative feedback. Ein Slider allein erfüllt dies nicht.
- Tests: Unit Tests für Fachlogik; Edge Cases; Playwright E2E, Screenshot-Regressionen, Keyboard, mobile Breiten, Dark/Light, Reduced Motion, A11y und untrusted content sanitization. WCAG 2.2 AA als Ziel für eigene Weboberfläche.

### Anki Runtime

- Ein separates `AnkiFrontendTarget`: HTML/CSS-Templates, note fields, selbstständige Front-/Back-Seiten, Dark Mode (z.B. `.nightMode`), responsive 320px aufwärts, MathJax/Anki-native Features, lokale Bilder/Medien.
- Standardpolicy: **keine JavaScript-Abhängigkeit in Review-Karten**. JS allenfalls nach explizitem Client-Matrix-Test und dokumentiertem Fallback. Anki behandelt Karten als Webseiten, garantiert aber keine JS-Kompatibilität.
- Karteikarten sind kein Ersatz für ausführliche Aufgaben, Beweise oder komplexe Labs. Die Frontend-Implementierung ist von der kognitiven Kartenentwicklung getrennt.
- Stabile `note_id` im ersten Importfeld, definierte Note Types, Medienverzeichnis und Import/Update-Vertrag; vor dem Import Test mit Probeprofil und Datenbackup. FSRS bleibt Ankis Scheduler.
- Checks: HTML/CSS auf 320/390/768 px, mobile Dark/Light, Formeln, lange Wörter, Codeblöcke, Bilder, fehlende Felder, note IDs; echte Tests auf Desktop + mobilen Clients; Reimport ohne Verlust der Lernhistorie.
- Gemeinsame **Design Tokens** und semantische Assets, aber keine erzwungene identische Web- und Anki-Laufzeit.

## 6. Book / Visual Engineering

- Manuskript semantisch strukturiert: theorem, proof, definition, case, example, table, warning, exercise, citation, figure, cross-reference; kein nur gestyltes Fließtext-Markdown.
- Visuelle Erklärungen entstehen früh beim fachlichen Design; der Book Designer darf zusätzliche Abbildungen vorschlagen, aber keinen fachlichen Inhalt unkontrolliert ändern.
- Print-Renderer getrennt von Web/Anki (z.B. Typst oder LaTeX statt zwingend Browserdruck). Reproduzierbarer Build, verknüpfte Assets, Inhaltsverzeichnis, Querverweise, konsistente Formeltypen.
- QA: Vollständiger Page-by-Page-Render, Text-/Formelüberlauf, Bildschärfe, Druckränder, Lesbarkeit, Caption-/Abbildungsbezüge, Tabellen- und Seitenumbruchlogik.

## 7. Qualitätsgates / Release States

| Gate | Blockierkriterien | Verifikation |
|---|---|---|
| G0 Input Integrity | Quelle fehlt, falsche Version, nicht untersuchte wichtige Foliengrafik | Hash, multimodaler Check |
| G1 Evidence | wichtige unbelegte/fehlbelegte Aussage, unsaubere Korrektur | source verifier, claim-level audit |
| G2 Scientific | falsch gerechneter Wert, unzulässige juristische Aussage, unbelegter medizinischer Rat | Fachreview + deterministische Prüfungen |
| G3 Pedagogy & Alignment | Kompetenz wird als abgedeckt geführt, ohne entsprechend geprüft zu werden | objective/assessment operation match, Lernwissenschaft |
| G4 Product Integrity | Anki-Überlauf, JS-Abhängigkeit ohne Fallback, kaputtes Labor, Buchlayoutfehler | Client-/Browser-/Print-Tests |
| G5 Release Review | offener abnahmekritischer Defekt oder Risiko nicht freigegeben | unabhängiger Audit + policy gate |
| G6 Learning Evidence | unbekannte Transferaufgaben nicht eigenständig gelöst | pilot experiments / learner study; G6 für empirisch *lernvalidiert*, nicht jede technische Releasepflicht |

States: `DRAFT` → `SOURCE_VERIFIED` → `CONTENT_REVIEWED` → `PRODUCT_TESTED` → `RELEASED`; optional `LEARNING_VALIDATED`. Jede Freigabe ist mit Testprotokoll, Version und Einschränkungen dokumentiert. Unabhängige Modellurteile reichen nicht ohne Evidenz; LLM-Judges sind bias-anfällig.

### Test des Fehlers aus dem NLP-Audit

Für Kompetenz `derive_attention_scale` darf die Coverage-Matrix erst `ASSESSMENT_VALIDATED` melden, wenn eine Aufgabe tatsächlich die Herleitung von `1/sqrt(d_k)` verlangt. Eine beliebige Normalisierungsrechnung erfüllt dies nicht. Die Reviewer prüfen zusätzlich, ob die Beurteilung semantisch stimmt. Ein maschinelles Feld `operation=derive` allein ist kein Beweis.

## 8. Lernbetrieb und Tutor-Freigabe

- Tutor wird aus freigegebenen Lernobjekten und Quellen gespeist; bei Widersprüchen oder fehlender Evidenz kennzeichnet er Unsicherheit.
- Default: Diagnose → abgestufter Hinweis → Selbstversuch → Feedback → vollständige Lösung nur bei Bedarf oder ausdrücklich auf Wunsch.
- Keine Vermischung von unterstützter Arbeitsleistung mit Kompetenzmessung; neue Aufgaben ohne KI nach Verzögerung messen tatsächliche Beherrschung.
- Datenschutz: lokale Lernhistorie als Default, transparente Lösch-/Exportfunktionen, keine unbemerkte Weitergabe sensibler Lerndaten. Für Medizin zusätzlich Evidenz-/Sicherheitsaufsicht; System ersetzt keine ärztliche Entscheidung.

## 9. Implementierungsstrategie ohne Big Bang

**Phase 0: Bestand sichern / Baseline.** Alten NLP-Pilot inkl. Attention-Labor, Audit, Anki und Steuer-K01 unverändert versionieren. Für identische Inputs eine starke Single-Agent-Baseline erstellen.

**Phase 1: Learning Object v1 + zwei HTML-Targets.** Ein `LearningUnit` mit einer mathematisch-technischen und einer steuerrechtlichen Kompetenz. Derselbe Source/Claim/Competency-Vertrag versorgt Buch, Anki und Web, aber jede Ausgabe benutzt einen eigenen Presenter. Funktionsfähige Anki-HTML/CSS-Karte mit Clients, echte Web-Lab-Interaktion mit Fixtures. Keine neue Graphdatenbank.

**Phase 2: Qualitätsschleife.** Claude arbeitet als Autor/Builder im versionierten Workspace, Gemini prüft separat Originalquellen und Artefakte. Eine Gate Policy verhindert `RELEASED` bei offenen P1-Findings. Negative Regressionstests aus NLP werden explizit übernommen.

**Phase 3: End-to-End-Vertical Slice.** Ein kompakter Attention-Lernabschnitt und ein kompakter Steuer-Abschnitt mit tatsächlich unterschiedlicher Didaktik, PDF, Anki und Lab (soweit lernwirksam). Blindbewertung gegenüber Baseline, unbekannte Transferaufgaben.

**Phase 4: Cross-Domain-Holdouts.** Arbeitsrecht, reine Mathematik und Computer Science, später Medizin (mit Fachsicherheitsreview). Keine Kern-Neuentwicklung pro Fach; fehlende Skills ergänzen, aber nur nach nachgewiesenem Bedarf.

**Phase 5: Skalierung.** Änderungspropagation, mehrere Kurse, Wiederaufnahme nach Unterbrechungen, Agenten-Monitoring, Katalog wiederverwendbarer Interaktionstypen, Tutor-Laufzeit.

## 10. Definition of Done für den ersten aussagekräftigen Release

- Ein Lehrabschnitt ist auch ohne Internet oder Tutorkonversation nutzbar.
- Sämtliche im Scope als `RELEASED` markierten Kernclaims haben nachprüfbare Belege; formale Rechenergebnisse sind unabhängig kontrolliert.
- Jede als geprüft deklarierte Kompetenz besitzt mindestens eine wirklich passende Aufgabenstellung, Lösung und Rubric.
- Anki-Karten sind in echten Clients importiert, mobil lesbar und ohne JS-Abhängigkeit funktionsfähig; eine aktualisierte Karte bewahrt bei dokumentiertem Reimport die Note-Identität/Lernhistorie.
- Das Web-Labor besitzt ein numerisches Referenzmodell, valide Eingabegrenzen, sinnvolle Lernhandlung, zugängliches Interface und Transferfrage.
- Das Buch ist hochwertig gesetzt, seitenweise kontrolliert und nutzt erklärende Diagramme, nicht bloß Dekoration.
- Externer Reviewer erhält Originalquellen, nicht nur einen vom Autor zusammengestellten Selbstbericht.
- Der Vergleich gegen eine starke Single-Agent-Baseline zeigt nachvollziehbar, in welchen Kriterien Verbesserungen erzielt wurden und wo nicht.
- `RELEASED` impliziert **keine** empirisch nachgewiesene Notenverbesserung; dazu ist `LEARNING_VALIDATED` erforderlich.

## 11. Entscheidungen, die wir bewusst nicht treffen

- Kein festes »20 Agenten pro Kapitel«.
- Kein generischer «immer ein Lab» oder «immer 100 Karten» Ansatz.
- Keine Gleichsetzung HTML mit einem einheitlichen Runtime-Vertrag für Web und Anki.
- Kein eigener Spaced-Repetition-Scheduler und kein automatisches Modell-Selbst-Approval.
- Keine Pflicht zu GraphRAG, Vektordatenbank, Multi-Agent-Debatten oder komplexen UI-Frameworks ohne empirischen Nutzen.
- Keine Blendung durch Coverage-Prozente, Seitenzahlen, blinde LLM-Qualitätsscores oder dekorative Screenshots.

## 12. Forschungsverweise und technische Primärdokumentation (Abgerufen 30.10.2026)

1. Anthropic (2024/aktuelle Dokumentation): https://www.anthropic.com/research/building-effective-agents
2. Google Research (2026): https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/
3. Chi & Wylie (2014), ICAP: https://doi.org/10.1080/00461520.2014.965823
4. Kestin et al. (2025), positive strukturierte AI-Tutor RCT: https://doi.org/10.1038/s41598-025-97652-6
5. Liu et al. (2026), negative course-integrated tutor RCT, Working Paper: https://doi.org/10.26300/y3f8-vh05
6. Bastani et al. (2025), unguarded GenAI harms learning: https://pubmed.ncbi.nlm.nih.gov/40560616/
7. Anki HTML/CSS/JS: https://docs.ankiweb.net/templates/styling.html
8. Anki fields/media: https://docs.ankiweb.net/templates/fields.html
9. Anki importer and stable identity: https://docs.ankiweb.net/exporting.html
10. Anki FSRS: https://docs.ankiweb.net/deck-options.html
11. WCAG 2.2: https://www.w3.org/TR/wcag/
12. Playwright screenshot tests: https://playwright.dev/docs/test-snapshots
13. LLM-as-a-judge biases (ACL 2025): https://aclanthology.org/2025.ijcnlp-long.18/

**Evidenzhinweis:** Diese Arbeiten stützen Prinzipien und einzelne Entscheidungen; sie validieren nicht die Exam-Mastery-Gesamtarchitektur. Ihre Überlegenheit muss experimentell gezeigt werden.
