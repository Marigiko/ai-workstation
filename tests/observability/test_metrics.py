"""Tests for metrics collector."""

import pytest
from observability import MetricsCollector, MetricType


@pytest.fixture
def collector():
    """Create a metrics collector instance."""
    return MetricsCollector(service_name="test-service")


def test_counter(collector):
    """Test counter metric."""
    collector.counter("requests_total", 1.0, {"method": "GET"})
    collector.counter("requests_total", 1.0, {"method": "GET"})
    collector.counter("requests_total", 1.0, {"method": "POST"})

    assert collector.get_counter("requests_total", {"method": "GET"}) == 2.0
    assert collector.get_counter("requests_total", {"method": "POST"}) == 1.0


def test_gauge(collector):
    """Test gauge metric."""
    collector.gauge("temperature", 25.5, {"location": "room1"})
    assert collector.get_gauge("temperature", {"location": "room1"}) == 25.5

    collector.gauge("temperature", 26.0, {"location": "room1"})
    assert collector.get_gauge("temperature", {"location": "room1"}) == 26.0


def test_histogram(collector):
    """Test histogram metric."""
    collector.histogram("request_duration_ms", 100.0, {"endpoint": "/api"})
    collector.histogram("request_duration_ms", 150.0, {"endpoint": "/api"})
    collector.histogram("request_duration_ms", 200.0, {"endpoint": "/api"})

    stats = collector.get_histogram_stats("request_duration_ms", {"endpoint": "/api"})
    assert stats["count"] == 3
    assert stats["sum"] == 450.0
    assert stats["avg"] == 150.0
    assert stats["min"] == 100.0
    assert stats["max"] == 200.0


def test_histogram_percentiles(collector):
    """Test histogram percentile calculations."""
    for i in range(1, 101):
        collector.histogram("latency", float(i))

    stats = collector.get_histogram_stats("latency")
    assert stats["count"] == 100
    # Percentiles are approximate due to index calculation
    assert 49.0 <= stats["p50"] <= 51.0
    assert 94.0 <= stats["p95"] <= 96.0
    assert 98.0 <= stats["p99"] <= 100.0


def test_empty_histogram(collector):
    """Test empty histogram stats."""
    stats = collector.get_histogram_stats("nonexistent")
    assert stats["count"] == 0
    assert stats["sum"] == 0.0
    assert stats["avg"] == 0.0


def test_list_metrics(collector):
    """Test listing metrics."""
    collector.counter("requests", 1.0)
    collector.gauge("temperature", 25.0)
    collector.histogram("latency", 100.0)

    metrics = collector.list_metrics()
    assert len(metrics) == 3
    assert metrics[0].type == MetricType.COUNTER
    assert metrics[1].type == MetricType.GAUGE
    assert metrics[2].type == MetricType.HISTOGRAM


def test_list_metrics_limit(collector):
    """Test listing metrics with limit."""
    for i in range(10):
        collector.counter(f"metric_{i}", 1.0)

    metrics = collector.list_metrics(limit=5)
    assert len(metrics) == 5


def test_clear_metrics(collector):
    """Test clearing metrics."""
    collector.counter("requests", 1.0)
    collector.gauge("temperature", 25.0)

    collector.clear_metrics()

    metrics = collector.list_metrics()
    assert len(metrics) == 0
    assert collector.get_counter("requests") == 0.0
    assert collector.get_gauge("temperature") == 0.0


def test_export_prometheus(collector):
    """Test Prometheus export."""
    collector.counter("http_requests_total", 5.0, {"method": "GET"})
    collector.gauge("temperature_celsius", 25.5, {"location": "room1"})
    collector.histogram("request_duration_seconds", 0.5, {"endpoint": "/api"})

    output = collector.export_prometheus()

    assert "http_requests_total" in output
    assert "method=" in output
    assert "temperature_celsius" in output
    assert "request_duration_seconds_count" in output
    assert "request_duration_seconds_sum" in output


def test_counter_with_description(collector):
    """Test counter with description."""
    collector.counter("requests_total", 1.0, description="Total HTTP requests")

    metrics = collector.list_metrics()
    assert len(metrics) == 1
    assert metrics[0].description == "Total HTTP requests"
