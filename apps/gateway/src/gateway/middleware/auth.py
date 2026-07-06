"""API key authentication middleware."""


from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware


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
            raise HTTPException(status_code=401, detail="API key required")

        if api_key not in self.api_keys:
            raise HTTPException(status_code=403, detail="Invalid API key")

        return await call_next(request)
