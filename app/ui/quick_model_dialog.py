from __future__ import annotations
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QTextEdit, QPushButton, QComboBox)
from PySide6.QtCore import Qt
from app.core.model_registry import list_models

class QuickModelDialog(QDialog):
    """
    Placeholder to pick/add a model. No heavy logic here—just a visual anchor so future apps
    know where model selection lives.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quick Model")
        self.setMinimumSize(520, 380)
        lay = QVBoxLayout(self)

        row = QHBoxLayout()
        row.addWidget(QLabel("Kind:"))
        self.kind = QComboBox(); self.kind.addItems(["ollama","hf","stt","tts","custom"])
        row.addWidget(self.kind)
        row.addWidget(QLabel("Handle:"))
        self.handle = QLineEdit(); self.handle.setPlaceholderText("e.g., ollama:llama3 or hf:Qwen/Qwen2.5")
        row.addWidget(self.handle,1)
        lay.addLayout(row)

        lay.addWidget(QLabel("Notes:"))
        self.notes = QTextEdit(); lay.addWidget(self.notes,1)

        btns = QHBoxLayout()
        self.btn_use = QPushButton("Use")
        self.btn_close = QPushButton("Close")
        btns.addStretch(1); btns.addWidget(self.btn_use); btns.addWidget(self.btn_close)
        lay.addLayout(btns)

        self.btn_close.clicked.connect(self.close)
        self.btn_use.clicked.connect(self.accept)

        # Stub list (future: list existing)
        existing = list_models()
        if existing:
            self.notes.setPlainText("Existing models:\n" + "\n".join(f"- {k}: {v.get('type')}" for k,v in existing.items()))
