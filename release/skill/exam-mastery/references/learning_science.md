# Lernwissenschaftliche Grundlage der interaktiven Labs (DR-1.2)

Stand: 10.11.2026.

Geprüft wurden die bibliografischen Angaben und die Kernaussagen anhand von Abstracts und Verlagsseiten. Nicht jede
Quelle wurde im Volltext gelesen; das ist bei den Einträgen vermerkt. Keine Aussage hier ist eine Wirksamkeitsgarantie
für Exam Mastery: Das System selbst wurde nicht empirisch evaluiert.

## Geprüfte Quellen

| Quelle | Geprüft | Kernaussage, soweit belegt |
|---|---|---|
| Chi & Wylie (2014), *Educational Psychologist* 49(4), 219–243 | Bibliografie, Abstract, Volltext verfügbar | ICAP: Lernen nimmt vom passiven über den aktiven und konstruktiven zum interaktiven Modus zu. Maßgeblich ist das beobachtbare Lernverhalten, nicht die Oberfläche. |
| Brod (2021), *Psychonomic Bulletin & Review* 28, 1839–1847 | Bibliografie, Abstract | Vorhersagen vor der Auflösung ist eine verbreitete Strategie mit berichteten positiven Effekten; die Mechanismen sind noch unklar. |
| Bisra et al. (2018), *Educational Psychology Review* 30(3), 703–725 | Bibliografie, Zusammenfassungen | Angeleitete Selbsterklärung wirkt lernförderlich (Metaanalyse, 64 Studien, überwiegend Studierende). |
| Kalyuga, Ayres, Chandler & Sweller (2003), *Educational Psychologist* 38(1), 23–31 | Bibliografie, Abstract | Expertise-Reversal: Was Novizen hilft, kann Fortgeschrittene behindern. |
| Renkl & Atkinson (2003); Sweller (1988) | schon in DR-1.0 geprüft | Lösungsbeispiele und schrittweises Ausblenden für Anfänger. |
| Roediger & Karpicke (2006); Dunlosky et al. (2013); Cepeda et al. (2006) | schon in DR-1.0 geprüft | Abrufübung und verteiltes Lernen. |
| Hattie & Timperley (2007); Wisniewski, Zierer & Hattie (2020), *Frontiers in Psychology* 10:3087 | Bibliografie, Abstract | Feedback wirkt im Mittel, aber sehr heterogen; der Informationsgehalt entscheidet. Lob und Belohnung wirken wenig. |
| Butterfield & Metcalfe (2001), *J. Exp. Psych.: Learning, Memory, and Cognition* 27(6), 1491–1494 | Bibliografie, Zusammenfassungen (Volltext nicht gelesen) | Hypercorrection: Mit hoher Sicherheit begangene Fehler werden nach Feedback eher korrigiert als unsichere; erklärt wird das mit höherer Aufmerksamkeit für das überraschende Feedback. |
| de Jong & van Joolingen (1998), *Review of Educational Research* 68(2), 179–201 | Bibliografie, Abstract | Entdeckendes Lernen mit Simulationen braucht Unterstützung; Lernende haben u. a. Schwierigkeiten, prüfbare Hypothesen zu bilden und Experimente zu planen. |
| Fiorella & Mayer (2016), *Educational Psychology Review* 28(4), 717–741 | Bibliografie, Abstract | Acht generative Lernstrategien, darunter Zusammenfassen, Selbsttesten und Selbsterklären, jeweils mit Randbedingungen. |
| D'Angelo et al. (2014), SRI International, Bericht | Bibliografie, Berichtseite | Metaanalyse zu Simulationen in K–12-MINT. Belegt die Fragestellung (Simulation versus Simulation mit Erweiterungen); Effektgrößen wurden hier nicht übernommen, die Population ist Schule, nicht Hochschule. |

## Einstufung der Gestaltungsregeln

