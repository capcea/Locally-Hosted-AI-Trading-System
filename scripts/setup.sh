#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
task_python="${PYTHON:-python3.12}"
if ! command -v "$task_python" >/dev/null 2>&1; then
  echo 'Python 3.12 is required. Set PYTHON=/absolute/path/to/python3.12.' >&2
  exit 1
fi
"$task_python" -c 'import sys; assert sys.version_info[:2] == (3, 12), "Python 3.12 required"'
"$task_python" -m venv .tools
.tools/bin/python -m pip install --cache-dir .cache/pip uv==0.13.5
export UV_CACHE_DIR="$PWD/.cache/uv"
.tools/bin/uv sync --frozen --python "$task_python"
npm --prefix apps/web ci --cache "$PWD/.cache/npm"
.venv/bin/python -m scripts.bootstrap

