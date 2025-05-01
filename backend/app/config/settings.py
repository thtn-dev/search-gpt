import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import Optional
class Settings(BaseSettings):
    DATABASE_URL: str 
    GOOGLE_API_KEY: Optional[str] = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int 
    ENCRYPT_KEY: str 
    REFRESH_TOKEN_EXPIRE_MINUTES: int 
    GOOGLE_CLIENT_ID: str
    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
        env_file_encoding = "utf-8"
        
load_dotenv(override=True)
settings = Settings()