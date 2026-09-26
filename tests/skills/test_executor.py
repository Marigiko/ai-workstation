"""Tests for SkillExecutor."""

from unittest.mock import AsyncMock, Mock

import pytest
from mcp import ToolRegistry
from providers import BaseProvider
from skills import SkillDefinition, SkillExecutionRequest, SkillExecutor

from contracts import CompletionResponse, Role


@pytest.fixture
def mock_provider():
    """Create a mock provider."""
    provider = Mock(spec=BaseProvider)
    provider.complete = AsyncMock(
        return_value=CompletionResponse(
            id="test-123",
            provider="test",
            model="test-model",
            content="Test response",
            role=Role.ASSISTANT,
            usage={"total_tokens": 10},
        )
    )
    return provider


@pytest.fixture
def tool_registry():
    """Create a tool registry."""
    return ToolRegistry()


@pytest.fixture
def executor(mock_provider, tool_registry):
    """Create a skill executor."""
    return SkillExecutor(mock_provider, tool_registry)


@pytest.fixture
def sample_skill():
    """Create a sample skill."""
    return SkillDefinition(
        name="test-skill",
        description="A test skill",
        system_prompt="You are a {role}.",
        user_prompt_template="Process this: {input}",
        variables=["role", "input"],
    )


@pytest.mark.asyncio
async def test_execute_skill(executor, sample_skill, mock_provider):
    """Test executing a skill."""
    request = SkillExecutionRequest(
        skill_name="test-skill",
        variables={"role": "test assistant", "input": "test data"},
    )

    result = await executor.execute(sample_skill, request)

    assert result.success
    assert result.skill_name == "test-skill"
    assert result.response == "Test response"
    assert result.metadata["tokens_used"] == 10

    # Verify provider was called with correct messages
    call_args = mock_provider.complete.call_args
    messages = call_args[0][0].messages
    assert len(messages) == 2
    assert messages[0].role == Role.SYSTEM
    assert "test assistant" in messages[0].content
    assert messages[1].role == Role.USER
    assert "test data" in messages[1].content


@pytest.mark.asyncio
async def test_execute_skill_with_context(executor, sample_skill, mock_provider):
    """Test executing a skill with additional context."""
    request = SkillExecutionRequest(
        skill_name="test-skill",
        variables={"role": "assistant", "input": "data"},
        context="Additional context here",
    )

    result = await executor.execute(sample_skill, request)

    assert result.success
    call_args = mock_provider.complete.call_args
    messages = call_args[0][0].messages
    assert "Additional context here" in messages[1].content


@pytest.mark.asyncio
async def test_execute_skill_failure(executor, sample_skill, mock_provider):
    """Test handling execution failure."""
    mock_provider.complete.side_effect = Exception("Provider error")

    request = SkillExecutionRequest(
        skill_name="test-skill",
        variables={"role": "assistant", "input": "data"},
    )

    result = await executor.execute(sample_skill, request)

    assert not result.success
    assert result.error == "Provider error"


def test_render_prompt(executor, sample_skill):
    """Test prompt rendering with variables."""
    template = "Hello {name}, you are {role}."
    variables = {"name": "Alice", "role": "a developer"}

    rendered = executor._render_prompt(template, variables)

    assert rendered == "Hello Alice, you are a developer."


def test_render_prompt_missing_variable(executor):
    """Test that missing variables are left as-is."""
    template = "Hello {name}."
    variables = {}

    rendered = executor._render_prompt(template, variables)

    assert rendered == "Hello {name}."
