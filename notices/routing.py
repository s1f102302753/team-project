from django.urls import re_path
from .consumers import NoticeConsumer

websocket_urlpatterns = [
    re_path(r'ws/notices/$', NoticeConsumer.as_asgi()),
]