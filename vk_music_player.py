import sys
import os
import json
import requests
import vk_api
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from datetime import datetime
import webbrowser
import time
import re
from urllib.parse import urlparse, parse_qs

class VKMusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VK Music Player Pro")
        self.setGeometry(100, 100, 1000, 700)
        
        # Настройка стиля
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a2e;
            }
            QListWidget {
                background-color: #16213e;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #0f3460;
            }
            QListWidget::item:selected {
                background-color: #0f3460;
            }
            QListWidget::item:hover {
                background-color: #1a2a4a;
            }
            QPushButton {
                background-color: #0f3460;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1a4a7a;
            }
            QPushButton:disabled {
                background-color: #2a2a4a;
                color: #666;
            }
            QLineEdit, QTextEdit {
                background-color: #16213e;
                color: white;
                border: 1px solid #0f3460;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
            QTextEdit {
                font-family: monospace;
                font-size: 12px;
                color: #a8a8b8;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
            }
            QProgressBar {
                background-color: #16213e;
                border: none;
                border-radius: 3px;
                height: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4ecdc4;
                border-radius: 3px;
            }
            QTabWidget::pane {
                background-color: transparent;
                border: none;
            }
            QTabBar::tab {
                background-color: #16213e;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px 5px 0 0;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #0f3460;
            }
            QTabBar::tab:hover {
                background-color: #1a2a4a;
            }
            QScrollBar:vertical {
                background-color: #16213e;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #0f3460;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #1a4a7a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        
        # Переменные для VK API
        self.vk_session = None
        self.vk_api = None
        self.current_playlist = []
        self.current_index = -1
        self.is_playing = False
        self.token = None
        self.playlists = []
        self.current_playlist_id = None
        self.playlist_type = "my"
        self.debug_mode = True
        self.user_id = None
        self.total_tracks_loaded = 0
        
        # ID приложения VK
        self.app_id = 6287487
        self.redirect_uri = "https://oauth.vk.com/blank.html"
        
        # Инициализация медиа плеера
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        # Создание UI
        self.init_ui()
        
        # Проверка сохраненного токена
        self.load_token()
        
        # Таймер для обновления прогресса
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        
        # Подключение сигналов
        self.player.positionChanged.connect(self.position_changed)
        self.player.playbackStateChanged.connect(self.playback_state_changed)
    
    def init_ui(self):
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Верхняя панель с авторизацией
        auth_layout = QHBoxLayout()
        
        self.login_btn = QPushButton("Войти в VK")
        self.login_btn.clicked.connect(self.login_vk)
        auth_layout.addWidget(self.login_btn)
        
        self.status_label = QLabel("Не авторизован")
        self.status_label.setStyleSheet("color: #ff6b6b;")
        auth_layout.addWidget(self.status_label)
        
        auth_layout.addStretch()
        
        # Кнопка загрузки
        self.load_btn = QPushButton("Загрузить еще")
        self.load_btn.clicked.connect(self.load_more_tracks)
        self.load_btn.setEnabled(False)
        auth_layout.addWidget(self.load_btn)
        
        # Кнопка отладки
        self.debug_btn = QPushButton("🐛 Debug")
        self.debug_btn.clicked.connect(self.show_debug_info)
        self.debug_btn.setEnabled(True)
        auth_layout.addWidget(self.debug_btn)
        
        main_layout.addLayout(auth_layout)
        
        # Вкладки
        self.tabs = QTabWidget()
        
        # Вкладка "Моя музыка"
        self.my_music_tab = QWidget()
        self.init_my_music_tab()
        self.tabs.addTab(self.my_music_tab, "🎵 Моя музыка")
        
        # Вкладка "Плейлисты"
        self.playlists_tab = QWidget()
        self.init_playlists_tab()
        self.tabs.addTab(self.playlists_tab, "📁 Плейлисты")
        
        # Вкладка "Поиск"
        self.search_tab = QWidget()
        self.init_search_tab()
        self.tabs.addTab(self.search_tab, "🔍 Поиск")
        
        main_layout.addWidget(self.tabs)
        
        # Панель управления
        control_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("⏮")
        self.prev_btn.clicked.connect(self.play_previous)
        self.prev_btn.setEnabled(False)
        control_layout.addWidget(self.prev_btn)
        
        self.play_btn = QPushButton("▶")
        self.play_btn.clicked.connect(self.toggle_play)
        self.play_btn.setEnabled(False)
        control_layout.addWidget(self.play_btn)
        
        self.next_btn = QPushButton("⏭")
        self.next_btn.clicked.connect(self.play_next)
        self.next_btn.setEnabled(False)
        control_layout.addWidget(self.next_btn)
        
        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        control_layout.addWidget(self.progress_bar)
        
        # Громкость
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.valueChanged.connect(self.change_volume)
        self.volume_slider.setMaximumWidth(100)
        control_layout.addWidget(self.volume_slider)
        
        main_layout.addLayout(control_layout)
        
        # Информация о текущем треке
        self.track_info = QLabel("Нет выбранного трека")
        self.track_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.track_info.setStyleSheet("font-size: 16px; color: #a8a8b8; padding: 10px;")
        main_layout.addWidget(self.track_info)
    
    def init_my_music_tab(self):
        layout = QVBoxLayout(self.my_music_tab)
        
        header = QLabel("Мои аудиозаписи")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #4ecdc4; padding: 10px;")
        layout.addWidget(header)
        
        self.music_list = QListWidget()
        self.music_list.itemDoubleClicked.connect(self.play_selected)
        layout.addWidget(self.music_list)
        
        btn_layout = QHBoxLayout()
        self.load_all_btn = QPushButton("Загрузить все треки")
        self.load_all_btn.clicked.connect(self.load_all_tracks)
        self.load_all_btn.setEnabled(False)
        btn_layout.addWidget(self.load_all_btn)
        
        self.tracks_count_label = QLabel("Всего треков: 0")
        self.tracks_count_label.setStyleSheet("color: #a8a8b8;")
        btn_layout.addWidget(self.tracks_count_label)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
    
    def init_playlists_tab(self):
        layout = QHBoxLayout(self.playlists_tab)
        
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 10, 0)
        
        header = QLabel("Ваши плейлисты")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #4ecdc4;")
        left_layout.addWidget(header)
        
        self.playlists_list = QListWidget()
        self.playlists_list.itemClicked.connect(self.load_playlist_tracks)
        self.playlists_list.setMaximumWidth(300)
        left_layout.addWidget(self.playlists_list)
        
        layout.addWidget(left_widget)
        
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        self.playlist_tracks_label = QLabel("Выберите плейлист")
        self.playlist_tracks_label.setStyleSheet("font-size: 16px; color: #a8a8b8; padding: 10px;")
        right_layout.addWidget(self.playlist_tracks_label)
        
        self.playlist_tracks_list = QListWidget()
        self.playlist_tracks_list.itemDoubleClicked.connect(self.play_selected_from_playlist)
        right_layout.addWidget(self.playlist_tracks_list)
        
        layout.addWidget(right_widget, stretch=2)
    
    def init_search_tab(self):
        layout = QVBoxLayout(self.search_tab)
        
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск музыки...")
        self.search_input.returnPressed.connect(self.search_music)
        
        self.search_btn = QPushButton("Найти")
        self.search_btn.clicked.connect(self.search_music)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        layout.addLayout(search_layout)
        
        self.search_results = QListWidget()
        self.search_results.itemDoubleClicked.connect(self.play_selected_from_search)
        layout.addWidget(self.search_results)
        
        self.search_count_label = QLabel("Найдено треков: 0")
        self.search_count_label.setStyleSheet("color: #a8a8b8; padding: 5px;")
        layout.addWidget(self.search_count_label)
    
    def extract_token_from_url(self, text):
        """Извлекает токен из полного URL или просто текста"""
        # Проверяем, есть ли в тексте access_token=
        if 'access_token=' not in text:
            return None
        
        # Пытаемся извлечь токен с помощью регулярного выражения
        # Ищем access_token= за которым следует строка до & или конца строки
        match = re.search(r'access_token=([^&\s]+)', text)
        if match:
            return match.group(1)
        
        # Альтернативный метод через parse_qs (если есть полный URL)
        try:
            # Если текст начинается с http, это URL
            if text.startswith('http'):
                parsed = urlparse(text)
                # Для URL с fragment (#)
                if parsed.fragment:
                    fragment_params = parse_qs(parsed.fragment)
                    if 'access_token' in fragment_params:
                        return fragment_params['access_token'][0]
                # Для URL с query string (?)
                if parsed.query:
                    query_params = parse_qs(parsed.query)
                    if 'access_token' in query_params:
                        return query_params['access_token'][0]
        except:
            pass
        
        return None
    
    def load_token(self):
        """Загрузка сохраненного токена"""
        try:
            if os.path.exists('vk_token.json'):
                with open('vk_token.json', 'r') as f:
                    data = json.load(f)
                    self.token = data.get('token')
                    self.user_id = data.get('user_id')
                    if self.token:
                        self.log_message(f"Загружен токен: {self.token[:30]}...")
                        success = self.login_with_token()
                        if not success:
                            self.log_message("Токен недействителен")
                            self.token = None
                            self.user_id = None
        except Exception as e:
            self.log_message(f"Ошибка загрузки токена: {e}")
    
    def save_token(self, token, user_id=None):
        """Сохранение токена и ID пользователя"""
        try:
            data = {'token': token}
            if user_id:
                data['user_id'] = user_id
            with open('vk_token.json', 'w') as f:
                json.dump(data, f)
            self.token = token
            if user_id:
                self.user_id = user_id
            self.log_message(f"Токен сохранен: {token[:30]}...")
        except Exception as e:
            self.log_message(f"Ошибка сохранения токена: {e}")
    
    def login_with_token(self):
        """Вход с использованием сохраненного токена"""
        try:
            self.log_message("Попытка входа с токеном...")
            
            if not self.token or len(self.token) < 20:
                self.log_message("Токен слишком короткий или пустой")
                return False
            
            self.vk_session = vk_api.VkApi(token=self.token)
            self.vk_api = self.vk_session.get_api()
            
            self.log_message("Проверка токена...")
            user_info = self.vk_api.users.get()
            
            if user_info and len(user_info) > 0:
                self.user_id = user_info[0]['id']
                self.log_message(f"Успешная авторизация: {user_info[0]['first_name']} (ID: {self.user_id})")
                self.status_label.setText(f"Авторизован: {user_info[0]['first_name']} {user_info[0]['last_name']}")
                self.status_label.setStyleSheet("color: #4ecdc4;")
                self.login_btn.setText("Выйти")
                self.load_all_btn.setEnabled(True)
                self.load_btn.setEnabled(True)
                
                self.load_all_tracks()
                self.load_playlists_list()
                return True
            return False
            
        except vk_api.exceptions.ApiError as e:
            error_msg = str(e)
            self.log_message(f"API ошибка: {error_msg}")
            
            if "another ip address" in error_msg.lower():
                QMessageBox.warning(self, "Ошибка IP", 
                    "Токен привязан к другому IP-адресу.\n\n"
                    "Получите новый токен с текущего компьютера.")
                return False
            else:
                QMessageBox.warning(self, "Ошибка API", f"Ошибка при обращении к API VK:\n{error_msg[:300]}")
                return False
                
        except Exception as e:
            self.log_message(f"Неизвестная ошибка: {e}")
            QMessageBox.warning(self, "Ошибка", f"Произошла ошибка:\n{str(e)[:300]}")
            return False
    
    def login_vk(self):
        """Авторизация через VK с автоматическим извлечением токена"""
        if self.token and self.vk_session:
            self.logout()
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Авторизация в VK")
        dialog.setFixedSize(700, 550)
        dialog.setStyleSheet("""
            QDialog { background-color: #1a1a2e; }
            QLabel { color: white; font-size: 14px; }
            QPushButton {
                background-color: #0f3460;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1a4a7a; }
            QLineEdit, QTextEdit {
                background-color: #16213e;
                color: white;
                border: 1px solid #0f3460;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
            QTextEdit {
                font-family: monospace;
                font-size: 12px;
                color: #a8a8b8;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        
        info_label = QLabel("🔑 Введите полный URL с токеном или сам токен")
        info_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4ecdc4;")
        layout.addWidget(info_label)
        
        # Поле для ввода URL или токена
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
        
        # Кнопка для автоматического извлечения токена
        extract_btn = QPushButton("🔍 Извлечь токен из URL")
        extract_btn.clicked.connect(self.extract_token_from_input)
        layout.addWidget(extract_btn)
        
        # Поле для отображения извлеченного токена
        extract_label = QLabel("Извлеченный токен:")
        extract_label.setStyleSheet("color: #a8a8b8; margin-top: 10px;")
        layout.addWidget(extract_label)
        
        self.extracted_token_display = QTextEdit()
        self.extracted_token_display.setPlaceholderText("Здесь появится извлеченный токен...")
        self.extracted_token_display.setMaximumHeight(60)
        self.extracted_token_display.setReadOnly(True)
        layout.addWidget(self.extracted_token_display)
        
        get_token_btn = QPushButton("🌐 Получить токен в браузере")
        get_token_btn.clicked.connect(lambda: self.get_token_in_browser(dialog))
        layout.addWidget(get_token_btn)
        
        instruction = QLabel(
            "📋 Инструкция:\n"
            "1. Нажмите кнопку для получения токена в браузере\n"
            "2. Войдите в VK и разрешите доступ\n"
            "3. Скопируйте ВЕСЬ URL из адресной строки\n"
            "4. Вставьте его в поле выше и нажмите 'Извлечь токен'\n"
            "5. Или просто вставьте токен и нажмите 'Войти'\n\n"
            "⚠️ Токен привязывается к вашему IP!"
        )
        instruction.setStyleSheet("color: #a8a8b8; font-size: 12px; padding: 10px; background-color: #16213e; border-radius: 5px;")
        layout.addWidget(instruction)
        
        # Поле для отладки
        debug_label = QLabel("🔍 Отладочная информация:")
        debug_label.setStyleSheet("color: #a8a8b8; font-size: 12px; margin-top: 10px;")
        layout.addWidget(debug_label)
        
        self.debug_text = QTextEdit()
        self.debug_text.setMaximumHeight(80)
        self.debug_text.setReadOnly(True)
        self.debug_text.setPlainText("Готов к авторизации...")
        layout.addWidget(self.debug_text)
        
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        login_btn = QPushButton("✅ Войти")
        login_btn.clicked.connect(lambda: self.process_token_input(dialog))
        btn_layout.addWidget(login_btn)
        
        layout.addLayout(btn_layout)
        dialog.exec()
    
    def extract_token_from_input(self):
        """Извлекает токен из введенного текста"""
        text = self.token_input.toPlainText().strip()
        if not text:
            self.debug_text.append("❌ Введите URL или токен")
            QMessageBox.warning(self, "Ошибка", "Введите URL или токен")
            return
        
        self.debug_text.append(f"📝 Получен текст: {text[:50]}...")
        
        # Пытаемся извлечь токен
        token = self.extract_token_from_url(text)
        
        if token:
            self.debug_text.append(f"✅ Токен извлечен: {token[:30]}...")
            self.extracted_token_display.setText(token)
            QMessageBox.information(self, "Успех", 
                "✅ Токен успешно извлечен!\n\n"
                f"Токен: {token[:30]}...\n\n"
                "Нажмите 'Войти' для авторизации.")
        else:
            self.debug_text.append("❌ Не удалось извлечь токен")
            QMessageBox.warning(self, "Ошибка", 
                "Не удалось извлечь токен.\n\n"
                "Убедитесь, что:\n"
                "1. Вы скопировали полный URL\n"
                "2. В URL есть access_token=\n"
                "3. Или введите токен вручную")
    
    def get_token_in_browser(self, dialog):
        """Открывает страницу для получения токена"""
        scope = "audio,offline"
        url = f"https://oauth.vk.com/authorize?client_id={self.app_id}&display=page&redirect_uri={self.redirect_uri}&scope={scope}&response_type=token&v=5.131"
        
        webbrowser.open(url)
        
        QMessageBox.information(
            dialog,
            "Инструкция по получению токена",
            "1. В браузере откроется страница VK\n"
            "2. Нажмите 'Разрешить'\n"
            "3. Скопируйте ВЕСЬ URL из адресной строки\n"
            "4. Вставьте его в поле и нажмите 'Извлечь токен'\n"
            "5. Или вручную скопируйте часть после 'access_token='\n"
            "   (до '&expires_in')\n\n"
            "⚠️ ВАЖНО: Токен будет привязан к текущему IP!"
        )
    
    def process_token_input(self, dialog):
        """Обработка введенного токена"""
        # Сначала проверяем, есть ли извлеченный токен
        token = self.extracted_token_display.toPlainText().strip()
        
        # Если нет, пробуем извлечь из основного поля
        if not token:
            text = self.token_input.toPlainText().strip()
            if text:
                token = self.extract_token_from_url(text)
                if token:
                    self.extracted_token_display.setText(token)
                    self.debug_text.append(f"✅ Автоматически извлечен токен из URL")
                else:
                    # Возможно, пользователь ввел просто токен
                    if text.startswith('vk1.a.') and len(text) > 50:
                        token = text
                    else:
                        self.debug_text.append("❌ Не удалось найти токен во введенном тексте")
                        QMessageBox.warning(self, "Ошибка", 
                            "Не удалось найти токен.\n\n"
                            "Убедитесь, что вы ввели правильный URL или токен.")
                        return
        
        if not token:
            self.debug_text.append("❌ Ошибка: токен не введен")
            QMessageBox.warning(self, "Ошибка", "Введите токен доступа")
            return
        
        self.debug_text.append(f"📝 Токен для входа: {token[:30]}...")
        self.debug_text.append(f"📏 Длина токена: {len(token)} символов")
        
        if not token.startswith('vk1.a.'):
            self.debug_text.append("⚠️ Токен не начинается с 'vk1.a.'")
            QMessageBox.warning(self, "Неверный формат", 
                "Токен должен начинаться с 'vk1.a.'\n"
                "Убедитесь, что вы скопировали правильную часть.")
            return
        
        self.token = token
        
        try:
            self.debug_text.append("🔄 Создание сессии VK...")
            self.vk_session = vk_api.VkApi(token=token)
            self.vk_api = self.vk_session.get_api()
            self.debug_text.append("✅ Сессия создана")
            
            self.debug_text.append("🔄 Проверка токена...")
            user_info = self.vk_api.users.get()
            
            if user_info and len(user_info) > 0:
                user_name = f"{user_info[0]['first_name']} {user_info[0]['last_name']}"
                self.user_id = user_info[0]['id']
                self.debug_text.append(f"✅ Авторизация успешна: {user_name} (ID: {self.user_id})")
                
                self.save_token(token, self.user_id)
                
                self.status_label.setText(f"Авторизован: {user_name}")
                self.status_label.setStyleSheet("color: #4ecdc4;")
                self.login_btn.setText("Выйти")
                self.load_all_btn.setEnabled(True)
                self.load_btn.setEnabled(True)
                dialog.accept()
                
                self.load_all_tracks()
                self.load_playlists_list()
                
                QMessageBox.information(self, "Успех", f"Добро пожаловать, {user_name}!")
            else:
                self.debug_text.append("❌ Не получены данные пользователя")
                QMessageBox.warning(self, "Ошибка", "Не удалось получить данные пользователя")
                
        except vk_api.exceptions.ApiError as e:
            error_msg = str(e)
            self.debug_text.append(f"❌ API ошибка: {error_msg}")
            
            if "another ip address" in error_msg.lower():
                QMessageBox.critical(self, "Ошибка IP", 
                    "Токен привязан к другому IP-адресу!\n\n"
                    "Получите новый токен с этого компьютера.")
            else:
                QMessageBox.critical(self, "Ошибка API", f"Ошибка:\n{error_msg[:300]}")
                
        except Exception as e:
            self.debug_text.append(f"❌ Неизвестная ошибка: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка:\n{str(e)[:300]}")
    
    def load_all_tracks(self):
        """Загрузка ВСЕХ аудиозаписей пользователя с пагинацией"""
        if not self.vk_api:
            return
        
        try:
            self.music_list.clear()
            self.current_playlist = []
            self.playlist_type = "my"
            self.total_tracks_loaded = 0
            
            offset = 0
            count = 200
            max_tracks = 2000
            
            self.status_label.setText("Загрузка треков...")
            self.tracks_count_label.setText("Загружается...")
            
            while self.total_tracks_loaded < max_tracks:
                self.log_message(f"Загрузка треков с offset={offset}")
                
                audio = self.vk_api.audio.get(
                    owner_id=self.user_id,
                    offset=offset,
                    count=count
                )
                
                items = audio.get('items', [])
                
                if not items:
                    self.log_message("Треки закончились")
                    break
                
                for item in items:
                    if 'title' in item and 'artist' in item and 'url' in item:
                        track_info = {
                            'title': item['title'],
                            'artist': item['artist'],
                            'duration': item.get('duration', 0),
                            'url': item['url'],
                            'id': item.get('id', 0)
                        }
                        self.current_playlist.append(track_info)
                        self.total_tracks_loaded += 1
                        
                        duration_str = self.format_duration(track_info['duration'])
                        display_text = f"{track_info['artist']} - {track_info['title']} [{duration_str}]"
                        self.music_list.addItem(display_text)
                        
                        if self.total_tracks_loaded % 50 == 0:
                            self.tracks_count_label.setText(f"Загружено: {self.total_tracks_loaded}")
                            QApplication.processEvents()
                
                self.log_message(f"Загружено {len(items)} треков, всего {self.total_tracks_loaded}")
                
                if len(items) < count:
                    self.log_message("Достигнут конец списка")
                    break
                
                offset += count
            
            self.tracks_count_label.setText(f"Всего треков: {len(self.current_playlist)}")
            self.status_label.setText(f"Загружено треков: {len(self.current_playlist)}")
            
            if len(self.current_playlist) == 0:
                self.music_list.addItem("🎵 У вас нет аудиозаписей")
            
            self.log_message(f"Загрузка завершена. Всего треков: {len(self.current_playlist)}")
            
        except Exception as e:
            self.log_message(f"Ошибка загрузки треков: {e}")
            QMessageBox.warning(self, "Предупреждение", f"Не удалось загрузить все треки: {str(e)}\n\nЗагружено: {len(self.current_playlist)} треков")
    
    def load_more_tracks(self):
        self.load_all_tracks()
    
    def load_playlists_list(self):
        """Загрузка списка плейлистов пользователя"""
        if not self.vk_api or not self.user_id:
            self.log_message("Нет API или user_id для загрузки плейлистов")
            return
        
        try:
            self.playlists_list.clear()
            self.playlists = []
            
            self.log_message(f"Загрузка плейлистов для user_id={self.user_id}")
            
            playlists = self.vk_api.audio.getPlaylists(
                owner_id=self.user_id,
                count=100
            )
            
            self.log_message(f"Получено плейлистов: {len(playlists.get('items', []))}")
            
            for playlist in playlists.get('items', []):
                playlist_info = {
                    'id': playlist['id'],
                    'owner_id': playlist['owner_id'],
                    'title': playlist['title'],
                    'count': playlist.get('count', 0),
                    'description': playlist.get('description', '')
                }
                self.playlists.append(playlist_info)
                
                display_text = f"📁 {playlist_info['title']} ({playlist_info['count']} треков)"
                self.playlists_list.addItem(display_text)
            
            if not self.playlists:
                self.playlists_list.addItem("Нет созданных плейлистов")
                self.log_message("Плейлисты не найдены")
            
        except Exception as e:
            self.log_message(f"Ошибка загрузки плейлистов: {e}")
            self.playlists_list.addItem(f"❌ Ошибка загрузки плейлистов")
    
    def load_playlist_tracks(self, item):
        """Загрузка треков выбранного плейлиста"""
        index = self.playlists_list.row(item)
        if index < 0 or index >= len(self.playlists):
            return
        
        playlist = self.playlists[index]
        
        try:
            self.playlist_tracks_list.clear()
            self.current_playlist = []
            self.playlist_type = "playlist"
            self.current_playlist_id = playlist['id']
            
            self.log_message(f"Загрузка плейлиста: {playlist['title']} (ID: {playlist['id']}, Owner: {playlist['owner_id']})")
            
            # Вариант 1: Пытаемся получить треки через audio.get с playlist_id
            try:
                self.log_message("Попытка получить треки через audio.get с playlist_id...")
                
                tracks_data = self.vk_api.audio.get(
                    owner_id=playlist['owner_id'],
                    playlist_id=playlist['id'],
                    count=200
                )
                
                items = tracks_data.get('items', [])
                self.log_message(f"Получено {len(items)} треков через audio.get")
                
                if items:
                    self._add_tracks_to_playlist(items)
                    self.log_message(f"✅ Загружено {len(self.current_playlist)} треков через audio.get")
            except Exception as e:
                self.log_message(f"Метод audio.get с playlist_id не сработал: {e}")
            
            # Вариант 2: Если не сработало, пробуем получить через execute
            if len(self.current_playlist) == 0:
                try:
                    self.log_message("Попытка получить треки через execute...")
                    
                    code = f"""
                    var playlist = API.audio.getPlaylistById({{
                        owner_id: {playlist['owner_id']},
                        playlist_id: {playlist['id']}
                    }});
                    
                    var tracks = [];
                    var i = 0;
                    while (i < 200 && i < playlist.count) {{
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
                    
                    result = self.vk_api.execute(code=code)
                    self.log_message(f"Результат execute: {list(result.keys()) if result else 'Нет данных'}")
                    
                    if result and 'tracks' in result:
                        items = result['tracks']
                        self.log_message(f"Получено {len(items)} треков через execute")
                        
                        if items:
                            self._add_tracks_to_playlist(items)
                            self.log_message(f"✅ Загружено {len(self.current_playlist)} треков через execute")
                except Exception as e:
                    self.log_message(f"Метод execute не сработал: {e}")
            
            # Вариант 3: Если execute не работает, пробуем через audio.get без playlist_id
            if len(self.current_playlist) == 0:
                try:
                    self.log_message("Попытка получить треки через фильтрацию всех аудиозаписей...")
                    
                    all_tracks = self.vk_api.audio.get(
                        owner_id=self.user_id,
                        count=600
                    )
                    
                    items = []
                    for track in all_tracks.get('items', []):
                        if 'playlist_id' in track and track['playlist_id'] == playlist['id']:
                            items.append(track)
                        elif 'playlist' in track and track['playlist'].get('id') == playlist['id']:
                            items.append(track)
                    
                    self.log_message(f"Найдено {len(items)} треков через фильтрацию")
                    
                    if items:
                        self._add_tracks_to_playlist(items)
                        self.log_message(f"✅ Загружено {len(self.current_playlist)} треков через фильтрацию")
                except Exception as e:
                    self.log_message(f"Метод фильтрации не сработал: {e}")
            
            # Обновляем информацию
            track_count = len(self.current_playlist)
            self.playlist_tracks_label.setText(f"Плейлист: {playlist['title']} ({track_count} треков)")
            self.status_label.setText(f"Загружено треков из плейлиста: {track_count}")
            
            if track_count == 0:
                self.playlist_tracks_list.addItem("❌ Не удалось загрузить треки из этого плейлиста")
                self.playlist_tracks_list.addItem("💡 Попробуйте обновить плейлисты и повторить")
                self.playlist_tracks_list.addItem("💡 Или откройте другой плейлист")
                self.log_message("Не удалось загрузить треки плейлиста")
            
        except Exception as e:
            self.log_message(f"Ошибка загрузки треков плейлиста: {e}")
            self.playlist_tracks_list.addItem(f"❌ Ошибка: {str(e)[:100]}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить треки плейлиста: {str(e)}")
    
    def _add_tracks_to_playlist(self, items):
        """Вспомогательный метод для добавления треков в плейлист"""
        for track in items:
            title = track.get('title', '')
            artist = track.get('artist', '')
            url = track.get('url', '')
            duration = track.get('duration', 0)
            track_id = track.get('id', 0)
            
            if not title and 'track' in track:
                track_data = track['track']
                title = track_data.get('title', '')
                artist = track_data.get('artist', '')
                url = track_data.get('url', '')
                duration = track_data.get('duration', 0)
                track_id = track_data.get('id', 0)
            
            elif not title and 'audio' in track:
                track_data = track['audio']
                title = track_data.get('title', '')
                artist = track_data.get('artist', '')
                url = track_data.get('url', '')
                duration = track_data.get('duration', 0)
                track_id = track_data.get('id', 0)
            
            elif not title and 'title' in track:
                title = track.get('title', '')
                artist = track.get('artist', '')
                url = track.get('url', '')
                duration = track.get('duration', 0)
                track_id = track.get('id', 0)
            
            if title and artist and url:
                track_info = {
                    'title': title,
                    'artist': artist,
                    'duration': duration,
                    'url': url,
                    'id': track_id
                }
                self.current_playlist.append(track_info)
                
                duration_str = self.format_duration(duration)
                display_text = f"{artist} - {title} [{duration_str}]"
                self.playlist_tracks_list.addItem(display_text)
                self.log_message(f"Добавлен трек: {artist} - {title}")
    
    def search_music(self):
        """Поиск музыки"""
        if not self.vk_api:
            QMessageBox.warning(self, "Ошибка", "Сначала авторизуйтесь в VK")
            return
        
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Ошибка", "Введите запрос для поиска")
            return
        
        try:
            self.search_results.clear()
            self.current_playlist = []
            self.playlist_type = "search"
            
            self.log_message(f"Поиск: {query}")
            
            result = self.vk_api.audio.search(q=query, count=200)
            
            for item in result.get('items', []):
                if 'title' in item and 'artist' in item and 'url' in item:
                    track_info = {
                        'title': item['title'],
                        'artist': item['artist'],
                        'duration': item.get('duration', 0),
                        'url': item['url'],
                        'id': item.get('id', 0)
                    }
                    self.current_playlist.append(track_info)
                    
                    duration_str = self.format_duration(track_info['duration'])
                    display_text = f"{track_info['artist']} - {track_info['title']} [{duration_str}]"
                    self.search_results.addItem(display_text)
            
            self.search_count_label.setText(f"Найдено треков: {len(self.current_playlist)}")
            self.status_label.setText(f"Найдено треков: {len(self.current_playlist)}")
            
            if len(self.current_playlist) == 0:
                self.search_results.addItem("Ничего не найдено")
            
        except Exception as e:
            self.log_message(f"Ошибка поиска: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось выполнить поиск: {str(e)}")
    
    def play_selected(self, item):
        self.play_selected_from_list(item, self.music_list)
    
    def play_selected_from_playlist(self, item):
        self.play_selected_from_list(item, self.playlist_tracks_list)
    
    def play_selected_from_search(self, item):
        self.play_selected_from_list(item, self.search_results)
    
    def play_selected_from_list(self, item, list_widget):
        index = list_widget.row(item)
        if 0 <= index < len(self.current_playlist):
            self.current_index = index
            self.play_track(index)
    
    def play_track(self, index):
        if 0 <= index < len(self.current_playlist):
            track = self.current_playlist[index]
            
            self.track_info.setText(f"🎵 {track['artist']} - {track['title']}")
            
            self.player.setSource(QUrl(track['url']))
            self.player.play()
            self.is_playing = True
            self.play_btn.setText("⏸")
            self.play_btn.setEnabled(True)
            self.prev_btn.setEnabled(True)
            self.next_btn.setEnabled(True)
            
            current_tab = self.tabs.currentIndex()
            if current_tab == 0 and hasattr(self, 'music_list'):
                self.music_list.setCurrentRow(index)
            elif current_tab == 1 and hasattr(self, 'playlist_tracks_list'):
                self.playlist_tracks_list.setCurrentRow(index)
            elif current_tab == 2 and hasattr(self, 'search_results'):
                self.search_results.setCurrentRow(index)
            
            self.timer.start(1000)
    
    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.play_btn.setText("▶")
            self.is_playing = False
        else:
            self.player.play()
            self.play_btn.setText("⏸")
            self.is_playing = True
    
    def play_next(self):
        if self.current_index < len(self.current_playlist) - 1:
            self.current_index += 1
            self.play_track(self.current_index)
    
    def play_previous(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.play_track(self.current_index)
    
    def format_duration(self, seconds):
        if not seconds:
            return "0:00"
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"
    
    def position_changed(self, position):
        duration = self.player.duration()
        if duration > 0:
            progress = int((position / duration) * 100)
            self.progress_bar.setValue(progress)
    
    def update_progress(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            position = self.player.position()
            duration = self.player.duration()
            if duration > 0:
                progress = int((position / duration) * 100)
                self.progress_bar.setValue(progress)
    
    def playback_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self.is_playing = False
            self.play_btn.setText("▶")
            self.timer.stop()
            if self.current_index < len(self.current_playlist) - 1:
                self.play_next()
    
    def change_volume(self, value):
        self.audio_output.setVolume(value / 100)
    
    def log_message(self, message):
        if self.debug_mode:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {message}")
    
    def show_debug_info(self):
        try:
            current_ip = requests.get('https://api.ipify.org', timeout=5).text
        except:
            current_ip = "Не удалось определить"
        
        info = f"""🐛 Отладочная информация:

🌐 Текущий IP: {current_ip}

👤 User ID: {self.user_id}
🔑 Токен: {'Есть' if self.token else 'Нет'}
📏 Длина токена: {len(self.token) if self.token else 0}

🔗 VK Session: {'Активна' if self.vk_session else 'Не активна'}
📊 VK API: {'Доступен' if self.vk_api else 'Не доступен'}

📂 Текущий плейлист: {len(self.current_playlist)} треков
🎵 Текущий индекс: {self.current_index}
▶️ Воспроизведение: {'Да' if self.is_playing else 'Нет'}

📁 Загружено плейлистов: {len(self.playlists)}
💾 Файл токена: {'Существует' if os.path.exists('vk_token.json') else 'Отсутствует'}
"""
        QMessageBox.information(self, "Отладка", info)
    
    def logout(self):
        self.token = None
        self.vk_session = None
        self.vk_api = None
        self.user_id = None
        self.current_playlist = []
        self.current_index = -1
        self.playlists = []
        
        self.status_label.setText("Не авторизован")
        self.status_label.setStyleSheet("color: #ff6b6b;")
        self.login_btn.setText("Войти в VK")
        self.load_all_btn.setEnabled(False)
        self.load_btn.setEnabled(False)
        
        self.music_list.clear()
        self.playlists_list.clear()
        self.playlist_tracks_list.clear()
        self.search_results.clear()
        
        self.play_btn.setEnabled(False)
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.track_info.setText("Нет выбранного трека")
        
        self.tracks_count_label.setText("Всего треков: 0")
        self.playlist_tracks_label.setText("Выберите плейлист")
        self.search_count_label.setText("Найдено треков: 0")
        
        try:
            os.remove('vk_token.json')
        except:
            pass

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = VKMusicPlayer()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
