"""API key authentication middleware."""


from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware that validates API keys for protected endpoints."""

    def __init__(self, app, api_keys: list[str] | None = None):
        super().__init__(app)
        self.api_keys = api_keys or []
        self.public_paths = ["/health", "/docs", "/redoc", "/openapi.json"]

    async def dispatch(self, request: Request, call_next):
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

        if api_key not in self.api_keys:
            return JSONResponse(
                {"error": {"code": "forbidden", "message": "Invalid API key"}},
                status_code=403,
            )

        return await call_next(request)
