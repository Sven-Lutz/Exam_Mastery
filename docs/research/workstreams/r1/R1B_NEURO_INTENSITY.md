# R1B — Neurowissenschaft, Physiologie, Motivation und nachhaltig hohe Lernintensität

Version 1, 27.11.2026. Workstream WP-R1, Teilpaket R1B. Autor: ein einzelner Agent (Claude, R1B). **Unabhängiger Review: pending.** Dieses Dokument ist eine gezielte, quellengebundene Scoping-Synthese, kein vollständiger systematischer Review und keine Freigabe irgendeiner Produktfunktion. Es behauptet keine Wirksamkeit von Exam Mastery.

Begleitdatei: [`r1b_evidence.json`](r1b_evidence.json) (Schema `r1-evidence/1`, 42 Einträge). Abgrenzung: Retrieval, Spacing, Interleaving, Cognitive Load/Worked Examples, Productive Failure, Selbsterklärung, Item-Feedback, metakognitive Kalibrierung und Transfer gehören zu R1A und werden hier nur dort berührt, wo sie mit Stress oder Aufmerksamkeit interagieren (z. B. `smith2016retrievalstress`, `szpunar2013interpolated`).

**Medizinische und sicherheitsbezogene Grenze (verbindlich für alle Abschnitte):** Dieses Dokument gibt keine individuelle medizinische Beratung und begründet keine. Es enthält keine Empfehlungen zu Substanzen, Nootropika, Koffein oder deren Dosierung; diese Themen wurden bewusst nicht recherchiert. Wo Symptome von Schlafstörungen, Burnout, Angst- oder depressiven Zuständen relevant werden, darf das Produkt ausschließlich allgemeine Information geben und auf professionelle Hilfe verweisen (Hochschul-Beratung, Ärztin/Arzt, Notdienste). Es darf weder diagnostizieren noch Schweregrade bewerten noch Behandlung (z. B. CBT-I) ersetzen.

Trennung der Ebenen, die in jedem Abschnitt eingehalten wird: **(M)** neuronaler Mechanismus/Korrelat → **(V)** behaviorale Lernevidenz → **(E)** praktische Empfehlung → **(P)** was eine Software tun darf. Ein Befund auf Ebene M begründet nie allein eine Produktregel.

---

## 1. Forschungsfragen, Suchprotokoll, Screening

### 1.1 Forschungsfragen

| Nr. | Frage | Zielpopulation |
|---|---|---|
| F1 | Wie stark beeinträchtigen Schlafentzug und Schlafrestriktion vor bzw. nach dem Lernen das Behalten; was gleicht Erholungsschlaf aus; was ist reine Laborevidenz (TMR, Stimulation)? | Studierende, junge Erwachsene |
| F2 | Gibt es einen belastbaren „Willenskraft-Akku“ (Ego Depletion)? Welche Modelle erklären Ermüdung/Anstrengung stattdessen? Was leisten (Mikro-)Pausen und Pomodoro-artige Pausenpläne für Wohlbefinden, Leistung und **Lernen**? | Studierende im Selbststudium |
| F3 | Was hilft gegen Mind-Wandering bei passivem Input; wie robust sind Smartphone-/Multitasking-Effekte? | Studierende |
| F4 | Welche Motivationsinterventionen (SDT, Utility Value, Growth Mindset) haben welche Effekte bei welcher Qualität? | Schule bis Hochschule |
| F5 | Wie wirkt akuter Stress phasenabhängig auf das Gedächtnis; was ist über Prüfungsangst-Interventionen (expressives Schreiben, Reappraisal) belastbar? | Studierende |
| F6 | Verbessert Sport kurz- oder langfristig Kognition/Gedächtnis gesunder junger Erwachsener nach Bias-Korrektur? | gesunde Erwachsene |
| F7 | Was folgt (und was nicht) aus Deliberate-Practice-Forschung für tägliche Lernstunden; was ist der Status der „10.000 Stunden“ und der „4 Stunden pro Tag“? | Expertise-Lernende, Studierende |
| F8 | Was ist über Lernzeit vs. Lernqualität, Burnout, Erholung/Detachment und lange Arbeitszeiten bekannt; was davon ist auf Studierende übertragbar? | Studierende; Beschäftigte (indirekt) |
| F9 | Welche „gehirnbasierten“ Aussagen sind Neuromythen oder unbegründete Brückenschlüsse und dürfen nicht ins Produkt? | Produktsprache |

### 1.2 Werkzeuge, Datum, Charakter der Suche

Alle Suchen am **2026-11-27**. Charakter: **seed- und known-item-getriebene gezielte Suche** (Charter-Seeds, im Auftrag genannte Schlüsselarbeiten, gezielte Suche nach Replikationen und Gegenbefunden). Keine lizenzierte Datenbank (PsycINFO, Scopus, WoS), keine vollständige Trefferdurchsicht, keine Doppelscreening-Prozedur. Trefferzahlen von Websuche sind nicht stabil und werden nicht als Vollständigkeitsmaß verwendet.

Werkzeuge:
- **PubMed E-utilities** (`esearch`, `esummary`, `elink`, `efetch rettype=abstract`, `efetch db=pmc` für Volltext-XML); Europe PMC REST (`fullTextXML`) als zweiter Volltextweg.
- **Allgemeine Websuche** (Claude-Werkzeug `WebSearch`, US-Index) und **WebFetch** für einzelne Seiten.
- **Semantic Scholar Graph API** (`/paper/batch`) für Metadaten/Abstracts nicht-PubMed-Artikel.
- Lokale Textextraktion (`pdftotext`) zweier öffentlich gehosteter PDFs **nur im Scratch-Verzeichnis**; keine Datei wurde ins Repository kopiert.

Aufwand: 33 Seiten-/Volltextabrufe inklusive Fehlschlägen (Budget ≤ 45), 8 Websuchen, 42 PubMed-`esearch`-Abfragen plus 3 `esummary`-, 1 `elink`- und 1 fehlgeschlagener `idconv`-Metadatenaufruf sowie 1 Semantic-Scholar-Batchabfrage.

### 1.3 Exakte Queries

**PubMed `esearch` (Feld `term`, db=pubmed):**

| ID | Exakte Query | Treffer | Entscheidung |
|---|---|---|---|
| P01 | `10.1152/physrev.00054.2024[doi]` | 1 | Seed `lutz2026sleep`; Abstract (Verlagsseite HTTP 403). |
| P02 | `Newbury[au] AND sleep deprivation memory meta-analytic[ti]` | 1 | `newbury2021sleepdeprivation`; Volltext (PMC). |
| P03 | `Cousins[au] AND nap cramming` | 1 | `cousins2019nap`; Volltext. |
| P04 | `Okano[au] AND sleep academic performance college` | 1 | `okano2019sleep`; Volltext. |
| P05 | `targeted memory reactivation meta-analysis[ti] AND Hu[au]` | 1 | `hu2020tmr`; Abstract genügt für „nur Labor“. |
| P06 | `Shields[au] AND stress memory meta-analysis 2017` | 1 | `shields2017stress`; Volltext. |
| P07 | `Smith[au] AND retrieval practice protects memory against acute stress` | 1 | `smith2016retrievalstress`; Abstract (nicht in PMC). |
| P08 | `Ciria[au] AND umbrella review physical exercise cognition` | 2 | Artikel + **Author Correction 2026** (Inhalt nicht zugänglich, siehe Lücken). |
| P09 | `Hagger[au] AND multilab preregistered replication ego-depletion` | 1 | `hagger2016egodepletion`. |
| P10 | `Vohs[au] AND multisite preregistered paradigmatic test ego-depletion` | 1 | `vohs2021egodepletion`; PMC-XML ohne Body → Abstract. |
| P11 | `Szpunar[au] AND interpolated memory tests mind wandering` | 2 | `szpunar2013interpolated`; Jing et al. 2016 ausgeschlossen (Budget, R1A-Nähe). PMC ohne Body → Abstract. |
| P12 | `Albulescu[au] AND micro-breaks` | 2 | Meta-Analyse 2022 eingeschlossen (Volltext); Tagebuchstudie 2026 ausgeschlossen (Beschäftigte, Einzelstudie). |
| P13 | `Biwer[au] AND Pomodoro` | 1 | `biwer2023pomodoro`; nicht in PMC → Abstract. |
| P14 | `Sisk[au] AND mind-sets academic achievement meta-analyses` | 1 | `sisk2018mindset`. |
| P15 | `Yeager[au] AND national experiment growth mindset 2019` | 2 | Nature-RCT eingeschlossen (Volltext); Dweck & Yeager 2019 (Perspektive) ausgeschlossen. |
| P16 | `Macnamara[au] AND Burgoyne[au] AND growth mindset` | 3 | Psych Bull 2023 eingeschlossen; Burgoyne 2020 ausgeschlossen (redundant). |
| P17 | `Burnette[au] AND growth mind-set interventions systematic review meta-analysis 2023` | **0** | Fehlgeschlagen → über Semantic Scholar (DOI) nachgeholt. |
| P18 | `Macnamara[au] AND deliberate practice meta-analysis 2014` | 2 | Meta-Analyse 2014 eingeschlossen; Reply 2016 ausgeschlossen. |
| P19 | `Macnamara[au] AND Maitra[au]` | 1 | `macnamara2019violin`; Volltext. |
| P20 | `Dekker[au] AND neuromyths teachers` | 1 | `dekker2012neuromyths`; Volltext. |
| P21 | `Kurzban[au] AND opportunity cost model subjective effort` | 1 | Theorie, Abstract. |
| P22 | `Shenhav[au] AND rational mechanistic account mental effort` | 1 | Theorie, Abstract. |
| P23 | `Wiradhany[au] AND media multitaskers replication meta-analysis` | 2 | Artikel + Korrekturnotiz. |
| P24 | `Roig[au] AND acute exercise memory meta-analysis` | 3 | `roig2013exercise`; zwei Off-Topic-Treffer (Schlaganfall, Parkinson) ausgeschlossen. |
| P25 | `Ramirez[au] AND Beilock[au] AND writing about testing worries` | 2 | Science 2011 eingeschlossen; Park et al. 2014 (Mathe-Angst) ausgeschlossen (Budget). |
| P26 | `Howard JL[au] AND self-determination theory student motivation meta-analysis` | 3 | PPS 2021 eingeschlossen; Bureau 2022, Howard 2020 ausgeschlossen (redundant). |
| P27 | `Bowers JS[au] AND educational neuroscience principled problems` | 2 | Psych Rev 2016 eingeschlossen; Bowers' Reply ausgeschlossen; Kommentare nur als Liste erfasst. |
| P28 | `Hulleman[au] AND promoting interest performance high school science` | 1 | Eingeschlossen. |
| P29 | `Hartanto[au] AND smartphone presence meta-analysis` | **0** | Fehlgeschlagen; die in der Websuche genannte Hartanto-Metaanalyse wurde **nicht** verifiziert und wird nicht zitiert. |
| P30 | `Böttger[au] AND brain drain meta-analysis` | 1 | Eingeschlossen; Volltext teilweise. |
| P31 | `Madigan DJ[au] AND Curran T[au] AND burnout academic achievement` | **0** | Nicht in PubMed → Autorenmanuskript (Websuche W6). |
| P32 | `Wendsche[au] AND detachment meta-analysis` | 3 | 2017-Metaanalyse eingeschlossen; Karabinski 2021 (Interventionen, Beschäftigte) Abstract gelesen, nicht aufgenommen; Zeigarnik-Metaanalyse 2026 nicht gescreent (Lücke). |
| P33 | `Camerer[au] AND replicability social science experiments Nature Science 2010 2015` | 1 | Eingeschlossen (Abstract). |
| P34 | `stress reappraisal intervention meta-analysis performance` | 5 | Bosshard & Gomez 2024 eingeschlossen; drei Off-Topic-Treffer (Pflege, Caregiver) ausgeschlossen. |
| P35 | `Thacher PV[au] AND all-nighters` | **0** | Fehlgeschlagen; keine All-nighter-Korrelationsstudie eingeschlossen (Lücke). |
| P36 | `Pega F[au] AND long working hours ischemic heart disease stroke WHO ILO` | 1 | Eingeschlossen als indirekter Kontext. |
| P37 | `test anxiety interventions meta-analysis university students randomized` | 61 | **Nicht gescreent** (Budget) → priorisierte Lücke G5. |
| P38 | `chronotype[ti] AND academic[ti] AND meta-analy*[ti]` | **0** | Fehlgeschlagen. |
| P39 | `chronotype AND (academic achievement OR academic performance) AND meta-analysis` | 1 | Off-Topic (Partnerkorrelationen) ausgeschlossen → Lücke G4. |
| P40 | `(sleep[ti]) AND (intervention*[ti] OR education[ti]) AND (university OR college) AND students AND (meta-analysis[pt] OR systematic review[pt])` | 21 | Top 6 nach Relevanz gescreent: Lu 2025 und Baron 2021 eingeschlossen; Friedrich & Schlarb 2018 Abstract gelesen, nicht aufgenommen (durch Lu 2025 überholt); JBI 2016, Cochrane (Kinder im Krankenhaus), Sleep Med 2022 ausgeschlossen. |
| P41 | `Wolf OT[au] AND Commentary Retrieval practice protects memory against acute stress` | 1 | Kommentar eingeschlossen (Volltext). |
| P42 | `all-nighter OR "all-nighters" AND students AND (grade OR GPA)` | **0** | Fehlgeschlagen (Lücke G4). |

