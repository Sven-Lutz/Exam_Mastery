# R4 — Verkörperte Fertigkeiten, Labor, Raum/CAD und Handwerk: Synthese und Learning Policies

Stand 27.11.2026. **Forschungsergebnis zur Begutachtung, keine Freigabe.** Alle 15 Policies sind `design_hypothesis` mit `learning_evaluation: NOT_RUN`. Keine Policy ist implementiert. Kein Mastery-Produkt hat dadurch eine nachgewiesene Lernwirkung. Historische `HUMAN_REJECTED`-Bewertungen bleiben unverändert. **Das Produkt zertifiziert keine physische, Labor- oder Sicherheitskompetenz** (§3).

**Produktidentität:** Seit Issue #34 heißt das Produkt **Mastery**, eine allgemeine Plattform für den Erwerb von Wissen und Fertigkeiten; Prüfungsvorbereitung ist ein optionaler Modus. Issue #25 nennt die Ausgabedatei `EMBODIED_EXPERIMENTAL_DESIGN.md`; im Programm heißt sie `R4_EMBODIED_EXPERIMENTAL_DESIGN.md`, Inhalt und Auftrag sind dieselben.

| Artefakt | Inhalt |
|---|---|
| [r4/r4_evidence.json](r4/r4_evidence.json) | Evidenzregister, 32 Einträge im R1-Schema (`r1-evidence/1`): motorisches Lernen (10), Simulation/VR (4), Labor und Experimentieren (7), Raum/CAD (5), Bewertungsinstrumente, Küche und Handwerk (4), Sicherheitstraining (2). Zugangsstufen: 4 Volltext-Claim-Review, 4 Volltext teilweise, 23 nur Abstract, 1 nur Metadaten. Suchprotokoll (`search_log`, 22 Zeilen inkl. gescheiterter Suchen). |
| [r4/r4_learning_policies.json](r4/r4_learning_policies.json) | 15 Policies, Zwei-Spuren-Kompetenzmodell (`competence_tracks`), erweiterter Messvertrag, 5 Konfliktregeln, zurückgestellte Operationen, deklarierte Lücken, Selbstprüfprotokoll. Neues Pflichtfeld `certification_boundary` je Policy. |
| `tests/test_r4_learning_policies.py` | Wendet den R1-Strukturvertrag auf R4 an; zusätzlich: Kernoperationen abgedeckt, `coverage_gaps` vorhanden, alle vier Produkte je Policy, jede Policy mit `embodied_psychomotor` oder `empirical_experimental` erklärt, dass das Produkt physische und Sicherheitskompetenz nicht zertifiziert und Spur-B-Evidenz nur extern-menschlich ist; Suchprotokoll vollständig; jede Quelle zitiert oder als Lücke deklariert. Prüft Struktur, nicht wissenschaftliche Richtigkeit. |

Arbeitsteilung: Ein Spezialistenlauf (R4) hat Register, Policies, Tests und diesen Bericht in einer Sitzung erstellt. Es gab keine Lead-Stichprobe; das `verification_log` ist eine Selbstprüfung desselben Modells. Eine menschliche oder unabhängige Fachprüfung steht aus.

**Lesart.** Jede Aussage ist einer von vier Arten zugeordnet: **Befund** (im Register mit Fundstelle belegt), **Hypothese** (plausibel aus Befunden abgeleitet, ungeprüft), **Designentscheidung** (Produktsetzung, die sich nicht empirisch begründen lässt), **nicht gestützt** (in §9 gesammelt). Wo eine Zahl nur aus einem Abstract stammt, steht „(Abstract)“.

## 1. Ergebnis in zwölf Punkten

1. **Ein digitales Produkt kann physische Ausführung nicht messen, nur vorbereiten.** *Designentscheidung (normativ):* drei Spuren — A Wissen (im Produkt prüfbar), B reale Ausführung (nur extern durch qualifizierte Menschen bewertet), C Zertifizierung und Sicherheit (vollständig außerhalb). Keine Promotion von A nach B durch Simulator-, Video-, Foto-, Sensor-, Selbstauskunfts- oder Sprachmodelldaten (R4-POL-01). *Befund dahinter:* Simulationseffekte gegenüber keiner Intervention sind in Testsettings groß (Fertigkeiten > 1) und an realen Patientenoutcomes kleiner (0,50) (`cook2011simulation`, Abstract).
2. **Zufällige statt geblockter Übungsreihenfolge hilft vor allem im Labor, kaum in angewandten Aufgaben.** *Befund (Volltext):* Behalten SMD 0,92 in 30 Laborstudien, 0,23 [−0,16; 0,62] in 24 angewandten Studien, nach Sensitivitätsanalyse −0,01; nur 3 von 54 Studien moderater oder hoher Qualität (`czyz2024ciretention`). Für Transfer dasselbe Muster (`czyz2024citransfer`, Abstract). In einer chirurgischen Studie kehrte sich der Vorteil bei einem komplexeren Transfertest um (`sattelmayer2016motorprinciples`). Eine weitere Meta-Analyse nennt den Effekt einen „Mythos“ (`ammar2023cimyth`, nur Metadaten).
3. **Die Guidance-Hypothese (seltener Feedback = besseres Behalten) ist meta-analytisch nicht gestützt.** *Befund (Preprint-Volltext):* verzögertes Behalten RoBMA g = 0,021, 95-%-Glaubwürdigkeitsintervall [−0,062; 0,279], BF01 = 4,22; Primärstudien stark unterpowert (`mckay2022feedbackfrequency`). *Designentscheidung:* kein Ausblendplan als „evidenzbasiert“; gemessen wird rückmeldungsfrei (R4-POL-04).
4. **Externer Aufmerksamkeitsfokus: nach Biaskorrektur kaum Effekt.** *Befund (Abstracts):* unkorrigiert g = 0,58 für Behalten (`chua2021externalfocus`), nach robust-bayesianischer Korrektur derselben Daten 0,15, Performance 0,01 (`mckay2024focusbias`). *Designentscheidung:* ergebnisbezogene Formulierung nur als Stilregel (R4-POL-05).
5. **Demonstrationen verändern vor allem die Bewegungsform, wenig das Ergebnis.** *Befund (Abstract):* 0,77 gegen 0,17 (`ashford2006observational`).
6. **Mentale Probe hilft unmittelbar ein wenig, Transfer ist offen.** *Befund (Volltext):* SMD 0,43 [0,01; 0,85] direkt nach dem Training, Transfer 0,20 [−0,56; 0,97]; alle Studien mit hohem Biasrisiko (`sattelmayer2016motorprinciples`).
7. **Simulation kann reale Geräte für Konzepte übertreffen; Immersion ist nicht Lernen.** *Befund (Volltext):* Studierende mit Stromkreissimulation bauten danach einen realen Stromkreis schneller (14,0 gegen 17,7 min) und lösten Klausuraufgaben besser (0,593 gegen 0,476) (`finkelstein2005cck`, quasi-experimentell, eine Sitzung). Immersive VR erzeugte mehr Präsenz, aber weniger Lernen (d = 0,80) (`makransky2019immersivevr`, Abstract). Chirurgischer Simulationstransfer ist belegt, wenn bis zu einem Profizienzkriterium trainiert wurde (`dawe2014transfer`, Abstract).
8. **Klassische Einführungslabore festigen Vorlesungsinhalte nicht messbar.** *Befund (Volltext, beobachtend):* mittlerer Labornutzen 0,24 % ± 0,67 % in neun Kursen an drei Hochschulen (`holmes2017labvalue`). Lehrbar sind dagegen experimentelle Praktiken, etwa Variablenkontrolle, g = 0,61 [0,53; 0,69] (`schwichow2016cvs`, Abstract), und Anleitung beim Forschen, d = 0,50 (`lazonder2016inquiry`, Abstract).
9. **Räumliche Fähigkeiten sind trainierbar; der Nutzen für Konstruktion ist unbelegt.** *Befund (Abstracts):* g = 0,47 in 217 Studien (`uttal2013spatial`); Kursnutzen für Ingenieur-Studienanfänger unter einem Schwellenwert (`sorby2018spatialstem`, Regressionsdiskontinuität); Mathematik nur 0,28, mit konkreten Materialien besser als am Bildschirm (`hawes2022spatialmath`). Der Seed-Review findet nur korrelative Belege und warnt, Skizzieren und CAD nicht zu verdrängen (`bartlett2026spatialdesign`).
10. **Bewertungsinstrumente für reale Ausführung existieren in der Medizin, nicht im Handwerk.** *Befund (Abstract):* Globalskala und Checkliste korrelieren 0,76, Interrater-Reliabilität 0,78 bzw. 0,81 (`ilgen2015checklistgrs`). Kochkompetenz-Instrumente sind Fragebögen ohne adäquate Inhaltsvalidität (`teixeira2021culinaryinstruments`, Volltext teilweise).
11. **Kochen wird überwiegend in der Praxis gelernt; Online-Kurse wirken gemischt.** *Befund (Abstracts):* `rossen2026cooking` (Seed, überwiegend qualitativ); signifikante Fertigkeitsverbesserung in 3 von 8 Studien (`sanaan2026onlinecooking`). Für Holzbearbeitung und Backen wurde **keine** Lernstudie gefunden.
12. **Sicherheitstraining wirkt aktiv und praktisch besser, besonders bei hoher Gefährdung.** *Befund (Abstracts):* `burke2006safetytraining`, `burke2011dread`. *Designentscheidung (normativ):* Enthaltung bei gefährlichen Prozeduren, Sicherheit nur als Wissen, Verweis auf Aufsicht (R4-POL-13).

## 2. Methode, Suche und Zugang

**Vorgehen.** Ein Batch am 27.11.2026, ausgehend von den drei Seeds aus Issue #25 und von Kandidaten aus dem Vorwissen des Spezialisten, ergänzt durch protokollierte Suchen. Alle 22 Suchen und Bekannte-Titel-Prüfungen stehen mit Abfragetext, Dienst, gesichteter Trefferzahl, Einschlüssen und Ausschlussgründen im `search_log` des Registers, auch die gescheiterten (OpenAlex: Tagesbudget erschöpft, HTTP 429; Crossref einmal 429; Semantic Scholar einmal 429; ScienceDirect HTTP 403; Repositorium Mainz durch Bot-Schutz gesperrt). Dienste: Crossref REST, PubMed E-utilities (esearch/efetch, PMC-Volltexte), Semantic Scholar Graph API (Abstracts), ERIC API, eine Websuche und ein Seitenabruf. Keine kostenpflichtigen Dienste, generischer User-Agent. **Keine systematische Suche:** Die Auswahl ist zielgerichtet; Rankings und Trefferzahlen der Dienste sind nicht stabil.

