# Create your views here.
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView

from .utils import fetch_notices_for_user
from .models import Notice, Post
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

app_name = 'notices'

class NoticeHomeView(TemplateView):
    template_name = 'notices/home.html'


@login_required
def notices_list(request):
    notices = fetch_notices_for_user(request.user)
    return render(request, 'notices/notices_list.html', {'notices': notices})

@login_required
def post_list(request):
    posts = Post.objects.all().order_by('-created_at')  # ここは適宜フィルタ可能
    return render(request, 'notices/post_list.html', {'posts': posts})

@login_required
def post_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        Post.objects.create(author=request.user, title=title, content=content)
        return redirect('notices:post_list')
    return render(request, 'notices/post_form.html')

@login_required
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, 'notices/post_detail.html', {'post': post})



@login_required
def api_notices(request):
    notices = Notice.objects.filter(
        municipality=request.user.municipality
    ).order_by('-created_at')
    data = [
        {"id": n.id, "title": n.title, "content": n.content} for n in notices
    ]
    return JsonResponse(data, safe=False)

@login_required
def api_posts(request):
    posts = Post.objects.filter(
        author__municipality=request.user.municipality
    ).order_by('-created_at')
    data = [
        {"id": p.id, "title": p.title, "content": p.content} for p in posts
    ]
    return JsonResponse(data, safe=False)