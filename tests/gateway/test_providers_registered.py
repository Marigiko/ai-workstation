"""Tests that at least one provider is registered (requires valid API keys)."""

import httpx

GATEWAY_URL = "http://localhost:8000"


def test_at_least_one_provider_registered():
    resp = httpx.get(f"{GATEWAY_URL}/v1/models", timeout=5)
    body = resp.json()
    assert len(body.get("data", [])) >= 1, (
        f"No providers registered. Check API keys in .env. Got: {body}"
    )
