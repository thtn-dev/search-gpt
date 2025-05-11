# pylint: disable=missing-module-docstring
import uuid
from sqlmodel import JSON, Column, SQLModel, Field, String
from typing import  Any, Dict, Optional
from datetime import datetime
from app.utils.uuid6 import uuid6
from enum import Enum

class MessageRole(str, Enum):
    HUMAN = "human"
    AI = "ai"

class MessageBase(SQLModel):
    content: str = Field()
    created_at: datetime = Field(default_factory=datetime.utcnow)
    thread_id: Optional[uuid.UUID] = Field(default=None, index=True)
    message_id: Optional[str] = Field(default=None, index=True)
    
    role: MessageRole = Field(
        default=MessageRole.HUMAN,
        sa_column=Column(String, nullable=False),
    )
    message_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Meta data as JSON, may be NULL."
    )

class MessageModel(MessageBase, table=True):
    __tablename__ = "messages"
    id: Optional[uuid.UUID] = Field(default_factory=uuid6, primary_key=True)
