"""Tests for rate limiting middleware."""

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

from gateway.middleware.rate_limit import RateLimitMiddleware


def make_app(rpm: int = 3) -> FastAPI:
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, requests_per_minute=rpm)

    @app.get("/")
    async def root(request: Request):
        return PlainTextResponse("ok")

    return app


def test_allows_within_quota():
    from fastapi.testclient import TestClient

    app = make_app(rpm=5)
    client = TestClient(app)
    for _ in range(5):
        resp = client.get("/")
        assert resp.status_code == 200


def test_blocks_after_quota():
    from fastapi.testclient import TestClient

    app = make_app(rpm=2)
    client = TestClient(app)
    r1 = client.get("/")
    r2 = client.get("/")
    r3 = client.get("/")
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r3.status_code == 429
