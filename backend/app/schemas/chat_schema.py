from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class ChatRequest2 (BaseModel):
    """
    Schema for AI chat request.
    """
    message: str = Field(..., description="The latest message from the user.")
    history: List[str] = Field(default_factory=list, description="A list of previous messages in the conversation, alternating user/AI.")
    systemInstructions: Optional[str] = Field(None, description="Optional system instructions for the AI.")
    
class ChatResponse2 (BaseModel):
    """
    Schema for AI chat response.
    """
    response: str = Field(..., description="The AI's response message.")
    