- **A:** gut gestützter empirischer Befund
- **B:** kontextabhängige Empfehlung
- **C:** plausible, nicht hinreichend geprüfte Produktentscheidung
- **D:** eigene Hypothese

| Regel | Stufe | Begründung | Umsetzung im Produkt |
|---|---|---|---|
| L1: Erst festlegen, dann sehen. Die Simulation öffnet sich erst nach Vorhersage **und** einer kurzen Begründung. | B | Brod 2021 (Vorhersagen), Bisra 2018 (Selbsterklärung), ICAP: Ein Regler allein ist nur „aktiv“, eine Begründung ist „konstruktiv“. | `predictFlow`: Ergebnis verborgen, Begründung Pflicht, danach ein Vergleichsimpuls („Welcher Schritt Ihres Arguments stimmt?“) |
| L2: Für Wiederholer ist die Vorhersage überspringbar; das wird nicht als Leistung gewertet. | B | Expertise-Reversal (Kalyuga 2003): Zwangsschritte belasten Fortgeschrittene. | Schaltfläche „Ohne Vorhersage erkunden“ |
| L3: Nach dem Ergebnis wird der Mechanismus erklärt, nicht nur richtig/falsch gemeldet. | A/B | Feedback-Metaanalysen: Der Informationsgehalt entscheidet. | `result_text` + `explanation` |
| L4: Gestufte Hinweise, die Lösung erst nach einem eigenen Versuch. | B | Abrufübung und generatives Lernen; vorzeitige Lösungen fördern Abschreiben. Die Stufenzahl selbst ist eine Produktentscheidung (C). | „Lösung zeigen“ bleibt bis zum ersten Prüfen gesperrt |
| L5: Typische Fehler werden diagnostiziert (z. B. Endsaldo statt Minimum, fehlendes σ′, Vorzeichen). | B | Fehlerbezogenes, korrigierendes Feedback (Hattie & Timperley 2007). | `errors` je Aufgabe, deterministisch geprüft |
| L6: Jede Lab-Sequenz endet mit einer Transferaufgabe mit neuen Parametern. | B | Constructive Alignment (Biggs) und Transfer als Lernziel. | letzte Aufgabe je Lab |
| L7: Modellannahmen und Grenzen stehen sichtbar beim Lab. | C | Schutz vor Überverallgemeinerung; nicht empirisch geprüft. | Abschnitt „Modell und Annahmen“ |
| L8: Kein Mastery-Prozentwert; der Status beschreibt beobachtete Versuche. | C | Eine einmalige richtige Antwort belegt kein Behalten (Retention braucht verteilte Wiederholung). | `INDEPENDENT_PASS`, `ASSISTED` usw., Hinweis auf Anki |
| L9: Interaktion ist an eine Lernaufgabe gebunden; kein Regler ohne Frage. | B | ICAP: Manipulieren ohne Denkauftrag bleibt passiv oder bloß aktiv. | jede Lab-Spezifikation braucht `sequence.predict` und `tasks` (Validierung) |
| L11: Zur Vorhersage wird die Sicherheit erfragt; sicher gemeinte Fehler werden in der Rückmeldung eigens angesprochen. | B | Hypercorrection (Butterfield & Metcalfe 2001); Übertragung auf Simulationen ungeprüft. | `predictFlow`: Pflichtangabe „sicher / eher sicher / geraten“, kalibrierte Rückmeldung |
| L12: Erst eigene Erklärung, dann die Expertenerklärung; eine Begriffs-Lesehilfe zeigt, welche Kernideen genannt wurden (keine Bewertung). | B | Selbsterklärung (Bisra 2018), ICAP „konstruktiv“; die Lesehilfe selbst ist eine Produktentscheidung (C). | `explainPhase` |
| L13: Erkunden geschieht über konkrete Aufträge mit überprüfbarem Zielzustand, nicht als freies Probieren. | B | Unterstütztes Entdecken (de Jong & van Joolingen 1998). Jeder Auftrag ist in Python als lösbar nachgewiesen. | `explorePhase`, `pedagogy.validate` |
| L14: Konzeptfragen mit einer Rückmeldung je falscher Option, die die zugrunde liegende Fehlvorstellung benennt. | B | Fehlerbezogenes Feedback (Hattie & Timperley 2007; Wisniewski 2020). | `choiceTask` |
| L15: Am Ende steht eine eigene Zusammenfassung vor dem Vergleich mit den Kernaussagen; Behalten wird an Anki verwiesen. | B | Generatives Zusammenfassen (Fiorella & Mayer 2016); verteiltes Wiederholen (DR-1.0). | `summaryPhase` |
| L10: Ein Lab je Kernkonzept, nicht für jede Formel. | D | Hypothese: weniger, gut gebaute Labs nützen mehr als viele dünne. | Labs nur für deterministische Modelle |

