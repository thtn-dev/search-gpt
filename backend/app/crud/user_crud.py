import logging
from typing import Any, Dict
import uuid
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import selectinload 
from app.database.session import get_async_session
from app.models.user_model import LinkedAccountModel, UserModel
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)
class UserCRUD:
    """
    CRUD class for User model.
    The database session is injected into the constructor.
    """
    def __init__(self, db: AsyncSession = Depends(get_async_session)):
        """
        Initializes the CRUD class with a database session provided by FastAPI's dependency injection.
        A new instance of ItemCRUD is created for each request.
        """
        self._db = db

    @property
    def session(self) -> AsyncSession:
        return self._db
    
    async def get_or_create_google_user(self, idinfo: Dict[str, Any]) -> UserModel:
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
        session = self.session
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