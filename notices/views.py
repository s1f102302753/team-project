# Create your views here.
from django.conf import settings
from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView
from .models import Notice, Post, UploadedPDF
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .utils import learn_pdf, query_pdf
from sklearn.feature_extraction.text import TfidfVectorizer
from openai import OpenAI
import os
from django.core.files.storage import FileSystemStorage
import json
from PyPDF2 import PdfReader
import numpy as np
import fitz  # PyMuPDF
import glob
import faiss
import openai
from pdf2image import convert_from_path
import pytesseract
import google.generativeai as genai

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
    """ユーザの都道府県に紐づくリアルタイムお知らせ"""
    municipality = request.user.municipality

    # 都道府県情報を持っていない場合
    if not municipality or not municipality.prefecture:
        return render(request, 'notices/notices_list.html', {'notices': []})

    prefecture = municipality.prefecture

    # utils.py の関数を使用
    notices = fetch_notices_for_prefecture(prefecture)

    return render(request, 'notices/notices_list.html', {'notices': notices})


pdf_dir = settings.PDF_DIR
os.makedirs(pdf_dir, exist_ok=True)

@login_required
def notices_list(request):
    notices = fetch_notices_for_user(request.user)
    return  render(request, 'notices/notices_list.html', {'notices': notices})

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

openai.api_key = settings.OPENAI_API_KEY

PDF_TEXTS = []  # PDFテキスト保存用
VECTORS = None  # FAISSベクトル保存用
VECTOR_TEXT_MAP = []  # テキストとベクトルの対応
VECTORIZER = None



class NoticeHomeView(View):
    def get(self, request):
        notices = Notice.objects.all()
        return render(request, "notices/home.html", {"notices": notices})
    


def extract_text_from_pdf(pdf_path):
    """PDFからテキストを抽出（OCR対応）"""
    text = ""
    try:
        # まず通常のテキスト抽出
        import fitz  # PyMuPDF
        with fitz.open(pdf_path) as doc:
            for page in doc:
                page_text = page.get_text()
                if page_text.strip():
                    text += page_text + "\n"

        # テキストが空ならOCRで抽出
        if not text.strip():
            pages = convert_from_path(pdf_path)
            for page in pages:
                text += pytesseract.image_to_string(page, lang="jpn") + "\n"

    except Exception as e:
        print(f"PDF読み込み失敗: {pdf_path}, {e}")
    return text.strip()

# PDFアップロード＆RAG用データ作成
@csrf_exempt
def upload_pdf(request):
    if request.method == "POST":
        pdf_file = request.FILES.get("pdf_file")
        if not pdf_file:
            return JsonResponse({"error": "PDFが選択されていません"}, status=400)

        pdf_dir = os.path.join(settings.MEDIA_ROOT, "pdfs")
        os.makedirs(pdf_dir, exist_ok=True)
        file_path = os.path.join(pdf_dir, pdf_file.name)

        with open(file_path, "wb") as f:
            for chunk in pdf_file.chunks():
                f.write(chunk)

        # アップロード後にベクトルを作成
        load_pdfs_and_build_index()

        return JsonResponse({"message": f"{pdf_file.name} をアップロードしました"})

    # GETの場合はアップロードページを表示
    return render(request, "notices/upload.html")

# PDFからテキストを読み込むヘルパー
def extract_text_from_pdfs():
    pdf_texts = []
    pdf_files = glob.glob(os.path.join(settings.MEDIA_ROOT, "pdfs", "*.pdf"))
    for pdf_file in pdf_files:
        doc = fitz.open(pdf_file)
        text = ""
        for page in doc:
            text += page.get_text()
        pdf_texts.append(text)
    return pdf_texts


def load_pdfs_and_build_index():
    global VECTOR_TEXT_MAP, VECTORIZER, VECTORS

    pdf_dir = os.path.join(settings.MEDIA_ROOT, 'pdfs')
    if not os.path.exists(pdf_dir):
        print(f"PDFディレクトリが存在しません: {pdf_dir}")
        return

    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
    if not pdf_files:
        print("PDFファイルが存在しません")
        return

    VECTOR_TEXT_MAP = []
    for pdf_file in pdf_files:
        path = os.path.join(pdf_dir, pdf_file)
        text = extract_text_from_pdf(path)
        if text:
            VECTOR_TEXT_MAP.append(text)
        else:
            print(f"PDF内容が空です: {pdf_file}")

    if not VECTOR_TEXT_MAP:
        print("有効なPDFテキストが見つかりません")
        return

    # TF-IDFベクトル化
    VECTORIZER = TfidfVectorizer()
    vectors = VECTORIZER.fit_transform(VECTOR_TEXT_MAP).toarray().astype("float32")

    # FAISS作成
    dim = vectors.shape[1]
    VECTORS = faiss.IndexFlatL2(dim)
    VECTORS.add(vectors)
    print("PDFベクトル化完了")

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro")

@csrf_exempt
@require_POST
def chat_with_pdf(request):
    global VECTORIZER, VECTORS, VECTOR_TEXT_MAP

    question = request.POST.get("question")
    if not question:
        return JsonResponse({"error": "質問が送信されていません"}, status=400)

    if not VECTOR_TEXT_MAP or VECTORS is None:
        return JsonResponse({"error": "PDFがまだアップロードされていません / ベクトル未構築"}, status=400)

    try:
        # 質問をベクトル化し、類似ページ検索
        q_vec = VECTORIZER.transform([question]).toarray().astype("float32")
        D, I = VECTORS.search(q_vec, k=3)
        context = "\n".join([VECTOR_TEXT_MAP[i] for i in I[0]])
    except Exception as e:
        return JsonResponse({"error": f"ベクトル検索エラー: {e}"}, status=500)

    # Geminiへ渡すプロンプト
    prompt = f"以下は参考文書の内容です:\n{context}\n\n質問: {question}\n文脈に基づいて日本語で簡潔に回答してください。"

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        answer = response.text
    except Exception as e:
        return JsonResponse({"error": f"Gemini API エラー: {e}"}, status=500)

    return JsonResponse({"answer": answer})

load_pdfs_and_build_index()
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
