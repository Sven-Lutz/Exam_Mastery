# R2 — Formale, quantitative und computationale Kompetenz: Synthese und Learning Policies

Stand 27.11.2026. **Forschungsergebnis zur Begutachtung, keine Freigabe.** Alle 21 Policies sind `design_hypothesis` mit `learning_evaluation: NOT_RUN`. Keine Policy ist implementiert. Kein Mastery-Produkt hat dadurch eine nachgewiesene Lernwirkung. Historische `HUMAN_REJECTED`-Bewertungen bleiben unverändert.

**Produktidentität:** Seit Issue #34 heißt das Produkt **Mastery**, eine allgemeine Plattform für den Erwerb von Wissen und Fertigkeiten. Prüfungsvorbereitung ist ein optionaler Modus. R2 gilt für jede Lernsituation mit Beweisen, symbolischen Verfahren, Programmierung oder statistischem Schließen. Der Phasenwert `final_exam_week` betrifft nur den Prüfungsmodus. Issue #23 nennt die Ausgabedatei `FORMAL_COMPUTATIONAL.md`; im Programm heißt sie `R2_FORMAL_QUANTITATIVE.md`, Inhalt und Auftrag sind dieselben.

| Artefakt | Inhalt |
|---|---|
| [r2/r2_evidence.json](r2/r2_evidence.json) | Evidenzregister, 57 Einträge im R1-Schema (`r1-evidence/1`): Beweise (17), Programmierung (16), Statistik (3), symbolische Verfahren, Problemlösen und E-Assessment (4); Batch 5 (§12): Algorithmen (9), quantitatives Problemlösen und Modellieren (7), Kausalinferenz (1). Zugangsstufen: 5 Volltext teilweise, 13 Volltext-Claim-Review, 37 nur Abstract, 2 nur Metadaten. Suchprotokoll für Batch 5 (`search_log`, 21 Suchen). |
| [r2/r2_learning_policies.json](r2/r2_learning_policies.json) | 21 Policies, 6 Konfliktregeln, zurückgestellte Operationen, deklarierte Lücken, Prüfprotokoll des Leads. |
| `tests/test_r2_learning_policies.py` | Wendet den R1-Strukturvertrag auf R2 an (Quellen auflösbar, Parameter als vorläufig markiert, KB-Regelverweise existieren, Kernoperationen abgedeckt, Prüferpolicy vorhanden, Lücken deklariert; Batch 5: Suchprotokoll vollständig, jede neue Quelle zitiert oder als Lücke deklariert, neue Policies nennen alle vier Produkte). Prüft Struktur, nicht wissenschaftliche Richtigkeit. |

Arbeitsteilung: Ein Spezialistenlauf (R2) hat Register und Policies in mehreren unbeaufsichtigten Sitzungen erstellt. Dieser Bericht und die Stichprobe in §9 stammen vom Lead. Lead und Spezialist sind dasselbe Modell. Ein Ergänzungslauf (R2S) hat Batch 5 und §12 hinzugefügt, ebenfalls ohne Lead-Stichprobe. Eine menschliche oder unabhängige Fachprüfung steht aus.

**Lesart.** Jede Aussage ist einer von vier Arten zugeordnet: **Befund** (im Register mit Fundstelle belegt), **Hypothese** (plausibel aus Befunden abgeleitet, ungeprüft), **Designentscheidung** (Produktsetzung, die sich nicht empirisch begründen lässt), **nicht gestützt** (in §13 gesammelt).

## 1. Ergebnis in elf Punkten

1. **Beweiskompetenz besteht aus mindestens zwei messbaren Komponenten.** *Befund:* In einer Strukturgleichungsstudie mit 153 Studienanfängern passt ein Modell „Konstruktion“ gegen „Lesen (Verständnis + Validierung)“ am besten; die latente Korrelation liegt bei .85, und kein Modell erreicht einen akzeptablen TLI (`neuhaus2025proofskills`). *Designentscheidung:* Verständnis, Validierung und Konstruktion werden getrennt beobachtet (R2-POL-02).
2. **Selbsterklärungstraining verbessert das Verständnis gelesener Beweise.** *Befund:* Im Labor d = 0,95, im Hörsaal d = 0,41, nach 20 Tagen 0,35, alles aus einer Forschungsgruppe (`hodds2014selfexplanation`). Über Konstruktion sagen diese Studien nichts.
3. **Interaktive „e-Proofs“ halfen nicht.** *Befund:* kein Gruppenunterschied; die e-Proof-Gruppe verlor bis zum verzögerten Test sogar mehr (`roy2017eproofs`, N = 49). Multimediale Aufbereitung ist also kein Ersatz für eine aktive Lernoperation.
4. **Validieren ist eine eigene Schwäche.** *Befund (deskriptiv, klein):* Studierende akzeptieren ungültige Argumente und achten auf Oberflächenmerkmale (`selden2003validation`, N = 8; `inglis2012reading`). Fachleute sind sich bei manchen Beweisen selbst uneinig (`inglis2013standards`, N = 109). *Designentscheidung:* Validierungsitems nur mit dokumentiertem, konsentiertem Fehler (R2-POL-03).
5. **Die Wahrheit eines Satzes beweist nicht, dass jemand ihn verstanden hat.** *Befund:* Sprachmodelle mit starken Endergebnis-Scores erreichen bei vollständigen USAMO-Lösungen höchstens 30 %, die meisten unter 5 % (`petrov2025proofbluff`, Abstract). LLM-Bewerter stimmen mit Experten schlechter überein als Experten untereinander (QWK ≈ 0,63–0,66 gegen 0,76; ohne Referenz höchstens 0,53) und bewerten oft zu gut (`ospanov2026llmgrading`, Preprint). In einem engen Aufgabentyp (Induktion) gelingt automatisches Rubrik-Feedback besser (`zhao2025inductiongrading`, ca. 89–90 % Itemübereinstimmung, Tutoren 86,6 %). *Designentscheidung:* LLM-Bewertung ist nie Kompetenzbeleg (R2-POL-05, R2-CR-2).
6. **Programmieren: Tracing und Erklären hängen mit Schreiben zusammen; die Hierarchie ist korrelativ belegt.** *Befund:* Tracing einschließlich Iteration und Erklären erklären zusammen 46 % der Varianz der Schreibleistung (`lopez2008tracing`, N = 38). Eine 5–10-minütige Tracing-Strategie brachte in einem block-randomisierten Experiment +15 % bei Tracing-Aufgaben (`xie2018tracing`, N = 24).
7. **Teilziel-Beispiele helfen in Übungen, kaum in Prüfungen.** *Befund:* In einem CS1-Quasi-Experiment mit 265 Studierenden: Quiz d = 0,44, Prüfung d = 0,20 (nicht signifikant), dafür weniger Studierende mit schwacher Prüfungsleistung (25 % gegen 44 %) (`margulieux2020subgoals`). Die Replikationslage ist gemischt.
8. **Debugging lässt sich unterrichten, aber wie gut, ist offen.** *Befund (Abstract):* g = 0,64 [0,32; 0,96]; die wahren Effekte reichen von −0,54 bis 1,82, Grundlage sind 18 Artikel, viele aus der Schule (`sun2024debuggingmeta`).
9. **Autograder verändern das Verhalten; ein Lerneffekt ist nicht belegt.** *Befund:* Eine Begrenzung der Einreichungen halbierte deren Zahl, die Noten sanken kaum (`baniassad2021autograder`, Abstract). Prüfer prüfen nur, was sie prüfen: Unit-Tests erfassen weder Stil noch Begründung (`messer2024autograding`). *Designentscheidung:* Für jede Aufgabe wird der Prüfer deklariert (R2-POL-14).
10. **Statistik: simulationsbasierte Inferenz ist mit etwas höheren Gewinnen assoziiert.** *Befund (beobachtend):* 1–2 Punkte von 24 bei 10.514 Studierenden. Die Autoren nennen den Effekt „relativ klein“. Selbstselektion der Lehrenden ist möglich (`chance2022sbi`). Fehlvorstellungen zum p-Wert sind verbreitet (`castrosotos2009misconceptions`).
11. **Batch 5: Algorithmen und quantitatives Problemlösen (§12).** *Befund:* Algorithmenvisualisierung nützt eher, wenn Lernende etwas tun (vorhersagen, antworten, das Tempo steuern), als wenn sie zusehen; die Belege sind alt, klein und teils nur sekundär gelesen. Lernende beurteilen Effizienz nach Oberflächenmerkmalen wie Programmlänge (`galezer2004efficiency`, Schule). Fortgeschrittene repräsentieren Physikaufgaben über Prinzipien; der Unterschied ist aber ein Kontinuum, keine Dichotomie (`mason2011categorization`). Modellieren mit Lösungsplan wirkte in Schulstudien bis zum Follow-up. *Designentscheidung:* R2-POL-17 bis 21, alle niedrig oder sehr niedrig belegt. Für Kausalinferenz gibt es nur einen deskriptiven Befund und keine Policy, für Finanzmodellierung keine Evidenz.

## 2. Suchjournal, Ein- und Ausschluss, Zugang

**Was protokolliert ist.** Metadatenabgleich über Crossref (27 DOIs), OpenAlex (ca. 30 Werke) und Semantic Scholar (8 Abfragen), jeweils über die freien APIs am 27.11.2026. Volltextabrufe: 26 von 45 budgetierten Seitenabrufen. Den Zugangsweg und die gelesenen Abschnitte jeder Quelle enthält `access` im Register; gescheiterte Volltextwege stehen dort in `access.url`, z. B. für `hodds2014selfexplanation` (Artikel gesperrt, inhaltsgleiche Dissertation gelesen) und `neuhaus2025proofskills` (Verlagsseite blockiert, Repositoriumsfassung gelesen).

**Was fehlt (deklarierte Lücke).** Die Spezialistenläufe haben die exakten Suchstrings nicht in die Checkpoints übernommen. Eine Suchtabelle wie in R0 (`SEARCH_PROTOCOL.md` §1) lässt sich deshalb für R2 nicht nachträglich wahrheitsgemäß erstellen. Sie wird hier auch nicht rekonstruiert. Für den Ergänzungsbatch 5 sind die Suchen protokolliert (§12). Reproduzierbar sind die eingeschlossenen Quellen über DOI/URL, Zugangsstufe und gelesene Abschnitte, nicht der Suchweg. Die geplanten Suchblöcke Q1–Q5 des Auftrags (Beweis, symbolisch, Programmierung, Statistik/Kausalinferenz, Physik/Finanzmodellierung) sind nicht als formale Suche abgeschlossen (siehe `coverage_gaps`).

**Angewandte Einschlusskriterien** (aus dem Register abgeleitet, nicht vorab registriert): (a) Lernende an Hochschulen oder Übergangskurse; Schulstudien nur, wenn keine Hochschulevidenz gefunden wurde, mit Kennzeichnung; (b) Outcome ist eine formale, quantitative oder computationale Leistung oder die Validität ihrer Bewertung; (c) Experiment, Quasi-Experiment, Messstudie, Review/Metaanalyse; deskriptive und qualitative Studien nur für Defizit- oder Machbarkeitsbefunde; (d) Locator verifizierbar. **Ausgeschlossen bzw. nicht vertieft:** reine Werkzeugbeschreibungen ohne Lernenden- oder Bewertungsdaten sowie Studien zu Faktenabruf in Mathematik, die R1 abdeckt (`murray2025mathspacing`, vermutlich identisch mit ERIC EJ1478558).

**Seed-Quellen:** 10.1007/s10763-025-10621-3 = `neuhaus2025proofskills` (Volltext gelesen); 10.1145/3690652 = `yang2024debuggingslr` (Abstract); **10.1145/3501385.3543977 nicht gesichtet**; ERIC EJ1478558 vermutlich `murray2025mathspacing` (R1A-Register), für R2 nicht ausgewertet.

**Zugangstiefe nach Bereich.** Beweise: 7 von 17 auf Volltextebene. Programmierung: 2 von 16 (`margulieux2020subgoals`, `lopez2008tracing`). Statistik: 2 von 3. Symbolik/E-Assessment: 1 von 4 (`jones2015cj`, Schulmathematik). Die Programmier- und Symbolik-Policies beruhen also überwiegend auf Abstracts. Ihre Stufen sind entsprechend niedrig.

## 3. Domänenunabhängige Lernoperationsmatrix mit Pflichtprüfer

Die Zeilen sind Lernoperationen, die in allen vier R2-Operationen vorkommen. Die Pflichtprüferspalte nennt, was mindestens nötig ist, damit ein Versuch als Kompetenzbeleg nach dem R1-Messvertrag zählt. Der Messvertrag verlangt: unassistiert, nach verstrichener Zeit, neues oder umformuliertes Item. Die Zuordnung ist eine **Designentscheidung**. Die Evidenzspalte zeigt, wie weit die Studien die Operation stützen.

