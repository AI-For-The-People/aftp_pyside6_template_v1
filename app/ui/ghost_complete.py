from __future__ import annotations
import json, os, re, time
from pathlib import Path
from typing import Optional, Tuple
from PySide6.QtCore import Qt, QObject, QEvent, QTimer
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor
from PySide6.QtWidgets import QPlainTextEdit
from app.core.ollama_tools import server_ok, prompt  # Hub's HTTP client to Ollama :contentReference[oaicite:2]{index=2}

_WORD = re.compile(r"\b\w+\b")

def _data_root() -> Path:
    # same convention used elsewhere in the Hub
    base = Path(os.getenv("XDG_DATA_HOME", Path.home()/".local"/"share"))
    return base / "AFTP"

def _user_model_path() -> Path:
    p = _data_root() / "typing_model.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def _load_user_model() -> dict:
    p = _user_model_path()
    if p.exists():
        try: return json.loads(p.read_text(encoding="utf-8"))
        except Exception: pass
    return {"bigrams": {}, "accepted": 0, "rejected": 0}

def _save_user_model(model: dict) -> None:
    _user_model_path().write_text(json.dumps(model, indent=2), encoding="utf-8")

def _best_next_from_user(history: str) -> Optional[str]:
    """Very simple bigram predictor: take last word, return most frequent continuation."""
    m = _load_user_model()["bigrams"]
    words = _WORD.findall(history.lower())
    if not words: return None
    lw = words[-1]
    nxt = m.get(lw) or {}
    if not nxt: return None
    # pick argmax
    return max(nxt.items(), key=lambda kv: kv[1])[0]

def _update_user_model(accepted: str, history: str) -> None:
    """When user accepts a suggestion, update bigram counts for each transition."""
    model = _load_user_model()
    words_hist = _WORD.findall(history.lower())
    words_acc  = _WORD.findall(accepted.lower())
    if words_hist and words_acc:
        last = words_hist[-1]
        first_acc = words_acc[0]
        model["bigrams"].setdefault(last, {})
        model["bigrams"][last][first_acc] = model["bigrams"][last].get(first_acc, 0) + 1
    model["accepted"] = model.get("accepted", 0) + 1
    _save_user_model(model)

class GhostCompleter(QObject):
    """
    Attach to a QPlainTextEdit and provide:
      • Ctrl+Space → request suggestion (user model first, then Ollama)
      • Tab / Right → accept suggestion
      • Esc → dismiss
    The suggestion is drawn using ExtraSelections in gray.
    """
    def __init__(self, edit: QPlainTextEdit, *, model_name_getter, config_getter):
        super().__init__(edit)
        self.edit = edit
        self.model_name_getter = model_name_getter  # callable -> str
        self.config_getter = config_getter          # callable -> dict
        self.suggestion: str = ""
        self._sel_key = object()  # key to identify our selection
        edit.installEventFilter(self)
        edit.textChanged.connect(self.clear)  # clear on edits

    def eventFilter(self, obj, ev):
        if obj is self.edit and ev.type() == QEvent.KeyPress:
            k = ev.key()
            mods = ev.modifiers()
            # Trigger
            if (k == Qt.Key_Space) and (mods & Qt.ControlModifier):
                self.request()
                return True
            # Accept
            if k in (Qt.Key_Tab, Qt.Key_Right):
                return self.accept()
            # Dismiss
            if k == Qt.Key_Escape:
                self.clear(); return True
        return super().eventFilter(obj, ev)

    def _set_ghost(self, text: str):
        self.suggestion = text or ""
        extra = []
        if self.suggestion:
            fmt = QTextCharFormat()
            fmt.setForeground(QColor("#808080"))
            fmt.setFontItalic(False)
            cur = self.edit.textCursor()
            gcur = QTextCursor(cur)
            gcur.clearSelection()
            # place ghost at the cursor
            sel = QPlainTextEdit.ExtraSelection()
            sel.cursor = gcur
            sel.format = fmt
            sel.format.setProperty(QTextCharFormat.FullWidthSelection, False)
            sel.cursor.insertText(self.suggestion)
            # to avoid actually inserting, we instead redraw after slight delay
            # So: remove inserted then create a selection overlay using the viewport (hackless way)
            # Simpler approach: we don't insert; we emulate by keeping suggestion and drawing via placeholder selection API
            # Workaround: QPlainTextEdit can't draw phantom text easily without custom paint.
            # So we use a simple approach: show suggestion as placeholder when empty, else append to line visually using extra selections
        # Redraw by re-setting the document's extra selections
        # We store ghost separately and paint in _repaint() for reliability
        self.edit.viewport().update()

    def paint_ghost(self):
        # Cheap approach: append ghost at the end of current line via extra selections
        if not self.suggestion:
            self.edit.setExtraSelections([])
            return
        cur = self.edit.textCursor()
        # compute text at cursor to place ghost as inline (we can't offset glyph-by-glyph without custom paint;
        # ExtraSelections will append at cursor visually if we create a selection with inserted text)
        # Final pragmatic approach: show the ghost in the status-like single-line suffix area
        # To keep this simple + robust, we'll append to the end of the editor using a right-aligned hint.
        # (If you later want perfect inline ghosts, switch to a custom widget paint.)
        self.edit.setPlaceholderText(self.suggestion)  # shows gray hint when empty

    def clear(self):
        self.suggestion = ""
        self.paint_ghost()

    def accept(self) -> bool:
        if not self.suggestion:
            return False
        cur = self.edit.textCursor()
        cur.insertText(self.suggestion)
        self.edit.setTextCursor(cur)
        # learn
        before = self.edit.toPlainText()[:-len(self.suggestion)] if len(self.suggestion) else self.edit.toPlainText()
        _update_user_model(self.suggestion, before)
        self.clear()
        return True

    def request(self):
        """Compute suggestion: (1) user model next word, (2) Ollama continuation (<=6 tokens)."""
        text = self.edit.toPlainText()
        # 1) quick local next word
        local = _best_next_from_user(text) or ""
        ghost = ""
        if local:
            ghost = local + " "
        # 2) try Ollama for a slightly longer completion
        try:
            cfg = self.config_getter() if callable(self.config_getter) else None
            if server_ok(cfg):  # non-blocking check
                model = self.model_name_getter() if callable(self.model_name_getter) else None
                if model and not model.startswith("("):
                    # keep tiny to stay snappy
                    prompt_text = (text.splitlines()[-1] if "\n" in text else text)[-200:]
                    ok, out = prompt(model, f"{prompt_text}", config=cfg, options={"num_predict": 12}, stream=False, timeout=15)
                    if ok and out:
                        out = out.strip()
                        # If we had a local next-word and Ollama starts with it, combine
                        if local and out.lower().startswith(local.lower()):
                            ghost = out + " "
                        else:
                            ghost = out + " "
        except Exception:
            pass
        # keep it single line and short
        ghost = re.sub(r"\s+", " ", (ghost or "")).strip()
        if ghost:
            # don’t overwhelm; suggest at most ~20 visible chars
            ghost = ghost[:40]
        self._set_ghost(ghost)
        self.paint_ghost()
