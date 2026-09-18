"""Local test fixture. Faults are server configuration, never runner-side mocks."""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

MODES = ["normal", "overlay", "invisible", "http500", "no_persist", "wrong_type", "duplicate_button", "delayed_commit", "keyboard_only", "cleanup_fail"]


class Fixture:
    def __init__(self, database: str = ":memory:", mode: str = "normal"):
        if mode not in MODES:
            raise ValueError("unknown fixture mode")
        self.mode = mode
        self.db = sqlite3.connect(database, check_same_thread=False)
        self.db.execute("CREATE TABLE IF NOT EXISTS devices (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, type TEXT NOT NULL)")
        self.db.commit()
        self.lock = threading.Lock()
        self.write_count = 0

    def seed(self, name, device_type="PCS"):
        with self.lock:
            self.db.execute("INSERT INTO devices(name,type) VALUES (?,?)", (name, device_type))
            self.db.commit()

    def rows(self):
        with self.lock:
            return [dict(zip(["id", "name", "type"], r)) for r in self.db.execute("SELECT id,name,type FROM devices ORDER BY id")]

    def handler(self):
        fixture = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def reply(self, status, value, content_type="application/json"):
                raw = value.encode() if isinstance(value, str) else json.dumps(value).encode()
                self.send_response(status)
                self.send_header("Content-Type", content_type + "; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                try:
                    self.wfile.write(raw)
                except BrokenPipeError:
                    pass

            def do_GET(self):
                p = urlsplit(self.path)
                if p.path == "/":
                    self.reply(200, Path(__file__).with_name("fixture.html").read_text(), "text/html")
                elif p.path == "/config":
                    self.reply(200, {"mode": fixture.mode, "build": "fixture-v1"})
                elif p.path == "/devices":
                    query = parse_qs(p.query).get("q", [""])[0]
                    self.reply(200, [r for r in fixture.rows() if query.lower() in r["name"].lower()])
                elif p.path == "/favicon.ico":
                    self.reply(204, "", "image/x-icon")
                else:
                    self.reply(404, {"error": "Not found"})

            def do_POST(self):
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if not 0 < length <= 10000:
                        return self.reply(400, {"error": "Invalid payload size"})
                    data = json.loads(self.rfile.read(length))
                    name, kind = data.get("name", "").strip(), data.get("type", "")
                    if not name or len(name) > 32 or kind not in {"PCS", "Inverter"}:
                        return self.reply(400, {"error": "Invalid device"})
                    if fixture.mode == "http500":
                        return self.reply(500, {"error": "Save failed"})
                    with fixture.lock:
                        fixture.write_count += 1
                        if fixture.mode != "no_persist":
                            if self.path == "/devices":
                                fixture.db.execute("INSERT INTO devices(name,type) VALUES (?,?)", (name, "Inverter" if fixture.mode == "wrong_type" else kind))
                            elif self.path.startswith("/devices/"):
                                fixture.db.execute("UPDATE devices SET name=?,type=? WHERE id=?", (name, kind, int(self.path.split("/")[-1])))
                            else:
                                return self.reply(404, {"error": "Not found"})
                            fixture.db.commit()
                    if fixture.mode == "delayed_commit":
                        time.sleep(4)
                    self.reply(200, {"ok": True})
                except sqlite3.IntegrityError:
                    self.reply(409, {"error": "Name already exists"})
                except (ValueError, TypeError, AttributeError):
                    self.reply(400, {"error": "Invalid request"})

            def do_DELETE(self):
                if fixture.mode == "cleanup_fail":
                    return self.reply(500, {"error": "Delete failed"})
                try:
                    ident = int(self.path.split("/")[-1])
                    with fixture.lock:
                        fixture.db.execute("DELETE FROM devices WHERE id=?", (ident,))
                        fixture.db.commit()
                    self.reply(200, {"ok": True})
                except ValueError:
                    self.reply(400, {"error": "Invalid identifier"})

        return Handler


@contextmanager
def serve_fixture(mode="normal", port=0, database=":memory:"):
    fixture = Fixture(database, mode)
    server = ThreadingHTTPServer(("127.0.0.1", port), fixture.handler())
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield fixture, f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        fixture.db.close()

