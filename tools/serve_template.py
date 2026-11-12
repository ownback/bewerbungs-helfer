#!/usr/bin/env python3
"""Serve the Mappe HTML files for visual review with the Tencil overlay.

The documents never contain the Tencil script tag (they are exported to PDF); this
server injects it on the fly, together with:

* ``data-tencil-src="<repo-relative path>:<line>:<col>"`` and ``data-tencil-component``
  on every element in <body>, so each Tencil pin names the exact source line.
  Attributes are inserted inside existing start tags, so line numbers never shift.
* a tiny live-reload poller that reloads the page when the file changes.

Modes
-----
local  (default) 127.0.0.1 only, no auth. The overlay talks to the daemon directly
       (http://localhost:4747). ``/`` is an overview with three kinds of documents:
       the master template (.agents/skills/bewerbungshelfer/assets/bewerbungsmappe.html),
       the profile templates (profile/<name>/assets/profile/<name>_template.html) and the
       built applications (profile/<name>/applications/**/application/bewerbungsmappe - *.html).
       They live at ``/f/<repo-relative path>``; besides these HTML files only images below
       profile/<name>/ are served (the Mappe references them). Personal data: loopback only.
remote Basic Auth (password file, mode 0600) in front of everything. Serves only the
       master template (data-free), at ``/``. The overlay is loaded same-origin
       (/tencil.js) and its WebSocket (/ws) is proxied to the daemon after auth, Origin
       and Host checks. This is the only port a tunnel may point at. The daemon itself
       must never be exposed, and profile files are never served in this mode.

Standard library only, no data, no secrets. See
.agents/skills/bewerbungshelfer/references/tencil.md.
"""

from __future__ import annotations

import argparse
import base64
import hmac
import html
import json
import os
import re
import secrets
import socket
import stat
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_REL = ".agents/skills/bewerbungshelfer/assets/bewerbungsmappe.html"
TEMPLATE = REPO_ROOT / TEMPLATE_REL

# Same skip list as Tencil's own source tagging, plus <body> itself.
SKIP_TAGS = {
    "html", "head", "body", "meta", "link", "script", "style", "title",
    "base", "noscript", "template", "slot",
}

SESSION_COOKIE = "mappe_review"
SESSION_TTL = 12 * 3600
MAX_FAILURES = 10
FAILURE_WINDOW = 600

IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}

RELOAD_SNIPPET = """<script data-review-only>(()=>{let v=null;const tick=async()=>{try{const r=await fetch("/__review/version?p="+encodeURIComponent(location.pathname),{cache:"no-store"});if(r.ok){const n=(await r.json()).version;if(v===null)v=n;else if(n!==v){location.reload();return}}}catch(e){}setTimeout(tick,1200)};tick()})();</script>"""


# --------------------------------------------------------------------------- render


