import uuid
from pydantic import BaseModel
from sqlmodel import  Column, DateTime, SQLModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime
from app.utils.datetime_utils import utc_now
from app.utils.uuid6 import uuid6
from enum import Enum
from sqlalchemy import types

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"

class Usage(BaseModel):
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None

class Step(BaseModel):
    state: str
    message_id: str
    finishReason: str
    isContinued: bool = False
    usage: Optional[Usage] = None

class ContentMetadata(BaseModel):
    unstable_annotations: Optional[List[Any]] = None
    unstable_data: Optional[List[Any]] = None
    steps: Optional[List[Step]] = None
    custom: Optional[Dict[str, Any]] = None

class ContentStatus(BaseModel):
    type: Optional[str] = None
    reason: Optional[str] = None

class Content(BaseModel):  # Pydantic model, not SQLModel
    role: Optional[MessageRole] = None
    content: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[ContentMetadata] = None
    status: Optional[ContentStatus] = None
    
    # Add method to convert to dict for storage
    def to_json(self):
        return self.model_dump(exclude_none=True)

# Custom SQLAlchemy type for Content objects
class ContentType(types.TypeDecorator):
    impl = types.JSON

    def process_bind_param(self, value):
        if value is None:
            return None
        if isinstance(value, Content):
            return value.to_json()
        return value
    
    def process_result_value(self, value):
        if value is None:
            return None
        return Content(**value)

class MessageBase(SQLModel):
    content: str = Field()
    
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), index=True)
    )
    
    thread_id: Optional[uuid.UUID] = Field(default=None, index=True)
    
    message_id: Optional[str] = Field(default=None, index=True)
    
    parent_id: Optional[str] = Field(default=None, index=True)
    
    created_by: Optional[str] = Field(default=None, index=True)
    
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), index=True)
    )
    
    updated_by: Optional[str] = Field(default=None, index=None)
    
    format: str = Field()
    
    content: Optional[Content] = Field(
        default=None,
        sa_column=Column(ContentType),
        description="Content as JSON, may be NULL."
    )
    
    height: int = Field(default=0)

class MessageModel(MessageBase, table=True):
    __tablename__ = "messages"
    id: Optional[uuid.UUID] = Field(default_factory=uuid6, primary_key=True)