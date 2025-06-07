from functools import lru_cache
from typing import Annotated, Tuple, Type

from fastapi import Depends
from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    TomlConfigSettingsSource,
)


class AppConfig(BaseModel):
    name: str = 'Default App'
    version: str = '1.0.0'
    debug: bool = False


class DatabaseConfig(BaseModel):
    default_connection: str = ''

class AuthConfig(BaseModel):
    encrypt_key: str = ''
    refresh_token_exp: int = 60 * 24 * 7
    access_token_exp: int = 120
    google_client_id: str = ''
    microsoft_client_id: str = ''
    microsoft_tenant_id: str = ''

class GeminiConfig(BaseModel):
    api_key: str = ""

class OpenAIConfig(BaseModel):
    api_key: str = ""

class LLMModelConfig(BaseModel):
    gemini: GeminiConfig = GeminiConfig()
    openai: OpenAIConfig = OpenAIConfig()

class ApiEndpointsConfig(BaseModel):
    searxng: str = ""

class AppSettings(BaseSettings):
    """
    Main application settings.
    """
    app: AppConfig = AppConfig()
    database: DatabaseConfig = DatabaseConfig()
    llmmodel: LLMModelConfig = LLMModelConfig()
    api_endpoints: ApiEndpointsConfig = ApiEndpointsConfig()
    auth: AuthConfig = AuthConfig()

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            TomlConfigSettingsSource(settings_cls, toml_file='appsettings.toml'),
            file_secret_settings,
        )


# Khởi tạo settings
settings = AppSettings()


class Config:
    def __init__(self) -> None:
        self.settings = AppSettings()


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()


"""
Dependency for FastAPI to inject settings
"""
app_settings = Annotated[AppSettings, Depends(get_settings)]
