# Mastery — Marken-Phase B: Bestandsaufnahme, Kompatibilitäts- und Risikomatrix

Stand 27.11.2026. Grundlage: Owner-Entscheidung [#34](https://github.com/Sven-Lutz/Exam_Mastery/issues/34). **Nur Plan, keine Umbenennung.** Dieser PR ändert keinen Code, keine Ausgabe, keine Kennung und keinen Lernverlauf.

## 1. Entscheidung und Nicht-Ziele

- **Produktidentität:** *Mastery* (vormals *Exam Mastery*), eine allgemeine Plattform für Wissens- und Fertigkeitserwerb. Prüfungsvorbereitung ist ein optionaler Lernmodus. Daraus folgt keine Zertifizierung physischer oder klinischer Fertigkeiten aus Simulationen.
- **Phase A ist erledigt** (27.11.2026, Programmzustand `docs/programme/PROGRAMME_STATE.json` auf `ops/programme-control-20261127`, Architekturentscheidung AD-3; Scope-Hinweis in R1, PR #35).
- **Phase B (dieses Dokument):** Bestandsaufnahme und Plan; Darstellungsänderungen nur dort, wo sie nachweislich nichts brechen.
- **Phase C:** technische und Repository-Migration nur nach gesonderter Owner-Freigabe.
- **Nicht in Phase B:**
  - kein Umbenennen von Python-Modul, CLI, Agent-Skill, Umgebungsvariablen oder Datenverzeichnissen;
  - keine Änderung an Anki-Deck- und -Notiztypnamen oder GUIDs;
  - keine Änderung an Schemas, Kompetenz-IDs, launchd-Labels, Worktree-Pfaden oder dem GitHub-Repo;
  - keine öffentliche kommerzielle Namensnutzung vor einer Markenprüfung.

## 2. Bestand (zählt Textvorkommen ohne JSON)

| Muster | `main` | Golden-Linie (#28) | lokaler RL-Pilot `f536fd5` | Art |
|---|---|---|---|---|
| `Exam Mastery` (Anzeige) | 80 in 41 Dateien | 90 in 47 | 94 in 53 | überwiegend Darstellung, einige gekoppelt (siehe 3) |
| `Exam_Mastery` | 24 / 12 | 25 / 13 | 38 / 22 | Repo- und Ausgabepfade (`~/Exam_Mastery_Output`) |
| `exam-mastery` | 206 / 46 | 211 / 49 | 228 / 51 | CLI, Agent-Skill, Verzeichnisse, Cache-Namen |
| `exam_mastery` | 707 / 121 | 767 / 137 | 793 / 155 | Python-Paket und Importe |
| `EXAM_MASTERY_*` | 28 / 17 | 28 / 17 | 28 / 17 | Umgebungsvariablen (10 verschiedene, siehe 3) |

Die drei Linien unterscheiden sich; jede Darstellungsänderung jetzt auf `main` erzeugt Konflikte mit dem ungemergten Stack #11–#19/#28 und dem RL-Pilot (die Linien teilen u. a. `typeset.py`, `figures_svg.py`). Deshalb ist Phase B hier **nur Dokumentation**.

## 3. Kompatibilitäts- und Risikomatrix

Klassen: **D** reine Darstellung, nach Integration sicher änderbar · **K** gekoppelt (Code, Tests oder Nutzerdaten hängen am Text) · **I** Identität (Änderung bricht Installationen, Lernverläufe oder Automatisierung) → Phase C.

| Bereich | Beispiele (Golden-Linie) | Klasse | Risiko bei Änderung | Vorgehen |
|---|---|---|---|---|
| Lernumgebung, HTML-Titel, Navigation | `labs/build.py` Nav/Footer, `learning/interactive_reference.py` Titel/Eyebrow, `runtime.py` `START.html`, `publish.py`, `campaign.py` | D | Ausgaben werden neu gerendert; „UNCHANGED“-Zweitlauf einmalig verletzt | nach Integration über eine zentrale Anzeigekonstante ändern |
| PDF-Metadaten | `typeset.py` (`author`, `creator`, Kopfzeile „Exam Mastery {engine}“), `chapter_publish.py`, `figure_status.py`, `scientific_visuals.py` | D | Bytegleichheit veröffentlichter PDFs ändert sich einmalig | wie oben, gemeinsam mit einem Versionssprung |
| Tutor-Texte | `learning/tutor.py` Überschrift, `templates/em_app.js` Tutor-Briefing | D | keiner funktional | wie oben |
| Fehlermeldungen | `product.py` („not an Exam Mastery product config“) | D | Tests könnten Text prüfen | mit Testanpassung |
| PDF-Seitenerkennung | `editorial.py`: sucht den Text „Exam Mastery - learning figure“ in PDF-Seiten | **K** | Erkennung der Figurenseiten bricht still | Erzeugung und Erkennung gemeinsam auf eine Konstante umstellen, mit Regressionstest |
| Anki-Notiztypen | `anki_v2.py`: „Exam Mastery · Basis (v2)“, „Exam Mastery · Lückentext (v2)“, Filter `startswith('Exam Mastery')`; `anki_qa.py` „Exam Mastery Basic v1“ | **I** | neuer Notiztyp oder nicht gefundener Typ beim Update; Konflikte im Import; Gefahr für Reviewverlauf | Phase C mit Import-Test auf echter Kopie: gleiche Notiztyp-IDs, Umbenennung nur des Anzeigenamens, Filter auf IDs umstellen |
| Anki-Decks | `chapter_publish.py`, `experience_anki.py`, `learning/anki_bridge.py`: `Exam Mastery::…` | **I** | Karten landen in neuem Deck oder bleiben im alten; Nutzerfilter brechen | Phase C; nur mit getestetem Reimport (Review-Historie, Fälligkeiten, Deckzuordnung) |
| Python-Paket, CLI, Skill | `exam_mastery`, `exam-mastery`, Skill `/exam-mastery`, `start` | **I** | bricht Installationen, Skill-Aufrufe des Owners, Codex-Links | Phase C: Alias zuerst (`mastery` → bestehender Einstieg), alter Name bleibt |
| Umgebungsvariablen | `EXAM_MASTERY_CONFIG`, `_OUTPUT`, `_PYTHON`, `_CALL_LEDGER`, `_PYTHON_BUILD`, `_HOME`, `_PYTHON_ENV`, `_FONT`, `_FONT_BOLD`, `_CAMPAIGN_COURSE` | **I** | bestehende Konfigurationen, Skripte und Ledger laufen ins Leere | Phase C: neue Namen nur als Alias mit Vorrang der alten |
| Datenverzeichnisse | `~/.config/exam-mastery`, `~/.local/share/exam-mastery(-backups)`, `~/Exam_Mastery_Output`, `~/.cache/exam-mastery*` | **I** | Datenverlust oder Doppelbestände | Phase C: Lesen beider Orte, keine automatische Verschiebung |
| Programmsteuerung | launchd `dev.exam-mastery.programme-supervisor`, `~/.local/state/exam-mastery-autonomy`, Worktrees `Exam_Mastery-*` | **I** | laufende autonome Fortsetzung bricht | unverändert bis Phase C; dann Agent ausbauen, umbenennen, neu testen |
| Schemas und IDs | `em-*`-Schemas, Kompetenz-/Inhalts-IDs, `em_*`-Templates | **I** | Reproduzierbarkeit, Provenienz | nie umbenennen; „em“ bleibt neutrales Kürzel |
| Repository | `Sven-Lutz/Exam_Mastery` | **I** | GitHub leitet die meisten URLs um, aber nicht jede Integration (u. a. Actions-Bezüge) | nur mit Owner-Freigabe, sauberem Zustand und Prüfliste |
| Doku | `README.md`, `ENGINE_README.md`, `release/*.md`, `docs/*` | D | keiner | vorwärtsgerichtete Prosa nach Integration anpassen; historische Berichte unverändert |
| Kommentare in CSS/JS | `templates/em_*.css/js` | D | keiner | nicht nötig |

## 4. Umsetzungsplan

1. **Jetzt (dieser PR):** Matrix und Plan. Keine Codeänderung.
2. **Nach der Integration des Draft-Stacks (P4):**
   - eine Anzeigekonstante (z. B. `PRODUCT_NAME = "Mastery"`, `LEGACY_NAME = "Exam Mastery"`) für alle Zeilen der Klasse D;
   - die gekoppelte Seitenerkennung (K) gemeinsam mit ihrer Erzeugung umstellen, abgesichert durch einen Regressionstest;
   - README und vorwärtsgerichtete Doku anpassen;
   - einmaliger Neuaufbau der Referenzen mit dokumentierter Bytedifferenz.
3. **Phase C (Owner-Freigabe):** Aliase für CLI, Skill und Umgebungsvariablen. Lesen alter und neuer Datenorte. Anki-Migration nur nach einem Import-Test auf einer Kopie einer echten Sammlung, der Review-Historie, Fälligkeiten und Deckzuordnung prüft. Danach optional die Umbenennung des Repositorys anhand einer Prüfliste (Actions, Remotes, Links, installierte Clients, launchd).

## 5. Abnahmekriterien aus #34 und Stand

| Kriterium | Stand |
|---|---|
| 1. Dokumentierte Entscheidung ohne Konflikt mit dem Forschungsprogramm | erfüllt: AD-3 im Programmzustand, R1-Hinweis, dieses Dokument |
| 2. Sicherer, nicht brechender Plan; keine erzwungenen Umbenennungen | erfüllt durch Abschnitt 4; nichts umbenannt |
| 3. Scope-neutrale Kompetenztaxonomie, Prüfung als optionaler Modus | an R6 übergeben (Arbeitspaket WP-R6, Hinweis im Programmzustand); Prüfungsziele bleiben erhalten |
| 4. Risiko- und Migrationsinventar | erfüllt durch Abschnitte 2–3 |
| 5. Kein Datenverlust, kein stiller Reset der Review-Historie, keine Unterbrechung der autonomen Fortsetzung | durch Nicht-Änderung gewährleistet; Phase C nur mit Import-Test |
| 6. Owner-Folgeschritte nur bei Irreversiblem, Öffentlichem oder Rechtlichem | siehe 6 |

## 6. Owner-Entscheidungen (nur diese)

1. **Öffentlicher Name:** „Mastery“ kollidiert mit bestehenden Bildungs- und KI-Apps (Signal, keine Rechtsbewertung). Vor öffentlicher oder kommerzieller Nutzung sind Marken-, Kategorie- und Territoriumsrecherche (EUIPO TMview, DPMA, WIPO) und eine Domain-/App-Store-/GitHub-Namensprüfung nötig. Ein Agent kann diese Recherche vorbereiten, nicht entscheiden.
2. **Phase C insgesamt:** Freigabe für Aliase, Anki-Migration und Datenorte.
3. **Repository-Umbenennung:** gesonderte Freigabe nach Prüfliste.
