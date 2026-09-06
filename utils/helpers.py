"""Вспомогательные функции"""

import re
from urllib.parse import urlparse, parse_qs


def format_duration(seconds):
    """Форматирование длительности трека"""
    if not seconds:
        return "0:00"
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes}:{seconds:02d}"


def extract_token_from_url(text):
    """Извлекает токен из полного URL или просто текста"""
    if 'access_token=' not in text:
        return None
    
    match = re.search(r'access_token=([^&\s]+)', text)
    if match:
        return match.group(1)
    
    try:
        if text.startswith('http'):
            parsed = urlparse(text)
            if parsed.fragment:
                fragment_params = parse_qs(parsed.fragment)
                if 'access_token' in fragment_params:
                    return fragment_params['access_token'][0]
            if parsed.query:
                query_params = parse_qs(parsed.query)
                if 'access_token' in query_params:
                    return query_params['access_token'][0]
    except:
        pass
    
    return None


def create_track_info(item):
    """Создает словарь с информацией о треке из данных VK"""
    # Обработка разных форматов
    if 'title' in item and 'artist' in item and 'url' in item:
        return {
            'title': item['title'],
            'artist': item['artist'],
            'duration': item.get('duration', 0),
            'url': item['url'],
            'id': item.get('id', 0)
        }
    
    # Вложенная структура
    track_data = None
    if 'track' in item:
        track_data = item['track']
    elif 'audio' in item:
        track_data = item['audio']
    
    if track_data:
        return {
            'title': track_data.get('title', ''),
            'artist': track_data.get('artist', ''),
            'duration': track_data.get('duration', 0),
            'url': track_data.get('url', ''),
            'id': track_data.get('id', 0)
        }
    
    return None


def get_track_display_text(track):
    """Форматирует текст для отображения трека"""
    duration_str = format_duration(track['duration'])
    return f"{track['artist']} - {track['title']} [{duration_str}]"
