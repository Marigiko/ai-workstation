"""Database model for persisting traces."""

from __future__ import annotations

from datetime import datetime

from conversation.models.base import Base
from sqlalchemy import JSON, DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column


class TraceModel(Base):
    """Persisted trace model for PostgreSQL storage."""

    __tablename__ = "traces"

    trace_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    service_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    root_span_name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_ms: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    spans_json: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return f"<Trace(trace_id={self.trace_id}, name={self.root_span_name})>"

    @classmethod
    def from_trace(cls, trace) -> TraceModel:
        """Create TraceModel from a Trace object."""
        return cls(
            trace_id=trace.trace_id,
            service_name=trace.root_span.service,
            root_span_name=trace.root_span.name,
            start_time=trace.start_time,
            end_time=trace.end_time,
            duration_ms=trace.duration_ms,
            status=trace.status.value,
            spans_json=[
                {
                    "span_id": s.span_id,
                    "parent_span_id": s.parent_span_id,
                    "name": s.name,
                    "service": s.service,
                    "start_time": s.start_time.isoformat(),
                    "end_time": s.end_time.isoformat(),
                    "duration_ms": s.duration_ms,
                    "status": s.status.value,
                    "attributes": s.attributes,
                    "events": s.events,
                }
                for s in trace.spans
            ],
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "trace_id": self.trace_id,
            "service_name": self.service_name,
            "root_span_name": self.root_span_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_ms": self.duration_ms,
            "status": self.status,
            "spans": self.spans_json,
        }
