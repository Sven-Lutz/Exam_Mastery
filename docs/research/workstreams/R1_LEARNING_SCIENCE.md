# R1 — Lernwissenschaft, Neurowissenschaft und nachhaltig intensives Lernen: Synthese und Learning Policies

Stand 27.11.2026. **Forschungsergebnis zur Begutachtung, keine Freigabe.** Alle 23 Policies sind `design_hypothesis` mit `learning_evaluation: NOT_RUN`. Keine Policy ist implementiert; kein Exam-Mastery-Produkt hat dadurch eine nachgewiesene Lernwirkung. Historische `HUMAN_REJECTED`-Bewertungen bleiben unverändert.

**Produktidentität:** Seit Issue #34 heißt das Produkt **Mastery** (vormals Exam Mastery), eine allgemeine Plattform für Wissens- und Fertigkeitserwerb. R1 wurde mit Blick auf intensive Prüfungsvorbereitung recherchiert. Policies mit Prüfungsbezug (B02, B08, die Prüfungswochenfälle in A05 und CR-4) gelten im optionalen Modus Prüfungsvorbereitung, alle übrigen unabhängig davon. Pfade, Schema-Namen und Bezeichner bleiben unverändert.

| Artefakt | Inhalt |
|---|---|
| [r1/R1A_COGNITIVE_INSTRUCTIONAL.md](r1/R1A_COGNITIVE_INSTRUCTIONAL.md) + [r1/r1a_evidence.json](r1/r1a_evidence.json) | Abruf, Verteilung, Interleaving, kognitive Belastung, Worked Examples, Expertise Reversal, Productive Failure, Selbsterklärung, Feedback, Kalibrierung, Transfer. 31 Quellen, 12 auf Volltextebene. Policies A01–A11. |
| [r1/R1B_NEURO_INTENSITY.md](r1/R1B_NEURO_INTENSITY.md) + [r1/r1b_evidence.json](r1/r1b_evidence.json) | Schlaf, Ermüdung, Pausen, Aufmerksamkeit, Motivation, Stress, Bewegung, gezieltes Üben, Expertise, nachhaltige Intensität, Neuromythen, medizinische Grenze. 42 Quellen, 13 auf Volltextebene. Policies B01–B12. |
| [r1/r1_learning_policies.json](r1/r1_learning_policies.json) | Maschinenlesbare Policies, Konfliktregeln, gemeinsamer Messvertrag, Zuständigkeiten, Prüfprotokoll. |
| `tests/test_r1_learning_policies.py` | 12 deterministische Konsistenzprüfungen (Quellen auflösbar, Zahlen als vorläufig markiert, jede Engine-Regel entschieden, kein erfundener Validierungsstatus). Prüft Struktur, nicht wissenschaftliche Richtigkeit. |

Arbeitsteilung: zwei Spezialisten-Agenten recherchierten getrennt (Suchjournal, Zugangsstufen und Screening in ihren Berichten §1). Der Lead schrieb diese Synthese, prüfte Kernzahlen stichprobenartig an den Quellen, korrigierte zwei Policies und löste Konflikte zwischen den Policies auf. Der Lead ist nicht Autor der Spezialberichte, aber dasselbe Modell; eine menschliche oder unabhängige Fachprüfung steht aus.

## 1. Ergebnis in zehn Punkten

