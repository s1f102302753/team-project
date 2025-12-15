import os
import pdfplumber
from pdf2image import convert_from_path
import pytesseract

from chromadb import PersistentClient
from chromadb.utils import embedding_functions

import google.generativeai as genai


# -----------------------------
# ChromaDB 初期化
# -----------------------------
CHROMA_PATH = "chromadb_store"

chroma_client = PersistentClient(path=CHROMA_PATH)

collection = chroma_client.get_or_create_collection(
    name="pdf_collection",
    metadata={"hnsw:space": "cosine"}
)

embedding_model = embedding_functions.DefaultEmbeddingFunction()


# -----------------------------
# Gemini
# -----------------------------
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")


# -----------------------------
# PDF → テキスト抽出（OCR対応）
# -----------------------------
def extract_text_with_ocr(pdf_path):
    pages_text = []

    print(f"[INFO] Extracting text from PDF: {pdf_path}")

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()

            # 通常テキストが取れたらそのまま使う
            if text and text.strip():
                pages_text.append(text.strip())
                continue

            # ------------ OCR 実行 -------------
            print(f"[INFO] Page {i} has no text. Running OCR...")

            # PDF → 画像
            images = convert_from_path(pdf_path, first_page=i+1, last_page=i+1)

            ocr_text = ""
            for img in images:
                ocr_text += pytesseract.image_to_string(img, lang="jpn+eng")

            pages_text.append(ocr_text.strip())

    return pages_text


# -----------------------------
# PDF → ChromaDB へ登録
# -----------------------------
def process_pdf_and_update_index(pdf_path):

    pages = extract_text_with_ocr(pdf_path)
    print(f"[DEBUG] Extracted {len(pages)} pages.")

    # 完全に空の場合
    pages = [p for p in pages if p.strip()]
    if len(pages) == 0:
        raise ValueError("PDF の全ページでテキストが抽出できませんでした。")

    # 埋め込み生成
    embeddings = embedding_model(pages)

    ids = [f"doc_{i}" for i in range(len(pages))]
    metadatas = [{"page": i} for i in range(len(pages))]

    collection.add(
        ids=ids,
        documents=pages,
        embeddings=embeddings,
        metadatas=metadatas
    )

    print("[INFO] ChromaDB updated with new PDF data.")


# -----------------------------
# 質問 → Gemini
# -----------------------------
def ask_gemini(query):

    results = collection.query(
        query_texts=[query],
        n_results=3
    )

    retrieved = results["documents"][0]
    context = "\n---\n".join(retrieved)

    prompt = f"""
以下は PDF から抽出された関連情報です：

{context}

質問：{query}

この情報を踏まえて、分かりやすく回答してください。
"""

    response = model.generate_content(prompt)
    return response.text
