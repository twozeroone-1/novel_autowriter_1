@echo off
wsl -d Ubuntu -- bash -lc "cd ~/novel_autowriter_1_check && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && streamlit run main.py --server.address 0.0.0.0 --server.port 8501"
pause
