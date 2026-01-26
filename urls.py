from django.urls import path, re_path
from django.http import HttpResponse
from views import proxy_view, home

urlpatterns = [
    path('favicon.ico', lambda r: HttpResponse(status=204)),  # Return empty
    re_path(r'^(?P<service>[^/\.]+)/(?P<path>.*)$', proxy_view),  # Exclude dots in service name
    path('', home),
]