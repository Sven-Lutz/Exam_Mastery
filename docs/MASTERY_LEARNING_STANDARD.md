# Mastery-Lernstandard v1: Vision, Grundkonzepte, Evidenz, visuelle Sprache

Stand 27.11.2026 · Status: **Entwurf zur Owner-Freigabe** · Herkunft: Owner-Aufträge #49 und #51 sowie die Owner-Vorgabe
„Grundkonzepte, Evidenz und Visionen müssen stehen, bevor Kapitel eingefügt werden; von 3Blue1Brown ist noch wenig zu
sehen“. Grundlage ist die Forschung R0–R9 (116 Policies, `docs/research/workstreams/r6/policy_index.json`) und die
Architektur H-AB. Dieses Dokument verdichtet sie zu verbindlichen Produktanforderungen. Es ist keine neue
Literaturrecherche und behauptet keine gemessene Lernwirkung: Alle Policies sind Designhypothesen mit
`learning_evaluation: NOT_RUN`.

---

## 1. Vision

Mastery ist ein wissenschaftlich fundiertes, KI-gestütztes System, mit dem ein Mensch anspruchsvolle Inhalte **tief
versteht, sicher anwendet und dauerhaft behält**, auf Universitäts- und Master-Niveau und darüber hinaus.

Reihenfolge der Ziele: (1) University Excellence, (2) Language Mastery, (3) Knowledge Mastery, (4) Skill Mastery (Coding,
Mathematik, Forschung, CAD, praktische Fertigkeiten; physische Kompetenz wird nie durch Simulation zertifiziert).

Mastery ist **kein** Karteikarten- oder Klausurtrainer. Prüfungsvorbereitung ist ein Modus. Der Kern ist Verständnis,
Können und Transfer.

Mastery arbeitet mit den **eigenen Kursen** der lernenden Person: Folien, Skripte, Übungen, Lösungen, Literatur,
Altklausuren. Daraus entsteht pro Kapitel eine zusammenhängende Lernumgebung aus vier Produkten (Lehrbuch, Arbeitsbuch,
Anki, Interaktiv) plus Tutor und Lernstand.

## 2. Grundkonzepte

### 2.1 Bausteine
| Begriff | Bedeutung |
|---|---|
| **Kurs** | importierte Lehrveranstaltung mit Quellen und Kapitelplan (`docs/COURSE_IMPORT.md`) |
| **Kapitel** | Lerneinheit mit Kompetenzen, vier Produkten, Quellenbezug je Aussage |
| **Kompetenz** | was man danach **kann**, typisiert: Begriff, Verfahren, Herleitung/Beweis, Modellierung, Diagnose, Transfer |
| **Operation** | die geistige Tätigkeit beim Üben (Charter-Taxonomie: Abruf, symbolisches Verfahren, formaler Beweis, Berechnung, Diagnose …) |
| **Evidenz** | beobachtete Leistung: **unassistiert/assistiert**, **Wiedererkennen/Produktion**, **sofort/nach verstrichener Zeit** |
| **Prüfer** | wer eine Antwort prüft: Regel, CAS, Tests, Simulation, Rubrik mit Mensch. Nie ein Sprachmodell als Note (R2-POL-14) |

### 2.2 Die Mastery-Lernkette (pro Kompetenz)
Jede Kompetenz wird entlang derselben Kette erarbeitet. Die Produkte sind Sichten auf diese Kette, keine getrennten Welten.

1. **Warum:** Welches Problem löst das? Einordnung in den Kurs.
2. **Intuition, sichtbar gemacht:** Das zentrale Bild, in dem sich die Idee bewegt (Abschnitt 4).
3. **Präzise Form:** Definition oder Satz, Annahmen benannt.
4. **Herleitung/Beweis** mit Selbsterklärungs-Prompts („Warum ist dieser Schritt erlaubt?“).
5. **Durchgerechnetes Beispiel**, konkrete Zahlen vor Symbolen.
6. **Fehlvorstellung widerlegen:** typische falsche Idee, warum sie falsch ist, Fehlerbeispiel.
7. **Geführte Übung** mit ausblendenden Hilfen.
8. **Selbstständige Übung**, unassistiert und geprüft.
9. **Transfer- und Klausurniveau:** veränderte Struktur, kombinierte Kompetenzen.
10. **Verteilter Abruf** in Anki (FSRS plant).
11. **Späterer unassistierter Nachweis** mit neuer Aufgabe, nach echter verstrichener Zeit.

## 3. Evidenzlage: was wie gut begründet ist

