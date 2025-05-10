"""Authentication service to handle user authorization."""
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
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid user ID in token")

        username: str = payload.get("username")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid username in token")

        email: str = payload.get("email")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid email in token")

        return UserLoggedIn(id=user_id, username=username, email=email)
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(status_code=401, detail="Token has expired") from e
    except jwt.PyJWTError as e: # Catch other JWT errors
        raise HTTPException(status_code=401, detail="Invalid token credentials") from e
    except Exception as e:
        # Log the exception for debugging purposes
        # logger.error(f"An unexpected error occurred during token decoding: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during authentication: {str(e)}"
        ) from e
