
import re
from typing import Annotated
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlmodel import SQLModel
class UserCreateSchema(SQLModel):
    email: EmailStr
    username: Annotated[str, Field(min_length=3, max_length=50)]
    password: Annotated[str, Field(min_length=8, max_length=128)]

class UserLoginSchema(BaseModel):
    emailOrUsername: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("emailOrUsername")
    @classmethod
    def validate_email_or_username(cls, value):
        try:
            EmailStr.validate(value)
            return value
        except Exception:
            pass

        if re.fullmatch(r"^\w{3,50}$", value):
            return value

        raise ValueError("EmailOrUsername must be a valid email or a valid username (including words, numbers, lower bricks, 3-50 characters)")

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        if (
            len(value) >= 8 and
            re.search(r"[A-Z]", value) and
            re.search(r"[a-z]", value) and
            re.search(r"\d", value)
        ):
            return value
        raise ValueError("Password must have at least 8 characters, including uppercase, normal and number")

class UserBaseSchema(SQLModel):
    id: int
    username: str
    email: str
    is_active: bool

class UserLoginResponse(BaseModel):
    accessToken: str
    tokenType: str = "Bearer"
    user: UserBaseSchema

class UserLoggedInSchema(SQLModel):
    id: int
    username: str
    email: str
    
        