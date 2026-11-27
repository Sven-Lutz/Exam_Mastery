# R1A — Kognitions- und Instruktionswissenschaft für anspruchsvolle Hochschulprüfungen

Stand: 27.11.2026. **Forschungszwischenstand zur unabhängigen Begutachtung, keine Freigabe und kein Wirksamkeitsnachweis für Exam Mastery.** Autor: Spezialagent R1A (Claude) im Arbeitspaket WP-R1, koordiniert durch den Lead-Agenten; Branch `research/r1-learning-science-20261127`. Ein Agent hat recherchiert, extrahiert und selbst kritisiert; **keine unabhängige Zweitextraktion**, die im Charter verlangte unabhängige Kritik steht aus. Schlaf, Fatigue, Aufmerksamkeit, Motivation, Stress, Bewegung, Deliberate Practice und nachhaltige Lernintensität gehören zu R1B und werden hier bewusst nicht behandelt.

Grundlage: [Forschungsprogramm](../../RESEARCH_FIRST_PROGRAM_20261126.md), [R0-Audit](../KB_GAP_AUDIT.md) (Deep Reviews werden als „R0-D2“ usw. zitiert und nicht wiederholt), [Evidenzregister-Schema](../EVIDENCE_REGISTER_SCHEMA.md). Maschinenlesbares Register: [`r1a_evidence.json`](r1a_evidence.json) (Schema `r1-evidence/1`, 31 Einträge). Vorhandene KB-IDs (`exam_mastery/knowledge/sources.json`, `principles.json`) bleiben unverändert; alle Korrekturen unten sind **Vorschläge**. Keine Volltexte im Repository; Zitate sind Paraphrasen mit Fundstelle.

## 0. Kurzbefund

1. **Abruf ist operationsspezifisch, kein universeller Standard.** In Hochschul-Klassenräumen ist Quizzing robust positiv (Yang et al. 2021: g = 0.499 [0.442; 0.557], PEESE-korrigiert 0.475; gegen Wiederlesen 0.330). Für Problemlösefertigkeiten, die aus Worked Examples erworben werden, fand eine Serie von vier Experimenten aber **keinen** Testeffekt nach einer Woche (van Gog et al. 2015); in der Mathematik ist Testen gegen Restudy metaanalytisch nicht robust (Murray et al. 2025: g = 0.18, KI schließt 0 ein); in Schulklassen sind Testeffekte für konzeptuelles/prozedurales Wissen und für Transfer-Outcomes nicht statistisch nachweisbar (Ruitenburg et al. 2026, kleine k).
2. **Spacing hilft auch in Mathematikkursen, aber kleiner als im Labor** (kursintegriert g = 0.24; Murray et al. 2025); ein randomisiertes Hochschulexperiment zu einer mathematischen Prozedur fand keinen Spacing- oder Lag-Effekt (Ebersbach & Barzagar Nazari 2020). **Interleaving** hat mit Rohrer et al. 2020 (präregistrierte Cluster-RCT, 54 Klassen) d = 0.83 [0.68; 0.97] nach einem Monat – Schulmathematik, konstruktionsbedingt mit Spacing konfundiert.
3. **Selbsterklärung** wirkt im Mittel (Bisra et al. 2018: g = .55 [.45; .65], Studierende .61), aber nur **g = .35 gegenüber Instruktionserklärungen (k = 6)**; metakognitive und Multiple-Choice-Prompts sind nicht signifikant; Publikationsbias wurde nur per Fail-safe-N geprüft. Barbieri et al. 2023 (Worked Examples Mathematik) und Kalyuga & Sweller 2004 (Schnelldiagnose) blieben ohne Volltext – eine valide Übergangsdiagnose für Hochschul-Fading ist **nicht** belegt.
4. **Productive Failure bleibt niedrig gesichert:** Sinha & Kapur 2021 blieb auch in R1A ohne Volltext (Sage 403); das Abstract nennt g = 0.36 [0.20; 0.51] und eine ungewöhnliche biasadjustierte Schätzung von 0.87, für Klasse 2–5 und domänenübergreifende Fertigkeiten ist Instruktion-zuerst überlegen. Ashman et al. 2020 (Klasse 5, randomisiert) favorisieren Instruktion zuerst bei hoher Elementinteraktivität.
5. **Feedback-Timing auf Aufgabenebene ist kein Hebel, Urteile sind nicht inert:** ManyClasses 1 (38 College-Kurse, präregistriert) schätzt sofort vs. um Tage verzögert auf 0.002 [−0.05; 0.05]. Korrektives Feedback nach Quizzen geht dagegen mit größerem Nutzen einher (Yang: .537 vs. .374; Moderatorvergleich, nicht randomisiert). Gedächtnisurteile während des Übens kehrten in zwei Experimenten den Testeffekt um (Higham et al. 2023); Monitoring-Interventionen verbessern Urteilsgenauigkeit leicht (g = 0.25), ein Effekt auf spätere Prüfungsleistung wurde nicht gefunden (Janssen & Lazonder 2024).

## 1. Forschungsfragen, Suchprotokoll und Screening

### 1.1 Forschungsfragen

Zielpopulation: Studierende, die anspruchsvolle Prüfungen in Mathematik, Informatik, Wirtschaft, Recht oder Medizin vorbereiten. Jede Frage zielt auf **verzögerte, selbstständige (unassistierte) Leistung**, nicht auf Übungsleistung.

| RQ | Frage | Entscheidungsrelevanz |
|---|---|---|
| RQ1 | Wirken Abrufübung, Successive Relearning und Pretesting bei komplexem, elementinteraktivem Material? Wann verdrängt Abruf nötige Instruktion? | RP-R1–R3, sp.4, Reihenfolge Beispiel/Abruf |
| RQ2 | Wie groß ist Spacing für komplexe Fertigkeiten und Mathematik, auch unter festem Zeitbudget (Cramming vs. Spacing)? | SP-Regeln, Anki-Planung |
| RQ3 | Wann hilft Interleaving in Mathematik, über welchen Mechanismus, wann ist Blocken zuerst besser? | IL-R1; baut auf R0-D5 |
| RQ4 | Was tragen CLT, Worked Examples, Completion, Fading und Expertise Reversal; wie valide ist Schnelldiagnose; wie belastbar ist CLT-Messung? | WE-R1/R2, CL-R1/R2; baut auf R0-D6/D9 |
| RQ5 | Unter welchen Bedingungen nützt Problemlösen vor Instruktion (PS-I/PF); welche Null-/Gegenbefunde gibt es? | PF-R1 |
| RQ6 | Welche Selbsterklärungs- und generativen Prompts wirken; welche Rolle spielt Erklärungsqualität? | SE-R1/R2 |
| RQ7 | Feedback auf Item-/Schrittebene: Timing, Elaboration, Hinweise und Hilfemissbrauch | FB-R1/R2, AI-R1; baut auf R0-D7/D8 |
| RQ8 | Metakognition: Genauigkeit von JOLs, verzögerte JOLs, Reaktivität, Überschätzung, Kalibrierungstraining; Konfidenz als Datum vs. Intervention | MC-Regeln, Konfidenzfelder |
| RQ9 | Transfer: nah vs. fern, Ferntransfer-Nullbefunde, Fallvergleich, Prädiktoren selbstständigen Transfers | TR-R1, unabhängige Outcome-Definition |

### 1.2 Werkzeuge und Datum

Alle Suchen und Zugriffe am **27.11.2026**. Werkzeuge: allgemeiner Web-Suchindex (Claude-Code-Tool `WebSearch`, Modus standard), Seitenabruf (`WebFetch`, liefert eine modellbasierte Zusammenfassung der Seite – deshalb als „tool-summarised“ gekennzeichnet), `curl` zu Crossref-, OpenAlex-, Semantic-Scholar- und Europe-PMC-APIs (nur Metadaten/Abstracts) sowie Download frei zugänglicher PDFs/DOCX in ein temporäres Scratch-Verzeichnis außerhalb des Repositories mit lokaler Textextraktion (`pdftotext`, `textutil`). Keine lizenzierten Datenbanken (PsycINFO, Scopus, Web of Science). Web-Suchindizes sind dynamisch; Trefferzahlen werden nicht berichtet. Insgesamt 46 Seitenabrufe auf Seitenebene einschließlich gescheiterter Versuche (Budget ~45 leicht überschritten, um einen frei zugänglichen Nullbefund im Volltext zu lesen) plus Metadaten-API-Aufrufe.

### 1.3 Suchjournal (exakte Queries)

| Nr. | Exakte Query / Zugriff | Tool | Ergebnis und Screeningentscheidung |
|---|---|---|---|
| S01 | `https://link.springer.com/article/10.1007/s10648-026-10225-5` | WebFetch, curl | Charter-Seed. Springer: Cookie-Redirect bzw. JavaScript-Challenge, **gescheitert**. |
| S02 | `api.crossref.org/works/10.1007/s10648-026-10225-5`; `api.openalex.org/works/doi:10.1007/s10648-026-10225-5` | curl | Abstract (CC BY 4.0) gelesen; OU-Repositoriumseintrag ohne Datei (gescheitert). |
| S03 | `https://eric.ed.gov/?id=EJ1478558` | WebFetch | Charter-Seed = Murray, Horner & Göbel 2025; Abstract der Version of Record. |
| S04 | OpenAlex-OA-Prüfung für `10.1007/s10648-025-10035-1`, `10.1037/bul0000309`, `10.3102/00346543211019105`, `10.1007/s10648-023-09745-1`, `10.1007/s10648-018-9434-x` | curl | Murray: OSF-Preprint (DOCX) gefunden und gelesen; Yang/Barbieri/Bisra: closed. |
| S05 | `Yang Luo Vadillo Yu Shanks 2021 "Testing (quizzing) boosts classroom learning" pdf transfer g` | WebSearch | Drittanbieter-Spiegel der APA-Online-first-Fassung; gelesen, nicht weiterverbreitet. UAM-Repositorium (JS-only) gescheitert. |
| S06 | `van Gog Kester Dirkx Hoogerheide Boerboom Verkoeijen 2015 "testing after worked example study does not enhance delayed problem-solving performance" pdf` | WebSearch | Universität Utrecht, Verlagsfassung Open Access; eingeschlossen. |
| S07 | `Karpicke Aue 2015 "The testing effect is alive and well with complex materials" pdf` | WebSearch | Nur inoffizieller Springer-Spiegel (**ausgeschlossen**); Karpicke & Aue nur Metadaten. van Gog & Sweller 2015 über UU-Repositorium eingeschlossen. |
| S08 | OpenAlex-Suche `Rawson "complexity of retrieval practice" 2015` | curl | Rawson-Erwiderung **nicht gefunden** (ersetzte Suche); stattdessen Redifer et al. 2025 identifiziert und eingeschlossen. |
| S09 | `Higham Zengel Bartlett Hadwin 2022 "successive relearning" multiple learning outcomes Journal of Educational Psychology pdf` | WebSearch | Southampton-PDF: HTTP 403 (gescheitert); Abstract via OpenAlex. Nebenfund Higham et al. 2023 (Reaktivität) eingeschlossen. |
| S10 | Crossref für `10.1007/s10648-023-09814-5`, `10.1007/s10648-021-09595-9`, `10.1037/edu0000268`, `10.1037/edu0000693`, `10.1037/xap0000345` | curl | Metadaten; Abstracts teils fehlend. Pan & Sana 2021 nur identifiziert, nicht gelesen. |
| S11 | Europe-PMC-REST `DOI:` für fünf EPR-Artikel | curl | 0 Treffer bzw. Fehler – **gescheitert**. |
| S12 | Springer-Redirectkette (`idp.springer.com/authorize` → `transit` → Artikel) für Pan & Carpenter 2023, Ruitenburg et al. 2026, Janssen & Lazonder 2024 | WebFetch | Jeweils ca. 100 000 Zeichen des CC-BY-Volltexts, modellbasiert zusammengefasst; Tabellenwerte teils nicht sichtbar → `fulltext_partial`. |
| S13 | `https://journals.sagepub.com/doi/full/10.3102/00346543211019105`; Sage-PDF; ETH Research Collection | WebFetch, curl | HTTP 403 bzw. „Access Restricted“ – Sinha & Kapur 2021 **erneut ohne Volltext**. |
| S14 | `Sinha Kapur 2021 "productive failure" meta-analysis "fidelity" conceptual procedural transfer Hedges g pdf` | WebSearch | Kein Volltext; Kapur, Saba & Roll 2023 (PMC) eingeschlossen; EdArXiv-Preprint „From problem-solving to sensemaking“ (Sinha & Kapur) nur identifiziert. |
| S15 | Crossref-Batch: Ashman 2020, Kalyuga & Sweller 2004, de Jong 2010, Rohrer 2020, Barbieri 2023, Bisra 2018, Sinha 2021, Alfieri 2013, Sala & Gobet 2017 | curl | Abstract nur für Sinha und Sala & Gobet; Rohrer 2020 als APA-Open-Access lizenziert. |
| S16 | OpenAlex-OA: de Jong 2010 → `ris.utwente.nl` Autorenfassung; Kalyuga & Sweller 2004 → UNSW-DSpace-Eintrag | curl | de Jong gelesen; UNSW-Eintrag ohne Datei (gescheitert). |
| S17 | `Kalyuga Sweller 2004 "Measuring knowledge to optimize cognitive load factors during instruction" rapid assessment first step pdf` | WebSearch | Kein Volltext; eScholarship-Link lieferte HTML statt PDF (gescheitert); Abstract später via OpenAlex. |
| S18 | `Rohrer Dedrick Hartwig Cheung 2020 "A randomized controlled trial of interleaved mathematics practice" pdf 787 students effect size` | WebSearch | Spiegel der Online-first-Fassung gelesen; WWC-Angaben nur als Sekundärinformation. |
| S19 | `Barbieri Miller-Cotto Clerjuste Chawla 2023 worked examples mathematics meta-analysis "g =" moderators fading self-explanation` | WebSearch | Nur Snippets/Poster mit widersprüchlichen Zahlen; **nicht als Beleg verwendet**. |
| S20 | OpenAlex-/Semantic-Scholar-Abstract-Batch (u. a. Yeo & Fazio 2019, Agarwal 2021, Higham 2022, Rhodes & Tauber 2011, Redifer 2025) | curl | Teilweise HTTP 429 (Rate-Limit); fehlende Abstracts bei APA/Springer bleiben fehlend. |
| S21 | Crossref `query.bibliographic`: Kalibrierungs-Metaanalyse; JOL-Reaktivität; verzögertes Feedback/Transfer; Ashman 2020; Bisra 2018; Concept Maps | curl | Gutierrez de Blume 2022, Double et al. 2018, Mullet et al. 2014, Schroeder et al. 2018 identifiziert; Nesbit & Adesope 2006 mit Abstract. |
| S22 | `Bisra Liu Nesbit Salimi Winne 2018 "Inducing self-explanation" meta-analysis "g =" 64 studies prompts` | WebSearch | CORE-Link lieferte HTML (gescheitert); Spiegel der Verlagsfassung gelesen. Clearinghouse-Zusammenfassung nicht als Beleg genutzt. |
| S23 | `"Calibrating calibration" Gutierrez de Blume 2022 meta-analysis monitoring accuracy effect size performance interventions results` | WebSearch | Keine Zahlen; Janssen & Lazonder 2024 gefunden und teilweise gelesen. |
| S24 | `Mullet Butler Verdin von Borries Marsh 2014 delaying feedback engineering course homework transfer exam results immediate vs delayed` | WebSearch | Mullet nur als Snippet; **ManyClasses 1** (Fyfe et al. 2021) gefunden, Abstract via Crossref. |
| S25 | `Ashman Kalyuga Sweller 2020 "which should go first when element interactivity is high" results explicit instruction first outperformed problem solving first` | WebSearch | Abstract-Inhalt über Snippet; Volltext nicht abgerufen. |
| S26 | `https://pmc.ncbi.nlm.nih.gov/articles/PMC10185511/` | WebFetch | Kapur et al. 2023 gelesen (modellbasiert zusammengefasst). |
| S27 | `https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2020.00811/full` | WebFetch | Ebersbach & Barzagar Nazari 2020 (aus Murrays Referenzliste) im Volltext gelesen. |

