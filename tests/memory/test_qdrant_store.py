"""Tests for QdrantMemoryStore."""

import json
import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import httpx
import pytest
from memory.qdrant_store import QdrantMemoryStore

from contracts import MemoryEntry, MemoryScope


def _ok_response(data, status_code=200):
    """Build an httpx.Response with a properly set request attribute."""
    req = httpx.Request("GET", "http://localhost:6333/fake")
    return httpx.Response(status_code, request=req, json=data)


@pytest.fixture
def httpx_mock():
    """Mock httpx.Client for QdrantMemoryStore tests."""
    with patch("httpx.Client") as mock_cls:
        client = MagicMock()
        mock_cls.return_value = client

        client.get.return_value = _ok_response({"result": {"collections": []}})
        client.put.return_value = _ok_response({"result": {"status": "ok"}})
        client.post.return_value = _ok_response({"result": []})
        yield client


@pytest.fixture
def memory_store(httpx_mock):
    """Create a QdrantMemoryStore with mocked HTTP."""
    with patch("memory.qdrant_store.QdrantClient", create=True):
        store = QdrantMemoryStore(qdrant_url="http://localhost:6333")
        store._http = httpx_mock
        return store


@pytest.mark.asyncio
async def test_store_memory(memory_store, httpx_mock):
    """Test storing a memory entry."""
    entry = MemoryEntry(
        id=str(uuid.uuid4()),
        content="Test memory content",
        scope=MemoryScope.GLOBAL,
        created_at=datetime.now(UTC),
        metadata={"test": "data"},
    )

    await memory_store.store(entry)

    # Ensure upsert was called via REST PUT
    put_calls = [c for c in httpx_mock.put.call_args_list if "/points" in c.args[0]]
    assert len(put_calls) >= 1
    body = put_calls[0].kwargs.get("json") or json.loads(put_calls[0].args[1])
    assert len(body["points"]) == 1


@pytest.mark.asyncio
async def test_recall_memories(memory_store, httpx_mock):
    """Test recalling memories."""
    mock_hit = {
        "id": "test-id",
        "payload": {
            "content": "Test content",
            "scope": "global",
            "project_id": None,
            "session_id": None,
            "created_at": datetime.now(UTC).isoformat(),
            "metadata": {},
        },
    }
    httpx_mock.post.return_value = _ok_response({"result": [mock_hit]})

    results = await memory_store.recall(
        query="test query",
        scope=MemoryScope.GLOBAL,
        limit=10,
    )

    assert len(results) == 1
    assert results[0].id == "test-id"
    assert results[0].content == "Test content"
    assert results[0].scope == MemoryScope.GLOBAL


@pytest.mark.asyncio
async def test_recall_with_project_filter(memory_store, httpx_mock):
    """Test recalling memories with project filter."""
    httpx_mock.post.return_value = _ok_response({"result": []})

    await memory_store.recall(
        query="test",
        scope=MemoryScope.PROJECT,
        project_id="proj-123",
    )

    post_calls = [c for c in httpx_mock.post.call_args_list if "/search" in c.args[0]]
    assert len(post_calls) >= 1
    body = post_calls[0].kwargs.get("json")
    assert body["filter"]["must"][0] == {"key": "scope", "match": {"value": "project"}}
    assert body["filter"]["must"][1] == {"key": "project_id", "match": {"value": "proj-123"}}


@pytest.mark.asyncio
async def test_forget_memory(memory_store, httpx_mock):
    """Test forgetting a memory."""
    memory_id = str(uuid.uuid4())

    await memory_store.forget(memory_id)

    post_calls = [c for c in httpx_mock.post.call_args_list if "/delete" in c.args[0]]
    assert len(post_calls) >= 1
    body = post_calls[0].kwargs.get("json")
    assert memory_id in body["points"]


@pytest.mark.asyncio
async def test_list_memories(memory_store, httpx_mock):
    """Test listing memories."""
    mock_hit = {
        "id": "test-id",
        "payload": {
            "content": "Test content",
            "scope": "global",
            "project_id": None,
            "session_id": None,
            "created_at": datetime.now(UTC).isoformat(),
            "metadata": {},
        },
    }
    httpx_mock.post.return_value = _ok_response({"result": {"points": [mock_hit]}})

    results = await memory_store.list_memories(limit=100)

    assert len(results) == 1
    assert results[0].id == "test-id"


@pytest.mark.asyncio
async def test_list_memories_with_scope_filter(memory_store, httpx_mock):
    """Test listing memories with scope filter."""
    httpx_mock.post.return_value = _ok_response({"result": {"points": []}})

    await memory_store.list_memories(scope=MemoryScope.PROJECT)

    post_calls = [c for c in httpx_mock.post.call_args_list if "/scroll" in c.args[0]]
    assert len(post_calls) >= 1
    body = post_calls[0].kwargs.get("json")
    assert body["filter"]["must"][0] == {"key": "scope", "match": {"value": "project"}}
