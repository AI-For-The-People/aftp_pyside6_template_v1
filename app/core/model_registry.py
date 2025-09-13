from __future__ import annotations
import json, os, sys
from pathlib import Path
from typing import Dict, Any, Optional

def _data_root() -> Path:
    if os.name == "nt":
        return Path(os.environ.get("APPDATA", "")) / "AFTP"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "AFTP"
    else:
        return Path.home() / ".local" / "share" / "AFTP"

def registry_path() -> Path:
    d = _data_root()
    d.mkdir(parents=True, exist_ok=True)
    return d / "models_registry.json"

def read_registry() -> Dict[str, Any]:
    p = registry_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"schema": 1, "models": {}}
    # models: { "handle": { "type": "ollama|hf|tts|stt|custom", "name": "...", "source": "...", "license_url": "...", "notes": "" } }

def write_registry(data: Dict[str, Any]) -> None:
    registry_path().write_text(json.dumps(data, indent=2), encoding="utf-8")

def upsert_model(handle: str, info: Dict[str, Any]) -> None:
    reg = read_registry()
    reg.setdefault("models", {})[handle] = info
    write_registry(reg)

def remove_model(handle: str) -> bool:
    reg = read_registry()
    if handle in reg.get("models", {}):
        del reg["models"][handle]
        write_registry(reg)
        return True
    return False

def list_models(kind: Optional[str] = None) -> Dict[str, Any]:
    reg = read_registry()
    items = reg.get("models", {})
    if kind:
        items = {k:v for k,v in items.items() if v.get("type")==kind}
    return items
