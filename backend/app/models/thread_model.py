# pylint: disable=missing-module-docstring
from typing import Any, ClassVar, Dict, Optional
from datetime import datetime
import uuid
from sqlmodel import JSON, SQLModel, Field, Column, DateTime

from app.utils.datetime_utils import utc_now
from app.utils.uuid6 import uuid6 

class ThreadBase(SQLModel):
    title: str = Field(default=None, index=False)
    
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), index=True)
    )
    created_by: Optional[str] = Field(default=None, index=True)
    
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), index=True)
    )
    
    last_message_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), index=True)
    )

    is_archived: bool = Field(default=False, index=True)
    
    workspace_id: Optional[str] = Field(default=None, index=True)
    
    thread_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON), # Giữ nguyên cho kiểu JSON
        description="Meta data as JSON, may be NULL."
    )

class ThreadModel(ThreadBase, table=True):
    __tablename__: ClassVar[str] = "threads" 
    id: Optional[uuid.UUID] = Field(default_factory=uuid6, primary_key=True)