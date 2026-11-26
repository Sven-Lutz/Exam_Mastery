# R0 — Reproduzierbares Such- und Prüfprotokoll

Version 1, 26.11.2026. Ein Agent, keine Subagents, keine parallelen Forschungsworkstreams. Referenzbestand: PR #20, Commit `3fdbc7d01ee45ecaf33bc17be5f2b1295d14d115`. Ergebnisse: [KB_GAP_AUDIT.md](KB_GAP_AUDIT.md). Datenmodell: [EVIDENCE_REGISTER_SCHEMA.md](EVIDENCE_REGISTER_SCHEMA.md).

## 1. Tatsächlich durchgeführter R0-Lauf

Dies war ein **begrenzter, vom bestehenden Register ausgehender Audit mit gezielter Volltextsuche**, keine systematische Suche der gesamten Learning-Sciences-Literatur. Keine nachträgliche Präregistrierung behauptet. Auswahl der elf vertieften Claims nach Einfluss auf Entscheidungen, numerischer Spezifität und Gefahr falscher Kompetenzbehauptungen. Bibliografische Prüfung aller 55 Kernreferenzen gegen vorhandenen Cache; aktuelle Online-Suche für ausgewählte Primärtexte. Keine PsycINFO-/Scopus-/Web-of-Science-Lizenzdatenbank benutzt. Web-Suchindex ist dynamisch; Rankings und Trefferzahlen sind nicht stabil. Suchtag dokumentiert, keine erfundenen sekundengenauen Suchzeitstempel oder vollständigen Trefferzahlen.

### Eingefrorene Eingaben

Gelesen: `AGENTS.md`, `docs/PRODUCT_CONTRACT.md`, `docs/TARGET_ARCHITECTURE.md`, Forschungscharter, `docs/RESEARCH_FOUNDATION.md`, `docs/learning_design_evidence_matrix.json`, `docs/EVALUATION_PROTOCOL.md`, `exam_mastery/knowledge/{sources,principles,specs,verification}.json`; ergänzend `scripts/verify_sources.py`, `knowledge/__init__.py`, `learning/{policy,diagnose,evaluation}.py`, ausgewählte vorhandene Tests und technische Reviewberichte. GitHub PR #20, Issue #21 einschließlich Ein-Agent-Kommentar sowie Human-Rejection-Issue #4 wurden gelesen. RL-Pilot-Berichte wurden ausschließlich lesend eingesehen; keine geschützten Kursquellen eingelesen oder veröffentlicht.

Der Snapshot enthält 55 Kernquellen, 52 Claims, 17 Prinzipien, sieben Specs und 17 Evidenzmatrix-Zeilen. Alle wurden triagiert. Fachbibliografien im 78-Einträge-Verifikationsregister sind keine zusätzliche lernwissenschaftliche Stichprobe. Elf Claim-Reviews verwenden elf Kernquellen als Hauptbelege; Reviews bleiben Sekundärsynthesen, auch wenn ihr Originalartikel gelesen wurde. Es wurden nicht sämtliche Primärstudien der Meta-Analysen nachgeprüft.

### Suchjournal: exakte ausgeführte Queries

Datenbank/Tool: allgemeiner Web-Suchindex über `web.run`, Datum für jede Zeile **2026-11-26**. Suchtreffer dienen nur der Entdeckung; Befunde aus Primärtexten oder ausdrücklich benannten Abstracts. Die folgende Liste enthält auch erfolglose/ersetzte Suchwege.

