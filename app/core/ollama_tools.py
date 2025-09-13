from __future__ import annotations
import os, json, json, platform, shutil
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import requests

# ------------------------------
# Host/Port resolution
# ------------------------------
def _resolve_host_port(config: Optional[Dict] = None) -> str:
    """
    Priority:
      1) config['ollama_host']  (no scheme)
      2) env OLLAMA_HOST        (scheme stripped if present)
      3) 127.0.0.1:11434
    """
    host: Optional[str] = None
    if isinstance(config, dict):
        host = config.get('ollama_host') or config.get('OLLAMA_HOST')
    if not host:
        env = os.environ.get('OLLAMA_HOST')
        if env:
            host = env.replace('http://', '').replace('https://', '')
    if not host:
        host = '127.0.0.1:11434'
    if ':' not in host:
        host = f'{host}:11434'
    return host

def _base_url(config: Optional[Dict] = None) -> str:
    return 'http://' + _resolve_host_port(config)

# ------------------------------
# Ollama HTTP helpers
# ------------------------------
def server_ok(config: Optional[Dict] = None, timeout: float = 1.5) -> bool:
    try:
        r = requests.get(_base_url(config) + '/api/version', timeout=timeout)
        return r.ok
    except Exception:
        return False

def list_models(config: Optional[Dict] = None, timeout: float = 3.0) -> List[str]:
    """Return model names; [] if none/error."""
    try:
        r = requests.get(_base_url(config) + '/api/tags', timeout=timeout)
        if not r.ok:
            return []
        data = r.json()
        out: List[str] = []
        for m in data.get('models', []):
            name = (m or {}).get('name')
            if name:
                out.append(name)
        return out
    except Exception:
        return []

def delete_model(name: str, config: Optional[Dict] = None, timeout: float = 30.0) -> Tuple[bool, str]:
    """DELETE model via POST /api/delete {"name": "..."}."""
    try:
        r = requests.post(_base_url(config) + '/api/delete', json={'name': name}, timeout=timeout)
        if not r.ok:
            return False, f'HTTP {r.status_code}'
        return True, ''
    except Exception as e:
        return False, str(e)

def pull_model(name: str, config: Optional[Dict] = None, timeout: float = 600.0) -> Tuple[bool, str]:
    """
    Pull model via streaming endpoint POST /api/pull {"name": "..."}.
    We drain the stream to completion to avoid 'Extra data' JSON decode errors elsewhere.
    """
    try:
        with requests.post(_base_url(config) + '/api/pull', json={'name': name}, stream=True, timeout=timeout) as r:
            if not r.ok:
                return False, f'HTTP {r.status_code}'
            for _ in r.iter_lines():
                pass  # drain
        return True, ''
    except Exception as e:
        return False, str(e)

def prompt(
    model: str,
    text: str,
    *,
    config: Optional[Dict] = None,
    options: Optional[Dict] = None,
    stream: bool = False,
    timeout: float = 600.0
) -> Tuple[bool, str]:
    """
    Simple text generation using POST /api/generate.
    If stream=True, consume JSON-lines and concatenate 'response' chunks.
    Returns (ok, text_or_error).
    """
    payload = {'model': model, 'prompt': text, 'stream': bool(stream)}
    if options:
        payload['options'] = options
    url = _base_url(config) + '/api/generate'
    try:
        if stream:
            out = []
            with requests.post(url, json=payload, stream=True, timeout=timeout) as r:
                if not r.ok:
                    return False, f'HTTP {r.status_code}'
                for line in r.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue  # tolerate any non-JSON noise
                    chunk = obj.get('response')
                    if chunk:
                        out.append(chunk)
            return True, ''.join(out)
        else:
            r = requests.post(url, json=payload, timeout=timeout)
            if not r.ok:
                return False, f'HTTP {r.status_code}'
            data = r.json()
            return True, data.get('response', '')
    except Exception as e:
        return False, str(e)

# ------------------------------
# Local "Conversations" (file-based)
# ------------------------------
def _data_root() -> Path:
    if platform.system() == "Windows":
        base = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / "AFTP"
    elif platform.system() == "Darwin":
        return Path.home() / "Library" / "Application Support" / "AFTP"
    else:
        base = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        return base / "AFTP"

def _conv_dir() -> Path:
    p = _data_root() / "conversations"
    p.mkdir(parents=True, exist_ok=True)
    return p

def list_conversations(config: Optional[Dict] = None) -> List[str]:
    """
    Return conversation IDs (filenames without .json).
    Ensures there is at least one default: 'conv_1'.
    """
    d = _conv_dir()
    convs = [f.stem for f in d.glob("*.json")]
    if not convs:
        create_conversation("conv_1", config)
        convs = ["conv_1"]
    return sorted(convs)

def create_conversation(name: str, config: Optional[Dict] = None) -> Tuple[bool, str]:
    """
    Create a new empty conversation file if it doesn't exist.
    """
    if not name:
        return False, "empty name"
    path = _conv_dir() / f"{name}.json"
    if path.exists():
        return True, ""
    try:
        path.write_text(json.dumps({"id": name, "messages": []}, indent=2), encoding="utf-8")
        return True, ""
    except Exception as e:
        return False, str(e)

