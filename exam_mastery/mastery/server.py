"""Offline static server for the Mastery library: stdlib only, 127.0.0.1 only, explicit file allow-list.

The fixed default port matters: localStorage belongs to the origin http://127.0.0.1:<port>, so a different port
shows a different (empty) learner state. POST /api/state accepts a size-limited, schema-checked snapshot of that
browser state as a backup into MASTERY_HOME/state; requests from other hosts or origins are refused (DNS rebinding,
cross-site POST).

Course import (wizard): GET /api/courses[/<slug>] and POST /api/import, /api/courses/<slug>/{reimport,materialize,plan,author},
/api/courses/<slug>/chapters/<id>/{packet,build}. Import accepts only absolute folders strictly inside the user's home
folder, outside the repository and the library; source folders are only read. Operations run one at a time.
"""
from __future__ import annotations

import json
import os
import shutil
import stat
from contextlib import ExitStack, contextmanager
import mimetypes
import re
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from . import TEMPLATES, MAX_STATE_BYTES, MasteryError, state_meta, store_state

ALLOWED = re.compile(
    r"^/(index\.html|library\.json|assets/[A-Za-z0-9_.-]+\.(?:css|js)|motion/[a-z0-9][a-z0-9-]{0,60}\.html"
    r"|units/[a-z0-9][a-z0-9-]*/(?:Lehrbuch\.pdf|Arbeitsbuch\.pdf|Anki\.apkg|anki_report\.json|quality\.(?:html|json)"
    r"|Interaktiv/index\.html"
    r"|tracks/[A-Za-z0-9_.-]+\.(?:html|json))"
    r"|courses/[a-z0-9][a-z0-9-]*/chapters/[a-z0-9][a-z0-9-]*/build/(?:Lehrbuch\.pdf|Arbeitsbuch\.pdf|Anki\.apkg"
    r"|anki_report\.json|quality\.(?:html|json)|Interaktiv/index\.html|tracks/[A-Za-z0-9_.-]+\.(?:html|json)))$")
COURSE_GET = re.compile(r"^/api/courses(?:/([a-z0-9][a-z0-9-]{0,40}))?$")
COURSE_POST = re.compile(r"^/api/(?:import|courses/([a-z0-9][a-z0-9-]{0,40})/(reimport|materialize|plan|author"
                         r"|chapters/([a-z0-9][a-z0-9-]{0,70})/(packet|build|feedback)))$")
CARD_VIEW = re.compile(r"/cards/([a-z0-9][a-z0-9-]{0,40})/([a-z0-9][a-z0-9-]{0,70})/(.*)")
MAX_API_BYTES = 64_000
MAX_ANKI_STATS_BYTES = 41_000_000   # base64 of an Anki export up to anki_stats.MAX_FILE_BYTES plus the JSON envelope
TYPES = {".html": "text/html; charset=utf-8", ".json": "application/json; charset=utf-8",
         ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".pdf": "application/pdf",
         ".apkg": "application/octet-stream"}


