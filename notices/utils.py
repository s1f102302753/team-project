import requests
import os
from openai import OpenAI
import numpy as np
import faiss
from PyPDF2 import PdfReader
import tiktoken

# API取得処理
def fetch_notices_for_user(user):
    """ログインユーザーの自治体APIからリアルタイムでお知らせを取得"""
    municipality = user.municipality
    if municipality and municipality.api_url:
        try:
            response = requests.get(municipality.api_url, timeout=5)
            response.raise_for_status()
            return response.json()  # APIのJSONを返す
        except requests.RequestException:
            return []
    return []

# 環境変数から API キーを読み込む
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 使用する埋め込みモデル（軽量）と保存ファイル名
EMBED_MODEL = "text-embedding-3-small"
INDEX_FILE = os.path.join("chatbot", "pdf_index.faiss")
CHUNKS_FILE = os.path.join("chatbot", "pdf_chunks.npy")

# トークナイザ（OpenAI の cl100k_base を使う）
encoding = tiktoken.get_encoding("cl100k_base")

def _chunk_text(text, max_tokens=500, overlap=50):
    """
    長いテキストをトークンベースでチャンク化。
    max_tokens はチャンク内の最大トークン数（概算）、overlap は隣接チャンクの重複トークン数。
    """
    tokens = encoding.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = start + max_tokens
        chunk_tokens = tokens[start:end]
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)
        start = end - overlap
        if start < 0:
            start = 0
    return chunks

def learn_pdf(pdf_path):
    """
    PDFを読み込んでチャンク分割し、埋め込みを生成してFAISSに保存する。
    戻り値: 登録したチャンク数
    """
    # 1) PDFから全文テキスト抽出
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    # 2) チャンク化（トークン数ベース）
    chunks = _chunk_text(text, max_tokens=500, overlap=50)

    # 3) 埋め込み生成（OpenAI）
    embeddings = []
    for chunk in chunks:
        # OpenAI embeddings API 呼び出し
        res = client.embeddings.create(model=EMBED_MODEL, input=chunk)
        emb = res.data[0].embedding
        embeddings.append(emb)

    embeddings = np.array(embeddings, dtype=np.float32)

    # 4) FAISS インデックス作成・保存
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    faiss.write_index(index, INDEX_FILE)

    # 5) チャンクテキストを保存（検索結果のコンテキスト用）
    np.save(CHUNKS_FILE, np.array(chunks, dtype=object))

    return len(chunks)

def query_pdf(query, k=3):
    """
    クエリを受けて最も近い k チャンクを返す（テキスト）
    """
    # index と chunks の存在確認
    if not os.path.exists(INDEX_FILE) or not os.path.exists(CHUNKS_FILE):
        return []

    index = faiss.read_index(INDEX_FILE)
    chunks = np.load(CHUNKS_FILE, allow_pickle=True)

    # クエリ埋め込み
    qres = client.embeddings.create(model=EMBED_MODEL, input=query)
    qemb = np.array(qres.data[0].embedding, dtype=np.float32)

    D, I = index.search(np.array([qemb]), k)
    hits = [chunks[i] for i in I[0] if i < len(chunks)]
    return hits