| Lernoperation | formal_proof | symbolic_procedure | computational_construction | empirical_experimental | Pflichtprüfer | Evidenzlage |
|---|---|---|---|---|---|---|
| Verstehen/verfolgen | Fragen zu gegebenem Beweis | Schritt begründen | Ausgabe vorhersagen, Code erklären | Verfahren/Design erklären | geschlossene Items mit Schlüssel; Freitext nur Mensch | Beweis moderat (POL-01); Tracing niedrig (POL-08) |
| Validieren/debuggen | Fehlerzeile im fremden Beweis | Fehler in Umformung | Fehler eingrenzen, minimaler Testfall | Fehlinterpretation erkennen | konsentierter Fehlerschlüssel + Begründung durch Mensch | niedrig (POL-03, POL-12, POL-16) |
| Konstruieren | eigener Beweis | Rechnung/Herleitung | Programm schreiben | Analyse planen und durchführen | Beweis: Mensch-Rubrik/CJ oder Beweisassistent (nur formale Variante); Symbolik: CAS je Schritt; Code: verborgene + Property-Tests | sehr niedrig bis niedrig |
| Methode wählen/begründen | Beweisstrategie | Verfahren, physikalisches Prinzip | Algorithmus/Datenstruktur, Komplexität | Test/Modell, Modellannahmen | Mensch; Prinzipschlüssel nur als Proxy (POL-20) | Physik-Repräsentation niedrig (POL-20); Komplexität und Modellieren sehr niedrig (POL-19, POL-21) |
| Voraussetzung prüfen, Gegenbeispiel | Hypothesen des Satzes | Definitionsbereich | Randfälle | Annahmen des Tests | Gegenbeispiel maschinell prüfbar, Begründung Mensch | indirekt (POL-06) |

Nicht übertragbar: Für `diagnostic_reasoning`, `spatial_design` und `embodied_psychomotor` hat R2 nichts untersucht (R4). Für `rule_based_contextual` und `open_synthesis` ist R3 zuständig.

## 4. Verifier-Matrix und die falsche Gleichsetzung von Wahrheit und didaktischer Gültigkeit

**Drei verschiedene Fragen** werden in formalen Fächern oft verwechselt:
1. *Ist die Aussage wahr?* Das kann ein Orakel, eine Bibliothek oder eine Referenzlösung entscheiden.
2. *Ist die vorgelegte Begründung gültig?* Das kann nur ein Beweisassistent bei formalisierten Beweisen entscheiden, sonst ein Mensch.
3. *Hat diese lernende Person die Fähigkeit, die das Item messen soll?* Das ist eine Validitätsfrage über Item, Bedingungen und Wiederholung, keine Eigenschaft einer einzelnen Antwort.

Ein Orakel für (1) sagt nichts über (2). Ein Prüfer für (2) sagt wenig über (3), wenn das Item gesehen, assistiert oder sofort wiederholt wurde. Auch ein maschinell verifizierter Lean-Beweis ist kein Beleg für das Verständnis des Papierbeweises (`iannone2023lean`, `thoma2022lean`: nur deskriptiv). Das regeln R2-POL-07 und R2-CR-4.

| Prüfer | Prüft | Prüft nicht | Kompetenzbeleg? | Belege |
|---|---|---|---|---|
| Algebraisches Orakel / CAS-Äquivalenz | Äquivalenz von Ausdrücken, je Teilschritt | Methodenwahl, Begründung; unentscheidbare Äquivalenzen | ja für den geprüften Schritt, wenn Item neu ist | `pelkola2018stack` (Abstract), `kinnear2022eassessment` (Agenda) |
| Numerische Einzelwertprüfung | ein Zahlenwert innerhalb Toleranz | Lösungsmenge, Weg, Einheiten, Vollständigkeit | nein allein (R2-POL-06) | Messproblem, keine Lernstudie |
| Beweisassistent | formale Gültigkeit des formalisierten Beweises | Papierbeweis, Verständnis, Formalisierungstreue der Aussage | nur für die formale Variante | `iannone2023lean`, `mahinpei2025itp` (Abstract) |
| Sichtbare Unit-Tests | Verhalten auf bekannten Fällen | Generalisierung (Hardcoding), Stil, Begründung | nein (Feedback) | `messer2024autograding`, `baniassad2021autograder` |
| Verborgene / neu erzeugte Tests, Property-Tests | Verhalten auf unbekannten Fällen bzw. Eigenschaften | Spezifikationsfehler, Lesbarkeit | ja für Funktionsverhalten | `wrenn2021pbt`, `milovancevic2025formalgrading` (Erfahrungsberichte) |
| Menschliche Rubrik | Gültigkeit und Vollständigkeit der Begründung | — (Kosten, Rater-Drift) | ja | `mejia2012proofassessment`, `jones2015cj` (Marking r = .91) |
| Comparative Judgement (Mensch) | relative Qualität offener Antworten | absolute Schwelle | ja, mit Reliabilitätsangabe | `davies2020cjproof` (SSR .86, aber r = .28 zu MC), `jones2015cj` |
| LLM-Bewertung | Hinweis auf mögliche Lücken | Gültigkeit verlässlich; neigt zu Überbewertung | **nie** (`agent_judgement`) | `ospanov2026llmgrading`, `zhao2025inductiongrading`, `petrov2025proofbluff` |
| Keiner | — | — | nein; nur Übungsprotokoll | R2-POL-14 |

Vier weitere Prüfer aus Batch 5 (Zustandsorakel, Laufzeit-Zusicherung, Operationszähler, Prinzipschlüssel) stehen in §12.3.

Bemerkenswert ist `davies2020cjproof`: Comparative Judgement für Beweiszusammenfassungen ist reliabel (SSR .86), korreliert aber nur schwach mit einem MC-Verständnistest (r = .28) und der Kursnote (r = .23). Reliabilität ist keine Validität. Welche Messung das Konstrukt besser trifft, ist offen.

## 5. Policies mit Mechanismuskette

Kette je Policy: Evidenz → Lernoperation → Intervention → Beobachtung im Produkt → unabhängiges Lernoutcome → Versagen/Gegenbefund. Erzeugt aus `r2/r2_learning_policies.json`; Relation und Zugangsstufe je Quelle in Klammern. Alle Parameter sind vorläufige Produktsetzungen.

### R2-POL-01 — Selbsterklärungstraining vor dem Lesen von Beweisen (Beweisverständnis)

*Operationen:* formal_proof; *Vorwissen:* novice, intermediate; *Phase:* acquisition. *Stufe:* moderat (Labor-RCT und Klassenraumstudie mit gleicher Richtung; eine Forschungsgruppe, kleine Stichproben, kurzer Messabstand).

- **Evidenz:** `hodds2014selfexplanation` (supports, fulltext_partial); `alcock2015notices` (supports, fulltext_claim_review); `mejia2012proofassessment` (context_only, metadata)
- **Intervention:** Vor dem ersten Beweislesen ein kurzes, generisches Selbsterklärungstraining (Beispiel: jede Zeile mit Begründung aus vorherigen Zeilen oder Vorwissen verknüpfen; Gegenbeispiel: Paraphrase). Danach Beweise mit Selbsterklärungsprompts lesen; Antworten mit Referenzerklärung abgleichen (R1-POL-A06).
- **Beobachtung im Produkt:** Antworten auf Selbsterklärungsprompts (Freitext, unverifiziert), Lesezeit, Verständnisitems
- **Unabhängiges Lernoutcome:** unassistierter Beweisverständnistest (Itemtypen nach Mejia-Ramos et al.) an neuem Beweis >= 1 Woche später
- **Versagen/Gegenbefund:** Prompts werden mit Paraphrasen beantwortet; Training wird übersprungen; Messung nur mit bereits gesehenem Beweis. Falsifikator: In einer vorab registrierten Randomisierung (Training vs. gleichlange Kontrolllektüre) zeigt der verzögerte Verständnistest an neuen Beweisen keinen Unterschied oberhalb einer festgelegten Mindestdifferenz.
- **Enthaltung:** keine Mastery-Aussage über Beweiskonstruktion aus Verständnisitems (R2-POL-02); keine automatische Bewertung freier Selbsterklärungen als richtig (SE-R2); bei Fortgeschrittenen optional, nicht verpflichtend

### R2-POL-02 — Beweisverständnis, -validierung und -konstruktion getrennt messen und berichten

*Operationen:* formal_proof; *Vorwissen:* alle; *Phase:* acquisition, consolidation, final_exam_week. *Stufe:* niedrig (eine Querschnittsstudie, Faktorlösung ohne akzeptablen Fit; hohe latente Korrelation spricht auch für Zusammenlegung; Trennung ist primär eine Validitätsvorsicht).

- **Evidenz:** `neuhaus2025proofskills` (supports, fulltext_claim_review); `neuhaus2025proofskills` (qualifies, fulltext_claim_review); `davies2020cjproof` (supports, fulltext_claim_review)
- **Intervention:** Der Lernstand führt drei getrennte Beobachtungen: Verständnis (Fragen zu gegebenem Beweis), Validierung (Urteil plus Begründung zu einem vorgelegten, ggf. fehlerhaften Beweis) und Konstruktion (eigener Beweis). Fortschritt in einer Komponente wird nicht als Fortschritt der anderen angezeigt.
- **Beobachtung im Produkt:** Versuchslog je Komponente
- **Unabhängiges Lernoutcome:** unassistierte, verzögerte Konstruktionsaufgabe, unabhängig von menschlicher Expertin/Experte bewertet
- **Versagen/Gegenbefund:** Komponentenetikett falsch vergeben; Konstruktion wird nur über Lückentext 'beobachtet'. Falsifikator: Wenn in einer Lernendenstichprobe die Konstruktionsleistung aus Verständnis- und Validierungswerten mit einem vorab festgelegten Fehler (z. B. r >= .95 auf Personenebene) vorhergesagt wird, ist die getrennte Führung unnötig.
- **Enthaltung:** wenn keine Konstruktionsaufgabe mit gültigem Prüfer existiert: Konstruktion als 'nicht beobachtet' ausweisen; keine Gesamtnote 'Beweisen' aus einer Komponente

### R2-POL-03 — Validierungsübungen mit fehlerhaften Beweisen und konsentierten Fehlern

*Operationen:* formal_proof; *Vorwissen:* novice, intermediate; *Phase:* acquisition, consolidation. *Stufe:* niedrig (Defizitbefund deskriptiv, kleine Stichproben; Intervention selbst nicht experimentell geprüft).

- **Evidenz:** `selden2003validation` (supports, abstract); `inglis2012reading` (supports, abstract); `inglis2013standards` (qualifies, abstract); `weber2013skimming` (qualifies, abstract)
- **Intervention:** Vorgelegte Beweise beurteilen lassen (gültig/ungültig, Fehlerzeile, Begründung). Nur Items mit fachlich eindeutigem, dokumentiertem Fehler verwenden; nach dem Urteil Referenzbegründung zeigen.
- **Beobachtung im Produkt:** Urteil, Fehlerzeile, Begründung (Begründung unverifiziert, außer Referenzabgleich durch Mensch)
- **Unabhängiges Lernoutcome:** verzögerter unassistierter Validierungstest mit neuen fehlerhaften Beweisen
- **Versagen/Gegenbefund:** Lernende lernen Fehlermuster der Itembank statt Prüfens; uneindeutige Items erzeugen falsches Feedback. Falsifikator: Randomisierter Vergleich (Validierungsübung vs. gleichlange Beweislektüre) zeigt bei verzögerter Validierung neuer Beweise keinen Vorteil.
- **Enthaltung:** keine Items, bei denen Fachleute uneinig sind (inglis2013standards); Validierungsurteil allein (ohne Begründung) zählt nicht als Beleg; keine Behauptung, Validierungsübung verbessere Konstruktion

### R2-POL-04 — Beweiskonstruktion: heuristische Lösungsbeispiele abhängig vom Vorwissen

*Operationen:* formal_proof, symbolic_procedure; *Vorwissen:* novice, intermediate; *Phase:* acquisition. *Stufe:* sehr niedrig (Hauptbeleg aus Schulmathematik und altem Meta-Review; Hochschulexperiment nur im Abstract gelesen, Effekte konditional).

- **Evidenz:** `hembree1992problemsolving` (supports, abstract); `kollar2014argumentation` (qualifies, abstract)
- **Intervention:** Heuristische Lösungsbeispiele zeigen den Suchprozess (Ziel umformen, Spezialfälle, Darstellung wechseln, Rückwärtsarbeiten) und nicht nur den fertigen Beweis; danach eigene Konstruktion mit gestuften Hinweisen (AI-R1). Für Lernende mit geringem Vorwissen stärker strukturieren; Wirkung je Vorwissen beobachten.
- **Beobachtung im Produkt:** Konstruktionsversuche mit Hinweisstufe, verwendete Heuristik (selbstberichtet)
- **Unabhängiges Lernoutcome:** unassistierte Konstruktion eines neuen Beweises nach >= 1 Woche, Bewertung durch Mensch mit Rubrik oder CJ
- **Versagen/Gegenbefund:** Beispiele werden memoriert; Hinweise ersetzen Suche. Falsifikator: Randomisierter Vergleich heuristischer vs. nur fertiger Beispiele zeigt in keiner Vorwissensgruppe einen Vorteil bei verzögerter Konstruktion.
- **Enthaltung:** kein Fading-Automatismus ohne Erster-Schritt-Probe (R1-POL-A03); keine Wirksamkeitsbehauptung für Hochschulbeweise ohne Evaluation

### R2-POL-05 — Bewertung offener Beweise: kein automatischer Kompetenzbeleg

*Operationen:* formal_proof; *Vorwissen:* alle; *Phase:* acquisition, consolidation, final_exam_week. *Stufe:* moderat (mehrere unabhängige Gruppen zeigen Lücke zwischen LLM- und Expertenbewertung; Modelle ändern sich schnell; Zahlen veralten).

