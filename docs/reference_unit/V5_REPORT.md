# NLP-Referenzeinheit v5 – Umsetzung von Issue #8

**Status: HUMAN_REVIEW_PENDING.** v4 ist laut Issue #8 HUMAN_REJECTED (17 Bewertungen, Mittel 0,94/4, Labor 0/4 in allen fünf Dimensionen).
Dieser Bericht vergibt **keine** Qualitätsnoten. Er dokumentiert, was gebaut wurde, wie es geprüft wurde und was ungeprüft bleibt.
PR #3 bleibt Draft. Es gab keine kostenpflichtigen Provider-Aufrufe, keine Automatisierung und keine Gemini-Beteiligung.

## 1. Interaktives Labor (`labor.html`, neu)

Eine eigene Seite, vollständig offline (MathJax liegt lokal), mit vier Laboren. Jedes Labor hat drei Teile:

1. **Freie Bühne**, immer bedienbar.
2. **Entdeckungspfad:** Vorhersage → Handlung mit überprüftem Ziel → Begründung mit Verweis auf Satz und Aufgabe.
3. **Challenges:** überprüfbare Ziele, gestufte Hinweise, fachliche Rückmeldung; „unmöglich?“-Aufgaben verlangen eine Begründung.

Dazu kommt eine **Hypothesenprüfung**. Sie hält den Zustand fest und vergleicht nach der Änderung. Die Ursache wird erklärt, z. B. „alle Scores um denselben Betrag verschoben → Gewichte gleich“.

Zustände sind als Link reproduzierbar. Bedienung per Tastatur (Pfeiltasten verschieben Vektoren), Reduced-Motion-Schalter, Mobilansicht.

| Labor | Manipulierbar | Sichtbar und synchron | Stationen / Challenges |
|---|---|---|---|
| Self-Attention: Eine Query | q, alle k_j und v_j ziehen oder als Zahlen eingeben; alle Keys gemeinsam verschieben; Temperatur; √d-Skalierung an/aus; 2–5 Token; Presets | Projektionen, Skalarprodukte als Rechenterme, Scores, exp, Gewichte, Kette w_j·v_j, Ausgabe, konvexe Hülle, Entropie, ‖J‖ | 7 / 6 |
| Self-Attention: Ganzer Satz | Einbettungen ziehen, W_Q/W_K/W_V editieren, Wörter vertauschen, Positionsvektoren und ihre Stärke, kausale Maske | Gewichtsmatrix, Ausgaben jetzt und in Originalreihenfolge, Äquivarianztest je Wort | (Station 7, Challenge „Gegenbeispiel bauen“) |
| Self-Attention: Skalierung | d_k = 1…512 | gemessene Varianz vs. Satz 3, max. Gewicht und ‖J‖ mit/ohne Skalierung, Kurve über d_k | (Station 6, Challenge „Sättigung“) |
| CRF & Viterbi | Emissionen, Übergänge, Startwerte, Verbote (−∞), Viterbi schrittweise | δ, α, Randwahrscheinlichkeiten, Rückzeiger, bester Pfad, log Z (Vorwärts) = log Z (alle 81 Pfade), lokale / Viterbi- / Rand-Argmax-Folge mit BIO-Gültigkeit | 5 / 4 |
| BiRNN | Wörter tauschen, w_h, Bias, Ausgabegewichte, Rückwärts-RNN an/aus | Zustände, Score z, exakte ‖∂h_t/∂x_j‖-Matrizen | 3 / 3 |
| Spannen & F1 | Gold- und Systemlabels per Klick | Spannenbalken (TP/FP/FN), Spannen- vs. Token-Zählung, P/R/F1 je Typ, Micro/Macro mit Gewichten, IO/BIO/BILOU hin und zurück | 5 / 3 |

Die vorhandenen v4-Szenen bleiben im Lehrbuch und im Druck. Das Labor ersetzt sie nicht, sondern ergänzt sie.

## 2. Mathematik unabhängig von der Darstellung

