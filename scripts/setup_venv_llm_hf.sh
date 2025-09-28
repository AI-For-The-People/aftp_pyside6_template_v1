#!/usr/bin/env bash
set -euo pipefail
"$(dirname "$0")/_venv_common.sh" llm_hf transformers accelerate safetensors requests
