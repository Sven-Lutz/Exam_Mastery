# Exam Mastery — Pre-registered Blind Generalization Protocol v1.0
**Datum:** 2026-10-30  
**Status:** Evaluationsvertrag vor Auswahl der unbekannten Vorlesung; keine behauptete Implementierung oder bestandene Evaluation.

## 1. Fragestellung
Kann Exam Mastery ein zuvor im Entwicklungsprozess nicht verwendetes Hochschulmodul anhand seiner Materialien **ohne manuelle fachbezogene Konfigurationsänderungen** korrekt analysieren und für dessen spezifische Ziele hochwertige, integrierte Lernprodukte erzeugen? Erzeugen diese Produkte einen nachweisbaren Mehrwert gegenüber einem starken Single-Agent-Baseline-Workflow?

Ein einzelner bestandener Test begründet keine Universalitätsgarantie; weitere unbekannte Fachfamilien sind erforderlich.

## 2. Vorab festzulegen und einzufrieren
1. Engine-Commit/Tag, Schemas, Prompts, Agentenverträge, Skills, Renderer, Testskripte, Abhängigkeitsversionen und erlaubte Toolzugriffe.
2. Modellnamen/-versionen, Ressourcenbudget und maximale autonome Iterationen.
3. Produktspezifikation und Blocker-Kriterien dieses Protokolls.
4. Baseline-Prompt und gleiche Quellenbasis; Budgetunterschiede ausweisen.
5. Unabhängige Evaluationsinstanz und Aufgabe(n), die nicht Teil der Produktion sind.

Die derzeitige Starterversion v0.1 erfüllt diese Einfriervoraussetzungen noch nicht als integrierter Produktworkflow.

## 3. Geheimhaltung und Datentrennung
- **Vor dem Freeze**: Der Nutzer gibt weder Kursname noch Fachfamilie, Dozierende, Quellen, Altklausuren oder Aufgaben aus dem Holdout preis. Auch nicht indirekt über Vorab-Screenshots oder Testdaten.
- **Erst nach Freeze**: Originalmaterialien gehen in einen isolierten Run. Der Course Architect bekommt lediglich die Dateien und allgemeine Produkt-/Qualitätsanforderungen. Keine nachträglichen Fachhinweise.
- Die Evaluationsfragen/Gold-Lösungen werden separat gehalten und sind für Produktionsagenten nicht zugänglich.
- Manuelle Promptänderungen, extern nachgerüstete Fach-Skills oder menschliche inhaltliche Reparaturen nach Sichtung der Holdout-Quellen zählen als **assistierte Adaption** und nicht als unveränderter Systemlauf. Automatische Skill-Auswahl, Skill-Synthese und interne Revisionen **sind erlaubt**, sofern sie ausdrücklich Teil der vorab eingefrorenen Engine sind, vollständig protokolliert werden und keine versteckten Gold-Lösungen auswerten. Das sind legitime Formen von Test-Time-Adaptation des Systems, nicht nachträgliches menschliches Tuning.
- Eine Vorlesung kann dem Modell bereits aus dem Pretraining bekannt sein. 'Unbekannt' bedeutet zunächst *unseen during system design*. Für einen strengeren Test sind unveröffentlichte Materialien und neue, privat erstellte Aufgaben erforderlich.

## 4. Open-world Routing, kein geschlossener Fächerkatalog
Keine Abhängigkeit von einer festen Auswahl `Law | Math | Medicine | CS`. Stattdessen werden pro Kompetenz ermittelt:
- Knowledge operations: z. B. beweisen, berechnen, auslegen, subsumieren, interpretieren, experimentieren, diagnostizieren, entwerfen, argumentieren.
- Evidenzart und Aktualität: Gesetze, Rechtsprechung, empirische Studien, Definitionen, Beweise, Code, Modelle, Primärdaten.
- Kompetenzniveau, Vorwissen, Klausurformat, didaktisches Risiko, Fehlerkosten, erforderliche Toolprüfungen.
- Lernprodukt-Eignung: Buch, Aufgaben, Karteikarten, interaktive Übung/Lab, Tutor; mit explizitem `NOT_NEEDED` und Begründung.
- Nicht erfasste fachliche Anforderungen lösen einen protokollierten Capability-Gap oder einen begründeten `NEEDS_REVIEW`-Status aus; niemals eine stillschweigende Zuordnung zu einem unpassenden Skill.

**Law** ist eine First-Class-Fähigkeitsfamilie (Normstand, Hierarchie, Auslegung, Fall/Prüfungsschema, Subsumtion, Gegenansichten). Sie ist **kein** abgeschlossener Sonderpfad; fachübergreifende Kombinationen sind erlaubt.

