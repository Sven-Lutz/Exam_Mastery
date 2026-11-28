# Lernstand: woher jede Zahl kommt und was sie nicht misst

Bezug: `docs/MASTERY_LEARNING_STANDARD.md` §5.6 (Lernstand und Statistik), §3 (Evidenzlage), §2.2 (Lernkette).
Code: `exam_mastery/mastery/ledger.py` (Python) und `exam_mastery/templates/mastery_ledger.js` (Browser). Beide liefern
für dieselben Eingaben dasselbe Ergebnis (`tests/test_mastery_ledger.py`). Zustand und Evidenzbasis rechnet die
getestete Übungslogik (`learning/policy.py`, im Browser `EMT.kcStatus` / `EMT.kcEvidenceBasis`).

**Grundsatz.** Alle Werte sind beobachtete Lernhandlungen in *einem* Browser unter *einer* Adresse
(`http://127.0.0.1:8765`). Sie sind Näherungsanzeigen im Produkt, keine Messung von Lernen oder Können. Es gibt
keinen Prozentwert, keine Punktzahl, keine Serien. Ob Mastery Lernen verbessert, ist nicht untersucht (`NOT_RUN`).

## 1. Ein Register über alle Speicher (`mastery-ledger-v1`)

Mastery speichert jede Handlung dort, wo sie passiert. Das Register liest alle Speicher, **ändert keinen** und baut
daraus bei jedem Aufruf eine geordnete Liste. Es ist abgeleitet und aus jeder Sicherung reproduzierbar.

| Speicher | Inhalt | im Register |
|---|---|---|
| `em-tutor-v1` | Übungsstrecken (z. B. Backpropagation): Versuche, Hinweise, Lösung, Tutor-Brief, geführte Hilfe, gezeigtes Beispiel | alle Lernhandlungen; Entscheidungen der Übungslogik (`decision`) werden ausgelassen und gezählt |
| `em-practice-v1` | Interaktiv (Explorable) je Einheit und Aufgabenfassung: Entscheidungsprotokoll `policy` (mit Prüfergebnis) und Aktionsprotokoll `events` (ohne Antworten; das ist der Export `em-practice-evidence-v1`) | `policy` vollständig; ein `events`-Eintrag, der dieselbe Handlung wie ein `policy`-Eintrag beschreibt (gleiche Aufgabe, gleicher Typ, ≤ 2 s), wird als `mirror_duplicate` ausgelassen; übrige `events`-Einträge bleiben, gekennzeichnet |
| `em-motion-v1` | Mastery Motion: Vorhersagen, Aufdecken, Regler-Aufträge | alle, als Lernhandlung ohne Kompetenznachweis |
| `em-learn-v2` | ältere Kapitel-App, falls unter dieser Adresse genutzt | alle, ohne Kompetenzzuordnung (nur Zeitleiste) |

**Warum war ein exportiertes `em-practice-evidence-v1` leer (`events: []`)?** Weil im Explorable dieser Einheit noch
nichts bearbeitet war. Die Backpropagation-Übungsstrecke speichert ihren Verlauf getrennt in `em-tutor-v1`. Die Seite
„Lernstand → Woher kommen die Daten?“ zeigt je Speicher: gelesen = in der Zeitleiste + ausgelassen (mit Grund).

Jeder Eintrag trägt seine Herkunft: `id = <speicher>#<datensatz>#<liste>#<index>` (zeigt auf den unveränderten
Originaleintrag), Produkt, Einheit/Kurs/Kapitel, Aufgabe, Aufgabentyp, Kompetenz, Hilfeart, Ergebnis,
`assist` (ohne/mit Hilfe), `source` (wer geprüft hat: `deterministic` = Regel, `unjudged` = Freitext unbewertet,
`self_report` = Selbstauskunft, `agent_judgement` = Sprachmodell außerhalb von Mastery), Rolle (Übung,
Nachweisaufgabe, spätere Prüfung) und Zeitqualität (`exact`, `date_only`, `missing`, `invalid`, `future`).
Unbekannte, alte, unlesbar oder in der Zukunft datierte Einträge bleiben in der Zeitleiste, zählen aber nie als
Nachweis. Antworttexte übernimmt das Register nicht.

## 2. Was jede Zahl bedeutet

Auf der Seite ist jede Zahl anklickbar („Woher?“): Regel, die zugehörigen Register-Einträge und „Was das nicht misst“.

