from __future__ import annotations
import json, os, shutil, subprocess, sys
from pathlib import Path
from typing import List, Tuple, Optional
import requests

OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
_HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}

def _get(url: str, timeout=8):
    return requests.get(url, headers=_HEADERS, timeout=timeout)

def _post(url: str, json_data: dict, timeout=120, stream: bool=False):
    return requests.post(url, json=json_data, headers=_HEADERS, timeout=timeout, stream=stream)

def server_ok() -> bool:
    try:
        r = _get(f"{OLLAMA_URL}/api/tags")
        return r.status_code == 200
    except Exception:
        return False

def list_models() -> List[str]:
    try:
        r = _get(f"{OLLAMA_URL}/api/tags")
        r.raise_for_status()
        data = r.json()
        names = []
        for m in data.get("models", []):
            tag = m.get("name") or m.get("model")
            if tag: names.append(tag)
        return sorted(set(names))
    except Exception:
        return []

def pull_model(name: str) -> Tuple[bool,str]:
    try:
        r = _post(f"{OLLAMA_URL}/api/pull", {"name": name}, timeout=600, stream=True)
        err = None
        for line in r.iter_lines(decode_unicode=True):
            if not line: continue
            try:
                obj = json.loads(line)
                if str(obj.get("status","")).lower().startswith("error"):
                    err = obj.get("status")
            except json.JSONDecodeError:
                pass
        return (True, "Pulled") if r.status_code in (200, 201) and not err else (False, err or f"HTTP {r.status_code}")
    except Exception as e:
        return False, str(e)

def delete_model(name: str) -> Tuple[bool, str]:
    try:
        r = _post(f"{OLLAMA_URL}/api/delete", {"name": name})
        if r.status_code == 200: return True, "Deleted"
        try: return False, r.text[:200]
        except Exception: return False, f"HTTP {r.status_code}"
    except Exception as e:
        return False, str(e)

def prompt(model: str, text: str) -> Tuple[bool,str]:
    try:
        r = _post(f"{OLLAMA_URL}/api/generate",
                  {"model": model, "prompt": text, "stream": False},
                  timeout=600, stream=True)
        if r.status_code not in (200, 201):
            try: return False, r.json().get("error") or r.text[:200]
            except Exception: return False, r.text[:200]

        assembled = []; last_obj = None
        for line in r.iter_lines(decode_unicode=True):
            if not line: continue
            try:
                obj = json.loads(line); last_obj = obj
                if "response" in obj: assembled.append(obj["response"])
                if obj.get("done") is True: break
            except json.JSONDecodeError:
                continue

        if not assembled and last_obj is None:
            try:
                data = r.json()
                return True, data.get("response") or data.get("message","")
            except Exception:
                return True, r.text

        return True, "".join(assembled) if assembled else (last_obj.get("response","") if last_obj else "")
    except Exception as e:
        return False, str(e)

# conversation storage
def conv_dir(base: Path) -> Path:
    d = base / "ollama_sessions"; d.mkdir(parents=True, exist_ok=True); return d

def list_conversations(base: Path) -> List[str]:
    return sorted([p.stem for p in conv_dir(base).glob("*.json")])

def load_conversation(base: Path, name: str) -> dict:
    f = conv_dir(base) / f"{name}.json"
    if f.exists():
        try: return json.loads(f.read_text(encoding="utf-8"))
        except Exception: pass
    return {"name": name, "model": None, "messages": []}

def save_conversation(base: Path, data: dict) -> None:
    (conv_dir(base) / f"{data['name']}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")

# discovery/install/license URLs
def which_ollama() -> Optional[str]:
    p = shutil.which("ollama")
    if p: return p
    if sys.platform.startswith("win"):
        guess = Path(os.getenv("ProgramFiles", "C:\\Program Files")) / "Ollama" / "ollama.exe"
        return str(guess) if guess.exists() else None
    return None

def install_ollama_linux(script_path: Path) -> Tuple[bool, str]:
    try:
        cp = subprocess.run(["bash", str(script_path)], check=False, capture_output=True, text=True)
        ok = cp.returncode == 0
        return ok, (cp.stdout + "\n" + cp.stderr)[-2000:]
    except Exception as e:
        return False, str(e)

def install_ollama_windows(ps1_path: Path) -> None:
    subprocess.Popen(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ps1_path)])

def license_url() -> str:
    return "https://github.com/ollama/ollama/blob/main/LICENSE.md"

def license_raw_url() -> str:
    return "https://raw.githubusercontent.com/ollama/ollama/main/LICENSE.md"

def fetch_ollama_license_text(timeout: int = 10):
    try:
        r = requests.get(license_raw_url(), timeout=timeout)
        if r.status_code == 200 and r.text: return True, r.text
        return False, f"HTTP {r.status_code}"
    except Exception as e:
        return False, str(e)

def download_url() -> str:
    return "https://ollama.com/download"
