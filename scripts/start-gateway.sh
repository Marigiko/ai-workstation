#!/usr/bin/env bash
set -euo pipefail
# Start ai-workstation gateway with correct database
# Run from project root: ./scripts/start-gateway.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

export DATABASE_URL="postgresql+asyncpg://awe:${AWE_PG_PASSWORD:?set AWE_PG_PASSWORD in ~/.config/awe/env/mcp.env}@localhost:5433/ai_workstation_gateway"
export REDIS_URL="redis://localhost:6380/0"
export QDRANT_URL="http://localhost:6335"

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

echo "Starting AI Workstation Gateway..."
echo "  Database: $(printf '%s' "$DATABASE_URL" | sed -E 's#://([^:/@]+):[^@]*@#://\1:***@#')"
echo "  Redis: $REDIS_URL"
echo "  Qdrant: $QDRANT_URL"
echo ""

uv run uvicorn gateway.main:app --host "$GATEWAY_HOST" --port 8000 --app-dir apps/gateway/src
