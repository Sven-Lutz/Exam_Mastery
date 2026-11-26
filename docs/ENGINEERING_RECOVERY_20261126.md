# Engineering-Integration und Qualitätsbefund, 26.11.2026

Status: technische Entwicklungskandidatur; **keine akademische oder menschliche Abnahme**.
Die historischen NLP-Versionen bleiben HUMAN_REJECTED. Synthetische Referenzen sind neue,
nicht abgenommene Testobjekte. Kein Modellaufruf für diese Arbeit, keine Gebühren-API,
keine Vorlesungsdateien oder Lernerdaten in diesem Patch.

## Verifizierter Bestand

- `main`: `5b646840a85b98518034e872f0b041081a60cdb9`.
- PR #18: `9ac7206e86e1ca68824c5d52da7a1359aea09aa3`.
- PR #11–#18 bilden einen durchgängigen Vorfahren-Stack; alle acht Heads liegen in
  #18. Nicht in main integriert. #18 hatte einen erfolgreichen PR-Workflow
  `44882095275`; das ist technische Evidenz, keine Inhaltsabnahme.
- Integration: `integration/quality-recovery-20261126`, separater Worktree.
- Vorhandener lokaler Pilot: `feat/rl-engine-pilot`, `f536fd5`, sauber, zehn Commits
  vor seinem Remote. Gemeinsamer Vorfahr mit #18 ist main; er ist **kein** Vorfahr
  des Stacks. Er enthält zusätzliche B35/B36-Orakel-, Argument-, Layout- und
  RL-Arbeit. Kein automatischer Merge oder Push dieses umfangreichen historischen
  Materials; Branch und Originalcheckout bleiben unverändert erhalten.
- Weitere lokale Studio- und archivierte Engine-Quellen existieren ohne eigenes
  Git-Checkout an den untersuchten Studio-Wurzeln. Der installierte Stand wurde
  laut `~/.local/share/exam-mastery/RETIRED.txt` am 23.11. stillgelegt; Quellcode
  verbleibt im Archiv. Dateivergleich bestätigt abweichendes typeset.py.
  Diese Bestände wurden nicht überschrieben, gelöscht oder öffentlich importiert.

## Implementierte Korrekturen

1. **Prozessabbruch beim Publizieren:** Der alte Recovery-Ordner enthielt nur
   Sicherungsdateien, aber keine Transaktionszuordnung. Ein Abbruch hinterließ
   neue Produkte neben alter Metadatenintegrität; der nächste Lauf meldete eine
   angebliche manuelle Änderung. Jetzt werden alle alten verwalteten Dateien und
   ein Journal mit Vorher-/Nachher-Hashes vor dem ersten Austausch gespeichert.
   `experience recover <Ausgabeordner>` prüft alle Quellen und Ziele vor der
   ersten Änderung und stellt den vorherigen Stand wieder her. Unbekannte
   Änderungen, Traversalpfade, umgeleitete Sicherungen und mehrdeutige Journale
   blockieren. Backups werden beim Wiederherstellen kopiert, nicht verbraucht.
   Builds verweigern offene Recovery-Vorgänge ausdrücklich. Normale Fehler
   behalten den bestehenden In-Process-Rollback.
2. **Veraltete PDF-/Anki-Caches:** Unveränderte Inhalts-JSON führte trotz
   geändertem Renderer/CSS zum Rückgabewert UNCHANGED. Cache-Schlüssel binden
   jetzt Code, Templates, lokale Fonts, MathJax (PDF) und relevante Paketversionen
   ein. Pfadnamen und Zeitstempel sind kein Bestandteil. Anki-GUIDs bleiben aus
   stabilen semantischen IDs abgeleitet.
3. **Leere Arbeitsbuchseiten:** Der Vierproduktadapter setzte vor jeder Stage
   einen Seitenumbruch, auch unmittelbar hinter einer Teilüberschrift. Er nutzt
   jetzt die bestehende `.stage.first`-Regel für die erste Aufgaben- und
   Lösungsstage. PDF-Regression prüft Teilüberschrift zusammen mit erster Aufgabe.
4. **Metadata-Sicherheit:** Gesamtpreflight prüft verwaltete Pfade und Metadaten
   vor dem Laden der Publisher-Manifeste auf umgeleitete/nichtreguläre Einträge.
5. **Reproduzierbare Referenzprüfung:** Ein Skript erzeugt drei synthetische
   Vierproduktpakete, macht einen zweiten unveränderten Lauf, rendert jede
   PDF-Seite, prüft Offline-HTML bei 390/1280 Pixeln, Fragmentziele und JS-Fehler
   sowie echte Anki-Templatevorschauen bei 390 Pixeln. Artefakte bleiben außerhalb
   des öffentlichen Repositorys. Neuer Finanzfall: Zeitpunkte und endliche
   Diskontierung; direkte Decimal-Summe prüft den vorhandenen Rückwärtsalgorithmus.