| Zahl | Regel | misst nicht |
|---|---|---|
| Versuche ohne Hilfe | Versuche der Kompetenz (nicht lesbare Eingaben ausgenommen) ohne vorherige Hilfe zur selben Aufgabe und ohne Hilfe zur selben Kompetenz in den 20 h davor; richtig oder falsch egal | Richtigkeit; Können außerhalb von Mastery |
| Versuche mit Hilfe | dasselbe mit vorheriger Hilfe (Hinweis, Lösung, Tutor-Brief, geführte Hilfe, gezeigtes Beispiel) | wie viel die Hilfe beitrug |
| davon Freitext | Versuche mit unbewertetem Freitext; ändern keinen Zustand | fachliche Qualität |
| wiederholt | Versuche an einer Aufgabe, die schon einen Versuch hatte | ob die Wiederholung besser war |
| Hilfen je Art | Hilfe-Ereignisse zu Aufgaben der Kompetenz bzw. mit dieser Kompetenz | ob die Hilfe verstanden wurde |
| selbstständig richtig | regelbasiert richtige Versuche ohne Hilfe, lesbare Zeit, aktuelle Aufgabenfassung | Behalten, Transfer |
| erste / letzte selbstständige Lösung | frühester / jüngster solcher Versuch | ob es heute noch sitzt |
| späterer Nachweis | erste selbstständige Lösung einer *anderen* Aufgabe ≥ 20 h nach einer früheren selbstständigen Lösung (echte verstrichene Zeit); Stunden ab der frühesten passenden Lösung | langfristiges Behalten (eine Stichprobe) |
| Zustand | `kc_status`: noch nicht geprüft → begonnen → mit Hilfe gelöst → heute ohne Hilfe → spätere Prüfung fällig → an einem späteren Tag erneut gelöst | keine Note, keine Wahrscheinlichkeit |
| Evidenzbasis | `kc_evidence_basis`: nur Auswahlaufgaben = nur Wiedererkennen; Zahl/Ausdruck/Rechenschritte = Produktion | Beweis- oder Begründungskonstruktion |
| Abdeckung je Kapitel | Kompetenzen mit / ohne selbstständig richtige Produktion (Übungsstrecke oder Interaktiv); ohne Quote | vollständige Beherrschung |
| Motion | Vorhersagen, davon zutreffend, aufgedeckt, Aufträge, davon erreicht | Können: Vorhersagen sind Lernhandlungen |

Der Bezugszeitpunkt für „spätere Prüfung fällig“ ist der Seitenaufruf (im Export: Erstellung).

## 3. Optionale Anki-Statistik (nur mit Freigabe)

Mastery öffnet die Anki-Sammlung nie. Wer möchte, exportiert in Anki selbst die Stapel „Exam Mastery::…“ als
Anki-Stapelpaket (`.apkg`) **mit Planungsdaten** und ohne Medien, setzt auf der Lernstand-Seite das Häkchen
„Ich erlaube …“ und wählt diese Datei. Der lokale Server liest sie in einem temporären Ordner (SQLite, nur lesend;
das aktuelle komprimierte Format über eine Wegwerf-Sammlung der anki-Bibliothek), löscht die Kopie und speichert nur
Zählwerte in `~/Mastery/anki-stats/latest.json` (nie als Datei ausgeliefert, jederzeit „entfernen“). Gezeigt werden
je Stapel und Karte: Wiederholungen (Antworten im revlog, ohne manuelle Umplanung), Lapses, aktuelles Intervall,
Status, letzte Wiederholung. Beschriftung: **„Anki-Planungsdaten, kein Kompetenznachweis“** (R8-POL-12). Unterstützt:
`.apkg` (alt und aktuell), `.colpkg` mit „Unterstützung für ältere Anki-Versionen“. Nicht unterstützt: komprimiertes
`.colpkg`, CSV/Text (enthält keine Wiederholungshistorie).

## 4. Sicherung

„Sicherung → Als Datei exportieren“ enthält die Speicher (`mastery-state-v1`, re-importierbar, jetzt auch
`em-learn-v2`) und zusätzlich `derived` mit Register (`mastery-ledger-v1`) und Zusammenfassung
(`mastery-progress-v1`). `mastery export` (`mastery-backup-v1`) enthält dasselbe aus der Server-Kopie plus die
Anki-Statistik, falls geladen. Beim Import zählt nur `storage`; `derived` wird neu berechnet.

## 5. Grenzen

Ein Browser, eine Adresse: andere Browser, Geräte oder Ports haben einen eigenen Lernstand (Sicherung nutzen). Die
Server-Sicherung ist eine Kopie desselben Browsers, kein zweiter Bestand. Kapitel-App-Einträge haben keine
Kompetenzzuordnung in Mastery. Quellenabdeckung je Kompetenz (welche Vorlesungsstelle geübt wurde) zeigt der
Lernstand noch nicht. Die Lernwirkung ist nicht gemessen.
