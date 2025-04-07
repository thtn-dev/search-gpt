import os
from pydantic_settings import BaseSettings
from typing import Optional
class Settings(BaseSettings):
    DATABASE_URL: str 
    GOOGLE_API_KEY: Optional[str] = None
    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
        env_file_encoding = "utf-8"
        
settings = Settings()