**Identität.** Jeder DOI wurde über Crossref aufgelöst; Band, Heft und Seiten nur dort angegeben, wo Crossref oder PubMed sie liefern (Stichprobe im `verification_log`). Ein geratener DOI lief ins Leere und wurde verworfen.

**Einschluss** (nicht vorab registriert): (a) Meta-Analysen, systematische Reviews, RCTs oder starke quasi-experimentelle Designs, sonst deskriptive/konzeptuelle Quellen nur für Konstrukt- oder Lückenbefunde; (b) Outcome ist Lernen oder Bewertung einer motorischen, experimentellen, räumlichen oder handwerklichen Leistung; (c) Null- und Gegenbefunde ausdrücklich gesucht (CI angewandt, Feedbackhäufigkeit, Aufmerksamkeitsfokus, Labornutzen, VR); (d) Abstract oder Volltext frei abrufbar. **Nicht registriert**, obwohl aufgelöst: u. a. Brady 2004 (CI-Meta-Analyse; Zahlen nur als Hintergrund über `czyz2024ciretention`), Brinson 2015 und Chan et al. 2021 (virtuelle Labore; kein Abstract abrufbar), Hatala et al. 2015 (OSATS), Company et al. 2015, Booth et al. 2016, Schwendimann et al. 2015 (kein Abstract). Gründe im `search_log`.

**Zugangstiefe nach Bereich.** Motorisches Lernen: 2 Volltext-Claim-Review (`sattelmayer2016motorprinciples`, `czyz2024ciretention`), 1 Volltext teilweise (`mckay2022feedbackfrequency`, Preprint), 6 Abstracts, 1 nur Metadaten. Simulation/VR: 1 teilweise (`radhakrishnan2021ivr`, Preprint), 3 Abstracts. Labor: 2 Claim-Review (`finkelstein2005cck`, `holmes2017labvalue`), 5 Abstracts (davon `holmes2015criticalthinking` nur die Significance-Kurzfassung). Raum/CAD: 1 teilweise (`otey2017designintent`), 4 Abstracts. Bewertung/Küche/Sicherheit: 1 teilweise (`teixeira2021culinaryinstruments`), 6 Abstracts. **Abstract-Lektüre ist hier nie als Volltextanalyse dargestellt.**

**Seeds.** PMID 26768734 = `sattelmayer2016motorprinciples` (Volltext); 10.1115/1.4070965 = `bartlett2026spatialdesign` (Abstract); 10.1016/j.appet.2026.108511 = `rossen2026cooking` (Abstract über PubMed). R1-Quellen `ericsson1993deliberate` und `macnamara2014deliberate` werden über die R1-Register zitiert, nicht neu registriert.

## 3. Explizites Modell: Konzept, Ausführung, Zertifizierung

*Designentscheidung (normativ), in `competence_tracks` und R4-POL-01 maschinenlesbar.*

| Spur | Was | Wo trainiert | Wo belegt | Wer bewertet | Was nie als Beleg zählt |
|---|---|---|---|---|---|
| **A Wissen** | Konzepte, Begründungen, Ablauf und Reihenfolge, Fehlerbilder, Diagnose, Planung, Gefahrenerkennung | Lehrbuch, Workbook, Anki, interaktive Labs/Simulationen | im Produkt: unassistiert, verzögert, neue Items (R1-Messvertrag) | Produkt (geschlossene Items), Mensch (offene Begründungen) | gelesene Seiten, abgespielte Videos, Karten-Statistik |
| **B Ausführung** | Handlung am realen Material/Gerät: Form, Ergebnis, Toleranz, Tempo, Sauberkeit | reale Werkstatt, Küche, Labor, Skills-Lab | nur Ereignis `external_assessment` | qualifizierte Person am realen Objekt, Instrument nach R4-POL-12, möglichst blind gegenüber App-Status | Simulator-/VR-Scores, Fotos/Videos durch Produkt oder Sprachmodell bewertet, Selbstauskunft, Übungsminuten |
| **C Zertifizierung/Sicherheit** | Unterweisung, Zulassung, Sicherheits- und Berufszertifikate | Einrichtung (Betrieb, Hochschule, Kammer) | außerhalb des Produkts | zuständige Stelle | jede Produktanzeige; auch eine externe Bewertung in Spur B ist kein Zertifikat |

Das Produkt **trainiert und prüft A, bereitet B vor und dokumentiert B-Bewertungen anderer, zertifiziert nie B oder C**. Reale Übung wird als `practice_log` erfasst (Reflexion und Planung), Selbstbewertung als `self_assessment`, externe Bewertung als `external_assessment`, eine Sicherheitsunterweisung nur als Vermerk `external_safety_briefing` ohne jede Ableitung. Diese Trennung ist keine empirische Erkenntnis, sondern eine Sicherheits- und Validitätssetzung; die Befunde unter §4 zeigen nur, warum die naheliegende Alternative (App-Daten als Fertigkeitsmaß) unzulässig wäre: Effekte schrumpfen zur realen Aufgabe hin, Selbstauskunft ist kein Fertigkeitsmaß, und Simulationen lassen Haptik, Toleranz und reale Gefahr systematisch aus.

## 4. Befunde je Bereich mit Validitätswarnungen

### 4.1 Motorisches und perzeptuelles Lernen

- **Kontextinterferenz.** *Befund:* Vorteil zufälliger Reihenfolge im Labor groß (0,92), angewandt klein bis null (0,23; Sensitivität −0,01), Jüngere 0,02, Ältere 1,45 — aber Alter und Setting sind konfundiert (Ältere nur im Labor) (`czyz2024ciretention`, Results/Discussion). *Validitätswarnung:* I² ≈ 90 %, kein Publikationsbiastest, 56 von 59 Studien ohne Angabe zur Verblindung der Bewertenden. Zwei Meta-Analysen von 2023/2024 widersprechen sich in der Gesamtgröße; die Autoren erklären das mit Suchstrategien. Für reale Handwerks- und Laborarbeit ist der angewandte Schätzer maßgeblich, nicht der gepoolte.
- **Komplexität als Moderator.** *Befund/Theorie:* Prinzipien aus einfachen Laboraufgaben generalisieren nicht auf komplexe Fertigkeiten; Belastung ist entscheidend (`wulfshea2002complex`, Abstract). *Hypothese:* Für Novizen an realen Werkzeugen erst Grundform stabilisieren (R4-POL-03).
- **Feedbackhäufigkeit.** *Befund:* kein Effekt reduzierter Häufigkeit zu irgendeinem Messzeitpunkt, Vorhersageintervalle über ±1 SD (`mckay2022feedbackfrequency`). Terminales vs. gleichzeitiges Feedback: verzögertes Behalten −0,35 n. s. zugunsten gleichzeitig, Transfer 0,94 zugunsten terminal in **einer** Studie mit 30 Personen (`sattelmayer2016motorprinciples`). *Warnung:* Abwesenheit von Evidenz, nicht Evidenz der Abwesenheit; überwiegend einfache Aufgaben und Novizen.
- **Aufmerksamkeitsfokus.** *Befund:* Konsens „extern ist überlegen“ nach Biaskorrektur nicht haltbar (`mckay2024focusbias` gegen `chua2021externalfocus`; beide Abstract).
- **Demonstration, mentale Probe.** siehe §1 Punkte 5–6. *Warnung:* Sofortmessungen nach Training überschätzen Lernen (`sattelmayer2016motorprinciples`, Discussion).
- **Fehlerbasiertes Lernen.** *Befund (Abstract):* Fehlermanagementtraining d = 0,44, adaptiver Transfer 0,80 (`keith2008errormanagement`); Aufgabendomänen nicht geprüft. *Designentscheidung:* nur in sicheren digitalen Umgebungen (R4-POL-15).
- **Deliberate Practice.** Über R1 (`macnamara2014deliberate`): Übung erklärt in Professionen nur einen kleinen Varianzanteil. *Folgerung:* Übungsminuten sind kein Kompetenzmaß.

### 4.2 Simulation und Transfer in die reale Welt

- **Was überträgt:** Konzepte und Ablaufverständnis (`finkelstein2005cck`: Simulationsgruppe besser beim Bau eines realen Stromkreises und in der Klausur); chirurgische Fertigkeiten, wenn bis zu Profizienz trainiert und im OP bewertet (`dawe2014transfer`).
- **Was nicht oder unbelegt überträgt:** Haptik, Kraftdosierung, Materialstreuung, Toleranz am realen Werkstück, reales Sicherheitsverhalten — dazu wurde **keine** Transferstudie gefunden (Lücke). Immersion steigert Präsenz, nicht Lernen (`makransky2019immersivevr`); in einer Übersicht über 40 Vergleichsstudien zu immersiver VR waren 6 schlechter und 5 unklar, Effektivität wurde aus Autorenurteilen ausgezählt (`radhakrishnan2021ivr`). Virtuelle Labore wurden überwiegend auf Inhaltswissen evaluiert, positive Ergebnisse eher Neuheit zugeschrieben (`reeves2021virtuallabs`).
- **Warnung:** `cook2011simulation` vergleicht mit „keiner Intervention“; das zeigt nicht, dass Simulation realer Übung gleichwertig ist. `finkelstein2005cck` ist eine Sitzung, Abschnittszuteilung, Entwicklergruppe.

### 4.3 Räumliche Fähigkeiten, Skizzieren, CAD und Konstruktionsdidaktik

- *Befunde:* §1 Punkt 9. Konstruktionsabsicht wird in der CAD-Didaktik als erwartetes Verhalten des Modells bei Änderung verstanden und auf drei Ebenen gefasst (Skizzenbedingungen, Operationen, Beziehungen) (`otey2017designintent`, konzeptuell).
- *Warnung:* Keine Interventionsstudie zu Constraint-Modellierung gelesen. Der Effekt räumlichen Trainings auf **Konstruktionsleistung** ist nicht kausal belegt (`bartlett2026spatialdesign`). Bildschirmtraining schnitt für Mathematiktransfer schlechter ab als konkrete Materialien (`hawes2022spatialmath`) — relevant für ein digitales Produkt.

### 4.4 Labor und experimentelles Lernen

