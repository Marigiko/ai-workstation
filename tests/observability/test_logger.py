"""Tests for structured logger."""

import io

import pytest
from observability import LogLevel, StructuredLogger


@pytest.fixture
def output_stream():
    """Create an output stream."""
    return io.StringIO()


@pytest.fixture
def logger(output_stream):
    """Create a logger instance."""
    return StructuredLogger(service_name="test-service", output=output_stream)


def test_log_info(logger, output_stream):
    """Test info logging."""
    logger.info("Test message", key="value")

    output = output_stream.getvalue()
    assert "Test message" in output
    assert '"level": "info"' in output
    assert '"service": "test-service"' in output
    assert '"key": "value"' in output


def test_log_error(logger, output_stream):
    """Test error logging."""
    logger.error("Error occurred", error_code=500)

    output = output_stream.getvalue()
    assert "Error occurred" in output
    assert '"level": "error"' in output
    assert '"error_code": 500' in output


def test_log_levels(output_stream):
    """Test different log levels."""
    logger = StructuredLogger(
        service_name="test-service",
        level=LogLevel.DEBUG,
        output=output_stream,
    )
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")

    output = output_stream.getvalue()
    assert "Debug message" in output
    assert "Info message" in output
    assert "Warning message" in output
    assert "Error message" in output
    assert "Critical message" in output


def test_log_level_filtering(output_stream):
    """Test log level filtering."""
    logger = StructuredLogger(
        service_name="test-service",
        level=LogLevel.WARNING,
        output=output_stream,
    )

    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")

    output = output_stream.getvalue()
    assert "Debug message" not in output
    assert "Info message" not in output
    assert "Warning message" in output
    assert "Error message" in output


def test_trace_context(logger, output_stream):
    """Test trace context in logs."""
    logger.set_context(trace_id="trace-123", span_id="span-456")
    logger.info("Message with context")

    output = output_stream.getvalue()
    assert '"trace_id": "trace-123"' in output
    assert '"span_id": "span-456"' in output


def test_clear_context(logger, output_stream):
    """Test clearing trace context."""
    logger.set_context(trace_id="trace-123")
    logger.info("Message with context")
    logger.clear_context()
    logger.info("Message without context")

    output = output_stream.getvalue()
    lines = output.strip().split("\n")
    assert len(lines) == 2
    assert "trace-123" in lines[0]
    assert "trace_id" not in lines[1]


def test_list_logs(logger):
    """Test listing logs."""
    logger.info("Message 1")
    logger.warning("Message 2")
    logger.error("Message 3")

    logs = logger.list_logs()
    assert len(logs) == 3
    assert logs[0].level == LogLevel.INFO
    assert logs[1].level == LogLevel.WARNING
    assert logs[2].level == LogLevel.ERROR


def test_list_logs_with_level_filter(logger):
    """Test listing logs with level filter."""
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")

    logs = logger.list_logs(level=LogLevel.ERROR)
    assert len(logs) == 1
    assert logs[0].level == LogLevel.ERROR


def test_list_logs_limit(logger):
    """Test listing logs with limit."""
    for i in range(10):
        logger.info(f"Message {i}")

    logs = logger.list_logs(limit=5)
    assert len(logs) == 5


def test_clear_logs(logger):
    """Test clearing logs."""
    logger.info("Message 1")
    logger.info("Message 2")

    logger.clear_logs()

    logs = logger.list_logs()
    assert len(logs) == 0


def test_get_error_count(logger):
    """Test getting error count."""
    logger.info("Info message")
    logger.error("Error 1")
    logger.critical("Critical 1")
    logger.error("Error 2")

    assert logger.get_error_count() == 3


def test_get_error_rate(logger):
    """Test getting error rate."""
    logger.info("Info 1")
    logger.info("Info 2")
    logger.error("Error 1")

    error_rate = logger.get_error_rate()
    assert error_rate == pytest.approx(1.0 / 3.0)


def test_get_error_rate_no_logs(logger):
    """Test getting error rate with no logs."""
    error_rate = logger.get_error_rate()
    assert error_rate == 0.0
