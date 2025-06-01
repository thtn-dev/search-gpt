from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator

class ThreadResponse(BaseModel):
    id: int
    title: str
    content: str
    
class ThreadsResponse(BaseModel):
    threads: list[ThreadResponse]
    

class CreateThreadRequestSchema(BaseModel):
    last_message_at: datetime
    
class CreateThreadResponseSchema(BaseModel):
    """
    Schema Pydantic cho phản hồi tạo chủ đề.
    """
    thread_id: str
    
class Usage(BaseModel):
    promptTokens: Optional[int] = None
    completionTokens: Optional[int] = None

class Step(BaseModel):
    state: Optional[str] = None
    messageId: Optional[str] = None
    finishReason: Optional[str] = None
    isContinued: bool = False
    usage: Optional[Usage] = None

class ContentMetadata(BaseModel):
    unstable_annotations: List[Any] | None = None
    unstable_data: List[Any] | None = None
    steps: List[Step] | None = None
    custom: Dict[str, Any] | None = None

class CreateThreadRequest(BaseModel):
    title: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "title": "Hỗ trợ sản phẩm X"
            }
        }