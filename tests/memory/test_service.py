"""Tests for MemoryService."""

from unittest.mock import AsyncMock, Mock

import pytest
from memory.service import MemoryService

from contracts import MemoryEntry, MemoryScope


@pytest.fixture
def mock_store():
    """Create a mock memory store."""
    store = Mock()
    store.store = AsyncMock()
    store.recall = AsyncMock(return_value=[])
    store.forget = AsyncMock()
    store.list_memories = AsyncMock(return_value=[])
    return store


@pytest.fixture
def memory_service(mock_store):
    """Create a MemoryService with mocked store."""
    return MemoryService(mock_store)


@pytest.mark.asyncio
async def test_remember_global(memory_service, mock_store):
    """Test remembering a global memory."""
    entry = await memory_service.remember(
        content="Test global memory",
        scope=MemoryScope.GLOBAL,
    )

    assert entry.content == "Test global memory"
    assert entry.scope == MemoryScope.GLOBAL
    assert entry.id is not None
    mock_store.store.assert_called_once_with(entry)


@pytest.mark.asyncio
async def test_remember_project(memory_service, mock_store):
    """Test remembering a project-scoped memory."""
    entry = await memory_service.remember(
        content="Test project memory",
        scope=MemoryScope.PROJECT,
        project_id="proj-123",
    )

    assert entry.scope == MemoryScope.PROJECT
    assert entry.project_id == "proj-123"
    mock_store.store.assert_called_once()


@pytest.mark.asyncio
async def test_remember_project_without_id_raises(memory_service):
    """Test that remembering project memory without project_id raises error."""
    with pytest.raises(ValueError, match="project_id is required"):
        await memory_service.remember(
            content="Test",
            scope=MemoryScope.PROJECT,
        )


@pytest.mark.asyncio
async def test_remember_session(memory_service, mock_store):
    """Test remembering a session-scoped memory."""
    entry = await memory_service.remember(
        content="Test session memory",
        scope=MemoryScope.SESSION,
        session_id="sess-456",
    )

    assert entry.scope == MemoryScope.SESSION
    assert entry.session_id == "sess-456"
    mock_store.store.assert_called_once()


@pytest.mark.asyncio
async def test_remember_session_without_id_raises(memory_service):
    """Test that remembering session memory without session_id raises error."""
    with pytest.raises(ValueError, match="session_id is required"):
        await memory_service.remember(
            content="Test",
            scope=MemoryScope.SESSION,
        )


@pytest.mark.asyncio
async def test_recall_memories(memory_service, mock_store):
    """Test recalling memories."""
    mock_entry = MemoryEntry(
        id="test-id",
        content="Test content",
        scope=MemoryScope.GLOBAL,
    )
    mock_store.recall.return_value = [mock_entry]

    results = await memory_service.recall_memories(
        query="test query",
        scope=MemoryScope.GLOBAL,
        limit=5,
    )

    assert len(results) == 1
    assert results[0].id == "test-id"
    mock_store.recall.assert_called_once_with(
        query="test query",
        scope=MemoryScope.GLOBAL,
        limit=5,
        project_id=None,
        session_id=None,
    )


@pytest.mark.asyncio
async def test_forget_memory(memory_service, mock_store):
    """Test forgetting a memory."""
    await memory_service.forget_memory("test-id")

    mock_store.forget.assert_called_once_with("test-id")


@pytest.mark.asyncio
async def test_list_memories(memory_service, mock_store):
    """Test listing memories."""
    mock_entry = MemoryEntry(
        id="test-id",
        content="Test content",
        scope=MemoryScope.GLOBAL,
    )
    mock_store.list_memories.return_value = [mock_entry]

    results = await memory_service.list_memories(
        scope=MemoryScope.GLOBAL,
        limit=50,
    )

    assert len(results) == 1
    mock_store.list_memories.assert_called_once_with(
        scope=MemoryScope.GLOBAL,
        project_id=None,
        session_id=None,
        limit=50,
    )


@pytest.mark.asyncio
async def test_get_memory_found(memory_service, mock_store):
    """Test getting a memory that exists."""
    mock_entry = MemoryEntry(
        id="test-id",
        content="Test content",
        scope=MemoryScope.GLOBAL,
    )
    mock_store.list_memories.return_value = [mock_entry]

    result = await memory_service.get_memory("test-id")

    assert result is not None
    assert result.id == "test-id"


@pytest.mark.asyncio
async def test_get_memory_not_found(memory_service, mock_store):
    """Test getting a memory that doesn't exist."""
    mock_store.list_memories.return_value = []

    result = await memory_service.get_memory("nonexistent-id")

    assert result is None
