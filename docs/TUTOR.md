# Tutor: Geführtes Lernen

Stand 2026-11-28 · Lernstandard §5.5, §2.2, §6 · Owner-Feedback Issue #51 (P2) · Policies R5-POL-03/04/06/08/09/10,
R9-POL-01…10, `docs/research/workstreams/TUTOR_BEHAVIORAL_CONTRACT.md`.

Der Tutor bewertet nicht nur Antworten. Fehlt eine Voraussetzung, lehrt er sie in der Übungsstrecke und im Explorable
selbst, ohne Export und ohne Sprachmodell. Ein externes Modell ist ein optionaler, sichtbar gekennzeichneter Zusatz.

## 1. Was offline geschieht (deterministisch, kein Modell)

**Voraussetzungsgraph je Aufgabe.** Lektionen (Schema `em-lesson-v1`, `exam_mastery/learning/guided.py`) sind Daten an
der Lernstrecke (`track["lessons"]`) oder an der Einheit (`unit["lessons"]`). Beide Felder sind optional, ältere Daten
bleiben gültig. Jede Lektion nennt, wofür sie Voraussetzung ist: Kompetenzen und Fehlerkategorien der Lernstrecke bzw.
Kompetenzen und Fehlvorstellungen der Einheit. Außerdem nennt sie, wo das Thema ausführlich steht: durchgerechnetes
Beispiel, Übungsaufgabe, Lehrtext-Abschnitt (Anker im Explorable) oder externe Fundstelle. `requires` ordnet Lektionen
vor (z. B. Softmax vor der Softmax-Ableitung). Die Validierung führt jede Kontrollfrage aus und prüft alle Verweise. Sie
lehnt eine Lektion ab, die einen Schlüssel einer Nachweisaufgabe enthält oder die Frage einer echten Aufgabe
wiederverwendet. Aufgaben und Fehlvorstellungen bleiben unverändert, deshalb ändert sich die Aufgabenfassung des
Explorables nicht.

**Panel „Geführtes Lernen“** unter jeder Aufgabe:

1. *Diese Aufgabe baut auf:* die Lektionen aus dem Graphen, jederzeit aufrufbar.
2. Nach einer Antwort, deren Fehlerkategorie zu einer Lektion gehört, erscheint ein Angebot, zum Beispiel: „Vermutlich
   fehlt eine Voraussetzung: Ableitung der Sigmoidfunktion“. Die Lektion öffnet sich erst auf Klick (R5-POL-08).
3. Die Lektion zeigt eine kurze Erklärung, die Formel, ein durchgerechnetes Mini-Beispiel (erst Zahlen, dann Symbole)
   und **eine Kontrollfrage**. Die Frage prüft dieselbe Diagnose wie die Aufgaben, mit erklärender Rückmeldung je
   Fehlermuster. Danach führt „Zurück zur Aufgabe“ wieder an die Eingabe.
4. „Ich hänge fest“ öffnet zuerst die diagnostizierte Lücke, sonst die erste noch nicht bestandene Voraussetzung, sonst
   die Hinweisleiter.

**Hinweisleiter** (R5-POL-03/06): Die Stufen heißen Orientierung → Strategie → konkreter Schritt; der letzte Hinweis ist
der Bottom-out-Hinweis. Die Musterlösung gibt es nur auf ausdrücklichen Klick. Bei einer späteren Prüfaufgabe gibt es
keinen Schlüssel (R9-POL-04).

**Inhalte heute:** Backpropagation (Kettenregel, Ableitung der Sigmoidfunktion), Attention (Softmax, Skalierung mit
√d_k, Ableitung einer Softmax-Zeile, Maske vor der Normierung), Explorable Attention (dieselben Kontrollfragen,
verknüpft mit Fehlvorstellungen und Lehrtext-Abschnitten). Inhaltsstatus wie die Lernstrecken: `HUMAN_REVIEW_PENDING`.

## 2. Was ein externes Modell braucht

**„Mit Claude/ChatGPT weiterdenken“** (Kennzeichnung: *Externes Modell · nicht offline · nicht geprüft*). Ein Klick
kopiert einen kompakten Brief: wörtlich die R9-Vertragsvorlage, die übertragenen Daten, die Aufgabe, die eigenen
Versuche, die vermutete Lücke, die schon gezeigte Lektion, Quellen und die eigene Frage. Brief-Modi (`guided.brief_mode`):

