# relay

Small HTTP server that holds one "currently playing" record. The tablet
listener POSTs updates; the Roku channel GETs the latest.

Stdlib-only Python ([relay.py](relay.py)) so it runs under the Python
that ships with Termux - no `pip`, no virtualenv. Designed to run on the
Lenovo tablet alongside the listener, so listening + hosting live on one
device.

## API

```
GET  /now-playing   -> latest record, or {} if nothing is set
POST /now-playing   -> store a record (JSON body)
POST /now-playing   with {} or {"clear": true} -> clear it
GET  /health        -> {"ok": true}
```

Accepted POST fields: `artist`, `title`, `album`, `artUrl`, `source`
(any string; empty/missing ones are dropped). The server stamps
`updatedAt` (unix seconds) on every store so the Roku can age out a
stale record if it wants.

Example:

```bash
curl -s localhost:8080/now-playing
curl -s -XPOST localhost:8080/now-playing \
  -d '{"artist":"Miles Davis","title":"So What","album":"Kind of Blue","artUrl":"https://example.com/kob.jpg"}'
```

## Run

```bash
python3 relay.py
```

Config via environment variables:

| var | default | meaning |
|---|---|---|
| `RELAY_HOST` | `0.0.0.0` | bind address |
| `RELAY_PORT` | `8080` | bind port |
| `RELAY_TOKEN` | *(unset)* | if set, POST requires `Authorization: Bearer <token>` |
| `RELAY_STATE_FILE` | `now_playing.json` next to the script | where the record is mirrored so a restart doesn't blank the TV |

The state file is gitignored.

## Test

```bash
cd relay && python3 -m unittest -v
```

Stdlib `unittest` - spins up the server on an ephemeral port per test.
