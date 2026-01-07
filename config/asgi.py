"""
ASGI config for config project.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path

from notices.consumers import PostConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Django の ASGI アプリ
django_asgi_app = get_asgi_application()

# WebSocket のルーティング
websocket_urlpatterns = [
    path("ws/post/", PostConsumer.as_asgi()),
]

# ASGI 全体
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})