# R2 — Formale, quantitative und computationale Kompetenz: Synthese und Learning Policies

Stand 27.11.2026. **Forschungsergebnis zur Begutachtung, keine Freigabe.** Alle 16 Policies sind `design_hypothesis` mit `learning_evaluation: NOT_RUN`. Keine Policy ist implementiert. Kein Mastery-Produkt hat dadurch eine nachgewiesene Lernwirkung. Historische `HUMAN_REJECTED`-Bewertungen bleiben unverändert.

**Produktidentität:** Seit Issue #34 heißt das Produkt **Mastery**, eine allgemeine Plattform für den Erwerb von Wissen und Fertigkeiten. Prüfungsvorbereitung ist ein optionaler Modus. R2 gilt für jede Lernsituation mit Beweisen, symbolischen Verfahren, Programmierung oder statistischem Schließen. Der Phasenwert `final_exam_week` betrifft nur den Prüfungsmodus. Issue #23 nennt die Ausgabedatei `FORMAL_COMPUTATIONAL.md`; im Programm heißt sie `R2_FORMAL_QUANTITATIVE.md`, Inhalt und Auftrag sind dieselben.

| Artefakt | Inhalt |
|---|---|
| [r2/r2_evidence.json](r2/r2_evidence.json) | Evidenzregister, 40 Einträge im R1-Schema (`r1-evidence/1`): Beweise (17), Programmierung (16), Statistik (3), symbolische Verfahren, Problemlösen und E-Assessment (4). Zugangsstufen: 2 Volltext teilweise, 10 Volltext-Claim-Review, 27 nur Abstract, 1 nur Metadaten. |
| [r2/r2_learning_policies.json](r2/r2_learning_policies.json) | 16 Policies, 4 Konfliktregeln, zurückgestellte Operationen, deklarierte Lücken, Prüfprotokoll des Leads. |
| `tests/test_r2_learning_policies.py` | Wendet den R1-Strukturvertrag auf R2 an (Quellen auflösbar, Parameter als vorläufig markiert, KB-Regelverweise existieren, Kernoperationen abgedeckt, Prüferpolicy vorhanden, Lücken deklariert). Prüft Struktur, nicht wissenschaftliche Richtigkeit. |

Arbeitsteilung: Ein Spezialistenlauf (R2) hat Register und Policies in mehreren unbeaufsichtigten Sitzungen erstellt. Dieser Bericht und die Stichprobe in §9 stammen vom Lead. Lead und Spezialist sind dasselbe Modell. Eine menschliche oder unabhängige Fachprüfung steht aus.

**Lesart.** Jede Aussage ist einer von vier Arten zugeordnet: **Befund** (im Register mit Fundstelle belegt), **Hypothese** (plausibel aus Befunden abgeleitet, ungeprüft), **Designentscheidung** (Produktsetzung, die sich nicht empirisch begründen lässt), **nicht gestützt** (in §12 gesammelt).

## 1. Ergebnis in zehn Punkten

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

## 2. Suchjournal, Ein- und Ausschluss, Zugang

**Was protokolliert ist.** Metadatenabgleich über Crossref (27 DOIs), OpenAlex (ca. 30 Werke) und Semantic Scholar (8 Abfragen), jeweils über die freien APIs am 27.11.2026. Volltextabrufe: 26 von 45 budgetierten Seitenabrufen. Den Zugangsweg und die gelesenen Abschnitte jeder Quelle enthält `access` im Register; gescheiterte Volltextwege stehen dort in `access.url`, z. B. für `hodds2014selfexplanation` (Artikel gesperrt, inhaltsgleiche Dissertation gelesen) und `neuhaus2025proofskills` (Verlagsseite blockiert, Repositoriumsfassung gelesen).

