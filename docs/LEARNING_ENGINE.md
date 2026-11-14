# Learning Engine (v0.18.0-preview)

Kompetenzorientierte Lernsteuerung statt fester Seitenabfolge. Deterministisch, offline, ohne Modellaufruf.
Zyklus: **Diagnose → gezielte Erklärung oder Lösungsbeispiel → eigenständige Anwendung → Feedback → Transfer → spätere Prüfung.**

## Bausteine (`exam_mastery/learning/`)
| Modul | Aufgabe |
|---|---|
| `expr.py` | geschlossener Ausdrucksparser (kein `eval`), randomisierter Identitätstest (12 Punkte, gleicher Zufallsgenerator wie im Browser), exakter sympy-Vergleich für Tests |
| `diagnose.py` | Diagnoseobjekt `em-diagnosis-v1`; Ebenen numeric (L1), expression (L2), steps (L3), choice/constraints (L4), open (L5 → `UNVERIFIED`) |
| `policy.py` | Regeln R0, RA, RB, RC1, RC2, RU, RL5, RP, RF, RD, RE; Entscheidung `em-decision-v1` mit Beobachtung, Regel, Begründung, Unsicherheit |
| `tracks.py` | drei Lernstrecken (`em-track-v1`), alle Sollwerte und Fehlerwerte aus `labs/models.py` berechnet; `validate()` diagnostiziert jede Musterantwort und jeden Fehlerwert neu |
| `render.py` | Workbench-Seite je Lernstrecke (CSP mit Hash, keine Netzwerkzugriffe) |
| `tutor.py` | Tutor-Kontext → Markdown-Brief für Claude Code |
| `anki_bridge.py` | Wiederholungskarten über `anki_v2.build_deck`, stabile GUIDs, Schlagwörter `em::fehler::<kategorie>` |
| `evaluation.py` | Parallelformen, Zuweisung, Analyseplan – keine Daten |
| `templates/em_tutor.js/.css` | Browser-Spiegel von Diagnose und Policy (Paritätstests) und die Workbench-Oberfläche |

## Kompetenzmodell
Jede Lernstrecke deklariert ihre Kompetenzen mit Typ (`prerequisite`, `conceptual`, `procedural`, `derivation`,
`argument`, `transfer`). Bestehende IDs bleiben (`ml/backpropagation`, `kc-d5d3fd65634ab3`, `math/inscribed-rectangle` …);
Voraussetzungen ohne ID bekommen `prereq/…`. Jede Aufgabe verweist auf genau eine Kompetenz; Fehlerkategorien verweisen auf
Lösungsbeispiele/Kontraste; Validierung schlägt fehl, wenn ein Verweis ins Leere geht. Weil alle Zahlen beim Build aus dem
Modell entstehen, aktualisiert eine Korrektur am Modell oder an einer Kompetenz alle abhängigen Aufgaben beim nächsten Build.

## Was deterministisch, was agentisch ist
Deterministisch: Diagnose L1–L4, Auswahl der nächsten Aufgabe, Visualisierungsfokus, Status, Anki-Export, Publishing, Export/Import.
Agentisch (nur auf ausdrücklichen Aufruf): Rückmeldung zu Freitext, offene Rückfragen, neue Aufgaben über die Bibliothek hinaus.

## Diagnose: was erkannt wird – und was nicht
Erkannt: Vorzeichen, Größenordnung/Einheit, Rundung, konstanter Faktor, algebraisch äquivalente Umformungen, alle in den
Fehlerbibliotheken hinterlegten Muster (z. B. fehlender Faktor x₁, fehlende Aktivierungsableitung, falscher Pfad,
Endsaldo statt Tiefpunkt, Periodenwert statt kumuliert, fehlende Voraussetzung „gleich lang“), erster falscher Rechenschritt.
Nicht erkannt: Ursachen außerhalb der Bibliothek (→ `unclassified`, kein Raten), Qualität freier Begründungen (→ `UNVERIFIED`),
Ausdrücke mit Funktionen (exp, tanh) im Eingabefeld, Fälle, in denen ein Fehlerwert zufällig mit anderem Denkweg entsteht
(Kategorie bleibt Hypothese und wird so formuliert).

## Bewusst nicht gebaut
Bayesian Knowledge Tracing (keine kalibrierten Parameter), eigener Spaced-Repetition-Scheduler (Anki), Live-Verbindung
Browser → Agent (bräuchte lokalen Server oder Native Messaging; Sicherheits- und Datenschutzrisiko ohne Lernnutzen),
MathLive (≈ 800 KB, Symbolleiste + lesbare Vorschau reichen für die Bibliotheksausdrücke), JSXGraph (eigene SVG-Szenen
decken die drei Fälle ab), jsPsych (erst bei einer echten Studie), OATutor-Code (übernommen nur die Konzepte: gestufte
Hilfen, Aufgaben mit Fehlerbibliothek, Skill-Zuordnung je Schritt; keine Firebase-Abhängigkeit).