**Websuche (`WebSearch`, Modus standard):**

| ID | Exakte Query | Ergebnis / Entscheidung |
|---|---|---|
| W1 | `Social Sciences Replication Project Camerer 2018 Ramirez Beilock 2011 writing about testing worries replication result` | Kein Einzelstudienergebnis; Folgestudien nur als Hinweise. |
| W2 | `replication "retrieval practice" "acute stress" Smith Floerke Thomas 2016 failed OR replicate OR preregistered` | Keine unabhängige präregistrierte Replikation gefunden; Kommentar Wolf & Kluge 2017 identifiziert. |
| W3 | `"brain drain" smartphone mere presence meta-analysis OR replication Ward 2017 cognitive capacity` | Ruiz Pardo & Minda 2022 und Böttger et al. 2023 identifiziert; weitere Meta-Analysen (u. a. ein Preprint) nur über Suchzusammenfassung bekannt → nicht verwendet. |
| W4 | `"Ramirez" "Beilock" SSRP replication report osf "Evaluating the replicability of social science experiments in Nature and Science"` | Fehlgeschlagen (keine relevanten Treffer). |
| W5 | `Plant Ericsson Hill Asberg 2005 "Why study time does not predict grade point average across college students" Contemporary Educational Psychology abstract` | Bibliografie bestätigt; Abstract nicht erreichbar (ScienceDirect 403, Semantic Scholar elidiert). |
| W6 | `Madigan Curran 2021 "Does burnout affect academic achievement? A meta-analysis" Educational Psychology Review` | Autorenmanuskript (York St John) → Volltext per `pdftotext` im Scratch gelesen. |
| W7 | `Ericsson Krampe Tesch-Römer 1993 "deliberate practice" pdf "4 hr" OR "four hours" sleep nap violinists effort constraint` | Kein direkter Volltext; öffentlich gehostete PDF-Kopie anschließend direkt abgerufen. |
| W8 | `"Ramirez and Beilock" 2011 expressive writing exam replication "did not replicate" OR "failed to replicate" OR "Social Sciences Replication Project"` | FORRT-Replikationsatlas-Eintrag gefunden (Ergebnis „failed“, Verweis auf Camerer 2018 Supplementary Table 5). |

**Semantic Scholar `paper/batch`** mit DOIs `10.1016/j.cedpsych.2004.06.001`, `10.1007/s10648-020-09533-1`, `10.1037/0033-295X.100.3.363`, `10.1111/ecoj.12166`, `10.3102/0034654315617832`, `10.1037/bul0000368`: Abstracts nur für Pencavel 2015 und Burnette et al. erhalten; übrige vom Verlag elidiert. Lazowski & Hulleman 2016 (Motivationsinterventionen, RER) daher **nicht** aufgenommen (Lücke).

### 1.4 Gescheiterte Abrufe (vollständig)

| Ziel | Ergebnis | Folge |
|---|---|---|
| `pubmed.ncbi.nlm.nih.gov/39427809/` (WebFetch) | Cookie-Sperre | Umstieg auf E-utilities. |
| `doi.org/10.1152/physrev.00054.2024` → `journals.physiology.org` | Redirect, dann HTTP 403 | `lutz2026sleep` nur Abstract. |
| Europe PMC `fullTextXML` für PMC8893218 (Newbury) | HTTP 500 | NCBI `efetch db=pmc` erfolgreich. |
| PMC3631699 (Szpunar), PMC12422598 (Vohs) | XML ohne Artikeltext (NCBI und Europe PMC) | Abstract-Ebene. |
| `socialsciencesreplicationproject.com` | DNS-Fehler | Sekundärquelle FORRT-Atlas. |
| `lirias.kuleuven.be/316700` | Redirect auf Katalogsuche | Nicht verwendet. |
| ScienceDirect-Abstractseite Plant 2005 | HTTP 403 | Nur Metadaten. |
| `nature.com` Author Correction Ciria 2026 | Authentifizierungs-Redirect | Inhalt der Korrektur unbekannt. |
| WebFetch Madigan-PDF | Binärinhalt nicht lesbar | Lokale Extraktion mit `pdftotext` (Scratch). |

### 1.5 Ein- und Ausschlusslogik

Eingeschlossen bevorzugt: Meta-Analysen mit Bias-Sensitivität, multizentrische/präregistrierte Replikationen, RCTs mit objektiven Outcomes, direkt relevante Kohorten (Studierende). Eingeschlossen trotz Indirektheit, wenn sie eine Produktbehauptung **begrenzen** (Beschäftigte, Historie, Burden-of-Disease). Ausgeschlossen: populärwissenschaftliche Sekundärdarstellungen als Beleg, Blogs, Suchmaschinen-Zusammenfassungen ohne Primärtext, Off-Topic-Treffer. „Study-maxing“-Inhalte (Videos, Foren) wurden **nicht** gesammelt: Sie sind informelle Anekdoten mit Selektions- und Survivorship-Bias und würden ohnehin nicht als Evidenz gezählt (siehe §8).

Wiederverwendung der KB: Keine der R1B-Quellen existierte in `exam_mastery/knowledge/sources.json`. Berührte KB-Claims: `ps.1` (Dehaene, „Konsolidierung“ und „Aufmerksamkeit“ als Säulen; `metadata_only`) wird durch `lutz2026sleep` und `bowers2016educationalneuro` **qualifiziert**, nicht bestätigt; `pashler2008` (Lernstile) ist mit `dekker2012neuromyths` konsistent, wurde aber nicht neu auditiert.

### 1.6 Zugangsebenen

| Ebene | Quellen |
|---|---|
| `fulltext_claim_review` (11) | newbury2021sleepdeprivation, cousins2019nap, okano2019sleep, shields2017stress, albulescu2022microbreaks, macnamara2019violin, dekker2012neuromyths, yeager2019mindset, madigan2021burnout (Autorenmanuskript), ericsson1993deliberate (öffentliche PDF-Kopie), wolf2017commentary |
| `fulltext_partial` (2) | bosshard2024reappraisal, bottger2023braindrain |
| `abstract` (28) | alle übrigen außer plant2005studytime |
| `metadata` (1) | plant2005studytime |

---

## 2. Evidenztabelle

Abkürzungen: obj = objektives Outcome; SR = Selbstbericht; FT = Volltext; Abs = Abstract. Schätzwerte exakt wie berichtet; Metriken nicht vermischen. Vollständige Felder in `r1b_evidence.json`.

### 2.1 Schlaf

| Quelle | Design / Population | Exposition vs. Vergleich | Outcome | Schätzung (wie berichtet) | Zugang | Bias / Anwendbarkeit | Inferenz |
|---|---|---|---|---|---|---|---|
| newbury2021sleepdeprivation | 2 Meta-Analysen; MA1 45 Reports, 130 ES, N = 1.616; MA2 31 Reports, 55 ES, N = 927; gesunde, überwiegend junge Erwachsene | ≥ 1 Nacht totaler Schlafentzug nach bzw. vor dem Lernen vs. Schlaf | obj Gedächtnistests; sofort vs. nach Erholungsschlaf | Nach Lernen g = 0,277 [0,177; 0,377], Trim-and-Fill 0,166 [0,086; 0,247]; mit Erholungsschlaf g = 0,176, ohne g = 0,410; prozedural 0,449 vs. deklarativ 0,218. Vor Lernen g = 0,621 [0,473; 0,769], adjustiert 0,463 [0,326; 0,601] | FT (Results MA1/MA2, Discussion) | Publikationsbias (Egger signifikant), mittlere Power der Primärstudien in MA1 13,98 %; Trim-and-Fill für Mehrebenenmodelle nur vorläufig; Laborlisten statt Prüfungsstoff | synthesis_mixed |
| crowley2024sleeprestriction | Meta-Analyse; 39 Reports, 125 ES, N = 1.234 | Restriktion 3–6,5 h vs. 7–11 h | obj Gedächtnis | g = 0,29 [0,13; 0,44]; kein Hinweis auf Publikationsbias; vs. Totalentzug insgesamt kein signifikanter Unterschied; post-encoding Totalentzug > Restriktion | Abs | Querschnitt zweier Meta-Analysen ist kein randomisierter Vergleich | synthesis_mixed |
| cousins2019nap | Experiment, 84 Studierende (NUS), wake 27 / nap 27 / cram 30 | 60 min Nap vs. Film vs. zusätzliches Wiederholen | obj 2AFC-Fakten, „certain“-Antworten; 30 min und 1 Woche | Nap vs. Wach: d = 0,95 (30 min), 0,56 (1 Woche); Cram vs. Wach: 0,60 bzw. 0,27 (n. s.); **Nap vs. Cram: 0,46 (p = 0,084) bzw. 0,29 (p = 0,282, n. s.)** | FT (Methods, Results) | Abstract überzeichnet: kein signifikanter Nap-über-Cram-Vorteil; nicht schlafdeprivierte Stichprobe; Einzelstudie | experimental_causal_within_scope |
| okano2019sleep | Prospektive Kohorte, N = 88 (MIT, Chemie-Einführung), Fitbit | Schlafdauer, -qualität, -regelmäßigkeit | obj Quiz-/Klausurnoten | r = 0,38 (Dauer), 0,44 (Fitbit-Qualität), −0,36 (Unregelmäßigkeit); 24,44 % Varianz (Stepwise); **Nacht vor Klausur: alle rs < 0,20, n. s.** | FT | Korrelativ, Freiwillige, Fitbit-Qualitätsscore laut Autoren nicht validiert; Overfitting-Risiko | correlational |
| hu2020tmr | Meta-Analyse, 91 Experimente, N = 2.004 | Cue-Reaktivierung im Schlaf vs. ungecuet | obj Labor | g = 0,29 [0,21; 0,38]; wirksam in NREM2/SWS, nicht in REM/Wach | Abs | Erfordert schlafstadiengenaue Cue-Gabe; keine Evidenz für unbeaufsichtigte App-Nutzung | synthesis_mixed |
| lutz2026sleep | Narrativer Review (Physiol Rev, epub 2025) | Mechanismen der Konsolidierung | gemischt | — | Abs | Aktive Systemkonsolidierung als Deutungsrahmen; Abstract benennt offene Kontroversen (Transformation, REM-Rolle, Schlaf vs. Wach) | mechanistic |
| baron2021sleepextension | Meta-Analyse, 42 Studien (10 mit Studierenden) | Verhaltensbasierte Schlafverlängerung | Schlafdauer | SMD 0,80 [0,28; 1,31] (I² = 99,2 %) zweiarmig; direkte Zeitplanvorgaben > indirekte Edukation | Abs | Extreme Heterogenität; kein Lernoutcome | synthesis_mixed |
| lu2025digitalsleep | Meta-Analyse, 13 RCTs, N = 5.251, 18–25 J. | Digitale CBT-I, Achtsamkeit, Schlafedukation | meist SR Schlafskalen | Schlafqualität g = −1,25 (I² = 97 %); Insomnieschwere g = −4,08; Schlafhygiene g = −0,19; Vorzeichen-Inkonsistenz bei „sleep knowledge“ im Abstract | Abs | GRADE moderat bis sehr niedrig; implausible Effektgrößen; wirksame Komponenten sind klinisch | synthesis_mixed |

### 2.2 Stress und Prüfungsangst

| Quelle | Design / Population | Exposition vs. Vergleich | Outcome | Schätzung | Zugang | Bias / Anwendbarkeit | Inferenz |
|---|---|---|---|---|---|---|---|
| shields2017stress | Meta-Analyse, 113 Studien, N = 6.216 | Akuter Laborstressor in verschiedenen Gedächtnisphasen | obj episodisches Gedächtnis | Enkodierung gesamt g+ = −0,109 [−0,282; 0,065] (n. s.; zeitabhängig, Beeinträchtigung ab ca. 22 min Stressor-Enkodier-Abstand); post-encoding +0,206 [0,013; 0,399]; Abruf −0,215 [−0,346; −0,085] (neutral −0,136) | FT (Results Encoding/Post-encoding/Retrieval, Bias) | Laborstressoren (TSST, Cold Pressor), Wortlisten; Moderatoren mit kleinen df; Cortisolanstieg kein Moderator | synthesis_mixed |
| smith2016retrievalstress | 2×2-Experiment | Retrieval Practice vs. Restudy; Stress vs. kein Stress 24 h später | obj Endtest | Restudy-Gruppe zeigte Stresseinbuße, Retrieval-Gruppe nicht | Abs | Einzelstudie; „immune“ ist Nicht-Signifikanz, kein Äquivalenznachweis | experimental_causal_within_scope |
| wolf2017commentary | Kommentar | — | — | Gedächtnisstärke-Konfundierung (Retrieval-Gruppe insgesamt besser), keine Cortisolmessung | FT | Qualifiziert smith2016 | theoretical |
| ramirez2011writing | 2 Labor- + 2 Feldexperimente | ~10 min expressives Schreiben über Sorgen vor Prüfung vs. Kontrolle | obj Prüfungsnoten | „signifikant verbessert, v. a. bei Ängstlichen“ | Abs | kleine Stichproben; Erratum 2014 (Inhalt ungeprüft) | experimental_causal_within_scope |
| camerer2018ssrp | 21 präregistrierte, hochgepowerte Replikationen | — | — | 13/21 (62 %) repliziert, Replikationseffekte ≈ 50 % der Originale; **Ramirez & Beilock 2011 laut FORRT-Atlas „failed“** (Supplementary Table 5, nicht selbst eingesehen) | Abs + Sekundäratlas | Einzelstudienkodierung sekundär | experimental_causal_within_scope |
| bosshard2024reappraisal | Meta-Analyse von RCTs, 44 ES, N = 5.638, mittleres Alter 22,6 | Stress-Arousal-Reappraisal / Stress-is-enhancing-Mindset vs. Kontrollen | obj Aufgabenleistung (inkl. Prüfungen) | d = 0,23; Trim-and-Fill 0,14 [0,04; 0,24]; kognitiv-schriftlich d = 0,20; öffentliche Leistung 0,34; SIE allein 0,18 (n. s.) | FT teilweise | Egger signifikant; p-Curve ohne klaren Evidenzwert; Prüfungsteilmenge nicht separat geprüft | synthesis_mixed |

