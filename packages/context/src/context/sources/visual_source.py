"""PixelRAG visual context source — screenshot-based retrieval."""

import logging
import os

import httpx

from contracts import (
    ContextChunk,
    ContextQuery,
    ContextResult,
    IndexResult,
    ProjectRef,
)

logger = logging.getLogger(__name__)


class PixelRAGSource:
    """Visual context source using PixelRAG server.

    Renders documents as screenshots and retrieves by visual similarity.
    Requires a running PixelRAG server (`pixelrag serve`).
    """

    def __init__(
        self,
        server_url: str | None = None,
        render_output_dir: str = "/tmp/pixelrag_tiles",
    ):
        self.name = "pixelrag"
        self.server_url = server_url or os.getenv("PIXELRAG_URL", "http://localhost:30001")
        self.render_output_dir = render_output_dir
        self._client = httpx.AsyncClient(timeout=60.0)

    async def gather(self, query: ContextQuery) -> ContextResult:
        chunks = await self.search(query.query, top_k=5)
        total_tokens = sum(len(c.content.split()) * 4 // 3 for c in chunks)
        return ContextResult(chunks=chunks, total_tokens=total_tokens)

    async def index(self, project: ProjectRef) -> IndexResult:
        return IndexResult(
            project_id=project.id,
            chunks_indexed=0,
            index_time_ms=0.0,
            status="pixelrag_uses_external_index",
        )

    async def search(self, query: str, top_k: int = 5) -> list[ContextChunk]:
        try:
            response = await self._client.post(
                f"{self.server_url}/search",
                json={"queries": [{"text": query}], "n_docs": top_k},
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            logger.warning("PixelRAG search failed: %s", e)
            return []

        chunks: list[ContextChunk] = []
        for result in data.get("results", []):
            chunks.append(
                ContextChunk(
                    id=str(result.get("doc_id", "")),
                    content=result.get("text", ""),
                    source="pixelrag",
                    score=result.get("score", 0.0),
                    metadata={
                        "visual": True,
                        "url": result.get("url", ""),
                        "page": result.get("page", 0),
                    },
                )
            )
        return chunks

    async def render_url(self, url: str) -> str:
        try:
            response = await self._client.post(
                f"{self.server_url}/render",
                json={"url": url, "output_dir": self.render_output_dir},
            )
            response.raise_for_status()
            return response.json().get("tiles_dir", self.render_output_dir)
        except httpx.HTTPError as e:
            logger.warning("PixelRAG render failed: %s", e)
            return ""

    async def close(self) -> None:
        await self._client.aclose()