- *Befunde:* §1 Punkt 8. Pre-Lab-Aktivitäten: Rahmenwerk mit Trennung unterstützender (vorab) und prozeduraler (just in time) Information (`agustian2017prelab`, narrativ, keine Effektgröße).
- *Warnung:* `holmes2017labvalue` ist beobachtend (optionale Labore, Differenzwerte); die Autoren schließen nicht, Labore könnten keine Inhalte lehren, sondern dass diese Labore es nicht messbar taten. Die positive Gegenseite (`holmes2015criticalthinking`) ist nur als Kurzfassung gelesen. `schwichow2016cvs` zeigt, dass das Testformat einen Großteil der Varianz erklärt — produktinterne Item-Scores zur Versuchsplanung sind daher besonders vorsichtig zu lesen.

### 4.5 Handwerk, Küche, Bewertungsinstrumente

- *Befunde:* §1 Punkte 10–11. Kochkompetenz-Instrumente: von 12 Studien keine mit adäquater Inhaltsvalidität, Kriteriumsvalidität einmal berichtet und unzureichend; in den gelesenen Abschnitten nur Fragebögen (Zutrauen, Selbstwirksamkeit, Häufigkeit) (`teixeira2021culinaryinstruments`).
- *Lücke:* Holzbearbeitung, Handwerkzeuge, Lehrlingsausbildung und Backen: keine registrierte Lernstudie. Aussagen dazu sind Übertragungen (Hypothesen) aus Motorik-, Simulations- und Bewertungsforschung.

### 4.6 Sicherheit

- *Befund (Abstracts):* aktivere Methoden (Verhaltensmodellierung, Hands-on, Dialog) gehen mit mehr Wissen und weniger Unfällen einher; die Autoren kritisieren passive computerbasierte Schulung (`burke2006safetytraining`); der Vorteil aktiver Schulung zeigt sich vor allem bei hoher Gefährdung (`burke2011dread`). *Designentscheidung:* §3 und R4-POL-13.

## 5. Policies mit Mechanismuskette

Kette je Policy: Evidenz → Lernoperation/Intervention → Beobachtung im Produkt → unabhängiges Lernoutcome → Versagen/Gegenbefund. Erzeugt aus `r4/r4_learning_policies.json`; Relation und Zugangsstufe je Quelle in Klammern. Alle Parameter sind vorläufige Produktsetzungen.

### R4-POL-01 — Zwei-Spuren-Kompetenzmodell: Wissen im Produkt, physische Ausführung nur über externe menschliche Bewertung

*Operationen:* embodied_psychomotor, empirical_experimental, spatial_design; *Vorwissen:* any; *Phase:* acquisition, consolidation, final_exam_week. *Stufe:* normativ (Grenze zwischen Produkt und realer Ausführung ist eine Sicherheits- und Validitätssetzung; empirisch gestützt ist nur, dass Effekte zur realen Aufgabe hin abnehmen und Selbstauskunft Fertigkeit nicht misst).

- **Evidenz:** `dawe2014transfer` (supports, abstract); `cook2011simulation` (supports, abstract); `teixeira2021culinaryinstruments` (supports, fulltext_partial); `ilgen2015checklistgrs` (supports, abstract); `sanaan2026onlinecooking` (qualifies, abstract); `macnamara2014deliberate` (context_only, abstract)
- **Lernoperation und Intervention:** Jede Kompetenz mit physischem Anteil wird in Spur A (Konzepte, Begründungen, Ablaufwissen, Fehlerdiagnose, Planung; im Produkt unassistiert und verzögert prüfbar) und Spur B (reale Ausführung; nur durch eine qualifizierte Person am realen Objekt bewertet) zerlegt. Spur C (Sicherheits- oder Berufszertifizierung) liegt vollständig außerhalb des Produkts. Fortschrittsanzeigen zeigen Spur A und B getrennt; Spur B steht auf 'nicht beobachtet', bis ein externer Bewertungseintrag vorliegt. Simulator-, Video-, Selbstauskunfts- oder Sensorwerte aus der App erhöhen Spur B nie.
- **Beobachtung im Produkt:** Statusfelder je Kompetenz: spur_a (unassistiert/verzögert, R1-Messvertrag), spur_b (nur externe Einträge), spur_c (immer 'außerhalb des Produkts'). Reale Praxis: Lernende erfassen reale Übungseinheiten (Datum, Aufgabe, Dauer, Ergebnisfoto/Messwert optional, Selbstbeurteilung). Das Log ist Reflexionsmaterial und Planungsgrundlage, kein Kompetenzbeleg. Nur ein Eintrag 'external_assessment' (Bewertende Person mit Rolle, Instrument, Datum) verändert Spur B.
- **Unabhängiges Lernoutcome:** verzögerte reale Ausführung, von einer qualifizierten Person mit Instrument (GRS + aufgabenspezifische Checkliste) blind gegenüber dem App-Status bewertet
- **Versagen/Gegenbefund:** Spur-B-Feld wird über Selbstbeurteilung befüllt; Nutzende lesen Spur-A-Fortschritt als Handfertigkeit; Anbieter vermarkten Spur A als 'Zertifikat'. Falsifikator: Wenn in einer Stichprobe Spur-A-Werte die extern bewertete reale Ausführung so gut vorhersagen wie eine zweite unabhängige Bewertungsperson (vorab festgelegte Übereinstimmung), wäre die Trennung für diese Aufgabe überflüssig; die Sicherheitsgrenze bliebe bestehen.
- **Enthaltung:** kein Spur-B-Status ohne externen Bewertungseintrag; keine Bewertung von Fotos/Videos realer Ausführung durch das Produkt oder ein Sprachmodell als Kompetenzbeleg (AI-R2); fehlt eine qualifizierte Bewertungsperson: Spur B bleibt 'nicht beobachtet' und wird so angezeigt
- **Zertifizierungsgrenze:** physische Kompetenz zertifiziert: nein; Sicherheit zertifiziert: nein. Kernpolicy der Grenze; alle anderen R4-Policies verweisen hierauf.
- **KB-Regeln:** ITS-R1 (refines), AI-R2 (retains), MC-R2 (refines), R4-POL-01-N1 (new)

### R4-POL-02 — Demonstration und Beobachtungslernen als Vorbereitung auf reale Übung, nicht als Lernnachweis

*Operationen:* embodied_psychomotor; *Vorwissen:* novice; *Phase:* acquisition. *Stufe:* niedrig (eine ältere Meta-Analyse ohne sichtbare Biaskorrektur, nur Abstract; Effekt auf das Ergebnis klein).

- **Evidenz:** `ashford2006observational` (supports, abstract); `burke2006safetytraining` (supports, abstract); `sattelmayer2016motorprinciples` (qualifies, fulltext_claim_review)
- **Lernoperation und Intervention:** Vor der ersten realen Übung kurze, segmentierte Demonstrationen der Bewegungsform und Reihenfolge (Experte, Normaltempo und verlangsamt, mehrere Perspektiven), jeweils mit Benennung des Ergebnismerkmals, an dem man gelungene Ausführung erkennt. Zwischen realen Übungseinheiten erneut abrufbar. Ansehen zählt nie als Fortschritt; die Wirkung auf das Ergebnis (Genauigkeit, Passung) ist klein, die auf die Bewegungsform größer.
- **Beobachtung im Produkt:** Abrufzeitpunkt und -dauer der Demonstration; Antworten auf Beobachtungs-/Fehlerbildaufgaben (Spur A). Reale Praxis: Nach der realen Übung: welche Demonstration genutzt wurde und welches Ergebniskriterium erreicht schien (Selbstbeurteilung, kein Beleg).
- **Unabhängiges Lernoutcome:** extern bewertete reale Ausführung (Form und Ergebnis getrennt) >= 1 Woche nach der Übungsphase
- **Versagen/Gegenbefund:** Video ersetzt reale Übung; Lernende imitieren Form ohne Ergebniskontrolle; Kamerawinkel verdeckt kritisches Detail. Falsifikator: In einer randomisierten Studie mit gleicher realer Übungszeit zeigt die Demonstrationsgruppe bei verzögerter, extern bewerteter Ausführung weder in Form noch im Ergebnis einen Vorteil oberhalb einer festgelegten Mindestdifferenz.
- **Enthaltung:** keine Demonstration gefährlicher Arbeitsschritte ohne Sicherheitskontext und Verweis auf Aufsicht (R4-POL-13); kein Fortschritt aus Abspielzeit (MC-R2); bei rein ergebnisorientierten, formarmen Aufgaben (z. B. Teig abwiegen) keine Demonstrationspflicht
- **Zertifizierungsgrenze:** physische Kompetenz zertifiziert: nein; Sicherheit zertifiziert: nein.
- **KB-Regeln:** MM-R1 (retains), WE-R1 (refines), MC-R2 (retains)

### R4-POL-03 — Übungsplan für motorische Fertigkeiten: geblockt beginnen, Variation erst nach stabiler Grundform

*Operationen:* embodied_psychomotor; *Vorwissen:* novice, intermediate; *Phase:* acquisition, consolidation. *Stufe:* niedrig (CI-Vorteil vor allem im Labor, in angewandten Settings klein oder null; niedrige Studienqualität, Alter und Setting konfundiert, Meta-Analysen widersprechen sich).

- **Evidenz:** `czyz2024ciretention` (supports, fulltext_claim_review); `czyz2024citransfer` (supports, abstract); `wulfshea2002complex` (supports, abstract); `sattelmayer2016motorprinciples` (supports, fulltext_claim_review); `czyz2024ciretention` (qualifies, fulltext_claim_review); `ammar2023cimyth` (context_only, metadata)
- **Lernoperation und Intervention:** Für Novizen und komplexe reale Aufgaben Varianten zunächst geblockt üben, bis die Grundform ohne Hilfe gelingt (extern oder per Ergebniskriterium beobachtet); danach schrittweise variable/zufällige Reihenfolge. Keine Behauptung, zufällige Reihenfolge verbessere reale Handwerks- oder Laborleistung; die Wirkung ist vor allem in einfachen Laboraufgaben mit Erwachsenen belegt.
- **Beobachtung im Produkt:** Übungslog mit Reihenfolge und Wechselzeitpunkt. Reale Praxis: Pro Übungseinheit: Variante(n), Reihenfolge (geblockt/gemischt), Ergebniskriterium erreicht ja/nein (Selbst- oder Ausbilderurteil, getrennt markiert).
- **Unabhängiges Lernoutcome:** extern bewertete reale Ausführung einer neuen Variante (Transfer) >= 1 Woche nach der letzten Übungseinheit
- **Versagen/Gegenbefund:** frühe Variation überlastet Novizen; Lernende bleiben zu lange geblockt (Leistungsillusion); Wechselkriterium wird selbstberichtet geschönt. Falsifikator: Eine vorab registrierte Studie in einer realen Handwerks- oder Laboraufgabe zeigt, dass Zufallsreihenfolge von Beginn an bei verzögerter externer Bewertung dem Blocked-then-Variable-Plan überlegen ist.
- **Enthaltung:** keine Zufallsreihenfolge bei Sicherheitsrelevanz oder solange die Grundform nicht stabil ist; keine universelle Interleaving-Regel für physische Aufgaben; ohne Ergebniskriterium kein automatischer Wechsel
- **Zertifizierungsgrenze:** physische Kompetenz zertifiziert: nein; Sicherheit zertifiziert: nein.
- **KB-Regeln:** IL-R1 (refines), R4-POL-03-N1 (new)

