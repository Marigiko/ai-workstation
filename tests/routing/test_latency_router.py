"""Tests for latency-optimized router."""

import pytest
from routing import LatencyOptimizedRouter, ProviderRegistry

from contracts import CompletionRequest, Message, Outcome, Role
from tests.routing.test_registry import MockProvider


@pytest.fixture
def registry():
    """Create test registry."""
    reg = ProviderRegistry()
    reg.register(MockProvider("fast", cost=0.05))
    reg.register(MockProvider("slow", cost=0.01))
    return reg


@pytest.fixture
def router(registry):
    """Create latency-optimized router."""
    return LatencyOptimizedRouter(registry)


@pytest.mark.asyncio
async def test_selects_fastest(router):
    """Test that router selects provider with lowest latency."""
    # Report some latency data
    from contracts import RoutingDecision

    decision1 = RoutingDecision(
        provider="fast",
        model="test",
        fallback_chain=[],
        strategy="latency_optimized",
    )
    outcome1 = Outcome(success=True, latency_ms=50.0, cost_usd=0.05, tokens_used=10)
    await router.report_outcome(decision1, outcome1)

    decision2 = RoutingDecision(
        provider="slow",
        model="test",
        fallback_chain=[],
        strategy="latency_optimized",
    )
    outcome2 = Outcome(success=True, latency_ms=500.0, cost_usd=0.01, tokens_used=10)
    await router.report_outcome(decision2, outcome2)

    # Now resolve
    request = CompletionRequest(messages=[Message(role=Role.USER, content="Hello")])
    decision = await router.resolve(request)

    assert decision.provider == "fast"
    assert decision.strategy == "latency_optimized"


@pytest.mark.asyncio
async def test_no_data_selects_first(router):
    """Test that router selects first provider when no data."""
    request = CompletionRequest(messages=[Message(role=Role.USER, content="Hello")])
    decision = await router.resolve(request)

    # Should select one of them (order may vary)
    assert decision.provider in ["fast", "slow"]
