# R9 — Übernahmeentscheidung für Tutor-Ressourcen

Version 0.1, 27.11.2026. **Empfehlung zur Begutachtung, keine Freigabe, keine Implementierung.** Policies [r9/r9_tutor_policies.json](r9/r9_tutor_policies.json) (besonders R9-POL-07), Karten [r9/r9_resources.json](r9/r9_resources.json), Vergleich [TUTORING_RESOURCE_COMPARISON.md](TUTORING_RESOURCE_COMPARISON.md), Vertrag [TUTOR_BEHAVIORAL_CONTRACT.md](TUTOR_BEHAVIORAL_CONTRACT.md), Evaluation [TUTOR_EVALUATION_PROTOCOL.md](TUTOR_EVALUATION_PROTOCOL.md). Abstimmung mit R5 (Messung), R7 (weitere Ressourcen), R8 (Anki/Obsidian) und R6 (Architektursynthese) steht aus.

Kennzeichnung: **Fakt** = belegt (Quelle/Code gelesen); **Hypothese** = ungeprüfte Erwartung; **Designentscheidung** = Empfehlung mit Begründung; **Nicht belegt** = Behauptung ohne Evidenz.

## 1. Grundsatz

**Designentscheidung (R9-POL-07):** Kein externes Tutor-System wird eingebettet. Einzelne Mechanismen werden emuliert, je mit Herkunft, Lizenzprüfung, Abbildung auf einen vorhandenen Engine-Vertrag und eigenem Falsifikator. Begründung:
- **Fakt:** Fünf Ressourcen bringen eine eigene Wiederholungsplanung mit (DeepTutor Practice, OpenTutor FSRS 4.5, RemNote, Math Academy FIRe, StudyFetch-Lernplan) — Konflikt mit AD-1 (Anki/FSRS einziger Scheduler, SP-R1).
- **Fakt:** Mehrere führen Mastery-Schätzungen ohne dokumentierte Kalibrierung ein (OATutor BKT-Schwelle 0,95, DeepTutor „hard per-type mastery gate“) — Konflikt mit ITS-R1 und R5-POL-01/02.
- **Fakt:** Für 16 von 18 Ressourcen liegt kein gemessenes Lernergebnis vor; für die zwei anderen (OATutor, Khanmigo) betreffen die Ergebnisse Schulmathematik.
- **Hypothese:** Die wirksamen Bestandteile guter Tutoren liegen in der Hilfepolitik und der Messung unassistierter Leistung, nicht in Plattformbreite. Gestützt nur indirekt (bastani2025; oreopoulos2026khanmigo: Tutor ≈ KI-freie Übung).

## 2. Entscheidung je Ressource

| Ressource | Entscheidung | übernommen wird | ausdrücklich nicht | Opportunitätskosten |
|---|---|---|---|---|
| DeepTutor | emulate | Retrieval-Gold-Set mit Recall@k vor Quellenfreigabe (`kb eval`-Idee); getrennte Kontextarten | Agenten-Laufzeit, Memory, Practice-Scheduler, Mastery-Gate | Einbettung: Wochen Integration in einen schnell wechselnden ~200k-Zeilen-Stack; Emulation: zwei Felder/ein Skript |
| OATutor | emulate | Schritt-Hilfe mit Unterscheidung Hinweis vs. Scaffold; deterministische Variantenzuteilung für Evaluation | BKT-Steuerung, React/Firebase-Stack | Stack würde em_tutor.js duplizieren; CC-BY-Inhalte bleiben als spätere Testfallquelle |
| LMU SMART-RAG | emulate | Kursfilter auf jedem Quellenausschnitt; Datenschutzseite „was Löschung umfasst“ | Server-Stack (8 Dienste), Code (PolyForm NC) | Betrieb unverhältnismäßig für Einzelplatz |
| TutorBench | emulate | Rubrikmuster mit −5 für unaufgefordertes Lösungsverraten; Pflichtbericht Judge-Mensch-Übereinstimmung | Lauf auf dem Datensatz (nur 30 NC-Beispiele öffentlich) | Mittel besser in eigene versteckte Fälle mit verzögertem Test |
| MathTutorBench | defer | Bewertungsdimension „löst gut ≠ unterrichtet gut“ | Ausführung vor Lizenzklärung | gering |
| OpenTutor | reject | — | eigener FSRS-Scheduler, Verhaltens-Ermüdungserkennung | keine; Nützliches (lokale Modelle) liefert der Vertrag ohnehin |
| PAIDEIA | emulate | append-only, lokal lesbares Fehler-/Hilfelog; `twin` als unassistierter Abschluss; `blind` (Strategie benennen) als Transferprobe | „Hausaufgabendichte = Prüfungswahrscheinlichkeit“; LLM-„grade“ als Lernstand | Plugin würde zweite Kursordner-Konvention schaffen |
| Education Agent Skills | emulate | retrieve-first als Angebot; Reflexionsfrage bei schnellem Eskalieren (nur beobachten); unassisted checkpoint; Evidenzehrlichkeit; teach-back als FEEDBACK_UNVERIFIED | Textübernahme (CC BY-SA); „NEVER full solution“; Pflicht-Abruf für Novizen; Scheduler-Skill | Eigenformulierung kostet Schreibzeit, vermeidet Share-alike |
| ChatGPT Study Mode | reuse | als Vergleichsarm A2 und freie Option der Lernenden | Integration, Memory als Lernstand | nahezu null |
| ChatGPT Project / portabler Kontext | adapt | PR-#19-Brief → Vertrag v0.1 (§3) | API-Tutor | niedrig; Alternative bräuchte Budget, Schlüsselverwaltung, Anbieterbindung |
| NotebookLM | defer | optionaler Vergleichsarm für quellgebundenes Nachfragen | Pflichtarm (Google-Konto, Upload privater Materialien) | gering |
| YouLearn | reject | — | — | keine |
| StudyFetch | reject | — | Karten/Lernplan, klinisches Roleplay ohne Grenze | keine |
| Khanmigo | emulate | Tutorangebot im Fehlermoment mit vorbefülltem Kontext (existiert); Nutzungsquote im Fehlerfall als Pflicht-Prozessmaß | Produkt (US-only, proprietär) | Lehren kostenlos |
| Math Academy | defer → R6/R8 | — (Voraussetzungsgraph/Einstufung ist Sequenzierungsfrage) | FIRe-Wiederholungsplanung | keine für R9 |
| RemNote | reject | — | eigener Scheduler | keine |
| Margin Study | defer → R7/R8 | — (kein Tutor; lokale Randnotiz in eigenen Worten) | — | keine für R9 |
| Utterseen | reject | — | Bildschirm-Screenshots an nicht benannte Anbieter | keine; Kontextknopf liefert ausdrücklich gewählten Kontext |

