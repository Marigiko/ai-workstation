"""Tests for conversation service."""

import pytest
from conversation import ConversationService
from conversation.models.base import Base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest.fixture
async def db_session():
    """Create in-memory SQLite test database."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.mark.asyncio
async def test_create_session(db_session):
    """Test creating a session."""
    service = ConversationService(db_session)
    session = await service.create_session(title="Test Session")

    assert session.id is not None
    assert session.title == "Test Session"
    assert session.created_at is not None


@pytest.mark.asyncio
async def test_get_session(db_session):
    """Test getting a session by ID."""
    service = ConversationService(db_session)
    created = await service.create_session(title="Test")

    retrieved = await service.get_session(created.id)
    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.title == "Test"


@pytest.mark.asyncio
async def test_list_sessions(db_session):
    """Test listing sessions."""
    service = ConversationService(db_session)

    await service.create_session(title="Session 1")
    await service.create_session(title="Session 2")

    sessions = await service.list_sessions()
    assert len(sessions) == 2


@pytest.mark.asyncio
async def test_add_turn(db_session):
    """Test adding a turn to a session."""
    service = ConversationService(db_session)
    session = await service.create_session(title="Test")

    turn = await service.add_turn(
        session_id=session.id,
        role="user",
        content="Hello",
    )

    assert turn.id is not None
    assert turn.session_id == session.id
    assert turn.role == "user"
    assert turn.content == "Hello"


@pytest.mark.asyncio
async def test_get_history(db_session):
    """Test getting conversation history."""
    service = ConversationService(db_session)
    session = await service.create_session(title="Test")

    await service.add_turn(session_id=session.id, role="user", content="Hi")
    await service.add_turn(session_id=session.id, role="assistant", content="Hello!")

    history = await service.get_history(session.id)
    assert len(history) == 2
    assert history[0].role.value == "user"
    assert history[0].content == "Hi"
    assert history[1].role.value == "assistant"
    assert history[1].content == "Hello!"


@pytest.mark.asyncio
async def test_delete_session(db_session):
    """Test deleting a session."""
    service = ConversationService(db_session)
    session = await service.create_session(title="To Delete")

    deleted = await service.delete_session(session.id)
    assert deleted is True

    retrieved = await service.get_session(session.id)
    assert retrieved is None
