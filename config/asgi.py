"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path

# Consumers をインポート（notices アプリに作る前提）
from notices.consumers import PostConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_asgi_application()

# WebSocket のルーティング
websocket_urlpatterns = [
    path("ws/post/", PostConsumer.as_asgi()),
]

# ASGI アプリ全体
application = ProtocolTypeRouter({
    "http": django_app,                     # 通常の HTTP リクエスト
    "websocket": URLRouter(websocket_urlpatterns),  # WebSocket リクエスト
})