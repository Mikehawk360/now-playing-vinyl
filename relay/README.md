# relay

Small server that holds the "currently playing" JSON. The tablet listener
POSTs updates to it; the Roku channel GETs from it.

Planned to run on the Lenovo tablet via Termux so listening and hosting
live on one device.

## Planned API

```
POST /now-playing    body: { artist, title, album, artUrl }   (from the tablet)
GET  /now-playing     -> latest JSON, or {} if nothing playing (for the Roku)
```

Not built yet.