class _TagCollector(HTMLParser):
    """Records where each start tag in <body> sits in the source."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.inserts: list[tuple[int, int, int, str, dict[str, str | None]]] = []
        self.in_body = False
        self.svg_depth = 0

    def _record(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if not self.in_body or tag in SKIP_TAGS or self.svg_depth > 0:
            return
        line, col = self.getpos()  # 1-based line, 0-based column
        raw = self.get_starttag_text() or ""
        name_len = len(re.match(r"<\s*([^\s/>]+)", raw).group(1)) if raw else len(tag)
        self.inserts.append((line, col, name_len, tag, dict(attrs)))

    def handle_starttag(self, tag, attrs):
        if tag == "body":
            self.in_body = True
            return
        self._record(tag, attrs)
        if tag == "svg":
            self.svg_depth += 1

    def handle_startendtag(self, tag, attrs):
        self._record(tag, attrs)

    def handle_endtag(self, tag):
        if tag == "svg" and self.svg_depth > 0:
            self.svg_depth -= 1
        elif tag == "body":
            self.in_body = False


def _label(tag: str, attrs: dict[str, str | None]) -> str:
    if attrs.get("id"):
        return f"{tag}#{attrs['id']}"
    classes = (attrs.get("class") or "").split()
    return f"{tag}.{classes[0]}" if classes else tag


def render_template(source: str, tencil_src: str, rel: str = TEMPLATE_REL, back_link: bool = False) -> str:
    parser = _TagCollector()
    parser.feed(source)
    parser.close()

    line_starts = [0]
    for match in re.finditer("\n", source):
        line_starts.append(match.end())

    pieces: list[str] = []
    last = 0
    for line, col, name_len, tag, attrs in parser.inserts:
        at = line_starts[line - 1] + col + 1 + name_len
        extra = (
            f' data-tencil-src="{html.escape(f"{rel}:{line}:{col + 1}")}"'
            f' data-tencil-component="{html.escape(_label(tag, attrs))}"'
        )
        pieces.append(source[last:at])
        pieces.append(extra)
        last = at
    pieces.append(source[last:])
    out = "".join(pieces)

    # Same line as </body>, so line numbers stay identical to the source file.
    snippet = f'<script src="{html.escape(tencil_src)}" async></script>{RELOAD_SNIPPET}'
    if back_link:
        snippet += BACK_LINK
    idx = out.lower().rfind("</body>")
    if idx == -1:
        return out + snippet
    return out[:idx] + snippet + out[idx:]


BACK_LINK = (
    '<a data-review-only href="/" style="position:fixed;left:10px;bottom:10px;z-index:2147483000;'
    'font:12px/1 system-ui,sans-serif;padding:7px 10px;border-radius:999px;background:#1d1d1f;color:#fff;'
    'text-decoration:none;opacity:.8">&larr; Übersicht</a>'
)


def file_version(path: Path) -> str:
    st = path.stat()
    return f"{st.st_mtime_ns}-{st.st_size}"


# --------------------------------------------------------------------------- documents (local mode)


def _doc(kind: str, path: Path, label: str, detail: str) -> dict[str, str]:
    rel = path.relative_to(REPO_ROOT).as_posix()
    return {"kind": kind, "rel": rel, "label": label, "detail": detail,
            "url": "/f/" + urllib.parse.quote(rel)}


def _manifest_info(application_html: Path) -> str:
    try:
        manifest = json.loads((application_html.parent / "application-manifest.json").read_text(encoding="utf-8"))
        return f"{manifest.get('company', '')} · Status {manifest.get('status', '?')}"
    except (OSError, ValueError):
        return ""


def discover() -> list[dict[str, str]]:
    """The master template, every profile template and every built application. Never hidden/temp files."""
    docs = [_doc("master", TEMPLATE, "Master-Vorlage", "Skill-Vorlage, datenfrei: Design für alle")]
    profiles = REPO_ROOT / "profile"
    for tpl in sorted(profiles.glob("*/assets/profile/*_template.html")):
        if not tpl.name.startswith("."):
            docs.append(_doc("profile", tpl, f"Profilvorlage {tpl.parent.parent.parent.name}",
                             "Deckblatt, Lebenslauf, Nachweise aus dem Profil"))
    for app in sorted(profiles.glob("*/applications/**/application/bewerbungsmappe - *.html")):
        if not app.name.startswith("."):
            docs.append(_doc("application", app, "Bewerbung " + app.parent.parent.name,
                             _manifest_info(app) or "gebaute Mappe"))
    return docs


def resolve_doc(url_path: str) -> Path | None:
    """/f/<rel> -> file, only for discovered documents (HTML) or images below profile/<name>/."""
    if not url_path.startswith("/f/"):
        return None
    rel = urllib.parse.unquote(url_path[3:])
    if not rel or "\x00" in rel:
        return None
    path = (REPO_ROOT / rel).resolve()
    if path in {(REPO_ROOT / d["rel"]).resolve() for d in discover()}:
        return path
    profiles = (REPO_ROOT / "profile").resolve()
    if path.suffix.lower() in IMAGE_TYPES and path.is_file() and profiles in path.parents \
            and len(path.relative_to(profiles).parts) > 1:
        return path
    return None


KIND_NOTES = {
    "master": "Pins ändern direkt diese Datei. Danach Profilvorlagen und Mappen neu bauen.",
    "profile": "Gebaute Datei. Pins werden in die Master-Vorlage, das Profil-JSON oder das Build-Skript übersetzt, dann neu gebaut.",
    "application": "Gebaute Datei. Pins werden in Master-Vorlage, Profil, Texte (.md) oder Build-Skript übersetzt, dann neu gebaut.",
}


def landing_page() -> str:
    groups = {"master": [], "profile": [], "application": []}
    for d in discover():
        groups[d["kind"]].append(d)
    titles = {"master": "Master-Vorlage", "profile": "Meine Profilvorlage", "application": "Meine Bewerbungen"}
    parts = []
    for kind in ("master", "profile", "application"):
        items = "".join(
            f'<li><a href="{html.escape(d["url"])}"><strong>{html.escape(d["label"])}</strong>'
            f'<span>{html.escape(d["detail"])}</span><code>{html.escape(d["rel"])}</code></a></li>'
            for d in groups[kind]) or "<li class=none>keine gefunden</li>"
        parts.append(f"<section><h2>{titles[kind]}</h2><p>{html.escape(KIND_NOTES[kind])}</p><ul>{items}</ul></section>")
    return (
        "<!doctype html><html lang=de><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
        "<title>Mappe prüfen</title><style>"
        "body{font:15px/1.5 system-ui,sans-serif;max-width:46rem;margin:3rem auto;padding:0 1.2rem;color:#1d1d1f}"
        "h1{font-size:1.5rem}h2{font-size:1.05rem;margin:2rem 0 .2rem}p{margin:.2rem 0 .8rem;color:#555}"
        "ul{list-style:none;padding:0;margin:0}li a{display:block;padding:.8rem 1rem;margin:.4rem 0;border:1px solid #d2d2d7;"
        "border-radius:12px;text-decoration:none;color:inherit}li a:hover{border-color:#0b4f5c;background:#f5f5f7}"
        "li span{display:block;color:#555}li code{display:block;font-size:12px;color:#6e6e73;word-break:break-all}"
        ".none{color:#6e6e73}.hint{background:#f5f5f7;border-radius:12px;padding:.8rem 1rem;margin-top:2rem}"
        "</style><h1>Mappe prüfen</h1>"
        "<p>Seite öffnen, <kbd>C</kbd> drücken, Element anklicken, Änderung beschreiben, <kbd>Enter</kbd>. "
        "Jeder Pin startet einen Agenten, der die Änderung an der richtigen Quelle macht und neu baut.</p>"
        + "".join(parts) +
        "<p class=hint>Diese Übersicht und die Profil- und Bewerbungsseiten sind nur lokal erreichbar "
        "(127.0.0.1). Über die Fernadresse läuft ausschließlich die Master-Vorlage.</p></html>"
    )


# --------------------------------------------------------------------------- auth


def load_credentials(path: Path) -> tuple[str, str]:
    st = path.stat()
    if st.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        sys.exit(f"{path} must not be readable by group/others (chmod 600)")
    line = path.read_text(encoding="utf-8").strip().splitlines()[0]
    user, sep, password = line.partition(":")
    if not sep or not user or len(password) < 16:
        sys.exit(f"{path}: expected one line 'user:password' with a password of 16+ characters")
    return user, password


def init_auth(path: Path, user: str) -> None:
    if path.exists():
        print(f"{path} exists, leaving it unchanged")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(f"{user}:{secrets.token_urlsafe(24)}\n")
    print(f"wrote {path} (0600)")


class Guard:
    """Basic Auth plus a short-lived session cookie (WebKit omits Basic credentials on WebSockets)."""

    def __init__(self, user: str, password: str) -> None:
        self.user = user.encode()
        self.password = password.encode()
        self.sessions: dict[str, float] = {}
        self.failures: dict[str, list[float]] = {}
        self.lock = threading.Lock()

    def locked_out(self, client: str) -> bool:
        now = time.time()
        with self.lock:
            recent = [t for t in self.failures.get(client, []) if now - t < FAILURE_WINDOW]
            self.failures[client] = recent
            return len(recent) >= MAX_FAILURES

    def fail(self, client: str) -> None:
        with self.lock:
            self.failures.setdefault(client, []).append(time.time())

    def check_basic(self, header: str | None) -> bool:
        if not header or not header.lower().startswith("basic "):
            return False
        try:
            decoded = base64.b64decode(header[6:].strip(), validate=True)
        except ValueError:
            return False
        user, sep, password = decoded.partition(b":")
        ok_user = hmac.compare_digest(user, self.user)
        ok_pass = hmac.compare_digest(password, self.password)
        return bool(sep) and ok_user and ok_pass

    def new_session(self) -> str:
        token = secrets.token_urlsafe(32)
        with self.lock:
            now = time.time()
            self.sessions = {k: v for k, v in self.sessions.items() if v > now}
            self.sessions[token] = now + SESSION_TTL
        return token

    def check_session(self, cookie_header: str | None) -> bool:
        if not cookie_header:
            return False
        for part in cookie_header.split(";"):
            name, _, value = part.strip().partition("=")
            if name == SESSION_COOKIE:
                with self.lock:
                    expiry = self.sessions.get(value)
                if expiry and expiry > time.time():
                    return True
        return False


# --------------------------------------------------------------------------- server


class Config:
    mode = "local"
    daemon = urllib.parse.urlsplit("http://127.0.0.1:4747")
    allowed_origins: set[str] = set()
    allowed_hosts: set[str] = set()
    guard: Guard | None = None
    verbose = False


def daemon_netloc() -> tuple[str, int]:
    return Config.daemon.hostname or "127.0.0.1", Config.daemon.port or 80


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "mappe-review"
    sys_version = ""

    # ---- helpers

    def log_message(self, fmt, *args):
        if Config.verbose:
            sys.stderr.write(f"{self.client_label()} {fmt % args}\n")

    def client_label(self) -> str:
        return self.headers.get("CF-Connecting-IP") or self.client_address[0]

    def send_plain(self, code: int, text: str, extra: dict[str, str] | None = None) -> None:
        body = (text + "\n").encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def common_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        if Config.mode == "remote":
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("X-Robots-Tag", "noindex, nofollow")

    def host_ok(self) -> bool:
        host = (self.headers.get("Host") or "").lower()
        return host in Config.allowed_hosts

    def authorize(self) -> str | None:
        """Returns None if the request may proceed, else a reason (already answered)."""
        if not self.host_ok():
            self.send_plain(403, "Forbidden host")
            return "host"
        guard = Config.guard
        if guard is None:
            return None
        client = self.client_label()
        if guard.check_session(self.headers.get("Cookie")):
            return None
        if guard.locked_out(client):
            self.send_plain(429, "Too many failed logins, try again later")
            return "locked"
        if guard.check_basic(self.headers.get("Authorization")):
            self._new_cookie = guard.new_session()
            return None
        if self.headers.get("Authorization"):
            guard.fail(client)
            time.sleep(0.5)
        self.send_plain(401, "Authentication required",
                        {"WWW-Authenticate": 'Basic realm="Bewerbungsmappe Review", charset="UTF-8"'})
        return "auth"

    def cookie_header(self) -> None:
        token = getattr(self, "_new_cookie", None)
        if not token:
            return
        secure = "; Secure" if self.headers.get("X-Forwarded-Proto", "").lower() == "https" else ""
        self.send_header(
            "Set-Cookie",
            f"{SESSION_COOKIE}={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={SESSION_TTL}{secure}",
        )

    # ---- routes

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        self._new_cookie = None
        if self.authorize():
            return
        split = urllib.parse.urlsplit(self.path)
        path = split.path
        if Config.mode == "remote" and path in ("/", "/bewerbungsmappe.html"):
            return self.serve_html(TEMPLATE, TEMPLATE_REL)
        if Config.mode == "local":
            if path == "/":
                return self.send_body(200, landing_page().encode("utf-8"), "text/html; charset=utf-8")
            if path.startswith("/f/"):
                return self.serve_file(path)
        if path == "/__review/version":
            target = TEMPLATE
            if Config.mode == "local":
                asked = urllib.parse.parse_qs(split.query).get("p", [""])[0]
                target = resolve_doc(asked) or TEMPLATE
            try:
                version = file_version(target)
            except OSError:
                version = "missing"
            body = json.dumps({"version": version}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.common_headers()
            self.cookie_header()
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)
            return
        if Config.mode == "remote" and path == "/tencil.js":
            return self.proxy_script()
        if Config.mode == "remote" and path == "/ws":
            return self.proxy_websocket()
        self.send_plain(404, "Not found")

    def send_body(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.common_headers()
        self.cookie_header()
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def serve_file(self, url_path: str) -> None:
        path = resolve_doc(url_path)
        if path is None:
            return self.send_plain(404, "Not found")
        if path.suffix.lower() in IMAGE_TYPES:
            try:
                return self.send_body(200, path.read_bytes(), IMAGE_TYPES[path.suffix.lower()])
            except OSError:
                return self.send_plain(404, "Not found")
        return self.serve_html(path, path.relative_to(REPO_ROOT).as_posix())

    def serve_html(self, path: Path, rel: str):
        try:
            source = path.read_text(encoding="utf-8")
        except OSError as exc:
            return self.send_plain(500, f"File unreadable: {exc}")
        root = urllib.parse.quote(str(REPO_ROOT), safe="")
        if Config.mode == "remote":
            src = f"/tencil.js?root={root}"
        else:
            src = f"http://localhost:{daemon_netloc()[1]}/tencil.js?root={root}"
        body = render_template(source, src, rel, back_link=Config.mode == "local").encode("utf-8")
        self.send_body(200, body, "text/html; charset=utf-8")

    def proxy_script(self):
        host, port = daemon_netloc()
        try:
            with urllib.request.urlopen(f"http://{host}:{port}/tencil.js", timeout=5) as resp:
                body = resp.read()
        except (urllib.error.URLError, OSError):
            return self.send_plain(502, "Tencil daemon not reachable (systemctl --user status tencil)")
        self.send_response(200)
        self.send_header("Content-Type", "text/javascript; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.common_headers()
        self.cookie_header()
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def proxy_websocket(self):
        if (self.headers.get("Upgrade") or "").lower() != "websocket":
            return self.send_plain(400, "WebSocket upgrade expected")
        origin = self.headers.get("Origin")
        if origin not in Config.allowed_origins:
            # Cross-site WebSocket hijacking guard: only our own page may connect.
            return self.send_plain(403, "Forbidden origin")
        host, port = daemon_netloc()
        try:
            upstream = socket.create_connection((host, port), timeout=5)
        except OSError:
            return self.send_plain(502, "Tencil daemon not reachable")
        upstream.settimeout(None)

        drop = {"host", "origin", "authorization", "cookie", "x-forwarded-for",
                "x-forwarded-proto", "x-forwarded-host", "x-real-ip"}
        lines = ["GET /ws HTTP/1.1", f"Host: {host}:{port}", f"Origin: http://localhost:{port}"]
        for key, value in self.headers.items():
            lk = key.lower()
            if lk in drop or lk.startswith("cf-"):
                continue
            lines.append(f"{key}: {value}")
        upstream.sendall(("\r\n".join(lines) + "\r\n\r\n").encode("latin-1"))
        self.close_connection = True

        client = self.connection
        client.settimeout(None)

        def client_to_upstream() -> None:
            # Read via rfile: it may already buffer bytes sent right after the handshake.
            try:
                while data := self.rfile.read1(65536):
                    upstream.sendall(data)
            except (OSError, ValueError):
                pass
            finally:
                _shutdown(upstream)

        pump = threading.Thread(target=client_to_upstream, daemon=True)
        pump.start()
        try:
            while data := upstream.recv(65536):
                client.sendall(data)
        except OSError:
            pass
        finally:
            _shutdown(client)
            pump.join(timeout=5)
            upstream.close()


def _shutdown(sock: socket.socket) -> None:
    try:
        sock.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=("local", "remote"), default="local")
    ap.add_argument("--host", default="127.0.0.1", help="bind address (keep loopback)")
    ap.add_argument("--port", type=int, default=8791)
    ap.add_argument("--daemon", default=os.environ.get("TENCIL_DAEMON", "http://127.0.0.1:4747"))
    ap.add_argument("--auth-file", type=Path, help="remote mode: file with one line user:password (0600)")
    ap.add_argument("--allow-origin", action="append", default=[],
                    help="remote mode: public origin of the page, e.g. https://review.example.org (repeatable)")
    ap.add_argument("--init-auth", action="store_true", help="create --auth-file with a random password and exit")
    ap.add_argument("--user", default="mappe", help="user name for --init-auth")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    if args.init_auth:
        if not args.auth_file:
            sys.exit("--init-auth needs --auth-file")
        init_auth(args.auth_file, args.user)
        return

    if not TEMPLATE.is_file():
        sys.exit(f"template missing: {TEMPLATE}")
    if args.host not in ("127.0.0.1", "::1", "localhost"):
        sys.exit("refusing to bind a non-loopback address; use a tunnel to the remote port instead")

    Config.mode = args.mode
    Config.verbose = args.verbose
    Config.daemon = urllib.parse.urlsplit(args.daemon)
    local_hosts = {f"127.0.0.1:{args.port}", f"localhost:{args.port}", f"[::1]:{args.port}"}
    if args.mode == "remote":
        if not args.auth_file:
            sys.exit("remote mode needs --auth-file")
        if not args.allow_origin:
            sys.exit("remote mode needs at least one --allow-origin")
        Config.guard = Guard(*load_credentials(args.auth_file))
        origins = {o.rstrip("/") for o in args.allow_origin}
        Config.allowed_origins = origins | {f"http://{h}" for h in local_hosts}
        Config.allowed_hosts = local_hosts | {urllib.parse.urlsplit(o).netloc.lower() for o in origins}
    else:
        Config.allowed_hosts = local_hosts

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.daemon_threads = True
    what = TEMPLATE_REL if args.mode == "remote" else "overview + master template, profile templates, applications"
    print(f"Serving {what} ({args.mode}) on http://{args.host}:{args.port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
