@echo off
echo ==========================================================
echo  Starting Project 3: Document-to-Workflow Platform
echo ==========================================================

cd /d "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    py -3.11 -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

echo Starting FastAPI server in background (Port 8003)...
start /B venv\Scripts\python.exe -m uvicorn src.main:app --host 127.0.0.1 --port 8003

echo Starting Streamlit Dashboard (Port 8501)...
venv\Scripts\streamlit.exe run dashboard.py --server.port 8501
