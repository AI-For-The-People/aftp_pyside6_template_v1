from __future__ import annotations
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QTextEdit, QPushButton, QMessageBox)
from PySide6.QtCore import Qt
from app.core.ollama_tools import which_ollama, generate_once

class QuickLLMDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quick LLM")
        self.setMinimumSize(520, 420)

        lay = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(QLabel("Model:"))
        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("e.g., llama3, mistral, qwen2.5, …")
        self.model_edit.setText("llama3")
        top.addWidget(self.model_edit, 1)
        lay.addLayout(top)

        lay.addWidget(QLabel("Prompt:"))
        self.prompt = QTextEdit()
        self.prompt.setPlaceholderText("Ask a quick question…")
        lay.addWidget(self.prompt, 1)

        lay.addWidget(QLabel("Response:"))
        self.out = QTextEdit()
        self.out.setReadOnly(True)
        lay.addWidget(self.out, 2)

        row = QHBoxLayout()
        self.btn_ask = QPushButton("Ask")
        self.btn_close = QPushButton("Close")
        row.addStretch(1)
        row.addWidget(self.btn_ask)
        row.addWidget(self.btn_close)
        lay.addLayout(row)

        self.btn_close.clicked.connect(self.close)
        self.btn_ask.clicked.connect(self._on_ask)

        if not which_ollama():
            QMessageBox.information(self, "Ollama not found",
                "Ollama server not detected. Install/Start it (Ollama tab) to use Quick LLM.")

    def _on_ask(self):
        model = self.model_edit.text().strip()
        prompt = self.prompt.toPlainText().strip()
        if not model or not prompt:
            QMessageBox.warning(self, "Missing", "Please enter a model and a prompt.")
            return
        self.out.clear()
        self.btn_ask.setEnabled(False)
        try:
            ok, text = generate_once(model=model, prompt=prompt, timeout=120)
            if ok:
                self.out.setPlainText(text)
            else:
                self.out.setPlainText(f"[error] {text}")
        finally:
            self.btn_ask.setEnabled(True)
