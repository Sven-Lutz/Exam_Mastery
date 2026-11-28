# Kurs importieren: vom Vorlesungsordner zum Kapitel

Stand 2026-11-27 · Auftrag: Issues #49, #51 · Vertrag: `docs/COURSE_TO_MASTERY_CONTRACT.md`

Mastery übernimmt einen lokalen Kursordner (Folien, Skripte, Übungsblätter, Lösungen, Literatur, Altklausuren,
Notebooks), zeigt, was darin erkannt wurde, prüft die Vollständigkeit, schlägt Kapitel und Kompetenzen vor, bereitet je
Kapitel ein Authoring-Paket vor und verfolgt jedes Kapitel bis zu den vier gebauten Produkten. Es braucht weder eine
vorbereitete JSON-Datei noch eine Codeänderung.

## 1. In der App (empfohlen)

1. `bin/mastery` starten, oben **Kurse** wählen.
2. Den Ordnerpfad einfügen (Finder: Ordner markieren, ⌥⌘C kopiert den Pfad) und optional einen Titel eintragen.
   **Importieren** klicken.
3. Mastery zeigt:
   - **Inventar**: jede Datei mit Art (Vorlesungsfolien, Skript, Übung, Lösung, Klausur, Literatur, Notebook,
     Sonstiges; die Begründung steht im Tooltip), Seiten/Folien, Seiten mit Text, Seiten, die Bildverständnis brauchen
     (Abbildungen, Formeln, nur Grafik), Status (gelesen, nicht lokal, nicht unterstützt, nicht lesbar, Duplikat).
   - **Vollständigkeit**: Lücken in der Vorlesungsnummerierung („Vorlesung 03 fehlt“), verschiedene Fassungen derselben
     Vorlesung, Übungen ohne Lösung, Kapitel ohne Übung, nicht unterstützte oder unlesbare Dateien, Seiten ohne
     Textebene, Duplikate – jeweils mit Datei (und Seite).
   - **iCloud**: Dateien, die nur als iCloud-Platzhalter vorliegen, werden **nicht geöffnet** (Öffnen würde sie
     herunterladen) und als „nicht lokal verfügbar“ aufgeführt. Erst ein Klick auf „… aus iCloud herunterladen“ (Ihre
     Zustimmung) lädt sie mit `brctl download`; nichts wird gelöscht oder verändert.
   - **Kapitelplan** (Vorschlag): ein Kapitel je Vorlesung bzw. Skriptdatei; Übungen nach Titel, Inhalt oder Nummer
     zugeordnet (die Grundlage steht dabei); Lösungen folgen ihrer Übung; Altklausuren gehören zu allen Kapiteln.
     Titel ändern, Kapitel überspringen, zusammenführen und umsortieren – **Planänderungen speichern**. Die Änderungen
     stehen in `course.json` (`plan_overrides`) und überleben jeden Neuimport.
   - **Kompetenzen** je Kapitel: als „Vorschlag“ gekennzeichnet, deterministisch aus Lernziel-Folien, sonst aus
     Folien-/Abschnittstiteln, mit Datei und Seite. Kein Modell beteiligt.
4. Je Kapitel läuft die Statuskette
   `Nicht erarbeitet → Paket bereit → Erarbeitet (KI: Claude-Code-Sitzung | Mensch) → Gebaut → Prüfung ausstehend`:
   - **Paket erstellen** schreibt `packet.json` (Text aller Seiten, Seitenbilder für Abbildungen/Formeln, zugehörige
     Übungen, Lösungen, Klausurseiten, Warnungen).
   - **Erarbeiten** zeigt den genauen Auftrag für eine Claude-Code-Sitzung (siehe 3.) oder schreibt ein Mensch.
   - **Bauen** prüft `unit.json` mit den Validatoren der Engine, baut Lehrbuch, Arbeitsbuch, Anki-Paket und Interaktiv
     und trägt das Kapitel als private Einheit in die Bibliothek ein. Es erscheint auf der Startseite unter seinem Kurs.
   - **Neu einlesen** erkennt geänderte, neue und entfernte Dateien und markiert betroffene Kapitel als „Quellen
     geändert“. Lernstand, `unit.json` und gebaute Produkte bleiben unverändert.

Der Server nimmt nur absolute Ordner innerhalb Ihres Benutzerordners an, nie das Mastery-Repository oder die
Bibliothek selbst, und liest den Kursordner nur.

## 2. Im Terminal

```sh
bin/mastery import ~/Studium/Kurs --title "Mein Kurs"     # Inventar, Warnungen, Kapitelplan
bin/mastery import ~/Studium/Kurs --materialize           # dasselbe, iCloud-Platzhalter mit Zustimmung laden
bin/mastery courses                                       # alle Kurse
bin/mastery course <kurs>                                 # Zustand: Inventar, Warnungen, Kapitel, Status
bin/mastery plan <kurs>                                   # Kapitelplan nach Änderungen in course.json neu berechnen
bin/mastery packet <kurs> <kapitel>                       # Authoring-Paket schreiben/erneuern
bin/mastery build-chapter <kurs> <kapitel>                # unit.json prüfen, vier Produkte bauen, eintragen
bin/mastery reimport <kurs> [--materialize]               # Änderungen erkennen, betroffene Kapitel markieren
```

