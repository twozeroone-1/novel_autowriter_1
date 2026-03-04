#!/usr/bin/env bash
set -e
cd /home/from0to01/novel_autowriter_1_check

if [ -f .venv/bin/activate ]; then
  . .venv/bin/activate
elif [ -f venv/bin/activate ]; then
  . venv/bin/activate
else
  python3 -m venv .venv
  . .venv/bin/activate
fi

python -m pip install -r requirements.txt
exec streamlit run main.py --server.address 0.0.0.0 --server.port 8501
