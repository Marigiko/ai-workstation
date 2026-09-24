"""Observability middleware for the gateway."""

import time

from fastapi import Request
from observability import ObservabilityService
from observability.models import SpanStatus
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware that traces all requests through the observability service."""

    def __init__(self, app, observability_service: ObservabilityService):  # type: ignore[override]
        super().__init__(app)
        self.observability = observability_service

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        operation = f"{request.method} {request.url.path}"

        trace_id = self.observability.start_request(operation=operation)

        try:
            response = await call_next(request)
            latency_ms = (time.time() - start_time) * 1000

            await self.observability.end_request(trace_id=trace_id, status=SpanStatus.OK)

            response.headers["X-Trace-Id"] = trace_id
            response.headers["X-Latency-Ms"] = str(int(latency_ms))

            return response

        except Exception as e:
            await self.observability.end_request(
                trace_id=trace_id, status=SpanStatus.ERROR, attributes={"error": str(e)}
            )
            raise
