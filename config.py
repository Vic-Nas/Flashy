"""Simple configuration - load service mappings from environment."""
import os

# Load service mappings from environment variables
# Format: SERVICE_name=target.domain.com or SERVICE_name=target.domain.com/base/path
# Optional: SERVICE_name_DESC=description, SERVICE_name_RANK=number
SERVICES = {}
SERVICE_BASE_PATHS = {}
SERVICE_DESCRIPTIONS = {}
SERVICE_RANKS = {}

for key, value in os.environ.items():
    if key.startswith('SERVICE_') and not key.endswith('_DESC') and not key.endswith('_RANK'):
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
        
        # Load optional description
        desc_key = f'SERVICE_{service_name}_DESC'
        if desc_key in os.environ:
            SERVICE_DESCRIPTIONS[service_name] = os.environ[desc_key]
        
        # Load optional rank (default to 999 for unranked)
        rank_key = f'SERVICE_{service_name}_RANK'
        if rank_key in os.environ:
            try:
                SERVICE_RANKS[service_name] = int(os.environ[rank_key])
            except ValueError:
                SERVICE_RANKS[service_name] = 999
        else:
            SERVICE_RANKS[service_name] = 999

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
    SERVICE_RANKS['_logs'] = 999

BLOCKED_SERVICES = ['www', 'mail', 'ftp', 'ssh']