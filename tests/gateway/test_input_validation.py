"""Tests for input validation on chat endpoint."""

import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://ai_workstation:ai_workstation_dev@localhost:5432/ai_workstation",
)

from fastapi.testclient import TestClient

from gateway.main import create_app


def _make_client_without_auth():
    original = os.environ.get("API_KEYS")
    os.environ.pop("API_KEYS", None)
    app = create_app()
    client = TestClient(app)
    return client, original


def _restore_key(original):
    if original is not None:
        os.environ["API_KEYS"] = original


def test_rejects_empty_messages():
    """Messages array vacio debe retornar 422."""
    client, original = _make_client_without_auth()
    try:
        resp = client.post("/chat", json={"messages": []})
        assert resp.status_code == 422
    finally:
        _restore_key(original)


def test_rejects_excessive_max_tokens():
    """max_tokens > 128000 debe retornar 422."""
    client, original = _make_client_without_auth()
    try:
        resp = client.post("/chat", json={
            "messages": [{"role": "user", "content": "hi"}],
            "max_tokens": 200000,
        })
        assert resp.status_code == 422
    finally:
        _restore_key(original)


def test_accepts_valid_request():
    """Request valido con 1 message debe pasar validacion."""
    client, original = _make_client_without_auth()
    try:
        resp = client.post("/chat", json={
            "messages": [{"role": "user", "content": "Hello"}],
        })
        # Puede ser 500 (no providers) o 200 — pero NO 422
        assert resp.status_code != 422
    finally:
        _restore_key(original)