## Unabhängige Qualitätsuntersuchung: konkrete Ursachen

| Bereich | Befund am ausführbaren Pfad | Klasse / Konsequenz |
|---|---|---|
| Autorenschaft | Experience Core verarbeitet bereits geschriebene `teaching.content`, `solution`, `cards`; es erzeugt keine wissenschaftlich tiefe Prosa aus Quellen. | Autorenschaft: synthetische Builds belegen Rendering, keine automatische hochwertige Kursproduktion. |
| Mathematik | `experience_proof_checks` prüft beschränkte Polynomgleichheiten. Die binomische Referenz ist elementar; Textbegründungen und Voraussetzungen werden dadurch nicht bewiesen. | Wissenschaft: für einen Master-Level-Golden-Reference fehlen anspruchsvollere Inhalte und Fachprüfung. |
| Abbildungen | `experience_books.book_model` liefert `figures={}`. Die gekoppelte Flächenzerlegung der App gelangt nicht in das PDF. | Integration/Design: im tatsächlich gerenderten Geometrie-Lehrbuch fehlt die zentrale erklärende Grafik. Offen, nicht durch weitere Validatoren gelöst. |
| Formeln | Offline-HTML zeigt geprüfte Gleichungen als präformatierte Parserausdrücke (`*`, `^`), PDF nutzt MathJax. | Rendering: lesbar, aber keine gemeinsame hochwertige mathematische Darstellung. |
| Aufgaben | Adapter übernimmt vorhandene Lösungen; alle Items werden unter einer gemeinsamen Stage geführt. | Lernprozess/Autorenschaft: keine automatisch entworfene sinnvolle Progression oder geprüfte Aufgabenvielfalt. |
| Anki | Native APKG und rationale/source-Felder sind tatsächlich implementiert. Unveränderte JSON maskierte aber Templateverbesserungen; Cachefehler behoben. | Integration: jetzt reales Reimport-Testsignal statt bloß identischer Hashformel. Mobile Clients bleiben ungeprüft. |
| Lernzustand | Export enthält Handlungen, keine Antworttexte; Sitzung liegt im RAM, kein Resume-Import. | Lernprozess: Reload verliert den aktiven Zustand. Export ist keine Wiederaufnahme. Offen. |
| Forschung | Claim-/Source-IDs und Locator werden übertragen; kein unabhängiger semantischer Literaturreview in diesen synthetischen Builds. | Wissenschaft/QA: bibliografische/strukturelle Validierung ersetzt kein Lesen und Bewerten der Belegstelle. |
| Historische Ablehnung | Issues #4–#10 nennen schlechte Herleitungen, fehlende Tiefe, Rendering und Lernaufgaben; CI prüfte vor allem Struktur und Beispiele. | Qualitätskontrollen: die Prüfinstrumente maßen andere Eigenschaften als die menschliche Abnahme. Die Ablehnung bleibt bestehen. |

Visuell inspiziert: Geometrie-PDF mit Herleitung, mobiles Offline-HTML,
Anki-Rückseite im Dunkelmodus, Finanz-Arbeitsbuchseite vor Korrektur. Nach der
Korrektur werden die Referenzen erneut erzeugt und die korrigierten Seiten
kontrolliert. Vorschauen verwenden Ankis Template-Engine plus Chromium;
kein Beleg für tatsächliche AnkiMobile-/AnkiDroid-Darstellung.

## Reproduktion

Python 3.12, Node und die bereits genutzten lokalen MathJax-/Fontpakete erforderlich.

```sh
python3.12 -m venv .venv
.venv/bin/pip install -e '.[qa]' pytest
.venv/bin/python -m playwright install chromium
npm install --prefix ~/.cache/exam-mastery-v05-node --save-exact mathjax-full@3.2.2 @fontsource/source-sans-3@5.1.0 @fontsource/source-serif-4@5.1.0 @fontsource/jetbrains-mono@5.1.0
.venv/bin/python scripts/verify_experience_references.py --out /tmp/em-reference-evidence
.venv/bin/python -m exam_mastery.cli experience recover /tmp/em-reference-evidence/experience_reference
```

Einstiege: `<out>/experience_{binomial_reference,reference,finance_reference}/Interaktiv/index.html`;
jeweils daneben `Lehrbuch.pdf`, `Arbeitsbuch.pdf`, `Anki.apkg`. Evidenz unter
`<out>/review/`, Zusammenfassung `<out>/report.json`.
Die Wiederherstellung betrifft ausschließlich einen unterbrochenen Publish,
nicht private Anki-Sammlungen oder Lernprotokolle.

## Offene P0/P1 nach Wirkung

- **P0 Produkt:** unabhängige fachliche, didaktische und menschliche Abnahme fehlt;
  kein positiver Golden-Reference-Befund. Tiefe, Visual Storytelling und anspruchsvolle
  neue Aufgaben sind nicht durch diesen Engineeringpatch gelöst.
