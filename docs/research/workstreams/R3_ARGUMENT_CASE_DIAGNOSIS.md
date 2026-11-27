# R3 — Juristisches, philosophisches, fallbasiertes und klinisches Schließen: Synthese und Learning Policies

Stand 27.11.2026. **Forschungsergebnis zur Begutachtung, keine Freigabe.** Alle 12 Policies sind `design_hypothesis` mit `learning_evaluation: NOT_RUN` und `implementation_status: not_implemented`. Kein Mastery-Produkt hat dadurch eine nachgewiesene Lernwirkung. Historische `HUMAN_REJECTED`-Bewertungen bleiben unverändert. Issue #24 nennt die Ausgabedatei `ARGUMENT_CASE_DIAGNOSIS.md`; im Programm heißt sie `R3_ARGUMENT_CASE_DIAGNOSIS.md`.

| Artefakt | Inhalt |
|---|---|
| [r3/r3_evidence.json](r3/r3_evidence.json) | Evidenzregister im R1-Schema (`r1-evidence/1`), 35 Einträge: Recht 10, Philosophie/Argumentation 6, Management/Ökonomie-Fälle 4, klinisches Schließen 12, Bewertung offener Antworten 3. Zugang: 4 Volltext-Claim-Review, 9 Volltext teilweise, 22 nur Abstract. Mit `search_log` (23 protokollierte Suchen, auch erfolglose). |
| [r3/r3_learning_policies.json](r3/r3_learning_policies.json) | 12 Policies, 4 Konfliktregeln, Messvertrag, zurückgestellte Operationen, `coverage_gaps`, Selbstprüfprotokoll. |
| `tests/test_r3_learning_policies.py` | R1-Strukturvertrag auf R3 angewandt, plus: Kernoperationen abgedeckt, `coverage_gaps` vorhanden, jede klinisch-/rechtspraktische Policy trägt eine `practice_boundary` mit Enthaltungsgrund, Simulationsgrenze (R3-POL-10) normativ, LLM-Feedback bleibt `FEEDBACK_UNVERIFIED`, jedes Register-Element stammt aus einer protokollierten Suche. Prüft Struktur, nicht wissenschaftliche Richtigkeit. |

Autorenschaft: ein einzelner Spezialistenlauf (R3). Es gab keinen Lead-Review und keine menschliche Fachprüfung. Die Stichprobenkontrolle in `verification_log` ist eine **Selbstprüfung** und zählt nicht als unabhängiges Review.

**Lesart.** Jede Aussage ist markiert als **Befund** (im Register mit Fundstelle), **Hypothese** (abgeleitet, ungeprüft), **Designentscheidung** (Produktsetzung ohne empirische Begründung) oder **nicht gestützt** (§11).

## 1. Ergebnis in zehn Punkten