### 2.3 Anstrengung, Ermüdung, Pausen, Aufmerksamkeit

| Quelle | Design / Population | Exposition vs. Vergleich | Outcome | Schätzung | Zugang | Bias / Anwendbarkeit | Inferenz |
|---|---|---|---|---|---|---|---|
| hagger2016egodepletion | RRR, 23 Labore, N = 2.141 | Sequenzielle Aufgabe (depletierend vs. nicht) | obj Folgeaufgabe | d = 0,04 [−0,07; 0,15] | Abs | Ein Protokoll; kurze Laboraufgaben | experimental_causal_within_scope |
| vohs2021egodepletion | Präregistriert, 36 Labore, N = 3.531 | Zwei Depletionsverfahren | obj Selbstkontrollmaß | konfirmatorisch d = 0,06 (n. s.); Daten ≈ 4× wahrscheinlicher unter H0; explorativ d = 0,08 | Abs | Konvergiert mit Hagger; explorativ größer bei hoher berichteter Müdigkeit | experimental_causal_within_scope |
| kurzban2013opportunitycost / shenhav2017effort | Theorie | Opportunitätskosten-/Expected-Value-of-Control-Modelle | — | — | Abs | Keine Sitzungsparameter ableitbar | theoretical |
| albulescu2022microbreaks | Meta-Analyse, 22 Stichproben, N = 2.335 (11 Studierenden-, 10 Beschäftigtenstichproben) | Pausen ≤ 10 min (8 s–10 min) vs. keine | SR Vitalität/Müdigkeit; Leistung gemischt; sofort | Vitalität d = 0,36; Müdigkeit d = 0,35; Leistung gesamt d = 0,16 (p = 0,116); kreativ 0,38, Routine 0,56, **kognitiv anspruchsvoll n. s.**; längere Pausen ↔ größerer Leistungseffekt (Meta-Regression) | FT | nur 4/22 Studien niedriges RoB; keine Behaltensmaße; Büro ≠ Studium (Autoren) | synthesis_mixed |
| biwer2023pomodoro | 3-armige Online-Intervention, 1 Tag, 87 NL-Studierende | 24/6-min- (n = 25) und 12/3-min-Takt (n = 27) vs. selbstregulierte Pausen (n = 35) | SR Stimmung, Effort, Aufgabenerledigung | Selbstregulierte: längere Sitzungen/Pausen, mehr Müdigkeit/Ablenkung, weniger Konzentration/Motivation; **kein Unterschied in investiertem Effort oder Aufgabenerledigung** | Abs | 1 Tag, Selbstbericht, Sitzungslänge konfundiert, Zuteilungsverfahren ungeprüft | experimental_causal_within_scope |
| szpunar2013interpolated | 2 Laborexperimente | Kurze Tests zwischen Videovorlesungssegmenten vs. ohne | SR Mind-Wandering-Proben, Notizen, obj Endtest | weniger Mind Wandering, mehr Notizen, besseres Lernen, weniger Angst | Abs | kurze Laborvorlesung, sofortiger Test | experimental_causal_within_scope |
| ruizpardo2022braindrain | Präregistrierte direkte Replikation von Ward 2017 Exp. 2 | Telefon auf Tisch vs. Tasche vs. außerhalb; an/aus | obj OSpan, Go/No-Go | **kein Unterschied** | Abs | Nur bloße Anwesenheit | experimental_causal_within_scope |
| bottger2023braindrain | Meta-Analyse, 22 Studien, 43 Effekte | Smartphone-Nutzung **und** Anwesenheit gepoolt | obj Kognition | g = −0,14 [−0,24; −0,03], I² = 61,84 % | FT teilweise | Bias nur per Funnel-Sichtprüfung; mischt Nutzung und Präsenz | synthesis_mixed |
| wiradhany2017mediamultitasking | 2 Replikationen (14 Tests) + Meta-Analyse (39 ES) | Habituelles Medien-Multitasking | obj Distraktorfilterung | 5/14 Tests signifikant, 2 Bayes-robust; Meta-Effekt nach Small-Study-Korrektur n. s. | Abs | Trait-Korrelation, nicht Task-Switching im Moment | correlational |

### 2.4 Motivation

| Quelle | Design / Population | Intervention vs. Vergleich | Outcome | Schätzung | Zugang | Bias / Anwendbarkeit | Inferenz |
|---|---|---|---|---|---|---|---|
| howard2021sdt | Meta-Analyse, 344 Stichproben, N = 223.209 | Motivationstypen (SDT) | gemischt, viel SR | intrinsisch ↔ Erfolg/Wohlbefinden; identifiziert ↔ Persistenz; introjiziert ↔ Persistenz **und** Ill-being; external ↔ keine Leistung, weniger Wohlbefinden | Abs | korrelativ, Common-Method-Varianz | correlational |
| hulleman2009utility | Randomisiertes Feldexperiment, Oberstufe | Utility-Value-Schreiben vs. Kontrolle | obj Noten, SR Interesse | Effekt nur bei niedriger Erfolgserwartung | Abs | Schule; College-Replikationen nicht abgerufen | experimental_causal_within_scope |
| sisk2018mindset | 2 Meta-Analysen (k = 273; k = 43) | Mindset bzw. Mindset-Intervention | Leistung | „insgesamt schwach“; ggf. Nutzen für niedrigen SES/Risikogruppen | Abs | Zahlen nicht extrahiert | synthesis_mixed |
| yeager2019mindset | Präregistriertes RCT, US-repräsentativ, n = 6.320 leistungsschwächere 9.-Klässler, 65 Schulen | < 1 h online Growth Mindset vs. Kontrolle | obj GPA | B = 0,10 Notenpunkte [0,04; 0,16], SMD 0,11; heterogen nach Schulnorm/-niveau | FT | Schule, nicht Hochschule; Autoren verbreiten Mindset-Forschung (COI-Erklärung) | experimental_causal_within_scope |
| macnamara2023mindset | Systematischer Review + 3 Meta-Analysen, 63 Studien, N = 97.672 | Mindset-Interventionen | Leistung | alle d̄ = 0,05 [0,02; 0,09] (n. s. nach Bias-Korrektur); höchste Qualität (6 Studien) d̄ = 0,02 [−0,06; 0,10] | Abs | Kritikerseite; Qualitätskodierung umstritten | synthesis_mixed |
| burnette2023mindset | Meta-Regression, 53 Stichproben | Mindset-Interventionen | Leistung, psychische Gesundheit | Zielgruppen + hohe Fidelity: Leistung d = 0,14 [0,06; 0,22], PI [−0,08; 0,35]; psych. Gesundheit d = 0,32 | Abs | Befürworterseite; konditionale Schätzung | synthesis_mixed |

### 2.5 Sport

| Quelle | Design | Exposition vs. Vergleich | Outcome | Schätzung | Zugang | Bias / Anwendbarkeit | Inferenz |
|---|---|---|---|---|---|---|---|
| ciria2023exercise | Umbrella-Review von 24 RCT-Meta-Analysen + Re-Meta-Analyse | Regelmäßiger Sport vs. Kontrollen | obj Kognition | d = 0,22 [0,16; 0,28] → 0,13 [0,07; 0,20] (aktive Kontrolle, Baseline) → **0,05 [−0,09; 0,14]** nach Publikationsbias-Korrektur | Abs | **Author Correction 2026** nicht einsehbar; gemischte Altersgruppen | synthesis_mixed |
| roig2013exercise | Meta-Analyse, 29 akute / 21 Langzeitstudien | Ausdauerbelastung | obj Gedächtnis | akut auf Langzeitgedächtnis SMD 0,52 [0,28; 0,75]; Langzeittraining auf Langzeitgedächtnis 0,07 [−0,13; 0,26] | Abs | 2013, keine moderne Bias-Analyse; kleine Studien | synthesis_mixed |

### 2.6 Expertise, Intensität, Erholung

| Quelle | Design | Exposition | Outcome | Schätzung | Zugang | Bias / Anwendbarkeit | Inferenz |
|---|---|---|---|---|---|---|---|
| ericsson1993deliberate | Theorie + 2 kleine Querschnittsstudien (je 10 Violinist:innen pro Gruppe; Pianist:innen) | Übung allein, Schlaf, Nickerchen | Gruppenzugehörigkeit, Tagebuch | Beste zwei Gruppen: 8,6 h Schlaf/Tag vs. 7,8 h (Lehrkräfte), Naps 2,8 vs. 0,9 h/Woche (S. 376); „around 4 hr“ deliberate practice täglich als **mögliche** allgemeine Grenze (S. 391), gestützt auf Pianist:innen, Interviews mit Schachmeistern (S. 390) und Anekdoten zu Schriftstellern (S. 371, 392) | FT | nicht verblindet, kleine N, Musik | correlational |
| macnamara2019violin | Präregistrierte doppelblinde Replikation, N = 39 (aus df) | Akkumulierte Übung allein / lehrergestaltet | Leistungsgruppe | η² = 0,26 [0,03; 0,44] bzw. 0,23 [0,02; 0,41] vs. 48 % im Original; geschätzte > geloggte Übungszeit | FT | Kernbefund nicht repliziert; kleine Expertenstichprobe | correlational |
| macnamara2014deliberate | Meta-Analyse | Akkumulierte deliberate practice | Leistung | erklärte Varianz: Spiele 26 %, Musik 21 %, Sport 18 %, **Bildung 4 %**, Berufe < 1 % | Abs | Erratum 2018 (Inhalt ungeprüft); Definitionsstreit | correlational |
| plant2005studytime | Korrelationsstudie, Studierende | Lernzeit | GPA | nur Titelaussage | Metadaten | **nicht gelesen** | correlational |
| madigan2021burnout | Meta-Analyse, 29 Studien, N = 109.396 | Studentisches Burnout | Leistung | rc+ = −0,24 [−0,31; −0,16]; Erschöpfung −0,15; Zynismus −0,24; reduzierte Wirksamkeit −0,39 | FT (Autorenmanuskript) | überwiegend Querschnitt (eigene Limitationen); nur Fail-safe-N als Biasprüfung; „leads to“ überzeichnet | correlational |
| wendsche2017detachment | Meta-Analyse, k = 91, N = 38.124 Beschäftigte | Psychologisches Abschalten | SR Wohlbefinden, Leistung | positiv mit Gesundheit/Wohlbefinden/Aufgabenleistung; **null** mit physiologischen Stressindikatoren; **negativ** mit Kreativität | Abs | Beschäftigte (indirekt) | correlational |
| pencavel2015hours | Historische Daten (Munitionsarbeiterinnen) | Wochenstunden | Output | proportional bis Schwelle, darüber abnehmender Grenzertrag | Abs | körperliche Arbeit, sehr indirekt | correlational |
| pega2021longhours | WHO/ILO-Burden-Modellierung | ≥ 55 h/Woche vs. 35–40 h | Herz-Kreislauf-Last | PAF Todesfälle 3,7 % (IHD), 6,9 % (Schlaganfall) | Abs | chronische Exposition bei Beschäftigten, sehr indirekt | synthesis_mixed |

### 2.7 Educational Neuroscience

| Quelle | Design | Befund | Zugang | Anwendbarkeit | Inferenz |
|---|---|---|---|---|---|
| dekker2012neuromyths | Survey, N = 242 Lehrkräfte (UK/NL) | Im Mittel 49 % der Neuromythen geglaubt; Lernstil-Meshing 93 % / 96 %; Hemisphärendominanz 91 % / 86 %; Koordinationsübungen integrieren Hemisphären 88 % / 82 %; mehr Hirnwissen ↔ mehr Mythenglaube (Table 1) | FT | Basisrate der Attraktivität von Hirnbehauptungen | descriptive |
| bowers2016educationalneuro | Konzeptuelle Kritik + Repliken | Für die Bewertung von Unterricht zählt das Verhalten; Hirnveränderung allein validiert keine Methode | Abs | Kern unstrittig für Produktvalidierung | theoretical |

---

## 3. Konkurrierende Modelle und widersprechende Befunde

### 3.1 Konkurrierende Modelle

