#!/usr/bin/env bash
# Start a listening session: relay + tablet listener in the background,
# plus a wake lock so Android doesn't suspend Termux mid-song.
#
# Usage: bash start.sh   (from anywhere - it cd's to the repo root)
# Stop:  bash stop.sh
set -euo pipefail
cd "$(dirname "$0")"

mkdir -p .run
RELAY_PID=.run/relay.pid
LISTENER_PID=.run/listener.pid

running() { [ -f "$1" ] && kill -0 "$(cat "$1")" 2>/dev/null; }

if running "$RELAY_PID"; then
    echo "relay already running (pid $(cat "$RELAY_PID"))"
else
    nohup python3 relay/relay.py > relay/relay.log 2>&1 &
    echo $! > "$RELAY_PID"
    echo "relay started (pid $!) - log: relay/relay.log"
fi

if running "$LISTENER_PID"; then
    echo "listener already running (pid $(cat "$LISTENER_PID"))"
else
    sleep 1  # give the relay a moment to bind its port
    nohup python3 tablet-listener/listener.py > tablet-listener/listener.log 2>&1 &
    echo $! > "$LISTENER_PID"
    echo "listener started (pid $!) - log: tablet-listener/listener.log"
fi

if command -v termux-wake-lock >/dev/null 2>&1; then
    termux-wake-lock
    echo "wake lock acquired"
fi

echo "listening. Run 'bash stop.sh' when you're done with the record(s)."
