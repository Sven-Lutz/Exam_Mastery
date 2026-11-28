# R9 — Vergleich der Tutoring-Ressourcen

Version 0.1, 27.11.2026. **Forschungsbericht, nicht unabhängig begutachtet.** [Issue #31](https://github.com/Sven-Lutz/Exam_Mastery/issues/31) · Brief [TUTORING_RESOURCE_REGISTRY_20261126.md](../TUTORING_RESOURCE_REGISTRY_20261126.md) · Ressourcenkarten [r9/r9_resources.json](r9/r9_resources.json) · Evidenzregister [r9/r9_evidence.json](r9/r9_evidence.json) · Policies [r9/r9_tutor_policies.json](r9/r9_tutor_policies.json). Ergänzt R5 (Tutoring-Forschung) und R7 (weitere Ressourcen), ersetzt sie nicht.

Kennzeichnung: **Fakt** = aus Primärseite, Repository-API, Code oder gelesenem Abstract/Volltext belegt (mit Zugriffsdatum 27.11.2026); **Hypothese** = Erwartung, ungeprüft; **Designentscheidung** = gesetzte Regel; **Nicht belegt** = Behauptung ohne gelesene Evidenz (oft Herstellerangabe).

## 1. Methode und Grenzen

- **Fakt:** Identität jeder Ressource über die GitHub-API (`gh api repos/<owner>/<repo>`, README, LICENSE, letzter Commit, Release) bzw. genau einen Abruf der offiziellen Herstellerseite; wissenschaftliche Quellen über arXiv-API, Crossref, Semantic Scholar, NBER-Seiten (Suchjournal S01–S11 im Register).
- **Fakt:** Nichts wurde installiert, geklont, ausgeführt; keine Konten, keine bezahlten Aufrufe. „Getestete Workflows“ gibt es deshalb **keine**; jede Karte trägt `tested_workflow: NOT_RUN`. Kosten, Latenz und Offline-Aufwand sind dokumentiert, nicht gemessen.
- Jede Behauptung einer Ressource ist klassifiziert: `marketing`, `documented_function`, `benchmark`, `learning_outcome`. Nur `learning_outcome` aus einer identifizierten Studie darf eine Lernwirkung stützen (in den Tests erzwungen).
- Zugriff auf Literatur: 1 Volltext teilweise (TutorBench-HTML, werkzeugzusammengefasst), 17 Abstracts. Keine Datenbanksuche (ERIC/PsycINFO) — das ist eine Lücke.

## 2. Inventar

| Ressource | Identität (Zugriff 27.11.2026) | Lizenz | Kategorie | höchste vorhandene Evidenz | Entscheidung |
|---|---|---|---|---|---|
| DeepTutor | github.com/HKUDS/DeepTutor, v1.7.4 (20.11.2026), Tech-Report arXiv 2604.26962 | Apache-2.0 | Open-Source-Tutor | Benchmark (eigener, simulierte Lernende) | emulate |
| OATutor | github.com/CAHLR/OATutor, v1.7, CHI 2023 | MIT; Inhalte CC BY 4.0 | Open-Source-ITS | Lernergebnis (pardos2024chatgpthints, R5) | emulate |
| LMU SMART-RAG | github.com/digillab-lmu/smart-rag, v0.3.0 | PolyForm Noncommercial 1.0.0 | Open-Source-Tutor (Server) | dokumentierte Funktion | emulate |
| TutorBench | labs.scale.com/leaderboard/tutorbench, arXiv 2510.02663 | Stichprobe CC BY-NC 4.0; Rest unveröffentlicht | Benchmark | Benchmark | emulate (Rubrikdesign) |
| MathTutorBench | github.com/eth-lre/mathtutorbench, EMNLP 2025 | keine erkannt | Benchmark | Benchmark | defer |
| OpenTutor | github.com/zijinz456/OpenTutor, Beta | MIT | Open-Source-Tutor (lokal) | dokumentierte Funktion | reject |
| PAIDEIA | github.com/OPTIMETA/PAIDEIA = github.com/TaewoooPark/PAIDEIA, v0.9.27 | MIT | Claude-Code-Plugin | dokumentierte Funktion | emulate |
| Education Agent Skills | github.com/GarethManning/education-agent-skills, v3.1.0 | CC BY-SA 4.0 | Skill-Bibliothek | dokumentierte Funktion | emulate |
| ChatGPT Study Mode | help.openai.com Artikel 11780217 | proprietär | Anbieter-Tutormodus | dokumentierte Funktion | reuse (als Vergleichsarm) |
| ChatGPT Project / portabler Kontext | PR #19 `tutor.py`, `tutor_protocol.md` v0.18 | projektintern | eigener Workflow | dokumentierte Funktion | adapt |
| NotebookLM | notebooklm.google.com → 301 notebook.google.com („Gemini Notebook“) | proprietär | quellgebundener Leser | Designstudie ohne Lernmessung | defer |
| YouLearn | youlearn.ai, YouLearn Inc. | proprietär | Lernplattform | marketing | reject |
| StudyFetch | studyfetch.com, StudyFetch Inc., Tutor „Sparky“ | proprietär | Lernplattform | marketing (Selbstauskunft) | reject |
| Khanmigo | khanmigo.ai, Khan Academy | proprietär | Anbieter-Tutor | Lernergebnis (unabhängige Cluster-RCT, Working Paper) | emulate (Lehren) |
| Math Academy | mathacademy.com/how-our-ai-works | proprietär | adaptives Curriculum | dokumentierte Funktion | defer (an R6/R8) |
| RemNote Guided Learn Mode | remnote.com; „Guided Learn Mode“ nicht gefunden | proprietär | Notizen + SRS | marketing | reject |
| Margin Study | marginstudy.app, v1.4.0, Eigentümer nicht angegeben | proprietär | Lese-/Annotationswerkzeug ohne KI | dokumentierte Funktion | defer (an R7/R8) |
| Utterseen | utterseen.com, FAINETZ CORP | proprietär | Bildschirm-Sprachassistent | marketing | reject |

Verteilung der 72 klassifizierten Behauptungen: 51 `documented_function`, 13 `marketing`, 6 `benchmark`, 2 `learning_outcome`. **Fakt:** Für 16 der 18 Ressourcen liegt kein gemessenes Lernergebnis vor.

## 3. Identitätsklärungen und Korrekturen am Brief

- **PAIDEIA (Fakt):** Beide URLs führen auf **ein** Repository. `gh api repos/TaewoooPark/PAIDEIA` und `repos/OPTIMETA/PAIDEIA` liefern dieselbe Repository-ID 1216957019; `github.com/TaewoooPark/PAIDEIA` antwortet mit HTTP 301 auf `OPTIMETA/PAIDEIA`. Das Repo entstand am 21.04.2026, die Organisation OPTIMETA am 01.06.2026 — konsistent mit einer Übertragung vom Nutzerkonto des Autors Taewoo Park (84 Commits) auf die Organisation. TaewoooPark besitzt zusätzlich Forks (05.09.2026) der OPTIMETA-Varianten für Codex, Hermes, MCP, opencode und „Alt“ (Exam Radar) sowie einen inaktiven Fork „PAIDEIA-1“. Es gibt also keine zwei konkurrierenden Codebasen; zu bewerten ist `OPTIMETA/PAIDEIA` (letzter Commit 11.07.2026).
- **NotebookLM (Fakt):** Die URL leitet auf `notebook.google.com` um, der Hilfeartikel heißt „Learn about Gemini Notebook“. Eine offizielle Umbenennungsmitteilung wurde nicht gelesen.
- **Margin Study (Fakt):** Die Startseite beschreibt einen lokalen PDF-Leser mit Randnotizen, **keinen** KI-Tutor und keinen Bildschirmkontext. Die Brief-Zeile „Margin Study / Utterseen … permissioned screen-context tutor“ vermischt zwei Produkte; Bildschirmkontext betrifft nur Utterseen (ein Screenshot pro Frage an nicht benannte Cloud-Anbieter).
- **RemNote (Fakt):** Auf der Startseite gibt es „AI Tutor Chat“, aber keinen „Guided Learn Mode“; die Funktion bleibt unidentifiziert (`identity_verified: false`).
- **StudyFetch (Fakt):** Der Tutor heißt „Sparky“; zusätzlich „Tutor Me“ und klinisches Roleplay.
- **ChatGPT Study Mode (Fakt):** nicht in Projects, Work oder Custom GPTs verfügbar; kann Memory nutzen; „may give direct answers“.
- **TutorBench (Fakt):** Der DeepTutor-Tech-Report führt einen **eigenen**, ebenfalls „TutorBench“ genannten interaktiven Benchmark ein. Er ist nicht der Scale-Benchmark aus dem Brief.

## 4. Mechanismen (Issue-Liste 1–9)

| Nr. | Mechanismus | wo dokumentiert | Evidenzstand | R9-Folgerung |
|---|---|---|---|---|
| 1 | sokratische Diagnose, Schrittfeedback | OATutor (Schritt-Hinweise/Scaffolds), EAS `stuck-and-error-diagnosis-coach`, Khanmigo, Al-Hossami-Datensatz | **Fakt:** Lösefähigkeit ≠ Unterrichten (macina2025mathtutorbench); manche LLMs eher QA-System als Tutor (maurya2025mrbench). Kein Lernergebnis für sokratisches LLM-Debugging gelesen | R9-POL-03, R9-POL-08 |
| 2 | Quellenbindung, Provenienz, Zeitstatus | SMART-RAG (Quelle aufgezeichnet, Kursfilter), DeepTutor (Zitate, `kb eval`), NotebookLM, OpenTutor, StudyFetch | **Fakt:** 51,5 % voll gestützte Sätze, 74,5 % stützende Zitate in generativer Suche (liu2023verifiability); 17–33 % Halluzination bei RAG-Rechtswerkzeugen (magesh2025legalrag). **Nicht belegt:** dass irgendein inventarisiertes System Entailment, Fassung oder Zeitstatus prüft | R9-POL-01, R9-POL-02 |
| 3 | explizite Hilfepolitik | EAS (retrieve-first, Hinweisleiter 0–5, unassisted checkpoint), PR #19 Protokoll, Study Mode, Khanmigo, Pisan-Supervisor (8 Stufen) | **Fakt:** Leitplanken-Tutor ohne späteren unassistierten Verlust (bastani2025, KB). **Fakt:** EAS-Leiter verbietet die vollständige Lösung auch auf Anforderung — Konflikt mit Nutzerkontrolle | R9-POL-03, R9-POL-09 |
| 4 | Tutor vs. Lab vs. Anki | DeepTutor (Practice mit Review-Datum), OpenTutor (FSRS 4.5), RemNote, Math Academy (FIRe), StudyFetch (Lernplan) | **Fakt:** fünf Ressourcen bringen eigene Wiederholungsplanung mit — Konflikt mit AD-1 | R9-POL-07 |
| 5 | aufgabenspezifisches Tutoring | Debugging: alhossami2024socratic, pisan2026withhold, liu2024cs50; Recht: magesh2025legalrag; Klinik/CAD: nur Herstellerseiten (StudyFetch-Roleplay) | **Nicht belegt:** Lernergebnisse je Domäne | R9-POL-08 |
| 6 | Offloading, Abhängigkeit | EAS `unassisted-evidence-checkpoint`; PAIDEIA `twin`/`blind` | **Fakt:** In-Sitzung-Kriterium ohne verzögerten Gewinn (oreopoulos2026mastery); angeleitete Nutzung mit Muster besserer No-help-Leistung, quasi-experimentell (amanlou2026guided); EEG-Befunde bei LLM-Schreiben sind kleine Stichprobe ohne Lerntest (kosmyna2025brain) | R9-POL-06, R9-POL-09 |
| 7 | Lernstandsintegrität, local-first, Kosten | OATutor (BKT-Defaults), DeepTutor-Memory, SMART-RAG-Lernendenspeicher, PAIDEIA (Markdown lokal), OpenTutor (Ollama) | **Fakt:** OATutor nutzt BKT „exactly identical to wikipedia“ mit Parametern pro KC und Schwelle 0,95; keine Kalibrierung dokumentiert | R9-POL-10 |
| 8 | Baseline direkter Chat, statische Hilfe | — (kein System bietet das) | **Fakt:** Khanmigo-Effekt ≈ KI-freie Übung (oreopoulos2026khanmigo) | R9-POL-06 |
| 9 | Benchmarks und Lücke zum Lernen | TutorBench, MathTutorBench, MRBench, LearnLM, DeepTutor-Benchmark | **Fakt:** alle messen Antwortqualität, keines Lernen | R9-POL-05 |

## 5. Benchmarks im Detail

**TutorBench (Scale), Fakt:** 1.490 expertenerstellte Szenarien (High School/AP; Biologie, Physik, Chemie, Statistik, Analysis, Informatik), drei Aufgaben (adaptive Erklärung, Feedback, Hinweise), 828 multimodal; 15.220 Rubrikkriterien mit +5/+1/−5; Judge Claude Sonnet 4; Judge-Mensch 0,78 vs. Mensch-Mensch 0,75; bestes Modell im Paper 55,65 % (Sec. 1–3, Table 1). Filter: Beispiel behalten, wenn mind. 3 von 5 Frontier-Modellen unter 50 % lagen (App. A.1). Öffentlich: 30 Beispiele, CC BY-NC 4.0; Rest „soon“.
- **Leakage:** Kontamination wird im Paper nicht diskutiert; die öffentliche Stichprobe kann in Trainingsdaten gelangen. Das Leaderboard zeigt inzwischen 27 Modelle mit einem Spitzenwert von 68,55, der Überblickstext noch 16 Modelle/55,7 % — inkonsistent, Rangfolgen sind zeitabhängig.
- **Was er nicht misst (Fakt, Sec. 5):** Mehrzugdialoge, echte Lernende, Lernergebnisse, Humanities; nur finale Antworten auf vorformulierte Gespräche. Damit auch keine Abhängigkeit, keinen verzögerten Transfer.
- **Designentscheidung:** Übernommen wird das Rubrikmuster (fallspezifisch, gewichtet, −5 für unaufgefordertes Lösungsverraten), nicht der Datensatz.

**MathTutorBench, Fakt (Abstract):** Lösefähigkeit und Pädagogik bilden einen Trade-off; längere Dialoge sind schwieriger. Repo ohne erkannte Lizenz → aufgeschoben.

**MRBench, Fakt (Abstract):** 192 Gespräche, 1.596 Antworten, acht Dimensionen; prüft LLMs als Bewerter. **LearnLM, Fakt (Abstract):** Expertenpräferenz +31 % gegenüber GPT-4o — Herstellerbericht, Präferenz, kein Lernen.

**Benchmark → Lernen:** Kein gelesener Benchmark verknüpft seine Werte mit Lernergebnissen. **Fakt:** adak2026tutorsynthesis findet Evidenz für Transfer und verzögertes Behalten besonders dünn. **Designentscheidung (R9-POL-05):** Benchmarkwerte heißen im Projekt immer „Antwortqualität unter Rubrik X“.

## 6. Lernergebnisse, Null- und Gegenbefunde

| Quelle | Design | Befund (Locator) | Bedeutung für R9 |
|---|---|---|---|
| oreopoulos2026khanmigo | 2 Jahre Cluster-RCT, 18 Schulen | +1,3 Perzentilränge/Term, ≈ KI-freie Übung; Nutzung im Fehlerfall 17 % (Abstract) | Tutor-Modus allein bringt wenig; statische Hilfe ist ernsthafte Kontrolle; Nutzung messen |
| oreopoulos2026mastery | RCT, > 6.000, faktoriell | 3-richtig-in-Folge ohne verzögerten Gewinn; KI + Mastery marginal auf geübtem Material (Abstract) | In-Sitzung-Erfolg ist kein Lernstand |
| amanlou2026guided | quasi-experimentell, 3 Bedingungen | angeleitete Nutzung: Muster stärkerer No-help-Quizleistung, Übung ohne Vorteil (Abstract, verhaltensdefiniert) | stützt Leitplanken schwach; Selbstselektion |
| bastani2025 (KB, R0-D10) | RCT | ungeschützter Zugang: Übungsgewinn, späterer Verlust; Leitplanken heben Verlust auf | Kernbeleg für Vertrag |
| kestin2025 (KB, R0-D11) | RCT, Sofortmessung | strukturierter KI-Tutor mit Lerngewinn | kein verzögerter Endpunkt |
| pardos2024chatgpthints (R5) | Experiment in OATutor | LLM-Hinweise ≈ menschliche Hinweise | siehe R5 |
| kosmyna2025brain | Preprint, n = 54/18 | geringere EEG-Konnektivität bei LLM-Schreiben (Abstract) | nur Kontext; kein Lerntest |

**Nicht belegt:** ein Lernergebnis für DeepTutor, SMART-RAG, OpenTutor, PAIDEIA, Education Agent Skills, Study Mode, NotebookLM, YouLearn, StudyFetch, Math Academy, RemNote, Margin Study oder Utterseen. StudyFetchs „92 % … reported grade improvements“ ist eine Selbstauskunft ohne Kontrollgruppe.

## 7. FOSS und Lizenzen

| Ressource | Lizenz | Folge für Übernahme |
|---|---|---|
| DeepTutor | Apache-2.0 | Code nutzbar mit Hinweis; aber Einbettung abgelehnt (Komplexität) |
| OATutor | MIT; Inhalte CC BY 4.0 | Schemaidee frei; Inhalte mit Namensnennung nutzbar |
| SMART-RAG | PolyForm Noncommercial, Pflicht-Namensnennung | kein Code in ein möglicherweise kommerzielles Produkt; nur Ideen |
| PAIDEIA | MIT | frei |
| OpenTutor | MIT | frei, aber abgelehnt |
| Education Agent Skills | CC BY-SA 4.0 | Textübernahme würde Share-alike auslösen → eigene Formulierung |
| TutorBench-Stichprobe | CC BY-NC 4.0 | nur nichtkommerzielle Forschung |
| MathTutorBench | keine erkannt | Nutzung erst nach Klärung |

## 8. Hypothesen, die dieser Vergleich nicht prüfen konnte

- **Hypothese:** DeepTutors `kb eval` (Recall@k gegen Gold-Passagen) ist eine nützliche Vorbedingung für quellgebundenes Tutoring. Ungeprüft, nicht ausgeführt.
- **Hypothese:** SMART-RAGs Kursfilter verhindert kursfremde Antworten; exakte Spans, widersprüchliche Dokumente und Entailment wurden nicht getestet (Issue-#31-Fragen offen).
- **Hypothese:** PAIDEIAs `twin`/`blind` sind gute unassistierte Abschlussformate; Antworten liegen dort nur als Nachbardatei — Trennung per Konvention, nicht per Zugriffskontrolle.
- **Hypothese:** Ein eingefügter Vertrag hält in Chats ähnlich gut wie Study Mode. Prüfung nur über [TUTOR_EVALUATION_PROTOCOL.md](TUTOR_EVALUATION_PROTOCOL.md).

## 9. Reviewfragen

1. Ist die PAIDEIA-Schlussfolgerung (Übertragung statt zweier Codebasen) aus Repo-ID, 301 und Datumsfolge ausreichend, oder ist eine Bestätigung des Autors nötig?
2. Sind die Entscheidungen „emulate“ für Education Agent Skills trotz CC BY-SA und „reuse als Vergleichsarm“ für Study Mode angemessen?
3. Soll Margin Study aus dem R9-Brief in den R7/R8-Brief verschoben werden?
4. Fehlen Systeme mit einem **anderen** Lernmechanismus (z. B. constraint-based modeling, Beweis-Tutoren mit Formalisierung)? R9 hat nicht systematisch danach gesucht.
5. Sind Working Papers auf Abstract-Ebene (NBER 35620/35621) ausreichend, um die Vier-Arm-Evaluation zu begründen?
