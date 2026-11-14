# Fähigkeiten und bewertete Werkzeuge (Stand v0.14.0-preview)

## Fähigkeitsmatrix (nur geprüfte Dateien und Tests)

| Fähigkeit | Vorhanden | Integriert | Getestet | Wiederverwendbar | Beleg |
|---|---|---|---|---|---|
| Vorlesungsanalyse (Inventar, Elemente, Kapitelplan, Sessions) | ja | ja | ja | ja | `fidelity.py`, `curriculum.py`, `tests/test_b6_3_*` |
| Bildauswertung durch den Agenten | ja | ja | ja | ja | `visual_evidence.py` (`visuals`, `--all`) |
| Lehrbuch, Arbeitsbuch, Lösungen, Klausur (PDF/HTML) | ja | ja | ja | ja | `typeset.py`, `book_model.py` |
| Qualitätsregeln DR-1.0/1.1, Zahlenprüfung | ja | ja | ja | ja | `didactic_rules.py`, `semantic_checks.py`, `numeric_checks.py` |
| Anki v2 mit stabilen Identitäten | ja | ja | ja | ja | `anki_v2.py`, Update-Test mit Lernstand |
| Interaktive Labs | ja (Altpfad: eine Formel, Quiz) | **neu: Kapitelpfad** | ja (Browser) | ja | `labs/*`, `templates/em_labs.*`, `tests/test_b13_labs.py` |
| Numerische Labs (Cashflow, Netz, Risikomatrix) | **neu** | ja | ja | ja | `labs/models.py` |
| Aufgaben mit deterministischem Feedback | **neu** in Labs | ja | ja | ja | `task()` in `em_labs.js` |
| Adaptives Feedback (gestufte Hinweise, Fehlerdiagnose) | **neu** | ja (Labs) | ja | ja | Lab-Aufgaben |
| Tutor-Modus | Protokoll vorhanden (`exam-mastery-studio/docs/TUTOR_PROTOCOL.md`) | **im Skill** (Abschnitt 9) | nein (Gesprächsführung, nicht automatisierbar) | ja | `SKILL.md` |
| Mentoring | Statusvokabular vorhanden | Labs speichern beobachtete Versuche lokal | teilweise (Browser-Test des Status) | ja | `EM.store`, Lernumgebung |
| Lernanalytik | nein | – | – | – | bewusst nicht: keine Telemetrie, kein Mastery-Score |

## Bewertete Open-Source-Werkzeuge

Lizenzangaben stammen aus dem Wissensstand des Agenten. Sie wurden in dieser Sitzung **nicht** an den Projektseiten
verifiziert und sind vor jeder Einbindung zu prüfen.

| Werkzeug | Könnte übernehmen | Lizenz (ungeprüft) | Offline | Entscheidung |
|---|---|---|---|---|
| JSXGraph | interaktive Geometrie/Funktionsgraphen | LGPL/MIT (dual) | ja, Bündel | **später** für Analysis-/Geometrie-Labs; für die drei Referenz-Labs reichten eigene SVG-Diagramme |
| MathLive | Formeleingabe | MIT | ja | **später**, wenn Aufgaben algebraische Eingaben prüfen; heute nur Zahlen |
| Mathigon/Polypad | Erkundungsumgebungen | teils proprietär | eingeschränkt | verworfen: Lizenz und Hosting |
| GeoGebra | Geometrie, Rechner | nicht-kommerziell beschränkt | Einbettung meist online | verworfen: Lizenz und Online-Abhängigkeit |
| H5P | interaktive Inhaltstypen | MIT | braucht Host (LMS/WordPress) | verworfen: Server/LMS-Pflicht |
| Cytoscape.js | Kompetenz-/Graphvisualisierung | MIT | ja | **später** für den Kompetenzgraphen |
| Mermaid | Diagramme aus Text | MIT | ja | nicht nötig: Diagramme entstehen deterministisch als SVG |
| Pyodide | Python im Browser | MPL-2.0 | ja, aber ~10 MB+ | verworfen für jetzt: Speicher/Ladezeit auf 8 GB-Geräten |
| TensorFlow Playground | NN-Visualisierung | Apache-2.0 | ja | als Vorbild geprüft; eigenes 2-2-1-Netz, weil jeder Rechenschritt sichtbar sein muss |
| NumPy | Referenzrechnung | BSD | ja | **genutzt** in Tests (unabhängige Backprop-Referenz) |
| SymPy | symbolische Äquivalenz | BSD | ja | **später** für algebraische Antworten |

Gewählt ist die kleinste Menge: Vanilla-JS ohne Abhängigkeiten zur Laufzeit, NumPy nur zum Prüfen.
