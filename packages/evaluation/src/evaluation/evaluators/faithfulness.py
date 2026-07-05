"""Faithfulness evaluator using LLM."""

import uuid

from providers import LiteLLMProvider

from evaluation.models import EvalMetric, EvalRequest, EvalResult


class FaithfulnessEvaluator:
    """Evaluator for measuring faithfulness to context without hallucinations."""

    def __init__(self, provider: LiteLLMProvider):
        """Initialize with LLM provider."""
        self.provider = provider

    async def evaluate(self, request: EvalRequest) -> EvalResult:
        """Evaluate faithfulness using LLM."""
        context_text = "\n\n".join(request.context) if request.context else "No context provided"

        prompt = f"""Evaluate how faithful the response is to the context without hallucinations.

Context:
{context_text}

Response: {request.response}

Rate the faithfulness on a scale from 0.0 to 1.0 where:
- 1.0: Completely faithful, no hallucinations or fabrications
- 0.7: Mostly faithful, minor inaccuracies
- 0.4: Partially faithful, some hallucinations present
- 0.0: Not faithful, mostly hallucinated content

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
            metric=EvalMetric.FAITHFULNESS,
            score=score,
            details={
                "context_count": len(request.context),
                "response_preview": request.response[:200],
            },
        )
