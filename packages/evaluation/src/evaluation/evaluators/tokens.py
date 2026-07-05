"""Tokens evaluator for tracking token usage."""

import uuid

from evaluation.models import EvalMetric, EvalRequest, EvalResult


class TokensEvaluator:
    """Evaluator for tracking token usage."""

    async def evaluate(self, request: EvalRequest) -> EvalResult:
        """Evaluate token usage based on metadata."""
        # Extract token counts from metadata
        tokens_used = request.metadata.get("tokens_used", 0)
        max_tokens = request.metadata.get("max_tokens", 4096)

        # Score: 1.0 if under limit, decreasing as usage approaches limit
        if max_tokens <= 0:
            score = 1.0 if tokens_used == 0 else 0.0
        else:
            score = max(0.0, 1.0 - (tokens_used / max_tokens))

        return EvalResult(
            id=str(uuid.uuid4()),
            metric=EvalMetric.TOKENS,
            score=score,
            details={
                "tokens_used": tokens_used,
                "max_tokens": max_tokens,
                "within_limit": tokens_used <= max_tokens,
                "utilization_percent": (tokens_used / max_tokens * 100) if max_tokens > 0 else 0,
            },
        )
