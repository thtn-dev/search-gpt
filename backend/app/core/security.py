from datetime import datetime, timedelta
from typing import Any, Dict, Tuple, Union
import uuid
import bcrypt
from cryptography.fernet import Fernet
import jwt

from app.config.settings import  settings
from app.utils.datetime_utils import utc_now

fernet = Fernet(str.encode(settings.ENCRYPT_KEY))
JWT_ALGORITHM = "HS256"


def create_access_token(subject: Union[str, Any], expires_delta: timedelta | None = None, additional_claims: Dict[str, Any] | None = None) -> str:
    if expires_delta:
        expire = utc_now() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    jti = uuid.uuid4()
    iat = utc_now()
    nbf = iat
    to_encode = {"exp": expire, "sub": str(subject), "type": "access_token", "jti": str(jti), "iat": iat, "nbf": nbf}

    # Thêm các claims tùy chọn nếu chúng được cung cấp
    if additional_claims:
        to_encode.update(additional_claims)

    return jwt.encode(
        payload=to_encode,
        key=settings.ENCRYPT_KEY,
        algorithm=JWT_ALGORITHM,
    )



def create_refresh_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    if expires_delta:
        expire = utc_now() + expires_delta
    else:
        expire = utc_now() + timedelta(
            minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}

    return jwt.encode(
        payload=to_encode,
        key=settings.ENCRYPT_KEY,
        algorithm=JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        jwt=token,
        key=settings.ENCRYPT_KEY,
        algorithms=[JWT_ALGORITHM],
    )


def verify_password(plain_password: str | bytes, hashed_password: str | bytes) -> bool:
    if isinstance(plain_password, str):
        plain_password = plain_password.encode()
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode()

    return bcrypt.checkpw(plain_password, hashed_password)


def get_password_hash(plain_password: str | bytes) -> str:
    if isinstance(plain_password, str):
        plain_password = plain_password.encode()

    return bcrypt.hashpw(plain_password, bcrypt.gensalt()).decode()


def get_data_encrypt(data) -> str:
    data = fernet.encrypt(data)
    return data.decode()


def get_content(variable: str) -> str:
    return fernet.decrypt(variable.encode()).decode()