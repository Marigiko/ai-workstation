"""Tiered token-budget router — cascades free → paid providers."""

import logging

from contracts import (
    CompletionRequest,
    Outcome,
    RoutingDecision,
    RoutingError,
    Tier,
    TokenBudget,
)
from routing.registry import ProviderRegistry

logger = logging.getLogger(__name__)


class TieredRouter:
    """Routes through ordered model tiers, respecting token budgets.

    Walks tiers in order. When a tier's budget is exhausted, moves to the next.
    Typical cascade: free tokens (OpenCode) → free tokens (Gemini) → paid (Claude/OpenAI).
    """

    def __init__(
        self,
        registry: ProviderRegistry,
        tiers: list[Tier],
    ):
        self.registry = registry
        self.tiers = tiers
        self._budgets: dict[str, TokenBudget] = {
            t.name: TokenBudget(tier_name=t.name, limit=t.token_budget) for t in tiers
        }

    async def resolve(self, request: CompletionRequest) -> RoutingDecision:
        all_models: list[str] = []
        for t in self.tiers:
            all_models.extend(t.models)

        for tier_idx, tier in enumerate(self.tiers):
            budget = self._budgets[tier.name]
            if budget.is_exhausted:
                continue

            for model_idx, model in enumerate(tier.models):
                provider_name = model.split("/")[0] if "/" in model else model.split("-")[0]
                provider = self.registry.get(provider_name)
                if not provider:
                    continue

                try:
                    is_healthy = await provider.health()
                except Exception:
                    is_healthy = False
                if not is_healthy:
                    continue

                fallback_chain = [
                    (m.split("/")[0] if "/" in m else m.split("-")[0], m)
                    for m in tier.models[model_idx + 1 :]
                ]
                for later_tier in self.tiers[tier_idx + 1 :]:
                    fallback_chain.extend(
                        [
                            (m.split("/")[0] if "/" in m else m.split("-")[0], m)
                            for m in later_tier.models
                        ]
                    )

                return RoutingDecision(
                    provider=provider_name,
                    model=model,
                    fallback_chain=fallback_chain[:3],
                    estimated_cost_usd=0.0,
                    strategy="tiered",
                    metadata={
                        "tier_name": tier.name,
                        "tier_index": tier_idx,
                        "model_index": model_idx,
                        "budget_remaining": budget.remaining,
                        "all_models": all_models,
                    },
                )

        if self.tiers and self.tiers[-1].models:
            model = self.tiers[-1].models[0]
            provider_name = model.split("/")[0] if "/" in model else model.split("-")[0]
            return RoutingDecision(
                provider=provider_name,
                model=model,
                fallback_chain=[],
                strategy="tiered_fallback",
                metadata={"tier_exhausted": True},
            )

        raise RoutingError("No models available in any tier")

    async def report_outcome(self, decision: RoutingDecision, outcome: Outcome) -> None:
        tier_name = decision.metadata.get("tier_name")
        if tier_name and tier_name in self._budgets and outcome.tokens_used > 0:
            self._budgets[tier_name].consumed += outcome.tokens_used
            logger.debug(
                "Tier %s: %d tokens consumed, %d remaining",
                tier_name,
                outcome.tokens_used,
                self._budgets[tier_name].remaining,
            )
