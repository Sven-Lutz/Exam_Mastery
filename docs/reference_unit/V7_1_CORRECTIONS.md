# v7.1 – Korrekturen nach dem unabhängigen v7-Audit (Issue #10, PR #3)

**Status**
- TECHNICAL_PASS: lokal 820 Tests bestanden, 6 übersprungen; GitHub-CI siehe PR.
- CONTENT_CORRECTNESS_REVIEW_REQUIRED · DIDACTIC_REVIEW_REQUIRED · PUBLISHING_REVIEW_REQUIRED.
- Keine Selbstfreigabe; PR #3 bleibt Draft.

| Audit-Befund | Korrektur | Nachweis |
|---|---|---|
| CI rot: 413 px bei 390-px-Viewport (`#learn/rnn` u. a.) | Ursache: v7-Regel `table.sym{display:table}` hob den Scrollschutz der bestehenden Orientierungstabelle auf; unter Linux-Schriften wurde sie zu breit. Tabellen werden unter 640 px wieder scrollbar und umbrechend. | Neue Tests: kein Dokument breiter als der Viewport bei 320 und 360 px auf 8 Seiten; v7-Layouttest zusätzlich bei 320/360 px; lokal von 320 bis 390 px ohne Überbreite. |
| W1–W4 charakterisieren die Softmax nicht | Ausdrücklicher Gegenbeispiel-Kasten (g = 1 + tanh, zentrierte Scores). **Satz 6.1\*** (Variationsprinzip) mit Existenz, Eindeutigkeit (strenge Konkavität), Innerer-Punkt-Argument, Lagrange-Bedingung, Exponentialform, Normierung und Optimalwert T·ln Z. Dazu Deutung der Temperatur, Grenzfälle (Gleichstand) und Sparsemax als Gegenstück. Belegt mit Blondel/Martins/Niculae 2020 (Gl. 6, Tab. 1) und Martins & Astudillo 2016. | `tests/test_v7_layout.py::V71Mathematics`: Gegenbeispiel; Variationsprinzip gegen 10 000 Zufallsverteilungen; Optimalwert = T·ln Z; Schranken max s ≤ T·ln Z ≤ max s + T·ln N. |
| Satz 6.2 zu weit gefasst | Gilt ausdrücklich für frei wählbare Scores. Neuer Kasten zur Erreichbarkeit mit fester Key-Matrix, s = Kq/√d_k (Bild von K plus Vielfache von 1), mit dem Gegenbeispiel gleicher Keys. Teil (c) präzisiert: „nur Darstellungen mit Nullgewicht“, inklusive des Falls affin abhängiger Values. | Test: Erreichbare Menge bei gleichen Keys ist die Diagonale. |
| Karte `attention/simplex` ignorierte Gleichstand | Rückseite korrigiert: Ecke nur bei eindeutigem Maximum; bei Gleichstand der Mittelpunkt der Kante bzw. Fläche; sind alle Scores gleich, bleibt w für jedes T in der Mitte. | Anki-Vorschauen hell, dunkel, mobil. |
| A19/B-19 nur Zahlenvarianten von AT10 | **A19**: Gleiche Keys machen einen inneren Punkt unerreichbar; erreichbare Menge = offene Diagonale. **B-19**: Kausale Maske plus Vertauschung als Gegenbeispiel zu Satz 4. Beide mit vollständiger Lösung und Punkteschema. | `verify` (231 Prüfungen) und unabhängige Python-Tests. |
| PDF: Abb.-6.1-Galerie nach Kapitel-7-Überschrift; halbleere Seiten; Etikett allein am Seitenende | Die alte Szene ist im Druck ausgeschlossen (im Web als „Abb. 7.1“ erhalten). Umbruchregeln: Kastenetikett bleibt beim Inhalt, Ebenen-Etikett bei der Überschrift. | Kontaktbogen `review_v7_1/contact_pdf_p12_28.png`; §7 beginnt nach 6.12. |
| Farbsemantik der Temperaturkurven | Alle Kurven sind Gewichte, also violett; die Wörter werden über Linienart und Beschriftung unterschieden. | `review_v7_1/fig_3_*.png` |
| Simplex-Grafik: Beschriftungen auf Linien | Beschriftungen links neben den Punkten, Mitte-Etikett darunter. | `review_v7_1/fig_4_*.png` |
| Lab mobil: Formel abgeschnitten | Die Formelzeile bricht unter 640 px um. | `review_v7_1/lab_simplex_phone_*.png` |
| §6.11 nur Abstracts | Volltexte gelesen; Aufbau, Tests, Befunde und **selbst genannte Grenzen** beider Arbeiten wiedergegeben. Eigenes Beispiel zur Nichtinjektivität (vier Values, zwei verschiedene Gewichtsvektoren, gleiche Ausgabe), klar getrennt von den Aussagen der Arbeiten. | `units/nlp_sequence_labeling/research_log.jsonl` (Textvorkommen, SHA-256); Test zur Nichtinjektivität. |

## Bewusst offen

- Die Simplex-Kartengrafik bleibt am Handy klein beschriftet (etwa 10–11 px); ein eigenes Kartenformat wäre der nächste Schritt.
- Die Volltextprüfung belegt Textvorkommen. Die Interpretation der Studien ist durch den Agenten gelesen, aber nicht fachkundig bestätigt.
- Keine Expertenprüfung der Beweise, kein Lerntest. Weitere Kapitel bleiben unverändert (keine Ausweitung vor Abnahme).
