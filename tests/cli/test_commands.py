"""Tests for CLI commands."""

from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from cli.main import app

runner = CliRunner()


@pytest.fixture
def mock_client():
    """Mock gateway client."""
    with patch("cli.main.get_client") as mock_get_client:
        client = Mock()
        mock_get_client.return_value = client
        yield client


def test_status_command(mock_client):
    """Test status command."""
    mock_client.health_check.return_value = {"status": "healthy"}
    mock_client.base_url = "http://localhost:8000"

    result = runner.invoke(app, ["status"])

    assert result.exit_code == 0
    assert "healthy" in result.stdout.lower()


def test_chat_command(mock_client):
    """Test chat command."""
    mock_client.chat.return_value = {
        "content": "Hello! How can I help?",
        "usage": {"total_tokens": 10},
        "latency_ms": 100.0,
    }

    result = runner.invoke(app, ["chat", "Hi"])

    assert result.exit_code == 0
    assert "Hello! How can I help?" in result.stdout


def test_chat_with_session(mock_client):
    """Test chat command with session."""
    mock_client.chat.return_value = {
        "content": "Response",
        "usage": {"total_tokens": 10},
        "latency_ms": 100.0,
    }

    result = runner.invoke(app, ["chat", "Hi", "--session", "session-123"])

    assert result.exit_code == 0
    mock_client.chat.assert_called_once()


def test_session_create(mock_client):
    """Test session create command."""
    mock_client.create_session.return_value = {"id": "session-123", "title": "Test"}

    result = runner.invoke(app, ["session", "create", "--title", "Test"])

    assert result.exit_code == 0
    assert "session-123" in result.stdout


def test_session_list(mock_client):
    """Test session list command."""
    mock_client.list_sessions.return_value = [
        {"id": "session-1", "title": "Test 1", "created_at": "2026-01-01T00:00:00"},
        {"id": "session-2", "title": "Test 2", "created_at": "2026-01-02T00:00:00"},
    ]

    result = runner.invoke(app, ["session", "list"])

    assert result.exit_code == 0
    assert "session-1" in result.stdout or "Test 1" in result.stdout


def test_session_show(mock_client):
    """Test session show command."""
    mock_client.get_session.return_value = {
        "id": "session-123",
        "title": "Test",
        "created_at": "2026-01-01T00:00:00",
        "turns": [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
        ],
    }

    result = runner.invoke(app, ["session", "show", "session-123"])

    assert result.exit_code == 0
    assert "session-123" in result.stdout


def test_session_delete(mock_client):
    """Test session delete command."""
    mock_client.delete_session.return_value = {"deleted": True}

    result = runner.invoke(app, ["session", "delete", "session-123"])

    assert result.exit_code == 0
    assert "Deleted" in result.stdout


def test_tools_list(mock_client):
    """Test tools list command."""
    mock_client.list_tools.return_value = {
        "tools": [
            {"name": "filesystem", "description": "File operations"},
            {"name": "git", "description": "Git operations"},
        ]
    }

    result = runner.invoke(app, ["tools", "list"])

    assert result.exit_code == 0
    assert "filesystem" in result.stdout


def test_tools_exec(mock_client):
    """Test tools exec command."""
    mock_client.execute_tool.return_value = {
        "success": True,
        "output": {"content": "file content"},
        "error": None,
    }

    result = runner.invoke(
        app,
        ["tools", "exec", "filesystem", "--params", '{"operation": "read"}'],
    )

    assert result.exit_code == 0


def test_tools_exec_invalid_json(mock_client):
    """Test tools exec with invalid JSON."""
    result = runner.invoke(app, ["tools", "exec", "filesystem", "--params", "invalid"])

    assert result.exit_code == 1
    assert "Invalid JSON" in result.stdout


def test_skills_list(mock_client):
    """Test skills list command."""
    mock_client.list_skills.return_value = {
        "skills": [
            {"name": "code-review", "description": "Review code", "variables": ["code"]},
            {"name": "refactor", "description": "Refactor code", "variables": ["code", "goals"]},
        ]
    }

    result = runner.invoke(app, ["skills", "list"])

    assert result.exit_code == 0
    assert "code-review" in result.stdout


def test_skills_exec(mock_client):
    """Test skills exec command."""
    mock_client.execute_skill.return_value = {
        "success": True,
        "response": "Code review complete",
        "error": None,
    }

    result = runner.invoke(
        app,
        ["skills", "exec", "code-review", "--vars", '{"code": "def test(): pass"}'],
    )

    assert result.exit_code == 0
    assert "Code review complete" in result.stdout


def test_memory_remember(mock_client):
    """Test memory remember command."""
    mock_client.remember.return_value = {"id": "memory-123", "content": "Test memory"}

    result = runner.invoke(app, ["memory", "remember", "Test memory", "--scope", "global"])

    assert result.exit_code == 0
    assert "memory-123" in result.stdout


def test_memory_recall(mock_client):
    """Test memory recall command."""
    mock_client.recall.return_value = {
        "memories": [
            {"id": "memory-1", "content": "Memory 1", "scope": "global"},
            {"id": "memory-2", "content": "Memory 2", "scope": "global"},
        ],
        "count": 2,
    }

    result = runner.invoke(app, ["memory", "recall", "test query", "--scope", "global"])

    assert result.exit_code == 0


def test_memory_recall_empty(mock_client):
    """Test memory recall with no results."""
    mock_client.recall.return_value = {"memories": [], "count": 0}

    result = runner.invoke(app, ["memory", "recall", "test query"])

    assert result.exit_code == 0
    assert "No memories found" in result.stdout


def test_eval_run(mock_client):
    """Test evaluation run command."""
    mock_client.evaluate.return_value = {
        "results": [
            {"metric": "relevance", "score": 0.85},
            {"metric": "grounding", "score": 0.90},
        ]
    }

    result = runner.invoke(
        app,
        [
            "eval",
            "run",
            "--query",
            "What is Python?",
            "--response",
            "Python is a language",
            "--metrics",
            "relevance,grounding",
        ],
    )

    assert result.exit_code == 0
    assert "relevance" in result.stdout


def test_metrics_command(mock_client):
    """Test metrics command."""
    mock_client.get_observability_summary.return_value = {
        "total_traces": 100,
        "total_spans": 500,
        "total_metrics": 1000,
        "total_logs": 2000,
        "error_rate": 0.05,
        "avg_latency_ms": 150.0,
        "p95_latency_ms": 300.0,
        "p99_latency_ms": 500.0,
    }

    result = runner.invoke(app, ["metrics"])

    assert result.exit_code == 0
    assert "100" in result.stdout  # total_traces
    assert "0.05" in result.stdout or "5.00%" in result.stdout  # error_rate


def test_error_handling(mock_client):
    """Test error handling."""
    from httpx import HTTPStatusError

    mock_response = Mock()
    mock_response.json.return_value = {"detail": "Test error"}
    error = HTTPStatusError("Test error", request=Mock(), response=mock_response)
    mock_client.health_check.side_effect = error

    result = runner.invoke(app, ["status"])

    assert result.exit_code == 1
    assert "Error" in result.stdout
