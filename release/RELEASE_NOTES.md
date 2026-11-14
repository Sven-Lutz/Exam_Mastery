# Exam Mastery v0.21.0-rc1

## Cross-Domain-Release-Candidate: Leistung, ehrlicher Status, Prüf-Fixes
- **Resume ohne Neuplanung:** `auto_scope` baute den Elementindex eines Kurses pro Kapitel-Gate und pro Kompetenz neu (quadratisch; NLP mit 67 619 Elementen ≈ 1,5–2 h je Wiederaufnahme). Jetzt einmal pro Manifest; gemessen 0,32 s für alle 27 Gates, Ergebnisse identisch. Plan-Cache auf Kursebene (Schlüssel: Quellen-Snapshot, Engine-Code, Argumente, Kursdateien außer Resume-Zeigern): unveränderte Wiederaufnahme 31–56 s statt ≥ 1,5 h.
- **Kampagnen-Dashboard ehrlich:** nie „geprüft“ bei PARTIAL-Gate, NOT_TESTED-Dimensionen oder offenen Befunden; offene P2/P3 werden mitgezählt; Datenstand und Ledgergröße auf der Seite.
- **Numerik-Prüfung:** LaTeX-Prozent `\%` wird als Prozent gelesen; gerechnete Ketten werden nie auf ein Zahlpräfix gekürzt (`= 5.4+…` nicht als `5`). Beide erzeugten falsche FAILs auf korrekten Inhalten.
- **Bekannt, nicht behoben:** drei Browser-Tests (`test_b16_scenes` Animation, zwei `test_b17_design`) schlagen nur im Gesamtlauf fehl (Testisolation, auch auf dem Ausgangscommit 1633242), einzeln grün. Checkpoint einer erfolgreichen Stage wird bei späterem Gate-FAIL wiederverwendet (manuelle Archivierung nötig).

# Exam Mastery v0.20.0-preview

## Wissenschaftliche Grundlage, Editionen und Buchgestaltung „Folio“ (B20)
- **Wissensbasis KB-1.1.0:** 7 zentrale Quellen am Volltext geprüft (Rowland 2014, Brunmair & Richter 2019, Kalyuga 2007, Kluger & DeNisi 1996, Wisniewski et al. 2020, Bastani et al. 2025, Kestin et al. 2025); Basis `fulltext_checked` mit Fundstelle, vom Validator erzwungen. Übergeneralisierte Regeln eingeschränkt: WE-R1/WE-R2 (Expertise Reversal, Einstieg nach Kurzdiagnose), RP-R1 (Abruf mit Hinweisreiz, Feedback bei niedriger Erfolgsquote), IL-R1 (nicht für Sachtext/Begriffslisten), PF-R1 (nur bei generierbarem Vorwissen), FB-R1 (Teilschritt-Feedback bei komplexen Aufgaben), AI-R1 (geprüfte Musterlösung im Tutor; nur Schadensvermeidung belegt). Nicht zugängliche Volltexte sind benannt.
- **Fachliches Quellenregister** `knowledge/subject/entrepreneurship.json` (22 Quellen: Meta-Analysen, Theorie, Lehrbücher, §§ 5, 5a GmbHG, § 721 BGB, EXIST); je Quelle Lesestand und erlaubte Verwendung. `scripts/verify_sources.py` prüft auch diese Register (DOI/ISBN; Gesetze als gelesene Primärtexte).
- **Editionen** (`exam_mastery/edition.py`, Schema `em-edition-v1`): kuratierte, versionierte Überarbeitung eines produzierten Kapitels außerhalb des Vorlesungsordners – fachliche Ergänzungen, Rechenbeispiele, Aufgaben, Blueprint-Klausur, Anki-Karten –, beim Veröffentlichen ohne Modellaufruf angewendet. Fail-closed: Ergänzungen brauchen eine verifizierte Fachquelle, selbst entworfene Zahlen bestandene Rechenprüfungen, keine Vorlesungsinhalte erfinden, keine stillen Löschungen; gleiche Kartenschlüssel = erhaltener Lernstand.
- **Buchgestaltung „Folio“:** Textspalte mit Randspalte für Herkunft und Quellen, nummerierte Definitionen, Beispiele, Abbildungen und Tabellen, Kapitelauftakt mit Lernzielen und Wegweiser, Rechenbeispiele zweispaltig (Rechnung | Begründung), laufende Kopfzeile. Neue gemeinsame Abbildungstypen: Verlauf (`line`), Risikomatrix (`heat_matrix`), Netzplan mit kritischem Pfad (`gantt`), Adoptionskurve.
- **Aufgaben und Klausur:** Operator und Bearbeitungszeit je Aufgabe, geführte Aufgaben mit Lücken (Fading), alternative Lösungswege, Klausur mit Namensfeld, Zeitplan, Blueprint (Kompetenz × Operator × Anforderung × Punkte × Zeit) und Integritätsprüfung (Zeit, Blueprint-Punkte).
- **Lernumgebung:** Klausurzeit mit Zeitbudget, Blueprint nach Abgabe, Aufgabentitel, Lückengerüste, Formeln scrollen statt abgeschnitten zu werden.
- **Fixes:** Testsuite las die echte Provider-Konfiguration des Nutzers (unter pytest) – jetzt isoliert; Gemini-SDK als optionales Extra `[gemini]`; `exam-mastery kb` im installierten Befehl; Entwicklungsumgebung außerhalb des iCloud-Ordners (macOS markiert dort `.pth`-Dateien als versteckt, Python 3.12 ignoriert sie).

