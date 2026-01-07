<<<<<<< HEAD
print(">>> notices.urls LOADED")
from django.urls import path
=======
from django.urls import path          # ← ★これが必要
>>>>>>> a3f551c282b83d33684491832a7d9398c18eb97e
from .views import NoticeHomeView
from . import views
from django.shortcuts import render

app_name = 'notices'

urlpatterns = [
    path('', NoticeHomeView.as_view(), name='home'),
    path('list/', views.notices_list, name='notices_list'),
    path('posts/', views.post_list, name='post_list'),
    path('posts/new/', views.post_create, name='post_create'),
    path('posts/<int:pk>/', views.post_detail, name='post_detail'),
    path('api/notices/', views.api_notices, name='api_notices'),
<<<<<<< HEAD
    path("ws-test/", lambda request: render(request, "ws_test.html")),
]
=======

    # ws-test 用
    path('ws-test/', lambda request: render(request, 'notices/ws_test.html')),
]
>>>>>>> a3f551c282b83d33684491832a7d9398c18eb97e
