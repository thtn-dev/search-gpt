
"""
BaseUUIDModel
This module defines a base model class for SQLModel that uses UUIDs as primary keys.
"""
from uuid import UUID, uuid4
from datetime import datetime
from sqlmodel import SQLModel, Field

class BaseUUIDModel(SQLModel):
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    updated_at: datetime | None = Field(
        default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow}
    )
    created_at: datetime | None = Field(default_factory=datetime.utcnow)
