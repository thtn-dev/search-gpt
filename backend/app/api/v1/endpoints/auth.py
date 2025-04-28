from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.core.security import create_access_token, get_password_hash, verify_password
from app.database.session import get_async_session
from app.models.user_model import UserModel
from app.schemas.user.create_user_schema import UserCreate, UserLogin, UserLoginResponse, UserRead
from sqlalchemy.exc import IntegrityError

router = APIRouter()
@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
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
        UserModel.username == login_dto.username
    )
    result = await session.execute(statement)
    db_user = result.scalars().first()
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Kiểm tra mật khẩu
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