## 5. Pflichtausgaben des Testlaufs
1. **Course Blueprint**: Ziele, Quelleninventar, fehlende Materialien, fachliche Operationen, Lern-/Prüfungsprofil und aktivierte Skills.
2. **Learning Knowledge Model**: Quellenbezüge, zentrale Claims, Voraussetzungen, Kompetenzen, Fehlkonzepte und Objekt-IDs.
3. **Lehrprodukt**: eigenständige, hochwertige Erklärungen mit fachlich passenden Beispielen und Visualisierungen.
4. **Assessment**: Aufgabenprogression, vollständige Lösungen, Bewertungskriterien, unabhängige Transferaufgabe.
5. **Anki (falls passend)**: geprüfter Karteninhalt mit Anki-tauglichen HTML/CSS-Templates; stabile Note-Identitäten und Clienttests.
6. **Interaktion (falls sinnvoll)**: interaktives Lab/Fallwerkstatt/Simulation mit valider fachlicher Logik, Feedback und Tests. Keine Pflicht-Animation ohne Lernwert.
7. **Editorial Design**: hochwertiges, fachgemäß gesetztes Buch/PDF und verifizierter Web-Output.
8. **Audit**: tatsächliche Quellen- und Inhaltsprüfung, Kompetenz-Assessment-Abgleich, technische Resultate, dokumentierte Grenzen, klares GO/NO-GO.

## 6. Bewertungsdesign
**A. Prozess/Generalisierung:** Keine kursbezogenen Hardcodes oder Handreparaturen, korrekte Erkennung von Wissensoperationen, dokumentierte Skill-Aktivierungen, reproduzierbarer Lauf.

**B. Fachlichkeit/Provenienz:** Quellen-Claim-Audit, Nachrechnung und formale/rechtliche/empirische Verifikation; aktuelle Aussagen nicht unbesehen aus alten Unterlagen übernehmen; Unsicherheit explizit.

**C. Pädagogik/Assessment:** unabhängige Rubric, angemessene Lehrprogression, vollständige Abdeckung *deklarierter* Kompetenzen durch passende Aufgaben, neue Transferaufgaben.

**D. Produkte/UX:** Seitenweises PDF-Review; Anki: echte Clienttests, Reimport, mobile Darstellung; Web: semantische Tests, Grenzwerte, Browserbreiten, Accessibility, Ausfallpfade.

**E. Baseline-Vergleich:** Starke Standard-KI mit gleichen Inputs und dokumentiertem Budget. Anonyme, randomisierte Paarbewertung durch unabhängige Experten; zusätzlich sachliche deterministische Checks und selbstständig gelöste unbekannte Aufgaben.

**Harte NO-GO-Blocker:** nachgewiesener wesentlicher Fachfehler, wesentliche unbelegte Kernbehauptung, falsche behauptete Kompetenzabdeckung, funktionslose geforderte Interaktion, unbrauchbarer Anki-Import, fehlender/irreführender Audit oder unzulässige Holdout-Adaption. Fehlende essentielle Quellen können zum ehrlichen `NEEDS_INPUT` statt erfundener Fertigstellung führen.

## 7. Auswertung und Interpretation
- Ein erfolgreiches Produkt zeigt **Generalisation auf diese Vorlesung**, nicht Universalisierung auf alle Fächer.
- Fehlversuch: Fehleranalyse, neuer Engine-Release; dieselbe Vorlesung gilt ab dann als Entwicklungs-/Regressionstest, nicht mehr als unberührter Blind-Holdout.
- Danach wiederholte Tests über mehrere *neue*, kontrastierende Fächer, unterschiedliche Quellenformate und hybride Fachkombinationen.
- `RELEASED` bedeutet Produktfreigabe, nicht empirisch bewiesene Notenverbesserung. Der gesonderte Status `LEARNING_VALIDATED` erfordert belastbare Lernleistungsdaten.

## 8. Unmittelbare nächste Entwicklungsschritte (vor Reveal)
1. Vorhandene NLP-Labs, Audits, Steuer-Lehrmaterialien und Agentenverträge sichern und als **Entwicklungs-/Regressionstests** markieren.
2. Universellen Intake mit multimodaler Quellenprüfung und offenem Knowledge-Operation-Routing implementieren.
3. Eine vertikale Produktionskette für Lehrbuch, Assessment, Anki und bedarfsgerechtes interaktives Produkt samt getrennten Renderern und QA implementieren.
4. Einen vollständigen End-to-End-Smoketest mit bekannten *Entwicklungsfächern* ausführen.
5. Version, Prompt-/Skill-Stand und Evaluation einfrieren. Erst danach Kurs-Holdout enthüllen.

**Forschungskontext:** Benchmarkkontamination und dynamische Holdout-Evaluation werden behandelt in Chen et al. (EMNLP 2025, https://aclanthology.org/2025.emnlp-main.511/) und Princeton SAGE, Emerging Trends in AI Agent Evaluation (https://sage.cs.princeton.edu/trends/). Diese Literatur stützt die Testmethodik, nicht eine Behauptung von Exam-Mastery-Überlegenheit.
