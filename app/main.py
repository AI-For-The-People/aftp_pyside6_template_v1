from __future__ import annotations
import sys
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow
from app.core.paths import ensure_dirs
from app.ui import fallback_locate_install as _aftp_fallback

def main():
    ensure_dirs()
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
