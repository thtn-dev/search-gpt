
import re
from typing import Annotated
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlmodel import SQLModel

class UserCreate(SQLModel):
    """
    User registration schema.
    """
    email: EmailStr
    username: Annotated[str, Field(min_length=3, max_length=50)]
    password: Annotated[str, Field(min_length=8, max_length=128)]

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        """
        Password testing must meet the following conditions:
        - At least 8 characters
        - At least one capital letter (A-Z)
        - At least one normal letter (A-Z)
        - At least one digit (0-9)
        """
        # Biểu thức chính quy kết hợp các điều kiện:
        # ^            : Bắt đầu chuỗi
        # (?=.*[A-Z]) : Positive lookahead - Đảm bảo có ít nhất 1 chữ hoa ở bất kỳ đâu
        # (?=.*[a-z]) : Positive lookahead - Đảm bảo có ít nhất 1 chữ thường ở bất kỳ đâu
        # (?=.*\d)    : Positive lookahead - Đảm bảo có ít nhất 1 chữ số ở bất kỳ đâu
        # .{8,128}       : Khớp với bất kỳ ký tự nào (ngoại trừ newline) ít nhất 8 lần và tối đa 128 lần
        # $            : Kết thúc chuỗi
        password_regex = r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d).{6,128}$"

        if not re.match(password_regex, value):
            raise ValueError("Password must have at least 8 characters, including uppercase, normal and number")
        return value

class UserLogin(BaseModel):
    """
    User login schema.
    """
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        """
        Password testing must meet the following conditions:
        - At least 8 characters
        - At least one capital letter (A-Z)
        - At least one normal letter (A-Z)
        - At least one digit (0-9)
        """
        # Biểu thức chính quy kết hợp các điều kiện:
        # ^            : Bắt đầu chuỗi
        # (?=.*[A-Z]) : Positive lookahead - Đảm bảo có ít nhất 1 chữ hoa ở bất kỳ đâu
        # (?=.*[a-z]) : Positive lookahead - Đảm bảo có ít nhất 1 chữ thường ở bất kỳ đâu
        # (?=.*\d)    : Positive lookahead - Đảm bảo có ít nhất 1 chữ số ở bất kỳ đâu
        # .{8,128}       : Khớp với bất kỳ ký tự nào (ngoại trừ newline) ít nhất 8 lần và tối đa 128 lần
        # $            : Kết thúc chuỗi
        password_regex = r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d).{6,128}$"

        if not re.match(password_regex, value):
            raise ValueError("Password must have at least 8 characters, including uppercase, normal and number")
        return value

class UserBase(SQLModel):
    id: int
    username: str
    email: str
    is_active: bool

class UserLoginResponse(BaseModel):
    accessToken: str
    tokenType: str = "Bearer"
    user: UserBase

class UserLoggedIn(SQLModel):
    id: int
    username: str
    email: str
    

class GoogleTokenData(BaseModel):
    """Model to receive the Google ID Token from Next.js backend"""
    google_id_token: str

class TokenPayload(BaseModel):
    """Payload data inside our FastAPI JWT"""
    sub: str # Subject (usually user ID or email)
    # Add other claims if needed, e.g., roles

class TokenResponse(BaseModel):
    """Response model containing the FastAPI access token"""
    access_token: str
    token_type: str = "bearer"