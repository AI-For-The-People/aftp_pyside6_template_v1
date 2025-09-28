#!/usr/bin/env bash
set -euo pipefail
"$(dirname "$0")/_venv_common.sh" ocr_vision pytesseract opencv-python-headless Pillow
