"""Simple configuration - load service mappings from environment."""
import os

# Load service mappings from environment variables
# Format: SERVICE_name=target.domain.com or SERVICE_name=target.domain.com/base/path
SERVICES = {}
SERVICE_BASE_PATHS = {}

for key, value in os.environ.items():
    if key.startswith('SERVICE_'):
        service_name = key.replace('SERVICE_', '')
        # Skip duplicates (take first occurrence)
        if service_name in SERVICES:
            print(f"[WARNING] Duplicate service '{service_name}' ignored (keeping first: {SERVICES[service_name]})")
            continue
        
        # Split domain and base path
        if '/' in value:
            parts = value.split('/', 1)
            SERVICES[service_name] = parts[0]
            SERVICE_BASE_PATHS[service_name] = '/' + parts[1]
        else:
            SERVICES[service_name] = value
            SERVICE_BASE_PATHS[service_name] = ''

SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-in-production')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

# Coffee button settings
COFFEE_USERNAME = os.environ.get('COFFEE_USERNAME', 'vicnas')
SHOW_COFFEE = os.environ.get('COFFEE', 'true').lower() == 'true'

# Feature flags
SHOW_FIXES = os.environ.get('FIXES', 'false').lower() == 'true'

# Logs service - if LOGS=true, adds a /_logs/ service
ENABLE_LOGS = os.environ.get('LOGS', 'false').lower() == 'true'
if ENABLE_LOGS:
    SERVICES['_logs'] = 'internal-logs'
    SERVICE_BASE_PATHS['_logs'] = ''

BLOCKED_SERVICES = ['www', 'mail', 'ftp', 'ssh']