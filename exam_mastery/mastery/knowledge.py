"""Project authored chapter semantics into a portable, course-local knowledge graph."""
import json
import re
from collections import defaultdict

import pymupdf
import yaml

from .. import figures_svg
from ..learning import experience_graphics, experience_math
from ..learning.experience import validate
from . import MasteryError, resolve_home
from .courses import _packet_name, load_course
from .knowledge_publish import digest, publish


def label(key):
    return key.rsplit("/", 1)[-1].replace("-", " ").capitalize()


def filename(kind, identity):
    stem = re.sub(r"[^a-z0-9-]+", "-", identity.lower()).strip("-")[-48:]
    return f"{kind}-{stem}-{digest(identity.encode())[:16]}"


class Graph:
    def __init__(self):
        self.nodes = {}
        self.edges = defaultdict(dict)
        self.files = {}

    def add(self, kind, identity, title, body="", **properties):
        path = filename(kind, identity)
        if path in self.nodes:
            raise MasteryError("Mehrdeutige Wissens-ID: " + identity)
        self.nodes[path] = (kind, identity, title, body, properties)
        return path

    def link(self, source, target, relation):
        if source not in self.nodes or target not in self.nodes:
            raise MasteryError("Fehlendes Verweisziel: " + target)
        self.edges[source][target] = relation
        self.edges[target].setdefault(source, "Verwendet in")

    def render(self):
        for path, (kind, identity, title, body, properties) in self.nodes.items():
            lines = ["# " + title, "", body]
            for target, relation in self.edges[path].items():
                title_to = self.nodes[target][2].replace("\n", " ").replace("|", "–").replace("]", ")")
                lines.append(f"- [{relation}]({target}.md) · [[{target}|{title_to}]]")
            content = "\n".join(lines).strip() + "\n"
            content = experience_math.MATH.sub(lambda m: "$" + m[1] + "$" if m[1] is not None
                                               else "\n$$\n" + m[2] + "\n$$\n", content)
            props = dict(em_id=kind + "/" + identity, em_kind=kind, em_generated=True, aliases=[title], **properties)
            props["em_version"] = digest((content + json.dumps(props, sort_keys=True)).encode())
            self.files[path + ".md"] = ("---\n" + yaml.safe_dump(props, allow_unicode=True, sort_keys=False)
                                        + "---\n\n" + content).encode()
        return self.files


def chapter_graph(graph, parent, course_slug, chapter_id, unit, built):
    result = validate(unit)
    if not result["valid"]:
        raise MasteryError("Ungültige Kapitelreferenz: " + "; ".join(result["errors"][:5]))
    u = experience_math.project(unit)
    identity = course_slug + "/" + u["unit_id"]
    assets = "Medien/" + filename("kapitel", identity)
    book_pages = {}
    task_pages = {}
    if built:
        from ..learning.experience_pipeline import preflight
        try:
            preflight(unit, built)
        except ValueError as exc:
            raise MasteryError(str(exc)) from exc
        for name in ("Lehrbuch.pdf", "Arbeitsbuch.pdf", "Interaktiv/index.html", "Anki.apkg"):
            src = built / name
            if src.resolve() != src or not src.is_file():
                raise MasteryError("Produkt fehlt oder ist umgeleitet: " + name)
            graph.files[assets + "/" + name] = src
        with pymupdf.open(built / "Lehrbuch.pdf") as doc:
            book_pages = {title.split(" ", 1)[-1].strip(): page for _, title, page in doc.get_toc()}
        with pymupdf.open(built / "Arbeitsbuch.pdf") as doc:
            for number, page in enumerate(doc, 1):
                for taskno in re.findall(r"^Aufgabe (\d+)\b", page.get_text(), re.M):
                    task_pages.setdefault(int(taskno), number)
    products = ("\n".join(f"- [{name}]({assets}/{name})" for name in
                ("Lehrbuch.pdf", "Arbeitsbuch.pdf", "Interaktiv/index.html", "Anki.apkg")) if built else
                "Für diese Fassung liegen keine aktuellen gebauten Lernprodukte vor.")
    cap = graph.add("Kapitel", course_slug + "/" + chapter_id, u["title"], products)
    graph.link(parent, cap, "Kapitel")
    ids = {}
    def node(kind, key, title, body, **props):
        path = graph.add(kind, identity + "/" + kind + "/" + key, title, body, **props)
        ids[kind, key] = path
        graph.link(cap, path, kind)
        return path

    for source in u["sources"]:
        node("Quelle", source["id"], source.get("short") or source["id"], source["locator"],
             em_source_kind=source["kind"], em_source_id=source["id"])
    for claim in u["claims"]:
        path = node("Aussage", claim["id"], label(claim["id"]), claim["text"],
                    em_sources=claim["source_refs"], em_evidence=claim["evidence_status"])
        for key in claim["source_refs"]:
            graph.link(path, ids["Quelle", key], "Beleg")
    for skill in u["competencies"]:
        node("Kompetenz", skill["id"], skill.get("title") or label(skill["id"]), skill["operation"])
    for skill in u["competencies"]:
        for key in skill.get("prerequisites", []):
            graph.link(ids["Kompetenz", skill["id"]], ids["Kompetenz", key], "Voraussetzung")

    sources_by_claim = {claim["id"]: claim["source_refs"] for claim in u["claims"]}

    def connect(path, item):
        props = graph.nodes[path][4]
        props["em_competencies"] = item.get("competency_ids", [])
        props["em_sources"] = sorted({src for claim in item.get("claim_ids", []) for src in sources_by_claim[claim]})
        for key in item.get("competency_ids", []):
            graph.link(path, ids["Kompetenz", key], "Kompetenz")
        for key in item.get("claim_ids", []):
            graph.link(path, ids["Aussage", key], "Fachliche Grundlage")

    for section in u["teaching"]:
        title = section.get("section_title") or label(section["id"])
        body = section["content"]
        if derivation := section.get("derivation"):
            from ..learning.experience_proof_checks import verify
            steps = [derivation["given"]]
            for step in derivation["steps"]:
                steps.append(step["statement"] + " " + step["justification"])
                if "math_check" in step:
                    steps.append(verify(step["math_check"])["latex"])
            body += "\n\n## " + derivation["title"] + "\n\n" + "\n\n".join(steps + [derivation["result"]])
        if title in book_pages:
            body += f"\n\n[Lehrbuchabschnitt]({assets}/Lehrbuch.pdf#page={book_pages[title]})"
        path = node("Konzept", section["id"], title, body)
        connect(path, section)
        definitions = [b for b in section.get("blocks", []) if b["type"] == "definition"]
        if len(definitions) > 1 and any(not b.get("id") for b in definitions):
            raise MasteryError("Mehrere Definitionen in einem Abschnitt benötigen stabile IDs: " + section["id"])
        for block in definitions:
            key = block.get("id") or section["id"] + "/definition"
            definition = node("Definition", key, block["term"], block["md"])
            graph.link(definition, path, "Erklärung")
            connect(definition, section)
    for taskno, task in enumerate(u["assessments"], 1):
        body = task["prompt"]
        if built:
            anchor = f"#page={task_pages[taskno]}" if taskno in task_pages else ""
            body += f"\n\n[Aufgabe {taskno} im Arbeitsbuch]({assets}/Arbeitsbuch.pdf{anchor})"
        connect(node("Aufgabe", task["id"], task.get("title") or label(task["id"]), body), task)
    for scene in u["interactions"]:
        body = scene.get("prediction_prompt") or label(scene["id"])
        if built:
            body += f"\n\n[Interaktive Erklärung öffnen]({assets}/Interaktiv/index.html)"
        connect(node("Interaktion", scene["id"], label(scene["id"]), body), scene)
    for card in u["cards"]:
        connect(node("Karte", card["key"], label(card["key"]), card.get("front") or card.get("text", ""),
                     em_cards=[card["key"]]), card)
    for graphic, frame, spec in experience_graphics.specifications(u):
        image = assets + "/" + filename("bild", graphic["id"]) + f"-{frame}.svg"
        graph.files[image] = figures_svg.render(spec).encode()
        node_id = ids["Konzept", graphic["teaching_id"]]
        kind, key, title, body, props = graph.nodes[node_id]
        graph.nodes[node_id] = kind, key, title, body + f"\n\n![{graphic['alt']}]({image})\n\n{graphic['caption']}", props


