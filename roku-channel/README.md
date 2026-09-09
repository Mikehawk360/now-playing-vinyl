# roku-channel

BrightScript / SceneGraph app for the Roku Express. Displays a fullscreen
black screen with a centered placeholder label. Later it will poll the
relay for now-playing JSON and show the album art fullscreen.

## Layout

```
manifest                     channel metadata
source/main.brs              entry point, creates the SceneGraph screen
components/MainScene.xml      fullscreen background + centered label
components/MainScene.brs      scene logic (polling loop goes here later)
```

## Package and sideload

The Roku web installer expects a .zip whose root contains `manifest`
(not a wrapper folder). From this directory:

```bash
./package.sh
```

That writes `now-playing-vinyl.zip`. Then:

1. Open `http://<roku-ip>/` in a browser (user `rokudev`, the dev
   password set when Developer Mode was enabled).
2. Upload `now-playing-vinyl.zip` and click **Replace**.
3. The channel launches automatically; you should see
   "Hello World - it's alive!" centered on a black screen.
