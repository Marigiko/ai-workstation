"""Conversation service for managing sessions and turns."""

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from contracts import Message, Role
from conversation.models.session import SessionModel
from conversation.models.turn import TurnModel

logger = logging.getLogger(__name__)


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

    async def get_history(
        self,
        session_id: str,
        max_turns: int | None = None,
        max_tokens: int | None = None,
    ) -> list[Message]:
        """Get conversation history as Message list.

        Args:
            session_id: Session ID to retrieve history for
            max_turns: Maximum number of recent turns to return.
                If None, returns all turns.
            max_tokens: Maximum total tokens (approximate).
                If set, truncates oldest messages first to fit budget.

        Returns:
            List of messages ordered by creation time.
        """
        stmt = (
            select(TurnModel)
            .where(TurnModel.session_id == session_id)
            .order_by(TurnModel.created_at.asc())
        )

        result = await self.session.execute(stmt)
        turns = list(result.scalars().all())

        # Keep only the most recent N turns if max_turns is set
        if max_turns and len(turns) > max_turns:
            turns = turns[-max_turns:]

        messages = [
            Message(role=Role(turn.role), content=turn.content)
            for turn in turns
        ]

        if max_tokens and messages:
            messages = self._truncate_by_tokens(messages, max_tokens)

        return messages

    def _truncate_by_tokens(
        self, messages: list[Message], max_tokens: int
    ) -> list[Message]:
        """Truncate messages to fit token budget (oldest first)."""
        try:
            import tiktoken
            encoder = tiktoken.get_encoding("cl100k_base")
        except ImportError:
            logger.warning("tiktoken not available, skipping token truncation")
            return messages

        result = []
        total_tokens = 0
        # Iterate in reverse (newest first) to keep recent context
        for msg in reversed(messages):
            token_count = len(encoder.encode(msg.content))
            if total_tokens + token_count > max_tokens:
                break
            result.append(msg)
            total_tokens += token_count

        result.reverse()
        if len(result) < len(messages):
            logger.info(
                "Truncated history from %d to %d messages (token budget: %d)",
                len(messages),
                len(result),
                max_tokens,
            )
        return result
