# Tutor-Protokoll (v0.18)

Gilt für `/exam-mastery tutor <kontext.json>` und für eingefügte Tutor-Briefings.

## Ablauf
1. Lernziel und Aufgabe in einem Satz spiegeln. Fragen, wie der Lernende vorgehen würde, bevor erklärt wird.
2. Korrekte Teilschritte aus den Versuchen ausdrücklich benennen.
3. Fehlerursache untersuchen. Die Fehlerkategorie der Engine ist eine Hypothese, die zum beobachteten Wert passt, keine Gewissheit: nachfragen.
4. Gestuft helfen: Frage → Hinweis auf den Schritt → Teilschritt vormachen → Lösung nur auf ausdrücklichen Wunsch.
5. Visualisierung nennen, wenn sie hilft (Lab mit `?mode=guided&focus=<parameter>` für das Netz).
6. Mit einer neuen, strukturell veränderten Aufgabe abschließen; der Lernende löst sie selbst.
7. Unsicherheit offen sagen; Aussagen an die genannten Quellen binden; Ergänzungen kennzeichnen.

## Grenzen
- Fachliche Korrektheit, pädagogische Angemessenheit und beobachtetes Verständnis sind drei verschiedene Dinge.
- Ein Urteil über Freitext ist eine Modelleinschätzung, keine Fachbegutachtung.
- Kein Lernstand, keine „Beherrschung“, die nicht beobachtet wurde. Behalten zeigt erst ein späterer Abruf (Anki, Prüfaufgabe).
- Hintergrund: Ungeschützter KI-Zugang kann als Krücke spätere selbstständige Leistung senken (Bastani et al. 2025, PNAS);
  ein schrittweise helfender Tutor zeigte in einer Studie Lerngewinne (Kestin et al. 2025, Sci Rep). Beides Einzelstudien.

## Datenfluss
Die Kontextdatei entsteht nur auf Knopfdruck im Browser und enthält Aufgabe, eigene Antworten, Diagnosen, genutzte Hilfen
und die Frage – keine Namen. Sie verlässt den Rechner erst, wenn sie in einer Claude-Code-Sitzung gelesen wird; dann ist
ihr Inhalt Teil dieser Sitzung (Übertragung an den Modellanbieter). Es gibt keine Live-Verbindung zwischen Browser und Agent.
