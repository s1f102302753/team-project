from django.urls import path
from .views import notice_list, notice_detail

urlpatterns = [
    path('', notice_list, name='notice_list'),
    path('<int:pk>/', notice_detail, name='notice_detail'),
]
