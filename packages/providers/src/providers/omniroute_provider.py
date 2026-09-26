"""OmniRoute gateway provider implementation."""

import json
import logging
import os
import time
import uuid
from collections.abc import AsyncIterator

import httpx

from contracts import (
    CompletionRequest,
    CompletionResponse,
    ProviderCapabilities,
    ProviderError,
    Role,
    StreamChunk,
)
from providers.base import BaseProvider

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "http://localhost:20128/v1"
_DONE = object()


class OmniRouteProvider(BaseProvider):
    """Provider that routes all completions through the OmniRoute gateway.

    The gateway exposes an OpenAI-compatible API at ``/chat/completions``.
    """

    def __init__(
        self,
        model: str,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 120.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        """Initialize OmniRoute provider.

        Args:
            model: OmniRoute combo or model id (e.g. "agente", "liviano").
            base_url: Gateway base URL. Defaults to ``OMNIROUTE_BASE_URL`` env
                var, else ``http://localhost:20128/v1``.
            api_key: Gateway API key. Defaults to ``OMNIROUTE_API_KEY`` env var.
            timeout: Request timeout in seconds.
            transport: Optional httpx transport (for test injection).
        """
        self._model = model
        self._base_url = (base_url or os.getenv("OMNIROUTE_BASE_URL") or DEFAULT_BASE_URL).rstrip(
            "/"
        )
        self._api_key = api_key or os.getenv("OMNIROUTE_API_KEY")
        self._timeout = timeout
        self._transport = transport

    @property
    def name(self) -> str:
        return f"omniroute/{self._model}"

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def _payload(self, request: CompletionRequest, *, stream: bool) -> dict:
        body: dict = {
            "model": self._model,
            "messages": [
                {"role": msg.role.value, "content": msg.content} for msg in request.messages
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": stream,
        }
        if request.tools:
            body["tools"] = request.tools
        return body

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
            headers=self._headers(),
            transport=self._transport,
        )

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute a completion request through the gateway."""
        start_time = time.time()
        try:
            async with self._client() as client:
                payload = self._payload(request, stream=False)
                resp = await client.post("/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()
        except ProviderError:
            raise
        except httpx.HTTPStatusError as e:
            raise ProviderError(self.name, f"gateway returned {e.response.status_code}", e) from e
        except (httpx.HTTPError, TimeoutError) as e:
            raise ProviderError(self.name, f"gateway request failed: {type(e).__name__}", e) from e
        except json.JSONDecodeError as e:
            raise ProviderError(self.name, "gateway returned malformed JSON", e) from e

        try:
            choice = data["choices"][0]
            usage = {}
            if data.get("usage"):
                usage = {
                    "prompt_tokens": data["usage"].get("prompt_tokens", 0),
                    "completion_tokens": data["usage"].get("completion_tokens", 0),
                    "total_tokens": data["usage"].get("total_tokens", 0),
                }
            latency_ms = (time.time() - start_time) * 1000
            return CompletionResponse(
                id=data.get("id") or str(uuid.uuid4()),
                provider=self.name,
                model=self._model,
                content=choice.get("message", {}).get("content") or "",
                role=Role.ASSISTANT,
                finish_reason=choice.get("finish_reason"),
                usage=usage,
                latency_ms=latency_ms,
                cost_usd=0.0,
                metadata={"model": self._model, "gateway": "omniroute"},
            )
        except (KeyError, IndexError, TypeError) as e:
            raise ProviderError(self.name, "gateway response in unexpected format", e) from e

    async def stream(self, request: CompletionRequest) -> AsyncIterator[StreamChunk]:
        """Execute a streaming completion request through the gateway."""
        chunk_id = str(uuid.uuid4())
        payload = self._payload(request, stream=True)
        try:
            async with (
                self._client() as client,
                client.stream("POST", "/chat/completions", json=payload) as resp,
            ):
                if resp.is_error:
                    raise ProviderError(self.name, f"gateway returned {resp.status_code}")
                async for line in resp.aiter_lines():
                    chunk = self._parse_sse_line(line.strip(), chunk_id)
                    if chunk is _DONE:
                        break
                    if chunk is not None:
                        yield chunk
        except ProviderError:
            raise
        except (httpx.HTTPError, TimeoutError) as e:
            raise ProviderError(self.name, f"gateway stream failed: {type(e).__name__}", e) from e

    def _parse_sse_line(self, line: str, chunk_id: str) -> "StreamChunk | object | None":
        """Parse one SSE line into a chunk, the end sentinel, or None to skip it."""
        if not line.startswith("data:"):
            return None
        data_str = line[len("data:") :].strip()
        if data_str == "[DONE]":
            return _DONE
        if not data_str:
            return None
        try:
            data = json.loads(data_str)
        except json.JSONDecodeError as e:
            raise ProviderError(self.name, "gateway returned malformed SSE JSON", e) from e
        choices = data.get("choices") or []
        delta = (choices[0].get("delta") or {}).get("content") if choices else None
        if not delta:
            return None
        return StreamChunk(
            id=chunk_id,
            provider=self.name,
            model=self._model,
            delta=delta,
            finish_reason=choices[0].get("finish_reason"),
        )

    async def capabilities(self) -> ProviderCapabilities:
        """Return provider capabilities."""
        return ProviderCapabilities(
            provider=self.name,
            model=self._model,
            supports_streaming=True,
            supports_tools=True,
            supports_vision=False,
            max_context_tokens=128000,
            cost_per_1k_input_tokens=0.0,
            cost_per_1k_output_tokens=0.0,
        )

    async def health(self) -> bool:
        """Check if the gateway is reachable (never raises)."""
        try:
            async with self._client() as client:
                resp = await client.get("/models")
            return 200 <= resp.status_code < 300
        except Exception:
            return False
