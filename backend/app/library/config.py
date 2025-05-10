"""
Config file for the application.
This file contains the configuration settings for the application, including API keys and other parameters.
"""
import tomllib
import os
CONFIG_FILE = "config.toml"
def load_config_tomllib():
    """Load the configuration file using tomllib."""
    if not os.path.exists(CONFIG_FILE):
        return None

    try:
        with open(CONFIG_FILE, "rb") as f:
            config = tomllib.load(f)
            return config
    except tomllib.TOMLDecodeError:
        return None
    except Exception:
        return None

def get_gemini_api_key() -> str:
    """Get the Gemini API key from the config file."""
    config = load_config_tomllib()
    return config["MODELS"]["GEMINI"]["API_KEY"]
    