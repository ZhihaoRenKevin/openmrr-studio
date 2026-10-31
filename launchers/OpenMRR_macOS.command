#!/bin/zsh
# Double-clickable macOS Launcher for OpenMRR Studio
# Automatically sets up a local .venv on first launch if needed.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT" || exit 1
export PYTHONPATH="$REPO_ROOT/src:${PYTHONPATH}"

if [ -n "${OPENMRR_PYTHON:-}" ] && [ -x "${OPENMRR_PYTHON}" ]; then
  exec "${OPENMRR_PYTHON}" -u -m openmrr.desktop_app "$@"
fi

if [ ! -x "$REPO_ROOT/.venv/bin/python" ]; then
  if command -v uv >/dev/null 2>&1; then
    echo "[OpenMRR Studio] First-time setup via uv (~30s)..."
    uv sync --extra desktop || uv sync
  else
    SYS_PY=""
    for candidate in python3.12 python3.13 python3.11 /opt/homebrew/bin/python3 /usr/local/bin/python3 python3; do
      if command -v "$candidate" >/dev/null 2>&1; then
        if "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1; then
          SYS_PY="$(command -v "$candidate")"
          break
        fi
      fi
    done
    if [ -z "$SYS_PY" ]; then
      echo "[OpenMRR Studio] Python 3.11 or newer was not found."
      echo "Please install Python 3.12 from https://www.python.org/downloads/macos/ and run this launcher again."
      read -r "?Press Enter to close..."
      exit 1
    fi
    echo "[OpenMRR Studio] First-time setup: creating .venv and installing packages (~1 minute)..."
    "$SYS_PY" -m venv "$REPO_ROOT/.venv"
    "$REPO_ROOT/.venv/bin/python" -m pip install --upgrade pip
    "$REPO_ROOT/.venv/bin/pip" install -e ".[desktop]" || "$REPO_ROOT/.venv/bin/pip" install -e "."
  fi
fi

exec "$REPO_ROOT/.venv/bin/python" -u -m openmrr.desktop_app "$@"