1. **Abruf ist operationsspezifisch.** Quizzing mit Korrektur stärkt verzögertes Behalten von Kursinhalten in Hochschulklassen robust (`yang2021classroom`, g = 0,499; gegen Wiederlesen 0,330). Beim Erwerb eines neuen Lösungsverfahrens aus Worked Examples brachte Testen in vier Experimenten keinen Zusatznutzen (`vangog2015testingwe`). In Mathematik ist Testen gegen Wiederlesen metaanalytisch nicht robust (`murray2025mathspacing`), für Transfer-Outcomes in Schulklassen nicht nachweisbar (`ruitenburg2026classroom`). Die bisherige Engine-Regel „jede Einheit endet mit Abruf“ (RP-R1) ist damit zu grob.
2. **Verteilung wirkt, in Mathematikkursen aber klein** (kursintegriert g = 0,24); ein Hochschulexperiment zu einer Rechenprozedur fand keinen Effekt. Feste Intervallkonstanten lassen sich daraus nicht ableiten; Anki bleibt Scheduler.
3. **Interleaving verbessert die Methodenwahl** in einer großen präregistrierten Schul-RCT (`rohrer2020interleaved`, d = 0,83), ist dort aber mit Verteilung konfundiert. Für Hochschulmathematik indirekt, für Recht und Medizin unbelegt.
4. **Novizen brauchen zuerst Beispiele, Fortgeschrittene nicht.** Eine valide Schnelldiagnose für den Umschaltpunkt ist für Hochschulfächer nicht belegt; Übergänge müssen reversibel sein.
5. **Selbsterklärungsprompts helfen gegenüber keiner Zusatzerklärung** (`bisra2018`, g = .55), gegenüber einer guten Instruktionserklärung nur wenig (.35, k = 6); rein metakognitive und Multiple-Choice-Prompts nicht nachweisbar.
6. **Productive Failure bleibt niedrig gesichert**: Hauptmetaanalyse nur als Abstract zugänglich, eine ungewöhnliche biasadjustierte Schätzung ungeklärt, randomisierte Gegenbefunde bei hoher Elementinteraktivität.
7. **Feedback-Zeitpunkt ist auf Aufgabenebene kein Hebel** (ManyClasses: 0,002 [−0,05; 0,05]); korrektive Information nach dem Abruf ist es eher. **Lernurteile sind nicht neutral:** Gedächtnisurteile während des Übens kehrten den Testeffekt in zwei Experimenten um.
8. **Schlafverlust schadet der Gedächtnisbildung im Labor** (vor dem Lernen adjustiert g = 0,463, nach dem Lernen 0,166; Restriktion 0,29), aber eine einzelne Nacht vor der Prüfung war in einer Hochschulkohorte nicht mit Noten assoziiert. Schlafschutz gehört in die Planung über Wochen, nicht in Angstbotschaften über die letzte Nacht.
9. **Mehrere populäre Intensitätsannahmen tragen nicht:** Ego-Depletion repliziert nicht; keine universelle Tagesobergrenze („4 h“ ist eine Hypothese aus kleinen Musik-/Schachstichproben); Übungsmenge erklärt in Bildung nur einen kleinen Leistungsanteil; Sport-, Mindset- und „Handy-Präsenz“-Effekte liegen nach Biaskorrektur bzw. Replikation nahe null.
10. **Pausen verbessern Befinden, nicht nachweislich Lernen**; keine Pausenstudie mit Behaltensmaß gefunden. Wohlbefindensfunktionen sind daher Angebote mit ehrlicher Begründung, keine Lernversprechen.

## 2. Entscheidung je bestehender Engine-Regel

Jede der 30 Regeln in `exam_mastery/knowledge/principles.json` hat jetzt eine R1-Entscheidung oder einen benannten Zuständigen (Test `test_every_existing_engine_rule_is_reviewed`).

