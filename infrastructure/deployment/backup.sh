#!/usr/bin/env bash
# Backup script for AI Workstation databases
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup PostgreSQL
backup_postgres() {
    log_info "Backing up PostgreSQL database..."
    
    local backup_file="$BACKUP_DIR/postgres_${TIMESTAMP}.sql.gz"
    
    docker exec ai-workstation-postgres \
        pg_dump -U "${POSTGRES_USER:-ai_workstation}" \
        "${POSTGRES_DB:-ai_workstation}" | gzip > "$backup_file"
    
    log_info "PostgreSQL backup created: $backup_file"
}

# Backup Qdrant collections
backup_qdrant() {
    log_info "Backing up Qdrant collections..."
    
    local backup_file="$BACKUP_DIR/qdrant_${TIMESTAMP}.tar.gz"
    
    docker exec ai-workstation-qdrant \
        tar czf - /qdrant/storage | cat > "$backup_file"
    
    log_info "Qdrant backup created: $backup_file"
}

# Backup Redis
backup_redis() {
    log_info "Backing up Redis data..."
    
    local backup_file="$BACKUP_DIR/redis_${TIMESTAMP}.rdb"
    
    # Trigger Redis BGSAVE
    docker exec ai-workstation-redis redis-cli BGSAVE > /dev/null 2>&1
    
    # Wait for save to complete
    sleep 2
    
    # Copy RDB file
    docker cp ai-workstation-redis:/data/dump.rdb "$backup_file"
    
    log_info "Redis backup created: $backup_file"
}

# Cleanup old backups
cleanup_old_backups() {
    local retention_days="${BACKUP_RETENTION_DAYS:-7}"
    
    log_info "Cleaning up backups older than $retention_days days..."
    
    find "$BACKUP_DIR" -type f -mtime "+$retention_days" -delete
    
    log_info "Cleanup completed"
}

# Main
case "${1:-all}" in
    postgres)
        backup_postgres
        ;;
    qdrant)
        backup_qdrant
        ;;
    redis)
        backup_redis
        ;;
    all)
        backup_postgres
        backup_qdrant
        backup_redis
        cleanup_old_backups
        ;;
    cleanup)
        cleanup_old_backups
        ;;
    *)
        echo "Usage: $0 {all|postgres|qdrant|redis|cleanup}"
        exit 1
        ;;
esac

log_info "Backup completed successfully!"
