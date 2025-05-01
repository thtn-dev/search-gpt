from datetime import timedelta
import logging
from typing import Any, Dict
import uuid
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.config.settings import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.database.session import get_async_session
from app.models.user_model import LinkedAccountModel, UserModel
from sqlalchemy.exc import IntegrityError
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.schemas.user_schema import GoogleTokenData, TokenPayload, TokenResponse, UserLogin, UserLoginResponse, UserBase, UserCreate
from sqlalchemy.orm import selectinload 
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
    
    if not verify_password(login_dto.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )
        
    additional_claims = {"username": db_user.username, "email": db_user.email, }
        
    access_token = create_access_token(subject=db_user.id, additional_claims=additional_claims)
    
    response = UserLoginResponse(
            accessToken=access_token,
            user=db_user
        )
    
    return response


@router.post("/google/verify-token", response_model=UserLoginResponse)
async def verify_google_token(token_data: GoogleTokenData = Body(...), session: AsyncSession = Depends(get_async_session)):
    """
    Receives Google ID Token from Next.js backend, verifies it,
    finds/creates user, and returns a FastAPI JWT.
    """
    google_token = token_data.google_id_token

    try:
        # Verify the ID token using google-auth library
        # This checks signature, expiration, issuer, and audience
        idinfo = id_token.verify_oauth2_token(
            google_token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID # Specify your Google Client ID here
        )

        # --- Optional: Additional Check ---
        # You might want to double-check the issuer, though verify_oauth2_token usually handles it
        # if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
        #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect issuer")

        # --- User Lookup / Creation ---
        # idinfo contains verified user data like: sub, email, name, picture etc.
        print("Google ID Token Verified Successfully. User Info:", idinfo)
        db_user = await get_or_create_user(idinfo, session)

        # --- Create FastAPI Access Token ---
        # Create the payload for our JWT. 'sub' should be the unique identifier in *your* system.
        # Here we use the user_id from our DB (which we set to Google's 'sub').
        additional_claims = {"username": db_user.username, "email": db_user.email, }
        access_token = create_access_token(
            subject=db_user.id,
            additional_claims=additional_claims,
        )

        print(f"Generated FastAPI token for user: {db_user.id}")
        return UserLoginResponse(
            accessToken=access_token,
            user=db_user
        )

    except ValueError as e:
        # This can happen if the token is invalid format or library internal errors
        print(f"Token verification value error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token format or value",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        # Catch other potential exceptions during verification (e.g., network issues fetching keys)
        # or during user lookup/creation
        print(f"An unexpected error occurred: {e}")
        # Be careful not to expose sensitive error details to the client
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred during token verification or user processing.",
        )
        
        
