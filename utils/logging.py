"""Logging utilities."""
import sys
from collections import deque
from config import ENABLE_LOGS

# Simple in-memory log storage (last 1000 lines)
LOG_BUFFER = deque(maxlen=1000)


def log(msg):
    """Log to stdout immediately and optionally store in buffer."""
    sys.stdout.write(f"{msg}\n")
    sys.stdout.flush()
    
    # Store in buffer if logs service is enabled
    if ENABLE_LOGS:
        from datetime import datetime
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        LOG_BUFFER.append(f"[{timestamp}] {msg}")


def get_log_buffer():
    """Get the log buffer for display."""
    return LOG_BUFFER
