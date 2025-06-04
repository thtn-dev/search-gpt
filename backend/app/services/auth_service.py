"""Authentication service to handle user authorization."""
from typing import Optional
import uuid
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from app.core.security import decode_token
# Assuming UserLoggedIn is defined in auth_schemas, adjust if necessary
from app.schemas.user_schema import UserLoggedIn


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())
) -> UserLoggedIn:
    """
    Decodes the JWT token from the Authorization header and returns the logged-in user.

    Args:
        credentials: The HTTP Authorization credentials (Bearer token).

    Raises:
        HTTPException: If the token is invalid, expired, or user details are missing.

    Returns:
        UserLoggedIn: An object containing the authenticated user's details.
    """
    try:
        # It's generally better to use a logger here instead of print for production code
        print(f"Token: {credentials.credentials}")
        payload = decode_token(credentials.credentials)
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid user ID in token")

        username: Optional[str] = payload.get("username")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid username in token")

        email: Optional[str] = payload.get("email")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid email in token")

        return UserLoggedIn(id=uuid.UUID(user_id), username=username, email=email)
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(status_code=401, detail="Token has expired") from e
    except jwt.PyJWTError as e: # Catch other JWT errors
        raise HTTPException(status_code=401, detail="Invalid token credentials") from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during authentication: {str(e)}"
        ) from e

async def get_optional_current_user(
    # Sử dụng optional_http_bearer.
    # auth sẽ là None nếu không có header "Authorization" hoặc header không đúng định dạng Bearer.
    auth: Optional[HTTPAuthorizationCredentials] = Security(HTTPBearer(auto_error=False))
) -> Optional[UserLoggedIn]: # Kiểu trả về bây giờ là Optional[UserLoggedIn]
    """
    Optionally decodes the JWT token from the Authorization header.
    If a valid token is present, returns the logged-in user.
    If no token is present or the token is invalid, returns None.

    Args:
        auth: The HTTP Authorization credentials (Bearer token), or None if not provided/valid.

    Returns:
        Optional[UserLoggedIn]: An object containing the authenticated user's details,
                                 or None if authentication fails or is not attempted.
    """
    if auth is None or auth.credentials is None:
        # Không có token được cung cấp hoặc header không đúng định dạng
        # print("No authentication credentials provided.") # Để gỡ lỗi
        return None

    token = auth.credentials
    try:
        # print(f"Attempting to decode token: {token[:20]}...") # Để gỡ lỗi, chỉ hiển thị một phần token
        payload = decode_token(token) # Hàm này nên raise jwt.ExpiredSignatureError hoặc jwt.PyJWTError nếu token có vấn đề

        user_id: Optional[str] = payload.get("sub")
        username: Optional[str] = payload.get("username")
        email: Optional[str] = payload.get("email")

        if not user_id or not username or not email:
            # Nếu một trong các trường bắt buộc bị thiếu trong payload,
            # coi như token không hợp lệ cho mục đích này.
            # print("Token payload is missing required fields (sub, username, or email).") # Để gỡ lỗi
            return None # Trả về None thay vì raise HTTPException

        return UserLoggedIn(id=uuid.UUID(user_id), username=username, email=email)

    except jwt.ExpiredSignatureError:
        # Token đã hết hạn
        # print("Token has expired.") # Để gỡ lỗi
        return None # Trả về None
    except jwt.PyJWTError as e:
        # Lỗi JWT khác (ví dụ: token không hợp lệ, chữ ký sai)
        # print(f"Invalid token credentials: {e}") # Để gỡ lỗi
        return None # Trả về None
    except Exception as e:
        # Ghi log lỗi này cho mục đích gỡ lỗi vì đây là lỗi không mong muốn
        # logger.error(f"An unexpected error occurred during optional token decoding: {e}", exc_info=True)
        # print(f"An unexpected server error occurred during authentication: {str(e)}") # Để gỡ lỗi

        # Đối với các lỗi máy chủ không mong muốn khác xảy ra trong quá trình xác thực,
        # việc raise lỗi 500 vẫn hợp lý để thông báo về sự cố ở phía máy chủ.
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during optional authentication: {str(e)}"
        ) from e