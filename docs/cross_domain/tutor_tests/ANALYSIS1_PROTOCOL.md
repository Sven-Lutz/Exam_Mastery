# Tutor-Testprotokoll – Analysis 1 (Konvergenz von Folgen)

**Status:** vorbereitet, **nicht durchgeführt**. Es liegen keine echten Gesprächsprotokolle vor; es wird keine Evaluation behauptet.

## Aufbau (ca. 5 Minuten)

1. Wähle eine Variante:
   - **Projekt:** In ChatGPT ein neues Projekt „Analysis 1 – Folgen“ anlegen. Den Inhalt von `modules/analysis1_folgen/tutor/PROJECT_INSTRUCTIONS.md` (Ausgabe unter `~/Exam_Mastery_Output/modules/analysis1_folgen/tutor/`) in die Projektanweisungen kopieren. `tutor_context.md` als Projektdatei hochladen. `answer_key.md` erst für Szenario 6 hochladen.
   - **Study Mode:** Einen normalen Chat außerhalb von Projekten öffnen, den Lernmodus aktivieren und beide Dateien anhängen.
2. Für jedes Szenario einen **neuen Chat** beginnen.
3. Die Lerneräußerungen **wörtlich** eingeben.
4. Das Gespräch als Text kopieren und unter `tutor_tests/transcripts/ANA_<Szenario>_<Datum>.md` speichern.
5. Den Bewertungsbogen am Ende ausfüllen.

## Bewertung je Kriterium

- **0** verfehlt
- **1** teilweise
- **2** erfüllt

**K.O.-Kriterien** (das Szenario gilt als nicht bestanden):
- Der Tutor gibt die volle Lösung, obwohl die Person noch löst und nicht danach gefragt hat.
- Der Tutor bestätigt eine falsche Rechnung.
- Der Tutor erfindet Quellen, Seitenzahlen oder Links.

## Szenarien

### A1 – Sokratischer Einstieg und Randfall (konv, AN1)
**Lerneräußerungen:**
1. „Ich will verstehen, wie man N(ε) findet. Bei (2n−1)/(n+3) → 2 und ε = 0,01 komme ich auf N = 697.“
2. Nach der ersten Rückfrage: „7/(n+3) < 0,01 heißt n + 3 > 700, also n > 697, also N = 697.“

**Erwartet:**
- Der Tutor fragt nach dem Rechenweg, statt das Ergebnis zu nennen.
- Er lenkt den Blick auf die strenge Ungleichung bei n = 697 (7/700 = 0,01 ist nicht < 0,01).
- Er lässt die Person N = 698 selbst finden.

**Referenz (nur Prüfer):** N = 698.

**Kriterien:**
- (a) genau eine Frage pro Zug
- (b) Fehlerstelle präzise benannt
- (c) keine vorweggenommene Lösung
- (d) Rechnung korrekt

### A2 – Gemeinsame Herleitung (monoton, AN2)
**Lerneräußerungen:**
1. „Lass uns zeigen, dass aₙ₊₁ = (aₙ + 2/aₙ)/2 mit a₁ = 2 gegen √2 geht. Ich setze einfach a = (a + 2/a)/2, dann ist a = √2.“
2. Später: „Für a₁ = −1 kommt dann auch √2 raus.“

**Erwartet:**
- Der Tutor verlangt zuerst den Existenznachweis (Monotonie und Beschränktheit, Satz 2.14), bevor der Grenzübergang erlaubt ist.
- Er weist darauf hin, dass die Fixpunktgleichung zwei Lösungen hat.
- Er korrigiert, dass a₁ = −1 zu −√2 führt.

**Referenz (nur Prüfer):** aₙ₊₁ − √2 = (aₙ − √2)²/(2aₙ); bei negativem Start ist der Grenzwert −√2.

**Kriterien:**
- (a) Existenz vor Grenzübergang
- (b) Wahl der Wurzel begründet
- (c) die Person führt die Schritte selbst aus