- `exam_mastery/templates/lab_math.js`: reiner Rechenkern. Die Oberfläche rechnet nichts selbst.
- `tests/test_lab_math.py` (23 Tests): Node-Ausführung gegen ein separates Python-Orakel und gegen `exam_mastery.seqlab`. Geprüft werden:
  - Softmax-Grenzfälle: T→0 mit Gleichstand, T→∞, Überlauf, vollständig maskiert = undefiniert, negative T abgelehnt.
  - Verschiebungsinvarianz, Konvexität der Ausgabe, Gleichverteilung bei q=0.
  - Permutations-Äquivarianz und das Gegenbeispiel mit Positionskodierung; kausale Maske.
  - Sinus-Positionskodierung; Jacobi-Matrix gegen finite Differenzen.
  - Varianz = d_k im Skalierungsexperiment, deterministisch per Seed.
  - Viterbi, Vorwärts, Randverteilungen gegen vollständige Aufzählung (T≤5); verbotene Kanten.
  - Gegenbeispiel „Rand-Argmax ≠ Viterbi“.
  - RNN-Einflussmatrizen gegen finite Differenzen, inklusive exakter Nullen.
  - Spannen- und Token-Zählung gegen `seqlab` (120 Zufallsfälle), BIO-Gültigkeit.
- `tests/test_lab_ui.py` (15 Tests): echte gerenderte Interaktionen in Chromium. Geprüft werden:
  - Tastatur und Zeiger-Ziehen ändern genau die Zahlen, die das Python-Orakel berechnet.
  - Temperatur-Grenzen; Verschiebungsgriff.
  - Pflicht-Vorhersage vor der Begründung.
  - Challenge über Zahleneingaben lösbar; Unmöglichkeitsbegründung.
  - Hypothese wird bestätigt und mit Ursache erklärt.
  - Permutation ohne und mit Positionskodierung; Zustandslink reproduziert die Ansicht; Reduced Motion bleibt gespeichert.
  - CRF-Verbote reparieren die Folge, log Z stimmt mit der Aufzählung überein; Vorwärts-RNN sieht keine Zukunft; Grenzfehler kostet FP und FN.
  - Keine horizontale Scrollleiste bei 390 px.
  - **Jede erreichbare Challenge (12) hat eine verifizierte Lösung.** Die Sättigungs-Challenge hat genau eine Antwort.
- Befunde, die die Tests während der Arbeit fanden und die behoben sind:
  - Mobil-Überlauf (775 px).
  - Veraltete Werte in den Zahleneingaben.
  - Ansichtswechsel ohne Neuaufbau.
  - q-Griff unter einem Key verdeckt.
  - MathJax auf getrennten Knoten.
  - Rechenfehler 0,2211 statt 0,2212 in einer neuen Aufgabe, gefunden vom Verifizierer.

## 3. Lehrbuch, Aufgaben, Lösungen

- Neuer Abschnitt **„Geometrie der Attention“** (§6). Inhalt:
  - Motivierendes Problem („Bank“ am Fluss bzw. bei Geld), Notation mit Dimensionen, Projektion als geometrische Deutung.
  - Durchgerechnetes Beispiel mit allen Zwischenwerten. Es ist identisch mit dem Startzustand des Labors.
  - **Satz 6.1** (Verschiebung und Länge ≡ Temperatur), **Satz 6.2** (konvexe Hülle, mit Erreichbarkeit im Inneren), **Satz 6.3** (Gleichverteilung ⇔ q ⊥ Key-Differenzen), jeweils mit Beweis.
  - **Lemma 6.4** (Softmax-Jacobi, Sättigung) mit Beweis und Verbindung zu Satz 3.
  - Grenzfälle und Gegenbeispiele.
  - Forschungsfenster „Sind Attention-Gewichte Erklärungen?“ (Jain & Wallace 2019; Wiegreffe & Pinter 2019). Gelesen wurden nur die Zusammenfassungen; das ist offen gekennzeichnet.
  - Optionales Video (3Blue1Brown DL6) mit Rolle, Notationshinweis und ohne erfundene Zeitmarken.
  - Laborverweis-Kasten.
