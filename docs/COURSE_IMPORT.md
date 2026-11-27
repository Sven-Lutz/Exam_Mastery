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

## 3. Erarbeiten: KI-gestützt, nicht offline

Import, Inventar, Vollständigkeit, Kapitelplan, Pakete, Validierung und Bau sind **offline und ohne Modell**.
Das Schreiben eines Kapitels (`unit.json`: Lehrtext, Herleitungen, Aufgaben mit Lösungen, Karten, Explorable) ist es
**nicht**: Es braucht eine **Claude-Code-Sitzung mit Ihrem Abo** (kein API-Schlüssel, keine bezahlten Aufrufe, keine
versteckten Modellaufrufe durch Mastery) – oder einen Menschen. Die App zeigt dafür bei „Paket bereit“ den Befehl und
den Auftrag zum Kopieren. Danach `authoring.json` (Autor `claude_code_session` oder `human`, Prüfprotokoll, offene
Punkte) daneben legen und bauen. Ergebnisse bleiben `HUMAN_REVIEW_PENDING`; Lernwirkung `NOT_RUN`.

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
| Folienbilder für PPTX | nicht verfügbar (kein Renderer); Folientext wird übernommen |
| OCR für Scans | nicht verfügbar; Seiten ohne Textebene werden gemeldet und als Bild ins Paket gelegt (PDF) |
| Inhaltliche Qualität eines Kapitels | hängt von der Erarbeitung ab; nicht automatisch belegt |

## 5. Datenschutz

Kursmaterial und alles daraus Erzeugte bleibt auf diesem Rechner unter `~/Mastery`. Ins Repository gelangt nichts
davon; die Tests verwenden einen erzeugten Beispielkurs (`tests/course_fixture.py`).
