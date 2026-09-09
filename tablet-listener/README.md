# tablet-listener

Runs on the Lenovo TB3-850F tablet under Termux. On an interval:

1. records a short mic clip (`termux-microphone-record`)
2. sends it to AudD (https://audd.io) for recognition
3. pulls artist / title / album / album-art URL from the response
4. POSTs that to the [relay](../relay)

Stdlib-only Python ([listener.py](listener.py)) — no `pip`. The recorder,
recogniser and poster are injectable, so the loop is tested off the
tablet ([test_listener.py](test_listener.py), 9 cases).

## Behaviour

- **Dedupe:** only POSTs when the (artist, title) changes, so the relay's
  `updatedAt` doesn't churn while one side of a record plays.
- **Album art:** prefers Apple Music artwork (its URL is a `{w}x{h}`
  template, filled to `ART_SIZE`), then Spotify, then Deezer.
- **Clearing:** after `CLEAR_AFTER_MISSES` consecutive no-matches it
  POSTs `{"clear": true}` so the TV goes blank when the music stops. Set
  to `0` to leave the last art up indefinitely.
- The loop swallows per-cycle errors (network blips, AudD hiccups) and
  keeps going.

## Setup on the tablet

```bash
pkg install python termux-api        # + the Termux:API app from F-Droid
cp .env.example .env                 # then edit: add AUDD_TOKEN
```

Grant the Termux:API app microphone permission (Android settings), and
keep the tablet plugged in (wired only — no wireless charging).

## Run

```bash
python3 listener.py            # loop forever
python3 listener.py --once     # single cycle (record → recognise → POST)
python3 listener.py --dry-run  # recognise + print, never POST
```

To keep it alive across reboots/disconnects, run it under
`termux-services` or a `while true` wrapper, alongside the relay.

## Config

Environment variables, optionally seeded from `.env` (gitignored). See
[.env.example](.env.example) for the full list — the essentials:

| var | default | |
|---|---|---|
| `AUDD_TOKEN` | *(required)* | AudD API token |
| `RELAY_URL` | `http://localhost:8080` | relay base URL (same tablet → localhost) |
| `POLL_INTERVAL` | `120` | seconds between attempts (AudD: 300 free, then ~$5/1000) |
| `CLIP_SECONDS` | `8` | clip length |
| `CLEAR_AFTER_MISSES` | `3` | misses before blanking the TV (`0` = never) |

## Test

```bash
cd tablet-listener && python3 -m unittest -v
```
