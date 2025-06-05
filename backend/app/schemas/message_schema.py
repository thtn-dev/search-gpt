"""Pydantic schemas for chat message requests and responses."""

import secrets
import time
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field

from app.models.message_model import MessageRole


def gen_message_id() -> str:
    """Tạo ID tin nhắn duy nhất dựa trên timestamp và hex."""
    timestamp = int(time.time() * 1e6)  # microseconds for higher uniqueness
    hex_part = secrets.token_hex(8)
    return f'{timestamp:x}-{hex_part}'


class Messsage(BaseModel):
    message_id: Optional[str] = Field(
        description='Unique identifier for the message, generated if not provided.',
        min_length=16,
    )
    content: str = Field(..., description='The content of the message.', min_length=2)
    thread_id: Optional[str] = Field(
        None, description='Optional thread ID for the conversation.'
    )


class MessageCreateRequest(Messsage):
    role: MessageRole = Field(
        MessageRole.USER, description='The role of the message sender, default is USER.'
    )


class MessageRequest(BaseModel):
    """
    Schema for AI chat request.
    """

    message: Messsage = Field(
        ..., description='The message content and metadata for the AI chat request.'
    )
    history: List[Tuple[MessageRole, str]] = Field(
        default_factory=list,
        description='A list of previous messages in the conversation, alternating user/AI.',
    )
    system_instructions: Optional[str] = Field(
        None, description='Optional system instructions for the AI.'
    )

    class Config:
        use_enum_values = True
        # Example for the schema
        json_schema_extra = {
            'example': {
                'message': {
                    'message_id': gen_message_id(),
                    'content': 'Xin chào, tôi cần giúp đỡ với sản phẩm X.',
                    'thread_id': 'a1b2c3d4-e5f6-7890-1234-567890abcdef',
                },
                'history': [
                    (MessageRole.USER, 'Tôi cần thông tin về sản phẩm X.'),
                    (
                        MessageRole.ASSISTANT,
                        'Chào bạn, sản phẩm X có các tính năng A, B, C.',
                    ),
                ],
                'system_instructions': 'Hãy trả lời một cách thân thiện và chuyên nghiệp.',
            }
        }
