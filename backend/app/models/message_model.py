import uuid
from pydantic import BaseModel
from sqlmodel import  Column, DateTime, SQLModel, Field, String, Text
from typing import Any, ClassVar, Dict, List, Optional
from datetime import datetime
from app.schemas.thread_schema import ContentItem, ContentMetadata, ContentStatus
from app.utils.datetime_utils import utc_now
from app.utils.uuid6 import uuid6
from enum import Enum
from sqlalchemy import types

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
class ContentMetadataType(types.TypeDecorator):
    impl = types.JSON

    def process_bind_param(self, value: Optional[ContentMetadata], dialect) -> Optional[Dict[str, Any]]:
        if value is None:
            return None
        if isinstance(value, ContentMetadata):
            return value.model_dump()
        return value

    def process_result_value(self, value: Optional[Dict[str, Any]], dialect) -> Optional[ContentMetadata]:
        if value is None:
            return None
        return ContentMetadata(**value)

class MessageBase(SQLModel):
    
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), index=True)
    )
    
    role: MessageRole = Field(
        default=MessageRole.USER,
        sa_column=Column(types.Enum(MessageRole), index=True, nullable=False)
    )
    
    thread_id: Optional[uuid.UUID] = Field(default=None, index=True)
    
    message_id: Optional[str] = Field(default=None, index=False)
    
    parent_id: Optional[str] = Field(default=None, index=True)
    
    created_by: Optional[str] = Field(default=None, index=True)
    
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), index=True)
    )
    
    updated_by: Optional[str] = Field(default=None, index=False)
    
    msg_metadata: ContentMetadata = Field(
        default=None,
        sa_column=Column(ContentMetadataType, nullable=True, index=False)
    )
    
    format: str = Field()
    
    content: str = Field(
        sa_column=Column(Text, nullable=False, index=False))
    height: int = Field(default=0)

class MessageModel(MessageBase, table=True):
    __tablename__: ClassVar[str] = "messages" 
    id: Optional[uuid.UUID] = Field(default_factory=uuid6, primary_key=True)