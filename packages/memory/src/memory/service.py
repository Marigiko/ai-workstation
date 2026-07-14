"""Memory service for high-level memory operations."""

import uuid
from datetime import UTC, datetime

from contracts import MemoryEntry, MemoryScope
from memory.qdrant_store import QdrantMemoryStore


class MemoryService:
    """Service for managing memories with business logic."""

    def __init__(self, store: QdrantMemoryStore):
        """Initialize memory service.

        Args:
            store: Memory store backend
        """
        self.store = store

    async def remember(
        self,
        content: str,
        scope: MemoryScope,
        project_id: str | None = None,
        session_id: str | None = None,
        metadata: dict | None = None,
    ) -> MemoryEntry:
        """Create and store a new memory.

        Args:
            content: Memory content
            scope: Memory scope (global, project, session)
            project_id: Project ID (required for project scope)
            session_id: Session ID (required for session scope)
            metadata: Additional metadata

        Returns:
            Created memory entry

        Raises:
            ValueError: If scope requirements are not met
        """
        # Validate scope requirements
        if scope == MemoryScope.PROJECT and not project_id:
            raise ValueError("project_id is required for project scope")
        if scope == MemoryScope.SESSION and not session_id:
            raise ValueError("session_id is required for session scope")

        entry = MemoryEntry(
            id=str(uuid.uuid4()),
            content=content,
            scope=scope,
            project_id=project_id,
            session_id=session_id,
            created_at=datetime.now(UTC),
            metadata=metadata or {},
        )

        await self.store.store(entry)
        return entry

    async def recall_memories(
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
        return await self.store.recall(
            query=query,
            scope=scope,
            limit=limit,
            project_id=project_id,
            session_id=session_id,
        )

    async def forget_memory(self, memory_id: str) -> None:
        """Forget (delete) a memory.

        Args:
            memory_id: ID of the memory to forget
        """
        await self.store.forget(memory_id)

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
        return await self.store.list_memories(
            scope=scope,
            project_id=project_id,
            session_id=session_id,
            limit=limit,
        )

    async def get_memory(self, memory_id: str) -> MemoryEntry | None:
        """Get a specific memory by ID.

        Args:
            memory_id: ID of the memory to retrieve

        Returns:
            Memory entry if found, None otherwise
        """
        memories = await self.store.list_memories(limit=1000)
        for memory in memories:
            if memory.id == memory_id:
                return memory
        return None