- **Evidenz:** `ospanov2026llmgrading` (supports, fulltext_partial); `zhao2025inductiongrading` (qualifies, fulltext_claim_review); `zhao2025inductiongrading` (supports, fulltext_claim_review); `petrov2025proofbluff` (supports, abstract); `davies2020cjproof` (qualifies, fulltext_claim_review); `jones2015cj` (qualifies, fulltext_claim_review)
- **Intervention:** Automatische (LLM-)Bewertung offener Beweise ist Feedback-Hinweis mit Kennzeichnung 'agent_judgement', nie Kompetenzbeleg. Wenn genutzt: nur mit Referenzlösung und Bewertungsschema, enger Aufgabentyp (z. B. Induktion), Überbewertungs-Prüfung. Kompetenzbelege für Konstruktion stammen aus menschlicher Bewertung (Rubrik oder Comparative Judgement) oder formaler Verifikation (R2-POL-07).
- **Beobachtung im Produkt:** Bewertungsquelle je Versuch (deterministisch / agent_judgement / Mensch)
- **Unabhängiges Lernoutcome:** unabhängige menschliche Zweitbewertung einer Stichprobe; Übereinstimmungsmaß vorab festgelegt
- **Versagen/Gegenbefund:** Kennzeichnung verschwindet in Aggregaten; Lernende optimieren auf Bewerter statt Beweis. Falsifikator: Wenn ein automatischer Bewerter auf einer neuen, vorab registrierten Stichprobe des Kurses die menschliche Inter-Rater-Übereinstimmung erreicht und keinen systematischen Überbewertungsbias zeigt, ist die Abstufung zu lockern.
- **Enthaltung:** kein Bestehen-Status aus LLM-Bewertung; keine LLM-Bewertung ohne Referenz ('blind'); bei Uneinigkeit von Bewertung und Lernenden: als ungeklärt markieren

### R2-POL-06 — Adversariale Aufgaben: Endergebnis, Wahrheit des Satzes und Erkennen genügen nicht

*Operationen:* formal_proof, symbolic_procedure, computational_construction, empirical_experimental; *Vorwissen:* alle; *Phase:* acquisition, consolidation, final_exam_week. *Stufe:* niedrig (Belege zeigen das Messproblem, nicht die Lernwirkung adversarialer Aufgaben).

- **Evidenz:** `petrov2025proofbluff` (supports, abstract); `selden2003validation` (supports, abstract); `castrosotos2009misconceptions` (supports, abstract)
- **Intervention:** Jede Kompetenz erhält mindestens eine Aufgabe, die Faktenabruf, generisches MC und reine Zahlenprüfung bricht: Begründung des Schritts, Voraussetzung prüfen, Gegenbeispiel finden, Fehler in fremder Lösung lokalisieren, Wahl der Methode begründen. Ein wahres Ergebnis mit ungültiger Begründung gilt als nicht gelöst; ein korrekter Beweis eines Satzes belegt nicht, dass Lernende ihn verstanden haben.
- **Beobachtung im Produkt:** Getrennte Korrektheit von Ergebnis und Begründung
- **Unabhängiges Lernoutcome:** verzögerte unassistierte Transferaufgabe mit verändertem Kontext (TR-R1)
- **Versagen/Gegenbefund:** Aufgaben werden zu Rätseln ohne Lernziel; Begründungsfelder werden mit Floskeln gefüllt. Falsifikator: Wenn in Pilotdaten Ergebnis- und Begründungskorrektheit nahezu vollständig übereinstimmen (vorab festgelegte Schwelle), liefert die Trennung keine Information.
- **Enthaltung:** Begründungsteil ohne gültigen Prüfer: als unverifiziert führen, nicht als bestanden; keine MC-Items, deren Distraktoren durch Oberflächenmerkmale ausschließbar sind

### R2-POL-07 — Beweisassistenten nur optional und mit expliziter Syntaxhilfe

*Operationen:* formal_proof; *Vorwissen:* intermediate, advanced; *Phase:* acquisition, consolidation. *Stufe:* sehr niedrig (nur deskriptive und Selbstberichtsstudien, Selbstselektion).

- **Evidenz:** `iannone2023lean` (supports, abstract); `mahinpei2025itp` (qualifies, abstract); `thoma2022lean` (context_only, abstract)
- **Intervention:** Beweisassistenten nicht als Standardweg; als optionale Übung mit vorgefertigter Umgebung, Syntaxspickzettel und Verknüpfung zum Papierbeweis anbieten. Ein maschinell geprüfter Beweis belegt die Gültigkeit des formalen Beweises, nicht das Verständnis oder die Papierbeweis-Kompetenz.
- **Beobachtung im Produkt:** Nutzung, Abbruchpunkte, geprüfte Beweise
- **Unabhängiges Lernoutcome:** Papierbeweis-Konstruktion an neuer Aufgabe, menschlich bewertet
- **Versagen/Gegenbefund:** Werkzeugkampf verdrängt Mathematik; Taktik-Automatisierung ersetzt Beweisidee. Falsifikator: Ein randomisierter Vergleich mit Papierbeweis-Endpunkt zeigt einen klaren Vorteil der Assistenznutzung auch bei Novizen; dann wäre 'optional' zu schwach.
- **Enthaltung:** keine Pflichtnutzung; keine Lernwirkungsbehauptung; Assistent-Erfolg zählt nur als Beleg formaler Gültigkeit

### R2-POL-08 — Programme verfolgen und erklären vor dem Schreiben

*Operationen:* computational_construction; *Vorwissen:* novice; *Phase:* acquisition. *Stufe:* niedrig (Kausalbeleg nur aus kleiner Studie; Hierarchie korrelativ).

- **Evidenz:** `xie2018tracing` (supports, abstract); `lister2004tracing` (supports, abstract); `lopez2008tracing` (supports, fulltext_claim_review); `lopez2008tracing` (qualifies, fulltext_claim_review)
- **Intervention:** Vor Schreibaufgaben: Ausgabe vorhersagen (Tracing) mit expliziter Strategie (Variablentabelle), dann Code in Alltagssprache erklären; erst danach schreiben. Tracing-Schwächen diagnostisch nutzen, nicht als Endziel.
- **Beobachtung im Produkt:** Vorhersage vs. tatsächliche Ausgabe; Erklärung (unverifiziert)
- **Unabhängiges Lernoutcome:** verzögerte unassistierte Schreibaufgabe mit verborgenen Tests
- **Versagen/Gegenbefund:** Tracing wird zur Routineübung ohne Bezug; Erklärungen werden nicht geprüft. Falsifikator: Randomisierter Vergleich (Tracing-zuerst vs. direkt schreiben, gleiche Zeit) zeigt keinen Vorteil bei verzögerten Schreibaufgaben.
- **Enthaltung:** keine Schreibkompetenz aus Tracing-Erfolg ableiten; Fortgeschrittene mit bestandener Tracing-Probe überspringen

### R2-POL-09 — Teilziel-beschriftete Lösungsbeispiele für Programmieranfänger

*Operationen:* computational_construction; *Vorwissen:* novice; *Phase:* acquisition. *Stufe:* niedrig (gemischte Replikation, quasi-experimentell; Prüfungseffekt nicht signifikant).

- **Evidenz:** `margulieux2020subgoals` (supports, fulltext_claim_review); `morrison2015subgoals` (contradicts, abstract); `muldner2023workedexamples` (context_only, abstract)
- **Intervention:** Lösungsbeispiele mit Teilziel-Beschriftungen (z. B. 'Akkumulator initialisieren') anbieten, danach Aufgaben mit gleichen Teilzielen; Fading nach R1-POL-A03.
- **Beobachtung im Produkt:** Fehler je Teilziel
- **Unabhängiges Lernoutcome:** verzögerte unassistierte Schreibaufgabe mit verborgenen Tests
- **Versagen/Gegenbefund:** Beschriftungen werden ignoriert; Teilziele zementieren eine Lösungsform. Falsifikator: Vorab registrierter Vergleich mit und ohne Beschriftung zeigt bei verzögerten Schreibaufgaben keinen Unterschied.
- **Enthaltung:** Wirkung auf Prüfungsleistung unsicher: nicht als Hauptmaßnahme verkaufen; keine starre Vorgabe für Fortgeschrittene

### R2-POL-10 — Parsons-Aufgaben als effiziente Übung, nicht als Schreibnachweis

*Operationen:* computational_construction; *Vorwissen:* novice; *Phase:* acquisition. *Stufe:* niedrig (eine Vergleichsstudie im Abstract; Review nennt viele unbelegte Nutzenbehauptungen).

- **Evidenz:** `ericson2017parsons` (supports, abstract); `ericson2022parsonswg` (context_only, abstract)
- **Intervention:** Parsons-Aufgaben (Codezeilen ordnen, mit Distraktoren) als zeitsparende Übung anbieten; Kompetenz im Schreiben nur über freie Schreibaufgaben belegen.
- **Beobachtung im Produkt:** Lösezeit, Versuche
- **Unabhängiges Lernoutcome:** verzögerte freie Schreibaufgabe
- **Versagen/Gegenbefund:** Ausschlussraten statt Verständnis; Distraktoren zu offensichtlich. Falsifikator: Ein randomisierter Vergleich zeigt bei gleicher Zeit schlechtere verzögerte Schreibleistung nach Parsons als nach Schreibübungen.
- **Enthaltung:** Parsons-Erfolg zählt nicht als Schreibbeleg; keine Überlegenheitsbehauptung

### R2-POL-11 — Vorhersagen vor Ausführen (Predict-Run-Investigate-Modify-Make)

*Operationen:* computational_construction, empirical_experimental; *Vorwissen:* novice; *Phase:* acquisition. *Stufe:* niedrig (eine große Schulstudie, Zuteilung nicht gelesen, Hochschulpopulation abweichend).

- **Evidenz:** `sentance2019primm` (supports, abstract)
- **Intervention:** Vor Ausführen von Code oder einer Simulation eine schriftliche Vorhersage verlangen, dann ausführen, untersuchen, verändern, selbst erstellen.
- **Beobachtung im Produkt:** Vorhersage vs. Ergebnis
- **Unabhängiges Lernoutcome:** verzögerte Schreib- und Erklärungsaufgabe
- **Versagen/Gegenbefund:** Vorhersagen werden geraten; Ablauf wird mechanisch. Falsifikator: Randomisierter Hochschulvergleich mit/ohne Vorhersageschritt zeigt keinen Unterschied in verzögerten Aufgaben.
- **Enthaltung:** Vorhersage nicht bewerten, nur protokollieren; keine Konfidenzabfrage bei jeder Vorhersage (R1 CR-5)

### R2-POL-12 — Debugging ausdrücklich unterrichten

*Operationen:* computational_construction; *Vorwissen:* novice, intermediate; *Phase:* acquisition, consolidation. *Stufe:* niedrig (Meta-Analyse nur im Abstract, sehr breiter Vorhersagebereich; Heterogene Interventionen).

- **Evidenz:** `sun2024debuggingmeta` (supports, abstract); `sun2024debuggingmeta` (qualifies, abstract); `yang2024debuggingslr` (supports, abstract); `michaeli2019debugging` (supports, abstract)
- **Intervention:** Systematisches Debugging als eigenes Lernziel: Hypothese bilden, Fehler eingrenzen, minimalen Testfall bauen, Ursache benennen. Übungen mit eingebauten Fehlern verschiedener Typen; Werkzeug-Ausgaben erklären lassen.
- **Beobachtung im Produkt:** Lokalisierungszeit, Hypothesen, Erfolg ohne Hilfe
- **Unabhängiges Lernoutcome:** verzögerte unassistierte Debugging-Aufgabe mit neuem Fehlertyp
- **Versagen/Gegenbefund:** nur Syntaxfehler geübt; Werkzeug macht die Arbeit. Falsifikator: Vorab registrierter Vergleich zeigt keinen Vorteil bei verzögerten Debugging-Aufgaben mit neuen Fehlern.
- **Enthaltung:** keine Lösungsanzeige vor eigenem Lokalisierungsversuch (RP-R2); Selbstwirksamkeitsgewinne nicht als Kompetenz zählen

### R2-POL-13 — Autograder und Orakel: begrenzte Einreichungen, eigene Tests, verborgene Prüfungen

*Operationen:* computational_construction, symbolic_procedure; *Vorwissen:* alle; *Phase:* acquisition, consolidation, final_exam_week. *Stufe:* niedrig (Verhaltensänderung belegt, Lerneffekt nicht).

- **Evidenz:** `baniassad2021autograder` (supports, abstract); `messer2024autograding` (supports, abstract); `milovancevic2025formalgrading` (supports, abstract); `wrenn2021pbt` (context_only, abstract)
- **Intervention:** Sichtbare Tests als Feedback, Kompetenzbeleg nur über verborgene oder neu erzeugte Tests; Einreichungen begrenzen oder verteuern; vor dem Einreichen eigene Tests verlangen; Bewertung deckt nur ab, was der Prüfer prüft (Stil, Lesbarkeit, Begründung sonst unverifiziert).
- **Beobachtung im Produkt:** Einreichungsanzahl, eigene Tests, Ergebnis verborgener Tests
- **Unabhängiges Lernoutcome:** verzögerte Aufgabe ohne Autograder, mit verborgenen Tests bewertet
- **Versagen/Gegenbefund:** Frustration und Abbruch; Tests zu schwach, falsch-positive Bestanden. Falsifikator: Randomisierter Vergleich mit/ohne Limit zeigt keinen Unterschied in verzögerten Leistungen ohne Autograder.
- **Enthaltung:** Bestehen sichtbarer Tests zählt nicht als Kompetenz; kein Belohnen von Trial-and-Error-Einreichungen

