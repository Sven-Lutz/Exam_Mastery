# v6 – Umsetzung von Issue #9 (und offene Punkte aus #8)

**Status: HUMAN_REVIEW_PENDING.** v5 ist HUMAN_REJECTED (16 von 17 bewertet, Mittel 1,375/4) und so in `RELEASE_STATUS.json` und `NEXT_ACTION.json` eingetragen. PR #3 bleibt Draft.

Es gab keine bezahlten Provider-Aufrufe, keinen Wochenjob und kein Gemini. Dieser Bericht vergibt keine Qualitätsnoten.

## Was umgesetzt, was getestet, was menschlich zu bewerten ist

| Anforderung | Umgesetzt | Automatisch geprüft | Menschlich zu bewerten |
|---|---|---|---|
| v5 als HUMAN_REJECTED dokumentieren | ja (mit allen 16 Bewertungen) | – | – |
| Grenzfall Softmax T→0 bei gleich großen Maxima | korrigiert in Anki-Karte, Labor-Begründung und Lehrtext | Test: Labor-Rückmeldung nennt „gleichauf liegende Values“ | – |
| Jacobi-Matrix bei variabler Temperatur | Lemma 6.4 neu: Schranke ‖J‖ ≤ 4(1−w_m)/T ≤ 4(N−1)e^{−Δ/T}/T; (a) T fest, (b) T→0 eindeutig ⇒ J→0, (c) T→0 Gleichstand ⇒ J divergiert; mit Beweis; Karte angepasst | Test der drei Regime und der Schranke (Python + JS-Kern) | Beweis gegenlesen |
| Kanaltrennung | Labor ohne Karteikarten; die browserinterne Leitner-Warteschlange der Lernplattform ist entfernt und durch die Seite „Wiederholen mit Anki“ ersetzt; neue Seite „Tutor“ | Test: im Labor-Code und in der Oberfläche keine Karteikarten-/Wiederholungsbegriffe; QC-Dimension `channels` | ob die Trennung im Alltag trägt |
| Quellenrecherche fachübergreifend | `exam_mastery/modules/sources.py`: domänenspezifische Recherchepläne, Register mit gelesener Passage, Zugriffsniveau, Evidenz, Grenzen, Funktion; harte Regeln | Regeltests (Abstract ≠ Beleg für Ergebnisse, ungeprüfte Quellen nie zitiert, private Quellen ohne URL, Videos mit Urheber und Datum, Zeitmarken nur geprüft) | Auswahl und Relevanz der Quellen |
| Tutor (ChatGPT) | gemeinsame Anweisung `exam_mastery/tutor/PROJECT_INSTRUCTIONS.md` (2 224 Zeichen, fachneutral); Export je Modul: `tutor_context.md/.json`, getrennter `answer_key.md`, `README.md` mit Projekt- und Study-Mode-Variante und Startsätzen für 7 Lernabsichten; Lernstand nur aus echtem JSON-Export der Lernplattform | Tests: keine Lösungen im Kontext, kein erfundener Lernstand, echter Lernstand korrekt zusammengefasst, keine lokalen Pfade, Anweisung fachneutral | Gesprächsqualität in ChatGPT |
| API später | `tutor_adapter.py`: anbieterneutral, ohne Netzwerkcode; Aufruf erst mit Opt-in, Budget in `NEXT_ACTION.json` und registriertem Anbieter; Lernstand nur mit eigener Zustimmung | Test: gesperrt ohne Zustimmung, Budget oder Anbieter; Budget derzeit 0 | – |
| Fachübergreifend | Analysis 1 (Mathematik) und Entrepreneurship (Wirtschaft) im selben Vertrag; NLP über Adapter | QC-Schema mit denselben 9 Dimensionen für alle drei Module | fachliche und didaktische Güte |

## Quellen: was tatsächlich gelesen wurde

**Geprüft (Passage gelesen, mit Lokator im Register):**
- Lebl, *Basic Analysis I*, v6.3 (15.05.2026, offenes Lehrbuch): Beispiel 2.2.8, Satz 2.1.10, Satz 2.3.8, Beispiel 2.4.3, Definition 7.6.1 und Satz 7.6.2 mit dem Hinweis „complete and contraction are necessary“.
- Y Combinator, *Post-Money SAFE User Guide*, S. 1–6.
- HTGF-Investitionskriterien (Seite vom 09.11.2026).
- Kaplan & Strömberg (2003): **nur Abstract**. Die Quelle wird deshalb nur als Kontext und Forschungsfrage verwendet; die DOI wurde korrigiert.

**Nicht prüfbar, als `unverified` dokumentiert und nicht verwendet:**
- Gompers (1995): Verlagsseite gesperrt.
- Fowler & Robson (1998): nicht gelesen.

