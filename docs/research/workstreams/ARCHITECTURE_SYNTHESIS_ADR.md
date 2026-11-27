# R6 — Domänenübergreifende Synthese und Architecture Decision Record

Stand 27.11.2026. **Entscheidungsstatus: PROPOSED.** Nur der Owner kann den Vorschlag annehmen, ändern oder verwerfen. Dieses Dokument ist Forschung, keine Implementierung und keine Freigabe. Alle 116 Policies der Workstreams R1–R5 und R7–R9 sind `design_hypothesis` mit `learning_evaluation: NOT_RUN`. Kein Mastery-Produkt hat eine gemessene Lernwirkung. Historische `HUMAN_REJECTED`-Bewertungen bleiben unverändert.

| Artefakt | Inhalt |
|---|---|
| dieses Dokument | Synthese, ADR mit Optionen und Bewertung, Ontologie- und Vertragsübersicht, Minimum Credible System, Phasen-Gates, OWNER_DECISIONS_REQUIRED, P4-Integrationsplan |
| [r6/adr.json](r6/adr.json) | Optionen, Kriterienbewertung (ordinal, mit Fundstellen und offenen Unbekannten), vorgeschlagene Entscheidung `PROPOSED`, verworfene Optionen, Gates, Owner-Entscheidungen mit `blocks`/`default` |
| [r6/skill_ontology_v1.json](r6/skill_ontology_v1.json) | Operationen (Charter-Taxonomie), Kompetenztypen, Evidenzarten, Hilfestufen, beobachtbare Zustände, Prüferklassen, Spuren und Praxis-/Zertifizierungsgrenze, Abbildung der heutigen Engine-Vokabulare |
| [r6/observation_contract_v1.json](r6/observation_contract_v1.json) | Ereignisschema (wer/was/wann, Hilfestatus, Quelle, Zeitsemantik, Itemrolle, Provenienz) und Ableitungsregeln für Zustände |
| [r6/policy_index.json](r6/policy_index.json) | eingefrorener Schnappschuss aller 116 Policies mit Quell-Commits (Eingabe, nicht Quelle der Wahrheit) |
| `tests/test_r6_architecture.py` | Strukturprüfungen: Status `PROPOSED`, Policy-IDs existieren, Operationen = Charter-Taxonomie, jede Owner-Entscheidung hat `blocks` und `default`, keine numerischen Bewertungsfelder. Prüft Struktur, nicht Richtigkeit. |

**Lesart.** **Befund** = in einem Workstream-Bericht mit Fundstelle belegt; **Hypothese** = abgeleitet, ungeprüft; **Designentscheidung** = Setzung mit Begründung, ohne empirischen Lernbeleg; **nicht gestützt** = darf nicht behauptet werden. Die Bewertung der Architekturen ist durchgehend Designurteil, keine Messung.

## 0. Kurzfassung

1. **Die 116 Hypothesen stimmen in einem Punkt überein, und der betrifft Messung, nicht Didaktik.** Jeder Workstream verlangt denselben Kompetenzbeleg: unassistiert, nach echter verstrichener Zeit, an einem neuen oder umformulierten Item, mit deklariertem Prüfer. Dieser Konsens ist überwiegend normativ (25 Policies `normative`), nicht empirisch.
2. **Die didaktischen Empfehlungen sind schwach belegt und domänengebunden.** 0 Policies `high`, 14 `moderate`, 61 `low`, 16 `very_low`. Für mehrere angeblich universelle Regeln gibt es in mindestens einer Domäne einen Gegenbefund (§2.4).
3. **Daraus folgt eine Asymmetrie für die Architektur:** Harte, deterministische und testbare Technik gehört in die Evidenz-, Prüfer- und Enthaltungsschicht. Die Sequenzierung bleibt einfach, parametrisiert und reversibel.
4. **Vorgeschlagen (PROPOSED): Hybrid H-AB „Evidenzkern mit Vorlagen“.** Ein schmaler Kern aus B (typisierter semantischer Vertrag, Beobachtungsvertrag, Prüferadapter, deterministische Zustandsableitung) trägt Vorlagen je Operationsfamilie und Domänenpakete als Daten aus A. Agenten helfen nur beim Erstellen zur Build-Zeit, hinter deterministischen Gates und menschlicher Prüfung. Es gibt keinen Laufzeitagenten, keine generische Policy-Sprache, kein Knowledge Tracing und keinen eigenen Scheduler.
5. **H-AB liegt am nächsten an der vorhandenen Engine** (`em-experience-v1`, `em-decision-v1`, `em-diagnosis-v1`, `em-track-v1`) und hat deshalb die geringsten Migrationskosten. Die vorhandenen Produkte wurden wegen ihrer Inhaltsqualität abgelehnt. Keine Architektur löst dieses Autorenproblem (CD-5).
6. **Verworfen:** C (agentisch komponierte Erfahrungen zur Laufzeit) wegen Budget 0, fehlender Offline-Fähigkeit, Sicherheitsrisiken und weil Auditoren aus demselben Modellumfeld keine Kompetenzbelege liefern. Volles B (generische Policy-Engine, vollständiger Kompetenzgraph), weil die Evidenzlage diese zusätzliche Schicht nicht trägt. Reines A, weil der Messvertrag ohne gemeinsamen Kern pro Vorlage dupliziert und nicht durchgesetzt würde.
7. **Minimum Credible System:** eine Operationsfamilie (`symbolic_procedure` mit abrufbaren Bausteinen) in einem quellenfreien quantitativen Thema mit vorhandenen deterministischen Prüfern. Manipuliert wird nur das interaktive Produkt (adaptive Strecke gegen statische Workbook-Sequenz bei gleicher Zeit). Anki und Lehrbuch bleiben konstant. Endpunkt: unassistierter Test nach mindestens 7 Tagen mit unabhängig verfassten neuen Items. Ein Nullbefund ist ein zulässiges Ergebnis.
8. **Acht Gates** (G0–G7) plus ein Marken-Gate, jedes mit falsifizierbarem Bestehenskriterium. **33 Owner-Entscheidungen** (OD-01 bis OD-31, OD-13 dreigeteilt), jede mit blockiertem Gate und Default bei Untätigkeit.
10. **Red-Team abgeglichen (§12):** 40 Befunde der Schwere Blocker oder Major. 34 sind angenommen und haben Änderungen ausgelöst, 6 teilweise angenommen, keiner abgelehnt. Der einzige Blocker (RT-26) betrifft `kc_status`: Hilfe wird nur an derselben Aufgabe gezählt, Zeitstempel werden nicht geprüft. Deshalb ist `kc_status` nie Evaluationsendpunkt, und der Evidenzkern zählt Hilfe auf KC-Ebene und prüft die Zeit auf Plausibilität.
9. **Vor der Annahme kann architekturunabhängige Arbeit laufen:** der CD-8-Fix (Anki-Exportidentität), Hygiene-Fixes und Testpflege. Merges macht nur der Owner, Agenten nie.

## 1. Eingaben, Methode, Grenzen

**Eingaben** (gelesen am 27.11.2026, nur Kurzfassungen, Entscheidungs- und Owner-Abschnitte; keine neue Literatursuche):

