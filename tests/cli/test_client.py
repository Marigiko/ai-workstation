"""Tests for CLI client."""

from unittest.mock import Mock, patch

import pytest

from cli.client import GatewayClient


@pytest.fixture
def mock_httpx_client():
    """Mock httpx client."""
    with patch("cli.client.httpx.Client") as mock_client:
        yield mock_client


@pytest.fixture
def client(mock_httpx_client):
    """Create CLI client with mocked HTTP."""
    return GatewayClient(base_url="http://test:8000")


def test_client_initialization(mock_httpx_client):
    """Test client initialization."""
    client = GatewayClient(base_url="http://test:8000")
    assert client.base_url == "http://test:8000"
    mock_httpx_client.assert_called_once()


def test_health_check(client, mock_httpx_client):
    """Test health check."""
    mock_response = Mock()
    mock_response.json.return_value = {"status": "healthy"}
    mock_httpx_client.return_value.get.return_value = mock_response

    result = client.health_check()

    assert result["status"] == "healthy"
    mock_httpx_client.return_value.get.assert_called_with("/health")


def test_chat(client, mock_httpx_client):
    """Test chat request."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "content": "Hello!",
        "usage": {"total_tokens": 10},
        "latency_ms": 100.0,
    }
    mock_httpx_client.return_value.post.return_value = mock_response

    messages = [{"role": "user", "content": "Hi"}]
    result = client.chat(messages)

    assert result["content"] == "Hello!"
    mock_httpx_client.return_value.post.assert_called_once()


def test_create_session(client, mock_httpx_client):
    """Test session creation."""
    mock_response = Mock()
    mock_response.json.return_value = {"id": "session-123", "title": "Test"}
    mock_httpx_client.return_value.post.return_value = mock_response

    result = client.create_session(title="Test")

    assert result["id"] == "session-123"
    mock_httpx_client.return_value.post.assert_called_once()


def test_list_sessions(client, mock_httpx_client):
    """Test listing sessions."""
    mock_response = Mock()
    mock_response.json.return_value = [
        {"id": "session-1", "title": "Test 1"},
        {"id": "session-2", "title": "Test 2"},
    ]
    mock_httpx_client.return_value.get.return_value = mock_response

    result = client.list_sessions(limit=10)

    assert len(result) == 2
    assert result[0]["id"] == "session-1"


def test_list_tools(client, mock_httpx_client):
    """Test listing tools."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "tools": [
            {"name": "filesystem", "description": "File operations"},
            {"name": "git", "description": "Git operations"},
        ]
    }
    mock_httpx_client.return_value.get.return_value = mock_response

    result = client.list_tools()

    assert len(result["tools"]) == 2
    assert result["tools"][0]["name"] == "filesystem"


def test_execute_tool(client, mock_httpx_client):
    """Test tool execution."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "success": True,
        "output": {"content": "file content"},
    }
    mock_httpx_client.return_value.post.return_value = mock_response

    result = client.execute_tool("filesystem", {"operation": "read", "path": "/test.txt"})

    assert result["success"] is True
    assert result["output"]["content"] == "file content"


def test_list_skills(client, mock_httpx_client):
    """Test listing skills."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "skills": [
            {"name": "code-review", "description": "Review code"},
            {"name": "refactor", "description": "Refactor code"},
        ]
    }
    mock_httpx_client.return_value.get.return_value = mock_response

    result = client.list_skills()

    assert len(result["skills"]) == 2
    assert result["skills"][0]["name"] == "code-review"


def test_execute_skill(client, mock_httpx_client):
    """Test skill execution."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "success": True,
        "response": "Code review complete",
    }
    mock_httpx_client.return_value.post.return_value = mock_response

    result = client.execute_skill("code-review", {"code": "def test(): pass"})

    assert result["success"] is True
    assert result["response"] == "Code review complete"


def test_remember(client, mock_httpx_client):
    """Test storing memory."""
    mock_response = Mock()
    mock_response.json.return_value = {"id": "memory-123", "content": "Test memory"}
    mock_httpx_client.return_value.post.return_value = mock_response

    result = client.remember("Test memory", "global")

    assert result["id"] == "memory-123"
    mock_httpx_client.return_value.post.assert_called_once()


def test_recall(client, mock_httpx_client):
    """Test recalling memories."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "memories": [
            {"id": "memory-1", "content": "Memory 1"},
            {"id": "memory-2", "content": "Memory 2"},
        ],
        "count": 2,
    }
    mock_httpx_client.return_value.post.return_value = mock_response

    result = client.recall("test query", "global", limit=10)

    assert result["count"] == 2
    assert len(result["memories"]) == 2


def test_evaluate(client, mock_httpx_client):
    """Test evaluation."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "results": [
            {"metric": "relevance", "score": 0.85},
            {"metric": "grounding", "score": 0.90},
        ]
    }
    mock_httpx_client.return_value.post.return_value = mock_response

    result = client.evaluate("What is Python?", "Python is a language", ["relevance", "grounding"])

    assert len(result["results"]) == 2
    assert result["results"][0]["score"] == 0.85


def test_get_observability_summary(client, mock_httpx_client):
    """Test getting observability summary."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "total_traces": 100,
        "total_spans": 500,
        "error_rate": 0.05,
        "avg_latency_ms": 150.0,
    }
    mock_httpx_client.return_value.get.return_value = mock_response

    result = client.get_observability_summary()

    assert result["total_traces"] == 100
    assert result["error_rate"] == 0.05


def test_close(client, mock_httpx_client):
    """Test closing client."""
    client.close()
    mock_httpx_client.return_value.close.assert_called_once()
