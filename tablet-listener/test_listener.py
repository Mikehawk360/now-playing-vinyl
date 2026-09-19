#!/usr/bin/env python3
"""Tests for the tablet listener. Stdlib only: python -m unittest (from
tablet-listener/). No Termux, no network - recorder/recogniser/poster
are stubbed.
"""

import unittest

import listener
from listener import Config, Listener, extract


APPLE = {
    "artist": "Miles Davis", "title": "So What", "album": "Kind of Blue",
    "apple_music": {"artwork": {
        "url": "https://is1-ssl.mzstatic.com/image/thumb/abc/{w}x{h}{f}.jpg"}},
}
SPOTIFY_ONLY = {
    "artist": "Fugazi", "title": "Waiting Room", "album": "13 Songs",
    "spotify": {"album": {"images": [
        {"url": "https://i.scdn.co/image/big", "width": 640},
        {"url": "https://i.scdn.co/image/small", "width": 64}]}},
}
DEEZER_ONLY = {
    "artist": "Air", "title": "La Femme d'Argent", "album": "Moon Safari",
    "deezer": {"album": {"cover_big": "https://e-cdn.deezer.com/big",
                         "cover_xl": "https://e-cdn.deezer.com/xl"}},
}
NO_ART = {"artist": "Someone", "title": "Untitled", "album": ""}


def _cfg(**over):
    base = dict(audd_token="t", relay_url="http://r", interval=120,
                clip_seconds=8, clip_path="/tmp/x.m4a", art_size=1000,
                clear_after=3)
    base.update(over)
    return Config(**base)


class ExtractTest(unittest.TestCase):
    def test_apple_artwork_template_filled(self):
        rec = extract(APPLE, art_size=1200)
        self.assertEqual(
            rec["artUrl"],
            "https://is1-ssl.mzstatic.com/image/thumb/abc/1200x1200jpg.jpg")
        self.assertEqual(rec["album"], "Kind of Blue")
        self.assertEqual(rec["source"], "audd")

    def test_spotify_fallback_picks_first(self):
        self.assertEqual(extract(SPOTIFY_ONLY)["artUrl"],
                         "https://i.scdn.co/image/big")

    def test_deezer_fallback_prefers_xl(self):
        self.assertEqual(extract(DEEZER_ONLY)["artUrl"],
                         "https://e-cdn.deezer.com/xl")

    def test_no_art_drops_empty_fields(self):
        rec = extract(NO_ART)
        self.assertNotIn("artUrl", rec)
        self.assertNotIn("album", rec)
        self.assertEqual(rec["artist"], "Someone")


class MultipartTest(unittest.TestCase):
    def test_body_has_boundary_fields_and_file(self):
        body, boundary = listener._multipart(
            {"api_token": "T", "return": "spotify"}, "c.m4a", b"AUDIO", "audio/mp4")
        text = body.decode("latin-1")
        self.assertIn(f"--{boundary}\r\n", text)
        self.assertIn('name="api_token"', text)
        self.assertIn('filename="c.m4a"', text)
        self.assertIn("AUDIO", text)
        self.assertTrue(text.endswith(f"--{boundary}--\r\n"))


class LoopTest(unittest.TestCase):
    def setUp(self):
        self.posted = []
        self.audio_written = []

        def fake_recorder(path, seconds, **kw):
            self.audio_written.append((path, seconds))

        def fake_poster(record, url, token="", **kw):
            self.posted.append(record)
            return {}

        self.fake_recorder = fake_recorder
        self.fake_poster = fake_poster

    def _listener(self, results, **cfg_over):
        it = iter(results)

        def fake_recognizer(audio, token, **kw):
            return next(it)

        lis = Listener(_cfg(**cfg_over), recorder=self.fake_recorder,
                       recognizer=fake_recognizer, poster=self.fake_poster)
        # skip the real file read
        lis.run_once = _patch_run_once(lis)
        return lis

    def test_posts_on_new_track_then_dedupes(self):
        lis = self._listener([APPLE, APPLE, SPOTIFY_ONLY])
        lis.run_once(); lis.run_once(); lis.run_once()
        self.assertEqual(len(self.posted), 2)
        self.assertEqual(self.posted[0]["artist"], "Miles Davis")
        self.assertEqual(self.posted[1]["artist"], "Fugazi")

    def test_clears_after_configured_misses(self):
        lis = self._listener([APPLE, None, None, None], clear_after=3)
        lis.run_once()                      # sets a track
        lis.run_once(); lis.run_once()      # miss 1, 2 - no clear yet
        self.assertEqual(len(self.posted), 1)
        lis.run_once()                      # miss 3 - clear
        self.assertEqual(self.posted[-1], {"clear": True})
        self.assertIsNone(lis.last_key)

    def test_never_clears_when_disabled(self):
        lis = self._listener([APPLE, None, None, None, None], clear_after=0)
        for _ in range(5):
            lis.run_once()
        self.assertEqual(len(self.posted), 1)

    def test_miss_before_any_match_does_not_post(self):
        lis = self._listener([None, None, None, None])
        for _ in range(4):
            lis.run_once()
        self.assertEqual(self.posted, [])


def _patch_run_once(lis):
    """Return a run_once bound to `lis` that skips reading the clip file."""
    from pathlib import Path
    real = type(lis).run_once

    def run_once():
        orig = Path.read_bytes
        Path.read_bytes = lambda self: b"AUDIO"
        try:
            return real(lis)
        finally:
            Path.read_bytes = orig
    return run_once


if __name__ == "__main__":
    unittest.main()
