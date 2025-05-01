from sqlmodel import SQLModel, Field
from typing import  Optional
from datetime import datetime, timezone
import uuid
from app.utils.uuid6 import uuid6
class ThreadBase(SQLModel):
    title: str = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: Optional[int] = Field(default=None, index=True)

class ThreadModel(ThreadBase, table=True):
    __tablename__ = "threads"
    id: Optional[uuid.UUID] = Field(default_factory=uuid6, primary_key=True)