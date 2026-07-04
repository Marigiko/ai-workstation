"""Tests for gateway health endpoints."""

from fastapi.testclient import TestClient

from gateway.main import create_app


def test_health_check():
    """Test health check endpoint."""
    app = create_app()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root():
    """Test root endpoint."""
    app = create_app()
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "AI Workstation Gateway"
    assert data["version"] == "0.1.0"
