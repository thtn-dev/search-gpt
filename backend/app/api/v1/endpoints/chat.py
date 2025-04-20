import asyncio
import json
from fastapi import APIRouter, Body, Depends, HTTPException, status
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
        yield f"data: {json.dumps({'err': 'LLM service is unavailable.'})}\n\n"
        return

    print("Starting stream generation...")
    try:
        async for chunk in llm.astream(messages):
            if chunk.content:
                # format: "data: <json_string>\n\n"
                yield f"data: {json.dumps({'chk': chunk.content}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.01)
    except Exception as e:
        error_message = f"Error during LLM streaming: {str(e)}"
        print(error_message) 
        yield f"event: {json.dumps({'err': error_message})}\n\n"
    finally:
        yield f"event: {json.dumps({'eofs': True})}\n\n"
        print("Stream generation finished.")

@router.post("/chat2/stream",
            summary="Process a chat message with streaming",
            description="Receives a user message and conversation history, streams the AI's reply chunk by chunk using Server-Sent Events (SSE).",
            tags=["Chat (Streaming)"])
async def chat_stream_endpoint(request: ChatRequest2):
    """
    Handles incoming chat requests and streams the response.
    """
    print(f"Received message for /chat/stream: {request.message}") # Logging
    models = load_gemini_chat_models()
    llm = models.get("gemini-2.0-flash")
    if not llm:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM model is not available due to initialization error."
        )
    # --- Prepare messages for Langchain ---
    messages = []
    if request.systemInstructions:
        messages.append(SystemMessage(content=request.systemInstructions))
        print(f"   Added System Message: {request.systemInstructions}")
    else:
        print("   No System Message provided.")
    
    for i, msg_content in enumerate(request.history):
        if i % 2 == 0: # Even index = User message (assuming history starts with user)
            messages.append(HumanMessage(content=msg_content))
            print(f"   Added History (Human): {msg_content}")
        else: # Odd index = AI message
            messages.append(AIMessage(content=msg_content))
            print(f"   Added History (AI): {msg_content}")
            
    messages.append(HumanMessage(content=request.message))
    print(f"   Added Current User Message: {request.message}")        
    # Trả về StreamingResponse với generator và media type phù hợp cho SSE
    return StreamingResponse(
        _stream_generator(messages, llm.model),
        media_type="text/event-stream",
        headers={"Content-Type": "text/event-stream"}
    )