#!/usr/bin/env bash
set -euo pipefail
# Start ai-workstation gateway as a persistent background daemon
# Uses setsid+nohup double-detachment to survive shell exit

export PATH="$HOME/.micromamba/bin:$HOME/.local/bin:$HOME/.nvm/versions/node/v24.18.0/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

GATEWAY_HOST="${GATEWAY_HOST:-127.0.0.1}"
case "$GATEWAY_HOST" in
    127.0.0.1|localhost|::1) ;;
    *)
        if [ -z "${API_KEYS:-}" ]; then
            echo "ERROR: binding GATEWAY_HOST='$GATEWAY_HOST' without API_KEYS would expose the gateway unauthenticated." >&2
            echo "Set API_KEYS or use GATEWAY_HOST=127.0.0.1." >&2
            exit 1
        fi
        ;;
esac

LOG_FILE="/tmp/gateway.log"
PID_FILE="/tmp/gateway.pid"

# Kill existing
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE" 2>/dev/null || echo "")
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Stopping existing gateway (PID $OLD_PID)..."
        kill "$OLD_PID" 2>/dev/null || true
        sleep 2
    fi
    rm -f "$PID_FILE"
fi

echo "Starting AI Workstation Gateway..."

# Double-detach: setsid + nohup so the process survives shell exit
(setsid nohup .venv/bin/uvicorn gateway.main:app \
    --host "$GATEWAY_HOST" \
    --port 8000 \
    --app-dir apps/gateway/src \
    > "$LOG_FILE" 2>&1 < /dev/null &)

# Wait for startup
for i in $(seq 1 30); do
    sleep 2
    if ss -tlnp 2>/dev/null | grep -q ':8000 '; then
        GATEWAY_PID=$(pgrep -f "uvicorn gateway.main" | head -1)
        echo "$GATEWAY_PID" > "$PID_FILE"
        echo "Gateway started successfully!"
        echo "  PID: $GATEWAY_PID"
        echo "  URL: http://localhost:8000"
        echo "  Health: $(curl -s http://localhost:8000/health 2>&1 || echo 'N/A')"
        echo "  Logs: $LOG_FILE"
        exit 0
    fi
done

echo "Gateway may still be starting."
echo "Check logs: tail -f $LOG_FILE"
echo "Check port: ss -tlnp | grep 8000"
