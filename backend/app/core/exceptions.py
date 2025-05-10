from fastapi import HTTPException, status, Request
from typing import Dict, Any
from functools import wraps
class GeminiAPIException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gemini API error: {detail}"
        )

class BadRequestException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

def handle_gemini_exceptions(func):
    """Decorator to handle exceptions from Google Gemini API."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            raise GeminiAPIException(str(e)) from e
    return wrapper

async def gemini_exception_handler(request: Request):
    """Dependency để xử lý exception từ Gemini API."""
    # Không làm gì ở đây, chỉ setup exception handler
    try:
        yield
    except Exception as e:
        raise GeminiAPIException(str(e)) from e