1. **Für das Lernen des deutschen Gutachtenstils fehlt empirische Evidenz.** *Befund:* Die Suche auf Deutsch und Englisch (R3-S07, R3-S08) fand keine Lernstudie. Die einzige empirische Arbeit mit Gutachten bewertet LLM-Benotung, nicht Lernen (`zubaer2026gradelegal`). *Designentscheidung:* Das Gutachtenschema ist Gerüst, nicht Bewertungsziel (R3-POL-03).
2. **Juristische Falllösung profitiert bei Novizen von reduzierter Suchlast und Lösungsbeispielen.** *Befund:* Wer in der Lernphase nur die einschlägigen 12 Artikel nutzte, löste später einen Fall mit dem vollständigen Gesetz besser (M = 23,37 gegen 12,74; F(1,75) = 15,46; N = 79; `nievelstein2011lawsupport`, Volltext). Lösungsbeispiele halfen Novizen und Fortgeschrittenen, ein Expertise-Reversal zeigte sich nicht (`nievelstein2013lawexamples`, nur Abstract).
3. **Argumentdiagramme im Recht: gemischt.** *Befund:* Das LARGO-System half in einer Pilotstudie vor allem schwächeren Studierenden, im verpflichtenden Kurs gab es keinen Unterschied (`pinkwart2009largo`, Abstract). Die Autoren betonen, dass sich die Richtigkeit juristischer Argumente nicht formal prüfen lässt.
4. **Sprachmodelle sind keine Rechtsquelle.** *Befund:* 58–88 % Halluzinationen bei überprüfbaren Fragen zu US-Bundesentscheidungen, systematisch überhöhte Modellkonfidenz (`dahl2024legalfictions`). Auch RAG-Rechercheprodukte halluzinierten in 17–33 % der Fälle und zitierten etwa eine aufgehobene Entscheidung als geltend (`magesh2025legalrag`). *Designentscheidung:* Rechtsaussagen nur mit Quelle, Fassung und Stichtag, sonst Enthaltung (R3-POL-01).
5. **Intensive Argumentanalyse mit Rückmeldung überträgt sich, aber der Anteil der Karte ist unbekannt.** *Befund:* LSAT-Gewinn d = 0,71 [0,37; 1,04], Essays d = 0,87, nicht randomisiert; die Autoren können Visualisierung nicht von intensiver Betreuung trennen (`cullen2018argumentvisualization`, Volltext). Die Meta-Analyse zu Critical-Thinking-Instruktion findet g+ = 0,30 bei hoher Heterogenität (`abrami2015ctmeta`, Abstract).
6. **Formales Logiktraining überträgt sich nur begrenzt.** *Befund:* 40 Stunden Konditionallogik ohne Effekt auf Wahlaufgaben (Cheng et al. 1986, nur als Sekundärbeschreibung in `attridge2013conditional`). Mathematikschüler veränderten ihr Konditionalverständnis, aber zur „defective“- statt zur normativen Lesart.
7. **Entscheidungsfälle: Debiasing-Training überträgt sich auf einen unangekündigten Business-Fall.** *Befund:* Trainierte wählten im 6-Tage-Fenster seltener die bestätigende, schlechtere Option (48,0 % gegen 72,7 %; N = 290; nicht randomisiert; `sellier2019debiasing`, Volltext). Fallvergleich fördert Schema-Transfer (`gentner2003analogicalencoding`). Für die Fallmethode als Ganzes ist die Evidenz uneinheitlich; Zufriedenheit ist hoch (`thistlethwaite2012cbl`). Kontrollierte Evidenz zur Business-Fallmethode wurde nicht gefunden.
8. **Klinisch: Gezielte Reflexion verbessert verzögertes Diagnostizieren an schriftlichen Fällen. Der Sofortvorteil täuscht.** *Befund:* Unmittelbar schnitt die Reflexionsgruppe schlechter ab (0,48 gegen 0,62), nach einer Woche besser (0,66 gegen 0,48/0,52; N = 46; `mamede2012reflection`). Gelenkte Reflexion schlug freie, aber auf Nachbarerkrankungen übertrug sich nichts (`mamede2019guidedreflection`).
9. **Generisches Debiasing und Checklisten: überwiegend Nullbefunde.** *Befund:* „Langsam und gründlich“ brachte 45,0 % gegen 44,5 % Genauigkeit (`norman2014system1`). Cognitive-forcing-Training bei Studierenden blieb ohne Effekt (`sherbino2014forcing`). Eine Checkliste in der Praxis senkte Fehler nicht signifikant (`ely2015checklists`). Werkzeuge *während* der Diagnose bringen g = 0,20 (`staal2022reasoningtools`). Ärztinnen und Ärzte waren bei schweren Fällen nur zu 5,8 % richtig, aber fast so zuversichtlich wie bei leichten (`meyer2013calibration`).
10. **Mehrdeutige Antworten bewerten: Rubrik und Mensch, Modell nur als Hinweis.** *Befund:* LLM-Benotung deutscher Gutachten erreicht im öffentlichen Recht QWK 0,911 (16 Lösungen), im Strafrecht nur 0,599 (71 Lösungen) (`zubaer2026gradelegal`). Bei US-Klausuren ist r bis 0,93 nur mit detaillierter Rubrik erreicht (`cope2026gradingmachines`). Expertinnen und Experten selbst erreichen bei Differenzialdiagnose-Begründungen nur κ = 0,66 (`goh2024llmdiagnosis`). Panel-Aggregatbewertung kann einen Antwortstil belohnen (`lineberry2013sct`).

## 2. Methode, Suche, Zugang

**Protokoll.** R0-Methode ([SEARCH_PROTOCOL.md](SEARCH_PROTOCOL.md)), Registerschema ([EVIDENCE_REGISTER_SCHEMA.md](EVIDENCE_REGISTER_SCHEMA.md)) und R1-Policyformat. Gesucht wurde nur mit freien Quellen: Crossref REST, OpenAlex, Semantic Scholar Graph API, Europe PMC REST, NCBI E-utilities, arXiv sowie allgemeine Websuche und direkter Abruf. Alles am 27.11.2026 mit generischem User-Agent und ohne personenbezogene Daten. Keine Lizenzdatenbanken (PsycINFO, Scopus, Web of Science, Westlaw, beck-online, juris).

**Suchjournal.** Alle 23 Suchen stehen mit exakter Query, Werkzeug, gesichteter Trefferzahl, Einschlüssen und Ausschlussgründen im `search_log` des Registers (R3-S01 bis R3-S23). Erfolglose Suchen sind ebenfalls protokolliert, z. B. R3-S07 (Gutachtenstil), R3-S17 (Business-Fallmethode) und R3-S20 (Schwarcz & Farganis, HTTP 403). Der Test prüft, dass jeder Registereintrag aus einer protokollierten Suche stammt. Es gibt keine PRISMA-Flussgrafik, weil kein deduplizierbarer Gesamtexport existiert.

**Ein- und Ausschluss** (vor der Suche festgelegt, nicht präregistriert): (a) Lernende in Hochschule oder Berufsausbildung; Schulstudien nur gekennzeichnet (`attridge2013conditional`). (b) Das Outcome ist eine Leistung im juristischen, argumentativen, fallbasierten oder diagnostischen Schließen oder die Validität ihrer Bewertung. (c) Zugelassen sind Experiment, Quasi-Experiment, Messstudie, Review oder Metaanalyse; Benchmarks nur für Werkzeugrisiken, Theorie nur als Kontext. (d) Der Locator muss verifizierbar sein. Ausgeschlossen wurden Quellen ohne zugängliches Abstract (Cheng 1986, Farashahi 2018, Jonsson & Svingby 2007, Schwarcz & Farganis), reine Modell-Prüfungsleistung ohne Lern- oder Bewertungsbezug (Choi et al. 2023) und Budget-Doppelungen (Ibiapina 2014, Huber & Kuncel 2016). Nicht erreichbarer Zugang ist kein inhaltlicher Ausschluss.

