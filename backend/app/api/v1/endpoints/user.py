from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.database.session import get_session2
from app.models.user_model import UserModel
from app.schemas.user.create_user_schema import UserCreate, UserRead
from app.utils.security import get_password_hash
from sqlalchemy.exc import IntegrityError
router = APIRouter()

@router.post("/users/", response_model=UserRead, status_code=status.HTTP_201_CREATED, tags=["Users"])
async def create_new_user(
    *, # Dấu * yêu cầu các tham số sau phải là keyword arguments
    session: AsyncSession = Depends(get_session2),
    user_in: UserCreate # Dữ liệu user từ request body, được validate bởi UserCreate
):
    """
    Tạo một người dùng mới trong hệ thống.
    """
   
    statement = select(UserModel).where(
        (UserModel.username == user_in.username) | (UserModel.email == user_in.email)
    )
    result = await session.execute(statement)
    existing_user = result.scalars().first()
    if existing_user:
        if existing_user.username == user_in.username:
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
    hashed_password = user_in.password

    # Tạo đối tượng UserModel từ dữ liệu đầu vào và mật khẩu đã băm
    # Loại bỏ password khỏi user_in dict trước khi truyền vào UserModel
    user_data = user_in.model_dump(exclude={"password"})
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