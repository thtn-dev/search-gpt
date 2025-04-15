from pydantic import BaseModel


class ChatRequest2 (BaseModel):
    """
    Schema for AI chat request.
    """
    message: str
    
class ChatResponse2 (BaseModel):
    """
    Schema for AI chat response.
    """
    response: str
    