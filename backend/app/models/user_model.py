"""SQLModel definitions for User and LinkedAccount entities."""
from datetime import datetime
from typing import List, Optional
import uuid

from pydantic import EmailStr
from sqlmodel import (
    Column,
    DateTime,
    Field,
    ForeignKey,
    Relationship,
    SQLModel,
    UniqueConstraint,
)

from app.utils.datetime_utils import utc_now
from app.utils.uuid6 import uuid6


class UserBase(SQLModel):
    """Base model for user attributes, shared between creation and read models."""
    username: Optional[str] = Field(
        default=None, index=True, unique=True, max_length=50, nullable=True
    ) 
    
    email: EmailStr = Field(index=True, unique=True, nullable=False)
    
    hashed_password: Optional[str] = Field(default=None, nullable=True) 
    
    is_active: bool = Field(default=True)
    
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), index=True)
    )
    
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), index=True)
    )


class UserModel(UserBase, table=True):
    """Database model for users."""
    __tablename__ = "users"
    id: Optional[uuid.UUID] = Field(default_factory=uuid6, primary_key=True)

    linked_accounts: List["LinkedAccountModel"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"}
    )


class LinkedAccountModel(SQLModel, table=True):
    """Database model for linking external OAuth provider accounts to a user."""
    __tablename__ = "linked_accounts"
    
    id: Optional[uuid.UUID] = Field(default_factory=uuid6, primary_key=True)
    
    user_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
        )
    )
    
    provider: str = Field(max_length=50, nullable=False) 
    
    provider_key: str = Field(max_length=255, nullable=False) 
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), index=True)
    )
    
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), index=True)
    )

    user: Optional[UserModel] = Relationship(back_populates="linked_accounts")

    __table_args__ = (
        UniqueConstraint("provider", "provider_key", name="uq_provider_provider_key"),
        # Consider a unique constraint on user_id and provider if a user can only link one account per provider
        # UniqueConstraint("user_id", "provider", name="uq_user_provider"),
    )
