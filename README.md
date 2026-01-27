# Path-Based Reverse Proxy

Route multiple services through a single domain using URL paths instead of subdomains.

## Why Use This?

✨ **Single DNS record** - One domain, many services  
🚀 **Simple routing** - Path-based instead of subdomain-based  
🛡️ **Centralized proxy** - Manage all traffic in one place  
🎯 **Works anywhere** - Railway, VPS, Docker, anywhere Django runs

## 🎬 Demo

**Live at https://vicnas.me** - See it in action!
- Visit the home page to see available services
- Access any service via `/service-name/`

## Quick Start

### 1. Environment Setup

Create a `.env` file with your services:

```bash
SERVICE_api=api.example.com
SERVICE_app=myapp.example.com

SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
```

### 2. Deploy

**Easiest:** [Deploy to Railway](https://railway.com?referralCode=ZIdvo-) (includes free credits)

Or deploy anywhere Django runs (Docker, VPS, etc.)

### 3. Point DNS

One DNS record to your proxy:
```
yourdomain.com → your-proxy-server
```

Done! ✓

## Usage

Access your services via paths:
- `https://yourdomain.com/app/settings` → `https://myapp.example.com/settings`

Unknown services show a friendly "not found" page.

## Notes

- Each service is defined via `SERVICE_name=domain` env variables
- Content is automatically rewritten to work behind the proxy
- Supports HTML, JSON, CSS, JavaScript
- WebSockets are not supported