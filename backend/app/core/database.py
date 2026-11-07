"""Database connection and session management."""
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

# Global engine (initialized on startup)
_engine: AsyncEngine | None = None
_async_session: type[sessionmaker[AsyncSession]] | None = None


def get_engine() -> AsyncEngine:
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        url = settings.database_url
        if "sqlite" not in url and "postgresql" in url:
            url = url.replace("postgresql", "postgresql+asyncpg")
        _engine = create_async_engine(url, echo=settings.db_echo)
    return _engine


def get_session_maker() -> type[sessionmaker[AsyncSession]]:
    """Get or create the session factory."""
    global _async_session
    if _async_session is None:
        _async_session = sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session


async def get_session() -> AsyncSession:
    """Get a database session (use as dependency)."""
    session = await get_session_maker()().__anext__()
    try:
        yield session
    finally:
        await session.close()


async def close_engine():
    """Close the database engine."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None