"""Base router interface."""

from typing import Protocol

from contracts import CompletionRequest, Outcome, RoutingDecision


class Router(Protocol):
    """Router interface for model selection."""

    async def resolve(self, request: CompletionRequest) -> RoutingDecision:
        """Decide which provider/model to use."""
        ...

    async def report_outcome(self, decision: RoutingDecision, outcome: Outcome) -> None:
        """Report the outcome of a routing decision."""
        ...
