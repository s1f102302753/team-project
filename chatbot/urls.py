from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path("", views.chat_page, name="chat_page"),
    path("upload/", views.upload_pdf, name="upload_pdf"),
    path('api/', views.chat_api, name='chat_api'),
]
