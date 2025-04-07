from fastapi import APIRouter, Body, Depends
from fastapi.responses import StreamingResponse
from typing import Any
from app.core.exceptions import gemini_exception_handler, GeminiAPIException
from app.models.chat_model import ChatRequest, ChatResponse
from app.services.gemini_service import GeminiService

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest = Body(...),
     _: None = Depends(gemini_exception_handler),
) -> ChatResponse:
    """Process a chat request and return a response from Gemini model.

    Args:
        request: The chat request containing message and history.

    Returns:
        ChatResponse: The model's response to the chat request.
    """
    response_text = await GeminiService.generate_chat_response(request)
    return ChatResponse(response=response_text)
    
@router.post("/stream/chat")
async def stream_chat(
    request: ChatRequest = Body(...),
    _: None = Depends(gemini_exception_handler),
) -> StreamingResponse:
    """Process a chat request and return a streaming response from Gemini model.

    Args:
        request: The chat request containing message and history.

    Returns:
        StreamingResponse: A streaming response of the model's output.
    """
    return StreamingResponse(
        GeminiService.generate_streaming_response(request),
        media_type="text/event-stream",
        headers={"Content-Type": "text/event-stream"}
        )
     