"""Unified router — combines all routing strategies into one.

Replaces AgentRouter, TieredRouter, CostOptimizedRouter,
LatencyOptimizedRouter, and CapabilityRouter with a single
composable strategy.

Selection process:
1. CAPABILITY FILTER: Remove providers that don't meet requirements
2. TASK CLASSIFICATION: Classify task type (code/docs/debug/test/planning/review)
3. SCORE: Weighted score of cost, latency, and tier preference
4. FALLBACK: Next-ranked providers are returned in fallback_chain for callers such as FallbackRouter
"""

import logging
import re
from collections.abc import Callable

from contracts import (
    CompletionRequest,
    Message,
    Outcome,
    RoutingDecision,
)
from routing.registry import ProviderRegistry

logger = logging.getLogger(__name__)


# Task classification patterns
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

# Cost weights per task type (cheaper models preferred for simpler tasks)
_TASK_COST_PRIORITY: dict[str, float] = {
    "docs": 0.8,      # docs can use cheap models
    "test": 0.6,      # tests can use medium models
    "review": 0.4,    # reviews need better models
    "debug": 0.3,     # debugging needs good models
    "planning": 0.3,  # planning needs best models
    "code": 0.5,      # code generation varies
    "general": 0.5,
}


def classify_task(messages: list[Message]) -> str:
    """Classify task type from message content."""
    content = " ".join(m.content for m in messages).lower()
    for agent_type, patterns in _TASK_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, content):
                return agent_type
    return "general"


class UnifiedRouter:
    """Unified router combining capability, cost, latency, and tier strategies.

    Usage:
        router = UnifiedRouter(provider_registry)
        decision = await router.resolve(request)
    """

    def __init__(
        self,
        registry: ProviderRegistry,
        classifier: Callable[[list[Message]], str] | None = None,
        # Weights for scoring (0-1, higher = more important)
        cost_weight: float = 0.4,
        latency_weight: float = 0.3,
        tier_weight: float = 0.3,
        # Latency tracking
        latency_history_size: int = 100,
    ):
        self.registry = registry
        self._classifier = classifier or classify_task
        self._cost_weight = cost_weight
        self._latency_weight = latency_weight
        self._tier_weight = tier_weight
        # Latency tracking: provider_name -> list of recent latencies
        self._latency_history: dict[str, list[float]] = {}
        self._latency_history_size = latency_history_size
        # Tier preference: lower = preferred (0=free, 1=budget, 2=standard, 3=premium)
        self._provider_tiers: dict[str, int] = {}

    def set_provider_tier(self, provider_name: str, tier: int) -> None:
        """Set tier for provider (0=free, 1=budget, 2=standard, 3=premium)."""
        self._provider_tiers[provider_name] = tier

    async def resolve(
        self,
        request: CompletionRequest,
        required_capabilities: list[str] | None = None,
    ) -> RoutingDecision:
        """Resolve best provider for request.

        Args:
            request: Completion request
            required_capabilities: Required capabilities (e.g., ["tools", "vision"])

        Returns:
            RoutingDecision with selected provider
        """
        task_type = self._classifier(request.messages)
        providers = self.registry.list_providers()

        if not providers:
            raise RuntimeError("No providers registered")

        # Filter by capabilities if specified
        candidates = await self._filter_by_capabilities(
            providers, required_capabilities or []
        )

        if not candidates:
            # Fallback to all providers if none meet capabilities
            candidates = providers

        # Score each candidate
        scores: list[tuple[str, float]] = []
        for name in candidates:
            score = await self._score_provider(name, task_type)
            scores.append((name, score))

        # Sort by score (highest first)
        scores.sort(key=lambda x: x[1], reverse=True)

        best_name = scores[0][0]

        return RoutingDecision(
            provider=best_name,
            model=best_name,  # provider name IS the model (e.g., "gpt-4o")
            fallback_chain=[(name, name) for name, _ in scores[1:3]],
            strategy="unified",
            metadata={
                "task_type": task_type,
                "score": scores[0][1],
                "candidates": len(candidates),
                "all_scores": dict(scores),
            },
        )

    async def report_outcome(self, decision: RoutingDecision, outcome: Outcome) -> None:
        """Report outcome for learning."""
        provider_name = decision.provider
        if outcome.success and outcome.latency_ms > 0:
            if provider_name not in self._latency_history:
                self._latency_history[provider_name] = []
            history = self._latency_history[provider_name]
            history.append(outcome.latency_ms)
            # Keep only recent history
            if len(history) > self._latency_history_size:
                self._latency_history[provider_name] = history[-self._latency_history_size:]

    async def _filter_by_capabilities(
        self,
        providers: list[str],
        required: list[str],
    ) -> list[str]:
        """Filter providers by required capabilities."""
        if not required:
            return providers

        filtered = []
        for name in providers:
            caps = await self.registry.get_capabilities(name)
            if caps and all(getattr(caps, cap, False) for cap in required):
                filtered.append(name)

        return filtered

    async def _score_provider(self, name: str, task_type: str) -> float:
        """Score a provider for the given task type.

        Returns score 0-1 (higher = better).
        """
        provider = self.registry.get(name)
        if not provider:
            return 0.0

        # 1. Tier score (lower tier = higher score)
        tier = self._provider_tiers.get(name, 2)
        tier_score = 1.0 - (tier / 3.0)  # tier 0 = 1.0, tier 3 = 0.0

        # 2. Latency score (lower latency = higher score)
        latency_score = self._get_latency_score(name)

        # 3. Cost priority for task type
        cost_priority = _TASK_COST_PRIORITY.get(task_type, 0.5)

        # Weighted combination
        # For high cost-priority tasks, tier (free→paid) matters more
        # For low cost-priority tasks, latency matters more
        effective_cost_weight = self._cost_weight * cost_priority
        effective_latency_weight = self._latency_weight * (1.0 - cost_priority + 0.5)
        effective_tier_weight = self._tier_weight

        # Normalize weights
        total_weight = effective_cost_weight + effective_latency_weight + effective_tier_weight
        if total_weight > 0:
            effective_cost_weight /= total_weight
            effective_latency_weight /= total_weight
            effective_tier_weight /= total_weight

        score = (
            effective_tier_weight * tier_score
            + effective_latency_weight * latency_score
            + effective_cost_weight * tier_score  # tier approximates cost
        )

        return score

    def _get_latency_score(self, name: str) -> float:
        """Get normalized latency score (higher = faster)."""
        history = self._latency_history.get(name)
        if not history:
            return 0.5  # Unknown latency = neutral

        avg_latency = sum(history) / len(history)
        # Normalize: assume 1000ms = bad (0.0), 100ms = good (1.0)
        if avg_latency <= 100:
            return 1.0
        elif avg_latency >= 2000:
            return 0.0
        else:
            return 1.0 - (avg_latency - 100) / 1900

    def get_latency_stats(self) -> dict[str, dict]:
        """Get latency statistics per provider."""
        stats = {}
        for name, history in self._latency_history.items():
            if history:
                sorted_h = sorted(history)
                stats[name] = {
                    "count": len(history),
                    "avg_ms": sum(history) / len(history),
                    "p50_ms": sorted_h[len(sorted_h) // 2],
                    "p95_ms": sorted_h[int(len(sorted_h) * 0.95)],
                }
        return stats
