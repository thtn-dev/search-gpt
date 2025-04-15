import asyncio
import json
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import Any
from app.core.exceptions import gemini_exception_handler, GeminiAPIException
from app.library.providers.gemini import load_gemini_chat_models
from app.models.chat_model import ChatRequest, ChatResponse
from app.schemas.chat_schema import ChatRequest2, ChatResponse2
from app.services.gemini_service import GeminiService
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel


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
     
     
@router.post("/chat2")
async def chat2(
    request: ChatRequest2 = Body(...)
) -> ChatResponse2:
    models = load_gemini_chat_models()
    llm = models.get("gemini-2.0-flash")
    if not llm:
        raise HTTPException(status_code=503, detail="LLM service is unavailable.")
    
    print(f"Received message for /chat: {request.message}")
    
    messages = [
        HumanMessage(content=request.message)
    ]
    
    try:
        response = await llm.model.ainvoke(messages)
        print(f"LLM response for /chat: {response.content}")
        return ChatResponse2(response=response.content)
    except Exception as e:
        print(f"Error during LLM invocation for /chat: {e}") 
        raise HTTPException(status_code=500, detail="Internal server error.")

async def _stream_generator(messages: list, llm: BaseChatModel):
    """
    Async generator để tạo ra các chunk phản hồi từ LLM.
    """
    if llm is None:
        # Không thể raise HTTPException từ generator, nên cần cách xử lý khác
        # Có thể yield một thông báo lỗi đặc biệt
        yield f"data: {json.dumps({'error': 'LLM service is unavailable.'})}\n\n"
        return

    print("Starting stream generation...") # Logging
    try:
        # Sử dụng astream để nhận các chunk phản hồi
        async for chunk in llm.astream(messages):
            if chunk.content:
                # Định dạng theo Server-Sent Events (SSE)
                # Mỗi chunk được gửi dưới dạng: "data: <json_string>\n\n"
                yield f"data: {json.dumps({'chk': chunk.content}, ensure_ascii=False)}\n\n"
                # print(f"Sent chunk: {chunk.content}") # Logging (có thể tạo nhiều log)
                await asyncio.sleep(0.01) # Thêm delay nhỏ để tránh quá tải client (tùy chọn)

        # (Tùy chọn) Gửi một thông điệp kết thúc stream
        yield f"data: {json.dumps({'eofs': True})}\n\n"
        print("Stream generation finished.") # Logging

    except Exception as e:
        error_message = f"Error during LLM streaming: {str(e)}"
        print(error_message) # Logging
        # Gửi thông báo lỗi qua stream
        yield f"e: {json.dumps({'error': error_message})}\n\n"

@router.post("/chat2/stream")
async def chat_stream_endpoint(request: ChatRequest2):
    """
    Nhận tin nhắn từ client và trả về phản hồi dạng luồng (streaming) từ Gemini.
    """
    print(f"Received message for /chat/stream: {request.message}") # Logging
    models = load_gemini_chat_models()
    llm = models.get("gemini-2.0-flash")
    if not llm:
        raise HTTPException(status_code=503, detail="LLM service is unavailable.")
    # --- Chuẩn bị prompt (tương tự /chat) ---
    messages = [
        HumanMessage(content=request.message)
    ]

    # Trả về StreamingResponse với generator và media type phù hợp cho SSE
    return StreamingResponse(
        _stream_generator(messages, llm.model),
        media_type="text/event-stream",
        headers={"Content-Type": "text/event-stream"}
    )