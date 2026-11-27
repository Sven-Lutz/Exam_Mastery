# Mastery V1 – lokale Lernumgebung

Stand 2026-11-27 · Auftrag: Issue #49 · Architektur H-AB (deterministischer Evidenzkern, Vorlagen als Daten, kein
Laufzeit-Agent, kein Knowledge Tracing, kein eigener Scheduler, keine bezahlten Modellaufrufe).

Mastery V1 ist die kleinste vollständige Tageslernumgebung für **ein** anspruchsvolles KI/Mathe-Thema:
*Attention verstehen: vom Skalarprodukt zur gewichteten Information* (Scaled Dot-Product Attention, an Vaswani et
al. 2017 gebunden, synthetische Zahlen) mit der Übungsstrecke *Backpropagation* als Voraussetzung. Alles läuft
offline auf dem eigenen Rechner.

## 1. Start mit einem Befehl

```sh
bin/mastery            # = bin/mastery start
```

`start` erstellt die Bibliothek, wenn sie fehlt oder veraltet ist (Inhalts-Hash über Einheit, Übungsstrecke und
Engine-Dateien), stellt sie unter **http://127.0.0.1:8765/** bereit (nur lokal, Python-Standardbibliothek) und öffnet
den Browser. Beenden mit Ctrl+C.

| Befehl | Wirkung |
|---|---|
| `bin/mastery start [--port N] [--no-open] [--rebuild]` | erstellen falls nötig, bereitstellen, Browser öffnen |
| `bin/mastery build [--force]` | Bibliothek erstellen/aktualisieren |
| `bin/mastery build --unit /pfad/einheit.json [--slug s] [--track ml/backprop-track]` | private Einheit hinzufügen |
| `bin/mastery status` | Zustand der Bibliothek und letzte Server-Sicherung (JSON) |
| `bin/mastery export [--out datei.json]` | vom Server empfangenen Lernstand als Sicherung schreiben |

Gleichwertig: `python -m exam_mastery.mastery …` aus dem Repository. Python: `$MASTERY_PYTHON`, sonst `.venv` des
Checkouts, sonst `python3` (benötigt die Engine-Abhängigkeiten inkl. Node-MathJax-Laufzeit für die PDFs).

**Bibliothek:** `~/Mastery` (oder `$MASTERY_HOME`). Mastery weigert sich, in das Engine-Repository oder das installierte
Paket zu schreiben. **Port:** Der Browser speichert den Lernstand pro Adresse. Ein anderer Port (`--port`) zeigt einen
anderen, meist leeren Lernstand; Wechsel über *Sicherung → exportieren/importieren*.

## 2. Täglicher Ablauf

1. `bin/mastery` – die Startseite öffnet sich.
2. **Weiter, wo Sie aufgehört haben:** letzte Lernhandlung (Übungsstrecke oder Explorable) mit Direktlink.
3. **Nächster empfohlener Schritt** mit sichtbarer Regel:
   - `M1` – die Voraussetzung (Übungsstrecke) ist noch nicht in allen Kompetenzen ohne Hilfe gelöst → nächste Aufgabe
     laut `EMT.decide` (Engine-Regel R0, RA, RB, RC1/2, RD, RF, RP, RU … wird angezeigt);
   - `M2` – danach die nächste noch nicht bearbeitete Aufgabe im Explorable (Engine-Regel des Explorables oder
     `M2-Reihenfolge`);
   - `M3` – alles einmal bearbeitet → Wiederholung in Anki; Behalten zeigt erst ein späterer Abruf.
   Spätere Prüfaufgaben werden nie empfohlen oder gedrängt; sie stehen nur in der Liste **Fällige spätere Prüfungen
   (nur zur Information)** (OD-28).
4. **Lernen:** Lehrbuch (PDF), Interaktiv (Erklären → Vorhersage → Experiment → Üben), Arbeitsbuch (PDF).
5. **Üben mit Rückmeldung:** Übungsstrecke Backpropagation – Zahlen, Ausdrücke (Zufallsstellen-Identitätstest, kein
   symbolischer Beweis) und Rechenschritte werden regelbasiert geprüft; Fehlerkategorie, Hinweisleiter, durchgerechnete
   Beispiele; jede Empfehlung nennt ihre Regel und was unsicher bleibt.
6. **Tutor:** bei jeder Aufgabe „Tutor-Brief kopieren“ (im Explorable nach einem eigenen Versuch). Der Brief beginnt
   mit der Kopiervorlage des R9-Tutorvertrags (`docs/research/workstreams/TUTOR_BEHAVIORAL_CONTRACT.md` §9, wörtlich;
   ein Test hält beide gleich), danach Aufgabe, eigene Versuche, genutzte Hinweise, Quellen und die eigene Frage. Bei
   Nachweisaufgaben (Rollen *similar*, *transfer*, *retest*) enthält er **keine Musterlösung** (CD-7). In Claude oder
   ChatGPT einfügen – erst dann verlässt der Inhalt den Rechner. Ein Tutor-Brief zählt als Hilfe (`tutor`-Ereignis);
   die Lösung zu sehen bleibt die Entscheidung des Lernenden und wird als Hilfe vermerkt (OD-10/11/12/30).