**DOI-Prüfung.** Jede DOI im Register wurde über Crossref aufgelöst (R3-S01, S08, S17, S19, S23); Titel, Erstautoren und Jahr stimmen überein. Ohne DOI: `zubaer2026gradelegal` (arXiv) und `gii2026hinweise` (amtliche Webseite).

**Zugangstiefe nach Domäne.** Recht: 5 von 10 auf Volltextebene (drei davon Preprint-Fassungen, deren Version of Record nicht verglichen wurde, eine amtliche Webseite). Philosophie: 2 von 6. Management: 1 von 4. Klinik: 5 von 12. Bewertung: 0 von 3. Abstract-Einträge zitieren nur Zahlen, die im Abstract stehen. Gesperrte Wege (Wiley, OUP, BMJ, SSRN, ScienceDirect, HTTP 403) stehen jeweils in `access.url`.

**Seeds.** `nesbit2025argumentmapping` (DOI 10.1111/hequ.70063): nur Abstract, Volltext gesperrt. `wark2025clinicalreasoning` (PMC12758103): Volltext teilweise. `cooper2018lawstudyhabits` (SLU-Seed): nur Abstract, PDF gesperrt, korrelative Umfrage.

## 3. Recht

**Validitätswarnung.** Fast alle Lernstudien stammen aus den Niederlanden oder den USA und messen unmittelbar nach dem Lernen. Die LLM-Befunde betreffen US-Recht und Modellstände von 2023/24. Ob sie sich auf deutsches Recht übertragen lassen, ist ungeprüft. Gutachtenstil, Auslegungsmethoden und formatives Feedback im deutschen Studium sind empirisch nicht abgedeckt.

- **Issue Spotting.** Keine Interventionsstudie gefunden. *Befund (korrelativ, Abstract):* Selbsttests mit Anwendung hängen mit besseren Jura-Noten zusammen, Briefing und Auswendiglernen ohne Anwendung negativ (`cooper2018lawstudyhabits`). *Hypothese:* Unannotierte Sachverhalte trainieren das Erkennen der Probleme, das Klausuren verlangen; hervorgehobene Probleme nehmen genau diese Operation ab (R3-POL-02).
- **Subsumtion und strukturierte Falllösung.** *Befund:* Siehe §1 Punkt 2. Die Autoren schlagen selbst vor, den Suchraum schrittweise auf das volle Gesetz zu erweitern. Dieser Vorschlag ist ungeprüft (`nievelstein2011lawsupport`, Discussion). *Designentscheidung:* Fading von Beispielen und vom Normbestand (R3-POL-03). Bewertet wird die Tragfähigkeit der Subsumtion, nicht die Form.
- **Fallanalyse und Hypotheticals.** *Befund:* LARGO ohne Effekt in der ökologisch valideren Studie (`pinkwart2009largo`). *Hypothese:* Kontrafaktische Variation einer einzelnen Tatsache macht das entscheidende Merkmal sichtbar (R3-POL-04). Belegt ist nur der allgemeine Fallvergleichseffekt (`gentner2003analogicalencoding`, R1A `alfieri2013comparison`).
- **Datierte Autorität.** *Befund (normativ-technisch):* Konsolidierte Texte auf gesetze-im-internet.de sind nicht amtlich. Maßgeblich ist das Bundesgesetzblatt, seit 1.1.2023 elektronisch. „Stand“ verweist auf das letzte Änderungsgesetz (`gii2026hinweise`). *Befund:* Modelle und RAG-Werkzeuge geben überholtes Recht als geltend aus (`magesh2025legalrag`, Figure 2). *Designentscheidung:* R3-POL-01.
- **Formatives Feedback und Probeklausuren.** Die einzige gefundene kontrollierte Studie (Schwarcz & Farganis, natürliches Experiment zu individueller Rückmeldung) war nicht lesbar und ist deshalb nicht registriert. Wir behaupten **nichts** über ihre Ergebnisse. Allgemeine Feedbackevidenz liefert R1 (R1-POL-A08).
- **LLM-Leistung und Benotung.** *Befund:* Mit GPT-4 lösten Jurastudierende Aufgaben deutlich schneller, aber kaum besser (`choi2024lawyeringai`, Abstract). Das ist assistierte Leistung, kein Lernen. Zur Benotung siehe §7.

## 4. Philosophie und Argumentation

**Validitätswarnung.** Die stärksten Studien sind nicht randomisiert oder vergleichen mit Gruppen ganz ohne Instruktion. Das Kartenformat ist deshalb mit Betreuungsintensität konfundiert. Critical-Thinking-Tests (CCTST, HCTA, LSAT) messen unterschiedliche Konstrukte; Cullen et al. halten den CCTST selbst für psychometrisch schwach. Zu interpretativer Fairness („charity“) fehlt empirische Evidenz.

- **Argument Mapping.** *Befund:* Die systematische Übersicht kodiert 124 Studien. Viele messen Einstellungen (44 %) oder Kartenqualität (51 %), nicht Transfer (`nesbit2025argumentmapping`, Abstract). Positive Transferbefunde: `cullen2018argumentvisualization`, `dwyer2012argumentmapping`. Gegenbefund im Recht: `pinkwart2009largo`. *Designentscheidung:* Die Karte ist Werkzeug, Messung erfolgt an unkartierten Texten (R3-POL-05).
- **Einwand und Erwiderung.** *Befund:* Ein Organizer erzeugt mehr Widerlegungen, Kriterieninstruktion bessere Integration (`nussbaum2007counterargument`). Wie viele Widerlegungen jemand nennt, sagt also nichts darüber, wie gut er sie abwägt.
- **Logikunterricht.** Siehe §1 Punkt 6. *Designentscheidung:* Kein Transferversprechen; formale Aufgaben immer mit Fachargumenten koppeln (R3-POL-06).
- **Bewertung argumentativer Essays.** Siehe §7. LLM-Bewertung philosophischer Essays wurde nicht gesichtet (Lücke).

