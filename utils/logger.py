"""Логирование"""

from datetime import datetime
import os
from config.settings import DEBUG_MODE, LOG_FILE


class Logger:
    def __init__(self):
        self.debug_mode = DEBUG_MODE
        
    def log(self, message, level="INFO"):
        """Логирование сообщения"""
        if not self.debug_mode and level != "ERROR":
            return
            
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        
        # Вывод в консоль
        print(log_message)
        
        # Запись в файл
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(log_message + "\n")
        except:
            pass
    
    def info(self, message):
        self.log(message, "INFO")
    
    def error(self, message):
        self.log(message, "ERROR")
    
    def debug(self, message):
        self.log(message, "DEBUG")
    
    def warning(self, message):
        self.log(message, "WARNING")


# Глобальный экземпляр логгера
logger = Logger()