7. **Lernstand:** pro Kompetenz Zustand im Vokabular von `kc_status` (nie ein Prozentwert), Evidenzbasis
   (`kc_evidence_basis`: keine / nur Wiedererkennen / selbst erzeugt), Zahl der Versuche ohne und mit Hilfe, davon
   Freitext (unbewertet), Hilfen. „Mit Hilfe“ heißt Hinweis, Lösung oder Tutor zu dieser Aufgabe oder bis 20 Stunden
   davor zur selben Kompetenz (CD-9). Behalten wird nur aus selbstständigen richtigen Lösungen mit ≥ 20 Stunden Abstand
   abgeleitet. Freitext im Explorable ändert keinen Zustand.
8. **Anki:** `Anki.apkg` herunterladen, in Anki *Datei → Importieren*, Voreinstellungen lassen (Notizen und Notiztypen
   „aktualisieren, falls neuer“). Das Paket enthält keine Planungsdaten; Notizen werden über stabile GUIDs
   wiedererkannt, unveränderte Notizen behalten ihre Änderungszeit (CD-8), die Wiederholungshistorie bleibt erhalten.
   Die Startseite listet, welche Notizen die letzte Erstellung neu gestempelt hat (`anki_report.json`). Mastery plant
   keine Wiederholungen; das macht allein Anki (FSRS).

## 3. Wo was liegt

| Was | Wo |
|---|---|
| Produkte | `~/Mastery/units/<einheit>/` (`Lehrbuch.pdf`, `Arbeitsbuch.pdf`, `Anki.apkg`, `Interaktiv/index.html`, `tracks/…html`) |
| Bibliotheksbeschreibung (öffentlich) | `exam_mastery/mastery/library.json` im Repository |
| Private Einheiten | `~/Mastery/library-spec.local.json` (nie im Repository, nicht ausgeliefert) |
| Lernstand | Browser, localStorage von `http://127.0.0.1:8765`: `em-tutor-v1` (Übungsstrecke, Schlüssel `mastery|<track>`), `em-practice-v1` (Explorable, je Einheit und Aufgabenfassung) |
| Server-Sicherung | `~/Mastery/state/latest.json` + `state/history/` (letzte 30); die Startseite sendet bei jedem Öffnen eine geprüfte Kopie |
| Sicherungsdatei | `bin/mastery export` → `~/Mastery/exports/`; oder Startseite → Sicherung → *Als Datei exportieren* |

Der Server liefert nur eine Positivliste von Dateien aus, nimmt nur `POST /api/state` an (JSON, ≤ 4 MB, Schema
`mastery-state-v1`, nur die beiden Speicherschlüssel), prüft Host und Origin (Schutz vor DNS-Rebinding und fremden
Seiten) und beantwortet keine CORS-Vorabanfragen.

## 4. Private Einheit hinzufügen

```sh
bin/mastery build --unit ~/Lernen/meine-einheit.json --slug meine-einheit --track ml/backprop-track
```

Die Einheit (Schema `em-experience-v1`) muss außerhalb des Repositorys liegen und wird nur nach `~/Mastery` gebaut.
`library.json` der Bibliothek enthält keinen Pfad. Keine Codeänderung nötig.

## 5. Mini-Abnahme für den Owner (10 Schritte, ca. 15 Minuten)

1. `bin/mastery` ausführen. Erwartet: Bau ohne Fehler (beim ersten Mal einige Sekunden), Browser zeigt „Mastery“.
2. Startseite: „Noch nichts bearbeitet“; „Nächster empfohlener Schritt“ zeigt Regel `M1` · Engine-Regel `R0`.
3. Die vier Produkte und die Übungsstrecke anklicken: beide PDFs öffnen sich, `Anki.apkg` wird heruntergeladen,
   Interaktiv und Übungsstrecke laden.
4. Übungsstrecke: bei der ersten Aufgabe absichtlich `0,5` eingeben → Rückmeldung mit Regel; dann `0,24` → „Richtig“.
5. Weiter zur Hauptaufgabe, „Hinweis“ klicken, `delta_o*v1*fp1*x1` eingeben → richtig, aber Regel `RF` („mit Hilfe
   gelöst“), weiter zur ähnlichen Aufgabe ohne Hinweise.
6. Dort „Frage an den Tutor vorbereiten“ → „Tutor-Brief kopieren“ → in Claude oder ChatGPT einfügen. Prüfen: Regeln
   oben, Aufgabe, Ihre Versuche, *keine* Musterlösung.
7. Interaktiv: eine Übungsaufgabe unten frei beantworten, Hinweis und Musterlösung öffnen, dann die Seite neu laden.
   Erwartet: Versuch, Hinweis und „Musterlösung eingesehen“ sind wiederhergestellt.
8. Startseite → **Lernstand**: Sigmoid-Ableitung „heute ohne Hilfe gelöst / selbst erzeugte Lösung geprüft“,
   Kettenregel „mit Hilfe gelöst“, Explorable-Aufgabe als Freitext (unbewertet) gezählt; kein Prozentwert.
