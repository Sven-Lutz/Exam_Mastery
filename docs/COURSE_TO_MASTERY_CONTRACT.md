# Course-to-Mastery: Ordner- und Authoring-Vertrag (v1)

Stand 2026-11-27 · Auftrag: Issues #49, #51. Verbindlich für Import (`WP-C2M-IMPORT`) und Authoring (`WP-C2M-AUTHOR-*`).

## Grundsätze
- Private Kursquellen und alles daraus Erzeugte liegen **nur** unter `$MASTERY_HOME` (Standard `~/Mastery`), nie im Repository.
- Import, Inventar, Vollständigkeitsprüfung, Kapitelvorschlag, Validierung und Produktbau sind **deterministisch und offline**.
- **Autorenschaft ist KI-gestützt und nicht offline:** Ein Kapitel wird von einer Claude-Code-Sitzung (Abo des Owners, kein API-Schlüssel, keine bezahlten Aufrufe) aus dem Authoring-Paket geschrieben, oder von einem Menschen. Die UI kennzeichnet das ausdrücklich. Es gibt keine stille Modellnutzung.
- **Orchestrierung (M2, #58):** `bin/mastery author` bzw. „Kurs erarbeiten (KI)“ führt die Erarbeitung kursweit aus
  (Freigabe mit Höchstzahl der Aufrufe, Entwurf in `draft/`, Entwurfsprüfung mit Rückmeldung, Versionen, Bau, Gates,
  Pause bei Nutzungslimits, Aktualisieren geänderter Kapitel). Details: `docs/COURSE_IMPORT.md` §3. Zusätzliche
  Dateien je Kurs: `authoring/{authorization,job}.json`; je Kapitel: `draft/`, `versions/`, `authoring/runs/`.
- Jede fachliche Aussage trägt einen Quellenverweis auf Datei und Seite/Folie oder ist als eigene Herleitung markiert. Zahlen, Herleitungen und Lösungen werden rechnerisch geprüft (sympy/numpy), nicht nach sprachlicher Plausibilität.

## Ordnerstruktur
```
$MASTERY_HOME/courses/<course-slug>/
  course.json                 # mastery-course-v1: Titel, Quellwurzel (nur lokal), Dateien, Klassifikation, Kapitelplan, Status
  inventory/                  # Ausgabe von exam_mastery.fidelity.inventory (+ impact bei Änderungen)
  chapters/<NN-chapter-slug>/
    packet.json               # mastery-authoring-packet-v1 (siehe unten)
    pages/<file_id>-p<NNN>.png  # Seitenbilder für Abbildungen/Formeln (Vision des Autors)
    unit.json                 # em-experience-v1, vom Autor geschrieben (gleiche unit_id bei Überarbeitung: Anki-Identität)
    authoring.json            # mastery-authoring-record-v1: Autor (claude_code_session|human), Datum, Prüfprotokoll, offene Punkte
    build/                    # Lehrbuch.pdf, Arbeitsbuch.pdf, Anki.apkg, Interaktiv/ (experience_pipeline.build)
$MASTERY_HOME/library-spec.local.json   # gebaute Kapitel werden hier als private Einheiten eingetragen
```

## `packet.json` (mastery-authoring-packet-v1)
```json
{
 "schema": "mastery-authoring-packet-v1",
 "course": {"slug": "...", "title": "..."},
 "chapter": {"id": "NN-slug", "order": 5, "title": "...", "unit_id": "course/<course-slug>/<NN-slug>"},
 "sources": [{"file_id": "lecture-05", "rel_path": "Lecture/05 - ....pdf", "kind": "lecture_slides|script|exercise|solution|exam|literature|notebook|other",
              "pages": [{"n": 1, "text": "...", "has_images": true, "needs_vision": true, "image": "pages/lecture-05-p001.png"}]}],
 "related": {"exercises": ["file_id"], "solutions": ["file_id"], "exams": ["file_id"], "prerequisite_chapters": ["NN-slug"]},
 "coverage_warnings": ["..."],
 "target_schema": "em-experience-v1",
 "quality_contract": "docs/COURSE_TO_MASTERY_CONTRACT.md#qualitätsvertrag"
}
```

## Qualitätsvertrag (Autor)
1. **Lehrbuch:** vollständige, strenge Herleitungen mit Intuition davor, Annahmen benannt, Gegenbeispiele, Bezug zu Forschung und Literatur nur mit echten, geprüften Quellen. Original-Abbildungen, die genau die Aussage des Textes zeigen (keine Dekoration).
2. **Arbeitsbuch:** gestuft (durchgerechnetes Beispiel → geführt → selbstständig → Transfer/Klausurniveau), vollständige, geprüfte Lösungen, Fehlvorstellungen mit Bewertungsraster.
3. **Anki:** Abruf von Prinzipien, Bedingungen und Zusammenhängen. Wo sinnvoll Kontext, Formel und Abbildung auf der Karte. Keine Definitionslisten.
4. **Interaktiv:** Explorable, in dem eine Steuergröße eine Gleichung und ein Bild gemeinsam verändert und eine Vorhersage vor dem Aufdecken verlangt wird (Prinzipien wie bei 3Blue1Brown/Mathigon, ohne deren Inhalte zu kopieren).
5. **Kennzeichnung:** `HUMAN_REVIEW_PENDING`, nie selbst freigegeben. Lernwirkung `NOT_RUN`.

### Numerische Aussagen in Musterlösungen

Die Prüfung liest die **gedruckten Felder** `solution`, `solution_approach` sowie Aussage und Begründung jedes `solution_steps`-Paars. Für zuverlässig prüfbare Rechnungen jeweils eine Behauptung pro Zeile schreiben. Der JSON-Bericht `worked_coverage` nennt Aufgabe, Feld, Zeile und Ergebnis. Unverstandene Zeilen zählen als ungeprüfte Lösungsstellen; eine Zeile kann mehrere natürlichsprachliche Behauptungen enthalten.

- `2 * 3 = 6` und `1 / 3 ≈ 0,33` werden mit rationaler Arithmetik geprüft. `=` verlangt exakte Gleichheit, `≈` rundet auf die angegebenen Dezimalstellen (bei Gleichstand zur geraden Endziffer). Komma und Punkt sind Dezimaltrennzeichen; keine Tausendertrennzeichen verwenden.
- `Bei a=2 und b=3 beträgt die Quadratfläche 25.` prüft die behauptete Fläche des Quadrats mit Seitenlänge **a+b**. Ohne explizite Bindung muss eine Flächenvariante derselben Aufgabenkompetenz diese beiden positiven Seitenabschnitte vorgeben.
- Für strukturierte Zwischenwerte erhält die Aufgabe beispielsweise `"solution_oracle": {"interaction": "interaction/binomial-area", "variant": "a=2, b=3"}`. Die Variante muss eindeutig zu einem Modell `binomial_area_partition` gehören. Mit dessen kanonischen Parametern werden etwa `a² = 4`, `ab = 6`, `ba = 6`, `b² = 9`, `a + b = 5` und `Quadratfläche = 25` unabhängig berechnet. Schlüssel und Variantenlabel stammen aus dem jeweiligen Kapitel.
- `Polynomidentität: (a-b)^2 = a^2-2*a*b+b^2` verwendet den vorhandenen exakten Polynomprüfer über den reellen Zahlen. Aussagen mit zusätzlicher Definitionsbereichsbedingung benötigen fachliche Prüfung.
- Der Status `CHECKED` gilt für die bezeichnete Aussage. `UNVERIFIED` erfordert menschliche Prüfung. Ein belegter Widerspruch oder ein ungültiger expliziter Orakelverweis blockiert die Veröffentlichung. Antwortschlüssel, Rubriken und Autorenselbstauskunft verifizieren keinen Lösungstext. Bewusst falsche Beispiele gehören in `typical_errors`.
