#!/usr/bin/env bash
set -euo pipefail
"$(dirname "$0")/_venv_common.sh" embeddings sentence-transformers faiss-cpu
