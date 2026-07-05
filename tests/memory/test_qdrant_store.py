"""Tests for QdrantMemoryStore."""

import uuid
from datetime import datetime
from unittest.mock import Mock

import pytest
from memory.qdrant_store import QdrantMemoryStore

from contracts import MemoryEntry, MemoryScope


@pytest.fixture
def mock_qdrant_client():
    """Create a mock Qdrant client."""
    client = Mock()
    client.get_collections.return_value = Mock(collections=[])
    client.create_collection.return_value = None
    client.upsert.return_value = None
    client.delete.return_value = None
    client.search.return_value = []
    client.scroll.return_value = ([], None)
    return client


@pytest.fixture
def memory_store(mock_qdrant_client):
    """Create a QdrantMemoryStore with mocked client."""
    with pytest.MonkeyPatch.context() as m:
        m.setattr(
            "memory.qdrant_store.QdrantClient",
            lambda url: mock_qdrant_client,
        )
        store = QdrantMemoryStore()
        store.client = mock_qdrant_client
        return store


@pytest.mark.asyncio
async def test_store_memory(memory_store, mock_qdrant_client):
    """Test storing a memory entry."""
    entry = MemoryEntry(
        id=str(uuid.uuid4()),
        content="Test memory content",
        scope=MemoryScope.GLOBAL,
        created_at=datetime.utcnow(),
        metadata={"test": "data"},
    )

    await memory_store.store(entry)

    mock_qdrant_client.upsert.assert_called_once()
    call_args = mock_qdrant_client.upsert.call_args
    assert call_args.kwargs["collection_name"] == "memory"
    assert len(call_args.kwargs["points"]) == 1
    point = call_args.kwargs["points"][0]
    assert point.id == entry.id
    assert point.payload["content"] == entry.content
    assert point.payload["scope"] == "global"


@pytest.mark.asyncio
async def test_recall_memories(memory_store, mock_qdrant_client):
    """Test recalling memories."""
    # Mock search results
    mock_point = Mock()
    mock_point.id = "test-id"
    mock_point.payload = {
        "content": "Test content",
        "scope": "global",
        "project_id": None,
        "session_id": None,
        "created_at": datetime.utcnow().isoformat(),
        "metadata": {},
    }
    mock_qdrant_client.search.return_value = [mock_point]

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
async def test_recall_with_project_filter(memory_store, mock_qdrant_client):
    """Test recalling memories with project filter."""
    mock_qdrant_client.search.return_value = []

    await memory_store.recall(
        query="test",
        scope=MemoryScope.PROJECT,
        project_id="proj-123",
    )

    call_args = mock_qdrant_client.search.call_args
    assert call_args.kwargs["query_filter"]["scope"] == "project"
    assert call_args.kwargs["query_filter"]["project_id"] == "proj-123"


@pytest.mark.asyncio
async def test_forget_memory(memory_store, mock_qdrant_client):
    """Test forgetting a memory."""
    memory_id = str(uuid.uuid4())

    await memory_store.forget(memory_id)

    mock_qdrant_client.delete.assert_called_once()
    call_args = mock_qdrant_client.delete.call_args
    assert call_args.kwargs["collection_name"] == "memory"
    assert memory_id in call_args.kwargs["points_selector"]


@pytest.mark.asyncio
async def test_list_memories(memory_store, mock_qdrant_client):
    """Test listing memories."""
    mock_point = Mock()
    mock_point.id = "test-id"
    mock_point.payload = {
        "content": "Test content",
        "scope": "global",
        "project_id": None,
        "session_id": None,
        "created_at": datetime.utcnow().isoformat(),
        "metadata": {},
    }
    mock_qdrant_client.scroll.return_value = ([mock_point], None)

    results = await memory_store.list_memories(limit=100)

    assert len(results) == 1
    assert results[0].id == "test-id"


@pytest.mark.asyncio
async def test_list_memories_with_scope_filter(memory_store, mock_qdrant_client):
    """Test listing memories with scope filter."""
    mock_qdrant_client.scroll.return_value = ([], None)

    await memory_store.list_memories(scope=MemoryScope.PROJECT)

    call_args = mock_qdrant_client.scroll.call_args
    assert call_args.kwargs["scroll_filter"]["scope"] == "project"
