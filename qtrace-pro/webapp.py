"""
webapp.py — Q-Trace Pro web UI (lightweight, dependency-free)
=============================================================
A professional single-page security dashboard served by Python's **stdlib**
http.server — no Streamlit, Flask/FastAPI, or build step. It exposes the full
depth of the analyzer (findings, cross-file taint, symbolic proof, self-healing
engine health, entropy/physics metrics, tamper-evident provenance) over a small
JSON API and serves a static HTML/CSS/JS front end from ``web/``.

Run:
    python webapp.py                 # http://127.0.0.1:8000
    python webapp.py --port 9000 --host 0.0.0.0

Endpoints:
    GET  /              -> the dashboard (web/index.html)
    GET  /health        -> engine status JSON
    POST /api/scan      -> {"code": "..."}                       single snippet
    POST /api/scan-files-> {"files": {"path": "code", ...}}      multi-file + cross-file taint
    POST /api/scan-zip   -> raw .zip bytes                        whole project (server unzips)
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from analyzer import analyze
from report import json_report_string, sarif_string
from self_healing import ValidationError, health
from taint import analyze_package

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
MAX_BODY = 8_000_000          # 8 MB request cap
MAX_FILES = 300               # refuse pathological project sizes
MAX_TOTAL_SRC = 6_000_000     # 6 MB of combined source
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", ".mypy_cache",
             ".pytest_cache", "build", "dist", ".tox", ".eggs"}


def _agg_physics(metrics_list):
    if not metrics_list:
        return {}
    keys = metrics_list[0].keys()
    return {k: round(sum(m[k] for m in metrics_list) / len(metrics_list), 3) for k in keys}


def _finding_dict(f):
    from findings import attack_narrative
    d = f.to_dict()
    d["cwe_uri"] = f.meta.cwe_uri()
    d["artifact_uri"] = getattr(f, "artifact_uri", "") or "snippet"
    # Deterministic Entry → Mechanism → Impact story (the no-LLM "explanation").
    d["narrative"] = attack_narrative(f.pattern, f.meta, f.evidence)
    return d


def _payload(findings, *, files_scanned, entropy=0.0, physics=None, symbolic=None,
             symbolic_unsafe=False, sinks=None, duration_ms=0.0):
    counts: dict = {}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1
    json_report = json_report_string(findings)
    return {
        "ok": True,
        "summary": {
            "total": len(findings),
            "by_severity": counts,
            "max_cvss": max((f.cvss for f in findings), default=0.0),
            "ast_entropy": round(entropy, 2),
            "files_scanned": files_scanned,
            "duration_ms": round(duration_ms, 1),
        },
        "symbolic": symbolic if symbolic else "N/A",
        "symbolic_unsafe": bool(symbolic_unsafe),
        "physics": physics or {},
        "sinks": sinks or [],
        "findings": [_finding_dict(f) for f in findings],
        "health": [{"name": e.name, "state": e.state.value, "detail": e.detail,
                    "emoji": e.emoji(), "failures": e.failures} for e in health.snapshot()],
        "provenance": {"report_sha256": hashlib.sha256(json_report.encode()).hexdigest()},
        "sarif": sarif_string(findings),
        "json": json_report,
    }


def build_scan_response(code: str) -> dict:
    """Single snippet."""
    try:
        res = analyze(code, use_symbolic=True, use_cache=True)
    except ValidationError as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:
        return {"ok": False, "error": f"internal error: {e}"}
    return _payload(
        res.findings, files_scanned=1, entropy=res.ast_entropy,
        physics=_agg_physics(res.physics_metrics),
        symbolic=res.symbolic[0] if res.symbolic else None,
        symbolic_unsafe=res.symbolic[1] if res.symbolic else False,
        sinks=[{"name": s.name, "line": s.line, "guarded": s.in_guarded_branch} for s in res.sinks],
        duration_ms=res.duration_s * 1000,
    )


def build_files_response(files: dict) -> dict:
    """Multiple files: per-file analysis + cross-file interprocedural taint."""
    if not files:
        return {"ok": False, "error": "no files provided"}
    if len(files) > MAX_FILES:
        return {"ok": False, "error": f"too many files ({len(files)} > {MAX_FILES})"}
    if sum(len(v) for v in files.values()) > MAX_TOTAL_SRC:
        return {"ok": False, "error": "combined source exceeds size limit"}

    import time
    start = time.time()
    all_findings = []
    entropies = []
    unsafe = False
    for path, code in files.items():
        try:
            res = analyze(code, use_symbolic=True, use_cache=False)
        except ValidationError:
            continue
        entropies.append(res.ast_entropy)
        unsafe = unsafe or (res.symbolic[1] if res.symbolic else False)
        for f in res.findings:
            f.artifact_uri = path
        all_findings.extend(res.findings)
    # Cross-file taint over the whole set.
    try:
        all_findings.extend(analyze_package(files))
    except Exception:
        pass
    # Dependency manifests in the upload: typosquat / slopsquat checks.
    try:
        from dependency_audit import audit_manifest, is_manifest
        for path, code in files.items():
            if is_manifest(path):
                all_findings.extend(audit_manifest(path, code))
    except Exception:
        pass

    avg_entropy = sum(entropies) / len(entropies) if entropies else 0.0
    return _payload(
        all_findings, files_scanned=len(files), entropy=avg_entropy,
        symbolic=("UNSAFE (reachable sink in ≥1 file)" if unsafe
                  else "SAFE (no unconditional reachable sink)"),
        symbolic_unsafe=unsafe, duration_ms=(time.time() - start) * 1000,
    )


def build_zip_response(zip_bytes: bytes) -> dict:
    """Extract .py files from an uploaded zip and scan as a project."""
    files = {}
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            total = 0
            for info in zf.infolist():
                if info.is_dir() or not info.filename.endswith(".py"):
                    continue
                if any(part in SKIP_DIRS for part in info.filename.split("/")):
                    continue
                if info.file_size > 1_000_000:      # skip absurd single files
                    continue
                total += info.file_size
                if total > MAX_TOTAL_SRC or len(files) >= MAX_FILES:
                    break
                with zf.open(info) as fh:
                    files[info.filename] = fh.read().decode("utf-8", "replace")
    except zipfile.BadZipFile:
        return {"ok": False, "error": "not a valid .zip archive"}
    if not files:
        return {"ok": False, "error": "no .py files found in archive"}
    return build_files_response(files)


def _engine_status() -> dict:
    snap = health.snapshot()
    return {"status": "ok",
            "engines": (str(len(snap)) + " ready") if snap else "ready",
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

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length > MAX_BODY:
            return None
        return self.rfile.read(length) if length else b""

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
        path = self.path.split("?", 1)[0]
        raw = self._read_body()
        if raw is None:
            self._send(413, json.dumps({"ok": False, "error": "request too large"}))
            return
        try:
            if path == "/api/scan":
                code = json.loads(raw or b"{}").get("code", "")
                self._send(200, json.dumps(build_scan_response(code)))
            elif path == "/api/scan-files":
                files = json.loads(raw or b"{}").get("files", {})
                self._send(200, json.dumps(build_files_response(files)))
            elif path == "/api/scan-zip":
                self._send(200, json.dumps(build_zip_response(raw)))
            else:
                self._send(404, json.dumps({"error": "not found"}))
        except json.JSONDecodeError:
            self._send(400, json.dumps({"ok": False, "error": "invalid JSON body"}))
        except Exception as e:
            self._send(500, json.dumps({"ok": False, "error": f"internal error: {e}"}))

    def log_message(self, *args):
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