Alles liegt unter `~/Mastery/courses/<kurs>/` (Aufbau: Vertrag). Ein `packet.json`, das nicht vom Import stammt, wird
nie überschrieben; das neue Paket heißt dann `packet.import.json` (`--force` ersetzt bewusst).

## 3. Erarbeiten: ganzer Kurs auf Knopfdruck (KI, nur mit Ihrer Freigabe)

Import, Inventar, Vollständigkeit, Kapitelplan, Pakete, Validierung und Bau sind **offline und ohne Modell**. Das
Schreiben eines Kapitels (`unit.json`: Lehrtext, Herleitungen, Aufgaben mit Lösungen, Karten, Explorable) braucht ein
Modell. Mastery orchestriert das für den **ganzen Kurs**; niemand muss je Kapitel einen Auftrag kopieren.

**In der App** (Kurse → Kurs → „Kurs erarbeiten (KI)“):
1. Anbieter wählen – **Claude Code (Ihr Abo)** oder **Manuell (Mensch)** –, Höchstzahl der Modellaufrufe eintragen,
   Zustimmung ankreuzen, **Freigeben**. Ohne diese Freigabe startet Mastery keinen einzigen Aufruf.
2. **Kurs erarbeiten** (bzw. **Fortsetzen** / **Kurs aktualisieren**) startet die Erarbeitung im Hintergrund.
   Die Seite zeigt je Kapitel Schritt, Status, Versuche und den letzten Prüfbefund; **Anhalten** beendet sie.

**Im Terminal:**
```sh
bin/mastery author <kurs> plan                                  # was zu tun ist und wie viele Aufrufe höchstens
bin/mastery author <kurs> authorize --max-runs 20               # Freigabe: Claude Code (Abo), höchstens 20 Aufrufe
bin/mastery author <kurs> run [--chapter <id>] [--max-steps N]  # erarbeiten / fortsetzen (Vordergrund)
bin/mastery author <kurs> run --background --wait-for-reset     # im Hintergrund, wartet Limits ab
bin/mastery author <kurs> status | stop
bin/mastery author <kurs> check-draft --chapter <id>            # Entwurfsprüfung (nutzt auch der Autor selbst)
```

**Ablauf je Kapitel** (`exam_mastery/mastery/authoring.py`): Paket (neu, wenn Quellen geändert) → Auftrag an den
Anbieter; er schreibt nur nach `chapters/<id>/draft/` → **Entwurfsprüfung**: Schema, `unit_id` (Anki-Identität),
Prüfprotokoll in `authoring.json`, maschinelle Qualitätsgates; Fehler und Blocker gehen als Rückmeldung in einen
zweiten Versuch → bisherige Fassung nach `versions/` archivieren → Entwurf atomar übernehmen → vier Produkte bauen →
Qualitätsgates. Ein Bau mit Blockern oder schweren Befunden führt zu **einer** automatischen Überarbeitung mit den
Befunden; bleibt ein Blocker, steht das Kapitel als „Qualitätsblocker“ offen und wird nicht als fertig gemeldet.
Geänderte Quellen (`Neu einlesen`) ergeben den Schritt „aktualisieren“: der Autor ändert nur das Betroffene und behält
die IDs (Lernverlauf in Anki bleibt).

**Transparenz und Grenzen:**
- Anbieter `claude_code_cli` ruft `claude -p` mit Ihrer Anmeldung auf. Der Prozess erhält keine Umgebungsvariable mit
  Schlüssel oder Token; meldet Claude Code trotzdem einen API-Schlüssel als Anmeldung, bricht Mastery ab
  (`paid_key_refused`). Keine Websuche (Standard), keine MCP-Server, Schreibzugriff nur im Kapitelordner.
- Jeder Aufruf zählt gegen die Freigabe (`authoring/authorization.json`) und hinterlässt einen Laufbericht
  (`chapters/<id>/authoring/runs/<lauf>/`: Auftrag, Protokoll, Dauer, Ergebnis der Entwurfsprüfung).
- Meldet der Anbieter ein Nutzungslimit, pausiert der Lauf bis zur gemeldeten Freigabe; früher startet Mastery nicht
  (`--wait-for-reset` wartet und setzt dann fort). Ein Kapitel braucht je nach Umfang einen erheblichen Teil eines
  Nutzungsfensters; der Plan nennt die Höchstzahl der Aufrufe.
- Die Qualität des Inhalts belegt das nicht: Ergebnisse bleiben `HUMAN_REVIEW_PENDING`, Lernwirkung `NOT_RUN`.
- Anbieter `command` (nur Terminal) ruft ein von Ihnen genanntes lokales Programm auf, das den Auftrag von stdin liest;
  `manual` legt den Auftrag als `authoring/ORDER.md` für einen Menschen ab.

