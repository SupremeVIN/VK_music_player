"""Виджет для отображения списка музыки"""

from PyQt6.QtWidgets import QListWidget, QVBoxLayout, QWidget, QPushButton, QLabel, QHBoxLayout
from PyQt6.QtCore import pyqtSignal

from utils.helpers import get_track_display_text


class MusicListWidget(QWidget):
    track_double_clicked = pyqtSignal(int)
    
    def __init__(self, title="Музыка", parent=None):
        super().__init__(parent)
        self.tracks = []
        self.setup_ui(title)
    
    def setup_ui(self, title):
        layout = QVBoxLayout(self)
        
        self.header = QLabel(title)
        self.header.setProperty("class", "header")
        layout.addWidget(self.header)
        
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.list_widget)
        
        # Нижняя панель с информацией
        bottom_layout = QHBoxLayout()
        
        self.count_label = QLabel("Всего треков: 0")
        self.count_label.setProperty("class", "info")
        bottom_layout.addWidget(self.count_label)
        
        bottom_layout.addStretch()
        
        self.load_btn = QPushButton("Загрузить все")
        self.load_btn.setEnabled(False)
        bottom_layout.addWidget(self.load_btn)
        
        layout.addLayout(bottom_layout)
    
    def set_tracks(self, tracks):
        """Установка списка треков"""
        self.tracks = tracks
        self.list_widget.clear()
        
        for i, track in enumerate(tracks):
            display_text = get_track_display_text(track)
            self.list_widget.addItem(display_text)
        
        self.count_label.setText(f"Всего треков: {len(tracks)}")
    
    def add_track(self, track):
        """Добавление одного трека"""
        self.tracks.append(track)
        display_text = get_track_display_text(track)
        self.list_widget.addItem(display_text)
        self.count_label.setText(f"Всего треков: {len(self.tracks)}")
    
    def clear(self):
        """Очистка списка"""
        self.tracks = []
        self.list_widget.clear()
        self.count_label.setText("Всего треков: 0")
    
    def set_selected(self, index):
        """Выбор трека по индексу"""
        if 0 <= index < self.list_widget.count():
            self.list_widget.setCurrentRow(index)
    
    def get_selected_index(self):
        """Получение индекса выбранного трека"""
        return self.list_widget.currentRow()
    
    def get_track_at(self, index):
        """Получение трека по индексу"""
        if 0 <= index < len(self.tracks):
            return self.tracks[index]
        return None
    
    def get_tracks(self):
        return self.tracks
    
    def _on_double_click(self, item):
        """Обработка двойного клика"""
        index = self.list_widget.row(item)
        self.track_double_clicked.emit(index)
    
    def set_load_enabled(self, enabled):
        self.load_btn.setEnabled(enabled)
