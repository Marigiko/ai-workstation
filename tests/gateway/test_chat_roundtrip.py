"""End-to-end chat roundtrip test (requires gateway + valid API keys)."""

import httpx

GATEWAY_URL = "http://localhost:8000"


def test_full_chat_roundtrip():
    """Simulates what Terax does when sending a chat request."""
    resp = httpx.post(
        f"{GATEWAY_URL}/v1/chat/completions",
        json={
            "model": "claude-sonnet-4-20250514",
            "messages": [{"role": "user", "content": "Say hello in 3 words."}],
            "max_tokens": 50,
        },
        timeout=60,
    )
    assert resp.status_code == 200, f"Chat failed: {resp.status_code} {resp.text[:200]}"
    body = resp.json()
    assert "choices" in body
    assert len(body["choices"]) > 0
    assert "content" in body["choices"][0]["message"]
