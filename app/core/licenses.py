from __future__ import annotations
from pathlib import Path
from typing import List, Tuple, Dict
import urllib.request

LICENSE_FILENAMES = (
    "LICENSE","LICENSE.txt","LICENSE.md","COPYING","COPYING.txt","NOTICE","NOTICE.txt",
)

KNOWN_LICENSES: Dict[str, dict] = {
    "ollama_llama3": {
        "url": "https://ollama.com/library/llama3:latest/blobs/4fa551d4f938",
        "filename": "ollama_llama3_LICENSE.txt",
        "homepage": "https://ollama.com/library/llama3",
    },
    "ollama": {
        "url": "https://raw.githubusercontent.com/ollama/ollama/main/LICENSE.md",
        "filename": "ollama_LICENSE.md",
        "homepage": "https://github.com/ollama/ollama/blob/main/LICENSE.md",
    },
    "ffmpeg": {
        "url": "https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/COPYING.LGPLv2.1",
        "filename": "ffmpeg_LICENSE_LGPLv2.1.txt",
        "homepage": "https://www.ffmpeg.org/legal.html",
    },
    "tesseract": {
        "url": "https://raw.githubusercontent.com/tesseract-ocr/tesseract/main/LICENSE",
        "filename": "tesseract_LICENSE.txt",
        "homepage": "https://github.com/tesseract-ocr/tesseract/blob/main/LICENSE",
    },
}

def project_root() -> Path:
    return Path.cwd()

def licenses_dir() -> Path:
    d = project_root() / "licenses"
    d.mkdir(parents=True, exist_ok=True)
    return d

def discover_license_files() -> List[Path]:
    root = project_root()
    candidates: List[Path] = []
    for name in LICENSE_FILENAMES:
        p = root / name
        if p.exists() and p.is_file():
            candidates.append(p)
    for p in sorted(licenses_dir().glob("*")):
        if p.is_file():
            candidates.append(p)
    seen = set(); unique: List[Path] = []
    for p in candidates:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp); unique.append(p)
    return unique

def load_text(p: Path, limit_mb: int = 2) -> Tuple[str, str]:
    title = p.name
    try:
        sz = p.stat().st_size
        if sz > limit_mb * 1024 * 1024:
            return title, f"[Skipped: {sz} bytes > {limit_mb}MB]"
        text = p.read_text(encoding="utf-8", errors="replace")
        return title, text
    except Exception as e:
        return title, f"[Error reading {p}: {e}]"

def fetch_and_cache_license(name: str, timeout: int = 15) -> Tuple[bool, str]:
    meta = KNOWN_LICENSES.get(name)
    if not meta:
        return False, f"Unknown license key: {name}"
    url = meta["url"]; dest = licenses_dir() / meta["filename"]
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            data = r.read()
        dest.write_bytes(data)
        return True, str(dest)
    except Exception as e:
        return False, f"{e}"

def fetch_all_known_licenses(timeout: int = 15) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for name in KNOWN_LICENSES:
        ok, msg = fetch_and_cache_license(name, timeout=timeout)
        out[name] = "OK" if ok else f"ERR: {msg}"
    return out