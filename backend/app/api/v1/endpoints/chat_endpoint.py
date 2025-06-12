import asyncio
import logging
import uuid
from typing import AsyncGenerator, Callable, List, Optional, Union

import orjson
from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.chat_crud import ChatCRUD
from app.database.session import get_async_ctx_session
from app.library.providers.gemini import load_gemini_chat_models
from app.library.providers.openai import load_openai_chat_models
from app.models.message_model import MessageRole
from app.schemas.message_schema import (
    MessageCreateRequest,
    MessageRequest,
    gen_message_id,
)
from app.schemas.thread_schema import CreateThreadRequest
from app.schemas.user_schema import UserLoggedIn
from app.services.auth_service import get_current_user, get_optional_current_user
from app.utils.uuid_utils import is_valid_uuid

logger = logging.getLogger(__name__)
router = APIRouter()

LLM_UNAVAILABLE_ERROR = 'LLM service is unavailable.'
LLM_STREAM_ERROR_MESSAGE = 'Error during LLM streaming'
EMPTY_RESPONSE_INFO = 'AI returned an empty response.'
DEFAULT_USER_ID = None


class MessageStreamMetadata(BaseModel):
    thread_id: str
    ai_message_id: str


async def _generate_llm_stream_and_log(
    thread_id: str,
    messages_for_llm: List[Union[HumanMessage, AIMessage, SystemMessage]],
    llm: BaseChatModel,
    background_tasks: BackgroundTasks,
    ai_message_id: str,
) -> AsyncGenerator[str, None]:
    """
    Async generator tạo ra một luồng tin nhắn từ LLM và ghi lại phản hồi.
    Yields các chunk của phản hồi từ AI dưới dạng chuỗi JSON được định dạng cho Server-Sent Events (SSE).
    """
    full_ai_response_chunks: List[str] = []
    error_occurred = False
    any_content_streamed = False

    if llm is None:
        logger.error(f'LLM is None for thread_id: {thread_id}. Cannot stream.')
        yield f'data: {orjson.dumps({"err": LLM_UNAVAILABLE_ERROR}).decode("utf-8")}\n\n'
        return

    logger.info(
        f'Starting LLM stream generation for thread_id: {thread_id}, ai_message_id: {ai_message_id}'
    )
    try:
        metadata = MessageStreamMetadata(
            thread_id=thread_id, ai_message_id=ai_message_id
        )
        yield f'data: {orjson.dumps({"metadata": metadata}).decode("utf-8")}\n\n'
        async for chunk in llm.astream(messages_for_llm):
            if chunk.content:
                any_content_streamed = True
                content_str = str(chunk.content)
                full_ai_response_chunks.append(content_str)
                yield f'data: {orjson.dumps({"chk": content_str}).decode("utf-8")}\n\n'
                await asyncio.sleep(0.005)
    except Exception as e:
        error_message = f'{LLM_STREAM_ERROR_MESSAGE}: {e}'
        logger.exception(error_message)
        error_occurred = True
        yield f'data: {orjson.dumps({"err": error_message}).decode("utf-8")}\n\n'
    finally:
        if not any_content_streamed and not error_occurred:
            logger.warning(
                f'LLM stream finished without yielding any content for thread_id: {thread_id}. '
                f'This might be an empty response from the LLM.'
            )
            yield f'data: {orjson.dumps({"info": EMPTY_RESPONSE_INFO}).decode("utf-8")}\n\n'

        final_ai_response = ''.join(full_ai_response_chunks)

        if final_ai_response:
            background_tasks.add_task(
                _save_ai_message_in_background,
                content=final_ai_response,
                thread_id_str=thread_id,
                ai_message_id=ai_message_id,
                session_factory=get_async_ctx_session,  # type: ignore
            )
            logger.info(
                f'AI response for thread_id {thread_id} queued for saving. Length: {len(final_ai_response)}'
            )
        elif not error_occurred:
            logger.warning(f'No final AI response to save for thread_id: {thread_id}.')

        yield f'data: {orjson.dumps({"eofs": True}).decode("utf-8")}\n\n'
        logger.info(f'LLM stream generation finished for thread_id: {thread_id}')


async def _save_ai_message_in_background(
    content: str,
    thread_id_str: str,
    ai_message_id: str,
    session_factory: Callable[[], AsyncSession],
):
    """
    Hàm chạy trong background để lưu tin nhắn AI.
    Hàm này tạo và quản lý session DB của riêng nó.
    """
    logger.info(
        f'Background task started: Saving AI message for thread {thread_id_str}, message_id {ai_message_id}'
    )
    async with session_factory() as new_db_session:
        crud_for_bg = ChatCRUD(db=new_db_session)
        try:
            await crud_for_bg.save_assistant_message(
                content=content,
                thread_id=thread_id_str,
                ai_message_id=ai_message_id,
            )
            logger.info(
                f'Background task: AI message successfully saved for thread {thread_id_str}, message_id {ai_message_id}.'
            )
        except Exception as e:
            logger.error(
                f'Background task: Failed to save AI message for thread {thread_id_str}, message_id {ai_message_id}. Error: {e}',
                exc_info=True,
            )
            if new_db_session.is_active:
                await new_db_session.rollback()
    logger.info(
        f'Background task finished: Saving AI message for thread {thread_id_str}, message_id {ai_message_id}'
    )


