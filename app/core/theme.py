from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Optional
import json
from PySide6.QtCore import QObject, Signal, QFileSystemWatcher
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication
from .paths import shared_theme_file, ensure_dirs

Mode = Literal["dark","light"]

@dataclass
class Accent:
    primary: str
    secondary: str

@dataclass
class Scheme:
    key: str
    name: str
    dark: Accent
    light: Accent

SCHEMES = [
    Scheme(
        key="aftp_signature",
        name="AFTP Signature",
        dark=Accent(primary="#8A1A1A", secondary="#B1911F"),
        light=Accent(primary="#D64545", secondary="#D8B455"),
    ),
    Scheme(
        key="blue_steel",
        name="Blue Steel",
        dark=Accent(primary="#1E4D7A", secondary="#A9B2BA"),
        light=Accent(primary="#2E6EA8", secondary="#C9D1D9"),
    ),
    Scheme(
        key="verdant_bronze",
        name="Verdant Bronze",
        dark=Accent(primary="#1F5E3A", secondary="#A86F32"),
        light=Accent(primary="#2F8E58", secondary="#CD8740"),
    ),
]

DEFAULT = {"mode": "dark", "scheme": "aftp_signature", "custom_accent": None}

def scheme_by_key(key: str) -> Scheme:
    for s in SCHEMES:
        if s.key == key: return s
    return SCHEMES[0]

class ThemeManager(QObject):
    changed = Signal()
    def __init__(self):
        super().__init__()
        ensure_dirs()
        self.file = shared_theme_file()
        self.watcher = QFileSystemWatcher([str(self.file)]) if self.file.exists() else QFileSystemWatcher()
        if self.file.exists(): self.watcher.addPath(str(self.file))
        self.watcher.fileChanged.connect(self._on_external_change)
        self._data = self._load()

    def _load(self) -> dict:
        try:
            return {**DEFAULT, **json.load(open(self.file, "r", encoding="utf-8"))}
        except Exception:
            return DEFAULT.copy()

    def save(self):
        self.file.parent.mkdir(parents=True, exist_ok=True)
        json.dump(self._data, open(self.file, "w", encoding="utf-8"), indent=2)
        self.changed.emit()

    def _on_external_change(self, *_):
        self._data = self._load()
        self.apply()

    def mode(self) -> Mode:
        return self._data.get("mode","dark")  # type: ignore

    def set_mode(self, mode: Mode):
        self._data["mode"] = mode; self.save(); self.apply()

    def set_scheme(self, key: str):
        self._data["scheme"] = key; self.save(); self.apply()

    def set_custom_accent(self, primary: str, secondary: Optional[str]=None):
        self._data["custom_accent"] = {"primary": primary, "secondary": secondary or primary}
        self.save(); self.apply()

    def clear_custom_accent(self):
        self._data["custom_accent"] = None; self.save(); self.apply()

    def current_accent(self) -> Accent:
        c = self._data.get("custom_accent")
        if c: return Accent(primary=c["primary"], secondary=c.get("secondary", c["primary"]))
        sch = scheme_by_key(self._data.get("scheme","aftp_signature"))
        return sch.dark if self.mode()=="dark" else sch.light

    def apply(self):
        acc = self.current_accent()
        qss = f"""
        QPushButton {{
            border-radius: 8px; padding: 6px 10px; border: 1px solid rgba(0,0,0,0.15);
        }}
        QPushButton:hover {{ background: rgba(0,0,0,0.06); }}
        QPushButton:pressed {{ background: rgba(0,0,0,0.12); }}
        QTabBar::tab:selected {{ color: {acc.primary}; }}
        QProgressBar::chunk {{ background-color: {acc.primary}; }}
        QSlider::handle:horizontal {{ background: {acc.primary}; width: 16px; border-radius: 8px; }}
        """
        app = QApplication.instance()
        if not app: return
        app.setStyleSheet(qss)
        pal = app.palette()
        if self.mode()=="dark":
            pal.setColor(QPalette.ColorRole.Window, QColor("#121212"))
            pal.setColor(QPalette.ColorRole.Base, QColor("#1a1a1a"))
            pal.setColor(QPalette.ColorRole.Text, QColor("#e6e6e6"))
            pal.setColor(QPalette.ColorRole.WindowText, QColor("#e6e6e6"))
        else:
            pal.setColor(QPalette.ColorRole.Window, QColor("#ffffff"))
            pal.setColor(QPalette.ColorRole.Base, QColor("#f6f6f6"))
            pal.setColor(QPalette.ColorRole.Text, QColor("#101010"))
            pal.setColor(QPalette.ColorRole.WindowText, QColor("#101010"))
        app.setPalette(pal)
