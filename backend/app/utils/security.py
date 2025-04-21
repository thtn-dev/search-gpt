# Sử dụng passlib
from passlib.context import CryptContext

# Tạo context cho password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Mã hóa mật khẩu sử dụng bcrypt
    
    Args:
        password: Mật khẩu dạng plain text
        
    Returns:
        Chuỗi mật khẩu đã được hash
    """
    return pwd_context.hash(password)

# Hàm xác thực mật khẩu
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Xác thực mật khẩu
    
    Args:
        plain_password: Mật khẩu dạng plain text cần kiểm tra
        hashed_password: Mật khẩu đã hash từ database
        
    Returns:
        True nếu mật khẩu đúng, False nếu sai
    """
    return pwd_context.verify(plain_password, hashed_password)