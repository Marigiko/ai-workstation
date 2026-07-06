"""Tests for agent router and task classifier."""

import pytest
from routing import AgentRouter, ProviderRegistry, classify_task

from contracts import (
    CompletionRequest,
    CompletionResponse,
    Message,
    ProviderCapabilities,
    Role,
    StreamChunk,
)


class MockProvider:
    def __init__(self, name: str):
        self._name = name

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
        return True


@pytest.fixture
def registry():
    reg = ProviderRegistry()
    reg.register(MockProvider("gemini"))
    reg.register(MockProvider("claude"))
    reg.register(MockProvider("openai"))
    return reg


def test_classify_code_task():
    messages = [Message(role=Role.USER, content="Implement a function that sorts a list")]
    assert classify_task(messages) == "code"


def test_classify_docs_task():
    messages = [Message(role=Role.USER, content="Create documentation for the API endpoints")]
    assert classify_task(messages) == "docs"


def test_classify_planning_task():
    messages = [Message(role=Role.USER, content="Design the architecture for a new microservice")]
    assert classify_task(messages) == "planning"


def test_classify_review_task():
    messages = [Message(role=Role.USER, content="Review this pull request for security issues")]
    assert classify_task(messages) == "review"


def test_classify_debug_task():
    messages = [Message(role=Role.USER, content="Debug why the tests are failing")]
    assert classify_task(messages) == "debug"


def test_classify_test_task():
    messages = [
        Message(role=Role.USER, content="Add pytest coverage for the auth module")
    ]
    assert classify_task(messages) == "test"


def test_classify_general_task():
    messages = [Message(role=Role.USER, content="What is the meaning of life?")]
    assert classify_task(messages) == "general"


@pytest.mark.asyncio
async def test_agent_router_resolves_correct_agent(registry):
    router = AgentRouter(registry)
    request = CompletionRequest(
        messages=[Message(role=Role.USER, content="Implement a new API endpoint")]
    )
    decision = await router.resolve(request)
    assert decision.metadata["agent_type"] == "code"
    assert decision.strategy == "agent_tiered"


@pytest.mark.asyncio
async def test_agent_router_debug_task(registry):
    router = AgentRouter(registry)
    request = CompletionRequest(
        messages=[Message(role=Role.USER, content="Why is the app crashing?")]
    )
    decision = await router.resolve(request)
    assert decision.metadata["agent_type"] == "debug"


@pytest.mark.asyncio
async def test_agent_router_report_outcome(registry):
    from contracts import Outcome

    router = AgentRouter(registry)
    request = CompletionRequest(
        messages=[Message(role=Role.USER, content="Implement a function")]
    )
    decision = await router.resolve(request)
    outcome = Outcome(success=True, latency_ms=100.0, cost_usd=0.0, tokens_used=50)
    await router.report_outcome(decision, outcome)


@pytest.mark.asyncio
async def test_agent_router_custom_classifier(registry):
    def always_code(messages):
        return "code"

    router = AgentRouter(registry, classifier=always_code)
    request = CompletionRequest(
        messages=[Message(role=Role.USER, content="Anything at all")]
    )
    decision = await router.resolve(request)
    assert decision.metadata["agent_type"] == "code"