@contextmanager
def _open_product(root, relative):
    """Pin each directory while opening its child and refuse links throughout."""
    components = relative.parts
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    with ExitStack() as stack:
        directory = os.open(root, directory_flags)
        stack.callback(os.close, directory)
        for component in components[:-1]:
            directory = os.open(component, directory_flags, dir_fd=directory)
            stack.callback(os.close, directory)
        fd = os.open(components[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        stream = stack.enter_context(os.fdopen(fd, "rb"))
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise FileNotFoundError
        yield stream, info.st_size


class Handler(BaseHTTPRequestHandler):
    server_version = "Mastery/1"
    sys_version = ""

    def log_message(self, fmt, *args):  # quiet by default; nothing about the learner goes to the terminal
        if getattr(self.server, "verbose", False):
            super().log_message(fmt, *args)

    def _hosts(self):
        port = self.server.server_address[1]
        return {f"127.0.0.1:{port}", f"localhost:{port}"}

    def _host_ok(self):
        return self.headers.get("Host", "") in self._hosts()

    def _send(self, code, body, ctype="application/json; charset=utf-8", extra=None):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        self._headers(code, len(data), ctype, extra)
        if self.command != "HEAD":
            self.wfile.write(data)

    def _headers(self, code, length, ctype, extra):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, {"error": "host"})
        path = unquote(urlsplit(self.path).path)
        if path == "/":
            path = "/index.html"
        if path == "/api/ping":
            return self._send(200, {"app": "mastery", "version": 1})
        if path == "/api/state/meta":
            return self._send(200, state_meta(self.server.root))
        if path == "/api/anki-stats":
            from . import anki_stats
            return self._send(200, {"stats": anki_stats.load(self.server.root)})
        cards = CARD_VIEW.fullmatch(path)
        if cards:
            return self._cards(*cards.groups())
        m = COURSE_GET.match(path)
        if m:
            from . import courses as C
            try:
                if m.group(1):
                    return self._send(200, C.course_status(m.group(1), self.server.root))
                return self._send(200, {"courses": C.list_courses(self.server.root), "import_enabled": True})
            except MasteryError as exc:
                return self._send(404, {"error": str(exc)[:300]})
        if not ALLOWED.fullmatch(path) or ".." in path:
            return self._send(404, {"error": "not found"})
        target = Path(path.lstrip("/"))
        extra = {}
        if target.suffix == ".apkg":
            extra["Content-Disposition"] = 'attachment; filename="Anki.apkg"'
        ctype = TYPES.get(target.suffix) or mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        with ExitStack() as stack:
            try:
                stream, length = stack.enter_context(_open_product(self.server.root, target))
            except OSError:
                return self._send(404, {"error": "not found"})
            self._headers(200, length, ctype, extra)
            if self.command != "HEAD":
                shutil.copyfileobj(stream, self.wfile)

    def _cards(self, slug, cid, resource):
        from . import card_feedback as F
        root = self.server.root
        try:
            if resource in ("", "browser.js"):
                name = "card_browser.js" if resource else "card_browser.html"
                return self._send(200, (TEMPLATES / name).read_bytes(), TYPES[Path(name).suffix])
            if resource == "data":
                _, index = F.preview(root, slug, cid)
                return self._send(200, {"package": index["package"], "cards": index["cards"],
                                        "report": F.report(root, slug, cid), "kinds": F.KINDS})
            media = re.fullmatch(r"([0-9a-f]{64})/([^/]+)", resource)
            if media:
                digest, name = media.groups()
                dest = F.chapter_dir(root, slug, cid) / "card-previews" / digest
                index = F._read_json(F.confined(root, dest / "index.json"))
                if index and name in index["files"]:
                    asset = F.confined(root, dest / name)
                    body = asset.read_bytes()
                    runtime = f"http://{self.headers['Host']}/cards/{slug}/{cid}/{digest}/tex-svg-full.js"
                    policy = (f"default-src 'none'; script-src {runtime}; style-src 'unsafe-inline'; "
                              "img-src 'self' data:; font-src 'self' data:; form-action 'none'; base-uri 'none'; "
                              "frame-ancestors 'self'; sandbox allow-same-origin allow-scripts")
                    return self._send(200, body, TYPES.get(asset.suffix) or
                                      mimetypes.guess_type(name)[0] or "application/octet-stream",
                                      {"Content-Security-Policy": policy})
        except (MasteryError, FileNotFoundError) as exc:
            return self._send(404, {"error": str(exc)[:200]})
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        if not self._host_ok():
            return self._send(403, {"error": "host"})
        origin = self.headers.get("Origin")
        if origin is not None and origin not in {"http://" + h for h in self._hosts()}:
            return self._send(403, {"error": "origin"})
        path = urlsplit(self.path).path
        course = COURSE_POST.match(path)
        if path not in ("/api/state", "/api/anki-stats", "/api/anki-stats/forget") and not course:
            return self._send(404, {"error": "not found"})
        if not self.headers.get("Content-Type", "").startswith("application/json"):
            return self._send(415, {"error": "json only"})
        if course:
            return self._course_post(path, course)
        if path.startswith("/api/anki-stats"):
            return self._anki_stats_post(path)
        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            length = -1
        if length < 0 or length > MAX_STATE_BYTES:
            return self._send(413, {"error": "size"})
        try:
            obj = json.loads(self.rfile.read(length).decode("utf-8"))
            received = store_state(self.server.root, obj)
        except (ValueError, MasteryError, UnicodeDecodeError) as exc:
            return self._send(400, {"error": str(exc)[:200]})
        return self._send(200, {"ok": True, "received_at": received})

    def _anki_stats_post(self, path):
        """Permission-gated Anki statistics: only an export file the learner chose, only after consent: true."""
        import base64
        import binascii
        from . import anki_stats
        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            length = -1
        if length < 0 or length > MAX_ANKI_STATS_BYTES:
            return self._send(413, {"error": "Datei zu groß (höchstens 30 MB)."})
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            if not isinstance(body, dict):
                raise MasteryError("JSON-Objekt erwartet")
            if path.endswith("/forget"):
                return self._send(200, {"ok": True, "removed": anki_stats.forget(self.server.root)})
            if body.get("consent") is not True:
                raise MasteryError("Anki-Statistik nur mit Ihrer ausdrücklichen Zustimmung (consent: true).")
            if set(body) - {"consent", "filename", "data_base64"} or not isinstance(body.get("data_base64"), str):
                raise MasteryError("Erwartet: {consent, filename, data_base64}")
            data = base64.b64decode(body["data_base64"], validate=True)
            with self.server.course_lock:
                stats = anki_stats.parse_export(data, str(body.get("filename") or "export.apkg"))
                anki_stats.store(self.server.root, stats)
            return self._send(200, {"stats": stats})
        except (ValueError, MasteryError, UnicodeDecodeError, binascii.Error) as exc:
            return self._send(400, {"error": str(exc)[:400]})
        except Exception as exc:  # report, never crash the server
            return self._send(500, {"error": f"{type(exc).__name__}: {str(exc)[:300]}"})

    def _course_post(self, path, m):
        from . import courses as C
        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            length = -1
        if length < 0 or length > MAX_API_BYTES:
            return self._send(413, {"error": "size"})
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            if not isinstance(body, dict):
                raise MasteryError("JSON-Objekt erwartet")
            root, log = self.server.root, (lambda *_: None)
            with self.server.course_lock:  # strictly one course operation at a time
                if path == "/api/import":
                    if set(body) - {"path", "slug", "title", "materialize"} or not isinstance(body.get("path"), str):
                        raise MasteryError("Erwartet: {path, slug?, title?, materialize?}")
                    if body.get("slug") is not None and not isinstance(body["slug"], str):
                        raise MasteryError("slug: Text")
                    result = C.import_course(body["path"], slug=body.get("slug") or None, title=body.get("title") or None,
                                             home=root, materialize_files=body.get("materialize") is True,
                                             base=self.server.import_base, log=log)
                    return self._send(200, result)
                slug, action, chapter, chapter_action = m.groups()
                if action == "reimport":
                    return self._send(200, C.reimport(slug, root, log=log))
                if action == "materialize":
                    if body.get("consent") is not True:
                        raise MasteryError("Herunterladen aus iCloud nur mit ausdrücklicher Zustimmung (consent: true).")
                    return self._send(200, C.reimport(slug, root, materialize_files=True, log=log))
                if action == "plan":
                    return self._send(200, C.set_overrides(slug, body.get("overrides") or {}, root))
                if action == "author":
                    return self._send(200, self._author(slug, body, root))
                if chapter_action == "feedback":
                    from .card_feedback import record
                    return self._send(200, record(root, slug, chapter, body))
                if chapter_action == "packet":
                    C.make_packet(slug, chapter, root, log=log)
                    return self._send(200, C.course_status(slug, root))
                if chapter_action == "build":
                    C.build_chapter(slug, chapter, root, log=log)
                    return self._send(200, C.course_status(slug, root))
        except (ValueError, MasteryError, UnicodeDecodeError) as exc:
            return self._send(400, {"error": str(exc)[:400]})
        except Exception as exc:  # report, never crash the server
            if getattr(self.server, "verbose", False):
                traceback.print_exc()
            return self._send(500, {"error": f"{type(exc).__name__}: {str(exc)[:300]}"})
        return self._send(404, {"error": "not found"})

    def _author(self, slug, body, root):
        """Kurs erarbeiten: plan | authorize (explicit consent) | start (background runner) | stop | status."""
        from . import authoring as A
        act = body.get("action")
        if act == "plan":
            return A.plan(slug, root)
        if act == "authorize":
            if body.get("consent") is not True:
                raise MasteryError("Freigabe nur mit ausdrücklicher Zustimmung (consent: true).")
            if body.get("revoke") is True:
                return A.authorize(slug, revoke=True, home=root)
            runs = body.get("max_runs")
            if not isinstance(runs, int) or isinstance(runs, bool):
                raise MasteryError("max_runs: ganze Zahl")
            if body.get("provider") not in ("claude_code_cli", "manual"):
                raise MasteryError("Anbieter in der App: claude_code_cli oder manual (andere über die Kommandozeile).")
            return A.authorize(slug, body["provider"], runs, root, allow_web=body.get("allow_web") is True,
                               granted_via="app")
        if act == "start":
            A.spawn_background(slug, root, wait_for_reset=True)
            return A.status(slug, root)
        if act == "stop":
            return A.stop(slug, root)
        if act == "status":
            return A.status(slug, root)
        raise MasteryError("action: plan | authorize | start | stop | status")

    def do_OPTIONS(self):  # no CORS: cross-origin preflights fail closed
        self._send(405, {"error": "method"})


def make_server(root, port, verbose=False, import_base=None):
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.root = Path(root)
    server.verbose = verbose
    server.import_base = Path(import_base) if import_base else Path.home()
    server.course_lock = threading.Lock()
    server.daemon_threads = True
    return server


def start_in_thread(root, port=0, import_base=None):
    """Test helper: serve on a free port in a daemon thread; returns (server, base_url)."""
    server = make_server(root, port, import_base=import_base)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}/"
