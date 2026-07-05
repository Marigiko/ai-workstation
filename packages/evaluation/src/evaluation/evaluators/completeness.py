"""Completeness evaluator using LLM."""

import uuid

from providers import LiteLLMProvider

from evaluation.models import EvalMetric, EvalRequest, EvalResult


class CompletenessEvaluator:
    """Evaluator for measuring if response covers all aspects of query."""

    def __init__(self, provider: LiteLLMProvider):
        """Initialize with LLM provider."""
        self.provider = provider

    async def evaluate(self, request: EvalRequest) -> EvalResult:
        """Evaluate completeness using LLM."""
        prompt = f"""Evaluate how complete the response is in addressing the query.

Query: {request.query}
Response: {request.response}

Rate the completeness on a scale from 0.0 to 1.0 where:
- 1.0: Fully complete, addresses all aspects of the query
- 0.7: Mostly complete, minor aspects missing
- 0.4: Partially complete, significant aspects missing
- 0.0: Incomplete, doesn't address the query

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
            metric=EvalMetric.COMPLETENESS,
            score=score,
            details={
                "query": request.query,
                "response_preview": request.response[:200],
            },
        )
