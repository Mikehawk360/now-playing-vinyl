#!/usr/bin/env bash
# Stop the relay + listener started by start.sh, and release the wake lock.
#
# Usage: bash stop.sh
set -uo pipefail
cd "$(dirname "$0")"

for name in relay listener; do
    pidfile=".run/${name}.pid"
    if [ -f "$pidfile" ]; then
        pid="$(cat "$pidfile")"
        if kill "$pid" 2>/dev/null; then
            echo "stopped $name (pid $pid)"
        else
            echo "$name (pid $pid) was not running"
        fi
        rm -f "$pidfile"
    else
        echo "$name was not running"
    fi
done

if command -v termux-wake-unlock >/dev/null 2>&1; then
    termux-wake-unlock
    echo "wake lock released"
fi
