# R6 — Red-Team-Review der Workstream-Policies (Issue #27)

**Stand:** 27.11.2026 · **Rolle:** R6-RT, unabhängig von der Architektur-Synthese (die ADR-Datei wurde nicht gelesen) · **Status:** Red-Team-Kritik, keine Abnahme. `learning_evaluation` bleibt für jede Policy und jedes Produkt `NOT_RUN`. Frühere Produkte bleiben **HUMAN_REJECTED**.

**Maschinenlesbar:** [r6/red_team_findings.json](r6/red_team_findings.json) (43 Befunde, 18 Prüfungen der Sicherheitsstufen) · **Prüfung:** `tests/test_r6_red_team.py`.

**Grundlage:** eingefrorener Index [r6/policy_index.json](r6/policy_index.json) (Commit 60535a6, 116 Policies aus R1–R5, R7–R9), Engine-Regeln in `exam_mastery/knowledge/principles.json`, kritische Defekte CD-1..CD-8 aus `PROGRAMME_STATE.json` (Branch `ops/programme-control-20261127`), Engine-Fixes PR #37 (Kopf 5bdfb6f) und PR #43 (Kopf 5ad257d).

---

## 0. Ergebnis in zehn Punkten

1. **Fünf Engine-Regeln sind universell formuliert, obwohl die eigenen Workstreams sie einschränken:** RP-R1 (jede Einheit endet mit Abruf, deterministisch erzwungen), WE-R1/WE-R2 (Fading für jede Prozedur, Überspringen nach einem Ein-Item-Test), MC-R1/PR-R1 (Konfidenz vor jeder Aufgabe bzw. jedem Lab), AS-R1 (jede Aufgabe mit genau einer Musterlösung, Punkten und Zeit) und AI-R1 (‚nur Schadensvermeidung‘). Siehe RT-01 bis RT-05.
2. **Die Prüfung der Sicherheitsstufen (18 Policies) ergab:** 6 Überschätzungen (R1-POL-A02, R1-POL-B09, R2-POL-01, R2-POL-11, R7-POL-04, R7-POL-06), 3 zu breite Geltungsbereiche, 2 Kategoriefehler (R5-POL-01: Vorhersage statt Lernen; R9-POL-06: Protokoll als ‚moderate‘), 1 verdeckter Mischwert (R1-POL-A08) und 1 Unterschätzung (R1-POL-A04 im engen Mathematik-Bereich). Die übrigen 5 sind konsistent.
3. **Jede der sechs Pflichtdomänen hat mindestens einen reproduzierbaren Fehler mit falschem Mastery-Signal oder Schaden** (RT-10 bis RT-18). In keinem der neun Fälle erkennt der eigene Falsifier der Policy den Fehler vollständig: viermal gar nicht, fünfmal nur teilweise.
4. **Zwei Befunde sind mit Engine-Code am PR-#43-Stand reproduziert** (Scratch-Kopie, keine Codeänderung): Der Ausdrucksprüfer akzeptiert `x` für `(x^2)^(1/2)` (RT-11), und `kc_status` meldet `RETAINED_ON_LATER_DAY`, wenn eine Minute vor der Retest-Lösung die Lösung einer Schwesteraufgabe angesehen wurde oder ein importierter Zeitstempel in der Zukunft liegt (RT-26).
5. **Der CD-2-Fix (PR #37) verengt das Loch, schließt es aber nicht.** Er ist ein **Blocker** für jede Nutzung von `kc_status` als Evaluationsendpunkt (RT-26). **Auch der CD-7-Fix (PR #43) verengt nur:** Nachweisaufgaben stehen schlüssellos weiter im Brief, und Hilfe außerhalb des Produkts bleibt unsichtbar (RT-27).
6. **Für Konflikte zwischen den Workstreams gibt es keine gemeinsame Rangfolge** (RT-25). Ein Konflikt widerspricht sich sogar innerhalb von R9: CR-R9-2 sagt, eine ausdrückliche Lösungsanforderung hat Vorrang; R9-POL-04 verlangt, sie bei Prüfaufgaben zu verweigern (RT-20).
7. **Strukturkonflikt zwischen Scheduler-Monopol und Messvertrag:** Anki ist der einzige Scheduler, liefert aber nur Selbstbewertungen. Der zulässige Beleg (ein unassistierter Retest nach verstrichener Zeit) braucht eine Planung, die die Engine nicht vornehmen darf (RT-22, RT-28).
8. **Für ein Ein-Personen-Projekt ist der Messvertrag (R5-POL-05) auf absehbare Zeit unerreichbar.** Damit droht, dass Ersatzgrößen still in Entscheidungen zurückkehren (RT-32).
9. **Keine der Architekturen A, B oder C lässt sich über Lernvalidität begründen.** Alle 116 Policies sind `design_hypothesis` mit `NOT_RUN` (RT-36). Für jede Architektur nennt §6 den wahrscheinlichsten Fehler und das billigste Experiment, das ihn aufdecken würde.
10. **Sieben Fragen kann nur der Owner entscheiden** (RT-37 bis RT-43), darunter die Grenze des Schedulers, Lösungen auf Wunsch bei Nachweisaufgaben, die Hochrisikodomänen ohne menschliche Bewertung und unabhängige menschliche Prüfung.

Schweregrade: 1 blocker, 39 major, 3 minor. Arten: 9 universal_rule, 9 domain_failure, 7 conflict, 7 measurement, 4 architecture, 7 owner_decision.

---

## 1. Methode

**Gelesen, in dieser Tiefe:**

| Quelle | Tiefe |
|---|---|
| Issue #27, Charter `RESEARCH_FIRST_PROGRAM_20261126.md` (Prinzipien, Taxonomie, Architektur-Gate) | vollständig |
| `policy_index.json` (116 Policies) | alle Titel, Sicherheitsstufen und Operationen; für 40 Policies `recommendation`, `abstain_or_fallback`, `observable` und `falsifier` im Wortlaut |
| Evidenzregister R1a, R1b, R2, R3, R4, R5, R7, R8, R9 (zusammen 316 Einträge) | maschinell mit allen `evidence`-IDs des Index verknüpft (Zugangsstufe, Design, Population, Schätzwert); für die 18 Prüfungen der Sicherheitsstufen einzeln gelesen |
| Engine-Regeln (30) in `principles.json` | vollständig; Wortlaut von 9 Regeln |
| `PROGRAMME_STATE.json` (critical_defects, architecture_decisions, product_quality) | vollständig |
| R0 `KB_GAP_AUDIT.md` | §2, §5 D6, §6 |
| R2 §6 Konfliktregeln; R4 §6 Konfliktregeln und §8 Risikoaudit; R9 `TUTOR_ADOPTION_DECISION.md` §3–§6; `r9_tutor_policies.json` (conflict_resolution, shared_measurement_contract); R1 §5 | gelesen |
| Übrige Abschnitte der Workstream-Berichte (R3, R5, R7, R8) | nur Inhaltsverzeichnis und gezielte Stellen; **nicht vollständig gelesen** |
| PR #37 (Beschreibung, Diff `policy.py`), PR #43 (Diff `policy.py`, `tutor.py`; `em_tutor.js` gezielt) | gelesen |
| Proben | `expr.same` und `policy.kc_status` vom Stand 5ad257d in eine Scratch-Kopie gezogen und mit synthetischen Eingaben ausgeführt; Engine und Repository unverändert |

**Vorgehen:** (1) Jede Engine-Regel und jede Policy mit ‚jede/alle/immer‘ oder breitem `applies_to_operations` gegen die `abstain_or_fallback`-Felder anderer Policies und gegen die Population der zitierten Belege halten. (2) Sicherheitsstufen gegen die Zugangsstufe und das Design der Belege prüfen. (3) Für jede Pflichtdomäne einen synthetischen Fall konstruieren, der die Policies so anwendet, wie sie geschrieben sind, und prüfen, ob `observable` und `falsifier` den Fehler sehen. (4) Die Engine-Fixes am Code prüfen und wo möglich mit Proben gegentesten.

**Nicht getan:** keine eigene Literatursuche; keine Volltexte gelesen; keine Lernenden; kein Engine-Lauf außer den zwei Proben; keine Bewertung einzelner Produkte.

---

## 2. Angebliche Universalregeln und geprüfte Sicherheitsstufen

### 2.1 Universell formulierte Regeln

| ID | Ziel | Kern |
|---|---|---|
| RT-01 | RP-R1 | ‚Jede Lerneinheit endet mit Abrufaufgaben‘, deterministisch erzwungen. R1-POL-A01 schließt Abrufitems für Beweisketten aus, R1-POL-A02 stellt sie für Novizen zurück, R4 kennt Spur B ohne Produktbewertung. |
| RT-02 | WE-R1, WE-R2 | Überspringen nach einem einzigen Erste-Schritt-Test. R0 D6, R1-POL-A03 (very_low) und R3-POL-03 (Beispiele im Recht verfügbar halten) widersprechen. |
| RT-03 | MC-R1, PR-R1 | Konfidenz vor jeder Aufgabe bzw. jedem Lab. Gegen die Reaktivitätsbefunde (`higham2023reactivity`, `janssen2024monitoring`) und gegen R1-POL-A09 und R2-POL-11, die Konfidenz nur stichprobenartig erlauben. |
| RT-04 | AS-R1 | Eine Musterlösung, Punkte und Zeit für jede Aufgabe. Unvereinbar mit Alternativrouten (R3-POL-11) und Spur B (R4-POL-01); die Zeit ist eine gesetzte Zahl (CD-4). |
| RT-05 | AI-R1 | ‚Nur Schadensvermeidung‘ steht auf dem R6-Basisstand unverändert (CD-3, R0 P0); die Musterlösung im Brief widerspricht R9-POL-04. |
| RT-06 | R2-POL-11 → R7-POL-02/08, R4-POL-09, PR-R1 | Predict-before-run stützt sich auf einen einzigen Abstract (11- bis 14-Jährige, ohne Effektschätzung) und wird über Querverweise domänenübergreifend weitergegeben. |
| RT-07 | R5-POL-08 | Die Belege für die Hinweisleiter stammen aus ITS der Mittelstufe; die Policy gilt aber auch für Beweis, Recht und Diagnose an Hochschulen. |
| RT-08 | R1-POL-A01/A04/A05, R5-POL-04/08 | Ein großer Teil der tragenden Evidenz stammt aus Schulen oder Laboren; die Population ist nirgends als Moderator mit eigener Sicherheit geführt. |
| RT-09 | R1-POL-A01 | ‚Moderate‘ aus Faktenlernen wird auf Tatbestandsmerkmale und bedingungstragende Aussagen übertragen. |

Nicht jede Regel ist ein Problem. LS-R1 (keine Lernstile), SE-R2 (Freitext bleibt unverifiziert), AI-R2 (agent_judgement getrennt) und ITS-R1 (keine Prozentwerte) sind Restriktionen. Sie verlieren nichts, wenn sie universell gelten.

### 2.2 Prüfung der Sicherheitsstufen (18 Policies)

Die Einzelheiten stehen in `certainty_spot_checks` der JSON-Datei.

| Policy | Angegeben | Urteil | Vorschlag | Ausschlaggebend |
|---|---|---|---|---|
| R1-POL-A01 | moderate | Geltungsbereich zu breit | moderate faktisch / low bedingungstragend | ruitenburg2026: konzeptuell, prozedural und Transfer n.s. |
| R1-POL-A02 | moderate | **Überschätzt** | low | einzige Volltext-Primärstudie (vangog2015) ist null; die verzögerten Befunde zeigen Gleichheit |
| R1-POL-A04 | low | unterschätzt (eng) | moderate nur für Mathematik-Aufgabentypen in der Schule | rohrer2020: präregistrierte Cluster-RCT, 0.83 |
| R1-POL-A05 | moderate | Geltungsbereich zu breit | low für kursintegrierte Hochschulmathematik | ebersbach2020: Hochschul-RCT null (p=.909) |
| R1-POL-A06 | moderate | konsistent | — | bisra2018 Volltext; Quelle doppelt gelistet |
| R1-POL-A08 | moderate | Mischwert | Komponenten trennen | nur korrektives Feedback meta-analytisch gestützt |
| R1-POL-B09 | moderate | **Überschätzt** | low | nur Abstracts |
| R2-POL-01 | moderate | **Überschätzt** | low | eine Forschungsgruppe, keine Replikation im Register |
| R2-POL-05 | moderate | konsistent (als Restriktion) | — | mehrere Bewertungsstudien |
| R2-POL-11 | low | **Überschätzt** | very_low | ein Abstract, Schätzwert unbekannt |
| R3-POL-08 | low | konsistent | — | Urhebergruppe; unabhängiger Nullbefund; I² = 88 % |
| R4-POL-10 | low | konsistent | — | nur Abstracts, Transfer auf CAD ungeprüft |
| R5-POL-01 | moderate | Kategoriefehler | nur als Messaussage | Simulation und Modellvergleich, kein Lernergebnis |
| R5-POL-04 | moderate | konsistent | — | bastani2025, lehmann2025 Volltext |
| R5-POL-08 | low | Geltungsbereich zu breit | very_low außerhalb symbolic_procedure | Mittelstufen-ITS |
| R7-POL-04 | moderate | **Überschätzt** | low | im Register nur ein narrativer Review (‚limited empirical evaluation‘) |
| R7-POL-06 | moderate | **Überschätzt** | low | keine Volltextquelle |
| R9-POL-06 | moderate | Kategoriefehler | normative | Evaluationsprotokoll, Belege sind Working-Paper-Abstracts |

**Systematisch (RT-31):** 17 Policies nennen dieselbe Quelle doppelt. 25 Zitate verweisen auf KB-Quellen, die in keinem Workstream-Register stehen. 17 Policies mit low oder moderate haben keine einzige Volltextquelle. Alle Stufen haben Agenten derselben Modellfamilie selbst vergeben; die Charter nennt sie ausdrücklich ein ‚reasoned internal label, not an externally validated guideline‘.

---

## 3. Falsifizierende Fehler je Domäne

Alle Fälle sind synthetisch; Normen sind fiktiv (‚MusterG‘), Patienten erfunden, und es kommen keine gefährlichen Verfahren vor.

| ID | Domäne | Szenario (kurz) | Was schiefgeht | Eigener Falsifier fängt es? | Minimale Änderung |
|---|---|---|---|---|---|
| RT-10 | math_proof | Beweis-KC; geprüft wird nur die Prämissenauswahl (constraints) | `DETERMINISTIC correct` → `RETAINED` für den Beweis-KC, obwohl die Lernende keinen Beweis schreiben kann | nein | Zustand je Komponente (verstehen/validieren/konstruieren) und Prüferabdeckung (R2-POL-14) |
| RT-11 | math_symbolic | ‚Vereinfache (x^2)^(1/2)‘, Antwort `x` | Stichproben nur in (0.15, 0.95), fester öffentlicher Seed, keine Betragsfunktion in der Grammatik → als richtig gewertet (**Probe bestätigt**) | nein | Stichproben aus dem deklarierten Definitionsbereich; symbolische Prüfung als Pflicht |
| RT-12 | law | Fristkarte mit 4-Monats-Intervall; die fiktive Norm ändert sich | Stabile GUID (R8-POL-02) vererbt das Intervall; die neue Frist erscheint erst nach Monaten | nein | Änderungsklasse ‚substanziell/Rechtsstand‘ mit Tag, Bericht und gefiltertem Stapel |
| RT-13 | law | ‚Umformulierter‘ Retest mit demselben binären Ergebnis; Lernende mit vertretbarer Mindermeinung | Das Ergebnis wird erinnert statt subsumiert; die Alternativroute wird gegen die eine Musterlösung als falsch gewertet | teilweise | Retest kontrafaktisch mit wechselndem Ergebnis; Begründung getrennt bewerten |
| RT-14 | clinical | Fallbank überrepräsentiert seltene Diagnosen | Kalibrierung auf die Basisrate der Fallbank; eine generierte falsche Referenz trainiert systematisch falsch | teilweise | Prävalenz deklarieren, Kalibrierung je Schicht, Testfälle mit anderer Basisrate |
| RT-15 | code_debugging | Off-by-one-Fehler; Tests werden einzeln freigeschaltet | Sonderfall-Patch besteht die sichtbaren und generatorgleiche verborgene Tests; eingefügte Ausgabe ist Selbstauskunft; ‚Vorhersage vor jedem Lauf‘ wird weggeklickt | teilweise | Belege nur aus Engine-Läufen mit property-/mutationsbasierten verborgenen Tests |
| RT-16 | cad_spatial | Änderungstests werden mit der Aufgabe angekündigt | Überanpassung an genau die angekündigten Werte; ohne CAD-Prüfer bleibt der Zustand dauerhaft ‚unverifiziert‘ und wirkt doch wie Fortschritt | teilweise | Verdeckte, randomisierte Änderungstests; NOT_APPLICABLE statt Scheinübung |
| RT-17 | craft_or_lab | Handgesägte Verbindung, Selbstlerner ohne Ausbildende | Spur A ist die einzige sichtbare Anzeige, wird als Können gelesen und verdrängt reale Übung; der Falsifier braucht Spur-B-Daten, die es nie gibt | nein | Anzeige ‚Wissen geprüft – Ausführung nicht beobachtet‘ ohne Balken; Zeitempfehlung für reale Übung |
| RT-18 | craft_or_lab | Hefegärung; Simulation ohne Messrauschen | Reale Streuung wird als Bedienfehler gedeutet, Daten werden ‚korrigiert‘ | teilweise | Messmodell in Simulationen; Transferetikett um ‚Messunsicherheit‘ ergänzen |

**Muster:** Die Falsifier der Policies sind fast immer **Lernwirkungsstudien** (‚randomisierter Vergleich zeigt keinen Vorteil‘). Die gefundenen Fehler sind meist **Messfehler** (falsches Signal, Leck, falsches Negativ). Eine Wirkungsstudie entdeckt sie erst, wenn sie längst in Daten stecken, und manchmal gar nicht (RT-17). Jede Policy mit Kompetenzbezug braucht deshalb zusätzlich einen **Integritätsfalsifier**: einen adversarialen synthetischen Fall, der ohne Lernende ausführbar ist.

---

## 4. Konflikte zwischen Workstreams

| ID | Konflikt | Lücke |
|---|---|---|
| RT-19 | Beispiel zuerst (R1-POL-A02, CR-1) gegen Vorhersage, Erkundung oder Pretesting zuerst (PR-R1, R7-POL-02, PF-R1, R1-POL-A11) | Die Auflösung hängt an der Novizen-Erkennung, und die ist ein unkalibrierter Ein-Item-Test |
| RT-20 | Hinweisleiter und Nachweisintegrität (R9-POL-04) gegen ausdrückliche Lösungsanforderungen (CR-R9-2, R5-POL-06, AI-R1) | R9 widerspricht sich selbst; PR #43 weicht zusätzlich von CR-R9-1 ab |
| RT-21 | Eigener generativer Weg (R8-POL-13, R1-POL-A06) gegen generierte Deck-Identität (R8-POL-05, CD-8) | Lernenden-Änderungen werden still überschrieben; Eigenkarten erzeugen Doppelwiederholungen |
| RT-22 | Anki als einziger Scheduler (R8-POL-01) gegen den Messvertrag (Retest nach verstrichener Zeit) | Der zulässige Beleg braucht eine verbotene zweite Planung |
| RT-23 | Predict-before-run (R2-POL-11, PR-R1, R4-POL-09) gegen Sicherheitsgates (R4-POL-13) | R4-CR-3 deckt Explore-Modi ab, Vorhersage-Gates aber nicht; das Produkt weiß nicht, ob ‚ausführen‘ simuliert oder real ist |
| RT-24 | Enthaltungsregeln (R9-POL-01, R3-POL-01/10/11, R4-POL-13) gegen Nützlichkeit | Kumuliert liefert das Produkt in den Hochrisikodomänen fast nur Enthaltungen; Abwanderung in den uneingeschränkten Chat wird nicht gemessen |
| RT-25 | Autonomie (R1-POL-B07) gegen Hilfebegrenzung (R9-POL-09), Feedback (R1-POL-A08) gegen Einreichungslimit (R2-POL-13) u. a. | Jede Workstream hat lokale Konfliktregeln, es gibt keine globale Rangfolge |

**Gelöste Konflikte (Vorbild):** R4-CR-1 grenzt Interleaving (R1-POL-A04) sauber von geblocktem Üben der physischen Ausführung ab (R4-POL-03). R2-CR-3 trennt Einreichungslimit und Erklärungen. Solche Paarregeln fehlen workstream-übergreifend.

---

## 5. Mess- und Evidenzintegrität

### 5.1 Stand der kritischen Defekte aus Red-Team-Sicht

| Defekt | Fix | Urteil |
|---|---|---|
| CD-1 (keine gemessene Lernwirkung) | — | offen; RT-32 und RT-36 |
| CD-2 (Kalenderdaten als Behalten) | PR #37 | **verengt, nicht geschlossen** (RT-26): Hilfe zählt nur für dieselbe Aufgabe, Zeitstempel kommen vom Client und sind importierbar, eine Prüfung ‚t ≤ jetzt‘ fehlt, 20 h sind weniger als die ≥ 1 Woche aus R1-POL-A01, der Statusname überzeichnet. **Blocker** für die Nutzung als Evaluationsendpunkt |
| CD-3 (AI-R1 ‚Schadensvermeidung‘) | — | offen; der Wortlaut steht auf dem R6-Basisstand (RT-05) |
| CD-4 (gesetzte Spezifikationszahlen) | — | offen; trägt RT-04, RT-07 und RT-33 |
| CD-5 (Golden References sitzungskuratiert) | — | offen; RT-32 (Gefahr der Ersatzgrößen) |
| CD-6 (Drift der Draft-Stapel) | — | nicht geprüft (außerhalb des Auftrags) |
| CD-7 (Musterlösung im Tutor-Brief) | PR #43 | **verengt, nicht geschlossen** (RT-27): Nachweisaufgaben stehen schlüssellos im Brief, Hilfe außerhalb des Produkts bleibt unsichtbar, core/contrast/harder behalten den Schlüssel, der Schlüssel kommt ohne vorherigen eigenen Versuch mit, die Mock-Rolle ist unklar |
| CD-8 (Anki-Exportidentität) | geplant (P4) | Der geplante Fix verhindert das Überschreiben unveränderter Notizen, aber nicht das stille Überschreiben bei Inhaltsänderung (RT-21), und er behandelt keine substanziellen Änderungen (RT-12) |

### 5.2 Wo der gemeinsame Messvertrag missbraucht oder fehlgelesen werden kann

- **Assistiert vs. unassistiert:** ‚Unassistiert‘ heißt im Produkt höchstens ‚ohne im Produkt protokollierte Hilfe‘ (RT-26, RT-27). Hilfe an einer Schwesteraufgabe desselben KC wird nicht erfasst.
- **Verstrichene Zeit:** Die Zeitstempel kommen vom Client und lassen sich per Import setzen; ein Zukunftsdatum wird akzeptiert (RT-26).
- **Selbstauskunft:** Das observable der zentralen Abruf-Policy ist in Anki eine Selbstbewertung (RT-28). Eingefügte Testausgaben im Tutor-Weg sind ebenfalls Selbstauskunft (RT-15).
- **‚Umformuliertes Item‘:** Das ist nicht operationalisiert; bei geringer Ergebnisvielfalt misst es Ergebnisgedächtnis (RT-13, RT-29).
- **Agentenurteile:** Die Lockerungsklauseln (R2-POL-05, R3-POL-11) prüfen die mittlere Übereinstimmung, aber keine Verzerrung in Teilgruppen und kein Goodhart; Auditoren derselben Modellfamilie haben korrelierte Fehler (RT-30).
- **Benchmark als Lernen:** R9-POL-05 verbietet das ausdrücklich. Ein Auditor in Architektur C, der Rubrik-Konformität misst, schleust es aber wieder ein (RT-35).
- **Unerreichbarer Vertrag:** Wer nur ‚nicht gemessen‘ sagen darf, entscheidet trotzdem, und zwar nach Ersatzgrößen (RT-32).

---

## 6. Architekturbedrohungen

Die Ausgangslage ist für alle Architekturen gleich: 116 Designhypothesen, keine mit evaluierter Lernwirkung, für Beweis, Recht, Klinik, CAD und Handwerk keine verfügbaren deterministischen Prüfer, Autorschaft von Agenten derselben Modellfamilie.

| Architektur | Wahrscheinlichster Fehler | Billigstes Experiment, das ihn aufdeckt | Verwerfen, wenn … |
|---|---|---|---|
| **A** Vorlagen + Domänenmodule (RT-33) | Die Vorlagen frieren die universell formulierten Regeln ein (RT-01/02/04), die Domänenmodule werden Ausnahmelisten, die Autorenkosten sind ungebunden; die HUMAN_REJECTED-Historie entstand vorlagengetrieben | 2 Vorlagen × 3 Domänen mit synthetischem Inhalt: Anteil überschriebener Felder bzw. NOT_APPLICABLE, dazu blinde menschliche Bewertung gegen handverfasstes Material | > vorab festgelegter Anteil (Vorschlag 30 %) der Felder je Domäne überschrieben wird oder die blinde Bewertung keinen Vorteil zeigt |
| **B** Kompetenzgraph + Policy-Engine + Adapter (RT-34) | Scheinpräzision: Regeln hängen an Kontextprädikaten, die das System nicht beobachten kann; ‚evidenzkonditioniert‘ ohne Evidenz; Adapter existieren nur in schmalen Bereichen; Konflikte werden implizit aufgelöst | 20 Policies aus 3 Operationen als Regeln, 30 synthetische Spuren: Konflikte je Entscheidung, Anteil an unbeobachtbaren Prädikaten, Übereinstimmung Fachleute–Engine vs. Fachleute untereinander | > vorab festgelegter Anteil an unbeobachtbaren Prädikaten oder Fachleute stimmen mit der Engine deutlich seltener überein als miteinander |
| **C** Agentengenerierung + Auditoren (RT-35) | Korrelierte Blindstellen von Generator und Auditor; Identitätsverlust bei Neugenerierung (CD-8); Schlüssellecks (CD-7-Klasse); Rubrik statt Lernen | 20 Artefakte mit gepflanzten Defekten (veraltete Fassung, ungültiger Schritt, Leck, unsicherer Parameter, abgewertete Alternativroute): Auditor-Recall gegen menschliche Prüfung; GUID-Churn bei Neugenerierung unveränderter Inhalte | Recall für Blocker-Klassen unter der Schwelle oder Churn > 0 |
| **Hybride** (RT-36) | Fehler addieren sich; jede Schicht braucht laut Charter eine konkrete Notwendigkeit | Minimal-Scheibe mit genau einer Operation je Schicht und Abbruchregel | eine Schicht keinen Fehler einer anderen nachweislich abfängt |

### 6.1 Behauptungen, die ein ADR nicht machen darf

1. Eine Architektur sei ‚lernwirksamer‘, ‚evidenzbasiert‘ oder ‚wissenschaftlich fundiert‘ im Sinne gemessener Wirkung (CD-1; alle Policies NOT_RUN).
2. ‚Evidenzkonditioniert‘ bedeute ‚evidenzgeprüft‘ (RT-34).
3. Auditoren derselben Modellfamilie seien ‚unabhängig‘ (RT-30, RT-35).
4. `kc_status`-Zustände oder Anki-Statistiken seien Kompetenz- oder Behaltensnachweise (RT-26, RT-28; R8-POL-12).
5. CD-2 oder CD-7 seien ‚behoben‘ (RT-26, RT-27).
6. Policies gälten für Erwachsene, Selbststudium oder Hochschule, wo nur K-12- oder Laborevidenz vorliegt (RT-08).
7. Die Sicherheitsstufen der Workstreams seien extern geprüft (RT-31).
8. Das Produkt vermittle oder prüfe physische Fertigkeit, klinische Kompetenz oder Rechtsberatungsfähigkeit (R3-POL-10, R4-POL-01).
9. Der Tutor sei schadensfrei oder ‚vermeide Schaden‘ (CD-3, RT-05).
10. Eine Spezifikationszahl (Fading-Stufen, Hinweisanzahl, 20 h, ±10 %, ≤ 60 Wörter) sei empirisch begründet (CD-4).

---

## 7. Was der Owner entscheiden muss (Red-Team-Sicht)

Diese Fragen kann Forschung nicht klären; sie verlangen eine Abwägung von Werten, Risiken oder Ressourcen.

| ID | Entscheidung |
|---|---|
| RT-37 | Darf die Engine fällige **Retest-Aufgaben** anzeigen (Grenze von AD-1), oder läuft der Retest nur über Anki-Verweiskarten? |
| RT-38 | Welche **schwächeren Designs** sind für Produktentscheidungen zulässig, und welche **Wortliste** gilt bis dahin (‚ohne protokollierte Hilfe‘, ‚nicht gemessen‘)? |
| RT-39 | Wird bei **Nachweisaufgaben** eine ausdrücklich angeforderte Lösung gezeigt und das Item ausgemustert, oder wird die Anforderung verweigert? |
| RT-40 | Werden **Recht, Klinik und Handwerk** ohne menschliche Bewertungspersonen angeboten, und wenn ja, in welchem Umfang und mit welcher Haftungsgrenze? |
| RT-41 | Wie wird mit **Lernenden-Änderungen** an generierten Anki-Notizen und mit **substanziellen Inhaltsänderungen** (Review-Historie) umgegangen? |
| RT-42 | Dürfen Musterlösungen und Lernstand an **Drittanbieter-Chats** gehen? |
| RT-43 | Wer prüft **unabhängig und menschlich** (Lernwissenschaft; je Hochrisikodomäne eine Fachperson), und mit welchem Budget? |

---

## 8. Grenzen dieses Reviews

- **Keine Unabhängigkeit im menschlichen Sinn:** Das Red Team ist ein Agent derselben Modellfamilie wie die Workstream-Autorinnen und -Autoren. Gemeinsame blinde Flecken (z. B. bei der Lesart deutscher Rechtsdogmatik oder klinischer Praxis) sind wahrscheinlich und durch dieses Review nicht ausgeschlossen. Die Charter verlangt eine unabhängige Zweitkritik; dieses Review ersetzt sie nicht (RT-43).
- **Keine Volltexte gelesen:** Die Prüfung der Sicherheitsstufen stützt sich auf die Registereinträge der Workstreams (Zugangsstufe, Design, Schätzwert), nicht auf eigene Lektüre der Quellen. Sind Registereinträge falsch, sind es auch die Urteile.
- **Selektive Berichtslektüre:** R3, R5, R7 und R8 wurden nur abschnittsweise gelesen. Konflikte oder Lösungen, die nur im Fließtext stehen, können übersehen sein.
- **Proben statt Tests:** Die zwei Engine-Proben liefen auf einer Scratch-Kopie des PR-#43-Stands. Sie sind Belege für das Verhalten des Codes, keine Regressionstests im Repository.
- **R7 im Index als ‚in Arbeit‘ markiert:** Spätere Änderungen an R7-Policies sind nicht berücksichtigt.
- **Szenarien sind konstruiert:** Sie zeigen, dass ein Fehler möglich ist, nicht wie häufig er bei realen Lernenden auftritt.
- **Schweregrade sind Urteile des Red Teams**, keine gemessenen Größen.

---

## 9. Fragen an unabhängige Prüferinnen und Prüfer

1. Sind die sechs Überschätzungen (§2.2) aus Ihrer Kenntnis der Volltexte haltbar, insbesondere R1-POL-A02 (Beispiel vor Abruf) und R2-POL-01 (Selbsterklärungstraining für Beweise)?
2. Ist ‚Ergebnisgedächtnis bei umformulierten Items mit geringer Ergebnisvielfalt‘ (RT-13, RT-29) in Ihrer Domäne ein reales Problem? Welche Operationalisierung von ‚neues Item‘ würden Sie verlangen?
3. Recht: Darf eine Karte mit substanziell geändertem Rechtsstand die alte Review-Historie behalten (RT-12)? Welche Änderungen gelten als ‚substanziell‘?
4. Klinik: Ist Kalibrierungsfeedback auf einer Fallbank mit unrealistischer Prävalenz schädlich oder neutral (RT-14)?
5. Handwerk und Labor: Ist eine Anzeige ‚Wissen geprüft – Ausführung nicht beobachtet‘ ausreichend, um Scheinkompetenz zu verhindern (RT-17)?
6. Welche globale Rangfolge für Policy-Konflikte halten Sie für vertretbar (RT-25)? Ist ‚Sicherheit > Messintegrität > ausdrücklicher Wunsch > Didaktik > Komfort‘ richtig geordnet?
7. Welches schwächere Studiendesign würden Sie für Produktentscheidungen (nicht für Wirkungsbehauptungen) akzeptieren (RT-32)?
8. Gibt es eine Architektur, für die die in §6 genannten Experimente nicht ausreichen, um sie zu verwerfen?

---

## 10. Reproduktion

```bash
cd <r6rt-worktree>
python3 -m unittest tests.test_r6_red_team
# Sicherheitsstufen: Evidenz-IDs aus r6/policy_index.json mit den Registern an den Commits in policy_index.json.sources verknüpfen
#   git show <commit>:docs/research/workstreams/<ws>/<ws>_evidence.json
# Proben (nur lesend, Scratch-Kopie):
#   git show 5ad257d:exam_mastery/learning/expr.py   > <scratch>/expr43.py
#   git show 5ad257d:exam_mastery/learning/policy.py > <scratch>/policy43.py
#   expr.same(parse('(x^2)^(1/2)'), parse('x'), sample_points(['x']))  -> True
#   kc_status: A korrekt (Tag 1, 09:00); 'solution' für B (Tag 2, 08:00); C korrekt (Tag 2, 08:01) -> RETAINED_ON_LATER_DAY
#   kc_status: Zeitstempel des zweiten Erfolgs auf +24 h gesetzt, today davor -> RETAINED_ON_LATER_DAY
```

Es gab keine Installationen, keine bezahlten Modellaufrufe, keine Änderungen am Produktionscode und keine Merges.
