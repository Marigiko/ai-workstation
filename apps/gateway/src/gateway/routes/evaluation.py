"""Evaluation endpoints for the gateway."""

import os

from evaluation import EvalMetric, EvalRequest, EvaluationService
from fastapi import APIRouter, HTTPException
from providers import OmniRouteProvider
from pydantic import BaseModel

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

# Lazy initialization
_evaluation_service: EvaluationService | None = None


def _get_evaluation_service() -> EvaluationService:
    """Get or create the evaluation service."""
    global _evaluation_service
    if _evaluation_service is None:
        model = os.getenv("DEFAULT_MODEL", "liviano")
        provider = OmniRouteProvider(model=model)
        _evaluation_service = EvaluationService(provider)
    return _evaluation_service


class EvaluateRequest(BaseModel):
    """Request to evaluate a response."""

    query: str
    response: str
    context: list[str] = []
    expected_response: str | None = None
    metrics: list[str] | None = None
    metadata: dict = {}


class BenchmarkRequest(BaseModel):
    """Request to run a benchmark."""

    test_cases: list[EvaluateRequest]
    metrics: list[str] | None = None


@router.post("/evaluate")
async def evaluate(request: EvaluateRequest):
    """Evaluate a response on specified metrics."""
    service = _get_evaluation_service()

    # Convert metrics if provided
    metrics = None
    if request.metrics:
        try:
            metrics = [EvalMetric(m) for m in request.metrics]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid metric: {e}")

    eval_request = EvalRequest(
        query=request.query,
        response=request.response,
        context=request.context,
        expected_response=request.expected_response,
        metadata=request.metadata,
    )

    results = await service.evaluate(eval_request, metrics)

    return {
        "results": [
            {
                "id": r.id,
                "metric": r.metric.value,
                "score": r.score,
                "details": r.details,
                "timestamp": r.timestamp.isoformat(),
            }
            for r in results
        ],
        "count": len(results),
    }


@router.post("/evaluate/{metric}")
async def evaluate_single(metric: str, request: EvaluateRequest):
    """Evaluate a response on a single metric."""
    service = _get_evaluation_service()

    try:
        eval_metric = EvalMetric(metric)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid metric: {metric}")

    eval_request = EvalRequest(
        query=request.query,
        response=request.response,
        context=request.context,
        expected_response=request.expected_response,
        metadata=request.metadata,
    )

    result = await service.evaluate_single(eval_request, eval_metric)

    return {
        "id": result.id,
        "metric": result.metric.value,
        "score": result.score,
        "details": result.details,
        "timestamp": result.timestamp.isoformat(),
    }


@router.post("/benchmark")
async def run_benchmark(request: BenchmarkRequest):
    """Run a benchmark suite."""
    service = _get_evaluation_service()

    # Convert metrics if provided
    metrics = None
    if request.metrics:
        try:
            metrics = [EvalMetric(m) for m in request.metrics]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid metric: {e}")

    # Convert test cases
    test_cases = [
        EvalRequest(
            query=tc.query,
            response=tc.response,
            context=tc.context,
            expected_response=tc.expected_response,
            metadata=tc.metadata,
        )
        for tc in request.test_cases
    ]

    benchmark_result = await service.run_benchmark(test_cases, metrics)

    return {
        "benchmark_id": benchmark_result.benchmark_id,
        "benchmark_name": benchmark_result.benchmark_name,
        "aggregate_scores": benchmark_result.aggregate_scores,
        "total_time_ms": benchmark_result.total_time_ms,
        "results_count": len(benchmark_result.results),
        "timestamp": benchmark_result.timestamp.isoformat(),
    }


@router.get("/evaluators")
async def list_evaluators():
    """List available evaluators."""
    service = _get_evaluation_service()
    evaluators = service.list_evaluators()

    return {
        "evaluators": evaluators,
        "count": len(evaluators),
    }


@router.get("/metrics")
async def list_metrics():
    """List available metrics."""
    metrics = [
        {
            "name": m.value,
            "description": _get_metric_description(m),
        }
        for m in EvalMetric
    ]

    return {
        "metrics": metrics,
        "count": len(metrics),
    }


def _get_metric_description(metric: EvalMetric) -> str:
    """Get description for a metric."""
    descriptions = {
        EvalMetric.RELEVANCE: "How relevant the response is to the query",
        EvalMetric.GROUNDING: "How well the response is grounded in context",
        EvalMetric.FAITHFULNESS: "How faithful the response is without hallucinations",
        EvalMetric.CORRECTNESS: "How correct the response is compared to expected",
        EvalMetric.COMPLETENESS: "How complete the response is for the query",
        EvalMetric.COST: "Cost efficiency of the response",
        EvalMetric.LATENCY: "Response time efficiency",
        EvalMetric.TOKENS: "Token usage efficiency",
    }
    return descriptions.get(metric, "No description available")
