"""Distributed tracing with OpenTelemetry."""

import logging
import uuid
from datetime import UTC, datetime

from observability.models import Span, SpanStatus, Trace

logger = logging.getLogger(__name__)


class Tracer:
    """Distributed tracer using OpenTelemetry-compatible format.

    Supports optional persistence to PostgreSQL for historical analysis.
    """

    def __init__(
        self,
        service_name: str = "ai-workstation",
        session_factory=None,
    ):
        """Initialize tracer.

        Args:
            service_name: Name of the service
            session_factory: Optional async session factory for persisting traces.
                If provided, completed traces are saved to PostgreSQL.
        """
        self.service_name = service_name
        self._traces: dict[str, Trace] = {}
        self._active_spans: dict[str, Span] = {}
        self._session_factory = session_factory

    def start_trace(self, name: str, attributes: dict | None = None) -> str:
        """Start a new trace.

        Args:
            name: Trace name
            attributes: Optional attributes

        Returns:
            Trace ID
        """
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())
        start_time = datetime.now(UTC)

        root_span = Span(
            trace_id=trace_id,
            span_id=span_id,
            name=name,
            service=self.service_name,
            start_time=start_time,
            end_time=start_time,
            duration_ms=0.0,
            status=SpanStatus.OK,
            attributes=attributes or {},
        )

        trace = Trace(
            trace_id=trace_id,
            root_span=root_span,
            spans=[root_span],
            start_time=start_time,
            end_time=start_time,
            duration_ms=0.0,
            status=SpanStatus.OK,
        )

        self._traces[trace_id] = trace
        self._active_spans[span_id] = root_span

        return trace_id

    def start_span(
        self,
        trace_id: str,
        name: str,
        parent_span_id: str | None = None,
        attributes: dict | None = None,
    ) -> str:
        """Start a new span within a trace.

        Args:
            trace_id: Trace ID
            name: Span name
            parent_span_id: Optional parent span ID
            attributes: Optional attributes

        Returns:
            Span ID
        """
        if trace_id not in self._traces:
            raise ValueError(f"Trace {trace_id} not found")

        span_id = str(uuid.uuid4())
        start_time = datetime.now(UTC)

        span = Span(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            name=name,
            service=self.service_name,
            start_time=start_time,
            end_time=start_time,
            duration_ms=0.0,
            status=SpanStatus.OK,
            attributes=attributes or {},
        )

        self._traces[trace_id].spans.append(span)
        self._active_spans[span_id] = span

        return span_id

    async def end_span(
        self,
        span_id: str,
        status: SpanStatus = SpanStatus.OK,
        attributes: dict | None = None,
    ):
        """End a span.

        Args:
            span_id: Span ID
            status: Span status
            attributes: Optional additional attributes
        """
        if span_id not in self._active_spans:
            raise ValueError(f"Span {span_id} not found or already ended")

        span = self._active_spans.pop(span_id)
        end_time = datetime.now(UTC)
        duration_ms = (end_time - span.start_time).total_seconds() * 1000

        span.end_time = end_time
        span.duration_ms = duration_ms
        span.status = status

        if attributes:
            span.attributes.update(attributes)

        # Update trace
        trace = self._traces[span.trace_id]
        trace.end_time = end_time
        trace.duration_ms = (end_time - trace.start_time).total_seconds() * 1000

        # Update trace status if any span has error
        if status == SpanStatus.ERROR:
            trace.status = SpanStatus.ERROR

        # Persist trace when root span ends
        if span.parent_span_id is None and self._session_factory:
            await self._persist_trace(trace)

    def add_span_event(self, span_id: str, name: str, attributes: dict | None = None):
        """Add an event to a span.

        Args:
            span_id: Span ID
            name: Event name
            attributes: Optional event attributes
        """
        if span_id not in self._active_spans:
            # Check if span is in trace
            for trace in self._traces.values():
                for span in trace.spans:
                    if span.span_id == span_id:
                        span.events.append({
                            "name": name,
                            "timestamp": datetime.now(UTC).isoformat(),
                            "attributes": attributes or {},
                        })
                        return
            raise ValueError(f"Span {span_id} not found")

        span = self._active_spans[span_id]
        span.events.append({
            "name": name,
            "timestamp": datetime.now(UTC).isoformat(),
            "attributes": attributes or {},
        })

    def get_trace(self, trace_id: str) -> Trace | None:
        """Get a trace by ID.

        Args:
            trace_id: Trace ID

        Returns:
            Trace if found, None otherwise
        """
        return self._traces.get(trace_id)

    def list_traces(self, limit: int = 100) -> list[Trace]:
        """List recent traces.

        Args:
            limit: Maximum number of traces

        Returns:
            List of traces
        """
        traces = list(self._traces.values())
        traces.sort(key=lambda t: t.start_time, reverse=True)
        return traces[:limit]

    def clear_traces(self):
        """Clear all traces."""
        self._traces.clear()
        self._active_spans.clear()

    async def list_persisted_traces(
        self,
        limit: int = 100,
        status: str | None = None,
        service_name: str | None = None,
    ) -> list[dict]:
        """List traces from PostgreSQL.

        Args:
            limit: Maximum number of traces
            status: Filter by status (ok/error)
            service_name: Filter by service name

        Returns:
            List of trace dictionaries
        """
        if not self._session_factory:
            return []

        try:
            from sqlalchemy import select

            from observability.trace_model import TraceModel

            async with self._session_factory() as session:
                stmt = select(TraceModel).order_by(TraceModel.start_time.desc()).limit(limit)
                if status:
                    stmt = stmt.where(TraceModel.status == status)
                if service_name:
                    stmt = stmt.where(TraceModel.service_name == service_name)

                result = await session.execute(stmt)
                traces = result.scalars().all()
                return [t.to_dict() for t in traces]
        except Exception as e:
            logger.warning("Failed to query traces: %s", e)
            return []

    async def _persist_trace(self, trace: Trace) -> None:
        """Persist completed trace to PostgreSQL."""
        if not self._session_factory:
            return

        try:
            from observability.trace_model import TraceModel

            async with self._session_factory() as session:
                trace_model = TraceModel.from_trace(trace)
                session.add(trace_model)
                await session.commit()
        except Exception as e:
            logger.warning("Failed to persist trace %s: %s", trace.trace_id, e)
