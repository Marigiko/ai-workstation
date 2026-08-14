"""Memory endpoints for the gateway."""

from fastapi import APIRouter, HTTPException, Query
from memory import MemoryService, QdrantMemoryStore

from contracts import MemoryScope

# Memory endpoints accept query params (not JSON body) so external clients
# like Terax-AI can call them with simple GET/POST requests.

router = APIRouter(prefix="/memory", tags=["memory"])

# Lazy initialization
_memory_store: QdrantMemoryStore | None = None
_memory_service: MemoryService | None = None


def _get_memory_service() -> MemoryService:
    """Get or create the memory service."""
    global _memory_store, _memory_service
    if _memory_service is None:
        _memory_store = QdrantMemoryStore()
        _memory_service = MemoryService(_memory_store)
    return _memory_service


@router.post("/remember")
async def remember(
    content: str = Query(..., description="Memory content"),
    scope: MemoryScope = Query(..., description="Memory scope"),
    project_id: str | None = None,
    session_id: str | None = None,
):
    """Store a new memory.

    Args:
        content: Memory content
        scope: Memory scope (global, project, session)
        project_id: Project ID (required for project scope)
        session_id: Session ID (required for session scope)

    Returns:
        Created memory entry
    """
    try:
        service = _get_memory_service()
        entry = await service.remember(
            content=content,
            scope=scope,
            project_id=project_id,
            session_id=session_id,
        )
        return {
            "id": entry.id,
            "content": entry.content,
            "scope": entry.scope.value,
            "project_id": entry.project_id,
            "session_id": entry.session_id,
            "created_at": entry.created_at.isoformat(),
            "metadata": entry.metadata,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/recall")
async def recall(
    query: str = Query(..., description="Query text to search for"),
    scope: MemoryScope = Query(..., description="Memory scope to search within"),
    limit: int = Query(default=10, ge=1, le=100),
    project_id: str | None = None,
    session_id: str | None = None,
):
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
    try:
        service = _get_memory_service()
        memories = await service.recall_memories(
            query=query,
            scope=scope,
            limit=limit,
            project_id=project_id,
            session_id=session_id,
        )
        return {
            "memories": [
                {
                    "id": m.id,
                    "content": m.content,
                    "scope": m.scope.value,
                    "project_id": m.project_id,
                    "session_id": m.session_id,
                    "created_at": m.created_at.isoformat(),
                    "metadata": m.metadata,
                }
                for m in memories
            ],
            "count": len(memories),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/forget/{memory_id}")
async def forget(memory_id: str):
    """Forget (delete) a memory.

    Args:
        memory_id: ID of the memory to forget

    Returns:
        Confirmation message
    """
    try:
        service = _get_memory_service()
        await service.forget_memory(memory_id)
        return {"status": "success", "message": f"Memory {memory_id} forgotten"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/list")
async def list_memories(
    scope: MemoryScope | None = None,
    project_id: str | None = None,
    session_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
):
    """List memories with optional filters.

    Args:
        scope: Filter by scope
        project_id: Filter by project ID
        session_id: Filter by session ID
        limit: Maximum number of results

    Returns:
        List of memory entries
    """
    try:
        service = _get_memory_service()
        memories = await service.list_memories(
            scope=scope,
            project_id=project_id,
            session_id=session_id,
            limit=limit,
        )
        return {
            "memories": [
                {
                    "id": m.id,
                    "content": m.content,
                    "scope": m.scope.value,
                    "project_id": m.project_id,
                    "session_id": m.session_id,
                    "created_at": m.created_at.isoformat(),
                    "metadata": m.metadata,
                }
                for m in memories
            ],
            "count": len(memories),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/get/{memory_id}")
async def get_memory(memory_id: str):
    """Get a specific memory by ID.

    Args:
        memory_id: ID of the memory to retrieve

    Returns:
        Memory entry if found
    """
    try:
        service = _get_memory_service()
        memory = await service.get_memory(memory_id)
        if not memory:
            raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")

        return {
            "id": memory.id,
            "content": memory.content,
            "scope": memory.scope.value,
            "project_id": memory.project_id,
            "session_id": memory.session_id,
            "created_at": memory.created_at.isoformat(),
            "metadata": memory.metadata,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
