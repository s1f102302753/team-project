# デジタル回覧板アプリ
**Hackathon / チームプロジェクト**  

このアプリは、社内やチーム内の回覧板・掲示板をデジタル化するためのWebアプリです。  
ユーザー登録、回覧板投稿、閲覧履歴管理などの機能を備えており、情報共有を効率化します。

---

## 技術スタック

- **バックエンド:** Django 5.2
- **フロントエンド:** HTML / CSS / Django Templates
- **データベース:** SQLite (開発用) / PostgreSQL (本番想定)
- **環境管理:** Python 3.10, virtualenv
- **その他:** Docker, Docker Compose (オプション)

---

## 環境構築手順

1. リポジトリをクローン
   ```bash
   git clone [リポジトリURL]
   cd team-project

2. 仮想環境を作成・有効化
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows

3. 依存パッケージをインストール
   ```bash
   pip install -r requirements.txt

4. マイグレーションを実行
   ```bash
   python manage.py migrate

5. 開発用サーバーを起動
   ```bash
   python manage.py runserver

---

## ディレクトリ構成
```text
team-project
├── config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── users
│   ├── templates
│   │   └── users
│   │       ├── login.html
│   │       ├── logout.html
│   │       ├── register.html
│   │       └── profile.html
│   ├── views.py
│   └── urls.py
├── notices
│   ├── templates
│   │   └── notices
│   │       ├── notice_list.html
│   │       ├── notice_detail.html
│   │       └── notice_form.html
│   ├── views.py
│   └── urls.py
├── templates
│   └── base.html
├── static
│   ├── css
│   └── js
├── manage.py
└── requirements.txt

```

## チーム開発における注意点
静的ファイル（CSS/JS）は static/ 内で管理

テンプレートは templates/ 内でアプリごとに分離

1. 新規パッケージを追加した場合は requirements.txt を更新
```bash
pip freeze > requirements.txt

```


## チャットボット機能実装におけるライブラリ
```bash
pip install django openai PyPDF2 faiss-cpu tiktoken

```

openai: ChatGPT API利用
PyPDF2: PDFテキスト抽出
faiss-cpu: ベクトル検索（PDFの内容検索）
tiktoken: トークン分割（埋め込み用）
※RAGのために必要最小限のライブラリ


## OpenAI APIキー管理
安全のため .env に保存し、Djangoで読み込みます。
```bash
pip install python-dotenv

```

```bash
# プロジェクトルートで
cat > .env <<'EOF'
# .env.example を作成するときは値は空にする
OPENAI_API_KEY=sk-xxxxREPLACE_WITH_YOUR_KEY
# 他の環境変数
POSTGRES_USER=team_user
POSTGRES_PASSWORD=password123
POSTGRES_DB=team_project_db
EOF

```

## fitzのインストール
```bash
pip install PyMuPDF

```
確認方法
```bash
python -m fitz
```
