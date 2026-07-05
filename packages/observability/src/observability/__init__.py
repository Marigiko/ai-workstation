"""Observability package for tracing, metrics, and logging."""

from observability.logger import StructuredLogger
from observability.metrics import MetricsCollector
from observability.models import (
    LogEntry,
    LogLevel,
    Metric,
    MetricType,
    ObservabilitySummary,
    Span,
    SpanStatus,
    Trace,
)
from observability.service import ObservabilityService
from observability.tracer import Tracer

__version__ = "0.1.0"

__all__ = [
    "LogEntry",
    "LogLevel",
    "Metric",
    "MetricType",
    "MetricsCollector",
    "ObservabilityService",
    "ObservabilitySummary",
    "Span",
    "SpanStatus",
    "StructuredLogger",
    "Trace",
    "Tracer",
]
