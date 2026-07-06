"""Tests for hybrid search."""

import pytest
from context.hybrid_search import HybridSearch, WeightedScoreFusion

from contracts import ContextChunk


def make_chunk(chunk_id: str, content: str, source: str, score: float) -> ContextChunk:
    """Helper to create a ContextChunk."""
    return ContextChunk(id=chunk_id, content=content, source=source, score=score)


class MockSource:
    """Mock context source for testing."""

    def __init__(self, name: str, results: list[ContextChunk]):
        self.name = name
        self._results = results

    async def search(self, query: str, project_id: str, top_k: int = 5) -> list[ContextChunk]:
        return self._results[:top_k]


@pytest.mark.asyncio
async def test_hybrid_search_rrf():
    """Test reciprocal rank fusion."""
    source_a = MockSource("a", [
        make_chunk("1", "content 1", "a", 0.9),
        make_chunk("2", "content 2", "a", 0.8),
    ])
    source_b = MockSource("b", [
        make_chunk("2", "content 2", "b", 0.95),
        make_chunk("3", "content 3", "b", 0.7),
    ])

    hybrid = HybridSearch(rrf_k=60)
    results = await hybrid.search(
        query="test",
        project_id="proj-1",
        sources=[source_a, source_b],
        top_k=5,
    )

    assert len(results) == 3
    chunk_2 = next(r for r in results if r.id == "2")
    assert chunk_2.score > 0

    for i in range(len(results) - 1):
        assert results[i].score >= results[i + 1].score


@pytest.mark.asyncio
async def test_hybrid_search_with_weights():
    """Test hybrid search with custom weights."""
    source_a = MockSource("a", [make_chunk("1", "content 1", "a", 0.9)])
    source_b = MockSource("b", [make_chunk("1", "content 1", "b", 0.9)])

    hybrid = HybridSearch(rrf_k=60)
    results = await hybrid.search(
        query="test",
        project_id="proj-1",
        sources=[source_a, source_b],
        weights={"a": 2.0, "b": 1.0},
    )

    assert len(results) == 1
    assert results[0].score > 0


@pytest.mark.asyncio
async def test_hybrid_search_empty_sources():
    """Test hybrid search with empty sources."""
    hybrid = HybridSearch()
    results = await hybrid.search(
        query="test",
        project_id="proj-1",
        sources=[],
    )

    assert results == []


@pytest.mark.asyncio
async def test_hybrid_search_source_failure():
    """Test hybrid search handles source failures."""

    class FailingSource:
        name = "failing"

        async def search(self, query, project_id, top_k=5):
            raise RuntimeError("Source failed")

    source_ok = MockSource("ok", [make_chunk("1", "content", "ok", 0.9)])

    hybrid = HybridSearch()
    results = await hybrid.search(
        query="test",
        project_id="proj-1",
        sources=[source_ok, FailingSource()],
    )

    assert len(results) == 1
    assert results[0].source == "ok"


def test_weighted_score_fusion():
    """Test weighted score fusion."""
    source_results = {
        "a": [make_chunk("1", "c1", "a", 0.9), make_chunk("2", "c2", "a", 0.5)],
        "b": [make_chunk("2", "c2", "b", 0.8), make_chunk("3", "c3", "b", 0.6)],
    }

    fusion = WeightedScoreFusion(weights={"a": 1.0, "b": 1.0})
    results = fusion.fuse(source_results)

    assert len(results) == 3
    for i in range(len(results) - 1):
        assert results[i].score >= results[i + 1].score


def test_weighted_score_fusion_empty():
    """Test weighted fusion with empty results."""
    fusion = WeightedScoreFusion()
    results = fusion.fuse({})
    assert results == []
