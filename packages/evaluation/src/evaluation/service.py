"""Evaluation service for coordinating evaluations."""

import time
import uuid

from providers import BaseProvider

from evaluation.evaluators import (
    CompletenessEvaluator,
    CorrectnessEvaluator,
    CostEvaluator,
    FaithfulnessEvaluator,
    GroundingEvaluator,
    LatencyEvaluator,
    RelevanceEvaluator,
    TokensEvaluator,
)
from evaluation.models import (
    BenchmarkResult,
    EvalMetric,
    EvalRequest,
    EvalResult,
)
from evaluation.registry import EvaluatorRegistry


class EvaluationService:
    """Service for coordinating evaluations."""

    def __init__(self, provider: BaseProvider):
        """Initialize evaluation service with LLM provider."""
        self.provider = provider
        self.registry = EvaluatorRegistry()
        self._register_default_evaluators()

    def _register_default_evaluators(self) -> None:
        """Register default evaluators."""
        # Objective evaluators (no LLM needed)
        self.registry.register(EvalMetric.COST.value, CostEvaluator())
        self.registry.register(EvalMetric.LATENCY.value, LatencyEvaluator())
        self.registry.register(EvalMetric.TOKENS.value, TokensEvaluator())

        # LLM-based evaluators
        self.registry.register(EvalMetric.RELEVANCE.value, RelevanceEvaluator(self.provider))
        self.registry.register(EvalMetric.GROUNDING.value, GroundingEvaluator(self.provider))
        self.registry.register(EvalMetric.FAITHFULNESS.value, FaithfulnessEvaluator(self.provider))
        self.registry.register(EvalMetric.CORRECTNESS.value, CorrectnessEvaluator(self.provider))
        self.registry.register(EvalMetric.COMPLETENESS.value, CompletenessEvaluator(self.provider))

    async def evaluate(
        self,
        request: EvalRequest,
        metrics: list[EvalMetric] | None = None,
    ) -> list[EvalResult]:
        """Evaluate a response on specified metrics.

        Args:
            request: Evaluation request
            metrics: List of metrics to evaluate (None = all metrics)

        Returns:
            List of evaluation results
        """
        if metrics is None:
            metrics = list(EvalMetric)

        results = []
        for metric in metrics:
            evaluator = self.registry.get(metric.value)
            if evaluator:
                result = await evaluator.evaluate(request)
                results.append(result)

        return results

    async def evaluate_single(
        self,
        request: EvalRequest,
        metric: EvalMetric,
    ) -> EvalResult:
        """Evaluate a response on a single metric.

        Args:
            request: Evaluation request
            metric: Metric to evaluate

        Returns:
            Evaluation result
        """
        evaluator = self.registry.get(metric.value)
        if not evaluator:
            raise ValueError(f"Evaluator for metric {metric.value} not found")

        return await evaluator.evaluate(request)

    async def run_benchmark(
        self,
        test_cases: list[EvalRequest],
        metrics: list[EvalMetric] | None = None,
    ) -> BenchmarkResult:
        """Run a benchmark suite.

        Args:
            test_cases: List of test cases
            metrics: Metrics to evaluate (None = all metrics)

        Returns:
            Benchmark result with aggregate scores
        """
        start_time = time.time()

        all_results = []
        for test_case in test_cases:
            results = await self.evaluate(test_case, metrics)
            all_results.extend(results)

        total_time_ms = (time.time() - start_time) * 1000

        # Calculate aggregate scores
        aggregate_scores = {}
        metric_totals = {}
        metric_counts = {}

        for result in all_results:
            metric_name = result.metric.value
            if metric_name not in metric_totals:
                metric_totals[metric_name] = 0.0
                metric_counts[metric_name] = 0

            metric_totals[metric_name] += result.score
            metric_counts[metric_name] += 1

        for metric_name in metric_totals:
            aggregate_scores[metric_name] = metric_totals[metric_name] / metric_counts[metric_name]

        return BenchmarkResult(
            benchmark_id=str(uuid.uuid4()),
            benchmark_name=f"benchmark-{int(time.time())}",
            results=all_results,
            aggregate_scores=aggregate_scores,
            total_time_ms=total_time_ms,
        )

    def list_evaluators(self) -> list[str]:
        """List available evaluators."""
        return self.registry.list_evaluators()
