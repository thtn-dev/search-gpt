"""Application configuration settings using Pydantic."""
import os
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Main application settings.

    Attributes:
        DATABASE_URL: The connection string for the database.
        GOOGLE_API_KEY: Optional API key for Google services.
        ACCESS_TOKEN_EXPIRE_MINUTES: Expiry time for access tokens in minutes.
        ENCRYPT_KEY: Key used for encryption purposes.
        REFRESH_TOKEN_EXPIRE_MINUTES: Expiry time for refresh tokens in minutes.
        GOOGLE_CLIENT_ID: Client ID for Google OAuth.
        MICROSOFT_TENANT_ID: Tenant ID for Microsoft Azure AD.
        MICROSOFT_CLIENT_ID: Client ID for Microsoft Azure AD.
    """
    DATABASE_URL: str
    GOOGLE_API_KEY: Optional[str] = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    ENCRYPT_KEY: str
    REFRESH_TOKEN_EXPIRE_MINUTES: int
    GOOGLE_CLIENT_ID: str
    MICROSOFT_TENANT_ID: str
    MICROSOFT_CLIENT_ID: str
    OPENAI_API_KEY: str
    class Config:
        """Pydantic model configuration."""
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
        env_file_encoding = "utf-8"

# Load environment variables from .env file
# override=True ensures that .env variables take precedence over system environment variables
load_dotenv(override=True, dotenv_path=Settings.Config.env_file)

settings = Settings()
