# Tutor-Kontext: Entrepreneurship – Funding a Venture

Modul `ent-funding` · Fach: business · erzeugt 2026-11-15

## Offizieller Rahmen
Kapitel 6 der Vorlesung Entrepreneurship: Finanzierungsformen (Eigen-, Mezzanine-, Fremdkapital), Risiko und Insolvenz, Lebens- und Finanzierungszyklus, Business Angels, Venture Capital (Fondsstruktur, Potenzialanforderung), Finanzierungsprozess (Deal Origination, Screening, Closing, Tranchen, Exit), Scheitern von Start-ups, HTGF-Beispiel mit Wandeldarlehen, Pre-/Post-Money-Bewertung und Verwässerung über zwei Runden.

Offizielle Kursquellen (definieren den Prüfungsstoff): Vorlesungsfolien Entrepreneurship, Kap. 6 „Funding a Venture“ (private Kursunterlage; Abschnittstitel als Lokatoren)

## Prüfung
Offizielle Angaben zu Dauer und Hilfsmitteln liegen nicht vor. Kapitelbezogen prüfbar: Begriffe und Unterschiede der Kapitalformen, Phasen- und Investorenlogik, Rechnungen zu Pre-/Post-Money, Anteilen und Verwässerung, Begründung der VC-Potenzialanforderung.

## Notation
- V_pre, V_post: Bewertung vor bzw. nach der Investition I; V_post = V_pre + I
- I/(V_pre + I): Anteil des neuen Investors nach der Runde
- A, C, d: SAFE-Betrag, Post-Money-Cap, Rabatt
- TVPI: Netto-Rückfluss an Fondsinvestoren / Fondsgröße (hier vereinfacht)

## Kompetenzen
### formen · Kapitalformen und Risikoklassen (Klausurkern)
Voraussetzungen: ext:Bilanz Grundbegriffe
- Ziel: Eigen-, Mezzanine- und Fremdkapital nach Haftung, Rückzahlung, Mitsprache unterscheiden
- Ziel: Liquidationsrangfolge an einem Beispiel durchrechnen
- Typische Fehlvorstellung: Eigenkapital ist kostenlos, weil keine Zinsen anfallen
Lernprodukte: {}
Quellen: kurs

### zyklus · Lebens- und Finanzierungszyklus, passende Kapitalquelle (Klausurkern)
Voraussetzungen: formen
- Ziel: Begründen, warum Banken frühe Start-ups kaum finanzieren
- Ziel: Business Angel vs. VC nach Motiv und Kriterien abgrenzen
Lernprodukte: {}
Quellen: kurs, htgf

### vc · VC-Fondslogik und Potenzialanforderung (Klausurkern)
Voraussetzungen: zyklus
- Ziel: Mit Fondsgröße, Anteil und Gebühren berechnen, welcher Exit den Fonds zurückzahlt
- Ziel: Erklären, warum wenige Ausreißer die Rendite tragen
- Typische Fehlvorstellung: Ein VC optimiert die Überlebenswahrscheinlichkeit einzelner Beteiligungen
Lernprodukte: {"lab": [{"lab": "runden", "item": "v4"}, {"lab": "runden", "item": "w-fund"}], "tasks": ["EN3"]}
Quellen: kurs

### prozess · Finanzierungsprozess, Tranchen, Vertragsrechte (Vertiefung)
Voraussetzungen: vc
- Ziel: Begründen, warum in Tranchen ausgezahlt wird
- Ziel: Trennung von Cash-Flow- und Kontrollrechten erläutern
Lernprodukte: {}
Quellen: kurs, kaplan-stromberg

