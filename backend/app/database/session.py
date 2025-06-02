# type: ignore
"""
Database session management for async operations.
"""
from typing import AsyncGenerator
from fastapi.concurrency import asynccontextmanager
from sqlalchemy import AsyncAdaptedQueuePool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings

# Database URLs
DATABASE_URL = settings.DATABASE_URL
ASYNC_DATABASE_URL = settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')


# Async engine and session
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=True,
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600,
    poolclass=AsyncAdaptedQueuePool,
    connect_args={
        "ssl": False, 
    }
)

AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get an AsyncSession."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
            

@asynccontextmanager
async def get_async_ctx_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager to get an AsyncSession."""
    async_session = AsyncSessionLocal()
    try:
        yield async_session
        # Không commit ở đây, để logic nghiệp vụ tự commit
    except Exception:
        await async_session.rollback()
        raise
    finally:
        await async_session.close()
