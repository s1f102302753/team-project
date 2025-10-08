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

## 仮想環境を作成・有効化
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows

## 依存パッケージをインストール
   ```bash
   pip install -r requirements.txt

## マイグレーションを実行
   ```bash
   python manage.py migrate

## 開発用サーバーを起動
   ```bash
   python manage.py runserver

