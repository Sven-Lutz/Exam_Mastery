# R8 — Anki (natives FSRS), Obsidian, Alternativen und reibungsarme Integration

Stand 27.11.2026. **Forschungsentwurf, nicht unabhängig geprüft.** Issue [#30](https://github.com/Sven-Lutz/Exam_Mastery/issues/30). Brief: [ANKI_OBSIDIAN_TOOLING_RESEARCH_20261126.md](../ANKI_OBSIDIAN_TOOLING_RESEARCH_20261126.md). Daten: [r8/r8_tools.json](r8/r8_tools.json) (30 Karten), [r8/r8_evidence.json](r8/r8_evidence.json) (41 Quellen, Suchprotokoll S01–S17), [r8/r8_workflow_policies.json](r8/r8_workflow_policies.json) (R8-POL-01…14). Tests: `tests/test_r8_workflows.py`.

Arbeitsgrundlage AD-1: natives Anki ist der einzige Scheduler. Alle Policies sind `design_hypothesis`, `learning_evaluation = NOT_RUN`. Kein Werkzeug wurde installiert oder ausgeführt; keine Sammlung und kein Vault wurde geöffnet.

## 0. Kurzfassung

1. **Der Standard hält, mit drei Korrekturen.** Natives Anki (SM-2 oder FSRS nach Wahl der Lernenden) plus ein gewöhnlicher, einseitig generierter Markdown-Ordner, den Obsidian optional anzeigt. Keine Alternative bietet einen belegten Lernvorteil; jede integrierte Alternative (RemNote, Mochi, Logseq, SiYuan, SuperMemo, Obsidian-SRS-Plugins) bringt einen zweiten Scheduler und ungeklärte oder proprietäre Historienportabilität.
2. **Die Identität im Entwurfsstapel ist fragiler als der Brief annimmt** (Quelltext des Anki-Importers gelesen): Notiztyp-IDs werden aus dem Anzeigenamen gehasht (eine Markenumbenennung blockiert alle Updates), GUIDs enthalten den Kapitel-Slug (Verschieben = neue Notiz), jeder Export stempelt alle Notizen neu (jeder Reimport überschreibt lokale Änderungen), Schriftdateien mit `_`-Präfix werden nie aktualisiert. Details §4, Befunde EF-1…EF-8.
3. **FSRS-Evidenz ist Vorhersagegüte, kein Lernergebnis.** Im srs-benchmark (9.999 Anki-Sammlungen) erreicht ein Mittelwert-Baseline ohne Scheduling (MOVING-AVG, Log Loss 0.3369) etwa das Niveau von FSRS-7 recency (0.3370; FSRS-7 ohne Recency 0.3401) und ist besser kalibriert als FSRS-6 (0.3460). Eine randomisierte Lernstudie FSRS vs. SM-2 wurde nicht gefunden (S09). Die Engine stellt FSRS deshalb weder ein noch bewirbt sie es.
4. **Stärkstes Gegenargument:** Pan et al. (2023, sechs Experimente, Abstract) fanden selbst erstellte Karteikarten nach 48 h besser als vorgefertigte (Gedächtnis d = 0.45, Anwendung d = 0.29). Das stellt rein generierte Decks in Frage. Antwort: generierte Karten bleiben Standard, plus optionaler generativer Weg in lernereigenem Notiztyp (R8-POL-13, Sicherheit niedrig).
5. **AnkiConnect bleibt zurückgestellt:** Standardmäßig ohne Authentifizierung (`apiKey: null`) und mit Schreibmethoden für Scheduling, Reviews, Löschen und Profilwechsel auf die laufende Sammlung.

## 1. Methode und Zugang

Dokumentationsanalyse nach [SEARCH_PROTOCOL.md](SEARCH_PROTOCOL.md) und [EVIDENCE_REGISTER_SCHEMA.md](EVIDENCE_REGISTER_SCHEMA.md); Register im R1-Schema `r1-evidence/1`.

| Zugang | Anzahl | Bedeutung |
|---|---|---|
| `fulltext_partial` | 28 | offizielle Seite einmal über ein Fetch-Werkzeug gelesen (werkzeugseitige Zusammenfassung mit Fundstellen) bzw. README/Quelltext direkt gelesen |
| `abstract` | 4 | Ye 2022, Tabibian 2019, Lindsey 2014, Pan 2023 |
| `metadata` | 9 | Release-/Repo-Metadaten, Su 2023, Settles 2016, Kobayashi 2005, SuperMemo-Sekundärquellen |

Evidenzklassen: 19 technische Dokumentation, 6 Repository-Metadaten, 5 Herstellerdokumentation, 1 Quelltext, 1 Benchmark, 3 Algorithmuspapiere, 1 Log-Analyse, 1 Synthese (nur Metadaten), 2 Sekundärquellen, **2 Lernoutcome-Experimente** (beide nur Abstract). Nur diese zwei dürfen eine Lernwirkung stützen (`may_support_learning_effect`).

Werkzeuge: `gh api` (Repos, README, Lizenz, Quelltext, Releases), PyPI-JSON, Crossref/OpenAlex, je eine Abfrage pro Handbuchseite, zwei Websuchen. Der Engine-Code wurde nur gelesen (`git show origin/integration/quality-recovery-20261126:<pfad>`), ebenso das Brand-Dokument auf `origin/feat/mastery-brand-phase-b` und die R9-Karten auf `origin/research/r9-tutoring-resources-20261127`. Spacing/Retrieval wurde nicht neu recherchiert; zitiert werden R1-IDs (`murray2025mathspacing`, `ebersbach2020mathspacing`, `higham2022relearning`, `bisra2018`).

Fehlschläge (protokolliert): Anki-FAQ mit `.html` 404; Pan-Preprint über OSF nur als JavaScript-Hülle lesbar; vermutete DOI für Lin et al. 2018 nicht auflösbar; Obsidian_to_Anki nicht in der offiziellen Plugin-Liste gefunden; SuperMemo nur über Sekundärquellen.

Versionsstand am Zugriffstag: Anki 26.09.4 (2026-11-04), PyPI `anki` 26.9.4, Obsidian 1.15.1 (2026-11-12), AnkiConnect Commit f0d96a8ac9, fsrs-rs 7.0.0, Joplin 3.7.24, Logseq 2.0.2, SiYuan 3.8.12.

### 1.1 Produktfunktion vs. Lernwirkung

| Aussage | Art | Beleglage |
|---|---|---|
| Anki erhält Karten und Revlog beim .apkg-Update gleicher GUID | Produktfunktion | Quelltext gelesen, nicht ausgeführt |
| FSRS sagt Abruf in Anki-Logs besser vorher als HLR | Benchmark | srs-benchmark, Entwickler-betrieben |
| FSRS spart Reviews (Anki-FAQ, RemNote „20–30 %“) | Marketing | ohne Quelle auf der Seite |
| Verteilter Abruf > massiert | Lernwirkung | R1-POL-A05 (moderat) |
| Modellbasierte personalisierte Wiederholung verbessert Kursretention | Lernwirkung | Lindsey 2014, ein Feldexperiment, nicht FSRS, Abstract |
| Selbst erstellte > vorgefertigte Karten | Lernwirkung | Pan 2023, Abstract, 48 h |
| FSRS > SM-2 im Lernergebnis | — | **nicht belegt** (S09) |

## 2. Engine-Ausgangslage (Entwurfsstapel, nur gelesen)

`anki_v2.build_deck` erzeugt `.apkg` über die offizielle `anki`-Bibliothek ohne Scheduling und ohne Deck-Presets, mit GUID = Hash(Kurs-Slug, Kapitel-Slug, semantischer Schlüssel), festen Notiztypen „Basis (v2)“ und „Lückentext (v2)“, Update-Delta und Ausmusterungsliste statt Löschen. `experience_anki.publish` verweigert das Überschreiben fremder oder manuell geänderter Pakete. `verify_package` importiert in eine Wegwerfsammlung. `experience.obsidian_note` schreibt eine Navigationsnotiz mit `review_scheduler: anki`. Das ist eine gute Basis. Befunde aus dem Abgleich mit dem Importer-Quelltext:

| ID | Befund | Folge | Policy |
|---|---|---|---|
| EF-1 | Notiztyp-, Feld- und Template-IDs werden aus dem Anzeigenamen gehasht | Markenumbenennung = neuer Notiztyp; vorhandene Notizen werden als `conflicting` nicht aktualisiert | R8-POL-02 |
| EF-2 | GUID enthält Kapitel-Slug (Einheit + Digest) | Karte in andere Einheit verschoben = neue Notiz, Historie bleibt an der alten | R8-POL-02 |
| EF-3 | Deckname = Präfix + Einheitstitel | Titeländerung: neue Karten im neuen Deck, alte bleiben im alten | R8-POL-02 |
| EF-4 | jeder Export setzt `mod` aller Notizen neu | „wenn neuer“ überschreibt bei jedem Reimport alle Felder, auch lokale Änderungen | R8-POL-05 |
| EF-5 | Schriften als `_em-sans-*.woff2` | Importer überspringt existierende `_`-Dateien: Schriftänderungen kommen nie an | R8-POL-04 |
| EF-6 | Abbildungsname ohne Inhalts-Hash | geänderte Abbildung wird umbenannt, alte bleibt als Medienmüll | R8-POL-04 |
| EF-7 | Reimport-Test setzt Kartenzustand und Revlog per SQL | echte Antworten und FSRS-Zustände ungeprüft | R8-POL-08 |
| EF-8 | Notiztyp-Filter über Namenspräfix | Tests koppeln an Marke (Brand-Dokument verlangt IDs) | R8-POL-03 |

Hinweis an Owner, außerhalb des R8-Auftrags: `learning/anki_bridge.py` enthält einen Quellenverweis mit dem Dateinamen einer Kursunterlage; ob das im öffentlichen Repository gewollt ist, sollte geprüft werden.

## 3. Entscheidungsmatrix

Legende Scheduler-Rolle: `native_anki` = AD-1-Scheduler; `none`; `can_modify` = kann Anki-Scheduling verändern; `second` = eigener Planer. Aufwand = Migrations-/Betriebsaufwand nach Dokumentlage.

| Karte | Option | Scheduler | Aufwand | Entscheidung | Kernbegründung |
|---|---|---|---|---|---|
| TOOL-ANKI-FSRS | Anki + natives FSRS (Desktop, AnkiMobile, AnkiDroid) | native_anki | niedrig | **ADOPT_DEFAULT** | AD-1; offen (AGPL), lokal, Historie bei Lernenden |
| TOOL-ANKI-APKG | .apkg mit stabilen GUIDs | none | niedrig | **ADOPT_DEFAULT** | einziger Weg ohne laufendes Anki und ohne Schreibzugriff auf die Sammlung |
| TOOL-MD-FOLDER | gewöhnlicher Markdown-Ordner | none | niedrig | **ADOPT_DEFAULT** | portabel, ohne App/Konto/Plugin |
| TOOL-OBSIDIAN-CORE | Obsidian (Vault, Links, Backlinks, Properties) | none | niedrig | OPTIONAL_ADAPTER | Betrachter; Engine schreibt nie `.obsidian` |
| TOOL-OBSIDIAN-BASES | Bases | none | niedrig | OPTIONAL_ADAPTER | Übersichten ohne Plugin; nur generierte `.base` |
| TOOL-ANKIWEB-SYNC | AnkiWeb | none | – | LINK | Nutzerentscheidung; Engine synchronisiert nie |
| TOOL-OBSIDIAN-SYNC | Obsidian Sync | none | – | LINK | keine bezahlte Pflichtabhängigkeit |
| TOOL-OBSIDIAN-SKILLS | Connectors / Agent Skills | none | – | LINK | Formatreferenz; Datenschutzhinweis |
| TOOL-ANKI-TEXTIMPORT | Text-/CSV-Import mit GUID-Spalte | none | mittel | DEFER | Rückfall, falls ein Client .apkg-Updates falsch verarbeitet |
| TOOL-ANKICONNECT | AnkiConnect | can_modify | mittel | DEFER | ohne Schlüssel offen; Schreibzugriff auf aktive Sammlung; kein gemessener Bedarf |
| TOOL-OBSIDIAN-CANVAS | Canvas / JSON Canvas | none | niedrig | DEFER | nur mit R7-Begründung |
| TOOL-OBSIDIAN-CLI | Obsidian CLI | none | mittel | DEFER | laufende App + `eval` als Abhängigkeit ohne Gewinn |
| TOOL-OBSIDIAN-ANKI-BRIDGES | Obsidian→Anki-Brücken | none | mittel | DEFER | respektiert AD-1, aber zweite Kartenquelle + AnkiConnect |
| TOOL-JOPLIN | Joplin | none | mittel | DEFER | Ersatzbetrachter, falls Obsidian abgelehnt |
| TOOL-LOGSEQ | Logseq | second | hoch | DEFER | Beta-DB mit dokumentiertem Datenverlustrisiko; eigene Karten |
| TOOL-OBSIDIAN-HEADLESS | Obsidian Headless | none | hoch | REJECT | Beta, Konto, npm-global; Engine synchronisiert keine Vaults |
| TOOL-FSRS-HELPER | FSRS Helper | can_modify | – | REJECT | verändert Scheduling; Handbuch warnt vor Intervall-Add-ons |
| TOOL-GENANKI | genanki | none | mittel | REJECT | offizielle Bibliothek bereits im Einsatz |
| TOOL-DIRECT-DB | direkte SQLite-Schreibzugriffe | can_modify | hoch | REJECT | umgeht Anki, Korruptionsrisiko |
| TOOL-OBSIDIAN-SRS-PLUGIN | Spaced Repetition (FSRS/SM-2) | second | hoch | REJECT | AD-1; Plugins ohne Sandbox |
| TOOL-OBSIDIAN-DECKS | Decks (FSRS-6, importiert Anki-Historie) | second | hoch | REJECT | AD-1; Einzelentwickler; als Gegenargument notiert |
| TOOL-OBSIDIAN-OTHER-SRS | weitere SRS-Plugins (87 Treffer) | second | hoch | REJECT | AD-1; 8.404 Plugin-Beschreibungen mit „nicht manuell geprüft“ |
| TOOL-REMNOTE | RemNote | second | hoch | REJECT | FSRS-6 nur Beta, Export ohne belegte Historie, Cloud (R9: RES-REMNOTE) |
| TOOL-MOCHI | Mochi | second | hoch | REJECT | eigener Planer, kein Optimierer, Historie nur in `.mochi` |
| TOOL-SIYUAN | SiYuan | second | hoch | REJECT | `.sy`-JSON statt Markdown, eigener FSRS |
| TOOL-SUPERMEMO | SuperMemo / other dedicated SRS | second | hoch | REJECT | Identität nicht offiziell geprüft; Historienverlust |
| TOOL-MATHACADEMY | Math Academy (als Workflow) | second | hoch | REJECT | FIRe-Planer (R9: RES-MATHACADEMY) |
| TOOL-DEEPTUTOR | DeepTutor (als Workflow) | second | hoch | REJECT | eigene Review-Termine (R9: RES-DEEPTUTOR) |
| TOOL-OPENTUTOR | OpenTutor (als Workflow) | second | hoch | REJECT | eigener FSRS-4.5 (R9: RES-OPENTUTOR) |
| TOOL-STUDYFETCH | StudyFetch (als Workflow) | second | hoch | REJECT | eigener Lernplan, Selbstauskunft (R9: RES-STUDYFETCH) |

Alle Optionen des Briefs (Anki + FSRS, RemNote, Mochi, Obsidian-Community-FSRS-Plugins, Obsidian core, Joplin, Logseq, SuperMemo/andere SRS) und von Issue #30 (AnkiConnect, AnkiWeb, Bases, Canvas, CLI, Headless, Agent Skills, SiYuan) sind enthalten; die Tests prüfen das. Opportunitätskosten stehen je Karte im JSON.

### 3.1 Warum kein Wechsel trotz besserer UX einiger Alternativen

Integrierte Notiz-plus-Karten-Systeme sparen einen Kontextwechsel. Dagegen stehen: (a) keine Lernstudie für eines davon; (b) jedes ersetzt Ankis Historie durch eine eigene, deren Export entweder proprietär (Mochi `.mochi`), unbelegt (RemNote) oder plugin-intern (Decks: SQLite im Plugin-Ordner) ist; (c) Community-Plugins laufen laut Obsidian ohne Sandbox mit Datei-, Netz- und Programmrechten; (d) die Engine besitzt bereits eine getestete .apkg-Strecke. Der Wechsel würde Aufwand verlagern, nicht senken.

### 3.2 FSRS: was die Evidenz trägt

- **Benchmark** (srs-benchmark, README Commit 57c0b0700c): 10.000 Anki-Nutzende, ca. 727 Mio. Reviews; ausgewertet ohne Same-Day-Reviews 9.999 Sammlungen, 349.923.850 Reviews; Log Loss / RMSE(bins) / AUC: FSRS-6 0.3460 / 0.0653 / 0.7034; FSRS-7 recency 0.3370 / 0.0593 / 0.7220; MOVING-AVG 0.3369 / 0.0592 / 0.7001; HLR 0.4694 / 0.1275 / 0.6369. Vom FSRS-Team betrieben, keine Lizenzangabe, kein Peer-Review.
- **Algorithmuspapiere** (Ye 2022, KB `ye2022`; Su 2023) berichten Scheduler-Gütemaße auf MaiMemo-Logs, keine randomisierte Lernstudie.
- **Lernoutcome** zu modellbasierter Wiederholung allgemein: Lindsey et al. 2014 (Abstract): personalisierte Wiederholung +16,5 % Kursretention gegenüber massiert und +10,0 % gegenüber einheitlichem Spacing in einem Mittelstufen-Fremdsprachenkurs. Nicht FSRS; Einheit (Prozentpunkte oder relativ) aus dem Abstract nicht prüfbar.
- **Folgerung:** FSRS ist eine plausible, offene, gut dokumentierte Option. Die Engine bleibt neutral (R8-POL-11, R8-POL-12).

## 4. Identität, Versionierung, Medien und FSRS-Prozess

### 4.1 Identität (R8-POL-02)

Aus dem Importer-Quelltext (ankitects/anki `rslib/src/import_export/package/apkg/import`, Stand main, notes.rs zuletzt 2026-11-11):

1. Notizen werden über die **GUID** gefunden. Ohne Treffer: neue Notiz.
2. Update nur, wenn die **Notiztyp-ID gleich** ist; sonst `conflicting` (kein Update). Bedingung „wenn neuer“ vergleicht die Änderungszeit.
3. Gleiche Notiztyp-ID mit **anderem Schema** ohne Merge: Duplikat-Notiztyp mit neuer ID; vorhandene Notizen werden nicht aktualisiert.
4. **Vorhandene Karten werden nie verändert**; nur fehlende Kartenordinale kommen hinzu; Revlog nur, wenn eindeutig.
5. **Decks** werden über den Namen zugeordnet; vorhandene Karten wandern nicht.

Regeln: GUID = Hash(Kurs-ID, globaler semantischer Kartenschlüssel), ohne Kapitel/Titel/Text. Notiztyp-, Feld- und Template-IDs sind Konstanten im Code; um bestehende Pakete nicht zu brechen, werden die **heute erzeugten Werte eingefroren** und der Anzeigename entkoppelt (Owner-Entscheidung 2). Deckname ist Darstellung, keine Identität. Verschieben einer Karte zwischen Einheiten nur über eine versionierte Zuordnung `alter Schlüssel → neuer Schlüssel`, die die GUID behält. Entfernte Karten: Ausmusterungsliste, nie löschen.

### 4.2 Notiztyp-Schema (R8-POL-03)

Feld- oder Template-Änderungen sind Schemaänderungen: Anki verlangt dann laut Handbuch eine Einweg-Synchronisation, und ein Merge beim Import „will require a full sync“. Deshalb: wenige, gebündelte Schemaversionen; Migrationsplan, Wegwerftest mit echten Reviews (T5), Hinweis im Update-Bericht; keine Umwandlung Basis↔Lückentext (Importer lehnt Merge verschiedener Arten ab); keine Schemaänderung in der Prüfungswoche. CSS/Template-Text ohne Feldänderung ist keine Schemaänderung.

### 4.3 Medien (R8-POL-04)

Abbildungen erhalten einen kurzen Inhalts-Hash im Namen. Statische `_`-Dateien bekommen eine Version im Namen und werden bei Änderung umbenannt. Keine Symlinks (werden nicht synchronisiert), keine Unterordner. Ungenutzte Medien entfernen Lernende mit „Check Media“; die Engine löscht nichts. Ankis Check Media durchsucht keine Templates; `_`-Schriften bleiben dadurch unangetastet.

### 4.4 Ein kanonisches Modell, erzeugte Artefakte (R8-POL-05)

| Zone | Inhalt | Wer schreibt | Regel |
|---|---|---|---|
| kanonisch | Einheiten, Kompetenzen, Claims, Quellen, Kartenschlüssel | Engine | einzige Quelle der Wahrheit, versioniert im Kursordner |
| generiert | `Anki.apkg`, Update-Bericht, Markdown-Bereich, `.base` | Engine | nur nach Hash-Prüfung ersetzt; manuell geänderte Dateien → Konflikt |
| anwendungseigen | Anki-Sammlung, Revlog, Presets, Obsidian-`.obsidian` | Anki/Obsidian | Engine liest und schreibt nie |
| lernereigen | eigene Karten (eigener Notiztyp/Deck), Sidecar-Notizen | Lernende | Engine schreibt nie (Ausnahme: einmalige leere Vorlage, wenn Datei fehlt) |

Versionierung: Paket- und Markdown-Stände tragen `em_version` (Inhalts-Hash des kanonischen Modells) und Schemaversion. Die Engine erhöht die Notiz-Änderungszeit nur für Notizen im Delta (EF-4). Weil ein Update alle Felder einer generierten Notiz ersetzt, werden Lernende im Update-Bericht und in der Anleitung darauf hingewiesen: eigene Ergänzungen in eigene Notizen, nicht in generierte.

### 4.5 FSRS-Prozess (R8-POL-11)

Die Engine setzt nichts: kein FSRS-Schalter, keine Retention, keine Parameter, kein „Reschedule cards on change“, keine Presets im Paket. Anleitungstext (neutral, nach Handbuch): FSRS nur global; Standard-Retention 90 %; höher = deutlich mehr Reviews, Empfehlung unter 97 %; Parameter mit „Optimize“ aus eigener Historie, etwa monatlich; „Reschedule“ beim Umstieg von SM-2 nicht empfohlen, vorher Backup; nur Clients mit FSRS-Unterstützung (Anki/AnkiMobile 23.10+, AnkiDroid 2.17+, AnkiWeb); keine intervallverändernden Add-ons.

## 5. Minimaler praktischer Aufbau

1. Lernende installieren Anki selbst (Desktop; Mobilclient optional). Kein Add-on nötig.
2. Engine erzeugt pro Kurs `Anki.apkg` plus `Anki-Update.md` (neu/geändert/unverändert/Ausmusterung, Schemaversion, Medienänderungen, Einweg-Sync-Warnung, Sicherungshinweis).
3. Lernende importieren über Datei > Importieren. Empfohlene Optionen: Notizen „wenn neuer“ aktualisieren, Notiztypen „wenn neuer“, Merge nur bei angekündigter Migration, Lernfortschritt und Deck-Presets nicht importieren.
4. Wiederholung ausschließlich in Anki. Workbook nimmt Aufgaben kumulativ wieder auf (R1-POL-A05), ohne Kartenfälligkeiten.
5. Optional: Engine schreibt einen Markdown-Ordner (§6). Wer Obsidian nutzt, öffnet ihn als Vault oder als Unterordner eines bestehenden Vaults; keine Plugins, keine CLI, kein Konto.
6. Optional: eigene Karten in einem lernereigenen Notiztyp/Deck (R8-POL-13).

### 5.1 Was nicht zum Aufbau gehört

AnkiConnect, Obsidian-SRS-Plugins, Obsidian→Anki-Brücken, Obsidian Headless/CLI, AnkiWeb- oder Obsidian-Sync durch die Engine, Lesen der Nutzersammlung.

### 5.2 AnkiConnect nur unter Bedingungen (R8-POL-14)

Falls ein Bedienungstest zeigt, dass der manuelle Import merklich stört: Opt-in je Sitzung; Pflicht-`apiKey`; Bindung 127.0.0.1; Profilbestätigung durch Lernende; Client-Allowlist nur Lesen und `notes.create`/`notes.update` im Engine-Notiztyp; verboten: `scheduling.*`, `advanced.*`, Reviews-Import, `*.delete`, `profiles.switch`, `collection.sync`, `noteTypes.editStructure`; Sicherung vorher. Kein Auslesen von Review-Daten ohne R6-Entscheidung.

## 6. Generierter Obsidian-Bereich und Sidecar

### 6.1 Generierter Bereich (R8-POL-06)

Vorschlag (Namen sind Owner-Entscheidung 6):

```text
<Vault oder Ordner>/
  Mastery/                       # GENERIERT – wird ersetzt, nie von Hand bearbeiten
    00-Start.md
    10-Kurse/<kurs-id>.md
    20-Konzepte/<em_id>.md       # Dateiname = stabile ID, Titel als alias
    30-Quellen/<source-id>.md    # nur Metadaten/Locator, keine Kursinhalte
    90-Ansichten/*.base          # optional
    .mastery-manifest.json       # Hashes der generierten Dateien
  Mastery-Notizen/               # LERNEREIGEN – Engine schreibt nie
```

Frontmatter flach (Obsidian unterstützt keine verschachtelten Properties) und mit Präfix gegen Typkonflikte im Vault: `em_id`, `em_kind`, `em_version`, `em_generated: true`, `em_competencies` (Liste), `em_sources` (Liste), `em_cards` (Liste semantischer Kartenschlüssel), `aliases`. Inhalt: Kurzbeschreibung aus dem kanonischen Modell, Links zu Textbuchabschnitt, Workbook-Aufgaben, interaktiver Einheit und Kartenschlüsseln; **keine Fälligkeiten, kein Lesefortschritt** (MC-R2). Dateinamen sind IDs, damit Titeländerungen keine Links brechen. Schreiben atomar, nur nach Hash-Vergleich mit dem Manifest; geänderte Dateien werden nicht überschrieben, sondern als `.conflict` neben die neue Fassung gelegt. Der Ordner funktioniert ohne Obsidian.

### 6.2 Sidecar (R8-POL-07)

Eigene Notizen liegen in `Mastery-Notizen/` und verweisen per `[[<em_id>]]` oder Property `em_ref`. Die Engine kann einmalig eine leere Vorlage anlegen, nur wenn die Datei fehlt. Sidecar-Inhalte fließen nie automatisch ins kanonische Modell und werden nicht bewertet (SE-R2). Eine spätere Übernahme ist ein ausdrücklicher Vorschlag mit Diff.

### 6.3 Reversibilität

Optional heißt: ausgeschaltet = nichts geschrieben; Abschalten = Löschen von `Mastery/` genügt; Sidecars bleiben byte-gleich, fehlende Linkziele werden berichtet. Keine Änderung an `.obsidian/`, keine Plugin-Installation, keine Einstellungen.

## 7. Backup- und Konfliktpolitik

| Situation | Regel | Beleg |
|---|---|---|
| vor Import mit Schemaänderung, Merge oder großer Ausmusterung | Update-Bericht empfiehlt `.colpkg`-Export **mit Medien**; automatische Backups enthalten keine Medien | Backups-Handbuch |
| mehrere Geräte | vor dem Import alle Geräte synchronisieren; nach Schemaänderung Einweg-Sync bewusst in Richtung Desktop | Syncing „Conflicts“ |
| Einweg-Sync | Engine kündigt an, löst nie aus | Syncing |
| Ablage | Anki-Ordner nicht in Dropbox/iCloud/Netzlaufwerk | Managing Files |
| fehlgeschlagener Import | Wiederherstellung über „Open Backup“ bzw. `.colpkg`; spätere Änderungen gehen verloren | Backups |
| Markdown-Konflikt | nie überschreiben; `.conflict`-Datei, Bericht | R8-POL-05 |
| Engine-Stände | Pakete versioniert aufbewahren; ein älteres Paket ist reimportierbar (Inhalte; Reviews bleiben in Anki) | R8-POL-10 |
| Obsidian-Sync mit anderen Diensten | Obsidian empfiehlt Backup bzw. vollständige Migration; Engine schreibt Manifest außerhalb synchronisierter App-Ordner | Obsidian Sync |

## 8. Testplan mit Wegwerfprofilen (R8-POL-08)

**Grundsatz:** Kein Test berührt den Standarddatenordner (macOS `~/Library/Application Support/Anki2`, Windows `%APPDATA%\Anki2`, Linux `~/.local/share/Anki2`), ein vorhandenes Profil oder einen privaten Vault. Automatische Tests: neue Sammlung in einem temporären Verzeichnis über die offizielle `anki`-Bibliothek. Sichtprüfung am Desktop: `anki -b <neuer temporärer Ordner>` (oder `ANKI_BASE`), ohne AnkiWeb-Anmeldung. Ein Pfadwächter bricht ab, wenn ein Zielpfad unter einem Standarddatenordner liegt. Reviews werden über den Scheduler beantwortet, nicht per SQL (EF-7), je einmal mit SM-2 und mit FSRS.

| Test | Ablauf | Bestanden, wenn |
|---|---|---|
| T1 Erstimport | Paket in leere Wegwerfsammlung | Notiz-/Kartenzahl stimmt; Notiztyp-IDs = Konstanten; Medien vorhanden; keine Revlog-/Preset-Daten |
| T2 Idempotenz | unverändertes Paket erneut exportieren und importieren | 0 Updates (nach EF-4-Korrektur), keine Duplikate |
| T3 Inhaltsupdate | 20 Karten über den Scheduler beantworten (SM-2 und FSRS), eine Karte inhaltlich ändern, reimportieren | Karten-IDs, due, ivl, Revlog, FSRS-Gedächtniszustand identisch; nur die geänderte Notiz aktualisiert |
| T4 Umbenennung | Einheitstitel und Notiztyp-Anzeigename ändern | gleiche Notiztyp-ID, 0 `conflicting`, Karten im bisherigen Deck, Historie unverändert |
| T5 Schemamigration | Feld hinzufügen nach Migrationsplan | kein Duplikat-Notiztyp, keine Kartenverluste, Revlog unverändert; Schemaänderung der Sammlung protokolliert (Einweg-Sync zu erwarten) |
| T6 Verschieben | Karte per Identitätszuordnung in andere Einheit | gleiche GUID, Historie erhalten |
| T7 Medien | Abbildung und Schrift ändern | neue Inhalte sichtbar; Check Media ohne fehlende Dateien |
| T8 Lokale Bearbeitung | generierte Notiz in Anki bearbeiten, Tags `marked`/`leech` setzen, Update einspielen | dokumentiert, was verloren geht (erwartet: Felder); Tag-Verhalten gemessen (offene Lücke) |
| T9 Wiederherstellung | `.colpkg` mit Medien exportieren, fehlerhaften Import simulieren, wiederherstellen | Sammlung inhaltsgleich zum Vorzustand |
| T10 AnkiConnect (nur nach Freigabe) | Client gegen Anki mit `-b` Wegwerfordner | verbotene Methoden werden clientseitig abgewiesen; ohne Schlüssel kein Zugriff |
| T11 Darstellung | Wegwerf-Desktop, Light/Dark, 320/390 px | keine Überläufe, Formeln/Abbildungen lesbar |
| T12 Mobilclients | AnkiDroid mit frischem Profil (manuell, außerhalb CI); AnkiMobile nur mit Testgerät | T3/T7 sinngemäß; Ergebnis getrennt berichtet |

| Vault-Test | Ablauf | Bestanden, wenn |
|---|---|---|
| V1 Erzeugen | in leeren temporären Ordner | Dateiliste und flaches Frontmatter mit `em_`-Präfix |
| V2 Idempotenz | erneut erzeugen ohne Änderung | keine Schreibvorgänge, Dateien byte-gleich |
| V3 Sidecar-Schutz | Sidecar anlegen, regenerieren, `Mastery/` löschen und neu erzeugen | Sidecar byte-gleich; fehlende Linkziele berichtet |
| V4 Konflikt | generierte Datei von Hand ändern, regenerieren | Datei nicht überschrieben; `.conflict` erzeugt |
| V5 Titeländerung | Konzepttitel ändern | Dateiname stabil; Alias aktualisiert; Links aus Sidecars lösen auf |
| V6 Pfadwächter | Ziel außerhalb `Mastery/` bzw. in `.obsidian/` | Abbruch ohne Schreibvorgang |

## 9. Gegenargumente zum Standard

| ID | Gegenargument | Gewicht | Umgang |
|---|---|---|---|
| G1 | Selbst erstellte Karten wirken besser als vorgefertigte (Pan 2023: d = 0.45 Gedächtnis, d = 0.29 Anwendung, 48 h, sechs Experimente) – ein generiertes Deck könnte schlechter sein als eigene Arbeit | ernst; einzige direkte Lernevidenz in R8 | R8-POL-13: generativer Weg optional; Zeitkosten benennen; Vergleich als Studie vorgemerkt |
| G2 | Integrierte Systeme (RemNote, Decks-Plugin) vermeiden Kontextwechsel; Decks importiert sogar Anki-Historie, ein Wechsel ist also technisch möglich | mittel | kein Lernbeleg, Plugin-/Cloud-Risiken, zweiter Scheduler; Wiedervorlage nur bei Studie und AD-1-Änderung |
| G3 | Die Obsidian-Ansicht dupliziert das Textbuch und hat keinen belegten Nutzen | ernst | nur gewöhnlicher Ordner, standardmäßig aus; Owner-Entscheidung 1 erlaubt Verzicht ganz |
| G4 | Manueller .apkg-Import ist Reibung; AnkiConnect wäre „automatisch“ | mittel | erst messen; dann nur unter §5.2 |
| G5 | FSRS gewinnt Benchmarks – also standardmäßig einschalten | schwach | Benchmark ≠ Lernen; MOVING-AVG nahe FSRS-7 recency; Engine bleibt neutral |
| G6 | Anki hängt an einem kleinen Kernteam; Mobilzugang hat Hürden (Kosten/Bedienung nicht geprüft) | mittel | AGPL-Quelltext, offenes Paketformat, Text-Import als Rückfall; Mobilprüfung T12 |
| G7 | Generierte Karten können Bedingungen zerstören (Atomisierung) | mittel | Kartenregeln der Engine (C1–C5) und R1-POL-A01; keine neuen Kartenregeln ohne Beleg |

## 10. Nicht-Ziele

Kein eigener Scheduler, keine zweite Warteschlange, keine Intervall- oder Retentionsvorgaben. Kein Lesen oder Schreiben der Nutzersammlung, keine Auswertung von Review-Daten. Keine Pflicht-Plugins, kein Obsidian-Konto, keine bezahlte Sync-Abhängigkeit. Keine bidirektionale Synchronisation von Markdown-Änderungen ins kanonische Modell. Kein fünftes Produkt: die Markdown-Ansicht ist eine Exportansicht. Keine Visualisierungsbewertung (R7). Keine Tutorbewertung (R9).

## 11. Risiken

- Identitätskorrekturen (EF-1/EF-2) können bestehende Testdecks einmalig brechen; Owner muss zwischen Einfrieren und einmaligem Bruch vor Freigabe wählen.
- Mobilclients können vom Desktop-Importer abweichen (nicht geprüft).
- `update_tags` könnte lokale Tags wie `leech` ersetzen (offen).
- Lernende bearbeiten generierte Karten trotz Hinweis und verlieren Änderungen.
- Obsidian-Property-Typen sind vault-weit; Konflikte mit bestehenden Vaults trotz Präfix möglich.
- Der generative Weg (POL-13) kostet Zeit und kann fehlerhafte Karten erzeugen.
- Die Werkzeuglandschaft ändert sich schnell (Obsidian CLI/Headless Beta, Logseq DB Beta, FSRS-7); Karten veralten.

## 12. Was wir nicht behaupten

Dass FSRS, Anki oder irgendeine Alternative Lernen verbessert. Dass die Obsidian-Ansicht oder Sidecar-Notizen Lernen verbessern. Dass Benchmarkwerte Kompetenz oder Lernerfolg messen. Dass die gelesenen Quelltextstellen das Verhalten aller Clients beschreiben. Dass irgendein Workflow funktioniert: nichts wurde ausgeführt. Dass Pan et al. auf verteilte Anki-Wiederholung über Wochen übertragbar ist. Keine Qualitätsbewertung früherer Produkte; diese bleiben HUMAN_REJECTED.

## 13. Owner-Entscheidungen

1. Standard annehmen: Anki als einziger Scheduler + gewöhnlicher Markdown-Ordner, Obsidian nur optional; oder Markdown-Ansicht ganz weglassen (G3).
2. Notiztyp-IDs: heutige Werte als Konstanten einfrieren und Anzeigenamen entkoppeln (empfohlen) oder neue IDs mit Migration.
3. GUID-Schema: Kapitel-Slug entfernen und Identitätszuordnung einführen; einmaliger Bruch vor erster Freigabe akzeptabel?
4. Generativer Weg (R8-POL-13): Vorlage „Eigene Karte“ und Workbook-Formulierungsaufgaben anbieten? Spätere Obsidian→Anki-Brücke für eigene Karten prüfen?
5. AnkiConnect zurückgestellt lassen, bis ein Bedienungstest des manuellen Imports vorliegt?
6. Ordnernamen und Frontmatter-Felder des generierten Bereichs; `.base`-Ansichten erzeugen ja/nein.
7. Umfang der Mobilprüfung (AnkiDroid, AnkiMobile) vor einer Freigabe.
8. Bestätigung, dass die Markdown-Ansicht kein fünftes Produkt ist.

## 14. Fragen an Reviewer

1. Ist die Lesart des Importers korrekt (GUID-Abgleich, `conflicting` bei anderer Notiztyp-ID, keine Aktualisierung vorhandener Karten, `_`-Medien übersprungen)?
2. Ersetzt `update_tags: true` lokale Tags oder führt es zusammen?
3. Isoliert `anki -b` auch AnkiWeb-Anmeldedaten und Add-ons vollständig?
4. Ist Pan et al. 2023 zeitangeglichen, und wie groß ist der Zeitaufwand der Kartenerstellung? Gibt es Replikationen?
5. Ist `normative` als Sicherheitsstufe für Datenerhalt-Policies angemessen, oder verdeckt es fehlende Evidenz?
6. Ist die Deutung von MOVING-AVG im srs-benchmark richtig (Kalibrierung, nicht Planungsqualität)?
7. Fehlt eine ernsthafte Alternative (z. B. Anki-Forks, Quizlet, Hashcards)?
8. Sind die Engine-Befunde EF-1 bis EF-8 vollständig und richtig?

## 15. Reproduktion

Ohne Installation, ohne Anki/Obsidian, ohne bezahlte Aufrufe:

```sh
gh issue view 30
gh api repos/ankitects/anki/releases/latest -q '.tag_name+" "+.published_at'
for f in notes cards media decks; do
  gh api "repos/ankitects/anki/contents/rslib/src/import_export/package/apkg/import/$f.rs" -q .content | base64 -d | grep -n -E "guid|fn |is_static|TODO"
done
gh api repos/FooSoft/anki-connect/contents/API_V1.md -q .content | base64 -d | grep -n -E "apiKey|Bearer|Scheduling"
gh api repos/open-spaced-repetition/srs-benchmark/readme -q .content | base64 -d | sed -n 99,135p
curl -s https://api.crossref.org/works/10.1037/mac0000083 | python3 -m json.tool | head -40
git show origin/integration/quality-recovery-20261126:exam_mastery/anki_v2.py | sed -n 79,112p
cd tests && python3 -m unittest test_r8_workflows test_r1_learning_policies
```

Handbuchseiten: URLs im Register (`access.url`); je Seite einmal abgerufen am 27.11.2026.

## Anhang A — Implementierungsauftrag für einen Coding-Agenten (gesperrt)

**Erst nach** Owner-Annahme dieses Berichts (Owner-Entscheidungen 1–6 dokumentiert) und wenn R6 nichts Widersprechendes festlegt. Vorher nicht starten.

```text
Rolle: Engineering-Agent im Repository Sven-Lutz/Exam_Mastery.
Voraussetzung: Owner hat R8 (docs/research/workstreams/R8_ANKI_OBSIDIAN_WORKFLOWS.md) angenommen;
Entscheidungen 1–6 sind in NEXT_ACTION.json bzw. im Programmzustand vermerkt. Fehlt das: STOPP.
Kein aktiver Engine-Lauf (supervisor.py status prüfen). Keine bezahlten Aufrufe. Keine Installation
außer der bereits deklarierten anki-Python-Abhängigkeit. Nie den Standarddatenordner von Anki,
ein Nutzerprofil oder einen privaten Vault lesen oder schreiben.

Basis: aktueller Integrationszweig mit exam_mastery/anki_v2.py, learning/experience_anki.py,
learning/experience.py. Eigener Branch, ein Draft-PR, keine Merges.

Aufgaben:
1. Identität (R8-POL-02): Notiztyp-, Feld- und Template-IDs als Konstanten (heutige Hash-Werte
   eingefroren, sofern Owner-Entscheidung 2 nichts anderes sagt); Anzeigename entkoppelt.
   GUID = Hash(Kurs-ID, semantischer Schlüssel) gemäß Owner-Entscheidung 3, plus versionierte
   Identitätszuordnung für Verschiebungen. Deckname nicht identitätsrelevant.
2. Änderungszeit nur für Notizen im Delta setzen (EF-4).
3. Medien (R8-POL-04): Inhalts-Hash im Abbildungsnamen; versionierte _-Schriftdateien.
4. Update-Bericht (R8-POL-09/10): neu/geändert/unverändert/Ausmusterung, Schemaversion,
   Medienänderungen, Einweg-Sync-Warnung, Sicherungshinweis (.colpkg mit Medien).
5. Notiztyp-Filter in Tests über IDs (EF-8).
6. Optionaler Markdown-Bereich (R8-POL-06/07) gemäß Owner-Entscheidung 6: Manifest mit Hashes,
   atomare Schreibvorgänge, .conflict statt Überschreiben, Pfadwächter, Sidecar-Ordner nie schreiben.
7. Tests T1–T9 und V1–V6 aus §8, ausschließlich in Wegwerfprofilen bzw. temporären Verzeichnissen; Reviews über den
   Scheduler (SM-2 und FSRS), nicht per SQL. Pfadwächter-Test, der den Standarddatenordner ablehnt.

Nicht tun: kein Scheduler, keine Intervalle, keine Presets, kein AnkiConnect, keine Obsidian-
Plugins/CLI/Headless, kein Lesen von Review-Daten, keine Änderung an Produktaussagen zur Wirkung.

Abnahme (technisch, nicht didaktisch): alle neuen Tests grün; bestehende Anki-Tests grün;
learning_evaluation bleibt NOT_RUN; menschliche Abnahme bleibt offen. Bericht im PR mit
Befehl, Datum und Ergebnis je Test. Bei jedem Hinweis auf Zugriff außerhalb temporärer Ordner: STOPP.
```
