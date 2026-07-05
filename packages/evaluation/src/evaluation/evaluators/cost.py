"""Cost evaluator for tracking API costs."""

import uuid

from evaluation.models import EvalMetric, EvalRequest, EvalResult


class CostEvaluator:
    """Evaluator for tracking API costs."""

    async def evaluate(self, request: EvalRequest) -> EvalResult:
        """Evaluate cost based on metadata."""
        # Extract cost from metadata
        cost = request.metadata.get("cost_usd", 0.0)
        max_budget = request.metadata.get("max_budget_usd", 1.0)

        # Score: 1.0 if under budget, decreasing as cost approaches budget
        if max_budget <= 0:
            score = 1.0 if cost == 0 else 0.0
        else:
            score = max(0.0, 1.0 - (cost / max_budget))

        return EvalResult(
            id=str(uuid.uuid4()),
            metric=EvalMetric.COST,
            score=score,
            details={
                "cost_usd": cost,
                "max_budget_usd": max_budget,
                "within_budget": cost <= max_budget,
            },
        )
