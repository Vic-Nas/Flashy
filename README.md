# Path-Based Reverse Proxy

Route requests through URL paths instead of subdomains.

## Usage

`https://yourdomain.com/{service}/{path}` → `https://{service}.platform.com/{path}`

## Setup

1. Edit `config.py`:
   ```python
   TARGET_DOMAIN_PATTERN = "{service}.up.railway.app"
   ```

2. Deploy to Railway

3. Add custom domain in Railway settings

4. Update DNS with Railway's records

## Known Limitations

- **No WebSocket support** - WebSockets need a real reverse proxy (Nginx/Caddy)
- URL rewriting is basic - complex SPAs may need backend changes
- Backend must support being proxied

## Files

- `config.py` - Configure target domains
- `views.py` - Proxy logic
- `settings.py` - Django settings
- `urls.py` - URL routing
- `wsgi.py` - WSGI app
- `Dockerfile` - Container config