## 4. Was funktioniert, was experimentell ist

| Bereich | Stand |
|---|---|
| Import, Inventar, PDF (Text, Titel, Abbildungen, Formeln je Seite), PPTX/DOCX/Notebook/Markdown/LaTeX über die `fidelity`-Parser | funktioniert, getestet |
| iCloud-Platzhalter erkennen, nur mit Zustimmung laden | funktioniert (Test simuliert das Flag; am echten RL-Kurs geprüft) |
| Vollständigkeit: Nummerierungslücken, Fassungskonflikte, Übung ohne Lösung, Kapitel ohne Übung, Duplikate, Formate | funktioniert; Heuristik nach Dateinamen, Titeln und Inhalt |
| Kapitelvorschlag, Zuordnung von Übungen | Heuristik; die Grundlage (Titel/Inhalt/Nummer) wird angezeigt, Plan ist editierbar |
| Mathematik-Kurse (zweiter Kurs, Lineare Algebra) | Dateinamen wie „Folien 12“, „Loesungsvorschlag 3“, „Blatt 1 (1)“ werden nummeriert; Kapiteltitel von der Titelfolie („Vorlesung 19: …“, abweichende Nummer wird gemeldet); ein langes Skript mit PDF-Inhaltsverzeichnis wird in Abschnitte geteilt und den Vorlesungen in Kursreihenfolge zugeordnet (Abschnitte ohne Vorlesung werden eigene Kapitel); Lösungen nur innerhalb ihrer Serie (Übungsblatt ≠ Tutorium); nummerierte Übungsserien werden monoton in Kursreihenfolge zugeordnet, Vorlagenwörter der Blätter zählen nicht; TeX-Textartefakte („Vektorr¨aume“, „̸ =“, „7→“, Ligaturen) werden repariert; Kompetenzvorschläge aus benannten Sätzen/Definitionen |
| Kompetenzvorschläge | einfache Heuristik aus Lernzielen, benannten Sätzen/Definitionen und Folientiteln; nur Vorschlag |
| Paket, Validierung, Bau, Eintrag in die Bibliothek, stabile Anki-Identität, Neuimport mit „veraltet“ | funktioniert, getestet |
| Kursweite Erarbeitung (Freigabe, Entwurfsprüfung mit Rückmeldung, Versionen, Limit-Pause, Aktualisieren) | funktioniert, getestet mit Test-Autor; echter Claude-Code-Aufruf geprüft (Abo, Schreibrechte); ganzer realer Kurs noch nicht erarbeitet |
| Folienbilder für PPTX | nicht verfügbar (kein Renderer); Folientext wird übernommen |
| OCR für Scans | nicht verfügbar; Seiten ohne Textebene werden gemeldet und als Bild ins Paket gelegt (PDF) |
| Inhaltliche Qualität eines Kapitels | hängt von der Erarbeitung ab; nicht automatisch belegt |

## 5. Datenschutz

Kursmaterial und alles daraus Erzeugte bleibt auf diesem Rechner unter `~/Mastery`. Ins Repository gelangt nichts
davon; die Tests verwenden einen erzeugten Beispielkurs (`tests/course_fixture.py`).

### Seitenbilder und Kartenfeedback

Ein Paket erhält höchstens 100 gerenderte Seitenbilder und 100 Millionen Pixel, ein Kurs insgesamt 500 Bilder und 500 Millionen Pixel. Die Einzelgrenze beträgt acht Millionen Pixel. Seiten ohne Bild wegen eines erschöpften Budgets behalten ihren Text und erhalten im Paket den Status `budget_exhausted`. Paket und Kursansicht melden die Lücke.

Unter **Kurse → gebautes Kapitel → Anki-Karten und Feedback** erscheinen Frage und Antwort aus dem gebauten Anki-Paket. Rückmeldungen beziehen sich auf Kartenschlüssel, Kartenordinal und Paketversion. Sie liegen unter `$MASTERY_HOME/state/card-feedback/`. Der Qualitätsbericht zählt Rückmeldungen und betroffene Karten. Lernfortschritt und Anki-Wiederholungsintervalle werden hier nicht gemessen.

`bin/mastery export` sichert die Feedbackjournale zusammen mit dem serverseitigen Lernstand. Der Browserexport des Lernstands auf der Startseite erfasst den lokalen Browserzustand. Mit `bin/mastery card-feedback <kurs> <kapitel>` entsteht neben dem Paket eine aktuelle `feedback.json` für die nächste Autorenrunde. Freitext ist eine Rückmeldung von Lernenden. Nach fachlicher Prüfung die Karte in `unit.json` unter ihrem bisherigen Schlüssel überarbeiten. `bin/mastery build-chapter <kurs> <kapitel>` nennt die neu gestempelten Notizschlüssel. Beim Import in Anki aktualisiert eine solche Änderung die generierten Notizfelder. Persönliche Ergänzungen gehören in eigene Notizen.
