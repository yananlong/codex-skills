#!/usr/bin/env python3
"""Offline regression tests for the Zotero scripts against a local mock Web API."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
FETCH = SCRIPTS / "fetch_zotero_items.py"
EXPORT = SCRIPTS / "export_zotero_items.py"
INSPECT = SCRIPTS / "inspect_zotero_account.py"
API_KEY = "SYNTHETICKEY0123456789"
LIBRARY_SIZE = 250
REQUEST_CAP = 50


class MockZotero(BaseHTTPRequestHandler):
    """Fake 250-item user library 42; users 403/404 fail, user 429 throttles once."""

    requests: list[str] = []
    throttled = False

    def log_message(self, *args) -> None:  # silence test output
        pass

    def send(self, status: int, body: str, headers: dict[str, str] | None = None) -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        type(self).requests.append(self.path)
        if len(type(self).requests) > REQUEST_CAP:
            self.send(500, "request cap exceeded: pagination did not terminate")
            return
        url = urlsplit(self.path)
        query = parse_qs(url.query)
        if self.headers.get("Zotero-API-Key") != API_KEY:
            self.send(403, "Forbidden")
            return
        if url.path == "/keys/current":
            self.send(200, json.dumps({"key": API_KEY, "userID": 42, "username": "synthetic", "access": {"user": {"library": True}}}))
            return
        if url.path.endswith("/groups"):
            self.send(200, "[]")
            return
        if url.path.startswith("/users/403/"):
            self.send(403, "Forbidden")
            return
        if url.path.startswith("/users/404/"):
            self.send(404, "Not found")
            return
        if url.path.startswith("/users/429/") and not type(self).throttled:
            type(self).throttled = True
            self.send(429, "Too many requests", {"Retry-After": "0"})
            return
        start = int(query.get("start", ["0"])[0])
        limit = int(query.get("limit", ["25"])[0])
        fmt = query.get("format", ["json"])[0]
        page = range(start, min(start + limit, LIBRARY_SIZE))
        headers = {"Total-Results": str(LIBRARY_SIZE)}
        if fmt in ("bibtex", "biblatex", "ris"):
            body = "\n".join(f"@article{{k{i},\n  title = {{Synthetic {i}}}\n}}" for i in page)
            self.send(200, body, headers)
        else:
            self.send(200, json.dumps([{"key": f"K{i:04d}", "data": {"title": f"Synthetic {i}"}} for i in page]), headers)


class ZoteroScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), MockZotero)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.api_root = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self) -> None:
        MockZotero.requests = []
        MockZotero.throttled = False
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_script(self, script: Path, *args: str, api_key: str = API_KEY) -> subprocess.CompletedProcess[str]:
        env = {k: v for k, v in os.environ.items() if "proxy" not in k.lower()}
        env.update(ZOTERO_API_ROOT=self.api_root, ZOTERO_API_KEY=api_key, NO_PROXY="127.0.0.1,localhost")
        return subprocess.run([sys.executable, str(script), *args], text=True, capture_output=True, env=env, timeout=60)

    def test_fetch_paginates_full_library_by_default(self) -> None:
        out = self.root / "zotero" / "zotero-items.json"
        note = self.root / "zotero" / "zotero-sync.md"
        cp = self.run_script(FETCH, "--out", str(out), "--sync-note", str(note))
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        payload = json.loads(out.read_text())
        self.assertEqual(payload["item_count"], LIBRARY_SIZE)
        self.assertEqual(payload["total_results"], LIBRARY_SIZE)
        self.assertIs(payload["partial"], False)
        self.assertEqual(len({item["key"] for item in payload["items"]}), LIBRARY_SIZE)
        self.assertIn("Partial sync: no", note.read_text())

    def test_fetch_max_items_marks_partial(self) -> None:
        out = self.root / "items.json"
        cp = self.run_script(FETCH, "--out", str(out), "--max-items", "120")
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        payload = json.loads(out.read_text())
        self.assertEqual(payload["item_count"], 120)
        self.assertEqual(payload["total_results"], LIBRARY_SIZE)
        self.assertIs(payload["partial"], True)
        self.assertIn("WARNING: partial sync", cp.stderr)

    def test_export_bibtex_all_terminates_with_every_entry(self) -> None:
        out = self.root / "library-export.bib"
        cp = self.run_script(EXPORT, "--format", "bibtex", "--all", "--out", str(out))
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        self.assertLessEqual(len(MockZotero.requests), 10)
        self.assertEqual(out.read_text().count("@article{"), LIBRARY_SIZE)

    def test_export_json_default_is_complete(self) -> None:
        out = self.root / "library-export.json"
        cp = self.run_script(EXPORT, "--format", "json", "--out", str(out))
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        self.assertEqual(len(json.loads(out.read_text())), LIBRARY_SIZE)

    def test_inspect_never_writes_api_key(self) -> None:
        out = self.root / "zotero-account.json"
        cp = self.run_script(INSPECT, "--out", str(out))
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        text = out.read_text()
        self.assertNotIn(API_KEY, text)
        payload = json.loads(text)
        self.assertNotIn("key", payload["key_info"])
        self.assertEqual(payload["key_info"]["userID"], 42)

    def test_forbidden_and_missing_libraries_give_clear_messages(self) -> None:
        cp = self.run_script(FETCH, "--user-id", "403", "--out", str(self.root / "a.json"))
        self.assertEqual(cp.returncode, 1)
        self.assertIn("403 Forbidden", cp.stderr)
        self.assertIn("lacks read access", cp.stderr)
        self.assertNotIn("Traceback", cp.stderr)
        self.assertNotIn(API_KEY, cp.stderr)
        cp = self.run_script(FETCH, "--user-id", "404", "--out", str(self.root / "b.json"))
        self.assertEqual(cp.returncode, 1)
        self.assertIn("404 Not Found", cp.stderr)
        self.assertNotIn("Traceback", cp.stderr)
        cp = self.run_script(INSPECT, api_key="BOGUS")
        self.assertEqual(cp.returncode, 1)
        self.assertIn("403 Forbidden", cp.stderr)
        self.assertNotIn("Traceback", cp.stderr)

    def test_rate_limit_is_retried_after_retry_after(self) -> None:
        out = self.root / "items.json"
        cp = self.run_script(FETCH, "--user-id", "429", "--out", str(out))
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        self.assertIn("retrying", cp.stderr)
        self.assertEqual(json.loads(out.read_text())["item_count"], LIBRARY_SIZE)


if __name__ == "__main__":
    unittest.main()
