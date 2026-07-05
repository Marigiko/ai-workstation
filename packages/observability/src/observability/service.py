"""Observability service integrating tracing, metrics, and logging."""


from observability.logger import StructuredLogger
from observability.metrics import MetricsCollector
from observability.models import ObservabilitySummary, SpanStatus
from observability.tracer import Tracer


class ObservabilityService:
    """Unified observability service."""

    def __init__(self, service_name: str = "ai-workstation"):
        """Initialize observability service.

        Args:
            service_name: Name of the service
        """
        self.service_name = service_name
        self.tracer = Tracer(service_name)
        self.metrics = MetricsCollector(service_name)
        self.logger = StructuredLogger(service_name)

    def start_request(self, operation: str, attributes: dict | None = None) -> str:
        """Start tracking a request.

        Args:
            operation: Operation name
            attributes: Optional attributes

        Returns:
            Trace ID
        """
        trace_id = self.tracer.start_trace(operation, attributes)
        self.logger.set_context(trace_id=trace_id)

        # Record request start metric
        self.metrics.counter("requests_total", labels={"operation": operation})

        return trace_id

    def end_request(
        self,
        trace_id: str,
        status: SpanStatus = SpanStatus.OK,
        attributes: dict | None = None,
    ):
        """End tracking a request.

        Args:
            trace_id: Trace ID
            status: Request status
            attributes: Optional attributes
        """
        trace = self.tracer.get_trace(trace_id)
        if trace:
            self.tracer.end_span(trace.root_span.span_id, status, attributes)

            # Record latency
            self.metrics.histogram(
                "request_duration_ms",
                trace.duration_ms,
                labels={"operation": trace.root_span.name, "status": status.value},
            )

            # Record status
            if status == SpanStatus.ERROR:
                self.metrics.counter(
                    "requests_errors_total",
                    labels={"operation": trace.root_span.name},
                )

        self.logger.clear_context()

    def record_metric(self, name: str, value: float, labels: dict[str, str] | None = None):
        """Record a metric.

        Args:
            name: Metric name
            value: Metric value
            labels: Optional labels
        """
        self.metrics.gauge(name, value, labels)

    def log_event(self, level: str, message: str, **attributes):
        """Log an event.

        Args:
            level: Log level (debug, info, warning, error, critical)
            message: Log message
            **attributes: Additional attributes
        """
        log_method = getattr(self.logger, level, self.logger.info)
        log_method(message, **attributes)

    def get_summary(self) -> ObservabilitySummary:
        """Get observability summary.

        Returns:
            Observability summary
        """
        traces = self.tracer.list_traces(limit=1000)
        total_traces = len(traces)
        total_spans = sum(len(trace.spans) for trace in traces)

        # Calculate latency stats
        latencies = [trace.duration_ms for trace in traces]
        if latencies:
            sorted_latencies = sorted(latencies)
            avg_latency = sum(latencies) / len(latencies)
            p95_latency = sorted_latencies[int(len(sorted_latencies) * 0.95)]
            p99_latency = sorted_latencies[int(len(sorted_latencies) * 0.99)]
        else:
            avg_latency = 0.0
            p95_latency = 0.0
            p99_latency = 0.0

        # Calculate error rate
        error_traces = sum(1 for trace in traces if trace.status == SpanStatus.ERROR)
        error_rate = error_traces / total_traces if total_traces > 0 else 0.0

        return ObservabilitySummary(
            total_traces=total_traces,
            total_spans=total_spans,
            total_metrics=len(self.metrics.list_metrics()),
            total_logs=len(self.logger.list_logs()),
            error_rate=error_rate,
            avg_latency_ms=avg_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
        )

    def clear_all(self):
        """Clear all observability data."""
        self.tracer.clear_traces()
        self.metrics.clear_metrics()
        self.logger.clear_logs()
