#!/usr/bin/env python3
"""Now Playing relay.

Holds a single "currently playing" record in memory (and mirrors it to a
JSON file so a restart on the tablet doesn't blank the TV). The tablet
listener POSTs updates; the Roku channel GETs the latest.

Stdlib only - runs under the Python that ships with Termux, no pip.

Endpoints
    GET  /now-playing   -> latest record, or {} if nothing is set
    POST /now-playing   -> store a record (JSON body, see FIELDS)
    POST /now-playing   with body {} or {"clear": true} -> clear it
    GET  /health        -> {"ok": true}

Config (environment variables)
    RELAY_HOST        bind address           (default 0.0.0.0)
    RELAY_PORT        bind port              (default 8080)
    RELAY_TOKEN       if set, POST requires  Authorization: Bearer <token>
    RELAY_STATE_FILE  path to the mirror     (default now_playing.json
                      file                    next to this script)
"""

from __future__ import annotations

import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Fields we accept from the listener. Anything else in the body is dropped.
FIELDS = ("artist", "title", "album", "artUrl", "source")

HOST = os.environ.get("RELAY_HOST", "0.0.0.0")
PORT = int(os.environ.get("RELAY_PORT", "8080"))
TOKEN = os.environ.get("RELAY_TOKEN", "")
STATE_FILE = os.environ.get(
    "RELAY_STATE_FILE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "now_playing.json"),
)

MAX_BODY = 64 * 1024  # generous for a handful of short strings + a URL


class State:
    """The one record, guarded by nothing fancy - handlers are short and
    the GIL makes the dict swap atomic enough for this workload."""

    def __init__(self, path: str):
        self.path = path
        self.record: dict = {}
        self._load()

    def _load(self) -> None:
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, dict):
                self.record = data
        except FileNotFoundError:
            pass
        except (OSError, ValueError) as exc:
            print(f"relay: ignoring unreadable state file: {exc}", file=sys.stderr)

    def _persist(self) -> None:
        tmp = f"{self.path}.tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(self.record, fh)
            os.replace(tmp, self.path)
        except OSError as exc:
            print(f"relay: could not write state file: {exc}", file=sys.stderr)

    def get(self) -> dict:
        return self.record

    def set(self, body: dict) -> dict:
        if not body or body.get("clear") is True:
            self.record = {}
            self._persist()
            return self.record

        cleaned = {k: body[k] for k in FIELDS if isinstance(body.get(k), str) and body[k]}
        cleaned["updatedAt"] = int(time.time())
        self.record = cleaned
        self._persist()
        return self.record


STATE = State(STATE_FILE)


class Handler(BaseHTTPRequestHandler):
    server_version = "NowPlayingRelay/0.1"

    # --- helpers -------------------------------------------------------

    def _send_json(self, obj: dict, status: int = 200) -> None:
        payload = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)

    def _authorized(self) -> bool:
        if not TOKEN:
            return True
        header = self.headers.get("Authorization", "")
        return header == f"Bearer {TOKEN}"

    def _read_json_body(self) -> dict | None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return None
        if length <= 0:
            return {}
        if length > MAX_BODY:
            return None
        raw = self.rfile.read(length)
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return None
        return parsed if isinstance(parsed, dict) else None

    # --- routes -------------------------------------------------------

    def _path(self) -> str:
        return self.path.split("?", 1)[0].rstrip("/") or "/"

    def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
        path = self._path()
        if path == "/now-playing":
            self._send_json(STATE.get())
        elif path == "/health":
            self._send_json({"ok": True})
        else:
            self._send_json({"error": "not found"}, 404)

    do_HEAD = do_GET

    def do_POST(self) -> None:  # noqa: N802
        if self._path() != "/now-playing":
            self._send_json({"error": "not found"}, 404)
            return
        if not self._authorized():
            self._send_json({"error": "unauthorized"}, 401)
            return
        body = self._read_json_body()
        if body is None:
            self._send_json({"error": "bad request"}, 400)
            return
        self._send_json(STATE.set(body))

    # Quieter, single-line logging.
    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write(
            "%s - %s\n" % (self.address_string(), fmt % args)
        )


def main() -> None:
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    auth = "on" if TOKEN else "off"
    print(f"relay: listening on {HOST}:{PORT}  (auth: {auth})  state: {STATE_FILE}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nrelay: stopping")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
