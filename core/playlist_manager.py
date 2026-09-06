"""Менеджер плейлистов"""

from utils.logger import logger
from utils.helpers import create_track_info, get_track_display_text


class PlaylistManager:
    def __init__(self, vk_client):
        self.vk_client = vk_client
        self.current_playlist = []
        self.current_playlist_id = None
        self.playlist_type = "my"
        self.playlists = []
        
    def load_my_tracks(self, user_id, max_tracks=2000, per_request=200):
        """Загрузка всех аудиозаписей пользователя"""
        self.current_playlist = []
        self.playlist_type = "my"
        self.current_playlist_id = None
        
        offset = 0
        total_loaded = 0
        
        logger.info("Загрузка всех треков пользователя...")
        
        while total_loaded < max_tracks:
            try:
                audio = self.vk_client.get_audio(
                    owner_id=user_id,
                    offset=offset,
                    count=per_request
                )
                
                items = audio.get('items', [])
                
                if not items:
                    logger.info("Треки закончились")
                    break
                
                for item in items:
                    track = create_track_info(item)
                    if track:
                        self.current_playlist.append(track)
                        total_loaded += 1
                
                logger.info(f"Загружено {len(items)} треков, всего {total_loaded}")
                
                if len(items) < per_request:
                    logger.info("Достигнут конец списка")
                    break
                
                offset += per_request
                
            except Exception as e:
                logger.error(f"Ошибка загрузки треков: {e}")
                break
        
        logger.info(f"Загрузка завершена. Всего треков: {len(self.current_playlist)}")
        return self.current_playlist
    
    def load_playlists(self, user_id, count=100):
        """Загрузка списка плейлистов"""
        try:
            playlists_data = self.vk_client.get_playlists(
                owner_id=user_id,
                count=count
            )
            
            self.playlists = []
            for playlist in playlists_data.get('items', []):
                playlist_info = {
                    'id': playlist['id'],
                    'owner_id': playlist['owner_id'],
                    'title': playlist['title'],
                    'count': playlist.get('count', 0),
                    'description': playlist.get('description', '')
                }
                self.playlists.append(playlist_info)
            
            logger.info(f"Загружено плейлистов: {len(self.playlists)}")
            return self.playlists
            
        except Exception as e:
            logger.error(f"Ошибка загрузки плейлистов: {e}")
            return []
    
    def load_playlist_tracks(self, playlist_id, owner_id, max_tracks=200):
        """Загрузка треков из плейлиста"""
        self.current_playlist = []
        self.playlist_type = "playlist"
        self.current_playlist_id = playlist_id
        
        logger.info(f"Загрузка плейлиста ID: {playlist_id}")
        
        # Пробуем разные методы загрузки
        methods = [
            self._load_via_audio_get,
            self._load_via_execute,
            self._load_via_filtering
        ]
        
        for method in methods:
            if len(self.current_playlist) > 0:
                break
            try:
                method(playlist_id, owner_id, max_tracks)
            except Exception as e:
                logger.warning(f"Метод {method.__name__} не сработал: {e}")
        
        logger.info(f"Загружено треков из плейлиста: {len(self.current_playlist)}")
        return self.current_playlist
    
    def _load_via_audio_get(self, playlist_id, owner_id, max_tracks):
        """Загрузка через audio.get с playlist_id"""
        audio = self.vk_client.get_audio(
            owner_id=owner_id,
            playlist_id=playlist_id,
            count=min(max_tracks, 200)
        )
        
        items = audio.get('items', [])
        for item in items:
            track = create_track_info(item)
            if track:
                self.current_playlist.append(track)
    
    def _load_via_execute(self, playlist_id, owner_id, max_tracks):
        """Загрузка через execute"""
        code = f"""
        var playlist = API.audio.getPlaylistById({{
            owner_id: {owner_id},
            playlist_id: {playlist_id}
        }});
        
        var tracks = [];
        var i = 0;
        while (i < {max_tracks} && i < playlist.count) {{
            var track = playlist.tracks[i];
            if (track != null) {{
                tracks.push(track);
            }}
            i = i + 1;
        }}
        
        return {{
            tracks: tracks,
            count: playlist.count
        }};
        """
        
        result = self.vk_client.execute_code(code)
        
        if result and 'tracks' in result:
            for track in result['tracks']:
                track_info = create_track_info(track)
                if track_info:
                    self.current_playlist.append(track_info)
    
    def _load_via_filtering(self, playlist_id, owner_id, max_tracks):
        """Загрузка через фильтрацию всех аудиозаписей"""
        all_tracks = self.vk_client.get_audio(
            owner_id=owner_id,
            count=600
        )
        
        for item in all_tracks.get('items', []):
            # Проверяем принадлежность к плейлисту
            if 'playlist_id' in item and item['playlist_id'] == playlist_id:
                track = create_track_info(item)
                if track:
                    self.current_playlist.append(track)
            elif 'playlist' in item and item['playlist'].get('id') == playlist_id:
                track = create_track_info(item)
                if track:
                    self.current_playlist.append(track)
    
    def search_tracks(self, query, count=200):
        """Поиск треков"""
        self.current_playlist = []
        self.playlist_type = "search"
        self.current_playlist_id = None
        
        try:
            result = self.vk_client.search_audio(query, count=count)
            
            for item in result.get('items', []):
                track = create_track_info(item)
                if track:
                    self.current_playlist.append(track)
            
            logger.info(f"Найдено треков: {len(self.current_playlist)}")
            return self.current_playlist
            
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            return []
    
    def load_recommendations(self, rec_type, count=100):
        """Загрузка рекомендаций"""
        self.current_playlist = []
        self.playlist_type = "recommendations"
        self.current_playlist_id = None
        
        rec_map = {
            "for_you": {"section": "for_you"},
            "discoveries": {"section": "discoveries"},
            "new": {"section": "new"},
        }
        
        # Для дня недели
        if rec_type.startswith('day'):
            day_num = int(rec_type.replace('day', ''))
            params = {"section": "day", "day": day_num}
        else:
            params = rec_map.get(rec_type, {"section": "for_you"})
        
        try:
            recommendations = self.vk_client.get_recommendations(
                section=params.get("section"),
                day=params.get("day"),
                count=count
            )
            
            for item in recommendations.get('items', []):
                track = create_track_info(item)
                if track:
                    self.current_playlist.append(track)
            
            logger.info(f"Загружено рекомендаций: {len(self.current_playlist)}")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки рекомендаций: {e}")
        
        # Если не удалось загрузить, пробуем через поиск
        if len(self.current_playlist) == 0:
            self._load_recommendations_via_search(rec_type)
        
        return self.current_playlist
    
    def _load_recommendations_via_search(self, rec_type):
        """Загрузка рекомендаций через поиск (запасной вариант)"""
        search_queries = {
            "for_you": "для вас",
            "discoveries": "открытия",
            "new": "новинки",
            "day": "плейлист дня"
        }
        
        query = search_queries.get(rec_type, "")
        if rec_type.startswith('day'):
            query = f"{search_queries['day']} {rec_type.replace('day', '')}"
        
        if query:
            try:
                result = self.vk_client.search_audio(query, count=100)
                
                for item in result.get('items', []):
                    track = create_track_info(item)
                    if track:
                        self.current_playlist.append(track)
                
                logger.info(f"Загружено рекомендаций через поиск: {len(self.current_playlist)}")
                
            except Exception as e:
                logger.error(f"Ошибка загрузки рекомендаций через поиск: {e}")
    
    def get_track_display_list(self):
        """Возвращает список форматированных названий треков"""
        return [get_track_display_text(track) for track in self.current_playlist]
    
    def get_current_playlist(self):
        return self.current_playlist
    
    def get_playlist_count(self):
        return len(self.current_playlist)
