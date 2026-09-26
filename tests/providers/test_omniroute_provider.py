"""Tests for OmniRoute provider (no network — httpx.MockTransport only)."""

import httpx
import pytest
from providers import OmniRouteProvider

from contracts import CompletionRequest, Message, ProviderError, Role


def _mock_client(handler) -> httpx.MockTransport:
    return httpx.MockTransport(handler)


def _make_provider(handler, api_key: str = "secret-key") -> OmniRouteProvider:
    return OmniRouteProvider(
        model="liviano",
        base_url="http://gateway.test/v1",
        api_key=api_key,
        transport=_mock_client(handler),
    )


def test_provider_name():
    provider = OmniRouteProvider(
        model="agente", api_key="k", transport=_mock_client(lambda r: httpx.Response(200))
    )
    assert provider.name == "omniroute/agente"


@pytest.mark.asyncio
async def test_complete_maps_response():
    """complete() maps the gateway response to CompletionResponse."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer secret-key"
        body = request.read()
        import json

        payload = json.loads(body)
        assert payload["model"] == "liviano"
        assert payload["stream"] is False
        return httpx.Response(
            200,
            json={
                "id": "resp-1",
                "choices": [
                    {"message": {"role": "assistant", "content": "Hello!"}, "finish_reason": "stop"}
                ],
                "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
            },
        )

    provider = _make_provider(handler)
    request = CompletionRequest(
        messages=[Message(role=Role.USER, content="Hi")], max_tokens=10
    )
    response = await provider.complete(request)

    assert response.id == "resp-1"
    assert response.provider == "omniroute/liviano"
    assert response.model == "liviano"
    assert response.content == "Hello!"
    assert response.finish_reason == "stop"
    assert response.usage == {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8}
    assert response.cost_usd == 0.0
    assert response.metadata == {"model": "liviano", "gateway": "omniroute"}
    assert response.latency_ms >= 0


@pytest.mark.asyncio
async def test_stream_yields_deltas_and_stops_at_done():
    """stream() parses SSE lines, yields deltas and stops at [DONE]."""

    sse_body = (
        'data: {"choices": [{"delta": {"content": "Hel"}}]}\n'
        "\n"
        'data: {"choices": [{"delta": {"content": "lo"}}]}\n'
        "\n"
        'data: {"choices": [{"delta": {}}]}\n'
        "\n"
        "data: [DONE]\n"
        "\n"
        'data: {"choices": [{"delta": {"content": "IGNORED"}}]}\n'
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer secret-key"
        import json

        assert json.loads(request.read())["stream"] is True
        return httpx.Response(200, text=sse_body)

    provider = _make_provider(handler)
    request = CompletionRequest(
        messages=[Message(role=Role.USER, content="Hi")], max_tokens=10
    )
    chunks = [chunk async for chunk in provider.stream(request)]
    deltas = [chunk.delta for chunk in chunks]

    assert deltas == ["Hel", "lo"]
    for chunk in chunks:
        assert chunk.provider == "omniroute/liviano"
        assert chunk.model == "liviano"


@pytest.mark.asyncio
async def test_error_status_raises_provider_error_without_leaking_key():
    """A 500 response raises ProviderError and never leaks the API key."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="internal error")

    provider = _make_provider(handler, api_key="super-secret-value")
    request = CompletionRequest(
        messages=[Message(role=Role.USER, content="Hi")], max_tokens=10
    )

    with pytest.raises(ProviderError) as exc_info:
        await provider.complete(request)

    assert "super-secret-value" not in str(exc_info.value)
    assert "500" in str(exc_info.value)


@pytest.mark.asyncio
async def test_health_false_on_connection_error():
    """health() returns False (never raises) when the gateway is unreachable."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    provider = _make_provider(handler)
    assert await provider.health() is False


@pytest.mark.asyncio
async def test_health_true_on_2xx():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/models"
        return httpx.Response(200, json={"data": []})

    provider = _make_provider(handler)
    assert await provider.health() is True
