from __future__ import annotations
from sqlmodel import Relationship, SQLModel, Field
from typing import List, Optional
from datetime import datetime, timezone

class MessageModel(SQLModel, table=True):
    __tablename__ = "messages"
    id: Optional[int] = Field(default=None, primary_key=True)
    thread_id: str = Field(foreign_key="threads.id", index=True)
    content: str = Field()
    sender: str = Field(default="user") 
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationship Thread
    thread: "ThreadModel" = Relationship(back_populates="messages") # type: ignore