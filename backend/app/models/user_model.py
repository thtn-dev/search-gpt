"""SQLModel definitions for User and LinkedAccount entities."""
from datetime import datetime
from typing import List, Optional

from pydantic import EmailStr
from sqlmodel import (
    Column,
    Field,
    ForeignKey,
    Integer,
    Relationship,
    SQLModel,
    UniqueConstraint,
)


class UserBase(SQLModel):
    """Base model for user attributes, shared between creation and read models."""
    username: Optional[str] = Field(
        default=None, index=True, unique=True, max_length=50, nullable=True
    ) # Username can be optional if email is primary identifier
    email: EmailStr = Field(index=True, unique=True, nullable=False)
    hashed_password: Optional[str] = Field(default=None, nullable=True) # Nullable for social logins
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class UserModel(UserBase, table=True):
    """Database model for users."""
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)

    linked_accounts: List["LinkedAccountModel"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"}
    )


class LinkedAccountModel(SQLModel, table=True):
    """Database model for linking external OAuth provider accounts to a user."""
    __tablename__ = "linked_accounts"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(
        sa_column=Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    )
    provider: str = Field(max_length=50, nullable=False) # e.g., "google", "github"
    provider_key: str = Field(max_length=255, nullable=False) # User's unique ID from the provider
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    user: Optional[UserModel] = Relationship(back_populates="linked_accounts")

    __table_args__ = (
        UniqueConstraint("provider", "provider_key", name="uq_provider_provider_key"),
        # Consider a unique constraint on user_id and provider if a user can only link one account per provider
        # UniqueConstraint("user_id", "provider", name="uq_user_provider"),
    )
