# Create your views here.
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView

from .utils import fetch_notices_for_prefecture
# この 'Municipality' は notices.models.Municipality を指します
from .models import News, Post, Municipality 
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .utils import fetch_amami_detail

app_name = 'notices'

# ------------------------
# ▼▼▼ ヘルパー関数 (根本修正) ▼▼▼
# ------------------------
def _get_municipality_instance(request_user):
    """
    request.user.municipality が「どのアプリのオブジェクト」でも、
    あるいは「文字列」でも、最終的に「notices.models.Municipality」の
    オブジェクトを返すヘルパー関数
    """
    user_municipality_data = request_user.municipality
    
    pref_str = None
    name_str = None

    # Case 1: オブジェクトの場合 (users.models.Municipality など)
    if hasattr(user_municipality_data, 'prefecture') and hasattr(user_municipality_data, 'name'):
        pref_str = user_municipality_data.prefecture
        name_str = user_municipality_data.name
    
    # Case 2: 文字列 "都道府県名 市区町村名" の場合
    elif isinstance(user_municipality_data, str) and ' ' in user_municipality_data:
        try:
            pref_raw, name_raw = user_municipality_data.split(' ', 1)
            pref_str = pref_raw.strip()
            name_str = name_raw.strip()
        except ValueError:
            pass # 分割に失敗

    # pref_str と name_str が取得できた場合のみ、DBを検索
    if pref_str and name_str:
        # ▼▼▼ 修正箇所 ▼▼▼
        # get() ではなく get_or_create() を使うことで、
        # データが無い場合でも自動作成され、Noneにならずに済みます
        target_municipality, created = Municipality.objects.get_or_create(
            prefecture=pref_str,
            name=name_str
        )
        return target_municipality
        # ▲▲▲ 修正箇所 ▲▲▲

# ------------------------
# ホーム画面の表示
# ------------------------
class NoticeHomeView(TemplateView):
    template_name = 'notices/base.html'

# ------------------------
# (notices_list は前回修正済みなのでOK)
# ------------------------
from django.views.decorators.cache import never_cache

@never_cache
@login_required
def notices_list(request):
    """ユーザの都道府県に紐づくリアルタイムお知らせ"""
    
    user_municipality_data = request.user.municipality
    prefecture = None

    if hasattr(user_municipality_data, 'prefecture'):
        prefecture = user_municipality_data.prefecture
    
    elif isinstance(user_municipality_data, str):
        if ' ' in user_municipality_data:
            prefecture = user_municipality_data.split(' ', 1)[0].strip()
        else:
            prefecture = user_municipality_data.strip()
    
    if not prefecture:
        return render(request, 'notices/notices_list.html', {'notices': []})

    notices = fetch_notices_for_prefecture(prefecture)
    return render(request, 'notices/notices_list.html', {'notices': notices})

# ------------------------
# (post_list はヘルパー関数を呼ぶだけなので、変更不要)
# ------------------------
@login_required
def post_list(request):
    """掲示板投稿一覧（ユーザの自治体ごと）"""
    # 修正されたヘルパー関数を呼ぶ
    target_municipality = _get_municipality_instance(request.user)
    
    if target_municipality:
        posts = Post.objects.filter(municipality=target_municipality)
    else:
        posts = Post.objects.none() 
    return render(request, 'notices/post_list.html', {'posts': posts})

# ------------------------
# (post_create もヘルパー関数を呼ぶだけなので、変更不要)
# ------------------------
@login_required
def post_create(request):
    """掲示板投稿作成"""
    # 修正されたヘルパー関数を呼ぶ
    target_municipality = _get_municipality_instance(request.user)

    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        Post.objects.create(
            author=request.user,
            municipality=target_municipality,
            title=title,
            content=content
        )
        return redirect('notices:post_list')
    
    if not target_municipality:
        return redirect('notices:post_list')

    return render(request, 'notices/post_form.html')

# ------------------------
# (post_detail もヘルパー関数を呼ぶだけなので、変更不要)
# ------------------------
@login_required
def post_detail(request, pk):
    """掲示板投稿詳細"""
    target_municipality = _get_municipality_instance(request.user)
    post = get_object_or_404(Post, pk=pk, municipality=target_municipality)
    return render(request, 'notices/post_detail.html', {'post': post})

# ------------------------
# (api_notices もヘルパー関数を呼ぶだけなので、変更不要)
# ------------------------
@login_required
def api_notices(request):
    """API: ユーザの自治体ニュースをJSONで返す"""
    municipality = _get_municipality_instance(request.user)
    news_items = News.objects.filter(municipality=municipality)
    data = [
        {
            'id': n.id,
            'title': n.title,
            'content': n.content,
            'published_at': n.published_at.isoformat()
        }
        for n in news_items
    ]
    return JsonResponse(data, safe=False)

# ------------------------
# (api_posts もヘルパー関数を呼ぶだけなので、変更不要)
# ------------------------
@login_required
def api_posts(request):
    """API: ユーザの自治体掲示板投稿をJSONで返す"""
    municipality = _get_municipality_instance(request.user)
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

@login_required
def notice_detail(request):
    """
    外部サイトのお知らせ詳細をアプリ内で表示するビュー
    URLパラメータ 'url' で対象を指定する
    """
    target_url = request.GET.get('url')
    
    if not target_url:
        return redirect('notices:notices_list')
    
    # スクレイピング実行
    article_data = fetch_amami_detail(target_url)
    
    if not article_data:
        # 取得失敗や不正なURLの場合は元サイトへリダイレクト等の処理
        return redirect(target_url)

    return render(request, 'notices/notice_detail.html', {'article': article_data})

