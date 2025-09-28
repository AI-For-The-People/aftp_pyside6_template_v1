from __future__ import annotations
import json
from pathlib import Path
from typing import Dict
from .paths import venvs_dir, runtime_registry_path
from .venv_tools import is_created

def _read_json(p: Path) -> Dict:
    if not p.exists(): return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _write_json(p: Path, data: Dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

def rescan_and_update(expected: Dict[str, dict]) -> Dict:
    reg_path = runtime_registry_path()
    reg = _read_json(reg_path)
    reg.setdefault("venvs", {})
    for name in expected.keys():
        if is_created(name):
            reg["venvs"][name] = {"path": str((venvs_dir() / name).resolve())}
        else:
            reg["venvs"].pop(name, None)
    _write_json(reg_path, reg)
    return reg

def read_registry() -> Dict:
    return _read_json(runtime_registry_path())
