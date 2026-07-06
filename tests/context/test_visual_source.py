"""Tests for PixelRAG visual context source."""

import pytest
from context.sources.visual_source import PixelRAGSource

from contracts import ContextQuery


@pytest.fixture
def source():
    return PixelRAGSource(server_url="http://localhost:30001")


def test_source_name(source):
    assert source.name == "pixelrag"


def test_default_server_url():
    source = PixelRAGSource()
    assert source.server_url == "http://localhost:30001"


def test_custom_server_url():
    source = PixelRAGSource(server_url="http://custom:9999")
    assert source.server_url == "http://custom:9999"


@pytest.mark.asyncio
async def test_search_returns_empty_on_connection_error(source):
    chunks = await source.search("test query", top_k=3)
    assert chunks == []


@pytest.mark.asyncio
async def test_gather_returns_empty_on_connection_error(source):
    query = ContextQuery(project_id="test", query="test query")
    result = await source.gather(query)
    assert result.chunks == []
    assert result.total_tokens == 0


@pytest.mark.asyncio
async def test_index_returns_status(source):
    from contracts import ProjectRef

    project = ProjectRef(id="test", name="test", path="/tmp/test")
    result = await source.index(project)
    assert result.project_id == "test"
    assert result.status == "pixelrag_uses_external_index"


@pytest.mark.asyncio
async def test_render_url_returns_empty_on_error(source):
    tiles_dir = await source.render_url("https://example.com")
    assert tiles_dir == ""


@pytest.mark.asyncio
async def test_close(source):
    await source.close()
