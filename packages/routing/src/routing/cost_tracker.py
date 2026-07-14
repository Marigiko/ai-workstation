"""Cost tracking for routing decisions."""

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class CostRecord:
    """Record of a routing decision cost."""

    provider: str
    model: str
    cost_usd: float
    tokens_used: int
    timestamp: datetime


class CostTracker:
    """Track costs across routing decisions."""

    def __init__(self):
        self._records: list[CostRecord] = []

    def record(self, provider: str, model: str, cost_usd: float, tokens_used: int):
        """Record a cost."""
        self._records.append(
            CostRecord(
                provider=provider,
                model=model,
                cost_usd=cost_usd,
                tokens_used=tokens_used,
                timestamp=datetime.now(UTC),
            )
        )

    def total_cost(self, provider: str | None = None) -> float:
        """Get total cost, optionally filtered by provider."""
        if provider:
            return sum(r.cost_usd for r in self._records if r.provider == provider)
        return sum(r.cost_usd for r in self._records)

    def total_tokens(self, provider: str | None = None) -> int:
        """Get total tokens used, optionally filtered by provider."""
        if provider:
            return sum(r.tokens_used for r in self._records if r.provider == provider)
        return sum(r.tokens_used for r in self._records)

    def get_records(self, limit: int = 100) -> list[CostRecord]:
        """Get recent cost records."""
        return self._records[-limit:]

    def reset(self):
        """Reset all records."""
        self._records.clear()