# Exam Mastery v0.19.0-preview

## Designsystem „Bühne“ und adaptives Lernen im Kapitel (B19)
- **Neues Designsystem** (`em_tokens.css`): „Papier & Tinte“ verworfen. Zwei Räume – helle, editoriale Lesefläche und eine dunkle mathematische Bühne (`.ds-stage`, in hellem und dunklem Modus dunkel) mit festen Rollenfarben. Keine Kartenwüsten, keine Versalien-Labels, Schrift auf der Bühne ≥ 12,5 px. Begründung, verworfene Entscheidungen und zwei gerenderte Richtungen: `docs/DESIGN_v0_19.md`.
- **Labs:** Skript links, Szene rechts (Desktop); alle bestehenden Szenen laufen auf der Bühne. Netz-Lab *Geführt*: farbcodierter Kettenterm, Wert, Gradient, gemessene Wirkung, sichtbares Vorher→Nachher je Lernschritt; *Erkunden*: alle Parameter, Gleichungen und eine Finite-Differenzen-Prüfung jedes Gradienten.
- **Lernstrecken:** große Bühne; Cashflow als Ursache-Wirkung (Auftrag → Zahlungsziel-Bogen → Zahlungen → kumulierter Verlauf, Bedarf als Klammer am Tiefpunkt); Geometrie mit Thales-Kreis, der zeigt, *warum* „gleich lang“ nötig ist; Evidenz-Etikett je Rückmeldung (Stichprobentest ausdrücklich kein symbolischer Beweis); Definitionsbereichsprüfung; Vorschau der passenden Anki-Karte.
- **Integration ins Kapitel:** `learn_app.republish()` rendert eine veröffentlichte Lernumgebung neu (ohne Modellaufruf, Inhalt unverändert) und bettet die Lernstrecken ein, deren Kompetenzen zum Kapitel gehören; Lernstand zeigt deren beobachteten Stand. Referenz-Lernstrecken speichern getrennt (`referenz|…`).
- **Tutor-Brief** nennt die passende Visualisierung.
- **Fix:** Statuszeile zeigte Markdown-Sternchen.

# Exam Mastery v0.18.0-preview

## Learning Engine: Diagnose, adaptive Lernsteuerung, Tutor (B18)
- **Neues Paket `exam_mastery/learning/`** (deterministisch, offline): Diagnoseobjekt `em-diagnosis-v1` auf fünf Ebenen (Zahl, Ausdruck, Rechenschritte, Konzept/Voraussetzungen, Freitext = `UNVERIFIED`), regelbasierte Policy `em-decision-v1` (Fälle Voraussetzung, Rechenschritt, wiederholte Verwechslung, selbstständiger Erfolg, Behalten) mit sichtbarer Begründung, kein Mastery-Prozentwert.
- **Drei adaptive Lernstrecken** (`lernstrecken/*.html`): Backpropagation (fehlender Faktor x₁ → Pfad im Netz markiert), Liquiditätsplanung Kapitel 7 (Endsaldo 2.136 statt Tiefpunkt 2.144 → Kontrast und neues Zahlungsziel), Beweisschritt Rechteck (fehlende Voraussetzung „gleich lang“ → Gegenbeispiel Parallelogramm, constraint-basiert).
- **Netz-Lab: Geführt / Erkunden** – zwei Ansichten desselben Modells; geführt mit einem Parameter im Fokus (Verbindung, Term, Wert, Gradient, Wirkung auf den Verlust), `?mode=` und `?focus=` als Einstieg.
- **Tutor-Workflow:** Kontextdatei `em-tutor-context-v1` aus dem Browser (nur auf Knopfdruck), `python -m exam_mastery.learning tutor-brief`, Skill-Aufruf `/exam-mastery tutor <datei>`, Protokoll `references/tutor_protocol.md`.
- **Anki:** Wiederholungskarten mit stabilen IDs und Schlagwörtern `em::fehler::<kategorie>`; Anki plant, Exam Mastery verweist.
- **Evidenzmatrix** `docs/learning_design_evidence_matrix.json`, Evaluationsprotokoll (nicht durchgeführt) `docs/EVALUATION_PROTOCOL.md`.
- **Fachliche Korrektur:** Das Cashflow-Lab behauptete, ein späteres Zahlungsziel lasse den Tiefpunkt immer sinken. Richtig (bei nicht negativen Aufträgen): Er sinkt oder bleibt gleich; mit Rückerstattungen kann die Aussage scheitern. Beides ist getestet.

