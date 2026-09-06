"""Виджет для поиска музыки"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import pyqtSignal

from utils.helpers import get_track_display_text


class SearchWidget(QWidget):
    search_requested = pyqtSignal(str)
    track_double_clicked = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tracks = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Поисковая строка
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск музыки...")
        self.search_input.returnPressed.connect(self._on_search)
        
        self.search_btn = QPushButton("Найти")
        self.search_btn.clicked.connect(self._on_search)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        layout.addLayout(search_layout)
        
        # Результаты
        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.results_list)
        
        # Информация
        self.count_label = QLabel("Найдено треков: 0")
        self.count_label.setProperty("class", "info")
        layout.addWidget(self.count_label)
    
    def set_results(self, tracks):
        """Установка результатов поиска"""
        self.tracks = tracks
        self.results_list.clear()
        
        for track in tracks:
            display_text = get_track_display_text(track)
            self.results_list.addItem(display_text)
        
        self.count_label.setText(f"Найдено треков: {len(tracks)}")
    
    def clear(self):
        """Очистка результатов"""
        self.tracks = []
        self.results_list.clear()
        self.count_label.setText("Найдено треков: 0")
    
    def set_selected(self, index):
        """Выбор трека по индексу"""
        if 0 <= index < self.results_list.count():
            self.results_list.setCurrentRow(index)
    
    def get_selected_index(self):
        """Получение индекса выбранного трека"""
        return self.results_list.currentRow()
    
    def get_query(self):
        return self.search_input.text().strip()
    
    def _on_search(self):
        query = self.search_input.text().strip()
        if query:
            self.search_requested.emit(query)
    
    def _on_double_click(self, item):
        """Обработка двойного клика"""
        index = self.results_list.row(item)
        self.track_double_clicked.emit(index)
