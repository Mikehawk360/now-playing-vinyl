#!/usr/bin/env python3
"""Now Playing tablet listener.

Loop, on a conservative interval:
  1. record a short clip from the tablet mic (Termux:API)
  2. send it to AudD (https://audd.io) for recognition
  3. pull artist / title / album / album-art URL out of the response
  4. POST that to the relay

Stdlib only - runs under Termux's Python, no pip. The recorder,
recogniser, and poster are injectable so the whole loop is testable off
the tablet (see test_listener.py).

Usage:
  python3 listener.py            # loop forever
  python3 listener.py --once     # one cycle, then exit
  python3 listener.py --dry-run  # recognise + print, never POST

Config: environment variables, optionally seeded from a .env file next
to this script (KEY=value lines). See .env.example.

  AUDD_TOKEN        (required) AudD API token
  RELAY_URL        default http://localhost:8080
  RELAY_TOKEN      bearer token, if the relay requires one
  POLL_INTERVAL    seconds between recognition attempts (default 120)
  CLIP_SECONDS     clip length to record (default 8)
  CLIP_PATH        where to write the clip (default: temp dir)
  ART_SIZE         px for Apple Music artwork template (default 1000)
  CLEAR_AFTER_MISSES  consecutive no-matches before clearing the relay
                      (default 3; 0 = never clear)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path

AUDD_ENDPOINT = "https://api.audd.io/"
AUDD_RETURN = "apple_music,spotify,deezer"


def log(msg: str) -> None:
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"{stamp}  {msg}", flush=True)


# --------------------------------------------------------------------- config


@dataclass
class Config:
    audd_token: str
    relay_url: str = "http://localhost:8080"
    relay_token: str = ""
    interval: int = 120
    clip_seconds: int = 8
    clip_path: str = ""
    art_size: int = 1000
    clear_after: int = 3


def _load_dotenv(path: Path) -> dict:
    values: dict = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        values[key.strip()] = val.strip().strip('"').strip("'")
    return values


def load_config(env: dict | None = None) -> Config:
    here = Path(__file__).resolve().parent
    merged = {**_load_dotenv(here / ".env"), **(env if env is not None else os.environ)}

    token = merged.get("AUDD_TOKEN", "").strip()
    if not token:
        raise SystemExit(
            "AUDD_TOKEN is not set. Put it in tablet-listener/.env or the "
            "environment (see .env.example)."
        )

    def _int(key: str, default: int) -> int:
        try:
            return int(merged.get(key, default))
        except (TypeError, ValueError):
            return default

    clip_path = merged.get("CLIP_PATH", "").strip()
    if not clip_path:
        clip_path = str(Path(tempfile.gettempdir()) / "nowplaying_clip.m4a")

    return Config(
        audd_token=token,
        relay_url=merged.get("RELAY_URL", "http://localhost:8080").strip(),
        relay_token=merged.get("RELAY_TOKEN", "").strip(),
        interval=max(15, _int("POLL_INTERVAL", 120)),
        clip_seconds=max(3, _int("CLIP_SECONDS", 8)),
        clip_path=clip_path,
        art_size=max(100, _int("ART_SIZE", 1000)),
        clear_after=max(0, _int("CLEAR_AFTER_MISSES", 3)),
    )


# ----------------------------------------------------------------- recording


def record_clip(path: str, seconds: int) -> None:
    """Record `seconds` of audio to `path` via Termux:API."""
    Path(path).unlink(missing_ok=True)
    subprocess.run(
        ["termux-microphone-record", "-d", "-f", path, "-l", str(seconds)],
        check=True, capture_output=True, timeout=20,
    )
    time.sleep(seconds + 1)
    # Force-stop in case the limit didn't fire; harmless if already stopped.
    subprocess.run(
        ["termux-microphone-record", "-q"], capture_output=True, timeout=10,
    )
    if not Path(path).exists() or Path(path).stat().st_size == 0:
        raise RuntimeError(f"no audio captured at {path}")


# --------------------------------------------------------------- recognition


def _multipart(fields: dict, filename: str, content: bytes, ctype: str):
    boundary = "----nowplaying" + uuid.uuid4().hex
    parts: list[bytes] = []
    for name, value in fields.items():
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
        )
        parts.append(f"{value}\r\n".encode())
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        .encode()
    )
    parts.append(f"Content-Type: {ctype}\r\n\r\n".encode())
    parts.append(content)
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    return b"".join(parts), boundary


def recognize(audio: bytes, token: str, *, filename: str = "clip.m4a",
              timeout: int = 30) -> dict | None:
    """Return AudD's `result` dict, or None when nothing matched."""
    body, boundary = _multipart(
        {"api_token": token, "return": AUDD_RETURN},
        filename, audio, "audio/mp4",
    )
    req = urllib.request.Request(
        AUDD_ENDPOINT, data=body, method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    if payload.get("status") != "success":
        raise RuntimeError(f"AudD error: {payload.get('error', payload)}")
    return payload.get("result")


def _artwork_url(result: dict, size: int) -> str:
    apple = result.get("apple_music") or {}
    art = (apple.get("artwork") or {}).get("url")
    if art:
        return (art.replace("{w}", str(size))
                   .replace("{h}", str(size))
                   .replace("{f}", "jpg"))

    spotify = result.get("spotify") or {}
    images = (spotify.get("album") or {}).get("images") or []
    if images and images[0].get("url"):
        return images[0]["url"]

    deezer = result.get("deezer") or {}
    album = deezer.get("album") or {}
    for key in ("cover_xl", "cover_big", "cover_medium"):
        if album.get(key):
            return album[key]

    return ""


def extract(result: dict, *, art_size: int = 1000) -> dict:
    """Flatten an AudD result into a relay record (empty fields dropped)."""
    record = {
        "artist": (result.get("artist") or "").strip(),
        "title": (result.get("title") or "").strip(),
        "album": (result.get("album") or "").strip(),
        "artUrl": _artwork_url(result, art_size),
        "source": "audd",
    }
    return {k: v for k, v in record.items() if v}


# ---------------------------------------------------------------------- relay


def post_now_playing(record: dict, relay_url: str, token: str = "",
                     *, timeout: int = 10) -> dict:
    data = json.dumps(record).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        relay_url.rstrip("/") + "/now-playing",
        data=data, headers=headers, method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ----------------------------------------------------------------------- loop


class Listener:
    def __init__(self, cfg: Config, *, recorder=record_clip,
                 recognizer=recognize, poster=post_now_playing, dry_run=False):
        self.cfg = cfg
        self.recorder = recorder
        self.recognizer = recognizer
        self.poster = poster
        self.dry_run = dry_run
        self.last_key: tuple | None = None
        self.misses = 0

    def _send(self, record: dict) -> None:
        if self.dry_run:
            log(f"[dry-run] would POST {record}")
            return
        self.poster(record, self.cfg.relay_url, self.cfg.relay_token)

    def run_once(self) -> dict | None:
        self.recorder(self.cfg.clip_path, self.cfg.clip_seconds)
        audio = Path(self.cfg.clip_path).read_bytes()
        result = self.recognizer(audio, self.cfg.audd_token)

        if not result:
            self.misses += 1
            log(f"no match ({self.misses})")
            if (self.cfg.clear_after
                    and self.misses >= self.cfg.clear_after
                    and self.last_key is not None):
                self._send({"clear": True})
                self.last_key = None
                log("cleared relay after repeated misses")
            return None

        self.misses = 0
        record = extract(result, art_size=self.cfg.art_size)
        key = (record.get("artist", ""), record.get("title", ""))

        if key == self.last_key:
            log(f"still playing: {key[0]} - {key[1]}")
            return record

        self._send(record)
        self.last_key = key
        log(f"now playing: {key[0]} - {key[1]}"
            + ("" if record.get("artUrl") else "  (no art url!)"))
        return record

    def run_forever(self) -> None:
        log(f"listener up: relay={self.cfg.relay_url} "
            f"interval={self.cfg.interval}s clip={self.cfg.clip_seconds}s "
            f"{'[dry-run] ' if self.dry_run else ''}")
        while True:
            start = time.monotonic()
            try:
                self.run_once()
            except Exception as exc:  # keep the loop alive
                log(f"cycle error: {exc!r}")
            time.sleep(max(5.0, self.cfg.interval - (time.monotonic() - start)))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Now Playing tablet listener")
    parser.add_argument("--once", action="store_true", help="one cycle then exit")
    parser.add_argument("--dry-run", action="store_true",
                        help="recognise and print, never POST")
    args = parser.parse_args(argv)

    listener = Listener(load_config(), dry_run=args.dry_run)
    if args.once:
        listener.run_once()
    else:
        try:
            listener.run_forever()
        except KeyboardInterrupt:
            log("stopping")


if __name__ == "__main__":
    sys.exit(main())