### bewertung · Pre-/Post-Money, Wandelinstrumente und Verwässerung (Klausurkern)
Voraussetzungen: formen
- Ziel: Kapitalisierungstabelle über SAFE/Wandeldarlehen, Seed und Serie A aufstellen
- Ziel: Cap und Rabatt vergleichen
- Ziel: Verwässerung von Wertverlust unterscheiden
- Typische Fehlvorstellung: Verwässerung bedeutet immer Geldverlust
- Typische Fehlvorstellung: Optionspool belastet den neuen Investor
- Typische Fehlvorstellung: höherer Cap kann dem Investor mehr geben
Lernprodukte: {"lab": [{"lab": "runden", "item": "v1"}, {"lab": "runden", "item": "v2"}, {"lab": "runden", "item": "v3"}, {"lab": "runden", "item": "w-imp"}], "tasks": ["EN1", "EN2", "EN4"]}
Quellen: kurs, yc-safe

## Übungsaufgaben (ohne Lösungen; Schlüssel separat in answer_key.md)
- **EN1** (bewertung, worked): Stellen Sie die Kapitalisierungstabelle aus Beispiel X1 nach Seed auf: SAFE-Aktien, neue Pool-Aktien, Preis je Anteil, Anteile aller Gesellschafter.
- **EN2** (bewertung, transfer): Gleiche Daten wie X1, aber Seed-Pre-Money nur 5 Mio. €. Gilt für den SAFE der Cap oder der Rabatt? Begründen Sie mit beiden Umwandlungspreisen.
- **EN3** (vc, independent): Ein 150-Mio.-€-Fonds hält bei Exit typischerweise 12 % je Beteiligung. Ab welchem Exitwert zahlt eine einzelne Beteiligung den Fonds zurück? Welcher Bruttorückfluss ist für 2× netto bei 20 % Carry nötig?
- **EN4** (bewertung, error): Die Folie sagt: „Verwässerung bedeutet, dass die Gründer Geld verlieren.“ Formulieren Sie die Aussage so, dass sie stimmt, und belegen Sie mit X1.

## Eigene, geprüfte Beispiele
- **X1** (bewertung): Drei Runden mit Post-Money-SAFE: Anteil sinkt, Wert steigt – Gründer mit 1 Mio. Anteilen; SAFE 500 Tsd. € bei Post-Money-Cap 5 Mio. € (20 % Rabatt); Seed 2 Mio. € bei 8 Mio. € Pre-Money mit 10 % Pool-Ziel; Serie A 6 Mio. € bei 24 Mio. € Pre-Money. Ergebnis (exakt): SAFE vor Seed 10 %, nach Seed 7 %; Gründer 63 % → 50,4 %; Preis je Anteil 6,30 € → 15,12 €; Gründerwert 6,3 → 15,12 Mio. €. Gegenbeispiele: Down-Round (Pre-Money 6 Mio. €) senkt den Gründerwert auf 3,78 Mio. €; bei Seed-Pre-Money 5 Mio. € greift der Rabatt statt des Caps.
- **X2** (vc): Fondslogik: Was ein Exit leisten muss – 100-Mio.-€-Fonds, 15 % Anteil bei Exit: Ein Exit zahlt den Fonds ab ≈ 667 Mio. € zurück. 25 solide Exits zu je 40 Mio. € ergeben nur 1,4× netto (nach 20 % Carry); für 3× netto braucht es 350 Mio. € brutto, also einen Exit von ≈ 2,33 Mrd. €. Eigene Rechnung, keine Marktdaten.
- **X3** (bewertung): Zahlenprobe der Aufgaben EN1–EN3 – Prüft alle Zahlen der Arbeitsaufgaben unabhängig.

## Geprüfte Quellen (nur diese zitieren)
- **kurs** [official, lecture, Zugriff: private_course_material] Vorlesungsfolien Entrepreneurship, Kapitel 6 „Funding a Venture“ (private Kursunterlage des Nutzers, nicht veröffentlicht) 
  - Abschnitte Kapitalformen, Insolvenz, Lebenszyklus, Business Angels, Venture Capital, Finanzierungsprozess, HTGF-Beispiel mit Wandeldarlehen, Verwässerung über zwei Runden: Gliederung aus der Engine-Erfassung; Inhalt nur mit eigenen Worten.
  - Grenzen: Marktzahlen der Folien wurden nicht unabhängig geprüft und werden nicht übernommen.
  - Funktion: legt Prüfungsstoff und Fragestellungen fest
