# app/core/theme.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional
from pathlib import Path
import json, os, platform

from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication

# ---------- central config paths (shared by ALL AFTP apps) ----------
def _config_dir() -> Path:
    sys = platform.system()
    if sys == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming"))
        return base / "AFTP"
    elif sys == "Darwin":
        return Path.home() / "Library" / "Application Support" / "AFTP"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        return base / "AFTP"

def _theme_file() -> Path:
    d = _config_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d / "theme.json"

# ---------- two-accent schemes ----------
@dataclass(frozen=True)
class Scheme:
    key: str
    name: str
    primary: str    # hex
    secondary: str  # hex

SCHEMES = [
    Scheme("aftp_signature", "AFTP Signature (Red/Gold)",
           primary="#B5182A", secondary="#C6A23A"),
    Scheme("steel_cobalt", "Steel & Cobalt (Silver/Blue)",
           primary="#64778C", secondary="#2F64C0"),
    Scheme("verdigris_bronze", "Verdigris & Bronze (Green/Bronze)",
           primary="#198F7A", secondary="#8C6239"),
]
SCHEMES_BY_KEY: Dict[str, Scheme] = {s.key: s for s in SCHEMES}

DEFAULT_MODE = "dark"
DEFAULT_SCHEME_KEY = "aftp_signature"

