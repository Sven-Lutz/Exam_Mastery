"""Offline static server for the Mastery library: stdlib only, 127.0.0.1 only, explicit file allow-list.

The fixed default port matters: localStorage belongs to the origin http://127.0.0.1:<port>, so a different port
shows a different (empty) learner state. POST /api/state accepts a size-limited, schema-checked snapshot of that
browser state as a backup into MASTERY_HOME/state; requests from other hosts or origins are refused (DNS rebinding,
cross-site POST).
"""
from __future__ import annotations

import json
import mimetypes
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from . import MAX_STATE_BYTES, MasteryError, state_meta, store_state

ALLOWED = re.compile(
    r"^/(index\.html|library\.json|assets/[A-Za-z0-9_.-]+\.(?:css|js)"
    r"|units/[a-z0-9][a-z0-9-]*/(?:Lehrbuch\.pdf|Arbeitsbuch\.pdf|Anki\.apkg|anki_report\.json|Interaktiv/index\.html"
    r"|tracks/[A-Za-z0-9_.-]+\.(?:html|json)))$")
TYPES = {".html": "text/html; charset=utf-8", ".json": "application/json; charset=utf-8",
         ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".pdf": "application/pdf",
         ".apkg": "application/octet-stream"}


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
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

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
        if not ALLOWED.match(path) or ".." in path:
            return self._send(404, {"error": "not found"})
        target = self.server.root / path.lstrip("/")
        if target.is_symlink() or not target.is_file():
            return self._send(404, {"error": "not found"})
        extra = {}
        if target.suffix == ".apkg":
            extra["Content-Disposition"] = 'attachment; filename="Anki.apkg"'
        ctype = TYPES.get(target.suffix) or mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        return self._send(200, target.read_bytes(), ctype, extra)

    def do_POST(self):
        if not self._host_ok():
            return self._send(403, {"error": "host"})
        origin = self.headers.get("Origin")
        if origin is not None and origin not in {"http://" + h for h in self._hosts()}:
            return self._send(403, {"error": "origin"})
        if urlsplit(self.path).path != "/api/state":
            return self._send(404, {"error": "not found"})
        if not self.headers.get("Content-Type", "").startswith("application/json"):
            return self._send(415, {"error": "json only"})
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

    def do_OPTIONS(self):  # no CORS: cross-origin preflights fail closed
        self._send(405, {"error": "method"})


def make_server(root, port, verbose=False):
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.root = Path(root)
    server.verbose = verbose
    server.daemon_threads = True
    return server


def start_in_thread(root, port=0):
    """Test helper: serve on a free port in a daemon thread; returns (server, base_url)."""
    server = make_server(root, port)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}/"