### 1.4 Screeningregeln und Zugriffsentscheidungen

- **Eingeschlossen bevorzugt:** neuere Metaanalysen mit Bias-Sensitivität, präregistrierte oder Multi-Site-Studien, Klassenraum-RCTs mit verzögertem, unassistiertem Outcome, explizite Null-/Negativbefunde, Volltexte aus Repositorien/PMC/OSF/Verlags-Open-Access.
- **Ausgeschlossen als Beleg:** Blogs, Lehrerplattformen, Clearinghouse-Zusammenfassungen, Poster, LinkedIn/Scribd, Suchmaschinen-Zusammenfassungen. Wo Inhalte nur über ein Snippet erreichbar waren (Barbieri, Ashman, Mullet), ist das im Register als `metadata` bzw. ausdrücklich als Snippet markiert und **nicht** zahlentragend verwendet.
- **Drittanbieter-Spiegel** (Yang 2021, Rohrer 2020, Bisra 2018): nur gelesen, nicht kopiert; Seitenangaben beziehen sich auf die gespiegelte Fassung (bei Yang/Rohrer Online-first-Paginierung). Versionsabgleich mit der Version of Record ist offen (G12).
- **Modellbasierte Seitenzusammenfassungen** (WebFetch: Ruitenburg, Pan & Carpenter, Janssen & Lazonder, Kapur 2023, Ebersbach 2020) sind fehleranfälliger als selbst extrahierter Text. Zahlen daraus werden berichtet, aber vor Übernahme in die KB gegen den Originaltext zu prüfen.
- **Preprint vs. Version of Record:** Bei Murray et al. weichen Preprint (g = 0.26 gesamt; Testen 0.221) und VoR-Abstract (0.28; Testen 0.18, 7 Studien/32 Effekte) ab. Zitiert werden VoR-Zahlen; Struktur, KI und Bias-Analysen nur aus dem Preprint, entsprechend markiert.
- **Nicht gesucht/gelesen (Umfangsgrenze):** Renkl-Primärstudien zum Fading, Fiorella & Mayer 2016 (KB `fiorella2016`), Elaborative Interrogation, Aleven-Primärstudien zu Hilfesuche (nur KB-Claim its.5), Rawson-Erwiderung 2015, Pan & Sana 2021, Schroeder et al. 2018. Sie stehen in der Lückenliste (Abschnitt 8).

### 1.5 Bilanz

31 Quellen im Register: 3 vorhandene KB-Quellen (`sinha2021`, `bisra2018`, `barbieri2023`), 28 neue. Zugriffsebene: **9 `fulltext_claim_review`, 3 `fulltext_partial`, 13 `abstract`, 6 `metadata`.** Damit liegen 12 Quellen auf Volltext-/Claim-Ebene (Untergrenze des Auftrags). Keine neue Metaanalyse, keine PRISMA-Vollständigkeit, keine RoB-2-/AMSTAR-2-Bewertung; Bias-Einwände sind begründete Einzelurteile eines Reviewers.

## 2. Evidenztabelle

Abkürzungen: *ua* = unassistiert (ohne Hilfen beim Outcome), *verz.* = verzögert, *KI* = 95 %-Konfidenzintervall, *FT* = Volltext (claim-level), *FT-p* = Volltext teilweise/modellbasiert, *Abs* = Abstract, *Meta* = nur Metadaten/Snippet. Metriken wie berichtet; g = Hedges g, d = Cohen d.