def _prepare_langchain_messages(
    request: MessageRequest,
) -> List[Union[HumanMessage, AIMessage, SystemMessage]]:
    """Chuẩn bị danh sách tin nhắn cho Langchain từ request."""
    messages: List[Union[HumanMessage, AIMessage, SystemMessage]] = []
    if request.system_instructions:
        messages.append(SystemMessage(content=request.system_instructions))
        logger.debug(f'Added System Message: {request.system_instructions[:100]}...')
    else:
        logger.debug('No System Message provided.')

    for role, hist_content in request.history:
        if role == MessageRole.USER:
            messages.append(HumanMessage(content=hist_content))
            logger.debug(f'Added History (Human): {hist_content[:100]}...')
        elif role == MessageRole.ASSISTANT:
            messages.append(AIMessage(content=hist_content))
            logger.debug(f'Added History (AI): {hist_content[:100]}...')
        else:
            logger.warning(f'Unknown role in history: {role}')

    messages.append(HumanMessage(content=request.message.content))
    logger.debug(f'Added Current User Message: {request.message.content[:100]}...')
    return messages


async def _generate_llm_stream(
    thread_id: str,
    messages_for_llm: List[Union[HumanMessage, AIMessage, SystemMessage]],
    llm: BaseChatModel,
) -> AsyncGenerator[str, None]:
    """
    Async generator tạo ra một luồng tin nhắn từ LLM và ghi lại phản hồi.
    Yields các chunk của phản hồi từ AI dưới dạng chuỗi JSON được định dạng cho Server-Sent Events (SSE).
    """
    full_ai_response_chunks: List[str] = []
    error_occurred = False
    any_content_streamed = False

    if llm is None:
        logger.error(f'LLM is None for thread_id: {thread_id}. Cannot stream.')
        yield f'data: {orjson.dumps({"err": LLM_UNAVAILABLE_ERROR}).decode("utf-8")}\n\n'
        return
    try:
        async for chunk in llm.astream(messages_for_llm):
            if chunk.content:
                any_content_streamed = True
                content_str = str(chunk.content)
                full_ai_response_chunks.append(content_str)
                yield f'data: {orjson.dumps({"chk": content_str}).decode("utf-8")}\n\n'
                await asyncio.sleep(0.005)
    except Exception as e:
        error_message = f'{LLM_STREAM_ERROR_MESSAGE}: {e}'
        logger.exception(error_message)
        error_occurred = True
        yield f'data: {orjson.dumps({"err": error_message}).decode("utf-8")}\n\n'
    finally:
        if not any_content_streamed and not error_occurred:
            logger.warning(
                f'LLM stream finished without yielding any content for thread_id: {thread_id}. '
                f'This might be an empty response from the LLM.'
            )
            yield f'data: {orjson.dumps({"info": EMPTY_RESPONSE_INFO}).decode("utf-8")}\n\n'
        yield f'data: {orjson.dumps({"eofs": True}).decode("utf-8")}\n\n'
        logger.info(f'LLM stream generation finished for thread_id: {thread_id}')