| Feld | Modell A | Modell B (und ggf. C) | Was die Evidenz hier unterscheidet | Produktrelevanz |
|---|---|---|---|---|
| Schlaf und Gedächtnis | **Aktive Systemkonsolidierung** mit Replay und NREM-Oszillationen, begleitet von synaptischer Herunterregulierung (`lutz2026sleep`, Abstract) | **Ermüdung zum Testzeitpunkt** bzw. **Interferenzschutz** als Teil-Erklärung von Schlafentzugseffekten; `newbury2021sleepdeprivation` diskutiert beide Alternativen für den kleineren Effekt nach Erholungsschlaf (Discussion) | Restdefizit auch nach Erholungsschlaf (g = 0,176) spricht gegen reine Testmüdigkeit, schließt Interferenz aber nicht aus | Gering: Alle Modelle sagen „Schlafgelegenheit nach dem Lernen schützen“ voraus. Das Produkt braucht kein Mechanismusmodell, um so zu planen. |
| Anstrengung/Ermüdung | **Ressourcen-/Stärkemodell** („Willenskraft-Akku“) | **Opportunitätskosten-** und **Expected-Value-of-Control-Modelle**: gefühlte Anstrengung als Kosten-Nutzen-Signal (`kurzban2013opportunitycost`, `shenhav2017effort`) | Zwei große präregistrierte Replikationen finden keinen Depletionseffekt (`hagger2016egodepletion` d = 0,04; `vohs2021egodepletion` d = 0,06) | Hoch für Produktsprache: Pausen nicht als „Akku aufladen“ begründen; Ermüdungsmeldungen als Information über Wert/Kosten behandeln (Aufgabe wechseln, Ziel klären, beenden). |
| Expertise | **Deliberate Practice** erklärt individuelle Unterschiede weitgehend (`ericsson1993deliberate`) | **Multifaktorielles Modell**: Übung wichtig, aber begrenzter Varianzanteil (`macnamara2014deliberate`; Bildung 4 %), Kernbefund nicht repliziert (`macnamara2019violin`) | Replikation mit Verblindung findet η² 0,26 statt 48 % | Stunden sind kein Mastery-Maß; kein „10.000-Stunden“-Narrativ. |
| Growth Mindset | **Kontextabhängige, kleine, aber reale Effekte** in Zielgruppen (`yeager2019mindset`, `burnette2023mindset`) | **Effekte durch Design-/Berichtsmängel und Bias erklärt** (`macnamara2023mindset`) | Beide Seiten finden kleine Durchschnittswerte; Streit betrifft Qualität, Konditionierung und Interpretation | Keine Mindset-Intervention als Leistungsversprechen; neutrale, nicht beschämende Fehlerkommunikation bleibt unabhängig davon sinnvoll. |
| Stress | **Phasenspezifisches Modell**: vor Abruf schädlich, nach Enkodierung oft förderlich, Enkodierung zeitabhängig (`shields2017stress`) | **Bewertungsmodell**: Reappraisal verändert Wirkung von Erregung (`bosshard2024reappraisal`); **Gedächtnisstärke-Modell**: stärker gelernte Inhalte sind stressresistenter (`smith2016retrievalstress` vs. `wolf2017commentary`) | Reappraisal-Effekt nach Bias-Korrektur klein (d = 0,14); Retrieval-Schutz nicht von Gedächtnisstärke getrennt | Prüfungsnahes Üben bis zu stabiler Abrufleistung ist ohnehin R1A-Kern; Stressbotschaften nur als kleines, optionales Zusatzangebot. |
| Educational Neuroscience | Neurowissenschaft kann Unterricht verbessern | Für Unterrichtsbewertung zählt nur Verhalten (`bowers2016educationalneuro`); Repliken im selben Heft widersprechen teilweise (nicht gelesen) | Unentschieden auf Theorieebene | Für Exam Mastery unstrittig: Funktionen werden an verzögerter, unassistierter Leistung gemessen, nie an „Hirnwirkung“. |

### 3.2 Null-, negative und widersprechende Beobachtungen (≥ 3 gefordert, 12 dokumentiert)

1. **Ego Depletion repliziert nicht:** d = 0,04 [−0,07; 0,15] (23 Labore) und d = 0,06 (36 Labore, Bayes-Evidenz für H0) — `hagger2016egodepletion`, `vohs2021egodepletion` (Abstracts).
2. **Sport → Kognition nach Bias-Korrektur vernachlässigbar:** d = 0,05 [−0,09; 0,14] — `ciria2023exercise` (Abstract; Korrektur 2026 ungeprüft).
3. **Growth-Mindset-Interventionen in hochwertigsten Studien null:** d̄ = 0,02 [−0,06; 0,10] — `macnamara2023mindset`; Prognoseintervall der Befürworter-Analyse schließt 0 ein — `burnette2023mindset`.
4. **Schlaf in der Nacht vor der Klausur nicht mit dem Ergebnis assoziiert** (alle rs < 0,20), während Schlaf über Wochen/Monat assoziiert ist — `okano2019sleep`, Results „Night before assessments“.
5. **Nap vs. zusätzliches Wiederholen nach einer Woche nicht signifikant verschieden** (d = 0,29, p = 0,282); der Cramming-Vorteil gegenüber Wachpause verschwindet nach einer Woche (d = 0,27, n. s.) — `cousins2019nap`, Results.
6. **Mikropausen verbessern die Leistung bei kognitiv anspruchsvollen Aufgaben nicht signifikant**; Gesamtleistung d = 0,16, p = 0,116 — `albulescu2022microbreaks`.
7. **Pomodoro vs. selbstregulierte Pausen: kein Unterschied in investiertem Effort und Aufgabenerledigung** — `biwer2023pomodoro`.
8. **„Brain Drain“ durch bloße Smartphone-Präsenz nicht repliziert** — `ruizpardo2022braindrain`; die gegenteilige Meta-Analyse (`bottger2023braindrain`, g = −0,14) poolt Nutzung und Präsenz.
9. **Medien-Multitasking ↔ Ablenkbarkeit nach Small-Study-Korrektur n. s.** — `wiradhany2017mediamultitasking`.
10. **Expressives Schreiben vor Prüfungen: Replikation gescheitert** (sekundäre Kodierung, Camerer 2018 Suppl. Table 5) — `camerer2018ssrp`.
11. **Akuter Stress vor/während Enkodierung insgesamt n. s.**; Höhe des Cortisolanstiegs moderiert keinen Effekt — `shields2017stress`, Results Encoding/Retrieval.
12. **Deliberate-Practice-Kernbefund nicht repliziert**; geschätzte Übungszeiten überstiegen Tagebuchwerte — `macnamara2019violin`.

Zusätzliche Inkonsistenzen in Quellen selbst: `albulescu2022microbreaks` berichtet die Gesamtleistung im Abstract mit d = 0,16, im Publikationsbias-Abschnitt beobachtet mit 0,14 [−0,07; 0,36]; `lu2025digitalsleep` enthält eine Vorzeichen-/CI-Inkonsistenz im Abstract; `madigan2021burnout` formuliert kausal („leads to“), obwohl die eigene Limitationsdiskussion überwiegend Querschnittsdaten nennt.

### 3.3 Vier-Ebenen-Trennung je Thema

| Thema | (M) Mechanismus/Korrelat | (V) Behaviorale Evidenz | (E) Praktische Empfehlung | (P) Produkt darf … |
|---|---|---|---|---|
| Schlaf | Replay, Spindeln/Slow Oscillations; TMR wirkt in NREM im Labor | Totalentzug und Restriktion verschlechtern Gedächtnis (kleine bis mittlere g, biasbereinigt kleiner); Regelmäßigkeit korreliert mit Noten | Ausreichende, regelmäßige Schlafgelegenheit über die gesamte Lernphase, nicht nur vor der Prüfung | Schlaffenster des Nutzers respektieren, Pläne ohne Nachtarbeit bauen, keine All-nighter vorschlagen; **nicht** Schlaf messen/bewerten oder TMR anbieten |
| Ermüdung | Kontrollkosten-Modelle, mechanistisch ungeklärt | keine Depletion; Pausen verbessern SR-Vitalität, nicht sicher Leistung/Lernen | Pausen als Option, nicht als Leistungsbooster | konfigurierbare Pausen-Defaults, ehrliche Begründung (Wohlbefinden), keine „Akku“-Metapher |
| Aufmerksamkeit | — | Interpolierte Tests reduzieren Mind Wandering bei Videovorlesungen; Smartphone-Präsenz unklar | Passiven Input in Segmente mit Abruf gliedern; Ablenkungen reduzieren, wo selbst gewünscht | Abrufchecks in lange Inputs einbauen; optionaler Fokusmodus ohne „Brain-Drain“-Behauptung |
| Stress | Noradrenerg-glukokortikoide Interaktion (Kommentar) | Stress vor Abruf schadet klein; Reappraisal klein und biasanfällig | Prüfungsnahe Übung, realistische Erwartung an Anspannung | optionale kurze Reappraisal-Info, Verweis auf Beratung bei starker Angst |
| Sport | BDNF-„Priming“ (Roig, spekulativ) | chronisch: kein robuster Kognitionseffekt; akut: kleine Laborstudien | Bewegung aus Gesundheitsgründen ist ein eigenes Thema außerhalb dieser Frage | keine Leistungsversprechen; Bewegungspausen nur als Nutzerwahl |
| Expertise/Stunden | — | Übungsmenge erklärt begrenzte Varianz; „4 h“ ist Hypothese | Qualität und Prüfungsnähe vor Stundenmaximierung | keine Stundenziele als Erfolgsmaß, keine Stunden-Gamification |

---

## 4. Mechanismus → Lernerhandlung → Systemaffordanz → Observable → unabhängiges Outcome → Fehlermodus

„Observable“ = was das Produkt sehen kann (immer unvollständig, lokal, mit Einwilligung). „Unabhängiges Outcome“ = was nur außerhalb der Produktlogik den Lernerfolg belegen könnte. Keine Zeile ist ein Wirksamkeitsnachweis für Exam Mastery.

| Mechanismus (Ebene, Quelle) | Lernerhandlung | Systemaffordanz | Observable im Produkt | Unabhängiges Outcome | Fehlermodus |
|---|---|---|---|---|---|
| Schlafabhängige Konsolidierung (M; `lutz2026sleep`) + Schlafverlust schadet Behalten (V; `newbury2021sleepdeprivation`, `crowley2024sleeprestriction`) | Regelmäßige Schlafgelegenheit über Wochen; Lernen nicht in die Nacht verlagern | Nutzerdefiniertes Schlaf-/Off-Fenster; Planer platziert keine Einheiten darin; keine Erinnerungen darin | geplante vs. tatsächliche Sitzungszeitstempel relativ zum Fenster; Anzahl manueller Overrides | verzögerte (≥ 1 Woche), unassistierte Leistung auf zurückgehaltenen Items; extern bewertete Prüfung (optional vom Nutzer gemeldet) | Schuldgefühl bei Abweichung; Schichtarbeit/Eltern falsch behandelt; Über-Medikalisierung („Schlafprobleme“); Datensammlung über Schlaf |
| Schlafverlust vor Enkodierung (V; `newbury2021sleepdeprivation` MA2) | Neues, schwieriges Material nicht nach durchwachter Nacht einführen | Plan-Hinweis: nach vom Nutzer gemeldeter Kurznacht leichtere Wiederholung statt Neustoff anbieten | vom Nutzer gemeldete Kurznacht (opt-in), gewählte Option | Behalten des am Folgetag eingeführten Stoffs im verzögerten Test | Paternalismus; Fehlinformation bei falscher Selbstauskunft; Sorge/Angst durch Warnungen |
| Akuter Stress beeinträchtigt Abruf (V; `shields2017stress`); Stärke-Hypothese (`smith2016retrievalstress`, umstritten `wolf2017commentary`) | Prüfungsnah und bis zu stabilem Abruf üben; Anspannung als normal einordnen | Prüfungssimulation unter Zeitbedingungen (R1A-Komponente); optionale 1-Absatz-Reappraisal-Info | Simulationsergebnisse; Nutzung der Info-Karte | Prüfungsleistung, unabhängige verzögerte Tests | „Stressimmunität“ versprechen; Angststörung bagatellisieren statt verweisen |
| Kontrollkosten/Ermüdungssignal (Theorie; `kurzban2013opportunitycost`, `shenhav2017effort`); Pausen verbessern SR-Vitalität (V; `albulescu2022microbreaks`, `biwer2023pomodoro`) | Geplante kurze Pausen; Aufgabenwechsel oder Ende bei anhaltender Erschöpfung | Konfigurierbarer Block-/Pausen-Timer; „Stopp ist eine gültige Option“ | Pausenannahme, Abbrüche, optional 1–5-Müdigkeitsselbstbericht | Behalten (nicht nur Tagesproduktivität) in verzögerten Tests | Pausen werden als Lernbeschleuniger verkauft; Timer-Zwang stört Flow; „Willenskraft-Akku“-Sprache |
| Mind Wandering bei passivem Input (V; `szpunar2013interpolated`) | Video/Text in Segmenten konsumieren und zwischendurch abrufen | Eingebettete Kurzabrufe nach Segmenten (Schnittstelle R1A/R5) | Antworten auf Zwischenabrufe, Überspringraten | Endtest ohne Hilfe, verzögert | Zu häufige Unterbrechung; Abruf ohne Feedback auf falschem Niveau; Messung = Training (Testnähe) |
| Smartphone/Unterbrechungen (V; widersprüchlich: `ruizpardo2022braindrain`, `bottger2023braindrain`) | Benachrichtigungen während Sitzungen reduzieren, falls gewünscht | Optionaler Fokusmodus/OS-Integration; eigene Benachrichtigungen während Sitzungen stumm | Aktivierung des Fokusmodus | — (kein valides unabhängiges Outcome im Produkt) | Überwachung des Telefons; unbelegte „Brain-Drain“-Behauptung |
| Autonome Motivation korreliert mit Persistenz/Wohlbefinden; kontrollierende mit Ill-being (V-korr.; `howard2021sdt`) | Eigene Gründe und Relevanz formulieren; Ziele selbst setzen | Optionale Relevanzreflexion (Utility Value, `hulleman2009utility`); neutrale, nicht beschämende Sprache; keine Streak-Strafen | Nutzung, Abbrüche, Zielanpassungen | Persistenz bis Prüfung; Prüfungsleistung; validierte Fragebögen nur in genehmigter Studie | Manipulative Gamification; Reflexionsaufgaben als Zeitfresser; Scheinwirksamkeit |
| Überlastung/Burnout-Assoziation (V-korr.; `madigan2021burnout`); Erholung/Detachment (V-korr., indirekt; `wendsche2017detachment`) | Belastung an eigener Basis ausrichten; leichte Tage; Off-Zeiten | Lastvergleich mit eigener 7-Tage-Basis; Reflexionshinweis statt Verbot; Off-Fenster ohne Benachrichtigungen | geplante/erledigte Minuten, aufeinanderfolgende Tage ohne leichten Tag | Prüfungsleistung, Abbruchquote, Wohlbefinden in Studie | Stundenquote durch die Hintertür; Pathologisierung von Fleiß; Missbrauch als Leistungsüberwachung |
| Übungsmenge erklärt begrenzte Varianz (V-korr.; `macnamara2014deliberate`, `macnamara2019violin`) | Qualität vor Menge: prüfungsnahe, fehlerorientierte Übung | Anzeige verzögerter Abrufleistung statt Stundenbilanz | Abrufgenauigkeit nach Abstand, Itemabdeckung | Unabhängiger Transfertest | Stunden als Erfolgsmetrik; Selbstschätzungen überschätzen Lernzeit |