def export_course(slug, home=None):
    root = resolve_home(home)
    cdir, course = load_course(slug, root)
    if cdir.resolve() != cdir:
        raise MasteryError("Umgeleiteter Kursordner")
    graph = Graph()
    start = graph.add("Kurs", slug, course["title"], "## Kapitelübersicht\n")
    for ch in course["chapters"]:
        if ch.get("skip"):
            continue
        folder = cdir / "chapters" / ch["id"]
        if folder.resolve() != folder or folder.parent != cdir / "chapters":
            raise MasteryError("Ungültiger Kapitelpfad")
        path = folder / "unit.json"
        if not path.exists():
            graph.link(start, graph.add("Kapitel", slug + "/" + ch["id"], ch["title"],
                                        "Dieses geplante Kapitel ist noch nicht erarbeitet."), "Geplant")
            continue
        if path.is_symlink():
            raise MasteryError("Umgeleitete Kapiteldatei")
        raw = path.read_bytes()
        rec = folder / "build-record.json"
        built = rec.is_file() and not rec.is_symlink() and json.loads(rec.read_text()).get("unit_sha256") == digest(raw)
        unit = json.loads(raw)
        chapter_graph(graph, start, slug, ch["id"], unit, folder / "build" if built else None)
        cap = filename("Kapitel", slug + "/" + ch["id"])
        packet_path = folder / _packet_name(folder)
        if packet_path.is_file() and not packet_path.is_symlink():
            packet = json.loads(packet_path.read_text())
            inventory = {f["file_id"]: f for f in course["files"]}
            listed = []
            for source in packet.get("sources", []):
                locators = ", ".join(str(p.get("locator") or p["n"]) for p in source.get("pages", []))
                fingerprint = inventory.get(source["file_id"], {}).get("sha256") or "unbekannt"
                listed.append(f"- {source['rel_path']} · {locators or 'keine Seiten ausgewiesen'} "
                              f"· Inventar-ID `{source['file_id']}` · aktueller Inventarhash `{fingerprint}`")
            if listed:
                provenance = graph.add("Quellumfang", slug + "/" + unit["unit_id"], "Quellumfang · " + ch["title"],
                                       "Im Autorenpaket enthaltene Quellen. Einzelbelege stehen bei den Aussagen.\n\n"
                                       + "\n".join(listed))
                graph.link(cap, provenance, "Paketumfang")
        if course.get("chapter_state", {}).get(ch["id"], {}).get("stale"):
            graph.link(cap, graph.add("Quellenstand", slug + "/" + ch["id"], "Quellen seit Paket geändert",
                                      "Die Kapitelüberarbeitung steht aus."), "Prüfbedarf")
    files = graph.render()
    files["00-Start.md"] = (f"# {course['title']}\n\n[Kursübersicht und Inhaltsverzeichnis]({start}.md)\n\n"
                            "Eigene Ergänzungen gehören in den benachbarten Ordner Mastery-Notizen.\n").encode()
    vault = root / "Wissensgraph" / slug
    publish(vault, files)
    return vault / "Mastery" / "00-Start.md"
