import json
import logging
from pathlib import Path
from django.conf import settings
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .utils import process_pdf_and_update_index, ask_gemini

logger = logging.getLogger(__name__)

def chat_page(request):
    """チャット画面の表示"""
    return render(request, "chatbot/chat.html")

@login_required
def upload_pdf(request):
    """
    PDFアップロード処理
    - ログイン必須
    - 自治体職員 (is_official) のみ実行可能
    """
    # 権限チェック: 職員でなければ 403 Forbidden
    if not request.user.is_official:
        return JsonResponse({"error": "この操作を行う権限がありません。"}, status=403)

    if request.method == "POST":
        uploaded_file = request.FILES.get("pdf")
        
        if not uploaded_file:
            return JsonResponse({"error": "ファイルが選択されていません。"}, status=400)

        # ファイル名に日本語が含まれる場合のトラブル回避のため、必要ならリネーム等を検討
        # ここではシンプルにそのまま保存します
        pdf_dir = settings.BASE_DIR / "chatbot" / "pdfs"
        pdf_dir.mkdir(parents=True, exist_ok=True)

        save_path = pdf_dir / uploaded_file.name

        try:
            with open(save_path, "wb") as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)
            
            # ベクトルDBへの登録処理
            process_pdf_and_update_index(str(save_path))
            
            return JsonResponse({"status": "success", "filename": uploaded_file.name})

        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "POST method required"}, status=405)


@csrf_exempt
def chat_api(request):
    """チャットボットAPI (POSTのみ)"""
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8"))
        question = body.get("question", "").strip()

        if not question:
            return JsonResponse({"error": "質問内容が空です。"}, status=400)

        # Geminiへ問い合わせ
        answer = ask_gemini(question)
        return JsonResponse({"answer": answer})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Chat API Error: {e}")
        return JsonResponse({"error": str(e)}, status=500)
    