### R2-POL-14 — Pflicht-Prüferdeklaration je Aufgabe (Verifier-Matrix)

*Operationen:* formal_proof, symbolic_procedure, computational_construction, empirical_experimental; *Vorwissen:* alle; *Phase:* acquisition, consolidation, final_exam_week. *Stufe:* normativ (Validitätsgrenze des Lernstands; keine empirische Lernwirkung beansprucht).

- **Evidenz:** `messer2024autograding` (supports, abstract); `ospanov2026llmgrading` (supports, fulltext_partial); `milovancevic2025formalgrading` (supports, abstract); `pelkola2018stack` (qualifies, abstract); `kinnear2022eassessment` (context_only, abstract)
- **Intervention:** Jede Aufgabe deklariert ihren Prüfer (algebraisches Orakel/CAS, Beweisassistent, Unit-Tests, Property-Tests, Rubrik mit Mensch, Expertenurteil, keiner) und welchen Teil der Antwort er prüft. Fortschritt zählt nur für geprüfte Teile; der Rest bleibt 'unverifiziert'.
- **Beobachtung im Produkt:** Prüferfeld je Aufgabe, Anteil geprüfter Beobachtungen
- **Unabhängiges Lernoutcome:** Audit: Stichprobe von Aufgaben mit menschlicher Prüfung, ob Deklaration zutrifft
- **Versagen/Gegenbefund:** Deklaration falsch; zu viele unverifizierte Aufgaben ohne Hinweis. Falsifikator: Wenn ein Audit zeigt, dass deklarierte Prüfer regelmäßig andere Teile prüfen als angegeben, ist die Deklaration ohne Prüfung wertlos und muss technisch erzwungen werden.
- **Enthaltung:** fehlender Prüfer: kein Kompetenzbeleg, nur Übungsprotokoll; kein Ersatz eines Prüfers durch einen schwächeren ohne Kennzeichnung

### R2-POL-15 — CAS-gestützte Schrittprüfung für symbolische Verfahren

*Operationen:* symbolic_procedure; *Vorwissen:* alle; *Phase:* acquisition, consolidation. *Stufe:* niedrig (eine Studie im Abstract; offene Forschungsagenda).

- **Evidenz:** `pelkola2018stack` (supports, abstract); `kinnear2022eassessment` (context_only, abstract)
- **Intervention:** Eingaben je Teilschritt per CAS auf Äquivalenz prüfen; typische Fehler (Vorzeichen, Kettenregel, Einheiten) deterministisch erkennen und benennen; Endergebnis allein reicht nicht für Kompetenz.
- **Beobachtung im Produkt:** Schrittkorrektheit, Fehlertyp
- **Unabhängiges Lernoutcome:** verzögerte unassistierte Aufgabe auf Papier oder ohne Schrittprüfung
- **Versagen/Gegenbefund:** Eingabesyntax wird zur Hürde; Lernende raten Äquivalente. Falsifikator: Randomisierter Vergleich (Schrittprüfung vs. nur Endergebnis) zeigt keinen verzögerten Vorteil.
- **Enthaltung:** Bei nicht entscheidbarer Äquivalenz: unverifiziert; keine Bewertung der Methodenwahl durch CAS

### R2-POL-16 — Statistisches Schließen: simulationsbasierte Inferenz und gezielte Fehlvorstellungen

*Operationen:* empirical_experimental; *Vorwissen:* novice; *Phase:* acquisition, consolidation. *Stufe:* niedrig (nur Beobachtungsstudien, kleine Effekte).

- **Evidenz:** `tintle2012retention` (supports, fulltext_claim_review); `tintle2012retention` (qualifies, fulltext_claim_review); `chance2022sbi` (qualifies, fulltext_claim_review); `castrosotos2009misconceptions` (supports, abstract)
- **Intervention:** Inferenz über Randomisierung und Simulation einführen (Nullmodell simulieren, p-Wert als Anteil), dann formale Verfahren; bekannte Fehlvorstellungen (p-Wert als Wahrscheinlichkeit der Hypothese, Signifikanz als Effektgröße) mit Diagnose-Items gezielt und wiederholt prüfen.
- **Beobachtung im Produkt:** Antworten auf Fehlvorstellungs-Items mit Begründung
- **Unabhängiges Lernoutcome:** verzögertes unassistiertes Konzeptinventar mit neuen Items
- **Versagen/Gegenbefund:** Simulation wird bloß bedient; Items werden auswendig gelernt. Falsifikator: Randomisierter Vergleich SBI vs. konventionell zeigt keinen verzögerten Vorteil im Konzeptinventar.
- **Enthaltung:** keine Behauptung großer Effekte (Unterschied 1-2 Punkte von 24); keine Kausalinterpretation der Kohortenstudien

## 6. Konfliktregeln

- **R2-CR-1** (POL-08, POL-09, R1-A02): Programmieranfänger erhalten zuerst eine Tracing-Probe. Wer sie besteht, beginnt mit Teilziel-Beispielen, die anderen mit Tracing-Übung.
- **R2-CR-2** (POL-05, POL-14): LLM-Bewertung ist immer `agent_judgement` und nie Kompetenzbeleg.
- **R2-CR-3** (POL-13, R1-A08): Korrektives Feedback nach jedem Versuch bleibt. Das Einreichungslimit begrenzt nur Orakelaufrufe, keine Erklärungen.
- **R2-CR-4** (POL-07, POL-02): Ein maschinell geprüfter Beweis belegt Konstruktion nur in der formalen Variante.

Gemeinsamer Messvertrag: Übernahme aus R1, ergänzt um die Prüferdeklaration nach R2-POL-14. Ein Teil einer Antwort ohne deklarierten gültigen Prüfer ist `unverifiziert` und zählt nicht.

## 7. Synthetisches Fallbeispiel und adversariale Aufgaben

Alle Beispiele sind für diesen Bericht erfunden. Sie stammen nicht aus Vorlesungsmaterial.

### 7.1 Durchgerechneter Fall: Induktionsbeweise in einem Einführungskurs

Eine lernende Person (Novize, Übergang zur Beweismathematik) arbeitet am Kompetenzziel „Beweise durch vollständige Induktion verstehen, prüfen und führen“.

1. **Vorwissensprobe:** Die Person soll den ersten Schritt eines Induktionsbeweises für Σ_{k=1}^{n} (2k−1) = n² nennen. Sie scheitert → Beispielpfad (R1-A02/A03). Erst eine wiederholte Erste-Schritt-Probe entscheidet über das Fading.
2. **Verständnis (POL-01):** 15-minütiges Selbsterklärungstraining, danach ein gegebener Beweis mit Prompts „Warum folgt Zeile 4 aus Zeile 3?“. *Beobachtung:* Freitextantworten werden mit der Referenzerklärung abgeglichen und als unverifiziert protokolliert. Dazu kommen geschlossene Verständnisitems mit Schlüssel → Komponente *Verständnis*.
3. **Validierung (POL-03):** Ein vorgelegter „Beweis“, dass 2ⁿ > n² für alle n ≥ 1 gilt. Der Anfang n = 1 stimmt, und der Induktionsschritt wirkt plausibel. Er braucht aber n² ≥ 2n + 1, gilt also erst ab n = 3. Die Aussage scheitert bei n = 2, 3, 4 und gilt erst ab n = 5. Gefordert sind Urteil, Fehlerzeile und Begründung. Urteil und Fehlerzeile werden gegen den Schlüssel geprüft, die Begründung von einem Menschen oder bleibt unverifiziert → Komponente *Validierung*.
4. **Konstruktion (POL-04, POL-05):** eigener Beweis für 3 | n³ − n. Ein LLM-Feedback darf auf eine fehlende Begründung im Induktionsschritt hinweisen, ist aber als `agent_judgement` gekennzeichnet. Kompetenzbeleg wird der Beweis erst durch Rubrikbewertung einer Lehrperson. Gibt es keinen menschlichen Prüfer, wird die Komponente *Konstruktion* als **nicht beobachtet** ausgewiesen (POL-02).
5. **Spätere Prüfung (R1-Messvertrag):** Nach mindestens einer Woche folgt ein neues Item, etwa 4ⁿ − 1 durch 3 teilbar, unassistiert. Nur dieses Ergebnis zählt für den Lernstand.

*Anzeige:* „Verständnis: belegt (2 Items, verzögert); Validierung: 1 Item, Begründung unverifiziert; Konstruktion: nicht beobachtet.“ Eine Gesamtnote „Induktion gemeistert“ erscheint nicht.

### 7.2 Adversariale Aufgaben (brechen Faktenabruf, generisches MC und Einzelzahlprüfung)

| Bereich | Aufgabe | Was sie bricht |
|---|---|---|
| Beweis, wahre Aussage, ungültiger Beweis | „Zeige Σ_{k=1}^{n} k = n(n+1)/2.“ Antwort: Prüfung für n = 1, 2, 3, dann „also allgemein“. | Ein Prüfer, der nur die Wahrheit der Aussage oder das Endergebnis prüft, akzeptiert die Antwort. Nach POL-06 gilt sie als **nicht gelöst**. |
| Beweis, falsche Verallgemeinerung | „n² + n + 41 ist für alle n ≥ 0 prim. Beweise oder widerlege.“ | Fallprüfung bis n = 39 stützt die Behauptung; n = 40 liefert 41². Verlangt ist ein Gegenbeispiel, nicht das Abrufen eines Satzes. |
| Symbolik, Einzelzahlprüfung | „Löse x² = 2x.“ Antwort „x = 2“ (durch x geteilt). | Ein Prüfer, der nur einsetzt, akzeptiert x = 2. Die Lösungsmenge {0, 2} ist unvollständig. Nötig ist der Prüfer „Mengenvergleich“, nicht „Einsetzprobe“. |
| Symbolik, Voraussetzung | „Berechne ∫_{−1}^{1} x⁻² dx.“ Rechnung mit Stammfunktion ergibt −2. | Wer nur das Ergebnis mit einem naiven Rechenweg vergleicht, übersieht die Divergenz. Das Item prüft die Voraussetzung (Stetigkeit). |
| Programmierung, Hardcoding | `median(xs)`: Die sichtbaren Tests nutzen nur ungerade Längen. | Eine Lösung ohne Mittelwertbildung bei gerader Länge besteht die sichtbaren Tests. Property-Test: Median liegt zwischen min und max und ist invariant unter Permutation; verborgene Tests mit gerader Länge (POL-13). |
| Programmierung, Tracing statt Abruf | Vorhersage der Ausgabe einer Schleife mit Aliasing zweier Listen | MC-Distraktoren, die sich an Oberflächenmerkmalen ausschließen lassen, sind unzulässig. Gefragt ist eine freie Vorhersage mit Variablentabelle. |
| Statistik, Fehlvorstellung | „p = 0,03. Welche Aussage folgt?“, Distraktor „Die Nullhypothese ist mit 3 % Wahrscheinlichkeit wahr.“ Dazu: „p = 0,40, also kein Effekt?“ | Das bricht reines Definitionswissen. Der zweite Teil greift den Item-Befund aus `chance2022sbi` auf (großer p-Wert als Beleg für die Nullhypothese; in allen Lehrbuchgruppen abnehmend). |
| Statistik, Design | Beobachtungsstudie zeigt Korrelation: „Welche Aussage über Ursache ist gerechtfertigt?“ | Kausalurteil statt Formelanwendung. Kausalinferenz über die Einführungsstatistik hinaus ist hier nicht recherchiert (Lücke). |

## 8. Risiko- und Validitätsaudit

**Evidenzbasis.**
- 27 von 40 Quellen der Batches 1–4 nur als Abstract. Programmier- und Symbolik-Policies stützen sich fast ausschließlich darauf. Batch 5: 10 von 17 (§12.6).
- Die Beweisbefunde stammen überwiegend von einer Forschungsgruppe (Loughborough: Alcock, Inglis, Hodds, Roy), die ihre Interventionen selbst entwickelt hat.
- `ospanov2026llmgrading` und `petrov2025proofbluff` sind Preprints über sich schnell ändernde Modelle. Ihre Zahlen veralten.
- `zhao2025inductiongrading` enthält eine ungeklärte Abweichung zwischen Text (90,0/90,2 %) und Tabelle (89,3/89,4 %). Eine Tabelle wurde über eine werkzeuggenerierte Seitenzusammenfassung extrahiert.
- Die Statistikbefunde sind beobachtend, mit Selbstselektion der Lehrenden.

**Alternative Erklärungen.**
- *Selbsterklärung:* längere Beschäftigung mit dem Beweis statt Selbsterklärung als solcher (Kontrolle zeitgleich, aber nicht inhaltsgleich).
- *Teilziele:* Neuheits- und Lehrendeneffekte im Quasi-Experiment.
- *Tracing → Schreiben:* gemeinsame allgemeine Fähigkeit statt Hierarchie.
- *Autograder:* geringere Einreichungszahl durch mehr Planung oder durch Abschreckung.
- *SBI:* Lehrende, die neue Curricula wählen, unterrichten anders.

