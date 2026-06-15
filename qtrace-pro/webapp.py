"""
webapp.py — Q-Trace Pro web UI (lightweight, dependency-free)
=============================================================
A small professional single-page UI served by Python's **stdlib** http.server —
no Streamlit, no Flask/FastAPI, no build step, no extra dependencies. It exposes
the same analyzer the CLI uses over a tiny JSON API and serves a static
HTML/CSS/JS front end from ``web/``.

Run:
    python webapp.py            # http://127.0.0.1:8000
    python webapp.py --port 9000 --host 0.0.0.0

Endpoints:
    GET  /            -> the single-page app (web/index.html)
    GET  /health      -> engine status JSON
    POST /api/scan    -> {"code": "..."} -> analysis result JSON (findings, SARIF, ...)
"""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from analyzer import analyze
from report import json_report_string, sarif_string
from self_healing import ValidationError, health

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
MAX_BODY = 2_000_000  # refuse absurd request bodies


def build_scan_response(code: str) -> dict:
    """Run an audit and shape it for the UI. Never raises for ordinary input."""
    try:
        res = analyze(code, use_symbolic=True, use_cache=True)
    except ValidationError as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:  # last-resort guard
        return {"ok": False, "error": f"internal error: {e}"}

    findings = []
    counts: dict = {}
    for f in res.findings:
        d = f.to_dict()
        d["cwe_uri"] = f.meta.cwe_uri()
        findings.append(d)
        counts[f.severity] = counts.get(f.severity, 0) + 1

    return {
        "ok": True,
        "summary": {
            "total": len(res.findings),
            "by_severity": counts,
            "max_cvss": max((f.cvss for f in res.findings), default=0.0),
            "ast_entropy": round(res.ast_entropy, 2),
            "duration_ms": round(res.duration_s * 1000, 1),
        },
        "symbolic": res.symbolic[0] if res.symbolic else "N/A",
        "symbolic_unsafe": bool(res.symbolic[1]) if res.symbolic else False,
        "findings": findings,
        "health": res.health,
        "sarif": sarif_string(res.findings),
        "json": json_report_string(res.findings),
    }


def _engine_status() -> dict:
    snap = health.snapshot()
    return {"status": "ok",
            "engines": ", ".join(f"{e.name}" for e in snap) if snap else "ready",
            "overall": health.overall().value}


class Handler(BaseHTTPRequestHandler):
    server_version = "QTrace/2.1"

    def _send(self, status: int, body, ctype="application/json"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            try:
                with open(os.path.join(WEB_DIR, "index.html"), "rb") as fh:
                    self._send(200, fh.read(), "text/html; charset=utf-8")
            except FileNotFoundError:
                self._send(500, json.dumps({"error": "UI asset missing"}))
        elif path == "/health":
            self._send(200, json.dumps(_engine_status()))
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/api/scan":
            self._send(404, json.dumps({"error": "not found"}))
            return
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length > MAX_BODY:
            self._send(413, json.dumps({"ok": False, "error": "request too large"}))
            return
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw or b"{}")
            code = payload.get("code", "")
        except Exception:
            self._send(400, json.dumps({"ok": False, "error": "invalid JSON body"}))
            return
        self._send(200, json.dumps(build_scan_response(code)))

    def log_message(self, *args):  # keep the console quiet
        pass


def serve(host: str = "127.0.0.1", port: int = 8000):
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"⚛ Q-Trace Pro web UI running at http://{host}:{port}  (Ctrl+C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down…")
        httpd.server_close()


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Q-Trace Pro web UI")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    serve(args.host, args.port)
