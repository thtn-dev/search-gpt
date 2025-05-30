"""
CRUD operations for chat messages.
This module provides functions to create, read, update, and delete chat messages.
"""
import logging
from typing import Optional
import uuid

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_async_session
from app.models.message_model import MessageModel, MessageRole
from app.models.thread_model import ThreadModel
from app.schemas.message_schema import MessageRequest
from sqlmodel import asc, desc, select

from app.schemas.thread_schema import ContentMetadata
from app.utils.datetime_utils import utc_now


logger = logging.getLogger(__name__)

class ChatCRUD:
    """
    CRUD operations for chat messages.
    This class provides methods to create, read, update, and delete chat messages.
    """

    def __init__(self, db: AsyncSession = Depends(get_async_session)):
        """
        Initializes the CRUD class with a database session.

        A new instance of UserCRUD is created for each request,
        with the session provided by FastAPI's dependency injection.

        Args:
            db: The asynchronous database session.
        """
        self._db = db

    @property
    def session(self) -> AsyncSession:
        """Provides access to the database session."""
        return self._db
    
    async def get_thread_by_id(self, thread_id: uuid.UUID) -> Optional[ThreadModel]:
        """Get a thread by ID."""
        if not thread_id:
            return None
        statement = select(ThreadModel).where(ThreadModel.id == thread_id) # Sửa: ThreadModel.id thay vì ThreadModel.thread_id
        result = await self.session.execute(statement)
        return result.scalars().first()
    
    async def create_thread(self, user_id: uuid.UUID | None, title: Optional[str] = "New Thread") -> ThreadModel:
        """Create new thread."""
        effective_title = title if title and title.strip() else "New Thread"

        thread = ThreadModel(
            title=effective_title,
            created_by=str(user_id) if user_id else None,
            is_archived=False,
            last_message_at=utc_now(),  # Set to None initially
        )
        self.session.add(thread)
        await self.session.flush() # use flush to get the ID before commit
        await self.session.refresh(thread)
        logger.info(f"Thread created with ID: {thread.id} for user_id: {user_id}")
        return thread

    async def save_message(
        self,
        content: str,
        thread_id: uuid.UUID,
        message_id: str,
        role: MessageRole,
        message_metadata: Optional[dict] = None,
    ) -> MessageModel:
        """Save a message (Human or AI) to the database."""
        if not thread_id:
            logger.error("Attempted to save message with no thread_id.")
            raise ValueError("thread_id is required to save a message.")

        message = MessageModel(
            content=content,
            thread_id=thread_id,
            message_id=message_id,
            role=role,
            format="text",  
            msg_metadata=ContentMetadata(custom=dict())
        )
        self.session.add(message)
        await self.session.flush() 
        await self.session.refresh(message)
        logger.info(f"Message saved: ID {message.id}, message_id {message_id}, role {role.value}, thread_id {thread_id}")
        return message
    
    async def save_assistant_message(
        self,
        content: str,
        thread_id: str, # Nhận thread_id dạng string từ background task
        ai_message_id: str,
    ) -> MessageModel:
        """
        Lưu tin nhắn của trợ lý (AI). 
        Hàm này sẽ commit và đóng session vì nó được chạy trong background task.
        """
        assistant_message_obj: Optional[MessageModel] = None
        try:
            uuid_thread_id = uuid.UUID(thread_id)
            
            # Thực hiện các thao tác cơ sở dữ liệu
            # save_message thêm vào session, flush và refresh, nhưng không commit
            assistant_message_obj = await self.save_message(
                content=content,
                thread_id=uuid_thread_id,
                message_id=ai_message_id,
                role=MessageRole.ASSISTANT,
            )
            
            await self.session.commit() # Commit transaction
            await self.session.refresh(assistant_message_obj) # Lấy trạng thái mới nhất sau commit
            logger.info(f"Assistant message {assistant_message_obj.id} (message_id: {ai_message_id}) committed for thread_id: {thread_id}")
            
        except Exception as e:
            logger.exception(f"Error during DB operations or commit for assistant message (thread_id {thread_id}, ai_message_id {ai_message_id}): {e}")
            # Chỉ rollback nếu session đang trong một transaction và còn active
            if self.session.is_active:
                try:
                    await self.session.rollback()
                    logger.info(f"Session rolled back for assistant message due to error (thread_id {thread_id})")
                except Exception as rb_exc:
                    logger.exception(f"Error during rollback for assistant message (thread_id {thread_id}): {rb_exc}")
            raise # Ném lại lỗi ban đầu để background task handler có thể xử lý
        finally:
            # Đảm bảo session được đóng vì đây là background task
            # và có thể không được quản lý bởi vòng đời session request-response thông thường của FastAPI.
            if self.session: # Kiểm tra xem session có tồn tại không
                try:
                    await self.session.close()
                    logger.info(f"Session closed for assistant message task (thread_id {thread_id}, ai_message_id {ai_message_id})")
                except Exception as close_exc:
                    # Ghi log lỗi khi đóng session, nhưng không để nó che mất lỗi gốc (nếu có)
                    logger.exception(f"Error closing session for assistant message task (thread_id {thread_id}): {close_exc}")
        
        if assistant_message_obj is None:
            # Trường hợp này không nên xảy ra nếu một exception đã được ném và xử lý ở tầng cao hơn.
            # Nếu không có exception nhưng object là None, đó là một điều bất thường.
            logger.error(f"assistant_message_obj is None after try-finally block for thread_id {thread_id} (ai_message_id: {ai_message_id}). This is unexpected if no error was re-raised.")
            raise Exception(f"Failed to save assistant message for thread_id {thread_id} due to an internal issue.")
            
        return assistant_message_obj
        
    async def save_human_message_and_ensure_thread(
        self,
        request_message: MessageRequest,
        user_id: uuid.UUID | None,
        human_message_id: str,
    ) -> MessageModel:
        """
        Save user messages.
        If Request_Message.thread_ID is provided and valid, using that thread.
        If not, create a new thread.
        Returns the message saved.
        """
        thread: Optional[ThreadModel] = None
        final_thread_id: Optional[uuid.UUID] = None

        if request_message.thread_id:
            try:
                parsed_thread_id = uuid.UUID(request_message.thread_id)
                thread = await self.get_thread_by_id(parsed_thread_id)
                if thread:
                    # Kiểm tra xem thread có thuộc về user_id không (nếu cần)
                    # if thread.user_id != user_id:
                    #     logger.warning(f"User {user_id} attempted to use thread {thread.id} owned by user {thread.user_id}")
                    #     thread = None # Coi như không tìm thấy thread hợp lệ
                    # else:
                    final_thread_id = thread.id
                    logger.info(f"Using existing thread: {final_thread_id} for user_id: {user_id}")
                else:
                    logger.warning(f"Thread ID {request_message.thread_id} provided but not found. A new thread will be created.")
            except ValueError:
                logger.warning(f"Invalid thread_id format: {request_message.thread_id}. A new thread will be created.")


        if not thread: # Nếu không có thread_id hợp lệ hoặc thread không tìm thấy
            # Tạo title cho thread mới từ message đầu tiên (nếu có)
            # Hoặc để title mặc định
            new_thread_title = request_message.message[:50] + "..." if request_message.message else "New Thread"

            thread = await self.create_thread(user_id=user_id, title=new_thread_title)
            final_thread_id = thread.id
            logger.info(f"New thread created with ID: {final_thread_id} for user_id: {user_id}")


        if not final_thread_id:
            logger.error("Failed to obtain a valid thread_id for saving human message.")
            raise Exception("Internal server error: Could not determine thread for message.")


        human_message = await self.save_message(
            content=request_message.message,
            thread_id=final_thread_id,
            message_id=human_message_id,
            role=MessageRole.USER,
            message_metadata=None
        )

        await self.session.commit()
        logger.info(f"Human message {human_message.id} and thread operations committed for thread_id: {final_thread_id}")
        
        
        await self.session.refresh(human_message)
        if thread and thread in self.session: 
             await self.session.refresh(thread)

        return human_message

    async def get_messages_by_thread_id(
        self, thread_id: uuid.UUID, limit: int = 100, offset: int = 0
    ) -> list[MessageModel]:
        """Lấy danh sách tin nhắn cho một thread_id cụ thể, sắp xếp theo thời gian tạo."""
        statement = (
            select(MessageModel)
            .where(MessageModel.thread_id == thread_id)
            .order_by(asc(MessageModel.created_at))  
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_threads_for_user(
        self, user_id: int, limit: int = 50, offset: int = 0
    ) -> list[ThreadModel]:
        """Lấy danh sách các threads cho một user_id, sắp xếp theo thời gian tạo gần nhất."""
        statement = (
            select(ThreadModel)
            .where(ThreadModel.created_by == user_id)
            .order_by(desc(ThreadModel.created_at))
            .offset(offset)
            .limit(limit)
            # .options(selectinload(ThreadModel.messages)) # Ví dụ nếu muốn load cả messages (cẩn thận N+1)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())
        
        
    
        
        
        
        