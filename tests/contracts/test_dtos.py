"""Tests for contracts package."""

from contracts import (
    CompletionRequest,
    CompletionResponse,
    ContextChunk,
    MemoryEntry,
    MemoryScope,
    Message,
    Provider,
    Role,
)


def test_message_creation():
    """Test Message DTO creation."""
    msg = Message(role=Role.USER, content="Hello")
    assert msg.role == Role.USER
    assert msg.content == "Hello"


def test_completion_request():
    """Test CompletionRequest DTO."""
    messages = [Message(role=Role.USER, content="Test")]
    request = CompletionRequest(messages=messages, temperature=0.5)
    assert len(request.messages) == 1
    assert request.temperature == 0.5
    assert request.stream is False


def test_completion_response():
    """Test CompletionResponse DTO."""
    response = CompletionResponse(
        id="test-123",
        provider="test-provider",
        model="test-model",
        content="Response content",
        usage={"prompt_tokens": 10, "completion_tokens": 20},
    )
    assert response.id == "test-123"
    assert response.provider == "test-provider"
    assert response.usage["prompt_tokens"] == 10


def test_context_chunk():
    """Test ContextChunk DTO."""
    chunk = ContextChunk(
        id="chunk-1",
        content="Some content",
        source="file.py",
        score=0.95,
    )
    assert chunk.score == 0.95


def test_memory_entry():
    """Test MemoryEntry DTO."""
    entry = MemoryEntry(
        id="mem-1",
        content="Important info",
        scope=MemoryScope.PROJECT,
        project_id="proj-1",
    )
    assert entry.scope == MemoryScope.PROJECT
    assert entry.project_id == "proj-1"


def test_provider_protocol():
    """Test that Provider is a Protocol."""
    assert hasattr(Provider, "complete")
    assert hasattr(Provider, "stream")
    assert hasattr(Provider, "capabilities")
    assert hasattr(Provider, "health")
