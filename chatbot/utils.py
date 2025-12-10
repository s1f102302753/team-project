import numpy as np
import PyPDF2
from google import genai
from django.conf import settings
import os
from chromadb import Client as ChromaClient
from chromadb import PersistentClient
from chromadb.config import Settings

# =========================
# Gemini クライアント初期化
# =========================
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

EMBED_MODEL = "models/text-embedding-004"
LLM_MODEL = "models/gemini-2.5-flash"

# =========================
# Chroma クライアント
# =========================
# ChromaDB の保存先フォルダ
CHROMA_PATH = "vector_db"

# 新方式の Chroma Client
chroma_client = PersistentClient(path=CHROMA_PATH)

# コレクション取得（なければ作成）
collection = chroma_client.get_or_create_collection(
    name="pdf_index",
    metadata={"hnsw:space": "cosine"}
)

# コレクション（存在しない場合は作る）
try:
    collection = chroma_client.get_collection("pdf_index")
except:
    collection = chroma_client.create_collection("pdf_index")


# =========================
# テキストを Embed
# =========================
def embed_text(text: str):
    response = client.models.embed_text(
        model=EMBED_MODEL,
        text=text
    )
    return response.embeddings[0].values


# =========================
# PDF を読み込み → チャンク → ChromaDB へ保存
# =========================
def process_pdf_and_update_index(pdf_path):
    reader = PyPDF2.PdfReader(pdf_path)
    text = ""

    for i, page in enumerate(reader.pages):
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"

    # チャンク分割
    chunks = []
    step = 400
    for i in range(0, len(text), step):
        chunk = text[i:i+step].strip()
        if chunk:
            chunks.append(chunk)

    # ChromaDB に登録
    for idx, chunk in enumerate(chunks):
        emb = embed_text(chunk)
        collection.upsert(
            ids=[f"{os.path.basename(pdf_path)}_{idx}"],
            documents=[chunk],
            embeddings=[emb],
            metadatas=[{
                "file": os.path.basename(pdf_path),
                "chunk": idx
            }]
        )

    chroma_client.persist()


# =========================
# ChromaDB 類似検索
# =========================
def search_vector_db(query_text, top_k=3):
    results = collection.query(
        query_texts=[query_text],
        n_results=top_k
    )
    return results


# =========================
# RAG + Gemini
# =========================
def ask_gemini(question):

    # ① ChromaDB 検索
    results = search_vector_db(question, top_k=3)

    context_blocks = []
    for txt, meta in zip(results["documents"][0], results["metadatas"][0]):
        block = f"[file={meta['file']}, chunk={meta['chunk']}]\n{txt}"
        context_blocks.append(block)

    context = "\n\n".join(context_blocks)

    # ② プロンプト構築
    system_prompt = """
あなたはPDF文書に基づいて正確に回答するアシスタントです。
- 回答は必ずPDFの内容（以下のコンテキスト）から得られる情報のみで行ってください。
- 推測で答えないこと。
- 情報が無ければ「PDFに情報がありません」と答えること。
"""

    user_prompt = f"""
====== PDFコンテキスト ======
{context}
===========================

質問：
{question}
"""

    # ③ Gemini 呼び出し
    response = client.models.generate_content(
        model=LLM_MODEL,
        contents=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        generation_config={
            "temperature": 0.0,
            "max_output_tokens": 800
        }
    )

    return response.text
