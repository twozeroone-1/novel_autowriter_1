@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\\Scripts\\activate.bat" (
    call ".venv\\Scripts\\activate.bat"
) else if exist "venv\\Scripts\\activate.bat" (
    call "venv\\Scripts\\activate.bat"
)

streamlit run main.py --server.address 0.0.0.0 --server.port 8501
