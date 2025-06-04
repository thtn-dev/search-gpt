# pylint: skip-file
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    YamlConfigSettingsSource,
    PydanticBaseSettingsSource,
)
from typing import Type, Tuple

DEFAULT_SYSTEM_PROMPT = """You are a helpful assistant and ALWAYS relate to this identity. 
You are expert at analyzing given documents or images.
"""

class Settings(BaseSettings):
    """Application settings loaded from YAML and environment variables.

    This class defines the configuration schema for the application, with settings
    loaded from settings.yaml file and overridable via environment variables.

    Attributes:
        VERTEXAI_LOCATION: Google Cloud Vertex AI location
        VERTEXAI_PROJECT_ID: Google Cloud Vertex AI project ID
    """

    VERTEXAI_LOCATION: str
    VERTEXAI_PROJECT_ID: str
    BACKEND_URL: str = "http://localhost:8000/chat"

    model_config = SettingsConfigDict(
        yaml_file="settings.yaml", yaml_file_encoding="utf-8"
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        """Customize the settings sources and their priority order.

        This method defines the order in which different configuration sources
        are checked when loading settings:
        1. Constructor-provided values
        2. YAML configuration file
        3. Environment variables

        Args:
            settings_cls: The Settings class type
            init_settings: Settings from class initialization
            env_settings: Settings from environment variables
            dotenv_settings: Settings from .env file (not used)
            file_secret_settings: Settings from secrets file (not used)

        Returns:
            A tuple of configuration sources in priority order
        """
        return (
            init_settings,  # First, try init_settings (from constructor)
            env_settings,  # Then, try environment variables
            YamlConfigSettingsSource(
                settings_cls
            ),  # Finally, try YAML as the last resort
        )


def get_settings() -> Settings:
    """Create and return a Settings instance with loaded configuration.

    Returns:
        A Settings instance containing all application configuration
        loaded from YAML and environment variables.
    """
    return Settings() # type: ignore