Die Stufen entsprechen der Sicherheitsskala der Workstreams. **Gut begründet** heißt: mehrere Studien bzw. Metaanalysen
mit moderater Sicherheit, aber kontextgebunden. **Designhypothese** heißt: plausibel, im Produkt prüfbar, nicht belegt.
**Normativ** heißt: Integritäts- oder Sicherheitsregel, die keine Wirksamkeitsbehauptung braucht.

| Element der Lernkette | Stufe | Anker |
|---|---|---|
| Abruf mit korrigierendem Feedback, wiederholtes Neulernen | gut begründet | R1-POL-A01 |
| Verteiltes, kumulatives Üben statt Massierung | gut begründet | R1-POL-A05 |
| Durchgerechnete Beispiele zuerst bei Novizen und hoher Komplexität, dann Ausblenden | gut begründet | R1-POL-A02 |
| Offene, inhaltsbezogene Selbsterklärung mit Abgleich | gut begründet | R1-POL-A06, R2-POL-01 |
| Feedback nach jedem Versuch, Hilfe erst nach eigenem Versuch | gut begründet | R1-POL-A08 |
| Verknüpfte Darstellungen mit gleicher Benennung und Nähe | gut begründet | R7-POL-04 |
| Fehlvorstellungen widerlegen, danach eigene Aufgabe; Zuschauen ist kein Fortschritt | gut begründet | R7-POL-06 |
| Beweisverständnis, -prüfung und -konstruktion getrennt üben und messen | Designhypothese | R2-POL-02, R2-POL-03 |
| Vorhersage vor dem Aufdecken | Designhypothese | R7-POL-02 |
| Animation nur, wenn die Veränderung selbst der Lerngegenstand ist | Designhypothese | R7-POL-05, R2-POL-17 |
| Wenige zielrelevante Regler mit Auftrag | Designhypothese | R7-POL-03 |
| Hilfeleiter auf Anforderung, Fehlerbeispiele nach korrektem Beispiel | Designhypothese | R5-POL-08, R5-POL-10 |
| Beobachtbare Zustände statt „Mastery-Prozent“ | gut begründet (Messvalidität) | R5-POL-01 |
| Assistierte und unassistierte Evidenz trennen | gut begründet | R5-POL-04 |
| Messvertrag für jede Lernwirkungsbehauptung | normativ | R5-POL-05 |
| Anki einziger Scheduler, stabile Identität, Eigentumszonen | normativ | R8-POL-01/02/05 |
| Quellenbezug, Simulation ist keine Praxisbefugnis, Sicherheitsgrenzen | normativ | R3-POL-01/10, R4-POL-01/13 |

**Ausdrücklich nicht behauptet:** Lernstile, „Gehirntraining“, Mastery-Prozentwerte, Benchmark- oder Kartenzahlen als
Lernerfolg (R1-POL-B11, R8-POL-12, R9-POL-05). Flüssige, schöne Erklärungen erhöhen das Gefühl, verstanden zu haben,
nicht automatisch das Verstehen (R7-Register: Carpenter 2013/2016). Deshalb folgt auf jede Erklärung eine eigene
Leistung.

## 4. Visuelle Sprache „Mastery Motion“

Leitbild sind die didaktischen **Prinzipien** von 3Blue1Brown und Mathigon: Mathematik wird als Bewegung von Objekten
sichtbar, und die Formel ist die Beschreibung dessen, was man sieht. Übernommen werden nur Prinzipien. Es gibt keine
kopierten Inhalte, Grafiken, Farben, Animationen oder Erzähltexte; Mastery hat eine eigene Palette und eigene Szenen
(R7-POL-10).

### 4.1 Zehn Regeln
- **V1 Das Bild ist das Argument.** Jede Szene trägt eine prüfbare Aussage und eine Lernhandlung (R7-POL-01). Keine Dekoration.
- **V2 Veränderung zeigen, wenn die Veränderung der Begriff ist.** Kontinuierliche Transformation von Zustand A nach B.
  Beispiele: lineare Abbildung der Ebene, Softmax bei sinkender Temperatur, Gradientenschritt, Stichprobenwolke wächst,
  Bellman-Update breitet sich aus (R7-POL-05).
- **V3 Formel und Bild sind gekoppelt.** Gleiches Symbol bedeutet gleiche Farbe und gleiches Objekt. Wenn sich ein Objekt
  ändert, leuchtet sein Term in der Gleichung auf, und umgekehrt (R7-POL-04).
- **V4 Erst vorhersagen, dann sehen.** An jedem Wendepunkt einer Szene steht eine Vorhersage: wohin, welches Vorzeichen,
  größer oder kleiner (R7-POL-02).
