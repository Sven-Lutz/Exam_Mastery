# R0 — Vorschlag für ein nachvollziehbares Evidenzregister

Version 1, 26.11.2026. **Normativer Vorschlag zur Begutachtung, nicht implementiert oder bereits genehmigt.** Gilt als Arbeitsstandard für spätere Forschung nach Annahme; verändert weder KB-JSON noch Engine-Schemata. Kompatibel mit vorhandenen IDs; keine zweite unabhängige Knowledge Base. Herkunft und Änderungsvorschläge bleiben erhalten.

Begleitdokumente: [Audit](KB_GAP_AUDIT.md), [Suchprotokoll](SEARCH_PROTOCOL.md). Autor/Prüfer in R0: derselbe einzelne Codex-Agent. `independent_review` bleibt `pending`; Selbstkorrektur wird nicht als zweite unabhängige Stimme gezählt.

## 1. Warum mehrere Achsen notwendig sind

Ein DOI kann korrekt sein, während die Aussage falsch ist; ein Volltext kann gelesen, aber methodisch schwach sein. Eine experimentell gestützte Aussage kann für unsere Population indirekt sein; eine saubere Implementierung kann ohne Lernnutzen bleiben. Deshalb keine lineare Leiter, in der „IMPLEMENTED“ oder „fulltext“ automatisch einen höheren wissenschaftlichen Rang bedeutet.

| Achse | Zulässige Werte / Bedeutung |
|---|---|
| Identität | `unresolved`, `cache_match`, `primary_metadata_checked`, `version_reconciled`; jeweils Datum, Methode, Umfang |
| Textzugang | `metadata`, `abstract`, `fulltext_partial`, `fulltext_claim_review`; versioniert und mit tatsächlich gelesenen Abschnitten |
| Methodik | `not_assessed`, `provisional_single_reviewer`, `independently_reviewed`; Instrument/Version/Fundstellen separat |
| Inferenz | `descriptive`, `correlational`, `experimental_causal_within_scope`, `synthesis_mixed`, `theoretical`, `design_hypothesis` |
| Geltung | Population, Operation, Comparator, Setting, Unterstützung und Zeitpunkt als Felder; `conditional` keine Ausrede ohne Bedingungen |
| Aussageprüfung | `supported_within_scope`, `partially_supported`, `overstated`, `contradicted`, `unresolved`, `not_empirical` |
| Unsicherheit | Fehlende Daten, CI/Präzision, Bias, Inkonsistenz, Indirektheit, Versionsunsicherheit; nicht auf eine Zahl reduzieren |
| Produktbezug | `candidate`, `specified`, `code_inspected`, `behavior_tested`, `human_product_reviewed`, `learning_evaluated`; **separate Nachweise**, keine automatische Promotion |

„Empirisch gut gestützt“ ist ein begründetes Syntheseurteil über einen abgegrenzten Befund, nicht das Default-Etikett aller Regeln eines Prinzips. Lernstile-REJECTED bleibt eine Produktablehnung der unbelegten Meshing-Anwendung, kein Beweis, dass jedes Format für jede Person gleich wirksam wäre.

## 2. Entitäten und Pflichtfelder

`required` bedeutet: Wert **oder** explizites `unknown`/`not_applicable` mit Grund. Leere Strings sind kein Nachweis. Zahlen ohne Einheiten/Denominator sind unzulässig. Datum in ISO-8601; wenn Uhrzeit nicht aufgezeichnet, keine Uhrzeit erfinden.

### A. SourceRecord — bibliografische Identität und Zugriff

| Pflichtfeld | Inhalt / Regel |
|---|---|
| `source_id`, `study_family_id` | Vorhandene KB-ID weiterverwenden; Preprint/Artikel/Korrektur derselben Studie verknüpfen. |
| `citation` | Autoren, Titel, Jahr, Publikationsort, DOI/ISBN; Online-/Printjahr ggf. getrennt. |
| `source_type` | Primärstudie, Synthese, narrativer Review, Theorie, Instrument, technische Dokumentation, Produktwerbung. |
| `versions[]` | `version_id`, Datum, Status (Preprint/accepted/VoR/correction), dauerhafter Identifier. |
| `access_events[]` | URL, Zugangsdatum, Ergebnis (erreichbar/403/404/CAPTCHA/Timeout), tatsächlich gelesene Abschnitte, Reviewer. |
| `identity_check` | frisch/cache, Provider, Titel-/Autoren-/Jahresvergleich, Grenzen des Prüfers. |
| `rights` | Lizenz bekannt/unbekannt, öffentlich lesbar versus weiterverteilbar getrennt. Kein Download ins öffentliche Git ohne Rechte. |
| `integrity` | Korrektur-/Retraktionsprüfung mit Datum und Ergebnis oder `not_checked`; lokaler Hash nur bei vorhandener Datei, niemals erfunden. |