---

## 5. Policy-Kandidaten R1-POL-B01 bis R1-POL-B12

Lesehinweise: **Sicherheitslabel = interne Begründung, kein externer Leitlinien-Grad.** Alle Zahlen in Policies sind ausdrücklich **„provisorischer Produktparameter, keine empirische Konstante“** (abgekürzt: *PPP*). Jede Policy ist ein `design_hypothesis` im Sinne von `EVIDENCE_REGISTER_SCHEMA.md` und benötigt einen eigenen Lern-Evaluationsnachweis. Relationen: `supports`, `qualifies`, `contradicts`, `context_only`.

### R1-POL-B01 — Schlafschützende Planung über die gesamte Lernphase

- **Kontext:** Jeder automatisch erzeugte Lernplan (Tages-/Wochenplan, Prüfungsplan). Nutzer hat ein gewohntes Schlaf-/Off-Fenster angegeben oder nicht.
- **Empfehlung:** Der Planer legt keine Einheiten in das vom Nutzer angegebene Schlaffenster und schlägt nie eine durchgearbeitete Nacht vor. Fehlt eine Angabe, fragt er einmal nach; ohne Antwort nutzt er einen neutralen Default mit einer Schlafgelegenheit von 8 h (*PPP*; zur Einordnung: die Kontrollbedingungen in `crowley2024sleeprestriction` lagen bei 7–11 h, die Restriktionsbedingungen bei 3–6,5 h — das ist kein Schwellenwert für Einzelpersonen). Regelmäßigkeit wird über Wochen geschützt, nicht nur in der Prüfungswoche. Ein Nickerchen darf der Nutzer als Planbaustein wählen; das Produkt schlägt es nicht als Ersatz für Nachtschlaf vor.
- **Abstention/Fallback:** Bei Schichtarbeit, Betreuungspflichten oder abweichender Chronobiologie gilt ausschließlich das vom Nutzer angegebene (auch tagsüber liegende oder fragmentierte) Fenster; keine Bewertung. Meldet der Nutzer anhaltende Schlafprobleme: keine Schlafratschläge, nur allgemeiner Hinweis und Verweis (R1-POL-B12).
- **Evidenzkanten:** `newbury2021sleepdeprivation` (Results MA1/MA2, adjustierte g 0,166 bzw. 0,463; `supports`); `crowley2024sleeprestriction` (Abstract, g = 0,29; `supports`); `okano2019sleep` (Results „Sleep duration, quality, and consistency“; `supports`, korrelativ); `baron2021sleepextension` (Abstract: direkte Zeitplanvorgaben > Edukation; `supports` für Zeitplan als Hebel); `cousins2019nap` (Results; `qualifies`: Nap nicht nachweislich besser als Weiterlernen, aber auch nicht schlechter); `ericsson1993deliberate` (S. 376; `context_only`).
- **Sicherheitslabel:** *moderate* für die Aussage „Schlafverlust beeinträchtigt Gedächtnisbildung im Labor“ (konsistente Richtung in zwei Meta-Analysen, aber Publikationsbias, geringe Power, Labormaterial); *low* für „ein schlafschützender Planer verbessert Prüfungsleistung“ (keine Interventionsstudie gefunden, Indirektheit).
- **Observable:** Anteil geplanter und tatsächlich protokollierter Sitzungen innerhalb des Fensters; Overrides; ob ein Fenster angegeben wurde.
- **Unabhängiges Outcome:** verzögerte (≥ 7 Tage, *PPP*), unassistierte Leistung auf zurückgehaltenen Items; optional extern bewertete Prüfungsnote.
- **Harm/Failure:** Schuld oder Angst bei Abweichungen („du hast zu wenig geschlafen“) → keine wertenden Meldungen; Über-Medikalisierung; Datenschutz (Schlafdaten sind Gesundheitsdaten) → nur lokal, nur Fenster, keine Wearable-Anbindung (siehe §7); Starrheit vor Prüfungen.
- **Falsifier:** In einem randomisierten Produktvergleich (schlafschützender vs. unbeschränkter Planer) zeigt sich bei ausreichender Präzision keine Verbesserung — oder eine Verschlechterung — der verzögerten unassistierten Leistung bzw. der Itemabdeckung; oder Nutzer verschieben Lernen systematisch in unprotokollierte Nachtzeiten.

### R1-POL-B02 — Prüfungsvorabend und Prüfungswoche

- **Kontext:** Letzte Tage vor einem eingetragenen Prüfungstermin.
- **Empfehlung:** Plan so bauen, dass jeder prüfungsrelevante Block möglichst mindestens eine Nacht vor der Prüfung erstmals gelernt und danach noch mindestens einmal abgerufen wurde (*PPP*: ≥ 1 Nacht, ≥ 1 Abruf). Am Vorabend leichte, prüfungsnahe Wiederholung bekannter Inhalte statt Einführung großer neuer Blöcke. Das Produkt darf **nicht** behaupten, der Schlaf der letzten Nacht entscheide die Note.
- **Abstention/Fallback:** Wenn der Plan rechnerisch nicht mehr aufgeht (zu viel unbearbeiteter Stoff), wird die Zielkonflikt-Lage offen gezeigt (Priorisierung nach Prüfungsgewicht), ohne Moralisierung und ohne eine Nachtschicht vorzuschlagen (siehe §6.2).
- **Evidenzkanten:** `newbury2021sleepdeprivation` (MA2, Schlafentzug vor dem Lernen; `supports` gegen Neustoff nach Durchwachen); `okano2019sleep` (Results „Night before assessments“; `qualifies`: Einzelnacht nicht assoziiert, Wochen/Monat schon); `shields2017stress` (Results Retrieval; `context_only`).
- **Sicherheitslabel:** *low* — mechanistisch plausibel und richtungskonsistent, aber keine Studie hat genau diese Planregel getestet; Okano spricht gegen Überbetonung der letzten Nacht.
- **Observable:** Zeitpunkt der ersten Bearbeitung je Block relativ zum Prüfungstermin; Anzahl Abrufe danach.
- **Unabhängiges Outcome:** Prüfungsleistung je Block (falls vom Nutzer gemeldet), verzögerter Test.
- **Harm/Failure:** Panik durch „zu spät“-Meldungen; falsche Sicherheit durch Plan-Compliance.
- **Falsifier:** Blöcke, die erst am Prüfungsvortag eingeführt wurden, schneiden bei gleicher Lernzeit nicht schlechter ab als früher eingeführte (innerhalb- oder zwischen-Nutzer-Analyse mit Kontrolle der Schwierigkeit).

### R1-POL-B03 — Sitzungslänge und Pausen

- **Kontext:** Lernsitzungen im Produkt (Timer, Planblöcke).
- **Empfehlung:** Konfigurierbare Defaults: Fokusblock 25–50 min mit 5–10 min Pause; nach etwa 2 h Fokuszeit eine längere Pause von ≥ 20 min angeboten (alle Werte *PPP*). Der Nutzer kann Takt und Länge frei ändern oder abschalten. Begründung im Produkt: „Pausen können Müdigkeit und Stimmung verbessern“ — **nicht** „Pausen verbessern dein Lernen“.
- **Abstention/Fallback:** Wird der Timer regelmäßig übersprungen oder als störend gemeldet, wird er nicht weiter nahegelegt. Für Prüfungssimulationen gelten Prüfungsbedingungen statt Pausentakt.
- **Evidenzkanten:** `albulescu2022microbreaks` (Abstract, Results Task-Typ, Discussion; `supports` Vitalität/Müdigkeit, `qualifies` Leistung bei kognitiven Aufgaben n. s.); `biwer2023pomodoro` (Abstract RESULTS; `supports` Stimmung, `qualifies` kein Unterschied in Effort/Erledigung); `hagger2016egodepletion`, `vohs2021egodepletion` (`contradicts` Akku-Begründung); `kurzban2013opportunitycost` (`context_only`).
- **Sicherheitslabel:** *low* für Wohlbefinden-Effekte (kleine Effekte, unklares RoB, 1-Tages-Studie); *very_low* für jeden Lerneffekt (keine Behaltensmaße gefunden).
- **Observable:** Pausenannahme, Übersprungsrate, optionaler Müdigkeitsselbstbericht (1–5).
- **Unabhängiges Outcome:** verzögerte Behaltensleistung bei verschiedenen Takt-Einstellungen (Studie, nicht Produktdefault).
- **Harm/Failure:** Unterbrechung produktiver Phasen; Timer als Kontrollinstrument; Pseudowissenschaftliche Begründung („Gehirn braucht alle 25 min Pause“).
- **Falsifier:** Randomisierte Takt-Defaults zeigen keine Unterschiede in Müdigkeit/Abbrüchen, oder feste Takte senken die verzögerte Leistung gegenüber selbstregulierten Pausen.

### R1-POL-B04 — Arbeitslast und Überlastungshinweise ohne universelle Stundenquote

- **Kontext:** Nutzer plant sehr hohe Tageslast (z. B. „Study-maxing“-Ziel) oder steigert Last abrupt.
- **Empfehlung:** Keine allgemeingültige Obergrenze an Lernstunden. Stattdessen Vergleich mit der eigenen Basis: Reflexionshinweis, wenn die geplante Tageslast über 3 Tage > 1,5 × des eigenen gleitenden 7-Tage-Mittels der tatsächlich erledigten Fokuszeit liegt, oder wenn 7 Tage in Folge ohne leichten Tag geplant sind (beide Werte *PPP*). Optional kann der Nutzer selbst eine persönliche Obergrenze setzen. Hinweise sind abschaltbar und nie blockierend.
- **Abstention/Fallback:** Ohne ausreichende Historie (< 7 Tage) kein Vergleich, nur neutrale Information. Kein Hinweis während einer laufenden Prüfungssimulation.
- **Evidenzkanten:** `ericsson1993deliberate` (S. 369–371 „effort constraint“; S. 391 „around 4 hr“ als Hypothese; `context_only`); `macnamara2014deliberate` (Abstract, Bildung 4 % Varianz; `contradicts` Stundenmaximierung als Erfolgsrezept); `macnamara2019violin` (Results Tagebuch vs. Schätzung; `qualifies`); `madigan2021burnout` (Results; `supports` Relevanz von Überlastung, korrelativ); `pencavel2015hours`, `pega2021longhours` (`context_only`, indirekt); `plant2005studytime` (`context_only`, nur Titel).
- **Sicherheitslabel:** *very_low* für die konkrete Regel (keine Studie zu Lastwarnungen bei Studierenden; Evidenz indirekt, korrelativ, teils historisch); *moderate* für die Negativaussage „Stunden allein erklären Leistung nur begrenzt“ (Meta-Analyse + präregistrierte Replikation, aber anderer Bereich).
- **Observable:** geplante vs. erledigte Minuten je Tag; Anzahl Tage ohne leichten Tag; Reaktion auf Hinweis.
- **Unabhängiges Outcome:** Prüfungsleistung, Abbruch des Lernplans, Wohlbefinden (nur in genehmigter Studie mit validierten Instrumenten).
- **Harm/Failure:** Stundenquote durch die Hintertür; Bevormundung von Nutzern mit legitimen Intensivphasen; Fleiß wird pathologisiert; Daten zur Arbeitslast könnten zur Fremdüberwachung genutzt werden (nur lokal, nicht teilbar ohne aktive Zustimmung).
- **Falsifier:** Nutzer, die Hinweise erhalten, unterscheiden sich in verzögerter Leistung und Abbruchquote nicht von Nutzern ohne Hinweise, oder Hinweise senken die Lernzeit ohne Gewinn an Behalten/Wohlbefinden.

### R1-POL-B05 — Qualitäts- statt Stundenmetriken

