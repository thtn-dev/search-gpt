"""Pydantic models (schemas) for user-related data validation and serialization."""
import re
from typing import Annotated, Optional
from uuid import UUID

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
    def validate_password(cls, value: str) -> str:
        """
        Password testing must meet the following conditions:
        - At least 8 characters
        - At least one capital letter (A-Z)
        - At least one normal letter (a-z) # Corrected from A-Z
        - At least one digit (0-9)
        """
        # Regex combines conditions:
        # ^               : Start of string
        # (?=.*[A-Z])     : Positive lookahead - Ensures at least 1 uppercase letter
        # (?=.*[a-z])     : Positive lookahead - Ensures at least 1 lowercase letter
        # (?=.*\d)        : Positive lookahead - Ensures at least 1 digit
        # .{8,128}        : Matches any character (except newline) 8 to 128 times
        # $               : End of string
        password_regex = r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d).{8,128}$"

        if not re.match(password_regex, value):
            raise ValueError(
                "Password must be 8-128 characters long, including at least "
                "one uppercase letter, one lowercase letter, and one number."
            )
        return value


class UserLogin(BaseModel):
    """
    User login schema.
    """
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """
        Password validation for login.
        Ensures the password format matches the registration requirements.
        """
        # Reusing the same robust password validation logic
        password_regex = r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d).{8,128}$"
        if not re.match(password_regex, value):
            # For login, a generic message might be better for security
            # to avoid revealing which part of the validation failed.
            # However, for consistency with UserCreate, keeping detailed for now.
            raise ValueError(
                "Password format is incorrect. Please ensure it meets the required criteria."
            )
        return value


class UserBase(SQLModel):
    """Base user schema with core user information."""
    id: UUID
    username: str
    email: EmailStr # Changed from str to EmailStr for consistency
    is_active: bool

    # model_config = {
    #     "alias_generator": to_camel, # This would require to_camel to be imported
    #     "populate_by_name": True,
    #     "json_schema_extra": {
    #         "example": {
    #             "id": 1,
    #             "username": "string",
    #             "email": "user@example.com",
    #             "isActive": True
    #         }
    #     }
    # }


class UserLoginResponse(BaseModel):
    """Response model for user login, including token and user details."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    user: UserBase

    # model_config = {
    #     "alias_generator": to_camel, # This would require to_camel to be imported
    #     "populate_by_name": True,
    #     "json_schema_extra": {
    #         "example": {
    #             "accessToken": "your_access_token_here",
    #             "tokenType": "Bearer",
    #             "user": {
    #                 "id": 1,
    #                 "username": "johndoe",
    #                 "email": "johndoe@example.com",
    #                 "isActive": True
    #             }
    #         }
    #     }
    # }


class UserLoggedIn(SQLModel):
    """Schema representing the data of a currently logged-in user, typically from a token."""
    id: UUID
    username: str
    email: EmailStr # Changed from str to EmailStr for consistency


class GoogleTokenData(BaseModel):
    """Model to receive the Google ID Token from a client (e.g., Next.js backend)."""
    google_id_token: str


class TokenPayload(BaseModel):
    """Payload data contained within our application's JWT."""
    sub: str  # Subject (usually user ID)
    # Add other claims if needed, e.g., username, email, roles
    username: Optional[str] = None # Added for clarity if including in token
    email: Optional[EmailStr] = None    # Added for clarity if including in token


class TokenResponse(BaseModel):
    """Response model containing the FastAPI access token."""
    access_token: str
    token_type: str = "bearer"
