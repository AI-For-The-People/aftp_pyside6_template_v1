from __future__ import annotations
import importlib.util, os
from pathlib import Path
from typing import Callable, List, Tuple

def _plugins_dir() -> Path:
    # User plugins (no code execution unless they install them)
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA","")) / "AFTP"
    elif os.sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / "AFTP"
    else:
        base = Path.home() / ".local" / "share" / "AFTP"
    d = base / "plugins"
    d.mkdir(parents=True, exist_ok=True)
    return d

def discover_actions() -> List[Tuple[str, Callable]]:
    """
    Convention: plugins can define a function `aftp_actions()` returning [(label, callback), ...].
    (Callbacks should be safe and short; long tasks should spawn threads/subprocesses.)
    """
    actions: List[Tuple[str, Callable]] = []
    for py in _plugins_dir().glob("*.py"):
        try:
            spec = importlib.util.spec_from_file_location(py.stem, py)
            mod = importlib.util.module_from_spec(spec)
            assert spec and spec.loader
            spec.loader.exec_module(mod) # noqa
            if hasattr(mod, "aftp_actions"):
                items = mod.aftp_actions()
                if isinstance(items, list):
                    actions.extend([(str(lbl), cb) for (lbl, cb) in items if callable(cb)])
        except Exception:
            pass
    return actions
