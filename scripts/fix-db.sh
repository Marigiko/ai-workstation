#!/usr/bin/env bash
set -euo pipefail
# Fix database schema for ai-workstation gateway
# Run this once before starting the gateway

echo "Fixing database schema..."

# Drop and recreate the workspace database with correct schema
docker exec awe-postgresql psql -U awe -c "DROP DATABASE IF EXISTS workspace;" 2>/dev/null || true
docker exec awe-postgresql psql -U awe -c "CREATE DATABASE workspace OWNER awe;" 2>/dev/null || true

echo "Database 'workspace' recreated with clean schema."
echo "You can now start the gateway with: ./scripts/start-gateway.sh"
