from __future__ import annotations
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

# Schema cho dữ liệu client gửi lên khi tạo user
# Chỉ chứa các trường client cần cung cấp
class UserCreate(SQLModel):
    username: str
    email: str
    password: str # Client gửi mật khẩu dạng plain text
    
# Schema cho dữ liệu API trả về sau khi tạo user
# Kế thừa các trường từ UserModel nhưng không bao gồm mật khẩu
# và có thể thêm các trường khác nếu cần
class UserRead(SQLModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    updated_at: datetime