### R4-POL-04 — Rückmeldung zur physischen Ausführung: Häufigkeit und Ausblendung sind offene Parameter, gemessen wird ohne Rückmeldung

*Operationen:* embodied_psychomotor; *Vorwissen:* novice, intermediate; *Phase:* acquisition, consolidation. *Stufe:* sehr niedrig (Leitannahme (Guidance-Hypothese) meta-analytisch nicht gestützt; Einzelstudie für terminales Feedback, hohes Biasrisiko).

- **Evidenz:** `mckay2022feedbackfrequency` (contradicts, fulltext_partial); `sattelmayer2016motorprinciples` (supports, fulltext_claim_review); `wulfshea2002complex` (qualifies, abstract)
- **Lernoperation und Intervention:** Das Produkt schreibt keinen festen Ausblendplan vor und behauptet nicht, seltene Rückmeldung verbessere das Lernen. Es empfiehlt Rückmeldung zum Ergebniskriterium nach eigenem Versuch und zusammenfassend am Ende einer Serie, und es verlangt, dass jede Kompetenzaussage aus einem Versuch ohne Rückmeldung und mit Abstand stammt. Rückmeldungsformulierungen benennen Ergebnis und nächste Korrektur (FB-R1).
- **Beobachtung im Produkt:** Flag 'mit Rückmeldung' je Versuch; Anteil rückmeldungsfreier Versuche. Reale Praxis: Pro Versuch: mit/ohne externe Rückmeldung (Flag), sodass nur rückmeldungsfreie Versuche in Übersichten als 'unassistiert' erscheinen.
- **Unabhängiges Lernoutcome:** verzögerte, rückmeldungsfreie reale Ausführung, extern bewertet
- **Versagen/Gegenbefund:** Produkt verkauft Ausblendung als evidenzbasiert; Lernende werden von Messmitteln abhängig (Hypothese, nicht belegt). Falsifikator: Eine präregistrierte, ausreichend große Studie mit einer komplexen realen Aufgabe zeigt einen Vorteil eines bestimmten Ausblendplans beim verzögerten Behalten; dann würde der Plan als Option aufgenommen.
- **Enthaltung:** keine Wirksamkeitsbehauptung für Bandbreiten- oder Ausblendpläne; Sicherheitsfehler werden immer sofort zurückgemeldet und abgebrochen, unabhängig von jedem Ausblendplan (R4-POL-13)
- **Zertifizierungsgrenze:** physische Kompetenz zertifiziert: nein; Sicherheit zertifiziert: nein.
- **KB-Regeln:** FB-R1 (retains), R4-POL-04-N1 (new)

### R4-POL-05 — Aufmerksamkeitsfokus in Anleitungen: ergebnisbezogen formulieren ohne Wirksamkeitsversprechen

*Operationen:* embodied_psychomotor; *Vorwissen:* any; *Phase:* acquisition. *Stufe:* sehr niedrig (die umfassendste Meta-Analyse ist nach Biaskorrektur mit Null vereinbar; nur Abstracts gelesen).

- **Evidenz:** `chua2021externalfocus` (supports, abstract); `mckay2024focusbias` (contradicts, abstract)
- **Lernoperation und Intervention:** Hinweise dürfen das beabsichtigte Ergebnis am Werkzeug oder Material benennen (z. B. 'Sägeblatt bleibt an der Risslinie') statt Körperteile; das ist eine kostenneutrale Stilregel. Das Produkt behauptet keinen Lernvorteil externen Fokus' und personalisiert nicht danach.
- **Beobachtung im Produkt:** Stilprüfung der Anleitungstexte (agent_checklist). Reale Praxis: keine eigene Erfassung
- **Unabhängiges Lernoutcome:** nicht als Lernwirkung evaluiert; nur Verständlichkeit der Anleitung in Nutzertests
- **Versagen/Gegenbefund:** Regel wird als Wirkversprechen kommuniziert; Sicherheitsrelevante Körperhinweise werden gestrichen. Falsifikator: Eine präregistrierte Mehrlabor-Replikation mit realen Werkzeugaufgaben findet einen verzögerten Lernvorteil externen Fokus' oberhalb einer festgelegten Mindestdifferenz; dann würde die Stilregel zur Lernpolicy.
- **Enthaltung:** Körperhinweise bleiben erlaubt, wo Sicherheit oder Ergonomie sie erfordern (z. B. Hände hinter der Schneide); keine Produktbehauptung 'evidenzbasierter Fokus'
- **Zertifizierungsgrenze:** physische Kompetenz zertifiziert: nein; Sicherheit zertifiziert: nein.
- **KB-Regeln:** R4-POL-05-N1 (new)

### R4-POL-06 — Mentale Probe des Ablaufs als Ergänzung zur realen Übung, nie als Ersatz

*Operationen:* embodied_psychomotor, empirical_experimental; *Vorwissen:* novice, intermediate; *Phase:* acquisition, consolidation. *Stufe:* niedrig (kleine RCTs mit hohem Biasrisiko, Sofortmessung, Transfer n. s.).

- **Evidenz:** `sattelmayer2016motorprinciples` (supports, fulltext_claim_review)
- **Lernoperation und Intervention:** Vor realen Übungseinheiten eine kurze mentale Probe: Schritte in Reihenfolge abrufen, kritische Kontrollpunkte und Abbruchkriterien benennen, dann real üben. Die Probe ist Spur-A-Training (Ablaufwissen) und darf reale Übungszeit nicht ersetzen.
- **Beobachtung im Produkt:** Spur-A-Ergebnisse der Ablaufaufgaben (unassistiert, verzögert). Reale Praxis: Flag 'mentale Probe vor der Einheit ja/nein' im Übungslog.
- **Unabhängiges Lernoutcome:** extern bewertete reale Ausführung des Verfahrens nach >= 1 Woche; Reihenfolgefehler getrennt gezählt
- **Versagen/Gegenbefund:** Probe wird als 'Übung erledigt' gezählt; Ablaufwissen wird mit Handfertigkeit verwechselt. Falsifikator: Bei gleicher realer Übungszeit zeigt eine randomisierte Studie keinen Unterschied in verzögerten Reihenfolgefehlern und extern bewerteter Ausführung zwischen Probe- und Kontrollgruppe.
- **Enthaltung:** keine Reduktion realer Übungszeit zugunsten mentaler Probe; keine Aussagen über Bewegungsqualität aus der Probe
- **Zertifizierungsgrenze:** physische Kompetenz zertifiziert: nein; Sicherheit zertifiziert: nein.
- **KB-Regeln:** R4-POL-06-N1 (new)

### R4-POL-07 — Simulation und virtuelles Labor als Vorbereitung mit ausdrücklicher Nicht-Transfer-Kennzeichnung

*Operationen:* empirical_experimental, embodied_psychomotor, spatial_design; *Vorwissen:* novice, intermediate; *Phase:* acquisition. *Stufe:* niedrig (Simulation schlägt keine Intervention, Vergleiche mit realer Übung selten und klein; Transfer zur realen Aufgabe nur in Chirurgie mit Profizienzprogrammen belegt).

- **Evidenz:** `finkelstein2005cck` (supports, fulltext_claim_review); `cook2011simulation` (supports, abstract); `dawe2014transfer` (supports, abstract); `makransky2019immersivevr` (qualifies, abstract); `radhakrishnan2021ivr` (qualifies, fulltext_partial); `reeves2021virtuallabs` (qualifies, abstract)
- **Lernoperation und Intervention:** Simulationen werden eingesetzt, wo sie Unsichtbares sichtbar machen oder sichere Wiederholung erlauben, mit Vorhersage vor Manipulation (PR-R1). Jede Simulation trägt ein Transferetikett: was sie trainiert (z. B. Konzept, Variablenkontrolle, Reihenfolge) und was ausdrücklich nicht (Haptik, Kraftdosierung, Toleranz am realen Material, Materialstreuung, reales Sicherheitsverhalten, Geruch/Textur). Immersive VR ist kein Standard. Simulator-Scores zählen nur in Spur A.
- **Beobachtung im Produkt:** Vorhersagen, Manipulationen, Spur-A-Aufgaben nach dem Lab. Reale Praxis: Nach realem Folgeversuch: Abweichungen zur Simulation notieren (Reflexion, kein Beleg).
- **Unabhängiges Lernoutcome:** Spur A: verzögerter Konzepttest mit neuen Situationen; Spur B: extern bewertete reale Durchführung des Folgeversuchs
- **Versagen/Gegenbefund:** Transferetikett fehlt oder wird überlesen; Simulation suggeriert Präzision, die reales Material nicht hat; Präsenz/Motivation wird als Lernen gemeldet. Falsifikator: Eine Studie zeigt, dass Lernende mit Transferetikett bei realer Durchführung nicht weniger Simulations-Fehlübertragungen machen als ohne; dann ist das Etikett wirkungslos und muss durch geführte Übergangsaufgaben ersetzt werden.
- **Enthaltung:** keine Simulation, die gefährliche Synthesen, Mengen oder Bedingungen realistisch einübt (R4-POL-13); keine Profizienzaussage zur realen Ausführung aus Simulatorwerten; kein immersives VR ohne aufgabenbezogenen Grund
- **Zertifizierungsgrenze:** physische Kompetenz zertifiziert: nein; Sicherheit zertifiziert: nein. Simulatorwerte sind ausschließlich Spur-A-Daten.
- **KB-Regeln:** PR-R1 (retains), PR-R3 (retains), CL-R2 (retains), TR-R1 (refines)

### R4-POL-08 — Laborziele als experimentelle Praxis (Daten, Modelle, Unsicherheit, Versuchsplanung) statt Inhaltswiederholung

*Operationen:* empirical_experimental; *Vorwissen:* novice, intermediate; *Phase:* acquisition, consolidation. *Stufe:* niedrig (Nulleffekt der Inhaltsfestigung beobachtend, aber über neun Kurse konsistent; positive Belege für experimentelle Praxis teils nur Kurzfassung gelesen, Schulpopulationen).

