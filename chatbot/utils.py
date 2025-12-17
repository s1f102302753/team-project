import os
import uuid
from pathlib import Path
import pdfplumber
from pdf2image import convert_from_path
import pytesseract

from chromadb import PersistentClient
from chromadb.utils import embedding_functions

import google.generativeai as genai

# -----------------------------
# 設定・初期化
# -----------------------------
# 環境変数からAPIキーを取得
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

genai.configure(api_key=GEMINI_API_KEY)

# モデル設定 (Gemini 2.0 Flash)
# ※ system_instruction を設定することで、キャラ付けとガードレールを強化
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction="あなたは自治体の親切な窓口担当AIです。提供された「参考資料」の内容のみに基づいて回答してください。"
)

CHROMA_PATH = "chromadb_store"
chroma_client = PersistentClient(path=CHROMA_PATH)

# コレクションの取得・作成
collection = chroma_client.get_or_create_collection(
    name="pdf_collection",
    metadata={"hnsw:space": "cosine"}
)

# 埋め込みモデル
# 注意: 日本語精度を極限まで高めるなら GoogleGenerativeAIEmbeddingFunction への変更を推奨しますが
# まずは動作安定のため Default を使用します。
embedding_model = embedding_functions.DefaultEmbeddingFunction()


# -----------------------------
# PDF → テキスト抽出（OCR対応）
# -----------------------------
def extract_text_with_ocr(pdf_path):
    pages_text = []
    print(f"[INFO] Extracting text from PDF: {pdf_path}")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()

                # テキストが十分に取得できた場合
                if text and len(text.strip()) > 50:
                    pages_text.append(text.strip())
                    continue

                # ------------ OCR 実行 -------------
                print(f"[INFO] Page {i+1} text is empty or too short. Running OCR...")
                
                # popplerのパスが通っていない場合、poppler_path引数が必要になることがあります
                try:
                    images = convert_from_path(pdf_path, first_page=i+1, last_page=i+1)
                    ocr_text = ""
                    for img in images:
                        # 日本語読み取り設定
                        ocr_text += pytesseract.image_to_string(img, lang="jpn+eng")
                    
                    pages_text.append(ocr_text.strip())
                except Exception as e:
                    print(f"[ERROR] OCR failed on page {i+1}: {e}")
                    pages_text.append("") # エラー時は空文字を追加してページズレを防ぐ

    except Exception as e:
        print(f"[ERROR] Failed to open PDF: {e}")
        raise e

    return pages_text


# -----------------------------
# PDF → ChromaDB へ登録
# -----------------------------
def process_pdf_and_update_index(pdf_path):
    # ファイル名をIDのプレフィックスにして、ユニーク性を担保する
    file_name = Path(pdf_path).name
    
    pages = extract_text_with_ocr(pdf_path)
    print(f"[DEBUG] Extracted {len(pages)} pages from {file_name}.")

    # 空ページを除去しつつ、元のページ番号を保持したい場合は工夫が必要ですが
    # ここではシンプルに空文字を除外して登録します
    valid_docs = []
    valid_metadatas = []
    valid_ids = []

    for i, text in enumerate(pages):
        if not text.strip():
            continue
            
        valid_docs.append(text)
        # メタデータにファイル名を含めることで、どの資料か特定可能にする
        valid_metadatas.append({"source": file_name, "page": i + 1})
        # IDをユニークにする (ファイル名_ページ番号)
        # 日本語ファイル名はIDに使えない場合があるためUUIDを混ぜるかハッシュ化が安全ですが、簡易的に以下とします
        safe_id = f"{file_name}_{i}_{uuid.uuid4().hex[:8]}"
        valid_ids.append(safe_id)

    if not valid_docs:
        print("[WARN] No valid text extracted. Skipping database update.")
        return

    # 埋め込み生成
    embeddings = embedding_model(valid_docs)

    collection.add(
        ids=valid_ids,
        documents=valid_docs,
        embeddings=embeddings,
        metadatas=valid_metadatas
    )

    print(f"[INFO] Successfully added {len(valid_docs)} chunks to ChromaDB.")


# -----------------------------
# 質問 → Gemini
# -----------------------------
def ask_gemini(query):
    print(f"[QUERY] {query}")
    
    # 1. 関連情報の検索
    # n_results を 3 -> 10 に増加。
    # Gemini 2.0 Flash はコンテキストウィンドウが広いため、多めに情報を渡したほうが精度が上がります。
    results = collection.query(
        query_texts=[query],
        n_results=10
    )

    retrieved_docs = results["documents"][0]
    retrieved_meta = results["metadatas"][0]

    if not retrieved_docs:
        return "申し訳ありません。関連する情報が見つかりませんでした。"

    # 検索結果を見やすく整形（出典ファイル名も含める）
    context_list = []
    for doc, meta in zip(retrieved_docs, retrieved_meta):
        source_info = f"【出典: {meta.get('source', '不明')} (p.{meta.get('page', '?')})】"
        context_list.append(f"{source_info}\n{doc}")
    
    context_text = "\n\n----------------\n\n".join(context_list)

    # 2. プロンプト作成
    prompt = f"""
以下の【参考資料】に基づいて、ユーザーの質問に答えてください。

制約事項:
1. 【参考資料】に書かれていない情報は、「資料には記載がありません」と答えてください。勝手に捏造しないでください。
2. 引用元（ファイル名やページ）が分かる場合は、回答の中で言及してください。
3. 住民に分かりやすく、丁寧なトーンで回答してください。

質問：
{query}

【参考資料】：
{context_text}
"""

    # 3. 生成実行
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"[ERROR] Gemini generation failed: {e}")
        return "申し訳ありません。現在回答を生成できません。"
