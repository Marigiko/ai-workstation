#!/usr/bin/env bash
set -euo pipefail
# Start ai-workstation gateway as a persistent background daemon
# Uses setsid+nohup double-detachment to survive shell exit

export PATH="$HOME/.micromamba/bin:$HOME/.local/bin:$HOME/.nvm/versions/node/v24.18.0/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

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
echo "  (litellm import takes ~25s on first start)"

# Double-detach: setsid + nohup so the process survives shell exit
(setsid nohup .venv/bin/uvicorn gateway.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --app-dir apps/gateway/src \
    > "$LOG_FILE" 2>&1 < /dev/null &)

# Wait for startup (litellm import is slow)
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

echo "Gateway may still be starting (litellm import can take up to 40s)."
echo "Check logs: tail -f $LOG_FILE"
echo "Check port: ss -tlnp | grep 8000"
