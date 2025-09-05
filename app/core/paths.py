from __future__ import annotations
import os, sys
from pathlib import Path

APP_NAME = "AI For The People"

def user_config_dir() -> Path:
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
        return Path(base) / APP_NAME
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    else:
        base = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
        return Path(base) / APP_NAME

def shared_theme_file() -> Path:
    return user_config_dir() / "theme.json"

def app_local_data_dir() -> Path:
    return Path.cwd() / "data"

def venvs_dir() -> Path:
    return Path.cwd() / "venvs"

def ensure_dirs():
    user_config_dir().mkdir(parents=True, exist_ok=True)
    app_local_data_dir().mkdir(parents=True, exist_ok=True)
    venvs_dir().mkdir(parents=True, exist_ok=True)
