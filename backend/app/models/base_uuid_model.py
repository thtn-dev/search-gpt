
"""
BaseUUIDModel
This module defines a base model class for SQLModel that uses UUIDs as primary keys.
"""
from uuid import UUID
from datetime import datetime
from sqlmodel import SQLModel, Field
from app.utils.uuid6 import uuid7

class BaseUUIDModel(SQLModel):
    id: UUID = Field(
        default_factory=uuid7,
        primary_key=True,
        index=True,
        nullable=False,
    )
    updated_at: datetime | None = Field(
        default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow}
    )
    created_at: datetime | None = Field(default_factory=datetime.utcnow)
