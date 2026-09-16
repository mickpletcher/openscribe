from __future__ import annotations

import hmac
import json
import secrets
import ssl
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from importlib.resources import files
from pathlib import Path

from openscribe.project import load_project_config
from openscribe.word import MAX_DOCX_BYTES, apply_word_import, preview_word_import


class WordBridge(HTTPServer):
    def __init__(self, root: Path, port: int = 0, *, certificate: Path | None = None, key: Path | None = None):
        self.root = root.resolve()
        self.config = load_project_config(self.root)
        self.token = secrets.token_urlsafe(32)
        self.plans = {}
        if bool(certificate) != bool(key):
            raise ValueError("Provide both certificate and key for an HTTPS Word bridge.")
        super().__init__(("127.0.0.1", port), BridgeHandler)
        self.origin = f"{'https' if certificate else 'http'}://127.0.0.1:{self.server_port}"
        if certificate:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            context.load_cert_chain(certificate, key)
            self.socket = context.wrap_socket(self.socket, server_side=True)


class BridgeHandler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(15)

    def log_message(self, format, *args):
        pass

    def _reply(self, status, payload, content_type="application/json", *, discard_request_body=False):
        body = json.dumps(payload).encode("utf-8") if content_type == "application/json" else payload
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Access-Control-Allow-Origin", self.server.origin)
        if discard_request_body:
            self.send_header("Connection", "close")
            self.close_connection = True
        self.end_headers()
        self.wfile.write(body)
        self.wfile.flush()
        if discard_request_body:
            self._discard_request_body()

    def _discard_request_body(self):
        if self.headers.get("Transfer-Encoding"):
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return
        if size <= 0 or size > MAX_DOCX_BYTES:
            return
        remaining = size
        try:
            while remaining:
                chunk = self.rfile.read(min(remaining, 64 * 1024))
                if not chunk:
                    break
                remaining -= len(chunk)
        except OSError:
            pass

    def _authorized(self):
        if self.client_address[0] != "127.0.0.1" or self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}":
            self._reply(403, {"error": "Invalid local host."}, discard_request_body=True)
            return False
        if self.headers.get("Origin") != self.server.origin:
            self._reply(403, {"error": "Unapproved origin."}, discard_request_body=True)
            return False
        provided = self.headers.get("Authorization", "")
        if not hmac.compare_digest(provided, "Bearer " + self.server.token):
            self._reply(401, {"error": "A valid session token is required."}, discard_request_body=True)
            return False
        return True

    def do_OPTIONS(self):
        if self.headers.get("Origin") != self.server.origin:
            self._reply(403, {"error": "Unapproved origin."})
            return
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", self.server.origin)
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        if self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}":
            self._reply(403, {"error": "Invalid local host."})
            return
        assets = {"/taskpane.html": "text/html; charset=utf-8", "/taskpane.js": "text/javascript; charset=utf-8"}
        if self.path in assets:
            resource = files("openscribe").joinpath("word_addin", self.path.removeprefix("/"))
            self._reply(200, resource.read_bytes(), assets[self.path])
        else:
            self._reply(404, {"error": "Unknown route."})

    def do_POST(self):
        if not self._authorized():
            return
        if self.path not in {"/preview", "/apply"}:
            self._reply(404, {"error": "Unknown route."}, discard_request_body=True)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size <= 0 or size > MAX_DOCX_BYTES or self.headers.get("Transfer-Encoding"):
                self._reply(413, {"error": "Invalid request size."})
                return
            body = self.rfile.read(size)
            if len(body) != size:
                self._reply(400, {"error": "Incomplete request."})
                return
            if self.path == "/preview":
                plan = preview_word_import(self.server.root, body)
                preview_id = secrets.token_urlsafe(24)
                self.server.plans = {preview_id: (time.monotonic(), plan)}
                self._reply(200, {"preview_id": preview_id, "document_hash": plan.document_hash,
                                  "export_id": plan.export_id, "blocked": plan.blocked,
                                  "tracked_changes": plan.tracked_changes,
                                  "units": [{"id": r.identity, "status": r.status} for r in plan.reviews],
                                  "warnings": plan.warnings, "diff": plan.diff})
            else:
                request = json.loads(body)
                if not isinstance(request, dict) or set(request) != {"preview_id", "document_hash"}:
                    raise ValueError("Apply requires only a preview ID and current document hash.")
                preview_id = request["preview_id"]
                if not isinstance(preview_id, str) or preview_id not in self.server.plans:
                    raise ValueError("Preview is missing or expired. Preview again.")
                created, plan = self.server.plans[preview_id]
                if time.monotonic() - created > 300 or request["document_hash"] != plan.document_hash:
                    raise ValueError("Preview expired or the Word document changed. Preview again.")
                backup = apply_word_import(self.server.root, plan)
                self.server.plans.clear()
                self._reply(200, {"applied": len(plan.edits), "backup": backup.name if backup else None})
        except (OSError, RuntimeError, ValueError) as exc:
            self._reply(400, {"error": str(exc)})


def write_addin_manifest(bridge: WordBridge, output: Path):
    from openscribe.schema import atomic_write_text

    if not bridge.origin.startswith("https:"):
        raise ValueError("The Word task pane requires HTTPS and a locally trusted certificate.")
    if output.exists():
        raise FileExistsError("Choose a new manifest output path.")
    atomic_write_text(output, f'''<?xml version="1.0" encoding="UTF-8"?>
<OfficeApp xmlns="http://schemas.microsoft.com/office/appforoffice/1.1"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="TaskPaneApp">
 <Id>e964a66d-d75e-40ae-993f-b7d941212998</Id><Version>0.1.2.0</Version>
 <ProviderName>OpenScribe</ProviderName><DefaultLocale>en-US</DefaultLocale>
 <DisplayName DefaultValue="OpenScribe local round trip" />
 <Description DefaultValue="Preview and apply Word edits to a local OpenScribe project." />
 <Hosts><Host Name="Document" /></Hosts>
 <Requirements><Sets DefaultMinVersion="1.1"><Set Name="File" /><Set Name="CompressedFile" /></Sets></Requirements>
 <DefaultSettings><SourceLocation DefaultValue="{bridge.origin}/taskpane.html" /></DefaultSettings>
 <Permissions>ReadAllDocument</Permissions>
</OfficeApp>
''')