- **Kontext:** Dashboards, Fortschrittsanzeigen, Gamification.
- **Empfehlung:** Primäre Fortschrittsanzeige = verzögerte, unassistierte Abrufleistung und Abdeckung prüfungsrelevanter Items (R1A/R5-Messvertrag), nicht Minuten oder Streaks. Lernzeit darf angezeigt werden, aber nicht belohnt werden (keine Badges für Stunden, keine Rangliste nach Stunden).
- **Abstention/Fallback:** Wenn noch keine verzögerten Abrufdaten existieren: „noch keine Aussage möglich“ statt Ersatz durch Stunden.
- **Evidenzkanten:** `macnamara2014deliberate` (`contradicts` Stunden als Mastery-Proxy); `macnamara2019violin` (Results Tagebuch; `supports` Selbstschätzungen überschätzen Übungszeit); `plant2005studytime` (Titel; `context_only`); `howard2021sdt` (`context_only`: externe Regulation ohne Leistungsassoziation).
- **Sicherheitslabel:** *low* — Begründung über Negativevidenz und Konstruktvalidität, nicht über ein Experiment mit Dashboards.
- **Observable:** Interaktion mit Dashboard, Anteil Items mit verzögertem Abruf.
- **Unabhängiges Outcome:** unabhängiger Transfertest; Prüfungsnote.
- **Harm/Failure:** Leistungsdruck durch Abrufquoten statt Stunden; Messung wird Trainingsziel (Testnähe).
- **Falsifier:** Stunden-basierte Fortschrittsanzeige führt bei gleicher Zeit zu gleich guter oder besserer verzögerter Leistung und geringerer Abbruchrate.

### R1-POL-B06 — Aufmerksamkeitsschützendes Sitzungsdesign

- **Kontext:** Passiver Input (Videos, lange Texte, Skripte) und Ablenkungen während Sitzungen.
- **Empfehlung:** Lange passive Inputs in Segmente gliedern und nach jedem Segment einen kurzen Abrufcheck anbieten (*PPP*: Segmentlänge 10–20 min Video bzw. ein Abschnitt Text). Eigene Benachrichtigungen des Produkts während Sitzungen unterdrücken. Ein optionaler Fokusmodus (z. B. Hinweis auf OS-Fokusfunktionen) darf angeboten werden, mit der ehrlichen Begründung „Unterbrechungen reduzieren“ — ohne Aussage, dass die bloße Anwesenheit des Telefons die Denkleistung senkt.
- **Abstention/Fallback:** Wenn Zwischenchecks die Bearbeitung stark abbrechen lassen (Überspringen), Frequenz senken; bei Prüfungssimulationen keine Zwischenchecks.
- **Evidenzkanten:** `szpunar2013interpolated` (Abstract; `supports`); `ruizpardo2022braindrain` (Abstract; `contradicts` Präsenzeffekt); `bottger2023braindrain` (Results; `qualifies`: kleiner gepoolter Effekt Nutzung + Präsenz); `wiradhany2017mediamultitasking` (Abstract; `contradicts` Trait-Behauptungen).
- **Sicherheitslabel:** *moderate* für „interpolierte Tests verringern Mind Wandering bei Videovorlesungen“ (kontrollierte Experimente, im Einklang mit R1A-Abrufevidenz; Abstract-Ebene, kurze Laborvorlesungen); *low* für Fokusmodus-Nutzen.
- **Observable:** Antworten/Überspringen bei Zwischenchecks; Fokusmodus-Aktivierung.
- **Unabhängiges Outcome:** verzögerter Endtest ohne Hilfe.
- **Harm/Failure:** Fragmentierung, Frust; Überwachung von Gerätenutzung (nicht erlaubt); „Brain-Drain“-Mythos.
- **Falsifier:** Segmentierte Inputs mit Zwischenchecks zeigen bei gleicher Zeit keine bessere verzögerte Leistung als nicht segmentierte (Produkt-RCT), oder erhöhen Abbruch deutlich.

### R1-POL-B07 — Motivationsframing

- **Kontext:** Produktsprache, Onboarding, Rückmeldungen nach Fehlern, Erinnerungen.
- **Empfehlung:** Autonomieunterstützend formulieren (Wahlmöglichkeiten, Begründungen, keine Drohungen), Fehler als Information darstellen, keine Scham-, Schuld- oder Verlustmechaniken (keine Streak-Verlust-Strafen). Optional eine kurze Relevanzreflexion („Wofür brauchst du das?“) anbieten (Utility Value), besonders sinnvoll bei niedriger Erfolgserwartung — als Angebot, nicht Pflicht. Growth-Mindset-Botschaften dürfen nicht als Leistungsversprechen erscheinen.
- **Abstention/Fallback:** Reflexionsaufgaben weglassen, wenn sie Lernzeit verdrängen oder ignoriert werden.
- **Evidenzkanten:** `howard2021sdt` (Abstract; `supports`, korrelativ); `hulleman2009utility` (Abstract; `supports`, moderiert); `macnamara2023mindset` (Abstract; `contradicts` Leistungsversprechen); `yeager2019mindset` (GPA-Absatz; `qualifies`: klein, kontextabhängig, Schule); `burnette2023mindset` (Abstract; `qualifies`); `sisk2018mindset` (`qualifies`).
- **Sicherheitslabel:** *low* — korrelative SDT-Evidenz, Utility-Value-Befunde schulbezogen und moderiert, Mindset-Effekte umstritten.
- **Observable:** Nutzung optionaler Reflexion; Rückkehr nach Fehlversuchen; Abbrüche.
- **Unabhängiges Outcome:** Persistenz bis zur Prüfung; Prüfungsleistung; validierte Motivationsskalen nur in Studie.
- **Harm/Failure:** Manipulative Gamification; toxische Positivität; Reflexion als Zeitverschwendung.
- **Falsifier:** Kontrollierende/Verlust-Framing-Variante führt im Vergleich zu höherer Persistenz und Leistung ohne Wohlbefindenseinbuße.

### R1-POL-B08 — Stress und Prüfungsangst

- **Kontext:** Nutzer meldet Prüfungsangst/Anspannung oder nähert sich dem Prüfungstermin.
- **Empfehlung:** (1) Prüfungsnahe Simulation und Abrufübung bis zu stabiler Leistung anbieten (Kernkomponente R1A). (2) Optional eine kurze, ehrliche Information zur Neubewertung körperlicher Anspannung („Aufregung kann Energie bereitstellen“) mit dem Hinweis, dass Effekte im Mittel klein sind. (3) Expressives Schreiben vor Prüfungen **nicht** als wirksam bewerben; allenfalls als freiwillige Tagebuchfunktion ohne Wirksamkeitsversprechen. (4) Bei Hinweisen auf starke oder anhaltende Angst: allgemeine Information + Verweis (R1-POL-B12).
- **Abstention/Fallback:** Keine Stressmessung, keine Physiologie, keine Bewertung von Angstsymptomen.
- **Evidenzkanten:** `shields2017stress` (Results Retrieval, g+ = −0,215; `supports` Relevanz); `bosshard2024reappraisal` (Results Publication bias, adjustiert d = 0,14; `supports` klein); `smith2016retrievalstress` (`supports`, Einzelstudie) und `wolf2017commentary` (Absatz 2; `qualifies`); `ramirez2011writing` (`supports`, Original) und `camerer2018ssrp` (`contradicts`, sekundär kodiert).
- **Sicherheitslabel:** *low* — kleine, biasanfällige Effekte; Laborstress ≠ Prüfungsangst; zentrale Schutzstudie unrepliziert.
- **Observable:** Nutzung der Simulation und Info-Karte; vom Nutzer gemeldete Anspannung (optional, nicht gespeichert ohne Zustimmung).
- **Unabhängiges Outcome:** Prüfungsleistung; Leistung in unabhängiger, zeitlich begrenzter Testsituation.
- **Harm/Failure:** Bagatellisierung behandlungsbedürftiger Angst; Druck durch „Stress ist gut“-Botschaft; falsche Wirksamkeitsversprechen.
- **Falsifier:** Reappraisal-Karte verbessert in einer präregistrierten Produktstudie die Leistung in zeitlich begrenzten Tests nicht oder erhöht berichtete Belastung.

### R1-POL-B09 — Bewegung und Sport

- **Kontext:** Nutzer fragt nach „Sport für bessere Noten“ oder plant Bewegungspausen.
- **Empfehlung:** Das Produkt behauptet nicht, regelmäßiger Sport verbessere Kognition oder Prüfungsleistung. Bewegungspausen dürfen als nutzergewählte Erholungsaktivität im Plan stehen. Keine Trainingsvorgaben, keine Intensitäts- oder Dauerempfehlungen.
- **Abstention/Fallback:** Gesundheitsfragen zu Sport → allgemeiner Verweis auf öffentliche Gesundheitsinformationen/Ärztin/Arzt; nicht Gegenstand dieses Produkts.
- **Evidenzkanten:** `ciria2023exercise` (Abstract; `contradicts` Kognitionsversprechen; Korrektur 2026 ungeprüft); `roig2013exercise` (Abstract; `qualifies`: akute Laboreffekte, kleine Studien).
- **Sicherheitslabel:** *moderate* für die Unterlassungsregel (bias-sensitive Umbrella-Analyse zeigt vernachlässigbaren chronischen Effekt; Einschränkung: Korrektur ungeprüft, gemischte Altersgruppen); *very_low* für jeden akuten Timing-Nutzen.
- **Observable:** Nutzer plant Bewegungsblöcke (Information, keine Bewertung).
- **Unabhängiges Outcome:** —
- **Harm/Failure:** Unbelegte Versprechen; Druck zu Sport bei Krankheit/Behinderung; Gesundheitsdatensammlung.
- **Falsifier:** Eine neue, bias-sensitive Synthese von RCTs mit jungen Erwachsenen findet robuste Effekte akuter oder chronischer Bewegung auf verzögerte Lernleistung → Policy neu prüfen.

### R1-POL-B10 — Erholung, Off-Zeiten, Benachrichtigungen

- **Kontext:** Erinnerungen, Push-Nachrichten, Wochenplanung.
- **Empfehlung:** Keine Lern-Erinnerungen im Schlaf- oder vom Nutzer definierten Off-Fenster. Wochenpläne enthalten standardmäßig einen leichten Tag pro Woche (*PPP*), den der Nutzer entfernen kann. Erinnerungsfrequenz begrenzt (*PPP*: höchstens 2 pro Tag), abschaltbar.
- **Abstention/Fallback:** In den letzten Tagen vor einer Prüfung darf der Nutzer den leichten Tag streichen, ohne Warnschleife.
- **Evidenzkanten:** `wendsche2017detachment` (Abstract; `supports` Wohlbefinden, `qualifies`: null für physiologische Stressmarker, negativ für Kreativität; Beschäftigte); `ericsson1993deliberate` (S. 377 Wochenende/Freizeit als Ruhe, S. 371 Erholung; `context_only`); `madigan2021burnout` (`context_only`).
- **Sicherheitslabel:** *very_low* — indirekte, korrelative Evidenz aus Arbeitswelt; keine Studierendenstudie zu Benachrichtigungsregeln gefunden.
- **Observable:** Benachrichtigungen im Off-Fenster (Soll: 0), Deaktivierungsrate.
- **Unabhängiges Outcome:** Planabbruch, Prüfungsleistung, Wohlbefinden in Studie.
- **Harm/Failure:** Verpasste Termine durch zu wenig Erinnerungen; Paternalismus.
- **Falsifier:** Nutzer mit Off-Fenster-Regel brechen Pläne häufiger ab oder schneiden schlechter ab, ohne Wohlbefindensvorteil.

### R1-POL-B11 — Register verbotener Produktbehauptungen

- **Kontext:** Jede generierte oder redaktionelle Produktsprache, Marketing, Tutor-Antworten.
- **Empfehlung:** Folgende Aussagen dürfen nicht erscheinen (weder als Fakt noch als Begründung einer Funktion):
  1. Lernstil-Meshing (visuell/auditiv/kinästhetisch), Links-/Rechtshirn-Typen, „Brain Gym“/Koordinationsübungen zur Hemisphärenintegration, „10 % des Gehirns“ (`dekker2012neuromyths` Table 1; vgl. `pashler2008`).
  2. „Gehirnbasiert“, „neuro-optimiert“ oder „wissenschaftlich bewiesen für dein Gehirn“ als Validierung einer Funktion (`bowers2016educationalneuro`).
  3. Willenskraft als aufladbarer Akku / Ego Depletion (`hagger2016egodepletion`, `vohs2021egodepletion`).
  4. Lernen im Schlaf, Cue-Abspielen im Schlaf, Hirnstimulation (`hu2020tmr`, `lutz2026sleep`: Laborverfahren).
  5. „10.000 Stunden machen Experten“ und „maximal 4 Stunden pro Tag“ als Tatsache (`macnamara2014deliberate`, `macnamara2019violin`, `ericsson1993deliberate` S. 391).
  6. Growth Mindset oder Stressumdeutung als garantierter Leistungsboost (`macnamara2023mindset`, `bosshard2024reappraisal`).
  7. „Die bloße Anwesenheit des Handys senkt deine Intelligenz“ (`ruizpardo2022braindrain`).
  8. Sport als Kognitions-/Notenbooster (`ciria2023exercise`).
  9. Schlafbewertungen aus Wearables als valide Qualitätsmessung (`okano2019sleep`, Discussion: Fitbit-Qualitätsscore ohne publizierte Validierung).
  10. Jede Substanz-, Nootropika-, Koffein- oder Dosierungsempfehlung (Sicherheitsgrenze, nicht evidenzbasiert entschieden).
  11. „Study-maxing“-Routinen als wissenschaftlich validiert (informeller Sammelbegriff, Charter).
