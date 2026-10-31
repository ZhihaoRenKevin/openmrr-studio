#!/bin/zsh
# Double-clickable macOS Launcher for OpenMRR Studio v3.0
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT" || exit 1
export PYTHONPATH="$REPO_ROOT/src:${PYTHONPATH}"

if [ -x "$REPO_ROOT/.venv/bin/python" ]; then
  exec "$REPO_ROOT/.venv/bin/python" -m openmrr.desktop_app
elif command -v uv >/dev/null 2>&1; then
  exec uv run python -m openmrr.desktop_app
else
  exec python3 -m openmrr.desktop_app
fi
