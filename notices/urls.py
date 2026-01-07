print(">>> notices.urls LOADED")
from django.urls import path
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
    path("ws-test/", lambda request: render(request, "ws_test.html")),
]