| Regel | R1-Entscheidung | Kern der Änderung |
|---|---|---|
| RP-R1 | präzisiert (A01, A02, B06) | Abruf für abrufbare Bausteine und nach passiven Inputs; nicht als Ersatz für Beispielstudium beim Verfahrenserwerb |
| RP-R2, RP-R3 | beibehalten (A08, A01) | Lösung erst nach eigenem Versuch; Korrektur nach jedem Abruf |
| SP-R1 | beibehalten (A01, A05) | Anki bleibt einziger Scheduler |
| SP-R2 | präzisiert (A05) | spätere Prüfung mit neuer Aufgabe nach **verstrichener Zeit**, nicht nach neuem Kalenderdatum; kumulative Wiederaufnahme |
| IL-R1 | präzisiert (A04) | erst geblockte Einführung je Typ, dann Mischen mit Distraktoritem; Wirkung ggf. Verteilung |
| WE-R1, WE-R2 | präzisiert (A02, A03) | Beispiele zuerst für Novizen; Übergang nach wiederholtem Erste-Schritt-Erfolg, reversibel; keine Einstufung aus einem Item, keine automatische Einstufung bei Beweisen |
| PF-R1 | präzisiert (A07) | Erkundung zuerst nur optional, mit Voraussetzungstest, Zeitreserve und Pflichtkonsolidierung |
| SE-R1, SE-R2 | präzisiert/beibehalten (A06) | offene, schrittbezogene Prompts mit Referenz erst nach eigener Antwort; freie Erklärungen bleiben unverifiziert |
| FB-R1, FB-R2 | präzisiert/beibehalten (A08, B07) | keine Timing-Regel; Hilfestatus getrennt ausweisen; Fehlerdiagnose nur bei eindeutigen Fehlern |
| MC-R1 | präzisiert (A09) | Konfidenz stichprobenartig, bevorzugt retrospektiv; keine Urteile nach jedem Item in gemessenen Modi |
| MC-R2 | präzisiert (B05) | auch Minuten, Streaks und Stunden-Badges zählen nicht als Fortschritt |
| TR-R1 | präzisiert (A10) | Strukturvergleich mit Prinzip danach und Kontrastfall; kein Ferntransferanspruch |
| LS-R1 | beibehalten (B11) | Teil eines Registers verbotener Produktbehauptungen |
| neu | A11, B01–B04, B06, B08–B10, B12 | Vorfragen, Schlafschutz, Prüfungswoche, Pausen, Lasthinweise, Aufmerksamkeit, Stress, Bewegung, Off-Zeiten, medizinische Grenze |
| PR-R1–R3, MM-R1–R2, CL-R1–R2 | an R7/R2 | Lab-, Multimedia- und Darstellungsregeln; R1-Hinweis zur Belastungsmessung (`dejong2010clt`) mitgegeben |
| ITS-R1–R2, AI-R1–R2 | an R5 | Tutor und Mastery-Modelle |
| AS-R1–R2 | an R2/R5 | Aufgabenmetadaten und Blueprint |

Vorgeschlagene Textkorrekturen an KB-Claims (rp.3, rp.4, sp.1/2, sp.4, il.2, se.1, pf.1, fb.3, mc.*, cl.*, tr.1) stehen in R1A §5.12. Sie sind **nicht angewendet**; die Übernahme in die KB ist ein eigener Schritt nach Prüfung.

## 3. Policy-Übersicht

Stufe = interne Einschätzung der **Produktregel**; Teilaussagen mit anderer Stufe stehen in der JSON-Datei (`sub_claims`).

| ID | Operation | Kernregel | Stufe |
|---|---|---|---|
| A01 | Abruf/Diskrimination | Abruf mit Korrektur und Successive Relearning für Bausteine, Scheduling über Anki | moderate |
| A02 | Prozedur, Programmieren | Beispiele vor Abruf bei Novizen; erst eigenständiges Isomorph, dann Abruf | moderate |
| A03 | Prozedur | reversible Erste-Schritt-Probe für Fading | very_low |
| A04 | Prozedur, Methodenwahl | Mischen verwechselbarer Typen nach Erstkontakt | low |
| A05 | Abruf, Prozedur | verteilt und kumulativ statt massiert; keine eigenen Intervalle | moderate |
| A06 | Prozedur, Beweisverständnis, Fallbegründung, Code | offene Schritt-Selbsterklärung, Referenz danach | moderate |
| A07 | Prozedur (konzeptuell) | Problemlösen vor Instruktion nur optional und konsolidiert | low |
| A08 | Abruf, Prozedur, Code | Korrektur nach jedem Versuch; Hinweise nach Versuch; Hilfeabhängigkeit messen | moderate |
| A09 | Selbstregulation | Konfidenz als Daten, stichprobenartig, retrospektiv | low |
| A10 | Abruf, Prozedur | Fallvergleich, Prinzip danach, Kontrastfall | low |
| A11 | Abruf | Vorfragen optional, nur begleitet | low |
| B01 | Selbstregulation | Schlaffenster im Planer geschützt, nie Nachtschichten | low |
| B02 | Selbstregulation | Prüfungswoche: Erstlernen mindestens eine Nacht vorher, leichter Vorabend | low |
| B03 | Selbstregulation | Pausen als abschaltbares Befindensangebot | very_low |
| B04 | Selbstregulation | Lasthinweise relativ zur eigenen Basis, keine Stundenquote | very_low |
| B05 | Selbstregulation | Fortschritt = verzögerte unassistierte Leistung, nicht Stunden | low |
| B06 | Selbstregulation, Abruf | passive Inputs segmentieren, Zwischenabruf | low (Lead-Korrektur) |
| B07 | Selbstregulation | autonomieunterstützende Sprache, keine Verlustmechaniken | low |
| B08 | Selbstregulation | Prüfungsangst: Simulation statt Versprechen | low |
| B09 | Selbstregulation | keine Kognitionsversprechen für Sport | moderate |
| B10 | Selbstregulation | Off-Fenster für Erinnerungen, leichter Tag als Default | very_low |
| B11 | alle Produkttexte | Register verbotener Produktbehauptungen | moderate |
| B12 | Selbstregulation | medizinische Grenze, Verweis, keine Gesundheitsdaten als Default | normative |

