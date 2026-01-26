from django.http import HttpResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
def proxy_view(request, service, path=''):
    # Build target URL
    logger.info(f"Proxying: /{service}/{path}")
    print(f"Proxying to: https://{service}.up.railway.app/{path}")
    url = f"https://{service}.up.railway.app/{path}"
    
    # Forward request
    try:
        resp = requests.request(
            method=request.method,
            url=url,
            headers={
                **{k: v for k, v in request.headers.items() 
                if k.lower() not in ['connection']},
                'Host': f'{service}.up.railway.app',  # Keep original host
                'X-Forwarded-Host': request.get_host(),
                'X-Forwarded-Proto': 'https' if request.is_secure() else 'http',
            },
            data=request.body,
            cookies=request.COOKIES,
            allow_redirects=False,
            stream=True
        )
        
        # Build response
        response = StreamingHttpResponse(
            resp.iter_content(chunk_size=8192),
            status=resp.status_code
        )
        
        # Copy headers
        for key, value in resp.headers.items():
            if key.lower() not in ['connection', 'transfer-encoding']:
                # In the Location header rewriting part, replace with:
                if key.lower() == 'location':
                    # Rewrite redirects
                    if value.startswith('/'):
                        value = f'/{service}{value}'
                    elif value.startswith(f'https://{service}.up.railway.app/'):
                        value = value.replace(f'https://{service}.up.railway.app/', f'/{service}/')
                    elif f'{service}.up.railway.app' in value:
                        # Catch any other absolute URLs from the service
                        value = value.replace(f'{service}.up.railway.app', request.get_host())
                        value = value.replace(f'https://{request.get_host()}/', f'http://{request.get_host()}/{service}/')
        
        return response
        
    except requests.RequestException as e:
        return HttpResponse(f"Proxy error: {str(e)}", status=502)

def home(request):
    return HttpResponse("Proxy is running")