from __future__ import annotations
import json, os
from pathlib import Path
from typing import Any, Dict
from .paths import config_dir, data_dir, venvs_dir, hf_home_dir, faiss_home_dir

SETTINGS_FILE = config_dir() / "settings.json"

DEFAULTS: Dict[str, Any] = {
    "theme": {
        "mode": "dark",                  # "dark" | "light"
        "scheme": "aftp_signature",      # your default
        "custom": {"primary": "", "secondary": ""},
    },
    "ollama": {
        "host": "127.0.0.1",
        "port": 11434,
        "models_dir": str((Path.home() / ".ollama").resolve()),
        "binary": "",                    # optional absolute path, else PATH
    },
    "paths": {
        "venvs": str(venvs_dir().resolve()),
        "hf_home": str(hf_home_dir().resolve()),
        "faiss_home": str(faiss_home_dir().resolve()),
        "cache": str((data_dir() / "cache").resolve()),
        "logs": str((data_dir() / "logs").resolve()),
    },
    "shortcuts": {"profile": "default"},
    "gpu": {"preference": "auto"},       # "auto" | "cuda" | "rocm" | "intel" | "cpu"
    "proxies": {"http": "", "https": "", "no_proxy": ""},
    "privacy": {"telemetry_opt_in": False},
    "licenses": {"notice_ack": {}},      # e.g., {"ollama_model_notice": true}
}

def _read() -> Dict[str, Any]:
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return json.loads(json.dumps(DEFAULTS))  # deep copy

def _merge(dst: Dict[str, Any], src: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in src.items():
        if isinstance(v, dict):
            dst[k] = _merge(dst.get(k, {}), v)
        else:
            if k not in dst:
                dst[k] = v
    return dst

def load_config() -> Dict[str, Any]:
    cfg = _read()
    # Ensure new default keys appear over time
    cfg = _merge(cfg, DEFAULTS)
    # Honor OLLAMA_HOST env if set (strip scheme; allow host:port)
    env = os.environ.get("OLLAMA_HOST", "").strip()
    if env:
        host = env.replace("http://", "").replace("https://", "")
        if ":" in host:
            h, p = host.split(":", 1)
            cfg["ollama"]["host"] = h
            try: cfg["ollama"]["port"] = int(p)
            except Exception: pass
        else:
            cfg["ollama"]["host"] = host
    # Make sure essential paths exist:
    Path(cfg["paths"]["venvs"]).mkdir(parents=True, exist_ok=True)
    Path(cfg["paths"]["hf_home"]).mkdir(parents=True, exist_ok=True)
    Path(cfg["paths"]["faiss_home"]).mkdir(parents=True, exist_ok=True)
    Path(cfg["paths"]["cache"]).mkdir(parents=True, exist_ok=True)
    Path(cfg["paths"]["logs"]).mkdir(parents=True, exist_ok=True)
    return cfg

def save_config(cfg: Dict[str, Any]) -> None:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(cfg, indent=2, sort_keys=True), encoding="utf-8")