| Nr. | Exakte Query | Screeningentscheidung / Ziel |
|---|---|---|
| Q01 | `Rowland 2014 testing restudy meta analysis pdf table 1` | Sekundärbrief nicht als Beleg; Original-Volltext weiter gesucht. |
| Q02 | `Brunmair Richter 2019 interleaving meta analysis pdf` | Hochschul-Autorenmanuskript ausgewählt. |
| Q03 | `Kalyuga 2007 expertise reversal effect pdf 532` | Hochschul-PDF gewählt, keine Scribd-Zusammenfassung. |
| Q04 | `Rowland 2014 meta analysis filetype:pdf site:epfl.ch` | Kein nutzbarer vollständiger EPFL-Locator; weitergesucht. |
| Q05 | `Cepeda 2008 spacing effects learning temporal ridgeline filetype:pdf` | UCSD-PDF-Link später 404; Autorenarchiv als Ersatz. |
| Q06 | `Pan Rickard 2018 transfer test enhanced learning filetype:pdf` | Rickard-Lab-PDF ausgewählt. |
| Q07 | `Bastani 2025 generative artificial intelligence without guardrails harm learning PNAS full text` | PubMed→PMC veröffentlichter Artikel. |
| Q08 | `"Rowland2014" pdf` | Keine allein ausreichende Quelle; weitergesucht. |
| Q09 | `"Cepeda" "2008" "pdf" spacing` | Autorenpublikationsliste gefunden. |
| Q10 | `"Kluger" "DeNisi" "1996" pdf` | Sekundärarbeiten nicht als Originalbeleg übernommen. |
| Q11 | `"Sweller" "1988" "Cognitive Load During Problem Solving" pdf` | Originalartikel als Schul-PDF-Mirror gewählt. |
| Q12 | `"Rowland2014-meta-analysis.pdf"` | LinkedIn-Verweise verworfen; kein Volltextbeleg. |
| Q13 | `"Rowland" "2014" "meta-analysis" site:pdf.retrievalpractice.org` | Andere Texte/Referenzlisten reichen nicht; weitergesucht. |
| Q14 | `"Rowland" "2014" "testing" "pdf" -site:scribd.com -site:linkedin.com -site:teachingdb.com` | Vom Autor hochgeladener ResearchGate-Volltext lesbar. |
| Q15 | `"Roediger" "Karpicke" "2006" "249" pdf` | Originalartikel-Mirror an ECU gewählt. |
| Q16 | `"Kluger" "1996" site:mrbartonmaths.com` | Historischer Mirror nicht zuverlässig erreichbar; anderer Volltextweg. |
| Q17 | `"Kestin" "2025" "97652" full text` | Verlags-/PMC-Zugriff blockiert, Preprint v1 verfügbar. |
| Q18 | `"Kluger" "DeNisi" "1996" "Table 2" pdf` | Academia-Text des Originalartikels lesbar; nicht spätere Feedback-Reviews. |
| Q19 | `"10.1145/3534678.3539081"` | Identitäts-/Ableitungstriage für sp.3, keine neue Scheduler-Evaluation. |
| Q20 | `"10.1207/S15324818AME1503_5" guidelines validated` | Institutioneller Abstract präzisiert „logische“ Taxonomievalidierung. |

Keine zahlenmäßige PRISMA-Flussgrafik: Suchergebnisse wurden nicht als vollständiger deduplizierbarer Export geliefert. Reproduzierbar sind Auswahlbasis, Queries, Zugangswege, enthaltene Quellen und Ausschlussgründe, nicht eine erfundene Gesamtzahl aller Web-Treffer. Die elf Deep Reviews sind der endliche eingeschlossene Audit-Satz; andere Suchtreffer wurden nicht zur eigenen neuen Evidenzsynthese hochgestuft.

### Zugangs- und Versionsprotokoll

