from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel


class ChatModel(BaseModel):
    displayName: str
    model: BaseChatModel
