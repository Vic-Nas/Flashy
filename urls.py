from django.http import HttpResponse, HttpResponseNotFound
from django.urls import re_path
from views import proxy_view, home

def not_found(request):
    return HttpResponseNotFound("Not found")

urlpatterns = [
    re_path(r'^(favicon\.ico|robots\.txt)$', not_found),  # Block common bot files
    re_path(r'^(?P<service>[^/]+)/(?P<path>.*)$', proxy_view),
    re_path(r'^$', home),
]