- **Abstention/Fallback:** Fragt ein Nutzer explizit nach einem dieser Themen, antwortet das Produkt mit einer neutralen Einordnung des Evidenzstands (ggf. „umstritten/nicht belegt“) und ohne Handlungsanweisung; bei Substanzen nur Verweis auf ärztliche/pharmazeutische Beratung.
- **Sicherheitslabel:** *high* für Punkt 3 („nicht repliziert“: zwei große präregistrierte Multi-Lab-Replikationen); *moderate* für Punkt 1 (R1B belegt nur die Verbreitung des Glaubens, `dekker2012neuromyths`; die Zurückweisung des Meshing stützt sich auf die bestehende KB-Quelle `pashler2008`, hier nicht neu auditiert) und für Punkt 7 (eine präregistrierte direkte Replikation null, eine Meta-Analyse mit schwacher Biasprüfung klein negativ — als Tatsache jedenfalls nicht behauptbar); *moderate* für 4, 5, 6, 8 (Synthesen mit Bias-Analysen oder Replikationen, aber laufende Debatten); 9–11 sind normative Sicherheitsregeln.
- **Observable:** Automatisierte Prüfung generierter Texte gegen eine Begriffsliste (technisch, nicht Lernoutcome).
- **Unabhängiges Outcome:** Unabhängiger redaktioneller Review von Stichproben generierter Texte.
- **Harm/Failure:** Überblocken legitimer Erklärungen (z. B. Vorlesung *über* Neuromythen) → Regel gilt für Produktbehauptungen, nicht für Fachinhalte, die Nutzer lernen.
- **Falsifier:** Neue präregistrierte, unabhängig replizierte Evidenz für eine der Aussagen (z. B. Meshing-Interaktion) → Eintrag gezielt revidieren.

### R1-POL-B12 — Medizinische Grenze, Weiterverweisung und Datenschutz

- **Kontext:** Nutzer berichtet anhaltende Schlafprobleme, Erschöpfung/Burnout-Anzeichen, starke Angst, Panik, depressive Stimmung oder Krisen.
- **Empfehlung:** Ausschließlich allgemeine Information und Verweis auf professionelle Hilfe (Studierendenberatung, psychologische Beratungsstelle, Hausärztin/Hausarzt; in akuten Krisen lokale Notrufnummern). Keine Diagnose, kein Scoring, keine Therapieelemente (z. B. CBT-I-Protokolle), keine Medikamenten-/Substanzhinweise. Lernplanung darf auf Wunsch des Nutzers entlastet werden (z. B. Pause im Plan), ohne medizinische Begründung.
- **Abstention/Fallback:** Unklare Meldung → einmal nachfragen, ob Unterstützung gewünscht ist; keine wiederholten Nachfragen.
- **Datenschutz:** Keine Erhebung von Gesundheits-, Schlaf- oder Stimmungsdaten als Default. Falls opt-in: lokal gespeichert, löschbar, nicht in Analytik, nicht für Personalisierung von Lerninhalten ohne getrennte Zustimmung.
- **Evidenzkanten:** `lu2025digitalsleep` (Abstract; `qualifies`: wirksame digitale Komponenten sind klinische Interventionen mit sehr heterogener Evidenz); `madigan2021burnout` (`context_only`); `wendsche2017detachment` (`context_only`).
- **Sicherheitslabel:** *normativ* — Sicherheits- und Rechtsgrenze, keine empirische Ableitung; es wird keine empirische Sicherheit beansprucht.
- **Observable:** Anzahl angezeigter Verweise (aggregiert, ohne Inhalte).
- **Unabhängiges Outcome:** Externer Sicherheits-/Datenschutzreview; Nutzerbeschwerden.
- **Harm/Failure:** Über-Medikalisierung normaler Prüfungsaufregung; Untererkennung echter Krisen (das Produkt ist kein Screening-Instrument und darf nicht so wirken); Datenlecks.
- **Falsifier:** Externer Review zeigt, dass Verweise nicht verstanden werden, stigmatisierend wirken oder dass sensible Daten das Gerät verlassen.

### 5.1 Übersicht

| ID | Kurzname | Sicherheitslabel (intern) | Haupt-Evidenz |
|---|---|---|---|
| R1-POL-B01 | Schlafschützende Planung | moderate (Richtung) / low (Produktwirkung) | newbury2021, crowley2024, okano2019, baron2021 |
| R1-POL-B02 | Prüfungsvorabend/-woche | low | newbury2021 MA2, okano2019 |
| R1-POL-B03 | Sitzungslänge/Pausen | low (Wohlbefinden) / very_low (Lernen) | albulescu2022, biwer2023, hagger2016, vohs2021 |
| R1-POL-B04 | Last ohne Stundenquote | very_low (Regel) / moderate (Negativaussage) | ericsson1993, macnamara2014/2019, madigan2021 |
| R1-POL-B05 | Qualitäts- statt Stundenmetriken | low | macnamara2014/2019 |
| R1-POL-B06 | Aufmerksamkeitsschutz | moderate / low | szpunar2013, ruizpardo2022, bottger2023 |
| R1-POL-B07 | Motivationsframing | low | howard2021, hulleman2009, macnamara2023, yeager2019 |
| R1-POL-B08 | Stress/Prüfungsangst | low | shields2017, bosshard2024, smith2016, camerer2018 |
| R1-POL-B09 | Bewegung | moderate (Unterlassung) | ciria2023, roig2013 |
| R1-POL-B10 | Off-Zeiten/Benachrichtigungen | very_low | wendsche2017 |
| R1-POL-B11 | Verbotene Behauptungen | high (Depletion) / moderate (übrige) / normativ (9–11) | hagger2016, vohs2021, dekker2012, bowers2016, u. a. |
| R1-POL-B12 | Medizinische Grenze/Datenschutz | normativ | lu2025 (Kontext) |

---

## 6. Ausgearbeiteter Fall und harter Gegenfall (synthetisch)

Alle Personen, Zahlen und Materialien sind erfunden. Zeitangaben im Plan sind *PPP*. Die Fälle zeigen Policy-Verhalten, nicht Wirksamkeit.

### 6.1 Fall A — Statistik-II-Klausur in 21 Tagen

**Ausgangslage.** Lernende L (Bachelor, 2. Studienjahr), Klausur in 21 Tagen; Stoff: 12 Kapitel, 180 Übungsitems, 4 Altklausuren. Nebenjob montags und mittwochs je 4 h. Angegebenes Schlaffenster 00:30–08:30. Protokollierte Fokuszeit der letzten 7 Tage: im Mittel 2,5 h/Tag. Nach einem „Study-maxing“-Video möchte L „ab sofort 10 h täglich“.

**Produktverhalten, Schritt für Schritt.**

1. *Onboarding (B01, B12):* Schlaf-/Off-Fenster wird übernommen; keine Bewertung der Schlafdauer. Keine Gesundheitsdaten werden abgefragt.
2. *Zielkonflikt 10 h (B04, B05, B11):* Das Produkt blockiert nicht. Es zeigt: geplante Last = 4 × eigene Basis; Hinweis, dass Lernstunden allein Leistung nur begrenzt vorhersagen und es keine belegte universelle Stundenzahl gibt (weder „10.000 h“ noch „4 h/Tag“). Angebot: schrittweise Steigerung (z. B. 3,5 → 5 → 6 h Fokuszeit über die erste Woche) oder Beibehaltung von 10 h auf eigenen Wunsch. L wählt die Steigerung.
3. *Plangerüst:* Woche 1 Kapitel 1–6 (Erstbearbeitung, Videos in Segmenten mit Zwischenabruf, B06); Woche 2 Kapitel 7–12 plus verteilter Abruf von 1–6 (R1A); Woche 3 Altklausuren unter Zeitbedingungen (B08) und gezielte Wiederholung. Jedes Kapitel wird spätestens an Tag 19 erstmals bearbeitet und danach mindestens einmal abgerufen (B02). Tag 20 ist ein leichter Tag mit kurzer prüfungsnaher Wiederholung; kein neuer Stoff am Vorabend.
4. *Sitzungen (B03):* Default 50/10 min; L stellt auf 90-min-Blöcke um — akzeptiert, keine Rückfrage.
5. *Tag 9 (B01):* L protokolliert eine Sitzung von 01:30–03:00 innerhalb des Schlaffensters. Keine Rüge. Am Morgen fragt der Plan (opt-in-Funktion „kurze Nacht melden“), ob heute leichtere Wiederholung statt des geplanten neuen Kapitels gewünscht ist; L lehnt ab, der Plan bleibt.
6. *Tag 14 (B12, B08):* L schreibt, sie könne vor Aufregung kaum schlafen und habe Herzrasen. Das Produkt gibt allgemeine Information, verweist auf die psychologische Beratungsstelle der Hochschule bzw. ärztliche Abklärung, bietet an, die Planlast zu reduzieren, und bietet optional die kurze Reappraisal-Information mit ehrlichem Hinweis auf kleine Effekte an. Kein Schlafprotokoll, keine Atem- oder Medikamentenanleitung, kein Symptom-Score.
7. *Fortschrittsanzeige (B05):* Statt „42 h gelernt“ zeigt das Dashboard je Kapitel die Genauigkeit bei verzögerten, unassistierten Abrufchecks (≥ 7 Tage nach Erstbearbeitung) und die Abdeckung.

**Observables:** geplante vs. erledigte Minuten; Sitzungszeitstempel relativ zum Fenster; Overrides; Zwischenabruf-Antworten; verzögerte Abrufgenauigkeit je Kapitel.
**Unabhängiges Outcome:** Leistung auf zurückgehaltenen Altklausur-Items, die nie im Training vorkamen, ohne Hilfe, ≥ 7 Tage nach letzter Bearbeitung; optional die vom Nutzer gemeldete Klausurnote.
**Was dieser Fall nicht zeigt:** dass L durch dieses Verhalten besser abschneidet als mit einem 10-h-Plan. Das wäre nur durch eine kontrollierte Studie prüfbar.

### 6.2 Harter Gegenfall B — „Letzte-Minute-Konflikt“ bei Schichtarbeit

**Ausgangslage.** Lernender M (Fernstudium, Pflege im Nachtdienst), Klausur in 36 Stunden, 5 von 10 Kapiteln nie bearbeitet. Angegebenes Schlaffenster 08:00–14:00, oft unterbrochen. M fragt: „Soll ich die Nacht durchlernen?“

**Warum der Fall hart ist.**
- Die Schlafstudien vergleichen Bedingungen mit **gleicher Lerngelegenheit**; hier konkurriert Schlaf mit jeglicher Erstbegegnung mit dem Stoff. Totalentzug vor dem Lernen beeinträchtigt Enkodierung (adjustiert g = 0,463), Abruf ohne Erholungsschlaf ist stärker beeinträchtigt (g = 0,410) — `newbury2021sleepdeprivation`. Gar nicht gelernter Stoff wird aber gar nicht abgerufen. Die Evidenz bestimmt das individuelle Optimum dieser Abwägung **nicht**.
- Die Populationen der Kernstudien (junge Erwachsene mit regelmäßigem Nachtschlaf; MIT-Erstsemester in `okano2019sleep`; Singapurer Studierende ohne Schlafdefizit in `cousins2019nap`) decken Schichtarbeit, fragmentierten Tagschlaf und Erwerbsbelastung nicht ab.
- Defaults für Pausentakt, Erinnerungen und „leichter Tag“ (B03, B10) passen nicht zu Dienstplänen.

**Richtiges Produktverhalten.**
1. B01 bleibt: Das Produkt schlägt **keine** durchwachte Nacht vor und plant nichts in das angegebene Fenster — es verbietet aber auch nichts und moralisiert nicht; M kann manuell Einheiten anlegen.
2. Abstention auf Ebene der Abwägung: Das Produkt erklärt kurz, was bekannt ist (Schlafverlust beeinträchtigt Aufnahme und Abruf; Ungelerntes bringt keine Punkte) und dass die Forschung diese persönliche Abwägung nicht entscheidet.
3. Transparente Priorisierung nach Prüfungsgewicht und nach dem, was in der Zeit realistisch auf Wiedererkennungs-/Grundniveau erreichbar ist; prüfungsnaher Abruf der bereits gelernten Kapitel (R1A).
4. Erinnerungen nur außerhalb des Tagschlaffensters; keine Chronotyp- oder Schichtarbeitsratschläge (keine Evidenz geprüft; Lücke G4).
5. Bei Erschöpfungs- oder Gesundheitssignalen B12.

**Was der Fall über die Policies lehrt:** B01/B02 sind Planungsdefaults, keine Wahrheiten über Einzelfälle. Ein System, das in diesem Fall „Schlaf ist immer besser“ behauptet, überzieht die Evidenz; ein System, das die Nacht empfiehlt, ebenfalls.

---

## 7. Domänentransfer, NOT_APPLICABLE-Entscheidungen und Technologiekandidaten

### 7.1 Transferbedingungen