| ID | Design / Population | Operation, Material | Intervention vs. Vergleich | Outcome (Hilfe / Verzögerung / Transfer) | Schätzung wie berichtet | Zugriff | Hauptgrenzen | KB-Bezug |
|---|---|---|---|---|---|---|---|---|
| `yang2021classroom` | Mehrebenen-MA, 222 Studien, 573 Effekte, N = 48 478; Schule bis Hochschule | Fakten, Konzepte, Problemlösen in Kursprüfungen | Quizzing vs. Restudy/keine Aktivität/andere Strategien | ua; Kursprüfung; identisch/umformuliert/ungetestet | Gesamt g = 0.499 [0.442; 0.557]; PEESE 0.475 [0.329; 0.620]; vs. Restudy 0.330 [0.256; 0.404]; Hochschule 0.486; Mathe/Statistik 0.433 [0.193; 0.674]; Problemlösen 0.453 [0.309; 0.596]; ungetestetes Material 0.321 [0.210; 0.432]; mit Korrekturfeedback .537 vs. ohne .374 (pdf S.12–19, Tab. 2) | FT (Spiegel) | viele quasi-experimentelle Studien; „Problemlösen“ aus Prüfungsinhalt kodiert, nicht Elementinteraktivität; Inhaltstyp-Moderator n. s. (p = .087) | stützt rp.4; qualifiziert rp.3, rp.2 |
| `agarwal2021classroom` | Systematischer Review, 50 Experimente, 49 Effekte, n = 5 374 | Kursinhalte | Abruf vs. diverse | ua; diverse | 57 % mittlere oder große Effekte (Abstract); kein Pool | Abs | Vote-Counting; Titel stärker als 57 % | stützt rp.4 eingeschränkt |
| `ruitenburg2026classroom` (Testing) | 3-Ebenen-MA, 31 Studien, 120 Effekte, n = 3 391; Klasse 1–12 | Fakten/Konzepte/Prozeduren | Abruf vs. aktive Kontrolle | ua; diverse; Transfer kodiert | g = 0.37 [0.18; 0.56]; faktisch 0.53; konzeptuell p = .10 (k = 10), prozedural p = .63, Transfer-Outcome p = .92 (k = 9); im Gesamtmodell nur Testformat robust (Results 3.2.1) | FT-p | Schulpopulation; kleine k je Untergruppe; Multikollinearität (VIF 7–10.6) | qualifiziert rp.3, rp.4 |
| `ruitenburg2026classroom` (Spacing/Interleaving) | dto.; Spacing 15 Studien/56 Effekte, Interleaving 10/57 | diverse | verteilt vs. massiert/weniger verteilt; gemischt vs. geblockt | ua; RI < 1 h bis > 1 Woche | Spacing 0.20 [0.03; 0.36], vs. massiert 0.39, vs. weniger verteilt n. s.; ISI/RI 0.10–<1: 0.31. Interleaving 0.40 [0.10; 0.71]; ohne Feedback 0.25, verzögertes Feedback 0.82 (k = 5), sofortiges n. s. (Results 3.2.2–3.2.3) | FT-p | Schulpopulation; Tabelle 1 (Fach Mathematik) nicht gesehen; keine biasadjustierten Schätzer | qualifiziert sp.1, il.1 |
| `murray2025mathspacing` (Spacing) | präregistrierte MA (RVE); Mathematik; Kurs-Subset zu 65 % Hochschule | Prozeduren (Kombinatorik, Statistik, Analysis) | verteilt vs. massiert | Prüfung 2 Tage–5 Wochen; nahe | VoR: gesamt g = 0.28 (27 Studien/53 Effekte); isoliert 0.43; kursintegriert 0.24. Preprint: isoliert 0.384 [0.085; 0.683], Kurs 0.24 [0.155; 0.324] | FT (Preprint) + Abs (VoR) | Kurs-Subset: Abruf nicht gesichert (53 % konnten Unterlagen sehen), Spacing mit Interleaving konfundiert; Egger im Kurs-Subset signifikant (Preprint) | stützt sp.1 |
| `murray2025mathspacing` (Testing) | dto.; 7 Studien/32 Effekte (VoR) | Prozeduren/Konzepte | Abruf vs. Restudy | kurze bis mittlere RI | VoR g = 0.18, KI schließt 0 ein; Preprint 0.221 [−0.091; 0.532] | wie oben | kleine k; kurze Behaltensintervalle | qualifiziert rp.3 |
| `vangog2015testingwe` | 4 randomisierte Experimente, N = 448; Univ. NL, Exp. 4 Berufsschule | Fehlerdiagnose in Stromkreisen; Wahrscheinlichkeitsrechnung | Problemlösen/Beispielabruf nach Worked Example vs. Beispiel erneut studieren | ua; 5 min und 1 Woche; isomorph | Kein Testeffekt in keinem Experiment und in der Gesamtanalyse; Restudy mit weniger Aufwand (Abstract; S.283–284) | FT | n ≈ 20–43 pro Zelle; kurze Erwerbsphase | widerspricht rp.3 für diese Operation; stützt we.1 |
| `leahy2015testingwe` | 3 Experimente (sekundär berichtet); Grundschule | Busfahrpläne lesen | Beispiel-Problem-Paare vs. nur Beispiele | ua; sofort, 1 Woche | sofort: nur Beispiele besser; 1 Woche: kein Testeffekt (van Gog & Sweller 2015, S.254) | Meta | nur Sekundärbericht der Hypothesenvertreter | qualifiziert rp.3 |
| `yeo2019retrievalwe` | 3 Experimente | Text eines Beispiels merken vs. neue Mathe-Prozedur lernen | wiederholtes Testen vs. wiederholtes Studieren | sofort, 1 Woche; identische vs. variierte Lernprobleme | sofort: Studieren besser für Prozeduren; 1 Woche: Testen = Studieren bei variierten, > Studieren bei identischen Problemen (Abstract) | Abs | Population/Effektgrößen nicht gelesen | qualifiziert rp.3, we.1 |
| `redifer2025advanced` | Experiment, n = 213 Studierende | Forschungsartikel (fortgeschrittener Text) | kombinierte Abrufstrategien vs. Wiederlesen | ua; Verzögerung unbekannt | kein Vorteil des Abrufs; höhere kognitive Belastung vermittelte niedrigere Werte (Abstract) | Abs | Einzelstudie; Null ≠ Äquivalenz | qualifiziert rp.4 |
| `higham2022relearning` | kursintegriert, wöchentliche Alternation, Einführung Psychologie | Lückentexte zu Kursinhalten | Successive Relearning (3 Sitzungen, 2 Tage Abstand, Feedback, Fehlitems bis 2× wiederholt) vs. zeitgleiches Restudy | ua; Semesterende; Abruf, kein Transfer | Relearning besser; individuelle Unterschiede moderierten nicht (Abstract) | Abs | Effektgröße nicht gelesen; Outcome = Wiedergabe | stützt sp.4 (nur Abruf) |
| `higham2023reactivity` | 3 präregistrierte Online-Experimente | Swahili-Englisch-Wortpaare | verteilter Abruf vs. Restudy, mit/ohne Gedächtnisurteil pro Trial | ua; Sitzungen 2 Tage auseinander | mit Urteil: Restudy > Abruf (umgekehrter Testeffekt); ohne Urteil: Abruf ≥ Restudy (Abstract) | Abs | Wortpaare; Mechanismus (Reaktivität) interpretativ | qualifiziert rp.1; neu für mc |
| `pan2023pretesting` | narrativer Review | Text/Video/Vorlesung; wenige Klassifikations-/Prozeduraufgaben | Prequestions/Pretests vs. kein Pretest | ua; Minuten bis Wochen | oft Nutzen für vorgetestete Inhalte; gemischt für ungetestete; Inferenztransfer oft null; MOOC: kein Gesamtnutzen, mehr Abbruch | FT-p | Mathematik-/Problemlöseteile nicht gesehen | qualifiziert pr.1 |
| `ebersbach2020mathspacing` | randomisiert 3 × 2, N = 235 Studierende, DE | Permutationsformel | ISI 0/1/11 Tage | ua; 1 bzw. 5 Wochen; gleiche Aufgaben | ISI vs. massiert B = −0.02, p = .909; kein Lag-Effekt; nur RI-Effekt β = −0.24 | FT | ein Verfahren; niedrige Testwerte (Boden); Tutorial-Zeitpunkt im Massiert-Arm verschoben | qualifiziert sp.1/sp.2 |
| `rohrer2020interleaved` | präregistrierte Cluster-RCT, 54 Klassen, 15 Lehrkräfte; Klasse 7 | Strategiewahl zwischen Aufgabentypen | überwiegend gemischt vs. überwiegend geblockt (~4 Monate) | ua; unangekündigt nach 1 Monat; nah | d = 0.83 [0.68; 0.97]; 61 % vs. 38 %; je Typ 0.86–0.34 in Reihenfolge der Blockung (S.8) | FT (Spiegel) | Interleaving ⇒ zugleich Spacing; Schulpopulation | stützt il.2 |
| `bisra2018` | MA, 69 Effekte, N = 5 917 | Problemlösen, Verstehen, Transfer (inkl. medizinische Diagnose, Geometrie) | Selbsterklärungs-Prompts vs. keine zusätzliche Erklärung/Instruktionserklärung/andere Strategie | ua; Transfer kodiert | g = .552 [.454; .650]; vs. keine Zusatzerklärung .673; vs. Instruktionserklärung .354 [.175; .533] (k = 6); Transfer .534; Verstehen .282 n. s. (k = 3); metakognitive Prompts .192 n. s.; MC-Prompts .24 n. s. (k = 2); Studierende .611 (Tab. 1, 2, 6, 7) | FT (Spiegel) | Bias nur Fail-safe-N; Erklärungsqualität nicht moderiert | stützt/qualifiziert se.1 |
| `barbieri2023` | MA (RVE) | Mathematik | Worked Examples vs. Problemlösen | unbekannt | **nicht verifiziert** (Snippets: g = 0.48) | Meta | ungelesen | we.5 bleibt offen |
| `kalyuga2004measuring` | 4 Experimente; Klasse 9–10 | Algebra, Geometrie | Erste-Schritt-Schnelltest vs. traditioneller Test; adaptive Instruktion | Korrelation; Testzeit | r bis .92; Testzeit um Faktor 4.9 bzw. 2.5 reduziert (Abstract) | Abs | „bis zu“ = Bestfall; konkurrente, nicht prädiktive Validität | qualifiziert we.4 (R0-D6) |
| `dejong2010clt` | kritischer Review | — | — | — | Belastungsarten uneinheitlich definiert (S.113–114); Belastung oft post hoc aus Nachtest erschlossen (S.114); Ein-Item-Skala: hohe Reliabilität spricht eher für Personeneigenschaft (S.117); manche Effekte nur bei kurzer, systemgetakteter Lernzeit (S.125) | FT | theoretisch | qualifiziert cl.1, cl.2 |
| `vangog2015complexity` / `karpicke2015complex` | Editorial mit Post-hoc-EI-Kodierung / Kommentar | — | Testen vs. Restudy | — | Hypothese: Testeffekt sinkt mit Elementinteraktivität (Tab. 1, S.250–253); Gegenposition nur als Metadaten erfasst | FT / Meta | Kodierung post hoc, Studienauswahl umstritten | rp.3: unresolved |
| `sinha2021` | MA, 53 Studien, 166 Vergleiche | v. a. Konzepte in Mathe/Naturwissenschaften | PS-I vs. I-PS | ua; Verzögerung unbekannt | g = 0.36 [0.20; 0.51]; hohe PF-Treue 0.37–0.58; biasadjustiert 0.87; I-PS besser für Klasse 2–5 und domänenübergreifende Fertigkeiten (Abstract) | Abs | Treue nach eigenen PF-Prinzipien kodiert (Allegiance-Risiko); Volltext erneut unerreichbar | qualifiziert pf.1 |
| `ashman2020sequence` | 2 randomisierte Experimente, N = 64/71; Klasse 5 | Energieeffizienz (Licht) | Instruktion zuerst vs. Problemlösen zuerst | ähnliche und Transferprobleme | Exp.1: Instruktion zuerst besser bei ähnlichen, gleich bei Transfer; Exp.2 (höhere EI): besser bei beiden (Snippet des Abstracts) | Abs (Snippet) | junge Lernende – passt zu Sinhas eigenem Altersbefund | qualifiziert pf.1; stützt pf.2 |
| `kapur2023prior` | 2 quasi-experimentelle Studien nur mit PF, N = 217; Klasse 7/8 SG | Verhältnisse, Varianz | PF ohne Vergleichsarm | ua; 1 Woche; nah | Anzahl generierter Lösungsansätze sagt Nachtest vorher (F = 62.6 bzw. 105.5, p < .001) | FT-p | korrelativ; Gruppenprädiktor für Individuen | kontextuell zu pf.1 |
| `fyfe2021manyclasses` | präregistrierte Within-Class-Randomisierung in 38 College-Kursen | diverse Kursaufgaben | sofortiges vs. um einige Tage verzögertes Feedback | ua; Kursprüfungen | 0.002, 95 %-HDI [−0.05; 0.05]; 40 präregistrierte Moderatoren ohne glaubhaften Effekt (Abstract) | Abs | Aufgabenebene, nicht Schrittebene | qualifiziert fb.3 |
| `mullet2014delayedfb` | 2 Kursexperimente, Ingenieurwesen (Snippet) | Hausaufgaben | Feedback 1 Woche verzögert vs. sofort | Prüfung, neue Probleme | verzögert besser; Studierende bevorzugten sofort (Snippet) | Meta | nicht gelesen; Spacing-Konfundierung | Kontext zu fb.3 |
| `rhodes2011delayedjol` | 2 MAs | Wortpaare (überwiegend) | verzögerte vs. sofortige JOLs | relative Genauigkeit; Gedächtnis | Genauigkeit g = 0.93 (112 Effekte); Gedächtnis g = 0.08 (98 Effekte) (Abstract) | Abs | relative ≠ absolute Kalibrierung; Labor | Kontext zu mc.1 |
| `double2018reactivity` | MA | Wortpaare/-listen | JOLs abfragen vs. nicht | Erinnern | nicht gelesen (nur maschinelle Kurzfassung) | Meta | — | Lücke |
| `janssen2024monitoring` | MA, 35 Studien | Problemlösen (Mathe, Naturwiss., Reasoning) | Monitoring-Interventionen vs. Kontrolle | **Urteilsgenauigkeit**, nicht Leistung | g = 0.25 [0.12; 0.37]; Timing-Interventionen negativ (k = 2); Labor > Klasse; retrospektive Urteile > JOLs; Egger/Begg n. s. | FT-p | keine Leistungsanalyse; Tab. 3 nicht gesehen | qualifiziert mc.1 |
| `gutierrez2022calibrating` | MA | unbekannt | Strategieinstruktion | Monitoring-Genauigkeit | nicht gelesen | Meta | — | Lücke |
| `alfieri2013comparison` | MA, 57 Experimente, 336 Tests | Fallvergleiche | Vergleich vs. sequenziell/Einzelfall/traditionell | sofortiges Testen größer | d = .50 [.44; .56]; Moderatoren: Gemeinsamkeiten suchen, Prinzip **nach** Vergleich, perzeptueller Inhalt, sofortiger Test (Abstract) | Abs | abhängige Tests; verzögerter Transfer schwächer | Kontext zu tr.1 |
| `sala2017fartransfer` | 3 MAs (Schach, Musik, Arbeitsgedächtnistraining) | Ferntransfer | Training vs. passive/aktive Kontrolle | kognitive/schulische Leistung | Effekte sinken mit Designqualität; Ferntransfer selten (Abstract) | Abs | allgemeines Training ≠ Fachunterricht | stützt tr.1 |
| `nesbit2006conceptmaps` | MA, 55 Studien, 67 Effekte, N = 5 818 | Concept Maps, Klasse 4 bis postsekundär | Concept Maps vs. diverse | Erinnern und Transfer | „klein bis groß“ je Nutzung/Vergleich (Abstract) | Abs | Pool nicht gelesen | Kontext zu se.2 |

## 3. Konkurrierende Modelle und Gegenbefunde

### 3.1 Konkurrierende Modelle

