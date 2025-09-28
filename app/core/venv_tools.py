from __future__ import annotations
import os, subprocess
from pathlib import Path
from typing import Dict, List, Tuple
from .paths import venvs_dir

EXPECTED: Dict[str, Dict[str, List[str]]] = {
    "core":        {"imports": ["PySide6", "requests"], "pip": ["PySide6", "requests"]},
    "ollama":      {"imports": ["ollama", "requests"], "pip": ["ollama", "requests"]},
    "llm_hf":      {"imports": ["transformers", "accelerate", "safetensors"], "pip": ["transformers","accelerate","safetensors","requests"]},
    "image":       {"imports": ["diffusers", "torch"], "pip": ["diffusers","torch","accelerate","safetensors","Pillow"]},
    "embeddings":  {"imports": ["sentence_transformers", "faiss"], "pip": ["sentence-transformers","faiss-cpu"]},
    "indexer":     {"imports": ["trafilatura", "bs4", "lxml"], "pip": ["trafilatura","beautifulsoup4","lxml"]},
    "ocr_vision":  {"imports": ["pytesseract", "cv2", "PIL"], "pip": ["pytesseract","opencv-python-headless","Pillow"]},
    "stt":         {"imports": ["whisper"], "pip": ["openai-whisper"]},
    "tts":         {"imports": ["pyttsx3"], "pip": ["pyttsx3"]},
    "ai_dev":      {"imports": ["torch","transformers","datasets","accelerate"], "pip": ["torch","transformers","datasets","accelerate","peft","trl"]},
}

def _pybin(venv_name: str) -> Path:
    base = venvs_dir() / venv_name
    return base / ("Scripts/python.exe" if os.name == "nt" else "bin/python3")

def is_created(venv_name: str) -> bool:
    return _pybin(venv_name).exists()

def py_info(venv_name: str) -> str:
    py = _pybin(venv_name)
    if not py.exists(): return "(python missing)"
    try:
        r = subprocess.run([str(py), "-c", "import sys; print(sys.executable); print(sys.version)"],
                           capture_output=True, text=True, check=False)
        return (r.stdout or "").strip()
    except Exception as e:
        return f"(failed to run python: {e})"

def _try_imports_verbose(py: Path, mods: List[str]) -> Tuple[bool, List[str], List[str]]:
    missing: List[str] = []
    reasons: List[str] = []
    for m in mods:
        code = (
            "import importlib, traceback\n"
            f"m='{m}'\n"
            "try:\n"
            "    importlib.import_module(m)\n"
            "    print('OK:::{}'.format(m))\n"
            "except Exception as e:\n"
            "    print('MISS:::{}:::{}'.format(m, repr(e)))\n"
        )
        r = subprocess.run([str(py), "-c", code], capture_output=True, text=True)
        for line in (r.stdout or "").splitlines():
            if line.startswith("OK:::"):
                continue
            if line.startswith("MISS:::"):
                parts = line.split(":::", 2)
                mod = parts[1] if len(parts) > 1 else "unknown"
                err = parts[2] if len(parts) > 2 else "import error"
                missing.append(mod)
                reasons.append(f"{mod}: {err}")
    return (len(missing) == 0, missing, reasons)

def validate(venv_name: str) -> Tuple[bool, List[str]]:
    """Kept for existing callers; returns (ok, missing_imports)."""
    if not is_created(venv_name):
        return (False, ["_venv_missing_"])
    req = EXPECTED.get(venv_name, {})
    mods = req.get("imports", [])
    if not mods:
        return (True, [])
    ok, missing, _ = _try_imports_verbose(_pybin(venv_name), mods)
    return (ok, missing)

def details(venv_name: str) -> Dict[str, dict]:
    """Return per-module status with versions/reasons when possible."""
    out: Dict[str, dict] = {}
    py = _pybin(venv_name)
    if not py.exists():
        return out
    req = EXPECTED.get(venv_name, {})
    mods = req.get("imports", [])
    ok, missing, reasons = _try_imports_verbose(py, mods)
    reason_map = {r.split(':',1)[0]: r for r in reasons}
    for m in mods:
        info = {"ok": m not in missing}
        if not info["ok"]:
            info["error"] = reason_map.get(m, "import failed")
        # best-effort version
        try:
            code = (
                f"import importlib.metadata as im; "
                f"print(im.version('{m}'))"
            )
            r = subprocess.run([str(py), "-c", code], capture_output=True, text=True)
            v = (r.stdout or "").strip()
            if v:
                info["version"] = v
        except Exception:
            pass
        out[m] = info
    out["_python"] = {"exe": str(py), "info": py_info(venv_name)}
    return out