| Audit | Tatsächlich erreichter Text / geprüfte Stellen | Fehler / nicht geprüft |
|---|---|---|
| D1 | [ECU-PDF](https://psychology.ecu.edu/wp-content/pv-uploads/sites/216/2019/03/Roediger-Karpicke-2006.pdf), Originalartikel S.250–253 | Purdue-Downloadpfad 404; keine Originaldatenreplikation. |
| D2 | [ResearchGate-Autorenupload](https://www.researchgate.net/publication/264988491_The_Effect_of_Testing_Versus_Restudy_on_Retention_A_Meta-Analytic_Review_of_the_Testing_Effect), vollständiger Artikeltext; Tabellen 1/2 und Sensitivitätsdiskussion | Alter EPFL-Domainhinweis ohne Dateipfad nicht reproduzierbar. |
| D3 | [UCSD-Autoren-PDF](https://rickardlab.ucsd.edu/pdf/PR_2018.pdf), Tabellen 2–5, Manuskript S.25–27 | Rohdaten/alle Primärstudien nicht repliziert. |
| D4 | [York-Autoren-PDF](https://www.yorku.ca/ncepeda/publications/CVRWP2008.pdf), S.1096–1100 | UCSD-Suchlink 404; York-Link über Autorenpublikationsliste gefunden. |
| D5 | [Würzburg-Manuskript](https://www.uni-wuerzburg.de/fileadmin/06020400/2019/Brunmair_Richter_in_press__2019_META-ANALYSIS_OF_INTERLEAVED_LEARNING.pdf), Methoden/Ergebnisse/Tabellen 2/3 | Browser-Lesetool Timeout, direkter HTTP-Abruf erfolgreich; lokal mit vorhandenem PyMuPDF extrahiert. Nicht Version of Record; p-Ausdruck auffällig. |
| D6 | [Kentucky-PDF](https://www.uky.edu/~gmswan3/EDC608/Kalyuga2007_Article_ExpertiseReversalEffectAndItsI.pdf), S.515–518 und 530–532 | Review, nicht direkte Lektüre jeder experimentellen Primärquelle. |
| D7 | [Academia-Originalartikeltext](https://www.academia.edu/43519881/Kluger_DeNisi_1996_meta_analysis), Method/Ausschlüsse/Tabelle 2/Limitations | Mirror-OCR; keine fehlerfreie Tabellengeometrie voraussetzen. mrbartonmaths-Pfad nicht zugänglich. |
| D8 | [Frontiers-Volltext](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2019.03087/full), Methods/Results, Tabellen 2/3 | Nicht alle Primärstudien/Supplementdaten repliziert. |
| D9 | [Sweller-PDF](https://www.waddesdonschool.com/wp-content/uploads/2021/02/Cognitive-Load-Theory-Sweller-J-1988.pdf), S.277–282 | Mirror, keine eigene Replikation des Experiments/Computermodells. |
| D10 | [PMC12232635](https://pmc.ncbi.nlm.nih.gov/articles/PMC12232635/), Design/Main Results/Fußnoten | SI und Präregistrierung nicht vollständig geprüft; nicht alten Preprint als veröffentlichte Fassung ausgegeben. |
| D11 | [Research Square v1](https://assets-eu.researchsquare.com/files/rs-4243877/v1/5ebc554a-9a22-4dbf-a25c-8998783fd358.pdf?c=1750944764), S.3–4/9–10 | Nature HTML/PDF Redirect-Fehler, PMC CAPTCHA, EuropePMC nicht zugänglich; REST-Abruf Timeout. 2025-Volltextstatus nicht erneuert. |

Volltext-Mirrors sind Zugangswege, keine unabhängigen Replikationen. Copyright-PDFs und Volltextkopien bleiben außerhalb des Git-Repositories; nur paraphrasierte Befunde, Locator und Originalreferenz werden veröffentlicht. Nicht erreichbarer Zugang ist **nicht** gleich inhaltlicher Ausschluss oder negative Evidenz. Der lokale temporäre Download ist keine Voraussetzung zum Lesen des PR.

## 2. Verbindlicher Methodenvorschlag für spätere R1–R9-Arbeiten

Der folgende Standard ist ein **Vorschlag zur Begutachtung**, keine rückwirkend erfüllte Vollsystematik dieses R0-Laufs. Vor weiterer Suche eine datierte Protokollversion mit RQ, Population, Lernoperation, Intervention, Comparator, Outcome und Zeitpunkt festschreiben. Änderungen mit Grund/Zeitpunkt protokollieren. Keine eigenen Certainty-Prozentwerte.

### Suchstrategie und Screening

1. Zwei Stufen: Scoping für Begriffe/Lücken; danach begrenzte systematische Frage. [PRISMA-ScR](https://www.prisma-statement.org/scoping) strukturiert Berichterstattung, ist kein Qualitätssiegel. Suchberichte nach [PRISMA-S](https://www.prisma-statement.org/prisma-search): Datenbank, Plattform, Felder, vollständige Syntax, Filter, Zeitpunkt, Export und Update.
2. Datenbanken passend wählen: PsycINFO/ERIC für Lernen, PubMed für klinische und neurobezogene Fragen, ACM/IEEE für Informatik, Crossref/OpenAlex für Identität/Zitationswege; rechtliche Autorität zusätzlich anhand datierter Primärnormen. Zugangsmangel offen melden. Keine Behauptung einer Datenbanksuche aus einer Google-ähnlichen Web-Query.
3. Titel/Abstract-Screening und Volltext-Screening getrennt. Je Entscheidung Include/Exclude/Awaiting mit Grund, Reviewer, Datum und RQ. DOI normalisieren, Titel/Autor/Jahr prüfen, Preprint/Artikel/Erratum als eine Studienfamilie verknüpfen. Mehrere Experimente/Outcomes derselben Stichprobe nicht unabhängig zählen.
4. Einschluss: direkte Lernoperation oder begründeter Mechanismenbezug, nachvollziehbarer Comparator/Outcome; Null-/Schadensbefunde und unveröffentlichte Studien mit gleicher Relevanz. Theorien, technische Benchmarks und Produktberichte separat klassifizieren. Ausschluss aus Wirksamkeitssynthese: Werbung, bloße Nutzungszahlen, nicht identifizierbare Quelle, reine Antwortgenauigkeit ohne Lernoutcome. Diese dürfen als Kontext-/Technologieregister erhalten bleiben.
5. Rückwärts-/Vorwärtszitation je eingeschlossener Schlüsselsynthese; Originalquellen zu starken Zahlen und Gegenbefunden nachlesen. Korrekturen/Retraktionen und zeitlich neuere Studien prüfen. Sprach-/Zugangsbias ausweisen; zunächst Deutsch/Englisch als praktische Begrenzung, keine Aussage über andere Sprachräume.
6. Stoppen nach vorab festgelegtem Quellen-/Zeitumfang oder abnehmendem Ertrag und explizit offene Zugänge übergeben. Kein endloses Suchen, keine Wahl ausschließlich großer positiver Effekte. Ein vollständiger Screeningexport ist in späteren systematischen Sprints verpflichtend.

### Ausführbare Suchvorlagen — noch nicht ausgeführt

Die folgenden Strings sind Startvorlagen; Plattformsyntax/Deskriptoren müssen bei tatsächlicher Nutzung protokolliert werden. Eine Vorlage ist kein ausgeführter Suchlauf.

```text
("retrieval practice" OR "practice testing") AND (transfer OR "problem solving" OR proof) AND (random* OR experiment* OR "meta-analysis")
("worked example*" OR fading OR "expertise reversal") AND (mathematics OR programming OR proof) AND (retention OR transfer)
(spacing OR "distributed practice" OR interleaving) AND (complex OR procedural OR conceptual) AND (null OR adverse OR moderator* OR replication)
("AI tutor*" OR "generative AI" OR "intelligent tutoring") AND (unassisted OR delayed OR dependency OR offloading OR transfer) AND (random* OR controlled)
(feedback OR scaffolding) AND ("cognitive load" OR "mental effort") AND (learning OR retention) AND (negative OR null OR moderator*)
```

Für R1–R4 ergänzen: `sleep restriction`, `fatigue`, `deliberate practice`, `metacognitive calibration`; `legal reasoning/subsumption`, `clinical reasoning/diagnostic calibration`; `psychomotor/simulation transfer/laboratory safety`. Diese Begriffe eröffnen spätere Fragen, sind **keine bereits geprüften Befunde**.

### Evidenzextraktion und Bias

Extraktion auf **Outcome-/Kontrast-/Zeitpunkt-Ebene**, nicht ein Qualitätsetikett pro Paper. Felder im Registerschema: Design, Zuteilungseinheit, analysiertes N versus randomisiertes N, Vorwissen, Setting, Dauer, Aufgabenoperation, aktive Kontrolle, Assistenz, Messnähe, Ausschlüsse, Effektmetrik/CI, Clusterung, Missingness, Verblindung, Präregistrierung, Finanzierung/Interessenkonflikte und Grenzen.

[RoB 2](https://www.riskofbias.info/welcome/rob-2-0-tool) besitzt eigene Varianten für individuell randomisierte, Cluster- und Crossover-Studien. Passende Variante verwenden; Begründung und Fundstelle pro Domäne, fehlende Information als solche kennzeichnen. Keine aus Abstracts erfundene Gesamtbewertung. Bei nicht randomisierten Studien Confounding, Selektion und Zeittrends beurteilen; Vorher-Nachher ohne Kontrolle nicht als isolierten kausalen Interventionseffekt behandeln.

AMSTAR 2 ist für passende systematische Interventionsreviews zu prüfen, nicht mechanisch für narrative/Theoriereviews. Die in R0 versuchte [Originalpublikation](https://doi.org/10.1136/bmj.j4008) war im Web-Leser blockiert; deshalb hier keine vollständige Instrumentanwendung behauptet. Bei Reviews speziell suchen: Protokoll, Suchabdeckung, Doppel-Screening, Studienüberlappung, Abhängigkeit der Effekte, Modellwahl, Publikationsbias/Sensitivität und Umgang mit Risiko der Primärstudien.

Für Evidenzkörper getrennt von Einzelstudien die fünf [GRADE-Domänen](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-14) berücksichtigen: Bias, Inkonsistenz, Indirektheit, Impräzision, Publikationsbias. Eine angepasste interne Beurteilung als **GRADE-informiert**, nicht als formell zertifiziertes GRADE-Verfahren bezeichnen. Ein Moderator in einer Meta-Regression ist nicht automatisch kausal. I² misst keine Prozentwahrscheinlichkeit, dass eine Intervention nicht funktioniert. Nichtsignifikanz, Evidenz für kleine Wirkung und nachgewiesene Äquivalenz unterscheiden.

### Widersprüche und externe Validität

Ein Widerspruchsdatensatz nennt beide Claim-Versionen, Population/Operation/Comparator/Zeitpunkt und plausible Erklärung samt Status: getestet, teilweise gestützt oder offen. Keine „Auflösung“ allein durch eine passende Geschichte. Gleiche Studie mit mehreren Endpunkten ist kein Replikationspaket. Positive unmittelbare und negative verzögerte Wirkung können gleichzeitig zutreffen.

| Domäne | Zieloperationen trennen | Unabhängiger Outcome / Grenze |
|---|---|---|
| Mathematik | Definition abrufen, Verfahren ausführen, Beweis verstehen/prüfen/konstruieren | Unbekannter Beweis/Gegenbeispiel mit fachlicher Rubrik; numerischer Check kein allgemeiner Beweis. |
| Recht | Normwissen, Issue spotting, Subsumtion, Argumentbewertung | Neuer datierter Fall, vertretbare Alternativen; Recall ist kein Gutachten. |
| Informatik | Tracing, Implementieren, Debugging, Komplexitätsargument | Unbekannter Fehler/fachliche Erklärung; bestandene Tests können überfitten. |
| Medizin | Faktenabruf, Differentialdiagnose, Unsicherheitsentscheidung, praktische Durchführung | Neue sichere Fälle, Kalibrierung und externe Prüfung; Quiz/Simulator keine klinische Freigabe. |
| Naturwissenschaften | Modellannahmen, Messplanung, Inferenz, Laborhandlung | Neue Daten/Controls/Unsicherheit; Simulation ersetzt keine reale Mess-/Sicherheitskompetenz. |
| Praktische Fertigkeiten | Wahrnehmen, koordinieren, ausführen, Fehler korrigieren | Reale beobachtete Leistung unter Aufsicht; verbale Beschreibung nicht motorischer Transfer. |

Diese Tabelle ist ein Prüfrahmen, keine abgeschlossene Fachdidaktik-Synthese. NOT_APPLICABLE ist zulässig: z.B. Flashcards als alleiniger Nachweis einer motorischen Fertigkeit. Accessibility, Sprache und Vorwissen sind Moderatoren/Bedarfe, keine Lernstiltypen.

## 3. Von Evidenz zu Produktentscheidung

Pflichtkette: **Befund → Geltungsbedingungen → Zieloperation → Designentscheidung → technische Anforderung → beobachtbare Handlung → unabhängiger Outcome → Gegenfall**. Jede Kante erhält Begründung und Unsicherheit. Der wissenschaftliche Befund kann stark und die konkrete Policy trotzdem unvalidiert sein.

Prüfungen bleiben getrennt:

- bibliografisch/inhaltlich: Quelle/Passage tatsächlich passend;
- technisch: gespeichertes Ereignis, reproduzierbarer Algorithmus, richtige Darstellung;
- fachlich: gültiger Beweis, vollständige Lösung, semantisch passende Aufgabe;
- menschliche Produktqualität: verständliche selbstständig nutzbare Lernprodukte;
- empirisch: vorab definierter Lernerfolg ohne Hilfe, verzögert und an geeigneten Transferaufgaben.

Vor Studien: relevante minimale Wirkung bzw. Nichtunterlegenheitsgrenze begründen; Fallzahl einschließlich Clusterung/Dropout planen, Analyse vorab festlegen, Instrumente pilotieren, blind scoren. Effekte samt CI/absoluten Werten und Missingness berichten. Hilfesuchen, Klicks und Zufriedenheit sind mögliche Mediatoren/Prozessmaße, keine Ersatzendpunkte. Keine Studie startet durch dieses Protokoll.

## 4. Reproduzierbare lokale Dokumentprüfungen

Keine Installation, Engine-Ausführung oder bezahlter Modellaufruf erforderlich. Im Research-Worktree mit Python 3:

```sh
set -eu
python3 - <<'PY'
import collections, importlib.util, json, pathlib, re
p = pathlib.Path('.')
kb = p / 'exam_mastery/knowledge'
sources = json.loads((kb/'sources.json').read_text())['sources']
principles = json.loads((kb/'principles.json').read_text())['principles']
claims = [c for x in principles for c in x['claims']]
audit = (p/'docs/research/workstreams/KB_GAP_AUDIT.md').read_text()
assert len(sources) == 55 and len(principles) == 17 and len(claims) == 52
for s in sources:
    assert len(re.findall(r'^\| `' + re.escape(s['id']) + r'` —', audit, re.M)) == 1
for c in claims:
    assert len(re.findall(r'^\| `' + re.escape(c['id']) + r'` ', audit, re.M)) == 1
assert len(re.findall(r'^### D\d+ —', audit, re.M)) == 11
spec = importlib.util.spec_from_file_location('verify', 'scripts/verify_sources.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
results = {}
for s in sources:
    r = m.check_doi(s, offline=True) if s.get('doi') else m.check_isbn(s, offline=True)
    if s.get('doi') and s.get('isbn') and not r.get('found'):
        r = m.check_isbn(s, offline=True)
    assert r.get('found') and r.get('title_match') and r.get('year_match'), s['id']
    results[s['id']] = r
snippets = [e for c in claims for e in c.get('abstract_evidence', [])]
assert len(snippets) == 48
for e in snippets:
    assert m.norm(e['snippet']) in results[e['source']].get('abstract', '')
print('55 sources / 52 claims / 11 reviews / 48 cached snippets: PASS')
print(collections.Counter(c['basis'] for c in claims))
PY
git diff --check
git diff --name-only 3fdbc7d01ee45ecaf33bc17be5f2b1295d14d115
```

Die Importfunktionen nutzen `offline=True`; das Hauptprogramm von `verify_sources.py` wird absichtlich nicht gestartet, weil es `verification.json` neu schreiben würde. Keine Änderung historischer Evidenzklassifikation. Zusätzlich relative Markdown-Links, Dokumentumfang und geschützte Branch-Hashes vor Commit prüfen. Metadaten-/Snippet-PASS ist keine Prüfung der wissenschaftlichen Schlussfolgerung; dafür ist der gesamte Audit zu lesen und unabhängig zu kritisieren.
