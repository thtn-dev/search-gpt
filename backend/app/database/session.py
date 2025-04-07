from sqlmodel import create_engine, Session
from typing import Generator
from app.config.settings import settings

DATABASE_URL = settings.DATABASE_URL

engine = create_engine(
    DATABASE_URL,
)

def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
