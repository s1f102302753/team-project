from django.urls import path
from .views import CustomLoginView, SignUpView
from django.contrib.auth import views as auth_views

app_name = 'users'

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('signup/', SignUpView.as_view(), name='signup'),

    # ログアウト用
    path('logout/', auth_views.LogoutView.as_view(next_page='/users/login/'), name='logout'),
]