## 3. Minimale Integration mit der PR-#19-Engine

**Fakt (Code gelesen, nicht ausgeführt):** In PR #19 (`origin/integration/quality-recovery-20261126`) erzeugt `exam_mastery/templates/em_tutor.js` auf Knopfdruck eine Kontextdatei `em-tutor-context-v1` (Aufgabe, Versuche, `hints_used`, `solution_viewed`, `support_level`, Quellen, `source_status`, Frage). `exam_mastery/learning/tutor.py` validiert sie und baut ohne Modellaufruf einen Markdown-Brief mit Fehlerkategorien, **Musterlösung „NUR für den Tutor“**, Visualisierungshinweisen, Quellen und dem Protokoll `PROTOCOL` (8 Regeln). `learning/policy.py: helped()` zählt nur Ereignisse vom Typ `hint` und `solution` als Hilfe. Die Skill-Evals `tutor-context-file` und `tutor-no-solution-first` prüfen Einzelantworten mit LLM-Gradern (Antwortebene, kein Lernmaß).

**Designentscheidung — kleinster Schritt (nach Architektur-Gate, nicht in R9):**

1. `tutor.py`: `PROTOCOL` durch den Text aus [TUTOR_BEHAVIORAL_CONTRACT.md §9](TUTOR_BEHAVIORAL_CONTRACT.md) ersetzen (versioniert, eine Quelle für Skill und Brief); `brief()` erhält einen Parameter `mode` ∈ {`with_reference`, `keyless`}; Standard `keyless`; `with_reference` nur für Übungsaufgaben mit eigenem Versuch und mit sichtbarem Hinweis, dass die Lösung im Text steht (R9-POL-04).
2. `tutor.py`: Quellenblock je Ausschnitt mit `source_id`, Locator, Fassung, `as_of`, `temporal_status` (R9-POL-01) — `source_status` existiert bereits je Lernstrecke und wird aufgeteilt.
3. `tutor.py`: deterministischer Leck-Check vor Ausgabe — Abbruch, wenn eine Aufgabe mit Rolle `mock`/`retest`/`transfer`/`evaluation` oder deren Lösung im Brief steht.
4. `em_tutor.js`: Nach dem Export wird die Parallelaufgabe der Lernstrecke angezeigt; ihr Ergebnis ist ein normales unassistiertes Engine-Ereignis (keine neue Eingabe von Tutor-Urteilen). Optional ein Ereignis `type: "tutor"` beim Export, damit `helped()` die Exportaufgabe als assistiert zählt (R5-POL-04; heute zählt ein Tutor-Export nicht als Hilfe — **Fakt** aus `helped()`).
5. `release/skill/exam-mastery/references/tutor_protocol.md`: auf den Vertrag verweisen; Evals um die adversarialen Folgefragen aus [TUTOR_EVALUATION_PROTOCOL.md §3](TUTOR_EVALUATION_PROTOCOL.md) ergänzen und ausdrücklich als Antwortebene kennzeichnen (R9-POL-05).

