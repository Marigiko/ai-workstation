"""Embedding pipeline with Qdrant."""

import os
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from contracts import ContextChunk


class EmbeddingPipeline:
    """Pipeline for generating and storing embeddings in Qdrant."""

    def __init__(self, collection_name: str = "context"):
        """Initialize embedding pipeline.

        Args:
            collection_name: Name of Qdrant collection
        """
        self.collection_name = collection_name
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.client = QdrantClient(url=qdrant_url)
        self._ensure_collection()

    def _ensure_collection(self):
        """Ensure collection exists in Qdrant."""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
            )

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for text using OpenAI.

        Note: This is a placeholder. In production, use a proper embedding model.
        """
        import hashlib

        hash_value = hashlib.md5(text.encode()).hexdigest()
        return [float(int(hash_value[i : i + 2], 16)) / 255.0 for i in range(0, 32, 2)] * 48

    async def store_chunks(self, chunks: list[ContextChunk], project_id: str):
        """Store context chunks with embeddings in Qdrant."""
        points = []

        for chunk in chunks:
            embedding = await self.embed_text(chunk.content)

            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "content": chunk.content,
                    "source": chunk.source,
                    "file_path": chunk.file_path,
                    "project_id": project_id,
                    "line_start": chunk.line_start,
                    "line_end": chunk.line_end,
                },
            )
            points.append(point)

        if points:
            self.client.upsert(collection_name=self.collection_name, points=points)

    async def search(self, query: str, project_id: str, top_k: int = 5) -> list[ContextChunk]:
        """Search for relevant chunks using embeddings."""
        query_embedding = await self.embed_text(query)

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k,
            query_filter={"project_id": project_id},
        )

        chunks = []
        for result in results:
            payload = result.payload
            chunks.append(
                ContextChunk(
                    id=str(result.id),
                    content=payload["content"],
                    source=payload["source"],
                    file_path=payload.get("file_path"),
                    line_start=payload.get("line_start"),
                    line_end=payload.get("line_end"),
                    score=result.score,
                )
            )

        return chunks
