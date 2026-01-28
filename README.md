# Path-Based Reverse Proxy

Route multiple services through a single domain using URL paths instead of subdomains.

## Why?

✨ **One DNS record** - One domain, many services  
🚀 **Path routing** - `yourdomain.com/app/` instead of `app.yourdomain.com`  
🛡️ **Transparent** - JavaScript apps work without modification  
🎨 **Clean error pages** - Friendly 404s with optional coffee button

## Quick Start

```bash
# 1. Set your services
SERVICE_dev=vicnasdev.github.io
SERVICE_api=api.example.com
SECRET_KEY=your-secret-key

# 2. Deploy to Railway (includes free credits)
```
[Deploy to Railway](https://railway.com?referralCode=ZIdvo-)

```bash
# 3. Point DNS: yourdomain.com → your-proxy
```

**Usage:** `yourdomain.com/dev/` → `vicnasdev.github.io/`

## How It Works

The proxy rewrites content to be transparent:
- **JavaScript** - `window.location.pathname` sees clean paths (no `/service/` prefix)
- **Links/Assets** - Relative URLs get `/service/` prefix to route through proxy
- **API calls** - Absolute URLs left untouched
- **Base tags** - Automatically rewritten to include service prefix

## Features

### Smart URL Rewriting
- Handles `href`, `src`, `action` attributes
- Rewrites `fetch()` calls and location assignments
- Preserves absolute URLs (APIs, external resources)
- Respects `<base>` tags

### Better Error Handling
- **Service not found** - Clear message with setup instructions
- **Backend errors** - Detailed error pages for timeouts, connection issues
- **404 detection** - Catches GitHub 404s, Railway errors, and backend 404s
- **Optional coffee button** - Support link on error pages

### Debug Mode
Set `DEBUG=true` to:
- Disable caching for easier testing
- See detailed rewrite logs
- Get more verbose error messages

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_*` | - | Service mappings (e.g., `SERVICE_dev=example.com`) |
| `SECRET_KEY` | `change-me-in-production` | Django secret key |
| `DEBUG` | `false` | Enable debug mode (disables caching, verbose logs) |
| `LOGS` | `false` | Enable `/_logs/` service to view recent logs |
| `ALLOWED_HOSTS` | `*` | Comma-separated list of allowed hosts |
| `COFFEE_USERNAME` | `vicnas` | Buy Me a Coffee username |
| `COFFEE` | `true` | Show coffee button on error pages |

## Troubleshooting

- **Not working?** Hard refresh (Ctrl+Shift+R) to clear cache
- **Debugging?** Set `DEBUG=true` to disable caching and see detailed logs
- **Still broken?** Check the logs for `[REWRITE]` messages to see what's being changed

## Contributing

Keep it **light**, **clear**, and **general**. PRs welcome!

### Testing
```bash
# Run tests before submitting PRs
python test_proxy.py
```

See [TESTING.md](TESTING.md) for details.

**Live demo:** https://vicnas.me