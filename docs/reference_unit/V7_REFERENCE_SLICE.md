# v7 – Referenzsequenz „Self-Attention: Softmax und Konvexkombination“ (Issue #10)

**Status**
- TECHNICAL_PASS: lokale Tests grün, CI ausstehend.
- CONTENT_CORRECTNESS_REVIEW_REQUIRED · DIDACTIC_REVIEW_REQUIRED · PUBLISHING_REVIEW_REQUIRED.
- v6.1 ist HUMAN_REJECTED. Es gibt keine Selbstfreigabe; PR #3 bleibt Draft.

Die Sequenz ist **ein** vollständiger Vertikalschnitt; andere Kapitel sind bewusst nicht überarbeitet (Issue #10, P1). Alle Produkte nutzen dasselbe Konzeptmodell, dieselbe Notation (q, kⱼ, vⱼ, sⱼ, T, wⱼ, o) und dieselbe Farbsemantik:

| Objekt | Farbe |
|---|---|
| Query | Blau |
| Keys | Bernstein |
| Values | Petrol |
| Gewichte | Violett |
| Ausgabe | Karmin |
| Beweis | Grün |
| Fehler | Rot |

## Lernreise und Produkte

1. **Lehrbuch §6** (`index.html#learn/att-problem`, `Lehrbuch.pdf` S. 12–25).
   - 6.1 Problem („Bank“).
   - 6.2 Voraussetzungen: Skalarprodukt mit Beweis der Kosinusformel, Exponentialfunktion, Symbolverzeichnis mit Formen.
   - 6.3 Softmax **hergeleitet** aus vier Forderungen, mit Gegenbeispiel zur naiven Normierung und einem Beweis jeder Eigenschaft.
   - 6.4 Simplex.
   - 6.5 Konvexkombination, Satz 6.2 mit Beweis beider Richtungen.
   - 6.6 vollständig durchgerechnetes Beispiel, jeder Schritt begründet.
   - 6.7 Matrixform mit Dimensionsprobe.
   - 6.8 Satz 3: Varianz, sechs begründete Schritte.
   - Lemma 6.4: Jacobi-Matrix mit Temperaturbedingungen.
   - 6.9–6.10 Gleichverteilung und Denkfehler.
   - 6.11 Forschung (Jain & Wallace; Wiegreffe & Pinter), mit der Mathematik verbunden.
   - 6.12 Selbstcheck.
   - Klausurkern, Vertiefung und Forschung sind im Fließtext markiert.
2. **Sechs Originalgrafiken** (`exam_mastery/figures7.py`): Projektion, Rechenkette, Temperaturverlauf, Simplex, konvexe Hülle, Varianzexperiment. Alle Zahlen kommen aus demselben Rechenorakel wie der Text.
3. **Lab** (`labor.html#lab=attention`): neue Simplex-Ansicht, die denselben Gewichtsvektor wie Abb. 6.4 live zeigt, inklusive Temperaturbahn. Dazu kommen Entdeckungspfad, Challenges, Hypothesenprüfung und freie Bühne.
4. **Arbeitsbuch**:
   - AT0 (durchgerechnet), AT1 (Lückenschritt), AT2 (selbstständig), AT5 (durchgerechnetes Bank-Beispiel), AT6 (Beweis), AT7 (Transfer), AT8 (Gradient), AT9 (Fehleranalyse).
   - **Neu: AT10**, Attention rückwärts rechnen: Gewichte → Scores → Query → Temperatur, in fünf Teilen mit ausführlicher Lösung und Bewertungsschema.
5. **Probeklausur**: neue, unabhängige Transferaufgaben **A19** und **B-19** mit anderen Daten und anderen Prüfroutinen; Kurzschlüssel und ausführliche Lösung getrennt.
6. **Anki**: Karten der Sequenz neu gefasst, darunter neu `attention/softmax-why-exp` und `attention/simplex`.
   - Die Kartengrafiken kommen aus denselben Originalabbildungen und sind für die Karte zugeschnitten: ohne Titel, größere Schrift.
   - Bestehende IDs und Notetypes sind unverändert; nur das Template-Versionsfeld steigt auf 2.1.0.

## Korrekturen aus Issue #10

- **[cos 1, 1] falsch-negativ:**
  - Endpunkte lassen sich exakt als Ausdruck eingeben.
  - Exakte rationale Arithmetik oder identische Ausdrücke beweisen Randgleichheit.
  - Ergebnisse sind „bewiesen“, „widerlegt“ oder „nicht entscheidbar“.
  - Regressionstests nutzen sympy als Orakel und decken Grenzfälle ab.
- **Quellenabruf gehärtet:** nur http(s), keine privaten oder lokalen Adressen (auch nach Weiterleitung), Größen- und Inhaltstyp-Grenzen.
- **Ehrliche Etiketten:** Die Textprüfung heißt „Textvorkommen geprüft“; Interpretation und Studiendesign gelten ausdrücklich als nicht geprüft.

## Was automatisch geprüft ist (keine Aussage über Qualität)

- `verify`: 228 Zahlen nachgerechnet, inklusive aller Dezimalzahlen im neuen Text, in AT10, A19 und B-19 und in den Karten.
- `tests/test_v7_layout.py`:
  - keine horizontalen Überläufe und keine Schrift unter 12 px bei 390, 1280 und 1440 px;
  - keine kollidierenden Beschriftungen in den Grafiken;
  - keine übergroßen Formelblöcke;
  - semantische Farben hell und dunkel aufgelöst;
  - Lab-Simplex gleich Softmax;
  - Grafikzahlen gleich Orakel;
  - Varianzexperiment.
- Anki-Vorschauen: Chromium und WebKit, hell, dunkel und mobil, ohne Überlauf oder rohen TeX-Code.

## Vorher/Nachher-Nachweise

`docs/reference_unit/review_v7/`:
- `before/`: v6-Lehrbuchseiten 11–15.
- `after/`: HTML in vier Ansichten, alle Grafiken hell und dunkel, PDF-Kontaktbogen und Einzelseiten, Anki vorne und hinten, Lab-Zustände.

## Offen / bekannte Schwächen (bitte bewerten)

- **Seitenumbruch im PDF:** Verbessert (Beweise dürfen zwischen Schritten umbrechen); einzelne halbleere Seiten können bleiben.
- **Kurvenfarben der Temperaturgrafik:** Sie unterscheiden Wörter und nutzen dafür Farben, die sonst Objekttypen tragen. Ein Zielkonflikt der Farbsemantik.
- **Simplex-Kartengrafik am Handy:** Beschriftungen sind klein (etwa 10 px).
- **Restliche Kapitel** (BiRNN, CRF, Evaluation) sind noch auf altem Stand; Übertragung erst nach Abnahme.
- **Keine Expertenprüfung** der Beweise, **kein Lerntest.**
