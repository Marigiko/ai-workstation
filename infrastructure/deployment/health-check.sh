#!/usr/bin/env bash
# Health check script for AI Workstation services
set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

GATEWAY_PORT="${GATEWAY_PORT:-8000}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
REDIS_PORT="${REDIS_PORT:-6379}"
QDRANT_PORT="${QDRANT_PORT:-6333}"
PROMETHEUS_PORT="${PROMETHEUS_PORT:-9090}"
GRAFANA_PORT="${GRAFANA_PORT:-3000}"

check_service() {
    local name=$1
    local url=$2
    
    if curl -sf "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name is healthy"
        return 0
    else
        echo -e "${RED}✗${NC} $name is not responding"
        return 1
    fi
}

check_tcp() {
    local name=$1
    local port=$2
    
    if nc -z localhost "$port" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $name is listening on port $port"
        return 0
    else
        echo -e "${RED}✗${NC} $name is not listening on port $port"
        return 1
    fi
}

echo "=========================================="
echo "AI Workstation Health Check"
echo "=========================================="
echo ""

# Check HTTP services
echo "HTTP Services:"
check_service "Gateway" "http://localhost:$GATEWAY_PORT/health" || true
check_service "Prometheus" "http://localhost:$PROMETHEUS_PORT/-/healthy" || true
check_service "Grafana" "http://localhost:$GRAFANA_PORT/api/health" || true
echo ""

# Check TCP services
echo "TCP Services:"
check_tcp "PostgreSQL" "$POSTGRES_PORT" || true
check_tcp "Redis" "$REDIS_PORT" || true
check_tcp "Qdrant" "$QDRANT_PORT" || true
echo ""

# Check Docker containers
echo "Docker Containers:"
docker ps --filter "name=ai-workstation" --format "table {{.Names}}\t{{.Status}}" | grep -q "ai-workstation" && \
    echo -e "${GREEN}✓${NC} All containers are running" || \
    echo -e "${RED}✗${NC} Some containers are not running"
echo ""

echo "=========================================="
echo "Health check completed"
echo "=========================================="
