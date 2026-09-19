# roku-channel

BrightScript / SceneGraph app for the Roku Express. Polls the
[relay](../relay) and shows the current record's album art fullscreen,
centered on black. Falls back to a status label when nothing is playing,
the relay is unreachable, or the image fails to load.

## Layout

```
manifest                     channel metadata, version numbers
source/main.brs              entry point, creates the SceneGraph screen
components/MainScene.xml      background + centered Poster + status Label
components/MainScene.brs      config constants, reacts to the poller: art vs. status label
components/RelayPoller.xml    Task node interface
components/RelayPoller.brs    GET <relay_url>/now-playing on an interval
```

## Configure

Edit the two constants at the top of `init()` in
[components/MainScene.brs](components/MainScene.brs):

```brightscript
RELAY_URL = "http://192.168.1.100:8080"
POLL_INTERVAL_SECONDS = 10
```

(These used to be manifest keys read via `roAppInfo.GetValue()` — that
call isn't documented to support arbitrary custom keys, and on-device it
silently returned `""`, leaving the channel stuck on "Waiting for
music..." forever with no error. Hardcoded constants are boring but
guaranteed to work.)

`RELAY_URL` must be the tablet's LAN IP (where the Termux relay
listens), reachable from the Roku. Repackage after changing it, and bump
`build_version` in `manifest` — the web installer treats an identical
package as a no-op and won't reinstall/relaunch it.

## Package and sideload

The Roku web installer expects a .zip whose root contains `manifest`
(not a wrapper folder). From this directory:

```bash
powershell -File package.ps1
```

That writes `now-playing-vinyl.zip` (gitignored). Then:

1. Open `http://<roku-ip>/` (user `rokudev`, the dev password set when
   Developer Mode was enabled).
2. Upload `now-playing-vinyl.zip` and click **Replace**.
3. The channel launches. With no music playing you'll see
   "Waiting for music..."; start a record and the art should appear
   within `POLL_INTERVAL_SECONDS`.

## Debugging

`telnet <roku-ip> 8085` streams `print` output while the channel runs —
`init()`, `onNowPlaying()`, and `onReachable()` all log. This is the
first thing to check if the screen doesn't update: it'll show the
configured `relay_url`, whether each poll reached the relay, and what
JSON came back.
