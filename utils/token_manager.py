"""Управление токенами"""

import json
import os
from utils.logger import logger


class TokenManager:
    def __init__(self, token_file="vk_token.json"):
        self.token_file = token_file
        self.token = None
        self.user_id = None
    
    def load_token(self):
        """Загрузка сохраненного токена"""
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r') as f:
                    data = json.load(f)
                    self.token = data.get('token')
                    self.user_id = data.get('user_id')
                    if self.token:
                        logger.info(f"Загружен токен: {self.token[:30]}...")
                        return True
        except Exception as e:
            logger.error(f"Ошибка загрузки токена: {e}")
        return False
    
    def save_token(self, token, user_id=None):
        """Сохранение токена и ID пользователя"""
        try:
            data = {'token': token}
            if user_id:
                data['user_id'] = user_id
            with open(self.token_file, 'w') as f:
                json.dump(data, f)
            self.token = token
            if user_id:
                self.user_id = user_id
            logger.info(f"Токен сохранен: {token[:30]}...")
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения токена: {e}")
            return False
    
    def delete_token(self):
        """Удаление сохраненного токена"""
        try:
            if os.path.exists(self.token_file):
                os.remove(self.token_file)
                logger.info("Токен удален")
                return True
        except Exception as e:
            logger.error(f"Ошибка удаления токена: {e}")
        return False
    
    def get_token(self):
        return self.token
    
    def get_user_id(self):
        return self.user_id
    
    def clear(self):
        self.token = None
        self.user_id = None
