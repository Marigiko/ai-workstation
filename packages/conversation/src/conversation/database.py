"""Database configuration and session management."""

import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def _get_database_url() -> str | None:
    """Read DATABASE_URL dynamically to support test isolation."""
    return os.getenv("DATABASE_URL")


_ENGINE_CACHE: tuple[str, object, object] | None = None


def _get_engine_and_factory():
    """Get or create the async engine and session factory.

    Caches by DATABASE_URL so that changing the env var between tests
    (e.g. gateway tests vs conversation tests) works correctly.
    """
    global _ENGINE_CACHE
    url = _get_database_url()
    if not url:
        return None, None
    if _ENGINE_CACHE is None or _ENGINE_CACHE[0] != url:
        engine = create_async_engine(url, echo=False, pool_pre_ping=True)
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        _ENGINE_CACHE = (url, engine, factory)
    return _ENGINE_CACHE[1], _ENGINE_CACHE[2]


def _get_engine():
    eng, _ = _get_engine_and_factory()
    return eng


def _get_factory():
    _, fac = _get_engine_and_factory()
    return fac


def _require_db():
    """Raise if DATABASE_URL was not set."""
    if not _get_database_url():
        raise RuntimeError(
            "DATABASE_URL environment variable is required. "
            "Example: postgresql+asyncpg://user:pass@localhost:5432/ai_workstation"
        )


async def get_session() -> AsyncSession:
    """Get async database session."""
    _require_db()
    factory = _get_factory()
    async with factory() as session:
        yield session


async def init_db():
    """Initialize database tables."""
    _require_db()
    from conversation.models.base import Base
    engine = _get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections."""
    _require_db()
    engine = _get_engine()
    await engine.dispose()
