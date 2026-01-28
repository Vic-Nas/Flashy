from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
import requests
import re
import gzip
import zlib
import sys
from config import SERVICES, TARGET_DOMAIN_PATTERN, BLOCKED_SERVICES


def log(msg):
    """Log to stdout immediately."""
    sys.stdout.write(f"{msg}\n")
    sys.stdout.flush()


def unknown_service_page(service):
    """Show friendly 404 page when service doesn't exist."""
    html = f"""<!DOCTYPE html>
<html>
<head>
  <title>Service Not Found</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px; margin: 50px auto; color: #666; background: #fafafa; }}
    .container {{ background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
    h1 {{ color: #ff6b6b; margin-top: 0; }}
    .service-name {{ font-family: monospace; color: #0066cc; font-size: 1.1em; }}
    a {{ color: #0066cc; text-decoration: none; }}
    .home-link {{ margin-top: 30px; }}
    .home-link a {{ display: inline-block; background: #0066cc; color: white; padding: 10px 20px; border-radius: 6px; text-decoration: none; }}
  </style>
</head>
<body>
<div class="container">
  <h1>⚠️ Service Not Found</h1>
  <p>The service <span class="service-name">{service}</span> doesn't exist.</p>
  <p>Make sure <code>SERVICE_{service}=your-domain.com</code> is set in your environment.</p>
  <div class="home-link"><a href="/">← Back to Home</a></div>
</div>
</body></html>"""
    return HttpResponse(html, status=404)


def home(request):
    """Show available services on homepage."""
    html = """<!DOCTYPE html>
<html>
<head>
  <title>Reverse Proxy</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px; margin: 50px auto; color: #333; }
    h1 { color: #0066cc; }
    .services { background: #f5f5f5; padding: 15px; border-radius: 8px; }
    .services ul { list-style: none; padding: 0; }
    .services li { padding: 8px 0; }
    .services a { color: #0066cc; text-decoration: none; }
  </style>
</head>
<body>
<h1>🔄 Proxy Active</h1>
<p>Usage: <code>/{service}/{path}</code></p>
"""
    if SERVICES:
        html += '<div class="services"><p>Services:</p><ul>'
        for service, domain in SERVICES.items():
            html += f'<li><a href="/{service}/">{service}</a> → {domain}</li>\n'
        html += "</ul></div>"
    
    html += "</body></html>"
    return HttpResponse(html)


