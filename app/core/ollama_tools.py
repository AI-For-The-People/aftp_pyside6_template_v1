# app/core/ollama_tools.py
from __future__ import annotations
import os, sys, json, shutil, subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Iterable, Optional, Iterator
import requests

# ---------- Host/port helpers ----------
def _resolve_host_port(config: Dict | None = None) -> str:
    """
    Priority:
      1) config['ollama_host'] or config['OLLAMA_HOST']  (hostname[:port], no scheme)
         + optional config['ollama_port'] to add :port when missing
      2) env OLLAMA_HOST (scheme stripped if present)
      3) 127.0.0.1:11434
    """
    host: Optional[str] = None
    if isinstance(config, dict):
        host = (config.get("ollama_host")
                or config.get("OLLAMA_HOST")
                or config.get("ollama", {}).get("host"))
        port = (config.get("ollama_port")
                or config.get("ollama", {}).get("port"))
        if host and (":" not in str(host)) and port:
            host = f"{host}:{port}"
    if not host:
        env = os.environ.get("OLLAMA_HOST", "")
        if env:
            host = env.replace("http://", "").replace("https://", "")
    if not host:
        host = "127.0.0.1:11434"
    if ":" not in host:
        host = f"{host}:11434"
    return host

def _base_url(config: Dict | None = None) -> str:
    return f"http://{_resolve_host_port(config)}"

# ---------- Server & models ----------
def server_ok(config: Dict | None = None, timeout: float = 2.0) -> bool:
    try:
        r = requests.get(_base_url(config) + "/api/tags", timeout=timeout)
        return r.ok
    except Exception:
        return False

def list_models(config: Dict | None = None) -> List[str]:
    try:
        r = requests.get(_base_url(config) + "/api/tags", timeout=10)
        r.raise_for_status()
        data = r.json() or {}
        items = data.get("models") or data.get("data") or []
        names: List[str] = []
        for it in items:
            if isinstance(it, str):
                names.append(it)
            elif isinstance(it, dict):
                nm = it.get("name") or it.get("model")
                if nm:
                    names.append(nm)
        # unique, keep order
        seen, out = set(), []
        for n in names:
            if n not in seen:
                seen.add(n); out.append(n)
        return out
    except Exception:
        return []

def pull_model(name: str, config: Dict | None = None) -> Tuple[bool, str]:
    try:
        r = requests.post(_base_url(config) + "/api/pull",
                          json={"name": name, "stream": False}, timeout=600)
        return (True, "pulled") if r.ok else (False, f"{r.status_code} {r.text}")
    except Exception as e:
        return False, str(e)

def delete_model(name: str, config: Dict | None = None) -> Tuple[bool, str]:
    url = _base_url(config) + "/api/delete"
    try:
        # Newer servers prefer DELETE; older accepted POST
        r = requests.delete(url, json={"name": name}, timeout=30)
        if r.ok:
            return True, "deleted"
        r2 = requests.post(url, json={"name": name}, timeout=30)
        return (True, "deleted") if r2.ok else (False, f"{r.status_code} {r.text}")
    except Exception as e:
        return False, str(e)

# ---------- Prompt / generate ----------
def _gen_payload(model: str, text: str, options: Optional[Dict]) -> Dict:
    payload = {"model": model, "prompt": text, "stream": True}
    if options:
        payload["options"] = options
    return payload

