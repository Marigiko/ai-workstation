"""Database configuration and session management."""

import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = os.getenv("DATABASE_URL")

engine = None
async_session_factory = None

if DATABASE_URL:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


def _require_db():
    """Raise if DATABASE_URL was not set."""
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL environment variable is required. "
            "Example: postgresql+asyncpg://user:pass@localhost:5432/ai_workstation"
        )


async def get_session() -> AsyncSession:
    """Get async database session."""
    _require_db()
    async with async_session_factory() as session:
        yield session


async def init_db():
    """Initialize database tables."""
    _require_db()
    from conversation.models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections."""
    _require_db()
    await engine.dispose()