- **V5 Die lernende Person führt das Tempo.** Standard ist „Schritt“ und eine Zeitachse zum Ziehen. „Abspielen“ ist
  zweitrangig (R2-POL-17).
- **V6 Wenige Regler, klarer Auftrag.** Jeder Regler gehört zu einer Frage („Bringe die Determinante auf 0“), mit
  Experimentierhilfe (R7-POL-03).
- **V7 Vom Konkreten zum Allgemeinen.** Erst konkrete Zahlen und ein Fall, dann Symbole und der allgemeine Satz.
- **V8 Ein Objekt, drei Orte.** Dieselbe Szene erscheint als Keyframes im Lehrbuch, als interaktive Szene und als
  Abbildung auf der Anki-Karte.
- **V9 Zugänglich und offline.** Tastatur, Beschreibungstexte, Farbe nie allein bedeutungstragend, kein Netz (R7-POL-09).
- **V10 Korrekt vor schön.** Jeder gezeigte Wert wird berechnet und geprüft (seeded Simulation mit Orakel, R7-POL-07).

### 4.2 Szenengrammatik (technischer Kern, generisch)
- **Objekte:** Vektor, Gitter/Ebene, Kurve, Fläche, Punktwolke/Verteilung, Balken, Graph/MDP, Tabelle.
- **Übergänge:** interpolierte lineare Abbildung, Funktionsmorph, Iterationsschritt, Stichprobenziehung, Hervorhebung.
- **Bindungen:** Objekt ↔ Formelterm (Farbe, Name, Hervorhebung), Regler ↔ Parameter.
- **Haltepunkte:** Vorhersage, Aufdecken, Erklärung, eigene Aufgabe.
- **Ausgaben:** interaktive Szene (Browser, offline), Keyframes als SVG für Lehrbuch und Karten.

### 4.3 Vorzeigeszenen (Referenzen für den Standard)
1. **Lineare Algebra:** Eine Matrix verwandelt die Ebene. Gitter, Basisvektoren und ein Testvektor gehen kontinuierlich von
   der Identität zu A über. Die Spalten von A sind genau die Bilder der Basisvektoren. Die Determinante ist die vorzeichenbehaftete Fläche
   des Einheitsquadrats, inklusive Orientierungswechsel. Bei det = 0 fällt die Ebene auf eine Gerade (Kern und Bild).
   In Arbeit im Kapitel des zweiten Kurses.
2. **Reinforcement Learning:** Eine Softmax-Policy auf dem Wahrscheinlichkeitssimplex. Gradientenschritte bewegen den Punkt,
   die Schätzwolke von REINFORCE wird mit Baseline sichtbar enger, und die Gleichung zeigt, welcher Term was bewirkt.

## 5. Produktstandards und Abnahmekriterien

Jedes Kapitel muss diese Kriterien erfüllen, bevor es der Owner zur Prüfung erhält. Prüfbar heißt: Ein Gate im Build
oder eine dokumentierte Seitenprüfung kann das Kriterium entscheiden.

### 5.1 Lehrbuch
- Jede Kompetenz durchläuft die Lernkette, Schritte 1 bis 6.
- Jeder Satz hat einen vollständigen Beweis oder einen Quellenverweis. Annahmen sind benannt, und es gibt ein Gegenbeispiel für jede notwendige Annahme.
- Jede Abbildung stammt aus einer Mastery-Motion-Szene (V8) oder ist eine eigene, berechnete Grafik mit Aussage.
- Jede fachliche Aussage verweist auf Folie oder Seite oder ist als eigene Herleitung markiert.
- Abweichungen von den Kursunterlagen sind kenntlich (z. B. „Folienform weicht ab“).
- Seitenprüfung ohne Befund: keine abgeschnittenen Formeln, keine verwaisten Überschriften, keine leeren Halbseiten.

### 5.2 Arbeitsbuch
- Fünf Stufen: Beispiel, geführt, selbstständig, Transfer, Klausurniveau.
- Jede Aufgabe hat eine vollständige Lösung mit Prüfvermerk (CAS, Simulation, Beweisprüfung) und bei offenen Antworten eine Rubrik mit alternativen Lösungswegen.
- Pro Kapitel mindestens zwei Fehler-finden-Aufgaben.
- Beweiskompetenzen werden durch Produktion belegt, nicht nur durch Wiedererkennen (CD-11).

### 5.3 Interaktiv
- Mindestens eine Mastery-Motion-Szene pro Kapitel, die V1 bis V6 erfüllt.
- Jede Szene hat Auftrag, Vorhersage, Aufdecken und eine eigene Aufgabe danach.
- Lernstand bleibt erhalten, ist exportierbar und unterscheidet Hilfe von selbstständiger Leistung.