def delete_conversation(name: str, config: Optional[Dict] = None) -> Tuple[bool, str]:
    try:
        path = _conv_dir() / f"{name}.json"
        if path.exists():
            path.unlink()
        return True, ""
    except Exception as e:
        return False, str(e)

def load_conversation(name: str, config: Optional[Dict] = None) -> Dict:
    path = _conv_dir() / f"{name}.json"
    if not path.exists():
        create_conversation(name, config)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"id": name, "messages": []}

def append_message(name: str, role: str, content: str, config: Optional[Dict] = None) -> None:
    """
    Append a message (role: 'user' or 'assistant') and save.
    """
    doc = load_conversation(name, config)
    doc.setdefault("messages", []).append({"role": role, "content": content})
    (_conv_dir() / f"{name}.json").write_text(json.dumps(doc, indent=2), encoding="utf-8")

def save_conversation(name: str, doc: Dict, config: Optional[Dict] = None) -> Tuple[bool,str]:
    """
    Overwrite the conversation file with the provided document.
    Expected shape: {"id": name, "messages": [...]}
    """
    try:
        if not isinstance(doc, dict):
            return False, "doc must be a dict"
        path = _conv_dir() / f"{name}.json"
        path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
        return True, ""
    except Exception as e:
        return False, str(e)


def which_ollama() -> str | None:
    """Return full path to the 'ollama' binary if found in PATH; else None."""
    # Respect explicit env first
    env_path = os.environ.get("OLLAMA_BIN")
    if env_path and os.path.isfile(env_path):
        return env_path
    # Try PATH
    path = shutil.which("ollama")
    return path


def license_url() -> str:
    """Return the canonical website where users can find Ollama's terms and model licenses."""
    return "https://ollama.com"


def install_ollama_linux(script_path: Path | str) -> tuple[bool, str]:
    """Run your installer script if present; otherwise open the website for manual install.
    Returns (ok, output)."""
    try:
        sp = Path(script_path)
        if sp.exists():
            import subprocess
            proc = subprocess.run(["bash", str(sp)], capture_output=True, text=True)
            ok = proc.returncode == 0
            out = (proc.stdout or "") + (proc.stderr or "")
            return ok, out
        else:
            import webbrowser
            webbrowser.open(license_url())
            return False, "installer script not found — opened website"
    except Exception as e:
        return False, str(e)


def install_ollama_windows(script_path: Path | str) -> tuple[bool, str]:
    """Attempt winget install via a provided Powershell script; else open website.
    Returns (ok, output)."""
    try:
        sp = Path(script_path)
        if sp.exists():
            import subprocess
            cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(sp)]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            ok = proc.returncode == 0
            out = (proc.stdout or "") + (proc.stderr or "")
            return ok, out
        else:
            import webbrowser
            webbrowser.open(license_url())
            return False, "installer script not found — opened website"
    except Exception as e:
        return False, str(e)

def generate_once(model: str, text: str | None = None, *, prompt: str | None = None,
                  config: dict | None = None, options: dict | None = None, timeout: float = 600.0):
    """Compatibility wrapper used by QuickLLMDialog. Calls prompt(stream=False)."""
    text = text if text is not None else (prompt or '')
    return prompt(model, text, config=config, options=options, stream=False, timeout=timeout)

def prompt_stream(model: str, text: str, *, config: dict | None = None,
                  options: dict | None = None, timeout: float = 600.0):
    """Yield chunks from /api/generate with stream=true.
    Usage:
        for ok, chunk in prompt_stream("llama3:8b", "Hello", config=...):
            if not ok: print("error", chunk); break
            # else chunk is str piece of the response
    """
    payload = {'model': model, 'prompt': text, 'stream': True}
    if options:
        payload['options'] = options
    url = _base_url(config) + '/api/generate'
    try:
        with requests.post(url, json=payload, stream=True, timeout=timeout) as r:
            if not r.ok:
                yield False, f'HTTP {r.status_code}'
                return
            for line in r.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    # tolerate any non-JSON noise
                    continue
                chunk = obj.get('response')
                if chunk:
                    yield True, chunk
            # end of stream
    except Exception as e:
        yield False, str(e)


def prompt_stream_iter(model: str, text: str, *, config: dict | None = None,
                       options: dict | None = None, timeout: float = 600.0):
    """Yield text chunks from /api/generate (stream=true). Each yielded item is a str piece."""
    payload = {'model': model, 'prompt': text, 'stream': True}
    if options:
        payload['options'] = options
    url = _base_url(config) + '/api/generate'
    try:
        with requests.post(url, json=payload, stream=True, timeout=timeout) as r:
            if not r.ok:
                yield f"[http {r.status_code}]"
                return
            for line in r.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                piece = obj.get('response')
                if piece:
                    yield piece
    except Exception as e:
        yield f"[error] {e}"
