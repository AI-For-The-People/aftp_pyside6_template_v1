# AFTP Minimal Template

This is a **barebones starting point** for AI For The People apps.  

Includes only:
- Global theme manager
- Minimal main window
- Shared runtime conventions

## Structure

```
aftp_minimal_template/
  app/
    __main__.py
    main.py
    core/theme.py
    ui/
  scripts/
  venvs/
  examples/
```

## Developer Guidance

- Add a **tab**: see `examples/ui_tab.example.py`.
- Integrate **plugins**: see `examples/plugin_system.example.py`.
- Spawn a **runtime python**: see `examples/runtime_spawner.example.py`.
- Build distributables: see `examples/build_script.example.sh`.

## Setup

Linux/macOS:
```
./scripts/setup_venv_core.sh
source venvs/core/bin/activate
python3 -m app
```

Windows (PowerShell):
```
./scripts/setup_venv_core.ps1
.\scriptsun.ps1
```

## Next Steps

- Add tabs or dialogs under `app/ui/`.
- Add new runtimes by extending `app/core/venv_tools.py` (copy from full template).
- Update theme in `app/core/theme.py`.