| Cluster | Modell A | Modell B | Unterscheidende Vorhersage | Stand der Evidenz |
|---|---|---|---|---|
| Abruf bei komplexem Material (RQ1) | **Abruf als allgemeine „wünschenswerte Erschwernis“** (Karpicke & Aue 2015, nur Titel/Metadaten; Rowland, R0-D2): Abruf stärkt Gedächtnis auch für komplexe Inhalte. | **Elementinteraktivitäts-Grenze** (van Gog & Sweller 2015): Bei hoher Interaktivität fehlt erst das Schema; Testen bringt nichts oder verdrängt Studium. | A: Testeffekt nach Verzögerung auch nach 1–4 Worked Examples. B: kein Effekt, solange kein Schema vorliegt; Effekt erst nach Schemaerwerb. | van Gog 2015 (vier Nullbefunde, 1 Woche) und Leahy 2015 stützen B **für Problemlösen aus Beispielen in der Erwerbsphase**; Yang 2021 (Problemlöse-Prüfungsinhalte g = .453) stützt A **für Kursinhalte nach Instruktion**. Die Kodierung „hoch/niedrig“ ist post hoc (vgs2015, Tab. 1). |
| | **Passung Verarbeitung–Ziel** (Yeo & Fazio 2019; Ruitenburgs Interpretation): Abruf stärkt Gedächtnis/Flüssigkeit, Beispielstudium stärkt Schemainduktion; welches „gewinnt“, hängt von Ziel, Verzögerung und Variation ab. | — | sofortiger Test: Studieren ≥ Testen; verzögert mit identischen Problemen: Testen > Studieren; mit variierten Problemen: gleich. | Abstract-Ebene (Yeo & Fazio). Erklärt A und B zugleich, ist aber flexibel genug, um schwer falsifizierbar zu sein. |
| Spacing in Mathematik (RQ2) | **Study-phase retrieval**: Spacing wirkt, weil der zweite Durchgang den ersten abrufen muss. | **Deklarativ/prozedural-Dissoziation** (Ebersbach 2020, Diskussion): Für diskrete Prozeduren kann Massierung gleichwertig sein. | A: Spacing-Vorteil schrumpft, wenn Unterlagen sichtbar sind (kein Abruf). B: kein Spacing-Effekt für kurze Prozeduren unabhängig von Abrufbedingungen. | Murray et al. konnten „Abruf sicher/unsicher“ kodieren, fanden keinen signifikanten Moderator. Gegen B spricht Murrays Subset isolierter Prozeduren (u. a. Kombinatorik; Preprint g = 0.384 [0.085; 0.683]), für B Ebersbach 2020 mit demselben Aufgabentyp. Die einzelnen Primärstudien des Subsets wurden nicht gelesen. Unentschieden. |
| Interleaving (RQ3) | **Diskriminativer Kontrast / Strategiewahl** (Rohrer 2020): Mischen zwingt zur Wahl der Methode. | **Spacing-Nebenprodukt**: Mischen verteilt automatisch die Übung. | A: Vorteil auch bei gleichem Abstand; B: Vorteil verschwindet, wenn Abstände konstant gehalten werden. | Rohrer 2020 kann A und B nicht trennen (S.8, Reihenfolgekonfundierung). R0-D5: Materialähnlichkeit als Meta-Regression, nicht kausal. Ruitenburg: verzögertes Feedback als Moderator (k = 5). |
| Beispiele und Belastung (RQ4) | **CLT** (Sweller; Kalyuga): Begrenztes Arbeitsgedächtnis, Beispiele senken lernirrelevante Suche, Expertise kehrt dies um. | **Messkritik** (de Jong 2010): Belastung wird oft aus dem Lernergebnis rückgeschlossen; Konstrukte inkonsistent; Erklärung damit teilweise zirkulär. | CLT sagt vorher, dass unabhängig gemessene Belastung den Effekt vermittelt; Kritik erwartet, dass Belastungsmaße Effekte nicht unabhängig vorhersagen. | Verhaltenseffekt (Beispiele für Novizen) ist besser belegt als der CLT-Mechanismus. Redifer 2025 berichtet Belastung als Mediator – aber subjektiv gemessen. |
| PS-I/PF (RQ5) | **Productive Failure** (Kapur; Sinha & Kapur 2021): Vorwissensaktivierung, Lückenbewusstsein, Generierung vieler Lösungsansätze bereiten Konsolidierung vor. | **Instruktion zuerst** (Kirschner 2006 – KB pf.2; Ashman et al. 2020): Ungeleitetes Problemlösen überlastet Novizen bei hoher Interaktivität. | A: PS-I > I-PS für Konzept/Transfer bei Treue; B: I-PS ≥ PS-I bei niedrigem Vorwissen und hoher Interaktivität. | Beide finden Stützen in unterschiedlichen Populationen (Sinha: Vorteil ab Sekundarstufe, I-PS für Klasse 2–5; Ashman: Klasse 5). Direkter Hochschultest mit Vorwissen als randomisiertem/gemessenem Moderator fehlt in R1A-Lektüre. |
| Feedback-Timing (RQ7) | **Sofort** (Cognitive Tutors, KB its.4): Fehler früh korrigieren, Floundering vermeiden. | **Verzögert** (Mullet 2014): Verzögerung wirkt wie Spacing. | A vs. B auf derselben Granularität testen. | Auf Aufgabenebene: präregistrierte Multi-Site-Null (ManyClasses 1). Schulklassen-Interleaving: verzögertes Feedback .82 (k = 5, nicht randomisierter Moderator). Schrittebene in Hochschulmathematik: in R1A nicht neu belegt. |
| Metakognition (RQ8) | **Urteil als Messung**: JOL/Konfidenz liest Lernstand ab. | **Urteil als Intervention** (Reaktivität): Das Abfragen verändert Encodierung und Lernentscheidungen. | A: Urteile verändern Leistung nicht; B: Leistung mit Urteil ≠ ohne Urteil. | Higham 2023: Gedächtnisurteile kehrten den Testeffekt um; Rhodes & Tauber: verzögerte JOLs Gedächtnis g = 0.08 (klein, aber ≠ 0). B ist für Produktdesign relevant. |
| Transfer (RQ9) | **Gemeinsame Elemente/Schemaabstraktion**: Transfer, wenn Struktur explizit verglichen wird (Alfieri 2013). | **Ferntransfer-Skepsis** (Sala & Gobet 2017): Effekte verschwinden mit aktiven Kontrollen. | A: Fallvergleich verbessert verzögerten Strukturtransfer; B: Gewinne bleiben nah und kurzlebig. | Alfieri: sofortiges Testen → größere Effekte (Hinweis, dass verzögerter Transfer schwächer ist). Sala & Gobet betreffen allgemeines Training, nicht Fachunterricht. |

### 3.2 Explizite Null-, Negativ- und Gegenbefunde

Nullbefunde sind **keine Äquivalenznachweise**; die Spalte „Grenze“ nennt, was sie nicht zeigen.

| Nr. | Befund | Quelle / Fundstelle | Was er zeigt | Grenze |
|---|---|---|---|---|
| N1 | Kein Testeffekt nach Worked-Example-Studium in vier Experimenten (5 min und 1 Woche), auch nach vier Beispielen | `vangog2015testingwe`, Abstract; S.283 | Abruf/Problemlösen ersetzt in der Erwerbsphase kein weiteres Beispielstudium; Restudy erreichte gleiche Leistung mit weniger Aufwand | kleine Zellen; kurze Erwerbsphase; nahe Aufgaben |
| N2 | Testen vs. Restudy in Mathematik: g = 0.18, KI schließt 0 ein | `murray2025mathspacing`, VoR-Abstract; Preprint Subset 3 | Kein robuster Testeffekt für Mathematik metaanalytisch nachweisbar | nur 7 Studien; unpräzise, nicht „null bewiesen“ |
| N3 | Klassenraum-Testeffekt für Transfer-Outcome p = .92 (k = 9), konzeptuell/prozedural n. s. | `ruitenburg2026classroom`, Results 3.2.1.2 | Der Gesamteffekt g = 0.37 wird von Faktenwissen getragen | Schulpopulation; kleine k; modellbasierte Extraktion; Tabelle 1 offen |
| N4 | Sofort vs. verzögert: 0.002 [−0.05; 0.05] über 38 Kurse; 40 Moderatoren ohne glaubhaften Effekt | `fyfe2021manyclasses`, Abstract | Feedback-Timing auf Aufgabenebene ist im Mittel kein Hebel | Aufgabenebene; „einige Tage“; nicht Schritt-Feedback |
| N5 | Mit Gedächtnisurteilen: Restudy > verteilter Abruf | `higham2023reactivity`, Abstract | Metakognitive Abfragen können den Nutzen von Abruf aufheben/umkehren | Wortpaare; Abstract-Ebene |
| N6 | Kein Spacing- und kein Lag-Effekt für eine Mathe-Prozedur (N = 235) | `ebersbach2020mathspacing`, Results | Spacing-Vorteile für Prozeduren sind nicht garantiert | ein Verfahren; niedrige Testwerte; Massiert-Arm mit verschobenem Tutorial |
| N7 | Abrufstrategien nicht besser als Wiederlesen für einen Forschungsartikel; Belastung vermittelt Nachteil | `redifer2025advanced`, Abstract | Bei anspruchsvollen Texten kann Abruf Kapazität kosten | Abstract; Einzelstudie |
| N8 | Problemlösen zuerst schlechter als Instruktion zuerst bei höherer Elementinteraktivität (Transferprobleme) | `ashman2020sequence`, Abstract (Snippet) | PF-Vorteil ist nicht universell | Klasse 5; Snippet-Ebene |
| N9 | Metakognitive Selbsterklärungs-Prompts g = .192 n. s.; MC-Prompts g = .24 n. s.; Verstehens-Outcome n. s. | `bisra2018`, Tab. 2/6; S.17 | Nicht jeder „Erkläre!“-Prompt wirkt | k = 2–3, unpräzise |
| N10 | Monitoring-Interventionen über Urteils-Timing **senkten** die Genauigkeit | `janssen2024monitoring`, Results | Kalibrierungsinterventionen können schaden | k = 2; nur Genauigkeit, nicht Leistung |
| N11 | Pretests in einem MOOC: kein Gesamtnutzen, mehr Abbrüche | `pan2023pretesting`, Abschnitt „Authentic Educational Settings“ (Janelli & Lipnevich 2021, sekundär) | Pretesting kann in selbstgesteuerten Kontexten Motivation/Verbleib kosten | Sekundärbericht im Review |
| N12 | Ferntransfer allgemeiner Trainings verschwindet mit Designqualität | `sala2017fartransfer`, Abstract | Keine Ferntransferversprechen aus Übungsgewinnen | anderes Interventionsfeld |

### 3.3 Wo die Gegenbefunde selbst schwach sind

N1/N8 stammen überwiegend aus Laboren, die der CLT-Hypothese nahestehen (Allegiance-Risiko), N3/N9/N10 aus kleinen Untergruppen, N5/N7/N8/N11 nur auf Abstract- oder Sekundärebene. Gleichzeitig sind die positiven Gegenstücke (Sinha 2021, Barbieri 2023) ebenfalls nicht im Volltext geprüft. Die Konsequenz ist **keine Umkehr der KB-Prinzipien**, sondern engere Geltungsbereiche und Abstention dort, wo die Zieloperation nicht durch Evidenz gedeckt ist.

## 4. Mechanismus → Lernhandlung → Systemaffordanz → Beobachtbares → unabhängiges Outcome → Fehlermodus

„Mechanismus“ bezeichnet die **verhaltensbezogene Erklärungshypothese**, keinen neuronalen Nachweis. Beobachtbares im Produkt ist nie selbst Lernnachweis.

| Mechanismus (Hypothese) | Lernhandlung | Systemaffordanz | Beobachtbares | Unabhängiges Outcome | Fehlermodus |
|---|---|---|---|---|---|
| Abruf stärkt Zugänglichkeit abrufbaren Wissens | Antwort aus dem Gedächtnis erzeugen, dann Korrektur lesen | Karten/Kurzfragen mit verdeckter Antwort, Korrektur nach Versuch, Anki-Planung | Versuchs-Log mit Hilfestatus, Antwortlatenz, Korrektheit | verzögerter (≥ 1 Woche), unangekündigter, unassistierter Abruf **und** Anwendung an neuen Items | Abruf ersetzt nötiges Beispielstudium (N1); Karten zerschneiden Bedingungen; Erfolg durch Wiedererkennen der Kartenform |
| Successive Relearning: Abruf bis Kriterium über Sitzungen | Fehlitems in derselben Sitzung wiederholen, mehrere Sitzungen | Sitzungsweise Wiedervorlage falscher Items | Anzahl Versuche bis Kriterium je Sitzung | Semesterende-Abruf; zusätzlich Anwendungsitems | nur Lückentext-Abruf trainiert (Higham 2022 misst Abruf); Kriterium zu niedrig → Scheinsicherheit |
| Spacing / study-phase retrieval | Wiederholung nach Pause statt am Stück | Kumulative Übungssätze, Anki-Intervalle, Prüfungsdatum als Planungsparameter | tatsächlicher zeitlicher Abstand je Item (Kalendertag ≠ Intervall, R0 T2) | verzögerte unassistierte Leistung zu fixem Prüfungstermin | Spacing ohne Abruf (Unterlagen offen, Murray); zu kurze Restzeit; Prozeduren ohne Effekt (N6) |
| Diskriminativer Kontrast / Strategiewahl | Bei jeder Aufgabe zuerst Typ und Methode bestimmen | Gemischte Sätze nach Erstkontakt, Lösungen erst am Satzende | Fehler der Art „falsche Methode gewählt“ vs. „Methode falsch ausgeführt“ | unangekündigter gemischter Test mit neuen Items, inkl. Distraktortyp ohne passende Methode | Mischen vor Erstverständnis überfordert; Mischen unähnlicher Kategorien (Wörter: R0-D5 negativ) |
| Schemaerwerb durch Beispiele (CLT) | Beispiel studieren, Schritte begründen, Lücken ergänzen | Worked Example → Completion → Fading, Hilfen reversibel | Erste-Schritt-Korrektheit an unbekannten Isomorphen; Hilfeabrufe | verzögerte unassistierte Lösung isomorpher und strukturell variierter Aufgaben | Expertise Reversal (Fortgeschrittene langweilen/belasten sich); Fehlklassifikation durch Ein-Item-Diagnose (R0-D6) |
| Selbsterklärung: Inferenzen generieren, Lücken reparieren | Schritt in eigenen Worten begründen | offene, inhaltsbezogene Prompts; Vergleich mit Referenzerklärung | Erklärungstext; Abgleich mit Referenz-Kernaussagen (nicht nur Länge) | Transfer- und Problemlöseaufgaben ohne Prompt | falsche Selbsterklärung wird verfestigt; „Erklärung auf Abruf“ untergräbt eigenes Erklären (Schworm & Renkl, sekundär in Bisra S.16) |
| PS-I/PF: Vorwissensaktivierung, Lückenbewusstsein | Vor der Instruktion eigene Lösungsansätze versuchen | kurze, begrenzte Explorationsaufgabe, danach Konsolidierung mit Vergleich der eigenen Ansätze zur kanonischen Lösung | Anzahl/Art generierter Ansätze (Kapur 2023) | konzeptuelle und Transferitems nach Verzögerung, im Vergleich zu Instruktion-zuerst | Floundering ohne Konsolidierung; Zeitverlust kurz vor Prüfung; Novizen überlastet (N8) |
| Korrektives Feedback | Fehler mit korrekter Lösung vergleichen | Korrektur nach jedem Abruf/Versuch; bei Schritten: Markierung + gestufte Hinweise nach eigenem Versuch | Hilfestufe je Schritt, Zeit bis Hilfeabruf, Wiederholungsfehler | unassistierte Leistung ohne Hinweise auf neuen Items | Hilfemissbrauch/Durchklicken bis zur Lösung (KB its.5); Feedback ersetzt Denken (Offloading, R0-D10) |
| Monitoring: Urteile steuern Lernentscheidungen | Konfidenz/JOL abgeben, mit Ergebnis vergleichen | verzögerte/retrospektive Urteile, Kalibrierungsanzeige gegen externe Standards | Urteil vs. tatsächliches Ergebnis (Brier/Kalibrierungskurve), getrennt nach nahen und Transferitems | Kalibrierung **und** Leistung an späteren unbekannten Items | Reaktivität (N5); Kalibrierung nur auf nahen Items; Urteils-Timing-Interventionen schaden (N10) |
| Fallvergleich / Strukturabstraktion | Zwei Fälle auf gemeinsame Struktur vergleichen, dann Prinzip lesen | Paare strukturgleicher, oberflächenverschiedener Fälle plus Kontrastfall; Prinzip nach Vergleich | Benennung des gemeinsamen Prinzips; Klassifikation neuer Fälle | verzögerter Strukturtransfer an neuen Oberflächen | nur sofortige Effekte (Alfieri); Vergleich ohne Prinzip bleibt oberflächlich |