## 5. Ökonomie-, Management- und Gründungsfälle

**Validitätswarnung.** Nur eine Feldstudie (`sellier2019debiasing`, quasi-experimentell) betrifft Managementstudierende direkt. Die Belege zur Fallmethode stammen aus der Medizin (`thistlethwaite2012cbl`, `dochy2003pbl`). Zu kontrafaktischem Denken fand die Suche nur Theoriekapitel. Ob eine Managemententscheidung „richtig“ war, lässt sich oft nur am später bekannten Ergebnis messen. Musterlösungen laufen deshalb Gefahr, Rückschaufehler zu lehren.

- **Messbar:** Zahl und Verschiedenheit der Alternativen, Kriterien vor der Wahl, Qualität der Widerlegungstests, Konsistenz der Wahl mit den genannten Kriterien, Rechenkorrektheit (R2-Prüfer) und das Verhalten in unangekündigten Bestätigungsfallen (`sellier2019debiasing`).
- **Nicht messbar im Produkt:** Qualität realer Entscheidungen, unternehmerischer Erfolg und Urteilskraft unter echten Anreizen. Das Produkt behauptet hierzu nichts (R3-POL-07).
- **Fallmethode:** Wissenserwerb und Anwendung werden getrennt geprüft, weil problembasiertes Lernen bei Fertigkeiten robust positiv, beim Wissen nicht robust wirkt (`dochy2003pbl`; R3-POL-12).

## 6. Klinisches Schließen (nur Ausbildung)

**Harte Grenze.** Virtuelle Fälle, schriftliche Vignetten und generierte Erklärungen belegen **keine** Kompetenz am realen Patienten. Das Produkt zertifiziert nichts und gibt keine Behandlungsempfehlungen für reale Personen (R3-POL-10, `practice_boundary` in allen klinischen Policies).

**Validitätswarnung.** Fast alle Lernexperimente nutzen schriftliche Fälle, die alle Befunde liefern. In der Praxis müssen Befunde erst erhoben werden; diese Lücke benennt die Reflexionsforschung selbst (`mamede2022deliberatereflection`). Die Reflexionsstudien stammen überwiegend aus einer Forschungsgruppe. Virtuelle-Patienten-Studien messen Fertigkeiten fast nie an realen Patienten (laut Übersicht nur in einer Studie; meist standardisierte Patienten oder Papierfälle; `kononowicz2019virtualpatients`). Die Seed-Metaanalyse poolt unstandardisierte Mittelwertdifferenzen über verschiedene Instrumente (I² = 88 %, 6 RCTs; `wark2025clinicalreasoning`). Die gepoolte Zahl ist daher kaum interpretierbar.

- **Illness Scripts.** Theorie als Repräsentationsziel (`schmidt2007illnessscripts`), kein Interventionsbeleg. *Designentscheidung:* Skriptkomponenten (prädisponierende Faktoren, Pathophysiologie, Befunde) als Abrufkarten, ausdrücklich ohne Diagnosekompetenz-Aussage.
- **Gezielte Reflexion und Differenzialdiagnose.** Siehe §1 Punkt 8. Wer nur eine Differenzialdiagnose auflistet, lernt nicht besser als bei einer Sofortdiagnose (`mamede2012reflection`). *Designentscheidung:* Reflexionstabelle mit stützenden, widersprechenden und fehlenden Befunden für drei Hypothesen; Messung nach ≥ 7 Tagen (R3-POL-08).
- **Debiasing und Checklisten.** Siehe §1 Punkt 9. *Designentscheidung:* Kein Wirkversprechen für generische Checklisten; Checklisten nur als assistierte Arbeitshilfe gekennzeichnet (R3-POL-09).
- **Kalibrierung.** *Befund:* Die Konfidenz reagiert kaum auf die Genauigkeit (`meyer2013calibration`), und Modellkonfidenz ist ebenso überhöht (`dahl2024legalfictions`). *Hypothese:* Rückmeldung zur Kalibrierung über viele Fälle verbessert sie. Ungeprüft, `very_low`.
- **Virtuelle Patienten und reale Praxis.** *Befund:* Gegenüber traditioneller Lehre: Wissen SMD 0,11 [−0,17; 0,39], Fertigkeiten SMD 0,90 [0,49; 1,32], hohe Heterogenität, niedrige Evidenzqualität (`kononowicz2019virtualpatients`). Die Autoren schreiben, virtuelle Patienten sollten den realen Kontakt ergänzen, nicht ersetzen.
- **LLM als Diagnosehilfe.** *Befund:* Der Zugang zu GPT-4 verbesserte das ärztliche Schließen nicht (2 Prozentpunkte [−4; 8]), obwohl das Modell allein besser abschnitt (`goh2024llmdiagnosis`). Für Lernen heißt das: Selbst eine starke Hilfe erzeugt keine eigene Kompetenz (R3-POL-12, R5-POL-04).

## 7. Mehrdeutige, aber vertretbare Antworten bewerten

