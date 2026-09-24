"""Qdrant-based memory store implementation."""

import logging
import os
from datetime import datetime

import httpx

from contracts import EmbeddingProvider, MemoryEntry, MemoryScope
from memory.embedding import create_embedding_provider

logger = logging.getLogger(__name__)


class QdrantMemoryStore:
    """Memory store using Qdrant for vector similarity search."""

    def __init__(
        self,
        collection_name: str = "memory",
        qdrant_url: str | None = None,
        embedding_dim: int = 768,
        embedding_provider: EmbeddingProvider | None = None,
    ):
        """Initialize Qdrant memory store.

        Args:
            collection_name: Name of the Qdrant collection
            qdrant_url: URL of Qdrant server (defaults to QDRANT_URL env or http://localhost:6333)
            embedding_dim: Vector dimension used only when no embedding provider is available
            embedding_provider: Provider for generating embeddings.
                If None, auto-detects best available.
        """
        self.collection_name = collection_name
        self._embedding_provider = embedding_provider or create_embedding_provider()
        self.embedding_dim = (
            self._embedding_provider.dimension
            if self._embedding_provider is not None
            else embedding_dim
        )
        url = qdrant_url or os.getenv("QDRANT_URL", "http://localhost:6333")
        self.server_url = url.rstrip("/")
        self._http = httpx.Client(base_url=self.server_url, timeout=30.0)
        self._ensure_collection()

    def _qdrant_point_filter(self, conditions: dict) -> dict | None:
        """Build a Qdrant 1.7-compatible filter (plain dict)."""
        if not conditions:
            return None
        must = [{"key": k, "match": {"value": v}} for k, v in conditions.items()]
        return {"must": must}

    def _ensure_collection(self):
        """Ensure the memory collection exists in Qdrant."""
        resp = self._http.get("/collections")
        resp.raise_for_status()
        collections = resp.json()["result"]["collections"]
        collection_names = [c["name"] for c in collections]

        if self.collection_name not in collection_names:
            body = {
                "vectors": {
                    "size": self.embedding_dim,
                    "distance": "Cosine",
                }
            }
            resp = self._http.put(f"/collections/{self.collection_name}", json=body)
            resp.raise_for_status()

    async def _generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for text.

        Uses the configured EmbeddingProvider if available.
        Falls back to MD5-based placeholder if no provider is configured.
        """
        if self._embedding_provider is not None:
            try:
                return await self._embedding_provider.embed(text)
            except Exception as e:
                logger.warning("Embedding provider failed, using fallback: %s", e)

        # Fallback: deterministic but not semantically meaningful
        import hashlib
        hash_value = hashlib.md5(text.encode()).hexdigest()
        return [float(int(hash_value[i : i + 2], 16)) / 255.0 for i in range(0, 32, 2)] * 48

    async def store(self, entry: MemoryEntry) -> None:
        """Store a memory entry.

        Args:
            entry: Memory entry to store
        """
        embedding = await self._generate_embedding(entry.content)

        point = {
            "id": entry.id,
            "vector": embedding,
            "payload": {
                "content": entry.content,
                "scope": entry.scope.value,
                "project_id": entry.project_id,
                "session_id": entry.session_id,
                "created_at": entry.created_at.isoformat(),
                "metadata": entry.metadata,
            },
        }

        body = {"points": [point]}
        resp = self._http.put(
            f"/collections/{self.collection_name}/points",
            json=body,
        )
        resp.raise_for_status()

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
        query_embedding = await self._generate_embedding(query)

        conditions = {"scope": scope.value}
        if scope == MemoryScope.PROJECT and project_id:
            conditions["project_id"] = project_id
        elif scope == MemoryScope.SESSION and session_id:
            conditions["session_id"] = session_id

        body = {
            "vector": query_embedding,
            "limit": limit,
            "with_payload": True,
            "with_vector": False,
            "filter": self._qdrant_point_filter(conditions),
        }

        resp = self._http.post(
            f"/collections/{self.collection_name}/points/search",
            json=body,
        )
        resp.raise_for_status()
        hits = resp.json()["result"]

        memories = []
        for result in hits:
            payload = result.get("payload", {})
            memories.append(
                MemoryEntry(
                    id=str(result["id"]),
                    content=payload.get("content", ""),
                    scope=MemoryScope(payload.get("scope", "global")),
                    project_id=payload.get("project_id"),
                    session_id=payload.get("session_id"),
                    created_at=datetime.fromisoformat(
                        payload.get("created_at", datetime.utcnow().isoformat()),
                    ),
                    metadata=payload.get("metadata", {}),
                )
            )

        return memories

    async def forget(self, entry_id: str) -> None:
        """Forget (delete) a memory entry.

        Args:
            entry_id: ID of the memory entry to delete
        """
        body = {"points": [entry_id]}
        resp = self._http.post(
            f"/collections/{self.collection_name}/points/delete",
            json=body,
        )
        resp.raise_for_status()

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
        conditions = {}
        if scope:
            conditions["scope"] = scope.value
        if project_id:
            conditions["project_id"] = project_id
        if session_id:
            conditions["session_id"] = session_id

        body = {
            "limit": limit,
            "with_payload": True,
            "with_vector": False,
            "filter": self._qdrant_point_filter(conditions),
        }

        resp = self._http.post(
            f"/collections/{self.collection_name}/points/scroll",
            json=body,
        )
        resp.raise_for_status()
        points = resp.json().get("result", {}).get("points", [])

        memories = []
        for point in points:
            payload = point.get("payload", {})
            memories.append(
                MemoryEntry(
                    id=str(point["id"]),
                    content=payload.get("content", ""),
                    scope=MemoryScope(payload.get("scope", "global")),
                    project_id=payload.get("project_id"),
                    session_id=payload.get("session_id"),
                    created_at=datetime.fromisoformat(
                        payload.get("created_at", datetime.utcnow().isoformat()),
                    ),
                    metadata=payload.get("metadata", {}),
                )
            )

        return memories

    async def close(self) -> None:
        """Close HTTP client."""
        self._http.close()