Keine neuen Module, kein Netzwerkzugriff, kein Lernermodell, kein Scheduler. Geschätzter Umfang: ein Modul, ein Template, zwei Evals. **Nicht belegt:** dass diese Änderungen Lernen verbessern — erst Arm B vs. A/A2/C zeigt das.

## 4. Opportunitätskosten-Argument

- **Alternative 1, ein externes System einbetten (DeepTutor/SMART-RAG/OpenTutor):** hoher Integrations- und Betriebsaufwand, zweiter Scheduler bzw. zweites Lernermodell, Lizenzgrenzen (PolyForm NC), schneller fremder Release-Takt; kein Lernergebnis, das den Aufwand rechtfertigt (**Fakt**: keine gefunden).
- **Alternative 2, eigener API-Tutor:** braucht autorisiertes Budget, Schlüsselverwaltung, Anbieterwahl und Datenschutzprüfung; gewinnt Durchsetzbarkeit (z. B. deterministisches Entfernen von Lösungen, wie pisan2026withhold beschreibt), aber ohne Lernbeleg.
- **Alternative 3, nur Study Mode empfehlen:** null Aufwand; aber nicht in Projects, kein Quellen-Zeitstatus, keine Kopplung an Parallelaufgaben, Memory als undurchsichtiger Lernstand. Wird als Arm A2 mitgetestet — schlägt A2 den Vertrag nicht, ist der Vertrag überflüssig.
- **Gewählt (Hypothese):** portabler Vertrag + kleiner PR-#19-Umbau (§3) + Evaluation. Geringster Aufwand, der die Messbarkeit (unassistierte Parallelaufgabe, Hilfe-Ereignisse) erhält und von der Evaluation widerlegt werden kann.

## 5. Abstimmungspunkte mit anderen Workstreams

- **R5:** Ausgabetypen und Messvertrag unverändert übernommen (R5-POL-04/05/06); R9 fügt Brief-Modi und Leck-Check hinzu. Frage an R5: Soll `assist_level=tutor` für einen Export ohne Gespräch gelten?
- **R3/R4:** Grenzen aus R3-POL-10/11 und R4-POL-01/13 im Vertrag §6/§7; Bitte um Prüfung der klinischen und CAD-Formulierungen.
- **R7/R8:** Margin Study und Math Academy übergeben; Anki/FSRS bleibt einziger Scheduler.
- **R6:** Architektur-Gate für §3; keine Umsetzung vorher.

## 6. OWNER_DECISIONS_REQUIRED

1. **Brief-Modus:** Soll der Standard-Brief künftig `keyless` sein und die Musterlösung nur im Modus `with_reference` enthalten (heute immer enthalten, Anbieter erhält sie)?
2. **Lösung auf Anforderung:** Bestätigen, dass eine ausdrückliche Lösungsanforderung auch vor dem ersten eigenen Versuch erfüllt wird (protokolliert als assistiert), wie R5-POL-03/08 und AI-R1 es zulassen — statt der „NEVER full solution“-Regel aus Education Agent Skills.
3. **Parallelaufgabe aus der Engine:** Bestätigen, dass nur engine-gelieferte, deterministisch geprüfte Parallelaufgaben als unassistierte Evidenz zählen und vom Tutor erzeugte Aufgaben nie.
4. **Evaluationsbudget:** Freigabe (oder Ablehnung) bezahlter Modellaufrufe für Arme A/A2/B und Judge sowie unabhängiger menschlicher Fallautoren; ohne Freigabe bleibt das Protokoll Entwurf.
5. **Anbieterliste:** Welche Chats der Vertrag offiziell nennt (ChatGPT, Claude, Gemini, Codex) und ob Study Mode als empfohlene Option erscheinen darf.
6. **Lizenzpolitik:** Bestätigen, dass CC-BY-SA-Material (Education Agent Skills) nur emuliert, nicht wörtlich übernommen wird, und dass PolyForm-NC-Code (SMART-RAG) ausgeschlossen bleibt.
7. **TutorBench-Stichprobe:** Ob der öffentliche 30er-Ausschnitt (CC BY-NC) als Zusatzarm auf Antwortebene genutzt werden darf.
8. **Registerkorrekturen:** Margin Study in den R7/R8-Brief verschieben; NotebookLM als „Gemini Notebook“ nachführen; RemNote-„Guided Learn Mode“ als unbestätigt markieren.

## 7. Was nicht behauptet wird

- Keine Ressource wurde ausgeführt; keine Aussage über tatsächliche Kosten, Latenz, Offline-Fähigkeit oder Antwortqualität.
- Keine Entscheidung ist freigegeben; alle Policies sind `design_hypothesis`, `learning_evaluation: NOT_RUN`.
- **Nicht belegt:** dass emulierte Mechanismen ohne ihr Ursprungssystem dieselbe Wirkung haben — der Falsifikator von R9-POL-07 deckt genau das ab.
