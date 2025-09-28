#!/usr/bin/env bash
set -euo pipefail
"$(dirname "$0")/_venv_common.sh" image diffusers torch accelerate safetensors Pillow