Ein gescheiterter Abruf überschreibt keinen früheren Zugriff; er ergänzt die Ereignishistorie. Öffentlich erreichbar bedeutet nicht Public Domain. Ein neuer Mirror erhöht nicht die Zahl unabhängiger Studien.

### B. StudyContrast — Design und konkrete Messung

| Pflichtfeld | Inhalt / Regel |
|---|---|
| `contrast_id`, `source_version_id`, `experiment_id` | Eindeutiger Arm-/Zeitpunktvergleich, nicht nur Paper-ID. |
| `design`, `allocation_unit`, `analysis_unit` | RCT/quasi/korrelativ/Modell etc.; Person, Klasse, Aufgabe; Abhängigkeiten markieren. |
| `population` | Rekrutierung, Alter/Bildung, Vorwissen, Sprache, Land, In-/Exklusion, N rekrutiert/randomisiert/analysiert separat. |
| `operation`, `material`, `setting` | Abruf, Diskrimination, Verfahren, Erklärung, Beweis, Diagnose, praktische Handlung etc.; keine bloßen Fächertags. |
| `intervention`, `comparator`, `dose` | Inhalt, Hilfe, Feedback, Zeit, Sequenz; aktive Kontrolle und Kontamination. |
| `outcome` | Instrument/Skala, selbstständig oder assistiert, unmittelbarer/verzögerter Test, Transferdimension, Testnähe zur Übung. |
| `estimate` | Metrik, Wert, Richtung, CI/SE, N/k, Analysemodell, adjustiert/unadjustiert; bei fehlendem Wert `unknown` und Grund. |
| `missingness`, `analysis` | Ausfälle, Ausschlüsse, ITT/per-protocol, Kovariaten, Clusterung, Multiplikität, Präregistrierung/Abweichungen. |
| `risk_of_bias` | Domänenurteile + Begründungen/Locator, benutztes Instrument oder ausdrücklich vorläufige qualitative Einschätzung. |
| `external_validity` | Zu welchen Zieloperationen/Populationen direkt, indirekt oder nicht übertragbar; begründete Grenzen. |

Meta-Analysen zusätzlich: Suche/Protokoll, Anzahl Studien/Stichproben/Effekte/Personen getrennt, überlappende Primärstudien, Effektabhängigkeit, Heterogenität, Moderator- versus Interventionsvergleich, Sensitivität, Publikationsbias. `k` niemals ohne Definition. Standardisierte Regressionskoeffizienten, Cohen-d, Hedges-g, relative Prozentänderung und Prozentpunkte sind verschiedene Größen.

### C. ClaimAssessment — Behauptung und Belegkante

| Pflichtfeld | Inhalt / Regel |
|---|---|
| `assessment_id`, `claim_id`, `baseline_commit` | Bestehenden Claim stabil referenzieren; Snapshot genau benennen. |
| `original_text_locator`, `proposed_text` | Keine stille Umformulierung; Original über ID/Pfad auffindbar, Vorschlag daneben. |
| `claim_kind`, `scope` | Deskriptiv, kausal, theoretisch oder normativ; genaue Population/Operation/Outcome-Bedingung. |
| `evidence_edges[]` | Source-Version und Contrast-ID, genaue Seite/Tabelle/Absatz; `supports`, `qualifies`, `contradicts` oder `context_only`. |
| `access_basis`, `appraisal_status` | Tatsächlicher Zugriff und methodischer Review unabhängig voneinander. |
| `verdict`, `reason` | Abgegrenztes Urteil, Unsicherheit und mögliche alternative Erklärung. |
| `counterevidence[]` | Null-/negative Befunde, abweichende Outcomes; falls nicht gefunden, Suchumfang statt behaupteter Abwesenheit. |
| `decision_impact`, `next_action` | Betroffene Regel/Produktentscheidung, Risiko, Priorität, benötigter Nachweis. |
| `review_history` | Autor, Datum, Selbstrevisionen, unabhängiger Reviewer oder pending, dokumentierter Dissens. |

