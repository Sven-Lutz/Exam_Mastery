# Tutor-Kontext: Analysis 1 – Konvergenz von Folgen

Modul `analysis1-folgen` · Fach: mathematics · erzeugt 2026-11-15

## Offizieller Rahmen
Kapitel 2 der Vorlesung Analysis 1: Folgen, ε-N-Konvergenz und ihre Verneinung, Beschränktheit und Eindeutigkeit, Grenzwertsätze und Sandwich, monotone Konvergenz und Rekursionen, Teilfolgen, Häufungspunkte, lim sup/lim inf, Bolzano–Weierstraß, Cauchy-Kriterium und Vollständigkeit, Kontraktionsbedingung.

Offizielle Kursquellen (definieren den Prüfungsstoff): Vorlesungsskript Analysis 1, Kap. 2 (private Kursunterlage; Definitions- und Satznummern 2.1–2.31 als Lokatoren)

## Prüfung
Offizielle Angaben zu Dauer und Hilfsmitteln liegen nicht vor. Typische Anforderungen laut Kapitel: Definitionen exakt angeben, ε-N-Beweise führen, Grenzwerte mit Grenzwertsätzen berechnen, Konvergenz rekursiver Folgen über Monotonie oder Kontraktion zeigen, Gegenbeispiele angeben.

## Notation
- (a_n)_{n∈ℕ}: Folge; ℕ beginnt bei 1
- a_n → a: ∀ε>0 ∃N∈ℕ ∀n≥N: |a_n − a| < ε
- lim sup, lim inf: größter bzw. kleinster Häufungspunkt einer beschränkten reellen Folge
- q: Kontraktionskonstante: |a_{n+2} − a_{n+1}| ≤ q|a_{n+1} − a_n| mit 0 ≤ q < 1

## Kompetenzen
### konv · ε-N-Konvergenz und ihre Verneinung (Klausurkern)
Voraussetzungen: ext:Quantorenlogik, ext:Betrag und Dreiecksungleichung
- Ziel: Definition 2.2 exakt angeben und an Beispielen N(ε) bestimmen
- Ziel: Divergenz durch Verneinung mit vertauschten Quantoren nachweisen
- Typische Fehlvorstellung: N darf nicht von n abhängen, aber von ε
- Typische Fehlvorstellung: endlicher numerischer Test ersetzt keinen Beweis
- Typische Fehlvorstellung: beschränkt ⇒ konvergent
Lernprodukte: {"lab": [{"lab": "folgen", "item": "f1"}, {"lab": "folgen", "item": "f3"}, {"lab": "folgen", "item": "g-noN"}], "tasks": ["AN1"]}
Quellen: skript, lebl

### grenzw · Grenzwertsätze und Sandwichkriterium (Klausurkern)
Voraussetzungen: konv
- Ziel: Satz 2.7 und 2.10 anwenden; Voraussetzung a ≠ 0 beim Kehrwert prüfen
- Typische Fehlvorstellung: aus a_n < b_n folgt lim a_n < lim b_n
Lernprodukte: {}
Quellen: skript, lebl

### monoton · Monotone Konvergenz und rekursive Folgen (Klausurkern)
Voraussetzungen: konv
- Ziel: Theorem 2.14 anwenden: Monotonie und Beschränktheit per Induktion zeigen, Grenzwert aus Fixpunktgleichung
- Ziel: Wahl der Lösung der Fixpunktgleichung begründen
- Typische Fehlvorstellung: Grenzwert aus Fixpunktgleichung ohne Existenznachweis
- Typische Fehlvorstellung: Fixpunktgleichung legt das Vorzeichen fest
Lernprodukte: {"lab": [{"lab": "folgen", "item": "f4"}, {"lab": "folgen", "item": "g-fast"}], "tasks": ["AN2"]}
Quellen: skript, lebl

### hp · Teilfolgen, Häufungspunkte, Bolzano–Weierstraß (Klausurkern)
Voraussetzungen: konv
- Ziel: Häufungspunkte als Teilfolgengrenzwerte bestimmen
- Ziel: Konvergenz über eindeutigen Häufungspunkt einer beschränkten Folge entscheiden
- Typische Fehlvorstellung: ein Häufungspunkt ⇒ konvergent (ohne Beschränktheit)
Lernprodukte: {}
Quellen: skript, lebl

### cauchy · Cauchy-Kriterium und Vollständigkeit (Klausurkern)
Voraussetzungen: konv, hp
- Ziel: Cauchy-Folge definieren; Äquivalenz zur Konvergenz in ℝ nutzen
- Ziel: Gegenbeispiel: Nachbarglieder genügen nicht; ℚ ist nicht vollständig
- Typische Fehlvorstellung: |a_{n+1} − a_n| → 0 ⇒ Cauchy
Lernprodukte: {"tasks": ["AN3"]}
Quellen: skript, lebl

### kontraktion · Kontraktionsbedingung und Fixpunkt (Vertiefung)
Voraussetzungen: cauchy, monoton
- Ziel: Satz 2.31 anwenden; a-priori-Schranke berechnen
- Ziel: Unterschied kontraktiv vs. Kontraktion an einem Gegenbeispiel erklären
- Typische Fehlvorstellung: |f(x) − f(y)| < |x − y| genügt
Lernprodukte: {"lab": [{"lab": "folgen", "item": "f5"}, {"lab": "folgen", "item": "g-contr"}], "tasks": ["AN4"]}
Quellen: skript, lebl

