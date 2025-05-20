from uuid import UUID
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_async_session
from app.models.message_model import MessageModel, Content, MessageRole
from app.schemas.thread_schema import RequestCreateMessageSchema, UserMessage

class MessageCRUD:
    """
    CRUD operations for chat messages.
    This class provides methods to create, read, update, and delete chat messages.
    """

    def __init__(self, db: AsyncSession = Depends(get_async_session)):
        """
        Initializes the CRUD class with a database session.

        A new instance of MessageCRUD is created for each request,
        with the session provided by FastAPI's dependency injection.

        Args:
            db: The asynchronous database session.
        """
        self._db = db

    @property
    def session(self) -> AsyncSession:
        """Provides access to the database session."""
        return self._db
    
    async def create_user_message(self, thread_id: str, user_id: str, data: RequestCreateMessageSchema) -> UUID:
        """
        Creates a new user message in the database.

        Args:
            thread_id: The ID of the thread to which the message belongs.
            user_id: The ID of the user creating the message.
            data: The data for the new message.

        Returns:
            None
        """
        
        content = Content(
            role=data.content.role,
            metadata=data.content.metadata,
            status=data.content.status, 
            content=data.content.content,
        )
        
        new_message = MessageModel(
            thread_id=thread_id,
            content=content,
            format=data.format,
            height=0,
            parent_id=None,
            created_by=user_id,
            updated_by=user_id,
            message_id=None
        )
        self.session.add(new_message)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(new_message)
        return new_message.id
        
        
    
    
    
        