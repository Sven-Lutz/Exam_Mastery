# R7 — Lernressourcen, Visualisierung, Interaktiv-Referenzen und Wiederverwendungskandidaten

Version 0.1, 27.11.2026. Branch `research/r7-resources-20261127` (Basis `research/r1-learning-science-20261127`). Issue [#29](https://github.com/Sven-Lutz/Exam_Mastery/issues/29). Autor: R7-Spezialagent. **Unabhängige Prüfung: ausstehend.** Kein Dokument hier behauptet Lernwirksamkeit eines Produkts oder einer Policy; alle Policies sind `design_hypothesis` mit `learning_evaluation = NOT_RUN`, alle Entscheidungen sind Empfehlungen zur Begutachtung.

Artefakte:

| Datei | Inhalt |
|---|---|
| [r7/r7_resources.json](r7/r7_resources.json) | 30 Ressourcenkarten, 20 erhaltene Verweise (R8/R9/§B), 6 erhaltene Ideen (§D/§E), Shortlist (8) |
| [r7/r7_evidence.json](r7/r7_evidence.json) | 14 wissenschaftliche Quellen im R1-Evidenzschema + Suchjournal S01–S11 |
| [r7/r7_resource_policies.json](r7/r7_resource_policies.json) | R7-POL-01..10 im R1-Policy-Schema |
| [../../../tests/test_r7_resources.py](../../../tests/test_r7_resources.py) | Vertrags- und Erhaltungstests |

## 1. Ergebnis in Kürze

1. **Keine neue Plattform, keine fünfte Produktfläche, kein zweiter Scheduler.** Von 30 bewerteten Ressourcen wird genau eine als Bibliothek empfohlen (Pyodide, nur nach bestandenem Offline-/Größen-/Abbruch-Spike). Zehn liefern ein klar benanntes Prinzip zur Emulation, fünf sind nur optionale Links, zehn sind vertagt (sechs wegen fehlender Identität, fehlenden Bedarfs oder ausstehenden Spikes, vier an R6/R8/R9 übergeben), vier abgelehnt.
2. **Die Evidenz trägt die Form, nicht das Werkzeug.** Für keine der bewerteten Ressourcen (3Blue1Brown, Mathigon, Seeing Theory, Distill, Brilliant, StatQuest, Exercism u. a.) wurde eine kontrollierte Lernstudie gefunden. Was die Literatur stützt, sind Formmerkmale: Vorhersage vor Aufdecken, Führung statt freier Exploration, verknüpfte Darstellungen, Animation nur, wo Veränderung gelernt werden muss, Widerlegung von Fehlvorstellungen – und die Warnung, dass polierte Erklärungen das Lernurteil stärker heben als das Lernen.
3. **Die Engine hat vieles schon** (gelesen, nicht ausgeführt): Labs mit Vorhersage-, Missions- und Transferphase (`labs/pedagogy.py`), Szenen mit Formel↔Bild-Kopplung, Schrittsteuerung, `aria-live` und reduced motion (`templates/em_scene.js`). R7 empfiehlt daher vor allem **Verschärfungen**: Vorhersage-Gates auch in Szenen und Web-Lehrbuchfiguren, „Weiter" statt „Abspielen" als Primärknopf, Pflicht zu Aussage + Lernhandlung je Visualisierung, Fehlvorstellung nicht nur nennen, sondern widerlegen und eine Aufgabe folgen lassen.
4. **Acht R1-zugewiesene Engine-Regeln entschieden** (MM-R1/2, CL-R1/2, PR-R1..3, MC-R2): retains/refines, keine ersetzt.

## 2. Forschungsfragen, Methode, Zugang

**Fragen.** (F1) Welche Ressourcen aus Issue #29 und dem Registry sind was genau (Identität, Version, Lizenz)? (F2) Welchen Lernmechanismus tragen sie, und ist er belegt oder nur behauptet? (F3) Was davon gehört in welches der vier Produkte – als Bibliothek, Prinzip, Link oder gar nicht? (F4) Welche Befunde zu Simulation, Animation, Lernerkontrolle, Video, Verständnisillusion und Programmierfeedback ändern eine dieser Entscheidungen?

**Methode Ressourcen.** Identität über die GitHub-REST-API (27 Repo-Abfragen inkl. Lizenzdatei, README, letzte Releases/Commits) und je höchstens einen Abruf der offiziellen Seite (19 Abrufe). Keine Installation, kein Klonen, kein Konto, kein Ausführen fremden Codes, keine bezahlten Aufrufe; generischer User-Agent, keine personenbezogenen Daten in Anfragen. Abgerufene Inhalte gelten als untrusted data. Für die sechs Überschneidungen mit R9 (Khanmigo, YouLearn, StudyFetch, Math Academy, RemNote, Margin Study) plus Utterseen wurde die Identität aus den R9-Karten übernommen und nur der Nicht-Tutor-Aspekt bewertet. Jede Behauptung ist als `marketing`, `documented_function`, `benchmark` oder `learning_outcome` klassifiziert; nur `learning_outcome` darf einen Lerneffekt stützen (Test erzwingt das).

**Methode Evidenz.** Gezielte known-item-Verifikation von Schlüsselarbeiten (Auswahl nach Vorwissen des Agenten und nach Zitaten in Hohman et al. 2020), keine Datenbanksuche mit Suchstring. Identität jeder Quelle per Crossref; Abstracts über Crossref, OpenAlex, PubMed oder Repository. Zugangsstufen: 10 × `abstract`, 3 × `metadata`, 1 × `fulltext_partial`. Zahlen nur mit Locator aus gelesenem Text. Semantic-Scholar-TLDRs (maschinell) wurden abgerufen, aber nirgends verwendet.

**Fehlschläge (protokolliert in S01–S11):** `opendsa.org` (Zertifikat passt nicht), ein falscher Distill-Pfad (404), PhET-Lizenzseite ohne Inhalt gerendert, YouTube-Consent-Umleitung, Springer-Login-Umleitungen, ScienceDirect HTTP 403, ein falscher DOI-Kandidat für Höffler & Leutner (löste auf Ayres 2006 auf, verworfen), drei Repos 404. Ausgeschlossen mangels zugänglichem Abstract: Rutten et al. 2012, Toftness et al. 2018 (ersetzt durch Carpenter et al. 2016), Moyer-Packenham & Westenskow 2013.

## 3. Befunde je Ressource

Legende Entscheidung: **R** = REUSE_AS_LIBRARY, **E** = EMULATE_PRINCIPLE, **L** = LINK, **D** = DEFER, **X** = REJECT. Vollständige Karten mit Claims, Produktpassung, Workflow und 1–2 falsifizierbaren Evaluationen in `r7_resources.json`.

### 3.1 Mathematische Visualisierung

| Ressource | Identität / Lizenz (geprüft) | Mechanismus | Höchste Evidenz | Entsch. | Kernbegründung |
|---|---|---|---|---|---|
| 3Blue1Brown | FAQ: Clips < 60 s mit Attribution, sonst Anfrage; Szenen-Code `3b1b/videos` **CC BY-NC-SA 4.0** | Frage zuerst, eine Änderung je Szene, Formel↔Bild-Farbkopplung | documented_function | **E** | Szenenprogression und Kopplung übernehmen; passives Zuschauen und polierte Erzählung nicht (Fluency-Illusion) |
| manim (3b1b v1.7.2, Community v0.22.1) | beide MIT | Render-Bibliothek für Erklärvideos | documented_function | **D** | erzeugt passives Video; SVG/em_scene deckt Keyframes ab; nur bei nachgewiesenem Bewegungsbedarf |
| Mathigon (Amplify) | Kurse ohne Lizenzdatei + CLA → nicht nutzbar; Studio-Code MIT, Medien CC BY-SA | Lücke beantworten → Fortsetzung wird aufgedeckt (`[[…]]`, `reveal(when="blank-0")`) | documented_function (Quelltext) | **E** | Antwort-dann-Aufdecken-Gating ist klar, billig, passt zu PR-R1 |
| Polypad | Skript von `static.mathigon.org`, optionaler API-Key, keine Lizenz/Terms auf API-Seite; zu Amplify umgezogen | freie virtuelle Manipulative | documented_function | **L** | Offline-Vorgabe und unklare Terms verhindern Einbettung |
| Explanaria | MIT, Einzelkonto, „v0.2 … work in progress", Push 2025-05 | 3D-Präsentationen, Domain→Transformation→Output | documented_function | **X** | kein Mechanismus über verknüpfte Darstellungen hinaus; unreif, WebGL ohne A11y |
| Bright Side of Mathematics | tbsom.de (J. Großmann), Mitgliedschaft, keine Lizenzangabe | Definition→Satz→Beweis-Videos, Quiz | documented_function | **L** | Struktur ist bereits Produktvertrag; als Zweitzugang verlinkbar |
| Think Logic | **nicht auffindbar**; „Think Twice" nicht ersatzweise angenommen | – | – | **D** | Registry verbietet geratene URLs; Owner muss Quelle nennen |
| Visually Explained | nur Drittseite; YouTube-Consent-Umleitung | visuelle ML-/Optimierungsvideos (laut Drittseite) | Drittbeschreibung | **D** | Identität offen |
| GeoGebra (ergänzt) | Apps/Materialien nur nicht-kommerziell; Code EUPL 1.2; UI/Doku CC BY-NC-SA | dynamische Geometrie, verknüpfte Ansichten | documented_function | **L** | stärkster Konkurrent für Manipulation, aber Lizenz/Offline ungeklärt |
| JSXGraph (ergänzt) | LGPL-3.0, v1.14.3 | Geometrie-/Plotbibliothek | documented_function | **D** | nur bei konkretem Darstellungsdefizit von em_scene.js (Spike) |

### 3.2 Statistik und quantitative Modellierung

| Ressource | Identität / Lizenz | Mechanismus | Evidenz | Entsch. | Kernbegründung |
|---|---|---|---|---|---|
| Seeing Theory | `seeingtheory/Seeing-Theory` Apache-2.0; „no longer being maintained" (2019) | wiederholte Stichprobe, laufender Schätzer vs. Wahrheit | documented_function; Preise ≠ Evidenz | **E** | Kern simulationsbasierter Inferenz (R2-POL-16); Code alt → eigene Umsetzung mit Seed und Orakel |
| StatQuest | statquest.org, „© StatQuest" | winziger durchgehender Datensatz vor Formel | marketing/Beschreibung | **E** | „Mini-Beispiel zuerst" billig, passt zu WE-R1 |
| QuantEcon | QuantEcon.py MIT (v0.13.1); Vorlesungen **CC BY-SA 4.0** (Sargent & Stachurski) | Modell→Code→Abbildung, Notebook/Colab | documented_function | **L** | fachliche Vertiefung Ökonomie/Finanzen; Share-Alike verhindert Textübernahme; Colab = Datenabfluss |

### 3.3 Informatik und Programmieren

| Ressource | Identität / Lizenz | Mechanismus | Evidenz | Entsch. | Kernbegründung |
|---|---|---|---|---|---|
| OpenDSA | MIT (Karavirta & Shaffer, VT), Commit 2026-11-25; Docker/LTI | Proficiency-Aufgabe: Lernende führen Algorithmusschritt auf Struktur aus, Prüfung gegen Modell | documented_function; Verhaltensstudie nur Metadaten | **E** | konkreteste Umsetzung von R2-POL-17; Plattform wäre zweites Lehrbuchsystem |
| JSAV (ergänzt) | MIT | AV-/Proficiency-Bibliothek | documented_function | **D** | A11y/Abhängigkeiten ungeprüft → Spike gegen eigene SVG-Umsetzung |
| Exercism | Website **AGPL-3.0**; problem-specifications MIT | Stub + geordnete Tests (Stopp am ersten Fehler) + verdeckte Referenz („not the target code") + Analyzer | documented_function | **E** | billig emulierbares Aufgabenformat; Plattform/Mentoring nicht |
| Pyodide | MPL-2.0; Release-Tag „314.0.8" laut API | Python im Browser (WASM) | documented_function | **R** | einzige geprüfte Offline-Ausführung ohne Server; nur nach Spike |
| JupyterLite | BSD-3-Clause, v0.8.7; Offline nicht ausdrücklich bestätigt | volle Notebook-UI im Browser | documented_function | **D** | wäre faktisch eigene Arbeitsumgebung (Risiko fünfte Fläche); Pyodide genügt |
| GeeksforGeeks | Sanchhaya Education Pvt. Ltd., „All rights reserved" | Einsteiger-Tutorials | marketing | **L** | Rolle im Produktvertrag fixiert: Zugänglichkeitshilfe, nie Autorität |

### 3.4 Explorables und interaktives Publizieren

| Ressource | Identität / Lizenz | Mechanismus | Evidenz | Entsch. | Kernbegründung |
|---|---|---|---|---|---|
| Explorable Explanations (Bret Victor 2011/2024; Nicky Case; explorabl.es) | Essay; Hub ohne Lizenz („open sauce"); `ncase/trust` CC0 | reaktive Dokumente, explorierbare Beispiele, Kontextinfo | Designessay | **E** | Leitidee des Interaktiv-Produkts – aber nur mit Ziel, Vorhersage, Variablenkontrolle |
| Distill | Artikel **CC BY 4.0**, Template Apache-2.0; „indefinite hiatus" seit 2021 | Figur neben Text, Notation↔Grafik-Kopplung | Design-Review (Hohman 2020: „limited empirical evaluation") | **E** | Qualitätsmaßstab für MM-R2/CL-R1; Template ungepflegt |
| PhET (ergänzt) | scenery MIT bestätigt; Sim-Lizenz CC BY 4.0 nur per Suchsnippet, 2026er Lizenzänderung angedeutet | implizite Führung durch wenige, gewählte Regler | Lernstudien existieren (R4: finkelstein2005cck) | **E** | Guided-Reglerauswahl für CL-R2; Bündelung erst nach Primärlizenzprüfung |

### 3.5 Kommerzielle Lernplattformen (Nicht-Tutor-Aspekte; Tutorurteile in R9)

| Ressource | R9-Karte | Nicht-Tutor-Aspekt | Entsch. | Kernbegründung |
|---|---|---|---|---|
| Brilliant (Brilliant Worldwide, Inc.) | – | Pretest, Spacing, Mischen, Hinweisentzug, Streaks/XP | **X** | Mechanismen bereits als R1-Policies erfasst; eigene Spacing-Logik verletzt AD-1; Streaks widersprechen R1-POL-B05/MC-R2; keine Studie |
| Math Academy | RES-MATHACADEMY | Voraussetzungsgraph, Einstufung, FIRe | **D → R6** | Sequenzierung ist Kompetenzgraph-Thema; FIRe durch AD-1 ausgeschlossen |
| RemNote | RES-REMNOTE | Notiz-/Kartenwerkzeug | **D → R8** | kein Visualisierungsbeitrag |
| Margin Study (lokaler PDF-Annotator, R9-Korrektur) | RES-MARGINSTUDY | Randnotiz in eigenen Worten | **E** | generatives Paraphrasieren am Leseort, optional, nie bewertet (SE-R2) |
| YouLearn | RES-YOULEARN | Zusammenfassungen, Podcasts | **X** | passive Formate; kein eigener Mechanismus |
| StudyFetch | RES-STUDYFETCH | generierte Mini-Apps/Lernhilfen | **X** | Mini-Apps ohne deklarierte Lernoperation (R7-POL-01); eigene Karten (AD-1) |
| Khanmigo / Khan Labs | RES-KHANMIGO | keiner für Selbstlernende | **D → R9** | reine Tutorfrage |
| Utterseen | RES-UTTERSEEN | keiner | **D → R9** | reine Tutor-/Assistenzfrage |

### 3.6 Erhalten ohne eigene R7-Bewertung

Alle Namen aus Registry §A, §B, §D, §F bleiben im Inventar (`preserved_pointers`, `preserved_ideas`; Test liest das Registry aus und prüft jeden Namen): Anki, Obsidian (→ R8); DeepTutor, OATutor, LMU SMART-RAG, TutorBench, OpenTutor, PAIDEIA (beide URLs), Education Agent Skills, ChatGPT Study Mode, portable Tutor-Kontextpakete, NotebookLM, RemNote Guided Learn Mode (→ R9, mit R9-Kartenverweis); §B-Kategorien Beweisassistenten (→ R2), Argumentkarten/Fallpraxis/Medizinsimulation (→ R3), CAD/Psychomotorik (→ R4), Wissensgraphen/Annotation (→ R8/R6), adaptive Curricula/ITS (→ R5/R9), Statistiksimulation/Notebooks und A11y/Mathe-Typografie (→ R7, in Karten bzw. R7-POL-09). §D-Übungen sind als Validierungsaufgaben V1–V7 übernommen bzw. an R9/R4 übergeben.

## 4. Was die Belege an den Entscheidungen ändern

| Befund (Locator) | Zugang | Ändert |
|---|---|---|
| Animation vs. statisch: Hedges g = 0.226 [0.12, 0.33], 140 Vergleiche/61 Studien; Moderatoren systemgesteuert 0.309, mit Audio 0.336, ohne Text 0.883 (berney2016animation, Abstract) | abstract | R7-POL-05: Vorteil klein; **Gegenbefund**: systemgesteuerte Animation zeigte den größeren Moderatoreffekt → Einzelschritt-Standard ist zu testen, nicht gesetzt |
| Vorteil der Animation, wenn Merkmale der Veränderung gelernt werden müssen (ploetzner2020animationdemands, Abstract; post-hoc-Moderator) | abstract | R7-POL-05: Klassifikation `change_is_content` |
| Lernergesteuertes Tempo: besserer Transfer, gleiches Behalten (mayer2001learnerpacing, Abstract) | abstract | R7-POL-05: Schrittsteuerung bleibt Standard |
| Lernerkontrolle insgesamt g = 0.05 (18 Artikel/29 Effekte; karich2014learnercontrol, Abstract) – **Null-Befund** | abstract | R7-POL-01/03: Regler/Freiheit allein ist kein Mechanismus; Mission nötig |
| Video in Hochschule: ersetzend g = 0.28, ergänzend g = 0.80, Biasrisiko genannt (noetel2021video, Abstract) | abstract | R7-POL-06: Erklärszenen ergänzen, ersetzen keine Übung |
| Flüssiger Vortrag hebt Lernurteil, nicht Lernen; auch nach 1 Tag nicht konsistent besser; Überzuversicht (carpenter2013fluency, carpenter2016fluency, PubMed-Abstracts) – **Null-Befund für Lernen** | abstract | R7-POL-06: polierte (3B1B-artige) Erklärung zählt nie als Fortschritt; Lernurteil nur Datum |
| Refutation 0.79 / Dialog 0.83 vs. knappe Exposition, N = 364 Physik-Erstsemester, Effekttyp im Abstract unbestimmt (muller2008misconceptions) | abstract | R7-POL-06: Fehlvorstellung ausdrücklich widerlegen |
| Vorhersage + Selbsterklärung vor Datenanzeige > Kontrolle in Erinnern/Verständnis (kim2017predictionvis) | abstract | R7-POL-02/07: Vorhersage-Gates auch in Szenen/Figuren |
| Interaktive Artikel „limited empirical evaluation"; Scroll vs. Step ohne Engagement-Unterschied (Sekundärzitat McKenna 2017) (hohman2020interactivearticles) | fulltext_partial | R7-POL-01: Interaktivität ohne Aufgabe wird oft nicht genutzt |
| Automatisches Programmierfeedback meist Fehleridentifikation, selten nächster Schritt; 101 Werkzeuge (keuning2019programmingfeedback) | abstract | R7-POL-08: Tests + gestufte Hinweise; Testbestehen ≠ Kompetenz |
| Höffler & Leutner 2007, Tversky et al. 2002, Fouh et al. 2014 | metadata | nur Kontext, kein tragender Beleg |

Wiederverwendet statt neu recherchiert: R2 (Algorithmenvisualisierung hundhausen2002/naps2002/grissom2003, PRIMM, Autograder, simulationsbasierte Inferenz), R4 (PhET/virtuelle Labore, Nicht-Transfer), KB (mayer2020, ainsworth2006, brod2021, butterfield2001, dejong1998, kirschner2006, kalyuga2003, chi2014, roediger2006, shute2008, hattie2007).

## 5. Policies R7-POL-01..10 (Mechanismus → Lernhandlung → Affordanz → Observable → unabhängiges Outcome → Fehlermodus)

| ID | Mechanismus | Lernhandlung | Affordanz (Produkte) | Observable | Unabh. Outcome | Fehlermodus | Sicherheit |
|---|---|---|---|---|---|---|---|
| 01 | Kohärenz, ICAP | Aussage anwenden | Bildunterschrift = Aussage; Szenenfelder claim/operation/learner_action (T, I, A, W) | Feldabdeckung, Handlungslog | Aussage an neuer Instanz ohne Bild | formelhafte Pflichtfelder | low |
| 02 | Vorhersage/Überraschung | vorhersagen vor Aufdecken (≤ 3 Gates, „weiß nicht" erlaubt) | Szenen-Gates, Web-Lücken, PDF-Frage vor Figur (I, T, W) | Vorhersage, Sicherheit, Abbruch | verzögerter Transfer | Raten, Abbruch | low |
| 03 | Führung > freie Exploration | Mission mit 2–3 Reglern, dann Explore | Guided/Explore, Hypothesenfeld (I, T, W) | Missionserfüllung, Regler | Vorhersage ohne Simulation | Probieren statt Verstehen | low |
| 04 | Signalisierung, Kontiguität, Übersetzung | eine Darstellung in andere übersetzen | Namens-/Farbkopplung, Mini-Beispiel zuerst (T, I, W, A) | Layout-Review | Übersetzung ohne Hilfsfarben | Farbe allein | moderate |
| 05 | Animation nur bei Veränderung als Inhalt | Schritt für Schritt steuern, Zustand k vorhersagen | `change_is_content`, „Weiter" primär, Keyframes (I, T, W) | Nutzung Weiter/Abspielen | Zustand k bei neuer Eingabe | Durchklicken | low |
| 06 | Fluency-Illusion, Refutation | Kurzaufgabe nach Erklärsegment | Pflichtfeld misconception + Widerlegung (I, T, W, A) | Kurzaufgaben, Urteil vs. Ergebnis | Konzepttest mit Fehlvorstellungs-Items | Verankerung der Fehlvorstellung | moderate |
| 07 | Vorhersage + Simulation | Streuung vorhersagen, simulieren, erklären | Seed + Orakel + Keyframes (I, T, W, A) | Orakelprotokoll | Populationsaussage in neuem Kontext | Simulation als Beweis missverstanden | low |
| 08 | spezifisches Feedback | Ergebnis vorhersagen, Test für Test implementieren | Werkbank, Pyodide-Worker, Hinweisleiter (I, W, A) | Läufe, Hinweisstufen | verzögerte Variante mit Randfall + Komplexität | Test-Raten | low |
| 09 | Norm (A11y, Offline) | – | Tastatur, aria-live, Alt-Text = Aussage, Nicht-Farb-Kanal, kein Netz (I, T, A) | A11y-/Offline-Prüfung | lösbar mit assistiver Technik | Checkliste ohne Nutzbarkeit | normative |
| 10 | Norm (Lizenz, 4 Produkte, AD-1) | Link mit Zweck und Folgeaufgabe | „Weiterführend"-Abschnitt, keine Fremdeinbettung (T, W, I, A) | Linkregister, Build-Prüfung | Lizenz-/Offline-Audit | Linkwand, tote Links | normative |

T = Lehrbuch, W = Arbeitsbuch, A = Anki, I = Interaktiv. Konfliktregeln CR-R7-1..4 (u. a. Erklärung vor Vorhersage bei Novizen nach R1-POL-A02; Explore nach bestandener Probe wegen Expertise Reversal) und Regelentscheidungen in `r7_resource_policies.json`. Nicht abgedeckte Operationen: rule_based_contextual, open_synthesis (R3), embodied_psychomotor (R4), self_regulation (R1).

## 6. Shortlist (priorisiert, ≤ 8) mit Validierungsaufgaben

| # | Element | Herkunft | Validierungsaufgabe (alle NOT_RUN) |
|---|---|---|---|
| 1 | Vorhersage-Gate in Szenen und Web-Lehrbuchfiguren (R7-POL-02) | Mathigon-Gating, Explorables, 3B1B | **V1** Binomialkoeffizient als Pfadzählung: Szene ohne Eingabe vs. mit 3 Gates vs. statischer illustrierter Beweis; unassistierter Transfer nach 1 Woche; Abbruchquote als Schadensmaß |
| 2 | Refutation + eigene Aufgabe; Ansehen zählt nie (R7-POL-06) | 3B1B, StatQuest, Margin Study; Gegenbeispiele YouLearn, Brilliant | **V2** Refutationsszene + Folgeaufgabe vs. gleich lange Exposition; Lernurteil sofort, Konzepttest verzögert; Kriterium: kleinere Urteil-Leistungs-Lücke und bessere Konzeptleistung |
| 3 | Animation nur bei Veränderung als Inhalt; „Weiter" primär; Keyframes (R7-POL-05) | 3B1B, manim, OpenDSA | **V3** within-learner „Weiter"- vs. „Abspielen"-Standard; verzögert Zustand k einer neuen Eingabe vorhersagen; Gegenhypothese berney2016 (systemgesteuert) ausdrücklich |
| 4 | Mission + 2–3 Regler, Explore danach (R7-POL-03) | PhET, Explorables | **V4** gleiche Mission mit 2 vs. 6 Reglern bei Novizen; verzögerte Vorhersage mit Begründung ohne Simulation |
| 5 | Stichprobensimulation mit Vorhersage, Seed, Orakel (R7-POL-07) | Seeing Theory | **V5** Streuung vorhersagen → simulieren → erklären, warum eine Stichprobe keine Populationsaussage beweist; vs. statische Tabelle gleicher Information |
| 6 | Code-Werkbank im Exercism-Format auf Pyodide (R7-POL-08) | Exercism, Pyodide | **V6** Spike: offline laden, Kaltstart/Bytes, Endlosschleifen-Abbruch; dann inkrementelle Tests + Vorhersage vs. Vollsuite; verzögerter Randfall-/Komplexitätstest |
| 7 | Algorithmus-Proficiency-Aufgabe (R2-POL-17, keine neue R7-Policy) | OpenDSA, JSAV | **V7** Heap-Insert als Proficiency vs. Tracing-Tabelle vs. Parsons; verzögertes Tracing neuer Eingabe + Komplexitätsfrage; JSAV-Spike gegen eigene SVG (Tastatur, Screenreader, Größe) |
| 8 | Verknüpfte Darstellungen mit Übersetzungsaufgabe und Nicht-Farb-Kopplung (R7-POL-04/09) | Distill, StatQuest, 3B1B | **V8** Layout-Review; gekoppelt + Übersetzungsaufgabe vs. ungekoppelt; Übersetzungstest ohne Hilfsfarben; Screenreader-Durchlauf |

## 7. Konkrete Anforderungen an Interaktiv und Lehrbuch

**Emulieren:** Antwort-dann-Aufdecken (weich, „weiß nicht" zulässig); manipulierbare Parameter nur mit Mission und Lerngoal; verknüpfte Repräsentationen mit eigener Übersetzung; Mini-Beispiel vor Formel; Einzelschritt mit Zustandsbeschriftung und PDF-Keyframes; Fehlvorstellung nennen **und** widerlegen; inkrementelle Tests mit verdeckter Referenz; reaktive Zahl im Web-Text mit Richtungsvorhersage; generative Randnotiz optional.

**Nicht emulieren:** dekorative oder Ambient-Animation; Autoplay-Erzählung als Primärmodus; Zuschauen, Abspieldauer, Reglerbewegung, Linkklicks oder bestandene Tests als Fortschritt; Streaks/XP/Ligen; generierte Mini-Apps ohne deklarierte Lernoperation; freie Spielwiesen als Lerneinheit; eingebettete Fremdplattformen mit Konto, Netz oder eigener Wiederholungsplanung; volle Notebook-Umgebung als Parallelprodukt.

**Konkrete Engine-Befunde (code_inspected, Übergabe an Engineering nach R6):** `em_scene.js` macht „Abspielen" zum Primärknopf und führt Vorhersagen nur als beschreibenden Text; ein Feld „Typische Fehlvorstellung" existiert, Widerlegung und Folgeaufgabe sind nicht geprüft. Labs erfüllen PR-R1 bereits; Szenen nicht.

## 8. Durchgerechneter Fall und harter Gegenfall (synthetisch)

**Fall (Binomialkoeffizient, Szene).** Kompetenz: `C(n,k)` als Zahl der Gitterwege mit k Rechtsschritten. Szene: Schritt 1 zeigt ein 2×2-Gitter; Gate: „Wie viele Wege von links unten nach rechts oben?" (Auswahl 2/4/6/8, „weiß nicht"). Aufdecken: 6 Wege farbig, je Weg als Folge R/O beschriftet (Nicht-Farb-Kanal). Schritt 2 koppelt `C(4,2)` an „wähle 2 von 4 Positionen für R"; Fehlvorstellung „Wege = 2^n" wird ausdrücklich genannt und am Gitter widerlegt (16 Folgen, aber nur 6 mit genau zwei R). Folgeaufgabe unassistiert: 3×2-Gitter. Verzögerter Transfer (1 Woche): Anzahl 5-stelliger Binärwörter mit genau zwei Einsen – ohne Gitter. Kompetenzevidenz nur aus diesem verzögerten, unassistierten Item.

**Harter Gegenfall (Animation täuscht Verständnis vor).** Ein Lernender sieht eine flüssig erzählte, automatisch ablaufende Animation von Quicksort, gibt danach ein Lernurteil von 90 % ab und klickt alle Schritte durch. Im verzögerten Test soll er die Partition einer neuen Liste mit Duplikaten tracen und scheitert (Pivot-Gleichheit nie gesehen). Nach R7-POL-05/06 hätte die Szene (a) Einzelschritt-Standard, (b) ein Gate „Wohin wandert das Element gleich dem Pivot?" und (c) eine Folgeaufgabe mit Duplikaten erzwungen; das Lernurteil zählt nicht. **Transfergrenze:** Auch bestandene Gates belegen nur die Szene; Tracing einer neuen Eingabe bleibt die Messung. Für Simulationen physischer Systeme gilt zusätzlich R4-POL-07 (Simulation ≠ reale Handlung).

## 9. Explizite Nicht-Ziele

Keine Ressourcenwand und keine Installation von Apps/Plugins; keine fünfte Produktfläche (kein eigenes Notebook-, Kurs- oder Plattformprodukt); keine zweite Wiederholungsplanung neben Anki/FSRS (AD-1); keine Übernahme fremder Inhalte, Assets, Marken oder Stimmen; keine Einbettung von Drittskripten zur Laufzeit; keine Tutor-Bewertung (R9) und keine Notiz-/SRS-Werkzeugbewertung (R8); keine Produktionscode-Änderung in `exam_mastery/`.

## 10. Risiken

- **Gate-Ermüdung:** Vorhersage-Gates können Abbruch und Prüfungsangst erhöhen (Hinweis aus pan2023pretesting in R1A: MOOC ohne Gesamtnutzen, höhere Abbruchquote) – daher Obergrenze 3 und „weiß nicht".
- **Einzelschritt als Pseudo-Kontrolle:** schnelles Durchklicken ersetzt Autoplay ohne Lerngewinn; Gegenbefund Berney (systemgesteuert) ungeklärt.
- **Lizenzlage:** NC-/SA-Lizenzen (3b1b/videos, GeoGebra, QuantEcon, Mathigon-Medien) und die angedeutete PhET-Lizenzänderung 2026 sind ohne Owner-Entscheidung zum kommerziellen Status nicht abschließend bewertbar.
- **Pyodide:** Bundlegröße und Kaltstart ungemessen; Browser-Sandbox ist kein sicherer Code-Dienst.
- **Plattformrisiko:** Mathigon→Amplify, Distill-Hiatus, Seeing Theory unmaintained zeigen, dass Verlinkungen veralten.

## 11. Was wir nicht behaupten

- Dass irgendeine bewertete Ressource (3Blue1Brown, Mathigon, Seeing Theory, Distill, Brilliant, StatQuest, OpenDSA, Exercism …) Lernen nachweislich verbessert.
- Dass eine R7-Policy wirkt; alle sind `design_hypothesis`, `NOT_RUN`.
- Dass Animation statischen Bildern grundsätzlich überlegen oder unterlegen ist; der gelesene Mittelwert ist klein und moderatorabhängig.
- Dass Einzelschritt-Steuerung Autoplay schlägt; dafür gibt es einen stützenden und einen relativierenden Befund.
- Dass Höffler & Leutner 2007, Tversky et al. 2002 oder Fouh et al. 2014 inhaltlich geprüft wurden (nur Metadaten).
- Dass Lizenzangaben aus Suchsnippets (PhET) oder übernommenen R9-Karten primär geprüft sind.
- Dass ein Spike (Pyodide, JSAV, JSXGraph) bestanden ist – keiner wurde ausgeführt.

## 12. Owner-Entscheidungen

1. **Kommerzieller Status des Produkts:** bestimmt, ob NC-lizenzierte Komponenten (GeoGebra, 3b1b-Szenen-Code) überhaupt eingebettet werden dürften; bis dahin nur Links.
2. **Think Logic / Visually Explained:** bitte die ursprüngliche Quelle (Link/Kanal) nennen; sonst werden die Kandidaten geschlossen.
3. **Pyodide-Spike** (ca. ein Arbeitstag, keine Kosten) freigeben, bevor die Code-Werkbank weiter spezifiziert wird.

## 13. Reviewer-Fragen

1. Ist die Klassifikation „Veränderung ist Lerngegenstand" (Ploetzner) operationalisierbar genug für eine Szenen-Pflichtangabe, oder braucht sie Beispiele je Domäne?
2. Wie ist der Berney-Moderator (systemgesteuert 0.309) mit Mayer & Chandler (Lernertempo → Transfer) zu versöhnen – verschiedene Vergleichsfragen oder echter Widerspruch?
3. Ist Muller et al. 2008 (Physik, ein Standort, Effekttyp unklar) tragfähig genug für eine Pflichtwiderlegung in allen Domänen?
4. Ist „weiche" Gate-Logik (Aufdecken nie von Richtigkeit abhängig) mit der Mathigon-Emulation verträglich, oder verliert sie den Mechanismus?
5. Sind Pyodide (R) und JupyterLite (D) richtig gegeneinander abgegrenzt, oder unterschätzt R7 den Lernwert echter Notebook-Arbeit in Data-Science-Kursen?
6. Fehlen Ressourcen, die einen Mechanismus beitragen würden, der hier nicht abgedeckt ist (z. B. Beweis-Visualisierung, R2)?

## 14. Reproduktion

```
git -C <repo> checkout research/r7-resources-20261127
cd tests && python3 -m unittest test_r7_resources test_r1_learning_policies
gh api repos/<owner>/<repo> --jq '[.full_name,.fork,(.license.spdx_id//"none"),.pushed_at]'   # Identität je Karte
curl -s -A "research-metadata-check/1.0" https://api.crossref.org/works/<doi>                # Quellenidentität
```

Exakte Abfragen, Treffer, Ausschlüsse und Fehlschläge: `r7_evidence.json` → `search_log` (S01–S11). Zugriffsdatum aller Abrufe: 27.11.2026.
