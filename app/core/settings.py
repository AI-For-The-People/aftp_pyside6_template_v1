from __future__ import annotations
import json
from .paths import app_local_data_dir, ensure_dirs

CONFIG_FILE = app_local_data_dir() / "config.json"
DEFAULTS = {
    "show_model_license_notice": True,
    "runtimes": {
        "core": "venvs/core",
        "ollama": "venvs/ollama",
        "llm_hf": "venvs/llm_hf",
        "image": "venvs/image",
        "embeddings": "venvs/embeddings",
        "indexer": "venvs/indexer",
        "ocr_vision": "venvs/ocr_vision",
        "stt": "venvs/stt",
        "tts": "venvs/tts",
        "mamba2": "venvs/mamba2",
    },
    # show licenses modal on first run
    "show_licenses_on_start": True,
}

def load_config():
    ensure_dirs()
    try:
        return {**DEFAULTS, **json.loads(CONFIG_FILE.read_text(encoding="utf-8"))}
    except Exception:
        return DEFAULTS.copy()

def save_config(data: dict):
    ensure_dirs()
    CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
