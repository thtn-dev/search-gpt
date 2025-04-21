from sqlmodel import Relationship, SQLModel, Field
from typing import TYPE_CHECKING, Optional
from datetime import datetime, timezone

if TYPE_CHECKING:
    from app.models.thread_model import ThreadModel  # noqa: F401

class MessageBase(SQLModel):
    content: str = Field()
    sender: str = Field(default="user") 
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    thread_id: str = Field(foreign_key="threads.id", index=True)

class MessageModel(MessageBase, table=True):
    __tablename__ = "messages"
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationship Thread
    thread: "ThreadModel" = Relationship( 
        back_populates="messages") 
    
