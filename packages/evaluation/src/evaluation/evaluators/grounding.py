"""Grounding evaluator using LLM."""

import uuid

from providers import BaseProvider

from evaluation.models import EvalMetric, EvalRequest, EvalResult


class GroundingEvaluator:
    """Evaluator for measuring if response is grounded in context."""

    def __init__(self, provider: BaseProvider):
        """Initialize with LLM provider."""
        self.provider = provider

    async def evaluate(self, request: EvalRequest) -> EvalResult:
        """Evaluate grounding using LLM."""
        context_text = "\n\n".join(request.context) if request.context else "No context provided"

        prompt = f"""Evaluate how well the response is grounded in the provided context.

Context:
{context_text}

Response: {request.response}

Rate the grounding on a scale from 0.0 to 1.0 where:
- 1.0: Fully grounded, all claims supported by context
- 0.7: Mostly grounded, minor unsupported claims
- 0.4: Partially grounded, significant unsupported content
- 0.0: Not grounded, mostly fabricated information

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
            metric=EvalMetric.GROUNDING,
            score=score,
            details={
                "context_count": len(request.context),
                "response_preview": request.response[:200],
            },
        )
