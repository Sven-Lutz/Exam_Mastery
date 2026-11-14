# Wissenschaftliche Grundlage – Knowledge & Pedagogy Base KB-1.0.0

Stand 10.11.2026. Phase 1 des Auftrags „Research-Driven Academic Excellence“: lernwissenschaftliche Basis.
Fachlehrbücher für einzelne Kurse, Book Design und die Überarbeitung der Lernprodukte folgen in späteren Phasen.

## Was entstanden ist

| Datei | Inhalt |
|---|---|
| `exam_mastery/knowledge/sources.json` | 54 Quellen mit DOI/ISBN, Studiendesign (`kind`) und tatsächlichem Lesestand (`access`) |
| `exam_mastery/knowledge/principles.json` | 17 Prinzipien, 52 Aussagen, je Aussage Quellen, Evidenzbasis, Bedingungen, Grenzen, Widersprüche, Engine-Regeln, Fachanpassungen |
| `exam_mastery/knowledge/specs.json` | 7 wiederverwendbare Spezifikationen: Worked-Example-Fading, Fehlertaxonomie, Tutor-Hinweisstufen, Aufgabenschema, Klausur-Blueprint, Anki-Karte, Visualisierung |
| `exam_mastery/knowledge/verification.json` | Ergebnis der maschinellen Quellenprüfung |
| `exam_mastery/knowledge/__init__.py` | Laden, Integritätsprüfung, kompakter Regelauszug je Produkt, Fingerprint, deterministische Aufgaben- und Klausurprüfung |
| `exam_mastery/knowledge/audit.py` | Audit einer veröffentlichten Lernumgebung gegen die KB-Regeln |
| `scripts/verify_sources.py` | Crossref-/OpenAlex-/OpenLibrary-Prüfung mit inhaltsadressiertem Cache (`knowledge/cache`, offline wiederholbar) |
| `tests/test_knowledge_base.py` | 12 Tests inkl. Negativfällen |

CLI: `exam-mastery kb validate | summary | context <produkt> [--subject <fach>] | spec <id>`.

## Wie geprüft wurde – und wie nicht

1. **Bibliografie:** Alle 54 DOIs/ISBNs wurden maschinell gegen Crossref bzw. OpenLibrary aufgelöst; Titel und Jahr stimmen (54/54).
2. **Aussagen:** Für 40 Quellen liegt ein Abstract vor (Crossref oder OpenAlex). 36 Aussagen sind `abstract_checked`: Jede
   zitierte Zahl oder Kernformulierung steht als wörtlicher Ausschnitt in `abstract_evidence` und wird bei jedem Lauf
   gegen das gespeicherte Abstract verglichen (48/48 gefunden).
3. **Nicht geprüft:** 16 Aussagen sind `metadata_only` – nur die Bibliografie ist verifiziert, die Aussage beruht auf
   Fachkenntnis und muss am Volltext geprüft werden. Darunter Barbieri 2023 und Bisra 2018 (Effektgrößen bewusst
   nicht übernommen), Dunlosky 2013 (Nutzenstufen), Hattie & Timperley 2007, Rohrer & Taylor 2007, Pashler 2008.
4. **Kein Volltext** wurde für diese Phase systematisch gelesen. Methodische Beurteilungen (Studienqualität,
   Publikationsbias, Moderatoren) stützen sich daher auf das, was die Abstracts berichten. Das ist eine bewusste Grenze,
   kein Versehen; der Validator lässt keine Abstract-Belege aus Quellen ohne gespeichertes Abstract zu.

## Ergebnisse nach Evidenzstatus

- **EMPIRICAL_STRONG:** Abrufübung (Roediger & Karpicke 2006; Rowland 2014; Adesope 2017; Pan & Rickard 2018: Transfer d = 0.40),
  verteiltes Üben (Cepeda 2006/2008: optimaler Abstand 20–40 % bei 1 Woche, 5–10 % bei 1 Jahr Behaltensintervall).
- **EMPIRICAL_CONDITIONAL:** Interleaving (nur bei ähnlichen Kategorien; negativ bei Sachtexten, Brunmair & Richter 2019),
  Worked Examples + Fading (früh ja, später Problemlösen; Expertise Reversal), Productive Failure (g = 0.36, aber nicht
  bei jüngeren Lernenden/domänenübergreifenden Fertigkeiten), Feedback (d = 0.41 bzw. 0.48, über ein Drittel der
  Interventionen schadet), Multimedia-Prinzipien, ITS (d = 0.76 vs. menschliche Tutoren 0.79; Median 0.66 SD, stark
  testabhängig), generative KI (Bastani 2025: −17 % ohne Guardrails; Kestin 2025: Vorteil bei pädagogischem Design),
  Vorhersage/Hyperkorrektur/Simulationslernen.
- **THEORETICAL_MODEL:** Cognitive Load Theory, Transfer-Taxonomie, Constructive Alignment, populärwissenschaftliche Synthesen (nur Einordnung). ICAP und KLI sind als Teilaussagen ausdrücklich als Hypothese bzw. Rahmenmodell gekennzeichnet.
- **REJECTED:** Lernstile/Meshing (Pashler 2008).
- **DESIGN_HYPOTHESIS:** alle sieben Spezifikationen. Ihre Bausteine sind belegt, die konkrete Zusammensetzung nicht.

Widersprüche werden ausdrücklich geführt (Kirschner/Sweller vs. Kapur/Sinha; Bastani vs. Kestin) und in den
Spezifikationen aufgelöst, nicht verschwiegen.

