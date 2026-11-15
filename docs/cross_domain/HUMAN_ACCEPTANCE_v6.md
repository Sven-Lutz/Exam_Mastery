# Human-Acceptance-Paket v6 (Issue #9, Korrekturrunde v6.1)

**Status:** HUMAN_REVIEW_PENDING.
- Keine akademische Selbstfreigabe; PR #3 bleibt Draft.
- Die vier Aufgaben je neuem Fach sind **Piloten**, keine Kursprodukte.
- Lehrbuch, Arbeitsbuch, Musterlösungen, Prüfungen und Anki bleiben offene Produktanforderungen.

## 1. Was Sie öffnen (alles lokal, offline)

| Prüfgegenstand | Datei |
|---|---|
| Analysis-Labor | `~/Exam_Mastery_Output/modules/analysis1_folgen/labor.html` |
| Entrepreneurship-Labor | `~/Exam_Mastery_Output/modules/ent_funding/labor.html` |
| Tutor-Pakete und Testprotokolle | `…/modules/<modul>/tutor/` (README.md, TESTPROTOKOLL.md) |
| QC-Berichte (getrennte Dimensionen) | `…/modules/<modul>/qc_report.json` |
| Recherche-Nachweise | `…/modules/<modul>/research_trace.md`; Rohprotokoll `modules/<modul>/research_log.jsonl` im Repo |
| NLP-Einheit (Lernplattform, Labor, PDFs, Anki) | `~/Exam_Mastery_Output/reference_units/nlp_sequence_labeling/` |
| Nachweisbilder | `docs/cross_domain/evidence_v6_1/` (neu), `docs/cross_domain/evidence/` (v6) |

## 2. Korrekturen dieser Runde und ihre automatische Prüfung

| # | Mangel (Issue #9) | Korrektur | Automatischer Nachweis |
|---|---|---|---|
| 1 | „Kontraktion nachweisen“ wertete eine endliche Bahn als Beweis | Drei getrennte Stufen: Simulation, Indiz (Abtastung), **Beweis-Zertifikat**. Das Zertifikat verlangt: abgeschlossenes Intervall [a, b], analytisch begründete Invarianz f([a,b]) ⊆ [a,b], q = sup\|f′\| < 1 auf [a,b] (aus Monotonie von f und \|f′\|, kein Abtasten) und a₁ ∈ [a,b]. Challenge neu: „Kontraktion beweisen“. Neue Unmöglichkeits-Challenge: x + 1/x hat auf keinem [a,b] ein Zertifikat. | Zertifikat gegen dichte Python-Abtastung an 300 Zufallsintervallen: nie „bewiesen“ bei verletzter Bedingung. Browser: Simulation allein löst nichts; [0,6; 0,9] ohne a₁ löst nichts; [0,5; 1] löst. |
| 2 | QC vermengte Dimensionen | Getrennt: source_validity, literature_coverage, computation (nur registrierte Rechenwerte, Geltungsbereich ausgewiesen), proof_correctness (**immer** NOT_VERIFIED), didactic_quality (NOT_RATED). Abdeckung zählt nur Passagen, die der Kompetenz zugeordnet sind. | Test: entfernte Passage ⇒ literature_coverage FAIL. ENT meldet weiterhin die offene Lücke `formen`. |
| 3 | Keine echte Eigenrecherche | `exam_mastery/modules/research.py`: Bedarf → Suche → Abruf (HTTP-GET, SHA-256-Schnappschuss nur lokal) → wörtliche Passageprüfung → Entscheidung → Integration, alles protokolliert. Durchgeführt: Kerr, Nanda & Rhodes-Kropf 2014 (NBER w20358), 5/5 Passagen gefunden ⇒ neue Aufgabe EN5, Beispiel X4, Labor-Station v4, Tutor-Kontext. Lebl v6.3 KC-genau (9/9 Passagen). Lafferty (Penn-Repositorium) und Su (arXiv v5) belegt. | Test: jede Prüfung vollständig gefunden, SHA-256 vorhanden, Zitate ≤ 240 Zeichen, jede Integration verweist auf eine registrierte Quelle. |
| 4 | Tutor nicht erprobt | Zwei Testprotokolle mit je 6 Szenarien (sokratisch, Herleitung, gestufte Hinweise, Fehlerdiagnose, Rechenkorrektheit, neue Transferaufgabe; ENT zusätzlich Quellendisziplin). K.O.-Kriterien, Referenzwerte für Prüfer, JSON-Bewertungsbogen. Liegt jedem Tutor-Paket als `TESTPROTOKOLL.md` bei. | **Keine ChatGPT-Evaluation durchgeführt.** Es liegen keine Gesprächsprotokolle vor. |
| 5 | Sichtbares „null“; N = 698 nicht sichtbar | Ursache: Challenges ohne Bedingungstext schrieben `null` in den DOM. Behoben im gemeinsamen Kern. ε-Diagramm passt den Horizont an N, kleinstes N und Gegenbeispiel an; neue Abstandsansicht (log) zeigt die Schwelle bei 698. | Browsertest: kein „null“, „undefined“ oder „NaN“ in allen Tabs nach Hinweisen; SVG enthält „kleinstes N = 698“, „Gegenbeispiel n = 697“. |
| 5b | Quellen Lafferty/Su | URL nur aus abgerufener Fundstelle; Neurocomputing-DOI von Su **nicht** eingetragen (nicht bestätigt). | Test; NLP-QC jetzt source_validity PASS. |
| 5c | Veralteter PR-Titel, v5-Abnahmeaufforderung | PR-Titel aktualisiert; NEXT_ACTION.json bereinigt. | – |

