"""Logging utilities with aggressive deduplication."""
import sys
import re
from collections import deque
from config import ENABLE_LOGS

# Simple in-memory log storage (last 1000 lines)
LOG_BUFFER = deque(maxlen=1000)

# Track asset batches
_asset_batch = {}  # {service: {filetype: count}}
_last_log_type = None


def _get_asset_info(msg):
    """Extract service and file type from log message."""
    # Match [PROXY] logs
    proxy_match = re.search(r'\[PROXY\] GET /([^/]+)/.*\.([a-z0-9]+)\s', msg)
    if proxy_match:
        return 'proxy', proxy_match.group(1), proxy_match.group(2)
    
    # Match [REWRITE] logs for assets
    if '[REWRITE] Processing' in msg:
        rewrite_match = re.search(r'https://[^/]+/.*\.([a-z0-9]+)$', msg)
        if rewrite_match:
            service_match = re.search(r'\[PROXY\] GET /([^/]+)/', _last_log_type or '')
            service = service_match.group(1) if service_match else 'unknown'
            return 'rewrite', service, rewrite_match.group(1)
    
    return None, None, None


def _is_asset_detail(msg):
    """Check if this is a REWRITE detail line we should suppress."""
    suppressable = [
        '[REWRITE]   Content-Type:',
        '[REWRITE]   Contains pathname reads:',
        '[REWRITE]   Contains API calls:',
        '[REWRITE]   No changes made',
        '[REWRITE]   ✓ Modified'
    ]
    return any(s in msg for s in suppressable)


def _flush_batch():
    """Flush accumulated asset batches."""
    global _asset_batch
    
    if not _asset_batch:
        return
    
    for service, types in _asset_batch.items():
        for filetype, count in types.items():
            if count > 1:
                summary = f"[ASSETS] {service}: {count}x {filetype}"
                sys.stdout.write(f"{summary}\n")
                sys.stdout.flush()
                
                if ENABLE_LOGS:
                    from datetime import datetime
                    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                    LOG_BUFFER.append(f"[{timestamp}] {summary}")
    
    _asset_batch.clear()


def log(msg):
    """Log with aggressive asset deduplication."""
    global _last_log_type, _asset_batch
    
    # Suppress REWRITE detail lines entirely
    if _is_asset_detail(msg):
        return
    
    log_type, service, filetype = _get_asset_info(msg)
    
    # Asset extensions to group
    asset_types = ['svg', 'css', 'js', 'woff', 'woff2', 'ttf', 'png', 'jpg', 'webp', 'ico']
    
    # If this is an asset log
    if log_type and filetype in asset_types:
        # Track it
        if service not in _asset_batch:
            _asset_batch[service] = {}
        if filetype not in _asset_batch[service]:
            _asset_batch[service][filetype] = 0
        _asset_batch[service][filetype] += 1
        
        _last_log_type = msg
        return
    
    # Not an asset - flush batch and log normally
    _flush_batch()
    _last_log_type = msg
    
    sys.stdout.write(f"{msg}\n")
    sys.stdout.flush()
    
    if ENABLE_LOGS:
        from datetime import datetime
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        LOG_BUFFER.append(f"[{timestamp}] {msg}")


def get_log_buffer():
    """Get the log buffer for display."""
    _flush_batch()
    return LOG_BUFFER