- **Evidenz:** `holmes2017labvalue` (supports, fulltext_claim_review); `holmes2015criticalthinking` (supports, abstract); `schwichow2016cvs` (supports, abstract); `lazonder2016inquiry` (supports, abstract); `schwichow2016cvs` (qualifies, abstract)
- **Lernoperation und Intervention:** Laboreinheiten werden über experimentelle Ziele beschrieben und geprüft: Variablen kontrollieren, Datensätze und Daten mit Modellen vergleichen, Messunsicherheit begründen, über Verbesserung von Messung oder Modell entscheiden. Geführte statt offene Forschung; kognitiver Konflikt und Demonstrationen für die Variablenkontrollstrategie. Das Produkt behauptet nicht, Laborarbeit festige Vorlesungsinhalte.
- **Beobachtung im Produkt:** Spur-A-Aufgaben zu Datenvergleich, Unsicherheit und Versuchsplanung. Reale Praxis: Laborjournal-Einträge realer Versuche (Plan, Messung, Unsicherheit, Entscheidung) als Reflexion; Bewertung nur durch Betreuende.
- **Unabhängiges Lernoutcome:** verzögerte, unassistierte Bewertung eines neuen Versuchsplans und einer neuen Datensatzinterpretation durch eine Fachperson; reales Experimentieren nur durch Betreuende
- **Versagen/Gegenbefund:** Datensätze zu sauber, Unsicherheit trivial; Testformat misst Wiedererkennen statt Planung. Falsifikator: Eine kontrollierte Studie zeigt, dass Laboreinheiten mit experimentellen Zielen bei verzögerten Planungs- und Interpretationsaufgaben nicht besser abschneiden als inhaltsorientierte Labore.
- **Enthaltung:** keine Inhaltsfestigungsversprechen für Labore; keine offenen Forschungsaufgaben ohne Anleitung für Novizen; Versuchsplanung mit Gefahrstoffen nur auf Konzeptebene (R4-POL-13)
- **Zertifizierungsgrenze:** physische Kompetenz zertifiziert: nein; Sicherheit zertifiziert: nein. Labor-Sicherheitsunterweisung und Zulassung zum Praktikum erfolgen durch die Einrichtung.
- **KB-Regeln:** PR-R3 (refines), R4-POL-08-N1 (new)

### R4-POL-09 — Pre-Lab-Vorbereitung mit Vorhersage und Post-Lab-Fehleranalyse

*Operationen:* empirical_experimental, diagnostic_reasoning; *Vorwissen:* novice, intermediate; *Phase:* acquisition. *Stufe:* sehr niedrig (Pre-Lab-Beleg ist ein narrativer Review ohne Effektschätzung; Post-Lab-Fehleranalyse aus allgemeiner Fehlermanagement-Evidenz abgeleitet).

- **Evidenz:** `agustian2017prelab` (supports, abstract); `holmes2017labvalue` (supports, fulltext_claim_review); `keith2008errormanagement` (qualifies, abstract)
- **Lernoperation und Intervention:** Vor dem Labor: unterstützende Information (Konzepte, Ziel, Gefahrenhinweise der Einrichtung) und eine Vorhersage mit Begründung (PR-R1). Prozedurale Details just in time. Nach dem Labor: Abweichung zwischen Vorhersage, Messung und Modell analysieren, Fehlerquellen klassifizieren (systematisch, zufällig, Bedienfehler), nächsten Versuch planen. Falsche, sichere Vorhersagen werden ausdrücklich aufgelöst (PR-R2).
- **Beobachtung im Produkt:** Vorhersage, Konfidenz, Post-Lab-Fehlerklassifikation. Reale Praxis: Pre-Lab-Vorhersage und Post-Lab-Analyse realer Versuche können eingetragen werden; Bewertung der realen Durchführung nur durch Betreuende.
- **Unabhängiges Lernoutcome:** verzögerte, unassistierte Analyse eines neuen fehlerhaften Messdatensatzes; Fachpersonbewertung
- **Versagen/Gegenbefund:** Vorhersage wird geraten und übersprungen; Fehleranalyse bleibt bei 'Messfehler' ohne Klasse. Falsifikator: Bei gleicher Gesamtzeit zeigt eine randomisierte Studie keinen Vorteil von Vorhersage plus Post-Lab-Analyse gegenüber reiner Durchführung bei der verzögerten Analyse neuer Datensätze.
- **Enthaltung:** Pre-Lab ersetzt nie die Sicherheitsunterweisung der Einrichtung; keine Mengen- oder Bedingungsangaben für gefährliche Prozeduren (R4-POL-13)
- **Zertifizierungsgrenze:** physische Kompetenz zertifiziert: nein; Sicherheit zertifiziert: nein.
- **KB-Regeln:** PR-R1 (retains), PR-R2 (retains), FB-R2 (retains)

### R4-POL-10 — Räumliches Training gezielt für Lernende mit niedrigem Eingangswert, nicht als Ersatz für Skizzieren und CAD

*Operationen:* spatial_design; *Vorwissen:* novice; *Phase:* acquisition. *Stufe:* niedrig (Trainierbarkeit räumlicher Tests gut belegt; Nutzen für Ingenieur-/Konstruktionsleistung nur an einer Institution quasi-experimentell).

- **Evidenz:** `uttal2013spatial` (supports, abstract); `sorby2018spatialstem` (supports, abstract); `hawes2022spatialmath` (qualifies, abstract); `bartlett2026spatialdesign` (qualifies, abstract)
- **Lernoperation und Intervention:** Zu Beginn ein räumlicher Kurztest (z. B. mentale Rotation, Ansichten zuordnen) als Spur-A-Diagnose; bei niedrigem Wert ein Trainingsmodul mit Skizzieren und, wo möglich, realen Körpern/Modellen. Training wird nicht allen verordnet und nicht als Ersatz für Skizzier- und CAD-Praxis verkauft; Fernwirkung auf Noten oder Konstruktionsleistung wird nicht versprochen.
- **Beobachtung im Produkt:** Kurztest vorher/nachher (Spur A), Bearbeitung der Skizzierserien. Reale Praxis: Skizzen auf Papier können fotografiert und abgelegt werden; Bewertung nur durch Lehrende.
- **Unabhängiges Lernoutcome:** verzögerter, unassistierter Paralleltest räumlicher Fähigkeiten und eine neue, menschlich bewertete Skizzier- oder Modellieraufgabe
- **Versagen/Gegenbefund:** Test-Teaching: Rotationsaufgaben werden auswendig gelernt; Bildschirmtraining statt konkreter Materialien. Falsifikator: Eine Regressionsdiskontinuitäts- oder randomisierte Studie an einer anderen Einrichtung findet bei Lernenden unter dem Schwellenwert keinen Vorteil in verzögerten, menschlich bewerteten Skizzier-/CAD-Aufgaben.
- **Enthaltung:** kein Pflichttraining für Lernende über dem Schwellenwert; keine Aussage über Konstruktionskompetenz aus Rotationstests
- **Zertifizierungsgrenze:** physische Kompetenz zertifiziert: nein; Sicherheit zertifiziert: nein.
- **KB-Regeln:** R4-POL-10-N1 (new)

### R4-POL-11 — Constraint-basiertes CAD: Konstruktionsabsicht explizit machen und mit Änderungstests prüfen

*Operationen:* spatial_design, computational_construction; *Vorwissen:* novice, intermediate; *Phase:* acquisition, consolidation. *Stufe:* sehr niedrig (nur konzeptuelle Quelle zur Konstruktionsabsicht; keine Interventionsstudie gelesen).

- **Evidenz:** `otey2017designintent` (supports, fulltext_partial); `bartlett2026spatialdesign` (context_only, abstract); `keith2008errormanagement` (qualifies, abstract)
- **Lernoperation und Intervention:** Aufgaben verlangen vor dem Modellieren eine schriftliche Konstruktionsabsicht (welche Maße steuern, was bei Änderung erhalten bleiben muss) auf drei Ebenen: Skizzenbedingungen, Modellieroperationen, Beziehungen zwischen Operationen. Bewertet wird nicht nur die Endgeometrie, sondern ein Änderungstest: vorgegebene Parameteränderungen müssen das Modell regenerieren und die Absicht erhalten. Geometrie- und Regenerationsprüfungen deterministisch, Absicht und Modellqualität per Rubrik durch Menschen.
- **Beobachtung im Produkt:** Absichtstext, CAD-Datei, Ergebnis der Änderungstests, Rubrikbewertung. Reale Praxis: nicht physisch; Fertigung eines Teils (z. B. 3D-Druck, Fräsen) ist Spur B und wird extern bewertet.
- **Unabhängiges Lernoutcome:** verzögerte, unassistierte Modellierung eines neuen Teils mit verdeckten Änderungstests, Rubrik durch eine Fachperson
- **Versagen/Gegenbefund:** Änderungstests vorab bekannt und gezielt bedient; Rubrik bewertet Stil statt Absicht. Falsifikator: Modelle, die Änderungstests bestehen, werden von unabhängigen Fachleuten nicht häufiger als absichtsgerecht beurteilt als Modelle, die sie nicht bestehen.
- **Enthaltung:** keine automatische Bewertung der Absichtsbegründung als richtig; ohne CAD-Prüfer nur Spur-A-Aufgaben auf Papier/Skizze; keine Fertigungsfreigabe
- **Zertifizierungsgrenze:** physische Kompetenz zertifiziert: nein; Sicherheit zertifiziert: nein. Gefertigte Teile und Maßhaltigkeit sind Spur B.
- **KB-Regeln:** AS-R1 (refines), FB-R2 (refines), SE-R2 (retains)

### R4-POL-12 — Leistungsbewertung realer Ausführung: Globalskala plus aufgabenspezifische Checkliste als Instrument für menschliche Bewertende

*Operationen:* embodied_psychomotor, empirical_experimental, spatial_design; *Vorwissen:* any; *Phase:* consolidation, final_exam_week. *Stufe:* niedrig (Instrumenteigenschaften nur in medizinischer Simulation meta-analytisch belegt; Übertragung auf Handwerk/Küche ungeprüft).

