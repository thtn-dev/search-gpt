from enum import Enum
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field

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
    history: List[Tuple[HistoryType, str]] = Field(default_factory=list, description="A list of previous messages in the conversation, alternating user/AI.")
    systemInstructions: Optional[str] = Field(None, description="Optional system instructions for the AI.")
    
class ChatResponse2 (BaseModel):
    """
    Schema for AI chat response.
    """
    response: str = Field(..., description="The AI's response message.")
    