**Was fehlt (deklarierte Lücke).** Die Spezialistenläufe haben die exakten Suchstrings nicht in die Checkpoints übernommen. Eine Suchtabelle wie in R0 (`SEARCH_PROTOCOL.md` §1) lässt sich deshalb für R2 nicht nachträglich wahrheitsgemäß erstellen. Sie wird hier auch nicht rekonstruiert. Reproduzierbar sind die eingeschlossenen Quellen über DOI/URL, Zugangsstufe und gelesene Abschnitte, nicht der Suchweg. Die geplanten Suchblöcke Q1–Q5 des Auftrags (Beweis, symbolisch, Programmierung, Statistik/Kausalinferenz, Physik/Finanzmodellierung) sind nicht als formale Suche abgeschlossen (siehe `coverage_gaps`).

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
| Methode wählen/begründen | Beweisstrategie | Verfahren | Algorithmus/Datenstruktur | Test/Modell | Mensch; kein automatischer Prüfer belegt | keine direkte Evidenz |
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
- 27 von 40 Quellen nur als Abstract. Programmier- und Symbolik-Policies stützen sich fast ausschließlich darauf.
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
| Symbolisches Schließen, Fehlvorstellungen, Problemlösen | POL-04, POL-15 | teilweise; nur Abstracts, Schulmetaanalyse 1992 |
| Programmierung: Tracing, Parsons, Schreiben/Debuggen/Testen | POL-08–13 | bearbeitet; überwiegend Abstracts |
| Komplexitätsanalyse | — | **nicht bearbeitet** |
| Property-Testing | POL-13 (`wrenn2021pbt`) | nur Erfahrungsbericht |
| Statistik | POL-16 | teilweise; beobachtend |
| Kausalinferenz | — | **nicht bearbeitet** über Einführungsstatistik hinaus |
| Mathematische Physik, Finanz-/Wirtschaftsmodellierung | — | **nicht bearbeitet** |
| Verifier-Frage | §4, POL-14 | bearbeitet (Designentscheidung) |
| Adversariale Aufgaben | §7.2, POL-06 | bearbeitet |
| Lernoperationsmatrix | §3 | bearbeitet |
| Suchjournal mit exakten Queries | §2 | **Lücke**: Queries nicht protokolliert |

**Priorisierte Lücken:**
1. Formale Suche Q1–Q5 mit protokollierten Queries und Ein-/Ausschlusszahlen.
2. Volltexte zu Teilzielen (Morrison 2015), Parsons (Ericson 2017), PRIMM, Debugging-Metaanalyse, STACK.
3. Physik- und Finanzmodellierung, Komplexitätsanalyse, Kausalinferenz.
4. Seed 10.1145/3501385.3543977.
5. Experimentelle Belege für Validierungs- oder adversariale Übungen.
6. Unabhängige Zweitextraktion der Volltextzahlen.

**Übergaben:**
- R5 (LLM-Bewertung, Tutor-Abhängigkeit, `agent_judgement`)
- R6 (Sequenz aus §7.1 und R2-CR-1)
- R7 (Prüferdeklaration als Datenfeld, Anzeige „nicht beobachtet“)
- P4-Engineering (Prüferdeklaration im Lernstand, erst nach R6)

## 12. Was wir nicht behaupten können

- Dass eine Policy in Mastery Lernen verbessert: Es gibt weder Implementierung noch Evaluation.
- Dass die Stufen eine externe GRADE-Bewertung sind.
- Dass Beweisbefunde aus Zahlentheorie und reeller Analysis auf andere Gebiete, auf Physik oder auf Wirtschaftsmodellierung übertragbar sind.
- Dass Tracing-Übung das Schreiben kausal verbessert (die Hierarchie ist korrelativ).
- Dass Beweisassistenten, Parsons-Aufgaben oder Autograder Lernwirkung haben.
- Dass LLM-Bewertung von Beweisen verlässlich ist. Und umgekehrt: dass sie für immer unbrauchbar bleibt, denn die Zahlen gelten für Modelle von 2025/26.
- Dass die Lead-Stichprobe die übrigen 36 Einträge bestätigt.
- Dass die Suche vollständig oder reproduzierbar im Sinne einer systematischen Übersicht war.

## 13. Reproduktion

```bash
cd tests && python3 -m unittest test_r2_learning_policies test_r1_learning_policies
python3 -c "import json; [json.load(open('docs/research/workstreams/r2/'+f)) for f in ('r2_evidence.json','r2_learning_policies.json')]"
```

§5 dieses Berichts ist aus `r2_learning_policies.json` und `r2_evidence.json` erzeugt (Felder `recommendation`, `observable`, `independent_outcome`, `failure_modes`, `falsifier`, `abstain_or_fallback`, Zugangsstufe je Quelle). Bei Abweichungen gilt die JSON-Datei. Das Repository enthält keine Volltexte, Vorlesungsmaterialien oder Lernerdaten. Befunde sind paraphrasiert und mit Fundstellen versehen.
