from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget, QPlainTextEdit, QDialogButtonBox, QLabel, QPushButton, QHBoxLayout, QMessageBox
)
from app.core.licenses import discover_license_files, load_text, fetch_all_known_licenses

class LicenseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Licenses & Notices")
        self.resize(900, 600)
        lay = QVBoxLayout(self)

        top = QHBoxLayout()
        info = QLabel(
            "Project and cached third-party licenses appear below.\n"
            "Click “Refresh from Internet” to fetch/update (Ollama, FFmpeg, Tesseract)."
        )
        info.setWordWrap(True)
        btn_refresh = QPushButton("Refresh from Internet")
        btn_refresh.clicked.connect(self._refresh)
        top.addWidget(info, 1); top.addWidget(btn_refresh, 0, Qt.AlignmentFlag.AlignRight)
        lay.addLayout(top)

        self.tabs = QTabWidget(self)
        self._populate_tabs()
        lay.addWidget(self.tabs, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Close, self)
        buttons.rejected.connect(self.reject)
        buttons.clicked.connect(self.close)
        lay.addWidget(buttons)

    def _populate_tabs(self):
        self.tabs.clear()
        for p in discover_license_files():
            title, text = load_text(p)
            page = QWidget(); v = QVBoxLayout(page)
            view = QPlainTextEdit(); view.setReadOnly(True); view.setPlainText(text)
            v.addWidget(view)
            self.tabs.addTab(page, title)

    def _refresh(self):
        status = fetch_all_known_licenses()
        msg = "\n".join([f"{k}: {v}" for k, v in status.items()])
        QMessageBox.information(self, "License fetch", msg)
        self._populate_tabs()
