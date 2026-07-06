"""Hybrid search with score fusion across multiple context sources."""

import asyncio
import logging
from collections import defaultdict

from contracts import ContextChunk

logger = logging.getLogger(__name__)


class HybridSearch:
    """Hybrid search combining multiple context sources with score fusion.

    Uses Reciprocal Rank Fusion (RRF) to combine results from:
    - File source (text embeddings)
    - Tree-sitter source (code embeddings)
    - PixelRAG source (visual embeddings)
    """

    def __init__(self, rrf_k: int = 60):
        """Initialize hybrid search.

        Args:
            rrf_k: Constant for RRF scoring (default 60)
        """
        self.rrf_k = rrf_k

    async def search(
        self,
        query: str,
        project_id: str,
        sources: list,
        top_k: int = 10,
        weights: dict[str, float] | None = None,
    ) -> list[ContextChunk]:
        """Search across multiple sources with score fusion.

        Args:
            query: Search query
            project_id: Project identifier
            sources: List of context source instances
            top_k: Number of results to return
            weights: Optional weights per source name (default: equal weights)

        Returns:
            Fused and ranked list of context chunks
        """
        if not sources:
            return []

        if weights is None:
            weights = {source.name: 1.0 for source in sources}

        search_tasks = [source.search(query, project_id, top_k=top_k) for source in sources]
        results_per_source = await asyncio.gather(*search_tasks, return_exceptions=True)

        source_results: dict[str, list[ContextChunk]] = {}
        for source, results in zip(sources, results_per_source):
            if isinstance(results, Exception):
                logger.warning("Search failed for source %s: %s", source.name, results)
                source_results[source.name] = []
            else:
                source_results[source.name] = results

        fused = self._reciprocal_rank_fusion(source_results, weights)

        fused.sort(key=lambda x: x.score, reverse=True)
        return fused[:top_k]

    def _reciprocal_rank_fusion(
        self,
        source_results: dict[str, list[ContextChunk]],
        weights: dict[str, float],
    ) -> list[ContextChunk]:
        """Combine results using Reciprocal Rank Fusion.

        RRF score = sum(weight / (k + rank)) for each source where the doc appears.

        Args:
            source_results: Results per source name
            weights: Weight per source name

        Returns:
            List of chunks with fused scores
        """
        chunk_scores: dict[str, float] = defaultdict(float)
        chunk_map: dict[str, ContextChunk] = {}

        for source_name, chunks in source_results.items():
            weight = weights.get(source_name, 1.0)

            for rank, chunk in enumerate(chunks):
                rrf_score = weight / (self.rrf_k + rank + 1)
                chunk_scores[chunk.id] += rrf_score

                if chunk.id not in chunk_map:
                    chunk_map[chunk.id] = chunk

        fused_chunks = []
        for chunk_id, fused_score in chunk_scores.items():
            chunk = chunk_map[chunk_id]
            fused_chunk = chunk.model_copy(update={"score": fused_score})
            fused_chunks.append(fused_chunk)

        return fused_chunks


class WeightedScoreFusion:
    """Alternative fusion using weighted average of normalized scores."""

    def __init__(self, weights: dict[str, float] | None = None):
        """Initialize with source weights.

        Args:
            weights: Weight per source name (default: equal weights)
        """
        self.weights = weights or {}

    def fuse(
        self,
        source_results: dict[str, list[ContextChunk]],
    ) -> list[ContextChunk]:
        """Fuse results using weighted average of normalized scores.

        Args:
            source_results: Results per source name

        Returns:
            List of chunks with fused scores
        """
        chunk_scores: dict[str, float] = defaultdict(float)
        chunk_weights: dict[str, float] = defaultdict(float)
        chunk_map: dict[str, ContextChunk] = {}

        for source_name, chunks in source_results.items():
            if not chunks:
                continue

            weight = self.weights.get(source_name, 1.0)
            max_score = max(c.score for c in chunks) if chunks else 1.0
            min_score = min(c.score for c in chunks) if chunks else 0.0
            score_range = max_score - min_score if max_score != min_score else 1.0

            for chunk in chunks:
                normalized = (chunk.score - min_score) / score_range
                chunk_scores[chunk.id] += normalized * weight
                chunk_weights[chunk.id] += weight

                if chunk.id not in chunk_map:
                    chunk_map[chunk.id] = chunk

        fused_chunks = []
        for chunk_id, total_score in chunk_scores.items():
            weight = chunk_weights[chunk_id]
            avg_score = total_score / weight if weight > 0 else 0.0
            chunk = chunk_map[chunk_id]
            fused_chunk = chunk.model_copy(update={"score": avg_score})
            fused_chunks.append(fused_chunk)

        fused_chunks.sort(key=lambda x: x.score, reverse=True)
        return fused_chunks
