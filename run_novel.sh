#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f ".venv/bin/activate" ]; then
  . ".venv/bin/activate"
elif [ -f "venv/bin/activate" ]; then
  . "venv/bin/activate"
fi

exec streamlit run main.py --server.address 0.0.0.0 --server.port 8501
