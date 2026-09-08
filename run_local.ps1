# PowerShell runner for Project 3: Document-to-Workflow Platform
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Starting Project 3: Document-to-Workflow Platform " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

if (-not (Test-Path ".\venv\Scripts\Activate.ps1")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    py -3.11 -m venv venv
    .\venv\Scripts\pip install -r requirements.txt
}

Write-Host "Starting FastAPI API server on port 8003..." -ForegroundColor Green
$apiProcess = Start-Process -FilePath ".\venv\Scripts\python.exe" -ArgumentList "-m", "uvicorn", "src.main:app", "--host", "127.0.0.1", "--port", "8003" -PassThru

Write-Host "Starting Streamlit Operations Dashboard on port 8501..." -ForegroundColor Green
Write-Host "API docs: http://127.0.0.1:8003/docs" -ForegroundColor Cyan
Write-Host "Ops Dashboard: http://localhost:8501" -ForegroundColor Cyan

.\venv\Scripts\streamlit.exe run dashboard.py --server.port 8501