# Exam Mastery v0.17.0-preview

## Gestaltung und Lernerlebnis: „Papier & Tinte“ (B17)
- **Gemeinsames Designsystem** `templates/em_tokens.css` für Labs, Referenzsammlung und Lernumgebung: Typografie (Source Serif 4 / Source Sans 3, lokal), Skalen für Schrift, Abstand, Radius, Schatten, Bewegung, Farbrollen hell/dunkel, Fokus- und Interaktionszustände, Breakpoints. Fachneutral, kein Kursbezug. Ausgewählt aus zwei gerenderten Richtungen („Papier & Tinte“ vs. „Observatorium“); Begründung im Abnahmebericht.
- **Referenzsammlung neu** (`labs/build.py: gallery()`): Experimente mit Live-Vorschau statt Linkliste. Jede Vorschau ist der echte Szenen-Renderer, gespeist aus Modell und Standardwerten des Labs (`EM.scene.preview`), ruhig animiert, bei reduzierter Bewegung ein Standbild, außerhalb des Bildschirms pausiert. Kein Lernstand auf der Übersicht.
- **Mathematical Visual Workspace:** Szene als großflächige Bühne mit Erklärspalte (Schritt, Formel, Text, Farbschlüssel der mathematischen Rollen), kompakte Transportleiste, Parameter und Zusatzdarstellungen als aufklappbare Werkzeuge, Lernziel/Voraussetzungen und Modell/Annahmen/Quellen als ruhiger Anhang, Vorhersage als kompakte Experimentkarte. Formeln umbrechen statt abgeschnitten zu werden.
- **Bessere Erklärbilder:** Netz mit Schichtbeschriftung und sichtbarem Update je Gewicht (Δ = −η·∂L/∂w, aus der Rechenspur, gegen Python getestet); Cashflow mit Periodensaldo über der Liquiditätskurve und Begründung des Tiefpunkts (letzter negativer, erster positiver Cashflow – nur angezeigt, wenn es zutrifft); Sehnen-Lift größer; stärkere Linien, Beschriftungen ≥ 12 px.
- **Klartext statt Interna:** keine Kompetenz-IDs, Versionsnummern oder Statuscodes im UI („ohne Hilfe gelöst“ statt INDEPENDENT_PASS); Ereignisprotokoll in Worten.
- **Lernstand-Namespacing:** Referenz-Labs speichern unter dem Kontext `referenz` (`referenz|lab::aufgabe`, Feld `ctx`); die Kapitel-Lernumgebung zählt solche Einträge nie. Bestehende Einträge bleiben unverändert (keine Migration, keine Löschung).
- **Lernumgebung:** Lehrbuchsatz mit Lesespalte, Kapitelinhalt und Simulationen auf der Startseite, Klausur-Fokusmodus (ohne Navigation), Tutor-Seite mit klarer Trennung „funktioniert hier“ / „braucht einen Agenten“, differenzierte Rückmeldungsflächen.
- **Fix:** Die Klasse `.em-lab` galt zugleich für SVG-Beschriftungen und den Lab-Bereich (UI-Texte erschienen fett in Serifenschrift).

# Exam Mastery v0.16.0-preview

