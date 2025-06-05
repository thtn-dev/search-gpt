from datetime import datetime, timezone  # Thêm 'timezone'


def utc_now():
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)
