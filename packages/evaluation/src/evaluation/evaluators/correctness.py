"""Correctness evaluator using LLM."""

import uuid

from providers import BaseProvider

from evaluation.models import EvalMetric, EvalRequest, EvalResult


class CorrectnessEvaluator:
    """Evaluator for measuring correctness against expected response."""

    def __init__(self, provider: BaseProvider):
        """Initialize with LLM provider."""
        self.provider = provider

    async def evaluate(self, request: EvalRequest) -> EvalResult:
        """Evaluate correctness using LLM."""
        if not request.expected_response:
            # If no expected response, we can't evaluate correctness
            return EvalResult(
                id=str(uuid.uuid4()),
                metric=EvalMetric.CORRECTNESS,
                score=0.5,
                details={
                    "reason": "No expected response provided",
                    "response_preview": request.response[:200],
                },
            )

        prompt = f"""Evaluate how correct the response is compared to the expected response.

Query: {request.query}
Expected Response: {request.expected_response}
Actual Response: {request.response}

Rate the correctness on a scale from 0.0 to 1.0 where:
- 1.0: Perfectly correct, matches expected response
- 0.7: Mostly correct, minor differences
- 0.4: Partially correct, significant differences
- 0.0: Completely incorrect

Respond with ONLY a number between 0.0 and 1.0, nothing else."""

        from contracts import CompletionRequest, Message, Role

        completion_request = CompletionRequest(
            messages=[Message(role=Role.USER, content=prompt)],
            temperature=0.1,
            max_tokens=10,
        )

        response = await self.provider.complete(completion_request)

        try:
            score = float(response.content.strip())
            score = max(0.0, min(1.0, score))
        except (ValueError, AttributeError):
            score = 0.5

        return EvalResult(
            id=str(uuid.uuid4()),
            metric=EvalMetric.CORRECTNESS,
            score=score,
            details={
                "query": request.query,
                "expected_preview": request.expected_response[:200],
                "response_preview": request.response[:200],
            },
        )
