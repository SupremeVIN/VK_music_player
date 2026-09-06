"""Главный файл для запуска приложения"""

import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import VKMusicPlayer


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = VKMusicPlayer()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
