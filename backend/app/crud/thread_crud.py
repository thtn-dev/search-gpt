from datetime import datetime
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_async_session
from app.models.thread_model import ThreadModel

class ThreadCRUD:
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
    
    async def create_thread(self, user_id: str, workspace_id: str, last_message_at: datetime) -> dict:
        """
        Creates a new thread in the database.

        Args:
            user_id: The ID of the user creating the thread.
            thread_data: The data for the new thread.

        Returns:
            The created thread.
        """
        
        new_thread = ThreadModel(
            title=None,
            created_by=user_id,
            workspace_id=workspace_id,
            last_message_at=last_message_at,
            is_archived=False,
            external_id=None,
            thread_metadata=None,
        )
        self.session.add(new_thread)
        await self.session.commit()
        await self.session.refresh(new_thread)
        return new_thread
    
        