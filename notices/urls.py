from django.urls import path
from .views import NoticeHomeView
from . import views

app_name = 'notices'

urlpatterns = [
    path('', NoticeHomeView.as_view(), name='home'),  # / にアクセスすると homeに遷移

]