**Validitätsrisiken im Produkt.**
1. Komponentenverwechslung: Verständnisitems werden als Beweiskompetenz angezeigt.
2. Prüferdrift: Ein stärkerer Prüfer wird stillschweigend durch einen schwächeren ersetzt, z. B. Rubrik durch LLM.
3. Teaching to the test: Sichtbare Tests werden zum Ziel.
4. Itemwiederholung: Verzögerte Tests nutzen bekannte Beweise.
5. Konsens: Validierungsitems mit strittigem Fehlerstatus (`inglis2013standards`).
6. Reliabilität wird mit Validität verwechselt (`davies2020cjproof`).

Gegenmaßnahmen stehen in den Enthaltungen von POL-02, POL-05, POL-13 und POL-14. Ob sie greifen, ist ungeprüft.

**Bewertung der Stufen.** Die Stufen sind eine interne Einschätzung desselben Modells ohne zweite unabhängige Extraktion. Höchste Stufe: moderat (POL-01, POL-05). Keine Policy ist `high`.

## 9. Gegenprüfung durch den Lead

**Stichprobe an frei abrufbaren Abstracts** (OpenAlex, Crossref, arXiv API, 27.11.2026; Protokoll in `verification_log`):
- `xie2018tracing` (block-randomisiert, N = 24, +15 %, +7 %): **stimmt überein**.
- `sun2024debuggingmeta` (g = 0,64 [0,32; 0,96], 62/18, −0,54 bis 1,82): **stimmt überein**.
- `neuhaus2025proofskills` (N = 153, Zwei-Faktoren-Modell): **stimmt überein**. Das Abstract formuliert den Modellfit positiver als die Volltextnotiz (kein akzeptabler TLI). Die Policy-Stufe bleibt `low`.
- `petrov2025proofbluff`: **Abweichung**. Das Abstract nennt „kein Modell über 30 %, die meisten unter 5 %“; der Registerwert „ein Modell ca. 25 %“ steht dort nicht. Der Registerwert wurde korrigiert. Die Aussage in §1 folgt dem Abstract.

**Nicht geprüft:** alle Volltextzahlen (Hodds, Roy, Margulieux, Lopez, Davies, Jones, Zhao, Ospanov, Tintle, Chance). Die Stichprobe deckt vier von 40 Einträgen ab und sagt nichts über die übrigen.

**Umfangsdisziplin.** Sofort produktrelevant ohne neuen Baustein sind POL-02, POL-05, POL-06 und POL-14. Sie betreffen, was der Lernstand anzeigen darf. Die übrigen Policies beschreiben Inhalts- und Übungsformate. Sie begründen erst dann Engineering-Arbeit, wenn R6 die Lernsequenz beschließt.

## 10. Fragen an unabhängige Gutachterinnen und Gutachter

1. Trägt die Zwei-Faktoren-Lösung von Neuhaus et al. ohne akzeptablen TLI die Designentscheidung, Komponenten getrennt anzuzeigen? Oder spricht die Korrelation von .85 eher für eine gemeinsame Anzeige mit Teilbelegen?
2. Ist Comparative Judgement trotz r = .28 zu MC-Verständnistests als menschlicher Prüfer für Beweiskonstruktion geeignet? Welches Kriterium sollte Validität belegen?
3. Gibt es experimentelle Hochschulevidenz, dass Validierungsübungen die Konstruktion verbessern? R2 fand keine.
4. Sind die Teilziel-Befunde (gemischte Replikation, Prüfungseffekt n. s.) stark genug für eine Standardempfehlung, oder sollte POL-09 optional bleiben?
5. Welche Toleranz- und Äquivalenzregeln braucht ein CAS-Prüfer, damit er Lösungsmengen und Definitionsbereiche nicht systematisch falsch akzeptiert (§7.2)?
6. Unter welchen Bedingungen wäre automatisches Rubrik-Feedback zu Beweisen (Zhao 2025) mehr als ein Hinweis? Welche Fehlerrate wäre tolerierbar?
7. Fehlt ein bekannter Gegenbefund, etwa zu Parsons-Aufgaben, PRIMM oder simulationsbasierter Inferenz?
8. Ist die Seed-Quelle 10.1145/3501385.3543977 für eine der Policies entscheidend?

## 11. Abdeckung des R2-Auftrags und Lücken

