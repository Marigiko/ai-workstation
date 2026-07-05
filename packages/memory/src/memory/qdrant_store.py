"""Qdrant-based memory store implementation."""

from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from contracts import MemoryEntry, MemoryScope


class QdrantMemoryStore:
    """Memory store using Qdrant for vector similarity search."""

    def __init__(
        self,
        collection_name: str = "memory",
        qdrant_url: str = "http://localhost:6333",
        embedding_dim: int = 1536,
    ):
        """Initialize Qdrant memory store.

        Args:
            collection_name: Name of the Qdrant collection
            qdrant_url: URL of Qdrant server
            embedding_dim: Dimension of embedding vectors
        """
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        self.client = QdrantClient(url=qdrant_url)
        self._ensure_collection()

    def _ensure_collection(self):
        """Ensure the memory collection exists in Qdrant."""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE,
                ),
            )

    def _generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for text.

        Note: This is a placeholder. In production, use a proper embedding model.
        """
        import hashlib

        hash_value = hashlib.md5(text.encode()).hexdigest()
        return [float(int(hash_value[i : i + 2], 16)) / 255.0 for i in range(0, 32, 2)] * 48

    async def store(self, entry: MemoryEntry) -> None:
        """Store a memory entry.

        Args:
            entry: Memory entry to store
        """
        embedding = self._generate_embedding(entry.content)

        point = PointStruct(
            id=entry.id,
            vector=embedding,
            payload={
                "content": entry.content,
                "scope": entry.scope.value,
                "project_id": entry.project_id,
                "session_id": entry.session_id,
                "created_at": entry.created_at.isoformat(),
                "metadata": entry.metadata,
            },
        )

        self.client.upsert(
            collection_name=self.collection_name,
            points=[point],
        )

    async def recall(
        self,
        query: str,
        scope: MemoryScope,
        limit: int = 10,
        project_id: str | None = None,
        session_id: str | None = None,
    ) -> list[MemoryEntry]:
        """Recall memories matching a query.

        Args:
            query: Query text to search for
            scope: Memory scope to search within
            limit: Maximum number of results
            project_id: Project ID filter (for project scope)
            session_id: Session ID filter (for session scope)

        Returns:
            List of matching memory entries
        """
        query_embedding = self._generate_embedding(query)

        # Build filter based on scope
        query_filter = {"scope": scope.value}

        if scope == MemoryScope.PROJECT and project_id:
            query_filter["project_id"] = project_id
        elif scope == MemoryScope.SESSION and session_id:
            query_filter["session_id"] = session_id

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit,
            query_filter=query_filter,
        )

        memories = []
        for result in results:
            payload = result.payload
            memories.append(
                MemoryEntry(
                    id=str(result.id),
                    content=payload["content"],
                    scope=MemoryScope(payload["scope"]),
                    project_id=payload.get("project_id"),
                    session_id=payload.get("session_id"),
                    created_at=datetime.fromisoformat(payload["created_at"]),
                    metadata=payload.get("metadata", {}),
                )
            )

        return memories

    async def forget(self, entry_id: str) -> None:
        """Forget (delete) a memory entry.

        Args:
            entry_id: ID of the memory entry to delete
        """
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=[entry_id],
        )

    async def list_memories(
        self,
        scope: MemoryScope | None = None,
        project_id: str | None = None,
        session_id: str | None = None,
        limit: int = 100,
    ) -> list[MemoryEntry]:
        """List memories with optional filters.

        Args:
            scope: Filter by scope
            project_id: Filter by project ID
            session_id: Filter by session ID
            limit: Maximum number of results

        Returns:
            List of memory entries
        """
        query_filter = {}

        if scope:
            query_filter["scope"] = scope.value
        if project_id:
            query_filter["project_id"] = project_id
        if session_id:
            query_filter["session_id"] = session_id

        results = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=query_filter if query_filter else None,
            limit=limit,
        )

        memories = []
        for point in results[0]:
            payload = point.payload
            memories.append(
                MemoryEntry(
                    id=str(point.id),
                    content=payload["content"],
                    scope=MemoryScope(payload["scope"]),
                    project_id=payload.get("project_id"),
                    session_id=payload.get("session_id"),
                    created_at=datetime.fromisoformat(payload["created_at"]),
                    metadata=payload.get("metadata", {}),
                )
            )

        return memories
