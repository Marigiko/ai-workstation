"""Tests for LiteLLM provider."""

import pytest
from providers import LiteLLMProvider

from contracts import Role


@pytest.fixture
def mock_provider():
    """Create a mock provider for testing."""
    return LiteLLMProvider(model="gpt-4o-mini", api_key="test-key")


def test_provider_name(mock_provider):
    """Test provider name extraction."""
    assert mock_provider.name == "openai"


def test_provider_name_claude():
    """Test Claude provider name."""
    provider = LiteLLMProvider(model="claude-3-opus-20240229")
    assert provider.name == "anthropic"


def test_provider_name_custom():
    """Test custom provider name."""
    provider = LiteLLMProvider(model="ollama/llama2")
    assert provider.name == "ollama"


@pytest.mark.asyncio
async def test_provider_capabilities(mock_provider):
    """Test provider capabilities."""
    caps = await mock_provider.capabilities()
    assert caps.provider == "openai"
    assert caps.model == "gpt-4o-mini"
    assert caps.supports_streaming is True
    assert caps.supports_tools is True
    assert caps.max_context_tokens > 0


@pytest.mark.asyncio
async def test_provider_health_mock(mock_provider, monkeypatch):
    """Test provider health check with mocked response."""
    from contracts import CompletionResponse

    async def mock_complete(request):
        return CompletionResponse(
            id="test-123",
            provider="openai",
            model="gpt-4o-mini",
            content="Hello!",
            role=Role.ASSISTANT,
        )

    monkeypatch.setattr(mock_provider, "complete", mock_complete)

    is_healthy = await mock_provider.health()
    assert is_healthy is True