## Mathematische Szenen: erklären, wie ein Ergebnis entsteht (B16)
- **Szenen-Schicht im bestehenden Lab-Laufzeitmodul** (`templates/em_scene.js`, Schema `em-scene-v1`, Python `labs/scenes.py`): Schritt-Player (Abspielen/Pause, Weiter, Zurück, Neustart, Tempo, reduzierte Bewegung, Tastatur), Formel-Terme mit Farbrollen und Kopplung an Grafikobjekte, Zoom auf Teilstrukturen, fortschreitendes Aufdecken, Übergänge. Keine zweite Lab-Engine, keine Abhängigkeiten.
- **Eine Wahrheit:** Jede angezeigte Zahl ist ein Pfad in eine Rechenspur des Referenzmodells (`mlp_trace`, `chord_trace`, `cash_trace`); der Browser spiegelt die Modelle und wird dagegen getestet. Der Validator prüft Pfade, Objektreferenzen, Farbrollen, Animationsarten, Didaktikkarte und alle Erwartungswerte.
- **Referenz A – Neuron Schritt für Schritt:** gewichtete Summe Term für Term, Bias, Aktivierungskurve, Ausgabe, Verlust, Fehlersignal, Gradient als Kettenprodukt, Update aller Parameter, vorher/nachher; Neuron/Gewicht per Klick wählbar, Gewichte im Bild ziehbar.
- **Referenz B – Sehnen-Lift (Inscribed Rectangle):** Punktpaar → (Mittelpunkt, Abstand) → Punkt im Raum, Kamerafahrt von Draufsicht zu 3D, Fläche aller Paare, Newton-Suche nach zwei Paaren mit gleichem Bildpunkt = Rechteck (Restfehler angezeigt, ausdrücklich kein Beweis).
- **Referenz C – Cashflow als Prozess:** Verkäufe, Zahlungsziel-Bögen, Zahlungseingänge, Auszahlungen, Liquidität Periode für Periode; Änderung des Zahlungsziels verschiebt die Zahlungen sichtbar; Bedarf als tiefster Punkt; Vergleichsszenario. In Kapitel 7 automatisch aktiv.
- **Neues Lab-Modell `chord`** mit Lernsequenz (Vorhersagen, Beobachten, Erklären, Üben, Transfer).
- `scripts/build_reference_scenes.py` baut die drei Referenzen offline.

# Exam Mastery v0.15.0-preview

## Integrierte Lernumgebung statt Dokumentenportal (B15)
- **`Lernumgebung/index.html`** wird bei jeder Kapitelveröffentlichung deterministisch aus dem Buchmodell erzeugt (`exam_mastery/learn_app.py`, Laufzeit `templates/em_app.js`, Designsystem `templates/em_app.css`): eine Datei, offline, ohne Abhängigkeiten.
- **Lernen:** das Lehrbuch als interaktives Kapitel mit Seitennavigation, Lernzielen je Abschnitt, Kontextspalte (Lernziele, Simulation, passende Übungen, Quellen), Kurzabfragen aus den Karten und Vor/Zurück-Navigation.
- **Labs im Text:** jede Simulation steht im Abschnitt mit denselben Kompetenzen, nach dem letzten erklärenden Block (iframe im Einbettungsmodus, Höhe und Theme synchronisiert, statische Abbildung aufklappbar). Ohne Kompetenzbezug kein Platz im Text.
- **Üben:** Aufgaben nach Stufe und Lernziel, Zahlenabgleich mit der Musterlösung, gestufte Hinweise, Lösung erst nach eigenem Versuch, Selbsteinschätzung, Verweis auf den passenden Abschnitt bei Fehlern, Entwürfe bleiben erhalten.
- **Klausur:** eigener Modus, Lösungen und Bewertungsschema erst nach Abgabe, Selbstbewertung (keine offizielle Bewertung).
- **Lernstand:** je Abschnitt und Lernziel in Worten (gelesen, im Lab, ohne/mit Hilfe richtig, Lösung angesehen, später erneut richtig); kein Beherrschungswert; Export/Import (em-learn-export-v1, ohne Duplikate), kontrolliertes Löschen; Lab-Versuche aus em-progress-v1 werden gelesen, nie überschrieben.
- **Tutor-Briefing:** kopierbarer Kontext (Abschnitt, Lernziele, Quellen, offene Aufgabe, beobachtete Versuche) für ein Gespräch mit Claude Code; keine Live-Verbindung, nichts wird automatisch übertragen.
- **Design:** Tokens für Farbe, Typografie, Abstand, Radius, Status, Hell/Dunkel; drei Spalten am Desktop, Schublade am Handy; Tastatur, Fokus, Sprunglink, `prefers-reduced-motion`.
- **Labs:** Phasenprofile je Lernziel statt Pflichtsequenz (Risikomatrix ohne Erkunden/Sichern); Einbettungsmodus; Theme per `data-theme`.
- **Fachübergreifend:** dieselbe Umgebung für Mathematik, Recht und ML (synthetische Fixtures im Browser getestet); Kurse ohne Labs funktionieren ohne Platzhalter.
- **Sicherheit:** CSP mit gehashten Inline-Skripten, keine Netzwerkziele (`connect-src 'none'`), Dateien nur lokal; `style-src 'unsafe-inline'` nur wegen MathJax-SVG.

# Exam Mastery v0.14.2-preview