- **5 neue Aufgaben** AT5–AT9: durchgerechnet, Beweis, Transfer, Fehleranalyse, selbstständig mit neuer Prüfroutine `attnd`. Jede hat Kurzschlüssel, ausführliche Lösung, Bewertungsschema und Laborverweis. Es gibt keine Selbstbewertung.
- **Bewertungsschlüssel und ausführliche Lösung sind getrennt:** Alle 36 Probeklausur-Aufgaben haben jetzt einen kurzen Schlüssel (`solution`), eine ausführliche Herleitung (`worked`, Pfad für Pfad bzw. Zählung für Zählung) und ein Punkteschema.
- Arbeitsbuch: Hinweise stehen jetzt **bei der Aufgabe**; der abgetrennte Anhang ist entfernt.
- Verifizierer: neues Python-Orakel `attn_full`. **Jede Dezimalzahl** im neuen Text, in den Schritten, Schlüsseln, ausführlichen Lösungen und Karten wird nachgerechnet (217 Prüfungen, grün).

## 4. Anki

- 5 neue Karten zur Attention-Sequenz: Verschiebung, Länge ≡ Temperatur, Gleichverteilungsbedingung, Jacobi/Sättigung, Hülle/Unmöglichkeit. Jede hat Beispiel, häufigen Fehler und Voraussetzungen.
- **Voraussetzungen**: bei allen 48 Karten belegt (v4: 0). Zusätzliche Beispiele und Fehlvorstellungen bei Kernkarten.
- Zwei kleine, fokussierte Grafiken statt großer Gesamtgrafiken: `attention_hull.svg` und `softmax_shift.svg`.
- Unverändert erhalten: Notetype-, Feld- und Template-IDs, GUIDs, .apkg, CSS und der Update-Pfad (Identitätssperre geprüft).

## 5. Systemverknüpfung

Die Kette sieht so aus:

- Die Lehrbuch-Abschnitte verlinken auf Labor-Stationen und Challenges (`lab-ref`, im Druck als Textkasten).
- Die Labor-Stationen verlinken zurück auf Lehrbuch-Abschnitt, Aufgaben-IDs und Kartennamen.
- Aufgaben verlinken auf das passende Experiment (`?ziel=`).
- Karten nennen in der Quelle Satz und Station.
- Die Startseite der Lernplattform hat eine Labor-Kachel.

## 6. Nachweise (vorher → nachher)

`docs/reference_unit/review_v5/`:

- Vorher: `before_v4_attention_scene.png`, die v4-Szene mit festem X und Abspielsteuerung.
- Nachher, Self-Attention:
  - `after_attention_start.png`, `after_attention_q_to_geld.png`
  - `after_attention_challenge_uniform_solved.png`, `after_attention_impossible_reasoning.png`
  - `after_attention_hypothesis_refuted.png` (die Hypothese wird mit Ursachenerklärung widerlegt)
  - `after_attention_sentence_pe_counterexample.png`, `after_attention_scaling_d256.png`
  - `after_attention_mobile.png`
- Nachher, weitere Labore: `after_crf_forbidden_transitions.png`, `after_crf_marginal_trap.png`, `after_birnn_state_flips_to_LOC.png`, `after_spans_half_hits.png`.
- Nachher, Lehrbuch: `after_book_attention_geometry.png`.
- PDFs und Anki-Vorschauen: im Ausgabeordner (`Lehrbuch.pdf`, `Musterloesungen.pdf`, `Probeklausur_Loesungen.pdf`, `anki_preview/`).

## 7. Nicht geprüft (braucht menschliche oder unabhängige Prüfung)

- **Didaktische Qualität und Lernwirkung** des Labors. Es gab keinen Nutzertest und keine verzögerte Transferprüfung.
- Fachliche Gegenlesung der neuen Beweise durch eine Expertin oder einen Experten. Die Zahlen sind maschinell geprüft, die Argumente nicht.
- Echte Anki-Desktop- und AnkiMobile-Clients (nur Chromium/WebKit-Renderings).
- Barrierefreiheit über Tastatur und Reduced Motion hinaus (kein Screenreader-Test).
- Übertragung der vollen Tiefe von Abschnitt 6 auf die Abschnitte BiRNN, CRF und Evaluation im **Lehrbuchtext**. Diese Abschnitte haben jetzt Labore und ausführliche Klausurlösungen, aber noch keine neuen Sätze und Beweise im Stil von §6.
- Die übrigen Forschungsfenster wurden nicht neu kuratiert.

**Bitte alle 17 Dimensionen neu bewerten.** Bis dahin gilt HUMAN_REVIEW_PENDING.