| Bewertungsweg | Belegt | Grenze | Produktstatus |
|---|---|---|---|
| Rubrik mit klaren Kriterien | Qualität bei klaren, fokussierten Kriterien (`brookhart2015rubrics`, Abstract) | eine Rubrik aus einer Musterlösung kodiert eine Route | Pflicht, mit ausdrücklichen Alternativrouten und Beispielantworten |
| Menschliche Doppelbewertung | Experten-κ 0,66 bei Diagnosebegründungen (`goh2024llmdiagnosis`); menschliche QWK 0,911 im öffentlichen Recht, aber nur 16 Lösungen (`zubaer2026gradelegal`) | Kosten, Drift | einzige Quelle für Kompetenzbelege; Stichprobe mit berichteter Übereinstimmung |
| Comparative Judgement | SSR .70 ab ca. 10–14 Vergleichen je Arbeit (`verhavert2019cj`) | Reliabilität ist nicht Validität (R2 `davies2020cjproof`); braucht Kohorte | Option für Kurse und Peer-Pools |
| Panel-Aggregatbewertung (SCT-Stil) | — | belohnt das Meiden von Extremen (`lineberry2013sct`) | nicht ohne Reliabilitätsprüfung |
| LLM-Bewertung | QWK 0,911 (öffentliches Recht) bzw. 0,599 (Strafrecht); r bis 0,93 nur mit Rubrik (`zubaer2026gradelegal`, `cope2026gradingmachines`) | domänen-, rubrik- und modellabhängig; überhöhte Konfidenz; Halluzinationen | nur `FEEDBACK_UNVERIFIED` (`agent_judgement`), Abweichungsflag für menschliche Zweitprüfung |

**Was menschlich geprüft bleiben muss** (Designentscheidung, R3-POL-11): jede Kompetenzaussage aus offenen Antworten; jede Rechtsaussage zum geltenden Recht (R3-POL-01); Problemlisten und Rubriken samt Alternativrouten; jede Antwort, die von der Rubrik abweicht, aber begründet ist („Prüfung nötig“ statt „falsch“); klinische Referenzdiagnosen und Lösungswege.

**Unsicherheitssignal im Produkt:** Jede Bewertung zeigt ihre Quelle („menschlich bewertet“, „Modell-Feedback, nicht geprüft“ oder „Prüfung nötig“) und die Rubrikversion; Rechtsaussagen zusätzlich den Rechtsstand. Simulationsergebnisse heißen „Fallleistung in der Simulation“.

## 8. Mechanismusketten und Policies

Kette: Evidenz → Lernoperation → Intervention → Beobachtung → unabhängiges Outcome → Gegenbefund/Versagen. Details, Parameter, Falsifikatoren und Fundstellen stehen in `r3/r3_learning_policies.json`.

| Policy | Evidenz → Operation | Intervention | Beobachtung → unabhängiges Outcome | Gegenbefund/Versagen | Stufe |
|---|---|---|---|---|---|
| R3-POL-01 Datierte Autorität | `gii2026hinweise`, `magesh2025legalrag`, `dahl2024legalfictions` → Normanwendung | Quelle + Fassung + Stichtag; Enthaltung | Anteil „Fassung ungeprüft“ → Audit gegen amtliche Fassung | Stichtag falsch, Wartungslast | normativ |
| R3-POL-02 Issue Spotting | `cooper2018lawstudyhabits` (korrelativ) → Probleme erkennen | unannotierter Sachverhalt, Problemliste vor Gliederung | gefunden/ausgelassen/Scheinproblem → neuer Fall, blind bewertet | Musterlernen; Liste zu eng | very_low |
| R3-POL-03 Falllösung mit Fading | `nievelstein2011lawsupport`, `nievelstein2013lawexamples` → Subsumtion | Lösungsbeispiele, Ausblenden, Normauszug → volles Gesetz | Hilfe je Stufe → verzögerter Fall mit vollem Gesetz | Schema mechanisch ausgefüllt | low |
| R3-POL-04 Kontrafaktische Variation | `gentner2003analogicalencoding`, `alfieri2013comparison`; Gegenbefund `pinkwart2009largo` | eine Tatsache ändern, vorher sagen; Fallpaare vergleichen | Vorhersage + Merkmal → neuer Fall mit kritischem Merkmal | Variantenmuster raten; Rückschaufehler | low |
| R3-POL-05 Argumentrekonstruktion | `cullen2018…`, `dwyer2012…`, `abrami2015ctmeta`, `nussbaum2007…`; Gegenbefund `pinkwart2009largo` | Karte + Einwand + Erwiderung + Charity-Check, Rückmeldung | Rekonstruktion → unkartierter Text und Essay, doppelt blind bewertet | Formalismus, Strohmann | low |
| R3-POL-06 Logik mit Anwendung | `attridge2013conditional` | formale und kontextualisierte Aufgabe gekoppelt | getrennte Logs → neue Fachargumente | nur Muster gelöst | low |
| R3-POL-07 Entscheidungsfälle | `sellier2019debiasing`, `gentner2003…`; qualifiziert durch `thistlethwaite2012cbl`, `dochy2003pbl` | Alternativen, Kriterien, Widerlegungstest, Kontrafaktum | Vorlage → unangekündigte Bestätigungsfalle | Pflichtfelder als Formalie | low |
| R3-POL-08 Gezielte Reflexion | `mamede2012…`, `mamede2019…`, `mamede2022…`; qualifiziert durch `norman2014system1` | Reflexionstabelle, gelenkt bei Novizen, Test ≥ 7 Tage | Tabelle → verzögerte neue Fälle (keine Patientenaussage) | kein Transfer auf Nachbarerkrankungen | low |
| R3-POL-09 Kalibrierung | `meyer2013calibration`, `sherbino2014forcing`; qualifiziert durch `staal2022…`, `ely2015…` | Konfidenz je Hypothese, Kalibrierungsanzeige ab 10 Fällen | Brier-Score → verzögerte Kalibrierung mit Kontrollgruppe | strategische Mittelwerte | low |
| R3-POL-10 Simulation ≠ Autorität | `kononowicz2019…`, `mamede2022…`, `staal2022…` | Label „Simulation“, ABSTAIN bei realen Fällen | Label, Enthaltungen → Audit verbotener Formulierungen | Label übersehen | normativ |
| R3-POL-11 Mehrdeutige Antworten | `zubaer2026…`, `cope2026…`, `goh2024…`, `lineberry2013sct`, `brookhart2015rubrics`, `verhavert2019cj` | Rubrik mit Alternativrouten, Mensch bewertet, LLM = FEEDBACK_UNVERIFIED | Bewertungsquelle, Übereinstimmung → Reliabilitäts- und Validitätsstudie | stille LLM-Nutzung aus Kostengründen | normativ |
| R3-POL-12 Fallmodule mit Wissensprüfung | `dochy2003pbl`, `thistlethwaite2012cbl`, `choi2024…`, `goh2024…` | getrennte Wissens- und Anwendungsprüfung; assistiert zählt nicht | getrennte Logs → verzögerte Prüfung beider Teile | Zeitlast | low |

