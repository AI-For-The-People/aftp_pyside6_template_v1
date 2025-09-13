from __future__ import annotations
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem)
from PySide6.QtCore import Qt

class CommandPalette(QDialog):
    """
    Minimal command palette: filter & run provided actions.
    Expected actions: list of tuples (label, callback).
    """
    def __init__(self, actions, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Command Palette")
        self.setMinimumWidth(520)
        self._actions = actions or []
        lay = QVBoxLayout(self)
        self.edit = QLineEdit(self); self.edit.setPlaceholderText("Type a command…")
        self.list = QListWidget(self)
        lay.addWidget(self.edit); lay.addWidget(self.list, 1)
        self.edit.textChanged.connect(self._filter)
        self.list.itemActivated.connect(self._run)
        self._refresh()
    def _refresh(self):
        self.list.clear()
        for label, cb in self._actions:
            it = QListWidgetItem(label)
            it.setData(Qt.UserRole, cb)
            self.list.addItem(it)
    def _filter(self, text: str):
        t = text.lower().strip()
        for i in range(self.list.count()):
            it = self.list.item(i)
            it.setHidden(t not in it.text().lower())
    def _run(self, item: QListWidgetItem):
        cb = item.data(Qt.UserRole)
        if callable(cb):
            try: cb()
            except Exception: pass
        self.accept()
