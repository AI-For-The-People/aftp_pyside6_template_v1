from __future__ import annotations
import os, sys
from pathlib import Path
from typing import Dict

# ---------- OS base ----------
def _platform_base_dir() -> Path:
    """OS-specific base directory for AFTP."""
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming")))
        return base / "AFTP"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "AFTP"
    else:
        # Linux / other Unix
        xdg = os.environ.get("XDG_DATA_HOME")
        base = Path(xdg) if xdg else (Path.home() / ".local" / "share")
        return base / "AFTP"

# ---------- Top-level ----------
def aftp_root() -> Path:
    """Top-level AFTP folder for shared resources (venvs, data, logs, config)."""
    return _platform_base_dir()

def data_dir() -> Path:
    return aftp_root() / "data"

def venvs_dir() -> Path:
    return aftp_root() / "venvs"

def logs_dir() -> Path:
    return aftp_root() / "logs"

def config_dir() -> Path:
    """Config directory for JSON settings, etc."""
    return aftp_root() / "config"

# ---------- Subfolders commonly used by apps ----------
def models_dir() -> Path:
    """Optional shared models dir (not required by all apps)."""
    return data_dir() / "models"

def conversations_dir() -> Path:
    return data_dir() / "conversations"

def hf_home_dir() -> Path:
    """Hugging Face cache location (HF_HOME)."""
    return data_dir() / "hf_cache"

def faiss_home_dir() -> Path:
    """Place to pin FAISS resources if needed."""
    return data_dir() / "faiss"

def runtime_registry_path() -> Path:
    """Machine-wide registry used by apps to discover runtimes."""
    return data_dir() / "runtime_registry.json"

# Back-compat alias (older code calls this)
def app_local_data_dir() -> Path:
    return data_dir()

# ---------- Ensure layout ----------
def ensure_dirs() -> Dict[str, str]:
    """
    Create the standard AFTP folder layout if missing.
    Returns a map of created/ensured directories (string paths for logging).
    """
    created: Dict[str, str] = {}
    dirs = [
        aftp_root(), data_dir(), venvs_dir(), logs_dir(), config_dir(),
        models_dir(), conversations_dir(), hf_home_dir(), faiss_home_dir()
    ]
    for p in dirs:
        try:
            p.mkdir(parents=True, exist_ok=True)
            created[p.name] = str(p)
        except Exception:
            # Don't fail startup if a directory can't be created; just skip.
            pass

    # Touch the runtime registry file if it doesn't exist
    try:
        reg = runtime_registry_path()
        if not reg.exists():
            reg.write_text("{}", encoding="utf-8")
    except Exception:
        pass

    return created