- **Prüfebenen im Dossier:** `solution_verification` und `setup_review` (aus `verification/` im Kursausgabeordner) – Inhalts-Hash je Aufgabe, STALE bei späterer Änderung, FAIL bei CONTRADICTED, nie Teil der technischen Freigabe.
- **S3 (Kausalbehauptungen):** „die Folge der Ein- und Auszahlungen“ im Sinne einer Abfolge ist keine Kausalbehauptung mehr; kausale Verwendungen bleiben markiert (Regressionstests).
- **Kapitel 7:** 26 Lösungen ohne Modellaufruf geprüft (4 numerisch unabhängig nachgerechnet, 22 gegen Folientext und Gesetzeswortlaut), Prüfskript per Mutationstest abgesichert; sieben Lösungsansätze gegen die Vorlesung geprüft; Errata E4/E5 wortlautgenau zu § 5a Abs. 3 GmbHG.

# Exam Mastery v0.14.1-preview

## Kapitel 7 ohne neue Modellgenerierung abgeschlossen (soweit maschinell möglich)
- **B14 Planung:** Fallstudien- und Anhangseiten beenden Session-Labels; layoutbedingt abgeschnittene Aufgabenkopien werden verworfen (Ursache von Exit 2 in Kapitel 7).
- **`recover-chapter <id>`:** veröffentlicht ein Kapitel nach einer reinen Entfernungs-Planänderung aus den gespeicherten Rollenantworten neu – ohne Modellaufruf, mit Nachweis, dass der neue Kontext exakt dem alten minus der entfernten IDs entspricht, transitiver Bereinigung abhängiger Blöcke und allen Gates. Verweigert bei jeder Hinzufügung oder Änderung.
- **Errata (`errata/<kapitel>.json`, Schema em-errata-v1):** begründete redaktionelle Korrekturen mit Rechts-/Quellengrundlage, nur bei eindeutigem Alttext, sichtbar in Publish-Report, Dossier und LIES_MICH. Keine Review-Wirkung.
- **Coverage:** Eine Kompetenz, die die Planung selbst als Titelfolien-Überschrift ohne Lernziel einstuft, zählt nicht als Lücke – nur wenn alle verknüpften Prüfungsfragen beantwortet sind.
- **Korrekturen:** „aamp;“ in den Quellenabbildungen; LIES_MICH nennt nur tatsächlich ausgelieferte Dateien und korrekte Zählungen.

## Interaktive Labs: Lernsequenz in sieben Phasen (DR-1.2, Regeln L11–L15)
- Vorhersagen mit Sicherheitsangabe und kalibrierter Rückmeldung; Beobachten; Erklären (eigene Erklärung vor der Expertenerklärung, Begriffs-Lesehilfe); Erkunden (Aufträge, live gegen den Simulationszustand geprüft, in Python als lösbar nachgewiesen); Üben (Rechen- und Konzeptaufgaben mit Fehlvorstellungs-Feedback); Übertragen; Sichern (eigene Zusammenfassung, dann Kernaussagen, Verweis auf Anki).
- Fortschrittsleiste in Schritten (nie ein Prozentwert der Beherrschung), klebend mit Scroll-Abstand, mobil kompakt.
- Kompetenzbezeichnungen statt IDs im Lab-Kopf.
- Vierter Katalogeintrag Van Westendorp (aus v0.14.0) mit derselben Sequenz.

# Exam Mastery v0.14.0-preview

## Local preview addition: fourth reference lab (Van Westendorp)
- Uses the existing Python reference models, shared JavaScript runtime, em-lab-v1 and chapter publisher.
- Two explicit range conventions, segments, what-if changes, checked tasks and offline SVG/PDF fallback.
- Course competencies and method anchors come from the real ENT plan. All 240 starting responses are explicitly synthetic, never lecture findings.
- Lab/browser regression: 29 tests PASS; existing chapter-publishing regression: 6 tests PASS. No new model production.
- **No full chapter E2E release:** existing coverage FAIL, didactic A1 FAIL and semantic review remain open; product exit 2 is retained.

## New in 0.14.0: interactive learning core
- **Interactive labs** (schema em-lab-v1):
  - reference models in Python (`labs/models.py`): cash flow and liquidity, a 2-2-1 neural network with backpropagation, and the lecture's risk matrix;
  - a dependency-free browser runtime (`templates/em_labs.js`);
  - a learning sequence of prediction with a reason, then simulation, explanation, hint ladder, gated solution and transfer task;
  - offline use, a CSP pinned by hashes, no eval and no network access;
  - a static SVG figure for PDF and print.
- **Labs in the chapter path:** the author role requests labs as data; the engine builds them deterministically. The textbook shows the static figure, and `Lernumgebung/index.html` links the documents and labs and shows the observed progress of this browser (tutor-protocol states, never a mastery %).
- **`visuals --all`:** a deterministic pre-triage of every page whose figure may carry content.
- **New commands:** `course-title` sets the display title on covers; the card identity stays bound to the course folder.
- **Readable source names:** an artefact like `aamp;` in a file name shows as `&`.
- **Dossier:** content coverage (taught and practised) is reported separately from exam evidence (an official question exists).
- **References:** `learning_science.md` (DR-1.2, with literature checked in this session), `capabilities_and_tools.md` and `resource_efficiency.md` (measured values).
- **SKILL.md section 9:** learning modes Lecture, Tutor, Practice and Mentoring, all on one competency structure.
- **Fixes from the corrected chapter-7 run:** a display title must never re-key Anki cards (test added).

