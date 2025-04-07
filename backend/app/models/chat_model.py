from pydantic import BaseModel
from typing import List, Optional
from app.config.gemini_settings import DEFAULT_SYSTEM_PROMPT

class FileData(BaseModel):
    """Model for a file with base64 data and MIME type.

    Attributes:
        data: Base64 encoded string of the file content.
        mime_type: The MIME type of the file.
    """

    data: str
    mime_type: str


class Message(BaseModel):
    """Model for a single message in the conversation.

    Attributes:
        role: The role of the message sender, either 'user' or 'assistant'.
        content: The text content of the message or a list of file data objects.
    """

    role: str
    content: str | List[FileData]


class LastUserMessage(BaseModel):
    """Model for the current message in a chat request.

    Attributes:
        text: The text content of the message.
        files: List of file data objects containing base64 data and MIME type.
    """

    text: str
    files: List[FileData] = []


class ChatRequest(BaseModel):
    """Model for a chat request.

    Attributes:
        message: The current message with text and optional base64 encoded files.
        history: List of previous messages in the conversation.
        system_prompt: Optional system prompt to be used in the chat.
    """

    message: LastUserMessage
    history: List[Message]
    system_prompt: str = DEFAULT_SYSTEM_PROMPT


class ChatResponse(BaseModel):
    """Model for a chat response.

    Attributes:
        response: The text response from the model.
        error: Optional error message if something went wrong.
    """

    response: str
    error: Optional[str] = None