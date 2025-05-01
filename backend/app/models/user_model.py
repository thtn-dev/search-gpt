from sqlmodel import Column, ForeignKey, Integer, Relationship, SQLModel, Field, UniqueConstraint
from typing import List, Optional
from datetime import datetime
from pydantic import EmailStr

class UserBase(SQLModel):
    username: str = Field(index=True, unique=True, max_length=50, nullable=True)
    email: EmailStr = Field(index=True, unique=True, nullable=False)
    hashed_password: str = Field(nullable=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserModel(UserBase, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    
    linked_accounts: List["LinkedAccountModel"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"}
    )
class LinkedAccountModel(SQLModel, table=True):
    __tablename__ = "linked_accounts"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(
        sa_column=Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    )
    provider: str = Field(max_length=50, nullable=False)
    provider_key: str = Field(max_length=255, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    user: Optional[UserModel] = Relationship(back_populates="linked_accounts")
    
    __table_args__ = (
        UniqueConstraint("provider", "provider_key", name="unique_provider_user"),
    )
    
    
    


