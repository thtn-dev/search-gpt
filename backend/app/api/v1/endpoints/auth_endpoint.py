"""Authentication and user registration endpoints."""
from datetime import datetime, timedelta
import logging
import uuid

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.crud.user_crud import UserCRUD
from app.database.session import get_async_session
from app.models.user_model import UserModel
from app.schemas.auth_schemas import NextAuthSigninPayload
from app.schemas.user_schema import (
    UserBase,
    UserCreate,
    UserLogin,
    UserLoginResponse,
)
from app.utils.auth_utils import verify_identity_from_nextauth

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", response_model=UserBase, status_code=status.HTTP_201_CREATED)
async def register(
    *,
    session: AsyncSession = Depends(get_async_session),
    register_dto: UserCreate
):
    """
    Create a new user in the system.
    """
    statement = select(UserModel).where(
        (UserModel.username == register_dto.username) | (UserModel.email == register_dto.email)
    )
    result = await session.execute(statement)
    existing_user = result.scalars().first()

    if existing_user:
        if existing_user.username == register_dto.username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already registered",
            )
        # If not username, it must be email due to the OR condition in the query
        # and existing_user being True.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Hash the password before saving
    hashed_password = get_password_hash(register_dto.password)

    # Create UserModel instance from input data and hashed password
    user_data = register_dto.model_dump(exclude={"password"})
    db_user = UserModel(**user_data, hashed_password=hashed_password)

    # Add new user to session and commit
    session.add(db_user)
    try:
        await session.commit()
        await session.refresh(db_user)  # Get user info from DB (including ID)
        return db_user
    except IntegrityError as e:
        await session.rollback()
        error_detail = str(e.orig)
        if "users_username_key" in error_detail:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already registered (database constraint).",
            ) from e
        if "users_email_key" in error_detail: # Changed from elif due to no-else-raise
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered (database constraint).",
            ) from e
        # Other IntegrityError
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {error_detail}",
        ) from e
    except Exception as e:
        await session.rollback()
        logger.error("An unexpected error occurred during registration", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred during registration.",
        ) from e


@router.post("/login", response_model=UserLoginResponse)
async def login(
    *,
    session: AsyncSession = Depends(get_async_session),
    login_dto: UserLogin = Body(...)
):
    """
    Login a user and return the user information along with an access token.
    """
    statement = select(UserModel).where(UserModel.email == login_dto.email)
    result = await session.execute(statement)
    db_user = result.scalars().first()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if db_user.hashed_password is None: # Changed from == None
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no password set (e.g., social login)",
        )

    if not verify_password(login_dto.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )

    additional_claims = {"username": db_user.username, "email": db_user.email}
    access_token = create_access_token(subject=str(db_user.id), additional_claims=additional_claims)
    
    # refresh_token 
    refresh_token = create_access_token(
        subject=str(db_user.id),  # ID hệ thống FastAPI
        expires_delta=timedelta(days=30)  # Example: 30 days for refresh token
    )

    response = UserLoginResponse(
        access_token=access_token,
        user=UserBase.model_validate(db_user),
        refresh_token=refresh_token,
    )
    return response


@router.post("/nextauth-signin", response_model=UserLoginResponse)
async def handle_nextauth_signin(
    payload: NextAuthSigninPayload = Body(...),
    crud: UserCRUD = Depends(UserCRUD),
):
    """
    Generic endpoint for NextAuth callback. Verifies provider token/info,
    gets/creates user, issues FastAPI JWT.
    """
    logger.info("Processing NextAuth signin for provider '%s'", payload.provider.value)
    try:
        # 1. Verify identity via auth_utils dispatcher
        verified_user_info = await verify_identity_from_nextauth(payload)

        # 2. Get or Create User in DB using CRUD
        db_user_model = await crud.get_or_create_oauth_user(verified_user_info)

        try:
            await crud.session.commit()
            await crud.session.refresh(db_user_model)
            logger.info("User Get/Create successful & committed. User system ID: %d", db_user_model.id)
        except IntegrityError as commit_err: # More specific error type
            logger.error("Rolling back due to commit integrity error: ", exc_info=True)
            await crud.session.rollback()
            # Attempt to fetch the user again, as it might have been created by a concurrent request
            db_user_model = await crud.get_user_by_oauth_details(
                provider=verified_user_info.provider,
                provider_id=verified_user_info.provider_id
            )
            if not db_user_model:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database commit error and could not retrieve user."
                ) from commit_err
            logger.info("Found user after commit failed, likely race condition resolved.")
        except Exception as commit_err:
            logger.error("Rolling back due to unexpected commit error: ", exc_info=True)
            await crud.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database commit error."
            ) from commit_err # Corrected from 'e' to 'commit_err'

        # 3. Create FastAPI JWT
        additional_claims = {"username": db_user_model.username, "email": db_user_model.email}
        fastapi_access_token = create_access_token(
            subject=str(db_user_model.id),  # ID hệ thống FastAPI
            additional_claims=additional_claims
        )
        
        # refresh_token
        refresh_token = create_access_token(
            subject=str(db_user_model.id),  # ID hệ thống FastAPI
            expires_delta=timedelta(days=30)  # Example: 30 days for refresh token
        )

        # 4. Prepare and Return Response
        user_response_data = UserBase.model_validate(db_user_model)
        return UserLoginResponse(
            access_token=fastapi_access_token,
            user=user_response_data,
            refresh_token=refresh_token,
        )

    except HTTPException as e:
        # Known HTTP exceptions (e.g., 401 from verify, 403 from secret), re-raise
        # Rollback might be needed if CRUD operations occurred before this point in this try block
        # However, verify_identity_from_nextauth is usually non-modifying.
        # await crud.session.rollback() # Consider if necessary based on verify_identity_from_nextauth
        logger.warning("HTTPException during NextAuth signin: ", exc_info=True)
        raise e
    except Exception as e:
        # Unexpected errors
        logger.error("Rolling back due to unexpected error in NextAuth signin endpoint: ", exc_info=True)
        await crud.session.rollback() # Rollback for any unknown errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during sign-in processing."
        ) from e

@router.post("/tokens/anonymous")
async def create_anonymous_token():
    """
    Create an anonymous token for a user.
    """
    claims = {
        "workspace_id": uuid.uuid4().__str__(),
        "project_id": uuid.uuid4().__str__(),
        "sub": uuid.uuid4().__str__(),
        "iss": "http://127.0.0.1:8000",
    }
    
    at = create_access_token(
        subject=str(claims["sub"]),
        additional_claims=claims,
    )
    
    refesh_token = {
        "token": "refresh" + str(uuid.uuid4()),
        "expires_at": datetime.utcnow() + timedelta(days=20),
    }
    
    return {
        "access_token": at,
        "refresh_token": refesh_token,
    }

class RefreshTokenRequest(BaseModel):
    """
    Request model for refreshing tokens.
    """
    refresh_token: str


@router.post("/tokens/refresh")	
async def refresh_token(
    body: RefreshTokenRequest = Body(...)
):
    """
    Refresh the access token using the refresh token.
    """
    # Here you would typically verify the refresh token and issue a new access token
    # For simplicity, let's assume the refresh token is valid and we generate a new access token
    
    if not body.refresh_token.startswith("refresh"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid refresh token",
        )
    
    claims = {
        "workspace_id": uuid.uuid4().__str__(),
        "project_id": uuid.uuid4().__str__(),
        "sub": uuid.uuid4().__str__(),
        "iss": "http://127.0.0.1:8000",
    }
    
    at = create_access_token(
        subject=str(claims["sub"]),
        additional_claims=claims,
    )
    
    return {
        "access_token": at,
    }