9. **Sicherung**: „Am lokalen Server gesichert“ erscheint; im Terminal `bin/mastery export` schreibt eine Datei.
10. `Anki.apkg` in ein **Test-Profil** von Anki importieren (Datei → Importieren, Voreinstellungen lassen); 16 Notizen
    im Stapel „Exam Mastery::Attention verstehen …“. Danach `bin/mastery build --force`: Startseite meldet
    „keine Notiz geändert“.

## 6. Ehrliche Grenzen

- **Lernwirkung: NOT_RUN.** Ob Mastery Lernen verbessert, ist nicht gemessen. Alle Zustände sind Näherungsanzeigen im
  Produkt (proximal indicators), keine Messung von Lernen.
- **Inhalt:** Die Attention-Einheit ist nicht unabhängig fachlich geprüft (`HUMAN_REVIEW_PENDING`); frühere Produkte
  bleiben `HUMAN_REJECTED`, bis ein Mensch sie neu bewertet.
- **Bewertung:** Freitext wird nicht bewertet. Regelbasiert geprüft werden nur die Übungsstrecke (Zahl, Ausdruck,
  Rechenschritte) und numerische Aufgaben mit `machine_check`; die Attention-Aufgaben haben keine.
- **Ein Lernender, ein Browser, ein Port.** Kein Konto, keine Synchronisation zwischen Geräten.
- **Nicht getestet:** Handy/Tablet (das Layout ist schmal nutzbar, aber ungeprüft), Screenreader im Detail, Import in
  die Anki-Desktop-App und AnkiMobile (automatisch geprüft nur mit der Anki-26.9.3-Python-Bibliothek gegen eine
  Wegwerf-Sammlung).
- **Tutor:** kein Live-Tutor; Mastery kopiert einen Brief. Ob Claude/ChatGPT sich an den R9-Vertrag halten, ist nicht
  geprüft (`TUTOR_EVALUATION_PROTOCOL.md`, nicht gelaufen).
- Browserdaten können gelöscht werden; die Startseite sichert beim Öffnen an den lokalen Server, aber nur, wenn sie
  geöffnet wird.

## 7. Vergleich mit „gutes Lehrbuch + ChatGPT/Claude + Anki“

**Wo V1 heute besser ist**

- Ein Ort für Lesen, Üben, Tutor und Wiederholung derselben Einheit; Aufgaben, Karten und Erklärungen sind
  aufeinander abgestimmt und quellengebunden.
- Übungsaufgaben mit sofortiger, **deterministischer** Prüfung und benannten Fehlermustern statt einer
  Modelleinschätzung; jede Empfehlung zeigt ihre Regel.
- Ehrlicher Lernstand: Hilfe (Hinweis, Lösung, Tutor) wird mitgezählt und trennt „mit Hilfe“ von „selbstständig“;
  kein geschönter Prozentwert.
- Der Tutor bekommt einen strukturierten Kontext mit Verhaltensregeln und ohne Lösungsschlüssel bei
  Nachweisaufgaben – im freien Chat liefert das Modell sonst oft sofort die Lösung.
- Anki-Karten kommen fertig und lassen sich gefahrlos neu importieren (stabile IDs, Historie bleibt).

**Wo V1 (noch) nicht besser ist**

- Inhaltsbreite: eine Einheit statt eines ganzen Lehrbuchs; die Inhalte sind nicht unabhängig geprüft – ein
  etabliertes Lehrbuch ist fachlich verlässlicher.
- Freitext und Beweise bewertet V1 nicht; ein guter Chat-Tutor gibt dazu sofort (unverifiziertes) Feedback.
- Der Tutor ist nicht eingebaut: Kopieren und Einfügen kostet einen Schritt.
- Kein Nachweis, dass Lernende damit mehr lernen; die Baseline ist ebenfalls nicht gemessen.
- Ein Gerät, ein Browser; die Baseline funktioniert überall.

## 8. Technik und Tests

- Code: `exam_mastery/mastery/` (`__init__.py` Bau/Status/Export/Zustandsprüfung, `server.py`, `__main__.py`,
  `library.json`), `exam_mastery/templates/mastery_home.{js,css}`, `bin/mastery`. Entscheidungen kommen aus der
  getesteten Laufzeit `templates/em_tutor.js` (`EMT.decide`, `EMT.kcStatus`, `EMT.kcEvidenceBasis`, neu
  `EMT.assisted`, `EMT.portableBrief`).
- Explorable (`learning/interactive_reference.py`): Zustand in `em-practice-v1`, Export des Lernprotokolls weiterhin ohne
  Antworten; neues Hilfe-Ereignis `tutor_brief` (`learning/experience_evidence.py`).
- Tests: `tests/test_mastery_v1_app.py` (Browser-Ende-zu-Ende, Server-Schutz, Repository-Sperre, Anki-Rundweg,
  private Einheit, R9-Kopiervorlage wörtlich).