## 5. Policy-Kandidaten R1-POL-Axx

**Status aller Kandidaten: `design_hypothesis`.** Die Sicherheitslabels sind eine **interne, an GRADE angelehnte Einschätzung** eines einzelnen Reviewers (Start: hoch für randomisierte Evidenz in der Zielpopulation; Abwertung für Indirektheit, Inkonsistenz, Unpräzision, Bias, Publikationsbias), keine externe Leitlinie. Jeder Zahlenwert ist als **„provisional product parameter, not an empirical constant“** gekennzeichnet. Taxonomie nach Charter: *recall/discrimination*, *symbolic procedure*, *formal proof*, *rule-based contextual reasoning*, *diagnostic reasoning*, *computational construction*, *open-ended synthesis*.

### R1-POL-A01 — Abruf mit Korrektur und Successive Relearning für abrufbares Wissen

- **Zieloperation:** recall/discrimination (Definitionen, Satzaussagen mit Voraussetzungen, Normtatbestandsmerkmale, Fachbegriffe, Formeln mit Gültigkeitsbedingungen) als **Bausteine** aller Domänen.
- **Lernkontext:** nach erster verständnisorientierter Instruktion; beliebige Phase; sinnvoll ab ≥ 1 Woche bis zur Prüfung.
- **Empfehlung:** Abrufitems mit verdeckter Antwort, unmittelbar korrektivem Feedback, Wiedervorlage falscher Items in derselben Sitzung und über mehrere Sitzungen; Planung über Anki (kein eigener Scheduler, R0/R8).
- **Abstention/Fallback:** Kein Abruf als Ersatz für Instruktion, solange das zugrunde liegende Verfahren nicht verstanden ist (→ A02). Keine Abrufitems für Beweis-/Lösungsketten, deren Teile nur im Zusammenhang Sinn ergeben. Keine Mastery-Aussage aus Kartenstatistik.
- **Evidenzkanten:** `yang2021classroom` pdf S.12, Tab. 2 S.15, S.18 (supports; Hochschule .486, Korrekturfeedback .537 vs. .374); `higham2022relearning` Abstract (supports, nur Abruf); R0-D1/D2 (supports, Labor); `ruitenburg2026classroom` Results 3.2.1 (qualifies: faktisch ja, Transfer n. s.); `agarwal2021classroom` Abstract (supports, 57 %); `higham2023reactivity` (qualifies: keine Urteile pro Trial, → A09).
- **Interne Sicherheit:** **moderat** für verzögerten Abruf von Kursinhalten (große, biasgeprüfte Klassenraum-MA; Abwertung wegen Heterogenität Q(572) = 4 816 und vieler quasi-experimenteller Studien); **niedrig** für Effekte auf Anwendung/Transfer.
- **Beobachtbares:** Versuchs-Log (Antwort vor Aufdecken ja/nein, Korrektheit, Sitzung, tatsächlicher Abstand in Tagen).
- **Unabhängiges Outcome:** unangekündigter, unassistierter Test ≥ 1 Woche nach letzter Sitzung mit neu formulierten Items (Yang: „rephrased“) und separaten Anwendungsitems.
- **Schaden/Fehlermodus:** Atomisierung zerstört Bedingungen (z. B. Satzaussage ohne Voraussetzung); Wiedererkennen der Kartenform statt Abruf; Zeitverdrängung von Verständnisarbeit.
- **Falsifikator:** In einer vorab registrierten Within-Learner-Randomisierung von Items (Relearning vs. zeitgleiches Restudy) zeigt der verzögerte unassistierte Abruf keinen Vorteil oberhalb einer vorab festgelegten Mindestdifferenz.
- **Parameter:** 3 Sitzungen, Kriterium 1 korrekter Abruf je Item und Sitzung, Abstand ≥ 1 Tag — *provisional product parameter, not an empirical constant* (Higham 2022 nutzte 3 Sitzungen im Abstand von 2 Tagen; die Kriteriumsforschung von Rawson & Dunlosky wurde hier nicht gelesen).

### R1-POL-A02 — Beispiel vor Abruf bei Novizen und hoher Elementinteraktivität

- **Zieloperation:** symbolic procedure, computational construction, prozedurale Teile von diagnostic reasoning.
- **Lernkontext:** neues Verfahren, niedriges aufgabenspezifisches Vorwissen; frühe Erwerbsphase.
- **Empfehlung:** Zuerst Worked Examples (mehrere, oberflächenvariiert, mit Selbsterklärungsprompt → A06), danach Completion-Aufgaben; selbstständiges Problemlösen und Abruf erst, wenn mindestens ein unbekanntes Isomorph ohne Hilfe gelöst wurde.
- **Abstention/Fallback:** Bei nachgewiesenem Vorwissen (A03) Beispiele überspringen bzw. ausblenden (Expertise Reversal). Wenn keine verlässliche Diagnose möglich ist: Lernenden die Wahl lassen und Beispiele reversibel anbieten.
- **Evidenzkanten:** `vangog2015testingwe` Abstract, S.283–284 (supports: kein Zusatznutzen von Testen in der Erwerbsphase); `yeo2019retrievalwe` Abstract (supports/qualifies: sofortige Prozedurleistung nach Studieren besser; nach 1 Woche gleich bei variierten Problemen); `leahy2015testingwe` (qualifies, sekundär); R0-D6 Kalyuga 2007 (supports, Primärstudien heterogen); `barbieri2023` (context_only, ungelesen); `dejong2010clt` S.114–117 (qualifies: Mechanismus „Belastung“ nicht unabhängig gemessen).
- **Interne Sicherheit:** **moderat**, dass Abruf in der Erwerbsphase keinen Zusatznutzen gegenüber weiterem Beispielstudium hat; **niedrig** für die genaue Abfolge und den Umschaltpunkt.
- **Beobachtbares:** Zahl studierter Beispiele, Completion-Korrektheit, erstes unassistiertes Isomorph.
- **Unabhängiges Outcome:** verzögerte (≥ 1 Woche) unassistierte Lösung isomorpher **und** strukturell variierter Aufgaben.
- **Schaden/Fehlermodus:** Fortgeschrittene werden mit Beispielen gebremst; passive Beispielrezeption ohne Selbsterklärung; Beispiele mit Fehlern verwirren Novizen (Barbieri-Snippet: korrekte Beispiele stärker – unverifiziert).
- **Falsifikator:** Wenn bei gleicher Zeit „Beispiel → sofort Abruf/Problemlösen“ gegenüber „Beispiel → weiteres Beispiel → Problemlösen“ beim verzögerten unassistierten Test besser abschneidet, ist die Reihenfolgeregel für die geprüfte Operation zu verwerfen.
- **Parameter:** „≥ 2 Beispiele vor erstem eigenständigem Lösen“ — *provisional product parameter, not an empirical constant*.

### R1-POL-A03 — Reversible Übergangsdiagnose (Erster-Schritt-Probe) und Fading

- **Zieloperation:** symbolic procedure (Algebra-/Analysis-/Statistikverfahren); **nicht** formal proof.
- **Lernkontext:** zwischen Beispielphase und selbstständigem Üben; bei heterogenem Vorwissen.
- **Empfehlung:** Kurze Probes, die nur den ersten Lösungsschritt an unbekannten Isomorphen verlangen; Übergang zu weniger Unterstützung nach wiederholtem Erfolg, Rückkehr nach Fehlschlag; Hilfen jederzeit reversibel.
- **Abstention/Fallback:** Keine Expertenklassifikation aus einem Item (R0-D6). Bei Beweisaufgaben, offenen Modellierungen oder wenn der erste Schritt mehrdeutig ist: keine automatische Einstufung, stattdessen Selbstwahl plus vollständige Aufgabe.
- **Evidenzkanten:** `kalyuga2004measuring` Abstract (supports nur konkurrente Validität: r bis .92 in Klasse 9–10, Zeitersparnis 4.9/2.5); R0-D6 (qualifies: Effektgrößen aus Einzelstudien); `dejong2010clt` (qualifies).
- **Interne Sicherheit:** **sehr niedrig** für Hochschulfächer (indirekte Population, nur Abstract, keine Fehlklassifikationsraten, keine Daten zur Wirkung der Adaptivität auf verzögerte Leistung).
- **Beobachtbares:** Erster-Schritt-Korrektheit, Latenz, Folge der Unterstützungsstufen.
- **Unabhängiges Outcome:** Übereinstimmung der Probe-Einstufung mit einer vollständigen, unabhängig bewerteten Lösung neuer Aufgaben (Fehlklassifikationsrate) **und** verzögerter Leistungsvergleich adaptiv vs. feste Sequenz.
- **Schaden/Fehlermodus:** Falsch-positive Einstufung → zu früh ohne Hilfe, Frustration; falsch-negative → Langeweile; Raten des ersten Schritts.
- **Falsifikator:** Fehlklassifikationsrate gegenüber vollständiger Lösung über einer vorab festgelegten Grenze oder keine Überlegenheit adaptiver gegenüber fester Sequenz im verzögerten Test.
- **Parameter:** Übergang nach 2 aufeinanderfolgenden korrekten ersten Schritten, Rückfall nach 1 Fehlschlag — *provisional product parameter, not an empirical constant*.

### R1-POL-A04 — Interleaving verwechselbarer Aufgabentypen nach Erstkontakt

