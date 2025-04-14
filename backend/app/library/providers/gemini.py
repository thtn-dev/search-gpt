from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory
from pydantic import BaseModel
from typing import Dict, List
from langchain_core.language_models.chat_models import BaseChatModel
from app.library.config import get_gemini_api_key

class ChatModel(BaseModel):
    displayName: str
    model: BaseChatModel

class GeminiChatModel(BaseModel):
    displayName: str
    key: str

class GeminiChatModels(BaseModel):
    models: List[GeminiChatModel]
    
GEMINI_CHAT_MODELS = GeminiChatModels(models=[
    {"displayName": "Gemini 2.5 Pro Experimental", "key": "gemini-2.5-pro-exp-03-25"},
    {"displayName": "Gemini 2.0 Flash", "key": "gemini-2.0-flash"},
    {"displayName": "Gemini 2.0 Flash-Lite", "key": "gemini-2.0-flash-lite"},
    {"displayName": "Gemini 2.0 Flash Thinking Experimental", "key": "gemini-2.0-flash-thinking-exp-01-21"},
    {"displayName": "Gemini 1.5 Flash", "key": "gemini-1.5-flash"},
    {"displayName": "Gemini 1.5 Flash-8B", "key": "gemini-1.5-flash-8b"},
    {"displayName": "Gemini 1.5 Pro", "key": "gemini-1.5-pro"},
])

safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

def load_gemini_chat_models() -> Dict[str, ChatModel]:
    """
    Load Gemini chat models from the predefined list.
    """
    geminiApiKey = get_gemini_api_key()
    
    if not geminiApiKey:
        raise ValueError("Gemini API key is not set.")
    if not isinstance(geminiApiKey, str):
        raise ValueError("Gemini API key must be a string.")
    
    try:
        chat_models = Dict[str, BaseChatModel] = {}
        
        for model in GEMINI_CHAT_MODELS.models:
            if model.key in chat_models:
                raise ValueError(f"Duplicate model key found: {model.key}")
            
            chat_model = ChatModel(
                displayName=model.displayName,
                model=ChatGoogleGenerativeAI(
                    api_key=geminiApiKey,
                    model=model.key,
                    temperature=0.7,
                )
            )
            chat_models[model.key] = chat_model
        return chat_models
    except Exception as e:
        raise ValueError(f"Failed to load Gemini chat models: {e}")