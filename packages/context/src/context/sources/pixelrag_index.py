"""PixelRAG index builder for visual document indexing."""

import logging
import os
from pathlib import Path

import aiofiles
import httpx

logger = logging.getLogger(__name__)


class PixelRAGIndexBuilder:
    """Builds visual index for PixelRAG server.

    Processes documents (PDFs, URLs, images) and sends them to PixelRAG
    for visual indexing and tile generation.
    """

    def __init__(
        self,
        server_url: str | None = None,
        render_output_dir: str = "/tmp/pixelrag_tiles",
    ):
        self.server_url = server_url or os.getenv("PIXELRAG_URL", "http://localhost:30001")
        self.render_output_dir = render_output_dir
        self._client = httpx.AsyncClient(timeout=120.0)

    async def index_document(self, file_path: str, project_id: str) -> dict:
        """Index a single document file.

        Args:
            file_path: Path to the document file
            project_id: Project identifier

        Returns:
            Indexing result with document ID and status
        """
        try:
            async with aiofiles.open(file_path, "rb") as f:
                content = await f.read()

            response = await self._client.post(
                f"{self.server_url}/index",
                files={"file": (Path(file_path).name, content)},
                data={"project_id": project_id, "output_dir": self.render_output_dir},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error("PixelRAG index_document failed for %s: %s", file_path, e)
            return {"error": str(e), "status": "failed"}

    async def index_url(self, url: str, project_id: str) -> dict:
        """Index a document from URL.

        Args:
            url: URL of the document to index
            project_id: Project identifier

        Returns:
            Indexing result with document ID and status
        """
        try:
            response = await self._client.post(
                f"{self.server_url}/index_url",
                json={"url": url, "project_id": project_id, "output_dir": self.render_output_dir},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error("PixelRAG index_url failed for %s: %s", url, e)
            return {"error": str(e), "status": "failed"}

    async def index_directory(self, directory: str, project_id: str) -> dict:
        """Index all supported documents in a directory.

        Args:
            directory: Directory path to scan
            project_id: Project identifier

        Returns:
            Summary of indexing results
        """
        supported_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".html", ".md"}
        results = {"indexed": 0, "failed": 0, "skipped": 0}

        for root, _, files in os.walk(directory):
            for filename in files:
                ext = Path(filename).suffix.lower()
                if ext not in supported_extensions:
                    results["skipped"] += 1
                    continue

                file_path = Path(root) / filename
                result = await self.index_document(str(file_path), project_id)

                if result.get("status") == "success":
                    results["indexed"] += 1
                else:
                    results["failed"] += 1

        return results

    async def health(self) -> bool:
        """Check if PixelRAG server is healthy.

        Returns:
            True if server is reachable
        """
        try:
            response = await self._client.get(f"{self.server_url}/health")
            response.raise_for_status()
            return True
        except httpx.HTTPError:
            return False

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()
