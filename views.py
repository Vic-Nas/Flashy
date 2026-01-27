from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import re
import json
from config import TARGET_DOMAIN_PATTERN, ALLOWED_SERVICES, BLOCKED_SERVICES


def home(request):
    """Simple status page."""
    html = """<!DOCTYPE html>
<html>
<head><title>Reverse Proxy</title></head>
<body style="font-family: sans-serif; max-width: 600px; margin: 50px auto;">
<h1>🔄 Proxy Active</h1>
<p>Usage: <code>/{service}/{path}</code></p>
</body>
</html>"""
    return HttpResponse(html)


@csrf_exempt
def proxy_view(request, service, path=''):
    """Proxy requests to backend services."""
    if BLOCKED_SERVICES and service in BLOCKED_SERVICES:
        return JsonResponse({'error': f'Blocked'}, status=403)
    
    if ALLOWED_SERVICES and service not in ALLOWED_SERVICES:
        return JsonResponse({'error': f'Not allowed'}, status=403)
    
    target_domain = TARGET_DOMAIN_PATTERN.format(service=service)
    url = f"https://{target_domain}/{path}"
    
    if request.META.get('QUERY_STRING'):
        url += f"?{request.META['QUERY_STRING']}"
    
    if not any(path.endswith(ext) for ext in ['.svg', '.ico', '.css', '.js', '.png', '.jpg']):
        print(f"[PROXY] {request.method} /{service}/{path}")
    
    try:
        headers = {}
        for k, v in request.headers.items():
            if k.lower() not in ['connection', 'host']:
                headers[k] = v
        
        if 'Referer' in headers:
            headers['Referer'] = re.sub(rf'https?://[^/]+/{service}/', f'https://{target_domain}/', headers['Referer'])
        
        if 'Origin' in headers:
            headers['Origin'] = f'https://{target_domain}'
        
        headers['Host'] = target_domain
        headers['X-Forwarded-Host'] = request.get_host()
        headers['X-Forwarded-Proto'] = 'https' if request.is_secure() else 'http'
        
        cookies = {key: value for key, value in request.COOKIES.items()}
        
        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=request.body,
            cookies=cookies,
            allow_redirects=False,
            timeout=30
        )
        
        content_type = resp.headers.get('content-type', '')
        
        if 'text/html' in content_type:
            content = resp.content.decode('utf-8', errors='ignore')
            content = rewrite_html(content, service)
            response = HttpResponse(content, status=resp.status_code)
        elif 'javascript' in content_type:
            content = resp.content.decode('utf-8', errors='ignore')
            content = rewrite_js(content, service)
            response = HttpResponse(content, status=resp.status_code)
        else:
            response = HttpResponse(resp.content, status=resp.status_code)
        
        for key, value in resp.headers.items():
            if key.lower() not in ['connection', 'transfer-encoding', 'content-encoding', 'content-length', 'set-cookie']:
                if key.lower() == 'location':
                    if value.startswith('/') and not value.startswith(f'/{service}/'):
                        value = f'/{service}{value}'
                response[key] = value
        
        if 'Set-Cookie' in resp.headers:
            for cookie in resp.raw.headers.getlist('Set-Cookie'):
                response['Set-Cookie'] = cookie
        
        return response
        
    except requests.exceptions.Timeout:
        return JsonResponse({'error': 'Timeout'}, status=504)
    except requests.exceptions.ConnectionError:
        return JsonResponse({'error': 'Connection failed'}, status=502)
    except Exception as e:
        print(f"[ERROR] {e}")
        return JsonResponse({'error': 'Proxy error'}, status=502)


def rewrite_html(content, service):
    """Rewrite HTML URLs."""
    # Fix absolute paths
    content = re.sub(
        r'(href|src|action)="(/(?!' + re.escape(service) + r'/)[^"]+)"',
        rf'\1="/{service}\2"',
        content
    )
    # Fix fetch calls
    content = re.sub(
        r'fetch\s*\(\s*["\'](/(?!' + re.escape(service) + r'/)[^"\']+)["\']',
        rf'fetch("/{service}\1"',
        content
    )
    # Fix window.location
    content = re.sub(
        r'window\.location\s*=\s*["\'](/(?!' + re.escape(service) + r'/)[^"\']+)["\']',
        rf'window.location="/{service}\1"',
        content
    )
    return content


def rewrite_js(content, service):
    """Rewrite JS URLs."""
    content = re.sub(
        r'fetch\s*\(\s*["\'](/(?!' + re.escape(service) + r'/)[^"\']+)["\']',
        rf'fetch("/{service}\1"',
        content
    )
    return content