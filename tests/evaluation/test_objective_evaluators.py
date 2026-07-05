"""Tests for objective evaluators (cost, latency, tokens)."""

import pytest
from evaluation.evaluators import CostEvaluator, LatencyEvaluator, TokensEvaluator
from evaluation.models import EvalMetric, EvalRequest


@pytest.fixture
def cost_evaluator():
    """Create cost evaluator."""
    return CostEvaluator()


@pytest.fixture
def latency_evaluator():
    """Create latency evaluator."""
    return LatencyEvaluator()


@pytest.fixture
def tokens_evaluator():
    """Create tokens evaluator."""
    return TokensEvaluator()


@pytest.mark.asyncio
async def test_cost_evaluator_under_budget(cost_evaluator):
    """Test cost evaluator when under budget."""
    request = EvalRequest(
        query="test",
        response="test response",
        metadata={"cost_usd": 0.05, "max_budget_usd": 0.10},
    )

    result = await cost_evaluator.evaluate(request)

    assert result.metric == EvalMetric.COST
    assert result.score == 0.5  # 1.0 - (0.05/0.10)
    assert result.details["cost_usd"] == 0.05
    assert result.details["within_budget"] is True


@pytest.mark.asyncio
async def test_cost_evaluator_over_budget(cost_evaluator):
    """Test cost evaluator when over budget."""
    request = EvalRequest(
        query="test",
        response="test response",
        metadata={"cost_usd": 0.15, "max_budget_usd": 0.10},
    )

    result = await cost_evaluator.evaluate(request)

    assert result.metric == EvalMetric.COST
    assert result.score == 0.0  # max(0, 1.0 - 1.5)
    assert result.details["within_budget"] is False


@pytest.mark.asyncio
async def test_latency_evaluator_fast(latency_evaluator):
    """Test latency evaluator for fast response."""
    request = EvalRequest(
        query="test",
        response="test response",
        metadata={"latency_ms": 1000.0, "max_latency_ms": 10000.0},
    )

    result = await latency_evaluator.evaluate(request)

    assert result.metric == EvalMetric.LATENCY
    assert result.score == 0.9  # 1.0 - (1000/10000)
    assert result.details["within_threshold"] is True


@pytest.mark.asyncio
async def test_latency_evaluator_slow(latency_evaluator):
    """Test latency evaluator for slow response."""
    request = EvalRequest(
        query="test",
        response="test response",
        metadata={"latency_ms": 15000.0, "max_latency_ms": 10000.0},
    )

    result = await latency_evaluator.evaluate(request)

    assert result.metric == EvalMetric.LATENCY
    assert result.score == 0.0  # max(0, 1.0 - 1.5)
    assert result.details["within_threshold"] is False


@pytest.mark.asyncio
async def test_tokens_evaluator_under_limit(tokens_evaluator):
    """Test tokens evaluator when under limit."""
    request = EvalRequest(
        query="test",
        response="test response",
        metadata={"tokens_used": 2000, "max_tokens": 4000},
    )

    result = await tokens_evaluator.evaluate(request)

    assert result.metric == EvalMetric.TOKENS
    assert result.score == 0.5  # 1.0 - (2000/4000)
    assert result.details["within_limit"] is True
    assert result.details["utilization_percent"] == 50.0


@pytest.mark.asyncio
async def test_tokens_evaluator_over_limit(tokens_evaluator):
    """Test tokens evaluator when over limit."""
    request = EvalRequest(
        query="test",
        response="test response",
        metadata={"tokens_used": 5000, "max_tokens": 4000},
    )

    result = await tokens_evaluator.evaluate(request)

    assert result.metric == EvalMetric.TOKENS
    assert result.score == 0.0  # max(0, 1.0 - 1.25)
    assert result.details["within_limit"] is False
