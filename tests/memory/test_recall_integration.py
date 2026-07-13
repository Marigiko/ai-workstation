"""Integracion: store → recall roundtrip."""

import httpx


async def test_recall_returns_relevant_memories():
    client = httpx.AsyncClient(base_url="http://localhost:8000")
    await client.post(
        "/memory/remember",
        json={
            "content": "Terax gateway integration usa port 8000",
            "scope": "project",
        },
    )
    resp = await client.post(
        "/memory/recall",
        json={"query": "gateway port", "scope": "project"},
    )
    data = resp.json()
    assert len(data["memories"]) >= 1


def test_remember_endpoint_exists():
    """Verifica que el endpoint de remember responde 200."""
    resp = httpx.post(
        "http://localhost:8000/memory/remember",
        json={"content": "test memory entry", "scope": "global"},
        timeout=10,
    )
    assert resp.status_code == 200
