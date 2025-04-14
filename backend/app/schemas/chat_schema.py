from pydantic import BaseModel


class ChatRequest (BaseModel):
    """
    Schema for AI chat request.
    """
    message: str
    
class ChatResponse (BaseModel):
    """
    Schema for AI chat response.
    """
    response: str
    