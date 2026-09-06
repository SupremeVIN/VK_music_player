"""Стили UI"""

STYLES = """
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
QPushButton.active {
    background-color: #4ecdc4;
    color: #1a1a2e;
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
QLabel.header {
    font-size: 18px;
    font-weight: bold;
    color: #4ecdc4;
    padding: 10px;
}
QLabel.info {
    color: #a8a8b8;
    padding: 5px;
}
QLabel.track_info {
    font-size: 16px;
    color: #a8a8b8;
    padding: 10px;
}
"""

AUTH_DIALOG_STYLES = """
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
QLabel.instruction {
    color: #a8a8b8;
    font-size: 12px;
    padding: 10px;
    background-color: #16213e;
    border-radius: 5px;
}
"""

def get_styles():
    return STYLES

def get_auth_dialog_styles():
    return AUTH_DIALOG_STYLES