@router.post(
    '/stream',
    summary='Xử lý tin nhắn chat với streaming',
    status_code=status.HTTP_200_OK,
    response_model=None,
    responses={
        status.HTTP_200_OK: {
            'description': 'Luồng phản hồi từ AI.',
            'content': {
                'text/event-stream': {
                    'example': {
                        'chk': 'Xin chào, tôi có thể giúp gì cho bạn?',
                        'eofs': True,
                        'err': 'Thông báo lỗi nếu có.',
                        'info': 'Thông tin bổ sung, ví dụ: AI trả về phản hồi rỗng.',
                    }
                }
            },
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            'description': 'Dịch vụ không khả dụng',
            'content': {
                'application/json': {
                    'example': {'detail': 'Mô hình LLM không khả dụng do lỗi khởi tạo.'}
                }
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {  # Thêm mô tả cho lỗi 500
            'description': 'Lỗi máy chủ nội bộ',
            'content': {
                'application/json': {
                    'example': {'detail': 'Không thể xử lý lưu tin nhắn.'}
                }
            },
        },
    },
    description=(
        'Nhận tin nhắn của người dùng và lịch sử cuộc trò chuyện, '
        'truyền phát phản hồi của AI từng đoạn bằng Server-Sent Events (SSE).'
    ),
)
async def chat_stream_endpoint(
    background_tasks: BackgroundTasks,
    request: MessageRequest = Body(...),
    crud_for_request: ChatCRUD = Depends(ChatCRUD),
    current_user: Optional[UserLoggedIn] = Depends(get_optional_current_user),
):
    """
    Xử lý các yêu cầu chat đến và truyền phát phản hồi.
    """
    logger.info(
        f'Received message for /chat/stream. Message: {request.message.content[:100]}...'
    )
    user_id = current_user.id if current_user else DEFAULT_USER_ID

    models = load_gemini_chat_models()
    llm_object = models.get('gemini-2.0-flash')  # Đổi tên biến để tránh nhầm lẫn

    if (
        not llm_object
        or not hasattr(llm_object, 'model')
        or not isinstance(llm_object.model, BaseChatModel)
    ):
        logger.error(
            "LLM model ('gemini-2.0-flash') is not available or not a BaseChatModel instance."
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Mô hình LLM không khả dụng do lỗi khởi tạo hoặc cấu hình.',
        )

    actual_llm_model = llm_object.model  # Lấy model thực sự để truyền đi

    langchain_messages = _prepare_langchain_messages(request)

    human_message_id = None
    if request.message.message_id:
        human_message_id = request.message.message_id
    else:
        human_message_id = gen_message_id()

    ai_message_id = gen_message_id()

    try:
        # crud_for_request sử dụng session từ request, được quản lý bởi FastAPI
        saved_human_message = (
            await crud_for_request.save_human_message_and_ensure_thread(
                request_message=request,
                user_id=user_id,  # Đảm bảo DEFAULT_USER_ID có giá trị hợp lệ
                human_message_id=human_message_id,
            )
        )
        thread_id = str(saved_human_message.thread_id)
        logger.info(
            f'Human message saved for thread_id: {thread_id}, message_id: {human_message_id}'
        )
    except ValueError as ve:  # Bắt lỗi cụ thể hơn nếu có thể
        logger.exception(
            f'Validation error saving human message or ensuring thread: {ve}'
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Invalid data for message saving: {ve}',
        ) from ve
    except Exception as e:
        logger.exception(f'Failed to save human message or ensure thread: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Could not process message saving.',
        ) from e

    return StreamingResponse(
        _generate_llm_stream_and_log(
            thread_id=thread_id,
            messages_for_llm=langchain_messages,
            llm=actual_llm_model,
            background_tasks=background_tasks,
            ai_message_id=ai_message_id,
        ),
        media_type='text/event-stream',
        headers={'Content-Type': 'text/event-stream'},
    )


@router.post(
    '/stream2',
    summary='Xử lý tin nhắn chat với streaming',
    status_code=status.HTTP_200_OK,
    response_model=None,
    responses={
        status.HTTP_200_OK: {
            'description': 'Luồng phản hồi từ AI.',
            'content': {
                'text/event-stream': {
                    'example': {
                        'chk': 'Xin chào, tôi có thể giúp gì cho bạn?',
                        'eofs': True,
                        'err': 'Thông báo lỗi nếu có.',
                        'info': 'Thông tin bổ sung, ví dụ: AI trả về phản hồi rỗng.',
                    }
                }
            },
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            'description': 'Dịch vụ không khả dụng',
            'content': {
                'application/json': {
                    'example': {'detail': 'Mô hình LLM không khả dụng do lỗi khởi tạo.'}
                }
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {  # Thêm mô tả cho lỗi 500
            'description': 'Lỗi máy chủ nội bộ',
            'content': {
                'application/json': {
                    'example': {'detail': 'Không thể xử lý lưu tin nhắn.'}
                }
            },
        },
    },
    description=(
        'Nhận tin nhắn của người dùng và lịch sử cuộc trò chuyện, '
        'truyền phát phản hồi của AI từng đoạn bằng Server-Sent Events (SSE).'
    ),
)
async def chat_stream_endpoint2(
    request: MessageRequest = Body(...),
    current_user: Optional[UserLoggedIn] = Depends(get_optional_current_user),
):
    """
    Xử lý các yêu cầu chat đến và truyền phát phản hồi.
    """
    logger.info(
        f'Received message for /chat/stream. Message: {request.message.content[:100]}...'
    )
    user_id = current_user.id if current_user else DEFAULT_USER_ID

    models = load_openai_chat_models()
    llm_object = models.get('gpt-4o-mini')  # Đổi tên biến để tránh nhầm lẫn

    if (
        not llm_object
        or not hasattr(llm_object, 'model')
        or not isinstance(llm_object.model, BaseChatModel)
    ):
        logger.error(
            "LLM model ('gemini-2.0-flash') is not available or not a BaseChatModel instance."
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Mô hình LLM không khả dụng do lỗi khởi tạo hoặc cấu hình.',
        )

    actual_llm_model = llm_object.model

    langchain_messages = _prepare_langchain_messages(request)

    return StreamingResponse(
        _generate_llm_stream(
            thread_id=request.message.thread_id or gen_message_id(),  # hehe
            messages_for_llm=langchain_messages,
            llm=actual_llm_model,
        ),
        media_type='text/event-stream',
        headers={'Content-Type': 'text/event-stream'},
    )


@router.get('/threads', status_code=status.HTTP_200_OK)
async def get_threads_endpoint(
    crud: ChatCRUD = Depends(ChatCRUD),
    current_user: UserLoggedIn = Depends(get_current_user),
):
    """
    Lấy danh sách tất cả các thread.
    """
    try:
        threads = await crud.get_threads_for_user(current_user.id)
        return threads
    except Exception as e:
        logger.error(f'Error retrieving threads: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Could not retrieve threads.',
        ) from e


@router.post('/threads', status_code=status.HTTP_201_CREATED)
async def create_thread_endpoint(
    crud: ChatCRUD = Depends(ChatCRUD),
    current_user: UserLoggedIn = Depends(get_current_user),
    request: CreateThreadRequest = Body(),
):
    """
    Tạo một thread mới cho người dùng hiện tại.
    """
    try:
        new_thread = await crud.create_thread(
            user_id=current_user.id,
            title=request.title,
        )
        await crud.session.commit()
        return {'thread_id': str(new_thread.id)}
    except Exception as e:
        logger.error(f'Error creating thread for user {current_user.id}: {e}')
        await crud.session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Could not create thread.',
        ) from e


@router.post('/threads/{thread_id}/messages', status_code=status.HTTP_201_CREATED)
async def add_message_to_thread_endpoint(
    request: MessageCreateRequest = Body(...),
    crud: ChatCRUD = Depends(ChatCRUD),
    current_user: UserLoggedIn = Depends(get_current_user),
):
    """
    Thêm một tin nhắn vào một thread cụ thể.
    """
    try:
        thread_id = request.thread_id
        thread_uuid_valid = is_valid_uuid(thread_id)

        if not thread_uuid_valid:
            logger.error(f'Invalid thread_id format: {thread_id}')
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Invalid thread ID format.',
            )

        thread_uuid = uuid.UUID(request.thread_id)
        saved_human_message = await crud.save_message_and_commit(
            content=request.content,
            thread_id=thread_uuid,
            message_id=request.message_id or gen_message_id(),
            role=request.role,
        )
        return {'message_id': str(saved_human_message.message_id)}
    except ValueError as ve:
        logger.exception(f'Validation error saving message in thread {thread_id}: {ve}')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Invalid data for message saving: {ve}',
        ) from ve
    except Exception as e:
        logger.error(f'Error adding message to thread {thread_id}: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Could not add message to thread.',
        ) from e


@router.get('/threads/{thread_id}', status_code=status.HTTP_200_OK)
async def get_thread_endpoint(
    thread_id: str,
    crud: ChatCRUD = Depends(ChatCRUD),
    current_user: UserLoggedIn = Depends(get_current_user),
):
    """
    Lấy thông tin của một thread cụ thể.
    """
    try:
        thread_uuid_valid = is_valid_uuid(thread_id)

        if not thread_uuid_valid:
            logger.error(f'Invalid thread_id format: {thread_id}')
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Invalid thread ID format.',
            )

        thread_uuid = uuid.UUID(thread_id)

        thread = await crud.get_thread_by_id(thread_id=thread_uuid)
        if not thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Thread not found.',
            )
        return thread
    except Exception as e:
        logger.error(f'Error retrieving thread {thread_id}: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Could not retrieve thread.',
        ) from e


@router.get('/threads/{thread_id}/messages', status_code=status.HTTP_200_OK)
async def get_thread_messages_endpoint(
    thread_id: str,
    crud: ChatCRUD = Depends(ChatCRUD),
    current_user: UserLoggedIn = Depends(get_current_user),
):
    """
    Lấy tất cả tin nhắn trong một thread cụ thể.
    """
    try:
        thread_uuid_valid = is_valid_uuid(thread_id)

        if not thread_uuid_valid:
            logger.error(f'Invalid thread_id format: {thread_id}')
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Invalid thread ID format.',
            )

        thread_uuid = uuid.UUID(thread_id)

        messages = await crud.get_messages_by_thread_id(
            thread_id=thread_uuid,
        )
        return messages
    except Exception as e:
        logger.error(f'Error retrieving messages for thread {thread_id}: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Could not retrieve messages.',
        ) from e
