"""Pydantic schemas for chat message requests and responses."""
import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import uuid
from pydantic import BaseModel, Field

from app.models.message_model import MessageRole

class HistoryType(Enum):
    """
    Enum for message history types.
    """
    HUMAN = "human"
    AI = "ai"


class MessageRequest(BaseModel):
    """
    Schema for AI chat request.
    """
    message: str = Field(..., description="The latest message from the user.", min_length=2)
    history: List[Tuple[HistoryType, str]] = Field(
        default_factory=list,
        description="A list of previous messages in the conversation, alternating user/AI."
    )
    system_instructions: Optional[str] = Field(None, description="Optional system instructions for the AI.")
    thread_id: Optional[str] = Field(None, description="Optional thread ID for the conversation.")
    # message_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadata tùy chọn cho tin nhắn.")
    class Config:
        # Cho phép Pydantic sử dụng Enum làm giá trị
        use_enum_values = True
        # Ví dụ về dữ liệu mẫu cho OpenAPI docs
        json_schema_extra = {
            "example": {
                "message": "Xin chào, bạn có thể giúp tôi không?",
                "history": [
                    (MessageRole.HUMAN, "Tôi cần thông tin về sản phẩm X."),
                    (MessageRole.AI, "Chào bạn, sản phẩm X có các tính năng A, B, C.")
                ],
                "thread_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "system_instructions": "Hãy trả lời một cách thân thiện và chuyên nghiệp.",
                # "message_metadata": {"client_version": "1.2.3"}
            }
        }
        


# class MessageResponse(BaseModel):
#     id: uuid.UUID
#     message_id: str
#     thread_id: uuid.UUID
#     content: str
#     role: MessageRole
#     created_at: datetime
#     message_metadata: Optional[Dict[str, Any]]

   
        
# class ThreadResponse(BaseModel):
#     id: uuid.UUID
#     title: str
#     user_id: Optional[int]
#     created_at: datetime
#     # messages: List[MessageResponse] 

    