- **Zieloperation:** recall/discrimination **der Methodenwahl** innerhalb symbolic procedure (z. B. Summations-, Integrations-, Testverfahren); für rule-based contextual reasoning (Anspruchsgrundlagen, Delikttypen) und diagnostic reasoning nur **Hypothese** (→ R3).
- **Lernkontext:** jeder Typ wurde einzeln eingeführt und mindestens einmal selbstständig gelöst; Wiederholungs-/Prüfungsvorbereitungsphase.
- **Empfehlung:** Erst geblockte Einführung pro Typ, dann gemischte Übungssätze, die die Typwahl erzwingen; Lösungen gesammelt am Satzende (Rohrer) bzw. verzögert; mindestens ein Item, für das keine der geübten Methoden passt.
- **Abstention/Fallback:** Kein Interleaving vor Erstverständnis eines Typs; kein Mischen unähnlicher, nicht verwechselbarer Inhalte (Wortlisten: R0-D5 negativ) – dort geblockt.
- **Evidenzkanten:** `rohrer2020interleaved` Abstract, S.8 (supports, Schule; Spacing-Konfundierung); R0-D5 Brunmair & Richter (supports Mathematik g = 0.34, qualifies Wörter); `ruitenburg2026classroom` Results 3.2.3 (qualifies: Feedback-Moderator, k = 5); `murray2025mathspacing` Diskussion (Interleaving im Kurs-Subset konfundiert).
- **Interne Sicherheit:** **moderat** für Schulmathematik-Strategiewahl; **niedrig** für Hochschulmathematik (Indirektheit); **sehr niedrig** für Recht/Medizin.
- **Beobachtbares:** Fehlerklassifikation „falsche Methode gewählt“ vs. „richtig gewählt, falsch ausgeführt“.
- **Unabhängiges Outcome:** unangekündigter gemischter Test ≥ 2 Wochen später mit neuen Items und Distraktoritem.
- **Schaden/Fehlermodus:** Gefühl geringerer Kompetenz während der Übung (desirable difficulty, KB mc.3) → Abbruch; Mischen zu früh.
- **Falsifikator:** Bei konstant gehaltenen Abständen kein Vorteil gemischter gegenüber geblockter Übung bei der Methodenwahl im verzögerten Test → Wirkung auf Spacing zurückführen, Policy in A05 einschmelzen.
- **Parameter:** ≥ 1 geblockter Satz je Typ, danach gemischte Sätze mit ≥ 3 Typen — *provisional product parameter, not an empirical constant*.

### R1-POL-A05 — Verteiltes, kumulatives Üben statt Massierung unter festem Zeitbudget

- **Zieloperation:** alle Behaltensziele; für symbolic procedure mit Vorbehalt (N6).
- **Lernkontext:** ab Beginn des Kurses bis zur Prüfung; bei kurzer Restzeit verkleinerte Abstände statt Verzicht.
- **Empfehlung:** Bei gleicher Gesamtzeit Übungsgelegenheiten auf mehrere Tage verteilen und frühere Themen kumulativ wiederaufnehmen; Prüfungstermin als Planungsgrundlage; Ausführung durch Anki/kumulative Sätze.
- **Abstention/Fallback:** Keine festen Abstandskonstanten (R0-D4); keine Behauptung, dass Spacing für jede Prozedur wirkt. Wenn Spacing ohne Abruf erfolgt (Unterlagen offen), keinen Spacing-Nutzen unterstellen.
- **Evidenzkanten:** `murray2025mathspacing` VoR-Abstract (supports, Kurs g = 0.24); `ruitenburg2026classroom` Results 3.2.2 (supports vs. massiert 0.39, ISI/RI 0.10–<1: 0.31; qualifies: vs. weniger verteilt n. s.); `ebersbach2020mathspacing` (qualifies, Null für Prozedur); R0-D4 Cepeda 2008 (qualifies).
- **Interne Sicherheit:** **moderat** für „verteilt > massiert“ bei Behalten; **niedrig** für Mathematikprozeduren; **sehr niedrig** für konkrete Intervalle.
- **Beobachtbares:** tatsächlicher Abstand je Item (Tage), Anteil kumulativer Items, ob Abruf ohne Unterlagen erfolgte.
- **Unabhängiges Outcome:** Leistung zum festen Prüfungstermin bzw. verzögerter Test mit unbekannten Items.
- **Schaden/Fehlermodus:** Planungsaufwand; Spacing verdrängt vertiefende Erarbeitung neuer Inhalte; Pseudo-Spacing an aufeinanderfolgenden Kalendertagen ohne Abruf.
- **Falsifikator:** Gleich lange massierte Übung in der letzten Woche ergibt im unassistierten Prüfungstest gleiche oder bessere Leistung innerhalb einer Äquivalenzgrenze.
- **Parameter:** Abstand zwischen Wiederholungen etwa 10–30 % der verbleibenden Zeit bis zur Prüfung — *provisional product parameter, not an empirical constant* (abgeleitet aus Ruitenburgs ISI/RI-Band und R0-D4; Anki-Planung hat Vorrang).

### R1-POL-A06 — Offene, inhaltsbezogene Selbsterklärungsprompts mit Referenzabgleich

- **Zieloperation:** symbolic procedure, Beweisverständnis (nicht Beweiskonstruktion), diagnostic reasoning (Begründung von Fallentscheidungen), computational construction (Code-Tracing).
- **Lernkontext:** beim Studieren von Beispielen, Beweisen, gelösten Fällen; alle Vorwissensstufen, Prompt-Stärke abnehmend mit Kompetenz (Bisra-Diskussion, Hypothese).
- **Empfehlung:** Prompts, die nach Begründung eines konkreten Schritts fragen („Warum ist dieser Schritt zulässig? Welche Voraussetzung wird genutzt?“), offen formuliert; danach Abgleich mit einer Referenzerklärung, die der Lernende erst nach eigener Antwort sieht.
- **Abstention/Fallback:** Keine rein metakognitiven Prompts („Wie gut verstehst du das?“) als Lernintervention; keine MC-„Selbsterklärung“ als Ersatz. Keine automatische Bewertung freier Erklärungen als „korrekt“ ohne validierten Abgleich (KB T9: `UNVERIFIED` bleibt).
- **Evidenzkanten:** `bisra2018` Tab. 1 (supports: .552; Studierende .611), S.16 (qualifies: vs. Instruktionserklärung .354, k = 6), Tab. 2/S.17 (qualifies: metakognitiv/MC n. s.), Publikationsbias S.15 (qualifies: nur Fail-safe-N); `nesbit2006conceptmaps` (context_only).
- **Interne Sicherheit:** **moderat** für „Prompts > keine zusätzliche Erklärung“; **niedrig** für „Prompts > gute Instruktionserklärung“ und für Wirkung bei falschen Erklärungen.
- **Beobachtbares:** Erklärungstext, Zeit, Abdeckung der Referenz-Kernaussagen (nur als Indikator).
- **Unabhängiges Outcome:** verzögerte unassistierte Problemlöse-/Transferaufgaben ohne Prompts.
- **Schaden/Fehlermodus:** Verfestigung falscher Erklärungen; Zeitkosten; Antworten werden aus der Referenz kopiert, wenn diese vorab sichtbar ist.
- **Falsifikator:** Gegenüber zeitgleich gelesener, guter Instruktionserklärung kein Vorteil im verzögerten Transfertest.
- **Parameter:** ein Prompt pro kritischem Schritt, maximal 3 pro Beispiel — *provisional product parameter, not an empirical constant*.

### R1-POL-A07 — Problemlösen vor Instruktion nur optional und konsolidiert

- **Zieloperation:** konzeptuelles Verständnis in symbolic procedure / quantitative Modellierung (z. B. warum ein Varianzmaß so definiert ist); **nicht** für reine Prozedurflüssigkeit oder Sicherheitsprozeduren.
- **Lernkontext:** ausreichendes Vorwissen (Voraussetzungstest bestanden), ≥ 2 Wochen bis zur Prüfung, neues Konzept.
- **Empfehlung:** Kurze, zeitlich begrenzte Generierungsaufgabe vor der Erklärung; danach zwingend Konsolidierung, in der eigene Ansätze mit der kanonischen Lösung verglichen werden; Instruktion-zuerst als gleichwertige Standardoption.
- **Abstention/Fallback:** Abstention bei niedrigem Vorwissen + hoher Elementinteraktivität, kurz vor der Prüfung und bei selbstgesteuertem Lernen ohne Konsolidierung → Instruktion zuerst (A02).
- **Evidenzkanten:** `sinha2021` Abstract (qualifies: g = 0.36; Treue-Moderator; I-PS für Klasse 2–5; biasadjustiert 0.87 methodisch ungeklärt); `ashman2020sequence` (qualifies: Instruktion zuerst bei hoher EI, Klasse 5); `kapur2023prior` (context_only: korrelativ); KB pf.2 / `kirschner2006` (qualifies).
- **Interne Sicherheit:** **niedrig** (Volltext der Haupt-MA ungelesen; Allegiance; Populationsindirektheit; widersprüchliche randomisierte Einzelstudien).
- **Beobachtbares:** Anzahl/Vielfalt generierter Ansätze, Zeit, ob Konsolidierung absolviert wurde.
- **Unabhängiges Outcome:** verzögerte konzeptuelle und Transferitems im randomisierten Vergleich PS-I vs. I-PS bei gleicher Zeit.
- **Schaden/Fehlermodus:** Frustration/Abbruch, Zeitverlust, fehlerhafte Eigenansätze bleiben ohne Konsolidierung hängen.
- **Falsifikator:** Kein Vorteil oder Nachteil von PS-I gegenüber I-PS bei Studierenden mit gemessenem Vorwissen auf verzögerten konzeptuellen Items.
- **Parameter:** Generierungsphase ≤ 15 min — *provisional product parameter, not an empirical constant* (bestehende Spec nennt ≤ 5 min, ebenfalls nur Setzung, R0 T5).

### R1-POL-A08 — Korrektives Feedback nach jedem Versuch; Schritthilfen erst nach eigenem Versuch, Hilfeabhängigkeit messen

- **Zieloperation:** alle; Schrittebene vor allem symbolic procedure und computational construction.
- **Lernkontext:** Übungsphase mit Rückmeldung.
- **Empfehlung:** Nach jedem Abruf- oder Lösungsversuch korrigierende Information (richtige Antwort plus kurze Begründung); bei mehrschrittigen Aufgaben Fehler markieren, gestufte Hinweise erst nach eigenem Versuch; Hilfeabrufe protokollieren und in der Bewertung „mit Hilfe gelöst“ getrennt ausweisen. Keine eigene Timing-Regel auf Aufgabenebene.
- **Abstention/Fallback:** Keine Behauptung, sofortiges Feedback sei generell überlegen (N4). Keine Fehlerursachen-Diagnose aus gleichem Endergebnis (R0 T10). Lösung auf Wunsch zugänglich, aber als Hilfe gekennzeichnet.
- **Evidenzkanten:** `yang2021classroom` S.18 (supports: .537 vs. .374, Moderator); R0-D7/D8 (qualifies: Feedback kann schaden, Designunterschiede); `fyfe2021manyclasses` (qualifies: Timing ≈ 0); `ruitenburg2026classroom` 3.2.3 (qualifies: verzögertes Feedback bei Interleaving); KB its.4/its.5 (context: Schrittfeedback; Hilfesuch-Feedback verbesserte Hilfesuche, nicht Lernergebnis – nicht neu gelesen).
- **Interne Sicherheit:** **moderat** für „Korrektur nach Abruf“; **niedrig** für Schrittfeedback-Details; **sehr niedrig** für konkrete Hinweisleitern.
- **Beobachtbares:** Hinweisstufe je Schritt, Zeit bis zum ersten Hinweis, Anteil „bottom-out“ bis zur Lösung, Wiederholungsfehler.
- **Unabhängiges Outcome:** unassistierte Leistung an neuen Items **ohne** Hinweise; separat: Anteil Lernender, die ohne Hilfe nicht mehr starten (Abhängigkeit).
- **Schaden/Fehlermodus:** Hilfemissbrauch, Offloading (R0-D10), Feedback auf Personenebene (KB fb.4).
- **Falsifikator:** Gruppen mit gestuften Hinweisen zeigen im unassistierten verzögerten Test keine bessere oder schlechtere Leistung als Gruppen mit nur „richtig/falsch + Lösung“.
- **Parameter:** max. 3 Hinweisstufen vor Lösung (bestehende Spec) — *provisional product parameter, not an empirical constant*.

### R1-POL-A09 — Konfidenz und JOLs als Daten, nicht als Lernintervention