Exakte Fundstelle muss claimtragend sein: „Results“ reicht bei Tabellenwerten nicht, wenn mehrere Modelle existieren. Kurze Paraphrase und Locator bevorzugen; keine langen geschützten Passagen. Ein Abstract-Zitat zum Gesamtmittelwert bestätigt nicht die methodischen Einzelheiten oder sämtliche Teilbehauptungen im selben Claim.

### D. DesignDecision und ImplementationEvidence — getrennte Objekte

| Objekt | Pflichtfelder |
|---|---|
| `DesignDecision` | ID, betroffene vorhandene Regel, ClaimAssessment-Refs, Zieloperation, Voraussetzungen, erwartete Handlung, Alternativen, Ableitungsbegründung, Abstention/Fallback, schädlicher Gegenfall, Validierungsplan, Status `design_hypothesis` bis eigener Nachweis. |
| `ImplementationEvidence` | Decision-ID, Repo/Commit/Pfad/Symbol, überprüfte Eigenschaft, Methode (Code gelesen/Test ausgeführt/Artefakt geprüft), exakter Befehl/Datum/Resultat falls ausgeführt, Grenzen, **kein** automatisch daraus abgeleitetes Lernoutcome. |
| `LearningEvaluation` | Vorabprotokoll, Design, Population, Zuteilung, Stichprobenbegründung, Instrumentvalidität, Assistance-/Delay-/Transferdefinition, blinde Bewertung, Analyse/Unsicherheit, Datenzugangs-/Ethikstatus; nicht vorhanden ⇒ `NOT_RUN`. |
| `HumanAcceptance` | Konkrete Release-ID, Datum, tatsächlicher menschlicher Reviewer, Kriterien/Ergebnis; historische Ablehnung unverändert, spätere Version getrennt. |

Ein technischer `PASS` kann neben `learning_evaluation=NOT_RUN` und `human_acceptance=HUMAN_REJECTED` stehen. Keine automatische Gleichsetzung. Forschung kann einen Produktvertrag kritisieren, aber nicht allein genehmigungspflichtige Produktziele oder historische Reviews umschreiben.

## 3. Ausgefülltes Beispiel aus R0

Illustrativer JSON-Datensatz, **kein neuer Parser oder Schema-Migrationscode**. Der Trace referenziert D2/T1 im Audit; Primärstudien der Meta-Analyse nicht vollständig nachgeprüft. Exakte extrahierte Zahlen stehen ausschließlich im Audit, um inkonsistente Duplikate zu vermeiden.

```json
{
  "assessment_id": "R0-20261126-rp2",
  "claim_id": "rp.2",
  "baseline_commit": "3fdbc7d01ee45ecaf33bc17be5f2b1295d14d115",
  "original_text_locator": "exam_mastery/knowledge/principles.json#rp.2",
  "source_id": "rowland2014",
  "source_version_id": "rowland2014-author-upload-article",
  "access": {
    "date": "2026-11-26",
    "level": "fulltext_claim_review",
    "url": "https://www.researchgate.net/publication/264988491_The_Effect_of_Testing_Versus_Restudy_on_Retention_A_Meta-Analytic_Review_of_the_Testing_Effect",
    "sections_read": ["Tables 1 and 2", "Categorical Moderator Analyses", "Initial test type", "Publication status"],
    "version_limit": "Author-uploaded article text; no new primary-study replication"
  },
  "inference": "synthesis_mixed",
  "verdict": "partially_supported",
  "appraisal_status": "provisional_single_reviewer",
  "proposed_text": "Retrieval benefits depend on exposure, feedback and target operation; the unadjusted cued/free-recall comparison is not a causal ranking of formats.",
  "evidence_edges": [
    {"locator": "Table 1", "relation": "supports", "detail": "Reported full-dataset subgroup values"},
    {"locator": "Table 2 and Initial test type discussion", "relation": "qualifies", "detail": "High-exposure sensitivity changes the format comparison"}
  ],
  "estimate_record": "KB_GAP_AUDIT.md / D2",
  "uncertainty": ["Moderator confounding", "Indirectness to proof construction", "Primary-study bias not fully reassessed"],
  "decision": {
    "existing_rule": "RP-R1",
    "status": "design_hypothesis",
    "recommendation": "Choose retrieval format by target operation; do not impose universal cued-recall superiority",
    "falsifier": "Under equal exposure and feedback, a different format yields better delayed unassisted target performance"
  },
  "implementation_evidence": {
    "locator": "exam_mastery/learning/policy.py:helped",
    "method": "code_inspected",
    "test_run": "not_run_in_R0",
    "limit": "Logged assistance is not a measurement of mental retrieval or external help"
  },
  "learning_evaluation": "NOT_RUN",
  "independent_review": "pending"
}
```

