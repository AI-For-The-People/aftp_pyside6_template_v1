from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, List
from PySide6.QtGui import QAction, QKeySequence   # QAction is in QtGui in Qt6
from PySide6.QtWidgets import QWidget

@dataclass
class ActionSpec:
    text: str
    shortcut: str | None
    handler: Callable[[], None]
    category: str = "General"

def attach_actions(win: QWidget, specs: List[ActionSpec]):
    actions: List[QAction] = []
    for s in specs:
        act = QAction(s.text, win)
        if s.shortcut:
            act.setShortcut(QKeySequence(s.shortcut))
        act.triggered.connect(s.handler)
        win.addAction(act)
        actions.append(act)
    return actions
