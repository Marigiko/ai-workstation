"""Agent router — classifies tasks and routes to specialized agents."""

import logging
import re
from collections.abc import Callable

from contracts import (
    CompletionRequest,
    Message,
    Outcome,
    RoutingDecision,
)
from routing.agent_registry import AgentRegistry
from routing.registry import ProviderRegistry
from routing.tiered_router import TieredRouter

logger = logging.getLogger(__name__)

_TASK_PATTERNS: dict[str, list[str]] = {
    "test": [
        r"\b(test|spec|coverage|assert|mock|fixture|unittest|pytest)\b",
    ],
    "docs": [
        r"\b(document|documentation|readme|comment|explain|describe|guide|tutorial|docstring|changelog)\b",
    ],
    "debug": [
        r"\b(debug|trace|investigate|diagnose|why|what.*wrong|not working|broken|failing)\b",
    ],
    "review": [
        r"\b(review|audit|inspect|evaluate|assess|critique)\b",
    ],
    "planning": [
        r"\b(plan|design|architect|strategy|roadmap|approach|proposal|estimate|breakdown)\b",
    ],
    "code": [
        r"\b(implement|write|create|add|build|make|code|function|class|method|module|component|api|endpoint|refactor)\b",
        r"\b(fix|bug|error|patch|resolve|issue)\b",
    ],
}


def classify_task(messages: list[Message]) -> str:
    content = " ".join(m.content for m in messages).lower()
    for agent_type, patterns in _TASK_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, content):
                return agent_type
    return "general"


class AgentRouter:
    """Classifies tasks and routes to specialized agents, each with its own model cascade."""

    def __init__(
        self,
        registry: ProviderRegistry,
        agent_registry: AgentRegistry | None = None,
        classifier: Callable[[list[Message]], str] | None = None,
    ):
        self.registry = registry
        self.agent_registry = agent_registry or AgentRegistry()
        self._classifier = classifier or classify_task
        self._tiered_routers: dict[str, TieredRouter] = {}

    def _get_tiered_router(self, agent_type: str) -> TieredRouter:
        if agent_type not in self._tiered_routers:
            config = self.agent_registry.get(agent_type)
            self._tiered_routers[agent_type] = TieredRouter(self.registry, config.tiers)
        return self._tiered_routers[agent_type]

    async def resolve(self, request: CompletionRequest) -> RoutingDecision:
        agent_type = self._classifier(request.messages)
        logger.info("Task classified as '%s'", agent_type)

        tiered_router = self._get_tiered_router(agent_type)
        decision = await tiered_router.resolve(request)
        decision.metadata["agent_type"] = agent_type
        decision.strategy = "agent_tiered"
        return decision

    async def report_outcome(self, decision: RoutingDecision, outcome: Outcome) -> None:
        agent_type = decision.metadata.get("agent_type", "general")
        tiered_router = self._get_tiered_router(agent_type)
        await tiered_router.report_outcome(decision, outcome)
