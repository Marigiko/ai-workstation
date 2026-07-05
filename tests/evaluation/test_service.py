"""Tests for evaluation service."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from evaluation import EvalMetric, EvalRequest, EvaluationService
from evaluation.models import BenchmarkResult


@pytest.fixture
def mock_provider():
    """Create mock provider."""
    provider = MagicMock()
    provider.complete = AsyncMock()
    return provider


@pytest.fixture
def evaluation_service(mock_provider):
    """Create evaluation service."""
    return EvaluationService(mock_provider)


@pytest.mark.asyncio
async def test_evaluation_service_initialization(evaluation_service):
    """Test evaluation service initializes with all evaluators."""
    evaluators = evaluation_service.list_evaluators()

    assert len(evaluators) == 8
    assert "cost" in evaluators
    assert "latency" in evaluators
    assert "tokens" in evaluators
    assert "relevance" in evaluators
    assert "grounding" in evaluators
    assert "faithfulness" in evaluators
    assert "correctness" in evaluators
    assert "completeness" in evaluators


@pytest.mark.asyncio
async def test_evaluate_all_metrics(evaluation_service, mock_provider):
    """Test evaluating all metrics."""
    from contracts import CompletionResponse, Role

    mock_provider.complete.return_value = CompletionResponse(
        id="test",
        provider="test",
        model="test",
        content="0.85",
        role=Role.ASSISTANT,
    )

    request = EvalRequest(
        query="test query",
        response="test response",
        metadata={"cost_usd": 0.05, "latency_ms": 1000, "tokens_used": 100},
    )

    results = await evaluation_service.evaluate(request)

    assert len(results) == 8
    metrics = [r.metric for r in results]
    assert EvalMetric.COST in metrics
    assert EvalMetric.LATENCY in metrics
    assert EvalMetric.TOKENS in metrics


@pytest.mark.asyncio
async def test_evaluate_specific_metrics(evaluation_service):
    """Test evaluating specific metrics."""
    request = EvalRequest(
        query="test query",
        response="test response",
        metadata={"cost_usd": 0.05, "latency_ms": 1000},
    )

    results = await evaluation_service.evaluate(
        request,
        metrics=[EvalMetric.COST, EvalMetric.LATENCY],
    )

    assert len(results) == 2
    metrics = [r.metric for r in results]
    assert EvalMetric.COST in metrics
    assert EvalMetric.LATENCY in metrics
    assert EvalMetric.TOKENS not in metrics


@pytest.mark.asyncio
async def test_evaluate_single_metric(evaluation_service):
    """Test evaluating a single metric."""
    request = EvalRequest(
        query="test query",
        response="test response",
        metadata={"cost_usd": 0.50, "max_budget_usd": 1.0},
    )

    result = await evaluation_service.evaluate_single(request, EvalMetric.COST)

    assert result.metric == EvalMetric.COST
    assert result.score == 0.5  # 1.0 - (0.50/1.0) = 0.5


@pytest.mark.asyncio
async def test_run_benchmark(evaluation_service, mock_provider):
    """Test running a benchmark."""
    from contracts import CompletionResponse, Role

    mock_provider.complete.return_value = CompletionResponse(
        id="test",
        provider="test",
        model="test",
        content="0.80",
        role=Role.ASSISTANT,
    )

    test_cases = [
        EvalRequest(
            query="query 1",
            response="response 1",
            metadata={"cost_usd": 0.05},
        ),
        EvalRequest(
            query="query 2",
            response="response 2",
            metadata={"cost_usd": 0.10},
        ),
    ]

    result = await evaluation_service.run_benchmark(
        test_cases,
        metrics=[EvalMetric.COST],
    )

    assert isinstance(result, BenchmarkResult)
    assert len(result.results) == 2
    assert "cost" in result.aggregate_scores
    assert result.total_time_ms >= 0  # Can be 0 if execution is very fast


@pytest.mark.asyncio
async def test_list_evaluators(evaluation_service):
    """Test listing evaluators."""
    evaluators = evaluation_service.list_evaluators()

    assert isinstance(evaluators, list)
    assert len(evaluators) == 8
    assert "cost" in evaluators