@csrf_exempt
def proxy_view(request, service, path=''):
    """Main proxy logic - forwards requests to backend services."""
    
    # Block reserved service names
    if service in BLOCKED_SERVICES:
        return JsonResponse({'error': 'Blocked'}, status=403)
    
    # Get target domain from environment or use pattern
    if service in SERVICES:
        target_domain = SERVICES[service]
    else:
        target_domain = TARGET_DOMAIN_PATTERN.format(service=service)
        # Test if service exists
        try:
            test_resp = requests.get(f'https://{target_domain}/', timeout=5, allow_redirects=True)
            if test_resp.status_code == 404 or ('Railway' in test_resp.text and 'not found' in test_resp.text.lower()):
                return unknown_service_page(service)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.RequestException):
            return unknown_service_page(service)
    
    # Ensure trailing slash for service root
    if not path or path == '/':
        if not request.path.endswith('/'):
            return HttpResponseRedirect(f'/{service}/')
        path = ''
    
    # Build target URL
    url = f"https://{target_domain}/{path}"
    if request.META.get('QUERY_STRING'):
        url += f"?{request.META['QUERY_STRING']}"
    
    # Log main requests (skip assets)
    if not any(path.endswith(ext) for ext in ['.svg', '.ico', '.css', '.js', '.png', '.jpg', '.woff', '.woff2', '.ttf']):
        log(f"[PROXY] {request.method} /{service}/{path} → {url}")
    
    try:
        # Prepare headers
        headers = {}
        for k, v in request.headers.items():
            if k.lower() not in ['connection', 'host', 'accept-encoding']:
                headers[k] = v
        
        # Rewrite referer and origin to match target
        if 'Referer' in headers:
            headers['Referer'] = re.sub(rf'https?://[^/]+/{service}/', f'https://{target_domain}/', headers['Referer'])
        if 'Origin' in headers:
            headers['Origin'] = f'https://{target_domain}'
        
        headers['Host'] = target_domain
        headers['X-Forwarded-Host'] = request.get_host()
        headers['X-Forwarded-Proto'] = 'https' if request.is_secure() else 'http'
        
        cookies = {key: value for key, value in request.COOKIES.items()}
        
        # Make request to backend
        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=request.body,
            cookies=cookies,
            allow_redirects=False,
            timeout=30
        )
        
        # Decompress if needed
        content = resp.content
        encoding = resp.headers.get('content-encoding', '').lower()
        
        if encoding == 'gzip':
            try:
                content = gzip.decompress(content)
            except Exception as e:
                log(f"[WARNING] Gzip decompression failed: {e}")
        elif encoding == 'deflate':
            try:
                content = zlib.decompress(content)
            except Exception as e:
                log(f"[WARNING] Deflate decompression failed: {e}")
        
        content_type = resp.headers.get('content-type', '')
        
        # Rewrite text content (HTML, JS, JSON, CSS)
        is_text = any(x in content_type.lower() for x in ['text/', 'javascript', 'json'])
        
        if is_text:
            log(f"[REWRITE] Processing {url}")
            log(f"[REWRITE]   Content-Type: {content_type}")
            
            text_content = content.decode('utf-8', errors='ignore')
            original_len = len(text_content)
            
            # Track what we're rewriting
            has_pathname = 'window.location.pathname' in text_content or 'location.pathname' in text_content
            has_api = 'api.github.com' in text_content or 'api.' in text_content
            
            log(f"[REWRITE]   Contains pathname reads: {has_pathname}")
            log(f"[REWRITE]   Contains API calls: {has_api}")
            
            text_content = rewrite_content(text_content, service)
            
            if len(text_content) != original_len:
                log(f"[REWRITE]   ✓ Modified ({original_len} → {len(text_content)} bytes)")
            else:
                log(f"[REWRITE]   No changes made")
            
            response = HttpResponse(text_content, status=resp.status_code)
        else:
            response = HttpResponse(content, status=resp.status_code)
        
        # Copy headers from backend response
        for key, value in resp.headers.items():
            if key.lower() not in ['connection', 'transfer-encoding', 'content-encoding', 'content-length', 'set-cookie']:
                if key.lower() == 'location':
                    # Rewrite redirects to include service prefix
                    if f'/{service}/' not in value and f'/{service}' not in value:
                        if value.startswith(f'https://{target_domain}'):
                            path = value[len(f'https://{target_domain}'):]
                            value = f'/{service}{path or "/"}'
                        elif value.startswith('/'):
                            value = f'/{service}{value}'
                response[key] = value
        
        # Handle cookies
        if 'Set-Cookie' in resp.headers:
            for cookie in resp.raw.headers.getlist('Set-Cookie'):
                response['Set-Cookie'] = cookie
        
        return response
        
    except requests.exceptions.Timeout:
        return JsonResponse({'error': 'Backend timeout'}, status=504)
    except requests.exceptions.ConnectionError:
        return JsonResponse({'error': 'Cannot connect to backend'}, status=502)
    except Exception as e:
        log(f"[ERROR] {e}")
        return JsonResponse({'error': str(e)}, status=502)


def rewrite_content(content, service):
    """
    Rewrite URLs in HTML/JS/CSS to work behind the proxy.
    
    Key rewrites:
    1. window.location.pathname → strips /service/ prefix so apps see clean paths
    2. Relative URLs (/path) → adds /service/ prefix so they route through proxy
    """
    
    # Rewrite pathname reads to hide the /service/ prefix from JavaScript
    # This makes the proxy transparent - apps don't know they're behind a proxy
    pathname_count = content.count('window.location.pathname') + content.count('location.pathname')
    if pathname_count > 0:
        log(f"[REWRITE]   Found {pathname_count} pathname references, rewriting...")
    
    # Match window.location.pathname (but not document.location.pathname)
    content = re.sub(
        r'(?<!document\.)window\.location\.pathname\b',
        f'(window.location.pathname.replace(/^\\/{service}\\//, "/"))',
        content
    )
    # Match standalone location.pathname (but not window.location or document.location)
    content = re.sub(
        r'(?<!window\.)(?<!document\.)location\.pathname\b',
        f'(location.pathname.replace(/^\\/{service}\\//, "/"))',
        content
    )
    
    # Helper: check if URL is inside an absolute URL (don't rewrite those)
    def is_safe(match):
        start = max(0, match.start() - 20)
        end = min(len(content), match.end() + 20)
        context = content[start:end]
        return not any(x in context for x in ['://', '.com', '.io', '.org', '.net', 'api.'])
    
    # Rewrite helper: add /service/ prefix to relative URLs
    def rewrite(match, quote='"'):
        return match.group(1) + quote + f'/{service}' + match.group(2) + quote if is_safe(match) else match.group(0)
    
    # Rewrite href/src/action attributes (but not absolute URLs)
    content = re.sub(r'((?:href|src|action)=")(/[a-zA-Z][^"]*)"', lambda m: rewrite(m, '"'), content)
    content = re.sub(r"((?:href|src|action)=')(/[a-zA-Z][^']*)'", lambda m: rewrite(m, "'"), content)
    
    # Rewrite fetch() calls (but not absolute URLs)
    content = re.sub(r'(fetch\s*\(\s*")(/[a-zA-Z][^"]*)"', lambda m: rewrite(m, '"'), content)
    
    return content