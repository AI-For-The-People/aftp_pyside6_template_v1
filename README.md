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
