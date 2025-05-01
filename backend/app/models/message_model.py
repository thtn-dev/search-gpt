import uuid
from sqlmodel import SQLModel, Field
from typing import  Optional
from datetime import datetime, timezone

from app.utils.uuid6 import uuid6



class MessageBase(SQLModel):
    content: str = Field()
    sender: str = Field(default="user") 
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    thread_id: Optional[uuid.UUID] = Field(default=None, index=True)

class MessageModel(MessageBase, table=True):
    __tablename__ = "messages"
    id: Optional[uuid.UUID] = Field(default_factory=uuid6, primary_key=True)