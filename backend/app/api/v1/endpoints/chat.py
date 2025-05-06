import asyncio
import logging
import orjson
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from app.library.providers.gemini import load_gemini_chat_models
from app.schemas.message_schema import MessageRequest
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
import secrets

logger = logging.getLogger(__name__)
router = APIRouter()

def gen_message_id() -> str:
    random_hex = secrets.token_hex(7)
    return random_hex
    

async def _stream_generator(messages: list, llm: BaseChatModel):
    """
    Async generator creating a stream of messages from the LLM.
    Yields chunks of the AI's response.
    """
    if llm is None:
        yield f"data: {orjson.dumps({'err': 'LLM service is unavailable.'}).decode('utf-8')}\n\n"
        return

    logger.info("Starting stream generation...")
    try:
        async for chunk in llm.astream(messages):
            if chunk.content:
                # format: "data: <json_string>\n\n"
                yield f"data: {orjson.dumps({'chk': chunk.content}).decode('utf-8')}\n\n"
                await asyncio.sleep(0.01)
    except Exception as e:
        error_message = f"Error during LLM streaming: {str(e)}"
        logger.error(error_message) 
        yield f"data: {orjson.dumps({'err': error_message}).decode('utf-8')}\n\n"
    finally:
        yield f"data: {orjson.dumps({'eofs': True}).decode('utf-8')}\n\n"
        logger.info("Stream generation finished.")

@router.post("/stream",
            summary="Process a chat message with streaming",
            status_code=status.HTTP_200_OK,
            response_model=None,
            responses={
                200: {
                    "description": "Streaming response of AI's reply.",
                    "content": {
                        "text/event-stream": {
                            "example": {
                                "chk": "Hello, how can I assist you today?",
                                "eofs": True,
                                "err": "Error message if any."
                            }                               
                        }
                    }
                },
                503: {
                    "description": "Service Unavailable",
                    "content": {
                        "application/json": {
                            "example": {"detail": "LLM model is not available due to initialization error."}
                        }
                    }
                }
            },
            description="Receives a user message and conversation history, streams the AI's reply chunk by chunk using Server-Sent Events (SSE).",)
async def chat_stream(request: MessageRequest):
    """
    Handles incoming chat requests and streams the response.
    """
    logger.info(f"Received message for /chat/stream: {request.message}") # Logging
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
        logger.info(f"   Added System Message: {request.systemInstructions}")
    else:
        logger.info("   No System Message provided.")
    
    for i, msg_content in enumerate(request.history):
        if i % 2 == 0: # Even index = User message (assuming history starts with user)
            messages.append(HumanMessage(content=msg_content))
            logger.info(f"   Added History (Human): {msg_content}")
        else: # Odd index = AI message
            messages.append(AIMessage(content=msg_content))
            logger.info(f"   Added History (AI): {msg_content}")
            
    messages.append(HumanMessage(content=request.message))
    logger.info(f"   Added Current User Message: {request.message}")        
    return StreamingResponse(
        _stream_generator(messages, llm.model),
        media_type="text/event-stream",
        headers={"Content-Type": "text/event-stream"}
    )