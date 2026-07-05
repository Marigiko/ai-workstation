"""Metrics collection and export."""

from collections import defaultdict

from observability.models import Metric, MetricType


class MetricsCollector:
    """Collects and manages metrics."""

    def __init__(self, service_name: str = "ai-workstation"):
        """Initialize metrics collector.

        Args:
            service_name: Name of the service
        """
        self.service_name = service_name
        self._metrics: list[Metric] = []
        self._counters: dict[str, float] = defaultdict(float)
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = defaultdict(list)

    def counter(
        self,
        name: str,
        value: float = 1.0,
        labels: dict[str, str] | None = None,
        description: str = "",
    ):
        """Increment a counter metric.

        Args:
            name: Metric name
            value: Value to increment by
            labels: Optional labels
            description: Optional description
        """
        key = self._make_key(name, labels)
        self._counters[key] += value

        metric = Metric(
            name=name,
            type=MetricType.COUNTER,
            value=self._counters[key],
            labels=labels or {},
            description=description,
        )
        self._metrics.append(metric)

    def gauge(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
        description: str = "",
    ):
        """Set a gauge metric.

        Args:
            name: Metric name
            value: Gauge value
            labels: Optional labels
            description: Optional description
        """
        key = self._make_key(name, labels)
        self._gauges[key] = value

        metric = Metric(
            name=name,
            type=MetricType.GAUGE,
            value=value,
            labels=labels or {},
            description=description,
        )
        self._metrics.append(metric)

    def histogram(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
        description: str = "",
    ):
        """Record a histogram observation.

        Args:
            name: Metric name
            value: Observed value
            labels: Optional labels
            description: Optional description
        """
        key = self._make_key(name, labels)
        self._histograms[key].append(value)

        metric = Metric(
            name=name,
            type=MetricType.HISTOGRAM,
            value=value,
            labels=labels or {},
            description=description,
        )
        self._metrics.append(metric)

    def _make_key(self, name: str, labels: dict[str, str] | None) -> str:
        """Create a unique key for a metric with labels."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}:{label_str}"

    def get_counter(self, name: str, labels: dict[str, str] | None = None) -> float:
        """Get counter value.

        Args:
            name: Metric name
            labels: Optional labels

        Returns:
            Counter value
        """
        key = self._make_key(name, labels)
        return self._counters.get(key, 0.0)

    def get_gauge(self, name: str, labels: dict[str, str] | None = None) -> float:
        """Get gauge value.

        Args:
            name: Metric name
            labels: Optional labels

        Returns:
            Gauge value
        """
        key = self._make_key(name, labels)
        return self._gauges.get(key, 0.0)

    def get_histogram_stats(
        self,
        name: str,
        labels: dict[str, str] | None = None,
    ) -> dict[str, float]:
        """Get histogram statistics.

        Args:
            name: Metric name
            labels: Optional labels

        Returns:
            Dictionary with count, sum, avg, min, max, p50, p95, p99
        """
        key = self._make_key(name, labels)
        values = self._histograms.get(key, [])

        if not values:
            return {
                "count": 0,
                "sum": 0.0,
                "avg": 0.0,
                "min": 0.0,
                "max": 0.0,
                "p50": 0.0,
                "p95": 0.0,
                "p99": 0.0,
            }

        sorted_values = sorted(values)
        count = len(sorted_values)
        total = sum(sorted_values)

        return {
            "count": count,
            "sum": total,
            "avg": total / count,
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "p50": self._percentile(sorted_values, 50),
            "p95": self._percentile(sorted_values, 95),
            "p99": self._percentile(sorted_values, 99),
        }

    def _percentile(self, sorted_values: list[float], percentile: int) -> float:
        """Calculate percentile from sorted values."""
        if not sorted_values:
            return 0.0
        index = int(len(sorted_values) * percentile / 100)
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]

    def list_metrics(self, limit: int = 1000) -> list[Metric]:
        """List recent metrics.

        Args:
            limit: Maximum number of metrics

        Returns:
            List of metrics
        """
        return self._metrics[-limit:]

    def clear_metrics(self):
        """Clear all metrics."""
        self._metrics.clear()
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format.

        Returns:
            Prometheus-formatted metrics string
        """
        lines = []

        # Export counters
        for key, value in self._counters.items():
            name = key.split(":")[0]
            labels = self._parse_labels(key)
            label_str = self._format_labels(labels)
            lines.append(f"{name}{label_str} {value}")

        # Export gauges
        for key, value in self._gauges.items():
            name = key.split(":")[0]
            labels = self._parse_labels(key)
            label_str = self._format_labels(labels)
            lines.append(f"{name}{label_str} {value}")

        # Export histograms
        for key, values in self._histograms.items():
            name = key.split(":")[0]
            labels = self._parse_labels(key)
            label_str = self._format_labels(labels)
            stats = self.get_histogram_stats(name, labels)
            lines.append(f"{name}_count{label_str} {stats['count']}")
            lines.append(f"{name}_sum{label_str} {stats['sum']}")

        return "\n".join(lines)

    def _parse_labels(self, key: str) -> dict[str, str]:
        """Parse labels from key."""
        if ":" not in key:
            return {}
        label_str = key.split(":", 1)[1]
        labels = {}
        for pair in label_str.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                labels[k] = v
        return labels

    def _format_labels(self, labels: dict[str, str]) -> str:
        """Format labels for Prometheus."""
        if not labels:
            return ""
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{{{label_str}}}"
