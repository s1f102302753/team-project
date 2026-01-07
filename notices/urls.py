from django.urls import path
from . import views

app_name = 'notices'

urlpatterns = [
    # ここを修正：name を 'notices_list' に設定する（これがホームになる）
    path('', views.notices_list, name='notices_list'),
    path('posts/', views.post_list, name='post_list'),
    path('posts/new/', views.post_create, name='post_create'),
    path('posts/<int:pk>/', views.post_detail, name='post_detail'),
    path('api/notices/', views.api_notices, name='api_notices'),
]
