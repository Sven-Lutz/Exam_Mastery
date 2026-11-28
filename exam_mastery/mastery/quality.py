"""Machine quality gates for Mastery chapters (catalogue ``mastery-quality-v1``; standard §5.1-§5.4, §4.1 V1-V10,
docs/COURSE_TO_MASTERY_CONTRACT.md).

Each gate decides one criterion that a machine can decide from the unit (em-experience-v1), the built products
(Lehrbuch.pdf, Arbeitsbuch.pdf, Anki.apkg, Interaktiv/index.html) and the chapter folder (packet.json, authoring.json,
build-record.json). The result is a report (``build/quality.json`` + ``quality.html`` + ``quality.md``) for the author
session and the owner. Gates block obvious defects; they never approve a chapter, never replace the owner's acceptance
and never assert a learning effect (HUMAN_REVIEW_PENDING, learning evaluation NOT_RUN). Offline, deterministic, no
model calls. Heuristic rules say so in their rule text.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from html import escape
from pathlib import Path

CATALOGUE = "mastery-quality-v1"
SCHEMA = "mastery-quality-report-v1"
SEVERITIES = ("blocker", "major", "minor")
SEVERITY_DE = {"blocker": "Blocker", "major": "schwer", "minor": "leicht"}
PRODUCT_DE = {"textbook": "Lehrbuch", "workbook": "Arbeitsbuch", "anki": "Anki", "interactive": "Interaktiv",
              "pages": "Seitenprüfung", "integrity": "Integrität"}
STAGES = ("worked_example", "guided", "independent", "transfer", "exam")
STAGE_DE = {"worked_example": "Beispiel", "guided": "geführt", "independent": "selbstständig", "transfer": "Transfer",
            "exam": "Klausurniveau"}
CHAIN_DE = {1: "Warum", 2: "Intuition sichtbar", 3: "präzise Form", 4: "Herleitung/Beweis",
            5: "durchgerechnetes Beispiel", 6: "Fehlvorstellung"}
COURSE_KINDS = {"lecture", "lecture_slides", "script", "exercise", "solution", "exam"}
OWN_KINDS = {"own_derivation", "original_derivation", "synthetic"}
EVIDENCE_ROLES = ("similar", "transfer", "retest")
PROOF_OPS = {"prove", "derive"}
OPEN_OPS = {"prove", "derive", "explain", "argue", "design", "evaluate", "compare", "interpret", "transfer", "diagnose",
            "subsume"}
SELF_APPROVAL = {"APPROVED", "ACCEPTED", "GO", "PASS", "HUMAN_APPROVED", "RELEASED", "FREIGEGEBEN"}
# Page geometry (pt). Body = everything between the running header and footer bands.
BAND_TOP, BAND_BOTTOM = 60.0, 790.0
FONT_FLOOR_PT = 6.0          # below this, print text is not reliably legible (figure labels included)
EDGE_PT = 14.0               # text closer to the paper edge than this is outside the printable area
NEAR_EMPTY = 0.20            # a page whose body text covers < 20 % of the body height and starts without a heading

WHY = re.compile(r"(?i)\b(warum|wozu|wofür|weshalb|wieso|problem\w*|motivation|ziel\w*|frage\w*|why|nutzen|einordnung|"
                 r"anwendung\w*|wo(?:rauf|ran|für) .{0,30}(an|gut)|brauch\w*)\b")
EXAMPLE = re.compile(r"(?i)(beispiel|example|durchgerechnet|zahlen|konkret)")
DEFLIST_FRONT = re.compile(r"(?i)^\s*(was (ist|sind|bedeutet|bezeichnet|versteht man unter)\b|wie (lautet|ist) die "
                           r"definition|definieren sie|geben sie die definition|nennen sie (die|alle)|zählen sie|"
                           r"what (is|are)\b|define\b)")
FIND_ERROR = re.compile(r"(?i)(fehler|falsch|irrtum|wo steckt|stimmt .{0,40}nicht|trugschluss|"
                        r"prüfen sie .{0,60}(behauptung|argument|rechnung|beweis|lösung))")
PRODUCE = re.compile(r"(?i)(beweis|zeigen sie|leiten sie|herleit|begründen sie|weisen sie nach|prove|show that|derive)")
ALT_ROUTE = re.compile(r"(?i)(alternativ|andere[rnms]? (weg|ansatz|lösungsweg|begründung)|zweiter weg|gleichwertig|"
                       r"ebenso (gültig|richtig|zulässig)|auch (möglich|zulässig|akzeptiert|richtig)|oder über|"
                       r"jeder (korrekte|gültige|richtige))")
DIVERGENCE = re.compile(r"(?i)(weicht.{0,40}\bab\b|abweich|folienform|anders als (auf|in) de[rnm] (folie|vorlesung|skript)"
                        r"|notation der (folie|vorlesung))")
PAGE_REF = re.compile(r"(?i)(?:\b(?:pdf-)?seiten?|\bs\.|\bfolien?|\bslides?|\bpages?|\bpp?\.)\s*"
                      r"(\d{1,4})(?:\s*(?:[-–—]|bis)\s*(\d{1,4}))?")
SHEET_REF = re.compile(r"(?i)\b(blatt|übung\w*|aufgabe|sheet|exercise|kapitel|chapter|abschnitt|section|§)\s*\d")
PRIVATE_PATH = re.compile(r"(/Users/[^/\s\"'<>]+|/home/[^/\s\"'<>]+|[A-Za-z]:\\\\?Users\\\\?|file://)")
CHAIN_NEEDS_PROOF = PROOF_OPS | {"calculate", "explain"}


def _g(gid, product, section, severity, rule, fix):
    return {"id": gid, "product": product, "section": section, "severity": severity, "rule": rule, "fix": fix}


GATES = (
    _g("TB-CHAIN", "textbook", "§2.2, §5.1", "major",
       "Jede Kompetenz hat in der Einheit Bausteine für die Lernkettenschritte 1-6: (1) Warum: Abschnitt, dessen Titel oder "
       "Einstieg nach Problem/Zweck fragt (heuristisch); (2) Bild: Grafik oder Mastery-Motion-Szene der Kompetenz; "
       "(3) präzise Form: Definition, Kernaussage, Formel oder Satz mit Ergebnis; (4) Herleitung: derivation-Block oder "
       "Musterbeispiel mit begründeten Schritten (für prove/derive/calculate/explain); (5) durchgerechnetes Beispiel; "
       "(6) Fehlvorstellung: misconception, pitfall-Kasten, Kontrastaufgabe oder Denkfehler-Karte.",
       "Fehlenden Baustein in unit.json ergänzen (teaching.blocks, graphics, derivation, assessments mit stage "
       "'worked_example', misconceptions) und der Kompetenz über competency_ids zuordnen."),
    _g("TB-PROOF", "textbook", "§5.1", "major",
       "Jede Aussage (claim) ist belegt: durch einen Herleitungsschritt, der sie nennt, durch eine Quelle mit Seiten-/"
       "Folien-/Abschnittsangabe oder durch eine als eigene Herleitung markierte Quelle.",
       "Beweis/Herleitung mit claim_ids ergänzen oder den Quellenverweis um Seite/Folie präzisieren."),
    _g("TB-FIGURE", "textbook", "§5.1, V1, V8", "major",
       "Jede Abbildung ist berechnet (Modell der Einheit bzw. Mastery-Motion-Keyframe), trägt eine Aussage (Bildunterschrift "
       "mit mindestens 5 Wörtern, claim_ids), einen Beschreibungstext und steht in ihrem Abschnitt.",
       "caption als prüfbare Aussage formulieren, alt-Text und claim_ids setzen, Grafik als graphic-Block platzieren."),
    _g("TB-LOCATOR", "textbook", "§5.1", "major",
       "Kursquellen (Folien, Skript, Übung, Lösung, Klausur) nennen Seite, Folie oder Blatt/Aufgabe; genannte Seiten- und "
       "Foliennummern kommen in den Seiten des Authoring-Pakets vor.",
       "Locator präzisieren (z. B. 'Folie 12', 'Skript S. 34') bzw. eine Seite aus packet.json zitieren."),
    _g("TB-DIVERGENCE", "textbook", "§5.1", "minor",
       "Eine quellengebundene Einheit mit Kursquellen macht Abweichungen von den Kursunterlagen kenntlich (Hinweis "
       "'weicht ab'/'Folienform' im Text) oder erklärt in authoring.json ausdrücklich 'divergences': [].",
       "Abweichung im Text benennen oder in authoring.json 'divergences' (Liste, ggf. leer) eintragen."),
    _g("WB-STAGES", "workbook", "§5.2", "major",
       "Das Arbeitsbuch hat alle fünf Stufen: Beispiel, geführt, selbstständig, Transfer, Klausurniveau (assessments.stage).",
       "Für jede fehlende Stufe mindestens eine Aufgabe mit passender 'stage' ergänzen."),
    _g("WB-SOLUTION", "workbook", "§5.2", "major",
       "Jede Aufgabe hat eine vollständige Lösung (mind. 12 Wörter oder begründete solution_steps) und einen Prüfvermerk: "
       "machine_check (numerisch/CAS), begründete Lösungsschritte (Beweisprüfung) oder eine Rubrik mit mindestens zwei "
       "Kriterien.",
       "Lösung ausschreiben; Zahlenergebnis mit machine_check prüfen oder die Rubrik in Kriterien aufteilen."),
    _g("WB-ALT-ROUTES", "workbook", "§5.2", "minor",
       "Offene Aufgaben (ohne machine_check, Kompetenz mit offener Operation) nennen in Rubrik oder Lösung alternative "
       "Lösungswege (heuristisch: 'alternativ', 'auch zulässig', 'gleichwertig' …).",
       "In der Rubrik festhalten, welche anderen Wege volle Punkte bekommen."),
    _g("WB-FIND-ERROR", "workbook", "§5.2", "major",
       "Mindestens zwei Fehler-finden-Aufgaben (role 'contrast' oder Auftrag, einen Fehler zu finden).",
       "Aufgaben ergänzen, in denen eine fehlerhafte Rechnung/ein fehlerhafter Beweis geprüft und korrigiert wird."),
    _g("WB-PROOF-PRODUCTION", "workbook", "§5.2, CD-11", "major",
       "Jede Beweis-/Herleitungskompetenz (prove, derive) hat eine Aufgabe, die die Herleitung selbst verlangt (Beweisen, "
       "Zeigen, Herleiten), nicht nur Wiedererkennen; nicht nur als Musterbeispiel.",
       "Eine selbstständige Beweis- oder Herleitungsaufgabe mit Rubrik für diese Kompetenz ergänzen."),
    _g("AN-LINT", "anki", "§5.4", "blocker",
       "Jede Karte besteht card_lint (eine Frage, kurze Antwort, semantischer Schlüssel, bekannte Kartenart).",
       "Karte nach der Meldung kürzen bzw. teilen."),
    _g("AN-DEFLIST", "anki", "§5.4", "major",
       "Keine Definitionslisten: keine Karte fragt 'Was ist …/Definieren Sie …' als Begriffs-/Faktenkarte oder verlangt "
       "eine Aufzählung (mind. 4 Glieder); höchstens die Hälfte der Karten sind Begriffs-/Faktenkarten (heuristisch).",
       "Nach Bedingung, Zusammenhang, Grund oder Herleitungsschritt fragen statt nach dem Wortlaut der Definition."),
    _g("AN-CONTEXT", "anki", "§5.4", "major",
       "Jede Karte hat Kontext (Feld 'context': Situation bzw. Einordnung, in der die Frage gestellt wird).",
       "Einen Satz Kontext ergänzen (Wo im Kapitel? Welche Situation? Welche Annahmen?)."),
    _g("AN-VISUAL", "anki", "§5.4, V8", "major",
       "Hat eine Kompetenz eine Abbildung in der Einheit, trägt mindestens eine ihrer Karten diese Abbildung (figure); "
       "Karten der Art 'visual' haben immer eine Abbildung.",
       "Auf einer Karte der Kompetenz 'figure': '<graphic-id>-state-<n>' setzen."),
    _g("AN-IDENTITY", "anki", "§5.4, R8-POL-02", "blocker",
       "Stabile Identität: unit_id gleich dem bisherigen Bau, keine fremden Anki-Manifeste im Bauordner, eindeutige "
       "Kartenschlüssel. Entfallene Karten werden als leichter Befund gemeldet (in Anki von Hand zurückziehen).",
       "Bisherige unit_id und Kartenschlüssel beibehalten; Kartentexte dürfen sich ändern, Schlüssel nicht."),
    _g("IA-SCENE", "interactive", "§5.3", "major",
       "Mindestens eine Mastery-Motion-Szene pro Kapitel (Interaktion mit Motion-Modell, z. B. plane_linear_map).",
       "Eine Interaktion mit einem Modell anlegen, das eine Mastery-Motion-Szene hat."),
    _g("IA-MOTION-RULES", "interactive", "§4.1 V1-V6, §5.3", "major",
       "Jede Szene: V1 Aussage (claim); V2 mindestens ein Übergang, der einen Parameter kontinuierlich verändert; V3 "
       "Gleichungsterme an Objekte gebunden; V4 mindestens ein Vorhersage-Haltepunkt; V5 mindestens zwei Schritte, "
       "Schritt und Zeitachse als Hauptbedienung; V6 ein Auftrag mit 1-3 Reglern und Ziel; danach eine eigene Aufgabe.",
       "Szene bzw. Interaktion (variants, prediction_prompt, transfer_prompt) ergänzen."),
    _g("IA-PERSIST", "interactive", "§5.3", "major",
       "Interaktiv speichert den Lernstand (em-practice-v1, bei Szenen em-motion-v1) und protokolliert Versuch und Hilfe "
       "getrennt (attempt vs. hint/solution_reveal/guided_help).",
       "Mit der aktuellen Engine neu bauen; die Seite darf nicht von Hand verändert werden."),
    _g("PG-OVERFLOW", "pages", "§5.1 Seitenprüfung", "blocker",
       "Kein Text, keine Formel und keine Grafik ragt über den Seitenrand oder in den nicht druckbaren Rand "
       f"({EDGE_PT:g} pt).",
       "Formel umbrechen oder als abgesetzte Formel setzen; breite Tabellen/Grafiken verkleinern."),
    _g("PG-ORPHAN-HEADING", "pages", "§5.1 Seitenprüfung", "major",
       "Keine Überschrift steht als letzte Zeile (oder mit nur einer Folgezeile) unten auf einer Seite.",
       "Abschnitt kürzen/umstellen oder Umbruch vor der Überschrift erzwingen."),
    _g("PG-NEAR-EMPTY", "pages", "§5.1 Seitenprüfung", "major",
       f"Keine fast leere Seite: Seiten, die nicht mit einer Überschrift beginnen und deren Text weniger als "
       f"{int(NEAR_EMPTY * 100)} % der Satzspiegelhöhe füllt (Überlauf-Rest eines Abschnitts).",
       "Abschnitt kürzen, Kasten/Grafik verkleinern oder Inhalt umstellen, damit kein Rest auf eine eigene Seite fällt."),
    _g("PG-LINKS", "pages", "§5.1 Seitenprüfung", "major",
       "Interne Verweise im PDF zeigen auf existierende Seiten.",
       "Mit der aktuellen Engine neu bauen; Verweisziele prüfen."),
    _g("PG-FONT-FLOOR", "pages", "§5.1 Seitenprüfung, V9", "major",
       f"Keine Schrift kleiner als {FONT_FLOOR_PT:g} pt (auch Beschriftungen in Grafiken).",
       "Grafik größer setzen oder Beschriftungen kürzen."),
    _g("INT-REVIEW", "integrity", "§5, Qualitätsvertrag 5", "blocker",
       "Kennzeichnung HUMAN_REVIEW_PENDING: keine Selbstfreigabe in unit.json/authoring.json; die Produkte tragen "
       "HUMAN_REVIEW_PENDING.",
       "Status auf HUMAN_REVIEW_PENDING setzen; freigeben kann nur der Owner."),
    _g("INT-LEARNING-EVAL", "integrity", "§7, R5-POL-05", "blocker",
       "Lernwirkung NOT_RUN: keine Angabe in unit.json/authoring.json behauptet eine gemessene Lernwirkung.",
       "learning_effect/learning_evaluation auf NOT_RUN setzen."),
    _g("INT-TUTOR-KEYS", "integrity", "§5.5, R9-POL-04", "blocker",
       "Tutor-Material enthält keine Lösungsschlüssel von Nachweisaufgaben (similar, transfer, retest): keine Lösung in "
       "deren Tutor-Ansicht, keine Schlüssel in Hinweisen und Vorlektionen.",
       "Lösung/Zahl aus Hinweis bzw. Lektion entfernen oder die Aufgabenrolle ändern."),
    _g("INT-PRIVATE-PATHS", "integrity", "AGENTS.md, Qualitätsvertrag", "blocker",
       "Keine lokalen Pfade (/Users/…, /home/…, file://) in unit.json und den Produkten.",
       "Pfad aus dem Text entfernen; Quellen nur mit Titel und Seite nennen."),
)
GATE = {g["id"]: g for g in GATES}


# ------------------------------------------------------------------ helpers

def _now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _words(text):
    return len(re.findall(r"\w+", str(text or "")))


def _cids(item):
    return [c for c in item.get("competency_ids") or [] if isinstance(c, str)]


def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


class _Ctx:
    def __init__(self, unit, build_dir=None, chapter_dir=None):
        self.unit = unit
        self.build_dir = Path(build_dir) if build_dir else None
        self.chapter_dir = Path(chapter_dir) if chapter_dir else None
        self.findings = []
        self.not_checked = {}
        u = unit
        self.teaching = [t for t in u.get("teaching") or [] if isinstance(t, dict)]
        self.tasks = [a for a in u.get("assessments") or [] if isinstance(a, dict)]
        self.cards = [c for c in u.get("cards") or [] if isinstance(c, dict)]
        self.graphics = [g for g in u.get("graphics") or [] if isinstance(g, dict)]
        self.interactions = [i for i in u.get("interactions") or [] if isinstance(i, dict)]
        self.misconceptions = [m for m in u.get("misconceptions") or [] if isinstance(m, dict)]
        self.competencies = [c for c in u.get("competencies") or [] if isinstance(c, dict)]
        self.sources = {s.get("id"): s for s in u.get("sources") or [] if isinstance(s, dict)}
        self.claims = [c for c in u.get("claims") or [] if isinstance(c, dict)]
        self.math = {m.get("id"): m for m in u.get("mathematics") or [] if isinstance(m, dict)}
        self.packet = _read_json(self.chapter_dir / "packet.json") if self.chapter_dir else None
        self.authoring = _read_json(self.chapter_dir / "authoring.json") if self.chapter_dir else None
        self.record = _read_json(self.chapter_dir / "build-record.json") if self.chapter_dir else None
        self._scenes = None

    def add(self, gid, location, message, severity=None):
        g = GATE[gid]
        self.findings.append({"gate": gid, "severity": severity or g["severity"], "product": g["product"],
                              "section": g["section"], "location": location, "message": message, "fix": g["fix"]})

    def skip(self, gid, reason):
        self.not_checked[gid] = reason

    def scenes(self):
        """(interaction, scene or None, error) for every interaction; a scene only where a Motion model exists."""
        if self._scenes is None:
            from ..motion.embed import scene_for_interaction
            out = []
            for i in self.interactions:
                try:
                    out.append((i, scene_for_interaction(i), None))
                except Exception as exc:  # an unbuildable scene is a finding, not a crash
                    out.append((i, None, str(exc)[:200]))
            self._scenes = out
        return self._scenes


# ------------------------------------------------------------------ textbook

def _section_text(t):
    parts = [t.get("section_title") or "", t.get("content") or ""]
    for b in t.get("blocks") or []:
        if isinstance(b, dict):
            parts += [str(b.get(k) or "") for k in ("term", "title", "md")]
    return "\n".join(parts)


def _has_formal(t, math):
    blocks = [b for b in t.get("blocks") or [] if isinstance(b, dict)]
    if any(b.get("type") == "definition" or (b.get("type") == "box" and b.get("kind") == "key") for b in blocks):
        return True
    if isinstance(t.get("derivation"), dict) and t["derivation"].get("result"):
        return True
    text = _section_text(t)
    if re.search(r"\\\[|\$\$", text):
        return True
    return any(math.get(m, {}).get("display") for m in re.findall(r"\[\[math:([A-Za-z0-9_:.-]+)\]\]", text))


def gate_chain(ctx):
    graphic_teach = {}
    for g in ctx.graphics:
        for c in _cids(g):
            graphic_teach.setdefault(c, True)
        graphic_teach.setdefault(("t", g.get("teaching_id")), True)
    scene_cids = {c for i, s, _ in ctx.scenes() if s for c in _cids(i)}
    inter_cids = {c for i in ctx.interactions for c in _cids(i)}
    for comp in ctx.competencies:
        cid = comp.get("id")
        secs = [t for t in ctx.teaching if cid in _cids(t)]
        tasks = [a for a in ctx.tasks if cid in _cids(a)]
        have = set()
        if any(WHY.search((t.get("section_title") or "") + "\n" + (t.get("content") or "")[:600]) or
               any(isinstance(b, dict) and b.get("kind") == "question" for b in t.get("blocks") or []) for t in secs):
            have.add(1)
        if cid in graphic_teach or any(("t", t.get("id")) in graphic_teach for t in secs) or cid in scene_cids \
                or cid in inter_cids:
            have.add(2)
        if any(_has_formal(t, ctx.math) for t in secs):
            have.add(3)
        if any(isinstance(t.get("derivation"), dict) for t in secs) or any(
                a.get("stage") == "worked_example" and a.get("solution_steps") for a in tasks):
            have.add(4)
        if any(a.get("stage") == "worked_example" for a in tasks) or any(
                EXAMPLE.search(t.get("section_title") or "") and re.search(r"\d", t.get("content") or "") for t in secs):
            have.add(5)
        if any(cid in _cids(m) for m in ctx.misconceptions) or any(
                isinstance(b, dict) and b.get("kind") == "pitfall" for t in secs for b in t.get("blocks") or []) or any(
                a.get("role") == "contrast" for a in tasks) or any(
                c.get("kind") == "misconception" and cid in _cids(c) for c in ctx.cards):
            have.add(6)
        need = {1, 2, 3, 5, 6} | ({4} if comp.get("operation") in CHAIN_NEEDS_PROOF else set())
        missing = sorted(need - have)
        if not secs:
            ctx.add("TB-CHAIN", f"Kompetenz {cid}", "Kein Lehrbuchabschnitt ist dieser Kompetenz zugeordnet.")
        elif missing:
            ctx.add("TB-CHAIN", f"Kompetenz {cid}",
                    "Lernkette unvollständig, es fehlt: " + ", ".join(f"({n}) {CHAIN_DE[n]}" for n in missing) + ".")


def _page_numbers(locator):
    pages = []
    for a, b in PAGE_REF.findall(locator or ""):
        lo = int(a)
        hi = int(b) if b else lo
        if hi < lo or hi - lo > 400:
            hi = lo
        pages.append((lo, hi))
    return pages


def _has_locator(locator):
    return bool(PAGE_REF.search(locator or "") or SHEET_REF.search(locator or ""))


def gate_proof(ctx):
    in_proof = set()
    for t in ctx.teaching:
        d = t.get("derivation")
        if isinstance(d, dict):
            for st in d.get("steps") or []:
                if isinstance(st, dict):
                    in_proof.update(st.get("claim_ids") or [])
    for c in ctx.claims:
        refs = [ctx.sources.get(r) for r in c.get("source_refs") or []]
        refs = [s for s in refs if s]
        own = any(s.get("kind") in OWN_KINDS for s in refs)
        located = any(_has_locator(s.get("locator")) for s in refs)
        if c.get("id") in in_proof or own or located:
            continue
        ctx.add("TB-PROOF", f"Aussage {c.get('id')}",
                "Weder Herleitungsschritt noch Quelle mit Seite/Folie noch eigene Herleitung belegt diese Aussage.")


def gate_figures(ctx):
    placed = {}
    for t in ctx.teaching:
        for b in t.get("blocks") or []:
            if isinstance(b, dict) and b.get("type") == "graphic":
                placed[b.get("id")] = t.get("id")
    for g in ctx.graphics:
        gid = g.get("id")
        problems = []
        if _words(g.get("caption")) < 5:
            problems.append("Bildunterschrift trägt keine Aussage (unter 5 Wörtern)")
        if _words(g.get("alt")) < 5:
            problems.append("Beschreibungstext (alt) fehlt oder ist zu knapp")
        if not g.get("claim_ids"):
            problems.append("keine Aussage (claim_ids) verknüpft")
        if not g.get("model_ref") or not g.get("keyframes"):
            problems.append("nicht aus Modell/Keyframe berechnet")
        sec = next((t for t in ctx.teaching if t.get("id") == g.get("teaching_id")), None)
        if sec is not None and sec.get("blocks") and placed.get(gid) != sec.get("id"):
            problems.append("nicht als graphic-Block in ihrem Abschnitt platziert")
        if problems:
            ctx.add("TB-FIGURE", f"Abbildung {gid}", "; ".join(problems) + ".")


def _packet_pages(packet):
    pages = set()
    for s in (packet or {}).get("sources") or []:
        pages.update(p.get("n") for p in s.get("pages") or [] if isinstance(p, dict) and isinstance(p.get("n"), int))
    return pages


def gate_locators(ctx):
    pages = _packet_pages(ctx.packet) if ctx.packet else None
    for sid, s in ctx.sources.items():
        if s.get("kind") not in COURSE_KINDS:
            continue
        loc = s.get("locator") or ""
        if not _has_locator(loc):
            ctx.add("TB-LOCATOR", f"Quelle {sid}", "Kursquelle ohne Seite, Folie oder Blatt/Aufgabe.")
            continue
        if pages:
            cited = [n for lo, hi in _page_numbers(loc) for n in range(lo, hi + 1)]
            outside = sorted({n for n in cited if n not in pages})
            if outside:
                ctx.add("TB-LOCATOR", f"Quelle {sid}",
                        f"{len(outside)} zitierte Seite(n)/Folie(n) kommen im Authoring-Paket nicht vor "
                        f"(z. B. {', '.join(map(str, outside[:5]))}).")
    if ctx.packet is None:
        ctx.skip("TB-LOCATOR", "kein packet.json (öffentliche Einheit): nur Angabe von Seite/Folie geprüft")


def gate_divergence(ctx):
    if ctx.unit.get("source_mode") != "grounded" or not any(s.get("kind") in COURSE_KINDS for s in ctx.sources.values()):
        ctx.skip("TB-DIVERGENCE", "keine Kursquellen")
        return
    declared = isinstance((ctx.authoring or {}).get("divergences"), list) or isinstance(ctx.unit.get("divergences"), list)
    marked = any(DIVERGENCE.search(s) for s in _strings([ctx.teaching, ctx.claims, ctx.tasks]))
    if not (declared or marked):
        ctx.add("TB-DIVERGENCE", "Einheit",
                "Weder ein Abweichungshinweis im Text noch eine ausdrückliche Erklärung 'divergences' in authoring.json.")


# ------------------------------------------------------------------ workbook

def gate_stages(ctx):
    present = {a.get("stage") for a in ctx.tasks}
    missing = [s for s in STAGES if s not in present]
    if missing:
        ctx.add("WB-STAGES", "Arbeitsbuch", "Es fehlen Stufen: " + ", ".join(STAGE_DE[s] for s in missing) + ".")


def _verification(a):
    kinds = []
    if isinstance(a.get("machine_check"), dict):
        kinds.append("CAS/numerisch")
    steps = a.get("solution_steps") or []
    if isinstance(steps, list) and len(steps) >= 2 and all(isinstance(s, list) and len(s) == 2 and str(s[1]).strip()
                                                           for s in steps):
        kinds.append("Beweisprüfung")
    if len([r for r in a.get("rubric") or [] if isinstance(r, dict) and str(r.get("criterion") or "").strip()]) >= 2:
        kinds.append("Rubrik")
    return kinds


def gate_solutions(ctx):
    for a in ctx.tasks:
        where = f"Aufgabe {a.get('id')}"
        if _words(a.get("solution")) < 12 and len(a.get("solution_steps") or []) < 2:
            ctx.add("WB-SOLUTION", where, "Lösung zu knapp für eine vollständige Musterlösung (unter 12 Wörtern).")
        if not _verification(a):
            ctx.add("WB-SOLUTION", where, "Kein Prüfvermerk: weder machine_check noch begründete Schritte noch Rubrik "
                                          "mit mindestens zwei Kriterien.")


def gate_alt_routes(ctx):
    ops = {c.get("id"): c.get("operation") for c in ctx.competencies}
    for a in ctx.tasks:
        if isinstance(a.get("machine_check"), dict) or a.get("stage") == "worked_example":
            continue
        if not any(ops.get(c) in OPEN_OPS for c in _cids(a)):
            continue
        text = " ".join(_strings([a.get("rubric"), a.get("solution"), a.get("solution_approach")]))
        if not ALT_ROUTE.search(text):
            ctx.add("WB-ALT-ROUTES", f"Aufgabe {a.get('id')}", "Offene Aufgabe ohne Hinweis auf alternative Lösungswege.")


def gate_find_error(ctx):
    n = sum(1 for a in ctx.tasks if a.get("role") == "contrast" or FIND_ERROR.search(a.get("prompt") or ""))
    if n < 2:
        ctx.add("WB-FIND-ERROR", "Arbeitsbuch", f"Nur {n} Fehler-finden-Aufgabe(n), mindestens 2 nötig.")


def gate_proof_production(ctx):
    for comp in ctx.competencies:
        if comp.get("operation") not in PROOF_OPS:
            continue
        cid = comp.get("id")
        ok = any(cid in _cids(a) and a.get("stage") != "worked_example" and a.get("role") != "contrast"
                 and PRODUCE.search(a.get("prompt") or "") for a in ctx.tasks)
        if not ok:
            ctx.add("WB-PROOF-PRODUCTION", f"Kompetenz {cid}",
                    "Keine Aufgabe verlangt die Herleitung/den Beweis selbst (nur Wiedererkennen oder Musterbeispiel).")


# ------------------------------------------------------------------ anki

def gate_card_lint(ctx):
    from ..anki_v2 import card_lint
    for c in ctx.cards:
        for issue in card_lint(c):
            ctx.add("AN-LINT", f"Karte {c.get('key')}", issue)


def _enumeration(answer):
    a = str(answer or "")
    items = [x for x in re.split(r";|\n\s*[-•*]|\n\s*\d+[.)]", a) if x.strip()]
    return len(items) >= 4


def gate_deflist(ctx):
    concept = 0
    for c in ctx.cards:
        if c.get("kind") in ("concept", "fact"):
            concept += 1
        if (c.get("kind") in ("concept", "fact") and DEFLIST_FRONT.search(c.get("front") or "")) or \
                _enumeration(c.get("answer")):
            ctx.add("AN-DEFLIST", f"Karte {c.get('key')}",
                    "Fragt nach einer Definition bzw. Aufzählung statt nach Prinzip, Bedingung oder Zusammenhang.")
    if ctx.cards and concept * 2 > len(ctx.cards):
        ctx.add("AN-DEFLIST", "Kartensatz", f"{concept} von {len(ctx.cards)} Karten sind Begriffs-/Faktenkarten.")


def gate_context(ctx):
    for c in ctx.cards:
        if c.get("kind") == "cloze":
            continue
        if not str(c.get("context") or "").strip():
            ctx.add("AN-CONTEXT", f"Karte {c.get('key')}", "Kein Kontext auf der Karte.")


def gate_visual(ctx):
    visual = {}
    for g in ctx.graphics:
        for cid in _cids(g):
            visual.setdefault(cid, g.get("id"))
    for cid, gid in visual.items():
        if not any(cid in _cids(c) and c.get("figure") for c in ctx.cards):
            ctx.add("AN-VISUAL", f"Kompetenz {cid}", f"Abbildung {gid} gehört zur Kompetenz, aber keine ihrer Karten "
                                                     "zeigt eine Abbildung.")
    for c in ctx.cards:
        if c.get("kind") == "visual" and not c.get("figure"):
            ctx.add("AN-VISUAL", f"Karte {c.get('key')}", "Abbildungskarte ohne Abbildung.")


def gate_identity(ctx):
    uid = ctx.unit.get("unit_id")
    keys = [c.get("key") for c in ctx.cards]
    dup = sorted({k for k in keys if keys.count(k) > 1})
    if dup:
        ctx.add("AN-IDENTITY", "Kartensatz", "Doppelte Kartenschlüssel: " + ", ".join(map(str, dup[:5])))
    if ctx.record and ctx.record.get("unit_id") and ctx.record["unit_id"] != uid:
        ctx.add("AN-IDENTITY", "unit.json", f"unit_id geändert gegenüber dem letzten Bau ({ctx.record['unit_id']}).")
    if ctx.build_dir and (ctx.build_dir / ".em-state").is_dir():
        for m in sorted((ctx.build_dir / ".em-state").glob("anki-*.json")):
            data = _read_json(m) or {}
            if data.get("unit_id") and data["unit_id"] != uid:
                ctx.add("AN-IDENTITY", "Bauordner", f"Anki-Manifest einer anderen unit_id ({data['unit_id']}) im "
                                                    "Bauordner: Identität gebrochen.")
        report = _read_json(ctx.build_dir / "anki_report.json") or {}
        gone = (report.get("update_delta") or {}).get("retirement_candidates") or []
        if gone:
            ctx.add("AN-IDENTITY", "Kartensatz", f"{len(gone)} Karte(n) entfallen seit dem letzten Bau "
                                                 "(in Anki von Hand zurückziehen, nichts wird automatisch gelöscht).",
                    severity="minor")


# ------------------------------------------------------------------ interactive

def _runtime_controls():
    from . import TEMPLATES
    try:
        js = (TEMPLATES / "mastery_motion.js").read_text(encoding="utf-8")
    except OSError:
        return False
    return "type: 'range'" in js and "Schritt" in js


def gate_scenes(ctx):
    found = [(i, s) for i, s, _ in ctx.scenes() if s]
    for i, s, err in ctx.scenes():
        if err:
            ctx.add("IA-SCENE", f"Interaktion {i.get('id')}", "Mastery-Motion-Szene lässt sich nicht bauen: " + err)
    if not found:
        ctx.add("IA-SCENE", "Interaktiv", "Keine Mastery-Motion-Szene: keine Interaktion hat ein Motion-Modell "
                                          f"(Modelle: {', '.join(sorted({str(i.get('model_ref')) for i in ctx.interactions})) or '—'}).")
        return
    runtime = _runtime_controls()
    for i, s in found:
        where = f"Szene {s.get('id')}"
        steps = s.get("steps") or []
        miss = []
        if _words(s.get("claim")) < 4:
            miss.append("V1 keine Aussage (claim)")
        if not any((st.get("transition") or {}).get("kind") not in (None, "none", "highlight")
                   and ((st.get("transition") or {}).get("animate") or st.get("set")) for st in steps):
            miss.append("V2 kein kontinuierlicher Übergang")
        terms = s.get("terms") or {}
        if not terms or not all(isinstance(t, dict) and t.get("objects") for t in terms.values()):
            miss.append("V3 Gleichungsterme nicht an Objekte gebunden")
        if not any(st.get("checkpoint") for st in steps):
            miss.append("V4 kein Vorhersage-Haltepunkt")
        if len(steps) < 2 or not runtime:
            miss.append("V5 Schritt/Zeitachse fehlt")
        if not any(1 <= len(m.get("sliders") or []) <= 3 and m.get("goal") for m in s.get("missions") or []):
            miss.append("V6 kein Auftrag mit 1-3 Reglern und Ziel")
        if not str(i.get("transfer_prompt") or "").strip():
            miss.append("keine eigene Aufgabe nach der Szene")
        if miss:
            ctx.add("IA-MOTION-RULES", where, "; ".join(miss) + ".")


def gate_persist(ctx):
    page = ctx.build_dir / "Interaktiv" / "index.html" if ctx.build_dir else None
    if not page or not page.is_file():
        ctx.skip("IA-PERSIST", "kein gebautes Interaktiv/index.html")
        return
    html = page.read_text(encoding="utf-8", errors="replace")
    miss = []
    if "em-practice-v1" not in html or "localStorage" not in html:
        miss.append("Lernstand wird nicht gespeichert (em-practice-v1)")
    if not all(t in html for t in ('"attempt"', '"hint"', '"solution_reveal"')):
        miss.append("Versuch und Hilfe werden nicht getrennt protokolliert")
    if 'class="mm-scene"' in html and "em-motion-v1" not in html:
        miss.append("Motion-Vorhersagen werden nicht gespeichert (em-motion-v1)")
    if miss:
        ctx.add("IA-PERSIST", "Interaktiv/index.html", "; ".join(miss) + ".")


# ------------------------------------------------------------------ page QA (pymupdf geometry)

def _lines(page):
    out = []
    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        for ln in b["lines"]:
            spans = [s for s in ln["spans"] if s["text"].strip()]
            if spans:
                out.append({"bbox": ln["bbox"], "spans": spans, "size": max(s["size"] for s in spans),
                            "text": "".join(s["text"] for s in spans).strip()})
    return out


def _body_size(doc):
    from collections import Counter
    sizes = Counter()
    for page in doc:
        for ln in _lines(page):
            for s in ln["spans"]:
                sizes[round(s["size"], 1)] += len(s["text"])
    return sizes.most_common(1)[0][0] if sizes else 10.0


def _is_heading(ln, body):
    if len(re.findall(r"[^\W\d_]", ln["text"])) < 3:     # page numbers (table of contents), labels
        return False
    if ln["size"] >= body * 1.3:
        return True
    bold = all(re.search(r"(?i)bold|semibold|-bo|-se|heavy|black", s["font"]) for s in ln["spans"])
    return bold and ln["size"] >= body * 0.97 and len(ln["text"]) <= 90 and not ln["text"].endswith((".", ":", ","))


def _clipped_objects(page, pymupdf):
    """(edge, cut): drawn objects whose visible part crosses the paper edge, and glyph-sized filled paths (formula
    glyphs) cut by a container-sized clip. Visible part = rect intersected with the active clip regions. Objects
    entirely off the page are print-engine fragments of other pages (invisible, not cut); clips of glyph size are
    stretchy-delimiter assemblies (MathJax), and long strokes cut by a figure frame are intended (grid lines)."""
    r = page.rect
    stack, edge, cut = [], 0, 0
    for e in page.get_drawings(extended=True):
        lvl = e.get("level", 0)
        while stack and stack[-1][0] >= lvl:
            stack.pop()
        kind = e.get("type")
        if kind == "clip":
            stack.append((lvl, pymupdf.Rect(e["scissor"])))
            continue
        if kind == "group" or e.get("rect") is None:
            continue
        rect = pymupdf.Rect(e["rect"])
        vis = pymupdf.Rect(rect)
        for _, c in stack:
            vis &= c
        if vis.is_empty or not vis.intersects(r):
            continue
        if vis.x0 < r.x0 - 1 or vis.y0 < r.y0 - 1 or vis.x1 > r.x1 + 1 or vis.y1 > r.y1 + 1:
            edge += 1
        elif kind in ("f", "fs") and 0 < rect.width < 30 and 0 < rect.height < 30:
            cutters = [c for _, c in stack if not (rect.x0 >= c.x0 - 0.5 and rect.y0 >= c.y0 - 0.5
                                                    and rect.x1 <= c.x1 + 0.5 and rect.y1 <= c.y1 + 0.5)]
            if any(c.width >= 60 or c.height >= 60 for c in cutters):
                cut += 1
    for info in page.get_image_info():
        b = pymupdf.Rect(info["bbox"])
        if b.intersects(r) and (b.x0 < r.x0 - 1 or b.y0 < r.y0 - 1 or b.x1 > r.x1 + 1 or b.y1 > r.y1 + 1):
            edge += 1
    return edge, cut


def check_pdf(path, label):
    """Findings for one PDF as (gate, location, message). Pure geometry; no rendering, no model."""
    import pymupdf
    out = []
    with pymupdf.open(path) as doc:
        body = _body_size(doc)
        n = len(doc)
        small = {}
        for pno, page in enumerate(doc, start=1):
            r = page.rect
            lines = _lines(page)
            where = f"{label} S. {pno}"
            over = [ln for ln in lines if ln["bbox"][0] < r.x0 + EDGE_PT - 0.5 or ln["bbox"][2] > r.x1 - EDGE_PT + 0.5
                    or ln["bbox"][1] < r.y0 - 0.5 or ln["bbox"][3] > r.y1 + 0.5]
            if over:
                out.append(("PG-OVERFLOW", where, f"{len(over)} Textzeile(n) ragen über den Rand, z. B. "
                                                  f"„{over[0]['text'][:40]}“."))
            edge, cut = _clipped_objects(page, pymupdf)
            if edge:
                out.append(("PG-OVERFLOW", where, f"{edge} Grafik-/Formelobjekt(e) über den Seitenrand hinaus "
                                                  "(abgeschnitten)."))
            if cut:
                out.append(("PG-OVERFLOW", where, f"{cut} Formel-/Schriftzeichen von einem Rahmen abgeschnitten "
                                                  "(Inhalt breiter als sein Kasten)."))
            for ln in lines:
                for s in ln["spans"]:
                    if s["size"] < FONT_FLOOR_PT - 0.05:
                        small.setdefault(pno, [0, s["size"]])
                        small[pno][0] += 1
                        small[pno][1] = min(small[pno][1], s["size"])
            bodylines = sorted((ln for ln in lines if ln["bbox"][1] >= BAND_TOP and ln["bbox"][3] <= BAND_BOTTOM),
                               key=lambda ln: (ln["bbox"][1], ln["bbox"][0]))
            if not bodylines or pno == 1:
                continue
            heads = [k for k, ln in enumerate(bodylines) if _is_heading(ln, body)]
            toc = re.match(r"(?i)^(inhalt|inhaltsverzeichnis|contents)$", bodylines[0]["text"])   # entries, not headings
            if pno < n and heads and not toc:
                last = heads[-1]
                hy = bodylines[last]["bbox"][3]
                after = [ln for ln in bodylines[last + 1:] if ln["bbox"][1] > hy - 1]
                art = [d["rect"] for d in page.get_drawings() if d.get("rect") is not None and d["rect"].y0 > hy - 1
                       and d["rect"].y1 <= BAND_BOTTOM and d["rect"].height > 8] + \
                      [i["bbox"] for i in page.get_image_info() if hy - 1 < i["bbox"][1] < BAND_BOTTOM]
                if len(after) <= 1 and not art and bodylines[last]["bbox"][1] > BAND_TOP + (BAND_BOTTOM - BAND_TOP) * 0.5:
                    out.append(("PG-ORPHAN-HEADING", where, f"Überschrift „{bodylines[last]['text'][:50]}“ steht am "
                                                            "Seitenende ohne folgenden Text."))
            top, bottom = bodylines[0]["bbox"][1], max(ln["bbox"][3] for ln in bodylines)
            starts_with_heading = bool(heads) and heads[0] == 0
            if not starts_with_heading and (bottom - top) < NEAR_EMPTY * (BAND_BOTTOM - BAND_TOP):
                out.append(("PG-NEAR-EMPTY", where, f"Seite fast leer ({int(100 * (bottom - top) / (BAND_BOTTOM - BAND_TOP))} % "
                                                    "des Satzspiegels): Rest eines Abschnitts auf eigener Seite."))
            for link in page.get_links():
                if link.get("kind") == pymupdf.LINK_GOTO and not 0 <= link.get("page", -1) < n:
                    out.append(("PG-LINKS", where, f"Interner Verweis auf nicht vorhandene Seite {link.get('page', -1) + 1}."))
                if link.get("kind") == pymupdf.LINK_NAMED and not link.get("page", -1) in range(n):
                    out.append(("PG-LINKS", where, "Benannter Verweis ohne Ziel."))
                if PRIVATE_PATH.search(str(link.get("uri") or "") + str(link.get("file") or "")):
                    out.append(("INT-PRIVATE-PATHS", where, "Verweis auf einen lokalen Pfad."))
            if PRIVATE_PATH.search(page.get_text()):
                out.append(("INT-PRIVATE-PATHS", where, "Lokaler Pfad im Text."))
        for pno, (count, size) in sorted(small.items()):
            out.append(("PG-FONT-FLOOR", f"{label} S. {pno}", f"{count} Textstück(e) unter {FONT_FLOOR_PT:g} pt "
                                                               f"(kleinste {size:.1f} pt)."))
    return out


def gate_pages(ctx):
    if not ctx.build_dir:
        for g in ("PG-OVERFLOW", "PG-ORPHAN-HEADING", "PG-NEAR-EMPTY", "PG-LINKS", "PG-FONT-FLOOR"):
            ctx.skip(g, "keine gebauten PDFs")
        return
    try:
        import pymupdf  # noqa: F401
    except ImportError:
        for g in ("PG-OVERFLOW", "PG-ORPHAN-HEADING", "PG-NEAR-EMPTY", "PG-LINKS", "PG-FONT-FLOOR"):
            ctx.skip(g, "pymupdf nicht installiert")
        return
    for name, label in (("Lehrbuch.pdf", "Lehrbuch"), ("Arbeitsbuch.pdf", "Arbeitsbuch")):
        path = ctx.build_dir / name
        if not path.is_file():
            continue
        for gid, where, msg in check_pdf(path, label):
            ctx.add(gid, where, msg)


# ------------------------------------------------------------------ integrity

def _status_values(obj, keys):
    for k, v in (obj or {}).items():
        if k in keys and isinstance(v, str):
            yield k, v
        elif k in keys and isinstance(v, dict):
            for kk, vv in v.items():
                if isinstance(vv, str) and kk in ("status", "value", "state"):
                    yield k, vv


def gate_review(ctx):
    sources = [("unit.json", ctx.unit.get("authorship") or {}), ("unit.json", ctx.unit),
               ("authoring.json", ctx.authoring or {})]
    for where, obj in sources:
        for k, v in _status_values(obj, {"human_status", "status", "human_review", "academic_status", "review"}):
            if v.strip().upper() in SELF_APPROVAL:
                ctx.add("INT-REVIEW", where, f"{k} = {v}: Selbstfreigabe ist nicht zulässig.")
    if ctx.build_dir and (ctx.build_dir / ".em-state").is_dir():
        for m in sorted((ctx.build_dir / ".em-state").glob("anki-*.json")):
            st = (_read_json(m) or {}).get("academic_status")
            if st and st != "HUMAN_REVIEW_PENDING":
                ctx.add("INT-REVIEW", "Anki-Manifest", f"academic_status = {st} statt HUMAN_REVIEW_PENDING.")


def gate_learning_eval(ctx):
    for where, obj in (("unit.json", ctx.unit), ("unit.json", ctx.unit.get("authorship") or {}),
                       ("authoring.json", ctx.authoring or {})):
        for k, v in _status_values(obj, {"learning_effect", "learning_evaluation", "learning_status"}):
            if v.strip().upper() != "NOT_RUN":
                ctx.add("INT-LEARNING-EVAL", where, f"{k} = {v}: Lernwirkung ist nicht gemessen (NOT_RUN).")


def gate_tutor_keys(ctx):
    from ..learning.guided import evidence_keys
    keys = evidence_keys({"assessments": ctx.tasks})
    texts = []
    for a in ctx.tasks:
        texts += [("Hinweis " + str(a.get("id")), h) for h in a.get("hints") or [] if isinstance(h, str)]
    for lesson in ctx.unit.get("lessons") or []:
        if isinstance(lesson, dict):
            texts.append(("Lektion " + str(lesson.get("id")), "\n".join(_strings(lesson))))
    for where, text in texts:
        hit = [k for k in keys if k in text]
        if hit:
            ctx.add("INT-TUTOR-KEYS", where, f"Enthält den Schlüssel einer Nachweisaufgabe („{hit[0][:40]}“).")
    page = ctx.build_dir / "Interaktiv" / "index.html" if ctx.build_dir else None
    if page and page.is_file():
        html = page.read_text(encoding="utf-8", errors="replace")
        m = re.search(r'<script[^>]*id="em-interactive-data"[^>]*>(.*?)</script>', html, re.S)
        if m:
            try:
                data = json.loads(m.group(1))
            except ValueError:
                data = {}
            for view in data.get("assessments") or []:
                if view.get("role") in EVIDENCE_ROLES and view.get("solution"):
                    ctx.add("INT-TUTOR-KEYS", f"Interaktiv, Aufgabe {view.get('id')}",
                            "Tutor-Ansicht einer Nachweisaufgabe enthält die Lösung.")


def gate_private_paths(ctx):
    for s in _strings(ctx.unit):
        m = PRIVATE_PATH.search(s)
        if m:
            ctx.add("INT-PRIVATE-PATHS", "unit.json", f"Lokaler Pfad im Inhalt („{m.group(0)[:12]}…“).")
            break
    if not ctx.build_dir:
        return
    for name in ("Interaktiv/index.html", "anki_report.json"):
        p = ctx.build_dir / name
        if p.is_file():
            m = PRIVATE_PATH.search(p.read_text(encoding="utf-8", errors="replace"))
            if m:
                ctx.add("INT-PRIVATE-PATHS", name, f"Lokaler Pfad („{m.group(0)[:12]}…“).")


CHECKS = (gate_chain, gate_proof, gate_figures, gate_locators, gate_divergence, gate_stages, gate_solutions,
          gate_alt_routes, gate_find_error, gate_proof_production, gate_card_lint, gate_deflist, gate_context,
          gate_visual, gate_identity, gate_scenes, gate_persist, gate_pages, gate_review, gate_learning_eval,
          gate_tutor_keys, gate_private_paths)


# ------------------------------------------------------------------ report

def check(unit, build_dir=None, chapter_dir=None):
    """Run every gate of the catalogue; returns the report dict (schema mastery-quality-report-v1)."""
    ctx = _Ctx(unit, build_dir, chapter_dir)
    for fn in CHECKS:
        fn(ctx)
    order = {g["id"]: i for i, g in enumerate(GATES)}
    rank = {s: i for i, s in enumerate(SEVERITIES)}
    findings = sorted(ctx.findings, key=lambda f: (rank[f["severity"]], order[f["gate"]], f["location"]))
    counts = {s: sum(f["severity"] == s for f in findings) for s in SEVERITIES}
    gates = []
    for g in GATES:
        n = [f for f in findings if f["gate"] == g["id"]]
        status = "fail" if n else ("not_checked" if g["id"] in ctx.not_checked else "pass")
        if n and g["id"] in ctx.not_checked:
            status = "fail"
        gates.append({**{k: g[k] for k in ("id", "product", "section", "severity", "rule")}, "status": status,
                      "findings": len(n), **({"note": ctx.not_checked[g["id"]]} if g["id"] in ctx.not_checked else {})})
    status = ("BLOCKERS" if counts["blocker"] else "MAJOR_FINDINGS" if counts["major"] else
              "MINOR_FINDINGS" if counts["minor"] else "NO_MACHINE_FINDINGS")
    return {"schema": SCHEMA, "catalogue": CATALOGUE, "unit_id": unit.get("unit_id"), "title": unit.get("title"),
            "checked_at": _now(), "status": status, "counts": counts, "gates": gates, "findings": findings,
            "human_review": "HUMAN_REVIEW_PENDING", "learning_evaluation": "NOT_RUN", "model_calls": 0,
            "scope": "Maschinell entscheidbare Kriterien aus Lernstandard §5.1-§5.4 und V1-V10. Kein Gate gibt ein "
                     "Kapitel frei; die fachliche und didaktische Abnahme bleibt beim Owner."}


def summary(report):
    c = report["counts"]
    return {"status": report["status"], "counts": dict(c), "catalogue": report["catalogue"],
            "checked_at": report["checked_at"]}


def summary_line(report):
    c = report["counts"]
    return (f"Qualitätsprüfung ({report['catalogue']}): {c['blocker']} Blocker, {c['major']} schwer, {c['minor']} leicht"
            f" – {STATUS_DE[report['status']]}")


STATUS_DE = {"BLOCKERS": "Blocker vorhanden: nicht an den Owner geben",
             "MAJOR_FINDINGS": "schwere Befunde: vor der Owner-Prüfung beheben",
             "MINOR_FINDINGS": "nur leichte Befunde",
             "NO_MACHINE_FINDINGS": "ohne maschinellen Befund (fachliche Prüfung steht aus)"}
GATE_STATUS_DE = {"pass": "bestanden", "fail": "Befund", "not_checked": "nicht geprüft"}


def to_markdown(report):
    c = report["counts"]
    lines = [f"# Qualitätsbericht: {report['title']}", "",
             f"Katalog `{report['catalogue']}` · geprüft {report['checked_at']} · Einheit `{report['unit_id']}`", "",
             f"**{STATUS_DE[report['status']]}** – {c['blocker']} Blocker, {c['major']} schwer, {c['minor']} leicht.", "",
             "Maschinelle Prüfung. Sie ersetzt nicht die Abnahme durch den Owner (HUMAN_REVIEW_PENDING); "
             "Lernwirkung nicht gemessen (NOT_RUN).", "", "## Befunde", ""]
    if not report["findings"]:
        lines.append("Keine maschinellen Befunde.")
    for f in report["findings"]:
        lines.append(f"- **{SEVERITY_DE[f['severity']]}** `{f['gate']}` ({PRODUCT_DE[f['product']]}, {f['section']}) – "
                     f"{f['location']}: {f['message']} *Beheben:* {f['fix']}")
    lines += ["", "## Gates", "", "| Gate | Produkt | Schwere | Ergebnis | Befunde |", "|---|---|---|---|---|"]
    for g in report["gates"]:
        lines.append(f"| `{g['id']}` | {PRODUCT_DE[g['product']]} | {SEVERITY_DE[g['severity']]} | "
                     f"{GATE_STATUS_DE[g['status']]}{' (' + g['note'] + ')' if g.get('note') else ''} | {g['findings']} |")
    return "\n".join(lines) + "\n"


CSS = """body{font:15px/1.5 -apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;margin:0;background:#fbfbfa;color:#18212b}
main{max-width:980px;margin:0 auto;padding:24px 16px 48px}h1{font-size:1.5rem;margin:.2rem 0}h2{font-size:1.15rem;margin:1.6rem 0 .5rem}
.meta,.note{color:#4a5563;font-size:.9rem}.status{padding:.6rem .8rem;border-left:4px solid #1f5673;background:#eef3f6;margin:1rem 0}
.status[data-status=BLOCKERS]{border-color:#b3261e;background:#fbeceb}.status[data-status=MAJOR_FINDINGS]{border-color:#9a6100;background:#fbf3e6}
table{border-collapse:collapse;width:100%;font-size:.9rem}th,td{border-bottom:1px solid #d8dde2;padding:.35rem .4rem;text-align:left;vertical-align:top}
.sev{font-weight:700;white-space:nowrap}.sev-blocker{color:#b3261e}.sev-major{color:#8a5600}.sev-minor{color:#4a5563}
code{font-size:.85em}.fix{color:#4a5563}
@media (prefers-color-scheme:dark){body{background:#12161f;color:#e6e8ee}.meta,.note,.fix,.sev-minor{color:#aab2c0}
.status{background:#1b2230}.status[data-status=BLOCKERS]{background:#2a1716}.status[data-status=MAJOR_FINDINGS]{background:#2a2213}
th,td{border-color:#2c3442}.sev-blocker{color:#ff8a80}.sev-major{color:#f2b544}}"""


def to_html(report):
    c = report["counts"]
    rows = "".join(
        f'<tr data-gate="{escape(f["gate"])}" data-severity="{f["severity"]}"><td class="sev sev-{f["severity"]}">'
        f'{SEVERITY_DE[f["severity"]]}</td><td><code>{escape(f["gate"])}</code><br>{escape(PRODUCT_DE[f["product"]])}, '
        f'{escape(f["section"])}</td><td>{escape(f["location"])}</td><td>{escape(f["message"])}'
        f'<div class="fix">Beheben: {escape(f["fix"])}</div></td></tr>' for f in report["findings"])
    gates = "".join(
        f'<tr data-gate-status="{g["status"]}"><td><code>{escape(g["id"])}</code></td><td>{escape(PRODUCT_DE[g["product"]])}'
        f'</td><td>{SEVERITY_DE[g["severity"]]}</td><td>{GATE_STATUS_DE[g["status"]]}'
        f'{" – " + escape(g["note"]) if g.get("note") else ""}</td><td>{g["findings"]}</td><td>{escape(g["rule"])}</td></tr>'
        for g in report["gates"])
    csp = "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"
    return ('<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" '
            f'content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="{csp}">'
            f'<title>Qualitätsbericht – {escape(str(report["title"]))}</title><style>{CSS}</style></head><body><main>'
            f'<p class="meta">Mastery · Qualitätsbericht · Katalog {escape(report["catalogue"])}</p>'
            f'<h1>{escape(str(report["title"]))}</h1><p class="meta">Einheit <code>{escape(str(report["unit_id"]))}</code> · '
            f'geprüft {escape(report["checked_at"])}</p>'
            f'<p class="status" data-status="{report["status"]}" id="quality-status"><strong>{STATUS_DE[report["status"]]}</strong>'
            f' – <span data-count="blocker">{c["blocker"]}</span> Blocker, <span data-count="major">{c["major"]}</span> '
            f'schwer, <span data-count="minor">{c["minor"]}</span> leicht.</p>'
            '<p class="note">Maschinelle Prüfung der entscheidbaren Kriterien des Lernstandards (§5.1-§5.4, V1-V10). '
            'Sie blockiert offensichtliche Mängel und ersetzt nicht die Abnahme durch den Owner (HUMAN_REVIEW_PENDING). '
            'Lernwirkung nicht gemessen (NOT_RUN). Heuristische Regeln sind als solche gekennzeichnet.</p>'
            f'<h2>Befunde ({len(report["findings"])})</h2>'
            + (f'<table><thead><tr><th>Schwere</th><th>Gate</th><th>Ort</th><th>Befund</th></tr></thead><tbody>{rows}'
               '</tbody></table>' if report["findings"] else '<p>Keine maschinellen Befunde.</p>') +
            f'<h2>Gates ({len(report["gates"])})</h2><table><thead><tr><th>Gate</th><th>Produkt</th><th>Schwere</th>'
            f'<th>Ergebnis</th><th>Befunde</th><th>Regel</th></tr></thead><tbody>{gates}</tbody></table>'
            '</main></body></html>\n')


def write(report, build_dir):
    """Write quality.json, quality.html and quality.md into the build folder; returns their names."""
    out = Path(build_dir)
    out.mkdir(parents=True, exist_ok=True)
    files = {"quality.json": json.dumps(report, ensure_ascii=False, indent=1) + "\n",
             "quality.html": to_html(report), "quality.md": to_markdown(report)}
    for name, text in files.items():
        tmp = out / (name + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(out / name)
    return list(files)


def run(unit, build_dir, chapter_dir=None):
    report = check(unit, build_dir, chapter_dir)
    write(report, build_dir)
    return report


def catalogue():
    return {"schema": "mastery-quality-catalogue-v1", "id": CATALOGUE, "gates": [dict(g) for g in GATES]}
