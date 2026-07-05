"""Tests for provider registry."""

import pytest
from routing import ProviderRegistry

from contracts import CompletionRequest, CompletionResponse, ProviderCapabilities, Role, StreamChunk


class MockProvider:
    """Mock provider for testing."""

    def __init__(self, name: str, cost: float = 0.0):
        self._name = name
        self._cost = cost

    @property
    def name(self) -> str:
        return self._name

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        return CompletionResponse(
            id="test-123",
            provider=self._name,
            model="test-model",
            content="Mock response",
            role=Role.ASSISTANT,
            cost_usd=self._cost,
        )

    async def stream(self, request: CompletionRequest):
        yield StreamChunk(id="test-123", provider=self._name, model="test-model", delta="Mock")

    async def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider=self._name,
            model="test-model",
            supports_streaming=True,
            supports_tools=True,
            supports_vision=False,
            max_context_tokens=4096,
            cost_per_1k_input_tokens=self._cost,
            cost_per_1k_output_tokens=self._cost,
        )

    async def health(self) -> bool:
        return True


@pytest.fixture
def registry():
    """Create test registry."""
    reg = ProviderRegistry()
    reg.register(MockProvider("provider-a", cost=0.01))
    reg.register(MockProvider("provider-b", cost=0.05))
    reg.register(MockProvider("provider-c", cost=0.02))
    return reg


def test_register_provider(registry):
    """Test registering a provider."""
    assert "provider-a" in registry.list_providers()
    assert "provider-b" in registry.list_providers()


def test_get_provider(registry):
    """Test getting a provider."""
    provider = registry.get("provider-a")
    assert provider is not None
    assert provider.name == "provider-a"


def test_get_nonexistent_provider(registry):
    """Test getting a nonexistent provider."""
    provider = registry.get("nonexistent")
    assert provider is None


@pytest.mark.asyncio
async def test_get_capabilities(registry):
    """Test getting provider capabilities."""
    caps = await registry.get_capabilities("provider-a")
    assert caps is not None
    assert caps.provider == "provider-a"
    assert caps.cost_per_1k_input_tokens == 0.01


@pytest.mark.asyncio
async def test_get_all_capabilities(registry):
    """Test getting all capabilities."""
    caps = await registry.get_all_capabilities()
    assert len(caps) == 3
    assert "provider-a" in caps


@pytest.mark.asyncio
async def test_health_check(registry):
    """Test health check."""
    healthy = await registry.health_check("provider-a")
    assert healthy is True


@pytest.mark.asyncio
async def test_health_check_all(registry):
    """Test health check all."""
    results = await registry.health_check_all()
    assert len(results) == 3
    assert all(results.values())
