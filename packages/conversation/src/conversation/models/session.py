"""Session database model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from conversation.models.base import Base


class SessionModel(Base):
    """Conversation session model."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    turns: Mapped[list] = relationship(
        "TurnModel",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="TurnModel.created_at",
    )

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, title={self.title})>"
