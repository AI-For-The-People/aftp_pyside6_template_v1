from __future__ import annotations
from typing import List, Tuple
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem

class CommandPalette(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Command Palette")
        self.resize(520, 420)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        lay = QVBoxLayout(self)
        self.entry = QLineEdit(self)
        self.entry.setPlaceholderText("Type a command…")
        self.list = QListWidget(self)
        lay.addWidget(self.entry)
        lay.addWidget(self.list, 1)
        self._items: List[Tuple[str, callable]] = []
        self.entry.textChanged.connect(self._refilter)
        self.list.itemActivated.connect(self._run)

    def set_commands(self, cmds: List[Tuple[str, callable]]):
        self._items = cmds
        self._refilter()

    def _refilter(self):
        q = self.entry.text().strip().lower()
        self.list.clear()
        for label, fn in self._items:
            if not q or q in label.lower():
                QListWidgetItem(label, self.list)

    def _run(self, item: QListWidgetItem):
        label = item.text()
        for lbl, fn in self._items:
            if lbl == label:
                fn()
                break
        self.accept()