- **Evidenz:** `ilgen2015checklistgrs` (supports, abstract); `teixeira2021culinaryinstruments` (qualifies, fulltext_partial); `sattelmayer2016motorprinciples` (context_only, fulltext_claim_review)
- **Lernoperation und Intervention:** Das Produkt liefert Bewertungsinstrumente (Globalskala mit verankerten Stufen plus aufgabenspezifische Checkliste mit kritischen Fehlern und Sicherheitsabbruch) und eine Erfassungsmaske; die Bewertung nimmt ein qualifizierter Mensch am realen Objekt vor. Reliabilität wird nicht behauptet, bevor sie im jeweiligen Handwerk mit zwei Bewertenden geprüft ist. Selbstauskunftsskalen (Zutrauen, Selbstwirksamkeit) werden getrennt geführt und nie als Fertigkeit angezeigt.
- **Beobachtung im Produkt:** externe Bewertungseinträge, Übereinstimmung zweier Bewertender. Reale Praxis: Externe Bewertung als eigener Ereignistyp 'external_assessment' mit Instrumentversion; Selbstbewertung als 'self_assessment'.
- **Unabhängiges Lernoutcome:** Übereinstimmung zweier unabhängiger, gegenüber App-Daten verblindeter Bewertender an einer verzögerten realen Aufgabe
- **Versagen/Gegenbefund:** Checkliste belohnt Schrittabhaken statt Qualität; Bewertende kennen App-Fortschritt (Halo); Instrument wird ohne Anker benutzt. Falsifikator: In einer lokalen Prüfung erreichen zwei Bewertende mit dem Instrument keine vorab festgelegte Mindestübereinstimmung; dann darf es nicht als Spur-B-Instrument dienen.
- **Enthaltung:** keine Bewertung durch Sprachmodell oder Bildanalyse als Spur-B-Beleg; keine übernommenen Reliabilitätswerte aus der Chirurgie für Handwerk oder Küche; ohne qualifizierte Person bleibt Spur B leer
- **Zertifizierungsgrenze:** physische Kompetenz zertifiziert: nein; Sicherheit zertifiziert: nein. Auch eine externe Bewertung im Produkt ist kein Zertifikat; sie dokumentiert nur eine beobachtete Ausführung.
- **KB-Regeln:** AS-R1 (refines), AI-R2 (retains)

### R4-POL-13 — Sicherheitsgrenze: Enthaltung bei gefährlichen Verfahren, Verweis auf beaufsichtigte Settings, Sicherheitswissen nur als Spur A

*Operationen:* embodied_psychomotor, empirical_experimental; *Vorwissen:* any; *Phase:* acquisition, consolidation, final_exam_week. *Stufe:* normativ (Sicherheits- und Haftungsgrenze; keine empirische Sicherheit beansprucht; Evidenz stützt nur, dass passives digitales Sicherheitstraining weniger wirksam ist).

- **Evidenz:** `burke2006safetytraining` (supports, abstract); `burke2011dread` (supports, abstract); `dawe2014transfer` (context_only, abstract)
- **Lernoperation und Intervention:** Das Produkt erzeugt keine Schritt-für-Schritt-Anleitungen, Mengen oder Bedingungen, die eine gefährliche Handlung ermöglichen (z. B. Synthesen gefährlicher Stoffe, Umgehung von Schutzeinrichtungen). Sicherheitsinhalte werden als Wissen (Gefahrenerkennung, Begründung von Schutzmaßnahmen, Abbruchkriterien) gelehrt und geprüft und verweisen für Ausführung auf Unterweisung und Aufsicht der Einrichtung. Wo Sicherheitstraining wirksam sein soll, ist es aktiv und praktisch (Modellierung, Hands-on, Dialog) und findet real statt.
- **Beobachtung im Produkt:** Gate-Ereignisse (abgelehnte/umgeleitete Anfragen), Spur-A-Ergebnisse zu Gefahrenerkennung. Reale Praxis: Unterweisungen der Einrichtung können als 'external_safety_briefing' (Datum, Einrichtung) vermerkt werden; das Produkt prüft sie nicht und leitet keine Freigabe ab.
- **Unabhängiges Lernoutcome:** Spur A: verzögerte Gefahrenerkennung an neuen Szenen; real: Beobachtung durch Aufsicht der Einrichtung (außerhalb des Produkts)
- **Versagen/Gegenbefund:** Gate zu eng (blockiert harmlose Grundlagen); Gate zu weit (Anleitungen über Umwege); Nutzende halten Wissenstest für Unterweisung. Falsifikator: Normative Grenze, nicht falsifizierbar im Lernsinn; überprüfbar ist das Gate: ein Red-Team-Satz gefährlicher Anfragen wird in einem festgelegten Anteil nicht abgefangen, oder harmlose Grundlagenfragen werden über einer festgelegten Rate blockiert.
- **Enthaltung:** bei Unklarheit über Gefährdung: Enthaltung und Verweis; keine 'bestanden'-Anzeige für Sicherheitsunterweisungen; keine Simulation gefährlicher Prozeduren mit realistischen Parametern
- **Zertifizierungsgrenze:** physische Kompetenz zertifiziert: nein; Sicherheit zertifiziert: nein. Sicherheitszertifizierung (Spur C) erfolgt ausschließlich durch die zuständige Einrichtung.
- **KB-Regeln:** R4-POL-13-N1 (new)

### R4-POL-14 — Handwerk und Küche: praxisbasiertes Lernen mit Übungsprotokoll und Diagnosefällen; Selbstauskunft ist kein Fertigkeitsnachweis

*Operationen:* embodied_psychomotor, diagnostic_reasoning; *Vorwissen:* novice, intermediate; *Phase:* acquisition, consolidation. *Stufe:* sehr niedrig (Kochlern-Evidenz überwiegend qualitativ/selbstberichtet; keine Studie zu Diagnosefällen im Handwerk gefunden; Holzbearbeitung ohne Evidenz).

- **Evidenz:** `rossen2026cooking` (supports, abstract); `sanaan2026onlinecooking` (qualifies, abstract); `teixeira2021culinaryinstruments` (supports, fulltext_partial); `keith2008errormanagement` (qualifies, abstract); `ericsson1993deliberate` (context_only, fulltext_claim_review)
- **Lernoperation und Intervention:** Das Produkt unterstützt die reale Praxis, statt sie zu ersetzen: Übungsprotokoll mit Ergebnisbeschreibung, Diagnosefälle (Symptom -> mögliche Ursachen -> Prüfschritt -> Korrektur, z. B. Gärfehler, Ausriss an der Schnittkante), Vergleich mit Referenzbildern. Diagnose- und Begründungswissen ist Spur A und wird unassistiert, verzögert, an neuen Fällen geprüft. Zutrauen und Selbstwirksamkeit werden als Selbstauskunft angezeigt, nie als Fertigkeit. Für Feedback zur Ausführung wird an Menschen verwiesen (Kurs, Werkstatt, Mentor).
- **Beobachtung im Produkt:** Protokolleinträge; Spur-A-Diagnosefälle (unassistiert, verzögert, neue Fälle). Reale Praxis: Protokoll je realer Einheit: Rezept/Werkstück, Bedingungen (z. B. Raumtemperatur), Ergebnis, vermutete Ursache bei Fehlern, nächste Änderung. Reflexion, kein Beleg.
- **Unabhängiges Lernoutcome:** Spur A: verzögerte Diagnose neuer Fehlerfälle; Spur B: von Ausbildenden bewertetes reales Werkstück/Gericht mit Instrument nach R4-POL-12
- **Versagen/Gegenbefund:** Protokoll wird zur Fortschrittsanzeige; Diagnosefälle zu eindeutig (eine Ursache); Fotos erzeugen Scheingenauigkeit. Falsifikator: Lernende mit Diagnosefällen zeigen bei verzögerter realer Fehlerbehebung (extern beobachtet) keinen Vorteil gegenüber Lernenden mit gleicher Zeit für Rezepte/Anleitungen.
- **Enthaltung:** keine Ferndiagnose von Fotos als Kompetenzbewertung; keine Lebensmittelsicherheitsfreigaben (z. B. 'noch essbar') und keine Ersatzunterweisung für Maschinen; Selbstwirksamkeitsskalen nur als solche beschriftet
- **Zertifizierungsgrenze:** physische Kompetenz zertifiziert: nein; Sicherheit zertifiziert: nein. Keine Lebensmittelhygiene- oder Maschinenschein-Aussage.
- **KB-Regeln:** MC-R2 (retains), R4-POL-14-N1 (new)

### R4-POL-15 — Fehlerbasiertes Erkunden nur in sicheren Spur-A-Umgebungen (CAD, Simulation, Diagnosefälle)

*Operationen:* spatial_design, diagnostic_reasoning, empirical_experimental; *Vorwissen:* intermediate; *Phase:* consolidation. *Stufe:* niedrig (eine Meta-Analyse, nur Abstract, Aufgabendomänen nicht geprüft; Übertragung auf CAD und Diagnosefälle ist Hypothese).

- **Evidenz:** `keith2008errormanagement` (supports, abstract); `lazonder2016inquiry` (qualifies, abstract)
- **Lernoperation und Intervention:** In CAD-Übungen, Simulationen und Diagnosefällen werden Fehler ausdrücklich zugelassen und als Lerngelegenheit gerahmt (z. B. Überbestimmung erzeugen und auflösen, falsche Hypothese prüfen), gefolgt von Analyse. Ziel ist adaptiver Transfer; für Routineaufgaben bleibt fehlervermeidende Anleitung.
- **Beobachtung im Produkt:** Fehler im Explore-Modus, Analyseantworten. Reale Praxis: nicht anwendbar (nur digitale/konzeptuelle Umgebung).
- **Unabhängiges Lernoutcome:** verzögerte, unassistierte Aufgabe mit strukturell neuem Problem (adaptiver Transfer), menschlich bewertet
- **Versagen/Gegenbefund:** Fehlerermutigung wird auf reale Werkstattarbeit übertragen; Frustration bei Novizen. Falsifikator: In einer randomisierten CAD- oder Diagnoseaufgabe zeigt Fehlermanagementtraining bei adaptivem Transfer keinen Vorteil gegenüber fehlervermeidender Anleitung gleicher Dauer.
- **Enthaltung:** keine Fehlerermutigung bei realer Ausführung mit Verletzungs- oder Schadensrisiko; für Novizen ohne Grundinstruktion: zuerst Lösungsbeispiel (R1-POL-A02)
- **Zertifizierungsgrenze:** physische Kompetenz zertifiziert: nein; Sicherheit zertifiziert: nein.
- **KB-Regeln:** PR-R3 (retains), R4-POL-15-N1 (new)

## 6. Konfliktregeln

