from __future__ import annotations
import json, os, platform, sys
from pathlib import Path
from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout

class DiagnosticsDialog(QDialog):
    def __init__(self, report_text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Diagnostics")
        self.setMinimumSize(640, 420)
        lay = QVBoxLayout(self)
        self.text = QTextEdit(); self.text.setReadOnly(True)
        self.text.setPlainText(report_text)
        lay.addWidget(self.text, 1)
        row = QHBoxLayout()
        save = QPushButton("Copy to Clipboard")
        close = QPushButton("Close")
        row.addStretch(1); row.addWidget(save); row.addWidget(close)
        lay.addLayout(row)
        save.clicked.connect(self._copy)
        close.clicked.connect(self.accept)
    def _copy(self):
        self.text.selectAll()
        self.text.copy()
