"""
User CRUD operations module.

This module provides CRUD (Create, Read, Update, Delete) functionalities
for user and linked account management within the application.
It handles interactions with the database for user-related data.
"""

import logging
import uuid
from typing import Optional  # Removed Any, Dict as they were unused

from fastapi import Depends
from pydantic import EmailStr  # Part of Pydantic, typically considered third-party
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.database.session import get_async_session
from app.models.user_model import LinkedAccountModel, UserModel
from app.schemas.auth_schemas import AuthProvider, VerifiedUserData

logger = logging.getLogger(__name__)


class UserCRUD:
    """
    CRUD class for User model.
    The database session is injected into the constructor.
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

    async def get_user_by_provider_key(
        self, provider: AuthProvider, provider_key: str
    ) -> Optional[UserModel]:
        """
        Finds a user based on the linked account's provider and provider_key.
        Returns the UserModel if found, otherwise None.
        Loads the user with their linked accounts eagerly.
        """
        statement = (
            select(LinkedAccountModel)
            .where(LinkedAccountModel.provider == provider.value)
            .where(LinkedAccountModel.provider_key == provider_key)
            .options(
                selectinload(LinkedAccountModel.user).selectinload(
                    UserModel.linked_accounts
                )
            )
        )
        results = await self.session.execute(statement)
        linked_account = results.scalars().first()
        if linked_account and linked_account.user:
            logger.info(
                'Found LinkedAccount and User via provider_id. User ID: %s',
                linked_account.user.id,
            )
            return linked_account.user
        return None

    async def get_user_by_email(self, email: EmailStr) -> Optional[UserModel]:
        """
        Finds a user by their email address.
        Returns the UserModel if found, otherwise None.
        Loads the user with their linked accounts eagerly.
        """
        statement = (
            select(UserModel)
            .where(UserModel.email == email)
            .options(selectinload(UserModel.linked_accounts))
        )
        results = await self.session.execute(statement)
        return results.scalars().first()

    async def link_provider_to_user(
        self, user: UserModel, provider: AuthProvider, provider_key: str
    ) -> LinkedAccountModel:
        """
        Creates and links a new provider account to an existing user.
        Handles potential race conditions during commit.
        """
        logger.info(
            "Attempting to link provider '%s' (key: %s) to User ID: %s",
            provider.value,
            provider_key,
            user.id,
        )

        has_link = any(
            la.provider == provider.value and la.provider_key == provider_key
            for la in user.linked_accounts
        )
        if has_link:
            logger.info(
                "Link for provider '%s' already exists for User ID: %s in memory.",
                provider.value,
                user.id,
            )
            existing_link = next(
                (
                    la
                    for la in user.linked_accounts
                    if la.provider == provider.value and la.provider_key == provider_key
                ),
                None,
            )
            return existing_link  # type: ignore # Assuming existing_link will be found if has_link is True
        if user.id is None:
            logger.error(
                "Cannot link provider '%s' to User ID: %s because user ID is None.",
                provider.value,
                user.id,
            )
            raise ValueError('User ID cannot be None when linking a provider.')

        new_linked_account = LinkedAccountModel(
            provider=provider.value, provider_key=provider_key, user_id=user.id
        )
        self.session.add(new_linked_account)

        try:
            await self.session.flush()
            logger.info(
                "Successfully added LinkedAccount for provider '%s' to session for User ID: %s",
                provider.value,
                user.id,
            )
            user.linked_accounts.append(new_linked_account)
            return new_linked_account
        except IntegrityError as e:
            await self.session.rollback()
            logger.warning(
                'IntegrityError while linking account for User ID %s, provider %s: %s. Assuming link exists.',
                user.id,
                provider.value,
                e,
            )
            refreshed_user = await self.get_user_by_email(
                user.email
            )  # Or get user by ID
            if refreshed_user:
                existing_link = next(
                    (
                        la
                        for la in refreshed_user.linked_accounts
                        if la.provider == provider.value
                        and la.provider_key == provider_key
                    ),
                    None,
                )
                if existing_link:
                    logger.info(
                        "Confirmed existing link for provider '%s' after rollback for User ID: %s",
                        provider.value,
                        user.id,
                    )
                    return existing_link
                # Case: rollback but link still not found?
                logger.error(
                    "Could not find link for provider '%s' after rollback for User ID: %s. Raising original error.",
                    provider.value,
                    user.id,
                )
                raise e  # Raise original IntegrityError
            # Case: user not found after rollback
            logger.error(
                'User ID %s not found after rollback during linking. Raising original error.',
                user.id,
            )
            raise e  # Raise original IntegrityError
        except Exception as e:
            await self.session.rollback()
            logger.error(
                'Unexpected error linking account for User ID %s, provider %s: %s',
                user.id,
                provider.value,
                e,
            )
            raise

    async def create_new_oauth_user(self, user_info: VerifiedUserData) -> UserModel:
        """
        Creates a new user and links the initial provider account.
        Handles potential race conditions during commit.
        """
        logger.info(
            "Attempting to create new user for provider '%s', email=%s",
            user_info.provider.value,
            user_info.email,
        )

        if not user_info.email:
            logger.error('Cannot create user without an email address.')
            raise ValueError('Email is required to create a new user.')

        base_username = user_info.email.split('@')[0].lower()
        max_base_len = 50 - 7
        username = f'{base_username[:max_base_len]}_{uuid.uuid4().hex[:6]}'
        logger.info('Generated username: %s', username)

        # picture_url was unused, so removed its assignment
        # picture_url = str(user_info.picture) if user_info.picture else None

        new_user = UserModel(
            email=user_info.email,
            username=username,
            hashed_password=None,
            is_active=True,
        )

        self.session.add(new_user)
        await self.session.flush()

        if not new_user.id:
            logger.error('Failed to create new user, user ID is None.')
            raise ValueError('Failed to create new user, user ID is None.')

        new_linked_account = LinkedAccountModel(
            user_id=new_user.id,
            provider=user_info.provider.value,
            provider_key=str(user_info.provider_key),
        )

        self.session.add(new_linked_account)

        try:
            await self.session.flush()
            logger.info(
                'Successfully added new User (email: %s) and LinkedAccount to session.',
                new_user.email,
            )
            return new_user
        except IntegrityError as e:
            await self.session.rollback()
            logger.warning(
                'IntegrityError while creating new user (email: %s): %s. Retrying find.',
                user_info.email,
                e,
            )
            existing_user = await self.get_user_by_provider_key(
                user_info.provider, str(user_info.provider_key)
            )  # Changed provider_id to provider_key
            if existing_user:
                logger.info(
                    'Found existing user by provider key after rollback: %s',
                    existing_user.id,
                )
                return existing_user
            existing_user = await self.get_user_by_email(user_info.email)
            if existing_user:
                logger.info(
                    'Found existing user by email after rollback: %s. Attempting to link.',
                    existing_user.id,
                )
                await self.link_provider_to_user(
                    existing_user, user_info.provider, str(user_info.provider_key)
                )  # Changed provider_id to provider_key
                # Ensure the user object returned has the latest linked accounts
                refreshed_user = await self.get_user_by_email(user_info.email)
                if (
                    refreshed_user
                ):  # Check if user still exists after potential operations
                    return refreshed_user
                logger.error(
                    'User %s disappeared after attempting to link provider %s post-IntegrityError.',
                    user_info.email,
                    user_info.provider.value,
                )
                # Fall through to raise original error if user cannot be re-fetched
            logger.error(
                'Could not find user by provider key or email after rollback during creation. Raising original error.'
            )
            raise e
        except Exception as e:
            await self.session.rollback()
            logger.error(
                'Unexpected error creating new user (email: %s): %s', user_info.email, e
            )
            raise

    async def get_or_create_oauth_user(self, user_info: VerifiedUserData) -> UserModel:
        """
        Gets a user based on OAuth provider info or creates a new one.

        Prioritizes finding by provider_key, then by email (linking if found),
        and finally creates a new user if none exist.
        Handles potential race conditions. The final commit should happen
        in the calling endpoint.

        Args:
            user_info: Standardized user data from the verified provider token.

        Returns:
            The existing or newly created UserModel instance.

        Raises:
            ValueError: If user_info lacks necessary data (provider_key, email).
        """
        provider = user_info.provider
        provider_key = str(user_info.provider_key)
        email = user_info.email

        if not provider_key:
            logger.error("VerifiedUserData is missing 'provider_key'.")
            raise ValueError('OAuth information incomplete (missing provider_key).')
        if not email:
            logger.error("VerifiedUserData is missing 'email'.")
            raise ValueError('OAuth information incomplete (missing email).')

        logger.info(
            'Starting get_or_create for provider=%s, email=%s, provider_key=%s',
            provider.value,
            email,
            provider_key,
        )

        db_user = await self.get_user_by_provider_key(provider, provider_key)
        if db_user:
            logger.info('Found existing User ID %s via provider key.', db_user.id)
            return db_user

        logger.info('User not found by provider key, searching by email...')
        db_user_by_email = await self.get_user_by_email(
            email
        )  # email is already checked for not None
        if db_user_by_email:
            logger.info(
                "Found existing User ID %s by email. Linking provider '%s'...",
                db_user_by_email.id,
                provider.value,
            )
            await self.link_provider_to_user(db_user_by_email, provider, provider_key)
            # Return the user with potentially new link.
            # The link_provider_to_user method adds to session and appends to user.linked_accounts in memory.
            return db_user_by_email

        logger.info('User not found by provider key or email. Creating new user...')
        # Email is guaranteed to exist here due to earlier check if we reach this point without db_user_by_email
        new_user = await self.create_new_oauth_user(user_info)
        return new_user
