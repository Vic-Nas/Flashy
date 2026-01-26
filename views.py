from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import re

@csrf_exempt
def proxy_view(request, service, path=''):
    url = f"https://{service}.up.railway.app/{path}"
    
    print(f"Proxying to: {url}")
    
    try:
        # Prepare cookies - rewrite domain
        cookies = {}
        for key, value in request.COOKIES.items():
            cookies[key] = value
        
        resp = requests.request(
            method=request.method,
            url=url,
            headers={
                **{k: v for k, v in request.headers.items() 
                   if k.lower() not in ['connection', 'cookie']},
                'Host': f'{service}.up.railway.app',
                'X-Forwarded-Host': request.get_host(),
                'X-Forwarded-Proto': 'https' if request.is_secure() else 'http',
                'Referer': f'https://{service}.up.railway.app/{path}',
                'Origin': f'https://{service}.up.railway.app',
            },
            data=request.body,
            cookies=cookies,
            allow_redirects=False
        )
        
        content_type = resp.headers.get('content-type', '')
        
        # For HTML, rewrite paths
        if 'text/html' in content_type:
            content = resp.content.decode('utf-8', errors='ignore')
            content = re.sub(r'(href|src|action)="(/[^"]*)"', rf'\1="/{service}\2"', content)
            content = re.sub(r"(href|src|action)='(/[^']*)'", rf"\1='/{service}\2'", content)
            response = HttpResponse(content, status=resp.status_code)
        else:
            response = HttpResponse(resp.content, status=resp.status_code)
        
        # Copy headers and rewrite Set-Cookie
        for key, value in resp.headers.items():
            if key.lower() not in ['connection', 'transfer-encoding', 'content-encoding', 'content-length']:
                if key.lower() == 'location':
                    if value.startswith('/'):
                        value = f'/{service}{value}'
                    elif value.startswith(f'https://{service}.up.railway.app/'):
                        value = value.replace(f'https://{service}.up.railway.app/', f'/{service}/')
                elif key.lower() == 'set-cookie':
                    # Rewrite cookie domain
                    value = value.replace(f'Domain={service}.up.railway.app', f'Domain={request.get_host()}')
                    value = value.replace(f'domain={service}.up.railway.app', f'domain={request.get_host()}')
                response[key] = value
        
        return response
        
    except Exception as e:
        print(f"Proxy error: {e}")
        return HttpResponse(f"Proxy error: {str(e)}", status=502)

def home(request):
    return HttpResponse("Proxy is running")