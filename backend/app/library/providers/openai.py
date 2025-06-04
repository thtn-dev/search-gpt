from typing import Dict, List
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, SecretStr

from app.config import settings
from app.library.providers.core import ChatModel


class OpenAIChatModel(BaseModel):
    displayName: str
    key: str
    
class OpenAIChatModels(BaseModel):
    models: List[OpenAIChatModel]

OPENAI_CHAT_MODELS = OpenAIChatModels(models=[
    OpenAIChatModel(displayName="GPT-4 omni", key="gpt-4o"),
    OpenAIChatModel(displayName="GPT-4 omni mini", key="gpt-4o-mini"),
    OpenAIChatModel(displayName="GPT o4 mini", key="o4-mini"),
    OpenAIChatModel(displayName="GPT 4.1", key="gpt-4.1"),
])

def load_openai_chat_models() -> Dict[str, ChatModel]:
    """
    Load OpenAI chat models from the predefined list.
    """
    openaiApiKey = settings.settings.OPENAI_API_KEY
    
    if not openaiApiKey:
        raise ValueError("OpenAI API key is not set.")
    if not isinstance(openaiApiKey, str):
        raise ValueError("OpenAI API key must be a string.")
    
    try:
        chat_models : Dict[str, ChatModel] = {}
        
        for model in OPENAI_CHAT_MODELS.models:
            if model.key in chat_models:
                raise ValueError(f"Duplicate model key found: {model.key}")
            chat_model = ChatModel(
                displayName=model.displayName,
                model=ChatOpenAI(
                    api_key=SecretStr(openaiApiKey),
                    temperature=0.7,
                    model=model.key,
                )
            )
            chat_models[model.key] = chat_model
        
        return chat_models
    except Exception as e:
        raise ValueError(f"Failed to load OpenAI chat models: {str(e)}") from e
    