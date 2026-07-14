"""Conversation service for managing sessions and turns."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from contracts import Message, Role
from conversation.models.session import SessionModel
from conversation.models.turn import TurnModel


class ConversationService:
    """Service for conversation management."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(self, title: str | None = None) -> SessionModel:
        """Create a new conversation session."""
        session_model = SessionModel(title=title)
        self.session.add(session_model)
        await self.session.commit()
        await self.session.refresh(session_model)
        return session_model

    async def get_session(self, session_id: str) -> SessionModel | None:
        """Get a session by ID with all turns."""
        stmt = (
            select(SessionModel)
            .where(SessionModel.id == session_id)
            .options(selectinload(SessionModel.turns))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_sessions(self, limit: int = 50, offset: int = 0) -> list[SessionModel]:
        """List recent sessions."""
        stmt = (
            select(SessionModel)
            .order_by(SessionModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its turns."""
        session_model = await self.get_session(session_id)
        if not session_model:
            return False
        await self.session.delete(session_model)
        await self.session.commit()
        return True

    async def add_turn(
        self,
        session_id: str,
        role: str,
        content: str,
        model: str | None = None,
        provider: str | None = None,
        tokens_used: int | None = None,
        latency_ms: float | None = None,
    ) -> TurnModel:
        """Add a turn to a session."""
        turn = TurnModel(
            session_id=session_id,
            role=role,
            content=content,
            model=model,
            provider=provider,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
        )
        self.session.add(turn)

        session_model = await self.get_session(session_id)
        if session_model:
            session_model.updated_at = datetime.now(UTC)

        await self.session.commit()
        await self.session.refresh(turn)
        return turn

    async def get_history(self, session_id: str) -> list[Message]:
        """Get conversation history as Message list."""
        stmt = (
            select(TurnModel)
            .where(TurnModel.session_id == session_id)
            .order_by(TurnModel.created_at)
        )
        result = await self.session.execute(stmt)
        turns = result.scalars().all()

        return [
            Message(role=Role(turn.role), content=turn.content)
            for turn in turns
        ]
