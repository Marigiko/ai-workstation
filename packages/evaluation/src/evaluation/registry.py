"""Base evaluator interface and registry."""

from typing import Protocol

from evaluation.models import EvalRequest, EvalResult


class Evaluator(Protocol):
    """Protocol for evaluators."""

    async def evaluate(self, request: EvalRequest) -> EvalResult:
        """Evaluate a response."""
        ...


class EvaluatorRegistry:
    """Registry for managing evaluators."""

    def __init__(self):
        self._evaluators: dict[str, Evaluator] = {}

    def register(self, name: str, evaluator: Evaluator) -> None:
        """Register an evaluator."""
        self._evaluators[name] = evaluator

    def get(self, name: str) -> Evaluator | None:
        """Get an evaluator by name."""
        return self._evaluators.get(name)

    def list_evaluators(self) -> list[str]:
        """List all registered evaluators."""
        return list(self._evaluators.keys())

    def exists(self, name: str) -> bool:
        """Check if an evaluator exists."""
        return name in self._evaluators