Kein Eintrag ist `high`: Selbst gut belegte Richtungen (Abruf, Verteilung) werden durch Indirektheit zur Hochschulpopulation, Heterogenität und den Abstand zwischen Laborbefund und Produktregel begrenzt.

## 4. Zusammengesetzte Lernsequenz (Eingabe für R6)

Die Policies ergeben keine universelle „Seite → Karte → Simulation“-Pipeline, sondern eine vom Kontext abhängige Abfolge. Eingaben: Lernoperation, Phase, belegtes Vorwissen, verbleibende Zeit bis zur Prüfung, Schlaf-/Off-Fenster, jüngste Last.

1. **Erarbeitung.** Neues Verfahren und Novize → Worked Examples mit Schritt-Selbsterklärung (A02, A06). Neues Konzept, Voraussetzungen bestanden, ≥ 2 Wochen Zeit → optional kurzes Erkundungsproblem mit Pflichtkonsolidierung (A07). Deklarative Bausteine → Erklärung, optional Vorfragen (A11), dann Abruf (A01). Lange passive Inputs segmentiert mit Zwischenabruf (B06).
2. **Übergang.** Erste-Schritt-Proben an unbekannten Isomorphen, reversibel; keine automatische Einstufung bei Beweisen oder mehrdeutigen ersten Schritten (A03).
3. **Übung.** Abruf und Lösungsversuche mit korrigierender Information, Hinweise erst nach eigenem Versuch, Hilfestatus getrennt (A01, A08). Verwechselbare Typen erst nach Übergang mischen (A04). Strukturvergleich mit Kontrastfall vor der Prüfung (A10).
4. **Planung.** Atomare Items über Anki; Aufgaben kumulativ und verteilt (A05). Planung innerhalb des Schlaf- und Off-Fensters (B01, B10), Lasthinweise nur relativ zur eigenen Basis (B04), Prüfungswochenregeln (B02). Reicht die Zeit nicht: Umfang nach Prüfungsgewicht priorisieren, nie Schlaf kürzen (CR-4).
5. **Evidenz.** Lernstand nur aus unassistierten, verzögerten Versuchen an neuen Items (gemeinsamer Messvertrag); Konfidenz stichprobenartig als Daten (A09); Fortschrittsanzeige ohne Stunden (B05).
6. **Sprache und Grenzen.** Autonomieunterstützend, ohne Verlustmechanik (B07); verbotene Behauptungen (B11); medizinische Grenze und Datenschutz (B12).

Für R6 relevant: Diese Sequenz braucht ein **Operations- und Kontextmodell** (welche Operation, welche Phase, welche Belege), einen **Hilfestatus je Versuch** und **echte Zeitstempel**, aber keinen eigenen Scheduler und keine kalibrierte Mastery-Wahrscheinlichkeit. Ob das besser als deklarativer Kompetenzgraph mit Policy-Engine (Architektur B) oder als Vorlagen plus Expertenmodule (A) umgesetzt wird, entscheidet R6.

## 5. Konfliktregeln und gemeinsamer Messvertrag

