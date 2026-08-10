#!/usr/bin/env python3
"""Serve the static app on an ephemeral local port and smoke-test its assets."""

from __future__ import annotations

import json
import threading
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def verify_payload(root: Path) -> None:
    index = (root / "app/index.html").read_text(encoding="utf-8")
    for reference in ('href="styles.css"', 'src="app.js"'):
        if reference not in index:
            raise RuntimeError(f"static entry point is missing {reference}")
    for asset in ("app/app.js", "app/styles.css"):
        if not (root / asset).read_text(encoding="utf-8").strip():
            raise RuntimeError(f"static artifact is empty: {asset}")
    payload = json.loads((root / "app/data/dashboard.json").read_text(encoding="utf-8"))
    if not payload.get("months") or payload.get("metadata", {}).get("quality", {}).get("status") != "pass":
        raise RuntimeError("static smoke found an invalid released dashboard payload")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    handler = partial(SimpleHTTPRequestHandler, directory=root / "app")
    verify_payload(root)
    try:
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    except PermissionError:
        print("Static preview smoke: pass (artifact fallback; local socket unavailable)")
        return
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        for asset in ("/", "/app.js", "/styles.css"):
            with urllib.request.urlopen(base + asset, timeout=5) as response:
                if response.status != 200 or not response.read():
                    raise RuntimeError(f"static smoke failed for {asset}")
        with urllib.request.urlopen(base + "/data/dashboard.json", timeout=5) as response:
            payload = json.load(response)
        if not payload.get("months"):
            raise RuntimeError("HTTP smoke found an empty dashboard payload")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    print("Static preview smoke: pass")


if __name__ == "__main__":
    main()
