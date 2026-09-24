"""Observability endpoints for the gateway."""

from fastapi import APIRouter, HTTPException
from observability import ObservabilityService, SpanStatus
from pydantic import BaseModel

router = APIRouter(prefix="/observability", tags=["observability"])

# Lazy initialization
_observability_service: ObservabilityService | None = None


def _get_observability_service() -> ObservabilityService:
    """Get or create the observability service."""
    global _observability_service
    if _observability_service is None:
        _observability_service = ObservabilityService()
    return _observability_service


class StartRequest(BaseModel):
    """Request to start tracking."""

    operation: str
    attributes: dict | None = None


class EndRequest(BaseModel):
    """Request to end tracking."""

    status: str = "ok"
    attributes: dict | None = None


class RecordMetricRequest(BaseModel):
    """Request to record a metric."""

    name: str
    value: float
    labels: dict[str, str] | None = None


class LogEventRequest(BaseModel):
    """Request to log an event."""

    level: str = "info"
    message: str
    attributes: dict | None = None


@router.post("/start")
async def start_request(request: StartRequest):
    """Start tracking a request."""
    service = _get_observability_service()
    trace_id = service.start_request(request.operation, request.attributes)
    return {"trace_id": trace_id}


@router.post("/end/{trace_id}")
async def end_request(trace_id: str, request: EndRequest):
    """End tracking a request."""
    service = _get_observability_service()

    try:
        status = SpanStatus(request.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {request.status}")

    await service.end_request(trace_id, status, request.attributes)
    return {"status": "success", "trace_id": trace_id}


@router.post("/metrics")
async def record_metric(request: RecordMetricRequest):
    """Record a metric."""
    service = _get_observability_service()
    service.record_metric(request.name, request.value, request.labels)
    return {"status": "success", "metric": request.name}


@router.post("/log")
async def log_event(request: LogEventRequest):
    """Log an event."""
    service = _get_observability_service()
    service.log_event(request.level, request.message, **(request.attributes or {}))
    return {"status": "success"}


@router.get("/summary")
async def get_summary():
    """Get observability summary."""
    service = _get_observability_service()
    summary = service.get_summary()
    return {
        "total_traces": summary.total_traces,
        "total_spans": summary.total_spans,
        "total_metrics": summary.total_metrics,
        "total_logs": summary.total_logs,
        "error_rate": summary.error_rate,
        "avg_latency_ms": summary.avg_latency_ms,
        "p95_latency_ms": summary.p95_latency_ms,
        "p99_latency_ms": summary.p99_latency_ms,
    }


@router.get("/traces")
async def list_traces(limit: int = 100):
    """List recent traces."""
    service = _get_observability_service()
    traces = service.tracer.list_traces(limit=limit)
    return {
        "traces": [
            {
                "trace_id": trace.trace_id,
                "operation": trace.root_span.name,
                "duration_ms": trace.duration_ms,
                "status": trace.status.value,
                "start_time": trace.start_time.isoformat(),
                "span_count": len(trace.spans),
            }
            for trace in traces
        ],
        "count": len(traces),
    }


@router.get("/traces/{trace_id}")
async def get_trace(trace_id: str):
    """Get a specific trace."""
    service = _get_observability_service()
    trace = service.tracer.get_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")

    return {
        "trace_id": trace.trace_id,
        "operation": trace.root_span.name,
        "duration_ms": trace.duration_ms,
        "status": trace.status.value,
        "start_time": trace.start_time.isoformat(),
        "end_time": trace.end_time.isoformat(),
        "spans": [
            {
                "span_id": span.span_id,
                "parent_span_id": span.parent_span_id,
                "name": span.name,
                "duration_ms": span.duration_ms,
                "status": span.status.value,
                "attributes": span.attributes,
                "events": span.events,
            }
            for span in trace.spans
        ],
    }


@router.get("/metrics/list")
async def list_metrics(limit: int = 1000):
    """List recent metrics."""
    service = _get_observability_service()
    metrics = service.metrics.list_metrics(limit=limit)
    return {
        "metrics": [
            {
                "name": metric.name,
                "type": metric.type.value,
                "value": metric.value,
                "labels": metric.labels,
                "timestamp": metric.timestamp.isoformat(),
            }
            for metric in metrics
        ],
        "count": len(metrics),
    }


@router.get("/metrics/prometheus")
async def export_prometheus():
    """Export metrics in Prometheus format."""
    service = _get_observability_service()
    prometheus_output = service.metrics.export_prometheus()
    return {"metrics": prometheus_output}


@router.get("/logs")
async def list_logs(limit: int = 1000, level: str | None = None):
    """List log entries."""
    service = _get_observability_service()

    from observability import LogLevel

    log_level = None
    if level:
        try:
            log_level = LogLevel(level)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid log level: {level}")

    logs = service.logger.list_logs(limit=limit, level=log_level)
    return {
        "logs": [
            {
                "timestamp": log.timestamp.isoformat(),
                "level": log.level.value,
                "message": log.message,
                "service": log.service,
                "trace_id": log.trace_id,
                "span_id": log.span_id,
                "attributes": log.attributes,
            }
            for log in logs
        ],
        "count": len(logs),
    }


@router.get("/traces/persisted")
async def list_persisted_traces(
    limit: int = 100,
    status: str | None = None,
    service_name: str | None = None,
):
    """List traces from PostgreSQL (persistent storage)."""
    service = _get_observability_service()
    traces = await service.tracer.list_persisted_traces(
        limit=limit,
        status=status,
        service_name=service_name,
    )
    return {
        "traces": traces,
        "count": len(traces),
        "source": "postgresql",
    }


@router.delete("/clear")
async def clear_all():
    """Clear all observability data."""
    service = _get_observability_service()
    service.clear_all()
    return {"status": "success", "message": "All observability data cleared"}