**Konfliktregeln:** R3-CR-1 (Novizen zuerst Fading, dann unannotiert), R3-CR-2 (LLM nie Pflichtprüfer, wie R2-CR-2), R3-CR-3 (Konfidenz nur stichprobenartig, wie R1-CR-5), R3-CR-4 (Simulationsgrenze hat Vorrang).

**Tutor** (gehört zu Interaktiv, siehe R5): Jede Policy nennt eine `tutor_affordance`. Der Tutor gibt keine Lösung vor dem eigenen Versuch (AI-R1). Inhaltliche Bewertungen gibt er nur als `FEEDBACK_UNVERIFIED` aus. Bei realen Patienten- oder Mandatsfragen antwortet er mit `ABSTAIN(safety_or_professional_boundary)`, ohne Fundstelle mit `ABSTAIN(no_verified_reference)` (Ausgabetypen aus R5-POL-06).

## 9. Synthetische Fälle: je ein durchgerechneter und ein adversarialer Fall pro Domäne

Alle Fälle sind frei erfunden. Sie enthalten kein Vorlesungsmaterial, keine realen Patientendaten und keine Beratung zum geltenden Recht. Rechtliche Beispiele nennen bewusst keine konkreten Paragraphen; sie zeigen nur die Struktur.

**Recht – durchgerechnet.** Synthetischer Sachverhalt, Rechtsstand „fiktives Gesetz G, Fassung vom 01.03.2026“. Norm G-1: „Wer eine fremde bewegliche Sache beschädigt, ist zum Ersatz verpflichtet, wenn er vorsätzlich oder fahrlässig handelt.“ A stößt beim Rangieren gegen das geparkte Fahrrad des B. Schritt 1 (R3-POL-02): Die lernende Person listet die Probleme „fremde Sache“, „Beschädigung“, „Fahrlässigkeit beim Rangieren“, „Schadenshöhe“. Schritt 2 (R3-POL-03, Stufe 2): Der Obersatz ist vorgegeben, Definition und Subsumtion von „Fahrlässigkeit“ ergänzt sie selbst. Schritt 3 (R3-POL-04): Variante „B hatte das Fahrrad in eine markierte Feuerwehrzufahrt gestellt“. Ändert sich das Ergebnis, und an welchem Merkmal? Eine vertretbare Antwort: Die Haftung bleibt, aber ein Mitverschulden ist zu prüfen. Die Rubrik nennt „Mitverschulden geprüft“ und „Mitverschulden verneint mit Begründung“ als vertretbar. Beobachtung: Problemliste, Ergänzungen, Vorhersage. Unabhängiges Outcome: neuer fiktiver Sachverhalt nach einer Woche, blind bewertet.

**Recht – adversarial.** Dieselbe Aufgabe, aber ein Tutor-Modell zitiert „G-1 in der Fassung vom 01.01.2027“ mit einer zusätzlichen Haftungsgrenze, die es nicht gibt, und versichert hohe Sicherheit. Erwartetes Produktverhalten: Die Fassung ist im Kursbestand nicht vorhanden, also `ABSTAIN(no_verified_reference)` und der Hinweis „Fassung ungeprüft“ (R3-POL-01). Die Modellkonfidenz ist kein Signal (`dahl2024legalfictions`). Zweiter Angriff: Die lernende Person antwortet mit einer abweichenden, aber begründeten Konstruktion (Gefährdungshaftung analog). Die Rubrik kennt sie nicht, der LLM-Bewerter vergibt 2 von 18 Punkten. Korrekt ist der Status „Prüfung nötig“ statt „falsch“ (R3-POL-11).

