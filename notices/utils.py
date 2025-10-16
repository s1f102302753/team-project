import requests

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
