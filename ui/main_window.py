"""Главное окно приложения"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt

from config import settings
from core.vk_client import VKClient
from core.music_player import MusicPlayer
from core.playlist_manager import PlaylistManager
from ui.styles import get_styles
from ui.widgets import AuthDialog, MusicListWidget, PlaylistWidget, SearchWidget
from utils.token_manager import TokenManager
from utils.logger import logger
from utils.helpers import get_track_display_text


class VKMusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VK Music Player Pro")
        self.setGeometry(100, 100, settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT)
        self.setStyleSheet(get_styles())
        
        # Инициализация компонентов
        self.vk_client = VKClient()
        self.player = MusicPlayer()
        self.playlist_manager = PlaylistManager(self.vk_client)
        self.token_manager = TokenManager()
        
        # Настройка обратных вызовов плеера
        self.player.position_changed_callback = self._on_position_changed
        self.player.state_changed_callback = self._on_player_state_changed
        
        # Инициализация UI
        self.init_ui()
        
        # Проверка сохраненного токена
        self.check_saved_token()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Верхняя панель
        self.init_top_panel(main_layout)
        
        # Вкладки
        self.init_tabs(main_layout)
        
        # Панель управления
        self.init_control_panel(main_layout)
        
        # Информация о треке
        self.track_info = QLabel("Нет выбранного трека")
        self.track_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.track_info.setProperty("class", "track_info")
        main_layout.addWidget(self.track_info)
    
    def init_top_panel(self, layout):
        auth_layout = QHBoxLayout()
        
        self.login_btn = QPushButton("Войти в VK")
        self.login_btn.clicked.connect(self.login)
        auth_layout.addWidget(self.login_btn)
        
        self.status_label = QLabel("Не авторизован")
        self.status_label.setStyleSheet("color: #ff6b6b;")
        auth_layout.addWidget(self.status_label)
        
        auth_layout.addStretch()
        
        self.load_btn = QPushButton("Загрузить еще")
        self.load_btn.clicked.connect(self.load_more)
        self.load_btn.setEnabled(False)
        auth_layout.addWidget(self.load_btn)
        
        self.debug_btn = QPushButton("Debug")
        self.debug_btn.clicked.connect(self.show_debug_info)
        auth_layout.addWidget(self.debug_btn)
        
        layout.addLayout(auth_layout)
    
    def init_tabs(self, layout):
        self.tabs = QTabWidget()
        
        # Вкладка рекомендаций
        self.recommendations_widget = self.create_recommendations_tab()
        self.tabs.addTab(self.recommendations_widget, "Рекомендации")
        
        # Вкладка моей музыки
        self.my_music_widget = self.create_my_music_tab()
        self.tabs.addTab(self.my_music_widget, "Моя музыка")
        
        # Вкладка плейлистов
        self.playlist_widget = self.create_playlist_tab()
        self.tabs.addTab(self.playlist_widget, "Плейлисты")
        
        # Вкладка поиска
        self.search_widget = self.create_search_tab()
        self.tabs.addTab(self.search_widget, "Поиск")
        
        layout.addWidget(self.tabs)
    
    def create_recommendations_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        header = QLabel("Собрано алгоритмами")
        header.setProperty("class", "header")
        layout.addWidget(header)
        
        # Кнопки рекомендаций
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.recommendations_btns = {}
        rec_types = [
            ("Для вас", "for_you"),
            ("Открытия", "discoveries"),
            ("Новинки", "new"),
            ("Плейлист дня 1", "day1"),
            ("Плейлист дня 2", "day2"),
            ("Плейлист дня 3", "day3"),
            ("Плейлист дня 4", "day4"),
            ("Плейлист дня 5", "day5")
        ]
        
        for label, key in rec_types:
            btn = QPushButton(label)
            btn.setProperty("type", key)
            btn.clicked.connect(lambda checked, k=key: self.load_recommendations(k))
            btn.setEnabled(False)
            self.recommendations_btns[key] = btn
            btn_layout.addWidget(btn)
        
        layout.addLayout(btn_layout)
        
        self.recommendations_list = QListWidget()
        self.recommendations_list.itemDoubleClicked.connect(
            lambda item: self.play_from_list(item, self.recommendations_list)
        )
        layout.addWidget(self.recommendations_list)
        
        self.recommendations_count_label = QLabel("Выберите категорию рекомендаций")
        self.recommendations_count_label.setProperty("class", "info")
        layout.addWidget(self.recommendations_count_label)
        
        return widget
    
    def create_my_music_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        header = QLabel("Мои аудиозаписи")
        header.setProperty("class", "header")
        layout.addWidget(header)
        
        self.music_list = QListWidget()
        self.music_list.itemDoubleClicked.connect(
            lambda item: self.play_from_list(item, self.music_list)
        )
        layout.addWidget(self.music_list)
        
        btn_layout = QHBoxLayout()
        self.load_all_btn = QPushButton("Загрузить все треки")
        self.load_all_btn.clicked.connect(self.load_all_tracks)
        self.load_all_btn.setEnabled(False)
        btn_layout.addWidget(self.load_all_btn)
        
        self.tracks_count_label = QLabel("Всего треков: 0")
        self.tracks_count_label.setProperty("class", "info")
        btn_layout.addWidget(self.tracks_count_label)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        return widget
    
    def create_playlist_tab(self):
        widget = PlaylistWidget()
        widget.playlist_selected.connect(self.load_playlist_tracks)
        widget.track_double_clicked.connect(
            lambda index: self.play_playlist_track(index)
        )
        return widget
    
    def create_search_tab(self):
        widget = SearchWidget()
        widget.search_requested.connect(self.search_music)
        widget.track_double_clicked.connect(
            lambda index: self.play_search_result(index)
        )
        return widget
    
    def init_control_panel(self, layout):
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
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        control_layout.addWidget(self.progress_bar)
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(settings.VOLUME_DEFAULT)
        self.volume_slider.valueChanged.connect(self.change_volume)
        self.volume_slider.setMaximumWidth(100)
        control_layout.addWidget(self.volume_slider)
        
        layout.addLayout(control_layout)
    
    def check_saved_token(self):
        """Проверка сохраненного токена"""
        if self.token_manager.load_token():
            token = self.token_manager.get_token()
            if token:
                self.login_with_token(token)
    
    def login_with_token(self, token):
        """Вход с использованием токена"""
        try:
            if self.vk_client.login_with_token(token):
                user_info = self.vk_client.get_user_info()
                if user_info:
                    self.user_authenticated(user_info)
            else:
                self.token_manager.clear()
                self.update_auth_status(False)
        except Exception as e:
            logger.error(f"Ошибка входа: {e}")
            self.token_manager.clear()
            self.update_auth_status(False)
            QMessageBox.warning(self, "Ошибка", f"Не удалось войти: {str(e)}")
    
    def login(self):
        """Авторизация через диалог"""
        if self.vk_client.is_authenticated():
            self.logout()
            return
        
        dialog = AuthDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            token = dialog.get_token()
            if token:
                self.login_with_token(token)
    
    def user_authenticated(self, user_info):
        """Обработка успешной авторизации"""
        user_name = f"{user_info['first_name']} {user_info['last_name']}"
        self.user_id = user_info['id']
        
        self.token_manager.save_token(self.vk_client.token_manager.get_token(), self.user_id)
        
        self.status_label.setText(f"Авторизован: {user_name}")
        self.status_label.setStyleSheet("color: #4ecdc4;")
        self.login_btn.setText("Выйти")
        self.load_all_btn.setEnabled(True)
        self.load_btn.setEnabled(True)
        
        for btn in self.recommendations_btns.values():
            btn.setEnabled(True)
        
        self.load_all_tracks()
        self.load_playlists()
        
        QMessageBox.information(self, "Успех", f"Добро пожаловать, {user_name}!")
    
    def update_auth_status(self, authenticated):
        """Обновление статуса авторизации"""
        if authenticated:
            self.status_label.setText("Авторизован")
            self.status_label.setStyleSheet("color: #4ecdc4;")
            self.login_btn.setText("Выйти")
            self.load_all_btn.setEnabled(True)
            self.load_btn.setEnabled(True)
            for btn in self.recommendations_btns.values():
                btn.setEnabled(True)
        else:
            self.status_label.setText("Не авторизован")
            self.status_label.setStyleSheet("color: #ff6b6b;")
            self.login_btn.setText("Войти в VK")
            self.load_all_btn.setEnabled(False)
            self.load_btn.setEnabled(False)
            for btn in self.recommendations_btns.values():
                btn.setEnabled(False)
    
    def load_all_tracks(self):
        """Загрузка всех треков"""
        if not self.vk_client.is_authenticated():
            return
        
        self.status_label.setText("Загрузка треков...")
        
        tracks = self.playlist_manager.load_my_tracks(
            self.vk_client.user_id,
            settings.MAX_TRACKS_TO_LOAD,
            settings.TRACKS_PER_REQUEST
        )
        
        self.music_list.clear()
        for track in tracks:
            display_text = get_track_display_text(track)
            self.music_list.addItem(display_text)
        
        self.tracks_count_label.setText(f"Всего треков: {len(tracks)}")
        self.status_label.setText(f"Загружено треков: {len(tracks)}")
        
        if len(tracks) == 0:
            self.music_list.addItem("У вас нет аудиозаписей")
    
    def load_more(self):
        """Загрузка дополнительных треков"""
        self.load_all_tracks()
    
    def load_playlists(self):
        """Загрузка списка плейлистов"""
        if not self.vk_client.is_authenticated():
            return
        
        playlists = self.playlist_manager.load_playlists(self.vk_client.user_id)
        self.playlist_widget.set_playlists(playlists)
    
    def load_playlist_tracks(self, playlist):
        """Загрузка треков выбранного плейлиста"""
        if not self.vk_client.is_authenticated():
            return
        
        tracks = self.playlist_manager.load_playlist_tracks(
            playlist['id'],
            playlist['owner_id']
        )
        
        self.playlist_widget.set_playlist_tracks(tracks, playlist['title'])
    
    def play_playlist_track(self, index):
        """Воспроизведение трека из плейлиста"""
        tracks = self.playlist_manager.current_playlist
        if 0 <= index < len(tracks):
            self.play_track(index, tracks, self.playlist_widget.tracks_list)
    
    def search_music(self, query):
        """Поиск музыки"""
        if not self.vk_client.is_authenticated():
            QMessageBox.warning(self, "Ошибка", "Сначала авторизуйтесь в VK")
            return
        
        tracks = self.playlist_manager.search_tracks(query)
        self.search_widget.set_results(tracks)
        
        if len(tracks) == 0:
            self.search_widget.results_list.addItem("Ничего не найдено")
    
    def play_search_result(self, index):
        """Воспроизведение результата поиска"""
        tracks = self.playlist_manager.current_playlist
        if 0 <= index < len(tracks):
            self.play_track(index, tracks, self.search_widget.results_list)
    
    def load_recommendations(self, rec_type):
        """Загрузка рекомендаций"""
        if not self.vk_client.is_authenticated():
            QMessageBox.warning(self, "Ошибка", "Сначала авторизуйтесь в VK")
            return
        
        self.recommendations_list.clear()
        self.recommendations_count_label.setText("Загрузка рекомендаций...")
        
        tracks = self.playlist_manager.load_recommendations(rec_type)
        
        self.recommendations_list.clear()
        for track in tracks:
            display_text = get_track_display_text(track)
            self.recommendations_list.addItem(display_text)
        
        track_count = len(tracks)
        type_names = {
            "for_you": "Для вас",
            "discoveries": "Открытия",
            "new": "Новинки",
            "day1": "Плейлист дня 1",
            "day2": "Плейлист дня 2",
            "day3": "Плейлист дня 3",
            "day4": "Плейлист дня 4",
            "day5": "Плейлист дня 5"
        }
        
        self.recommendations_count_label.setText(
            f"{type_names.get(rec_type, rec_type)}: {track_count} треков"
        )
        self.status_label.setText(f"Загружено рекомендаций: {track_count}")
        
        if track_count == 0:
            self.recommendations_list.addItem("Не удалось загрузить рекомендации")
            self.recommendations_list.addItem("Попробуйте другую категорию")
    
    def play_from_list(self, item, list_widget):
        """Воспроизведение трека из списка"""
        index = list_widget.row(item)
        tracks = self.playlist_manager.current_playlist
        if 0 <= index < len(tracks):
            self.play_track(index, tracks, list_widget)
    
    def play_track(self, index, playlist=None, list_widget=None):
        """Воспроизведение трека"""
        if playlist is None:
            playlist = self.playlist_manager.current_playlist
        
        if 0 <= index < len(playlist):
            self.player.set_playlist(playlist)
            track = self.player.set_track(index)
            
            if track:
                self.track_info.setText(f"{track['artist']} - {track['title']}")
                self.play_btn.setText("⏸")
                self.play_btn.setEnabled(True)
                self.prev_btn.setEnabled(True)
                self.next_btn.setEnabled(True)
                
                if list_widget:
                    list_widget.setCurrentRow(index)
    
    def toggle_play(self):
        """Переключение воспроизведения"""
        if self.player.toggle():
            self.play_btn.setText("⏸")
        else:
            self.play_btn.setText("▶")
    
    def play_next(self):
        """Следующий трек"""
        track = self.player.next()
        if track:
            self.track_info.setText(f"{track['artist']} - {track['title']}")
            self.play_btn.setText("⏸")
    
    def play_previous(self):
        """Предыдущий трек"""
        track = self.player.previous()
        if track:
            self.track_info.setText(f"{track['artist']} - {track['title']}")
            self.play_btn.setText("⏸")
    
    def change_volume(self, value):
        """Изменение громкости"""
        self.player.set_volume(value)
    
    def _on_position_changed(self, progress):
        """Обновление прогресса воспроизведения"""
        self.progress_bar.setValue(progress)
    
    def _on_player_state_changed(self, state):
        """Обработка изменения состояния плеера"""
        if state == "stopped":
            self.play_btn.setText("▶")
            if self.player.current_index < self.player.get_playlist_count() - 1:
                self.play_next()
    
    def show_debug_info(self):
        """Отображение отладочной информации"""
        try:
            import requests
            current_ip = requests.get('https://api.ipify.org', timeout=5).text
        except:
            current_ip = "Не удалось определить"
        
        info = f"""Отладочная информация:

Текущий IP: {current_ip}

User ID: {self.vk_client.user_id}
Токен: {'Есть' if self.vk_client.token_manager.get_token() else 'Нет'}
Длина токена: {len(self.vk_client.token_manager.get_token() or '')}

VK API: {'Доступен' if self.vk_client.is_authenticated() else 'Не доступен'}

Текущий плейлист: {self.player.get_playlist_count()} треков
Текущий индекс: {self.player.current_index}
Воспроизведение: {'Да' if self.player.is_playing_state() else 'Нет'}

Загружено плейлистов: {len(self.playlist_manager.playlists)}
"""
        QMessageBox.information(self, "Отладка", info)
    
    def logout(self):
        """Выход из аккаунта"""
        self.vk_client.logout()
        self.playlist_manager.current_playlist = []
        self.playlist_manager.playlists = []
        self.player.stop()
        self.player.current_playlist = []
        self.player.current_index = -1
        
        self.token_manager.delete_token()
        self.update_auth_status(False)
        
        self.music_list.clear()
        self.playlist_widget.clear()
        self.search_widget.clear()
        self.recommendations_list.clear()
        
        self.play_btn.setEnabled(False)
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.track_info.setText("Нет выбранного трека")
        
        self.tracks_count_label.setText("Всего треков: 0")
        self.recommendations_count_label.setText("Выберите категорию рекомендаций")