# Exam Mastery v0.13.2-preview

## Fixes in 0.13.2, found by the first end-to-end run with the agent provider
The run took one chapter of a real course copy through all six model roles inside the Claude Code session, with no
second model process.
- **Visuals import:** numbers in figure readings may now be JSON numbers. Before, the import crashed with an AttributeError.
- **Session identity:** a folder with one lecture and the schedule now keeps the session of its unique schedule row. Before, the run stopped with SESSION_IDENTITY_UNRESOLVED.
- **Item-derived competencies:** a competency derived from an item of another session moves to the chapter of that session, or to the visible exam-gap scope when that lecture is absent. Before, it was attached to an unrelated chapter by word overlap (in the full course: 9 competencies; in a one-lecture folder: 58).
- **Authored cards:** the cards of the author role now reach the content AST. Before, only derived cards were published.
- **Answer-consistency gate:** it now reads a minus sign. Before, every negative result counted as "not stated".
- **Derived card keys:** they are transliterated to ASCII (ä to ae). Before, keys with umlauts were dropped by rule C5.
- **Rule A1:** it counts an item whose wording demands the operation ("Berechnen Sie … und erklären Sie …").
- **Rule S2:** it no longer reads the scale label "significant" as a statistical claim.
- **Mock exam overview:** topics are cut at a word boundary, and the chapter number comes from the evidenced session.

# Exam Mastery v0.13.1-preview

## Fixes in 0.13.1: release hardening (no new features)
- **Release smoke test** (`engine/scripts/release_smoke_test.sh <archive>`): checks only the shipped archive, under a temporary HOME. It covers:
  - install, CLI, skill discovery for Claude Code and Codex, host check;
  - read-only `status` and `update`, with a check that the course folder stays unchanged;
  - publishing of the math, law and ML fixture books, with all checks, PDF navigation, embedded fonts and no raw TeX;
  - Anki export and reimport;
  - agent hand-over without a model call;
  - uninstall and reinstall, with config, outputs and Anki state kept.
- **Host check:** without a provider, the result is now `HOST_READY_NO_PROVIDER` instead of `HOST_NOT_READY`. `status`, `update` and `visuals` work in that state; only production needs the one-time setup.
- **CLI:** `exam-mastery --help` shows the usage. Before, it was treated as a production call. The setup hint now names `--provider agent` first.
- **Figure status from one file** (`figure_status.py`): the source-figure PDF, the dossier and the competency matrix read the same file. Each figure has one of four states: integrated, no additional content, decorative, not reliably evaluated.
- **Unique `update-` and `visuals-` folder names:** two calls in the same second used to share a folder.
- **Test diagnostics:** two tests that publish through Chromium now report the publish error instead of a bare `StopIteration` or PASS mismatch.
- **Optional sample outputs:** these are bundled only when `SAMPLES=<dir>` is set. The runtime needs none of them (0.13.0 shipped without them: 0.56 MB instead of 5.9 MB).

# Exam Mastery v0.13.0-preview

## New in 0.13.0: semantic consistency checks (DR-1.1)
An independent review of the Funding v2 package found five subject-matter errors that all DR-1.0 checks had passed.
0.13 adds checks for these error classes. The checks work on any course, not only on these five passages.

- **`semantic_checks.py`**, run at every publish. Results go to `publish/semantic_checks.json` and to the dossier dimension `semantic_consistency`.
  - S1: count claims in the text are checked against their table.
  - S2: statistical inference needs a sample size, a test or an interval, or an explicit hedge.
  - S3: a cause asserted for a source inconsistency or a pattern needs evidence.
  - S4: term conflicts between table columns and text.
  - S5: a legal subsumption needs stated facts or assumptions; a prohibition stated without its exception is marked for review.
  - S6: card numbers are checked against the book.
  - C6–C9: list size without a reason, explanation for mechanism cards, honest visual label, answer cue on the front.
- **REVIEW status:** where no reliable automatic decision is possible, the status is REVIEW. It is never counted as PASS.
- **PDF navigation:** the table of contents is clickable again. Internal links were lost when the cover was merged with the content.
- **Prompts:** B10 sections for the author, assessment and solution roles.
- **Tests:** `tests/test_b10_semantic.py` has 24 tests. Each pairs a defective case with its corrected one, across economics, law, mathematics and ML.
- **Not included:** image occlusion; any independent subject review.

