from sqlmodel import create_engine, Session
from typing import AsyncGenerator, Generator
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
    # Tăng thời gian timeout cho các kết nối
    pool_pre_ping=True,  # Kiểm tra kết nối trước khi sử dụng
    pool_recycle=3600,   # Tái tạo kết nối sau 1 giờ
)

async_session_factory = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Tạo và quản lý async session với context manager"""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Sync engine and session
sync_engine = create_engine(
    DATABASE_URL,
    echo=True,
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600,
)

sync_session_factory = sessionmaker(
    bind=sync_engine,
    class_=Session,
    expire_on_commit=False,
)

def get_session() -> Generator[Session, None, None]:
    """Tạo và quản lý sync session với context manager"""
    with sync_session_factory() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()