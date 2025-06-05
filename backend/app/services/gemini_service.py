# pylint: skip-file
from typing import Generator, List

from google import genai
from google.genai.types import Part

from app.models.chat_model import ChatRequest
from app.utils.gemini_formatters import (
    format_message_history_to_gemini_standard,
    handle_multimodal_data,
)

# Initialize Google Gemini client
client = genai.Client(api_key='AIzaSyBv6bRVr5iSwXUOnAWeG_pAq-6fkSgdtno')


class GeminiService:
    """Service for interacting with Google Gemini models."""

    @staticmethod
    def prepare_chat_model(request: ChatRequest):
        """Prepare a chat model instance with history and system prompt."""
        converted_messages = format_message_history_to_gemini_standard(request.history)

        chat_model = client.chats.create(
            model='gemini-2.0-flash',
            history=converted_messages,
            config={'system_instruction': request.system_prompt}
            if request.system_prompt
            else {},
        )
        return chat_model

    @staticmethod
    def prepare_content_parts(request: ChatRequest) -> List[Part]:
        """Prepare content parts from request including text and files."""
        content_parts = []

        # Handle any base64 encoded files in the current message
        if request.message.files:
            for file_data in request.message.files:
                content_parts.append(handle_multimodal_data(file_data))

        # Add text content if provided
        if request.message.text:
            content_parts.append(Part.from_text(text=request.message.text))

        return content_parts

    @classmethod
    async def generate_chat_response(cls, request: ChatRequest) -> str:
        """Generate a complete chat response from the Gemini model."""
        chat_model = cls.prepare_chat_model(request)
        content_parts = cls.prepare_content_parts(request)

        # Send message to Gemini
        response = chat_model.send_message(content_parts)
        return response.text

    @classmethod
    def generate_streaming_response(
        cls, request: ChatRequest
    ) -> Generator[str, None, None]:
        """Generate a streaming chat response from the Gemini model."""
        chat_model = cls.prepare_chat_model(request)
        content_parts = cls.prepare_content_parts(request)

        # Send message to Gemini with streaming
        response_stream = chat_model.send_message_stream(content_parts)

        for part in response_stream:
            if part.text:
                yield f'0:"{part.text}"\n'