async def get_or_create_user(idinfo: Dict[str, Any], session: AsyncSession) -> UserModel:
    """
    Lấy người dùng dựa trên thông tin OAuth provider (ưu tiên provider_key)
    hoặc tạo người dùng mới nếu chưa tồn tại và liên kết provider.

    Args:
        idinfo: Dictionary chứa thông tin từ OAuth provider (cần có 'sub' và 'email').
        session: AsyncSession để tương tác với DB.

    Returns:
        Đối tượng UserModel đã tồn tại hoặc vừa được tạo.

    Raises:
        ValueError: Nếu idinfo thiếu thông tin cần thiết.
        IntegrityError: Nếu có lỗi không mong muốn khi commit (ngoài race condition đã xử lý).
    """
    provider = "google" # Hoặc lấy động nếu hàm này xử lý nhiều provider

    # --- Input Validation ---
    google_user_id = idinfo.get("sub")
    email = idinfo.get("email")

    if not google_user_id or not email:
        logger.error("idinfo thiếu 'sub' hoặc 'email'.")
        raise ValueError("Thông tin OAuth không đầy đủ (thiếu sub hoặc email).")

    logger.info(f"Bắt đầu get_or_create cho provider={provider}, email={email}, provider_id={google_user_id}")

    # --- 1. Ưu tiên tìm kiếm bằng Provider ID ---
    stmt_find_link = (
        select(LinkedAccountModel)
        .where(LinkedAccountModel.provider == provider)
        .where(LinkedAccountModel.provider_key == google_user_id)
        # Tải luôn thông tin user liên quan để tránh query N+1
        .options(selectinload(LinkedAccountModel.user).selectinload(UserModel.linked_accounts))
    )
    result_link = await session.execute(stmt_find_link)
    linked_account = result_link.scalars().first()

    if linked_account and linked_account.user:
        logger.info(f"Tìm thấy LinkedAccount và User tồn tại qua provider_id. User ID: {linked_account.user.id}")
        # Đảm bảo user có danh sách linked_accounts được load (do selectinload)
        # await session.refresh(linked_account.user, ['linked_accounts']) # Có thể không cần nếu selectinload hoạt động đúng
        return linked_account.user

    # --- 2. Nếu không tìm thấy bằng Provider ID, tìm User bằng Email ---
    logger.info("Không tìm thấy bằng provider_id, tìm user bằng email...")
    stmt_find_user_by_email = (
        select(UserModel)
        .where(UserModel.email == email)
         # Tải luôn các linked_accounts của user này
        .options(selectinload(UserModel.linked_accounts))
    )
    result_user = await session.execute(stmt_find_user_by_email)
    db_user = result_user.scalars().first()

    if db_user:
        # --- 3. User tồn tại bằng Email, nhưng chưa liên kết Provider này ---
        logger.info(f"Tìm thấy User bằng email (ID: {db_user.id}), nhưng chưa có LinkedAccount cho {provider}. Tiến hành liên kết...")

        # Kiểm tra lại xem có thực sự chưa liên kết không (phòng trường hợp race condition nhỏ)
        has_provider_link = any(
            la.provider == provider and la.provider_key == google_user_id
            for la in db_user.linked_accounts
        )

        if not has_provider_link:
            new_linked_account = LinkedAccountModel(
                provider=provider,
                provider_key=google_user_id,
                # user_id=db_user.id # Không cần gán trực tiếp user_id nếu dùng relationship
                user=db_user # Gán trực tiếp object user
            )
            # Không cần add(new_linked_account) vì nó sẽ được thêm qua relationship khi commit
            # session.add(new_linked_account) # Chỉ cần nếu không dùng relationship hoặc cascade
            try:
                await session.commit()
                await session.refresh(db_user) # Refresh user để cập nhật list linked_accounts
                logger.info(f"Đã liên kết {provider} cho User ID: {db_user.id}")
            except IntegrityError as e:
                await session.rollback()
                # Có thể link đã được tạo bởi một request khác? Thử tải lại
                logger.warning(f"Lỗi IntegrityError khi liên kết tài khoản {provider} cho user {db_user.id}: {e}. Thử tải lại.")
                result_user_retry = await session.execute(stmt_find_user_by_email)
                db_user = result_user_retry.scalars().first()
                if not db_user: # Trường hợp rất hiếm: user bị xóa giữa chừng?
                     logger.error(f"User {db_user.id} không còn tồn tại sau khi rollback.")
                     # Có thể raise lỗi ở đây hoặc xử lý khác
                     raise e # Ném lại lỗi ban đầu
            except Exception as e:
                await session.rollback()
                logger.error(f"Lỗi không xác định khi liên kết tài khoản {provider} cho user {db_user.id}: {e}")
                raise # Ném lại lỗi để xử lý ở tầng cao hơn
        else:
             logger.info(f"Tài khoản {provider} đã được liên kết cho User ID: {db_user.id} (có thể do request khác).")

        return db_user

    # --- 4. User hoàn toàn mới ---
    logger.info("Không tìm thấy User bằng email. Tạo User và LinkedAccount mới...")
    try:
        # Tạo username duy nhất (có thể cải thiện logic này nếu cần)
        base_username = email.split("@")[0] if "@" in email else "user"
        # Giới hạn độ dài base_username để tránh vượt quá max_length của cột
        max_base_len = 50 - 7 # 50 là max_length, 6 là hex, 1 là dấu gạch nối/số
        username = f"{base_username[:max_base_len]}_{uuid.uuid4().hex[:6]}"
        logger.info(f"Username được tạo: {username}")

        new_user = UserModel(
            email=email,
            username=username, # Cân nhắc để null và yêu cầu user đặt sau
            hashed_password=None, # Không có password cho OAuth user
        )
        new_linked_account = LinkedAccountModel(
            provider=provider,
            provider_key=google_user_id,
        )

        # Liên kết chúng lại với nhau thông qua relationship
        new_user.linked_accounts.append(new_linked_account)
        # Chỉ cần add new_user, linked_account sẽ được add theo nhờ cascade
        session.add(new_user)

        await session.commit()
        await session.refresh(new_user) # Lấy ID và các giá trị DB khác
        # Có thể cần refresh cả linked_account nếu muốn lấy ID của nó
        # await session.refresh(new_linked_account)
        logger.info(f"Đã tạo User mới (ID: {new_user.id}) và LinkedAccount.")
        return new_user

    except IntegrityError as e:
        # --- Xử lý Race Condition khi tạo User ---
        await session.rollback() # Quan trọng: rollback transaction lỗi
        logger.warning(f"Lỗi IntegrityError khi tạo user mới (có thể do race condition): {e}. Thử tìm lại user...")

        # Có thể user/email/username đã được tạo bởi một request khác. Thử tìm lại.
        # Ưu tiên tìm lại bằng provider_id trước
        result_link_retry = await session.execute(stmt_find_link)
        linked_account_retry = result_link_retry.scalars().first()
        if linked_account_retry and linked_account_retry.user:
             logger.info("Tìm thấy user sau khi rollback (tìm bằng provider_id).")
             return linked_account_retry.user

        # Nếu không, tìm lại bằng email
        result_user_retry = await session.execute(stmt_find_user_by_email)
        db_user_retry = result_user_retry.scalars().first()
        if db_user_retry:
            logger.info("Tìm thấy user sau khi rollback (tìm bằng email).")
            # Có thể cần kiểm tra và liên kết provider nếu chưa có (logic tương tự bước 3)
            # ... (thêm logic liên kết nếu cần) ...
            return db_user_retry
        else:
            # Nếu vẫn không tìm thấy, đây là lỗi IntegrityError khác không mong muốn
            logger.error(f"Lỗi IntegrityError không phải do race condition dự kiến: {e}")
            raise e # Ném lại lỗi để xử lý ở tầng cao hơn

    except Exception as e:
        await session.rollback()
        logger.error(f"Lỗi không xác định khi tạo user mới: {e}")
        raise # Ném lại lỗi để xử lý ở tầng cao hơn