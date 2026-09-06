"""Диалог авторизации"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
import webbrowser

from config import settings
from ui.styles import get_auth_dialog_styles
from utils.helpers import extract_token_from_url
from utils.logger import logger


class AuthDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Авторизация в VK")
        self.setFixedSize(700, 550)
        self.setStyleSheet(get_auth_dialog_styles())
        
        self.token = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Заголовок
        info_label = QLabel("Введите полный URL с токеном или сам токен")
        info_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4ecdc4;")
        layout.addWidget(info_label)
        
        # Поле для ввода
        input_label = QLabel("Вставьте сюда полный URL из адресной строки:")
        input_label.setStyleSheet("color: #a8a8b8; margin-top: 10px;")
        layout.addWidget(input_label)
        
        self.token_input = QTextEdit()
        self.token_input.setPlaceholderText(
            "Вставьте URL целиком, например:\n"
            "https://oauth.vk.com/blank.html#access_token=vk1.a.xxxxx...&expires_in=86400&user_id=123\n\n"
            "Или просто токен:\n"
            "vk1.a.xxxxx..."
        )
        self.token_input.setMaximumHeight(120)
        layout.addWidget(self.token_input)
        
        # Кнопка извлечения
        extract_btn = QPushButton("Извлечь токен из URL")
        extract_btn.clicked.connect(self.extract_token)
        layout.addWidget(extract_btn)
        
        # Отображение извлеченного токена
        extract_label = QLabel("Извлеченный токен:")
        extract_label.setStyleSheet("color: #a8a8b8; margin-top: 10px;")
        layout.addWidget(extract_label)
        
        self.extracted_token_display = QTextEdit()
        self.extracted_token_display.setPlaceholderText("Здесь появится извлеченный токен...")
        self.extracted_token_display.setMaximumHeight(60)
        self.extracted_token_display.setReadOnly(True)
        layout.addWidget(self.extracted_token_display)
        
        # Кнопка получения токена
        get_token_btn = QPushButton("Получить токен в браузере")
        get_token_btn.clicked.connect(self.get_token_in_browser)
        layout.addWidget(get_token_btn)
        
        # Инструкция
        instruction = QLabel(
            "Инструкция:\n"
            "1. Нажмите кнопку для получения токена в браузере\n"
            "2. Войдите в VK и разрешите доступ\n"
            "3. Скопируйте ВЕСЬ URL из адресной строки\n"
            "4. Вставьте его в поле выше и нажмите 'Извлечь токен'\n"
            "5. Или просто вставьте токен и нажмите 'Войти'\n\n"
            "Токен привязывается к вашему IP!"
        )
        instruction.setProperty("class", "instruction")
        layout.addWidget(instruction)
        
        # Отладочная информация
        debug_label = QLabel("Отладочная информация:")
        debug_label.setStyleSheet("color: #a8a8b8; font-size: 12px; margin-top: 10px;")
        layout.addWidget(debug_label)
        
        self.debug_text = QTextEdit()
        self.debug_text.setMaximumHeight(80)
        self.debug_text.setReadOnly(True)
        self.debug_text.setPlainText("Готов к авторизации...")
        layout.addWidget(self.debug_text)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        login_btn = QPushButton("Войти")
        login_btn.clicked.connect(self.process_token)
        btn_layout.addWidget(login_btn)
        
        layout.addLayout(btn_layout)
    
    def extract_token(self):
        """Извлекает токен из введенного текста"""
        text = self.token_input.toPlainText().strip()
        if not text:
            self.debug_text.append("Введите URL или токен")
            QMessageBox.warning(self, "Ошибка", "Введите URL или токен")
            return
        
        self.debug_text.append(f"Получен текст: {text[:50]}...")
        
        token = extract_token_from_url(text)
        
        if token:
            self.debug_text.append(f"Токен извлечен: {token[:30]}...")
            self.extracted_token_display.setText(token)
            QMessageBox.information(self, "Успех", 
                "Токен успешно извлечен!\n\n"
                f"Токен: {token[:30]}...\n\n"
                "Нажмите 'Войти' для авторизации.")
        else:
            self.debug_text.append("Не удалось извлечь токен")
            QMessageBox.warning(self, "Ошибка", 
                "Не удалось извлечь токен.\n\n"
                "Убедитесь, что:\n"
                "1. Вы скопировали полный URL\n"
                "2. В URL есть access_token=\n"
                "3. Или введите токен вручную")
    
    def get_token_in_browser(self):
        """Открывает страницу для получения токена"""
        url = f"https://oauth.vk.com/authorize?client_id={settings.VK_APP_ID}&display=page&redirect_uri={settings.VK_REDIRECT_URI}&scope={settings.VK_SCOPE}&response_type=token&v={settings.VK_API_VERSION}"
        
        webbrowser.open(url)
        
        QMessageBox.information(
            self,
            "Инструкция по получению токена",
            "1. В браузере откроется страница VK\n"
            "2. Нажмите 'Разрешить'\n"
            "3. Скопируйте ВЕСЬ URL из адресной строки\n"
            "4. Вставьте его в поле и нажмите 'Извлечь токен'\n"
            "5. Или вручную скопируйте часть после 'access_token='\n"
            "   (до '&expires_in')\n\n"
            "ВАЖНО: Токен будет привязан к текущему IP!"
        )
    
    def process_token(self):
        """Обработка введенного токена"""
        token = self.extracted_token_display.toPlainText().strip()
        
        if not token:
            text = self.token_input.toPlainText().strip()
            if text:
                token = extract_token_from_url(text)
                if token:
                    self.extracted_token_display.setText(token)
                    self.debug_text.append(f"Автоматически извлечен токен из URL")
                else:
                    if text.startswith('vk1.a.') and len(text) > 50:
                        token = text
                    else:
                        self.debug_text.append("Не удалось найти токен")
                        QMessageBox.warning(self, "Ошибка", 
                            "Не удалось найти токен.\n\n"
                            "Убедитесь, что вы ввели правильный URL или токен.")
                        return
        
        if not token:
            self.debug_text.append("Ошибка: токен не введен")
            QMessageBox.warning(self, "Ошибка", "Введите токен доступа")
            return
        
        self.debug_text.append(f"Токен для входа: {token[:30]}...")
        self.debug_text.append(f"Длина токена: {len(token)} символов")
        
        if not token.startswith('vk1.a.'):
            self.debug_text.append("Токен не начинается с 'vk1.a.'")
            QMessageBox.warning(self, "Неверный формат", 
                "Токен должен начинаться с 'vk1.a.'")
            return
        
        self.token = token
        self.accept()
    
    def get_token(self):
        return self.token
