from sqlmodel import SQLModel, Field, Relationship, Column, String
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from pydantic import EmailStr

if TYPE_CHECKING:
    from app.models.thread_model import ThreadModel  # noqa: F401

class UserBase(SQLModel):
    username: str = Field(sa_column=Column(String, index=True, unique=True))
    email: EmailStr = Field(sa_column=Column(String, index=True, unique=True))
    hashed_password: str = Field(sa_column=Column(String))
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserModel(UserBase, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    # Relationship Threads
    threads: List["ThreadModel"] = Relationship( 
        back_populates="user") 
    


