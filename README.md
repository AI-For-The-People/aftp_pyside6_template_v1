# AI For The People — Hub Template

This is the **landing / hub app** for the AI For The People ecosystem.  
It is intentionally minimal — you will almost never open it except to:

- **Set global themes** shared across all your AFTP apps.  
- **Create & validate AI runtimes (venvs)** for common tasks.  
- Serve as a **base template** for building specialized apps.

The goal of it is to keep everything else consistent in the ecosystem.

### Universal Shortcuts
- **Ctrl+K / Ctrl+Shift+P** — Command Palette
- **Ctrl+,** — Theme / Settings
- **Ctrl+O** — Ollama quick switcher
- **F1** — Open README

---

## Licenses & Third-Party Tools

**AI For The People (AFTP) Hub** does not bundle third-party runtimes or models.  
Instead, it helps you **link out** to official sources and interact with tools you install on your own.

- **Ollama**: This app does not include Ollama. Install it and review its license at **https://ollama.com**.  
  *Note:* individual models in the Ollama Library (e.g., Llama 3) may have **additional licenses/terms**.  
  The hub shows a one-time notice before your first model pull and links you to the Ollama website.

- **Project license**: See this repository’s own `LICENSE` file for AFTP Hub’s license.

If you add more third-party tools in derived apps, keep the same pattern:
1) Prefer linking users to the official website for install/license.  
2) If you **bundle** a tool, include the appropriate license text(s).  
3) If a model/tool has its own special terms, surface a clear notice in-app before download.

## 🚀 Quick Start

```bash
# from the project root
# Create the core venv
./scripts/setup_venv_core.sh
source venvs/core/bin/activate

# Launch the hub
python3 -m app
```

```powershell
# from the project root
.\scripts\run.ps1
```
\n\n## Shared Runtimes (One Set, Many Apps)

**Goal:** avoid N venvs for N apps. The AFTP Hub creates a **small set of purpose-based runtimes** (venvs) that **all AFTP apps reuse**.

### Where they live
- **Linux:** `~/.local/share/AFTP/venvs/*` and `~/.local/share/AFTP/data/*`
- **Windows:** `%APPDATA%\AFTP\venvs\*` and `%APPDATA%\AFTP\data\*`
- **macOS:** `~/Library/Application Support/AFTP/venvs/*` and `…/data/*`

The Hub keeps a machine-wide **runtime registry** at:

    ~/.local/share/AFTP/runtime_registry.json   (Linux; OS-specific paths elsewhere)

Apps read this file to know what runtimes/tools exist and where they are.

### Typical runtimes
    core/           # PySide6 + essentials
    ollama/         # Python client for Ollama (not the server)
    llm_hf/         # Hugging Face transformers, accelerate…
    image/          # Diffusers + torch (CPU by default)
    embeddings/     # sentence-transformers + faiss-cpu
    indexer/        # trafilatura + bs4 + lxml
    ocr_vision/     # pytesseract + opencv-python-headless + Pillow
    stt/            # whisper
    tts/            # pyttsx3
ai_dev/         # build your own AIs (torch, transformers, datasets, accelerate, peft, trl)

### How an app uses them
Apps **don’t activate** these venvs. They **spawn** the venv’s Python:

    import json, os, subprocess
    from pathlib import Path

    def _aftp_data_dir():
        if os.name == "nt":
            return Path(os.environ["APPDATA"]) / "AFTP"
        elif sys.platform == "darwin":
            return Path.home() / "Library/Application Support/AFTP"
        else:
            return Path.home() / ".local/share/AFTP"

    reg = json.loads((_aftp_data_dir() / "runtime_registry.json").read_text())
    emb_venv = Path(reg["venvs"]["embeddings"]["path"])
    py = emb_venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python3")

    proc = subprocess.run([str(py), "-c", "import faiss, sentence_transformers; print('OK')"],
                          capture_output=True, text=True)
    print(proc.stdout or proc.stderr)

If a runtime is missing, show:
> “This feature needs the *Embeddings* runtime. Open Hub → Runtimes → Create/Update.”

### Hugging Face cache
- Linux: `export HF_HOME=~/.local/share/AFTP/data/hf_cache`
- Windows: `$env:HF_HOME="$env:APPDATA\AFTP\data\hf_cache"`

### CUDA / GPU notes
Torch wheels default to CPU in the image runtime. For GPU:
- Install CUDA/ROCm.
- Reinstall torch with a GPU wheel.

---

## Adding a New Runtime

1. Add entry in `app/core/venv_tools.py` (imports + pip).
2. Add scripts (`setup_venv_<name>.sh/.ps1`).
3. Validate via Hub.
4. Update registry.
5. Spawn `<venv>/bin/python3 -m module`.

---

## Troubleshooting

- Missing imports → check **Details** in Runtimes tab.
- Torch CPU → reinstall with GPU wheel.
- FAISS issues → use `faiss-cpu` unless GPU needed.
- OpenCV GUI errors → use full `opencv-python`.
- Ollama server is separate → install via [https://ollama.com](https://ollama.com).

---

## Ecosystem Roadmap

- GPU auto-detect + wheels
- Shared model/data storage policy
- Build scripts (`build_nuitka.sh/.ps1`)
- Auto-update system
- Plugin system for niche apps
- CI/CD (GitHub Actions for lint/test/package)
- Telemetry (opt-in) with privacy
- License surfacing for bundled tools
- Theme sync & IPC across sibling apps\n

## Quick LLM (Ollama)

Press **Ctrl+J** or use **Tools → Quick LLM…** to open a small window where you can enter a model
name (e.g., `llama3`) and a prompt. This uses your local **Ollama** server via its REST API.
If Ollama is not installed or running, the dialog will let you know; install/start it from the **Ollama** tab.
\n\n## Menu Order Standard

To keep all AFTP apps consistent, follow this top-level menu order, even if some menus are empty:

    File → Edit → View → Tools → Help

### Rules
- **File**: new/open/save/export/quit (always first).
- **Edit**: undo/redo, cut/copy/paste, find/replace.
- **View**: layout, panels, zoom, theme toggle.
- **Tools**: utilities, runtimes, plugins, extensions.
- **Help**: docs, diagnostics, licenses, about (always last).

### Adding domain-specific menus
Insert between **View** and **Tools**:
- **Run / Compile**: for IDEs, training, analysis, or “execute” workflows.
- **Navigate / Go**: for file managers, browsers, indexers.
- **Insert / Format**: for editors with content creation.

### Examples
- **IDE-like app**:  
  `File → Edit → View → Run → Tools → Help`
- **Search/indexer app**:  
  `File → Edit → View → Navigate → Tools → Help`
- **Simple manager**:  
  `File → Edit → View → Tools → Help`

### Goal
- **Left** = most common universal actions (start work).  
- **Middle** = domain-specific tasks (compile, navigate).  
- **Right** = utilities, system info, help (meta actions).\n