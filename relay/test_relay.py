#!/usr/bin/env python3
"""Smoke tests for the relay. Stdlib only: python -m unittest (from relay/).

Each test gets a fresh server on an ephemeral port with its own temp
state file, so they don't share the module-level STATE.
"""

import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import relay


def _request(url, method="GET", body=None, headers=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode())


class RelayTest(unittest.TestCase):
    def setUp(self):
        fd, self.state_path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        os.unlink(self.state_path)  # start with no file

        relay.STATE = relay.State(self.state_path)
        relay.TOKEN = ""

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), relay.Handler)
        self.base = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=5)
        if os.path.exists(self.state_path):
            os.unlink(self.state_path)

    def test_empty_before_any_post(self):
        status, body = _request(f"{self.base}/now-playing")
        self.assertEqual(status, 200)
        self.assertEqual(body, {})

    def test_health(self):
        status, body = _request(f"{self.base}/health")
        self.assertEqual(status, 200)
        self.assertEqual(body, {"ok": True})

    def test_post_then_get_roundtrip(self):
        rec = {"artist": "Miles Davis", "title": "So What", "album": "Kind of Blue",
               "artUrl": "https://example.com/kob.jpg", "ignored": "drop me"}
        status, body = _request(f"{self.base}/now-playing", "POST", rec)
        self.assertEqual(status, 200)
        self.assertEqual(body["artist"], "Miles Davis")
        self.assertNotIn("ignored", body)
        self.assertIn("updatedAt", body)

        status, body = _request(f"{self.base}/now-playing")
        self.assertEqual(body["album"], "Kind of Blue")

    def test_clear(self):
        _request(f"{self.base}/now-playing", "POST", {"artist": "X", "title": "Y"})
        status, body = _request(f"{self.base}/now-playing", "POST", {"clear": True})
        self.assertEqual(body, {})
        _, body = _request(f"{self.base}/now-playing")
        self.assertEqual(body, {})

    def test_bad_json_is_400(self):
        req = urllib.request.Request(
            f"{self.base}/now-playing", data=b"{not json", method="POST")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=5)
        self.assertEqual(ctx.exception.code, 400)

    def test_token_required_when_set(self):
        relay.TOKEN = "sekret"
        status, _ = _request(f"{self.base}/now-playing", "POST", {"artist": "X"})
        self.assertEqual(status, 401)
        status, _ = _request(
            f"{self.base}/now-playing", "POST", {"artist": "X"},
            headers={"Authorization": "Bearer sekret"})
        self.assertEqual(status, 200)

    def test_state_survives_new_state_object(self):
        _request(f"{self.base}/now-playing", "POST", {"artist": "Persist", "title": "Me"})
        reloaded = relay.State(self.state_path)
        self.assertEqual(reloaded.get()["artist"], "Persist")


if __name__ == "__main__":
    unittest.main()
