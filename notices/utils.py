import requests
import random
from django.core.cache import cache

def fetch_amami_evacuation():
    """
    【避難所情報】BODIK APIから奄美市の指定緊急避難場所データを取得する
    """
    CACHE_KEY = 'amami_evacuation_data'
    
    # 1. キャッシュを確認
    full_data = cache.get(CACHE_KEY)
    
    if not full_data:
        # BODIK CKAN DataStore API
        api_url = 'https://data.bodik.jp/api/3/action/datastore_search'
        
        # 奄美市：指定緊急避難場所のリソースID
        resource_id = '815306ec-66f3-4e31-9706-e0f39e3368a5'
        
        params = {
            'resource_id': resource_id,
            'limit': 100
        }
        
        try:
            res = requests.get(api_url, params=params, timeout=10)
            res.raise_for_status()
            result = res.json()
            
            if result.get('success'):
                records = result['result']['records']
                full_data = []
                
                for record in records:
                    # 緯度経度を取得（地図リンク用）
                    lat = record.get('緯度')
                    lng = record.get('経度')
                    name = record.get('名称') or '名称不明'
                    
                    # Googleマップへのリンクを生成
                    map_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}" if lat and lng else "#"

                    full_data.append({
                        'title': f"🚨 {name}",
                        'content': f"【所在地】{record.get('所在地', '住所情報なし')}\n【対象災害】{record.get('災害種別', '全災害')}",
                        'url': map_url,
                        'created_at': '緊急避難場所',
                        'prefecture': '奄美市(防災)',
                        'is_emergency': True
                    })
                
                # 24時間キャッシュ（避難場所は頻繁に変わらないため）
                if full_data:
                    cache.set(CACHE_KEY, full_data, 60 * 60 * 24)
                    
        except Exception as e:
            print(f"Error fetching BODIK evacuation data: {e}")
            return []

    return full_data

def fetch_amami_weather():
    """
    【天気予報】Open-Meteo APIから奄美市（名瀬）の現在の天気を取得する
    """
    CACHE_KEY = 'amami_weather_data'
    weather_data = cache.get(CACHE_KEY)
    
    if not weather_data:
        # 奄美市名瀬の座標
        api_url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": 28.37,
            "longitude": 129.49,
            "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min"],
            "timezone": "Asia/Tokyo"
        }
        
        try:
            res = requests.get(api_url, params=params, timeout=10)
            res.raise_for_status()
            data = res.json()
            
            daily = data['daily']
            weather_code = daily['weather_code'][0]
            
            # WMOコードをアイコンと文字に変換
            weather_map = {
                0: "☀️ 快晴", 1: "🌤 晴れ", 2: "⛅ 曇り", 3: "☁️ 曇天",
                45: "🌫 霧", 51: "🌦 小雨", 61: "☔ 雨", 63: "🌧 激しい雨",
                71: "❄️ 雪", 95: "⚡ 雷雨"
            }
            
            weather_data = {
                'status': weather_map.get(weather_code, "☁️ 曇り"),
                'max_temp': daily['temperature_2m_max'][0],
                'min_temp': daily['temperature_2m_min'][0],
            }
            # 3時間キャッシュ
            cache.set(CACHE_KEY, weather_data, 60 * 60 * 3)
            
        except Exception as e:
            print(f"Error fetching weather data: {e}")
            return None
            
    return weather_data

# views.pyでの呼び出し互換性のために残す（必要に応じて）
def fetch_notices_for_prefecture(prefecture):
    # 現状は奄美市のデータのみを返す
    if "奄美" in prefecture or "鹿児島" in prefecture:
        return fetch_amami_evacuation()
    return []