"""Tests against a live running gateway (requires docker-compose up)."""

import httpx

GATEWAY_URL = "http://localhost:8000"


def test_health_endpoint():
    resp = httpx.get(f"{GATEWAY_URL}/health", timeout=5)
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_openai_models_endpoint():
    resp = httpx.get(f"{GATEWAY_URL}/v1/models", timeout=5)
    assert resp.status_code == 200
    assert "data" in resp.json()


def test_chat_endpoint_reachable():
    resp = httpx.post(
        f"{GATEWAY_URL}/chat",
        json={"messages": [{"role": "user", "content": "ping"}]},
        timeout=30,
    )
    assert resp.status_code != 500


def test_openai_chat_completions_reachable():
    resp = httpx.post(
        f"{GATEWAY_URL}/v1/chat/completions",
        json={
            "model": "claude-sonnet-4-20250514",
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 10,
        },
        timeout=60,
    )
    assert resp.status_code != 500
