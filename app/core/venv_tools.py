from __future__ import annotations
import os, subprocess, sys
from pathlib import Path
from typing import List, Tuple
from .paths import venvs_dir

EXPECTED = {
    "core": [],
    "ollama": ["ollama"],
    "llm_hf": ["transformers","accelerate","safetensors"],
    "image": ["diffusers","torch"],
    "embeddings": ["sentence_transformers","faiss"],
    "indexer": ["trafilatura","bs4","lxml"],
    "ocr_vision": ["pytesseract","cv2","PIL"],
    "stt": ["whisper"],
    "tts": ["pyttsx3"],
}

def pybin_for(name: str) -> Path:
    base = venvs_dir()/name
    if sys.platform.startswith("win"):
        return base/"Scripts"/"python.exe"
    return base/"bin"/"python"

def is_created(name: str) -> bool:
    return pybin_for(name).exists()

def validate(name: str) -> Tuple[bool, List[str]]:
    if not is_created(name):
        return False, ["_venv_missing_"]
    py = str(pybin_for(name))
    missing = []
    for mod in EXPECTED.get(name, []):
        code = f"import importlib,sys; sys.exit(0 if importlib.util.find_spec('{mod}') else 1)"
        ok = subprocess.run([py,"-c",code], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode==0
        if not ok: missing.append(mod)
    return len(missing)==0, missing