**Philosophie – durchgerechnet.** Synthetischer Text: „Weil Strafe abschrecken soll und milde Strafen nicht abschrecken, sind milde Strafen ungerecht.“ Die Rekonstruktion ergibt: P1 Strafe soll abschrecken. P2 Milde Strafen schrecken nicht ab. Implizite Prämisse P3: Eine Strafe ist ungerecht, wenn sie ihren Zweck verfehlt. K: Milde Strafen sind ungerecht. Stärkster Einwand: P3 setzt voraus, dass Abschreckung der einzige Zweck ist; vergeltende Theorien bestreiten das. Erwiderung: Die Autorin vertritt erkennbar eine rein präventive Theorie; im Rahmen dieser Theorie ist P3 plausibel. Charity-Check: Die Autorin würde P3 vermutlich zustimmen. Gemessen wird an einem neuen, nicht kartierten Text eine Woche später.

**Philosophie – adversarial.** Ein Text mit absichtlich mehrdeutigem „sollen“ (normativ gegenüber prognostisch). Zwei Rekonstruktionen sind vertretbar; die Referenzkarte enthält nur eine. Eine Lernende, die die andere Lesart sauber begründet, darf nicht als falsch gelten. Wer Kartenvollständigkeit als Kompetenz zählt, belohnt Formalismus. Deshalb gilt: Kartenqualität ist kein Lernbeleg (R3-POL-05, Messvertrag).

**Management – durchgerechnet.** Fiktives Start-up „Kistenwerk“: Soll das Unternehmen ein zweites Produkt einführen? Drei Alternativen: einführen, vorher einen Testmarkt aufsetzen, Ressourcen ins Kerngeschäft stecken. Kriterien vor der Wahl: Liquidität 12 Monate und Lerngewinn über die Kundschaft. Widerlegungstest für „einführen“: Wenn weniger als x % der Bestandskundschaft im Vorverkauf bestellen, ist die Annahme „Nachfrage vorhanden“ widerlegt. Kontrafaktum: Was müsste wahr sein, damit das Kerngeschäft besser ist? Bewertet werden Vollständigkeit und Konsistenz, nicht die Entscheidung. Rechenteile prüft ein R2-Prüfer.

**Management – adversarial.** Eine Musterlösung erklärt „einführen“ für richtig, weil das fiktive Unternehmen im Folgekapitel erfolgreich ist. Das ist Rückschaufehler: Das spätere Ergebnis ist nicht das Kriterium der Entscheidungsqualität. Außerdem enthält der Transferfall eine Bestätigungsfalle: Nur die bestätigende Datenquelle ist billig. Wer sie wählt, ohne eine disconfirmierende Prüfung zu planen, zeigt die Verzerrung (`sellier2019debiasing`).

**Klinik – durchgerechnet (nur Ausbildung, synthetisch).** Fiktive Vignette: 58 Jahre, seit zwei Tagen Atemnot bei Belastung, Unterschenkel einseitig geschwollen, kürzlich lange Busreise. Erste Verdachtsdiagnose der lernenden Person: Lungenembolie. Reflexionstabelle (R3-POL-08): stützend (einseitige Schwellung, Immobilisation), widersprechend (keine), erwartet aber fehlend (Angaben zu Puls und Sauerstoffsättigung). Alternativen: Herzinsuffizienz (spricht dagegen: einseitige Schwellung), Pneumonie (fehlend: Fieber, Husten). Konfidenz: 60 % / 25 % / 15 % (R3-POL-09). Nach einer Woche folgen neue Vignetten derselben und benachbarter Erkrankungen. Ergebnislabel: „Fallleistung in der Simulation“. Keine Behandlungsangaben.

**Klinik – adversarial.** Eine Nutzerin schreibt: „Meine Mutter hat genau diese Symptome, was soll ich tun?“ Erwartetes Verhalten: `ABSTAIN(safety_or_professional_boundary)` und der Hinweis auf ärztliche Hilfe bzw. den Notruf, keine Fallbesprechung (R3-POL-10). Zweiter Angriff: Eine Lernende erreicht 95 % in virtuellen Patienten und bittet um ein Zertifikat „klinisch kompetent“. Das Produkt verweigert jede Kompetenz- oder Zertifizierungsaussage, weil Outcomes an realen Patienten fehlen (`kononowicz2019virtualpatients`).

## 10. Risiko- und Validitätsaudit, alternative Erklärungen

| Risiko | Wo | Alternative Erklärung / Gegenmaßnahme |
|---|---|---|
| Konfundierung von Methode und Betreuungsintensität | `cullen2018…`, `dwyer2012…` | Gewinne könnten aus Rückmeldung und Zeit stammen, nicht aus Karten; daher Policy-Stufe low und Falsifikator Karte gegen Prosa |
| Eine Forschungsgruppe, Entwicklerbias | Reflexionsstudien (Mamede/Schmidt), Nievelstein, LARGO | Replikation durch unabhängige Gruppen fehlt im Register |
| Selbstselektion | `sellier2019…`, `cooper2018…`, `attridge2013…` | stärkere Lernende üben anders; Zeitfensteranalyse bei Sellier mildert, ersetzt keine Randomisierung |
| Sofort- statt verzögerter Messung | `nievelstein2011…`, `wark2025…` | `mamede2012reflection` zeigt Rangumkehr nach einer Woche; deshalb verzögerte Messung im Messvertrag |
| Vignette ≠ Praxis | Klinik insgesamt | Befunde werden geliefert statt erhoben; daher R3-POL-10 |
| Publikationsbias | `wark2025…` (46 von 50 positiv), Fallmethode | Positivquote nicht als Wirksamkeit lesen |
| Zeitgebundenheit von LLM-Befunden | Dahl, Magesh, Cope, GradeLegal, Goh | Modelle ändern sich; Policies verlangen Validierung je Modell und Aufgabentyp statt pauschaler Zulassung |
| Kleine Stichproben bei LLM-Bewertung | GradeLegal öffentliches Recht (16 Lösungen) | Autoren nennen die Schätzung vorläufig |
| Abstract-Lektüre | 22 von 35 Einträgen | Zahlen nur aus Abstracts zitiert; Design-Details als unbekannt markiert |
| Sprach- und Rechtsraum | fast nur US/NL/BR/DE-Einzelstudien | keine Aussage über andere Rechtsordnungen |
| Prüferkosten | R3-POL-11 | Menschliche Prüfung ist teuer; Risiko stiller Automatisierung, deshalb Testfall im Audit |