| Auftragsteil (Issue #23) | Ort | Status |
|---|---|---|
| Beweis: Verständnis/Validierung/Konstruktion | POL-01–07 | bearbeitet; Konstruktionsinterventionen sehr niedrig belegt |
| Symbolisches Schließen, Fehlvorstellungen, Problemlösen | POL-04, POL-15, POL-20 | teilweise; Physik-Problemlösen in Batch 5 (§12), überwiegend Abstracts und narrative Synthese |
| Programmierung: Tracing, Parsons, Schreiben/Debuggen/Testen | POL-08–13 | bearbeitet; überwiegend Abstracts |
| Algorithmen: Visualisierung, Invarianten, Rekursion | POL-17, POL-18 | teilweise (Batch 5); niedrig bzw. sehr niedrig |
| Komplexitätsanalyse | POL-19 | teilweise (Batch 5); nur deskriptive Defizitbefunde, keine Interventionsstudie |
| Property-Testing | POL-13 (`wrenn2021pbt`) | nur Erfahrungsbericht |
| Statistik | POL-16 | teilweise; beobachtend |
| Kausalinferenz | §12.1, §12.5 | eine deskriptive Quelle (`ellison2021dagtemporal`), **keine Policy** |
| Mathematische Physik, Finanz-/Wirtschaftsmodellierung | POL-20, POL-21 | Physik-Problemlösen und Modellieren teilweise (Batch 5); mathematische Physik im engeren Sinn und Finanz-/Wirtschaftsmodellierung **nicht bearbeitet** |
| Verifier-Frage | §4, POL-14 | bearbeitet (Designentscheidung) |
| Adversariale Aufgaben | §7.2, POL-06 | bearbeitet |
| Lernoperationsmatrix | §3 | bearbeitet |
| Suchjournal mit exakten Queries | §2, §12 | Batch 5 protokolliert (`search_log`); Batches 1–4 **Lücke** |

**Priorisierte Lücken:**
1. Formale Suche Q1–Q5 mit protokollierten Queries und Ein-/Ausschlusszahlen.
2. Volltexte zu Teilzielen (Morrison 2015), Parsons (Ericson 2017), PRIMM, Debugging-Metaanalyse, STACK.
3. Finanz-/Wirtschaftsmodellierung, mathematische Physik im engeren Sinn, Interventionsstudien zur Komplexitätsanalyse, Kausalinferenz über einen deskriptiven Befund hinaus, Primärtext der AV-Meta-Studie (`hundhausen2002avmeta`).
4. Seed 10.1145/3501385.3543977.
5. Experimentelle Belege für Validierungs- oder adversariale Übungen.
6. Unabhängige Zweitextraktion der Volltextzahlen.

**Übergaben:**
- R5 (LLM-Bewertung, Tutor-Abhängigkeit, `agent_judgement`)
- R6 (Sequenz aus §7.1 und R2-CR-1)
- R7 (Prüferdeklaration als Datenfeld, Anzeige „nicht beobachtet“)
- P4-Engineering (Prüferdeklaration im Lernstand, erst nach R6)

## 12. Batch 5: Algorithmen und quantitatives Problemlösen

Stand 27.11.2026. Ergänzungslauf R2S zu den in §11 deklarierten Lücken (Algorithmen und Komplexität, quantitatives Problemlösen und Modellieren, Kausalinferenz). Er ergänzt 17 Registereinträge, die Policies R2-POL-17 bis R2-POL-21 und die Konfliktregeln R2-CR-5 und R2-CR-6. Die Policies 1 bis 16 wurden nicht neu bewertet. **Alle neuen Policies sind `design_hypothesis` mit `learning_evaluation: NOT_RUN`.** Der Lauf stammt vom selben Modell wie Spezialist und Lead. Eine Lead-Stichprobe für Batch 5 gibt es nicht.

**Zugang.** Von den 17 Quellen sind 3 als Volltext-Claim-Review gelesen (`brieven2026gli`, `galezer2004efficiency`, `mason2011categorization`), 3 als Volltext teilweise (`saraiya2002avfeatures`, `docktor2014physicsder`, `ellison2021dagtemporal`), 10 nur als Abstract, 1 nur über Metadaten (`hundhausen2002avmeta`). Die Meta-Studie von Hundhausen et al. war über keinen freien Weg lesbar. Ihre Zahlen stammen aus einem Sekundärbericht (`saraiya2002avfeatures` S. 3, 15–16) und sind dort so gekennzeichnet.

**Suchprotokoll.** Anders als in den Batches 1–4 sind alle Suchen protokolliert: `search_log` in `r2/r2_evidence.json`, 21 Einträge mit exaktem Query, Dienst, Datum, gesichteten Treffern, Ein- und Ausschlussgrund. Auch fehlgeschlagene Suchen stehen dort. Das tägliche Kontingent der OpenAlex-Suche war erschöpft (HTTP 429), Semantic Scholar drosselte, und mehrere Verlage blockierten automatische Abrufe (ACM, ScienceDirect, Springer). Die Auswahl ist deshalb zugunsten frei zugänglicher Texte verzerrt (APS-Open-Access, Autorenkopien, Repositorien). Mehrere Kandidaten wurden aus Zeitgründen nicht bewertet; sie stehen im Protokoll.

### 12.1 Befunde

**Algorithmenvisualisierung.**
- *Befund (sekundär):* Die Meta-Studie über 24 Experimente fand, dass es mehr darauf ankommt, wie Lernende eine Visualisierung nutzen, als darauf, was sie zeigt. Laut Sekundärbericht waren 10 von 14 Studien mit aktiver Einbindung signifikant, aber nur 3 von 10 Studien, die Darstellungsmerkmale variierten (`hundhausen2002avmeta` über `saraiya2002avfeatures`). Der Primärtext ist nicht gelesen. Die Zählung ist ein Stimmenzählverfahren ohne Effektgrößen.
- *Befund (Abstract):* In einem Vergleich an mehreren Hochschulen stieg der Lernzuwachs mit der Engagement-Stufe (keine Visualisierung, kurzes Ansehen, längere Interaktion). Den größten Prä-Post-Zuwachs hatten Studierende, die in das Werkzeug integrierte Fragen beantworteten (`grissom2003avengagement`). Engagement-Stufe und Lernzeit sind dabei konfundiert.
- *Befund (Volltext, klein):* In zwei Heapsort-Experimenten (N = 66 und 44) war das wichtigste Merkmal, dass Lernende das Tempo selbst steuern. Eine minimale Darstellung reichte für prozedurales Verständnis. Eine Pseudocode-Anzeige schnitt bei prozeduralen Fragen signifikant schlechter ab, und insgesamt war die minimale Variante nur nicht signifikant besser (`saraiya2002avfeatures` 4.4, 5.2). Es gab nur sofortige Nachtests.
- *Befund (Abstract):* Von 18 Programm- und Algorithmusvisualisierungssystemen war die Hälfte nur auf Usability geprüft (`urquizafuentes2009avsurvey`).
- *Gegenbefund aus R2:* Interaktive e-Proofs halfen beim Beweisverständnis nicht (`roy2017eproofs`). Interaktivität allein ist also auch dort keine aktive Lernoperation.

**Korrektheit: Invarianten und Rekursion.**
- *Befund (Volltext, sehr klein):* In einem CS1-Experiment mit vier Unterstützungsstufen machte die Gruppe mit vollständig vorgegebener grafischer Schleifeninvariante weniger Fehler bei Schleifenbedingung und Variablenrollen. Aktualisierungsfehler blieben in allen Gruppen. Die Lückentext-Variante erhöhte oft die Last. Die Autoren nennen den Ansatz „weder notwendig noch hinreichend“ für korrekten Code (`brieven2026gli` 6.2, 6.3). Es waren etwa 10 Lernende je Gruppe, ein Kodierer, und alle Gruppen hatten den Ansatz zuvor gelernt (7).
- *Befund (Abstract):* Von Hunderten Artikeln zu Rekursion berichten weniger als 50 Forschungsergebnisse. Als wirksam bezeichnet werden mehrere Einführungskontexte und die Erklärung über den Aufrufstapel (`mccauley2015recursion`). Das ist eine Einordnung der Autoren, keine gepoolte Schätzung.

**Komplexitätsanalyse.**
- *Befund (Volltext, Schule):* Israelische Schülerinnen und Schüler hielten kürzere Programme und Programme mit weniger Variablen für effizienter, und Programme mit gleichen Anweisungen in anderer Reihenfolge für gleich effizient. Bei Frage 1 antworteten richtig: 19,44 % in Klasse 10 vor der Einheit, 27,5 % danach und 55,9 % in Klasse 11. Die Erklärung „kürzer“ gaben 55 %, 56,7 % und 34,3 % (`galezer2004efficiency` 4). Effizienz wurde dort über Ausführungszeit gelehrt, nicht über O-Notation.
- *Befund (Abstract, Hochschule):* Ein Konzeptinventar zur Algorithmenanalyse zeigte nach CS2, dass ausreichend viele Studierende die meisten gelisteten Fehlvorstellungen hatten (`farghally2017aaci`). Die Liste selbst ist nicht gelesen.
- *Nicht gefunden:* eine Interventionsstudie mit verzögertem Maß zur Vermittlung asymptotischer Analyse.

**Quantitatives Problemlösen (Physik).**
- *Befund (Abstract):* Fortgeschrittene beginnen die Repräsentation einer Aufgabe mit physikalischen Prinzipien, Anfänger mit wörtlichen Oberflächenmerkmalen (`chi1981categorization`).
- *Gegenbefund (Volltext):* Bei 403 Einführungsstudierenden, 21 Promovierenden und 7 Lehrenden überlappten die Kategorisierungen von Studierenden im analysisbasierten Kurs und von Promovierenden stark. Die Lehrenden waren signifikant besser. Die Autoren sehen ein Kontinuum statt einer Dichotomie und Kategorisierung nur als Proxy für Expertise (`mason2011categorization` V, VI).
- *Befund (Abstract):* Wer gezwungen wurde, Aufgaben qualitativ und hierarchisch zu analysieren (Prinzip, Konzept, Verfahren), urteilte expertennäher und löste Aufgaben besser (`dufresne1992constraining`). Vergleichsbedingung, N und Messabstand sind nicht bekannt.
- *Befund (Abstract):* Explizit vermittelte Heuristiken führten bei gleicher Übungszeit zu besseren Lösungen nicht isomorpher Aufgaben (`schoenfeld1979heuristics`).
- *Befund (Synthese, Volltext teilweise):* Explizite Problemlöse-Rahmen gehen mit besserer Kursleistung einher. Wer ein falsches Kräftediagramm zeichnet, schneidet schlechter ab als wer keines zeichnet. Mehrere Repräsentationswerkzeuge waren beliebt, ohne die Leistung zu verändern. Nur ein Drittel bis die Hälfte erkannte selbst ein unpassendes Prinzip. Die Autoren nennen kleine Stichproben, uneinheitliche Maße für Problemlösen und eine dünne Forschung zu Lösungsbeispielen in der Physik als Grenzen (`docktor2014physicsder` III.D–E).

**Mathematisches Modellieren.**
- *Befund (Abstract, Schule):* Vier Unterrichtsstunden Modellieren mit Lösungsplan verbesserten bei 157 Schweizer Schülerinnen und Schülern die Modellierungskompetenz bis zum Follow-up. Die Selbstwirksamkeit änderte sich nicht direkt. Die Kontrollgruppe hatte regulären Unterricht (`vogelsanger2025solutionplan`).
- *Befund (Abstract, auch Hochschule):* In vier Studien mit 453 Teilnehmenden, drei davon an Hochschulen in Südafrika, wirkte dieselbe fünfstündige Einheit unabhängig vom Kontext. Mit methodenintegrativem Lehrstil war sie stärker wirksam als mit lehrerzentriertem (`lindl2025costamm`). Es ist ein Prä-Post-Design; eine unbehandelte Kontrolle nennt das Abstract nicht.
- *Nicht gefunden:* Lernevidenz zu Finanz- oder Wirtschaftsmodellierung und zu Schätz-/Fermi-Aufgaben an Hochschulen.

**Kausalinferenz.**
- *Befund (Volltext teilweise):* 85 Medizinstudierende ordneten Kovariaten zuerst nach zeitlicher Reihenfolge und spezifizierten dann einen DAG. 84,5 % bzw. 92,4 % klassifizierten mindestens eine Kovariate falsch. Konfundierer wurden selten falsch eingeordnet (4,4 % bzw. 3,1 %), Mediatoren häufig (56,9 % bzw. 48,7 %). Modelle nach diesen DAGs wären in 50 von 66 Fällen (76,8 %) verzerrt gewesen (`ellison2021dagtemporal`, Abstract). Die Studie ist deskriptiv, ohne Kontrolle und ohne verzögertes Maß. Daraus folgt keine Policy.

### 12.2 Policies mit Mechanismuskette

Kette je Policy wie in §5, ergänzt um die vier Produkte. Erzeugt aus `r2/r2_learning_policies.json`; Relation und Zugangsstufe je Quelle in Klammern.

### R2-POL-17 — Algorithmenvisualisierung nur mit aktiver Lernoperation und lernergesteuertem Tempo

*Operationen:* computational_construction; *Vorwissen:* novice, intermediate; *Phase:* acquisition, consolidation. *Stufe:* niedrig (gleiche Richtung in Meta-Studie (nur sekundär gelesen), Mehrhochschulvergleich und kleinen Experimenten; Engagement mit Lernzeit konfundiert (grissom2003avengagement); nur unmittelbare Nachtests, keine verzögerten oder unassistierten Transfermaße gelesen; Studien überwiegend von Entwicklern der Werkzeuge).

- **Evidenz:** `grissom2003avengagement` (supports, abstract); `hundhausen2002avmeta` (supports, metadata); `saraiya2002avfeatures` (supports, fulltext_partial); `saraiya2002avfeatures` (qualifies, fulltext_partial); `naps2002engagement` (context_only, abstract); `urquizafuentes2009avsurvey` (qualifies, abstract)
- **Intervention:** Visualisierungen von Algorithmen werden nie zum bloßen Ansehen angeboten. Jede Visualisierung verlangt eine Lernoperation: den nächsten Zustand vorhersagen, eine Frage zum Schritt beantworten oder eine Eingabe konstruieren, die einen bestimmten Fall auslöst. Lernende steuern das Tempo selbst (Einzelschritt statt Autoplay). Die Darstellung bleibt minimal und zeigt die logischen Schritte; Zusatzansichten (Pseudocode, Leitfäden) nur, wenn sie für die Aufgabe nötig sind.
- **Produkte:**
  - *Lehrbuch:* Statische Zustandsfolgen mit Haltepunkten ('Wie sieht der Zustand nach dem nächsten Schritt aus?') vor der Auflösung; keine eingebetteten Animationen ohne Aufgabe; Beispieldaten decken Sonderfälle ab (Duplikate, bereits sortierte oder umgekehrte Eingabe)
  - *Arbeitsbuch:* Handsimulation auf vorgegebener Eingabe mit Zustandstabelle; Aufgabe 'konstruiere eine Eingabe, die den schlechtesten Fall auslöst' (z. B. Quicksort mit fester Pivotwahl)
  - *Anki:* Karten mit Zustand vor einer Operation und Frage nach dem Folgezustand (z. B. Min-Heap nach extract-min); Eingaben werden je Wiederholung neu erzeugt, damit das Verfahren und nicht die Karte abgerufen wird; nur Übung, kein Kompetenzbeleg
  - *Interaktiv:* Lernergesteuerter Stepper ohne Autoplay als Standard; an markierten Schritten Vorhersage vor der Auflösung, deterministisch gegen das Zustandsorakel der Referenzimplementierung geprüft; Lernende können eigene Eingaben eingeben
- **Beobachtung im Produkt:** Vorhersagegenauigkeit je Schritt und Fehlerart (welcher Zustand falsch vorhergesagt), selbst konstruierte Eingaben
- **Unabhängiges Lernoutcome:** verzögerte (mindestens 1 Woche), unassistierte Handsimulation des Algorithmus auf neuer Eingabe ohne Visualisierung plus ein Begründungsitem ('warum dieser Schritt')
- **Versagen/Gegenbefund:** Vorhersagen werden geraten oder durchgeklickt; visuelle Überladung durch Zusatzansichten (saraiya2002avfeatures); Wissen bleibt an die Darstellung gebunden und überträgt sich nicht auf Code oder Begründung; Verweildauer im Werkzeug wird mit Lernen verwechselt. Falsifikator: Ein vorab registrierter randomisierter Vergleich bei gleicher Lernzeit (Stepper mit Vorhersage vs. dieselbe Visualisierung als Animation) zeigt keinen Unterschied in der verzögerten, unassistierten Handsimulation neuer Eingaben ohne Visualisierung.
- **Enthaltung:** Ansehen einer Animation zählt nie als Lernfortschritt oder Kompetenzbeleg (MC-R2); ohne getestete Referenzimplementierung als Zustandsorakel keine interaktive Vorhersageprüfung; Rückfall auf Arbeitsbuch mit Musterlösung; keine Wirksamkeitsbehauptung für Visualisierung als solche

### R2-POL-18 — Korrektheitsargumente für Schleifen und Rekursion: Invariante erst interpretieren, dann konstruieren

*Operationen:* computational_construction, formal_proof; *Vorwissen:* novice, intermediate; *Phase:* acquisition, consolidation. *Stufe:* sehr niedrig (eine CS1-Studie mit etwa 10 Lernenden je Gruppe, ein Kodierer, keine externe Kontrollgruppe, nur unmittelbare Aufgaben; Rekursion nur über das Abstract eines narrativen Reviews; Stufung interpretieren vor konstruieren ist aus Fehlerbefunden abgeleitet, nicht getestet).

- **Evidenz:** `brieven2026gli` (supports, fulltext_claim_review); `brieven2026gli` (qualifies, fulltext_claim_review); `mccauley2015recursion` (context_only, abstract)
- **Intervention:** Schleifen- und Rekursionsalgorithmen werden mit expliziter Korrektheitsbegründung gelehrt: Invariante mit Initialisierung, Erhaltung und Terminierung bzw. Basisfall und Rekursionsschritt mit Aufrufstapel. Die Reihenfolge ist gestuft: zuerst eine gegebene, vollständige Invariante interpretieren und daraus Initialisierung und Abbruchbedingung ableiten, danach Verletzungen der Invariante in fremdem Code finden, zuletzt eigene Invarianten formulieren. Lückentext-Invarianten sind für Anfänger kein Standard. Invariantenbehauptungen werden als ausführbare Zusicherungen auf erzeugten Eingaben geprüft; das kann eine Invariante widerlegen, aber nicht beweisen.
- **Produkte:**
  - *Lehrbuch:* Jeder Schleifenalgorithmus mit Invariante, Initialisierung, Erhaltung und Terminierung direkt neben dem Code (CL-R1); Rekursion mit Aufrufstapel-Darstellung und Begründung des Basisfalls
  - *Arbeitsbuch:* Stufen: (1) gegebene Invariante interpretieren, Initialisierung und Abbruchbedingung ableiten; (2) Stelle finden, an der fremder Code die Invariante verletzt; (3) eigene Invariante und Korrektheitsargument schreiben (Mensch-Rubrik)
  - *Anki:* Ableitungskarten ('Invariante gegeben: welche Abbruchbedingung, welche Initialisierung?') mit wechselnden Algorithmen; keine Karten, die Invarianten bekannter Algorithmen nur abfragen
  - *Interaktiv:* Invariante als ausführbares Prädikat eingeben; das System prüft es auf erzeugten Eingaben vor und nach jeder Iteration und zeigt ein Gegenbeispiel; Status 'nicht widerlegt', nie 'bewiesen'; formale Verifikation nur als optionale formale Variante (R2-POL-07)
- **Beobachtung im Produkt:** Fehlerarten im Code (Schleifenbedingung, Variablenrolle, Aktualisierung), Gegenbeispiele zu eingegebenen Invarianten, genutzte Unterstützungsstufe
- **Unabhängiges Lernoutcome:** verzögerte unassistierte Schreibaufgabe einer neuen Schleife mit verborgenen Tests plus schriftliches Korrektheitsargument, von einem Menschen mit Rubrik bewertet
- **Versagen/Gegenbefund:** Invarianten werden als Formeln auswendig gelernt; Zusatzlast überfordert Anfänger, Code bleibt unfertig (brieven2026gli 6.2); Laufzeitprüfung mit schwachen Eingabegeneratoren lässt falsche Invarianten durch; Lernende umgehen die Invariante (mehrere Schleifen statt einer). Falsifikator: Ein vorab registrierter Vergleich (Invariante zuerst vs. gleich lange Codeübung) zeigt bei verzögerten, neuen Schleifenaufgaben keine Verringerung von Schleifenbedingungs- und Aktualisierungsfehlern.
- **Enthaltung:** bestandene Laufzeitprüfung einer Invariante gilt als 'nicht widerlegt', nicht als Korrektheitsbeweis; Korrektheitsargument in Prosa: Mensch-Rubrik oder unverifiziert; LLM-Bewertung nur agent_judgement (R2-CR-2); ohne bestandene Tracing-Probe zuerst R2-POL-08 (R2-CR-5); keine Lückentext-Invarianten als Standard für Anfänger (brieven2026gli)

### R2-POL-19 — Komplexitätsanalyse: Wachstumsbegründung statt Etikett, Oberflächenheuristiken gezielt brechen

*Operationen:* computational_construction, symbolic_procedure, formal_proof; *Vorwissen:* novice, intermediate; *Phase:* acquisition, consolidation, final_exam_week. *Stufe:* sehr niedrig (Defizitbefund deskriptiv, Hochschulbeleg nur als Abstract; Hauptquelle aus der Schule, Effizienz dort nicht asymptotisch gelehrt; keine Interventionsstudie zur Komplexitätsanalyse gelesen).

- **Evidenz:** `galezer2004efficiency` (supports, fulltext_claim_review); `galezer2004efficiency` (qualifies, fulltext_claim_review); `farghally2017aaci` (supports, abstract)
- **Intervention:** Komplexitätsurteile werden nie aus einem Etikett ('O(n log n)') oder einer Zahl allein gewertet. Aufgaben verlangen eine Wachstumsbegründung: dominante Operation benennen, Anzahl als Summe oder Rekurrenz aufstellen, Fall (bester, schlechtester, durchschnittlicher) benennen. Items brechen bekannte Oberflächenheuristiken gezielt: kürzerer Code ist langsamer, weniger Variablen ist langsamer, gleiche Anweisungen in anderer Reihenfolge ändern das Wachstum. Obere bzw. untere Schranke und bester bzw. schlechtester Fall werden getrennt abgefragt. Diagnoseitems zu typischen Fehlvorstellungen kommen vor und nach der Einheit.
- **Produkte:**
  - *Lehrbuch:* Paare semantisch gleichwertiger Programme, deren Oberfläche der Effizienz widerspricht; ausdrückliche Trennung von Schranke und Fall mit Gegenbeispiel
  - *Arbeitsbuch:* Paarvergleich mit Begründung; Operationszahl als Summe herleiten; Eingabe konstruieren, die den schlechtesten Fall auslöst; Gegenbeispiel zu einer falschen O-Behauptung finden
  - *Anki:* Diskriminationskarten (O vs. Θ, Schranke vs. Fall, Wachstumsvergleich zweier Funktionen) als Abrufstütze; sie zählen nicht als Analysekompetenz
  - *Interaktiv:* Wachstumsklasse erst vorhersagen, dann Operationszähler über steigende n mit doppelt-logarithmischer Darstellung; der Zähler prüft Instanzen, nicht die asymptotische Aussage; Summenherleitung per CAS-Äquivalenz je Schritt (R2-POL-15)
- **Beobachtung im Produkt:** Antworten auf Diagnoseitems je Fehlvorstellung mit Begründung; Herleitungsschritte (CAS-geprüft); Etikett-Herleitungs-Übereinstimmung
- **Unabhängiges Lernoutcome:** verzögertes unassistiertes Diagnoseinventar mit neuen Items plus Laufzeitherleitung für neuen Code, von einem Menschen bewertet
- **Versagen/Gegenbefund:** Faustregeln ('zwei Schleifen = n²') ersetzen die Fehlvorstellung und versagen bei abhängigen Grenzen; Diagnoseitems werden als Muster wiedererkannt; Messung im Werkzeug verdrängt die Analyse. Falsifikator: Ein vorab registrierter Vergleich (Paarvergleich mit Begründung vs. gleich lange Standardübungen) zeigt im verzögerten Diagnoseinventar mit neuen Items keinen Unterschied bei den Zielfehlvorstellungen.
- **Enthaltung:** Laufzeitmessungen und Operationszähler belegen keine Komplexitätsklasse (nur endlich viele Instanzen; Konstanten, Cache, Eingabewahl); Etikett ohne Herleitung: unverifiziert; Beweis einer Schranke: Mensch-Rubrik oder unverifiziert; LLM-Bewertung nur agent_judgement; keine Wirksamkeitsbehauptung für Paarvergleiche (nicht experimentell geprüft)

### R2-POL-20 — Quantitatives Problemlösen: Problemrepräsentation vor der Rechnung

*Operationen:* symbolic_procedure; *Vorwissen:* novice, intermediate; *Phase:* acquisition, consolidation. *Stufe:* niedrig (Expert-Novizen-Unterschied in der Richtung konsistent, aber Kategorisierung ist nur Proxy; Interventionsbelege alt, klein und nur als Abstract gelesen; narrative Synthese ohne Effektgrößen; Autor Mestre an Primärstudien beteiligt; Befunde zu externen Repräsentationen gemischt).

- **Evidenz:** `chi1981categorization` (supports, abstract); `dufresne1992constraining` (supports, abstract); `docktor2014physicsder` (supports, fulltext_partial); `schoenfeld1979heuristics` (supports, abstract); `docktor2014physicsder` (qualifies, fulltext_partial); `mason2011categorization` (qualifies, fulltext_claim_review)
- **Intervention:** Vor der Rechnung steht eine kurze qualitative Analyse: zugrunde liegendes Prinzip benennen, seine Anwendbarkeit begründen, Größen und Skizze festhalten, Plan formulieren (Strategieschreiben). Sortieraufgaben mit gekreuzten Oberflächen- und Tiefenmerkmalen dienen als Übung und Diagnose. Nach Fehlern folgt Selbstdiagnose mit Musterlösung und Rubrik. Die Prinzipwahl ist gegen einen Schlüssel prüfbar; Begründung und Plan bleiben unverifiziert oder werden menschlich bewertet.
- **Produkte:**
  - *Lehrbuch:* Lösungsbeispiele beginnen mit Prinzip, Begründung, Skizze und Plan, erst dann Gleichungen; Aufgabenpaare mit gleicher Oberfläche und verschiedenem Prinzip sowie umgekehrt
  - *Arbeitsbuch:* Sortieraufgaben (gleiche Oberfläche, anderes Prinzip und umgekehrt); Aufgaben 'Prinzip + Begründung + Plan, ohne Rechnung'; Selbstdiagnose nach Fehlern mit Musterlösung und Rubrik
  - *Anki:* Karten mit Aufgabentext und Frage nach Prinzip und Begründung statt nach dem Zahlenwert; Oberfläche je Wiederholung variiert; Aufgaben mit mehreren Prinzipien haben mehrere richtige Antworten
  - *Interaktiv:* Gleichungseingabe erst nach Prinzipwahl und Kurzbegründung; Prinzipwahl gegen Schlüssel geprüft, Rechnung je Schritt per CAS mit Einheitenprüfung (R2-POL-15), Begründung unverifiziert
- **Beobachtung im Produkt:** Prinzipwahl (geprüft), Begründung (unverifiziert), Schrittkorrektheit der Rechnung, Fehlerart
- **Unabhängiges Lernoutcome:** verzögerte unassistierte Lösung neuer, nicht isomorpher Aufgaben mit verändertem Oberflächenkontext, bewertet mit einer Lösungsrubrik (Prinzip, Ansatz, Rechnung, Plausibilität)
- **Versagen/Gegenbefund:** Planungsfeld wird mit Floskeln gefüllt; Prinzipwahl wird über Schlagworte im Aufgabentext erraten; Zusatzschritt kostet bei Routineaufgaben Zeit ohne Gewinn; fehlerhafte Skizzen verschlechtern Lösungen. Falsifikator: Ein vorab registrierter randomisierter Vergleich bei gleicher Zeit (Repräsentation zuerst vs. direktes Rechnen) zeigt bei verzögerten, neuen, nicht isomorphen Aufgaben keinen Unterschied in der Rubrikbewertung.
- **Enthaltung:** Sortier- bzw. Kategorisierungsleistung ist nur ein Proxy und zählt nicht als Problemlösekompetenz (mason2011categorization); Prinzipschlüssel nur für Items mit fachlich konsentiertem Prinzip; Aufgaben mit mehreren Prinzipien erhalten einen Mehrfachschlüssel; wer eine Erste-Schritt-Probe ohne Hilfe löst, darf die Planungsphase überspringen (WE-R2); eine fehlerhafte Skizze wird als Fehler zurückgemeldet und nicht als erfüllte Pflicht gezählt (docktor2014physicsder III.D.3)

### R2-POL-21 — Mathematisches Modellieren mit Lösungsplan und getrennt beobachteten Teilkompetenzen

*Operationen:* symbolic_procedure, empirical_experimental; *Vorwissen:* novice, intermediate; *Phase:* acquisition, consolidation. *Stufe:* sehr niedrig (nur Abstracts gelesen; überwiegend Schulstudien; Hochschulbeleg nur aus einer Studienreihe ohne unbehandelte Kontrolle; Studien aus einem Forschungsnetz, das den Lösungsplan entwickelt hat; Kontrollgruppe in vogelsanger2025solutionplan ohne gleiche Aufgaben (Zeit- und Aufgabenkonfundierung)).

- **Evidenz:** `vogelsanger2025solutionplan` (supports, abstract); `lindl2025costamm` (supports, abstract); `lindl2025costamm` (qualifies, abstract); `docktor2014physicsder` (context_only, fulltext_partial)
- **Intervention:** Modellierungsaufgaben werden mit einem Lösungsplan bearbeitet: verstehen, vereinfachen und Annahmen treffen, mathematisieren, mathematisch arbeiten, interpretieren, validieren. Teilkompetenzen werden getrennt beobachtet, weil nur der Rechenschritt deterministisch prüfbar ist; Annahmen und Validierung werden menschlich bewertet oder bleiben unverifiziert. Der Plan wird ausgeblendet, sobald Lernende ihn ohne Aufforderung anwenden.
- **Produkte:**
  - *Lehrbuch:* Modellierungskreislauf mit einem durchgerechneten Beispiel, das Annahmen ausdrücklich nennt und das Ergebnis gegen Größenordnung oder Realdaten validiert
  - *Arbeitsbuch:* Aufgaben mit Lösungsplan; zusätzlich Teilkompetenz-Items (fehlende Annahme benennen, Ergebnis validieren, Modell an veränderten Kontext anpassen); mehrere vertretbare Lösungen mit Bewertungsrubrik
  - *Anki:* nur unterstützend: Karten zu Plausibilitätsprüfungen (Größenordnung, Einheiten) und typischen Annahmen; vollständige Modellierung ist nicht kartentauglich
  - *Interaktiv:* Lösungsplan-Stepper mit Annahmenprotokoll; Rechenteil per CAS und Einheitenprüfung; Plausibilitätsband als Hinweis, nicht als Korrektheitsurteil; Annahmen und Validierung als 'unverifiziert' oder menschlich bewertet
- **Beobachtung im Produkt:** Bearbeitung je Planschritt; dokumentierte Annahmen; Validierungsaussage (unverifiziert); geprüfte Rechenschritte
- **Unabhängiges Lernoutcome:** verzögerte unassistierte neue Modellierungsaufgabe mit anderem Kontext, je Teilkompetenz von Menschen mit Rubrik bewertet
- **Versagen/Gegenbefund:** Plan wird mechanisch abgehakt; Annahmen werden aus dem Aufgabentext abgeschrieben statt getroffen; Plausibilitätsband wird als Lösungsschlüssel missverstanden; Schulbefunde tragen nicht für Hochschulmodellierung. Falsifikator: Ein vorab registrierter Vergleich derselben Modellierungsaufgaben mit und ohne Lösungsplan bei gleicher Zeit zeigt bei verzögerten neuen Aufgaben in keiner Teilkompetenz einen Unterschied.
- **Enthaltung:** keine Einzelzahlprüfung als Modellierungsbeleg, weil mehrere Ergebnisse vertretbar sind (R2-POL-06); keine Aussage über Finanz- oder Wirtschaftsmodellierung (keine Lernevidenz gesichtet); Lösungsplan nicht als starre Pflicht für Fortgeschrittene

### 12.3 Konfliktregeln (Ergänzung)

- **R2-CR-5** (POL-18, POL-08): Invariantenarbeit beginnt erst nach bestandener Tracing-Probe; vorher Tracing-Übung.
- **R2-CR-6** (POL-17, POL-11, R1-A08): Im Algorithmus-Stepper ersetzt die Zustandsvorhersage die PRIMM-Vorhersage. Korrigierendes Feedback nach jeder Vorhersage bleibt; eine Konfidenzabfrage gibt es nicht bei jeder Vorhersage.

**Ergänzung der Verifier-Matrix (§4).** R2-POL-14 nennt jetzt zusätzlich vier Prüfer. Keiner davon ist allein ein Kompetenzbeleg für die Begründung.

| Prüfer | Prüft | Prüft nicht | Kompetenzbeleg? | Bezug |
|---|---|---|---|---|
| Zustandsorakel einer Referenzimplementierung | vorhergesagten Zustand nach einem Algorithmusschritt | Begründung, Übertragung auf Code; Fehler der Referenzimplementierung | ja für Handsimulation, wenn die Eingabe neu ist | POL-17 |
| Laufzeit-Zusicherung für Invarianten | ob eine behauptete Invariante auf erzeugten Eingaben hält | Beweis; Güte des Eingabegenerators | nein, nur Widerlegung („nicht widerlegt“) | POL-18 |
| Operationszähler, Laufzeitmessung | Operationen bzw. Zeit für endlich viele n | asymptotische Aussage, Fallunterscheidung, Konstanten | nein | POL-19 |
| Prinzipschlüssel | gewähltes Prinzip bei fachlich konsentierten Items | Begründung; Aufgaben mit mehreren Prinzipien ohne Mehrfachschlüssel | nein allein (Proxy, `mason2011categorization`) | POL-20 |

### 12.4 Synthetische Fallbeispiele

Alle Beispiele sind für diesen Bericht erfunden. Sie stammen nicht aus Vorlesungsmaterial.

**(a) Algorithmen: Heaps und Heapsort.** Eine lernende Person (Novize in Algorithmen und Datenstrukturen) arbeitet am Kompetenzziel „Heapsort ausführen, als korrekt begründen und seine Laufzeit herleiten“.
1. *Tracing-Probe (POL-08, CR-5):* drei Schleifen-Items. Die Person besteht zwei von drei → zusätzliche Tracing-Übung, dann weiter.
2. *Stepper (POL-17):* Das Array [4, 10, 3, 5, 1] wird zum Max-Heap aufgebaut. Vor jedem Sift-down sagt die Person den Folgezustand vorher. Das Zustandsorakel der getesteten Referenzimplementierung prüft. Danach konstruiert sie eine Eingabe, bei der Sift-down von der Wurzel bis zum Blatt läuft. *Beobachtung:* 4 von 6 Vorhersagen richtig, Fehlerart „falsches Kind gewählt“.
3. *Invariante (POL-18):* Die Invariante des Heap-Aufbaus wird vorgegeben: „Vor jeder Iteration i (absteigend von ⌊n/2⌋) ist jeder Knoten mit Index > i Wurzel eines Max-Heaps.“ Daraus leitet die Person Startwert und Abbruchbedingung ab. Danach gibt sie die Invariante als ausführbares Prädikat ein. Bei 50 erzeugten Eingaben wird sie nicht widerlegt. *Anzeige:* „nicht widerlegt“, nicht „bewiesen“. Das Korrektheitsargument in Prosa bleibt ohne Lehrperson unverifiziert.
4. *Komplexität (POL-19):* Die Person behauptet „Θ(n log n), weil n/2-mal Sift-down mit O(log n)“. Das Diagnoseitem trennt obere Schranke und exakte Ordnung. Die Summenherleitung Σ_h ⌈n/2^(h+1)⌉·O(h) = O(n) wird je Schritt per CAS geprüft. Der Operationszähler zeigt das Wachstum für n bis 10⁶, gilt aber nicht als Beleg.
5. *Spätere Prüfung:* Nach mindestens einer Woche folgen eine Handsimulation an einer neuen Eingabe ohne Visualisierung, ein neues Diagnoseitem und eine Laufzeitherleitung für neuen Code, unassistiert.

*Anzeige:* „Handsimulation: belegt (verzögert, neue Eingabe); Invariante: nicht widerlegt, Argument unverifiziert; Laufzeit: Summenschritte geprüft, Schranke nicht beobachtet.“

**(b) Quantitatives Problemlösen und Modellieren.** Eine lernende Person (Einführung Mechanik, danach ein Modellierungsmodul) bearbeitet zwei Aufgaben.
1. *Repräsentation (POL-20):* „Ein Block gleitet reibungsfrei eine gekrümmte Bahn aus der Höhe h hinab. Wie schnell ist er unten?“ Die Gleichungseingabe öffnet erst nach Prinzipwahl und Kurzbegründung. Die Person wählt „Energieerhaltung, die Normalkraft verrichtet keine Arbeit“; der Schlüssel bestätigt das Prinzip, die Begründung bleibt unverifiziert. Die Rechnung v = √(2gh) wird per CAS und Einheitenprüfung kontrolliert.
2. *Anki-Variante:* Dasselbe Prinzip mit neuer Oberfläche (Pendel aus Auslenkung losgelassen). Die Karte fragt nach Prinzip und Begründung, nicht nach dem Zahlenwert.
3. *Modellieren (POL-21):* „Wie lange dauert es, bis ein Kaffee von 90 °C auf Trinktemperatur 60 °C abkühlt? Nach 5 Minuten misst du 80 °C.“ Der Lösungsplan verlangt Annahmen (Raumtemperatur 20 °C, Abkühlung proportional zur Temperaturdifferenz). Daraus folgt T(t) = 20 + 70·e^(−kt) mit k = ln(7/6)/5 ≈ 0,031 pro Minute und t = ln(7/4)/k ≈ 18 Minuten. Die Validierung („Was sagt dein Modell nach einer Stunde?“) ergibt rund 31 °C, also plausibel. *Beobachtung:* Rechenschritte geprüft, Annahmen und Validierung unverifiziert bis zur menschlichen Bewertung.
4. *Spätere Prüfung:* neue, nicht isomorphe Aufgabe (z. B. Entladung eines Kondensators als Modellierungskontext) nach mindestens einer Woche, Rubrik je Teilkompetenz.

### 12.5 Adversariale Aufgaben je Teilbereich

| Bereich | Aufgabe | Was sie bricht |
|---|---|---|
| Komplexität | Zwei Funktionen zum Entfernen von Duplikaten. A (kürzer): `if x not in out: out.append(x)` auf einer Liste. B (länger, eine Variable mehr): dasselbe mit einer Hilfsmenge `seen`. „Welche wächst langsamer? Begründe über die Anzahl der Vergleiche.“ | Die Oberflächenheuristik „kürzer und weniger Variablen = schneller“ (`galezer2004efficiency`). A wächst im schlechtesten Fall quadratisch, B erwartet linear. Eine Laufzeitmessung bei n = 10 entscheidet nichts. |
| Komplexität, Schranke | „Heap-Aufbau ruft n/2-mal Sift-down mit O(log n) auf. Also Θ(n log n)?“ | Das Abrufen der Formel „Anzahl × Kosten“. O(n log n) ist eine korrekte, aber nicht scharfe obere Schranke; Θ(n log n) ist falsch. |
| Invariante, Terminierung | Binäre Suche mit `lo = mid` statt `lo = mid + 1`. Die sichtbaren Tests suchen nur das erste Element. | Sichtbare Unit-Tests bestehen. Bei zwei Elementen und gesuchtem Maximum bleibt `lo` stehen, die Schleife endet nie. Erst die Laufzeit-Zusicherung „hi − lo nimmt strikt ab“ auf erzeugten Eingaben findet das Gegenbeispiel. |
| Visualisierung | Quicksort-Animation läuft ab; danach: „Konstruiere eine Eingabe der Länge 8, bei der diese Pivotwahl den schlechtesten Fall erzeugt.“ | Wer nur zugesehen hat, kann den Fall nicht konstruieren. Die Aufgabe verlangt ein Modell des Verfahrens, nicht das Wiedererkennen der Animation. |
| Physik, Einzelzahlprüfung | Block auf gekrümmter reibungsfreier Bahn; Antwort v = √(2gh) mit der Begründung „konstante Beschleunigung, v² = 2as“. | Der Zahlenwert stimmt, die Begründung ist ungültig (keine konstante Beschleunigung). Eine Einzelzahlprüfung akzeptiert sie, der Prinzipschlüssel nicht. |
| Physik, Mehrprinzip | Ballistisches Pendel: Geschwindigkeit des Geschosses aus der Steighöhe. | Wer nur „Energieerhaltung“ wählt, rechnet falsch, denn der Stoß ist inelastisch. Nötig sind Impulserhaltung im Stoß und danach Energieerhaltung. Ein Einzelprinzip-Schlüssel wäre hier selbst falsch (`mason2011categorization` V.A). |
| Modellieren | Kaffeeaufgabe aus §12.4. Antwort „15 Minuten“ mit linearer Abkühlung (10 °C je 5 Minuten). | 15 Minuten liegen in einer Toleranz von ±20 % um 18 Minuten; eine Einzelzahlprüfung akzeptiert die Antwort. Die Validierungsfrage zeigt den Modellfehler: Das lineare Modell sagt nach einer Stunde −30 °C voraus. |
| Kausalinferenz | „Tutoriumsteilnahme X, Klausurnote Y, wöchentliche Übungszeit M nach Tutoriumsbeginn, Vorwissen C vor X. Für den Gesamteffekt von X auf Y: Für welche Variablen adjustieren?“ | Das Rezept „für alles Korrelierte adjustieren“. Richtig ist C (Konfundierer), nicht M (Mediator). Mediatoren werden häufig falsch eingeordnet (`ellison2021dagtemporal`). Die zeitliche Ordnung allein entscheidet nicht, ob eine Variable vor X Konfundierer oder nur konkurrierende Exposition ist. |

### 12.6 Risiko und Validität

**Evidenzbasis.**
- 10 von 17 Quellen nur als Abstract, eine nur über Metadaten. Die Visualisierungs-Policy stützt sich auf einen Sekundärbericht der Meta-Studie.
- Viele Studien sind alt (1979, 1981, 1992, 2002/03) und klein. Physikbefunde stammen fast nur aus der einführenden Mechanik.
- Entwicklernähe: Die Visualisierungsstudien stammen von Werkzeugentwicklern (JHAVÉ, AlgoViz), die Invariantenstudie von den Kursentwicklern, die Modellierungsstudien aus dem Forschungsnetz, das den Lösungsplan entwickelt hat. Mestre ist Autor der Synthese und von Primärstudien.
- Schulpopulationen: `galezer2004efficiency`, `vogelsanger2025solutionplan` und ein Teil von `lindl2025costamm`.

**Alternative Erklärungen.**
- *Engagement-Stufen:* mehr Lernzeit statt aktiver Operation (`grissom2003avengagement`).
- *Repräsentation zuerst:* mehr Zeit und Aufmerksamkeit für die Aufgabe statt Repräsentation als solcher.
- *Lösungsplan:* mehr Modellierungsübung als in der Kontrollgruppe (regulärer Unterricht).
- *Invariante vorgegeben:* Die Vorgabe enthält Teile der Lösung (Grenzen, Variablenrollen); weniger Fehler bedeuten dann nicht mehr Verständnis.

**Validitätsrisiken im Produkt.**
1. Vorhersagen im Stepper werden als Kompetenzbeleg gezählt, obwohl sie assistiert und unmittelbar sind.
2. Eine Laufzeitprüfung von Invarianten wird als Beweis angezeigt.
3. Operationszähler oder Zeitmessung ersetzen die Komplexitätsherleitung.
4. Prinzipwahl gegen Schlüssel wird mit Problemlösekompetenz verwechselt (Proxy).
5. Modellierungsergebnisse werden mit einer Einzelzahl bewertet.

Gegenmaßnahmen stehen in den Enthaltungen von POL-17 bis POL-21 und in der Verifier-Ergänzung. Ob sie greifen, ist ungeprüft.

### 12.7 Fragen an unabhängige Gutachterinnen und Gutachter

1. Stimmen die Sekundärzahlen zur Meta-Studie von Hundhausen et al. mit dem Primärtext überein? Gibt es eine neuere Metaanalyse mit Effektgrößen zu Algorithmenvisualisierung, die zu einem anderen Ergebnis kommt?
2. Gibt es experimentelle Hochschulevidenz mit verzögertem Maß zur Vermittlung asymptotischer Analyse?
3. Gibt es kontrollierte Studien zu Invarianten- oder Verifikationsansätzen (z. B. Dafny, Frama-C) mit verzögertem Papier-Outcome?
4. Schadet „Repräsentation vor der Rechnung“ Fortgeschrittenen (Expertise-Umkehr)? Reicht die Überspring-Regel in POL-20?
5. Wurde der Lehrstil in den CoSTAMM-Studien randomisiert zugeteilt, und gibt es dort eine unbehandelte Kontrolle?
6. Rechtfertigt der deskriptive Befund zu Mediatoren eine eigene Diagnose-Policy für Kausalinferenz, oder bleibt das eine Lücke?
7. Fehlt Lernevidenz zu Finanz- oder Wirtschaftsmodellierung, die R2S übersehen hat?

## 13. Was wir nicht behaupten können

- Dass eine Policy in Mastery Lernen verbessert: Es gibt weder Implementierung noch Evaluation.
- Dass die Stufen eine externe GRADE-Bewertung sind.
- Dass Beweisbefunde aus Zahlentheorie und reeller Analysis auf andere Gebiete, auf Physik oder auf Wirtschaftsmodellierung übertragbar sind.
- Dass Tracing-Übung das Schreiben kausal verbessert (die Hierarchie ist korrelativ).
- Dass Beweisassistenten, Parsons-Aufgaben oder Autograder Lernwirkung haben.
- Dass LLM-Bewertung von Beweisen verlässlich ist. Und umgekehrt: dass sie für immer unbrauchbar bleibt, denn die Zahlen gelten für Modelle von 2025/26.
- Dass die Lead-Stichprobe die übrigen 36 Einträge der Batches 1–4 bestätigt. Batch 5 hat keine Lead-Stichprobe.
- Dass Algorithmenvisualisierung, Invarianten-Gerüste, Repräsentation vor der Rechnung oder ein Lösungsplan in Mastery verzögerte, unassistierte Leistung verbessern (POL-17 bis 21).
- Dass Befunde aus einführender Mechanik und Schulmodellierung auf andere quantitative Fächer, auf Hochschulmodellierung oder auf Finanzmodellierung übertragbar sind.
- Dass Studierende ein bestimmtes Training zu Kausaldiagrammen brauchen oder davon profitieren; belegt ist nur ein Defizit in einer Kohorte.
- Dass die Suche vollständig oder reproduzierbar im Sinne einer systematischen Übersicht war.

## 14. Reproduktion

```bash
cd tests && python3 -m unittest test_r2_learning_policies test_r1_learning_policies
python3 -c "import json; [json.load(open('docs/research/workstreams/r2/'+f)) for f in ('r2_evidence.json','r2_learning_policies.json')]"
```

§5 und §12.2 dieses Berichts sind aus `r2_learning_policies.json` und `r2_evidence.json` erzeugt (Felder `recommendation`, `observable`, `independent_outcome`, `failure_modes`, `falsifier`, `abstain_or_fallback`, Zugangsstufe je Quelle). Bei Abweichungen gilt die JSON-Datei. Das Repository enthält keine Volltexte, Vorlesungsmaterialien oder Lernerdaten. Befunde sind paraphrasiert und mit Fundstellen versehen.
