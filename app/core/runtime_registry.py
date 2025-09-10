from __future__ import annotations
import json, os, shutil, sys
from pathlib import Path
from typing import Dict, Any

def _data_root() -> Path:
    # OS-specific user data dir
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", str(Path.home()/"AppData/Roaming")))
        return base / "AFTP"
    elif sys.platform == "darwin":
        return Path.home() / "Library/Application Support" / "AFTP"
    else:
        return Path.home() / ".local" / "share" / "AFTP"

def registry_path() -> Path:
    d = _data_root()
    d.mkdir(parents=True, exist_ok=True)
    return d / "runtime_registry.json"

def read_registry() -> Dict[str, Any]:
    p = registry_path()
    if p.exists():
        try: return json.loads(p.read_text(encoding="utf-8"))
        except Exception: pass
    return {"schema": 1, "venvs": {}, "tools": {}}

def write_registry(data: Dict[str, Any]) -> None:
    p = registry_path()
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")

def _which(name: str) -> str | None:
    p = shutil.which(name)
    return p if p else None

def scan_tools() -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    # Ollama
    path = _which("ollama")
    if not path and os.name == "nt":
        g = Path(os.getenv("ProgramFiles", "C:\\Program Files")) / "Ollama" / "ollama.exe"
        path = str(g) if g.exists() else None
    out["ollama"] = {"found": bool(path), "path": path or ""}
    # FFmpeg
    f = _which("ffmpeg")
    out["ffmpeg"] = {"found": bool(f), "path": f or ""}
    # Tesseract
    t = _which("tesseract")
    out["tesseract"] = {"found": bool(t), "path": t or ""}
    return out

def scan_venvs(expected: Dict[str, Any], project_root: Path) -> Dict[str, Any]:
    # Expected is name -> metadata; just verify interpreter exists
    out: Dict[str, Any] = {}
    for name in expected.keys():
        if os.name == "nt":
            py = project_root / "venvs" / name / "Scripts" / "python.exe"
        else:
            py = project_root / "venvs" / name / "bin" / "python3"
        ok = py.exists()
        out[name] = {"path": str(py.parent.parent) if ok else "", "ok": ok}
    return out

def rescan_and_update(expected: Dict[str, Any], project_root: Path) -> Dict[str, Any]:
    reg = read_registry()
    reg["tools"] = scan_tools()
    reg["venvs"] = scan_venvs(expected, project_root)
    write_registry(reg)
    return reg
