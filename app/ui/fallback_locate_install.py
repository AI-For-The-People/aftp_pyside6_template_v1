from __future__ import annotations
import webbrowser
from PySide6.QtWidgets import QMessageBox

# Import MainWindow class so we can attach methods
from app.ui.main_window import MainWindow

# Try to import which_ollama (optional)
try:
    from app.core.ollama_tools import which_ollama
except Exception:
    which_ollama = None

def _open_ollama_site(self):
    """Open the Ollama website as a safe fallback for install/help."""
    try:
        webbrowser.open("https://ollama.com")
    except Exception:
        pass

def _locate_or_install_ollama(self):
    """
    Minimal handler: try to find Ollama; if found, show location;
    otherwise open the official site for install instructions.
    """
    path = None
    if which_ollama:
        try:
            path = which_ollama()
        except Exception:
            path = None

    if path:
        QMessageBox.information(
            self, "Ollama",
            f"Found Ollama at:\n{path}\n\nIf the server isn't running, try 'ollama serve'."
        )
    else:
        QMessageBox.information(
            self, "Ollama",
            "Ollama not found. Opening the official website to install."
        )
        _open_ollama_site(self)

# Only add these if they aren't already present (so richer impls override us)
if not hasattr(MainWindow, "_open_ollama_site"):
    MainWindow._open_ollama_site = _open_ollama_site
if not hasattr(MainWindow, "_locate_or_install_ollama"):
    MainWindow._locate_or_install_ollama = _locate_or_install_ollama
