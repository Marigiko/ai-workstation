"""HTTP request tool for making web requests."""

from typing import Any

import httpx

from contracts import ToolResult


class HttpRequestTool:
    """Tool for making HTTP requests to external APIs.

    Supports GET, POST, PUT, DELETE methods with configurable headers and body.
    Includes domain allowlist for security.
    """

    name = "http_request"
    description = "Make HTTP requests to external APIs. Returns response body and status."
    input_schema = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "URL to request",
            },
            "method": {
                "type": "string",
                "description": "HTTP method (GET, POST, PUT, DELETE)",
                "default": "GET",
                "enum": ["GET", "POST", "PUT", "DELETE"],
            },
            "headers": {
                "type": "object",
                "description": "HTTP headers as key-value pairs",
            },
            "body": {
                "type": "string",
                "description": "Request body (for POST/PUT)",
            },
        },
        "required": ["url"],
    }

    def __init__(self, allowed_domains: list[str] | None = None):
        self.allowed_domains = allowed_domains or []
        self._client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    def _is_allowed(self, url: str) -> bool:
        """Check if URL domain is in allowlist."""
        if not self.allowed_domains:
            return True

        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        return any(
            domain == allowed or domain.endswith(f".{allowed}")
            for allowed in self.allowed_domains
        )

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        """Execute HTTP request."""
        url = params.get("url", "")
        method = params.get("method", "GET").upper()
        headers = params.get("headers", {})
        body = params.get("body")

        if not url:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error="URL is required",
            )

        if not self._is_allowed(url):
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error=f"Domain not in allowlist: {url}",
            )

        try:
            response = await self._client.request(
                method=method,
                url=url,
                headers=headers,
                content=body,
            )

            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                output = response.json()
            else:
                output = response.text[:10000]

            return ToolResult(
                tool_name=self.name,
                success=True,
                output={
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": output,
                },
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error=str(e),
            )

    async def close(self):
        await self._client.aclose()
