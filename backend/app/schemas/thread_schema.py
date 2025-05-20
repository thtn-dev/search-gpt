from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator


class ThreadResponse(BaseModel):
    id: int
    title: str
    content: str
    
class ThreadsResponse(BaseModel):
    threads: list[ThreadResponse]
    

class CreateThreadRequestSchema(BaseModel):
    last_message_at: datetime
    
class CreateThreadResponseSchema(BaseModel):
    """
    Schema Pydantic cho phản hồi tạo chủ đề.
    """
    thread_id: str
    
class Usage(BaseModel):
    promptTokens: Optional[int] = None
    completionTokens: Optional[int] = None

class Step(BaseModel):
    state: Optional[str] = None
    messageId: Optional[str] = None
    finishReason: Optional[str] = None
    isContinued: bool = False
    usage: Optional[Usage] = None

class ContentMetadata(BaseModel):
    unstable_annotations: List[Any] | None = None
    unstable_data: List[Any] | None = None
    steps: List[Step] | None = None
    custom: Dict[str, Any] | None = None

class ContentStatus(BaseModel):
    type: str | None = None
    reason: str | None = None

class ContentItem(BaseModel):
    """
    Đại diện cho một mục nội dung, ví dụ như một đoạn văn bản.
    """
    type: str
    text: str

# Định nghĩa schema cho đối tượng content (giữ nguyên)
class Content(BaseModel):
    """
    Chứa thông tin về vai trò và nội dung chính của request.
    """
    role: str
    content: List[ContentItem]
    metadata: Optional[ContentMetadata] = None
    status: Optional[ContentStatus] = None

# Định nghĩa schema chính cho toàn bộ request (CẬP NHẬT TRƯỜNG METADATA)
class RequestCreateMessageSchema(BaseModel):
    """
    Schema Pydantic chính cho cấu trúc request đầu vào.
    Trường 'metadata' giờ đây hoàn toàn động.
    """
    parent_id: Optional[str] = None
    format: str
    content: Content
    # metadata giờ là một dictionary động, chấp nhận bất kỳ key-value nào
    
class ResponseCreateMessageSchema(BaseModel):
    """
    Schema Pydantic cho cấu trúc response đầu ra.
    """
    message_id: str
    
    

class ContentItemStatus(BaseModel):
    """ Trạng thái của một mục nội dung (thường trong tin nhắn của assistant). """
    type: str  # Loại trạng thái, ví dụ: "complete"
    reason: str # Lý do, ví dụ: "unknown"

class Usage(BaseModel):
    """ Thông tin về số lượng token đã sử dụng. """
    promptTokens: Optional[int] = Field(None, alias="promptTokens") # Số token của prompt (có thể là null)
    completionTokens: Optional[int] = Field(None, alias="completionTokens") # Số token của completion (có thể là null)

class Step(BaseModel):
    """ Một bước xử lý trong metadata của tin nhắn assistant. """
    state: str  # Trạng thái của bước, ví dụ: "finished"
    messageId: str = Field(..., alias="messageId") # ID của tin nhắn liên quan
    finishReason: str = Field(..., alias="finishReason") # Lý do kết thúc, ví dụ: "stop"
    usage: Usage  # Thông tin sử dụng token cho bước này
    isContinued: bool = Field(..., alias="isContinued") # Bước này có được tiếp tục không

class MessageStatus(BaseModel):
    """ Trạng thái tổng thể của tin nhắn assistant. """
    type: str  # Loại trạng thái, ví dụ: "complete"
    reason: str # Lý do, ví dụ: "stop"

# ------------ Model cho Nội dung Tin nhắn (Content Item) ------------

class BaseContentItem(BaseModel):
    """ Model cơ sở cho một mục nội dung trong tin nhắn. """
    type: str # Xác định loại nội dung (ví dụ: "text")

class TextContentItem(BaseContentItem):
    """ Nội dung dạng văn bản. """
    type: Literal["text"] = "text" # Loại cố định là "text"
    text: str # Nội dung văn bản
    # Trạng thái có thể có trong mục nội dung của assistant
    status: Optional[ContentItemStatus] = None

# Union để có thể mở rộng các loại nội dung khác trong tương lai (vd: image)
# Hiện tại, ví dụ chỉ có loại "text"
ContentType = Union[TextContentItem]

# ------------ Model cho Metadata của Tin nhắn ------------

class MessageMetadata(BaseModel):
    """ Siêu dữ liệu (metadata) cho một tin nhắn. """
    custom: Dict[str, Any] = Field(default_factory=dict) # Metadata tùy chỉnh, động
    # Các trường thường có trong metadata của assistant (không bắt buộc)
    unstable_annotations: Optional[List[Any]] = Field(None, alias="unstable_annotations")
    unstable_data: Optional[List[Any]] = Field(None, alias="unstable_data")
    steps: Optional[List[Step]] = None # Danh sách các bước xử lý

# ------------ Model cho Tin nhắn (Sử dụng Discriminated Union) ------------

class BaseMessage(BaseModel):
    """ Model cơ sở cho một tin nhắn trong luồng. """
    id: str # ID định danh tin nhắn
    createdAt: datetime = Field(..., alias="createdAt") # Thời gian tạo tin nhắn
    role: str # Vai trò (user hoặc assistant) - dùng làm discriminator
    metadata: MessageMetadata # Siêu dữ liệu của tin nhắn

    # Validator để chuyển đổi chuỗi ISO 8601 thành đối tượng datetime
    @field_validator('createdAt', mode='before')
    @classmethod
    def parse_datetime(cls, value):
        if isinstance(value, str):
            try:
                # Pydantic thường tự xử lý ISO 8601, nhưng thêm bước chuẩn hóa 'Z'
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError(f"Định dạng datetime không hợp lệ: {value}")
        return value # Trả về nếu đã là datetime

class UserMessage(BaseMessage):
    """ Tin nhắn từ người dùng. """
    role: Literal["user"] = "user" # Vai trò cố định là "user"
    content: List[ContentType] # Danh sách nội dung (ví dụ: TextContentItem)
    # Danh sách tệp đính kèm (kiểu dữ liệu bất kỳ trong list)
    attachments: List[Any] = Field(default_factory=list)
    # Tin nhắn user không có status ở cấp độ này trong ví dụ
    status: None = None # Thêm để nhất quán kiểu dữ liệu, nhưng giá trị luôn là None

class AssistantMessage(BaseMessage):
    """ Tin nhắn từ trợ lý ảo (assistant). """
    role: Literal["assistant"] = "assistant" # Vai trò cố định là "assistant"
    content: List[ContentType] # Danh sách nội dung (TextContentItem có thể chứa status)
    status: MessageStatus # Trạng thái tổng thể của tin nhắn assistant
    # Tin nhắn assistant không có attachments trong ví dụ
    attachments: None = None # Thêm để nhất quán

# ------------ Schema Tổng thể cho Luồng Hội thoại ------------

class ThreadSchema(BaseModel):
    """ Schema Pydantic chính cho toàn bộ cấu trúc luồng hội thoại. """
    thread_id: str = Field(..., alias="thread_id") # ID của luồng
    assistant_id: str = Field(..., alias="assistant_id") # ID của assistant
    # Danh sách các tin nhắn, sử dụng discriminated union dựa trên trường 'role'
    messages: List[Union[UserMessage, AssistantMessage]]