## 3. Prüfung der Challenge-Ziele (fachliche Gültigkeit und Aussagekraft)

Bewertung durch den Autor. **Bitte gegenprüfen.**

| Labor | Challenge | Fachlich gültig? | Kognitive Aussagekraft / Einschränkung |
|---|---|---|---|
| Folgen | g-minN | ja (exakter Randfall 697/698) | gut: strenge Ungleichung |
| Folgen | g-noN | ja (Unmöglichkeit mit Begründung) | gut: Verneinung der Definition |
| Folgen | g-fast | ja | **Simulation** – zeigt quadratische Konvergenz numerisch, beweist sie nicht (Beweis steht in AN2) |
| Folgen | g-contr | ja (Zertifikat) | gut: trennt Simulation, Indiz und Beweis |
| Folgen | g-xinv | ja | gut: trennt Lipschitz-Schranke von Invarianz |
| Runden | w-major | ja (Modellrahmen) | mittel: Parameterexploration; Modellannahmen sichtbar |
| Runden | w-cap | ja | mittel |
| Runden | w-fund | ja | gut: Carry-Gleichung |
| Runden | w-imp | ja (Monotonie-Argument) | gut |
| NLP Attention | c-spot, c-uniform, c-target, c-impossible, c-order | ja | gut |
| NLP Attention | c-sat | ja | **Messung** im Zufallsexperiment (Seed 11) – Indiz für Satz 3, kein Beweis |
| NLP CRF | k-soft, k-sure, k-mm, k-imp | ja | gut |
| NLP BiRNN | n-imp, n-far, n-sat | ja | gut |
| NLP Spannen | f-half, f-prec | ja | gut |
| NLP Spannen | f-macro | ja | **schwach:** verlangt Änderung des Golds – fachlich zulässig als Gedankenexperiment, aber missverständlich; Überarbeitung empfohlen |

## 4. Was Sie bewerten (bitte je 0–4)

1. Beweissicherheit im Analysis-Labor: Ist die Trennung von Simulation, Indiz und Beweis fachlich sauber und didaktisch wirksam?
2. Korrektheit der Zertifikatslemmata (Monotonie-Argumente für cos, 1/(3+x), √(3+2x), Heron, x+1/x).
3. Quellenauswahl und -einordnung (Lebl, YC-Leitfaden, HTGF, Kerr/Nanda/Rhodes-Kropf, Kaplan/Strömberg nur Abstract).
4. Der Recherchepfad: Ist Bedarf → Integration nachvollziehbar und ausreichend selbstständig?
5. Originelle Beispiele (E1, E2, X1, X2, X4) und Pilotaufgaben (AN1–4, EN1–5).
6. Labore Analysis/ENT: Experimentiercharakter, Rückmeldung, UX.
7. Tutor: nach Durchführung der Protokolle (Bögen unter `docs/cross_domain/tutor_tests/results/`).
8. QC-Ehrlichkeit: Sind die Dimensionen jetzt aussagekräftig?

## 5. Nicht geprüft / offen

- Keine maschinelle Beweisprüfung; `proof_correctness` bleibt NOT_VERIFIED.
- Keine echte ChatGPT-Sitzung.
- ENT-Lücke `formen` (Kapitalformen) ohne geprüfte Ergänzungsquelle.
- NLP-Abdeckung beruht auf den Belegstellen des Lehrbuchs (Zuordnung durch Autor), nicht auf neuen KC-genauen Prüfungen.
- Anki, Lehrbuch, Arbeitsbuch, Musterlösungen und Probeklausuren: unverändert mangelhaft laut v5-Bewertung; nicht Teil dieser Runde.