Acht Konfliktregeln (CR-1 bis CR-8) stehen in der JSON-Datei; die wichtigsten: Beispiele schlagen Abruf beim Verfahrenserwerb (CR-1); Instruktion zuerst ist Standard, Erkundung zuerst nur unter Bedingungen (CR-2); Zeitknappheit kürzt Umfang, nie Schlaf (CR-4); assistierte Versuche zählen nie als Kompetenzbeleg (CR-6); Wohlbefindensfunktionen lösen keinen neuen Planer-Ausbau aus, solange R6 keinen Planer beschließt (CR-8).

**Messvertrag:** Kompetenzbeleg ist nur ein unassistierter Versuch nach echter verstrichener Zeit an einem neuen oder umformulierten Item. Kein Beleg: gelesene Seiten, Minuten, verschiedene Kalenderdaten ohne verstrichene Zeit, Versuche mit Hinweis oder sichtbarer Lösung, Konfidenzangaben, Anki-Statistik als Kompetenz.

**Übergabe an Engineering (P4, nach R6):** Der kritische Defekt CD-2 (`policy.kc_status` zählt verschiedene Kalenderdaten als Spacing-/Mastery-Beleg) widerspricht A01, A05 und dem Messvertrag direkt und ist der erste konkrete Engine-Fix aus R1.

## 6. Gegenprüfung durch den Lead

**Stichprobe an den Quellen** (NCBI E-Utilities bzw. Crossref-Abstract, 27.11.2026): Newbury 2021 (g = 0,277/0,621), Crowley 2024 (g = 0,29; 125 Effekte, 39 Berichte, 1234 Personen), Macnamara 2014 (26/21/18/4/< 1 %), Yang 2021 (g = 0,499), ManyClasses (0,002 [−0,05; 0,05]), Ruitenburg 2026 (0,37/0,20/0,40), Sinha 2021 (0,36): **alle übereinstimmend.** Nicht unabhängig geprüft, weil kein Abstract maschinell abrufbar war: Rohrer 2020 (d = 0,83), Bisra 2018 (g = .55), Murray 2025. Adjustierte Werte, Tabellenwerte und Moderatoren wurden nicht nachgerechnet. Zu Macnamara 2014 existiert ein Corrigendum (Psychol Sci 2018), dessen Inhalt nicht gelesen wurde.

**Korrekturen des Leads:**
- A05: Die von R1A vorgeschlagene Abstandsregel „10–30 % der Restzeit“ ist eine Umformung der Cepeda-Retentionsfläche für Faktenlernen, vor der R0-D4 ausdrücklich warnt. Ersetzt durch Anki plus mindestens zweimalige kumulative Wiederaufnahme je Thema (vorläufige Setzung).
- B06: Policy-Stufe von `moderate` auf `low` gesenkt; die Teilaussage zu interpolierten Tests bleibt `moderate`, die Produktwirkung ist aus Abstracts kurzer Laborvorlesungen nicht moderat belegt.
- A09: Die Änderung an MC-R1 (prospektive Einschätzung vor jedem Lösen) stützt sich auf Reaktivitätsbefunde mit Wortmaterial; die Übertragung auf Problemlösen ist ungeklärt und als solche markiert.

**Restrisiken der Extraktion:** Drei Volltexte stammen aus Kopien Dritter (Yang, Rohrer, Bisra), vier wurden über werkzeuggenerierte Seitenzusammenfassungen gelesen (Ruitenburg, Pan & Carpenter, Janssen & Lazonder, Ebersbach). Zahlen daraus vor einer KB-Übernahme am Original prüfen. Hauptquellen ohne Volltext: Sinha & Kapur 2021, Barbieri 2023, Kalyuga & Sweller 2004, Plant 2005; R1B zu 28 von 42 Quellen nur Abstract.

**Umfangsdisziplin:** Die B-Policies betreffen vor allem einen Planer, den Exam Mastery heute nicht hat. Sie begründen keinen neuen Produktbaustein. Sofort produktrelevant sind B05 (Fortschritt), B07 (Sprache), B11 (verbotene Behauptungen) und B12 (Grenze und Datenschutz); B01–B04 und B10 erst, wenn R6 einen Planer beschließt.

