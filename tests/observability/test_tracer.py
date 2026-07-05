"""Tests for tracer."""

import pytest
from observability import SpanStatus, Tracer


@pytest.fixture
def tracer():
    """Create a tracer instance."""
    return Tracer(service_name="test-service")


def test_start_trace(tracer):
    """Test starting a trace."""
    trace_id = tracer.start_trace("test-operation", {"key": "value"})

    assert trace_id is not None
    trace = tracer.get_trace(trace_id)
    assert trace is not None
    assert trace.root_span.name == "test-operation"
    assert trace.root_span.attributes["key"] == "value"


def test_start_span(tracer):
    """Test starting a span within a trace."""
    trace_id = tracer.start_trace("parent-operation")
    span_id = tracer.start_span(trace_id, "child-operation")

    assert span_id is not None
    trace = tracer.get_trace(trace_id)
    assert len(trace.spans) == 2


def test_end_span(tracer):
    """Test ending a span."""
    trace_id = tracer.start_trace("test-operation")
    span_id = tracer.start_span(trace_id, "child-operation")

    tracer.end_span(span_id, SpanStatus.OK, {"result": "success"})

    trace = tracer.get_trace(trace_id)
    span = next(s for s in trace.spans if s.span_id == span_id)
    assert span.status == SpanStatus.OK
    assert span.attributes["result"] == "success"
    assert span.duration_ms >= 0


def test_end_span_with_error(tracer):
    """Test ending a span with error status."""
    trace_id = tracer.start_trace("test-operation")
    span_id = tracer.start_span(trace_id, "failing-operation")

    tracer.end_span(span_id, SpanStatus.ERROR, {"error": "something went wrong"})

    trace = tracer.get_trace(trace_id)
    assert trace.status == SpanStatus.ERROR


def test_add_span_event(tracer):
    """Test adding an event to a span."""
    trace_id = tracer.start_trace("test-operation")
    span_id = tracer.start_span(trace_id, "operation-with-events")

    tracer.add_span_event(span_id, "checkpoint", {"step": 1})
    tracer.add_span_event(span_id, "checkpoint", {"step": 2})

    trace = tracer.get_trace(trace_id)
    span = next(s for s in trace.spans if s.span_id == span_id)
    assert len(span.events) == 2
    assert span.events[0]["name"] == "checkpoint"
    assert span.events[0]["attributes"]["step"] == 1


def test_list_traces(tracer):
    """Test listing traces."""
    tracer.start_trace("operation-1")
    tracer.start_trace("operation-2")
    tracer.start_trace("operation-3")

    traces = tracer.list_traces(limit=2)
    assert len(traces) == 2


def test_clear_traces(tracer):
    """Test clearing traces."""
    tracer.start_trace("operation-1")
    tracer.start_trace("operation-2")

    tracer.clear_traces()

    traces = tracer.list_traces()
    assert len(traces) == 0


def test_get_nonexistent_trace(tracer):
    """Test getting a nonexistent trace."""
    trace = tracer.get_trace("nonexistent-id")
    assert trace is None


def test_start_span_invalid_trace(tracer):
    """Test starting a span with invalid trace ID."""
    with pytest.raises(ValueError, match="Trace .* not found"):
        tracer.start_span("invalid-trace-id", "operation")


def test_end_span_invalid_span(tracer):
    """Test ending an invalid span."""
    with pytest.raises(ValueError, match="Span .* not found"):
        tracer.end_span("invalid-span-id")
