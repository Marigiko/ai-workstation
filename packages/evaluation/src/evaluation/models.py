"""Evaluation models for measuring response quality."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class EvalMetric(StrEnum):
    """Evaluation metrics."""

    RELEVANCE = "relevance"
    GROUNDING = "grounding"
    FAITHFULNESS = "faithfulness"
    CORRECTNESS = "correctness"
    COMPLETENESS = "completeness"
    COST = "cost"
    LATENCY = "latency"
    TOKENS = "tokens"


class EvalResult(BaseModel):
    """Result of an evaluation."""

    id: str = Field(description="Unique evaluation ID")
    metric: EvalMetric = Field(description="Metric being evaluated")
    score: float = Field(description="Score from 0.0 to 1.0", ge=0.0, le=1.0)
    details: dict[str, Any] = Field(default_factory=dict, description="Additional details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EvalRequest(BaseModel):
    """Request to evaluate a response."""

    query: str = Field(description="Original query")
    response: str = Field(description="Response to evaluate")
    context: list[str] = Field(default_factory=list, description="Context used")
    expected_response: str | None = Field(default=None, description="Expected response")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class EvalBenchmark(BaseModel):
    """Benchmark suite for regression testing."""

    id: str = Field(description="Unique benchmark ID")
    name: str = Field(description="Benchmark name")
    description: str = Field(description="Benchmark description")
    test_cases: list[EvalRequest] = Field(default_factory=list, description="Test cases")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BenchmarkResult(BaseModel):
    """Result of running a benchmark."""

    benchmark_id: str = Field(description="Benchmark ID")
    benchmark_name: str = Field(description="Benchmark name")
    results: list[EvalResult] = Field(description="Evaluation results")
    aggregate_scores: dict[str, float] = Field(description="Aggregate scores by metric")
    total_time_ms: float = Field(description="Total evaluation time")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
