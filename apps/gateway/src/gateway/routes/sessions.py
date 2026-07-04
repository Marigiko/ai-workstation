"""Sessions endpoints."""

from conversation import ConversationService
from conversation.database import get_session
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("")
async def create_session(
    title: str | None = None,
    db: AsyncSession = Depends(get_session),
):
    """Create a new conversation session."""
    service = ConversationService(db)
    session = await service.create_session(title=title)
    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }


@router.get("")
async def list_sessions(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_session),
):
    """List recent sessions."""
    service = ConversationService(db)
    sessions = await service.list_sessions(limit=limit, offset=offset)
    return [
        {
            "id": s.id,
            "title": s.title,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat(),
        }
        for s in sessions
    ]


@router.get("/{session_id}")
async def get_session_endpoint(
    session_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Get a session with all turns."""
    service = ConversationService(db)
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "turns": [
            {
                "id": t.id,
                "role": t.role,
                "content": t.content,
                "model": t.model,
                "provider": t.provider,
                "tokens_used": t.tokens_used,
                "latency_ms": t.latency_ms,
                "created_at": t.created_at.isoformat(),
            }
            for t in session.turns
        ],
    }


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Delete a session."""
    service = ConversationService(db)
    deleted = await service.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": True}
