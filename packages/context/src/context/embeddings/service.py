"""Real embedding service using OpenAI text-embedding-3-small."""

import logging
import os

import httpx

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using OpenAI API."""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: str | None = None,
        dimensions: int = 1536,
    ):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.dimensions = dimensions
        self._client = httpx.AsyncClient(timeout=30.0)
        self._base_url = "https://api.openai.com/v1/embeddings"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors (1536 dimensions each)
        """
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set, returning zero vectors")
            return [[0.0] * self.dimensions for _ in texts]

        try:
            response = await self._client.post(
                self._base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "input": texts,
                    "model": self.model,
                    "dimensions": self.dimensions,
                },
            )
            response.raise_for_status()
            data = response.json()

            embeddings = [item["embedding"] for item in data["data"]]
            return embeddings

        except httpx.HTTPError as e:
            logger.error("OpenAI embedding API error: %s", e)
            return [[0.0] * self.dimensions for _ in texts]

    async def embed_single(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text string to embed

        Returns:
            Embedding vector (1536 dimensions)
        """
        embeddings = await self.embed([text])
        return embeddings[0]

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()
