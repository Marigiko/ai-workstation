"""API key authentication middleware."""

import hmac

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware that validates API keys for protected endpoints."""

    def __init__(self, app, api_keys: list[str] | None = None):  # type: ignore[override]
        super().__init__(app)
        self.api_keys = api_keys or []
        self.public_paths = ["/health", "/docs", "/redoc", "/openapi.json"]

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in self.public_paths:
            return await call_next(request)

        if not self.api_keys:
            return await call_next(request)

        api_key = request.headers.get("X-API-Key") or request.headers.get(
            "Authorization", ""
        ).replace("Bearer ", "")

        if not api_key:
            return JSONResponse(
                {"error": {"code": "unauthorized", "message": "API key required"}},
                status_code=401,
            )

        if not any(
            hmac.compare_digest(api_key, valid_key) for valid_key in self.api_keys
        ):
            return JSONResponse(
                {"error": {"code": "forbidden", "message": "Invalid API key"}},
                status_code=403,
            )

        return await call_next(request)
