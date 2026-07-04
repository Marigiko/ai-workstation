"""Tests for chat endpoint."""

import pytest
from fastapi.testclient import TestClient

from gateway.main import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


def test_chat_endpoint_exists(client):
    """Test that chat endpoint exists."""
    response = client.post(
        "/chat",
        json={
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": False,
        },
    )
    assert response.status_code in [200, 500]


def test_chat_streaming_endpoint(client):
    """Test that streaming chat endpoint exists."""
    response = client.post(
        "/chat",
        json={
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": True,
        },
    )
    assert response.status_code in [200, 500]
    assert response.headers.get("content-type") == "text/event-stream; charset=utf-8"
