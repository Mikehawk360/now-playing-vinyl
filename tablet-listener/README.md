# tablet-listener

Runs on the Lenovo TB3-850F tablet (2GB RAM, Android, Termux). On an
interval: records a short audio clip, sends it to the AudD API
(https://audd.io) for recognition, and POSTs the resulting
artist/title/album-art URL to the relay.

Not built yet.

## Notes

- AudD: 300 free requests, ~$5/1000 after. API token goes in `.env`
  (gitignored), never committed.
- Keep the poll interval conservative to stay within quota.
