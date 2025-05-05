from datetime import timedelta
import logging
from typing import Any, Dict
import uuid
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.config.settings import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.crud.user_crud import UserCRUD
from app.database.session import get_async_session
from app.models.user_model import LinkedAccountModel, UserModel
from sqlalchemy.exc import IntegrityError
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.schemas.auth_schemas import NextAuthSigninPayload
from app.schemas.user_schema import GoogleTokenData, TokenPayload, TokenResponse, UserLogin, UserLoginResponse, UserBase, UserCreate
from sqlalchemy.orm import selectinload

from app.utils.auth_utils import verify_identity_from_nextauth 
logger = logging.getLogger(__name__)
router = APIRouter()
@router.post("/register", response_model=UserBase, status_code=status.HTTP_201_CREATED)
async def register(
    *, 
    session: AsyncSession = Depends(get_async_session),
    register_dto: UserCreate):
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
        else: # existing_user.email == user_in.email
             raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

    # Băm mật khẩu trước khi lưu
    hashed_password = get_password_hash(register_dto.password)

    # Tạo đối tượng UserModel từ dữ liệu đầu vào và mật khẩu đã băm
    # Loại bỏ password khỏi user_in dict trước khi truyền vào UserModel
    user_data = register_dto.model_dump(exclude={"password"})
    db_user = UserModel(**user_data, hashed_password=hashed_password)

    # Thêm user mới vào session và commit
    session.add(db_user)
    try:
        await session.commit()
        await session.refresh(db_user) # Lấy lại thông tin user từ DB (bao gồm ID)
        return db_user # FastAPI sẽ tự chuyển đổi db_user thành UserRead
    except IntegrityError as e: # Bắt lỗi nếu username/email bị trùng (do race condition hoặc không kiểm tra trước)
        await session.rollback() # Quan trọng: rollback transaction khi có lỗi
        # Phân tích lỗi chi tiết hơn nếu cần (ví dụ: xem constraint nào bị vi phạm)
        error_detail = str(e.orig) # Thông tin lỗi gốc từ DB driver (asyncpg)
        if "users_username_key" in error_detail:
             raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already registered (database constraint).",
            )
        elif "users_email_key" in error_detail:
             raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered (database constraint).",
            )
        else:
            # Lỗi IntegrityError khác
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database integrity error: {error_detail}",
            )
    except Exception as e:
        await session.rollback()
        # Ghi log lỗi ở đây nếu cần
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred.",
        )

@router.post("/login", response_model=UserLoginResponse)
async def login(*, 
    session: AsyncSession = Depends(get_async_session),
    login_dto: UserLogin = Body(...)):
    """
    Login user and return access token.
    """
    """
    Login a user and return the user information.
    """
    statement = select(UserModel).where(
        UserModel.email == login_dto.email
    )
    result = await session.execute(statement)
    db_user = result.scalars().first()
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
        
    if db_user.hashed_password == None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no password set",
        )
    
    if not verify_password(login_dto.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )
        
    additional_claims = {"username": db_user.username, "email": db_user.email, }
        
    access_token = create_access_token(subject=db_user.id, additional_claims=additional_claims)
    
    response = UserLoginResponse(
            access_token=access_token,
            user=db_user
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

    print(f"Endpoint: Processing signin for provider '{payload.provider.value}'")
    try:
        # 1. Verify identity via auth_utils dispatcher
        verified_user_info = await verify_identity_from_nextauth(payload)
        # 2. Get or Create User in DB using CRUD
        db_user_model = await crud.get_or_create_oauth_user(verified_user_info)

        try:
            await crud.session.commit()
            await crud.session.refresh(db_user_model) 
            print(f"Endpoint: User Get/Create successful & committed. User system ID: {db_user_model.id}")
        except Exception as commit_err:
             # Lỗi khi commit (ví dụ: unique constraint nếu user được tạo đồng thời)
             print(f"Endpoint: Rolling back due to commit error: {commit_err}")
             await crud.session.rollback()
             # Có thể thử lại việc lấy user nếu lỗi là do race condition khi tạo mới
             # db_user_model = await crud.get_user_by_provider_id(verified_user_info.provider, str(verified_user_info.provider_id))
             # if not db_user_model: # Nếu vẫn không tìm thấy thì raise lỗi 500
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database commit error.")
             # else: print("Found user after commit failed, likely race condition.")

        # 3. Create FastAPI JWT
        additional_claims = {"username": db_user_model.username, "email": db_user_model.email}
        fastapi_access_token = create_access_token(
            subject=str(db_user_model.id), # ID hệ thống FastAPI
            additional_claims=additional_claims
        )

        # 4. Prepare and Return Response
        user_response_data = UserBase.model_validate(db_user_model)
        return UserLoginResponse(
            access_token=fastapi_access_token,
            user=user_response_data
        )

    except HTTPException as e:
        # Lỗi đã biết (ví dụ: 401 từ verify, 403 từ secret), rollback và re-raise
        # Rollback chỉ cần thiết nếu đã có thay đổi trong session trước khi lỗi xảy ra
        # Các hàm verify thường không thay đổi DB nên rollback ở đây có thể không cần
        # await crud.session.rollback() # Xem xét cẩn thận
        raise e
    except Exception as e:
        # Lỗi không mong muốn
        print(f"Endpoint: Rolling back due to unexpected error in signin endpoint: {e}")
        await crud.session.rollback() # Rollback khi có lỗi không xác định
        # Log lỗi chi tiết và bảo mật
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during sign-in processing."
        )