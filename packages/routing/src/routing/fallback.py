"""Fallback router with chain support."""

import time

from contracts import (
    CompletionRequest,
    CompletionResponse,
    Outcome,
    RoutingError,
)
from routing.base import Router
from routing.registry import ProviderRegistry


class FallbackRouter:
    """Router that executes requests with fallback chain support."""

    def __init__(self, registry: ProviderRegistry, base_router: Router):
        self.registry = registry
        self.base_router = base_router

    async def execute(self, request: CompletionRequest) -> CompletionResponse:
        """Execute request with fallback chain."""
        # Get routing decision
        decision = await self.base_router.resolve(request)

        # Try primary provider
        provider = self.registry.get(decision.provider)
        if not provider:
            raise RoutingError(f"Provider {decision.provider} not found")

        start_time = time.time()
        try:
            response = await provider.complete(request)
            latency_ms = (time.time() - start_time) * 1000

            # Report success
            outcome = Outcome(
                success=True,
                latency_ms=latency_ms,
                cost_usd=response.cost_usd,
                tokens_used=response.usage.get("total_tokens", 0),
            )
            await self.base_router.report_outcome(decision, outcome)

            return response

        except Exception as primary_error:
            # Try fallback providers
            for fallback_provider, fallback_model in decision.fallback_chain:
                provider = self.registry.get(fallback_provider)
                if not provider:
                    continue

                try:
                    # Update request to use fallback model
                    fallback_request = request.model_copy()
                    fallback_request.model = fallback_model

                    response = await provider.complete(fallback_request)
                    latency_ms = (time.time() - start_time) * 1000

                    # Report success with fallback
                    outcome = Outcome(
                        success=True,
                        latency_ms=latency_ms,
                        cost_usd=response.cost_usd,
                        tokens_used=response.usage.get("total_tokens", 0),
                    )
                    await self.base_router.report_outcome(decision, outcome)

                    return response

                except Exception:
                    continue

            # All providers failed
            outcome = Outcome(
                success=False,
                latency_ms=(time.time() - start_time) * 1000,
                cost_usd=0.0,
                tokens_used=0,
                error=str(primary_error),
            )
            await self.base_router.report_outcome(decision, outcome)

            raise RoutingError(
                f"All providers failed. Primary: {primary_error}"
            ) from primary_error