| Kürzel | Datei | Commit |
|---|---|---|
| R0 | `KB_GAP_AUDIT.md` (§1, §6, §8, §9) | `2fbd2031` |
| R1 | `R1_LEARNING_SCIENCE.md` (§1, §2, §4, §5, §8), `r1/r1_learning_policies.json` | `35598727` |
| R2 | `R2_FORMAL_QUANTITATIVE.md` (§1, §3, §4, §6, §12.3, §13) | `e73c3fe1` |
| R3 | `R3_ARGUMENT_CASE_DIAGNOSIS.md` (§1, §7, §11), `r3/r3_learning_policies.json` | `b675dec2` |
| R4 | `R4_EMBODIED_EXPERIMENTAL_DESIGN.md` (§1, §3, §6, §9), `r4/r4_learning_policies.json` | `92828609` |
| R5 | `r5/AI_TUTOR_MEASUREMENT.md` (§1, §4, §6, §7, §9, §12.3), `r5/r5_tutoring_policies.json` | `4b444c27` |
| R7 | `R7_RESOURCES_VISUALISATION.md` (§1, §6, §7, §11, §12) | `308394aa` |
| R8 | `R8_ANKI_OBSIDIAN_WORKFLOWS.md` (§0, §2, §5, §12, §13) | `8d6194b4` |
| R9 | `TUTOR_ADOPTION_DECISION.md`, `TUTOR_EVALUATION_PROTOCOL.md` (§2, §6) | `c63e0028` |
| Programm | `docs/programme/PROGRAMME_STATE.json` (AD-0…AD-3, CD-1…CD-8, `engine_capabilities`, `product_identity`, `owner_attention`) | `bd36f0a3` |
| Engine | `exam_mastery/learning/{policy,tracks,diagnose,experience,experience_evidence,experience_adaptation,tutor,evaluation}.py`, `exam_mastery/prompts/`, `exam_mastery/knowledge/principles.json`; nur gelesen, nicht ausgeführt | `5ad257d9` (Spitze des Entwurfsstapels, PR #43) |
| Charter | `docs/research/RESEARCH_FIRST_PROGRAM_20261126.md`, `docs/PRODUCT_CONTRACT.md`, `docs/LEARNING_PRODUCT_CONTRACT.md` | dieser Branch |

**Methode.** (1) Policy-Index nach Operation, Sicherheitsstufe und Produkt ausgewertet (Zählungen in §2.1 sind reproduzierbar, §13). (2) Domänenübergreifende Befunde nur dann als „übergreifend“ geführt, wenn mindestens zwei Workstreams mit verschiedenen Domänen denselben Befund berichten. (3) Für jede als universell gehandelte Regel ein Gegenbefund aus den Berichten gesucht (§2.4). (4) Architekturoptionen an den Charter-Kriterien ordinal bewertet, je Urteil mit Fundstelle und ausdrücklichen Unbekannten (`r6/adr.json`). (5) Engine nur gelesen, um Migrationskosten zu beurteilen.

**Grenzen.** R6 hat kein eigenes Evidenzregister und keine Primärquelle gelesen. Alle Befunde stammen aus den Workstream-Berichten, deren unabhängige Prüfung aussteht (R0–R9 je „independent review pending“). Fehler dort setzen sich hier fort. Autor ist dasselbe Modell wie bei den Workstreams. Ein Red-Team arbeitet parallel und unabhängig (§12). Für Zeit- und Komplexitätsaussagen gibt es keine Messung. Sie sind als ordinale Urteile mit Begründung formuliert, Zahlen werden nicht erfunden.

## 2. Synthese

### 2.1 Was die 116 Hypothesen gemeinsam ausweisen (Befund, aus dem Index gezählt)

- **Status:** 116/116 `design_hypothesis`, 116/116 `learning_evaluation: NOT_RUN`. 100 `not_implemented`, 16 `partially_implemented_unverified` (R5-POL-01, R5-POL-02, R5-POL-04, R7-POL-02, R7-POL-03, R7-POL-04, R7-POL-06, R7-POL-09, R8-POL-01, R8-POL-02, R8-POL-05, R8-POL-06, R8-POL-08, R8-POL-09, R9-POL-03, R9-POL-10).
- **Sicherheit:** 0 `high`, 14 `moderate`, 61 `low`, 16 `very_low`, 25 `normative`.
- **Abdeckung nach Operation** (Mehrfachzuordnung): `symbolic_procedure` 47, `recall_discrimination` 41, `computational_construction` 41, `formal_proof` 31, `self_regulation` 28, `empirical_experimental` 26, `diagnostic_reasoning` 23, `rule_based_contextual` 18, `spatial_design` 14, `open_synthesis` 13, `embodied_psychomotor` 12.
- **Moderat gestützte Policies je Operation:** Für `open_synthesis` gibt es nur eine (R5-POL-04, eine Messregel), für `spatial_design` nur eine (R9-POL-06, eine Evaluationsregel), für `embodied_psychomotor` keine. Wo die Evidenz am dünnsten ist, liegen auch die nicht automatisch prüfbaren Operationen.

### 2.2 Domänenübergreifend tragfähige Befunde

| # | Befund | Domänen mit Beleg | Art | Fundstellen | Grenze |
|---|---|---|---|---|---|
| X1 | Assistierte und unassistierte Leistung laufen auseinander. Mehr Hilfe steigert In-Sitzung-Leistung, ohne unassistierte Leistung zu heben, teils senkt sie sie. | Schulmathematik, Python, Essay, Hochschulkurse | empirisch, moderat | R5 §1 Nr. 1, 5, 8; R0 D10; R5-POL-04 | überwiegend Schule und Labor; Hilfe außerhalb des Produkts unsichtbar (R5 §6 Nr. 1) |
| X2 | Sofortleistung ist kein Ersatz für verzögerte Messung; Vorteile zeigen sich teils erst verzögert, teils kehren sie sich um. | Klinik, Mathematik (Fehlerbeispiele), Beweise, Motorik, Tutoring | empirisch, niedrig bis moderat | R3 §1 Nr. 8 (`mamede2012reflection`); R5 §1 Nr. 11; R2 §1 Nr. 3 (`roy2017eproofs`); R4 §1 Nr. 2; R5 §6 Nr. 6 | wenige, kleine Studien je Domäne |
| X3 | Wahrheit einer Aussage, Gültigkeit einer Begründung und Kompetenz einer Person sind drei verschiedene Prüfgegenstände. | Beweis, Code, Recht, Klinik, Handwerk | normativ, gestützt durch Messbefunde | R2 §4; R3 §7; R4 §3; R2-POL-14; R9-POL-08 | Zuordnung der Prüfer ist Designentscheidung |
| X4 | Modellbewertung offener Antworten ist kein Kompetenzbeleg; sie überbewertet und schwankt nach Domäne und Rubrik. | Beweise, deutsches Recht, Differenzialdiagnose | empirisch, niedrig bis moderat | R2 §1 Nr. 5; R3 §1 Nr. 10; R2-POL-05; R3-POL-11; R9-POL-05 | Zahlen gelten für Modelle von 2025/26 (R2 §13) |
| X5 | Novizen profitieren zuerst von Lösungsbeispielen bzw. reduzierter Suchlast; für Fortgeschrittene gilt das nicht, und ein valider Umschaltpunkt ist nicht belegt. | Mathematik, Programmieren, Recht | empirisch, niedrig bis moderat | R1 §1 Nr. 4; R1-POL-A02; R1-POL-A03; R2-POL-09; R3 §1 Nr. 2; R3-POL-03 | Umschaltdiagnose `very_low`; Gutachtenstil selbst ohne Lernstudie |
| X6 | Aufbereitung ist nicht Lernhandlung: polierte Darstellung, Immersion oder Zusehen heben Urteil oder Präsenz stärker als Lernen. | Beweise, Algorithmen, Labor/VR, Visualisierung | empirisch, niedrig | R2 §1 Nr. 3; R2-POL-17; R4 §1 Nr. 7; R7 §1 Nr. 2; R7-POL-01 | Ressourcen selbst ohne kontrollierte Studie (R7 §11) |
| X7 | Inhaltsfreies Training überträgt sich schlecht (Logik, generisches Debiasing, Raumtraining → Konstruktion). | Philosophie, Klinik, CAD | empirisch, niedrig | R3 §1 Nr. 6 und 9; R4 §1 Nr. 9; R3-POL-06; R4-POL-10 | Sekundärbeschreibungen, Abstracts |
| X8 | Selbstauskunft, Konfidenz, Zufriedenheit und Kartenstatistik sind keine Kompetenzbelege. Lernurteile während des Übens können das Lernen sogar verändern. | alle | empirisch (Reaktivität) und normativ | R1 §1 Nr. 7; R1-POL-A09; R5 §6 Nr. 8; R4-POL-14; R8-POL-12 | Reaktivität mit Wortmaterial belegt, Übertrag auf Problemlösen offen |
| X9 | Hilfe auf Anforderung, Bottom-out-Hinweis zählt als Lösungseinsicht, unproduktive Hilfenutzung wird beobachtet, nicht sanktioniert. | Mathematik-ITS | empirisch, niedrig (korrelativ) | R5 §1 Nr. 11; R5-POL-03; R5-POL-08; R1-POL-A08 | Stufenzahl ungeprüft (CD-4) |
| X10 | Ein einziger Scheduler (Anki); Benchmark-Vorhersagegüte ist kein Lernergebnis. | alle mit abrufbaren Bausteinen | normativ, gestützt durch Benchmarkbefunde | R8 §0 Nr. 3; R8-POL-01; R8-POL-12; R1-POL-A05; AD-1 | keine RCT FSRS gegen SM-2 gefunden |

**Population (nach Red-Team RT-08):** Ein großer Teil der tragenden Evidenz für X1, X9 und die Abruf-, Interleaving- und Hinweis-Policies stammt aus Schulen oder Laboren, etwa `bastani2025` (Klassen 9–11), `rohrer2020interleaved` (Klasse 7) und die Mittelstufen-ITS. Mastery richtet sich an Hochschule und Erwachsene. „Übergreifend“ heißt hier „über Domänen“, nicht „über Populationen“. Eine Gültigkeit für Erwachsene oder das Selbststudium wird nicht behauptet. Ein Feld `population_match` je Policy ist als Eingabe für die unabhängige Prüfung (OD-26) empfohlen.

### 2.3 Domänengebundene Befunde (nicht übertragen)

| Bereich | Befund oder Setzung | Fundstellen | Warum nicht übertragbar |
|---|---|---|---|
| Abruf | robust für abrufbare Bausteine; kein Zusatznutzen beim Verfahrenserwerb aus Worked Examples; in Mathematik gegen Wiederlesen nicht robust | R1 §1 Nr. 1; R1-POL-A01; R1-POL-A02 | „jede Einheit endet mit Abruf“ ist zu grob |
| Interleaving | verbessert Methodenwahl in Schulmathematik (mit Verteilung konfundiert); für physische Ausführung „geblockt beginnen“ | R1-POL-A04; R4-POL-03; R4-CR-1 | in angewandten motorischen Studien nahe null |
| Rückmeldung | Spur A: korrigierende Information nach jedem Versuch; physische Ausführung: kein Ausblendplan als evidenzbasiert, Messung rückmeldungsfrei | R1-POL-A08; R4-POL-04; R4-CR-4 | Guidance-Hypothese meta-analytisch nicht gestützt |
| Beweise | Verständnis, Validierung und Konstruktion getrennt messen; Selbsterklärungstraining für Beweisverständnis | R2-POL-01; R2-POL-02; R2-POL-03 | Befunde aus Zahlentheorie und Analysis, eine Forschungsgruppe |
| Programmieren | Tracing vor Schreiben (korrelativ); verborgene und Property-Tests statt sichtbarer Tests als Beleg | R2-POL-08; R2-POL-13; R7-POL-08 | Hierarchie nur korrelativ |
| Recht | datierte Quellen mit Stichtag, sonst Enthaltung; Issue Spotting an unannotierten Sachverhalten | R3-POL-01; R3-POL-02 | deutsches Recht ohne Lernstudie |
| Klinik | gezielte Reflexion mit verzögerter Messung; Simulation ist keine Praxisautorität | R3-POL-08; R3-POL-10 | nur Ausbildungsfälle |
| Verkörperte Fertigkeiten | Drei-Spuren-Modell, externe menschliche Bewertung, Sicherheitsenthaltung | R4-POL-01; R4-POL-12; R4-POL-13 | Produkt kann Ausführung nicht messen |
| CAD | Konstruktionsabsicht mit Änderungstests prüfen | R4-POL-11 | nur konzeptuell begründet |
| Labor | experimentelle Praxis statt Inhaltswiederholung | R4-POL-08; R4-POL-09 | Labornutzen für Inhalte beobachtend nahe null |
| Statistik | simulationsbasierte Inferenz, Stichprobensimulation mit Vorhersage | R2-POL-16; R7-POL-07 | beobachtend, kleiner Effekt |
| Intensität | Schlafschutz über Wochen, Prüfungswochenregeln | R1-POL-B01; R1-POL-B02 | gilt nur im optionalen Modus Prüfungsvorbereitung |

### 2.4 Angeblich universelle Regeln und ihr Gegenbefund je Domäne

Die Charter verlangt für Beweis, Recht, Medizin, Debugging, CAD und Handwerk/Labor je mindestens einen falsifizierenden Fall. Diese Tabelle stellt die in den Berichten belegten Gegenbefunde zusammen. Das unabhängige Red-Team prüft sie separat (§12).

| Angeblich universelle Regel | Domäne | Gegenbefund oder Versagen | Fundstelle |
|---|---|---|---|
| „Jede Einheit endet mit Abruf“ (RP-R1) | Mathematik/Beweis | Testen nach Worked Examples ohne Zusatznutzen; Beweis- und Gutachtenketten lassen sich nicht sinnvoll atomisieren | R1 §1 Nr. 1; R1-POL-A01 (Enthaltung); R1-POL-A02 |
| „Richtiges Endergebnis belegt Können“ | Beweis | starke Endergebnis-Scores, aber höchstens 30 % vollständige Lösungen | R2 §1 Nr. 5; R2-POL-06 |
| dieselbe Regel | Debugging/Code | sichtbare Unit-Tests prüfen weder Generalisierung noch Begründung | R2 §4; R2-POL-13 |
| „Automatische Bewertung genügt“ | Recht | LLM-Benotung im Strafrecht QWK 0,599 | R3 §1 Nr. 10; R3-POL-11 |
| „Gutes Abschneiden in der Sitzung zeigt Lernen“ | Medizin | Reflexionsgruppe sofort schlechter, nach einer Woche besser | R3 §1 Nr. 8; R3-POL-08 |
| „Langsam und gründlich denken“ / Checklisten | Medizin | 45,0 % gegen 44,5 %; Cognitive Forcing ohne Effekt | R3 §1 Nr. 9 |
| „Verwechselbares mischen“ | Handwerk/Motorik | angewandte Studien 0,23 [−0,16; 0,62], nach Sensitivitätsanalyse −0,01; chirurgischer Transfer kehrte sich um | R4 §1 Nr. 2; R4-CR-1 |
| „Seltener Feedback = besseres Behalten“ | Motorik | RoBMA g = 0,021 | R4 §1 Nr. 3; R4-POL-04 |
| „Visualisierung/Immersion hilft“ | Beweis; Labor | e-Proofs ohne Vorteil, verzögert mehr Verlust; immersive VR: mehr Präsenz, weniger Lernen | R2 §1 Nr. 3; R4 §1 Nr. 7 |
| „Simulationserfolg ist Kompetenz“ | Klinik, Handwerk | Effekte schrumpfen zum realen Outcome; zu Haptik und Toleranz keine Studie | R4 §1 Nr. 1; R4 §9; R3-POL-10 |
| „Raumtraining verbessert CAD“ | CAD | Konstruktionsnutzen unbelegt, nur korrelativ | R4 §1 Nr. 9; R4-POL-10 |
| „Labore festigen Vorlesungsinhalte“ | Labor | mittlerer Labornutzen 0,24 % ± 0,67 % | R4 §1 Nr. 8; R4-POL-08 |
| „Tutorhilfe verbessert Lernen“ | Mathematik, Python | assistiert besser, unassistiert gleich oder schlechter | R5 §1 Nr. 1 und 8 |
| „Zwei Kalenderdaten belegen Verteilung“ | alle | 23:59 und 00:01 zählten als zwei Tage | CD-2; R5 §6 Nr. 3 |
| „Logiktraining überträgt sich auf Argumentieren“ | Philosophie | 40 h Konditionallogik ohne Effekt (Sekundärbeschreibung) | R3 §1 Nr. 6; R3-POL-06 |

### 2.5 Was die Hypothesen gemeinsam für das System bedeuten

Operationen × Prüfer × Evidenzzustände × Hilfe × Produkte (Designentscheidung, abgeleitet aus §2.2–2.4; Details in `r6/skill_ontology_v1.json`):

| Operation | Kompetenzbeleg im Produkt möglich? | Standardprüfer (R2-POL-14 und Ergänzungen) | Spur | im MCS |
|---|---|---|---|---|
| `recall_discrimination` | ja, deterministisch | Schlüssel für Auswahl und Kurzantwort, numerisch | A | ja (Bausteine, konstant gehalten) |
| `symbolic_procedure` | ja, je geprüftem Schritt | algebraisches Orakel/CAS, Ausdrucksäquivalenz, numerisch mit Einheit | A | **ja (manipuliert)** |
| `computational_construction` | ja, für Funktionsverhalten | verborgene bzw. Property-Tests, Zustandsorakel; sichtbare Tests nur Feedback | A | nein (Pyodide-Spike offen) |
| `formal_proof` | Verständnis und Validierung mit geschlossenen Items; Konstruktion nur durch Menschen oder in formaler Variante | Schlüssel, menschliche Rubrik/CJ, Beweisassistent | A | nein |
| `rule_based_contextual` | nur menschlich; Rechtsstand deterministisch prüfbar | menschliche Rubrik mit Alternativrouten, Quellen-/Fassungsprüfung | A | nein |
| `diagnostic_reasoning` | Referenzdiagnose geschlossen, Begründung menschlich; „Fallleistung in der Simulation“ | Schlüssel, menschliche Rubrik | A | nein |
| `empirical_experimental` | Planung und Interpretation teilweise; Durchführung nie im Produkt | Schlüssel, numerisch, Mensch; `external_assessment` | A/B | nein |
| `spatial_design` | Änderungstests (konzeptuell), menschliche Prüfung | Änderungstest, Mensch; `external_assessment` | A/B | nein |
| `embodied_psychomotor` | nie im Produkt | nur `external_assessment` | B (C außerhalb) | nein |
| `open_synthesis` | nur menschlich | Rubrik, Comparative Judgement | A | nein |
| `self_regulation` | keine Kompetenzaussage; eigenes Verhalten als Open Learner Model | keiner | – | nur Anzeige ohne Stunden (R1-POL-B05) |

Für **jede** Operation gilt derselbe Messvertrag (R1, R5-POL-04/05). Ein Zustand ändert sich nur durch ein Ereignis mit `assist_level = none`, gültiger Prüferquelle, an einem für diese Person neuen Item und mit exakter Zeit (§5). Hilfe ist für alle Operationen gleich typisiert (R5-POL-06). Produkte rendern dasselbe kanonische Objekt. Ist ein Container nicht anwendbar, wird er als `NOT_APPLICABLE` mit Fallback ausgewiesen (AD-0). Anki erhält nur abrufbare Bausteine (R1-POL-A01).

### 2.6 Was keine Architektur behaupten darf

1. Dass ein Produkt, eine Policy oder die Architektur Lernen verbessert: 116/116 `NOT_RUN`, CD-1.
2. Dass Benchmark-, Judge-, Präferenz- oder Rubrikwerte eines Modells ein Lernergebnis sind (R9-POL-05).
3. Dass Scheduler-Kennzahlen, FSRS-Parameter oder Kartenstatistik Kompetenz oder Lernen messen (R8-POL-12).
4. Dass Simulations-, VR-, Video- oder Fallleistung Praxiskompetenz belegt. Sie heißt „Fallleistung in der Simulation“ (R3-POL-10, R4-POL-01, R4-POL-07).
5. Eine Zertifizierung jeglicher Art: Spur C liegt vollständig außerhalb (R4-POL-01). Auch kein Zustand ist ein Zertifikat (R5-POL-01).
6. Eine Mastery-Wahrscheinlichkeit, einen Mastery-Prozentwert oder ein Label „gemeistert“ ohne verzögerten unassistierten Beleg (R5-POL-01, Produktvertrag).
7. Rechtsberatung, Behandlungs- oder Dosierungsempfehlungen (R3-POL-01, R3-POL-10, R1-POL-B12).
8. Dass der Leitplanken-Tutor nicht schadet; Nicht-Signifikanz ist keine Äquivalenz (CD-3, R5 §9).
9. Eine Fehlkonzeptdiagnose einer Person; Fehlerklassen sind Hypothesen (R5-POL-09).
10. Dass Parameter wie 20 h, 7 Tage, 2 Versuche oder 3 Hinweisstufen empirisch kalibriert sind (CD-4).
11. Kognitions-, Neuro- oder Wohlbefindenseffekte auf Leistung (R1-POL-B09, R1-POL-B11).
12. Dass unassistiert „ohne jede Hilfe“ heißt. Belegbar ist nur „ohne protokollierte Hilfe“ (R5 §6 Nr. 1, RT-27).
13. Dass die Architekturbewertung in diesem ADR eine Messung ist. Sie ist ein begründetes Designurteil.
14. Eine Gültigkeit für Erwachsene oder das Selbststudium, wo nur Schul- oder Laborevidenz vorliegt (RT-08).
15. Dass eine Anki-Bewertung (Again/Good) Korrektheit misst. Sie ist Selbstbewertung nach dem Aufdecken (RT-28).

## 3. Architecture Decision Record

### 3.1 Kontext und Frage

AD-2 ist offen: Welche Architektur trägt die von R1–R9 begründeten Operationen und kann bei unzureichender Evidenz zuverlässig abstinieren? Randbedingungen: Es gibt vier Produktcontainer (AD-0), Anki ist der einzige Scheduler (AD-1), Mastery ist scope-neutral mit optionalem Prüfungsmodus und ohne technische Umbenennungen vor einer getesteten Migration (AD-3). Das Budget für bezahlte Aufrufe ist 0. Der Entwurfsstapel #11–#19, #28, #37, #43 ist nicht gemergt (CD-6).

**Was die Engine heute ist** (Fakt, gelesen bei `5ad257d9`): ein Hybrid. Hand- bzw. agentisch erstellte Referenzstrecken (`em-track-v1`, drei Strecken) entsprechen A. Ein kanonischer Einheitenvertrag (`em-experience-v1`) enthält Kompetenzen mit Voraussetzungen, eigenem Vokabular aus 18 Operationen und 11 Wissensmodi; er ist ein leichter Graph im Sinne von B. Hinzu kommen eine deterministische Regelpolitik mit stabilen Regel-IDs (`em-decision-v1`, R0–RE) und eine deterministische Diagnose in fünf Stufen (`em-diagnosis-v1`, offene Antworten `UNVERIFIED`). Die Autorenrollen (`exam_mastery/prompts/`: architect, author, audit, domain_audit, pedagogy_audit …) entsprechen C, laufen aber zur Build-Zeit. Der Tutor ist eine Übergabe ohne Modellaufruf (`em-tutor-context-v1`). Maschinelle Bewertungsprüfer in Einheiten sind nur numerisch (`machine_check`), dazu exakte Polynomschritte (#17).

### 3.2 Entscheidungstreiber (gelten für jede Option)

| ID | Treiber | Fundstellen |
|---|---|---|
| D1 | einheitlicher Messvertrag über alle Operationen | R1 §5; R5-POL-04; R5-POL-05 |
| D2 | Prüferdeklaration je Aufgabe und Antwortteil; fehlender Prüfer ergibt nur ein Übungsprotokoll | R2-POL-14 |
| D3 | Spuren A/B/C, Simulationsgrenze, Sicherheitsenthaltung | R4-POL-01; R3-POL-10; R4-POL-13 |
| D4 | Anki einziger Scheduler, stabile Identität | R8-POL-01; R8-POL-02; AD-1; CD-8 |
| D5 | ein kanonisches Objekt, vier Container, `NOT_APPLICABLE` mit Fallback | AD-0; R8-POL-05 |
| D6 | deterministische, erklärbare Adaptation mit Regel-ID; keine Wahrscheinlichkeiten | R5-POL-01; R5-POL-02 |
| D7 | Enthaltung als Normalfall (fehlende Quelle, Fassung, Referenz, Grenze) | R5-POL-06; R3-POL-01; R9-POL-01 |
| D8 | offline, 0 bezahlte Aufrufe, reproduzierbar | Produktvertrag; `costs_and_limits` |
| D9 | Tutor schreibt nie in den Lernstand; kein Schlüssel für Nachweisitems | R9-POL-10; R9-POL-04; CD-7 |
| D10 | Kontextabhängigkeit (Operation, Phase, belegtes Vorwissen, Hilfestatus), aber parametrisiert und reversibel wegen niedriger Sicherheit | R1 §4; R1-POL-A03 |
| D11 | Rückverfolgbarkeit Policy → Regel → Version | Charter „traceable rule versions“ |
| D12 | keine technischen Umbenennungen ohne getestete Migration | AD-3 |

### 3.3 Optionen

- **S0 — Status quo:** Entwurfsstapel wie er ist, ohne Architekturentscheidung. Dies ist der Zustand, wenn der Owner nichts entscheidet.
- **A — Vorlagen + Domänenpakete:** generische Lehrvorlagen (Worked Example → Fading → selbstständig → Transfer; Abrufkarte; Fallschema; Labor) plus von Fachleuten erstellte Fachmodule mit Items, Fehlerbibliotheken und Prüfern je Paket.
- **B — Deklarativer Kompetenzgraph + evidenzkonditionierte Policy-Engine + verifizierte Domänenadapter:** vollständiger Kompetenz- und Operationsgraph mit Voraussetzungen; generische Regel-Engine, die Policies aus dem Index als deklarative Regeln über Kontext und Evidenz auswertet; zentrale Prüferadapter.
- **C — Agentisch komponierte Erfahrungen + unabhängige Auditoren:** Agenten erzeugen zur Laufzeit je Thema Erklärung, Aufgaben, Visualisierung und Tutorhilfe mit eingeschränkter Werkzeugausführung; weitere Agenten auditieren.
- **H-AB — Evidenzkern mit Vorlagen (vorgeschlagen):** B nur als schmaler Kern (typisierter Vertrag, Beobachtungsvertrag, Prüferadapter, deterministische Zustandsableitung, Entscheidungsfunktionen mit Regel-IDs ohne generische Regelsprache), darauf Vorlagen je Operationsfamilie und Domänenpakete als Daten aus A. Agenten nur zur Build-Zeit als Autorenhilfe hinter Gates und menschlicher Prüfung.
- **H-BC — Kern + Laufzeitkomposition:** H-AB-Kern, aber Erfahrungen werden zur Laufzeit agentisch erzeugt und gegen den Kern validiert.

### 3.4 Bewertung (ordinal, Designurteil; Fundstellen und Unbekannte je Zelle in `r6/adr.json`)

Skala: **günstig**, **gemischt**, **ungünstig** relativ zu den Treibern D1–D12. Es gibt keine Punktzahl und keine Aggregation. Wichtiger als die Spalte ist die Begründung.

| Kriterium | S0 | A | B | C | **H-AB** | H-BC |
|---|---|---|---|---|---|---|
| Lernrelevanz (Passung zu §2, nicht Wirkung) | gemischt: Regeln teils passend, Taxonomie ≠ Charter, Spec-Zahlen als Regeln (CD-4) | gemischt: Sequenzen ja, Messvertrag je Vorlage dupliziert | gemischt: Struktur passt, aber 77 von 116 Policies `low`/`very_low` würden als Engine-Regeln Scheinpräzision erzeugen | ungünstig: generierte Hinweise fielen zu 32 % durch die QA, Modellbewerter überbewerten, Halluzinationen im Recht | gemischt wie alle: keine Lernevidenz; Vorteil nur bei Messintegrität (RT-36) | gemischt: Kern passt, Laufzeitinhalt ungeprüft |
| Prüferabdeckung | ungünstig: nur numerisch + Polynom, keine Deklaration | gemischt: je Paket, nicht durchgesetzt | günstig: zentral | ungünstig: Auditoren sind `agent_judgement` | günstig für deterministische Operationen, ehrlich „Mensch/keiner“ sonst | gemischt: Laufzeitartefakte brauchen je eigene Prüfer |
| Technische Komplexität | gemischt: vorhanden, aber groß, Python/JS doppelt | günstig | ungünstig: Regelsprache, Graphwerkzeuge | ungünstig: Agentenlaufzeit, Sandbox | gemischt bis günstig: Schemas + Registry, keine Regelsprache | ungünstig |
| Betreibbarkeit (ein Owner, 0 Budget) | gemischt: Autorenläufe brauchen Modellzugang | günstig | gemischt | ungünstig: Budget 0, nicht deterministisch | günstig | ungünstig |
| Offline | günstig | günstig | günstig | ungünstig für Komposition | günstig | ungünstig |
| Sicherheit | gemischt: CD-7 nur im Entwurf behoben | günstig | günstig | ungünstig: Prompt-Injection aus Quelltext, Werkzeugausführung | günstig | ungünstig |
| Autorenaufwand | ungünstig: Golden References sitzungskuratiert (CD-5), Produkte abgelehnt | ungünstig: Expertenarbeit je Paket | ungünstig: Graph je Kurs | gemischt: geringe Erzeugungskosten, hohe Prüfkosten | gemischt: Vorlagen senken Strukturkosten, Inhalt bleibt Fach- und Prüfarbeit | gemischt |
| Wartbarkeit | gemischt: Regel-IDs stabil, Stapeldrift (CD-6) | gemischt: Regeländerung in vielen Vorlagen | gemischt: gute Spur, aber Interpreter selbst ist Last | ungünstig: Modelldrift, nicht reproduzierbar | gemischt bis günstig: Policy-IDs an Regeln, eine Parameterdatei | ungünstig |
| Migrationskosten vom Entwurfsstapel | günstig (keine), trägt aber alle Defekte | gemischt: Strecken und Labs ähneln Paketen | ungünstig: Regeln aus Code in Regelsprache, JS-Spiegel portieren | gemischt: Rollen existieren, Laufzeit wäre neu | günstig: erweitert vorhandene Verträge | ungünstig |

**Auswahlbasis (nach RT-36):** Keine Option lässt sich mit Lernwirksamkeit begründen. Der Vorschlag stützt sich auf Prüferabdeckung, Sicherheit, Messintegrität, Betreibbarkeit, Offline-Fähigkeit und Migrationskosten. Die Zeile Lernrelevanz bleibt stehen, weil die Charter sie verlangt. Sie entscheidet nichts.

**Größte Unbekannte (für alle Optionen):** (U1) ob irgendeine Sequenzierung messbar besser ist als eine statische Folge (MCS prüft genau das); (U2) Autorenkosten je Kompetenz bei akzeptabler Qualität, es gibt keine Messung; (U3) Reliabilität menschlicher Bewertung für Recht, Beweis und offene Synthese in diesem Produkt; (U4) wie viele Kontextbedingungen tatsächlich nötig sind; davon hängt ab, ob eine Regelsprache (B) je gerechtfertigt wird; (U5) Größe des Python/JS-Paritätsaufwands; (U6) Verhalten der Anki-Mobilclients.

### 3.5 Vorgeschlagene Entscheidung (Status: PROPOSED)

**H-AB „Evidenzkern mit Vorlagen“.** Bestandteile, jeweils mit konkreter Notwendigkeit (Charter: „jede zusätzliche Schicht braucht eine konkrete Notwendigkeit“):

| Baustein | Inhalt | Notwendig wegen | Heute vorhanden als |
|---|---|---|---|
| K1 Semantischer Vertrag | Kompetenz mit Charter-Operation, Kompetenztyp, Voraussetzungen; Item mit Rolle (Übung/Nachweis), Prüferdeklaration und geprüften Teilen, Alternativrouten und Bewertungskanal (product/human/none, RT-04), Transferdimension (RT-29), Hilfepolitik, Spur, Quelle mit Stichtag, Grenz- und Sicherheitsflags; Containerzuordnung mit `NOT_APPLICABLE` | D2, D3, D5, D7 | `em-experience-v1` (Kompetenzen, Voraussetzungen, Rollen, `machine_check`) |
| K2 Evidenzkern | Ereignisse nach `observation_contract_v1`; reine Funktion Ereignisse → Zustände (R5-POL-01-Vokabular) je Kompetenz **und Kompetenztyp** (RT-10); Hilfe auf KC-Ebene mit Zeitfenster, Zeitplausibilität (RT-26); Register verbotener Behauptungen | D1, D6, D9 | `policy.kc_status`, `experience_evidence` (Typen attempt/hint/solution_reveal) |
| K3 Prüferadapter | Prüferklassen mit „prüft / prüft nicht / Kompetenzbeleg?“; Stichproben aus dem deklarierten Definitionsbereich, exakte Prüfung, wo möglich (RT-11); Modellurteil nur `FEEDBACK_UNVERIFIED` | D2, X3, X4 | `diagnose.py` L1–L5, `expr.py` (randomisierte Identität), `experience_proof_checks.py` |
| K4 Entscheidungsfunktionen | `em-decision-v1` liest Operation, Rolle und Hilfestatus aus K1/K2; jede Regel nennt die Policy-IDs, die sie umsetzt; Parameter in einer Datei als `provisional_product_parameter`; keine generische Regelsprache; **nur beobachtbare Prädikate**, kein automatisches Überspringen nach einem Item, kein Novizen-Klassifikator als Standard (Beispiel zuerst, Vorhersage und Erkundung als Angebot; RT-02, RT-19, RT-34) | D6, D10, D11 | `policy.decide` (R0–RE) |
| K5 Vorlagen je Operationsfamilie | Sequenzen als Daten, z. B. Verfahren (Worked Example → Selbsterklärung → Fading → selbstständig → Transfer → verzögerte Prüfaufgabe), Abruf (Erklärung → Abruf mit Korrektur → Anki), Fall (unannotiertes Issue Spotting → Struktur → kontrafaktische Variation), Beweis (Verständnis → Validierung → Konstruktion mit menschlicher Prüfung) | D5, D10, X5 | `labs/pedagogy.py`, Strecken in `tracks.py` |
| K6 Domänenpakete als Daten | Items, Fehlerbibliotheken, Prüferkonfiguration, Rechtsstand, Grenztexte; Erstellung mit Agentenhilfe nur zur Build-Zeit, durch deterministische Gates und menschliche Prüfung; Build-Zeit-Audits ersetzen nie G3/G4 (RT-35) | §2.3, CD-5 | Autorenrollen, Strecken |

**Welchen Fehler welcher Baustein abfängt (RT-36):** K1/K2 fangen den Fehler von A ab, bei dem die Prüferpflicht je Vorlage dupliziert und nicht durchgesetzt wird (RT-33). K4 ohne Regelsprache und nur mit beobachtbaren Prädikaten vermeidet die Scheinpräzision von B (RT-34). K3 und G3/G4 ersetzen die korrelierten Auditor-Blindstellen von C (RT-35). K2 schließt die Zähllücke von S0 (RT-26).

**Globale Rangfolge bei Policy-Konflikten (RT-25, abgeleitet aus der Konfliktregel des Produktvertrags; mit OD-01 zu bestätigen):** Wahrheit, Sicherheit und Datensicherheit vor Messintegrität, vor ausdrücklichem Wunsch der lernenden Person, vor didaktischem Standard, vor Komfort und Automatisierung. Jeder bekannte Paarkonflikt zwischen den Konfliktregeln der Workstreams erhält in G2 einen Testfall.

**Ausdrücklich nicht Teil von H-AB:** generische Policy-Engine oder Regelsprache, vollständiger Kompetenzgraph über Kurse, Knowledge Tracing oder Wahrscheinlichkeiten (R5-POL-02 nur Schattenbetrieb), eigener Scheduler, Laufzeitagent, eingebettete Fremdsysteme (R9-POL-07), AnkiConnect (R8-POL-14), Lernenden-Dashboards über das Open Learner Model hinaus (R5-POL-11). Der Tutor bleibt ein portabler Vertrag außerhalb des Kerns (R9-POL-03); seine Übergabe zählt als Hilfe.

### 3.6 Verworfene Optionen und Wiedervorlage

| Option | Verworfen, weil | Wiedervorlage, falls (falsifizierbar) |
|---|---|---|
| S0 | trägt CD-4, CD-5, CD-6 und CD-8; keine Prüferdeklaration; Engine-Operationen ≠ Charter-Taxonomie; erlaubt keine ehrliche Lernbehauptung | – (Ausgangspunkt der Migration) |
| A | Messvertrag und Prüferpflicht würden je Vorlage dupliziert und nicht zentral durchgesetzt; der R2-POL-14-Falsifikator (deklariert ≠ geprüft) bliebe ungeschützt; Vorlagen frieren universell formulierte Engine-Regeln ein (RT-33) | nie allein; H-AB enthält A. Vor Ausweitung der Vorlagen über das MCS hinaus: Experiment RT-33 (2 Vorlagen × 3 Domänen; Anteil der `NOT_APPLICABLE`- oder überschriebenen Felder; blinde menschliche Bewertung) |
| B (voll) | Regelsprache und vollständiger Graph sind eine zusätzliche Schicht ohne konkrete Notwendigkeit: 0 `high`, 14 `moderate` von 116, alle `NOT_RUN`; Voraussetzungsgraphen wurden zurückgestellt (R9 §2, Math Academy) | wenn nach G6 evaluierte Policies Kontextbedingungen verlangen, die K4 nur durch Code-Duplizierung ausdrücken kann, oder wenn ein Review zeigt, dass die Regelzahl in K4 nicht mehr prüfbar ist; zusätzlich Experiment RT-34 (20 Policies als Regeln auf 30 synthetischen Spuren): Entscheidungen dürfen nicht überwiegend an unbeobachtbaren Prädikaten hängen |
| C | Budget 0, nicht offline, nicht reproduzierbar; Auditoren liefern nur `agent_judgement` (R2-POL-05, R9-POL-05); Prompt-Injection aus nicht vertrauenswürdigem Quelltext; historische Produkte `HUMAN_REJECTED` | wenn eine vorab registrierte Evaluation zeigt, dass agentisch komponierte Strecken bei verzögertem unassistiertem Transfer nicht schlechter als autorisierte Vorlagen sind, menschlich geprüfte Inhaltsqualität nicht abgelehnt wird und ein Budget freigegeben ist; zusätzlich Experiment RT-35 mit gepflanzten Defekten (Auditor-Recall je Defektklasse gegen Mensch, GUID-Churn), Auditoren aus anderer Modellfamilie und Subgruppenanalyse für Alternativrouten (RT-30) |
| H-BC | erbt die Laufzeitnachteile von C; Validierung gegen den Kern ist auch zur Build-Zeit möglich (H-AB) | wie C |

### 3.7 Konsequenzen und Risiken

**Positiv (erwartet, nicht belegt):** Ein Messvertrag gilt für alle Container. Abstention wird testbar. Die Migration geschieht schrittweise auf vorhandenen Verträgen. Policies bleiben bis zur Regel nachvollziehbar.

**Negativ und Risiken:** (R-1) H-AB verschiebt das Hauptproblem, die Inhaltsqualität, auf Autoren und Prüfende. Ohne Budget für unabhängige Autorinnen, Autoren und Bewertende gibt es außerhalb deterministischer Operationen keine Kompetenzbelege. (R-2) Die Python/JS-Parität bleibt eine dauerhafte Fehlerquelle. (R-3) Wenige deterministisch prüfbare Operationen könnten das Produkt faktisch auf MINT-Rechenaufgaben verengen; das widerspricht dem Scope von AD-3, wenn es nicht als Phasenfolge ausgewiesen wird. (R-4) Wer K4-Regeln mit Policy-IDs etikettiert, kann Umsetzungsnähe vortäuschen; die Etikettierung ist kein Beleg (Test darf nur Existenz prüfen). (R-5) Nähe zum Status quo kann als Bestätigung früherer Arbeit gelesen werden. Die Ablehnung der Produkte bleibt bestehen.

### 3.8 Migrationspfad vom Entwurfsstapel (erst nach G0 und G1, außer M0)

| Schritt | Inhalt | Prüfbar durch |
|---|---|---|
| M0 (architekturunabhängig, vor G0 möglich) | CD-8-Fix in eigenem Entwurfs-PR, im Update-Bericht Änderungsklassen redaktionell/substanziell nach OD-31 (RT-12, RT-21); Hygiene in `anki_bridge.py` nach Owner-Entscheidung | Importtests in Wegwerfsammlung (R8-POL-08) |
| M1 | Charter-`operation` und `competence_type` neben dem bisherigen Vokabular in `em-experience-v1` (rückwärtskompatibel, Abbildung in `skill_ontology_v1.json`); Altbestand erzeugt Warnungen statt Fehler; keine Umbenennung (AD-3) | Validator-Tests mit alten und neuen Einheiten |
| M2 | Ereignisse um `assist_level`, `source`, `time_quality`, `item_role`, `item_variant`, `tutor_handoff`, `hint_bottom_out` erweitern; `kc_status` auf das R5-Vokabular abbilden (`RETAINED_ON_LATER_DAY` → `RETAINED_AFTER_ELAPSED_TIME` nur als Anzeige- oder getestete Datenmigration; `INSUFFICIENT_EVIDENCE` neu) | G2-Fixture-Suite, Python/JS-Parität |
| M3 | Prüferdeklaration je Item (`verifier.class`, `checks`, `unchecked`); `machine_check` wird eine Klasse; Item ohne Prüfer = nur Übung | G3-Audit |
| M4 | Vorlagen nur für die MCS-Familien (Verfahren, Abruf). Vorher werden die universell formulierten Engine-Regeln RP-R1, WE-R1/R2, MC-R1, PR-R1 und AS-R1 über OD-27 operationsgebunden (RT-01 bis RT-04, RT-19) | Vorlagen-Validator; `NOT_APPLICABLE`-Pfad je Regel getestet |
| M5 | MCS-Inhalt in einem Thema, menschliche Prüfung | G4 |
| M6 | `evaluation.py` um innerhalb-Lernende-Randomisierung je Kompetenz und Präregistrierung erweitern; unabhängige Items | G5 |

## 4. Skill-Ontologie v1 (Übersicht; maßgeblich ist `r6/skill_ontology_v1.json`)

- **Operationen:** genau die elf Charter-Operationen (gleiche Menge wie in `tests/test_r1_learning_policies.py`). Sie sind Hypothesen, keine endgültige Ontologie.
- **Kompetenztypen** (quer zu Operationen, aus R2 §3, R3, R4): `recall`, `recognize_discriminate`, `comprehend_trace`, `validate_debug`, `construct`, `select_justify_method`, `check_conditions_counterexample`, `issue_spot`, `diagnose_differential`, `argue_critique`, `plan_experiment`, `interpret_data`, `execute_physical` (nur Spur B), `monitor_calibrate`. Jeder Typ nennt die zulässigen Operationen.
- **Wissensmodi:** das Engine-Vokabular (`formal_reasoning` … `practical`) bleibt als Darstellungsattribut erhalten; es steuert keine Evidenz.
- **Evidenzarten:** `deterministic_check`, `human_rubric`, `comparative_judgement`, `external_assessment` (Spur B), `agent_judgement` (nie Kompetenz), `self_report` (nie), `practice_log` (nie), `anki_review` (Selbstbewertung, nie; RT-28), `scheduler_statistic` (nie), `benchmark_score` (nie), `exposure` (nie).
- **Zustandsschlüssel:** (Kompetenz, Kompetenztyp). Eine richtige Prämissenauswahl belegt Validierung, nicht Konstruktion (RT-10).
- **Itemfelder:** `alternative_routes`, `evidence_channel`, `verifier`, `transfer_dimension` (Pflicht für Nachweisrollen), `low_entropy_answer` (binär, MC, Einzeldiagnose: zählt nicht allein; RT-13, RT-29), `time_estimate` (Schätzung).
- **Hilfestufen:** `none`, `hint_n`, `hint_bottom_out`, `solution_seen`, `tutor`, `unknown`. Fehlender Hilfestatus zählt als assistiert. `hint_before_attempt` ist ein Flag.
- **Beobachtbare Zustände (R5-POL-01):** `NOT_ASSESSED`, `ASSISTED`, `INDEPENDENT_PASS`, `RETEST_DUE`, `RETAINED_AFTER_ELAPSED_TIME`, `INSUFFICIENT_EVIDENCE`. Die heutige Engine nutzt `RETAINED_ON_LATER_DAY` und `INDEPENDENT_PARTIAL`; die Abbildung steht im JSON, `INDEPENDENT_PARTIAL` ist eine offene Vokabularfrage.
- **Prüferklassen (R2-POL-14, §12.3, ergänzt um R3/R4/R9):** algebraisches Orakel/CAS, numerische Einzelwertprüfung, Beweisassistent, sichtbare Unit-Tests, verborgene/Property-Tests, menschliche Rubrik, Comparative Judgement, LLM-Bewertung, keiner, Zustandsorakel, Laufzeit-Zusicherung, Operationszähler, Prinzipschlüssel, Quellen-/Fassungsprüfung (R3-POL-01, R9-POL-02), CAD-Änderungstest (R4-POL-11), externe menschliche Bewertung (R4-POL-12).
- **Spuren und Grenze:** A Wissen (im Produkt), B reale Ausführung (nur `external_assessment`), C Zertifizierung und Sicherheit (außerhalb). Simulationsergebnisse heißen „Fallleistung in der Simulation“. Bei gefährlichen Verfahren gilt Enthaltung. Rechtsaussagen nur mit Stichtag. Kompetenzen mit physischem Anteil zeigen „Wissen geprüft – Ausführung nicht beobachtet“ ohne Fortschrittsbalken (RT-17). Vorhersage-Gates gibt es nur in Spur-A-Umgebungen mit engine-eigener Ausführung, nie als Aufforderung zum Ausprobieren in realer Praxis (RT-23).
- **Phasen und Modi:** `acquisition`, `practice`, `consolidation` sowie der optionale Modus `assessment_preparation`. Er ersetzt die R1-Phase `final_exam_week`; die Abbildung bleibt erhalten, damit Policy-Kontexte unverändert lesbar sind (AD-3).

**Offene Ontologiefrage (Konflikt zwischen Workstreams):** R5-POL-04 lässt nur `none` + `deterministic` für Zustände zu. R2-POL-14 und R3-POL-11 nennen die menschliche Rubrik als Kompetenzbeleg. Vorschlag: Menschlich bewertete Evidenz zählt, wenn Rubrikversion und bewertende Person protokolliert sind. Für eine Lernbehauptung muss zusätzlich die Übereinstimmung zwischen Bewertenden berichtet werden. Zustände daraus tragen die Kennzeichnung „menschlich bewertet“. Im MCS wird sie nicht genutzt.

## 5. Beobachtungs- und Bewertungsvertrag v1 (Übersicht; maßgeblich ist `r6/observation_contract_v1.json`)

- **Wer:** `learner_ref` (lokales Pseudonym, nie Name), `actor` (learner, engine, external_tutor, human_assessor), bei externer Bewertung Rolle und Qualifikation der Person.
- **Was:** Ereignistyp (`attempt`, `hint_request`, `hint_shown`, `solution_reveal`, `tutor_handoff`, `worked_example_view`, `prediction`, `confidence_report`, `self_assessment`, `practice_log`, `external_assessment`, `external_safety_briefing`, `item_exposure`); Item mit ID, Variante, Revision, Kompetenz, Operation, Kompetenztyp, Rolle; Ergebnis (`correct`/`incorrect`/`partial`/`unverified`/`invalid`), Fehlerkategorie nur als Hypothese.
- **Wann:** zeitzonenbewusster Zeitstempel. `time_quality` ∈ {`exact`, `date_only`, `unverified`, `unknown`}. Verstrichene Zeit ist die Differenz zweier exakter Zeitpunkte, nie ein Kalenderdatum (CD-2). Zeitstempel nach dem Erfassungszeitpunkt oder aus Importen gelten als `unverified` (RT-26). Bei `date_only`, `unverified` oder `unknown` werden Behaltens- und Leseregeln nicht ausgewertet (R5-POL-08). Die Anzeige lautet „erneut gelöst nach ≥ 20 h ohne protokollierte Hilfe“, nicht „behalten“.
- **Hilfe und Quelle:** `assist_level` und `source` ∈ {`deterministic`, `human_rubric`, `external_assessment`, `agent_judgement`, `self_report`}.
- **Itemrolle:** `practice` oder `evidence`. Nachweisrollen (`similar`, `transfer`, `retest`, `mock`, `evaluation`) erhalten nie einen Schlüssel im Tutor-Brief (CD-7). Ein mit Lösung gesehenes Item gilt für diese Person danach nur noch als Übung. Evaluationsitems liegen nie im Übungspool.
- **Provenienz:** Engine-Version, Regel-ID der Entscheidung, Policy-IDs, Inhaltsrevision, Prüferklasse und -version, Quellen mit Stichtag, Spur, Simulationsflag.
- **Datenschutz:** lokal gespeichert, standardmäßig kein Antworttext (wie `experience_evidence`), Subgruppenmerkmale nur nach Opt-in (R5-POL-07).
- **Ableitung:** Schlüssel ist (Kompetenz, Kompetenztyp). Hilfe im selben KC innerhalb eines Zeitfensters (vorläufiger Parameter, Wert in der Präregistrierung) macht folgende Versuche assistiert (RT-26). Items mit geringer Ergebnisvielfalt zählen nicht allein; ein Retest muss kontrafaktisch variiert sein (RT-13). Nachweisitems deklarieren ihre Transferdimension (RT-29). Ein Zustand ändert sich nur durch `attempt` mit `assist_level = none`, `source` ∈ {`deterministic`, `human_rubric` mit Kennzeichnung}, an einem für diese Person neuen Item (nie mit Lösung oder Schlüssel gesehen) und mit `time_quality = exact`. Nachweisrollen halten ein Item neu, weil ihr Schlüssel nie herausgegeben wird. Übungsitems verlieren diese Eigenschaft, sobald die Lösung sichtbar war. Für die unabhängige Evaluation zählen nur Items der Rolle `evaluation`. Spur B ändert sich nur durch `external_assessment`. Alles andere wird protokolliert, ändert aber keinen Zustand.
- **Bewertungsvertrag für Lernbehauptungen:** R5-POL-05 vollständig (vorab registrierte Hypothese und Mindestdifferenz, verdeckte Zuteilung, gleiche Zeit in der Kontrolle, verzögerter unassistierter Test mit neuen, nicht vom Produktteam abgeleiteten Items, Subgruppen und Attrition). In-Produkt-Zustände sind nur proximale Indikatoren; ein Evaluationsendpunkt wird nie aus `kc_status` abgeleitet (RT-26). **Entscheidungsstufe (RT-32, OD-29):** Für Produktentscheidungen im Ein-Personen-Betrieb können schwächere Designs zugelassen werden, etwa Itemrandomisierung innerhalb einer Person oder n-of-1 mit vorab festgelegter Analyse. Ersatzgrößen sind als Entscheidungsgrundlage ausgeschlossen: Anki-Retention, Nutzungszeit, Agenten-Audits, Golden References, Zufriedenheit. Bis zur Owner-Entscheidung gilt nur die Behauptungsstufe.

## 6. Minimum Credible System (MCS)

**Ziel:** die kleinste baubare Scheibe, die **eine** ehrliche, unabhängig messbare Lernbehauptung prüfen kann. Eine Bestätigung ist nicht das Ziel.

**Zu prüfende Behauptung (Hypothese, nicht behauptet):** Für die vorab benannte Lernendengruppe (Default: der Owner als einzelne Person, OD-21) führt die adaptive Strecke des interaktiven Produkts zu höherer unassistierter Leistung an neuen, unabhängig verfassten isomorphen und Transferaufgaben nach mindestens 7 Tagen echter verstrichener Zeit, und zwar um mindestens die vorab registrierte Mindestdifferenz. Die adaptive Strecke umfasst Evidenzkern, hilfeabhängiges Fading, eine Parallelaufgabe ohne Hilfe und eine verzögerte Prüfaufgabe. Verglichen wird mit einer statischen Workbook-Sequenz mit denselben Worked Examples und Aufgaben bei gleicher Zeit. **Sekundär:** Prädiktive Validität des Zustands `RETAINED_AFTER_ELAPSED_TIME` gegenüber `INDEPENDENT_PASS` (Falsifikator von R5-POL-01).

**Design:** Innerhalb einer Person werden Kompetenzen zufällig einer Bedingung zugeteilt (KC-Ebene, gegenbalanciert, Seed vor der ersten Exposition committet). Kompetenzen müssen inhaltlich getrennt sein, um Übertragung zwischen den Bedingungen zu begrenzen. Kompetenzzahl und Mindestdifferenz legt die Präregistrierung fest, nicht dieses Dokument. Die Bedingung ist für die lernende Person nicht verblindbar; das wird offengelegt. Bei Gruppen gilt R5-POL-05 mit Cluster- bzw. Personenrandomisierung.

**Umfang:**
- *Domäne:* `symbolic_procedure` mit abrufbaren Bausteinen aus `recall_discrimination` in **einem** quellenfreien quantitativen Thema. Kandidaten sind die vorhandenen synthetischen Strecken (Backpropagation-Gradient, Liquiditätsplanung) mit vorhandenen deterministischen Prüfern (numerisch mit Einheit, Ausdrucksäquivalenz, exakte Polynomschritte). Die Auswahl trifft der Owner (OD-22).
- *Produkte:* Interaktiv wird manipuliert. Das Workbook ist Kontrollbedingung und druckbare Fassung für beide Arme. Anki bleibt konstant: dasselbe Deck für beide Arme, nur Bausteine, Planung nicht manipuliert. Das Lehrbuch bleibt konstant: dieselbe Erklärung. Alle vier Container existieren, geprüft wird nur einer.
- *Kern:* K1–K4 für zwei Operationsfamilien, K5 für Verfahren und Abruf, K6 für ein Thema.

**Bewusst ausgeschlossen:** Beweiskonstruktion, Recht, Klinik, offene Synthese, verkörperte Fertigkeiten, CAD, Labor, Code-Werkbank; LLM-Tutor in den Armen (Nutzung während der Studie wird protokolliert und macht betroffene Versuche assistiert; empfohlen ist Verzicht); Knowledge Tracing; Obsidian-Ansicht; AnkiConnect; Mobilclients; Markenmigration Phase C; Kursmaterial-Ingestion; Dashboards; jede Zertifizierung.

**Messdetails nach Red-Team:** Endpunkt ist allein der unabhängige verzögerte Test, nie `kc_status` (RT-26). Test- und Nachweisitems deklarieren ihre Transferdimension und unterscheiden sich im Lösungsweg oder Ergebnis (RT-29). Der Ausdrucksprüfer wird vor G3 korrigiert: Stichproben aus dem Definitionsbereich, exakte Prüfung (RT-11). Die Hinweisleiter gilt nur für `symbolic_procedure`, die Stufenzahl ist vorläufig (RT-07). Population: Erwachsene; Schulevidenz wird nicht als Beleg übertragen (RT-08). Im Ein-Personen-Fall gilt die Entscheidungsstufe nach OD-29 (RT-32).

**Unabhängigkeit der Messung:** Testitems verfasst eine Person, die nicht an der Produkterstellung beteiligt ist (OD-13b). Die Parallelform-Äquivalenz wird in einem Pilot geprüft. Die Bewertung ist deterministisch. Die Zuteilung ist vorab committet. Ohne unabhängige Itemautorin oder unabhängigen Itemautor endet das MCS bei G4 mit dem Status „Lernwirkung nicht gemessen“.

**Zulässige Aussagen nach dem Lauf:** nur die vorab formulierte, auf diese Person bzw. Gruppe, diese Kompetenzen und diese Verzögerung beschränkte Aussage oder „nicht gezeigt“. Keine Übertragung auf andere Operationen oder Domänen.

## 7. Phasen-Gates

| Gate | Bestehenskriterium (falsifizierbar) | Scheitert, wenn | blockierende Owner-Entscheidungen |
|---|---|---|---|
| G0 Architektur | Der Owner trägt eine Entscheidung zu diesem ADR (angenommen, geändert oder verworfen) mit Datum in den Programmstatus ein. Agenten setzen nie `ACCEPTED`. | Status ändert sich ohne Owner-Eintrag | OD-01 |
| G1 Integrationsbasis (P4) | (a) Stapel bis #43 in owner-bestimmter Reihenfolge gemergt; (b) CI-äquivalente Suite auf dem Ergebnis grün, aus eingefrorener Kopie; (c) CD-8: Reexport unveränderter Inhalte ändert in einer Wegwerfsammlung 0 Notizen und 0 Notiztypen; Änderung des Anzeigenamens ändert keine Notiztyp-ID; (d) Hygieneprüfung findet keine Kursunterlagen-Bezeichner im öffentlichen Baum | eine der Prüfungen schlägt fehl | OD-02, OD-03, OD-04, OD-20, OD-31 |
| G2 Vertragskern | Adversariale Fixture-Suite mit 0 Verstößen in Python und JS: zwei Erfolge 2 min über Mitternacht → kein Behalten; dasselbe Item wiederholt → kein neuer Beleg; Tutor-Übergabe → assistiert; Bottom-out-Hinweis → assistiert; `agent_judgement` → keine Zustandsänderung; fehlender Hilfestatus → assistiert; `date_only` → kein Behalten; mit Lösung gesehenes Item → nicht neu; Simulationsergebnis → keine Spur-B-Änderung; Schwesterlösung im selben KC → assistiert; Zukunftszeitstempel oder Import → kein Behalten; binäre Antwort umformuliert → kein alleiniger Beleg; Prämissenauswahl → kein Konstruktionszustand (FX-13 bis FX-16, RT-10, RT-13, RT-26); je bekanntem Paarkonflikt der Rangfolge ein Testfall (RT-25) | ein einziger Verstoß | OD-01, OD-10, OD-12, OD-25, OD-27, OD-28, OD-30 |
| G3 Prüferaudit | Für jede im MCS genutzte Prüferklasse besteht ein Known-Answer-Satz mit adversarialen Antworten (äquivalente Formen, Einheitenfehler, richtiges Ergebnis aus falschem Teilschritt, wo prüfbar, definitionsbereichssensitive Fälle wie √(x²) gegen x und negative Werte; RT-11). Eine menschliche Stichprobe (Umfang vorab festgelegt) findet kein Item, dessen deklarierte geprüfte Teile von den tatsächlich geprüften abweichen | eine Abweichung (dann technische Erzwingung vor G4) | OD-01, OD-23 |
| G4 Menschliche Inhaltsprüfung | Eine benannte Person prüft die MCS-Strecke und stellt fest: nicht abgelehnt, kein offenes K.-o.-Kriterium nach Produktvertrag, mathematische Stichprobe korrekt | `HUMAN_REJECTED` oder offenes K.-o.-Kriterium | OD-01, OD-22, OD-23 |
| G5 Präregistrierung | Endpunkt ist der unabhängige verzögerte Test, nicht `kc_status` (RT-26). Protokoll mit Endpunkt, Mindestdifferenz, Verzögerung, Zuteilungsseed, Analyse- und Fehlwerteplan, Abbruchregeln, Einwilligung/Datenschutz und Ergebnissen des Äquivalenzpilots ist vor der ersten Exposition mit Zeitstempel committet; unabhängige Itemautorschaft bestätigt | Änderung nach Exposition (konfirmatorische Aussage entfällt) | OD-01, OD-13b, OD-21, OD-22, OD-25, OD-29 |
| G6 Durchführung und Bericht | Bericht nach Plan, Nullbefunde eingeschlossen; Formulierung wörtlich aus dem Protokoll. Entscheidungsregel: Ohne Unterschied ≥ Mindestdifferenz wird K4/K5 nicht ausgebaut, der Evidenzkern bleibt | Bericht weicht vom Plan ab oder fehlt | OD-01, OD-13b, OD-13c, OD-29 |
| G7 Zweite Operationsfamilie | G6-Bericht liegt vor; G3 für neue Prüferklassen bestanden; für menschlich bewertete Operationen Budget und berichtete Übereinstimmung zwischen Bewertenden im Pilot; für Code bestandener Pyodide-Spike (Offline-Laden, Abbruch von Endlosschleifen, Größe), Belege nur aus engine-ausgeführten Läufen mit property-/mutationsbasierten verborgenen Tests (RT-15); für Klinik deklarierte Prävalenz der Fallbank und fachlich geprüfte Referenzdiagnosen (RT-14); für CAD verdeckte, randomisierte Änderungstests oder `NOT_APPLICABLE` (RT-16); für Hochrisikodomänen Messgröße „Sitzungsende nach Enthaltung“ und abgestufte Rückfallebene (RT-24); Vorlagen-Experiment RT-33 durchgeführt | fehlende Voraussetzung | OD-01, OD-13a, OD-13c, OD-18, OD-24 |
| G-BRAND Phase C | erst nach G1(c); Migration in Wegwerfprofilen getestet; Owner-Freigabe | Umbenennung vor eingefrorenen IDs | OD-03, OD-19 |

## 8. OWNER_DECISIONS_REQUIRED

Konsolidiert aus R3–R9, Programmstatus und dieser Synthese. „Default“ heißt: Das gilt, solange der Owner nichts entscheidet. Agenten setzen den Default nicht als Entscheidung um, wenn er Code oder Daten ändern würde.

| ID | Entscheidung | Quelle | blockiert | Default bei Untätigkeit |
|---|---|---|---|---|
| OD-01 | ADR-Vorschlag H-AB annehmen, ändern oder verwerfen | R6 | G0, G2–G7 | bleibt `PROPOSED`; nur architekturunabhängige Arbeit (M0) |
| OD-02 | Merge-Reihenfolge und Merge des Entwurfsstapels und der Forschungs-PRs (§9) | CD-6 | G1 | nichts wird gemergt; Drift wächst |
| OD-03 | Notiztyp-IDs als Konstanten einfrieren und vom Anzeigenamen entkoppeln (empfohlen) oder neue IDs mit Migration | R8 §13 Nr. 2; CD-8 | G1, G-BRAND | heutige Werte bleiben; keine Umbenennung von Anzeigenamen |
| OD-04 | GUID ohne Kapitel-Slug mit Identitätszuordnung; einmaliger Bruch vor erster Freigabe akzeptabel? | R8 §13 Nr. 3; CD-8 | G1 | heutiges GUID-Schema bleibt; Verschieben zwischen Einheiten erzeugt neue Notizen (dokumentiert) |
| OD-05 | Standard „Anki + gewöhnlicher Markdown-Ordner, Obsidian optional“ oder Markdown-Ansicht weglassen; Bestätigung „kein fünftes Produkt“ | R8 §13 Nr. 1 und 8 | keines im MCS | keine Markdown-Ansicht im MCS; AD-1 bleibt |
| OD-06 | Generativer Weg (eigene Karten, Formulierungsaufgaben) anbieten | R8 §13 Nr. 4; R8-POL-13 | keines | nicht angeboten |
| OD-07 | AnkiConnect zurückgestellt lassen | R8 §13 Nr. 5; R8-POL-14 | keines | zurückgestellt |
| OD-08 | Ordnernamen, Frontmatter, `.base`-Ansichten des generierten Bereichs | R8 §13 Nr. 6 | keines | zurückgestellt |
| OD-09 | Umfang der Mobilprüfung (AnkiDroid, AnkiMobile) | R8 §13 Nr. 7 | Freigabe (`RELEASE`, nicht MCS) | nur Desktop, Mobil als ungeprüft ausgewiesen |
| OD-10 | Standard-Brief `keyless`, Musterlösung nur im Modus `with_reference` für Übungsitems nach protokolliertem Versuch; welche Daten überhaupt an Drittanbieter-Chats gehen (keine, nur Übungsschlüssel nach Versuch, frei mit Hinweis) | R9 §6 Nr. 1; CD-7; RT-27; RT-42 | G2 (falls Tutor im Umfang) | Verhalten von PR #43 (Schlüssel für Nachweisrollen zurückgehalten); Tutor nicht in MCS-Armen |
| OD-11 | Lösung auf ausdrückliche Anforderung auch vor erstem Versuch, protokolliert als assistiert | R9 §6 Nr. 2; R5-POL-03 | keines | erlaubt und als assistiert protokolliert (heutiges Verhalten) |
| OD-12 | Nur engine-gelieferte, deterministisch geprüfte Parallelaufgaben zählen; tutor-erzeugte nie | R9 §6 Nr. 3 | G2 | ja (Messvertrag) |
| OD-13a | Budget für bezahlte Modellaufrufe (Tutor-Evaluationsarme A/A2/B, Judge) | R9 §6 Nr. 4 | Tutor-Evaluation, G7 | 0; keine Tutor-Evaluation |
| OD-13b | Budget bzw. Person für unabhängige Item- und Fallautorschaft | R9 §6 Nr. 4; R5-POL-05 | G5, G6 | keine; MCS endet bei G4, „Lernwirkung nicht gemessen“ |
| OD-13c | Budget bzw. Personen für menschliche Bewertung (Rubrik, Doppelbewertung) und unabhängige Fachprüfung | R3-POL-11; R2-POL-05; Charter | G6, G7 | keine; menschlich bewertete Operationen ohne Kompetenzbelege |
| OD-14 | Anbieterliste des portablen Tutorvertrags; Study Mode als empfohlene Option | R9 §6 Nr. 5 | keines | keine offizielle Liste; Vertrag anbieterneutral |
| OD-15 | Lizenzpolitik: CC-BY-SA nur emulieren, PolyForm-NC ausgeschlossen; kommerzieller Status entscheidet über NC-Einbettung (GeoGebra, 3b1b-Code) | R9 §6 Nr. 6; R7 §12 Nr. 1 | jede Einbettung fremder Komponenten (`THIRD_PARTY_EMBEDDING`) | nur Links; keine NC-Einbettung; keine wörtliche Übernahme |
| OD-16 | TutorBench-Stichprobe (CC BY-NC) als Zusatzarm auf Antwortebene | R9 §6 Nr. 7 | keines | nicht genutzt |
| OD-17 | Registerkorrekturen (Margin Study, NotebookLM, RemNote) und Herkunft „Think Logic / Visually Explained“ | R9 §6 Nr. 8; R7 §12 Nr. 2 | keines | Korrekturen nur in Dokumenten; Kandidaten ohne Quelle geschlossen |
| OD-18 | Pyodide-Spike (etwa ein Arbeitstag, ohne Kosten) freigeben | R7 §12 Nr. 3 | G7 für `computational_construction` | kein Spike; Code-Werkbank nicht weiter spezifiziert |
| OD-19 | Marke Phase C: technische Migration (Modul, CLI, Decknamen/GUIDs, Schemas, Zustandsordner, launchd, Repo-Name) | `product_identity.phase_C`; AD-3 | G-BRAND | alle Bezeichner unverändert |
| OD-20 | Kursunterlagen-Dateiname mit Seitenangabe in `exam_mastery/learning/anki_bridge.py` (Entwurfsstapel, öffentlich) neutralisieren; ggf. Umgang mit Historie | `owner_attention`; R8 §2 | G1(d) | bleibt bis zur Entscheidung unverändert; Agenten ändern weder Datei noch Historie |
| OD-21 | Teilnehmende, Einwilligung, Ethik/Datenschutz der Evaluation (Owner allein oder Gruppe) | R5-POL-05; R5-POL-07 | G5 | Owner als einzige Person, innerhalb-Person-Design, Bericht ohne Verallgemeinerung |
| OD-22 | MCS-Thema (quellenfrei-synthetisch oder freigegebenes Material) | R6 §6; Produktvertrag „generisch“ | G4, G5 | vorhandene synthetische `symbolic_procedure`-Strecke |
| OD-23 | Wer prüft die MCS-Strecke inhaltlich und wer auditiert die Prüfer (G3/G4) | Produktvertrag §6; R2-POL-14 | G3, G4 | Owner prüft; bis dahin `HUMAN_REVIEW_PENDING` |
| OD-24 | Praxis-/Zertifizierungsgrenze und Liste gefährlicher Verfahren bestätigen; Umfang je Hochrisikodomäne (Kompetenzbereich oder nur Wissensbegleiter) und ob ein menschlicher Bewertungspfad aufgebaut wird | R3-POL-10; R4-POL-01; R4-POL-13; RT-40 | G7 für diese Domänen | nur Spur A mit Enthaltung; keine Pakete für diese Domänen |
| OD-25 | Vorläufige Produktparameter (20 h, 7 Tage, 2 unassistierte Versuche, 3 Hinweisstufen) für Präregistrierung festschreiben oder ändern | CD-4; R5-POL-01; R5-POL-03; R5-POL-05 | G2, G5 | Werte bleiben, als `provisional_product_parameter` gekennzeichnet |
| OD-26 | Unabhängige zweite Prüfung der Forschungsberichte R0–R9 und R6 (Charter: zweiter Kritiker): mindestens eine menschliche Fachprüfung Lernwissenschaft und je Hochrisikodomäne eine Fachperson für Stichproben; Übernahme der Red-Team-Sicherheitskorrekturen (RT-06, RT-08) | Charter; `workstreams.*.note`; RT-43 | Statuswechsel von Policies über `design_hypothesis` hinaus (`POLICY_STATUS_CHANGE`) | alle Policies bleiben `design_hypothesis`; Red-Team-Korrekturen nicht angewendet |
| OD-27 | KB- und Engine-Regeltexte korrigieren: CD-3 zu AI-R1 (RT-05), R1A §5.12, R7-Regelentscheidungen; RP-R1, WE-R1/R2, MC-R1, PR-R1, AS-R1 operationsgebunden (RT-01 bis RT-04, RT-19) | CD-3; R1 §2; RT-01–RT-05 | G2 (Regeltexte im Kontext der Autorenrollen) | nicht angewendet; ADR-Verbotsliste (§2.6) gilt trotzdem; M4 bleibt gesperrt |
| OD-28 | Darf die Engine fällige Retest-Aufgaben (nicht Karten) anzeigen, oder Retest nur über Anki-Verweiskarten? (Grenze von AD-1) | RT-37; RT-22; R8-POL-01 | G2 | passive Zustandsanzeige `RETEST_DUE` beim Öffnen der Strecke wie heute (Regel RE), ohne Warteschlange und ohne Benachrichtigung |
| OD-29 | Entscheidungsstufe des Messvertrags (zulässige schwächere Designs, verbotene Ersatzgrößen) und verbindliche Produktwortliste („ohne protokollierte Hilfe“, „nicht gemessen“) | RT-38; RT-32; R5-POL-05 | G5, G6 | nur Behauptungsstufe; jede Lernaussage „nicht gemessen“; Ersatzgrößen nicht als Entscheidungsgrundlage |
| OD-30 | Nachweisitem auf ausdrücklichen Wunsch zeigen und ausmustern (assistiert, frisches Nachweisitem) oder verweigern | RT-39; RT-20; R9-POL-04; R5-POL-06 | G2 | zeigen, als assistiert protokollieren, ausmustern; frisches Nachweisitem, sofern vorhanden |
| OD-31 | Edit- und Änderungsklassen-Politik für generierte Anki-Notizen (überschreiben, schützen, forken; redaktionell oder substanziell, ggf. neue GUID) vor dem CD-8-Fix | RT-41; RT-12; RT-21; R8-POL-05; CD-8 | G1 | R8-Standard: unveränderte Notizen nicht neu stempeln; substanzielle Änderungen überschreiben mit Eintrag im Update-Bericht; Historie bleibt; kein Lesen der Sammlung |

**Die fünf wichtigsten:** OD-01 (Architektur), OD-02 (Integrationsreihenfolge und Merge), OD-13b (unabhängige Itemautorschaft, ohne sie keine Lernbehauptung), OD-31 mit OD-03/OD-04 (Anki-Edit-Politik und Identität vor dem CD-8-Fix und vor jeder Umbenennung), OD-20 (Kursunterlagen-Bezeichner im öffentlichen Branch).

## 9. P4-Integrationsplan (CD-6)

**Stapelstruktur** (Basis-Branches laut GitHub, 27.11.2026): `main` ← #11 ← #12 ← #13 ← #14 ← #15 ← #16 ← #17 ← #18 ← #19. Auf #19 bauen zwei Äste auf: Engine #28 ← #37 (CD-2) ← #43 (CD-7) sowie Forschung #20 ← #32 (R0) ← #35 (R1) ← {#38 R2, #39 R5, #40 R3, #41 R4, #42 R9, #44 R8, #45 R7} ← R6. Unabhängig auf `main` liegen #3 (NLP-Referenzeinheit, `HUMAN_REVIEW_PENDING`), #33 (Programmsteuerung) und #36 (Marke Phase B, nur Doku).

**Vorgeschlagene Prüf- und Merge-Reihenfolge (Merge nur durch den Owner):**
1. Hygiene zuerst entscheiden (OD-20), weil der Bezeichner in #11–#19 liegt. Eine Korrektur wäre ein zusätzlicher Commit auf dem Stapel; über die Historie entscheidet der Owner.
2. Engine-Stapel linear: #11 → … → #19 → #28 → #37 → #43. Je Stufe die CI-äquivalente Suite aus eingefrorener Kopie (Speicherhinweis: Suiten nicht während Engine-Änderungen laufen lassen).
3. CD-8-Fix als neuer Entwurfs-PR auf #43 (M0), mit Wegwerfsammlungstests. Er darf vor G0 vorbereitet werden, weil er architekturunabhängig ist und keine sichtbaren Bezeichner ändert, wenn OD-03 beim Default bleibt. Die Edit- und Änderungsklassen-Politik (OD-31, RT-41) sollte vorher entschieden sein; bis dahin gilt ihr Default.
4. Forschungsast: #20 → #32 → #35, danach R2, R3, R4, R5, R7, R8, R9 in beliebiger Reihenfolge (sie fügen überwiegend eigene Dateien hinzu; Konflikte in gemeinsamen Dateien sind nicht geprüft, Unbekannte). Danach R6. Die Forschungs-PRs ändern keinen Produktionscode; ihre Tests lesen aber die KB des Entwurfsstapels (R1-Test prüft `principles.json`). Deshalb erst nach #19.
5. #33 und #36 sind unabhängig. Präsentationsänderungen aus #36 erst nach G1(c). #3 erst nach menschlicher Prüfung.

**Vor der Annahme zulässig (architekturunabhängig):** CD-8-Fix (M0), Hygiene nach OD-20, Testpflege, Dokumentkorrekturen ohne KB-Wirkung. **Nicht zulässig vor G0:** Implementierung von Ontologie, Beobachtungsvertrag, Prüferregistry, Vorlagen oder neuen Schemas.

**Lokaler RL-Pilot des Owners:** Er ist 66 Commits von `main` divergiert, nicht öffentlich und wird von R6 nicht verändert. Er stammt aus einer älteren Engine-Linie; seine Produkte (RL Kap. 3 v6) sind `HUMAN_REVIEW_PENDING`. Er enthält kursbasiertes Material und ist deshalb weder MCS-Kandidat noch Quelle für das öffentliche Repository. Ob Engine-Fixes (CD-2, CD-7, CD-8) dorthin übertragen oder der Pilot neu aufgesetzt wird, entscheidet der Owner nach G1. R6 schlägt dazu nichts vor.

## 10. Was wir nicht behaupten

- Dass H-AB Lernen verbessert oder besser lehrt als A, B oder C. Die Bewertung betrifft Passung, Prüfbarkeit, Betrieb und Kosten, nicht Wirkung.
- Dass die Ordinalurteile in §3.4 gemessen sind; es gibt keine Aufwands- oder Komplexitätsmessung.
- Dass die domänenübergreifenden Befunde (§2.2) unabhängig geprüft sind; sie stammen aus ungeprüften Workstream-Berichten desselben Modells.
- Dass die Gegenbefunde in §2.4 jede Regel in jeder Domäne widerlegen; sie zeigen nur, dass die Regel nicht universell gilt.
- Dass das MCS eine positive Wirkung zeigen wird oder dass ein Ergebnis über die Person, die Kompetenzen und die Verzögerung hinaus gilt.
- Dass die Engine-Abbildung (§3.1, Ontologie-JSON) vollständig ist; gelesen wurden ausgewählte Module, nichts wurde ausgeführt.
- Eine Freigabe, Validierung oder Annahme irgendeines Teils dieses Dokuments.

## 11. Fragen an unabhängige Prüfende

1. Ist H-AB von „Status quo mit neuen Namen“ unterscheidbar? Welche Prüfung in G2/G3 würde das zeigen?
2. Hält die Ablehnung von vollem B, obwohl R1 §4 ein Operations- und Kontextmodell verlangt? Wo kippt K4 in eine versteckte Regelsprache?
3. Ist `symbolic_procedure` als MCS-Domäne eine Verengung, die die Scope-Entscheidung AD-3 unterläuft, oder eine vertretbare erste Phase?
4. Reicht ein innerhalb-Person-Design mit N = 1 für eine „ehrliche“ Behauptung, oder sollte das MCS ausdrücklich nur Machbarkeit und Zustandsvalidität prüfen?
5. Wie wird Kontamination zwischen KCs der beiden Bedingungen begrenzt, wenn Bausteine über Anki gemeinsam geübt werden?
6. Ist die Auflösung des Konflikts R5-POL-04 gegen R2-POL-14/R3-POL-11 (menschliche Rubrik) tragfähig?
7. Fehlt eine Owner-Entscheidung, oder ist ein Default unsicher (ändert er stillschweigend etwas)?

## 12. Antwort auf den Red-Team-Review

Status: **vom ADR-Autor abgeglichen; Prüfung durch den Lead steht aus.** Quelle: `research/r6-red-team-20261127` @ `091ead46`, `docs/research/workstreams/r6/red_team_findings.json` (43 Befunde: 1 Blocker, 39 Major, 3 Minor) und `RED_TEAM_REVIEW.md`. Der ADR-Entwurf (Commit `3a95551`) entstand vor dem Lesen der Befunde. Abgeglichen sind alle Blocker- und Major-Befunde. Die drei Minor-Befunde (RT-09, RT-18, RT-31) sind nicht einzeln abgebildet. Ergebnis: 34 angenommen, 6 teilweise, 0 abgelehnt.

**Eigene Einordnung.** Das Red-Team stützt die Grundentscheidung des Entwurfs: kein volles B, kein C, kein reines A, und der Kern gehört in die Messung. Für vier Punkte war der Entwurf zu schwach, und sie verändern den Vorschlag: (1) RT-26 (Blocker): `kc_status` zählt Hilfe nur an derselben Aufgabe und vertraut Browser-Zeitstempeln. Der Evidenzkern zählt Hilfe deshalb auf KC-Ebene, prüft Zeit auf Plausibilität, und `kc_status` ist nie Evaluationsendpunkt. (2) RT-10: Zustände je Kompetenz *und* Kompetenztyp. (3) RT-11: Der MCS-Prüfer selbst hat eine Lücke im Definitionsbereich; G3 muss sie schließen, bevor das MCS beginnt. (4) RT-36: Die Lernrelevanz von H-AB ist nicht „günstig“, sondern „gemischt“ wie bei allen Optionen; die Auswahl stützt sich nur auf Prüfbarkeit, Sicherheit, Messintegrität, Kosten, Offline-Fähigkeit und Migration.

**Teilweise statt voll angenommen, mit Grund:** RT-03: Konfidenz als Stichprobe ja; die Stichprobe als Within-Learner-Experiment zu nutzen, liegt außerhalb des MCS. RT-06: R6 ändert keine Sicherheitsstufen fremder Workstreams; das ist Aufgabe der unabhängigen Prüfung (OD-26). RT-14, RT-16, RT-24: Die betroffenen Domänen liegen außerhalb des MCS und werden G7-Voraussetzungen, keine sofortigen Änderungen. RT-21: Lokale Änderungen in der Anki-Sammlung zu erkennen, hieße die Sammlung zu lesen. Das schließt R8 aus. Angenommen ist deshalb nur der Teil im Update-Bericht; alles Weitere entscheidet der Owner (OD-31).

| Befund | Schwere | Art / Domäne | Ziele (Auszug) | Entscheidung | Änderung (Ort) |
|---|---|---|---|---|---|
| RT-01 | major | universal_rule / cross_domain | RP-R1, R1-POL-A01, R1-POL-A02, R4-POL-01 | **angenommen** | universelle Regel RP-R1 vor Vorlagen operationsgebunden; NOT_APPLICABLE-Pfad (M4, OD-27) |
| RT-02 | major | universal_rule / cross_domain | WE-R1, WE-R2, R1-POL-A03, R3-POL-03 | **angenommen** | K4 ohne automatisches Überspringen nach einem Item; Überspringen nur als reversibles Angebot (K4, M4, OD-27) |
| RT-03 | major | universal_rule / cross_domain | MC-R1, PR-R1, R1-POL-A09, R3-POL-09 | **teilweise** | Konfidenz nur stichprobenartig (MC-R1/PR-R1 über OD-27); Nutzung der Stichprobe als Within-Learner-Vergleich außerhalb des MCS (M4, OD-27) |
| RT-04 | major | universal_rule / cross_domain | AS-R1, AS-R2, R3-POL-11, R4-POL-01 | **angenommen** | K1-Item mit alternative_routes, verifier, evidence_channel; Zeit als Schätzung (K1, ontology item_fields) |
| RT-05 | major | universal_rule / tutoring | AI-R1, CD-3, R9-POL-04, R5-POL-03 | **angenommen** | bereits OD-10/OD-27; AI-R1-Text bleibt bis Owner-Entscheidung unverändert, Verbotsliste gilt (OD-10, OD-27, cannot_claim) |
| RT-06 | major | universal_rule / cross_domain | R2-POL-11, R7-POL-02, R7-POL-08, R4-POL-09 | **teilweise** | R6 ändert keine Workstream-Sicherheitsstufen; Korrektur als Eingabe für OD-26; MCS hängt nicht an R2-POL-11 (OD-26) |
| RT-07 | major | universal_rule / tutoring | R5-POL-08, R5-POL-03, R9-POL-03, AI-R1 | **angenommen** | Hilfeleiter im MCS nur für symbolic_procedure, Stufenzahl vorläufig; für Beweis/Recht keine Stufenzahl (MCS hint_ladder) |
| RT-08 | major | universal_rule / cross_domain | R1-POL-A01, R1-POL-A04, R1-POL-A05, R5-POL-04 | **angenommen** | Verbotsliste: keine Gültigkeit für Erwachsene/Selbststudium aus Schulevidenz; population_match als Empfehlung an OD-26; MCS-Population benannt (cannot_claim, MCS population, OD-26) |
| RT-10 | major | domain_failure / math_proof | R2-POL-02, R2-POL-14, R2-POL-05, ITS-R2 | **angenommen** | Zustände je (Kompetenz, Kompetenztyp); Prüfer muss Kompetenztyp abdecken; Konstruktion ohne Prüfer nicht beobachtet (K2, observation_contract state_derivation) |
| RT-11 | major | domain_failure / math_symbolic | R2-POL-15, FB-R2, R2-POL-14, ITS-R2 | **angenommen** | Ausdrucksprüfer: Stichprobe aus deklariertem Definitionsbereich, exakte Prüfung Pflicht wo möglich; G3 mit definitionsbereichssensitiven Fällen (K3, G3, MCS verifiers) |
| RT-12 | major | domain_failure / law | R3-POL-01, R8-POL-02, R8-POL-12, R1-POL-A01 | **angenommen** | Änderungsklassen redaktionell/substanziell im Update-Bericht; Entscheidung OD-31 (M0, OD-31) |
| RT-13 | major | domain_failure / law | R3-POL-11, R3-POL-04, R5-POL-01, R9-POL-08 | **angenommen** | Items mit geringer Ergebnisvielfalt zählen nicht allein; Retest kontrafaktisch variiert; Begründung getrennt vom Ergebnis (observation_contract state_derivation, FX-15) |
| RT-14 | major | domain_failure / clinical | R3-POL-09, R3-POL-08, R3-POL-10, R1-POL-A09 | **teilweise** | Klinik nicht im MCS; als G7-Voraussetzung (Prävalenz deklariert, Referenzdiagnosen geprüft) (G7) |
| RT-15 | major | domain_failure / code_debugging | R7-POL-08, R2-POL-13, R2-POL-11, R9-POL-08 | **angenommen** | G7-Voraussetzung für Code: engine-ausgeführte Läufe, property-/mutationsbasierte verborgene Tests, eingefügte Ausgaben = self_report (G7, ontology hidden_or_property_tests) |
| RT-16 | major | domain_failure / cad_spatial | R4-POL-11, R4-POL-15, R2-POL-14, R4-POL-10 | **teilweise** | CAD nicht im MCS; G7: verdeckte randomisierte Änderungstests oder NOT_APPLICABLE (G7) |
| RT-17 | major | domain_failure / craft_or_lab | R4-POL-01, R4-POL-14, R4-POL-12, R1-POL-B05 | **angenommen** | Anzeige 'Wissen geprüft - Ausführung nicht beobachtet' ohne Fortschrittsbalken bei physischem Anteil; Übungsprotokoll eigener Kanal; Bewertungspfad OD-24 (ontology tracks display_rule, OD-24) |
| RT-19 | major | conflict / cross_domain | R1-POL-A02, R7-POL-02, PR-R1, PF-R1 | **angenommen** | Standard ohne Novizen-Klassifikator: Beispiel zuerst, Vorhersage/Erkundung als Angebot (K4) |
| RT-20 | major | conflict / tutoring | R9-POL-04, R9-POL-09, R9-POL-03, R5-POL-06 | **angenommen** | Rangfolge festgelegt (Vorschlag), Wertentscheidung OD-30; Nachweisitems nie im Brief (precedence, OD-30, FX-10) |
| RT-21 | major | conflict / anki | R8-POL-13, R8-POL-05, R8-POL-07, R8-POL-02 | **teilweise** | Update-Bericht nennt geänderte Notizen (Überschreibrisiko); Erkennung lokaler Änderungen durch Lesen der Sammlung abgelehnt (R8: keine Lesezugriffe), außer Owner erlaubt es über OD-31 (M0, OD-31) |
| RT-22 | major | conflict / measurement | R8-POL-01, SP-R1, SP-R2, R8-POL-12 | **angenommen** | ausdrückliche Entscheidung nötig: OD-28 mit Default passive Zustandsanzeige ohne Warteschlange (OD-28) |
| RT-23 | major | conflict / craft_or_lab | R2-POL-11, PR-R1, R4-POL-09, R4-POL-13 | **angenommen** | Vorhersage-Gates nur in Spur-A-Umgebungen mit engine-eigener Ausführung; keine Ausprobier-Aufforderung zu realer Praxis (ontology practice_certification_boundary) |
| RT-24 | major | conflict / cross_domain | R9-POL-01, R3-POL-01, R3-POL-10, R3-POL-11 | **teilweise** | normative Grenzen bleiben; G7 verlangt Messgröße Sitzungsende nach Enthaltung und abgestufte, gekennzeichnete Rückfallebene (G7) |
| RT-25 | major | conflict / cross_domain | R1-POL-B07, R9-POL-09, R5-POL-08, R1-POL-A08 | **angenommen** | globale Rangfolge aus dem Produktvertrag abgeleitet, Paarkonflikte mit Testfall in G2; Bestätigung mit OD-01 (precedence, G2) |
| RT-26 | blocker | measurement / measurement | CD-2, R5-POL-01, R5-POL-04, R1-POL-A01 | **angenommen** | Hilfe auf KC-Ebene mit Zeitfenster; Zeitstempel in der Zukunft oder aus Importen = time_quality unverified; Anzeige 'erneut gelöst nach >= 20 h ohne protokollierte Hilfe'; Evaluationsendpunkt nie kc_status (K2, observation_contract, FX-13/FX-14, G5, MCS endpoint_source) |
| RT-27 | major | measurement / tutoring | CD-7, R9-POL-04, R5-POL-04, R5-POL-03 | **angenommen** | Nachweisrollen nicht exportieren; Schlüssel nur nach protokolliertem Versuch; Produktwort 'ohne protokollierte Hilfe' (FX-10, OD-10, cannot_claim) |
| RT-28 | major | measurement / anki | R1-POL-A01, R8-POL-12, R5-POL-04, R8-POL-01 | **angenommen** | Anki-Reviews sind self_report; A01-Falsifikator nur an engine-geprüften Items; MCS nutzt keine Anki-Daten (ontology evidence_kinds anki_review, cannot_claim) |
| RT-29 | major | measurement / measurement | R5-POL-01, R1-POL-A01, TR-R1, R3-POL-04 | **angenommen** | 'umformuliert' operationalisiert: Transferdimension deklariert, Unterschied im Lösungsweg oder Ergebnis (K1, observation_contract item.transfer_dimension, MCS item_requirements) |
| RT-30 | major | measurement / measurement | R2-POL-05, R3-POL-11, R9-POL-05, R9-POL-06 | **angenommen** | keine Lockerung im ADR; Bedingungen in Wiedervorlage von C aufgenommen (rejected_options C) |
| RT-32 | major | measurement / measurement | R5-POL-05, R1-POL-B05, R8-POL-12, CD-1 | **angenommen** | zweistufiger Vertrag: Behauptungsstufe unverändert, Entscheidungsstufe per OD-29 (observation_contract evaluation_contract.decision_tier, OD-29) |
| RT-33 | major | architecture / architecture | RP-R1, WE-R1, AS-R1, CD-4 | **angenommen** | Vorlagen-Experiment vor Ausweitung über MCS (G7, Wiedervorlage A); universelle Regeln vor M4 korrigiert (G7, M4, rejected_options A) |
| RT-34 | major | architecture / architecture | R5-POL-02, R1-POL-A03, R2-POL-14, CD-1 | **angenommen** | K4 nur beobachtbare Prädikate; Experiment als Bedingung der Wiedervorlage von B (K4, rejected_options B) |
| RT-35 | major | architecture / architecture | CD-7, CD-8, R8-POL-02, R9-POL-04 | **angenommen** | Build-Zeit-Audits ersetzen nie G3/G4; Experiment als Bedingung der Wiedervorlage von C (K6, rejected_options C) |
| RT-36 | major | architecture / architecture | CD-1, R5-POL-05, R2-POL-14 | **angenommen** | Lernrelevanz von H-AB auf 'gemischt'; Auswahlbasis ausdrücklich ohne Lernwirksamkeit; je Baustein der abgefangene Fehler (assessments H-AB, selection_basis, components.catches) |
| RT-37 | major | owner_decision / measurement | R8-POL-01, SP-R2 | **angenommen** | neue Owner-Entscheidung (OD-28) |
| RT-38 | major | owner_decision / measurement | R5-POL-05, R1-POL-B05 | **angenommen** | neue Owner-Entscheidung (OD-29) |
| RT-39 | major | owner_decision / tutoring | R9-POL-04, R9-POL-09, AI-R1 | **angenommen** | neue Owner-Entscheidung (OD-30) |
| RT-40 | major | owner_decision / cross_domain | R3-POL-10, R3-POL-11, R4-POL-01, R4-POL-13 | **angenommen** | OD-24 erweitert (OD-24) |
| RT-41 | major | owner_decision / anki | R8-POL-05, R8-POL-02, CD-8, R3-POL-01 | **angenommen** | neue Owner-Entscheidung, blockiert G1 (CD-8-Fix) (OD-31) |
| RT-42 | major | owner_decision / tutoring | R9-POL-04, R9-POL-10, CD-7 | **angenommen** | OD-10 erweitert (OD-10) |
| RT-43 | major | owner_decision / evidence_integrity | CD-1, CD-5 | **angenommen** | OD-26 erweitert (OD-26) |


## 13. Reproduktion

```
git fetch origin
python3 docs/research/workstreams/r6/build_policy_index.py policy_index_check.json   # Index aus den gepinnten Branches neu bauen
python3 -c "import json,collections; P=json.load(open('docs/research/workstreams/r6/policy_index.json'))['policies']; print(collections.Counter(p['certainty'] for p in P)); print(collections.Counter(o for p in P for o in p['applies_to_operations']))"
python3 -m unittest tests.test_r6_architecture   # prüft nach dem Merge des Red-Team-Branches auch die Abdeckung aller Blocker-/Major-Befunde
git show origin/research/r6-red-team-20261127:docs/research/workstreams/r6/red_team_findings.json   # Red-Team-Eingabe (§12)
gh pr list --state open --json number,baseRefName,headRefName   # Stapelstruktur §9
```
Engine-Stellen: `git show origin/fix/tutor-evidence-integrity-20261127:exam_mastery/learning/policy.py` (Regeln R0–RE, `kc_status`, `ASSIST_EVENTS`), `…/experience.py` (`OPERATIONS`, `MODES`, Rollen, `machine_check`), `…/experience_evidence.py` (`TYPES`), `…/tutor.py` (`KEY_WITHHELD_ROLES`), `…/evaluation.py` (`assign`).
