#!/usr/bin/env bash
set -euo pipefail
"$(dirname "$0")/_venv_common.sh" core PySide6==6.9.2 requests
