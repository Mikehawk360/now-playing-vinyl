# roku-channel

BrightScript / SceneGraph app for the Roku Express. Polls the
[relay](../relay) and shows the current record's album art fullscreen,
centered on black. Falls back to a status label when nothing is playing,
the relay is unreachable, or the image fails to load.

## Layout

```
manifest                     channel metadata + relay_url / poll_interval_seconds
source/main.brs              entry point, creates the SceneGraph screen
components/MainScene.xml      background + centered Poster + status Label
components/MainScene.brs      reacts to the poller: art vs. status label
components/RelayPoller.xml    Task node interface
components/RelayPoller.brs    GET <relay_url>/now-playing on an interval
```

## Configure

Edit the config block at the bottom of `manifest`:

```
relay_url=http://192.168.1.100:8080
poll_interval_seconds=10
```

`relay_url` must be the tablet's LAN IP (where the Termux relay listens),
reachable from the Roku. Repackage after changing it.

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
   within `poll_interval_seconds`.

## Debugging

`telnet <roku-ip> 8085` streams `print` output from `RelayPoller.brs` /
`MainScene.brs` while the channel runs.