| ID | Zwischen | Regel |
|---|---|---|
| R4-CR-1 | R4-POL-03, R1-POL-A04 | Für physische Ausführung gilt „geblockt beginnen“; Interleaving (R1-POL-A04, IL-R1) nur für Spur-A-Aufgaben zur Methoden- oder Variantenwahl. |
| R4-CR-2 | R4-POL-07, R4-POL-01 | Simulator-, VR- und Lab-Scores sind Spur-A-Daten und verändern Spur B nie, auch nicht bei Profizienzkriterium. |
| R4-CR-3 | R4-POL-15, R4-POL-13 | Sicherheitsgate hat Vorrang: keine Fehlerermutigung und keine Explore-Modi bei gekennzeichneten Gefahreninhalten. |
| R4-CR-4 | R4-POL-04, R1-POL-A08 | Spur A: korrektives Feedback nach jedem Versuch (A08). Reale Ausführung: kein vorgeschriebener Plan, Messung nur rückmeldungsfrei. |
| R4-CR-5 | R4-POL-12, R4-POL-14 | Selbstbewertung und externe Bewertung sind getrennte Ereignistypen; nur die externe zählt für Spur B. |

## 7. Designszenarien: synthetische Fälle und adversariale Beispiele

Alle Fälle sind **synthetisch** (keine realen Lernenden, keine Kursmaterialien). Zahlen in den Fällen sind Illustrationen, keine Normen oder Toleranzvorgaben. Es gibt keine gefährlichen Arbeitsanweisungen; wo Gefahr besteht, endet der Fall beim Verweis auf Aufsicht.

### 7.1 Constraint-basiertes CAD-Teil (spatial_design; R4-POL-10, 11, 15)

**Aufgabe.** Ein flacher Winkelhalter mit zwei Befestigungsbohrungen. Vorgabe an die Konstruktionsabsicht: Bohrungen symmetrisch zur Mittellinie, Bohrungsabstand über einen Parameter gesteuert, Wandstärke überall gleich, Radien folgen der Wandstärke.

**Synthetischer Durchlauf.** Lernende L1 bestehen den räumlichen Kurztest knapp nicht und bearbeiten zuerst drei Skizzierserien auf Papier (isometrisch ↔ Ansichten). Dann schreiben sie die Absicht in drei Ebenen auf: (1) Skizze: Mittellinie als Symmetrieachse, Abstand als benannter Parameter; (2) Operationen: Extrusion, dann Bohrungsmuster gespiegelt; (3) Beziehungen: Radius = Funktion der Wandstärke. Das Produkt prüft deterministisch Endmaße und führt zwei verdeckte Änderungstests aus (Länge 80 → 120, Wandstärke 4 → 6, synthetische Werte). Test 1 regeneriert, Bohrungen bleiben symmetrisch; Test 2 bricht, weil ein Radius als fester Wert gesetzt war. Rückmeldung nennt die Stelle (FB-R1). Der Absichtstext bleibt „unverifiziert“, bis eine Lehrperson ihn mit Rubrik bewertet (SE-R2). Spur A: zwei Bestandteile bestanden, einer offen. Spur B entsteht erst, wenn das Teil gefertigt und extern vermessen wird.

**Adversariales Beispiel.** Ein Modell trifft alle Endmaße exakt, wurde aber ohne Bedingungen mit absoluten Koordinaten gezeichnet (oder als „toter“ Volumenkörper importiert). Eine reine Geometrieprüfung würde bestehen; der Änderungstest scheitert sofort. Zweites Beispiel: ein flüssig formulierter Absichtstext, der der tatsächlichen Feature-Struktur widerspricht — nur die menschliche Rubrik mit Blick in den Feature-Baum erkennt das. Ein Sprachmodell darf den Text nicht als „richtig“ markieren.

### 7.2 Experimentelle Chemieprozedur mit sicherer virtueller Simulation (empirical_experimental; R4-POL-07, 08, 09, 13)

**Aufgabe.** Säure-Base-Titration im **virtuellen** Labor mit abstrahierten Größen: Probe unbekannter Konzentration, Titrant mit vom Lab vorgegebener Konzentration, Indikatorwahl. Keine Rezepturen, keine Stoffmengen für reale Herstellung, keine gefährlichen Stoffe; die reale Durchführung findet nur im beaufsichtigten Praktikum nach Unterweisung der Einrichtung statt.

**Synthetischer Durchlauf.** Pre-Lab: Lernende L2 sagen das Äquivalenzvolumen aus den vorgegebenen Werten voraus und geben ihre Sicherheit an (PR-R1). Die Simulation liefert drei synthetische Messreihen; eine davon ist systematisch verschoben (eingebauter Fehler: Luftblase in der Bürettenspitze bzw. ungeeigneter Indikator). L2 vergleicht Vorhersage, Messungen und Modell, klassifiziert die Abweichung als systematisch, begründet die Ursache und plant eine Wiederholung (R4-POL-09). Rechen- und Einheitenfehler werden deterministisch geprüft (FB-R2). Das Transferetikett nennt, was die Simulation **nicht** lehrt: tropfenweise Kontrolle nahe dem Umschlag, Ablesen am realen Meniskus, Farbwahrnehmung unter Laborlicht, Umgang mit Glas und Chemikalien, persönliche Schutzausrüstung. Spur A: Vorhersage, Fehleranalyse und Planung unassistiert und nach einer Woche an einem neuen Datensatz geprüft. Spur B: Durchführung im Praktikum, von Betreuenden mit Checkliste und Globalskala bewertet (R4-POL-12). Spur C: Laborzulassung durch die Einrichtung.

**Adversariales Beispiel.** (a) Nach zehn perfekten Simulationsläufen fordert L2 den Status „Titration beherrscht“. Das Produkt zeigt Spur A = bestanden, Spur B = „nicht beobachtet“, Spur C = „außerhalb des Produkts“ (R4-CR-2). (b) Eine Anfrage, im Simulator die Konzentration auf ein gefährliches Niveau zu setzen oder eine Herstellungsprozedur für einen gefährlichen Stoff zu erhalten, wird vom Gate abgelehnt; Antwort auf Konzeptebene mit Verweis auf Aufsicht (R4-POL-13). (c) Ein Datensatz mit zu sauberen Werten (Streuung null) muss als unplausibel erkannt werden — ein Item, das Wiedererkennen statt Datenkritik bricht.

### 7.3 Fehlerdiagnose bei der Teiggärung (embodied_psychomotor, diagnostic_reasoning; R4-POL-14, 04)

**Aufgabe.** Diagnosefälle zu Hefeteig: Symptom → konkurrierende Ursachen → unterscheidendes Merkmal → Prüfschritt → Korrektur. Keine Aussagen zur Lebensmittelsicherheit („noch essbar“).

**Synthetischer Durchlauf.** Übungsprotokoll von L3 (synthetisch): Raumtemperatur 17 °C, Stückgare 45 min nach Rezeptvorgabe, Brot flach und dicht, seitlich aufgerissen. Diagnosekarte: Kandidaten sind Untergare (zu kalt/zu kurz), inaktive Hefe, Salz direkt auf Hefe, schwaches Mehl. Unterscheidende Merkmale: dichte, feine Krume und seitliches Aufreißen sprechen eher für Untergare; eine zusammengefallene, grobe, breitgelaufene Form eher für Übergare. Prüfschritte: Teigtemperatur messen, Fingerdruckprobe vor dem Backen, Hefe-Probe in lauwarmer Flüssigkeit. L3 wählt „Untergare durch Temperatur“, plant längere Gare und Fingerdruckprobe. Die Diagnose ist Spur A und wird nach einer Woche an neuen Fällen unassistiert geprüft. Ob das nächste Brot gelingt, ist Spur B; ohne Kurs oder Mentor bleibt Spur B leer, das Protokollfoto ist Reflexion.

**Adversariales Beispiel.** (a) Nur ein Foto eines flachen Brots, ohne Zeit- und Temperaturangaben: Über- und Untergare können ähnlich aussehen. Richtige Antwort ist, fehlende Information anzufordern, nicht eine Ursache zu raten; ein Item mit nur einer „richtigen“ Ursache würde Diagnosekompetenz verfehlen. (b) Lernende tragen „Selbstwirksamkeit: sehr hoch“ ein; das Produkt zeigt es als Selbstauskunft, nicht als Fertigkeit (`teixeira2021culinaryinstruments`).

### 7.4 Toleranz einer handgeschnittenen Holzverbindung (embodied_psychomotor; R4-POL-01, 02, 03, 06, 12, 13)

**Aufgabe.** Zapfenverbindung von Hand: Bezugsflächen festlegen, anreißen, auf der Abfallseite der Linie sägen, Brüstungen sauber, Zapfen passt mit Handdruck. Sicherheit (Werkstück sichern, Hände hinter der Schneide, Werkstattregeln) ist Spur A als Wissen und wird in der Werkstatt unterwiesen.

**Synthetischer Durchlauf.** L4 sieht segmentierte Demonstrationen (Anreißen, Sägeführung, Stemmen) mit dem Ergebniskriterium je Schritt (R4-POL-02), macht vor jeder Werkstatteinheit eine mentale Probe der Reihenfolge mit Kontrollpunkten (R4-POL-06) und übt fünf Verbindungen gleichen Typs geblockt, bevor andere Maße folgen (R4-POL-03). Das Protokoll enthält Selbsturteile („passt“). Die Ausbilderin bewertet die fünfte Verbindung mit dem Bogen nach R4-POL-12: Globalskala plus Checkliste (Fuge an der Brüstung mit Fühlerlehre gemessen, Rechtwinkligkeit, Passung, Ausrisse). Synthetisches Ergebnis: Fuge an einer Brüstung 0,5 mm, Ursache vermutlich verlaufender Sägeschnitt. Die Diagnosekarte „Fuge einseitig → Sägeschnitt verläuft → Führung/Anriss prüfen“ wird zu Spur-A-Übung, die nächste reale Einheit fokussiert die Sägeführung.

**Adversariales Beispiel.** (a) L4 lädt ein Foto einer makellosen Verbindung hoch — eigenes Werkstück oder nicht, Kamerawinkel verdeckt Fugen. Das Produkt bewertet es nicht; Spur B ändert sich nicht. (b) L4 besteht alle Quizfragen zu Reihenfolge und Fehlerbildern (Spur A), die externe Bewertung ist schwach (Spur B). Das Produkt zeigt beide getrennt und mittelt nicht. (c) Anfrage, wie man eine Schutzeinrichtung an einer Maschine umgeht, um schneller zu schneiden: Ablehnung und Verweis (R4-POL-13).

## 8. Risiko- und Validitätsaudit