# Exam Mastery v0.12.0-preview

## New in 0.12.0: product quality overhaul
- **Didactic rule set DR-1.0** (`skill/exam-mastery/references/didactic_rules.md`):
  - derived from verified sources (Roediger & Karpicke 2006; Dunlosky et al. 2013; Cepeda et al. 2006; Sweller 1988; Renkl & Atkinson 2003; Kalyuga et al. 2003; Chi et al. 1989; Rohrer & Taylor 2007; Hattie & Timperley 2007; Biggs 1996; Mayer; Wozniak 1999);
  - 18 rules, of which the deterministic ones run at every publish (`didactic_rules.py`);
  - the prompts of the author, assessment and solution roles carry them.
- **New typesetting** (`typeset.py`, `figures_svg.py`):
  - five separate documents with their own cover and page numbering: Lehrbuch, Arbeitsbuch, Musterlösungen, Probeklausur, Probeklausur-Lösungen;
  - table of contents with real page numbers, PDF bookmarks, MathJax formulas;
  - semantic boxes (definition, worked example, misconception, legal note, model limit);
  - reproducible SVG figures; OFL fonts (Source Serif 4, Source Sans 3, JetBrains Mono).
- **Mock exam integrity** (`exam_check`, blocking):
  - only complete items with points and a matching rubric; no evidence-gap items;
  - labelled as self-designed; no invented official duration.
  - This replaces the page-cutting that put an excluded item (a-17) and wrong page numbers into the old exam.
- **Numeric checks** (`numeric_checks.py`): every written equation and every table total is recomputed. A documented source inconsistency is shown as DOCUMENTED.
- **Anki v2** (`anki_v2.py`):
  - cards: authored cards checked by rules C1–C5;
  - note types: Basis (v2) and Lückentext (v2) with fixed ids;
  - identity: semantic GUIDs (course, chapter, concept key), so re-exports update notes instead of duplicating them;
  - design: calm light and dark mode, bundled font, figures on the answer side;
  - verified with a real update test: reviews through Anki's scheduler, an edited export and a double import leave scheduling and review history unchanged.
- **Pipeline:** every model-produced chapter goes through `book_model.py` into the new typesetting and deck. Without authored cards, only definition and misconception cards are derived; cards that fail the rules are dropped and reported. The dossier adds the dimension `didactic_rules` and uses the numeric checks.
- **Reference product:** Funding a Venture v2 (private course, not in this archive).
  - textbook 26 pages, workbook 12, solutions 15, exam 6 + solutions 7;
  - 54 notes / 59 cards;
  - 29/29 rules and 44/44 computations pass.
- **Demonstrations** (`fixtures/b9_domain_books.py`, sample_output): mathematics (proof), law (Gutachtenstil), ML (pseudocode). They are self-written standard knowledge, not course content.

# Previous release: v0.11.0-preview

## New in 0.11.0
- **Figures read by the calling agent (`exam-mastery visuals`):**
  - The engine lists every slide whose figure blocks a competency, with its rendered image and text layer.
  - The agent (e.g. Claude Code) reads the images with its own image understanding and writes `em-visual-evidence-v1`: per page CONTENT / DECORATIVE / UNREADABLE, atomic statements with a confidence, every number declared, every shown total written as an arithmetic check.
  - The engine checks the evidence deterministically:
    - the render hash must match;
    - every number must be declared, and is marked confirmed or "nur im Bild" against the text layer;
    - totals are recomputed;
    - LOW-confidence statements are never taught.
  - Accepted readings become labelled `visual_transcription` elements in the plan and the ContentAST (`AUTO_VISION_TRANSCRIBED`). The source-number gate then accepts only numbers from these readings.
  - A changed slide invalidates its reading.
- **Entrepreneurship course:** all 38 figure slides of the 37 previously excluded competencies were read in a Claude Code session.
  - 29 pages carry content: 109 statements accepted, 1 LOW statement kept out, 15/15 arithmetic checks pass.
  - 9 pages are decorative.
  - 37/37 competencies are now producible.
- **Provider `agent`:** the calling agent answers the model roles itself, so no second model process starts. The run stops with exit 4, the agent writes the answer, and the same command resumes.
- **One skill copy for Claude Code (`/exam-mastery`) and Codex (`$exam-mastery`):** the installer links both `~/.claude/skills` and `~/.agents/skills` to the library copy.

# Previous release: v0.10.1-preview

## New in 0.10.1
- **Commands:**
  - `exam-mastery status` (read-only) and `exam-mastery update` (offline change check).
  - `exam-mastery update --produce` regenerates only the changed and new chapters, each in a new run. Earlier materials are never modified.
  - Without a folder argument, the current directory is used; a folder without lecture files is refused.