- **yc-safe** [extension, docs, Zugriff: section] Y Combinator: Post-Money SAFE User Guide (inkl. Quick Start Guide), abgerufen über ycombinator.com/documents https://www.ycombinator.com/documents
  - Quick Start Guide, S. 1, Nr. 1: Verkaufter Anteil = Betrag / Post-Money-Cap; Beispiel 1 Mio. $ bei 15 % ⇒ Cap ≈ 6,7 Mio. $; 500 Tsd. $ ⇒ ≈ 7,5 %.
  - Quick Start Guide, S. 2, Note #2: SAFE-Anteil ist „post-safes“, nicht „post-Series A“; SAFEs werden in der Serie A verwässert wie alle anderen.
  - User Guide, S. 3–4: Cap ist „post“ aller SAFE-Gelder, NICHT „post“ der Eigenkapitalrunde; „post“ bestehender Optionen und Pools, NICHT eines in der Serie A neu geschaffenen oder aufgestockten Pools.
  - Grenzen: US-Instrument nach US-Recht; in Deutschland sind Wandeldarlehen bzw. andere Gestaltungen üblich. Die Rabatt-Umwandlung wird im Labor vereinfacht modelliert (Rabattpreis auf den Rundenpreis, günstigere Variante gilt).
  - Funktion: präzise Definition des Post-Money-Caps als Grundlage der Kapitalisierungstabelle im Labor und in X1
- **htgf** [extension, practice, Zugriff: section] High-Tech Gründerfonds: „Our investment criteria – Your chance“, htgf.de (englische Startseite, Stand der Seite 2026-11-09) https://www.htgf.de/en/
  - Abschnitt „Our investment criteria“: Erstinvestitionen in Pre-Seed/Seed typischerweise ab 800 000 €; in Wachstumsrunden bis zu 30 Mio. €; Unternehmen höchstens drei Jahre alt; Sitz oder Betriebsstätte in Deutschland.
  - Grenzen: Selbstdarstellung; Instrument (Eigenkapital/Wandeldarlehen) und Gesamtvolumen je Unternehmen auf der Seite nicht angegeben; Konditionen ändern sich – Datum beachten. Die Zahlen des Folienbeispiels können ältere Konditionen zeigen.
  - Funktion: datierter Abgleich des Folienbeispiels mit den aktuellen Kriterien
- **kaplan-stromberg** [extension, working_paper, Zugriff: abstract] Kaplan, S. N.; Strömberg, P. (2003): Financial Contracting Theory Meets the Real World: An Empirical Analysis of Venture Capital Contracts. Review of Economic Studies 70(2), 281–315; NBER Working Paper 7660 (2000). https://www.nber.org/papers/w7660
  - Abstract (RES und NBER): VC-Finanzierungen trennen Cash-Flow-, Board-, Stimm-, Liquidations- und andere Kontrollrechte; Wandelpapiere am häufigsten; Folgefinanzierungen oft an beobachtbare Kennzahlen geknüpft; bei schlechter Entwicklung übernehmen VCs die Kontrolle, bei sehr guter geben sie Kontroll- und Liquidationsrechte weitgehend ab.
  - Grenzen: Nur Abstract gelesen: Stichprobe, Methode und Effektgrößen nicht geprüft; keine Ergebnisse über das Abstract hinaus verwenden.
  - Funktion: Forschungsfrage für die Vertiefung „Warum Tranchen und getrennte Rechte?“

## Labore
- runden: Finanzierungsrunden & Fondslogik – Kapitalisierungstabelle mit SAFE (Cap/Rabatt), Pool-Shuffle, Up-/Down-Round, Fonds-Multiple

## Lernstand
Kein Lernstand erhoben. Beginne mit einer kurzen Diagnose; erfinde keinen Lernstand.
