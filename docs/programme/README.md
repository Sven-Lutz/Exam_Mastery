# Programmsteuerung und Wiederaufnahme

Stand 27.11.2026. Diese Steuerebene hält das autonome Exam-Mastery-Programm über Nutzungslimits, Abstürze und Neustarts hinweg rekonstruierbar. Sie ist bewusst klein: eine versionierte Zustandsdatei, ein Wiederaufnahmeprotokoll und ein Supervisor aus der Python-Standardbibliothek.

| Datei | Zweck |
|---|---|
| `PROGRAMME_STATE.json` | Einziger versionierter Programmzustand: Wissenschaftsstand, Workstreams, Architekturentscheidungen, Engine-Fähigkeiten, Produktqualität, kritische Defekte, Agenten, Arbeitspakete, Kosten/Limits, nächster Meilenstein. Nur der Lead (oder ein Headless-Lauf in dessen Rolle) schreibt ihn. |
| `agents/<agent-id>.json` | Checkpoint je Spezialist (Status, erledigt, offen, Artefakte, nächster Schritt). Jeder Agent schreibt nur seine eigene Datei. |
| `RESUME_PROMPT.md` | Arbeitsanweisung für unbeaufsichtigte Läufe: ein begrenzter Schritt, Checkpoint, Ende. |
| `../../ops/autonomy/supervisor.py` | Entscheidet bei jedem launchd-Takt, ob und welches Paket headless fortgesetzt wird. |

## Ablauf eines Supervisor-Takts (alle 30 Minuten)

1. Kill-Switch (`DISABLED`-Datei oder `enabled=false`) → nichts tun.
2. Dateisperre: nur ein Takt gleichzeitig.
3. Läuft der vorige Headless-Prozess noch → nichts tun. Ist er tot (Absturz, Neustart, `kill -9`), wird das als `interrupted` verbucht und **dieselbe Session** mit `--resume` fortgesetzt.
4. `BLOCKED` (nach drei Fehlschlägen in Folge) → warten auf `supervisor.py reset`.
5. Pause bis zum gemeldeten Reset, wenn das letzte gemeldete 5-Stunden- oder 7-Tage-Fenster abgelehnt hat oder die Obergrenze erreicht ist (Standard 90 % bzw. 85 %; Rest bleibt für die eigene Arbeit des Owners).
6. Aktive Lead-Session → nichts tun. Kriterien: Heartbeat jünger als 60 Minuten, Lead-Session laut `claude agents --json` beschäftigt (auch während sie selbst auf einen Limit-Reset wartet) oder eine beschäftigte interaktive Session in einem Exam-Mastery-Worktree.
7. Paketwahl: niedrigste `priority` unter `RESUMABLE`, `CHECKPOINTED`, `PAUSED_LIMIT`, `FAILED_RECOVERABLE`, `RUNNING` oder `PLANNED` mit `autostart`, deren `depends_on` abgeschlossen sind.
8. Höchstens vier Läufe in 24 Stunden; Laufzeitgrenze 150 Minuten.
9. Start: `claude -p … --output-format stream-json --permission-mode auto --permission-prompts none` mit einer Umgebung ohne API-Schlüssel oder Tokens (nur das angemeldete Abo, nie ein bezahlter Schlüssel). Alles, was eine Rückfrage bräuchte, wird abgelehnt.
10. Auswertung: Erfolg → `IDLE`; Limit → `PAUSED_LIMIT` bis zum gemeldeten `resetsAt` (+2 Minuten), ohne Rückmeldung eines Resets stündlicher Neuversuch (eine abgelehnte Anfrage verbraucht kein Kontingent); Fehler → Backoff 30/60 Minuten, danach `BLOCKED`.

Laufzeitdaten liegen außerhalb des Repositorys unter `~/.local/state/exam-mastery-autonomy/` (`runtime.json`, `heartbeat.json`, `supervisor.log`, `runs/*.jsonl`). Konfiguration optional in `~/.config/exam-mastery-autonomy/config.json` (Schlüssel siehe `DEFAULTS` im Skript).

## Bedienung

```bash
S=ops/autonomy/supervisor.py
/usr/bin/python3 $S status          # Zustand, Fenster, nächstes Paket, launchd geladen?
/usr/bin/python3 $S disable         # Kill-Switch: keine neuen Läufe
/usr/bin/python3 $S enable
/usr/bin/python3 $S reset           # nach Prüfung eines BLOCKED-Zustands
/usr/bin/python3 $S install         # launchd-Agent laden (Takt 30 min)
/usr/bin/python3 $S uninstall
/usr/bin/python3 $S smoke           # echter Mini-Aufruf + Resume derselben Session
/usr/bin/python3 $S launchd-smoke   # derselbe Test, von launchd gestartet
/usr/bin/python3 -m unittest tests.test_programme_supervisor
```

Eine interaktive Lead-Session meldet sich bei jedem Checkpoint mit `supervisor.py heartbeat --session <id> --wp <paket>`. Wer eine Lead-Session fortsetzt, prüft zuerst `status`: Läuft gerade ein Headless-Lauf, dessen Ende abwarten oder `disable` setzen, damit sich keine zwei Agenten in die Quere kommen.

## Nachgewiesen am 27.11.2026

- Echter Headless-Aufruf und `--resume` derselben Session (Token wiedergegeben).
- Derselbe Test von launchd gestartet: Abo-Anmeldung, Resume, `git` über SSH und `gh` funktionieren im Agentenkontext.
- Echter Absturztest: Takt mit `SIGKILL` mitten im Lauf beendet; der nächste Takt setzte dieselbe Session fort, erledigte die restlichen Schritte ohne Wiederholung; der dritte Takt war idempotent.
- `rate_limit_event` meldet Auslastung und Reset beider Fenster; der Supervisor speichert und beachtet sie.
- Unit-Tests mit gefälschter CLI für alle Entscheidungszweige (keine Modellaufrufe in CI).

## Nicht nachgewiesen

- Eine echte Limit-Ablehnung (während der Tests nicht erreicht). Die Auswertung folgt der in der CLI dokumentierten `rate_limit_info`-Form.
- Das in der CLI beschriebene eingebaute Warten einer interaktiven Session auf den Limit-Reset.
- Verhalten im Ruhezustand des Macs: launchd lässt Takte aus, der erste Takt nach dem Aufwachen holt nach.
- Gleichzeitiges Tippen in die Lead-Session während eines Headless-Laufs (nur durch das Protokoll oben abgesichert).
