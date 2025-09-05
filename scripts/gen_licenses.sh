#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$root/licenses"
shopt -s nullglob
for v in "$root"/venvs/*; do
  [ -d "$v" ] || continue
  name="$(basename "$v")"
  echo "[AFTP] Generating third-party licenses for venv: $name"
  source "$v/bin/activate"
  python -m pip install --upgrade pip-licenses >/dev/null 2>&1 || true
  pip-licenses --format=markdown --with-authors --with-urls --with-license-file > "$root/licenses/third_party_${name}.md" || echo "[warn] pip-licenses failed for $name"
done
echo "[AFTP] Done. See ./licenses/third_party_*.md"
