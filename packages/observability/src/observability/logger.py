"""Structured logging."""

import json
import sys
from typing import Any

from observability.models import LogEntry, LogLevel


class StructuredLogger:
    """Structured logger with JSON output."""

    def __init__(
        self,
        service_name: str = "ai-workstation",
        level: LogLevel = LogLevel.INFO,
        output: Any = None,
    ):
        """Initialize structured logger.

        Args:
            service_name: Name of the service
            level: Minimum log level
            output: Output stream (default: sys.stdout)
        """
        self.service_name = service_name
        self.level = level
        self.output = output or sys.stdout
        self._logs: list[LogEntry] = []
        self._trace_id: str | None = None
        self._span_id: str | None = None

    def set_context(self, trace_id: str | None = None, span_id: str | None = None):
        """Set trace context for logs.

        Args:
            trace_id: Optional trace ID
            span_id: Optional span ID
        """
        self._trace_id = trace_id
        self._span_id = span_id

    def clear_context(self):
        """Clear trace context."""
        self._trace_id = None
        self._span_id = None

    def debug(self, message: str, **attributes):
        """Log debug message.

        Args:
            message: Log message
            **attributes: Additional attributes
        """
        self._log(LogLevel.DEBUG, message, **attributes)

    def info(self, message: str, **attributes):
        """Log info message.

        Args:
            message: Log message
            **attributes: Additional attributes
        """
        self._log(LogLevel.INFO, message, **attributes)

    def warning(self, message: str, **attributes):
        """Log warning message.

        Args:
            message: Log message
            **attributes: Additional attributes
        """
        self._log(LogLevel.WARNING, message, **attributes)

    def error(self, message: str, **attributes):
        """Log error message.

        Args:
            message: Log message
            **attributes: Additional attributes
        """
        self._log(LogLevel.ERROR, message, **attributes)

    def critical(self, message: str, **attributes):
        """Log critical message.

        Args:
            message: Log message
            **attributes: Additional attributes
        """
        self._log(LogLevel.CRITICAL, message, **attributes)

    def _log(self, level: LogLevel, message: str, **attributes):
        """Internal log method.

        Args:
            level: Log level
            message: Log message
            **attributes: Additional attributes
        """
        if self._should_log(level):
            entry = LogEntry(
                level=level,
                message=message,
                service=self.service_name,
                trace_id=self._trace_id,
                span_id=self._span_id,
                attributes=attributes,
            )
            self._logs.append(entry)
            self._write(entry)

    def _should_log(self, level: LogLevel) -> bool:
        """Check if level should be logged."""
        levels = [
            LogLevel.DEBUG,
            LogLevel.INFO,
            LogLevel.WARNING,
            LogLevel.ERROR,
            LogLevel.CRITICAL,
        ]
        return levels.index(level) >= levels.index(self.level)

    def _write(self, entry: LogEntry):
        """Write log entry to output.

        Args:
            entry: Log entry to write
        """
        log_dict = {
            "timestamp": entry.timestamp.isoformat(),
            "level": entry.level.value,
            "message": entry.message,
            "service": entry.service,
        }

        if entry.trace_id:
            log_dict["trace_id"] = entry.trace_id
        if entry.span_id:
            log_dict["span_id"] = entry.span_id
        if entry.attributes:
            log_dict.update(entry.attributes)

        self.output.write(json.dumps(log_dict) + "\n")
        self.output.flush()

    def list_logs(self, limit: int = 1000, level: LogLevel | None = None) -> list[LogEntry]:
        """List log entries.

        Args:
            limit: Maximum number of logs
            level: Optional filter by level

        Returns:
            List of log entries
        """
        logs = self._logs
        if level:
            logs = [log for log in logs if log.level == level]
        return logs[-limit:]

    def clear_logs(self):
        """Clear all logs."""
        self._logs.clear()

    def get_error_count(self) -> int:
        """Get count of error and critical logs."""
        return sum(1 for log in self._logs if log.level in [LogLevel.ERROR, LogLevel.CRITICAL])

    def get_error_rate(self) -> float:
        """Get error rate (errors / total logs)."""
        if not self._logs:
            return 0.0
        error_count = self.get_error_count()
        return error_count / len(self._logs)
