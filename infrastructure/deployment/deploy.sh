#!/usr/bin/env bash
# Deploy script for AI Workstation Platform
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    log_info "Prerequisites check passed"
}

# Load environment variables
load_env() {
    if [ -f "$SCRIPT_DIR/../compose/.env" ]; then
        log_info "Loading environment from .env file"
        export $(grep -v '^#' "$SCRIPT_DIR/../compose/.env" | xargs)
    else
        log_warn "No .env file found, using defaults"
    fi
}

# Build images
build_images() {
    log_info "Building Docker images..."
    cd "$PROJECT_ROOT"
    
    docker compose -f infrastructure/compose/docker-compose.prod.yml build
    
    log_info "Images built successfully"
}

# Start services
start_services() {
    log_info "Starting services..."
    cd "$PROJECT_ROOT"
    
    docker compose -f infrastructure/compose/docker-compose.prod.yml up -d
    
    log_info "Services started successfully"
}

# Wait for services to be healthy
wait_for_services() {
    log_info "Waiting for services to be healthy..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -sf http://localhost:${GATEWAY_PORT:-8000}/health > /dev/null 2>&1; then
            log_info "Gateway is healthy"
            break
        fi
        
        log_warn "Attempt $attempt/$max_attempts: Gateway not ready yet..."
        sleep 2
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_error "Gateway failed to become healthy"
        exit 1
    fi
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    cd "$PROJECT_ROOT"
    
    docker compose -f infrastructure/compose/docker-compose.prod.yml exec gateway \
        alembic upgrade head
    
    log_info "Migrations completed"
}

# Main deployment function
deploy() {
    log_info "Starting deployment..."
    
    check_prerequisites
    load_env
    build_images
    start_services
    wait_for_services
    run_migrations
    
    log_info "Deployment completed successfully!"
    log_info "Gateway: http://localhost:${GATEWAY_PORT:-8000}"
    log_info "API Docs: http://localhost:${GATEWAY_PORT:-8000}/docs"
    log_info "Grafana: http://localhost:${GRAFANA_PORT:-3000}"
}

# Stop services
stop() {
    log_info "Stopping services..."
    cd "$PROJECT_ROOT"
    
    docker compose -f infrastructure/compose/docker-compose.prod.yml down
    
    log_info "Services stopped"
}

# Restart services
restart() {
    stop
    deploy
}

# Show status
status() {
    cd "$PROJECT_ROOT"
    docker compose -f infrastructure/compose/docker-compose.prod.yml ps
}

# Show logs
logs() {
    cd "$PROJECT_ROOT"
    docker compose -f infrastructure/compose/docker-compose.prod.yml logs -f "${@}"
}

# Main
case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        shift
        logs "$@"
        ;;
    *)
        echo "Usage: $0 {deploy|stop|restart|status|logs [service]}"
        exit 1
        ;;
esac
