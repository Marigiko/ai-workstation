"""Latency evaluator for tracking response time."""

import uuid

from evaluation.models import EvalMetric, EvalRequest, EvalResult


class LatencyEvaluator:
    """Evaluator for tracking response latency."""

    async def evaluate(self, request: EvalRequest) -> EvalResult:
        """Evaluate latency based on metadata."""
        # Extract latency from metadata
        latency_ms = request.metadata.get("latency_ms", 0.0)
        max_latency_ms = request.metadata.get("max_latency_ms", 30000.0)

        # Score: 1.0 if instant, decreasing as latency increases
        if max_latency_ms <= 0:
            score = 1.0 if latency_ms == 0 else 0.0
        else:
            score = max(0.0, 1.0 - (latency_ms / max_latency_ms))

        return EvalResult(
            id=str(uuid.uuid4()),
            metric=EvalMetric.LATENCY,
            score=score,
            details={
                "latency_ms": latency_ms,
                "max_latency_ms": max_latency_ms,
                "within_threshold": latency_ms <= max_latency_ms,
            },
        )
