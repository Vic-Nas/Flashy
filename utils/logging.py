"""Logging utilities."""
import sys
import re
from collections import deque
from config import ENABLE_LOGS

# Simple in-memory log storage (last 1000 lines)
LOG_BUFFER = deque(maxlen=1000)

# Track recent similar requests for grouping
_pending_group = None
_group_count = 0


def _extract_asset_pattern(msg):
    """Extract service and asset type from proxy log."""
    # Match: [PROXY] GET /service/path/to/file.hash.ext -> ...
    match = re.search(r'\[PROXY\] GET /([^/]+)/.*\.([a-z0-9]+)$', msg)
    if match:
        service = match.group(1)
        ext = match.group(2)
        # Only group common static assets
        if ext in ['svg', 'css', 'js', 'png', 'jpg', 'woff', 'woff2', 'ttf', 'webp']:
            return f"{service}:{ext}"
    return None


def _flush_pending_group():
    """Flush pending grouped logs."""
    global _pending_group, _group_count
    
    if _pending_group and _group_count > 0:
        if _group_count == 1:
            # Just log the single message (already logged)
            pass
        else:
            # Log summary
            service, ext = _pending_group.split(':')
            summary = f"[PROXY] ... +{_group_count - 1} more {ext} files for /{service}/"
            sys.stdout.write(f"{summary}\n")
            sys.stdout.flush()
            
            if ENABLE_LOGS:
                from datetime import datetime
                timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                LOG_BUFFER.append(f"[{timestamp}] {summary}")
    
    _pending_group = None
    _group_count = 0


def log(msg):
    """Log to stdout with smart grouping for similar static asset requests."""
    global _pending_group, _group_count
    
    pattern = _extract_asset_pattern(msg)
    
    # If this is a groupable asset request
    if pattern:
        # Same pattern as pending group - increment count
        if pattern == _pending_group:
            _group_count += 1
            return
        
        # Different pattern - flush previous group and start new one
        _flush_pending_group()
        _pending_group = pattern
        _group_count = 1
        
        # Log first message of group
        sys.stdout.write(f"{msg}\n")
        sys.stdout.flush()
        
        if ENABLE_LOGS:
            from datetime import datetime
            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            LOG_BUFFER.append(f"[{timestamp}] {msg}")
        
        return
    
    # Not a groupable message - flush any pending group
    _flush_pending_group()
    
    # Log normally
    sys.stdout.write(f"{msg}\n")
    sys.stdout.flush()
    
    if ENABLE_LOGS:
        from datetime import datetime
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        LOG_BUFFER.append(f"[{timestamp}] {msg}")


def get_log_buffer():
    """Get the log buffer for display."""
    _flush_pending_group()  # Ensure any pending groups are flushed
    return LOG_BUFFER