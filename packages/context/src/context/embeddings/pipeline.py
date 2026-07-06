"""Embedding pipeline with Qdrant."""

import os
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, Match, PointStruct, VectorParams

from context.embeddings.service import EmbeddingService
from contracts import ContextChunk


class EmbeddingPipeline:
    """Pipeline for generating and storing embeddings in Qdrant."""

    def __init__(
        self,
        collection_name: str = "context",
        embedding_service: EmbeddingService | None = None,
    ):
        """Initialize embedding pipeline.

        Args:
            collection_name: Name of Qdrant collection
            embedding_service: Optional embedding service instance
        """
        self.collection_name = collection_name
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.client = QdrantClient(url=qdrant_url)
        self.embedding_service = embedding_service or EmbeddingService()
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
        """Generate embedding for text using OpenAI text-embedding-3-small."""
        return await self.embedding_service.embed_single(text)

    async def store_chunks(self, chunks: list[ContextChunk], project_id: str):
        """Store context chunks with embeddings in Qdrant."""
        if not chunks:
            return

        texts = [chunk.content for chunk in chunks]
        embeddings = await self.embedding_service.embed(texts)

        points = []
        for chunk, embedding in zip(chunks, embeddings):
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

        query_filter = Filter(
            must=[
                FieldCondition(
                    key="project_id",
                    match=Match(value=project_id),
                )
            ]
        )

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=query_filter,
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

    async def close(self) -> None:
        """Close embedding service."""
        await self.embedding_service.close()
