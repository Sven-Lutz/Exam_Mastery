# Ressourceneffizienz: gemessene Werte (Kapitel 7, Agent-Provider)

Gemessen am 09.–10.11.2026 auf dem Entwicklungsrechner. Tokens werden beim Agent-Provider nicht gezählt; Tokenwerte sind
daher **unbekannt**. Angegeben ist die Promptgröße in Zeichen.

| Lauf | Modell-/Agent-Aufrufe | Promptvolumen | Neu erzeugte Prompts | Laufzeit der Engine |
|---|---|---|---|---|
| E2E v1, erste Produktion | 6 (inkl. 1 Überarbeitung) | 1,338,474 Zeichen | 6 | nicht gemessen |
| E2E v2, korrigierte Produktion | 5 (keine Überarbeitung nötig) | 1,170,731 Zeichen | 5 | nicht gemessen |
| Neuerzeugung nach Engine-Korrekturen (v1: 2×, v2: 4×) | **0** | 0 | 0 je Lauf | 28 s je Kapitel (v2, gemessen) |
| 3 Referenz-Labs bauen | **0** | 0 | – | unter 0,01 s; je Lab rund 50 KB HTML |

Wiederverwendung: Der Agent-Provider legt jede Antwort unter dem Hash ihres Prompts ab. Ist der Prompt unverändert,
wird die Antwort ohne neue Modellarbeit wiederverwendet. So entstanden nach sechs Engine-Korrekturen alle Produkte
neu – PDFs, Anki, Labs, Dossier –, ohne einen einzigen neuen Aufruf.

## Ausführungsform je Schritt

| Schritt | Ausführung |
|---|---|
| Inventar, Fingerprints, Änderungserkennung, Kapitelplan, Sessions | deterministisch (Python) |
| Bildvorsortierung für `visuals --all` | deterministisch (Fläche, Pfadanzahl, Logo-Wiederholung) |
| Bildinterpretation | Agent (Bildverständnis), danach deterministisch geprüft |
| Fachtext, Aufgaben, Lösungen, Karten, Lab-Daten | Agent (eine Antwort je Rolle) |
| Rechenprüfung, Zahlen gegen Quellen, Rubriksummen, Regeln DR-1.0/1.1 | deterministisch |
| Satz, PDF, Inhaltsverzeichnis, Links, Formeln (MathJax) | deterministisch |
| Labs: Modelle, erwartete Antworten, HTML, statische Abbildung | deterministisch (keine Modellausgabe als Code) |
| Anki-Export, Identität, Update-Delta | deterministisch |
| Semantische Prüfung, Risikoprüfung | Agent (Selbstprüfung; keine unabhängige Prüfung) |

Nicht gemessen: Rechenzeit der Erstproduktion (dominiert von der Agentenarbeit), Speicherbedarf im Spitzenwert.
