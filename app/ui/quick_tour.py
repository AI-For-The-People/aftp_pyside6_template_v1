from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt

TOUR_TEXT = """AFTP Hub — Quick Tour

Global Menus (top bar)
  File   — (reserved)
  Edit   — Undo/Redo, Cut/Copy/Paste
  View   — Theme, zoom, panels (varies per app)
  Tools  — Quick LLM…, Quick Model…, (future plugins)
  Help   — Shortcuts… (F1), Diagnostics…, About, Quick Tour… (Shift+F1)

Runtimes Tab (per row)
  Backend…       — Choose CPU / CUDA / ROCm / Intel (where applicable)
  Create/Update  — Build or refresh that venv
  Validate       — Try imports in that venv
  Details        — Shows per-module versions/errors
  Log            — Opens the live install/validate log view
Bottom buttons
  Check All      — Validate every runtime
  Refresh Status — Re-check venv presence/imports

GPU-Aware Backends (where available)
  image, ai_dev, stt  — CPU / CUDA / ROCm / Intel(OpenVINO)
  embeddings          — CPU (default) or CUDA (Linux-only attempt)

Other Tabs/Features
  Tools → Quick LLM… (Ctrl+J)
  Tools → Quick Model… (Ctrl+M)
  Command Palette (Ctrl+K)
  Help → Diagnostics…
  Help → Shortcuts… (F1)

Handy Shortcuts
  Ctrl+K           — Command Palette
  Ctrl+J           — Quick LLM
  Ctrl+M           — Quick Model
  Ctrl+Shift+L     — Toggle Log
  Ctrl+Shift+R     — Refresh Runtimes
  Ctrl+Tab / Shift — Switch tabs
  Ctrl+Z / Shift   — Undo/Redo
  Ctrl+C / V / X   — Copy / Paste / Cut
  Ctrl+Shift+D     — Dark/Light
  Ctrl++ / - / 0   — Zoom In/Out/Reset
  F1               — Shortcuts
  Shift+F1         — Quick Tour (this dialog)
"""

class QuickTour(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quick Tour")
        self.setMinimumSize(620, 520)
        lay = QVBoxLayout(self)
        t = QTextEdit(self); t.setReadOnly(True)
        t.setPlainText(TOUR_TEXT)
        lay.addWidget(t, 1)
        row = QHBoxLayout()
        b = QPushButton("Close"); b.clicked.connect(self.accept)
        row.addStretch(1); row.addWidget(b)
        lay.addLayout(row)
