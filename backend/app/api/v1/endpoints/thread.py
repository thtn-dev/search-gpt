from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union
import uuid
from app.crud.message_crud import MessageCRUD
from fastapi import APIRouter, Body, Depends, Response, status
from pydantic import BaseModel, Field, field_validator

from app.crud.thread_crud import ThreadCRUD
from app.schemas.thread_schema import CreateThreadRequestSchema, CreateThreadResponseSchema, RequestCreateMessageSchema, ResponseCreateMessageSchema, ThreadSchema, ThreadsResponse


router = APIRouter()

@router.get("/threads" )
async def get_threads():
    """
    Get all threads.
    """
    return ThreadsResponse(threads=[])


@router.post("/threads")
async def create_thread(
    request: CreateThreadRequestSchema = Body(...),
    thread_crud: ThreadCRUD = Depends(ThreadCRUD)
):
    """
    Get all threads.
    """
    thread_id = await thread_crud.create_thread(str(uuid.uuid4()), str(uuid.uuid4()), request.last_message_at)
    return CreateThreadResponseSchema(thread_id= str(thread_id))

@router.post("/threads/{thread_id}/messages", response_model=ResponseCreateMessageSchema)
async def create_message(
    thread_id: str,
    request: RequestCreateMessageSchema = Body(...),
    message_crud: MessageCRUD = Depends(MessageCRUD),
) -> ResponseCreateMessageSchema:
    """
    Tạo một tin nhắn mới trong một chủ đề cụ thể.
    """
    # Xử lý logic tạo tin nhắn ở đây
    # ...
    print(request)
    message_id = await message_crud.create_user_message(
        thread_id=thread_id,
        user_id=str(uuid.uuid4()),
        data=request,
    )
    # Trả về phản hồi
    return ResponseCreateMessageSchema(message_id=str(message_id))




@router.post("/runs/stream")
async def generate_thread_title(
    thread: ThreadSchema,
):
    """
    Tạo tiêu đề cho một luồng hội thoại.
    """
    # Xử lý logic tạo tiêu đề ở đây
    # ...
    
    text_content = "User Inquiry About Tokyo Weather" + uuid.uuid4().hex
    # Trả về phản hồi
    binary_data: bytes = text_content.encode('utf-8')
    return Response(content=binary_data, media_type="application/octet-stream")
