# Attention-Referenz: Implementation und Qualitätsnachweis

Stand: 26.11.2026. Basis: PR #19, `67f722be13fc4effeb16dcbd79ed8eda1a81cb2d`.
Branch: `feat/golden-attention-20261126`. `main` unverändert.
Historische NLP-Abnahmen bleiben **HUMAN_REJECTED**. Diese neue Referenz ist
**nicht fachlich oder menschlich freigegeben**.

## Tatsächlich implementiert

### Exklusiver Publisher-Lock — Commit `2511ae6`

`publication_lock.py` sperrt den Inode des Ausgabeverzeichnisses über POSIX flock.
Build sperrt vor Preflight, hält die Sperre über Staging/Commit/Rollback; Recovery
hält dieselbe Sperre über Prüfung und Wiederherstellung. Direkte PDF-, APKG- und
HTML-Publisher nehmen dieselbe Verzeichnissperre. Staging-Verzeichnisse erhalten
jeweils ihre eigene Sperre, daher gibt es keine rekursive Sperre auf derselben
Dateibeschreibung.

Kein entfernbarer Lockfile und keine PID-basierte Stale-Lock-Heuristik. Close,
Exception und Prozessende einschließlich Kill geben die Sperre im Kernel frei.
Timeout ist endlich, monoton gemessen, standardmäßig 30 Sekunden; Python-API
akzeptiert `lock_timeout`. Symlink als Publikationswurzel wird verweigert;
`O_NOFOLLOW`, `O_DIRECTORY`, `O_CLOEXEC` und Inode-Vergleich schützen den Erwerb.
Timeout/Konkurrenztests bewahren vorhandene Produktbytes. MacOS/Linux; andere
Plattformen sind nicht als unterstützt behauptet. flock koordiniert die
kooperierenden Publisher, keinen böswilligen externen Dateisystemschreiber.
Standalone-Preflight ist eine lesende Prüfung, keine Veröffentlichung.

### Gemeinsame Mathematik und Grafiken — Commit `6f423d9`

- Vorhandenes `math_publishing`-Register statt neuem Formelparser:
  semantische ID, TeX, Bedeutung, Symbole, Annahmen, Geltungsbereich, Quellen.
  `[[math:ID]]` wird für vorhandenen PDF-Satz und geeignete Anki-Felder in
  natives TeX aufgelöst. Offline-Web verwendet den **vorhandenen** MathJax-SVG-
  Renderer. SVG ist eingebettet, benötigt keinen CDN oder Browser-TeX-Interpreter.
- Gefährliche TeX-Kommandos, unbekannte Referenzen und zu große Formeln werden
  verweigert. Syntax/Satz sind von mathematischer Wahrheit getrennt.
- `graphics` verknüpft Modell/Interaktion, kanonische Variantenparameter,
  visuelle Objektbedeutungen, Claims, Kompetenzen, Lehr-/Aufgabenstellen,
  deterministische Keyframes, Caption und Alternativbeschreibung.
- Vorhandenes `figures_svg` rendert proportionale Quadratzerlegung und
  Attention-Zwischenwerte. Dieselben spezifizierten Zustände erscheinen im
  Offline-HTML, Lehrbuch und Arbeitsbuch. Keine zweite Grafikengine.
- Attention-Labor aktualisiert die semantischen Felder desselben SVG bei
  Q/K/V-/Temperatur-/Maskenänderungen. Eine zusätzliche lesbare Zahlenansicht
  und eine intern horizontal erkundbare Grafik verhindern mikroskopische Labels
  auf dem Telefon. Bei ungültigen Eingaben werden alte Ergebnisse ausgeblendet.
- Nach Sichtprüfung korrigiert: Herleitungsüberschrift/Voraussetzungen bleiben
  beim ersten Rechenschritt; Anhangstitel bleibt beim zugehörigen Absatz.
  Das dichte Zahlenbeispiel wurde als begründeter Rechenweg mit zwei Tabellen
  neu gestaltet; doppelte Abschnittsnummern und interne Testpfade in Quellen-
  Fußnoten wurden entfernt.

