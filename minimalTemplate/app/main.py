from PySide6.QtWidgets import QApplication, QMainWindow
import sys
from app.core.theme import ThemeManager

def main():
    app = QApplication(sys.argv)
    theme = ThemeManager()
    theme.apply()
    win = QMainWindow()
    win.setWindowTitle("AFTP Minimal Template")
    win.resize(600, 400)
    win.show()
    sys.exit(app.exec())
