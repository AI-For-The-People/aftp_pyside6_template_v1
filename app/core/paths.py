from __future__ import annotations
import os, sys
from pathlib import Path

def _base_dir() -> Path:
    if os.name == "nt":
        appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData/Roaming")
        return Path(appdata) / "AFTP"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "AFTP"
    else:
        return Path.home() / ".local" / "share" / "AFTP"

def app_local_data_dir() -> Path:
    """Legacy name used in a few places → keep pointing to shared base."""
    return _base_dir()

def venvs_dir() -> Path:
    return _base_dir() / "venvs"

def data_dir() -> Path:
    return _base_dir() / "data"

def runtime_registry_path() -> Path:
    return _base_dir() / "runtime_registry.json"

def ensure_dirs() -> None:
    (venvs_dir()).mkdir(parents=True, exist_ok=True)
    (data_dir()).mkdir(parents=True, exist_ok=True)
    _base_dir().mkdir(parents=True, exist_ok=True)