## Umfang der Attention-Einheit

Ein kuratiertes Kapitel mit elf Abschnitten, sechs Kompetenzzielen, zehn Aufgaben
mit Lösungen und Rubrics, sechzehn Anki-Notizen und einem veränderbaren Attention-
Labor. Die endgültigen PDFs haben jeweils 16 Seiten. Vier Kernprodukte:
`Lehrbuch.pdf`, `Arbeitsbuch.pdf`, `Anki.apkg`, `Interaktiv/index.html`.
Rendernachweise und Testberichte sind interne Entwicklungsartefakte außerhalb
GitHub, keine zusätzlichen Lernprodukte.

Behandelt werden Motivation, Zeilenkonvention und Dimensionen, Score-Matrix,
zeilenweise Softmax, Verschiebungsinvarianz, Max-Shift und Gleitkomma- Grenzen,
Quotientenregel/Jacobi-Matrix, konditionale Varianzrechnung für √d_k,
korrelierte Gegenbeispiele, vollständig gerechnete zwei Queries/drei Keys,
Value-Mischung/Konvexität, Maskierung und leere erlaubte Mengen, gemeinsame
Permutation und Nichtidentifizierbarkeit der Gewichte bei identischen Values.

Die Skalierung wird als unter Annahmen motivierte Modellierungsentscheidung
behandelt. Eine Rechnung über Varianzen ist kein Trainingsnachweis. Numerische
Kontrollen beweisen keine allgemeinen mathematischen Sätze. Vollständig
maskierte Zeilen sind hier undefiniert; keine fingierte Gleichverteilung oder
stillschweigende Nullausgabe. Dropout und Ausgabeprojektion sind ausdrücklich
nicht im Modell enthalten.

## Quellen und Autorenschaft

Öffentlich geöffnete Primärpassagen am 26.11.2026:

