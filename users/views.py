from django.shortcuts import render

# Create your views here.

# トップページ用のビュー（ログイン画面）
def index(request):
    return render(request, 'users/index.html')

