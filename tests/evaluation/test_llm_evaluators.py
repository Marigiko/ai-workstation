"""Tests for LLM-based evaluators."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from evaluation.evaluators import (
    CompletenessEvaluator,
    CorrectnessEvaluator,
    FaithfulnessEvaluator,
    GroundingEvaluator,
    RelevanceEvaluator,
)
from evaluation.models import EvalMetric, EvalRequest


@pytest.fixture
def mock_provider():
    """Create mock provider."""
    provider = MagicMock()
    provider.complete = AsyncMock()
    return provider


@pytest.fixture
def relevance_evaluator(mock_provider):
    """Create relevance evaluator."""
    return RelevanceEvaluator(mock_provider)


@pytest.fixture
def grounding_evaluator(mock_provider):
    """Create grounding evaluator."""
    return GroundingEvaluator(mock_provider)


@pytest.fixture
def faithfulness_evaluator(mock_provider):
    """Create faithfulness evaluator."""
    return FaithfulnessEvaluator(mock_provider)


@pytest.fixture
def correctness_evaluator(mock_provider):
    """Create correctness evaluator."""
    return CorrectnessEvaluator(mock_provider)


@pytest.fixture
def completeness_evaluator(mock_provider):
    """Create completeness evaluator."""
    return CompletenessEvaluator(mock_provider)


@pytest.mark.asyncio
async def test_relevance_evaluator(relevance_evaluator, mock_provider):
    """Test relevance evaluator."""
    from contracts import CompletionResponse, Role

    mock_provider.complete.return_value = CompletionResponse(
        id="test",
        provider="test",
        model="test",
        content="0.85",
        role=Role.ASSISTANT,
    )

    request = EvalRequest(
        query="What is Python?",
        response="Python is a programming language.",
    )

    result = await relevance_evaluator.evaluate(request)

    assert result.metric == EvalMetric.RELEVANCE
    assert result.score == 0.85
    assert "query" in result.details


@pytest.mark.asyncio
async def test_grounding_evaluator(grounding_evaluator, mock_provider):
    """Test grounding evaluator."""
    from contracts import CompletionResponse, Role

    mock_provider.complete.return_value = CompletionResponse(
        id="test",
        provider="test",
        model="test",
        content="0.75",
        role=Role.ASSISTANT,
    )

    request = EvalRequest(
        query="What is Python?",
        response="Python is a programming language.",
        context=["Python is a high-level programming language."],
    )

    result = await grounding_evaluator.evaluate(request)

    assert result.metric == EvalMetric.GROUNDING
    assert result.score == 0.75
    assert result.details["context_count"] == 1


@pytest.mark.asyncio
async def test_faithfulness_evaluator(faithfulness_evaluator, mock_provider):
    """Test faithfulness evaluator."""
    from contracts import CompletionResponse, Role

    mock_provider.complete.return_value = CompletionResponse(
        id="test",
        provider="test",
        model="test",
        content="0.90",
        role=Role.ASSISTANT,
    )

    request = EvalRequest(
        query="What is Python?",
        response="Python is a programming language.",
        context=["Python is a high-level programming language."],
    )

    result = await faithfulness_evaluator.evaluate(request)

    assert result.metric == EvalMetric.FAITHFULNESS
    assert result.score == 0.90


@pytest.mark.asyncio
async def test_correctness_evaluator_with_expected(correctness_evaluator, mock_provider):
    """Test correctness evaluator with expected response."""
    from contracts import CompletionResponse, Role

    mock_provider.complete.return_value = CompletionResponse(
        id="test",
        provider="test",
        model="test",
        content="0.95",
        role=Role.ASSISTANT,
    )

    request = EvalRequest(
        query="What is 2+2?",
        response="4",
        expected_response="4",
    )

    result = await correctness_evaluator.evaluate(request)

    assert result.metric == EvalMetric.CORRECTNESS
    assert result.score == 0.95


@pytest.mark.asyncio
async def test_correctness_evaluator_without_expected(correctness_evaluator):
    """Test correctness evaluator without expected response."""
    request = EvalRequest(
        query="What is 2+2?",
        response="4",
    )

    result = await correctness_evaluator.evaluate(request)

    assert result.metric == EvalMetric.CORRECTNESS
    assert result.score == 0.5  # Default when no expected response
    assert result.details["reason"] == "No expected response provided"


@pytest.mark.asyncio
async def test_completeness_evaluator(completeness_evaluator, mock_provider):
    """Test completeness evaluator."""
    from contracts import CompletionResponse, Role

    mock_provider.complete.return_value = CompletionResponse(
        id="test",
        provider="test",
        model="test",
        content="0.80",
        role=Role.ASSISTANT,
    )

    request = EvalRequest(
        query="Explain Python and its uses",
        response="Python is a programming language used for web development.",
    )

    result = await completeness_evaluator.evaluate(request)

    assert result.metric == EvalMetric.COMPLETENESS
    assert result.score == 0.80


@pytest.mark.asyncio
async def test_evaluator_invalid_score(mock_provider):
    """Test evaluator handles invalid score from LLM."""
    from contracts import CompletionResponse, Role

    mock_provider.complete.return_value = CompletionResponse(
        id="test",
        provider="test",
        model="test",
        content="invalid",
        role=Role.ASSISTANT,
    )

    evaluator = RelevanceEvaluator(mock_provider)
    request = EvalRequest(
        query="test",
        response="test response",
    )

    result = await evaluator.evaluate(request)

    assert result.score == 0.5  # Default fallback