- **P1 Publikation:** keine atomare Sichtbarkeit der ganzen Dateigruppe, keine
  Stromausfallgarantie/fsync-Kette, kein exklusiver Mehrprozess-Publisher-Lock.
  Hashvergleich schützt beobachtete Änderungen, beseitigt aber nicht jedes Race.
- **P1 Integration:** moderne lokale B35/B36-Arbeit und GitHub-Semantikstack sind
  getrennte Entwicklungslinien; selektive Portierung mit gezielter Prüfung nötig.
- **P1 Lernbetrieb:** dauerhafter, versionierter Resume-Import fehlt; keine
  Kompetenzbehauptung aus Selbstbericht, Ziffernantwort oder unterstütztem Versuch.
- **P1 Produktintegration:** statische Erklärgrafiken und typografische Formeln
  mediengerecht aus demselben Modell; echte Clientmatrix für Anki.
- **P1 Wissenschaft:** Belegstellen semantisch prüfen, Autorensollwerte unabhängig
  validieren, anspruchsvollere Beweise und Lernwirksamkeit getrennt untersuchen.
- **P1 Coding:** kein sicherer ausführbarer Coding-Workspace implementiert; der
  bestehende deklarative Trace/Parsons-Pfad ist kein Sandbox-Runner.

Nächster sinnvoller Meilenstein: eine anspruchsvolle synthetische Referenz mit
vollständiger Herleitung, gekoppelten statischen/dynamischen Grafiken, progressiven
Aufgaben und unabhängiger Fachprüfung; zuvor Publisher-Lock und State-Resume
gezielt schließen. Ein begrenzter technischer Referenzlauf ist möglich. Ein
akademischer Golden-Reference-Produktionslauf ist noch **nicht freigabereif**.

## Ausgeführte Prüfungen

- Gezielte CI-Integrationssuite: **185 bestanden**, keine Fehler/Skips, 14,40 s.
  Befehl:
  `.venv/bin/python -m pytest -q tests/test_experience_core.py tests/test_experience_evidence.py tests/test_experience_adaptation.py tests/test_experience_misconceptions.py tests/test_experience_proof_checks.py tests/test_interactive_reference.py tests/test_experience_anki.py tests/test_experience_books.py tests/test_experience_pipeline.py`.
- Bestehende Gesamtregression: `.venv/bin/python -m unittest discover -s tests`:
  **632 ausgeführt, OK, 6 übersprungen**, 348,077 s. Sechs Skips sind keine
  bestandenen Tests. Warnungen zu offenen Testdateien und erwartete asynchrone
  Exceptions in Negativtests bleiben technische Schulden.
- Erster Lauf innerhalb der macOS-Sandbox: 164 bestanden, 10 Browserstartfehler
  (MachPortRendezvous permission denied). Nach freigegebenem Browserstart:
  zunächst 174 bestanden; nach Ergänzung der Regressionen 185 bestanden.
- Die zwei Recovery-Regressionen und die zwei Cacheinvalidierungs-Regressionen
  wurden vor der jeweiligen Implementierung rot ausgeführt und danach grün.
- Tatsächliche Prozessbeendigung nach 1, 4 und 7 Dateiaustauschoperationen:
  vorherige Byte-Inhalte wiederhergestellt. Manipulation nach Abbruch blockiert.
- Isoliertes natives Anki-Reimport: Inhalt/Titel/CSS aktualisiert, Note/Card-IDs,
  revlog, reps, ivl und due unverändert.
- Drei echte Vierproduktreferenzen: PDFs, APKG, Offline-HTML; zweiter Lauf
  UNCHANGED, Bytes/Zeitstempel erhalten; alle PDF-Seiten gerendert; 390/1280 px
  ohne horizontales HTML-Overflow, JS-Seitenfehler oder fehlende Fragmentziele;
  Anki-Templatevorschauen 390 px ohne Overflow.
- `git diff --check`, Python compileall und beide bestehenden `bash -n`-Checks
  bestanden. Python 3.12.14; lokal u.a. Playwright 1.65.2, Anki 26.9.3,
  PyMuPDF 2.2, SymPy 1.14.0. Vollständiger lokaler Freeze in der Evidenzablage.
- Die Gesamtregression lief während der Entwicklung; die abschließenden
  Experience-Änderungen sind durch die finale gezielte Suite gedeckt. Keine
  Behauptung eines zweiten vollständigen Legacy-Laufs.

Kosten: null bezahlte Engine-/Modell-API-Aufrufe. Installationsdownloads für
Testabhängigkeiten sind keine Modellaufrufe. Sitzungs-Tokenkosten liegen nicht
als Messwert vor. Keine Storage-Bereinigung, daher keine freigegebenen Bytes.
