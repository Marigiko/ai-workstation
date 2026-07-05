"""Capability-based router strategy."""

from contracts import CompletionRequest, Outcome, RoutingDecision
from routing.registry import ProviderRegistry


class CapabilityRouter:
    """Router that selects provider based on required capabilities."""

    def __init__(self, registry: ProviderRegistry):
        self.registry = registry
        self._outcomes: list[tuple[RoutingDecision, Outcome]] = []

    async def resolve(self, request: CompletionRequest) -> RoutingDecision:
        """Select provider that matches required capabilities."""
        capabilities = await self.registry.get_all_capabilities()

        if not capabilities:
            raise ValueError("No providers registered")

        # Determine required capabilities from request
        requires_tools = request.tools is not None and len(request.tools) > 0
        requires_streaming = request.stream
        requires_vision = any(
            "image" in msg.content.lower() or "vision" in msg.content.lower()
            for msg in request.messages
        )

        # Filter providers by capabilities
        matching = []
        for name, caps in capabilities.items():
            if not await self.registry.health_check(name):
                continue

            # Check if provider meets requirements
            if requires_tools and not caps.supports_tools:
                continue
            if requires_streaming and not caps.supports_streaming:
                continue
            if requires_vision and not caps.supports_vision:
                continue

            matching.append((name, caps))

        if not matching:
            raise ValueError("No providers match required capabilities")

        # Select first matching provider (could add more sophisticated selection)
        best_name, best_caps = matching[0]

        # Build fallback chain
        fallback_chain = [(name, caps.model) for name, caps in matching[1:3]]

        return RoutingDecision(
            provider=best_name,
            model=best_caps.model,
            fallback_chain=fallback_chain,
            estimated_cost_usd=0.0,
            estimated_latency_ms=0.0,
            strategy="capability_based",
            metadata={
                "requires_tools": requires_tools,
                "requires_streaming": requires_streaming,
                "requires_vision": requires_vision,
            },
        )

    async def report_outcome(self, decision: RoutingDecision, outcome: Outcome) -> None:
        """Track outcome for learning."""
        self._outcomes.append((decision, outcome))
