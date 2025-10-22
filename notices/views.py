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

app_name = 'notices'

class NoticeHomeView(TemplateView):
    template_name = 'notices/home.html'

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


@csrf_exempt
@require_POST
def chat_with_pdf(request):
    global VECTORIZER, VECTORS, VECTOR_TEXT_MAP

    question = request.POST.get("question")
    if not question:
        return JsonResponse({"error": "質問が送信されていません"}, status=400)

    # デバッグ用出力
    if not VECTOR_TEXT_MAP or VECTORS is None:
        return JsonResponse({"error": "PDFがまだアップロードされていません / ベクトル未構築"}, status=400)

    try:
        # 質問をベクトル化
        q_vec = VECTORIZER.transform([question]).toarray().astype("float32")
        D, I = VECTORS.search(q_vec, k=3)
        context = "\n".join([VECTOR_TEXT_MAP[i] for i in I[0]])
    except Exception as e:
        return JsonResponse({"error": f"ベクトル検索エラー: {e}"}, status=500)

    prompt = f"以下の文脈を基に質問に答えてください。\n\n文脈:\n{context}\n\n質問: {question}\n\n回答:"

    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "あなたは優秀なアシスタントです。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=10000
        )

        answer = response.choices[0].message.content.strip()
    except Exception as e:
        return JsonResponse({"error": f"OpenAI API エラー: {e}"}, status=500)

    return JsonResponse({"answer": answer})

# サーバー起動時に既存 PDF を読み込む
load_pdfs_and_build_index()
