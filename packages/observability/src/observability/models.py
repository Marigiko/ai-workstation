"""Observability models for tracing, metrics, and logging."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class SpanStatus(StrEnum):
    """Status of a span."""

    OK = "ok"
    ERROR = "error"
    UNSET = "unset"


class Span(BaseModel):
    """Represents a trace span."""

    trace_id: str = Field(description="Unique trace ID")
    span_id: str = Field(description="Unique span ID")
    parent_span_id: str | None = Field(default=None, description="Parent span ID")
    name: str = Field(description="Span name")
    service: str = Field(description="Service name")
    start_time: datetime = Field(description="Start time")
    end_time: datetime = Field(description="End time")
    duration_ms: float = Field(description="Duration in milliseconds")
    status: SpanStatus = Field(default=SpanStatus.OK, description="Span status")
    attributes: dict[str, Any] = Field(default_factory=dict, description="Span attributes")
    events: list[dict[str, Any]] = Field(default_factory=list, description="Span events")


class Trace(BaseModel):
    """Represents a complete trace."""

    trace_id: str = Field(description="Unique trace ID")
    root_span: Span = Field(description="Root span")
    spans: list[Span] = Field(default_factory=list, description="All spans in trace")
    start_time: datetime = Field(description="Trace start time")
    end_time: datetime = Field(description="Trace end time")
    duration_ms: float = Field(description="Total duration in milliseconds")
    status: SpanStatus = Field(description="Overall trace status")


class MetricType(StrEnum):
    """Type of metric."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


class Metric(BaseModel):
    """Represents a metric."""

    name: str = Field(description="Metric name")
    type: MetricType = Field(description="Metric type")
    value: float = Field(description="Metric value")
    labels: dict[str, str] = Field(default_factory=dict, description="Metric labels")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Metric timestamp")
    description: str = Field(default="", description="Metric description")


class LogLevel(StrEnum):
    """Log level."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogEntry(BaseModel):
    """Represents a log entry."""

    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Log timestamp")
    level: LogLevel = Field(description="Log level")
    message: str = Field(description="Log message")
    service: str = Field(default="ai-workstation", description="Service name")
    trace_id: str | None = Field(default=None, description="Associated trace ID")
    span_id: str | None = Field(default=None, description="Associated span ID")
    attributes: dict[str, Any] = Field(default_factory=dict, description="Log attributes")


class ObservabilitySummary(BaseModel):
    """Summary of observability data."""

    total_traces: int = Field(description="Total number of traces")
    total_spans: int = Field(description="Total number of spans")
    total_metrics: int = Field(description="Total number of metrics")
    total_logs: int = Field(description="Total number of logs")
    error_rate: float = Field(description="Error rate (0.0-1.0)")
    avg_latency_ms: float = Field(description="Average latency in milliseconds")
    p95_latency_ms: float = Field(description="95th percentile latency in milliseconds")
    p99_latency_ms: float = Field(description="99th percentile latency in milliseconds")
