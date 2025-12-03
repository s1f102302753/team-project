from django.conf import settings
import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .utils import process_pdf_and_update_index, ask_gemini

def chat_page(request):
    return render(request, "chatbot/chat.html")


def upload_pdf(request):
    if request.method == "POST":
        uploaded_file = request.FILES["pdf"]

        # BASE_DIR からの絶対パス
        pdf_dir = settings.BASE_DIR / "chatbot" / "pdfs"
        pdf_dir.mkdir(exist_ok=True)

        save_path = pdf_dir / uploaded_file.name

        with open(save_path, "wb") as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        # ↓ ここで絶対パスを渡す
        process_pdf_and_update_index(str(save_path))

        return JsonResponse({"status": "success"})

    return JsonResponse({"status": "invalid method"})


@csrf_exempt
def chat_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=400)

    body = json.loads(request.body.decode("utf-8"))
    question = body.get("question", "")

    if not question:
        return JsonResponse({"error": "empty question"}, status=400)

    try:
        answer = ask_gemini(question)
        return JsonResponse({"answer": answer})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
