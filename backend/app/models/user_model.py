from __future__ import annotations
from sqlalchemy.orm import Mapped, relationship
from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from datetime import datetime, timezone

class UserModel(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())
    