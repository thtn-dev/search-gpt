import logging
from typing import Any, Dict, Optional
import uuid
from fastapi import Depends
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import selectinload 
from app.database.session import get_async_session
from app.models.user_model import LinkedAccountModel, UserModel
from sqlalchemy.exc import IntegrityError

from app.schemas.auth_schemas import AuthProvider, VerifiedUserData

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
            # Tải luôn user và các linked_accounts khác của user đó
            .options(
                selectinload(LinkedAccountModel.user)
                .selectinload(UserModel.linked_accounts)
            )
        )
        results = await self.session.exec(statement)
        linked_account = results.one_or_none() # Dùng one_or_none() an toàn hơn
        return linked_account.user if linked_account else None

    async def get_user_by_email(self, email: EmailStr) -> Optional[UserModel]:
        """
        Finds a user by their email address.
        Returns the UserModel if found, otherwise None.
        Loads the user with their linked accounts eagerly.
        """
        statement = (
            select(UserModel)
            .where(UserModel.email == email)
            .options(selectinload(UserModel.linked_accounts)) # Tải luôn linked_accounts
        )
        results = await self.session.exec(statement)
        return results.one_or_none() # Dùng one_or_none()

    async def link_provider_to_user(
        self, user: UserModel, provider: AuthProvider, provider_key: str
    ) -> LinkedAccountModel:
        """
        Creates and links a new provider account to an existing user.
        Handles potential race conditions during commit.
        """
        logger.info(f"Attempting to link provider '{provider.value}' (key: {provider_key}) to User ID: {user.id}")

        # Kiểm tra lại lần nữa trong bộ nhớ xem link đã tồn tại chưa (phòng trường hợp load chưa đủ)
        has_link = any(
            la.provider == provider.value and la.provider_key == provider_key
            for la in user.linked_accounts # Giả định linked_accounts đã được load
        )
        if has_link:
             logger.info(f"Link for provider '{provider.value}' already exists for User ID: {user.id} in memory.")
             # Tìm và trả về link account hiện có trong list
             existing_link = next((la for la in user.linked_accounts if la.provider == provider.value and la.provider_key == provider_key), None)
             return existing_link # Trả về link đã có


        # Nếu chưa có, tạo mới
        new_linked_account = LinkedAccountModel(
            provider=provider.value,
            provider_key=provider_key,
            user_id=user.id # Gán user_id trực tiếp
            # user=user # Hoặc gán user object nếu relationship được cấu hình đúng
        )
        self.session.add(new_linked_account)

        try:
            # Flush để kiểm tra IntegrityError sớm (unique constraint)
            await self.session.flush()
            # Không commit ở đây, commit sẽ ở endpoint
            logger.info(f"Successfully added LinkedAccount for provider '{provider.value}' to session for User ID: {user.id}")
            # Thêm vào list trong bộ nhớ của user để nhất quán
            user.linked_accounts.append(new_linked_account)
            return new_linked_account
        except IntegrityError as e:
            # Lỗi xảy ra, có thể do request khác đã tạo link này
            await self.session.rollback() # Quan trọng: rollback lại những thay đổi trong session
            logger.warning(f"IntegrityError while linking account for User ID {user.id}, provider {provider.value}: {e}. Assuming link exists due to race condition.")
            # Thử tải lại user và link account từ DB để đảm bảo
            refreshed_user = await self.get_user_by_email(user.email) # Hoặc get user by ID
            if refreshed_user:
                 existing_link = next((la for la in refreshed_user.linked_accounts if la.provider == provider.value and la.provider_key == provider_key), None)
                 if existing_link:
                      logger.info(f"Confirmed existing link for provider '{provider.value}' after rollback for User ID: {user.id}")
                      return existing_link
                 else:
                      # Trường hợp lạ: rollback nhưng link vẫn không có?
                      logger.error(f"Could not find link for provider '{provider.value}' after rollback for User ID: {user.id}. Raising original error.")
                      raise e # Ném lại lỗi ban đầu
            else:
                 logger.error(f"User ID {user.id} not found after rollback during linking. Raising original error.")
                 raise e # Ném lại lỗi ban đầu
        except Exception as e:
             await self.session.rollback()
             logger.error(f"Unexpected error linking account for User ID {user.id}, provider {provider.value}: {e}")
             raise

    async def create_new_oauth_user(
        self, user_info: VerifiedUserData
    ) -> UserModel:
        """
        Creates a new user and links the initial provider account.
        Handles potential race conditions during commit.
        """
        logger.info(f"Attempting to create new user for provider '{user_info.provider.value}', email={user_info.email}")

        if not user_info.email:
            # Xem xét lại logic nếu email là bắt buộc trong UserModel
            logger.error("Cannot create user without an email address.")
            raise ValueError("Email is required to create a new user.")

        # Tạo username duy nhất (logic có thể cần cải thiện)
        base_username = user_info.email.split("@")[0]
        # Giới hạn độ dài + thêm hex để tránh trùng và vượt max_length
        max_base_len = 50 - 7 # 50 là max_length của username, 6 hex, 1 gạch nối
        username = f"{base_username[:max_base_len]}_{uuid.uuid4().hex[:6]}"
        logger.info(f"Generated username: {username}")

        # Chuyển đổi picture từ HttpUrl sang string nếu cần
        picture_url = str(user_info.picture) if user_info.picture else None

        new_user = UserModel(
            email=user_info.email,
            username=username, # Cân nhắc để null và yêu cầu user đặt sau
            hashed_password=None, # OAuth users không có password
            is_active=True, # Kích hoạt mặc định
            # created_at/updated_at tự động nhờ default_factory
            # Thêm full_name nếu có trong model và user_info
            # full_name=user_info.name
        )
        # Tạo linked account ban đầu
        new_linked_account = LinkedAccountModel(
            provider=user_info.provider.value,
            provider_key=str(user_info.provider_id), # Đảm bảo là string
            # user=new_user # Liên kết qua relationship
        )
        # Thêm linked account vào list của user (SQLModel/SQLAlchemy sẽ xử lý liên kết)
        new_user.linked_accounts.append(new_linked_account)

        self.session.add(new_user) # Add user, linked account sẽ theo nhờ cascade

        try:
            # Flush để kiểm tra IntegrityError sớm (unique email/username/provider_key)
            await self.session.flush()
            # Không commit ở đây
            logger.info(f"Successfully added new User (email: {new_user.email}) and LinkedAccount to session.")
            return new_user
        except IntegrityError as e:
            # Lỗi xảy ra, có thể user/email/link đã được tạo bởi request khác
            await self.session.rollback()
            logger.warning(f"IntegrityError while creating new user (email: {user_info.email}): {e}. Assuming user/link exists due to race condition. Retrying find.")
            # Thử tìm lại user bằng provider key hoặc email
            existing_user = await self.get_user_by_provider_key(user_info.provider, str(user_info.provider_id))
            if existing_user:
                logger.info(f"Found existing user by provider key after rollback: {existing_user.id}")
                return existing_user
            existing_user = await self.get_user_by_email(user_info.email)
            if existing_user:
                 logger.info(f"Found existing user by email after rollback: {existing_user.id}. Attempting to link.")
                 # Cần đảm bảo liên kết được tạo nếu chưa có
                 await self.link_provider_to_user(existing_user, user_info.provider, str(user_info.provider_id))
                 # Tải lại user với link mới (nếu link_provider_to_user không trả về user)
                 return await self.get_user_by_email(user_info.email) # Hoặc get by ID
            else:
                 logger.error(f"Could not find user by provider key or email after rollback during creation. Raising original error.")
                 raise e # Lỗi IntegrityError không mong muốn
        except Exception as e:
             await self.session.rollback()
             logger.error(f"Unexpected error creating new user (email: {user_info.email}): {e}")
             raise

    async def get_or_create_oauth_user(
        self, user_info: VerifiedUserData
    ) -> UserModel:
        """
        Gets a user based on OAuth provider info (priority: provider_key)
        or creates a new user if they don't exist and links the provider.

        Handles potential race conditions during linking or creation.
        The final commit should happen in the calling endpoint.

        Args:
            user_info: Standardized user data from the verified provider token.

        Returns:
            The existing or newly created UserModel instance, ready for commit.

        Raises:
            ValueError: If user_info lacks necessary data (provider_id, email).
            HTTPException: Can be raised from underlying operations on commit failure.
        """
        # --- Input Validation ---
        provider = user_info.provider
        provider_key = str(user_info.provider_id) # Đảm bảo là string
        email = user_info.email

        if not provider_key:
            logger.error("VerifiedUserData is missing 'provider_id'.")
            raise ValueError("OAuth information incomplete (missing provider_id).")
        if not email:
            logger.error("VerifiedUserData is missing 'email'.")
            raise ValueError("OAuth information incomplete (missing email).")

        logger.info(f"Starting get_or_create for provider={provider.value}, email={email}, provider_key={provider_key}")

        # --- 1. Find by Provider Key (Most reliable) ---
        db_user = await self.get_user_by_provider_key(provider, provider_key)
        if db_user:
            logger.info(f"Found existing User ID {db_user.id} via provider key.")
            # Optional: Update user profile info (name, picture) if needed
            # ... (logic cập nhật thông tin user) ...
            # if needs_update: self.session.add(db_user)
            return db_user

        # --- 2. Find User by Email (Potential account linking) ---
        logger.info("User not found by provider key, searching by email...")
        if email: # Chỉ tìm bằng email nếu có email
            db_user_by_email = await self.get_user_by_email(email)
            if db_user_by_email:
                logger.info(f"Found existing User ID {db_user_by_email.id} by email. Linking provider '{provider.value}'...")
                # User exists, link this new provider account to them
                await self.link_provider_to_user(db_user_by_email, provider, provider_key)
                # Return the user found by email (now potentially with the new link added to session)
                # Cần load lại user để đảm bảo có link mới nhất nếu link_provider_to_user không trả về user
                # return await self.get_user_by_email(email) # Hoặc get by ID
                return db_user_by_email # Trả về user đã tìm thấy
            else:
                 logger.info(f"No user found with email {email}.")
        else:
            logger.info("No email provided in user_info, cannot search by email.")

        # --- 3. Create New User ---
        logger.info("User not found by provider key or email. Creating new user...")
        # Email là bắt buộc để tạo mới trong logic này
        if not email:
             logger.error("Cannot create new user without email address from provider.")
             raise ValueError("Email is required from provider to create a new user account.")

        new_user = await self.create_new_oauth_user(user_info)
        return new_user