- **Change detection:**
  - File fingerprints and per-chapter content fingerprints (competencies plus the extraction hash of every source element).
  - Chapter states: CURRENT, STALE, NEW, SOURCE_REMOVED.
  - Tested offline on synthetic courses: no change, new lecture, changed slide, removed or replaced lecture, single-chapter isolation, quota/failure stop, Anki re-export.
- **Skill:**
  - `/exam-mastery [folder | status | update]` with argument handling.
  - The provider setup is part of the skill workflow.
- **Installer:**
  - `--library DIR` makes the library the canonical skill location; the host gets a symlink.
  - Updates keep the config, outputs and Anki state; a changed skill folder is backed up before it is replaced.
- **Claude as model provider:** refused by setup with a clear message. The adapter exists but was never validated live.

# Previous release: v0.10.0-preview

**Technical preview.** Installable and usable; materials are technically checked model drafts. Not academically
validated: no independent subject review exists for any course.

## What works
- **One command:** `exam-mastery "<lecture folder>"` after a one-time provider setup (Codex CLI with a ChatGPT login, or an optional Gemini API key). No approval files, hashes or chapter selection.
- **Automatic planning:** inventory and fidelity checks, curriculum and exam analysis, subject-adaptive chapter planning.
  - Low-risk issues (no past exams, possible chapter merges, heading-only topics, figures next to readable text) are resolved automatically and labelled.
  - Only unresolvable order or eligibility conflicts go to a human.
- **Production:** author → assessment → solutions → semantic review → risk review → at most one revision. The revision returns only changed objects.
- **Deterministic gates between roles:**
  - source anchors and source numbers;
  - step arithmetic;
  - totals of multi-slide examples;
  - text-only scope;
  - checks re-run after the revision.
- **Publishing:**
  - `LERNMATERIAL/<chapter>/` contains `1_Lehrbuch.pdf`, `2_Arbeitsbuch.pdf`, `3_Musterloesungen.pdf`, `4_Probeklausur.pdf` (with solutions), `5_Quellenabbildungen_nicht_ausgewertet.pdf`, `kapitel.html`, the Anki deck (export and re-import tested in an isolated collection) and `LIES_MICH.md`.
  - Newly designed points are labelled as not official.
  - Questions whose source is missing are kept out of the mock exam.
- **Budget:** fail-closed per run (requests, time, tokens; Gemini also cost). Contract repairs count as requests.
  - A provider quota stop ends the run cleanly; restarting resumes it.
  - `exam_mastery.recover` reuses recorded outputs instead of paying for them again.
- **Agent Skill:** `skill/exam-mastery` with `SKILL.md`, a read-only host check, `install.sh` and `uninstall.sh`.

## Funding chapter (real course, private; not in this archive)
- **Delivered:** a complete preview with all five product files and an Anki deck (20 cards).
- **Generated by Codex `gpt-6.1-sol`:** author, items and solutions (live, 3 calls), plus semantic and risk review (live, 2 calls).
- **Two revision attempts failed:**
  - one hit the 600 s process limit;
  - one hit the account quota.
- **Revision done in a Claude Code session instead.** It was written as a documented delta (`Aenderungsprotokoll/`) and went through the same contracts and gates.
- **Checks:** all machine checks pass, and all 7 reviewer probes pass (mature lead: 75 k€ gap).
- **Dossier:** formulas/figures, Anki and rendering PASS; subject correctness, math set-up, didactics and items NOT_TESTED (no independent review); coverage FAIL, because 41/45 competencies are taught but only 5 are backed by an official exam question with a matching operation.

## Known limitations
- **Subject validation:** model reviews only. The Funding semantic review rated all 37 blocks UNCLEAR, which is not a pass.
- **Images:**
  - Figures are not interpreted by the engine. The figures of 24 Funding slides are kept as page images, unevaluated.
  - 37 course competencies whose content lives only in figures are not produced (`VISUAL_REVIEW_REQUIRED`, PDF with all of them).
  - The Gemini adapter refuses image input.
- **Untested hosts and live paths:**
  - Agent hosts: the skill uses the standard `SKILL.md` folder layout and is installed for Claude Code. Loading inside a host was not tested; other hosts are untested.
  - The delta revision has not yet run live against a provider.
  - The Gemini path has no live evidence.
- **Cost and platform:** Codex usage is not cost-capped by the engine (subscription quota). Tested on macOS with Python 3.12 and Node.js only.
- **Licences:**
  - The project has no LICENSE; the owner must choose one before any distribution.
  - `pymupdf` (core PDF handling) is AGPL-3.0 or commercial, and `anki` is AGPL-3.0. A sold or hosted product needs AGPL-compatible terms or a commercial PyMuPDF licence.
  - See `THIRD_PARTY_LICENSES.md`.
