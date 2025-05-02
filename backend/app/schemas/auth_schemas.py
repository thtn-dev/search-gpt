from pydantic import BaseModel, EmailStr, HttpUrl
from enum import Enum
import uuid

class AuthProvider(str, Enum):
    """Enum for supported authentication providers."""
    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "azure-ad" # Corresponds to azure-ad in NextAuth

class NextAuthSigninPayload(BaseModel):
    """
    Payload received from NextAuth callback.
    Contains token based on the provider.
    """
    provider: AuthProvider
    id_token: str | None = None      # Provided by Google, Microsoft (Azure AD)
    access_token: str | None = None

class VerifiedUserData(BaseModel):
    """Standardized user info extracted after successful verification"""
    provider: AuthProvider
    provider_key: str # ID duy nhất của user từ provider (Google sub, GitHub id, MS oid)
    email: EmailStr | None = None
    name: str | None = None
    picture: HttpUrl | None = None