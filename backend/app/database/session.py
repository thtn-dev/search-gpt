"""
Database session management for async operations.
"""
from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator

import orjson
from fastapi import Depends
from sqlalchemy import AsyncAdaptedQueuePool, text
from sqlalchemy.ext.asyncio import AsyncSession as SqlaAsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config.appsettings import get_settings

# Database URLs
DATABASE_URL = get_settings().database.default_connection
ASYNC_DATABASE_URL = DATABASE_URL.replace(
    'postgresql://', 'postgresql+asyncpg://'
)


def json_serializer(obj):
    return orjson.dumps(obj, default=str).decode("utf-8")


def json_deserializer(obj):
    return orjson.loads(obj)


# Async engine and session
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=True,
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600,
    max_overflow=10,
    pool_size=20,
    pool_timeout=30,
    poolclass=AsyncAdaptedQueuePool,
    connect_args={
        'server_settings': {
            'jit': 'off',  # Tắt JIT cho performance ổn định
            'application_name': 'fastapi_ai_explorer',
        },
        'command_timeout': 60,  # Timeout cho commands
        'ssl': 'prefer',  # SSL settings
    },
    json_serializer=json_serializer,
    json_deserializer=json_deserializer,
)

# Use async_sessionmaker instead of sessionmaker for async sessions
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=SqlaAsyncSession,
    autoflush=False,
    expire_on_commit=False,
)

async def get_async_session() -> AsyncGenerator[SqlaAsyncSession, None]:
    """Dependency to get an AsyncSession for FastAPI."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

@asynccontextmanager
async def get_async_ctx_session() -> AsyncGenerator[SqlaAsyncSession, None]:
    """Context manager to get an AsyncSession."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


# Alternative: Manual session management (if needed)
async def create_async_session() -> SqlaAsyncSession:
    """Create a new AsyncSession manually."""
    return AsyncSessionLocal()


# For dependency injection in FastAPI
async def get_db() -> AsyncGenerator[SqlaAsyncSession, None]:
    """FastAPI dependency for database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def check_db_health():
    try:
        async with async_engine.begin() as conn:
            result = await conn.execute(text('SELECT 1'))
            return result.scalar() == 1
    except Exception:
        return False

AsyncDbSession = Annotated[SqlaAsyncSession, Depends(get_db)]