**Befund des Validators in der NLP-Einheit:** Die Quellen `lafferty` und `su` haben weder URL noch DOI. Die NLP-QC meldet deshalb `sources: FAIL`. Das ist bewusst sichtbar gelassen und nicht kaschiert.

## Originelle, geprüfte Beispiele (je zwei pro Fach)

- **Analysis E1:** Heron/Newton für √2 in exakten Brüchen. Geprüft sind die Fehleridentität e_{n+1} = e_n²/(2a_n), Monotonie und Schranke, dass die Folge eine Cauchy-Folge in ℚ ohne Grenzwert in ℚ ist, und dass ein negativer Start gegen −√2 läuft. Lebl liefert den Grundbeweis; die Erweiterungen sind eigene.
- **Analysis E2:** cos als Kontraktion auf [cos 1, 1] mit q = sin 1. Die a-priori-Schranke liefert n = 48, tatsächlich genügen 16 Glieder. Gegenbeispiel x + 1/x: kontraktiv, aber kein q < 1 und kein Fixpunkt.
- **Entrepreneurship X1:** SAFE, Seed und Serie A in exakten Brüchen. Gründer 63 % → 50,4 %, Wert 6,3 → 15,12 Mio. €. Gegenbeispiele: Down-Round (Wert 3,78 Mio. €) und Wechsel von Cap zu Rabatt.
- **Entrepreneurship X2:** Fondslogik. Ein Exit von ≈ 667 Mio. € zahlt den Fonds zurück; ein solides Portfolio erreicht nur 1,4× netto; für 3× netto braucht es ≈ 2,33 Mrd. €.

Alle Zahlen werden von `checks.py` des jeweiligen Moduls unabhängig vom Rechenkern des Labors nachgerechnet. Der Bruchrechnungs-Löser hat dabei **einen echten Fehler im JS-Kern** gefunden: Ohne Rabatt wurde ein SAFE nie zum günstigeren Rundenpreis umgewandelt. Er ist behoben, und der Test ist über 60 Zufallsfälle verankert.

## Labore (gemeinsamer Kern, fachspezifische Experimente)

- **Folgen & Grenzwerte:**
  - ε-Streifen mit Beweis-gegen-Test-Unterscheidung: „bewiesen“ nur bei Formel für N(ε), sonst „kein Beweis“; der erste Gegenbeispiel-Index wird angezeigt.
  - Spinnwebdiagramm mit Lipschitz-Schätzung.
  - 5 Stationen und 4 Challenges, darunter eine Unmöglichkeitsbegründung für (−1)ⁿ.
- **Finanzierungsrunden & Fondslogik:**
  - Kapitalisierungstabelle mit Cap gegen Rabatt, Pool-Shuffle, Up- und Down-Round.
  - Fonds-Multiple.
  - 4 Stationen und 4 Challenges, darunter das Monotonie-Argument „höherer Cap gibt nie mehr“.
- **Wiederverwendung:** Der Kern (`lab_core.js`: Bühne, Entdeckungspfad, Challenges, Hypothesenprüfung, Zustandslinks, Tastatur, Reduced Motion) wird unverändert genutzt. Die NLP-Labore sind auf denselben Kern umgestellt.

## Nachweise

- `docs/cross_domain/evidence/`: Screenshots beider neuer Labore in charakteristischen Zuständen sowie der Anki- und Tutor-Seite der NLP-Lernplattform.
- `docs/cross_domain/samples/<modul>/`: echte Tutor-Pakete, QC-Berichte und Recherchepläne.
- Tests: `tests/test_modules.py` (18) und die gesamte Suite (797 bestanden, 6 übersprungen, vor dem letzten Zusatztest).

## Bewusst nicht getan / offen

- Kein Neuaufbau der Anki-Infrastruktur. Die Anki-Karten wurden nur fachlich korrigiert, nicht umfassend neu gestaltet; die Bewertung 1/4 aus v5 ist damit **nicht** adressiert.
- Lehrbuch, Arbeitsbuch und Probeklausur der NLP-Einheit sind außer Lemma 6.4 nicht weiter vertieft.
- Für Analysis 1 und Entrepreneurship gibt es Labor, Aufgaben (je 4), Beispiele und Tutor-Paket, aber keine neuen PDFs oder Anki-Decks. Die bestehenden Engine-Produkte dieser Kurse bleiben unverändert und ungeprüft.
- Die Tutor-Pakete wurden nicht in einer echten ChatGPT-Sitzung erprobt. Die Aussagen zu Projects und Study Mode stammen aus der OpenAI-Hilfe (Stand der Recherche 15.11.2026); Dateigrenzen hängen vom Tarif ab.
- Lernwirkung, didaktische Passung und fachliche Gegenlesung: menschliche Bewertung erforderlich.
