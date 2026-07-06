"""Tests for PixelRAG index builder."""

import tempfile
from pathlib import Path

import pytest
from context.sources.pixelrag_index import PixelRAGIndexBuilder


def test_index_builder_init():
    """Test index builder initialization."""
    builder = PixelRAGIndexBuilder()
    assert builder.server_url == "http://localhost:30001"


def test_index_builder_custom_url():
    """Test index builder with custom URL."""
    builder = PixelRAGIndexBuilder(server_url="http://custom:8080")
    assert builder.server_url == "http://custom:8080"


@pytest.mark.asyncio
async def test_index_builder_health_unreachable():
    """Test health check when server is unreachable."""
    builder = PixelRAGIndexBuilder(server_url="http://localhost:99999")
    result = await builder.health()
    assert result is False


@pytest.mark.asyncio
async def test_index_document_unreachable():
    """Test indexing document when server is unreachable."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(b"fake pdf content")
        tmp_path = tmp.name

    try:
        builder = PixelRAGIndexBuilder(server_url="http://localhost:99999")
        result = await builder.index_document(tmp_path, "proj-1")
        assert result.get("status") == "failed"
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_index_url_unreachable():
    """Test indexing URL when server is unreachable."""
    builder = PixelRAGIndexBuilder(server_url="http://localhost:99999")
    result = await builder.index_url("https://example.com", "proj-1")
    assert result.get("status") == "failed"
