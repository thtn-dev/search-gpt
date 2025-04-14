import tomllib 
import os
CONFIG_FILE = "config.toml"
def load_config_tomllib():
    if not os.path.exists(CONFIG_FILE):
        print(f"Lỗi: Không tìm thấy file cấu hình '{CONFIG_FILE}'")
        return None

    try:
        with open(CONFIG_FILE, "rb") as f:
            config = tomllib.load(f)
            print("Đã tải cấu hình thành công bằng tomllib:")
            return config
    except tomllib.TOMLDecodeError as e:
        print(f"Lỗi: File cấu hình '{CONFIG_FILE}' không đúng định dạng TOML: {e}")
        return None
    except Exception as e:
        print(f"Lỗi không xác định khi đọc file cấu hình: {e}")
        return None

def get_gemini_api_key() -> str:
    """Get the Gemini API key from the config file."""
    config = load_config_tomllib()
    return config["gemini"]["api_key"]
    
