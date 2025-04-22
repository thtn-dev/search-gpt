from sqlmodel import create_engine, Session
from typing import Generator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings

DATABASE_URL = settings.DATABASE_URL
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
)
# Create a session factory
async_session_factory = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
# Create a session generator
async def get_async_session() -> Generator[AsyncSession, None, None]: # type: ignore
    async with async_session_factory() as session:
        yield session
# Create a synchronous engine

sync_engine = create_engine(
    DATABASE_URL,
    echo=True,
    future=True,
)
# Create a synchronous session generator
def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

async def get_session2() -> AsyncSession: # type: ignore
    async_session = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session