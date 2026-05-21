#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

echo "=== Angriness Predictor — venv setup ==="

if [ -d "$VENV_DIR" ]; then
    echo "Existing .venv found at $VENV_DIR"
    echo "  Remove it first if you want a fresh install:"
    echo "  rm -rf $VENV_DIR"
    exit 1
fi

python3 -m venv "$VENV_DIR"
echo "Created venv at $VENV_DIR"

# Windows (Git Bash/MINGW) puts activate in Scripts/, Linux in bin/
if [ -f "$VENV_DIR/Scripts/activate" ]; then
    ACTIVATE="$VENV_DIR/Scripts/activate"
else
    ACTIVATE="$VENV_DIR/bin/activate"
fi

source "$ACTIVATE"
python -m pip install --upgrade pip
python -m pip install -r "$SCRIPT_DIR/requirements.txt"

echo ""
echo "Done. Activate with:"
echo "  source $ACTIVATE"
