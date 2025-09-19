# app/ui/diagnostics_dialog.py
from __future__ import annotations
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox
)
from typing import Dict, Any

def _build_report(parent) -> str:
    """Return a plain-text diagnostics report string."""
    # Keep this function side-effect free and ALWAYS return str.
    try:
        from app.core.runtime_registry import read_registry
        reg: Dict[str, Any] = read_registry() or {}
    except Exception:
        reg = {}

    lines = []
    lines.append("AFTP Hub — Diagnostics")
    lines.append("")
    lines.append("Runtimes in registry:")
    if reg:
        for k, v in reg.items():
            lines.append(f"  - {k}: {v}")
    else:
        lines.append("  (none)")
    lines.append("")
    lines.append("Tip: Use Runtimes → Validate / Details for per-venv info.")
    return "\n".join(lines)

class DiagnosticsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Diagnostics")
        self.resize(760, 520)

        lay = QVBoxLayout(self)

        self.text = QTextEdit(self)
        self.text.setReadOnly(True)
        lay.addWidget(self.text, 1)

        # Build the *string* report and set it.
        report_text: str = _build_report(parent)
        self.text.setPlainText(report_text)

        btns = QDialogButtonBox(QDialogButtonBox.Close, parent=self)
        btns.rejected.connect(self.reject)
        btns.accepted.connect(self.accept)
        lay.addWidget(btns)
