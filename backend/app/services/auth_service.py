from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from app.config.settings import settings
from app.core.security import decode_token
from app.schemas.user.create_user_schema import UserLoggedIn, UserRead

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())):
    try:
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
    except jwt.exceptions.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")