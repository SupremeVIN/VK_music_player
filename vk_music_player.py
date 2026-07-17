import sys
import json
import requests
import vk_api
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from datetime import datetime
import threading
import time
import webbrowser
from urllib.parse import urlparse, parse_qs

class VKMusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VK Music Player")
        self.setGeometry(100, 100, 800, 600)
        
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
            QLineEdit {
                background-color: #16213e;
                color: white;
                border: 1px solid #0f3460;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
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
                background-color: #0f3460;
                border-radius: 3px;
            }
        """)
        
        # Переменные для VK API
        self.vk_session = None
        self.vk_api = None
        self.current_playlist = []
        self.current_index = -1
        self.is_playing = False
        self.token = None
        
        # ID приложения VK (можно использовать тестовый)
        self.app_id = 6287487  # Тестовый ID, замените на свой
        
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
        
        # Кнопка обновления
        self.refresh_btn = QPushButton("Обновить плейлисты")
        self.refresh_btn.clicked.connect(self.load_playlists)
        self.refresh_btn.setEnabled(False)
        auth_layout.addWidget(self.refresh_btn)
        
        main_layout.addLayout(auth_layout)
        
        # Поиск
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск музыки...")
        self.search_input.returnPressed.connect(self.search_music)
        
        self.search_btn = QPushButton("Поиск")
        self.search_btn.clicked.connect(self.search_music)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        main_layout.addLayout(search_layout)
        
        # Список треков
        self.music_list = QListWidget()
        self.music_list.itemDoubleClicked.connect(self.play_selected)
        main_layout.addWidget(self.music_list)
        
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
        self.track_info.setStyleSheet("font-size: 16px; color: #a8a8b8;")
        main_layout.addWidget(self.track_info)
    
    def load_token(self):
        """Загрузка сохраненного токена"""
        try:
            if os.path.exists('vk_token.json'):
                with open('vk_token.json', 'r') as f:
                    data = json.load(f)
                    self.token = data.get('token')
                    if self.token:
                        self.login_with_token()
        except:
            pass
    
    def save_token(self, token):
        """Сохранение токена"""
        try:
            with open('vk_token.json', 'w') as f:
                json.dump({'token': token}, f)
            self.token = token
        except:
            pass
    
    def login_with_token(self):
        """Вход с использованием сохраненного токена"""
        try:
            self.vk_session = vk_api.VkApi(token=self.token)
            self.vk_api = self.vk_session.get_api()
            
            # Проверка токена
            user_info = self.vk_api.users.get()
            if user_info:
                self.status_label.setText(f"Авторизован: {user_info[0]['first_name']} {user_info[0]['last_name']}")
                self.status_label.setStyleSheet("color: #4ecdc4;")
                self.login_btn.setText("Выйти")
                self.refresh_btn.setEnabled(True)
                self.load_playlists()
                return True
        except Exception as e:
            print(f"Ошибка при входе с токеном: {e}")
            self.token = None
            return False
        return False
    
    def login_vk(self):
        """Авторизация через VK с получением токена"""
        if self.token and self.vk_session:
            # Выход
            self.token = None
            self.vk_session = None
            self.vk_api = None
            self.status_label.setText("Не авторизован")
            self.status_label.setStyleSheet("color: #ff6b6b;")
            self.login_btn.setText("Войти в VK")
            self.refresh_btn.setEnabled(False)
            self.music_list.clear()
            self.play_btn.setEnabled(False)
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            self.track_info.setText("Нет выбранного трека")
            try:
                os.remove('vk_token.json')
            except:
                pass
            return
        
        # Показываем диалог для получения токена
        auth_dialog = QDialog(self)
        auth_dialog.setWindowTitle("Авторизация в VK")
        auth_dialog.setFixedSize(500, 300)
        auth_dialog.setStyleSheet("""
            QDialog {
                background-color: #1a1a2e;
            }
            QLabel {
                color: white;
                font-size: 14px;
            }
            QPushButton {
                background-color: #0f3460;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1a4a7a;
            }
            QLineEdit {
                background-color: #16213e;
                color: white;
                border: 1px solid #0f3460;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
        """)
        
        layout = QVBoxLayout(auth_dialog)
        
        info_label = QLabel("Для авторизации введите токен доступа VK")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Поле для ввода токена
        token_input = QLineEdit()
        token_input.setPlaceholderText("Вставьте токен сюда...")
        layout.addWidget(token_input)
        
        # Кнопка для получения токена в браузере
        get_token_btn = QPushButton("Получить токен в браузере")
        get_token_btn.clicked.connect(lambda: self.get_token_in_browser())
        layout.addWidget(get_token_btn)
        
        # Инструкция
        instruction = QLabel(
            "1. Нажмите кнопку для получения токена\n"
            "2. Выберите 'Разрешить' в браузере\n"
            "3. Скопируйте токен из адресной строки\n"
            "4. Вставьте его в поле и нажмите 'Войти'"
        )
        instruction.setStyleSheet("color: #a8a8b8; font-size: 12px;")
        layout.addWidget(instruction)
        
        # Кнопка входа
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(auth_dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        login_btn = QPushButton("Войти")
        login_btn.clicked.connect(lambda: self.process_token_input(token_input.text(), auth_dialog))
        btn_layout.addWidget(login_btn)
        
        layout.addLayout(btn_layout)
        
        auth_dialog.exec()
    
    def get_token_in_browser(self):
        """Открывает страницу для получения токена"""
        # URL для OAuth авторизации
        redirect_uri = "https://oauth.vk.com/blank.html"
        scope = "audio"  # Права на музыку
        url = f"https://oauth.vk.com/authorize?client_id={self.app_id}&display=page&redirect_uri={redirect_uri}&scope={scope}&response_type=token&v=5.131"
        
        webbrowser.open(url)
        
        QMessageBox.information(
            self,
            "Инструкция",
            "1. В браузере откроется страница VK\n"
            "2. Нажмите 'Разрешить'\n"
            "3. Из адресной строки скопируйте часть после 'access_token='\n"
            "   (до '&expires_in')\n"
            "4. Вставьте скопированный токен в поле"
        )
    
    def process_token_input(self, token, dialog):
        """Обработка введенного токена"""
        if not token:
            QMessageBox.warning(self, "Ошибка", "Введите токен доступа")
            return
        
        # Сохраняем токен
        self.token = token
        self.save_token(token)
        
        try:
            self.vk_session = vk_api.VkApi(token=token)
            self.vk_api = self.vk_session.get_api()
            
            # Проверяем токен
            user_info = self.vk_api.users.get()
            if user_info:
                self.status_label.setText(f"Авторизован: {user_info[0]['first_name']} {user_info[0]['last_name']}")
                self.status_label.setStyleSheet("color: #4ecdc4;")
                self.login_btn.setText("Выйти")
                self.refresh_btn.setEnabled(True)
                dialog.accept()
                self.load_playlists()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось получить данные пользователя. Проверьте токен.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка авторизации: {str(e)}")
    
    def load_playlists(self):
        """Загрузка плейлистов пользователя"""
        if not self.vk_api:
            return
        
        try:
            self.music_list.clear()
            self.current_playlist = []
            
            # Получаем аудиозаписи пользователя
            audio = self.vk_api.audio.get(count=100)
            
            for item in audio['items']:
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
                    self.music_list.addItem(display_text)
            
            if self.current_playlist:
                self.status_label.setText(f"Загружено треков: {len(self.current_playlist)}")
            
        except Exception as e:
            QMessageBox.warning(self, "Предупреждение", f"Не удалось загрузить плейлисты: {str(e)}")
    
    def search_music(self):
        """Поиск музыки"""
        if not self.vk_api:
            QMessageBox.warning(self, "Ошибка", "Сначала авторизуйтесь в VK")
            return
        
        query = self.search_input.text().strip()
        if not query:
            self.load_playlists()
            return
        
        try:
            self.music_list.clear()
            self.current_playlist = []
            
            # Поиск аудиозаписей
            result = self.vk_api.audio.search(q=query, count=100)
            
            for item in result['items']:
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
                    self.music_list.addItem(display_text)
            
            self.status_label.setText(f"Найдено треков: {len(self.current_playlist)}")
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось выполнить поиск: {str(e)}")
    
    def play_selected(self, item):
        """Воспроизведение выбранного трека"""
        index = self.music_list.row(item)
        if 0 <= index < len(self.current_playlist):
            self.current_index = index
            self.play_track(index)
    
    def play_track(self, index):
        """Воспроизведение трека по индексу"""
        if 0 <= index < len(self.current_playlist):
            track = self.current_playlist[index]
            
            # Обновляем информацию
            self.track_info.setText(f"🎵 {track['artist']} - {track['title']}")
            
            # Загружаем и воспроизводим
            self.player.setSource(QUrl(track['url']))
            self.player.play()
            self.is_playing = True
            self.play_btn.setText("⏸")
            self.play_btn.setEnabled(True)
            self.prev_btn.setEnabled(True)
            self.next_btn.setEnabled(True)
            
            # Выделяем трек в списке
            self.music_list.setCurrentRow(index)
            
            # Запускаем таймер обновления
            self.timer.start(1000)
    
    def toggle_play(self):
        """Воспроизведение/Пауза"""
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.play_btn.setText("▶")
            self.is_playing = False
        else:
            self.player.play()
            self.play_btn.setText("⏸")
            self.is_playing = True
    
    def play_next(self):
        """Следующий трек"""
        if self.current_index < len(self.current_playlist) - 1:
            self.current_index += 1
            self.play_track(self.current_index)
    
    def play_previous(self):
        """Предыдущий трек"""
        if self.current_index > 0:
            self.current_index -= 1
            self.play_track(self.current_index)
    
    def format_duration(self, seconds):
        """Форматирование длительности"""
        if not seconds:
            return "0:00"
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"
    
    def position_changed(self, position):
        """Обновление позиции воспроизведения"""
        duration = self.player.duration()
        if duration > 0:
            progress = int((position / duration) * 100)
            self.progress_bar.setValue(progress)
    
    def update_progress(self):
        """Обновление прогресса"""
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            position = self.player.position()
            duration = self.player.duration()
            if duration > 0:
                progress = int((position / duration) * 100)
                self.progress_bar.setValue(progress)
    
    def playback_state_changed(self, state):
        """Обработка изменения состояния воспроизведения"""
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self.is_playing = False
            self.play_btn.setText("▶")
            self.timer.stop()
            # Автоматическое воспроизведение следующего трека
            if self.current_index < len(self.current_playlist) - 1:
                self.play_next()
    
    def change_volume(self, value):
        """Изменение громкости"""
        self.audio_output.setVolume(value / 100)

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = VKMusicPlayer()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