- **Zieloperation:** Selbstregulation über alle Operationen (Planungsunterstützung), getrennt nach Operation.
- **Lernkontext:** nach Abruf-/Lösungsversuchen; nicht bei jedem Trial.
- **Empfehlung:** Konfidenz **retrospektiv** nach einer Antwort oder als **verzögertes** Urteil erheben; Kalibrierung gegen externe Standards (tatsächliche Ergebnisse) sichtbar machen; Urteile nur stichprobenartig abfragen und Reaktivität in Evaluationen kontrollieren; nahe und Transferitems getrennt kalibrieren.
- **Abstention/Fallback:** Keine Behauptung, Kalibrierungstraining verbessere Prüfungsleistung (keine Evidenz gefunden). Keine Konfidenzabfrage nach jedem Abrufitem in Lernmodi, deren Wirkung gemessen wird (N5). Keine Timing-Manipulation von Urteilen als Intervention (N10).
- **Evidenzkanten:** `rhodes2011delayedjol` Abstract (supports: relative Genauigkeit g = 0.93 für verzögerte JOLs); `janssen2024monitoring` Results (supports Genauigkeit g = 0.25; qualifies: Timing negativ, Klasse < Labor, keine Leistungsanalyse); `higham2023reactivity` (qualifies); `double2018reactivity` (context_only); KB mc.1/mc.2 (context).
- **Interne Sicherheit:** **moderat**, dass verzögerte/retrospektive Urteile genauer sind (Wortmaterial); **niedrig** für Problemlösen; **sehr niedrig** für Leistungsnutzen von Kalibrierungsanzeigen.
- **Beobachtbares:** Konfidenz vs. Ergebnis (Brier-Score, Kalibrierungskurve) pro Operation.
- **Unabhängiges Outcome:** (a) Kalibrierung an unbekannten verzögerten Items; (b) Prüfungsleistung im randomisierten Vergleich mit/ohne Kalibrierungsanzeige.
- **Schaden/Fehlermodus:** Reaktivität (Urteile verändern Lernen); Überschätzung auf Transferitems trotz guter Kalibrierung auf nahen Items; Demotivation.
- **Falsifikator:** Kalibrierungsanzeige verbessert weder Kalibrierung an neuen Items noch Studienentscheidungen (z. B. Wiederholung schwacher Themen) gegenüber Kontrolle.
- **Parameter:** Kalibrierungsanzeige erst ab ≥ 20 Urteilen pro Operation; Konfidenz 0–100 — *provisional product parameter, not an empirical constant*.

### R1-POL-A10 — Fallvergleich mit nachgelagertem Prinzip für Strukturtransfer

- **Zieloperation:** discrimination auf Strukturebene; symbolic procedure (Erkennen verborgener Struktur), rule-based contextual reasoning und diagnostic reasoning nur als **Hypothese**.
- **Lernkontext:** nach Erwerb der Einzelverfahren; vor Prüfungen mit neuen Oberflächen.
- **Empfehlung:** Paare strukturgleicher, oberflächenverschiedener Fälle vergleichen lassen („Was ist gemeinsam?“), danach das Prinzip explizit nennen, plus ein Kontrastfall, der oberflächlich ähnlich, strukturell verschieden ist.
- **Abstention/Fallback:** Keine Ferntransfer-Behauptung; kein Transferanspruch ohne verzögerten Test an neuen Oberflächen.
- **Evidenzkanten:** `alfieri2013comparison` Abstract (supports d = .50; qualifies: Effekte größer bei sofortigem Test, Prinzip nach Vergleich besser); `sala2017fartransfer` (supports Skepsis); KB tr.1 (supports Dimensionierung).
- **Interne Sicherheit:** **niedrig** (Abstract-Ebene; verzögerte Effekte unklar; Populationen gemischt).
- **Beobachtbares:** Benennung des Prinzips, Klassifikation neuer Fälle nach Struktur.
- **Unabhängiges Outcome:** verzögerter unassistierter Test mit strukturell gleichen, oberflächlich neuen Aufgaben **und** oberflächlich ähnlichen, strukturell verschiedenen Kontrastfällen.
- **Schaden/Fehlermodus:** Prinzip wird auswendig gelernt statt angewendet; Kontrastfälle verwirren Novizen.
- **Falsifikator:** Gegenüber zeitgleicher zusätzlicher gemischter Übung kein Vorteil auf strukturell neuen Items nach ≥ 1 Woche.
- **Parameter:** 2 strukturgleiche + 1 Kontrastfall pro Prinzip — *provisional product parameter, not an empirical constant*.

### R1-POL-A11 — Pretesting/Vorfragen optional vor neuen Inhalten

- **Zieloperation:** recall/discrimination neuer Inhalte vor Vorlesung/Text/Video.
- **Lernkontext:** begleitete Lernsituation mit unmittelbar folgender Erklärung.
- **Empfehlung:** Wenige Vorfragen vor dem Studium neuer Inhalte, mit nachfolgender Gelegenheit zur korrekten Antwort; ausdrücklich als „noch nicht gelernt – Raten erlaubt“ gerahmt.
- **Abstention/Fallback:** Nicht in selbstgesteuerten Kontexten mit Abbruchrisiko ohne Monitoring (N11); nicht als Diagnose verwenden; nicht für Inferenz-/Transferziele beanspruchen.
- **Evidenzkanten:** `pan2023pretesting` (supports für vorgetestete Inhalte; qualifies: ungetestete gemischt, Inferenztransfer oft null, MOOC-Abbruch); KB pr.1 (context).
- **Interne Sicherheit:** **niedrig** (narrativer Review, teils nicht randomisierte Klassenstudien, Mathematik nicht gesehen).
- **Beobachtbares:** Vorfragenantworten, Fortsetzung/Abbruch nach Vorfragen.
- **Unabhängiges Outcome:** verzögerter Test auf vorgetestete und nicht vorgetestete Inhalte; Verbleibsrate.
- **Schaden/Fehlermodus:** Demotivation, Abbruch, falsche Antworten werden ohne Korrektur behalten.
- **Falsifikator:** Kein Vorteil für vorgetestete Inhalte bei gleicher Zeit oder erhöhter Abbruch.
- **Parameter:** ≤ 3 Vorfragen pro Lerneinheit — *provisional product parameter, not an empirical constant*.

### 5.12 Vorgeschlagene Korrekturen an KB-Claims (nicht angewendet)

| Claim | Problem | Vorschlag |
|---|---|---|
| rp.3 | „Testen erzeugt übertragbares Lernen“ ohne Operationsgrenze | ergänzen: kein Testeffekt für Problemlösen aus Worked Examples in der Erwerbsphase (`vangog2015testingwe`); Mathematik Testen vs. Restudy nicht robust (`murray2025mathspacing`) |
| rp.4 | „wirksamer als … alle anderen Vergleichsbedingungen“ | überzogen: Klassenraum vs. Restudy g = .330; 57 % mittlere/große Effekte (Agarwal); Nullbefund bei fortgeschrittenem Text (Redifer) |
| sp.1/sp.2 | Allgemeingültigkeit | Mathematikkurse kleiner (g = 0.24); Prozedur-Null (Ebersbach); Prozentwerte bleiben nach R0-D4 keine Konstanten |
| sp.4 | metadata_only | Abstract-Beleg Higham 2022 (Hochschulkurs, Abruf-Outcome) ergänzen; Anwendung/Transfer offen |
| il.2 | metadata_only, Mechanismus „weil Methodenwahl geübt wird“ kausal formuliert | Rohrer 2020 (RCT, d = 0.83) als Beleg; Mechanismus als Hypothese mit Spacing-Konfundierung |
| we.5 | Effektgröße unbekannt | weiterhin unverifiziert; keine Zahl aus Snippets übernehmen |
| se.1 | metadata_only | g = .55 [.45; .65], aber .35 vs. Instruktionserklärung (k = 6); metakognitive/MC-Prompts n. s.; Bias nur Fail-safe-N |
| pf.1 | Volltext offen | biasadjustierte 0.87 erwähnen und als methodisch zu prüfen markieren; Ashman 2020 als Gegenbefund für junge Lernende |
| fb.3 | „zeitnah“ als allgemeine Regel | auf Aufgabenebene keine generalisierbare Timing-Wirkung (ManyClasses 1) |
| mc.* | Reaktivität fehlt | neuer Claim-Vorschlag: Urteile während des Lernens können Lernergebnisse verändern (Higham 2023; Double 2018 ungelesen) |
| cl.1/cl.2 | Messung | de Jong 2010: Belastung häufig nicht unabhängig gemessen; Mechanismusclaims als theoretisch kennzeichnen |
| tr.1 | — | Sala & Gobet 2017 und Alfieri 2013 als stützende/qualifizierende Kanten ergänzen |

## 6. Fälle mit synthetischem Material

Beide Fälle verwenden selbst erstelltes Material, kein Vorlesungsmaterial. Alle Summenformeln wurden mit exakter rationaler Arithmetik für n = 1…8 (bzw. drei Werte von q, n = 0…6) nachgerechnet; das ersetzt keinen allgemeinen Beweis.

### 6.1 Ausgearbeiteter Lernfall: Summen in geschlossener Form

**Lernende Person (synthetisch):** zweites Semester, zehn Tage bis zur Klausur, kennt die geometrische Summenformel, hat Partialbruchzerlegung nie selbst durchgeführt. Zielkompetenz: drei verwechselbare Verfahren erkennen und ausführen.

- Typ G (geometrisch): Σ_{k=0}^{n} q^k = (q^{n+1} − 1)/(q − 1) für q ≠ 1; für q = 1 ist die Summe n + 1.
- Typ T (Teleskop sichtbar): Σ_{k=1}^{n} (a_k − a_{k+1}) = a_1 − a_{n+1}.
- Typ P (Partialbruch, dann Teleskop): 1/(k(k+1)) = 1/k − 1/(k+1), also Σ_{k=1}^{n} 1/(k(k+1)) = n/(n+1) (n = 5: 5/6).

| Schritt | Policy | Was das System tut | Beobachtbares | Entscheidung |
|---|---|---|---|---|
| 1. Eingangsprobe | A03 (sehr niedrige Sicherheit) | je ein unbekanntes Item pro Typ, nur erster Schritt | G korrekt; T korrekt; bei P kein Ansatz | Einstufung nur als Startpunkt, reversibel: G/T → Übung; P → Beispielphase |
| 2. Beispielphase P | A02, A06 | zwei Worked Examples mit Oberflächenvariation (1/(k(k+1)), 2/((k+1)(k+2))); Prompt: „Warum gilt 1/k − 1/(k+1) = 1/(k(k+1))? Prüfe über den Hauptnenner.“ Referenzerklärung erst nach eigener Antwort | Erklärungstext, Abgleich mit Kernaussage „gleicher Nenner, Zähler (k+1) − k = 1“ | Kernaussage fehlt → zweites Beispiel mit gezieltem Prompt |
| 3. Completion → selbstständig | A02, A08 | letzte zwei Schritte ausgeblendet, dann ein unbekanntes Isomorph ohne Hilfe; Fehler markiert, Hinweise erst nach Versuch | Lösung ohne Hinweis ja/nein; Hinweisstufe | erstes unassistiertes Isomorph gelöst → Übergang zu Übung |
| 4. Gemischte Sätze | A04, A08 | ab Tag 3 Sätze mit G, T, P und einem Distraktor Σ_{k=1}^{n} 1/k² (keine geschlossene Form mit diesen Mitteln); Lösungen am Satzende | Fehlerart: falsche Methodenwahl vs. Ausführungsfehler; Distraktor korrekt als „nicht anwendbar“ erkannt | Wahlfehler bei P/T-Unterscheidung → ein weiterer gemischter Satz zwei Tage später |
| 5. Abrufkarten nur für Abrufbares | A01, A05 | Karten: geometrische Formel **mit** Bedingung q ≠ 1 und Fall q = 1; Ansatz A/k + B/(k+1) für verschiedene lineare Faktoren; Erkennungsfrage „Wann ist eine Summe teleskopierend?“ Successive Relearning über Tag 2, 5, 8 | Versuche bis Kriterium je Sitzung | keine Karten für vollständige Lösungsketten |
| 6. Konfidenz | A09 | retrospektive Konfidenz nur nach jedem dritten gemischten Item | Kalibrierung getrennt für G/T/P | Überschätzung bei P → mehr gemischte P-Items, keine Leistungsbehauptung |
| 7. Unabhängiges Outcome | — | Tag 9, unangekündigt, ohne Hilfen, neue Items inkl. Σ_{k=1}^{n} 1/(k(k+2)) = 3/4 − (2n+3)/(2(n+1)(n+2)) (n = 5: 25/42), das einen Faktor 1/2 und ein Teleskop mit Abstand 2 verlangt | Lösung, Bewertung nach vorab festgelegter Rubrik | Ergebnis ist eine Messung für diese Person, **kein** Wirksamkeitsnachweis der Policies |

Was dieser Fall zeigt: Die Policies erzeugen eine nachvollziehbare Folge von Entscheidungen mit benannten Beobachtungen. Was er nicht zeigt: dass diese Folge besser ist als eine andere; das verlangt einen Vergleich (Abschnitt 8, G-Liste).

