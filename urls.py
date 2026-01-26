from django.urls import re_path
from views import proxy_view, home

urlpatterns = [
    re_path(r'^(?P<service>[^/]+)/(?P<path>.*)$', proxy_view),
    re_path(r'^$', home),
]