### 5.4 Anki
- Karten fragen nach Prinzipien, Bedingungen, Zusammenhängen und Herleitungsschritten, nicht nach Definitionslisten.
- Jede Karte hat Kontext. Formeln und Abbildungen stehen auf der Karte, wo sie das Verstehen tragen (V8).
- Feedback pro Karte: unklar, zu schwer, doppelt, Kontext fehlt, falsch, Abbildung vorschlagen. Daraus folgen kontrollierte Updates mit stabiler Identität.
- Die Planung macht ausschließlich Anki/FSRS.

### 5.5 Tutor
- Er lehrt fehlende Voraussetzungen ausdrücklich, statt nur Antworten zu bewerten.
- Er arbeitet sokratisch mit Hilfeleiter. Die Lösung gibt es nur auf ausdrücklichen Wunsch, und sie wird als Hilfe gezählt.
- Er stützt sich auf die Kapitelquellen und nennt seine Unsicherheit.
- Für Nachweisaufgaben bekommt er nie den Lösungsschlüssel.
- Die Abhängigkeit von einem externen Modell ist sichtbar. Ohne Modell steht eine deterministische Hilfe zur Verfügung (Voraussetzungsabschnitt, Beispiel, Hinweise).

### 5.6 Lernstand und Statistik
- Zeitleiste aller Lernhandlungen.
- Je Kompetenz: Zustand, Evidenzbasis, unassistiert/assistiert, Wiederholungen, Hilfen, verzögerter Nachweis.
- Jede Zahl nennt ihre Herkunft und was sie nicht misst.
- Anki-Statistiken erst nach ausdrücklichem, kontrolliertem Import durch die lernende Person.

### 5.7 Kursimport und Aktualisierung
- Vollständiges Inventar mit Herkunft und Vollständigkeitswarnungen.
- Änderungen an Quellen markieren betroffene Kapitel. Lernstände und Anki-Historien bleiben erhalten.

## 6. Rolle der KI

- **KI als Autor** zur Erstellungszeit, aus dem Authoring-Paket. Quellengebunden, jede Rechnung geprüft, Status
  `HUMAN_REVIEW_PENDING`. Abhängigkeit: Claude-Code-Sitzung mit Abo oder ein anderes vom Owner gewähltes Werkzeug. Keine
  versteckten oder bezahlten Aufrufe.
- **KI als Tutor** im Lernen: sokratisch, mit Voraussetzungen, nach Abschnitt 5.5.
- **KI nie als Notengeber** für Evidenz. Deterministische Prüfer oder Menschen bewerten. Modellurteile sind als
  `agent_judgement` gekennzeichnet.

## 7. Wie wir wissen, ob es wirkt

- **Produktqualität:** Abnahme durch den Owner mit den Kriterien aus Abschnitt 5 (OD-23). Eine unabhängige Prüfung durch
  ein Modell einer anderen Familie (Codex, Gemini) ergänzt sie, ersetzt aber keine menschliche Fachprüfung.
- **Lernwirkung:** nur über verzögerte, unassistierte Aufgaben, die unabhängig geschrieben sind (R5-POL-05, OD-13b). Bis
  dahin `NOT_RUN`. In-Produkt-Zustände sind Näherungen.

## 8. Umsetzungsreihenfolge

1. Dieser Standard: Owner-Freigabe oder Korrektur.
2. **Mastery-Motion-Engine** (Abschnitt 4.2) mit den zwei Vorzeigeszenen (4.3). Szenen erzeugen Keyframes für Buch und Karten.
3. Build-Gates und Seitenprüfung für Abschnitt 5.1 bis 5.4 (automatisch, wo möglich).
4. Tutor in der Oberfläche (5.5), Anki-Kartenfeedback (5.4), Lernstand mit Herkunft (5.6).
5. Erst dann: Kapitel in der Breite, beginnend mit vollständigen Kursen. Bereits erstellte Kapitel werden auf den
   Standard nachgezogen.

## 9. Fragen an den Owner

1. Stimmt die Lernkette (2.2) mit deinem Lernen überein, oder fehlt ein Schritt? Zum Beispiel ein eigenes Zusammenfassen oder eine eigene Mindmap.
2. Welche zwei Szenen aus deinen Kursen sollen nach den Vorzeigeszenen als Nächstes Mastery-Motion-Qualität bekommen?
3. Soll das Lehrbuch pro Kapitel eher kompakt (15 bis 25 Seiten) oder ausführlich (40 Seiten und mehr) sein?
