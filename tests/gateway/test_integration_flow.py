"""E2E: simula el flujo Terax → gateway → modelo."""

import os

import httpx
import pytest

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000")

_HAS_CHAT_KEYS = bool(
    os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or os.getenv("GEMINI_API_KEY")
)


@pytest.mark.skipif(not _HAS_CHAT_KEYS, reason="No API keys configured")
def test_full_chat_roundtrip():
    """Simula lo que Terax hace cuando envia un chat request."""
    resp = httpx.post(
        f"{GATEWAY_URL}/v1/chat/completions",
        json={
            "model": os.getenv("DEFAULT_MODEL", "claude-sonnet-4-20250514"),
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


@pytest.mark.live
def test_memory_recall_endpoint():
    """Simula el flujo de inyeccion de memoria de Terax."""
    resp = httpx.post(
        f"{GATEWAY_URL}/memory/recall",
        params={"query": "test query", "scope": "project", "limit": 5},
        timeout=10,
    )
    assert resp.status_code == 200
    assert "memories" in resp.json()


@pytest.mark.live
def test_openai_models_compatibility():
    """Verifica compatibilidad OpenAI SDK para consumers del gateway."""
    resp = httpx.get(f"{GATEWAY_URL}/v1/models", timeout=5)
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("object") == "list"
    assert isinstance(body.get("data"), list)
