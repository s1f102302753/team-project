import sys
import os
import socket
import threading
import json
import time
# プロジェクトのルートディレクトリのパスを計算し、sys.pathに追加
# notices/socket_server.py の親ディレクトリの親ディレクトリ (つまりプロジェクトルート)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

import django

# --- Django環境の初期化 ---
# manage.pyと同じ階層にある config/settings.py を指定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Djangoモデルのインポートは環境設定後に行う必要がある
from notices.models import Post # あなたが notices/models.py で定義するPostモデルを想定
from django.contrib.auth import get_user_model # ユーザーモデルを取得
from users.models import Municipality # Municipalityモデルの場所を仮定

User = get_user_model() # 現在使用されているカスタムユーザーモデルを取得

# --- グローバル設定 ---
connected_clients = []
HOST = '0.0.0.0'
PORT = 8888 

# --- ヘルパー関数 ---
def get_all_posts():
    """データベースから既存の全ての投稿を取得する"""
    # データベースから新しいもの順に取得
    posts_queryset = Post.objects.order_by('-created_at').all() 
    
    # JSONシリアル化のために辞書のリストに変換
    post_list = []
    for post in posts_queryset:
        post_list.append({
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "user": post.author.username if post.author else "匿名", # authorフィールドを想定
            "timestamp": post.created_at.strftime("%b. %d, %Y, %I:%M %p")
        })
    return post_list

def save_new_post(title, content, user_id, municipality_id):
    """新しい投稿をデータベースに保存する"""
    
    try:
        # user_idに基づいてユーザーオブジェクトを取得 (必須)
        try:
            author_obj = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            print(f"ユーザーID {user_id} が見つかりませんでした。投稿できません。")
            return None

        # municipality_idに基づいて自治体オブジェクトを取得 (null=Trueなので、IDがなければNoneを許可)
        municipality_obj = None
        if municipality_id:
            try:
                municipality_obj = Municipality.objects.get(pk=municipality_id)
            except Municipality.DoesNotExist:
                print(f"自治体ID {municipality_id} が見つかりませんでした。")

        # データベースに新しい投稿を作成
        new_post = Post.objects.create(
            title=title,
            content=content,
            author=author_obj,
            municipality=municipality_obj 
        )
        
        # クライアントへ返すデータを作成
        return {
            "id": new_post.id,
            "title": new_post.title,
            "content": new_post.content,
            "user": author_obj.username,
            "municipality": municipality_obj.name if municipality_obj else "全て",
            "timestamp": new_post.created_at.strftime("%b. %d, %Y, %I:%M %p")
        }
        
    except Exception as e:
        print(f"データベース保存エラー: {e}")
        return None

def broadcast(message, sender_socket=None):
    """接続中の全クライアントにメッセージを送信する"""
    # ブロードキャスト中にリストが変更されないようコピーを使用
    clients_to_check = connected_clients[:] 
    for client in clients_to_check:
        if client != sender_socket:
            try:
                client.send(message.encode('utf-8'))
            except:
                # 送信失敗（切断）したクライアントをリストから削除
                print(f"切断されたクライアントを削除: {client.getpeername()}")
                client.close()
                if client in connected_clients:
                    connected_clients.remove(client)

# --- クライアント処理スレッド ---
def handle_client(client_socket, client_address):
    print(f"接続確立: {client_address}")
    
    # 接続したクライアントに現在の全投稿を送信する（初期表示）
    posts_data = get_all_posts()
    initial_data = json.dumps({"type": "INIT", "posts": posts_data})
    
    try:
        client_socket.send(initial_data.encode('utf-8'))
    except:
        # 初期送信に失敗した場合、すぐに接続を終了
        client_socket.close()
        if client_socket in connected_clients:
            connected_clients.remove(client_socket)
        return

    while True:
        try:
            # クライアントからのデータ受信
            data = client_socket.recv(4096)
            if not data:
                break

            received_message = json.loads(data.decode('utf-8'))
            print(f"受信データ: {received_message}")

            if received_message.get('type') == 'NEW_POST':
                # 新しい投稿処理
                title = received_message.get('title', '無題')
                content = received_message.get('content', '')
                
                # ★★★ 修正箇所: user_id と municipality_id をクライアントから取得 ★★★
                user_id = received_message.get('user_id')
                municipality_id = received_message.get('municipality_id')

                if not user_id:
                    print("警告: user_id が提供されていません。投稿を拒否します。")
                    # エラーメッセージをクライアントに返すことも検討
                    continue 

                # ★★★ 修正箇所: save_new_post に title, content, user_id, municipality_id を渡す ★★★
                # save_new_post 関数がデータベースに保存し、完全な投稿データを返す
                new_post_data = save_new_post(title, content, user_id, municipality_id)
                
                if new_post_data:
                    # 投稿された新しいデータを全クライアントにブロードキャスト
                    broadcast_data = json.dumps({"type": "POST_ADDED", "post": new_post_data})
                    print(f"投稿をブロードキャストします...")
                    # 投稿した本人も含め、全員にブロードキャスト
                    broadcast(broadcast_data) 
                
        except json.JSONDecodeError:
            print("警告: 不正なJSONデータを受信しました。")
        except Exception as e:
            print(f"致命的なエラー発生 ({client_address}): {e}")
            break

    # クライアントが切断された場合
    print(f"接続切断: {client_address}")
    if client_socket in connected_clients:
        connected_clients.remove(client_socket)
    client_socket.close()

# --- メインサーバーロジック ---
def start_server():
    """サーバーの起動と接続の待ち受けを行う"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # サーバー再起動時にすぐにポートを再利用可能にする
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)
    print(f"サーバー起動中... ポート {PORT} で待機します。")

    while True:
        try:
            # 接続待ち
            client_socket, client_address = server_socket.accept()
            
            # クライアントリストに追加
            connected_clients.append(client_socket)
            
            # クライアント処理用の新しいスレッドを開始
            thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            thread.daemon = True 
            thread.start()
            
        except KeyboardInterrupt:
            print("\nサーバーを停止します...")
            break
        except Exception as e:
            print(f"接続受付エラー: {e}")
            break

    server_socket.close()

if __name__ == "__main__":
    start_server()