Zweiter Kontrasttyp: Für D10 muss das Register die relative Prüfungsänderung von der absoluten Differenz auf einer 0–1-Skala trennen. Ein Feld `harm_prevented=true` wäre unzulässig: Stattdessen Schätzwert/CI und fehlender Äquivalenznachweis. D11 benötigt eine eigene Preprint-Version; deren Lektüre darf keinen Zugriffseintrag für die veröffentlichte 2025-Version erzeugen.

## 4. Invarianten für die spätere Registerpflege

1. Jede der 52 bestehenden Claim-IDs besitzt genau einen initialen Audit-Eintrag; spätere Assessments versionieren, nicht überschreiben. Alle 55 Quellen bleiben erhalten, auch ohne direkten Claim-Verweis.
2. Jede Zahl hat Quelle, Version, Fundstelle, Metrik, Vergleich und Outcomezeitpunkt. Nicht vorhandene CI werden nicht erfunden; Null ist kein Ersatz für unbekannt.
3. `fulltext_claim_review` verlangt tatsächlich gelesene inhaltliche Abschnitte. Eine PDF-URL oder ein Metadaten-PASS genügt nicht.
4. Kausalität verlangt designspezifische Begründung; Meta-Regressionsmoderatoren bleiben zunächst Assoziationen. Theorien und Produktentscheidungen werden nicht durch Zitieren zu experimentellen Befunden.
5. Bei unabhängiger Reviewbehauptung muss ein anderer realer Reviewer dokumentiert sein. Zweite Antwort desselben Agenten genügt nicht; Dissens bleibt sichtbar.
6. Jeder technische Nachweis benennt die eng geprüfte Eigenschaft. `test_present`/`code_inspected` dürfen keinen ausgeführten Test vortäuschen. CI prüft keine unabhängige menschliche Abnahme.
7. Jede Entscheidung nennt Rückfall-/Abstentionsbedingungen: mangelndes Vorwissen, unzugänglicher Beleg, nicht diagnostizierbarer Fehler, ungeprüfte Transferoperation oder Sicherheitsgrenze.
8. Durchgestrichene/veraltete Behauptung erhält einen Supersedes-Link und Grund. Negative Evidenz wird nicht aus einem Register entfernt, um Konsens herzustellen.
9. Datenschutz: keine Namen, privaten Lernverläufe oder geschützten Kursdateien im öffentlichen Register. Zugangsmetadaten und eigenständige Paraphrasen genügen.
10. Laufzeitänderungen erst als gesonderter Engineeringauftrag nach wissenschaftlicher Entscheidung; dieser Sprint liefert ausschließlich Dokumente.

## 5. Reviewfragen und Übergabe

Ein unabhängiger Reviewer soll mindestens prüfen: Sind D2s Sensitivitätsgruppen korrekt interpretiert? Ist D7s Komplexitätsmoderator im richtigen Ausschlussdatensatz? Wurde D10s Zeitpunkt korrekt als sitzungsnah statt Langzeitbehalten dargestellt? Was ändert die finale D11-Version? Sind die Transferfälle wirklich von Abrufaufgaben unterschieden und fachlich korrekt? Welche Aussage ist nur aus einem Review statt einer experimentellen Primärarbeit belegt?

R1–R9 sollen dieses Schema zunächst an wenigen kontrastierenden Quellen testen und begründete Änderungen vorschlagen. Die priorisierte Arbeitsliste steht im Audit; **kein Workstream wird durch diese Übergabe gestartet**. Owner-/Fachreview und spätere Architektursynthese bleiben offen. Historisches HUMAN_REJECTED wird nicht durch den Abschluss des Forschungsdokuments aufgehoben.
