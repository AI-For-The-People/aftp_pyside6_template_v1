from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

class ThemeManager:
    def __init__(self, mode="dark", primary="#B5182A", secondary="#C6A23A"):
        self.mode = mode
        self.primary = primary
        self.secondary = secondary

    def apply(self):
        pal = QPalette()
        if self.mode == "dark":
            pal.setColor(QPalette.Window, QColor("#121212"))
            pal.setColor(QPalette.WindowText, Qt.white)
        else:
            pal.setColor(QPalette.Window, Qt.white)
            pal.setColor(QPalette.WindowText, Qt.black)
        from PySide6.QtWidgets import QApplication
        QApplication.instance().setPalette(pal)
