"""Клиент для работы с VK API"""

import vk_api
from utils.logger import logger
from utils.token_manager import TokenManager
from config import settings


class VKClient:
    def __init__(self):
        self.vk_session = None
        self.vk_api = None
        self.user_id = None
        self.token_manager = TokenManager()
        
    def login_with_token(self, token):
        """Вход с использованием токена"""
        try:
            logger.info("Попытка входа с токеном...")
            
            if not token or len(token) < 20:
                logger.error("Токен слишком короткий или пустой")
                return False
            
            self.vk_session = vk_api.VkApi(token=token)
            self.vk_api = self.vk_session.get_api()
            
            logger.info("Проверка токена...")
            user_info = self.vk_api.users.get()
            
            if user_info and len(user_info) > 0:
                self.user_id = user_info[0]['id']
                logger.info(f"Успешная авторизация: {user_info[0]['first_name']} (ID: {self.user_id})")
                return True
            
            return False
            
        except vk_api.exceptions.ApiError as e:
            error_msg = str(e)
            logger.error(f"API ошибка: {error_msg}")
            raise
            
        except Exception as e:
            logger.error(f"Неизвестная ошибка: {e}")
            raise
    
    def get_user_info(self):
        """Получение информации о пользователе"""
        try:
            if not self.vk_api:
                return None
            user_info = self.vk_api.users.get()
            if user_info and len(user_info) > 0:
                return user_info[0]
            return None
        except Exception as e:
            logger.error(f"Ошибка получения информации о пользователе: {e}")
            return None
    
    def get_audio(self, owner_id=None, offset=0, count=200, playlist_id=None):
        """Получение аудиозаписей"""
        try:
            params = {
                'owner_id': owner_id or self.user_id,
                'offset': offset,
                'count': count
            }
            if playlist_id:
                params['playlist_id'] = playlist_id
            
            return self.vk_api.audio.get(**params)
        except Exception as e:
            logger.error(f"Ошибка получения аудио: {e}")
            raise
    
    def search_audio(self, query, count=200):
        """Поиск аудиозаписей"""
        try:
            return self.vk_api.audio.search(q=query, count=count)
        except Exception as e:
            logger.error(f"Ошибка поиска аудио: {e}")
            raise
    
    def get_playlists(self, owner_id=None, count=100):
        """Получение списка плейлистов"""
        try:
            return self.vk_api.audio.getPlaylists(
                owner_id=owner_id or self.user_id,
                count=count
            )
        except Exception as e:
            logger.error(f"Ошибка получения плейлистов: {e}")
            raise
    
    def get_recommendations(self, section="for_you", day=None, count=100):
        """Получение рекомендаций"""
        try:
            params = {'section': section, 'count': count}
            if day is not None:
                params['day'] = day
            return self.vk_api.audio.getRecommendations(**params)
        except Exception as e:
            logger.error(f"Ошибка получения рекомендаций: {e}")
            raise
    
    def execute_code(self, code):
        """Выполнение VKScript"""
        try:
            return self.vk_api.execute(code=code)
        except Exception as e:
            logger.error(f"Ошибка выполнения execute: {e}")
            raise
    
    def is_authenticated(self):
        return self.vk_api is not None
    
    def logout(self):
        self.vk_session = None
        self.vk_api = None
        self.user_id = None
        self.token_manager.clear()
