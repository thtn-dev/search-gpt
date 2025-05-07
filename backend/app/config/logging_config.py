"""Cấu hình logging cho ứng dụng."""
import logging.config
from pathlib import Path

LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        # Formatter MẶC ĐỊNH của Uvicorn (có màu cho level)
        "uvicorn_default": {
            "()": "uvicorn.logging.DefaultFormatter", # Sử dụng lớp của uvicorn
            "fmt": "%(levelprefix)s %(asctime)s - %(name)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "use_colors": None, # Để Uvicorn tự động phát hiện TTY
        },
        # Formatter ACCESS của Uvicorn (có màu cho status code)
        "uvicorn_access": {
            "()": "uvicorn.logging.AccessFormatter", # Sử dụng lớp của uvicorn
            "fmt": '%(levelprefix)s %(asctime)s - %(client_addr)s - "%(request_line)s" %(status_code)s', # Format chuẩn của access log
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "use_colors": None,
        },
        "file_default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "uvicorn_default", # <-- DÙNG FORMATTER CÓ MÀU
            "level": "INFO",
            "stream": "ext://sys.stdout",
        },
        "console_access": { # Handler riêng cho access log ra console
            "class": "logging.StreamHandler",
            "formatter": "uvicorn_access", # <-- DÙNG FORMATTER ACCESS CÓ MÀU
            "level": "INFO",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "formatter": "file_default",
            "filename": LOGS_DIR / "app.log",
            "when": "midnight",
            "backupCount": 7,
            "encoding": "utf-8",
            "level": "DEBUG",
            "delay": True,
        },
    },
    "loggers": {
        "root": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
        },
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        "uvicorn.error": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        "uvicorn.access": {
            "level": "INFO",
            "handlers": ["console_access", "file"],
            "propagate": False,
        },
        "watchfiles": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}

def setup_logging():
    """Thiết lập cấu hình logging từ dictionary."""
    logging.config.dictConfig(LOGGING_CONFIG)