## 7. Abdeckung des R1-Auftrags und Lücken

| Thema | Ort | Status |
|---|---|---|
| Abruf, Verteilung | A01, A05 | bearbeitet |
| Interleaving | A04 | bearbeitet; Hochschule indirekt |
| Cognitive Load, Worked Examples, Expertise Reversal | A02, A03; `dejong2010clt` | bearbeitet; Umschaltdiagnose offen |
| Productive Failure | A07 | bearbeitet; Hauptquelle nur Abstract |
| Selbsterklärung | A06 | bearbeitet |
| Metakognition, Kalibrierung | A09 | bearbeitet; Leistungsnutzen offen |
| Feedback, gezieltes Üben | A08; B04, B05 | bearbeitet |
| Expertiseentwicklung | B04, B05 (Ericsson, Macnamara) | teilweise; Kompetenzentwicklung über Monate/Jahre nicht untersucht |
| Aufmerksamkeit, Motivation | B06, B07 | bearbeitet |
| Schlaf, Konsolidierung, Erholung, Ermüdung | B01–B03, B10 | bearbeitet; Chronotyp offen |
| Nachhaltig intensives Lernen | B04, B05, B10, B12 | bearbeitet; keine Interventionsstudie |
| Transfer, langfristige Kompetenz | A10 | teilweise |

**Priorisierte Lücken:** (1) Volltexte Sinha & Kapur 2021 und Barbieri 2023; (2) Umschaltdiagnose für Fading an Hochschulaufgaben (Fehlklassifikationsraten); (3) Interleaving und Abruf für juristische Subsumtion und klinische Diagnose (R3); (4) Leistungsnutzen von Kalibrierungsanzeigen; (5) Successive-Relearning-Kriterien (Rawson & Dunlosky) im Volltext; (6) Pausenstudien mit Behaltensmaß; (7) Prüfungsangst-Metaanalysen; (8) Chronotyp und Schichtarbeit; (9) langfristige Kompetenzentwicklung über Semester.

**Übergaben:** R2 (Beweiskonstruktion, Debugging, Messvertrag für unassistierte mathematische Kompetenz), R3 (Hypothesen aus A04/A10 für Recht und Medizin), R4 (motorisches Lernen, `embodied_psychomotor`), R5 (Hilfeabhängigkeit aus A08, Tutor-Regeln AI-R1/R2, Mastery ohne Wahrscheinlichkeit), R7 (CL-, MM-, PR-Regeln), R8 (Anki bleibt Scheduler, A01/A05), R6 (Abschnitt 4).

## 8. Was wir nicht behaupten können

- Dass eine dieser Policies in Exam Mastery Lernen verbessert: keine Evaluation, keine Implementierung.
- Dass die Stufen eine externe GRADE-Bewertung sind: es ist eine interne Einschätzung eines Modells ohne zweite unabhängige Extraktion.
- Dass Laborbefunde (Schlaf, Abruf mit Wortmaterial, Urteilsreaktivität) auf Hochschulprüfungen in Mathematik, Recht oder Medizin übertragbar sind.
- Dass eine Zahl in den Policies empirisch optimal ist; alle Parameter sind vorläufige Produktsetzungen.
- Dass Wohlbefindensfunktionen Prüfungsleistung verbessern, oder dass ein Produkt Burnout, Schlafstörungen oder Angst erkennen oder behandeln kann.
- Dass die Stichprobenprüfung des Leads die übrigen Zahlen bestätigt; sie deckt sieben Kernwerte ab.

## 9. Reproduktion

```bash
python -m unittest tests.test_r1_learning_policies   # 12 Strukturprüfungen
python -c "import json; [json.load(open('docs/research/workstreams/r1/'+f)) for f in ('r1a_evidence.json','r1b_evidence.json','r1_learning_policies.json')]"
```

Suchjournale, exakte Queries, gescheiterte Abrufe und Zugangsstufen: R1A §1 und R1B §1. Keine Volltexte, Vorlesungsmaterialien oder Lernerdaten im Repository; Befunde sind paraphrasiert mit Fundstellen.