## 11. Was wir nicht behaupten (nicht gestützt)

- dass der Gutachtenstil oder irgendein juristisches Prüfungsschema als Lernmethode wirkt;
- dass Argument Maps als Format kritisches Denken verbessern (nur Training mit Karten plus Rückmeldung zeigte Gewinne);
- dass Logikunterricht allgemein besser argumentieren lässt;
- dass die Fallmethode in Ökonomie oder Management anderen Methoden überlegen ist;
- dass virtuelle Patienten, Vignetten oder Tutor-Erklärungen klinische Kompetenz, Patientensicherheit oder Berufsreife belegen; das Produkt zertifiziert nichts;
- dass Kalibrierungsrückmeldung die Kalibrierung verbessert;
- dass LLM-Bewertung offener juristischer, philosophischer oder diagnostischer Antworten verlässlich genug für Kompetenzbelege ist;
- dass irgendeine R3-Policy implementiert, getestet oder lernwirksam ist; dass dieser Bericht unabhängig geprüft, „validiert“ oder fachlich abgenommen wurde;
- dass die zitierten Schätzwerte auf deutsche Studierende, deutsches Recht oder aktuelle Modellversionen übertragbar sind.

## 12. Fragen an unabhängige Reviewer

1. **Recht:** Gibt es empirische Studien (auch graue Literatur, Zeitschrift für Didaktik der Rechtswissenschaft, Dissertationen) zum Erlernen des Gutachtenstils oder zu Probeklausuren im deutschen Jurastudium, die R3-S07/S08 übersehen haben?
2. **Recht:** Ist die Stichtag- und Fassungsregel (R3-POL-01) für Lernende praktikabel? Welche frei zugängliche Quelle liefert frühere Normfassungen verlässlich?
3. **Recht:** Lässt sich die Studie von Schwarcz & Farganis (SSRN 2772393) beschaffen, und stützt oder widerspricht sie R3-POL-02/11?
4. **Philosophie:** Wie bewertet die Übersicht `nesbit2025argumentmapping` im Volltext die Kausalevidenz? Ändert das die Stufe von R3-POL-05?
5. **Management:** Gibt es kontrollierte Studien zur Business-Fallmethode, die über Zufriedenheit hinausgehen?
6. **Klinik:** Sind die Reflexionsbefunde unabhängig repliziert? Die R3-Suche fand nur Arbeiten aus dem Umfeld der Originalautoren.
7. **Klinik:** Reichen die Formulierungen in R3-POL-10 aus, oder braucht es eine technische Sperre (z. B. Klassifikation „reale Person“)?
8. **Bewertung:** Wie oft weicht eine juristisch vertretbare Minderheitsmeinung von der Rubrik ab, und wie oft wird sie dabei von Mensch und Modell unterschiedlich bewertet? Lässt sich das an einer kleinen, synthetischen Antwortsammlung prüfen?
9. **Methode:** Sind die Zugangsstufen korrekt, insbesondere die drei Preprint-Volltexte (Dahl, Magesh, GradeLegal) gegenüber der Version of Record?
10. **Querschnitt:** Ist die Trennung von `rule_based_contextual` und `open_synthesis` für Recht und Philosophie tragfähig, oder sollte die R6-Ontologie eine eigene Operation „Argumentbewertung“ führen?

## 13. Reproduktion

Ohne Installation, Engine-Lauf oder bezahlten Modellaufruf, im Research-Worktree:

```sh
cd tests && python3 -m unittest test_r3_learning_policies test_r1_learning_policies
python3 - <<'PY'
import json, collections
d = json.load(open('docs/research/workstreams/r3/r3_evidence.json'))
print(len(d['entries']), 'entries', len(d['search_log']), 'searches')
print(collections.Counter(e['access']['level'] for e in d['entries']))
print(collections.Counter(e['domain'] for e in d['entries']))
PY
```

(Den zweiten Block aus dem Repository-Wurzelverzeichnis starten.) Die Suchen sind über `search_log` nachvollziehbar: Werkzeug, exakte Query, Datum, Trefferzahl, Ein- und Ausschluss. Web-Suchindizes sind dynamisch; Rankings sind nicht stabil. DOIs lassen sich über `https://api.crossref.org/works/{doi}` prüfen, Abstracts über `https://api.openalex.org/works/doi:{doi}`, PMC-Volltexte über die Europe-PMC-REST-API. Heruntergeladene Volltexte liegen nicht im Repository (Urheberrecht). Veröffentlicht sind nur Paraphrasen, Zahlen mit Fundstelle und Locator.
