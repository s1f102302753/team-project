from django.urls import path
from .views import NoticeHomeView, chat_with_pdf
from . import views

app_name = 'notices'

urlpatterns = [
    path('', NoticeHomeView.as_view(), name='home'),  # / にアクセスすると homeに遷移
    path("upload/", views.upload_pdf, name="upload_pdf"),
    path("chat_with_pdf/", chat_with_pdf, name="chat_with_pdf"),
    path('upload_pdf/', views.upload_pdf, name='upload_pdf'),
    
    path('list/', views.notices_list, name='notices_list'),
    path('posts/', views.post_list, name='post_list'),
    path('posts/new/', views.post_create, name='post_create'),
    path('posts/<int:pk>/', views.post_detail, name='post_detail'),
    path('api/notices/', views.api_notices, name='api_notices'),
]