| Befund | Wahrscheinlich übertragbar auf | Bedingung / Grenze | Explizit NOT_APPLICABLE |
|---|---|---|---|
| Schlafverlust ↔ Gedächtnisbildung (`newbury2021sleepdeprivation`, `crowley2024sleeprestriction`) | Deklaratives Prüfungswissen (Recht, Anatomie, Begriffe); einfache Verfahren | Primärmaterial sind Wortlisten, Bilder, motorische Sequenzen; komplexes Problemlösen, Beweiskonstruktion, Programmieren nicht direkt untersucht → Richtung übertragen, Größe nicht | Ableitung von **Sicherheitsregeln** für übermüdete Labor-, Werkstatt- oder Klinikarbeit aus Gedächtnisstudien → gehört in R4/R3 mit arbeitsmedizinischen Quellen |
| Prozedurale Effekte größer (`newbury2021sleepdeprivation`, g .449 vs .218) | Motorische Fertigkeiten (R4) | Nur Richtungshinweis; reale Handwerks-/Chirurgieübung hat eigene Übungsverteilungsliteratur (nicht recherchiert) | Übernahme von Pausen- oder Sitzungsparametern (B03) auf physische Übung → **NOT_APPLICABLE** |
| Mikropausen/Pomodoro (`albulescu2022microbreaks`, `biwer2023pomodoro`) | Selbststudium am Schreibtisch | Outcomes Wohlbefinden/Tagesleistung, nicht Lernen | Prüfungssimulationen (dort gelten Prüfungsbedingungen); physische Praxis; klinische Dienste → **NOT_APPLICABLE** |
| Interpolierte Tests gegen Mind Wandering (`szpunar2013interpolated`) | Videovorlesungen, lange Skripte in allen Fächern | Passiver Input; Abruffragen müssen fachlich korrekt und zieloperationsnah sein (R2/R3) | Bereits aktive Praxis (Coden, Beweisen, Werkstück) — Unterbrechung dort nicht belegt nützlich |
| Stress vor Abruf (`shields2017stress`), Reappraisal (`bosshard2024reappraisal`) | Schriftliche Prüfungen; mündliche Prüfungen/OSCE (öffentliche Leistung: d = 0,34 vs. kognitiv 0,20, Subgruppe) | Laborstressoren ≠ Prüfungsangst; Subgruppen nicht biasbereinigt | Stressmanagement in klinischen Akutsituationen (Patientensicherheit) → **NOT_APPLICABLE**, R3 |
| Deliberate Practice (`ericsson1993deliberate`, `macnamara2014deliberate`) | Musik, Sport, Spiele (Quellbereiche) | Bildung: 4 % erklärte Varianz → für Prüfungslernen nur indirekt | Ableitung täglicher Stundenober- oder -untergrenzen für Prüfungslernen → **NOT_APPLICABLE** |
| Motivationsinterventionen (`yeager2019mindset`, `hulleman2009utility`) | Hochschule nur bedingt (meist Schule) | Effekte klein, moderiert durch Erwartung/Kontext | Leistungsversprechen jeder Art → **NOT_APPLICABLE** |
| Sport (`ciria2023exercise`) | — | — | Kognitive/notenbezogene Begründung von Sport → **NOT_APPLICABLE** |
| TMR, Hirnstimulation (`hu2020tmr`, `lutz2026sleep`) | — | Labor mit Schlafstadienkontrolle | Jede Produktfunktion → **NOT_APPLICABLE** |
| Ego Depletion | — | — | Als Erklärungsmodell im Produkt → **NOT_APPLICABLE** |
| Lange Arbeitszeiten (`pencavel2015hours`, `pega2021longhours`) | Allgemeiner Kontext „abnehmender Grenzertrag, Gesundheitsrisiko chronischer Überlast“ | Beschäftigte, chronische Exposition, körperliche Arbeit | Numerische Schwellen für Studierende → **NOT_APPLICABLE** |

### 7.2 Technologiekandidaten

Produktvertrag-Kompatibilität: Anki bleibt einziger Karten-Scheduler (R0-Audit §2). R1B-Kandidaten betreffen **Sitzungs- und Planebene** (Prüfungsplan, Erinnerungen, Sitzungstimer, Produktsprache), nicht Kartenintervalle.

| Kandidat | Status | Evidenzstatus | Abhängigkeiten | Barrierefreiheit | Sicherheit/Datenschutz | Kosten |
|---|---|---|---|---|---|---|
| Nutzerdefiniertes Schlaf-/Off-Fenster im Plan- und Erinnerungssystem | candidate | B01/B10: indirekt, low | Plan-/Reminder-Komponente; keine Anki-Änderung | einfach; fragmentierte Fenster unterstützen | nur Zeitfenster, lokal | gering |
| Lastvergleich mit eigener 7-Tage-Basis + Reflexionshinweis | candidate | B04: very_low | lokale Sitzungsprotokolle | abschaltbar, nicht blockierend | Lastdaten lokal, nicht teilbar ohne Zustimmung | gering |
| Interpolierte Abrufchecks in Video-/Skript-Segmenten | candidate (Schnittstelle R1A/R5) | B06: moderate (Mind Wandering) | Itemgenerierung mit fachlicher Prüfung | Untertitel/Text-Alternativen | — | mittel |
| Konfigurierbarer Pausen-Timer | candidate, niedrige Priorität | B03: low/very_low | — | visuelle + akustische Optionen | — | gering |
| OS-Fokusmodus-Hinweis | candidate, niedrige Priorität | low | plattformabhängig | — | keine Gerätenutzungsüberwachung | gering |
| Claim-Lint gegen R1-POL-B11-Liste | candidate | high/moderate (Negativaussagen) | Textpipeline | — | — | gering |
| Statische, lokalisierte Hilfeseite (Beratung, Notruf) | candidate | normativ | verifizierte Kontaktdaten je Land/Hochschule (nicht erfinden) | mehrsprachig | — | gering, Pflegeaufwand |
| Wearable-/Schlaftracker-Anbindung | **rejected** | Validität der Qualitätsscores ungeklärt (`okano2019sleep`); Über-Medikalisierung | Drittanbieter-APIs | — | Gesundheitsdaten | mittel |
| Stimmungs-/Stress-Tracking, „Wellbeing-Coach“-Chatbot | **rejected** | klinische Grenze (B12); `lu2025digitalsleep` zeigt, dass wirksame Komponenten klinische Interventionen sind | — | — | hohes Risiko | hoch |
| Schlaf-Audio-Cues / „Lernen im Schlaf“ | **rejected** | Laborverfahren (`hu2020tmr`) | — | — | — | — |

---

## 8. Priorisierte Lückenliste

| Rang | Lücke | Warum entscheidungsrelevant | Was sie schließen würde |
|---|---|---|---|
| G1 | Keine Interventionsstudie gefunden, in der ein **schlaf- oder lastschützender Lernplaner** bei Studierenden verzögerte Prüfungsleistung verbessert | B01, B04, B10 beruhen auf Laborevidenz + Korrelation | Präregistrierter Produkt-RCT mit unassistiertem verzögerten Outcome (R5-Messvertrag) |
| G2 | Pausen-/Sitzungsliteratur ohne **Behaltensmaße** | B03 kann nur Wohlbefinden begründen | Experimente mit Taktvariation und ≥ 1-Wochen-Behaltenstest |
| G3 | **Dosis-Wirkung von Lernstunden** bei Studierenden mit objektiver Zeitmessung und Qualitätsmaßen; `plant2005studytime` nicht gelesen | „Study-maxing“-Fragen, B04/B05 | Volltext Plant 2005; Suche nach Kohorten mit Logdaten (LMS) und Prüfungsnoten |
| G4 | **Chronotyp, Prüfungszeitpunkt, All-nighter, Schichtarbeit** — Suchen P35, P38, P39, P42 erfolglos | Gegenfall 6.2; Fairness der Defaults | Gezielte Suche (Psychology/Sleep-Datenbanken), Fachexpertise Schlafmedizin |
| G5 | **Prüfungsangst-Interventionen** bei Studierenden (61 PubMed-Treffer P37 nicht gescreent); Camerer-Suppl.-Table-5 nicht selbst gelesen | B08 | Screening + Volltext einer aktuellen Meta-Analyse; Supplement prüfen |
| G6 | `smith2016retrievalstress` ohne unabhängige Replikation; Gedächtnisstärke-Konfundierung | B08, Schnittstelle R1A | Suche nach Replikationen 2017–2026; Studien mit gematchter Ausgangsleistung |
| G7 | **Author Correction 2026** zu `ciria2023exercise` nicht zugänglich | B09-Zahlen | Korrekturtext lesen |
| G8 | Volltexte von `hagger2016egodepletion`, `vohs2021egodepletion`, `biwer2023pomodoro` (Zuteilungsverfahren), `szpunar2013interpolated` (N, Messung), `crowley2024sleeprestriction` | Locator-Präzision, RoB | Volltextabruf über Verlag/Repositorien |
| G9 | Studentisches Burnout: **Längsschnitt- und Interventionsstudien**; Detachment bei Studierenden | B04, B10 | Gezielte Suche; Zeigarnik-Metaanalyse 2026 screenen |
| G10 | Mechanistische Details `lutz2026sleep` (Volltext 403) | Nur Hintergrund; geringe Produktrelevanz | Zugang über Bibliothek |
| G11 | Lazowski & Hulleman 2016 (Motivationsinterventionen) und College-Utility-Value-RCTs nicht abgerufen | B07 | Volltexte |
| G12 | Bestandsaufnahme verbreiteter „Study-maxing“-Behauptungen | Sprachregeln B11 | Inhaltsanalyse mit Protokoll; Behauptungen nur als Anekdoten klassifizieren |

Bewusst nicht recherchiert (Sicherheitsgrenze): Koffein, Nootropika, Medikamente, Nahrungsergänzung, Schlafmittel.

---

## 9. Was wir nicht behaupten können

- Dass irgendeine R1B-Policy die Prüfungsleistung, das Behalten oder das Wohlbefinden von Exam-Mastery-Nutzern verbessert. Es gibt keine Lernerdaten und keine Evaluation (`learning_evaluation = NOT_RUN`).
- Dass es eine wissenschaftlich begründete **tägliche Stundenzahl** für intensives Prüfungslernen gibt — weder eine Obergrenze (die „4 Stunden“ sind eine Hypothese aus kleinen Musik- und Schachstichproben und Anekdoten, `ericsson1993deliberate` S. 390–392) noch eine Untergrenze („10.000 Stunden“ ist nicht gestützt).
- Dass „Study-maxing“ eine validierte Technik ist; es ist ein informeller Sammelbegriff, dessen Erfolgsberichte Selektions- und Survivorship-Bias unterliegen.
- Dass die bekannten Labor-Effektgrößen (g 0,17–0,62 für Schlafentzug, 0,29 für Restriktion) die Größe des Effekts auf echte Klausurnoten beschreiben.
- Dass die Nacht vor der Prüfung entscheidend ist (Okano: keine Assoziation) — oder dass sie unwichtig ist (eine Korrelationsstudie, N = 88).
- Dass Nickerchen besser sind als Weiterlernen (Cousins: nicht signifikant verschieden nach einer Woche).
- Dass Pausen oder ein bestimmter Pomodoro-Takt das Lernen verbessern; belegt sind kleine Effekte auf selbstberichtete Müdigkeit/Vitalität.
- Dass Ego Depletion, Lernstile-Meshing, Hemisphärentypen, „Brain Drain“ durch bloße Handy-Präsenz, Sport als Kognitionsbooster oder Lernen im Schlaf produktrelevante Tatsachen sind.
- Dass Growth-Mindset- oder Stress-Reappraisal-Botschaften bei Studierenden zuverlässig Leistung steigern; die Effekte sind klein, heterogen und biasanfällig.
- Dass Burnout schlechte Leistung **verursacht**; die Evidenz ist überwiegend querschnittlich.
- Dass Befunde aus der Arbeitswelt (lange Arbeitszeiten, Detachment) quantitativ auf Studierende übertragbar sind.
- Dass neuronale Korrelate (Replay, Spindeln, Cortisol) eine Lernfunktion validieren.
- Dass dieses Dokument unabhängig geprüft ist: Es stammt von einem einzelnen Agenten; Doppelscreening, RoB-2/AMSTAR-2-Bewertungen wurden **nicht** durchgeführt (keine Scores aus Abstracts erfunden); Zugangsebenen sind in §1.6 und im JSON dokumentiert.
- Dass die Suche vollständig ist: Sie war seed- und known-item-getrieben, ohne lizenzierte Datenbanken; Fehlschläge sind in §1.3–1.4 dokumentiert.

---

## 10. Reproduktion

- Evidenzdatei: `docs/research/workstreams/r1/r1b_evidence.json` (42 Einträge; Validierung: `python3 -c "import json; d=json.load(open('docs/research/workstreams/r1/r1b_evidence.json')); print(len(d['entries']))"`).
- Volltexte und PDFs wurden ausschließlich im Session-Scratch-Verzeichnis gelesen und **nicht** ins Repository übernommen; im Dokument stehen nur Paraphrasen mit Fundstellen und kurze Zahlenangaben.
- Kein Engine-Code, keine KB-JSON-Datei, kein Produktvertrag wurde verändert. Keine Commits.
- Unabhängiger Review: **pending**. Reviewfragen: (1) Sind die adjustierten Newbury-Werte korrekt als vorläufig eingeordnet? (2) Ist die Kodierung „Cousins: overstated“ fair? (3) Ist die sekundäre FORRT-Kodierung für Ramirez & Beilock gegen Camerer Suppl. Table 5 korrekt? (4) Sind die Seitenzahlen zu Ericsson 1993 (S. 369–371, 376–377, 382, 390–392) korrekt zugeordnet? (5) Sind B01 und B04 mit dem Prinzip „keine universellen Stundenquoten“ vereinbar?
