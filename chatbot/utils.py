import numpy as np
import PyPDF2
from google import genai
from django.conf import settings
import os

# =========================
# Gemini クライアント初期化
# =========================
client = genai.Client(api_key=settings.GEMINI_API_KEY)

# 埋め込みモデル
EMBED_MODEL = "models/text-embedding-004"

# LLM モデル
LLM_MODEL = "gemini-1.5-flash"

# RAG 用の保持データ
CHUNKS = []
VECTORS = []

# =========================
# テキストを Embed
# =========================
def embed_text(text: str):
    response = client.models.embed_text(
        model=EMBED_MODEL,
        text=text
    )
    return np.array(response.embeddings[0].values)

# =========================
# コサイン類似度
# =========================
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# =========================
# PDF -> Text -> Chunk -> Embedding
# =========================
def process_pdf_and_update_index(pdf_path):
    global CHUNKS, VECTORS

    reader = PyPDF2.PdfReader(pdf_path)
    text = ""

    for page in reader.pages:
        text += page.extract_text() + "\n"

    # チャンク分割
    chunks = []
    step = 400
    for i in range(0, len(text), step):
        chunk = text[i:i+step].strip()
        if chunk:
            chunks.append(chunk)

    vectors = [embed_text(c) for c in chunks]

    CHUNKS = chunks
    VECTORS = vectors

# =========================
# 類似チャンク検索
# =========================
def find_most_relevant_chunks(query):
    if not CHUNKS:
        return []

    q_vec = embed_text(query)

    scores = []
    for idx, v in enumerate(VECTORS):
        score = cosine_similarity(q_vec, v)
        scores.append((score, CHUNKS[idx]))

    scores.sort(reverse=True, key=lambda x: x[0])
    return [c for _, c in scores[:3]]

# =========================
# RAG + Gemini 回答生成
# =========================
def ask_gemini(question: str) -> str:
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",   # ←ここが重要
        contents=question
    )
    return response.text
