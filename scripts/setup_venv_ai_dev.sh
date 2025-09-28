#!/usr/bin/env bash
set -euo pipefail
"$(dirname "$0")/_venv_common.sh" ai_dev torch transformers datasets accelerate peft trl
