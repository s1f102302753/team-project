import requests
from bs4 import BeautifulSoup
import re

def fetch_okinawa():
    url = 'https://data.bodik.jp/api/3/action/package_search'
    params = {'q': '沖縄', 'rows': 5, 'sort': 'metadata_modified desc'}
    try:
        res = requests.get(url, params=params, timeout=5)
        res.raise_for_status()
        data = res.json()['result']['results']
        return [
            {
                'title': n['title'],
                'content': n['notes'],
                'url': n.get('url', '#'),
                'created_at': n['metadata_modified'],
                'prefecture': '沖縄'
            }
            for n in data
        ]
    except Exception:
        return []

def fetch_tokyo():
    url = 'https://catalog.data.metro.tokyo.lg.jp/api/3/action/package_search'
    params = {'q': '東京都', 'rows': 5, 'sort': 'metadata_modified desc'}
    try:
        res = requests.get(url, params=params, timeout=5)
        res.raise_for_status()
        data = res.json()['result']['results']
        return [
            {
                'title': n['title'],
                'content': n['notes'],
                'url': n.get('url', '#'),
                'created_at': n['metadata_modified'],
                'prefecture': '東京都'
            }
            for n in data
        ]
    except Exception:
        return []

# ▼▼▼ 修正版: 奄美市の新着情報一覧ページから取得 ▼▼▼
def fetch_amami():
    # 奄美市の「新着情報一覧」ページ（ここなら確実にリストがある）
    url = 'https://www.city.amami.lg.jp/shinchaku/index.html'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        res = requests.get(url, headers=headers, timeout=5)
        res.raise_for_status()
        res.encoding = res.apparent_encoding # 文字化け対策
        
        soup = BeautifulSoup(res.content, 'html.parser')
        data = []
        
        # サイト構造解析:
        # 奄美市の新着一覧は <div id="tmp_contents"> 内の <ul><li><a>...</a></li></ul> にある可能性が高い
        # 汎用的に、メインエリアと思われる場所からリンクを探す
        main_area = soup.find(id='tmp_contents') or soup.find(id='main') or soup.find(class_='main') or soup.body

        # メインエリア内のすべてのリンクを取得
        links = main_area.find_all('a')
        
        count = 0
        for a in links:
            if count >= 5: # 最新5件まで
                break
                
            title = a.text.strip().replace('\n', '').replace('\t', '')
            href = a.get('href')
            
            # ゴミリンク（「トップへ戻る」など）を除外するためのフィルタ
            # タイトルが短すぎる、または日付が含まれていないリンクは怪しいが、
            # まずは「タイトルがある」かつ「Javascriptではない」ものを取得
            if len(title) < 5 or 'javascript' in str(href).lower():
                continue

            # 相対パスを絶対パスに変換
            if href:
                if href.startswith('/'):
                    href = 'https://www.city.amami.lg.jp' + href
                elif not href.startswith('http'):
                    # 同じ階層あるいは相対パス対策
                    href = 'https://www.city.amami.lg.jp/shinchaku/' + href
            else:
                continue
            
            # 日付の抽出（奄美市サイトは「12月1日 タイトル」のような形式が多い）
            # リンクの親要素テキスト、またはリンクの前の要素から日付を探す
            date_str = ''
            
            # パターン1: <li> 2023年10月10日 <a href...>タイトル</a> </li> の場合
            parent_text = a.parent.text.strip()
            # 正規表現で日付(例: 12月9日)を探す
            match = re.search(r'(\d{1,2}月\d{1,2}日)', parent_text)
            if match:
                date_str = match.group(1)
            
            # 日付が見つかったものだけを「ニュース」として扱う（精度向上のため）
            if date_str:
                data.append({
                    'title': title,
                    'content': '奄美市公式ホームページで詳細を見る',
                    'url': href,
                    'created_at': date_str,
                    'prefecture': '奄美市'
                })
                count += 1

        # データが取れなかった場合のフェイルセーフ
        if not data:
             data.append({
                'title': '奄美市 新着情報一覧',
                'content': 'こちらをクリックして公式サイトを確認してください。',
                'url': url,
                'created_at': 'リンク',
                'prefecture': '奄美市'
            })
            
        return data

    except Exception as e:
        print(f"Error scraping Amami: {e}")
        return [{
            'title': '情報の取得に失敗しました',
            'content': 'エラーが発生しました。',
            'url': url,
            'created_at': '',
            'prefecture': '奄美市'
        }]

def fetch_notices_for_prefecture(prefecture: str):
    fetch_map = {
        '沖縄': fetch_okinawa,
        '沖縄県': fetch_okinawa,
        '東京都': fetch_amami,   # テスト用
        '鹿児島県': fetch_amami,
        '奄美市': fetch_amami,
    }
    
    if prefecture not in fetch_map:
        return []
        
    return fetch_map[prefecture]()


# notices/utils.py に追記・修正

# ... (既存のimportやfetch_amamiなどはそのまま) ...

def fetch_amami_detail(target_url):
    """
    指定されたURL（奄美市公式サイト）の本文を取得する
    """
    # セキュリティ対策: 奄美市のドメイン以外は拒否
    if not target_url.startswith('https://www.city.amami.lg.jp'):
        return None

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        res = requests.get(target_url, headers=headers, timeout=5)
        res.raise_for_status()
        res.encoding = res.apparent_encoding
        
        soup = BeautifulSoup(res.content, 'html.parser')
        
        # ----------------------------------------------------
        # 本文の抽出ロジック
        # ----------------------------------------------------
        # 奄美市サイトの構造に合わせてメインコンテンツを探す
        # 多くの場合 id="tmp_contents" または id="main" に本文がある
        content_area = soup.find(id='tmp_contents') or soup.find(id='main') or soup.find(class_='main')
        
        data = {
            'title': '',
            'body_html': '',
            'source_url': target_url
        }

        if content_area:
            # タイトル取得 (h1)
            h1 = content_area.find('h1')
            if h1:
                data['title'] = h1.text.strip()
                h1.decompose() # 本文からタイトルを削除（重複表示防止）

            # 不要な要素（パンくずリスト、印刷ボタン、更新日など）を削除
            for rubbish in content_area.find_all(['div'], class_=['topic_path', 'print_btn', 'update']):
                rubbish.decompose()

            # 画像のパスを相対パスから絶対パスに変換
            for img in content_area.find_all('img'):
                src = img.get('src')
                if src and src.startswith('/'):
                    img['src'] = 'https://www.city.amami.lg.jp' + src

            # リンクのパスも修正
            for a in content_area.find_all('a'):
                href = a.get('href')
                if href and href.startswith('/'):
                    a['href'] = 'https://www.city.amami.lg.jp' + href

            # HTMLとして取得
            data['body_html'] = str(content_area)
            
        else:
            # 構造が解析できなかった場合
            data['title'] = '詳細情報の取得失敗'
            data['body_html'] = '<p>詳細内容の取得に失敗しました。以下の発信元URLからご確認ください。</p>'

        return data

    except Exception as e:
        print(f"Error scraping detail: {e}")
        return None