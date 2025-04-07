import base64
from typing import List
from google.genai.types import Content, Part
from app.models.chat_model import Message, FileData

def handle_multimodal_data(file_data: FileData) -> Part:
    """Converts Multimodal data to a Google Gemini Part object.

    Args:
        file_data: FileData object with base64 data and MIME type.

    Returns:
        Part: A Google Gemini Part object containing the file data.
    """
    data = base64.b64decode(file_data.data)  # decode base64 string to bytes
    return Part.from_bytes(data=data, mime_type=file_data.mime_type)

def format_message_history_to_gemini_standard(
    message_history: List[Message],
) -> List[Content]:
    """Converts message history format to Google Gemini Content format.

    Args:
        message_history: List of message objects from the chat history.
            Each message contains 'role' and 'content' attributes.

    Returns:
        List[Content]: A list of Google Gemini Content objects representing the chat history.

    Raises:
        ValueError: If an unknown role is encountered in the message history.
    """
    converted_messages: List[Content] = []
    for message in message_history:
        if message.role == "assistant":
            converted_messages.append(
                Content(role="model", parts=[Part.from_text(text=message.content)])
            )
        elif message.role == "user":
            # Text-only messages
            if isinstance(message.content, str):
                converted_messages.append(
                    Content(role="user", parts=[Part.from_text(text=message.content)])
                )

            # Messages with files
            elif isinstance(message.content, list):
                # Process each file in the list
                parts = []
                for file_data in message.content:
                    parts.append(handle_multimodal_data(file_data))

                # Add the parts to a Content object
                if parts:
                    converted_messages.append(Content(role="user", parts=parts))

            else:
                raise ValueError(f"Unexpected content format: {type(message.content)}")

        else:
            raise ValueError(f"Unknown role: {message.role}")

    return converted_messages