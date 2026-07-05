"""Cost-optimized router strategy."""

from contracts import CompletionRequest, Outcome, RoutingDecision
from routing.registry import ProviderRegistry


class CostOptimizedRouter:
    """Router that selects the cheapest provider/model."""

    def __init__(self, registry: ProviderRegistry):
        self.registry = registry
        self._outcomes: list[tuple[RoutingDecision, Outcome]] = []

    async def resolve(self, request: CompletionRequest) -> RoutingDecision:
        """Select cheapest available provider."""
        capabilities = await self.registry.get_all_capabilities()

        if not capabilities:
            raise ValueError("No providers registered")

        # Filter healthy providers
        healthy = []
        for name, caps in capabilities.items():
            if await self.registry.health_check(name):
                healthy.append((name, caps))

        if not healthy:
            raise ValueError("No healthy providers available")

        # Sort by cost (input + output)
        def total_cost(item):
            _, caps = item
            return caps.cost_per_1k_input_tokens + caps.cost_per_1k_output_tokens

        healthy.sort(key=total_cost)

        best_name, best_caps = healthy[0]

        # Build fallback chain
        fallback_chain = [(name, caps.model) for name, caps in healthy[1:3]]

        return RoutingDecision(
            provider=best_name,
            model=best_caps.model,
            fallback_chain=fallback_chain,
            estimated_cost_usd=total_cost(healthy[0]) / 1000,
            estimated_latency_ms=0.0,
            strategy="cost_optimized",
        )

    async def report_outcome(self, decision: RoutingDecision, outcome: Outcome) -> None:
        """Track outcome for learning."""
        self._outcomes.append((decision, outcome))