### A3 – Gestufte Hinweise (kontraktion, AN4)
**Lerneräußerung:** „Ich hänge bei AN4 komplett. Gib mir bitte nur einen Hinweis.“ Danach zweimal „noch einen Hinweis“, dann „jetzt die Lösung bitte“.

**Erwartet:**
- Hinweis 1 gibt die Richtung (invariantes Intervall), Hinweis 2 das Werkzeug (Mittelwertsatz, sup |sin|), Hinweis 3 den konkreten nächsten Schritt.
- Die Lösung kommt erst auf ausdrückliche Bitte.
- Der Tutor betont, dass eine Simulation keinen Beweis ersetzt.

**Referenz (nur Prüfer):** z. B. [cos 1, 1] oder [0,5; 1]; q = sin 1 ≈ 0,8415; a-priori-Schranke n = 48 für Fehler ≤ 10⁻³ (tatsächlich reichen 16 Glieder).

**Kriterien:**
- (a) die Stufen bauen aufeinander auf
- (b) keine Lösung vor der Bitte
- (c) Beweis von Indiz getrennt
- (d) Zahlen korrekt

### A4 – Fehlerdiagnose (kontraktion / cauchy)
**Lerneräußerung:** „f(x) = x + 1/x verkleinert Abstände, also hat die Folge aₙ₊₁ = aₙ + 1/aₙ nach dem Fixpunktsatz einen Grenzwert. Und weil aₙ₊₁ − aₙ → 0, ist sie ohnehin Cauchy.“

**Erwartet:**
- Der Tutor findet **zwei** Fehler: Es gibt kein q < 1 und kein invariantes beschränktes Intervall (kein Fixpunkt). Außerdem folgt aus aₙ₊₁ − aₙ → 0 keine Cauchy-Eigenschaft.
- Er liefert ein Gegenbeispiel bzw. eine Rechnung (aₙ² wächst um mehr als 2 je Schritt).

**Kriterien:**
- (a) beide Fehler erkannt
- (b) Gegenbeispiel bzw. Rechnung korrekt
- (c) Bezug auf den Fixpunktsatz (Vollständigkeit plus Kontraktion)

### A5 – Quantitative Korrektheit (monoton)
**Lerneräußerung:** „Berechne die ersten fünf Glieder der Heron-Folge für √2 exakt als Brüche und den Fehler des fünften.“

**Erwartet:**
- Die Glieder 2, 3/2, 17/12, 577/408, 665857/470832.
- Der Fehler ≈ 1,6·10⁻¹².

**Kriterien:**
- (a) alle Brüche exakt
- (b) Fehler in der richtigen Größenordnung
- (c) Rechenweg nachvollziehbar

### A6 – Neue Transferaufgabe und Bewertung
**Ablauf:**
1. Lerneräußerung: „Stell mir eine neue Transferaufgabe zur Kontraktionsbedingung, die nicht im Arbeitsbuch steht. Keine Hinweise.“
2. Die Aufgabe ernsthaft und **mit einem absichtlichen Fehler** bearbeiten (z. B. Invarianz nicht prüfen).
3. Danach `answer_key.md` hochladen und um Bewertung nach Rubrik bitten.

**Erwartet:**
- Die Aufgabe ist neu, lösbar und fachlich korrekt (der Prüfer rechnet nach).
- Die Bewertung findet den eingebauten Fehler und nutzt ein Punkteschema.
- Der Tutor vergibt keine Note ohne Begründung.

**Kriterien:**
- (a) Aufgabe korrekt und neu
- (b) Fehler gefunden
- (c) Bewertung begründet
- (d) Unsicherheit benannt

## Bewertungsbogen (je Szenario ausfüllen)

```json
{"scenario": "A1", "date": "", "variant": "project|study_mode", "model_shown_in_ui": "", "transcript_file": "",
 "criteria": {"a": null, "b": null, "c": null, "d": null}, "ko": false, "notes": ""}
```

Ausgefüllte Bögen bitte unter `tutor_tests/results/` ablegen. Erst dann ist der Tutor-Kanal für dieses Modul evaluiert.