| Aufgabe | Modus | Inhalt |
|---|---|---|
| Übung (Voraussetzung, Haupt-, Kontrast-, schwerere Aufgabe) ohne eigenen Versuch | `keyless` | keine Musterlösung |
| Übung nach eigenem Versuch | `with_reference` | Musterlösung nur für den Tutor |
| Nachweisrolle (ähnlich, Transfer) | `keyless` | keine Musterlösung |
| spätere Prüfung | `task_withheld` | Aufgabe selbst nicht im Brief, nur die Voraussetzung |

Vor dem Kopieren prüft die Engine deterministisch den Teil des Briefs, den sie selbst schreibt. Steht darin ein
Schlüssel einer Nachweisaufgabe, wird der Brief zurückgehalten. Die Antwort des Modells muss nicht zurückkopiert werden.
Sie zählt nie als Bewertung.

**Lokales Modell (optional, aus):** Ein OpenAI-kompatibler Endpunkt *auf diesem Rechner* (`127.0.0.1`/`localhost`), den
die lernende Person selbst betreibt, zum Beispiel Ollama oder LM Studio. Er muss CORS für die Mastery-Adresse erlauben.
Die Einstellung liegt nur im Browser (`em-tutor-llm-v1`). Die CSP der Übungsstrecke erlaubt ausschließlich
Loopback-Verbindungen. Die Antwort erscheint als `FEEDBACK_UNVERIFIED`. **Mastery liefert kein Modell mit**, verwaltet
keine API-Schlüssel und ruft keinen bezahlten Dienst auf. Über die Qualität lokaler Modelle sagt Mastery nichts
(R9-POL-10).

## 3. Leitplanken (Evidenz)

- Jede Hilfe wird mit `assist_level` und `source` protokolliert (R5-POL-04): Lektion `prereq_lesson`, Kontrollfrage
  `prereq_check`, Hinweise `hint_1…`/`hint_bottom_out`, Lösung `solution_seen` (alle `deterministic`), Brief und
  lokales Modell `tutor`/`agent_judgement`.
- Ereignistyp `guided` (Übungsstrecke) bzw. `guided_help` (Explorable) zählt als Hilfe. Eine danach gelöste Aufgabe ist
  „mit Hilfe gelöst“ (Regel RF, Zustand ASSISTED), nie unabhängige Evidenz. Die Lektion nennt die Kompetenz, die sie
  lehrt. Damit gilt auch eine Aufgabe dieser Kompetenz kurz danach (20-h-Fenster, CD-9) als unterstützt.
- Eine Kontrollfrage ist eine Lernkontrolle, kein Versuch. Sie ändert keinen Kompetenzzustand.
- Im Explorable ist das Panel erst nach einem eigenen Versuch aktiv: Das strikte Lernprotokoll lehnt Hilfe vor dem
  Versuch ab. Auch das aufgeklappte Fehlvorstellungs-Beispiel zählt als Hilfe, weil es die korrigierte Zahl zeigt.
- Der Lernstand der Startseite zählt `guided` als Hilfe.

## 4. Grenzen

- Ob Lernende damit mehr lernen, ist nicht gemessen (`NOT_RUN`). Die Lektionen sind nicht unabhängig fachlich geprüft.
- Lektionen gibt es bisher für Backpropagation und Attention. Für Liquidität, den Rechteckbeweis und neu importierte
  Kurse fehlen sie noch; ein Autor (Mensch oder Authoring-Paket) muss sie als Daten ergänzen.
- Das Fenster für das lokale Modell ist nur in der Übungsstrecke eingebaut, nicht im Explorable; dort gibt es den
  Brief zum Kopieren.
- Für die Nachweisrollen „ähnlich“ und „Transfer“ zeigt die Übungsstrecke die Musterlösung weiterhin auf ausdrücklichen
  Wunsch (OD-30: zählt als Hilfe, die Aufgabe gilt danach nicht mehr als Nachweis). Bei der späteren Prüfung gibt es
  keinen Schlüssel.
- Tests: `tests/test_guided_tutor.py` mit Daten, Graph, Python/JS-Parität, Evidenz und Ende-zu-Ende-Läufen für
  Backpropagation, Attention, die spätere Prüfung, das lokale Modell (simuliert) und das Explorable.