- Vaswani et al., *Attention Is All You Need*, NeurIPS 2017:
  [§3.2.1, Gleichung (1), Fußnote 4; §3.2.3](https://proceedings.neurips.cc/paper/7181--attention-is-all-you-need.pdf).
- Blanchard, D. J. Higham, N. J. Higham, *Accurate Computation of the Log-Sum-Exp
  and Softmax Functions*, arXiv:1909.03469v1 (2019):
  [§1, Gleichungen (1.2)–(1.4), Algorithmus 4.1 und Satz 4.3](https://arxiv.org/pdf/1909.03469).

Keine fremden Figuren oder Volltexte eingecheckt. Zahlen, Aufgaben, Prosa und
Grafiken sind Originalmaterial dieser Arbeit. Kein realer Vorlesungskurs oder
Prüfungsumfang wurde erfunden. `source_mode=grounded` bezeichnet öffentliche
fachliche Quellen plus eigene gekennzeichnete Herleitungen; die Datenbeispiele
bleiben synthetisch.

| Entstehung | Tatsächlicher Status |
|---|---|
| Prosa, Aufgaben, Lösungen, Karten, Beispielauswahl | Von dieser Codex-Sitzung kuratiert; kein Nachweis automatischer hochwertiger Kursautorenschaft |
| Rechnen, Satz, Registry-Projektion, Keyframes, APKG | Deterministisch durch vorhandene Engine und Erweiterungen |
| Rechenkontrolle | Separater 65-stelliger Decimal-Rechenweg; Python/JS-Parität; exakte symbolische Dreivariablen-Jacobi-Kontrolle |
| Quellenkontrolle | Genannte Passagen durch die Sitzung gelesen; kein unabhängiger menschlicher Literaturreview |
| Fach-/Didaktik-/Humanabnahme | Ausstehend; keine erfundene zweite Person oder Bewertung |

`authorship` wird in Offline-HTML und PDF-Anhang sichtbar. Eigene weitergehende
Claims bleiben im Modell `unverified`, bis eine unabhängige fachliche Prüfung
vorliegt. Technische PASS-Ergebnisse verändern diese Einordnung nicht.

Der lokale RL-Pilot `f536fd5` mit zehn ungepushten Commits bleibt unverändert.
Selektiv geprüft wurde sein reiner `lab_math.js`-Kern (`attendOne`, Max-Shift):
Die arithmetischen Grundideen wurden mit zusätzlichen Eingabe-/Maskenprüfungen
in das neue registrierte Attention-Modell übertragen. Kein B35/B36-Blindimport;
der lokale `argument_graph`-Pfad mit unbeschränktem `sympify` wurde nicht übernommen.

## Prüfungen und Reproduktion

```sh
.venv/bin/python -m pytest -q tests/test_publication_lock.py tests/test_attention_reference.py tests/test_experience_core.py tests/test_experience_evidence.py tests/test_experience_adaptation.py tests/test_experience_misconceptions.py tests/test_experience_proof_checks.py tests/test_interactive_reference.py tests/test_experience_anki.py tests/test_experience_books.py tests/test_experience_pipeline.py
.venv/bin/python -m unittest discover -s tests
.venv/bin/python scripts/verify_experience_references.py --out /tmp/em-golden-reference
```

Installation/MathJax-/Font-Voraussetzungen stehen im Engineeringbericht von #19.
Keine kostenpflichtigen Modellaufrufe erforderlich. Publisher-Lock benötigt POSIX.

Lokale finale Evidenz: `/Users/svenlutz/Projects/Exam_Mastery-golden-20261126/final`.
`report.json` nennt die hashgebundenen Renderverzeichnisse. Darin jede PDF-Seite,
Anki-Vorder-/Rückseiten hell/dunkel bei 390 px, Offline-Seiten bei 390/1280 px,
Herleitungsausschnitte und tatsächliche Q/V-Interventionszustände. Alle vier
Referenzen werden zweimal gebaut; zweiter Lauf UNCHANGED mit erhaltenen mtimes.

Gezielte Suite: **215 bestanden**, 20,97 s. Anschließend bereinigte reine
Inhaltsfassung nochmals separat: **22 Attention-Tests bestanden**, 16,75 s.
Der erste Browser-Interaktionstest scheiterte am absichtlich eingeklappten
Maskenpanel; er öffnet dieses nun wie ein Nutzer. Ein zwischenzeitlicher Test
mit widersprüchlicher Tabellen-Stringbedingung wurde durch die tatsächliche
Autorenschafts-Projektionsprüfung ersetzt. Keine Fehler als bestanden gezählt.

Weitere Nachweise:
- Prozessübergreifende Sperre, wartender Prozess, Timeout und Kernelfreigabe nach
  Prozessende; vorhandene Bytes unverändert.
- Bestehende Recovery-Tests einschließlich echtem Prozessende an Commitgrenzen
  und native Anki-Reimport-/History-Regressionen bleiben in der Suite enthalten.
- 35 deterministische zufällige Matrix-/Masken-/Temperaturfälle gegen unabhängige
  Decimal-Summen; kontrastierende Query-/Key-/Value-Dimensionen.
- Falsche Masken, leere erlaubte Menge, NaN/Inf, boolesche Zahlen, inkompatible
  Dimensionen, unbekannte Felder, falsche Referenzen und unsicheres TeX abgelehnt.
- Diskrete vollständige Aufzählung kontrolliert das unabhängige Varianzbeispiel
  und den korrelierten Gegenfall. Das ersetzt nicht den allgemeinen Textbeweis.
- Gemeinsame K/V-/Masken-Permutation, reine Value-Intervention, maskierter Maximal-
  Score und identische Values geprüft; kein Schluss von Gewicht auf Kausalität.
- Tatsächliche Browserinteraktion, kein HTTP(S)-Abruf bei Offline-Nutzung,
  keine JS-Seitenfehler oder Dokument-Overflow in den geprüften Breiten.
- Python compileall, `git diff --check` und beide bestehenden Shell-Syntaxchecks.

Vollständige Legacy-Suite: **632 Tests ausgeführt, OK, sechs übersprungen**,
389,019 s. Diese Suite prüft den gemeinsamen Typesetter und bestehende Engine-
Pfade; die finalen Experience-Inhalts-/Darstellungsänderungen sind zusätzlich
durch die gezielte Suite gedeckt. Erwartete Negativtest-Exceptions und
ResourceWarnings zu offenen Testdateien sind keine behaupteten Testfehler,
bleiben aber technische Schulden.

Finale Artefakte: alle vier Referenzen erfolgreich; jeweils zweiter Lauf
UNCHANGED. Attention: 16+16 PDF-Seiten, 16 Notes und 64 gerenderte Seiten
(Front/Back × hell/dunkel). Alle Seiten wurden gerendert; visuell untersucht
wurden Kontaktübersichten, einzelne formelreiche Seiten, die Geometrieseite,
Attention-Zahlen-/Schaubildseiten, mobile Herleitung, Q/V-Intervention und
ausgewählte Anki-Front-/Rückseiten. Das ist keine externe Vollabnahme.
Die Nachweise bleiben lokal und enthalten keine privaten Lernerdaten.

Kosten: **null kostenpflichtige Modell-/Engine-API-Aufrufe**; Sitzungs-Tokenkosten
liegen nicht als Messwert vor. Keine Speicherbereinigung oder Löschung von
Referenzmaterial. Der RL-Pilot bleibt am unveränderten Commit f536fd5.

## Verbleibender Abstand zur exzellenten Golden Reference

1. **P0 wissenschaftliche Abnahme:** Der konditionale Beweis, didaktische
   Angemessenheit und Quelleninterpretation benötigen einen unabhängigen
   fachlichen Leser. Eine externe Fachbewertung wurde nicht erfunden.
2. **P1 Lernprozess:** Keine empirische Lernwirksamkeit, keine unabhängigen
   verzögerten Transferleistungen realer Lernender. Freitext wird nicht als
   automatisch korrekt oder gemeistert gewertet. Persistenter Lernzustandsimport
   bleibt offen; Anki/FSRS bleibt der einzige Wiederholungsplaner.
3. **P1 visuelle Erklärung:** Zahlenfluss und echte Intervention sind deutlich
   verbessert; kontinuierliche geometrische Query/Key-Vektorstory, Farblegende
   über alle Medien und weitere annotierte Übergänge sind noch kein geprüftes
   Publikationsdesign auf außergewöhnlichem Niveau. Die aktuelle SVG-Projektion
   ist auf maximal vier Keys und zwei Value-Koordinaten begrenzt und lehnt
   ungeeignete größere Zustände ab, während das mathematische Modell weiter reicht.
4. **P1 Clientmatrix:** Native Anki-Template-Engine und Chromium-Vorschau sind
   getestet, tatsächliche AnkiMobile-/AnkiDroid-Geräte fehlen.
5. **P1 Betriebsgrenze:** Exklusive kooperierende Publisher und explizite Crash-
   Recovery sind implementiert. Die ganze Vierdateigruppe ist weiterhin nicht
   atomar sichtbar und nicht gegen Stromausfall samt fsync-Kette abgesichert.

Die Arbeit nach der ersten Implementierung ging bereits in das wichtigste
sichtbare Defizit: vollständigerer, lesbarer Zahlenweg, mobile Zahlenalternative,
Satzkorrekturen und verständliche Quellenangaben. Nächster Produktmeilenstein:
unabhängig annotierter Fach-/Learner-Review dieser konkreten vier Produkte und
anschließend eine geometrische Score-/Value-Erklärung am selben Modell.
**Technisch als begrenzter Golden-Reference-Reviewkandidat ausführbar; keine
wissenschaftlich oder menschlich angenommene Golden Reference.**
