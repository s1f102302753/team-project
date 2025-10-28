# Create your views here.
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView

from .utils import fetch_notices_for_prefecture
from .models import News, Post
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

app_name = 'notices'

# ホーム画面の表示
class NoticeHomeView(TemplateView):
    template_name = 'notices/base.html'

# お知らせ一覧の表示
@login_required
def notices_list(request):
    """ユーザの自治体に紐づくニュース一覧"""
    municipality = request.user.municipality
    news_items = News.objects.filter(municipality=municipality)
    return render(request, 'notices/notices_list.html', {'news_items': news_items})


@login_required
def post_list(request):
    """掲示板投稿一覧（ユーザの自治体ごと）"""
    municipality = request.user.municipality
    posts = Post.objects.filter(municipality=municipality)
    return render(request, 'notices/post_list.html', {'posts': posts})


@login_required
def post_create(request):
    """掲示板投稿作成"""
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        Post.objects.create(
            author=request.user,
            municipality=request.user.municipality,
            title=title,
            content=content
        )
        return redirect('notices:post_list')
    return render(request, 'notices/post_form.html')


@login_required
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk, municipality=request.user.municipality)
    return render(request, 'notices/post_detail.html', {'post': post})


@login_required
def api_notices(request):
    """API: ユーザの自治体ニュースをJSONで返す"""
    municipality = request.user.municipality
    news_items = News.objects.filter(municipality=municipality)
    data = [
        {
            'id': n.id,
            'title': n.title,
            'content': n.content,
            'summary': n.summary,
            'published_at': n.published_at.isoformat()
        }
        for n in news_items
    ]
    return JsonResponse(data, safe=False)


@login_required
def api_posts(request):
    """API: ユーザの自治体掲示板投稿をJSONで返す"""
    municipality = request.user.municipality
    posts = Post.objects.filter(municipality=municipality)
    data = [
        {
            'id': p.id,
            'title': p.title,
            'content': p.content,
            'author': p.author.username,
            'created_at': p.created_at.isoformat()
        }
        for p in posts
    ]
    return JsonResponse(data, safe=False)