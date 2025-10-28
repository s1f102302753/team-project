# notices/utils.py
import requests

def fetch_okinawa():
    url = 'https://data.bodik.jp/api/3/action/package_search'
    params = {'q': '沖縄', 'rows': 5, 'sort': 'metadata_modified desc'}
    res = requests.get(url, params=params)
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

def fetch_tokyo():
    url = 'https://catalog.data.metro.tokyo.lg.jp/api/3/action/package_search'
    params = {'q': '東京都', 'rows': 5, 'sort': 'metadata_modified desc'}
    res = requests.get(url, params=params)
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

def fetch_notices_for_prefecture(prefecture: str):
    fetch_map = {
        '沖縄': fetch_okinawa,
        '東京都': fetch_tokyo,
        # 他の自治体も追加可能
    }
    if prefecture not in fetch_map:
        return []
    return fetch_map[prefecture]()