def prompt_stream_iter(model: str, text: str, *,
                       config: Dict | None = None,
                       options: Dict | None = None,
                       timeout: float = 600.0) -> Iterator[str]:
    """
    Yields decoded text chunks from Ollama's /api/generate stream.
    Handles both 'data: {json}' and raw JSON lines. Emits only text pieces.
    """
    url = _base_url(config) + "/api/generate"
    payload = _gen_payload(model, text, options)
    with requests.post(url, json=payload, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        for raw in r.iter_lines(chunk_size=1024, decode_unicode=False):
            if not raw:
                continue
            # Some versions prefix with 'data:'
            if raw.startswith(b"data:"):
                raw = raw[5:].strip()
            try:
                obj = json.loads(raw.decode("utf-8", "replace"))
            except Exception:
                # If it's not JSON, just surface text
                yield raw.decode("utf-8", "replace")
                continue
            if "error" in obj:
                # surface error inside the stream; UI will show it
                yield f"\n[stream-error] {obj['error']}"
                break
            piece = obj.get("response") or ""
            if piece:
                yield piece
            if obj.get("done"):
                break

def prompt(model: str, text: str, *,
           config: Dict | None = None,
           options: Dict | None = None,
           timeout: float = 600.0,
           stream: bool = False) -> Tuple[bool, str]:
    """
    Non-streamed call to /api/generate (or collect the stream if stream=True).
    """
    if stream:
        try:
            acc: List[str] = []
            for ch in prompt_stream_iter(model, text, config=config, options=options, timeout=timeout):
                acc.append(ch)
            return True, "".join(acc)
        except Exception as e:
            return False, str(e)
    try:
        url = _base_url(config) + "/api/generate"
        payload = _gen_payload(model, text, options)
        payload["stream"] = False
        r = requests.post(url, json=payload, timeout=timeout)
        if not r.ok:
            return False, f"{r.status_code} {r.text}"
        data = r.json() or {}
        return True, data.get("response", "")
    except Exception as e:
        return False, str(e)

# Back-compat for quick_llm_dialog.py
def generate_once(model: str,
                  text: Optional[str] = None,
                  *,
                  prompt: Optional[str] = None,
                  config: Dict | None = None,
                  options: Dict | None = None,
                  timeout: float = 600.0) -> Tuple[bool, str]:
    """
    Alias that accepts either text=... or prompt=... (older call sites used 'prompt=').
    """
    q = text if text is not None else (prompt or "")
    return prompt(model, q, config=config, options=options, timeout=timeout, stream=False)

# ---------- Minimal conversations on disk ----------
def _app_data_dir() -> Path:
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("APPDATA", str(Path.home() / "AppData/Roaming")))
        return base / "AFTP" / "data"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "AFTP" / "data"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share")))
        return Path(base) / "AFTP" / "data"

def _conv_dir() -> Path:
    d = _app_data_dir() / "conversations"
    d.mkdir(parents=True, exist_ok=True)
    return d

def list_conversations() -> List[str]:
    return sorted([p.stem for p in _conv_dir().glob("*.json")])

def load_conversation(name: str) -> Dict:
    p = _conv_dir() / f"{name}.json"
    if not p.exists():
        return {"id": name, "messages": []}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"id": name, "messages": []}

def save_conversation(name: str, data: Dict) -> None:
    p = _conv_dir() / f"{name}.json"
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

# ---------- Ollama binary helpers ----------
def which_ollama() -> Optional[str]:
    p = shutil.which("ollama")
    if p:
        return p
    for c in ("/usr/local/bin/ollama", "/usr/bin/ollama", str(Path.home() / "bin" / "ollama")):
        if os.path.exists(c):
            return c
    return None

def install_ollama_linux(script_path: Path | str) -> tuple[bool, str]:
    sp = Path(script_path)
    if sp.exists():
        try:
            out = subprocess.check_output(["bash", str(sp)], stderr=subprocess.STDOUT, text=True)
            return True, out
        except subprocess.CalledProcessError as e:
            return False, e.output
    # Fallback: open the site
    try:
        subprocess.Popen(["xdg-open", "https://ollama.com"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass
    return False, "Opened website"

def install_ollama_windows(script_path: Path | str) -> None:
    try:
        subprocess.Popen(["powershell", "-NoProfile", "-Command", "winget install -e --id Ollama.Ollama"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass
    try:
        subprocess.Popen(["start", "https://ollama.com"], shell=True)
    except Exception:
        pass

def license_url() -> str:
    # We now send users to the website instead of pinning a blob URL.
    return "https://ollama.com"
