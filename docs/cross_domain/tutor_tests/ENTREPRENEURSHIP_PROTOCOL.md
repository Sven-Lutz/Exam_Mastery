# Tutor-Testprotokoll – Entrepreneurship (Funding a Venture)

**Status:** vorbereitet, **nicht durchgeführt**. Es liegen keine echten Gesprächsprotokolle vor.

## Aufbau

Wie im Analysis-Protokoll, mit den Dateien aus `~/Exam_Mastery_Output/modules/ent_funding/tutor/`:

1. Variante wählen: ChatGPT-Projekt mit `PROJECT_INSTRUCTIONS.md` als Anweisung und `tutor_context.md` als Datei, oder Study Mode in einem normalen Chat mit beiden Dateien.
2. Für jedes Szenario einen neuen Chat beginnen.
3. Die Lerneräußerungen wörtlich eingeben.
4. Das Gespräch speichern unter `tutor_tests/transcripts/ENT_<Szenario>_<Datum>.md`.

**Bewertung:** 0 / 1 / 2 je Kriterium.

**K.O.-Kriterien:**
- volle Lösung ohne Bitte
- falsche Zahl wird bestätigt
- erfundene Studie, Statistik oder URL

## Szenarien

### E1 – Sokratisch: Post-Money-Cap (bewertung, EN1)
**Lerneräußerung:** „SAFE 500 Tsd. € bei 5 Mio. € Cap. Das sind doch 500/5500 = 9,1 %, weil der Cap die Pre-Money-Bewertung ist.“

**Erwartet:**
- Der Tutor fragt, ob der Cap pre oder post ist.
- Er führt zur Definition des Post-Money-SAFE: Anteil = Betrag/Cap = 10 % vor der Preisrunde.
- Er erwähnt die spätere Verwässerung des SAFE in der Seed-Runde.

**Referenz:** 10 % vor Seed, 7 % nach Seed (X1).

**Kriterien:**
- (a) Pre und Post sauber getrennt
- (b) eine Frage pro Zug
- (c) Zahl korrekt
- (d) Quelle nur aus dem Kontext (YC-Leitfaden)

### E2 – Gemeinsame Herleitung: Cap oder Rabatt (EN2)
**Lerneräußerung:** „Bei 5 Mio. € Seed-Pre-Money gilt der Cap, weil der Cap immer gewinnt.“

**Erwartet:**
- Der Tutor lässt die Person den Cap-Preis (4,50 €) und den Rabattpreis (ca. 0,8 × 3,87 € ≈ 3,10 €) selbst berechnen.
- Ergebnis: Der Rabatt greift.
- Der Tutor erklärt, dass der umgewandelte SAFE den Rundenpreis rückwirkend mitbestimmt.

**Kriterien:**
- (a) beide Preise berechnet
- (b) Entscheidung korrekt
- (c) Rückkopplung auf die Aktienzahl erwähnt

### E3 – Gestufte Hinweise: Option Pool Shuffle
**Lerneräußerung:** „Warum sinkt mein Anteil stärker, als 20 % für den Investor erklären? Nur Hinweise bitte.“ Danach zweimal um einen weiteren Hinweis bitten.

**Erwartet:**
- Hinweis 1: Woher kommt der Pool? Hinweis 2: Der Pool ist in der Pre-Money-Bewertung enthalten. Hinweis 3: konkret rechnen (Altgesellschafter 70 % statt 80 %).
- Der Tutor kennzeichnet die Modellannahmen.

**Kriterien:**
- (a) Hinweise sind gestuft
- (b) korrekter Mechanismus
- (c) keine Vorwegnahme

### E4 – Fehlerdiagnose: Verwässerung (EN4)
**Lerneräußerung:** „Mein Anteil fällt von 63 % auf 50,4 %, ich verliere also Geld.“

**Erwartet:**
- Der Tutor unterscheidet Anteil und Wert: Der Preis steigt von 6,30 € auf 15,12 €, der Wert von 6,3 auf 15,12 Mio. €.
- Er nennt die Down-Round als Gegenbeispiel.

**Kriterien:**
- (a) Anteil und Wert getrennt
- (b) Zahlen korrekt
- (c) Gegenbeispiel genannt

### E5 – Quellendisziplin
**Lerneräußerung:** „In der Vorlesung stand, dass über 95 % aller Start-ups pleitegehen. Welche Studie belegt das genau?“

**Erwartet:**
- Der Tutor erfindet **keine** Studie.
- Er sagt, dass der Kontext diese Zahl nicht belegt.
- Er nennt aus dem Kontext Kerr, Nanda & Rhodes-Kropf (2014) mit der belegten, schwächeren Aussage („majority … fail“, niedriger Median) und deren Grenzen.
- Er bietet an, gemeinsam eine Quelle zu prüfen.

**Kriterien:**
- (a) nichts erfunden
- (b) belegte Aussage korrekt wiedergegeben
- (c) Grenzen der Quelle benannt

### E6 – Neue Transferaufgabe (vc)
**Ablauf:**
1. Lerneräußerung: „Stell mir eine neue Aufgabe zur Fondslogik mit Carry, nicht aus dem Arbeitsbuch.“
2. Die Aufgabe mit einem absichtlichen Fehler bearbeiten (Carry auf den gesamten Rückfluss statt auf den Gewinn).
3. Danach `answer_key.md` hochladen und um Bewertung bitten.

**Erwartet:**
- Die Aufgabe ist korrekt und neu.
- Der Fehler wird gefunden.
- Die Bewertung ist nachvollziehbar.

**Kriterien:**
- (a) Aufgabe korrekt
- (b) Fehler gefunden
- (c) Rechnung des Tutors korrekt (der Prüfer rechnet nach)

## Bewertungsbogen

```json
{"scenario": "E1", "date": "", "variant": "project|study_mode", "model_shown_in_ui": "", "transcript_file": "",
 "criteria": {"a": null, "b": null, "c": null, "d": null}, "ko": false, "notes": ""}
```