class ThemeManager:
    """
    One theme for the whole ecosystem.
    - Persists to ~/.config/AFTP/theme.json (or OS equivalent).
    - Applies tuned QPalette + QSS that USES BOTH accent colors widely.
    - Supports custom per-user accents (primary/secondary).
    """
    def __init__(self):
        self._data = self._load_or_default()

    # ---- public API ----
    def mode(self) -> str:
        return self._data.get("mode", DEFAULT_MODE)

    def set_mode(self, mode: str):
        self._data["mode"] = "dark" if mode not in ("dark", "light") else mode
        self._save()
        self.apply()

    def toggle(self):
        self.set_mode("light" if self.mode() == "dark" else "dark")

    def set_scheme(self, key: str):
        if key not in SCHEMES_BY_KEY:
            key = DEFAULT_SCHEME_KEY
        self._data["scheme"] = key
        self._save()
        self.apply()

    def set_custom_accent(self, primary_hex: str, secondary_hex: Optional[str] = None):
        self._data["custom_primary"] = primary_hex
        if secondary_hex:
            self._data["custom_secondary"] = secondary_hex
        self._save()
        self.apply()

    def clear_custom_accent(self):
        self._data.pop("custom_primary", None)
        self._data.pop("custom_secondary", None)
        self._save()
        self.apply()

    def apply(self):
        app = QApplication.instance()
        if app is None:
            return

        is_dark = self.mode() == "dark"
        sch = SCHEMES_BY_KEY.get(self._data.get("scheme", DEFAULT_SCHEME_KEY), SCHEMES_BY_KEY[DEFAULT_SCHEME_KEY])
        primary = self._data.get("custom_primary", sch.primary)
        secondary = self._data.get("custom_secondary", sch.secondary)

        pal = self._build_palette(is_dark)
        app.setPalette(pal)

        qss = self._build_qss(is_dark, primary, secondary)
        app.setStyleSheet(qss)

    # ---- internals ----
    def _load_or_default(self) -> Dict:
        f = _theme_file()
        if f.exists():
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                data.setdefault("mode", DEFAULT_MODE)
                data.setdefault("scheme", DEFAULT_SCHEME_KEY)
                return data
            except Exception:
                pass
        data = {"mode": DEFAULT_MODE, "scheme": DEFAULT_SCHEME_KEY}
        f.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data

    def _save(self):
        try:
            _theme_file().write_text(json.dumps(self._data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _build_palette(self, is_dark: bool) -> QPalette:
        pal = QPalette()
        if is_dark:
            bg = QColor("#121212")
            base = QColor("#181818")
            panel = QColor("#151515")
            text = QColor("#EDEDED")
            muted = QColor("#B7B7B7")
            highlight = QColor("#2F64C0")

            pal.setColor(QPalette.Window, bg)
            pal.setColor(QPalette.Base, base)
            pal.setColor(QPalette.AlternateBase, panel)
            pal.setColor(QPalette.Text, text)
            pal.setColor(QPalette.WindowText, text)
            pal.setColor(QPalette.Button, panel)
            pal.setColor(QPalette.ButtonText, text)
            pal.setColor(QPalette.PlaceholderText, muted)
            pal.setColor(QPalette.Highlight, highlight)
            pal.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
        else:
            bg = QColor("#FFFFFF")
            base = QColor("#FFFFFF")
            panel = QColor("#F7F8F9")
            text = QColor("#161616")
            muted = QColor("#6A6A6A")
            highlight = QColor("#2F64C0")

            pal.setColor(QPalette.Window, bg)
            pal.setColor(QPalette.Base, base)
            pal.setColor(QPalette.AlternateBase, panel)
            pal.setColor(QPalette.Text, text)
            pal.setColor(QPalette.WindowText, text)
            pal.setColor(QPalette.Button, QColor("#FFFFFF"))
            pal.setColor(QPalette.ButtonText, text)
            pal.setColor(QPalette.PlaceholderText, muted)
            pal.setColor(QPalette.Highlight, highlight)
            pal.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
        return pal

    def _build_qss(self, is_dark: bool, primary: str, secondary: str) -> str:
        # neutrals per mode
        if is_dark:
            pane = "#181818"
            frame = "#222222"
            border = "#2A2A2A"
            text = "#EDEDED"
            text_muted = "#B7B7B7"
            input_bg = "#1E1E1E"
            menu_bg = "#202020"
            menu_sel = primary
        else:
            pane = "#FFFFFF"
            frame = "#F2F4F6"
            border = "#E1E4E8"
            text = "#161616"
            text_muted = "#6A6A6A"
            input_bg = "#FFFFFF"
            menu_bg = "#FFFFFF"
            menu_sel = primary

        # Helper: a subtle gradient using both accents for primary buttons
        prim_grad = f"qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 {primary}, stop:1 {secondary})"

        return f"""
        QWidget {{
            color: {text};
        }}

        /* Selection & caret accents */
        QTextEdit, QPlainTextEdit, QLineEdit {{
            selection-background-color: {primary};
            selection-color: #FFFFFF;
            background: {input_bg};
            border: 1px solid {border};
            border-radius: 6px;
            padding: 6px;
        }}
        QTextEdit:focus, QPlainTextEdit:focus, QLineEdit:focus {{
            border: 2px solid {secondary};
        }}
        QComboBox {{
            background: {input_bg};
            border: 1px solid {border};
            border-radius: 6px;
            padding: 4px 8px;
        }}
        QComboBox:focus {{
            border: 2px solid {secondary};
        }}

        /* Buttons (use BOTH colors) */
        QPushButton {{
            background: {frame};
            border: 1px solid {border};
            border-radius: 8px;
            padding: 6px 12px;
        }}
        QPushButton[role="primary"] {{
            background: {prim_grad};
            color: #FFFFFF;
            border: 1px solid {secondary};
        }}
        QPushButton:hover {{
            border-color: {secondary};
        }}
        QPushButton:pressed {{
            background: {pane};
        }}

        /* Tab bar: primary border; secondary title color */
        QTabWidget::pane {{
            border: 1px solid {border};
            background: {pane};
            border-radius: 8px;
        }}
        QTabBar::tab {{
            background: {pane};
            color: {text_muted};
            padding: 7px 14px;
            border: 1px solid {border};
            border-bottom: none;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            margin-right: 2px;
        }}
        QTabBar::tab:selected {{
            background: {frame};
            border-color: {primary};
            color: {secondary};
        }}
        QTabBar::tab:hover {{
            color: {primary};
        }}

        /* Group boxes use secondary for title, primary for border */
        QGroupBox {{
            border: 1px solid {primary};
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 6px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 4px;
            color: {secondary};
        }}

        /* Splitter: secondary handle, primary hover */
        QSplitter::handle {{
            background: {secondary};
        }}
        QSplitter::handle:hover {{
            background: {primary};
        }}

        /* Progress bars and sliders */
        QProgressBar {{
            background: {frame};
            border: 1px solid {border};
            border-radius: 6px;
            text-align: center;
        }}
        QProgressBar::chunk {{
            background-color: {primary};
            border-radius: 6px;
        }}
        QSlider::groove:horizontal {{
            background: {border};
            height: 6px;
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: {secondary};
            width: 14px;
            margin: -4px 0;
            border-radius: 7px;
        }}

        /* Menus: primary highlight, secondary text on hover */
        QMenu {{
            background: {menu_bg};
            border: 1px solid {border};
        }}
        QMenu::item:selected {{
            background: {menu_sel};
            color: #FFFFFF;
        }}
        QMenuBar::item:selected {{
            background: {menu_sel};
            color: #FFFFFF;
        }}

        /* Status bar & tooltips */
        QStatusBar {{
            color: {secondary};
        }}
        QToolTip {{
            background: #FFFFE1;
            color: #111;
            border: 1px solid {primary};
        }}

        /* Checkboxes / Radios */
        QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
            background: {primary};
            border: 1px solid {secondary};
        }}
        QCheckBox::indicator:unchecked, QRadioButton::indicator:unchecked {{
            background: {frame};
            border: 1px solid {border};
        }}

        /* Table headers use both accents */
        QHeaderView::section {{
            background: {frame};
            color: {secondary};
            border: 1px solid {border};
            padding: 4px 8px;
        }}

        /* Scrollbars lightly accented */
        QScrollBar:vertical, QScrollBar:horizontal {{
            background: {pane};
            border: 1px solid {border};
        }}
        QScrollBar::handle {{
            background: {secondary};
            border-radius: 6px;
        }}
        QScrollBar::handle:hover {{
            background: {primary};
        }}
        """
# Back-compat export name used in older code
DEFAULT_SCHEMES = SCHEMES