## Was die Engine jetzt anders macht

- Agenten erhalten je Produkt nur den passenden Regelauszug (`kb context`, ≤ 6 000 Zeichen) statt die Didaktik pro Kurs
  neu herzuleiten. Der Auszug trägt den KB-Fingerprint; jeder Kapitel-Publish-Bericht speichert ihn
  (`knowledge_base.fingerprint`). Ändert sich eine Regel, lassen sich betroffene Artefakte gezielt nachprüfen.
- Aufgaben und Probeklausuren sind deterministisch prüfbar (`check_item`, `check_item_set`,
  `check_exam_against_blueprint`): Rubriksummen, Transferdimension, Aufgaben, die sich nur in Zahlen unterscheiden,
  Punkte je Kompetenz gegen Blueprint (±10 %), Bearbeitungszeit.
- Das Audit macht Lücken bestehender Kurse sichtbar.

## Erster Befund an echtem Material: Business Planning v8

`python -m exam_mastery.knowledge.audit output/E2E_Agent_Kapitel07_Business_Planning_v8/Lernumgebung`:
0 kritisch, 3 schwer, 8 leicht.

- Schwer: 19 von 26 Aufgaben sind EXPLAIN (Operator-Monokultur); Probeklausur ohne Blueprint; keine Bearbeitungszeiten.
- Leicht: Transferaufgaben ohne deklarierte Transferdimension; drei doppelte Kompetenzbezeichnungen; eine Ja/Nein-Anki-Karte;
  Lab-Vorhersagen ohne Sicherheitsangabe.
- Info: Die Probeklausur deckt 11 von 36 Kompetenzen ab.

Funding v3 liegt im älteren Format ohne `Lernumgebung/course.json` und ist mit diesem Audit nicht prüfbar.
Das Audit sagt nichts über fachliche Richtigkeit oder Lernwirksamkeit.

## Offen für die nächsten Phasen

- Volltextprüfung der `metadata_only`-Aussagen (vor allem Effektgrößen der Meta-Analysen zu Worked Examples und Selbsterklärung).
- Fachliteratur je Kurs (Standardwerke für Entrepreneurship/Finance zuerst), mit eigener Quellenprovenienz und Lizenzprüfung.
- Recherche zu OER und Open-Source-Visualisierungssoftware (in dieser Phase nicht durchgeführt).
- Anwendung der Spezifikationen auf Business Planning und Funding; Book-Design-System.
- Unabhängige fachdidaktische Begutachtung der KB (bisher nur durch das Modell erstellt).
- Keine empirische Prüfung der Lernwirksamkeit von Exam Mastery.

## KB-1.1.0 (10.11.2026): Volltextprüfung und Korrekturen

Gelesen am Volltext (Fundstelle je Aussage in `fulltext_evidence`): Rowland 2014, Brunmair & Richter 2019 (Autorenmanuskript),
Kalyuga 2007, Kluger & DeNisi 1996, Wisniewski et al. 2020, Bastani et al. 2025 (Autoren-Preprint), Kestin et al. 2025.
Nicht zugänglich (Paywall/Blockade): Sinha & Kapur 2021, Adesope 2017, VanLehn 2011, Kulik & Fletcher 2016, Cepeda 2008,
Butterfield & Metcalfe 2001, Dunlosky 2013, Pashler 2008, Hattie & Timperley 2007, Rohrer & Taylor 2007, Barbieri 2023,
Bisra 2018, Renkl 2003 – dort bleibt die Basis unverändert.

Wesentliche Korrekturen übergeneralisierter Regeln:
- **Worked Examples:** Expertise Reversal ist stark (d = 1.20 Novizen vs. −0.36 Fortgeschrittene; Ausblendtempo 1.30 vs. −0.47).
  Ein vollständiges Beispiel ist daher nicht für alle Pflicht; Einstieg nach Erste-Schritt-Diagnose (adaptive Wahl d = 0.46).
- **Retrieval:** Abruf mit Hinweisreiz wirkt stärker (g = 0.61) als freier Abruf oder Wiedererkennen (je 0.29); ohne Feedback und
  bei ≤ 50 % Erstabruf kein Effekt (0.03).
- **Interleaving:** Mathematik g = 0.34, Sachtexte nicht signifikant, Wortlisten negativ (−0.39).
- **Feedback:** Bei hoher Aufgabenkomplexität d ≈ 0.03; Lösung im Feedback 0.43 vs. 0.25; Lob 0.09. Für komplexe Aufgaben
  Teilschritt-Feedback.
- **KI-Tutoring:** Bastani: ungeschützter Zugang −17 % in der späteren Prüfung, Tutor mit Schutz neutral (kein Vorteil);
  Kestin: Vorteil nur im unmittelbaren Nachtest bei Erstbegegnung und expertengeschriebenen Prompts. Die Engine behauptet
  nur Schadensvermeidung.

Fachliteratur Entrepreneurship: `exam_mastery/knowledge/subject/entrepreneurship.json` (22 Quellen). Zwei DOIs aus der
eigenen Vorrecherche waren falsch und wurden korrigiert (Delmar & Shane: 10.1002/smj.349; Richards & Laughlin: 10.2307/3665310).
Effektgrößen der Meta-Analysen Brinckmann 2010 und Read 2009 sind nicht übernommen (nur Abstract zugänglich).
