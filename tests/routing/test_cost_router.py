"""Tests for cost-optimized router."""

import pytest
from routing import CostOptimizedRouter, ProviderRegistry

from contracts import CompletionRequest, Message, Role
from tests.routing.test_registry import MockProvider


@pytest.fixture
def registry():
    """Create test registry."""
    reg = ProviderRegistry()
    reg.register(MockProvider("cheap", cost=0.01))
    reg.register(MockProvider("expensive", cost=0.10))
    reg.register(MockProvider("medium", cost=0.05))
    return reg


@pytest.fixture
def router(registry):
    """Create cost-optimized router."""
    return CostOptimizedRouter(registry)


@pytest.mark.asyncio
async def test_selects_cheapest(router):
    """Test that router selects cheapest provider."""
    request = CompletionRequest(messages=[Message(role=Role.USER, content="Hello")])
    decision = await router.resolve(request)

    assert decision.provider == "cheap"
    assert decision.strategy == "cost_optimized"


@pytest.mark.asyncio
async def test_fallback_chain(router):
    """Test that fallback chain is populated."""
    request = CompletionRequest(messages=[Message(role=Role.USER, content="Hello")])
    decision = await router.resolve(request)

    assert len(decision.fallback_chain) > 0
    assert decision.fallback_chain[0][0] == "medium"


@pytest.mark.asyncio
async def test_report_outcome(router):
    """Test reporting outcome."""
    from contracts import Outcome

    request = CompletionRequest(messages=[Message(role=Role.USER, content="Hello")])
    decision = await router.resolve(request)

    outcome = Outcome(success=True, latency_ms=100.0, cost_usd=0.01, tokens_used=10)
    await router.report_outcome(decision, outcome)

    assert len(router._outcomes) == 1