### 6.2 Harter Gegen- und Transferfall: alle Indikatoren grün, Prüfungsaufgabe scheitert

Dieselbe Person hat am Tag 9 alle G/T/P-Items gelöst, die Karten nach Kriterium gelernt und ist auf gemischten Sätzen gut kalibriert. In der Klausur steht:

> Zeige: Σ_{k=1}^{n} k/(k+1)! = 1 − 1/(n+1)!  (n = 5: 719/720)

Die Lösung verlangt, die verborgene Teleskopstruktur durch Umschreiben zu sehen: k = (k+1) − 1, also k/(k+1)! = 1/k! − 1/(k+1)!. Die Person scheitert, weil ihre Typerkennung an einer Oberflächenregel hing („Produkt linearer Faktoren im Nenner → Partialbruch“); hier gibt es keinen solchen Nenner. Eine zweite Variante des Scheiterns: Eine andere Person mit niedrigem Vorwissen hatte früh Karten zum Partialbruch-Ansatz bekommen und konnte „A/k + B/(k+1)“ fehlerfrei abrufen, aber A und B für k(k+2) nicht bestimmen – Abruf hatte das fehlende Verfahrensschema verdeckt (Muster von N1).

| Befund im Fall | Was die Policies daraus folgern müssen |
|---|---|
| Hohe Abruf- und gemischte Satzleistung, Scheitern an neuer Oberfläche | A01/A04-Indikatoren sind **nahe** Leistung; keine Mastery- oder Prüfungsreife-Aussage ohne strukturell variierte unassistierte Items (A10-Outcome). |
| Gute Kalibrierung auf nahen Items | Kalibrierung gilt nicht für Transferitems; A09 verlangt getrennte Kalibrierung nach Itemtyp. |
| Früher Abruf eines Ansatzes ohne Verfahren | A02-Abstention war verletzt: Abruf vor Schema; Rückgang zu Beispielen und Completion. |
| Verborgene Struktur nicht erkannt | A10: Vergleich „Teleskop sichtbar“ (1/k − 1/(k+1)) mit „Teleskop nach Umschreiben“ (k/(k+1)!) und Kontrastfall Σ 1/k² (kein Teleskop), Prinzip **nach** dem Vergleich: „Schreibe den Summanden als Differenz aufeinanderfolgender Terme einer Folge“. |

**Falsifikator für die Reaktion:** Wenn Lernende mit A10-Vergleich auf strukturell neuen, verzögert und unassistiert gestellten Items nicht besser abschneiden als Lernende mit zeitgleicher zusätzlicher gemischter Übung, ist A10 für diese Operation zu streichen. Der Fall zeigt außerdem, dass Induktion ein alternativer, legitimer Lösungsweg ist; eine Rubrik, die nur den Teleskopweg akzeptiert, wäre ein Validitätsfehler.

## 7. Übertragbarkeit über Domänen und NOT_APPLICABLE-Entscheidungen

### 7.1 Übertragungsbedingungen je Lernoperation

| Lernoperation | Übertragbar mit Evidenz | Nur Hypothese (Prüfung nötig) | Zuständig |
|---|---|---|---|
| recall/discrimination (alle Fächer) | A01, A05, A11 für Kursinhalte (Yang Hochschule; Higham Kurs) | Formatwahl nach Zieloperation (R0-D2) | R1A |
| symbolic procedure (Mathe, Statistik, Wirtschaft, Finanzen) | A02 (Erwerbsphase), A04 (Schulmathe), A05 mit Vorbehalt | A03, A06 in Hochschulmathematik; A07 | R1A/R2 |
| formal proof (Analysis, theoretische Informatik) | Abruf von Definitionen/Satzaussagen als Baustein (A01); Selbsterklärung beim **Lesen** von Beweisen (A06, indirekt) | Beweiskonstruktion durch irgendeine R1A-Policy | R2 |
| rule-based contextual reasoning (Recht, Steuern) | Abruf von Tatbestandsmerkmalen (A01) | Interleaving von Anspruchsgrundlagen/Fallgruppen (A04), Fallvergleich (A10) – Textbefunde nach R0-D5 uneindeutig; Rechtsstand datiert | R3 |
| diagnostic reasoning (Medizin, Debugging) | Selbsterklärung schließt medizinische Diagnoseaufgaben ein (Bisra, Tab. 6 Kodierbeispiel) | Fallvergleich, Interleaving von Differentialdiagnosen, Kalibrierung diagnostischer Konfidenz | R3/R2 |
| computational construction (Programmieren) | Worked Examples/Selbsterklärung beim Code-Lesen (indirekt) | Parsons-Aufgaben, Debugging-Interventionen | R2 |
| open-ended synthesis | — | — | R2/R3/R6 |
| perceptual/psychomotor | — | — | R4 |
| self-regulation | A09 (Messung) | Kalibrierung als Leistungsintervention | R1A/R1B |

Allgemeine Übertragungsbedingungen: (1) gleiche Zieloperation, nicht gleicher Fachname; (2) Outcome verzögert, unassistiert, mit neuen Items; (3) Population mit vergleichbarem Vorwissen; (4) Mechanismus im Produkt tatsächlich ausgelöst (Abruf ohne offene Unterlagen, Typwahl tatsächlich nötig, Erklärung tatsächlich generiert).

### 7.2 Ausdrückliche NOT_APPLICABLE-Entscheidungen

| ID | Entscheidung | Begründung |
|---|---|---|
| NA-1 | Abruf/Successive Relearning **nicht** als Hauptmethode für Beweiskonstruktion, offene Synthese oder psychomotorische Fertigkeiten | keine Evidenz in R1A; N1/N3 zeigen schon für Prozeduren/Konzepte Grenzen |
| NA-2 | Interleaving **nicht** für unverbundene, nicht verwechselbare Itemlisten | R0-D5: Wortmaterial negativ; dort geblockt |
| NA-3 | PS-I/PF **nicht** für Novizen ohne Voraussetzungen kurz vor der Prüfung und **nicht** für sicherheitskritische Prozeduren | N8; Sinha: I-PS für junge Lernende; Sicherheit (R3/R4) |
| NA-4 | Keine Policy dieses Berichts begründet juristische, klinische oder berufliche Kompetenzaussagen | Simulierte Fallleistung ≠ Berufskompetenz (Charter R3) |
| NA-5 | Kalibrierungstraining **nicht** als Prüfungsleistungs-Intervention | keine Leistungsevidenz gefunden (Janssen: nur Genauigkeit) |
| NA-6 | Keine Feedback-Timing-Regel auf Aufgabenebene | N4 (ManyClasses 1) |
| NA-7 | Keine neurobiologischen Mechanismusbehauptungen | R1A hat nur Verhaltensevidenz geprüft |
| NA-8 | Schlaf, Fatigue, Motivation, Stress, Bewegung, Lernintensität | Zuständigkeit R1B |

### 7.3 Technologiebezug (Hinweis an R5/R8, keine Empfehlung)

R1A schlägt keine Technologie vor. Die Policies setzen nur voraus: Versuchs-Logs mit Hilfestatus, tatsächliche Zeitabstände je Item, Item-Metadaten zu Operation und Strukturvariante, stichprobenartige Konfidenzerfassung und unangekündigte unassistierte Testitems. Anki bleibt einziger Scheduler (R0, Produktvertrag); kein eigener Planer aus A05-Parametern. Ob eine Browser-/PDF-/Anki-Umgebung „Abruf ohne Unterlagen“ überhaupt sicherstellen kann, ist offen (Murray: 53 % der Kurs-Effekte ohne gesicherten Abruf) und gehört zu R5.

## 8. Priorisierte Lücken und „Was wir nicht behaupten können“

### 8.1 Lückenliste

| Rang | Lücke | Warum entscheidungsrelevant | Nächster Schritt |
|---|---|---|---|
| G1 | Sinha & Kapur 2021 Volltext (Methode der biasadjustierten 0.87; Outcome-Moderatoren; Hochschul-Subset) | A07 hängt daran; R0 und R1A scheiterten (Sage 403, ETH restricted) | Bibliothekszugang oder Autorenkopie; zweite Person extrahiert |
| G2 | Barbieri et al. 2023 Volltext (Fading, Selbsterklärungsprompts, Vorwissen) | A02/A03/A06; we.5 seit R0 offen | dto. |
| G3 | Ruitenburg et al. 2026 Tabelle 1 inkl. Fach-Moderator; Verifikation der modellbasiert extrahierten Zahlen | N3 ist zentraler Gegenbefund | Originaltabelle lesen, Zahlen gegenprüfen |
| G4 | Kalyuga & Sweller 2004 Volltext; Renkl-Primärstudien zu Fading | A03 ist sehr niedrig gesichert | Fehlklassifikationsraten, Stichproben, adaptive Effekte extrahieren |
| G5 | Karpicke & Aue 2015, Rawson 2015, Agarwal 2021 Volltext | Gegenposition zur Komplexitätsgrenze nur als Titel | Argumente und ausgelassene Studien prüfen |
| G6 | Hilfesuche/Hilfemissbrauch (Aleven-Primärstudien, „gaming the system“) | A08-Hinweisleitern; R5-Abhängigkeitsmessung | an R5 übergeben |
| G7 | Kalibrierung → Leistung: Gutierrez de Blume 2022, Double et al. 2018 Volltexte | A09, NA-5 | Leistungsoutcomes extrahieren |
| G8 | Interleaving/Fallvergleich in Recht und Medizin auf Hochschulniveau | A04/A10 dort nur Hypothese | an R3 |
| G9 | Fiorella & Mayer 2016, Elaborative Interrogation, Schroeder et al. 2018 (Concept Maps) | se.2 bleibt metadata_only | gezielte Lektüre |
| G10 | Successive Relearning mit Anwendungs-/Transferoutcomes in MINT (Higham 2022 Volltext; Rawson/Dunlosky-Kursstudien) | A01-Geltung jenseits Abruf | Volltexte |
| G11 | Pretesting bei mathematischem Problemlösen (Pan & Carpenter, restliche Abschnitte; Pan & Sana 2021) | A11 | Lektüre |
| G12 | Versionsabgleich der Drittanbieter-Spiegel (Yang, Rohrer, Bisra) mit Version of Record | Seitenangaben/Zahlen | VoR-Abgleich |
| G13 | Eigenes Prüfdesign: randomisierte Within-Learner-Vergleiche für A01, A02, A04, A10 mit verzögertem unassistiertem Outcome | einzige Möglichkeit, Exam-Mastery-Wirksamkeit zu prüfen | an R5/R6 (Evaluationsprotokoll), NOT_RUN |

### 8.2 Was wir nicht behaupten können

- **Keine Wirksamkeit von Exam Mastery.** Keine Policy wurde implementiert oder an Lernenden getestet; alle sind `design_hypothesis`.
- **Keine systematische Vollständigkeit.** 31 Quellen nach gezielter Scoping-Suche, keine lizenzierten Datenbanken, kein PRISMA-Flussdiagramm, keine RoB-2-/AMSTAR-2-Bewertung.
- **Keine unabhängige Prüfung.** Ein Agent hat gesucht, extrahiert und bewertet; Sicherheitslabels sind interne Einschätzungen.
- **Keine Verallgemeinerung von Schul- auf Hochschulbefunde** ohne Abwertung: Ruitenburg (Klasse 1–12) und Rohrer (Klasse 7) sind indirekt.
- **Kein Beleg, dass Abruf komplexe Problemlöse-, Beweis- oder Transferkompetenz aufbaut**; ebenso wenig ein Beleg, dass er dies nie tut – die Evidenz ist gemischt und unpräzise.
- **Kein validierter Umschaltpunkt** zwischen Beispielen und Problemlösen, keine validierte Ein-Item-Expertisediagnose.
- **Keine gesicherte Überlegenheit von Productive Failure** für Studierende; keine gesicherte Unterlegenheit.
- **Kein Beleg, dass Kalibrierungsanzeigen oder Konfidenzabfragen Prüfungsleistung verbessern**; Hinweise, dass Urteile Lernen verändern können.
- **Keine allgemeine Feedback-Timing-Regel.**
- **Keine Zahl in diesem Bericht ist eine empirische Konstante für Planungsalgorithmen**; alle Produktparameter sind ausdrücklich vorläufig.
- **Keine neurowissenschaftliche Begründung**; „Mechanismus“ bedeutet hier verhaltensbezogene Erklärungshypothese.
- Modellbasiert zusammengefasste Volltexte (Ruitenburg, Pan & Carpenter, Janssen & Lazonder, Kapur 2023, Ebersbach) und Drittanbieter-Spiegel sind **vor KB-Übernahme gegenzuprüfen**.
