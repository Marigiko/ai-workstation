"""Latency-optimized router strategy."""

from contracts import CompletionRequest, Outcome, RoutingDecision
from routing.registry import ProviderRegistry


class LatencyOptimizedRouter:
    """Router that selects the fastest provider based on historical data."""

    def __init__(self, registry: ProviderRegistry):
        self.registry = registry
        self._latency_history: dict[str, list[float]] = {}
        self._outcomes: list[tuple[RoutingDecision, Outcome]] = []

    async def resolve(self, request: CompletionRequest) -> RoutingDecision:
        """Select fastest provider based on historical latency."""
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

        # Calculate average latency for each provider
        def avg_latency(name: str) -> float:
            if name not in self._latency_history:
                return 0.0  # No data, assume fast
            latencies = self._latency_history[name]
            return sum(latencies) / len(latencies) if latencies else 0.0

        # Sort by average latency (lower is better)
        healthy_with_latency = [(name, caps, avg_latency(name)) for name, caps in healthy]
        healthy_with_latency.sort(key=lambda x: x[2])

        best_name, best_caps, best_latency = healthy_with_latency[0]

        # Build fallback chain
        fallback_chain = [(name, caps.model) for name, caps, _ in healthy_with_latency[1:3]]

        return RoutingDecision(
            provider=best_name,
            model=best_caps.model,
            fallback_chain=fallback_chain,
            estimated_cost_usd=0.0,
            estimated_latency_ms=best_latency,
            strategy="latency_optimized",
        )

    async def report_outcome(self, decision: RoutingDecision, outcome: Outcome) -> None:
        """Track outcome and update latency history."""
        self._outcomes.append((decision, outcome))

        # Update latency history
        provider = decision.provider
        if provider not in self._latency_history:
            self._latency_history[provider] = []

        self._latency_history[provider].append(outcome.latency_ms)

        # Keep only last 100 measurements
        if len(self._latency_history[provider]) > 100:
            self._latency_history[provider] = self._latency_history[provider][-100:]
