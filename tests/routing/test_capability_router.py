"""Tests for capability router."""

import pytest
from routing import CapabilityRouter, ProviderRegistry

from contracts import CompletionRequest, Message, Role
from tests.routing.test_registry import MockProvider


@pytest.fixture
def registry():
    """Create test registry."""
    reg = ProviderRegistry()
    reg.register(MockProvider("basic", cost=0.01))
    reg.register(MockProvider("advanced", cost=0.05))
    return reg


@pytest.fixture
def router(registry):
    """Create capability router."""
    return CapabilityRouter(registry)


@pytest.mark.asyncio
async def test_selects_matching_provider(router):
    """Test that router selects provider matching capabilities."""
    request = CompletionRequest(
        messages=[Message(role=Role.USER, content="Hello")],
        tools=[{"name": "test_tool"}],
    )
    decision = await router.resolve(request)

    assert decision.strategy == "capability_based"
    assert decision.metadata["requires_tools"] is True


@pytest.mark.asyncio
async def test_no_tools_required(router):
    """Test routing without tools."""
    request = CompletionRequest(messages=[Message(role=Role.USER, content="Hello")])
    decision = await router.resolve(request)

    assert decision.metadata["requires_tools"] is False
