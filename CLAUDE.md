# Now Playing (Vinyl → Roku Album Art Display)

## Goal
Display the album art of whatever record is currently playing on the
turntable, shown full-screen on a TV via a sideloaded Roku Express channel.

## Architecture (3 pieces)
1. **roku-channel/** — BrightScript/SceneGraph app on the Roku Express.
   Polls a relay endpoint for now-playing JSON, displays the album art
   fullscreen.
2. **relay/** — small server that stores "currently playing" JSON.
   Tablet POSTs to it, Roku GETs from it. Not yet built. Likely candidate:
   run directly on the tablet via Termux, so listening + hosting live on
   one device (no separate Pi/cloud dependency needed).
3. **tablet-listener/** — runs on the Lenovo TB3-850F tablet. Records a
   short audio clip periodically, sends it to the AudD API
   (https://audd.io) for recognition, gets back artist/title/album art
   URL, posts it to the relay. Not yet built.

## Hardware
- **Roku Express** — Developer Mode enabled and confirmed working.
  Sideloading tested successfully via the web installer
  (http://<roku-ip>, user `rokudev`).
- **Lenovo TB3-850F tablet** — 2GB RAM, Android, wired charging only
  (no wireless charging). Will run the listener + relay via Termux.
  Plan is to leave it plugged in continuously near the turntable/speakers.

## Status
- [x] Roku Developer Mode enabled
- [x] "Hello World" BrightScript channel built and sideloaded successfully
      (proves the full package → upload → run pipeline works)
- [x] Repo structure created (roku-channel/, relay/, tablet-listener/)
- [x] Roku channel files in roku-channel/ (manifest, source/main.brs,
      components/MainScene.xml, components/MainScene.brs) — recreated in
      the repo rather than moved; the original sideloaded Hello World
      files were never checked in. package.ps1 builds the sideload zip.
- [ ] Re-sideload from roku-channel/ to confirm the repo copy runs
- [x] Build the relay endpoint (relay/relay.py — stdlib-only Python,
      GET/POST /now-playing + /health, optional bearer token, JSON
      mirror file. relay/test_relay.py: 7 unittest cases, passing.)
- [x] Build the tablet listener (tablet-listener/listener.py — stdlib
      Python: record clip → AudD → extract art (Apple/Spotify/Deezer
      fallback) → dedupe → POST relay; clears after N misses. --once /
      --dry-run flags. test_listener.py: 9 cases, passing. End-to-end
      extract→POST→relay GET verified locally.)
- [x] MainScene polls the relay and shows album art (components/
      RelayPoller.xml/.brs Task GETs /now-playing every
      poll_interval_seconds; MainScene.brs shows a centered 1080²
      Poster of artUrl, or a status Label when idle/unreachable/load
      fails). manifest bumped to 0.2; relay_url + poll_interval_seconds
      are manifest keys read via roAppInfo. Not yet run on hardware.
- [ ] Sideload v0.2 and verify against a live relay on the Roku
- [ ] Deploy relay + listener on the tablet via Termux (leave running)

## Key decisions made so far
- The Roku channel is code-complete: RelayPoller Task polls the relay,
  MainScene swaps between the album-art Poster and a status Label. All
  three code pieces (channel, relay, listener) are built and unit-tested;
  what's left is device deployment + hardware testing.
- AudD chosen over alternatives for recognition (300 free requests,
  ~$5/1000 after).
- Windows dev environment: Git Bash + VS Code, `code --wait` set as
  Git's default editor. Git Bash has no `zip`/`7z` (hence package.ps1).
  Python 3.12 installed via winget (Python.Python.3.12) at
  %LOCALAPPDATA%\Programs\Python\Python312 — not on PATH in Git Bash;
  invoke by full path or from PowerShell.
- Relay API contract: POST fields artist/title/album/artUrl/source
  (strings, empties dropped); server stamps updatedAt (unix seconds).
  POST {} or {"clear": true} clears. Roku GETs {} when nothing is set.

## Next step when resuming
All code is written and unit-tested. Remaining work is deployment:
1. Set relay_url in roku-channel/manifest to the tablet's LAN IP,
   run roku-channel/package.ps1, sideload the zip, confirm it shows
   "Waiting for music..." then real art once the relay has a record.
2. On the tablet: install Termux + Termux:API (+ the F-Droid Termux:API
   app, mic permission granted), copy tablet-listener/.env.example to
   .env with the AudD token, run relay.py and listener.py (see each
   README). Keep the tablet plugged in.
3. Play a record and confirm art appears on the TV within a poll cycle.