## Übungsaufgaben (ohne Lösungen; Schlüssel separat in answer_key.md)
- **AN1** (konv, independent): Zeigen Sie (2n−1)/(n+3) → 2 mit der ε-N-Definition und bestimmen Sie für ε = 1/100 das kleinste N.
- **AN2** (monoton, proof): Sei a₁ = 2, aₙ₊₁ = (aₙ + 2/aₙ)/2. Zeigen Sie: aₙ ≥ √2 für alle n, die Folge fällt monoton, und lim aₙ = √2. Was ändert sich für a₁ = −1?
- **AN3** (cauchy, error): Ein Kommilitone schreibt: „Wegen |aₙ₊₁ − aₙ| → 0 ist (aₙ) eine Cauchy-Folge und konvergiert.“ Widerlegen Sie das mit einem Gegenbeispiel und benennen Sie den Fehler.
- **AN4** (kontraktion, transfer): aₙ₊₁ = cos(aₙ), a₁ = 1. Zeigen Sie mit der Kontraktionsbedingung Konvergenz und bestimmen Sie mit der a-priori-Schranke ein n, ab dem |aₙ − a| ≤ 10⁻³ garantiert ist.

## Eigene, geprüfte Beispiele
- **E1** (monoton): Heron/Newton für √2 in exakten Brüchen – a₁ = 2, aₙ₊₁ = (aₙ + 2/aₙ)/2 liefert 3/2, 17/12, 577/408, 665857/470832 … Neu gegenüber der Quelle: exakte Fehleridentität eₙ₊₁ = eₙ²/(2aₙ) (Zahl korrekter Stellen verdoppelt sich), die Folge ist eine Cauchy-Folge rationaler Zahlen ohne Grenzwert in ℚ (Gegenbeispiel zur Vollständigkeit von ℚ) und ein negativer Start führt zu −√2 (Fixpunktgleichung allein wählt keine Wurzel).
- **E2** (kontraktion): cos als Kontraktion – x + 1/x als Gegenbeispiel – cos bildet [cos 1, 1] in sich ab, q = sin 1 ≈ 0,8415; die a-priori-Schranke verlangt n = 48 für Fehler ≤ 10⁻³, tatsächlich genügen 16 Glieder (Schranke ist pessimistisch). f(x) = x + 1/x verkleinert Abstände echt, hat aber kein q < 1 und keinen Fixpunkt: aₙ² wächst um mehr als 2 je Schritt.
- **E3** (konv): Zahlenprobe AN1 – Randfall N = 698.

## Geprüfte Quellen (nur diese zitieren)
- **skript** [official, lecture, Zugriff: private_course_material] Vorlesungsskript Analysis 1, Kapitel 2 „Konvergenz von Folgen“ (private Kursunterlage des Nutzers, nicht veröffentlicht) 
  - Def. 2.2, Satz 2.4, 2.7, 2.10, Thm. 2.14, Def. 2.17–2.19, Thm. 2.24, Def. 2.26, Thm. 2.27, Bem. 2.28, Satz 2.31: Gliederung und Nummerierung aus der Engine-Erfassung des Skripts; Inhalt hier nur mit eigenen Worten wiedergegeben.
  - Grenzen: Formeltranskription von vier Beweis-KCs ist laut Engine unsicher (HUMAN_DECISION_REQUIRED); Wortlaut wird nicht wiedergegeben.
  - Funktion: legt den Prüfungsstoff und die Nummerierung fest
- **lebl** [extension, textbook, Zugriff: full_text] Lebl, J.: Basic Analysis I: Introduction to Real Analysis, Version 6.3, 15. Mai 2026. Lizenz CC BY-NC-SA 4.0 / CC BY-SA 4.0. https://www.jirka.org/ra/
  - §2.2, Beispiel 2.2.8 (S. 66–67): x₁ = 2, xₙ₊₁ = xₙ − (xₙ² − 2)/(2xₙ): Wohldefiniertheit und Positivität per Induktion, Monotonie über xₙ₊₁² − 2 = (xₙ² − 2)²/(4xₙ²) ≥ 0, Grenzwert √2; Hinweis: mit negativem x₁ ergibt sich −√2; als Newton-Verfahren bezeichnet.
  - §2.1, Satz 2.1.10 (Monotone convergence theorem): Eine monotone Folge ist genau dann beschränkt, wenn sie konvergiert.
  - §2.3.3, Satz 2.3.8 (Bolzano–Weierstraß): Beschränkte Folgen besitzen eine konvergente Teilfolge.
  - §2.4, Beispiel 2.4.3: (−1)ⁿ ist keine Cauchy-Folge (Nachweis mit n gerade, k = n + 1).
  - §7.6.1, Def. 7.6.1 und Satz 7.6.2: Kontraktion = k-Lipschitz mit k < 1; jede Kontraktion eines nichtleeren vollständigen metrischen Raums hat genau einen Fixpunkt; „The words complete and contraction are necessary. See Exercise 7.6.6.“ (Aufgabe 7.6.6 b: 1-Lipschitz-Abbildung ohne Fixpunkt).
  - Grenzen: Englisch, metrische Räume allgemeiner als die Vorlesung; Nummerierung weicht vom Skript ab.
  - Funktion: offen zugängliche zweite Darstellung mit vollständigen Beweisen; Grundlage für E1 (erweitert um Fehleridentität und ℚ-Gegenbeispiel) und E2 (Gegenbeispiel x + 1/x zu Aufgabe 7.6.6 b)

## Labore
- folgen: Folgen & Grenzwerte – ε-Streifen mit Beweis/Test-Unterscheidung, Gegenbeispielsuche, Spinnwebdiagramme für Rekursionen und Kontraktionen

## Lernstand
Kein Lernstand erhoben. Beginne mit einer kurzen Diagnose; erfinde keinen Lernstand.
