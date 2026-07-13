"""Tests that infrastructure services are reachable (requires docker-compose up)."""

import subprocess

import httpx
import psycopg2
import redis


def test_postgres_reachable():
    conn = psycopg2.connect(
        "postgresql://ai_workstation:ai_workstation_dev@localhost:5432/ai_workstation"
    )
    assert conn.poll() == psycopg2.extensions.POLL_OK
    conn.close()


def test_redis_reachable():
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    assert r.ping()


def test_qdrant_reachable():
    resp = httpx.get("http://localhost:6333/health", timeout=5)
    assert resp.status_code == 200


def test_gateway_container_running():
    result = subprocess.run(
        [
            "docker", "ps",
            "--filter", "name=ai-workstation-gateway",
            "--format", "{{.Status}}",
        ],
        capture_output=True, text=True,
    )
    status = result.stdout.strip()
    assert "healthy" in status.lower() or "up" in status.lower(), \
        f"Gateway container not running. Status: '{status}'"
