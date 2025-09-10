from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path
from typing import Dict, List, Tuple

# ---- VENV DEFINITIONS (what we expect to be importable; pip names for installers) ----
EXPECTED: Dict[str, Dict[str, List[str]]] = {
    # minimal GUI runtime
    "core": {
        "imports": ["PySide6", "requests"],
        "pip":     ["PySide6", "requests"],
    },
    # Python client for Ollama (not the server)
    "ollama": {
        "imports": ["ollama", "requests"],
        "pip":     ["ollama", "requests"],
    },
    # Hugging Face Transformers (non-Ollama LLMs)
    "llm_hf": {
        "imports": ["transformers", "accelerate", "safetensors"],
        "pip":     ["transformers", "accelerate", "safetensors"],
    },
    # Image generation / diffusion
    "image": {
        "imports": ["diffusers", "torch"],
        "pip":     ["diffusers", "torch"],
    },
    # Embeddings / semantic search
    "embeddings": {
        "imports": ["sentence_transformers", "faiss"],
        "pip":     ["sentence-transformers", "faiss-cpu"],
    },
    # Indexer (crawl + parse)
    "indexer": {
        "imports": ["trafilatura", "bs4", "lxml"],
        "pip":     ["trafilatura", "beautifulsoup4", "lxml"],
    },
    # OCR & Vision basics
    "ocr_vision": {
        "imports": ["pytesseract", "cv2", "PIL"],
        "pip":     ["pytesseract", "opencv-python-headless", "Pillow"],
    },
    # Speech-to-Text
    "stt": {
        "imports": ["whisper"],
        "pip":     ["openai-whisper"],
    },
    # Text-to-Speech (offline)
    "tts": {
        "imports": ["pyttsx3"],
        "pip":     ["pyttsx3"],
    },
}

# ---- PATH HELPERS ----
def project_root() -> Path:
    return Path(".").resolve()

def venv_dir(name: str) -> Path:
    return project_root() / "venvs" / name

def venv_python(name: str) -> Path:
    if os.name == "nt":
        return venv_dir(name) / "Scripts" / "python.exe"
    else:
        return venv_dir(name) / "bin" / "python3"

def is_created(name: str) -> bool:
    return venv_python(name).exists()

# ---- VALIDATION ----
def _import_probe_code(mods: List[str]) -> str:
    return (
        "import importlib, json\n"
        f"mods = {json.dumps(mods)}\n"
        "out = {}\n"
        "for m in mods:\n"
        "    try:\n"
        "        mod = importlib.import_module(m)\n"
        "        ver = getattr(mod, '__version__', None)\n"
        "        if ver is None:\n"
        "            ver = getattr(getattr(mod, 'version', None), '__version__', None) or ''\n"
        "        out[m] = {'ok': True, 'version': ver}\n"
        "    except Exception as e:\n"
        "        out[m] = {'ok': False, 'error': str(e)}\n"
        "print(json.dumps(out))\n"
    )

def validate(name: str) -> Tuple[bool, List[str]]:
    """
    Try importing each expected module inside the venv's interpreter.
    Returns (ok, missing_import_names). If venv missing, returns (False, ['_venv_missing_']).
    """
    if name not in EXPECTED:
        return (is_created(name), [] if is_created(name) else ["_venv_missing_"])
    if not is_created(name):
        return (False, ["_venv_missing_"])

    py = str(venv_python(name))
    mods = EXPECTED[name]["imports"]
    code = _import_probe_code(mods)
    try:
        proc = subprocess.run([py, "-c", code], capture_output=True, text=True)
        if proc.returncode != 0:
            return (False, mods)
        data = json.loads(proc.stdout.strip() or "{}")
        missing = [k for k, v in data.items() if not v.get("ok")]
        return (len(missing) == 0, missing)
    except Exception:
        return (False, mods)

def details(name: str) -> Dict[str, Dict[str, str]]:
    """
    Return per-module info: { module: {ok: bool, version?: str, error?: str} }.
    """
    mods = EXPECTED.get(name, {}).get("imports", [])
    if not is_created(name):
        return {m: {"ok": False, "error": "venv not created"} for m in mods}
    py = str(venv_python(name))
    code = _import_probe_code(mods)
    try:
        proc = subprocess.run([py, "-c", code], capture_output=True, text=True)
        return json.loads(proc.stdout.strip() or "{}")
    except Exception as e:
        return {m: {"ok": False, "error": f"runner failed: {e}"} for m in mods}
