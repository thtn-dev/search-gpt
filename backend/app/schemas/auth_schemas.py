"""Pydantic schemas for authentication-related data, including OAuth providers and payloads."""

from enum import Enum
from typing import Optional  # Added Optional for type hinting consistency

from pydantic import BaseModel, EmailStr, HttpUrl


class AuthProvider(str, Enum):
    """Enum for supported authentication providers."""

    GOOGLE = 'google'
    GITHUB = 'github'
    MICROSOFT = 'azure-ad'  # Corresponds to azure-ad in NextAuth


class NextAuthSigninPayload(BaseModel):
    """
    Payload received from NextAuth callback.
    Contains token based on the provider.
    """

    provider: AuthProvider
    id_token: Optional[str] = None  # Provided by Google, Microsoft (Azure AD)
    access_token: Optional[str] = None  # Provided by GitHub, and sometimes others


class VerifiedUserData(BaseModel):
    """Standardized user info extracted after successful verification with an OAuth provider."""

    provider: AuthProvider
    provider_key: (
        str  # Unique user ID from the provider (e.g., Google sub, GitHub id, MS oid)
    )
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    picture: Optional[HttpUrl] = None