| Risiko | Betroffene Policies | Alternative Erklärung / Bias | Gegenmaßnahme |
|---|---|---|---|
| Publikationsbias und unterpowerte Primärstudien in der Motorikforschung | 03, 04, 05 | Gepoolte Effekte spiegeln Selektion, nicht Wirkung (`mckay2024focusbias`, `mckay2022feedbackfrequency`) | Stufen niedrig/sehr niedrig; keine Wirkversprechen; Falsifikatoren mit präregistrierten Studien |
| Labor-zu-Praxis-Lücke | 03, 07 | Einfache Laboraufgaben mit kurzer Übung; Setting und Alter konfundiert (`czyz2024ciretention`) | angewandte Schätzer maßgeblich; Enthaltung bei Universalregeln |
| Sofortmessung statt Behalten | 02, 06 | Leistung während/kurz nach Training ≠ Lernen (`sattelmayer2016motorprinciples`) | unabhängige Outcomes immer verzögert |
| Vergleich gegen „keine Intervention“ | 01, 07 | Simulation schlägt nichts, nicht reale Übung (`cook2011simulation`) | Simulation nur als Vorbereitung, Spur B nur extern |
| Entwickler- und Ein-Institutionen-Studien | 07, 08, 10 | Erwartungs- und Implementationseffekte (`finkelstein2005cck`, `sorby2018spatialstem`) | Stufe niedrig; Replikation als Bedingung |
| Selektion bei beobachtenden Laborvergleichen | 08 | Wer optionale Labore wählt, ist anders; Differenzwertmethode setzt itemspezifische Wirkung voraus (`holmes2017labvalue`) | Aussage auf „keine messbare Inhaltsfestigung“ beschränkt |
| Neuheit und Präsenz statt Lernen | 07 | Motivation und Präsenz werden als Wirkung berichtet (`reeves2021virtuallabs`, `makransky2019immersivevr`) | VR kein Standard; Lernoutcome statt Zufriedenheit |
| Selbstauskunft als Fertigkeitsmaß | 01, 12, 14 | Zutrauen ≠ Können (`teixeira2021culinaryinstruments`) | getrennte Ereignistypen |
| Testformat bestimmt Ergebnis | 08, 09 | Itemformat erklärt viel Varianz (`schwichow2016cvs`) | Spur-A-Prüfung mit neuen, offenen Planungsaufgaben und Fachbewertung |
| Halo der Bewertenden | 12 | Wer den App-Status kennt, bewertet milder | Verblindung empfohlen, zweite Bewertung |
| Indirektheit (Chirurgie → Handwerk/Küche) | 01, 02, 12 | Andere Aufgabenstruktur, andere Bewertende | Übertragung als Hypothese gekennzeichnet; lokale Reliabilitätsprüfung |
| Abstract- und Preprint-Lesart | alle | Abstracts überzeichnen; Preprint ≠ Version of Record | Zugangsstufe je Kante; Zahlen aus Preprints als solche markiert |
| Produktrisiko: Scheinkompetenz und Haftung | 01, 13 | Nutzende oder Dritte lesen Spur A als Befähigung | normative Grenze, Anzeige „nicht beobachtet“, keine Zertifikatssprache |
| Produktrisiko: Gate zu eng oder zu weit | 13 | Überblockieren harmloser Grundlagen oder Umgehung | Red-Team-Satz als Prüfgröße (Falsifikator) |
| Gerechtigkeit | 01, 12 | Spur B hängt vom Zugang zu Ausbildenden ab | Spur B leer ist neutral, kein Defizit; Hinweise auf Kurse/Werkstätten |

## 9. Was wir nicht behaupten können

- Dass irgendeine R4-Policy Lernen verbessert: `learning_evaluation` ist überall `NOT_RUN`.
- Dass das Produkt physische, Labor- oder Sicherheitskompetenz misst oder bescheinigt. Es tut beides ausdrücklich nicht.
- Dass zufällige Übungsreihenfolge, seltene Rückmeldung oder externer Aufmerksamkeitsfokus reale Handwerks-, Küchen- oder Laborleistung verbessern.
- Dass Simulationen Haptik, Toleranz, Materialgefühl oder Sicherheitsverhalten übertragen; dazu wurde keine Studie gefunden.
- Dass räumliches Training Konstruktions- oder CAD-Kompetenz verbessert.
- Dass Änderungstests Konstruktionsabsicht valide messen (nur konzeptuell begründet).
- Dass Globalskalen und Checklisten aus der Chirurgie im Holzhandwerk oder in der Küche reliabel sind.
- Dass Diagnosefälle reale Fehlerbehebung beim Backen oder Holzbearbeiten verbessern; es gibt dazu keine gelesene Studie.
- Eine unabhängige oder menschliche Prüfung dieser Arbeit. Die Selbstprüfung im `verification_log` stammt vom selben Modell.

## 10. Fragen an unabhängige Gutachterinnen und Gutachter

1. Ist die Lesart von `czyz2024ciretention` korrekt, dass der angewandte, nicht der gepoolte Schätzer für reale Handwerks- und Laborarbeit maßgeblich ist? Wie ist die Gegenposition von Ammar et al. 2023 (nur Metadaten) im Volltext begründet?
2. Ist die Folgerung aus `mckay2022feedbackfrequency` (kein Ausblendplan als Standard) zu stark für komplexe Aufgaben, die dort kaum vorkommen? Gibt es präregistrierte Studien zu komplexen realen Aufgaben?
3. Ist das Zwei-/Drei-Spuren-Modell (§3) für Lehrwerkstätten, Praktika und Kochkurse praktikabel, oder braucht Spur B Zwischenstufen (z. B. Peer-Bewertung mit Anker)?
4. Welche validierten Instrumente für reale Ausführung im Holzhandwerk, Backen oder Laborpraktikum existieren, die hier fehlen (Gesellenprüfungsbögen, Laborpraktikumsrubriken)?
5. Überzeichnet `finkelstein2005cck` den Simulationsvorteil (Abschnittszuteilung, Entwicklergruppe, sichtbarer Elektronenfluss)? Gibt es Chemie-spezifische Vergleiche virtuell vs. real mit realem Folgeversuch?
6. Ist die Interpretation von `holmes2017labvalue` (keine messbare Inhaltsfestigung) angemessen begrenzt?
7. Sind die Synthese- und Sicherheitsgrenzen in §7.2 ausreichend, oder gibt der Titrationsfall zu viel prozedurales Detail?
8. Sind die Unterscheidungsmerkmale Über-/Untergare in §7.3 fachlich korrekt (Bäckerei-Fachprüfung)?
9. Ist die Konstruktionsabsicht in drei Ebenen (`otey2017designintent`) der richtige Bewertungsrahmen, und gibt es empirische Studien zu Änderungstests als Bewertung?
10. Welche Evidenz zu Haptik und Kraftdosierung in Simulatoren (Chirurgie, Schweißen) würde R4-POL-07 ändern?

## 11. Abdeckung des R4-Auftrags und Lücken

| Auftrag (Issue #25) | Stand |
|---|---|
| Motorisches/perzeptuelles Lernen: Demonstration, deliberate practice, blocked/random, Feedback, Fokus, Fehler, mentale Probe | abgedeckt (R4-POL-02 bis 06, 15), überwiegend Abstracts; zwei Volltext-Meta-Analysen, ein Preprint |
| Simulation vs. reale Übertragung, VR, virtuelle/Remote-Labore | teilweise: Medizin und Physik; Chemie/Biologie-spezifisch und Remote-Labore nicht registriert |
| Raum, Skizzieren, CAD, Konstruktionsdidaktik | teilweise: räumliches Training gut, CAD/Skizzieren nur konzeptuell |
| Labor: Forschen vs. Kochbuchlabor, Versuchsplanung, Messunsicherheit, Materialcharakterisierung, Pre-Lab | teilweise: Nullbefund Inhaltsfestigung, Variablenkontrolle, Anleitung, Pre-Lab narrativ; Messunsicherheit und Materialcharakterisierung als Lernziel ohne Quelle |
| Handwerk und Küche, Lehrlingsmodelle, Bewertungsinstrumente | teilweise: Kochen qualitativ, Instrumente medizinisch; Holz, Backen, Lehrlingsausbildung ohne Lernstudie |
| Sicherheits- und Zertifizierungsgrenze | abgedeckt (§3, R4-POL-01, 13), normativ |
| Vier Designszenarien mit synthetischem Fall und adversarialem Beispiel | §7 |
| Evidenzregister mit Null-/Gegenbefunden, Suchprotokoll | `r4/r4_evidence.json` (u. a. `mckay2022feedbackfrequency`, `mckay2024focusbias`, `holmes2017labvalue`, `makransky2019immersivevr`, `ammar2023cimyth`) |

Deklarierte Lücken (vollständig in `coverage_gaps`): Holzbearbeitung/Handwerkzeuge, Backen, beobachtete Kochfertigkeit, CAD-Interventionen, Skizzieren, Chemie-spezifische virtuelle Labore, Messunsicherheit und Materialcharakterisierung, Haptik/Schweiß-VR, selbstgesteuertes Üben, Volltext von Ammar et al. 2023, laborspezifisches Sicherheitstraining. Für `rule_based_contextual` und `open_synthesis` ist R3 zuständig, für Programmieren R2; klinische Diagnostik bleibt bei R3.

## 12. Reproduktion

- Register und Suchprotokoll: `docs/research/workstreams/r4/r4_evidence.json` (`entries[].access` mit URL/Dienst und gelesenen Abschnitten; `search_log` mit exakten Abfragen). DOIs über `https://api.crossref.org/works/{doi}` prüfbar; PubMed-Abstracts über `efetch.fcgi?db=pubmed&id=<PMID>&rettype=abstract`; PMC-Volltexte über `efetch.fcgi?db=pmc&id=<PMCID>`; Semantic-Scholar-Abstracts über `POST /graph/v1/paper/batch`; ERIC über `https://api.ies.ed.gov/eric/`.
- Frei zugängliche Volltexte: PMC4714441 (`sattelmayer2016motorprinciples`), PMC11237090 (`czyz2024ciretention`), PMC8351978 (`teixeira2021culinaryinstruments`), APS Open Access (`finkelstein2005cck`, `holmes2017labvalue`), PsyArXiv-Preprint v2cp7 (`mckay2022feedbackfrequency`), Repositorien der Universität Aarhus (`radhakrishnan2021ivr`) und der Universitat Jaume I (`otey2017designintent`).
- Policies: `docs/research/workstreams/r4/r4_learning_policies.json`; §5 dieses Berichts ist daraus erzeugt.
- Tests: `cd tests && python3 -m unittest test_r4_learning_policies test_r1_learning_policies` (Ergebnis bei Abgabe: 34 Tests OK, 1 übersprungen — die R1-only-Prüfung aller Engine-Regeln).
- Keine Produktionscodeänderung (`exam_mastery/` unverändert), keine Kursmaterialien, keine personenbezogenen Daten, keine kostenpflichtigen Dienste.
