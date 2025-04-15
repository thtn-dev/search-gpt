from __future__ import annotations
from sqlmodel import Relationship, SQLModel, Field
from typing import List, Optional
from datetime import datetime, timezone

class ThreadModel(SQLModel, table=True):
    __tablename__ = "threads"
    id: Optional[str] = Field(default=None, primary_key=True)
    title: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: int = Field(foreign_key="users.id", index=True)
    
    # Relationship Messages
    messages: List["MessageModel"] = Relationship(back_populates="thread") # type: ignore
    user: "UserModel" = Relationship(back_populates="threads") # type: ignore


