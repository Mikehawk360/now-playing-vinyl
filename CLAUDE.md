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
- [ ] Move the working Hello World files into roku-channel/
      (manifest, source/main.brs, components/MainScene.xml,
      components/MainScene.brs)
- [ ] Build the relay endpoint
- [ ] Build the tablet listener (AudD integration)
- [ ] Update MainScene.brs to poll the relay and display real album art
      instead of the placeholder text

## Key decisions made so far
- BrightScript label placeholder currently reads "Hello World - it's
  alive!" — this is what gets replaced with a Poster component showing
  album art.
- AudD chosen over alternatives for recognition (300 free requests,
  ~$5/1000 after).
- Windows dev environment: Git Bash + VS Code, `code --wait` set as
  Git's default editor.

## Next step when resuming
Finish placing the Roku channel files into roku-channel/, commit, then
start on the relay endpoint.