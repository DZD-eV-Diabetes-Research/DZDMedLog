#!/usr/bin/env bash
# Regenerate docs/configuration.md from medlogserver/config.py via psyplus.
# Run from the repo root.
set -euo pipefail

# Prefer the project venv if it exists, otherwise fall back to whatever python is on PATH
VENV_PYTHON=".medlog-python-env/bin/python"
if [ -f "$VENV_PYTHON" ]; then
    PYTHON="$VENV_PYTHON"
else
    PYTHON="$(which python)"
fi

# Install psyplus into whichever Python we resolved above if it isn't there yet
if ! "$PYTHON" -c "import psyplus" 2>/dev/null; then
    echo "[INFO] psyplus not found — installing..."
    "$PYTHON" -m pip install psyplus -q
fi

"$PYTHON" MedLog/backend/scripts/generate_config_docs.py "$@"
