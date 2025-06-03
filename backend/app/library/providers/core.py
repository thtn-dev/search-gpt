from pydantic import BaseModel
from langchain_core.language_models.chat_models import BaseChatModel

class ChatModel(BaseModel):
    displayName: str
    model: BaseChatModel