Nicht behauptet wird: dass mehr Interaktivität automatisch besser ist, dass die Labs messbar Lernerfolg steigern, oder
dass Effekte aus Schulstudien (D'Angelo 2014) unverändert für Hochschulkurse gelten.

Quellen: https://education.asu.edu/lcl/publications/chi-m-t-h-wylie-r-2014-icap-framework-linking-cognitive-engagement-active-learning ·
https://link.springer.com/10.3758/s13423-021-01904-1 · https://ro.uow.edu.au/edupapers/136 ·
https://pmc.ncbi.nlm.nih.gov/articles/PMC6987456 · https://hal.science/hal-00190680 · https://link.springer.com/doi/10.1007/s10648-015-9348-9 · https://pmc.ncbi.nlm.nih.gov/articles/PMC4084803 ·
https://www.sri.com/publication/education-learning-pubs/stem-and-computer-science-pubs/simulations-for-stem-learning-systematic-review-and-meta-analysis-full-report/

## Lernumgebung (B15): Gestaltungsentscheidungen

| Entscheidung | Stufe | Begründung | Umsetzung |
|---|---|---|---|
| L16: Simulation steht im Text dort, wo das Konzept erklärt wird, nicht auf einer separaten Linkseite. | A/B | Räumliche/zeitliche Kontiguität: Metaanalyse über 50 Studien, Vorteile besonders bei komplexem Material und Novizen (Ginns 2006, *Learning and Instruction* 16, 511–525; Abstract geprüft). | Lab-Einbettung nach dem letzten Block mit derselben Kompetenz (`learn_app.app_model`) |
| L17: Kurzabfragen am Abschnittsende; erst selbst antworten, dann aufdecken. | A | Abrufübung (Roediger & Karpicke 2006; Dunlosky et al. 2013, schon in DR-1.0). | „Kurz prüfen“ aus den Anki-Karten, Selbsteinschätzung als Ereignis |
| L18: Musterlösung erst nach eigenem Versuch; Hinweise gestuft; Selbstbewertung nach Schema. | B | wie L4; Selbstbewertung ist Produktentscheidung (C). | Übungs- und Klausurmodus |
| L19: Lab-Phasen sind Bausteine nach Lernziel, keine Pflichtsequenz. | B | Expertise-Reversal und Cognitive Load (Kalyuga 2003): unnötige Schritte belasten; Risikomatrix ohne Erkunden/Sichern, modellhafte Labs mit allen Bausteinen. | `pedagogy.PROFILE` |
| L20: Fortschritt als beobachtete Ereignisse in Worten, kein Beherrschungswert; Behalten an Anki verwiesen. | C | Eine richtige Antwort belegt kein Behalten; Scheingenauigkeit vermeiden. | Lernstand je Lernziel, gruppiert nach Abschnitt |
| L21: Bei falscher Antwort Verweis auf den Abschnitt mit derselben Kompetenz. | B | Formatives Feedback mit Hinweis auf den nächsten Schritt (Hattie & Timperley 2007). | Kompetenzabgleich, deterministisch |

Quelle: Ginns, P. (2006). Integrating information: A meta-analysis of the spatial contiguity and temporal contiguity effects. *Learning and Instruction*, 16, 511–525. doi:10.1016/j.learninstruc.2006.10.001


## Mathematische Szenen (B16): Gestaltungsentscheidungen

| Entscheidung | Stufe | Begründung | Umsetzung |
|---|---|---|---|
| L22: Animation nur dort, wo sich etwas über Zeit oder Raum verändert (Rechenfluss, Transformation, Zahlungsverschiebung); keine dekorative Bewegung. | A/B | Metaanalyse: kleiner Gesamtvorteil von Animation gegenüber statischen Grafiken (g = 0,23), größer bei Veränderungen über Zeit (Berney & Bétrancourt 2016, *Computers & Education* 101, 150–167). | Animationsarten je Renderer begrenzt (`scenes.TYPES`), validiert |
| L23: Jede Animation pausierbar, schrittweise, rückwärts; Tempo wählbar; reduzierte Bewegung. | B | Animationen sind oft zu schnell/komplex, um wahrgenommen zu werden; kontinuierliche Vorgänge werden als Schrittfolge verstanden (Tversky, Morrison & Bétrancourt 2002, *IJHCS* 57, 247–262). | Player: Zurück/Weiter/Abspielen/Pause/Neustart, `prefers-reduced-motion` |
| L24: Mehrere Darstellungen (Bild, Formel, Zahl) werden aktiv verknüpft: gleiche Farbe je Größe, Klick auf Term hebt Objekt hervor. | B | Mehrfachrepräsentationen helfen nur, wenn Übersetzung zwischen ihnen unterstützt wird (Ainsworth 2006, DeFT, *Learning and Instruction* 16, 183–198). | Farbrollen, `data-ref`-Kopplung, Validator prüft jede Referenz |
| L25: Fokus durch Abblenden und Zoom auf die Teilstruktur des aktuellen Schritts. | B | Signalisierung lenkt Aufmerksamkeit (Mayer, Multimedia Learning). | `targets`, `zoom` je Schritt |
| L26: Numerische Exploration ist sichtbar von Beweis getrennt. | C | fachliche Redlichkeit | `status: exploration`, Hinweis im Lab |

Quellen (geprüft): Berney, S. & Bétrancourt, M. (2016) doi:10.1016/j.compedu.2016.06.005 · Tversky, B., Morrison, J. B. & Bétrancourt, M. (2002) doi:10.1006/ijhc.2002.1017 · Ainsworth, S. (2006) doi:10.1016/j.learninstruc.2006.03.001

## v0.18: Learning Engine (adaptive Lernstrecken)

Die vollständige, maschinenlesbare Evidenzmatrix liegt in der Engine unter `docs/learning_design_evidence_matrix.json`
(Prinzip, Quellen, Mechanismus, Produktfunktion, beobachtbare Handlung, Grenzen, Prüfmethode, Status, Evidenzklasse A–D).
Neu geprüft (10.11.2026, Abstracts/Verlagsseiten): Carpenter, Pan & Butler (2022) Nat Rev Psychol 1(9) 496–511;
Pan & Rickard (2018) Psychol Bull 144(7) 710–756; Anderson, Corbett, Koedinger & Pelletier (1995) J Learn Sci 4(2) 167–207;
VanLehn (2011) Educ Psychol 46(4) 197–221; Corbett & Anderson (1994) UMUAI 4(4) 253–278; Mitrovic, Martin & Suraweera (2007)
IEEE Intell Syst 22(4) 38–45; Bastani et al. (2025) PNAS 122(26) e2422633122; Kestin et al. (2025) Sci Rep.
Nur indirekt bestätigt: Rohrer & Taylor (2007); Ohlsson (Constraint-Based Modelling, Jahr 1992 oder 1994).
Bayesian Knowledge Tracing ist bewusst nicht implementiert (keine kalibrierten Parameter).
