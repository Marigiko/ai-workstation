"""Tests for API key authentication middleware."""

import os

from fastapi.testclient import TestClient

from gateway.main import create_app


def test_health_public_without_key():
    """Health endpoint is always public."""
    original = os.environ.get("API_KEYS")
    os.environ.pop("API_KEYS", None)
    app = create_app()
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    if original is not None:
        os.environ["API_KEYS"] = original


def test_root_public_without_key():
    """Root endpoint is always public."""
    original = os.environ.get("API_KEYS")
    os.environ.pop("API_KEYS", None)
    app = create_app()
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    if original is not None:
        os.environ["API_KEYS"] = original


def test_chat_without_key_when_not_configured():
    """If API_KEYS not set, chat should not return 401."""
    original = os.environ.get("API_KEYS")
    os.environ.pop("API_KEYS", None)
    app = create_app()
    client = TestClient(app)
    resp = client.post("/chat", json={"messages": [{"role": "user", "content": "hi"}]})
    # Should be 200 or 500 (no providers), NOT 401
    assert resp.status_code != 401
    if original is not None:
        os.environ["API_KEYS"] = original


def test_chat_requires_key_when_configured():
    """If API_KEYS is set, requests without key must be 401."""
    os.environ["API_KEYS"] = "test-key-123"
    try:
        app = create_app()
        client = TestClient(app)
        resp = client.post("/chat", json={"messages": [{"role": "user", "content": "hi"}]})
        assert resp.status_code == 401
    finally:
        os.environ.pop("API_KEYS", None)


def test_docs_requires_key_when_configured():
    """If API_KEYS is set, /docs is no longer public and returns 401 without a key."""
    os.environ["API_KEYS"] = "test-key-123"
    try:
        app = create_app()
        client = TestClient(app)
        resp = client.get("/docs")
        assert resp.status_code == 401
        resp = client.get("/health")
        assert resp.status_code == 200
    finally:
        os.environ.pop("API_KEYS", None)
