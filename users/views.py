from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import CustomLoginForm
from django.urls import reverse_lazy
from .forms import CustomLoginForm
from django.contrib.auth.views import LoginView

# Create your views here.

# トップページ用のビュー（ログイン画面）
def index(request):
    return render(request, 'users/index.html')



class CustomLoginView(LoginView):
    template_name = 'users/login.html'  # ログインフォームのテンプレート
    def get_success_url(self):
        # ログイン成功後に回覧板ページへ
        return reverse_lazy('notices:home')  # noticesアプリの home にリダイレクト