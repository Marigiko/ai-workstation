"""Relevance evaluator using LLM."""

import uuid

from providers import BaseProvider

from evaluation.models import EvalMetric, EvalRequest, EvalResult


class RelevanceEvaluator:
    """Evaluator for measuring response relevance to query."""

    def __init__(self, provider: BaseProvider):
        """Initialize with LLM provider."""
        self.provider = provider

    async def evaluate(self, request: EvalRequest) -> EvalResult:
        """Evaluate relevance using LLM."""
        prompt = f"""Evaluate how relevant the response is to the query.

Query: {request.query}
Response: {request.response}

Rate the relevance on a scale from 0.0 to 1.0 where:
- 1.0: Perfectly relevant, directly answers the query
- 0.7: Mostly relevant, minor tangential information
- 0.4: Partially relevant, significant off-topic content
- 0.0: Completely irrelevant

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
            metric=EvalMetric.RELEVANCE,
            score=score,
            details={
                "query": request.query,
                "response_preview": request.response[:200],
            },
        )
