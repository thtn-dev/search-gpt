from sqlmodel import Relationship, SQLModel, Field
from typing import TYPE_CHECKING, List, Optional
from datetime import datetime, timezone

if TYPE_CHECKING:
    from app.models.user_model import UserModel  # noqa: F401
    from app.models.message_model import MessageModel  # noqa: F401
class ThreadBase(SQLModel):
    title: str = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: int = Field(foreign_key="users.id", index=True)

class ThreadModel(ThreadBase, table=True):
    __tablename__ = "threads"
    id: Optional[str] = Field(default=None, primary_key=True)
    
    messages: List["MessageModel"] = Relationship(  
        back_populates="thread")  
    user: "UserModel" = Relationship( 
        back_populates="threads") 


