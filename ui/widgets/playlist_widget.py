"""Виджет для работы с плейлистами"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import pyqtSignal, Qt

from ui.widgets.music_list import MusicListWidget
from utils.helpers import get_track_display_text


class PlaylistWidget(QWidget):
    playlist_selected = pyqtSignal(dict)
    track_double_clicked = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.playlists = []
        self.current_playlist = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        
        # Левая панель - список плейлистов
        left_widget = QWidget()
        left_widget.setMaximumWidth(300)
        left_layout = QVBoxLayout(left_widget)
        
        header = QLabel("Ваши плейлисты")
        header.setProperty("class", "header")
        left_layout.addWidget(header)
        
        self.playlists_list = QListWidget()
        self.playlists_list.itemClicked.connect(self._on_playlist_selected)
        left_layout.addWidget(self.playlists_list)
        
        layout.addWidget(left_widget)
        
        # Правая панель - треки плейлиста
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        self.tracks_label = QLabel("Выберите плейлист")
        self.tracks_label.setProperty("class", "header")
        right_layout.addWidget(self.tracks_label)
        
        self.tracks_list = QListWidget()
        self.tracks_list.itemDoubleClicked.connect(self._on_track_double_click)
        right_layout.addWidget(self.tracks_list)
        
        layout.addWidget(right_widget, stretch=2)
    
    def set_playlists(self, playlists):
        """Установка списка плейлистов"""
        self.playlists = playlists
        self.playlists_list.clear()
        
        for playlist in playlists:
            display_text = f"{playlist['title']} ({playlist['count']} треков)"
            self.playlists_list.addItem(display_text)
        
        if not playlists:
            self.playlists_list.addItem("Нет созданных плейлистов")
    
    def set_playlist_tracks(self, tracks, playlist_title):
        """Установка треков выбранного плейлиста"""
        self.tracks_list.clear()
        self.tracks_label.setText(f"Плейлист: {playlist_title} ({len(tracks)} треков)")
        
        for track in tracks:
            display_text = get_track_display_text(track)
            self.tracks_list.addItem(display_text)
        
        if not tracks:
            self.tracks_list.addItem("Не удалось загрузить треки из этого плейлиста")
    
    def clear(self):
        """Очистка виджета"""
        self.playlists_list.clear()
        self.tracks_list.clear()
        self.tracks_label.setText("Выберите плейлист")
    
    def set_selected(self, index):
        """Выбор трека по индексу"""
        if 0 <= index < self.tracks_list.count():
            self.tracks_list.setCurrentRow(index)
    
    def get_selected_track_index(self):
        """Получение индекса выбранного трека"""
        return self.tracks_list.currentRow()
    
    def _on_playlist_selected(self, item):
        """Обработка выбора плейлиста"""
        index = self.playlists_list.row(item)
        if 0 <= index < len(self.playlists):
            self.current_playlist = self.playlists[index]
            self.playlist_selected.emit(self.current_playlist)
    
    def _on_track_double_click(self, item):
        """Обработка двойного клика по треку"""
        index = self.tracks_list.row(item)
        self.track_double_clicked.emit(index)
