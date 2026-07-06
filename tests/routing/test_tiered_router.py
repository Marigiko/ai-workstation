"""Tests for tiered router."""

import pytest
from routing import ProviderRegistry, TieredRouter

from contracts import (
    CompletionRequest,
    CompletionResponse,
    Message,
    Outcome,
    ProviderCapabilities,
    Role,
    RoutingError,
    StreamChunk,
    Tier,
)


class MockProvider:
    def __init__(self, name: str, healthy: bool = True):
        self._name = name
        self._healthy = healthy

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
        )

    async def stream(self, request: CompletionRequest):
        yield StreamChunk(id="test-123", provider=self._name, model="test-model", delta="Mock")

    async def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider=self._name,
            model="test-model",
            max_context_tokens=4096,
        )

    async def health(self) -> bool:
        return self._healthy


@pytest.fixture
def registry():
    reg = ProviderRegistry()
    reg.register(MockProvider("gemini"))
    reg.register(MockProvider("claude"))
    reg.register(MockProvider("openai"))
    return reg


@pytest.fixture
def tiers():
    return [
        Tier(name="free", models=["gemini/gemini-2.5-flash"], token_budget=1000),
        Tier(name="paid", models=["claude/claude-sonnet", "openai/gpt-4o"], token_budget=-1),
    ]


@pytest.mark.asyncio
async def test_resolves_first_tier_when_budget_available(registry, tiers):
    router = TieredRouter(registry, tiers)
    request = CompletionRequest(messages=[Message(role=Role.USER, content="Hello")])
    decision = await router.resolve(request)
    assert decision.provider == "gemini"
    assert decision.metadata["tier_name"] == "free"


@pytest.mark.asyncio
async def test_cascades_when_budget_exhausted(registry, tiers):
    router = TieredRouter(registry, tiers)
    request = CompletionRequest(messages=[Message(role=Role.USER, content="Hello")])

    outcome = Outcome(success=True, latency_ms=100.0, cost_usd=0.0, tokens_used=1000)
    decision = await router.resolve(request)
    await router.report_outcome(decision, outcome)

    decision2 = await router.resolve(request)
    assert decision2.provider == "claude"
    assert decision2.metadata["tier_name"] == "paid"


@pytest.mark.asyncio
async def test_skips_unhealthy_provider():
    reg = ProviderRegistry()
    reg.register(MockProvider("gemini", healthy=False))
    reg.register(MockProvider("claude"))
    tiers = [
        Tier(name="free", models=["gemini/flash"], token_budget=1000),
        Tier(name="paid", models=["claude/claude-sonnet"], token_budget=-1),
    ]
    router = TieredRouter(reg, tiers)
    request = CompletionRequest(messages=[Message(role=Role.USER, content="Hello")])
    decision = await router.resolve(request)
    assert decision.provider == "claude"
    assert decision.metadata["tier_name"] == "paid"


@pytest.mark.asyncio
async def test_raises_when_no_models():
    reg = ProviderRegistry()
    tiers = [Tier(name="free", models=[], token_budget=100)]
    router = TieredRouter(reg, tiers)
    request = CompletionRequest(messages=[Message(role=Role.USER, content="Hello")])
    with pytest.raises(RoutingError):
        await router.resolve(request)


@pytest.mark.asyncio
async def test_report_outcome_consumes_budget(registry, tiers):
    router = TieredRouter(registry, tiers)
    request = CompletionRequest(messages=[Message(role=Role.USER, content="Hello")])
    decision = await router.resolve(request)
    outcome = Outcome(success=True, latency_ms=100.0, cost_usd=0.0, tokens_used=500)
    await router.report_outcome(decision, outcome)
    assert router._budgets["free"].consumed == 500
    assert router._budgets["free"].remaining == 500


@pytest.mark.asyncio
async def test_unlimited_budget_never_exhausts():
    reg = ProviderRegistry()
    reg.register(MockProvider("claude"))
    tiers = [Tier(name="paid", models=["claude/claude-sonnet"], token_budget=-1)]
    router = TieredRouter(reg, tiers)
    request = CompletionRequest(messages=[Message(role=Role.USER, content="Hello")])

    for _ in range(100):
        decision = await router.resolve(request)
        outcome = Outcome(success=True, latency_ms=100.0, cost_usd=0.0, tokens_used=999_999)
        await router.report_outcome(decision, outcome)

    decision = await router.resolve(request)
    assert decision.provider == "claude"
