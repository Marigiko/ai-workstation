"""Tests for observability service."""

import pytest
from observability import ObservabilityService, SpanStatus


@pytest.fixture
def service():
    """Create an observability service instance."""
    return ObservabilityService(service_name="test-service")


def test_start_request(service):
    """Test starting a request."""
    trace_id = service.start_request("test-operation", {"key": "value"})

    assert trace_id is not None
    trace = service.tracer.get_trace(trace_id)
    assert trace is not None
    assert trace.root_span.name == "test-operation"


def test_end_request(service):
    """Test ending a request."""
    trace_id = service.start_request("test-operation")
    service.end_request(trace_id, SpanStatus.OK, {"result": "success"})

    trace = service.tracer.get_trace(trace_id)
    assert trace.status == SpanStatus.OK


def test_end_request_with_error(service):
    """Test ending a request with error."""
    trace_id = service.start_request("test-operation")
    service.end_request(trace_id, SpanStatus.ERROR)

    trace = service.tracer.get_trace(trace_id)
    assert trace.status == SpanStatus.ERROR


def test_record_metric(service):
    """Test recording a metric."""
    service.record_metric("temperature", 25.5, {"location": "room1"})

    assert service.metrics.get_gauge("temperature", {"location": "room1"}) == 25.5


def test_log_event(service):
    """Test logging an event."""
    service.log_event("info", "Test message", key="value")

    logs = service.logger.list_logs()
    assert len(logs) == 1
    assert logs[0].message == "Test message"


def test_get_summary(service):
    """Test getting observability summary."""
    # Create some traces
    trace_id1 = service.start_request("operation-1")
    service.end_request(trace_id1, SpanStatus.OK)

    trace_id2 = service.start_request("operation-2")
    service.end_request(trace_id2, SpanStatus.ERROR)

    # Record some metrics
    service.record_metric("temperature", 25.0)

    # Log some events
    service.log_event("info", "Test message")

    summary = service.get_summary()

    assert summary.total_traces == 2
    assert summary.total_spans >= 2
    assert summary.total_metrics >= 1
    assert summary.total_logs >= 1
    assert summary.error_rate == 0.5  # 1 error out of 2 traces


def test_get_summary_empty(service):
    """Test getting summary with no data."""
    summary = service.get_summary()

    assert summary.total_traces == 0
    assert summary.total_spans == 0
    assert summary.total_metrics == 0
    assert summary.total_logs == 0
    assert summary.error_rate == 0.0
    assert summary.avg_latency_ms == 0.0


def test_clear_all(service):
    """Test clearing all data."""
    service.start_request("operation")
    service.record_metric("temperature", 25.0)
    service.log_event("info", "Test message")

    service.clear_all()

    summary = service.get_summary()
    assert summary.total_traces == 0
    assert summary.total_metrics == 0
    assert summary.total_logs == 0


def test_request_latency_tracking(service):
    """Test that request latency is tracked."""
    import time

    trace_id = service.start_request("slow-operation")
    time.sleep(0.01)  # Sleep for 10ms
    service.end_request(trace_id)

    # Check with both operation and status labels
    stats = service.metrics.get_histogram_stats(
        "request_duration_ms",
        {"operation": "slow-operation", "status": "ok"},
    )
    assert stats["count"] == 1
    assert stats["sum"] >= 10.0  # At least 10ms


def test_error_counter(service):
    """Test that errors are counted."""
    trace_id1 = service.start_request("operation-1")
    service.end_request(trace_id1, SpanStatus.OK)

    trace_id2 = service.start_request("operation-2")
    service.end_request(trace_id2, SpanStatus.ERROR)

    error_count = service.metrics.get_counter("requests_errors_total", {"operation": "operation-2"})
    assert error_count == 1.0
